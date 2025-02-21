# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from psycopg.sql import SQL

from sqlalchemy import text
from sqlalchemy.engine import Connection

from uno.db.sql.sql_emitter import SQLEmitter, DB_NAME, DB_SCHEMA


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
        - Table will be named audit.{db_schema}_{table_name}
    """

    def emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            SET ROLE {db_name}_admin;
            CREATE TABLE audit.{db_schema}_{table_name}
            AS (
                SELECT 
                    t1.*,
                    t2.meta_type_name
                FROM {db_schema}.{table_name} t1
                INNER JOIN {db_schema}.meta t2
                ON t1.id = t2.id
            )
            WITH NO DATA;

            ALTER TABLE audit.{db_schema}_{table_name}
            ADD COLUMN pk INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

            CREATE INDEX {db_schema}_{table_name}_pk_idx
            ON audit.{db_schema}_{table_name} (pk);

            CREATE INDEX {db_schema}_{table_name}_id_modified_at_idx
            ON audit.{db_schema}_{table_name} (id, modified_at);
            """
                )
                .format(
                    db_name=DB_NAME,
                    db_schema=DB_SCHEMA,
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
                INSERT INTO audit.{db_schema}_{table_name}
                SELECT *
                FROM {db_schema}.{table_name}
                WHERE id = NEW.id;
                RETURN NEW;
            END;
            """
            )
            .format(
                db_schema=DB_SCHEMA,
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
