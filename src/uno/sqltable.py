# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import Optional, ClassVar

from psycopg import sql
from pydantic import BaseModel, ConfigDict, computed_field
from sqlalchemy.sql import text
from sqlalchemy.engine.base import Connection
from sqlalchemy import Table

from uno.errors import UnoError
from uno.config import settings


class InsertMetaRecordFunction(SQLEmitter):
    @computed_field
    def insert_meta_record_function(self) -> str:
        function_string = (
            sql.SQL(
                """
            DECLARE
                meta_id VARCHAR(26) := {schema_name}.generate_ulid();
            BEGIN
                /*
                Function used to insert a record into the meta_record table, when a 
                polymorphic record is inserted.
                */
                SET ROLE {writer_role};

                INSERT INTO {schema_name}.meta_record (id, meta_type_id) VALUES (meta_id, TG_TABLE_NAME);
                NEW.id = meta_id;
                RETURN NEW;
            END;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                writer_role=WRITER_ROLE,
            )
            .as_string()
        )

        return self.createsqlfunction(
            "insert_meta_record",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=False,
            db_function=True,
        )


class InsertMetaRecordTrigger(SQLEmitter):
    @computed_field
    def insert_meta_record_trigger(self) -> str:
        return self.createsqltrigger(
            "insert_meta_record",
            timing="BEFORE",
            operation="INSERT",
            for_each="ROW",
            db_function=True,
        )


class RecordStatusFunction(SQLEmitter):
    @computed_field
    def insert_status_columns(self) -> str:
        function_string = (
            sql.SQL(
                """
            DECLARE
                now TIMESTAMP := NOW();
            BEGIN
                SET ROLE {writer_role};

                IF TG_OP = 'INSERT' THEN
                    NEW.is_active = TRUE;
                    NEW.is_deleted = FALSE;
                    NEW.created_at = now;
                    NEW.modified_at = now;
                ELSIF TG_OP = 'UPDATE' THEN
                    NEW.modified_at = now;
                ELSIF TG_OP = 'DELETE' THEN
                    NEW.is_active = FALSE;
                    NEW.is_deleted = TRUE;
                    NEW.deleted_at = now;
                END IF;

                RETURN NEW;
            END;
            """
            )
            .format(writer_role=WRITER_ROLE)
            .as_string()
        )

        return self.createsqlfunction(
            "insert_record_status_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=True,
        )


class RecordUserAuditFunction(SQLEmitter):
    @computed_field
    def manage_record_user_audit_columns(self) -> str:
        function_string = (
            sql.SQL(
                """
            DECLARE
                user_id VARCHAR(26) := current_setting('rls_var.user_id', TRUE);
            BEGIN
                SET ROLE {writer_role};


                IF user_id IS NULL OR user_id = '' THEN
                    IF EXISTS (SELECT id FROM {schema_name}.user) THEN
                        RAISE EXCEPTION 'No user def ined in rls_vars';
                    END IF;
                END IF;
                IF NOT EXISTS (SELECT id FROM {schema_name}.user WHERE id = user_id) THEN
                    RAISE EXCEPTION 'User ID in rls_vars is not a valid user';
                END IF;

                IF TG_OP = 'INSERT' THEN
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
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

        return self.createsqlfunction(
            "manage_record_audit_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=True,
        )


class InsertPermission(SQLEmitter):

    @computed_field
    def insert_permissions(self) -> str:
        function_string = (
            sql.SQL(
                """
            BEGIN
                /*
                Function to create a new Permission record when a new MetaType is inserted.
                Records are created for each meta_type with each of the following permissions:
                    SELECT, INSERT, UPDATE, DELETE
                Deleted automatically by the DB via the FKDefinition Constraints ondelete when a meta_type is deleted.
                */
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'SELECT'::{schema_name}.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'INSERT'::{schema_name}.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'UPDATE'::{schema_name}.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'DELETE'::{schema_name}.sqloperation);
                RETURN NEW;
            END;
            """
            )
            .format(schema_name=DB_SCHEMA)
            .as_string()
        )

        return self.createsqlfunction(
            "insert_permissions",
            function_string,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
        )


class ValidateGroupInsert(SQLEmitter):

    @computed_field
    def validate_group_insert(self) -> str:
        function_string = (
            sql.SQL(
                """
            DECLARE
                group_count INT4;
                tenanttype tenanttype;
            BEGIN
                SELECT tenant_type INTO tenanttype
                FROM {schema_name}.tenant
                WHERE id = NEW.tenant_id;

                SELECT COUNT(*) INTO group_count
                FROM {schema_name}.group
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
                schema_name=DB_SCHEMA,
                ENFORCE_MAX_GROUPS=settings.ENFORCE_MAX_GROUPS,
                MAX_INDIVIDUAL_GROUPS=settings.MAX_INDIVIDUAL_GROUPS,
                MAX_BUSINESS_GROUPS=settings.MAX_BUSINESS_GROUPS,
                MAX_CORPORATE_GROUPS=settings.MAX_CORPORATE_GROUPS,
                MAX_ENTERPRISE_GROUPS=settings.MAX_ENTERPRISE_GROUPS,
            )
            .as_string()
        )

        return self.createsqlfunction(
            "validate_group_insert",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )


class InsertGroupForTenant(SQLEmitter):
    @computed_field
    def insert_group_for_tenant(self) -> str:
        return (
            sql.SQL(
                """
                SET ROLE {admin_role};
                CREATE OR REPLACE FUNCTION {schema_name}.insert_group_for_tenant()
                RETURNS TRIGGER
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    SET ROLE {admin_role};
                    INSERT INTO {schema_name}.group(tenant_id, name) VALUES (NEW.id, NEW.name);
                    RETURN NEW;
                END;
                $$;

                CREATE OR REPLACE TRIGGER insert_group_for_tenant_trigger
                -- The trigger to call the function
                AFTER INSERT ON tenant
                FOR EACH ROW
                EXECUTE FUNCTION {schema_name}.insert_group_for_tenant();
                """
            )
            .format(
                schema_name=DB_SCHEMA,
                admin_role=ADMIN_ROLE,
            )
            .as_string()
        )


class DefaultGroupTenant(SQLEmitter):
    @computed_field
    def insert_default_group_column(self) -> str:
        function_string = sql.SQL(
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
        return self.createsqlfunction(
            "insert_default_group_column",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )


class UserRecordUserAuditFunction(SQLEmitter):
    @computed_field
    def manage_user_user_audit_columns(self) -> str:
        function_string = (
            sql.SQL(
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
                    NOT EXISTS (SELECT id FROM {schema_name}.user WHERE id = user_id) THEN
                        RAISE EXCEPTION 'user_id in rls_vars is not a valid user';
                END IF;
                IF user_id IS NULL AND
                    EXISTS (SELECT id FROM {schema_name}.user) THEN
                        IF TG_OP = 'UPDATE' THEN
                            IF NOT EXISTS (SELECT id FROM {schema_name}.user WHERE id = OLD.id) THEN
                                RAISE EXCEPTION 'No user def ined in rls_vars and this is not the first user being updated';
                            ELSE
                                user_id := OLD.id;
                            END IF;
                        ELSE
                            RAISE EXCEPTION 'No user def ined in rls_vars and this is not the first user created';
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
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

        return self.createsqlfunction(
            "manage_audit_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=False,
        )


## TABLE sql.SQL


class AlterGrants(SQLEmitter):

    @computed_field
    def alter_grants(self) -> str:
        return (
            sql.SQL(
                """
            SET ROLE {admin_role};
            -- Congigure table ownership and privileges
            ALTER TABLE {schema_name}.{table_name} OWNER TO {admin_role};
            REVOKE ALL ON {schema_name}.{table_name} FROM PUBLIC, {writer_role}, {reader_role};
            GRANT SELECT ON {schema_name}.{table_name} TO
                {reader_role},
                {writer_role};
            GRANT ALL ON {schema_name}.{table_name} TO
                {writer_role};
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                table_name=sql.SQL(self.table.name),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class InsertMetaType(SQLEmitter):

    @computed_field
    def insert_meta_type(self) -> str:
        return (
            sql.SQL(
                """
            -- Create the meta_type record
            SET ROLE {writer_role};
            INSERT INTO {schema_name}.meta_type (id)
            VALUES ({table_name})
            ON CONFLICT DO NOTHING;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                writer_role=WRITER_ROLE,
                table_name=sql.Literal(self.table.name),
            )
            .as_string()
        )


class RecordVersionAudit(SQLEmitter):

    @computed_field
    def enable_version_audit(self) -> str:
        return (
            sql.SQL(
                """
            -- Enable auditing for the table
            SELECT audit.enable_tracking('{table_name}'::regclass);
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                table_name=sql.SQL(self.table.name),
            )
            .as_string()
        )


class EnableHistoricalAudit(SQLEmitter):

    @computed_field
    def create_history_table(self) -> str:
        return (
            sql.SQL(
                """
            SET ROLE {db_name}_admin;
            CREATE TABLE audit.{schema_name}_{table_name}
            AS (
                SELECT 
                    t1.*,
                    t2.meta_type_id
                FROM {schema_name}.{table_name} t1
                INNER JOIN meta_record t2
                ON t1.id = t2.id
            )
            WITH NO DATA;

            ALTER TABLE audit.{schema_name}_{table_name}
            ADD COLUMN pk INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

            CREATE INDEX {schema_name}_{table_name}_pk_idx
            ON audit.{schema_name}_{table_name} (pk);

            CREATE INDEX {schema_name}_{table_name}_id_modified_at_idx
            ON audit.{schema_name}_{table_name} (id, modified_at);
            """
            )
            .format(
                db_name=DB_NAME,
                schema_name=DB_SCHEMA,
                table_name=sql.SQL(self.table.name),
            )
            .as_string()
        )

    @computed_field
    def insert_history_record(self) -> str:
        function_string = (
            sql.SQL(
                """
            BEGIN
                INSERT INTO audit.{schema_name}_{table_name}
                SELECT *
                FROM {schema_name}.{table_name}
                WHERE id = NEW.id;
                RETURN NEW;
            END;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                table_name=sql.SQL(self.table.name),
            )
            .as_string()
        )

        return self.createsqlfunction(
            "history",
            function_string,
            timing="AFTER",
            operation="INSERT OR UPDATE",
            include_trigger=True,
            db_function=False,
            security_definer="SECURITY DEFINER",
        )


class MergeRecord(SQLEmitter):

    @computed_field
    def create_merge_record(self) -> str:
        with open(f"{settings.UNO_ROOT}/uno/merge_record.sql", "r") as file:
            sql_statment = file.read()
        return sql_statment
