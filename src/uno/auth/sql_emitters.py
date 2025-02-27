# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from psycopg.sql import SQL, Identifier, Literal

from sqlalchemy import text
from sqlalchemy.engine import Connection


from uno.db.sql.sql_emitter import (
    TableSQLEmitter,
    DB_SCHEMA,
    DB_NAME,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
    LOGIN_ROLE,
    BASE_ROLE,
    LIT_BASE_ROLE,
    LIT_READER_ROLE,
    LIT_WRITER_ROLE,
    LIT_ADMIN_ROLE,
    LIT_LOGIN_ROLE,
)
from uno.config import settings


class CreateRLSFunctions(TableSQLEmitter):
    def _emit_sql(self, conn: Connection) -> None:
        self.emit_create_authorize_user_function_sql(conn)
        self.emit_permissible_groups_sql(conn)

    def emit_create_authorize_user_function_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            CREATE OR REPLACE FUNCTION {db_schema}.authorize_user(token TEXT, role_name TEXT DEFAULT 'reader')
            /*
            Function to verify a JWT token and set the session variables necessary for enforcing RLS
            Ensures that:
                The token is valid or
                    raises an Exception (Invalid Token)
                The token contains a sub (which is an email address) or
                    raises an Exception (Token does not contain a sub)
                The email address provided in the sub is of a user in the user table or
                    raises an Exception (User not found)
                The user is active or  Raises an Exception (User is not active)
                The user is not deleted or Raises an Exception (User was deleted)
            If all checks pass, returns the information necessary to enforce RLS otherwise raises an Exception

            The information for RLS is:
                user_id: The ID of the user 
                is_superuser: Whether the user is a superuser
                tenant_id: The ID of the tenant to which the user is associated

            ::param token: The JWT token to verify
            ::param role_name: The role to set for the session
            */
                RETURNS BOOLEAN
                LANGUAGE plpgsql
            AS $$

            DECLARE
                token_header JSONB;
                token_payload JSONB;
                token_valid BOOLEAN;
                sub TEXT;
                expiration INT;
                user_email TEXT; 
                user_id TEXT;
                user_is_superuser TEXT;
                user_tenant_id TEXT;
                user_is_active BOOLEAN;
                user_is_deleted BOOLEAN;
                token_secret TEXT;
                full_role_name TEXT:= '{db_name}_' || role_name;
                admin_role_name TEXT:= '{db_name}_' || 'admin';
            BEGIN
                -- Set the role to the admin role to read from the token_secret table
                EXECUTE 'SET ROLE ' || admin_role_name;

                -- Get the secret from the token_secret table
                SELECT secret FROM {db_schema}.token_secret INTO token_secret;

                -- Verify the token
                SELECT header, payload, valid
                FROM {db_schema}.verify(token, token_secret)
                INTO token_header, token_payload, token_valid;

                IF token_valid THEN

                    -- Get the sub from the token payload
                    sub := token_payload ->> 'sub';

                    IF sub IS NULL THEN
                        RAISE EXCEPTION 'no sub in token';
                    END IF;

                    -- Get the expiration from the token payload
                    expiration := token_payload ->> 'exp';
                    IF expiration IS NULL THEN
                        RAISE EXCEPTION 'no exp in token';
                    END IF;

                    /*
                    Set the session variable for the user's email so that it can be used
                    in the query to get the user's information
                    */
                    PERFORM set_config('rls_var.email', sub, true);

                    -- Query the user table for the user to get the values for the session variables
                    SELECT id, email, is_superuser, tenant_id, is_active, is_deleted 
                    FROM {db_schema}.user
                    WHERE email = sub
                    INTO
                        user_id,
                        user_email,
                        user_is_superuser,
                        user_tenant_id,
                        user_is_active,
                        user_is_deleted;

                    IF user_id IS NULL THEN
                        RAISE EXCEPTION 'user not found';
                    END IF;

                    IF user_is_active = FALSE THEN 
                        RAISE EXCEPTION 'user is not active';
                    END IF; 

                    IF user_is_deleted = TRUE THEN
                        RAISE EXCEPTION 'user was deleted';
                    END IF; 

                    -- Set the session variables used for RLS
                    PERFORM set_config('rls_var.email', user_email, true);
                    PERFORM set_config('rls_var.user_id', user_id, true);
                    PERFORM set_config('rls_var.is_superuser', user_is_superuser, true);
                    PERFORM set_config('rls_var.tenant_id', user_tenant_id, true);

                    --Set the role to the role passed in
                    EXECUTE 'SET ROLE ' || full_role_name;

                ELSE
                    -- Token failed verification
                    RAISE EXCEPTION 'invalid token';
                END IF;
                -- Return the validity of the token
                RETURN token_valid;
            END;
            $$;
            """
                )
                .format(db_name=SQL(settings.DB_NAME))
                .as_string()
            )
        )

    def emit_permissible_groups_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            CREATE OR REPLACE FUNCTION {db_schema}.permissible_groups(table_name TEXT, operation TEXT)
            /*
            Function to get the permissible groups for the user
            */
                RETURNS SETOF {db_schema}.group
                LANGUAGE plpgsql
            AS $$
            DECLARE
                user_id TEXT;
            BEGIN
                user_id := current_setting('s_var.id', true);
                RETURN QUERY
                SELECT g.*
                FROM {db_schema}.group g
                JOIN {db_schema}.user__group__role ugr ON ugr.group_id = g.id
                JOIN {db_schema}.user u ON u.id = ugr.user_email
                JOIN {db_schema}.permission tp ON ugr.role_id = tp.id
                WHERE u.id = session_user_id AND tp.is_active = TRUE;
            END $$;
            """
                )
            )
        )


