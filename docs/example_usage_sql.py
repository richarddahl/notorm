# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Example usage of the refactored SQL module structure."""

from typing import List
import logging

from sqlalchemy import Table, MetaData, Column, String, Integer, ForeignKey
from uno.database.config import ConnectionConfig
from uno.database.engine.sync import SyncEngineFactory, sync_connection

# Import from new modular structure
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder, SQLIndexBuilder
from uno.sql.observers import LoggingSQLObserver
from uno.sql.emitters.grants import AlterGrants
from uno.sql.emitters.triggers import RecordUserAuditFunction

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register global observer
SQLEmitter.register_observer(LoggingSQLObserver(logger))

# Define tables
metadata = MetaData()

# Tenant table
tenant_table = Table(
    "tenant",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("domain", String, nullable=False),
    Column("status", String, nullable=False, default="ACTIVE"),
    Column("modified_by", String),
    Column("meta_id", String),
)

# Account table
account_table = Table(
    "account",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("tenant_id", String, ForeignKey("tenant.id"), nullable=False),
    Column("status", String, nullable=False, default="ACTIVE"),
    Column("modified_by", String),
    Column("meta_id", String),
)


# Custom emitter
class ValidateAccountEmitter(SQLEmitter):
    """Emitter for validating account records."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for account validation."""
        statements = []

        if not self.table:
            return statements

        # Get schema and table information
        schema = self.connection_config.db_schema
        table_name = self.table.name

        # Build validation function for unique account names within tenant
        function_body = """
        DECLARE
            account_exists BOOLEAN;
        BEGIN
            -- Check if account with same name already exists for this tenant
            SELECT EXISTS (
                SELECT 1 FROM {schema}.{table_name} 
                WHERE name = NEW.name 
                AND tenant_id = NEW.tenant_id
                AND id != NEW.id  -- Allow updating the same record
            ) INTO account_exists;
            
            IF account_exists THEN
                RAISE EXCEPTION 'Account with name % already exists for this tenant', NEW.name;
            END IF;
            
            RETURN NEW;
        END;
        """.format(
            schema=schema, table_name=table_name
        )

        function_sql = (
            SQLFunctionBuilder()
            .with_schema(schema)
            .with_name(f"{table_name}_validate_unique_name")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        statements.append(
            SQLStatement(
                name=f"{table_name}_validate_unique_name_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql,
            )
        )

        # Build the trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(schema)
            .with_table(table_name)
            .with_name(f"{table_name}_validate_unique_name_trigger")
            .with_function(f"{table_name}_validate_unique_name")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE")
            .with_for_each("ROW")
            .build()
        )

        statements.append(
            SQLStatement(
                name=f"{table_name}_validate_unique_name_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
                depends_on=[f"{table_name}_validate_unique_name_function"],
            )
        )

        # Build index for faster lookup
        index_sql = (
            SQLIndexBuilder()
            .with_schema(schema)
            .with_table(table_name)
            .with_name(f"{table_name}_tenant_name_idx")
            .with_columns(["tenant_id", "name"])
            .unique()
            .build()
        )

        statements.append(
            SQLStatement(
                name=f"{table_name}_tenant_name_idx",
                type=SQLStatementType.INDEX,
                sql=index_sql,
            )
        )

        return statements


# Define SQLConfig classes
class TenantSQLConfig(SQLConfig):
    """SQL configuration for the tenant table."""

    table = tenant_table
    default_emitters = [
        AlterGrants,
        RecordUserAuditFunction,
    ]


class AccountSQLConfig(SQLConfig):
    """SQL configuration for the account table."""

    table = account_table
    default_emitters = [
        AlterGrants,
        RecordUserAuditFunction,
        ValidateAccountEmitter,
    ]


# Example function to emit SQL for all configs
def emit_all_sql(db_name: str, db_user_pw: str, db_schema: str = "public"):
    """Emit SQL for all registered configurations."""
    # Create connection configuration
    connection_config = ConnectionConfig(
        db_name=db_name,
        db_user_pw=db_user_pw,
        db_schema=db_schema,
        db_role=f"{db_name}_login",
    )

    # Create engine factory
    engine_factory = SyncEngineFactory()

    # Emit SQL for all registered configs
    with sync_connection(factory=engine_factory, config=connection_config) as conn:
        logger.info(f"Emitting SQL for all registered SQLConfig classes")
        SQLConfigRegistry.emit_all(
            connection=conn,
            config=connection_config,
        )
        logger.info(f"SQL emission complete")


# Example function to test SQL generation without execution
def test_account_validation(db_schema: str = "test_schema"):
    """Test the account validation emitter."""
    # Create connection configuration
    connection_config = ConnectionConfig(
        db_name="test_db",
        db_user_pw="test_pw",
        db_schema=db_schema,
    )

    # Create emitter instance
    emitter = ValidateAccountEmitter(
        table=account_table,
        connection_config=connection_config,
    )

    # Generate SQL without execution (dry run)
    statements = emitter.generate_sql()

    # Print the generated statements
    print(f"Generated {len(statements)} SQL statements:")
    for stmt in statements:
        print(f"\n--- {stmt.name} ({stmt.type.value}) ---")
        print(stmt.sql)
        if stmt.depends_on:
            print(f"Depends on: {', '.join(stmt.depends_on)}")


# Example usage (commented out to prevent accidental execution)
if __name__ == "__main__":
    # Uncommment to test SQL generation
    # test_account_validation()

    # Uncomment to emit SQL to database
    # emit_all_sql(db_name="my_app", db_user_pw="secure_password")
    pass
