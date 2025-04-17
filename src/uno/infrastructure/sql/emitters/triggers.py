# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for triggers and trigger functions."""

from typing import List

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder


class RecordUserAuditFunction(SQLEmitter):
    """Emitter for user audit tracking functions and triggers.

    This emitter generates SQL for tracking which user modified a record.
    """

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for user audit tracking.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Get schema and table information
        schema = self.connection_config.db_schema
        table_name = self.table.name

        # Build the audit function
        function_body = """
        DECLARE
        BEGIN
            -- Update the modified_by field with the current user
            NEW.modified_by = (SELECT current_setting('app.current_user', TRUE));
            RETURN NEW;
        END;
        """

        function_sql = (
            SQLFunctionBuilder()
            .with_schema(schema)
            .with_name(f"{table_name}_audit_user")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Create a SQL statement with metadata
        statements.append(
            SQLStatement(
                name=f"{table_name}_audit_user_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql,
            )
        )

        # Build the trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(schema)
            .with_table(table_name)
            .with_name(f"{table_name}_audit_user_trigger")
            .with_function(f"{table_name}_audit_user")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE")
            .with_for_each("ROW")
            .build()
        )

        # Create a SQL statement with metadata and dependency
        statements.append(
            SQLStatement(
                name=f"{table_name}_audit_user_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
                depends_on=[f"{table_name}_audit_user_function"],
            )
        )

        return statements


class InsertMetaRecordTrigger(SQLEmitter):
    """Emitter for meta record insertion trigger.

    This emitter generates SQL for inserting meta records when data changes.
    """

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for meta record insertion.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Get schema and table information
        schema = self.connection_config.db_schema
        table_name = self.table.name

        # Build the trigger function
        function_body = """
        DECLARE
            meta_id pgulid;
        BEGIN
            -- Call the meta record insertion function
            SELECT insert_meta_record(
                TG_TABLE_SCHEMA,
                TG_TABLE_NAME,
                NEW.id::text,
                current_setting('app.current_user', TRUE)
            ) INTO meta_id;
            
            -- Set meta_id on the new record
            NEW.meta_id = meta_id;
            
            RETURN NEW;
        END;
        """

        function_sql = (
            SQLFunctionBuilder()
            .with_schema(schema)
            .with_name(f"{table_name}_insert_meta")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Create a SQL statement with metadata
        statements.append(
            SQLStatement(
                name=f"{table_name}_insert_meta_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql,
            )
        )

        # Build the trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(schema)
            .with_table(table_name)
            .with_name(f"{table_name}_insert_meta_trigger")
            .with_function(f"{table_name}_insert_meta")
            .with_timing("BEFORE")
            .with_operation("INSERT")
            .with_for_each("ROW")
            .build()
        )

        # Create a SQL statement with metadata and dependency
        statements.append(
            SQLStatement(
                name=f"{table_name}_insert_meta_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
                depends_on=[f"{table_name}_insert_meta_function"],
            )
        )

        return statements
