# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from psycopg.sql import SQL, Identifier, Literal

from sqlalchemy import text
from sqlalchemy.engine import Connection

from uno.storage.sql.sql_emitter import (
    SQLEmitter,
    DB_SCHEMA,
    DB_NAME,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
)


class AlterGrants(SQLEmitter):

    def emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
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
        )


class RecordVersionAudit(SQLEmitter):
    """Emits SQL to enable record version auditing for a specified table.

    This class prepares and executes SQL to enable audit tracking on a database table
    using the audit schema's enable_tracking function.

    Where used:
        RecordVersionAuditMixin

    Args:
        table_name (str): The name of the table to enable auditing for.

    Example:
        ```python
        emitter = RecordVersionAudit("my_table")
        emitter.emit_sql(engine)
        ```

    Note:
        Requires audit schema and enable_tracking function to be previously set up in the database.
        Uses the global DB_SCHEMA constant for the schema name.
    """

    def emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
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
        )


class CreateHistoryTable(SQLEmitter):
    """Creates a history/audit table for tracking changes in the main table.

    This class generates and executes SQL to create an audit table that mirrors the structure
    of the original table, with additional audit columns. The created table will be in the
    'audit' schema and will include:
    - All columns from the original table
    - A generated identity primary key column 'pk'
    - Indexes on the pk and (id, modified_at) columns

    The audit table is initially created empty (WITH NO DATA) and will be populated through
    triggers or other mechanisms when changes occur in the main table.

    Where used:
        HistoryTableAuditMixin

    Args:
        None directly, but inherits from SQLEmitter which provides table_name

    Returns:
        None

    Example:
        ```
        emitter = CreateHistoryTableSQL()
        emitter.emit_sql(engine)
        ```

    Note:
        - Requires {db_name}_admin role privileges
        - Creates table in the audit schema
        - Table will be named audit.{schema_name}_{table_name}
    """

    def emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
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
        )


class InsertHistoryTableRecord(SQLEmitter):
    """A SQL emitter class that generates audit triggers for database tables.

    This class creates SQL functions and triggers that automatically track changes to database tables
    by copying modified records into corresponding audit tables. It implements the audit trail pattern
    for database change tracking.

    The generated trigger function copies newly inserted or updated records from the source table
    into a corresponding audit table in the audit schema. The audit table must have an identical
    structure to the source table.

    Where used:
        HistoryTableAuditMixin

    Attributes:
        table_name (str): Name of the table to audit

        ```python
        # Create audit trigger for users table
        emitter = InsertHistoryTableRecordSQL('users')
        # This creates a trigger that copies changes from schema.users to audit.schema_users

    Note:
        - The audit tables must exist beforehand in the audit schema
        - Audit tables must have same structure as source tables
        - The naming convention for audit tables is: audit.{schema}_{table_name}
    """

    def emit_sql(self, conn: Connection) -> None:
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

        conn.execute(
            text(
                self.create_sql_function(
                    "history",
                    function_string,
                    timing="AFTER",
                    operation="INSERT OR UPDATE",
                    include_trigger=True,
                    db_function=False,
                    security_definer="SECURITY DEFINER",
                )
            )
        )


class InsertMetaType(SQLEmitter):

    def emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
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
        )


class InsertMetaRecordTrigger(SQLEmitter):
    def emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                self.create_sql_trigger(
                    "insert_meta_record",
                    timing="BEFORE",
                    operation="INSERT",
                    for_each="ROW",
                    db_function=True,
                )
            )
        )


class RecordStatusFunction(SQLEmitter):
    def emit_sql(self, conn: Connection) -> None:
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

        conn.execute(
            text(
                self.create_sql_function(
                    "set_record_status",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT OR UPDATE OR DELETE",
                    include_trigger=True,
                    db_function=True,
                )
            )
        )


class RecordUserAuditFunction(SQLEmitter):
    def emit_sql(self, conn: Connection) -> None:
        function_string = (
            SQL(
                """
            DECLARE
                user_id VARCHAR(26) := current_setting('rls_var.user_id', TRUE);
            BEGIN
                SET ROLE {writer_role};


                IF user_id IS NULL OR user_id = '' THEN
                    IF EXISTS (SELECT id FROM {schema_name}.user) THEN
                        RAISE EXCEPTION 'No user defined in rls_vars';
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

        conn.execute(
            text(
                self.create_sql_function(
                    "set_record_user_audit",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT OR UPDATE OR DELETE",
                    include_trigger=True,
                    db_function=True,
                )
            )
        )


class InsertPermission(SQLEmitter):

    def emit_sql(self, conn: Connection) -> None:
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

        conn.execute(
            text(
                self.create_sql_function(
                    "create_permissions",
                    function_string,
                    timing="AFTER",
                    operation="INSERT",
                    include_trigger=True,
                    db_function=True,
                )
            )
        )
