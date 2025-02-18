# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from dataclasses import dataclass

from psycopg.sql import SQL, Identifier, Literal

from uno.db.sql_emitters import SQLEmitter
from uno.config import settings


@dataclass
class InsertUserRelatedObjectFunctionSQL(SQLEmitter):
    table_name: str = "user"

    def emit_sql(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                relatedobject_id VARCHAR(26) := {db_schema}.generate_ulid();
                user_id VARCHAR(26) := current_setting('rls_var.user_id', true);
                estimate INT4;
            BEGIN
                IF user_id IS NULL THEN
                    /*
                    This should only happen when the very first user is created
                    and therefore a user_id cannot be set in the session variables
                    */
                    SELECT reltuples AS estimate FROM PG_CLASS WHERE relname = TG_TABLE_NAME INTO estimate;
                    IF TG_TABLE_NAME = 'user' AND estimate < 1 THEN
                        user_id := relatedobject_id;
                    END IF;
                END IF;
                /*
                Function used to insert a record into the relatedobject table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the relatedobject table.
                Set as a trigger on the table, so that the relatedobject record is created when the
                record is created.
                */

                SET ROLE {db_role};
                INSERT INTO {db_schema}.relatedobject (id, objecttype_name)
                    VALUES (relatedobject_id, {table_name});
                NEW.id = relatedobject_id;
                RETURN NEW;
            END;
            """
            )
            .format(
                db_schema=Identifier(settings.DB_SCHEMA),
                db_role=Identifier(f"{settings.DB_NAME}_writer"),
                table_name=Literal(self.table_name),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_user_relatedobject",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )


class RecordFieldAuditSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = """
            DECLARE
                user_id TEXT := current_setting('rls_var.user_id', true);
            BEGIN
                /* 
                Function used to set the owned_by_id and modified_by_id fields
                of a table to the user_id of the user making the change. 
                */

                SELECT current_setting('rls_var.user_id', true) INTO user_id;

                IF user_id IS NULL THEN
                    RAISE EXCEPTION 'user_id is NULL';
                END IF;

                IF user_id = '' THEN
                    RAISE EXCEPTION 'user_id is an empty string';
                END IF;

                NEW.modified_at := NOW();
                NEW.modified_by_id = user_id;

                IF TG_OP = 'INSERT' THEN
                    NEW.created_at := NOW();
                    NEW.owned_by_id = user_id;
                END IF;

                IF TG_OP = 'DELETE' THEN
                    NEW.deleted_at = NOW();
                    NEW.deleted_by_id = user_id;
                END IF;

                RETURN NEW;
            END;
            """

        return self.create_sql_function(
            "record_audit",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
        )


@dataclass
class GetPermissibleGroupsFunctionSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = """
            DECLARE
                user_id TEXT := current_setting('rls_var.user_id', true)::TEXT;
                permissible_groups VARCHAR(26)[];
            BEGIN
                SELECT id
                FROM uno.group g
                JOIN uno.user_group_role ugr ON ugr.group_id = g.id AND ugr.user_id = user_id
                JOIN uno.role on ugr.role_id = role.id
                JOIN uno.role_table_operation rto ON rto.role_id = role.id
                JOIN uno.permission tp ON tp.id = rto.table_operation_id
                JOIN uno.objecttype tt ON tt.id = tp.objecttype_name
                WHERE tt.name = objecttype
                INTO permissible_groups;
                RETURN permissible_groups;
            END;
            """

        return self.create_sql_function(
            "get_permissible_groups",
            function_string,
            return_type="VARCHAR[]",
            function_args="objecttype TEXT",
        )


class ValidateGroupInsert(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = f"""
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

                IF NOT {settings.ENFORCE_MAX_GROUPS} THEN
                    RETURN NEW;
                END IF;

                IF tenanttype = 'INDIVIDUAL' AND
                    {settings.MAX_INDIVIDUAL_GROUPS} > 0 AND
                    group_count >= {settings.MAX_INDIVIDUAL_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'BUSINESS' AND
                    {settings.MAX_BUSINESS_GROUPS} > 0 AND
                    group_count >= {settings.MAX_BUSINESS_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'CORPORATE' AND
                    {settings.MAX_CORPORATE_GROUPS} > 0 AND
                    group_count >= {settings.MAX_CORPORATE_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'ENTERPRISE' AND
                    {settings.MAX_ENTERPRISE_GROUPS} > 0 AND
                    group_count >= {settings.MAX_ENTERPRISE_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                RETURN NEW;
            END;
            """

        return self.create_sql_function(
            "validate_group_insert",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )


# class InsertGroupConstraint(SQLEmitter):
#    def emit_sql(self) -> str:
#        return """ALTER TABLE uno.group ADD CONSTRAINT ck_can_insert_group
#            CHECK (uno.validate_group_insert(tenant_id) = true);
#            """


class InsertGroupForTenant(SQLEmitter):
    def emit_sql(self) -> str:
        return f"""CREATE OR REPLACE FUNCTION uno.insert_group_for_tenant()
            RETURNS TRIGGER
            LANGUAGE plpgsql
            AS $$
            BEGIN
                SET ROLE {settings.DB_NAME}_admin;
                INSERT INTO uno.group(tenant_id, name) VALUES (NEW.id, NEW.name);
                RETURN NEW;
            END;
            $$;

            CREATE OR REPLACE TRIGGER insert_group_for_tenant_trigger
            -- The trigger to call the function
            AFTER INSERT ON uno.tenant
            FOR EACH ROW
            EXECUTE FUNCTION uno.insert_group_for_tenant();
            """


class DefaultGroupTenant(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = textwrap.dedent(
            """
            DECLARE
                tenant_id TEXT := current_setting('rls_var.tenant_id', true);
            BEGIN
                IF tenant_id IS NULL THEN
                    RAISE EXCEPTION 'tenant_id is NULL';
                END IF;

                NEW.tenant_id := tenant_id;

                RETURN NEW;
            END;
            """
        )
        return self.create_sql_function(
            "set_tenant_id",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )
