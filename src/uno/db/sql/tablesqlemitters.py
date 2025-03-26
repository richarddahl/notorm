# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from pydantic import computed_field

from psycopg.sql import SQL, Literal

from uno.db.sql.sqlemitter import (
    SQLEmitter,
    DB_SCHEMA,
    DB_NAME,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
)


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
                table_name=SQL(self.table.name),
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
            INSERT INTO {schema_name}.meta_type (id)
            VALUES ({table_name})
            ON CONFLICT DO NOTHING;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                writer_role=WRITER_ROLE,
                table_name=Literal(self.table.name),
            )
            .as_string()
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
                table_name=SQL(self.table.name),
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
                table_name=SQL(self.table.name),
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
                table_name=SQL(self.table.name),
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
