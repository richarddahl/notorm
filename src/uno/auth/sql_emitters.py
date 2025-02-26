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


class DisableRLSOnUserForFirstInsert(TableSQLEmitter):
    """Class for emitting SQL to modify tables before inserting the first user.

    This class handles the necessary table modifications required before inserting
    the initial user into the system. It performs the following operations:
    1. Sets the role to admin
    2. Disables row level security on the user table
    3. Drops NOT NULL constraints on created_by_id and modified_by_id columns in meta_record table

    Inherits from SQLEmitter base class.

    Methods:
        _emit_sql(conn: Engine) -> None: Executes the SQL statements using the provided database connection
    """

    def _emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
                -- Set the role to the admin role
                SET ROLE {admin_role};
                -- Disable row level security on the user table
                ALTER TABLE {db_schema}.user DISABLE ROW LEVEL SECURITY;
            """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    db_schema=DB_SCHEMA,
                )
                .as_string()
            )
        )


class EnableUserRLSAfterFirstInsert(TableSQLEmitter):
    """Emits SQL to alter tables after first user is inserted.

    After the first user is inserted, this class emits SQL that:
    1. Sets the role to admin
    2. Adds NOT NULL constraints to created_by_id and modified_by_id columns in the meta_record table
    3. Enables row level security on the user table

    Args:
        None

    Inherits:
        SQLEmitter

    Methods:
        _emit_sql(conn: Engine) -> None: Executes the SQL statements using the provided database connection
    """

    def _emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
                -- Set the role to the admin role
                SET ROLE {admin_role};
                -- Enable row level security on the user table
                ALTER TABLE {db_schema}.user ENABLE ROW LEVEL SECURITY;
            """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    db_schema=DB_SCHEMA,
                )
                .as_string()
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