class UserRecordAuditFunction(TableSQLEmitter):
    def _emit_sql(self, conn: Connection) -> None:
        function_string = (
            SQL(
                """
            DECLARE
                user_id VARCHAR(26) := current_setting('rls_var.user_id', TRUE);
            BEGIN
                /*
                Function used to insert a record into the meta_record table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the meta_record table.
                Set as a trigger on the table, so that the meta_record record is created when the
                record is created.

                Has particular logic to handle the case where the first user is created, as
                the user_id is not yet set in the rls_vars.
                */

                SET ROLE {writer_role};
                IF user_id IS NOT NULL AND
                    NOT EXISTS (SELECT id FROM {db_schema}.user WHERE id = user_id) THEN
                        RAISE EXCEPTION 'user_id in rls_vars is not a valid user';
                END IF;
                IF user_id IS NULL AND
                    EXISTS (SELECT id FROM {db_schema}.user) THEN
                        IF TG_OP = 'UPDATE' THEN
                            IF NOT EXISTS (SELECT id FROM {db_schema}.user WHERE id = OLD.id) THEN
                                RAISE EXCEPTION 'No user defined in rls_vars and this is not the first user being updated';
                            ELSE
                                user_id := OLD.id;
                            END IF;
                        ELSE
                            RAISE EXCEPTION 'No user defined in rls_vars and this is not the first user created';
                        END IF;
                END IF;

                IF TG_OP = 'INSERT' THEN
                    IF user_id IS NULL THEN
                        user_id := NEW.id;
                    END IF;
                    NEW.created_by_id = user_id;
                    NEW.modified_by_id = user_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    NEW.modified_by_id = user_id;
                ELSIF TG_OP = 'DELETE' THEN
                    NEW.deleted_by_id = user_id;
                END IF;

                RETURN NEW;
            END;
            """
            )
            .format(
                writer_role=WRITER_ROLE,
                db_schema=DB_SCHEMA,
            )
            .as_string()
        )

        conn.execute(
            text(
                self.create_sql_function(
                    "user_record_audit",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT OR UPDATE OR DELETE",
                    include_trigger=True,
                    db_function=False,
                )
            )
        )


class GetPermissibleGroupsFunction(TableSQLEmitter):

    def _emit_sql(self, conn: Connection, table_name: str = None) -> str:
        function_string = SQL(
            text(
                """
            DECLARE
                user_id TEXT := current_setting('rls_var.user_id', true)::TEXT;
                permissible_groups VARCHAR(26)[];
            BEGIN
                SELECT id
                FROM group g
                JOIN user__group__role ugr ON ugr.group_id = g.id AND ugr.user_id = user_id
                JOIN role on ugr.role_id = role.id
                JOIN role__permission rp ON rp.role_id = role.id
                JOIN permission p ON p.id = rp.permission_id
                JOIN meta_type mt ON mt.id = tp.meta_type_id
                WHERE mt.name = meta_type
                INTO permissible_groups;
                RETURN permissible_groups;
            END;
            """
            )
            .format(db_schema=DB_SCHEMA)
            .as_string()
        )

        return self.create_sql_function(
            "get_permissible_groups",
            function_string,
            return_type="VARCHAR[]",
            function_args="meta_type TEXT",
        )


