# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from pydantic import computed_field

from psycopg.sql import SQL, Literal

from uno.db.sql.sql_emitter import (
    SQLEmitter,
    DB_SCHEMA,
    DB_NAME,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
)
from uno.db.graph.sql_emitters import NodeSQLEmitter


class AlterGrants(SQLEmitter):

    @computed_field
    def alter_grants(self) -> str:
        return (
            SQL(
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
                table_name=SQL(self.table_name),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class InsertMetaType(SQLEmitter):

    @computed_field
    def insert_meta_type(self) -> str:
        return (
            SQL(
                """
            -- Create the meta_type record
            SET ROLE {writer_role};
            INSERT INTO {schema_name}.meta_type (name)
            VALUES ({table_name})
            ON CONFLICT DO NOTHING;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                writer_role=WRITER_ROLE,
                table_name=Literal(self.table_name),
            )
            .as_string()
        )


class InsertMetaRecordTrigger(SQLEmitter):
    @computed_field
    def insert_meta_record_trigger(self) -> str:
        return self.create_sql_trigger(
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
            SQL(
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

        return self.create_sql_function(
            "insert_record_status_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=True,
        )


class RecordUserAuditFunction(SQLEmitter):
    @computed_field
    def insert_record_user_audit_columns(self) -> str:
        function_string = (
            SQL(
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

        return self.create_sql_function(
            "insert_record_user_audit_columns",
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
            SQL(
                """
            BEGIN
                /*
                Function to create a new Permission record when a new MetaType is inserted.
                Records are created for each meta_type with each of the following permissions:
                    SELECT, INSERT, UPDATE, DELETE
                Deleted automatically by the DB via the FKDefinition Constraints ondelete when a meta_type is deleted.
                */
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'SELECT'::uno.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'INSERT'::uno.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'UPDATE'::uno.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'DELETE'::uno.sqloperation);
                RETURN NEW;
            END;
            """
            )
            .format(schema_name=DB_SCHEMA)
            .as_string()
        )

        return self.create_sql_function(
            "insert_permissions",
            function_string,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
        )


class RecordVersionAudit(SQLEmitter):

    @computed_field
    def enable_version_audit(self) -> str:
        return (
            SQL(
                """
            -- Enable auditing for the table
            SELECT audit.enable_tracking('{table_name}'::regclass);
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                table_name=SQL(self.table_name),
            )
            .as_string()
        )


class EnableHistoricalAudit(SQLEmitter):

    @computed_field
    def create_history_table(self) -> str:
        return (
            SQL(
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
                table_name=SQL(self.table_name),
            )
            .as_string()
        )

    @computed_field
    def insert_history_record(self) -> str:
        function_string = (
            SQL(
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
                table_name=SQL(self.table_name),
            )
            .as_string()
        )

        return self.create_sql_function(
            "history",
            function_string,
            timing="AFTER",
            operation="INSERT OR UPDATE",
            include_trigger=True,
            db_function=False,
            security_definer="SECURITY DEFINER",
        )


class GeneralSqlEmitter(
    AlterGrants,
    InsertMetaType,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
    NodeSQLEmitter,
):
    pass
