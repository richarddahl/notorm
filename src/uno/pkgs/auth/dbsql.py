# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from pydantic import computed_field

from psycopg.sql import SQL
from sqlalchemy.sql import text

from uno.db.sql.sql import (
    SQLEmitter,
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


class CreateRLSFunctions(SQLEmitter):
    @computed_field
    def emit_create_authorize_user_function_sql(self) -> str:
        return (
            SQL(
                """
            SET ROLE {admin_role};
            DROP FUNCTION IF EXISTS {schema_name}.authorize_user(token TEXT, role_name TEXT DEFAULT 'reader');
            CREATE OR REPLACE FUNCTION {schema_name}.authorize_user(token TEXT, role_name TEXT DEFAULT 'reader')
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
                SELECT secret FROM {schema_name}.token_secret INTO token_secret;

                -- Verify the token
                SELECT header, payload, valid
                FROM {schema_name}.verify(token, token_secret)
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
                    FROM {schema_name}.user
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
            .format(
                admin_role=ADMIN_ROLE,
                db_name=SQL(settings.DB_NAME),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

    @computed_field
    def emit_permissible_groups_sql(self) -> str:
        return (
            SQL(
                """
            SET ROLE {admin_role};
            DROP FUNCTION IF EXISTS {schema_name}.permissible_groups(table_name TEXT, operation TEXT);
            CREATE OR REPLACE FUNCTION {schema_name}.permissible_groups(table_name TEXT, operation TEXT)
            /*
            Function to get the permissible groups for the user
            */
                RETURNS SETOF {schema_name}.group
                LANGUAGE plpgsql
            AS $$
            DECLARE
                user_id TEXT;
            BEGIN
                user_id := current_setting('s_var.id', true);
                RETURN QUERY
                SELECT g.*
                FROM {schema_name}.group g
                JOIN {schema_name}.user__group__role ugr ON ugr.group_id = g.id
                JOIN {schema_name}.user u ON u.id = ugr.user_email
                JOIN {schema_name}.permission tp ON ugr.role_id = tp.id
                WHERE u.id = session_user_id AND tp.is_active = TRUE;
            END $$;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class GetPermissibleGroupsFunction(SQLEmitter):

    @computed_field
    def select_permissible_groups(self) -> str:
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
            .format(schema_name=DB_SCHEMA)
            .as_string()
        )

        return self.createsqlfunction(
            "select_permissible_groups",
            function_string,
            return_type="VARCHAR[]",
            function_args="meta_type TEXT",
        )


# class InsertGroupConstraint(SQLEmitter):
#    def   emit_sql(self, conn: Connection:Engine)-> str:
#        return """ALTER TABLE group ADD CONSTRAINT ck_can_insert_group
#            CHECK (validate_group_insert(tenant_id) = true);
#            """