class ValidateGroupInsert(TableSQLEmitter):

    def _emit_sql(self, conn: Connection, table_name: str = None) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                group_count INT4;
                tenanttype tenanttype;
            BEGIN
                SELECT tenant_type INTO tenanttype
                FROM tenant
                WHERE id = NEW.tenant_id;

                SELECT COUNT(*) INTO group_count
                FROM group
                WHERE tenant_id = NEW.tenant_id;

                IF NOT {ENFORCE_MAX_GROUPS} THEN
                    RETURN NEW;
                END IF;

                IF tenanttype = 'INDIVIDUAL' AND
                    {MAX_INDIVIDUAL_GROUPS} > 0 AND
                    group_count >= {MAX_INDIVIDUAL_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'BUSINESS' AND
                    {MAX_BUSINESS_GROUPS} > 0 AND
                    group_count >= {MAX_BUSINESS_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'CORPORATE' AND
                    {MAX_CORPORATE_GROUPS} > 0 AND
                    group_count >= {MAX_CORPORATE_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'ENTERPRISE' AND
                    {MAX_ENTERPRISE_GROUPS} > 0 AND
                    group_count >= {MAX_ENTERPRISE_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                RETURN NEW;
            END;
            """
            )
            .format(
                db_schema=DB_SCHEMA,
                ENFORCE_MAX_GROUPS=settings.ENFORCE_MAX_GROUPS,
                MAX_INDIVIDUAL_GROUPS=settings.MAX_INDIVIDUAL_GROUPS,
                MAX_BUSINESS_GROUPS=settings.MAX_BUSINESS_GROUPS,
                MAX_CORPORATE_GROUPS=settings.MAX_CORPORATE_GROUPS,
                MAX_ENTERPRISE_GROUPS=settings.MAX_ENTERPRISE_GROUPS,
            )
            .as_string()
        )

        return self.create_sql_function(
            "validate_group_insert",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )


# class InsertGroupConstraint(SQLEmitter):
#    def _emit_sql(self, conn: Connection:Engine)-> str:
#        return """ALTER TABLE group ADD CONSTRAINT ck_can_insert_group
#            CHECK (validate_group_insert(tenant_id) = true);
#            """


class InsertGroupForTenant(TableSQLEmitter):
    def _emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
                CREATE OR REPLACE FUNCTION {db_schema}.insert_group_for_tenant()
                RETURNS TRIGGER
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    SET ROLE {admin_role};
                    INSERT INTO {db_schema}.group(tenant_id, name) VALUES (NEW.id, NEW.name);
                    RETURN NEW;
                END;
                $$;

                CREATE OR REPLACE TRIGGER insert_group_for_tenant_trigger
                -- The trigger to call the function
                AFTER INSERT ON tenant
                FOR EACH ROW
                EXECUTE FUNCTION {db_schema}.insert_group_for_tenant();
                """
                )
                .format(
                    db_schema=DB_SCHEMA,
                    admin_role=ADMIN_ROLE,
                )
                .as_string()
            )
        )


class DefaultGroupTenant(TableSQLEmitter):
    def _emit_sql(self, conn: Connection) -> str:
        function_string = SQL(
            """
            DECLARE
                tenant_id VARCHAR(26) := current_setting('rls_var.tenant_id', true);
            BEGIN
                IF tenant_id IS NULL THEN
                    RAISE EXCEPTION 'tenant_id is NULL';
                END IF;

                NEW.tenant_id = tenant_id;

                RETURN NEW;
            END;
            """
        ).as_string()
        conn.execute(
            text(
                self.create_sql_function(
                    "set_tenant_id",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT",
                    include_trigger=True,
                    db_function=False,
                )
            )
        )
