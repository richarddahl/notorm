# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from psycopg.sql import SQL, Identifier, Literal

from sqlalchemy import text
from sqlalchemy.engine import Engine


from uno.db.sql_emitters import (
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


@dataclass
class GetPermissibleGroupsFunctionSQL(SQLEmitter):
    def emit_sql(self, conn: Engine) -> str:
        function_string = """
            DECLARE
                user_id TEXT := current_setting('rls_var.user_id', true)::TEXT;
                permissible_groups VARCHAR(26)[];
            BEGIN
                SELECT id
                FROM uno.group g
                JOIN uno.user__group__role ugr ON ugr.group_id = g.id AND ugr.user_id = user_id
                JOIN uno.role on ugr.role_id = role.id
                JOIN uno.role__permission rp ON rp.role_id = role.id
                JOIN uno.permission p ON p.id = rp.permission_id
                JOIN uno.meta_type mt ON mt.id = tp.metatype_name
                WHERE mt.name = meta_type
                INTO permissible_groups;
                RETURN permissible_groups;
            END;
            """

        return self.create_sql_function(
            "get_permissible_groups",
            function_string,
            return_type="VARCHAR[]",
            function_args="meta_type TEXT",
        )


class ValidateGroupInsert(SQLEmitter):
    def emit_sql(self, conn: Engine) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                group_count INT4;
                tenanttype uno.tenanttype;
            BEGIN
                SELECT tenant_type INTO tenanttype
                FROM uno.tenant
                WHERE id = NEW.tenant_id;

                SELECT COUNT(*) INTO group_count
                FROM uno.group
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
#    def emit_sql(self, conn:Engine)-> str:
#        return """ALTER TABLE uno.group ADD CONSTRAINT ck_can_insert_group
#            CHECK (uno.validate_group_insert(tenant_id) = true);
#            """


class InsertGroupForTenant(SQLEmitter):
    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """CREATE OR REPLACE FUNCTION uno.insert_group_for_tenant()
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
            AFTER INSERT ON {db_schema}.tenant
            FOR EACH ROW
            EXECUTE FUNCTION {db_schema}.insert_group_for_tenant();
            """
                )
                .format(db_schema=DB_SCHEMA, admin_role=ADMIN_ROLE)
                .as_string()
            )
        )


class DefaultGroupTenant(SQLEmitter):
    def emit_sql(self, conn: Engine) -> str:
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
