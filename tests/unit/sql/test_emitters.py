# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the SQL emitters functionality.

These tests verify the SQL generation capabilities of various emitters,
ensuring they produce the expected SQL statements.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from sqlalchemy import Table, Column, MetaData, String

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.emitters.table import (
    InsertMetaRecordFunction,
    RecordStatusFunction,
    InsertMetaRecordTrigger,
    AlterGrants,
    TableMergeFunction,
)


from pydantic import BaseModel


class MockSettings(BaseModel):
    """Mock settings for testing."""

    DB_NAME: str = "test_db"
    DB_SCHEMA: str = "test_schema"
    DB_USER_PW: str = "test_password"
    DB_SYNC_DRIVER: str = "postgresql+psycopg2"
    ENFORCE_MAX_GROUPS: bool = True
    MAX_INDIVIDUAL_GROUPS: int = 10
    MAX_BUSINESS_GROUPS: int = 20
    MAX_CORPORATE_GROUPS: int = 30
    MAX_ENTERPRISE_GROUPS: int = 40


@pytest.fixture
def mock_table():
    """Create a mock SQLAlchemy table for testing."""
    metadata = MetaData()
    return Table(
        "test_table",
        metadata,
        Column("id", String, primary_key=True),
        Column("name", String),
        Column("description", String),
    )


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return MockSettings()


class TestInsertMetaRecordFunction:
    """Tests for the InsertMetaRecordFunction emitter."""

    def test_generate_sql(self, mock_config):
        """Test that the emitter generates correct SQL for the meta record insertion function."""
        # Create the emitter with mocked config
        emitter = InsertMetaRecordFunction(config=mock_config)

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result
        assert len(statements) == 1
        assert isinstance(statements[0], SQLStatement)
        assert statements[0].name == "insert_meta_record_function"
        assert statements[0].type == SQLStatementType.FUNCTION

        # Check for essential function components in the SQL
        sql_text = statements[0].sql
        assert "CREATE OR REPLACE FUNCTION" in sql_text
        assert "test_schema.insert_meta_record" in sql_text
        assert "RETURNS TRIGGER" in sql_text
        assert "meta_id VARCHAR(26) := test_schema.generate_ulid();" in sql_text
        assert "SET ROLE test_db_writer;" in sql_text
        assert "INSERT INTO test_schema.meta_record" in sql_text
        assert "NEW.id = meta_id;" in sql_text
        assert "RETURN NEW;" in sql_text


class TestRecordStatusFunction:
    """Tests for the RecordStatusFunction emitter."""

    def test_generate_sql_with_table(self, mock_config, mock_table):
        """Test that the emitter generates correct SQL with a table."""
        # Create the emitter with mocked config and table
        emitter = RecordStatusFunction(config=mock_config, table=mock_table)

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result
        assert len(statements) == 2  # Function and trigger

        # Check the function statement
        function_stmt = [s for s in statements if s.name == "insert_status_columns"][0]
        assert function_stmt.type == SQLStatementType.FUNCTION

        # Check for essential function components in the SQL
        sql_text = function_stmt.sql
        assert "CREATE OR REPLACE FUNCTION" in sql_text
        assert "test_schema.insert_record_status" in sql_text
        assert "RETURNS TRIGGER" in sql_text
        assert "SET ROLE test_db_writer;" in sql_text
        assert "IF TG_OP = 'INSERT' THEN" in sql_text
        assert "NEW.is_active = TRUE;" in sql_text
        assert "ELSIF TG_OP = 'UPDATE' THEN" in sql_text
        assert "NEW.modified_at = now;" in sql_text
        assert "RETURN NEW;" in sql_text

        # Check the trigger statement
        trigger_stmt = [s for s in statements if s.name == "record_status_trigger"][0]
        assert trigger_stmt.type == SQLStatementType.TRIGGER

        # Check for essential trigger components in the SQL
        sql_text = trigger_stmt.sql
        assert "CREATE OR REPLACE TRIGGER" in sql_text
        assert "test_table_insert_record_status_trigger" in sql_text
        assert "BEFORE INSERT OR UPDATE OR DELETE" in sql_text
        assert "ON test_schema.test_table" in sql_text
        assert "FOR EACH ROW" in sql_text
        assert "EXECUTE FUNCTION test_schema.insert_record_status();" in sql_text

    def test_generate_sql_without_table(self, mock_config):
        """Test that the emitter returns empty list when no table is provided."""
        # Create the emitter with mocked config but no table
        emitter = RecordStatusFunction(config=mock_config)

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result is empty since there's no table
        assert len(statements) == 0


class TestInsertMetaRecordTrigger:
    """Tests for the InsertMetaRecordTrigger emitter."""

    def test_generate_sql_with_table(self, mock_config, mock_table):
        """Test that the emitter generates correct SQL with a table."""
        # Create the emitter with mocked config and table
        emitter = InsertMetaRecordTrigger(config=mock_config, table=mock_table)

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result
        assert len(statements) == 1
        assert statements[0].name == "insert_meta_record_trigger"
        assert statements[0].type == SQLStatementType.TRIGGER

        # Check for essential trigger components in the SQL
        sql_text = statements[0].sql
        assert (
            "CREATE OR REPLACE TRIGGER test_table_insert_meta_record_trigger"
            in sql_text
        )
        assert "BEFORE INSERT" in sql_text
        assert "ON test_schema.test_table" in sql_text
        assert "FOR EACH ROW" in sql_text
        assert "EXECUTE FUNCTION test_schema.insert_meta_record();" in sql_text

    def test_generate_sql_without_table(self, mock_config):
        """Test that the emitter returns empty list when no table is provided."""
        # Create the emitter with mocked config but no table
        emitter = InsertMetaRecordTrigger(config=mock_config)

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result is empty since there's no table
        assert len(statements) == 0


class TestAlterGrants:
    """Tests for the AlterGrants emitter."""

    def test_generate_sql_with_table(self, mock_config, mock_table):
        """Test that the emitter generates correct SQL with a table."""
        # Create the emitter with mocked config and table
        emitter = AlterGrants(config=mock_config, table=mock_table)

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result
        assert len(statements) == 1
        assert statements[0].name == "alter_grants"
        assert statements[0].type == SQLStatementType.GRANT

        # Check for essential grant components in the SQL
        sql_text = statements[0].sql
        assert "SET ROLE test_db_admin;" in sql_text
        assert "ALTER TABLE test_schema.test_table OWNER TO test_db_admin;" in sql_text
        assert "REVOKE ALL ON test_schema.test_table FROM PUBLIC" in sql_text
        assert "GRANT SELECT ON test_schema.test_table TO" in sql_text
        assert "test_db_reader" in sql_text
        assert "test_db_writer" in sql_text
        assert "GRANT ALL ON test_schema.test_table TO" in sql_text

    def test_generate_sql_without_table(self, mock_config):
        """Test that the emitter returns empty list when no table is provided."""
        # Create the emitter with mocked config but no table
        emitter = AlterGrants(config=mock_config)

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result is empty since there's no table
        assert len(statements) == 0


class TestTableMergeFunction:
    """Tests for the TableMergeFunction emitter."""

    def test_generate_sql_with_table(self, mock_config, mock_table):
        """Test that the emitter generates correct SQL with a table that has a primary key."""
        # Create a connection config with the expected schema
        from uno.database.config import ConnectionConfig

        # Explicitly initialize the connection_config with the test schema
        from unittest.mock import patch

        with patch("uno.settings.uno_settings", mock_config):
            connection_config = ConnectionConfig(
                db_name=mock_config.DB_NAME,
                db_schema=mock_config.DB_SCHEMA,
                db_user_pw=mock_config.DB_USER_PW,
                db_driver=mock_config.DB_SYNC_DRIVER,
            )

        # Create the emitter with mocked config, connection_config and table
        emitter = TableMergeFunction(
            config=mock_config, connection_config=connection_config, table=mock_table
        )

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result
        assert len(statements) == 1
        assert statements[0].name == "test_table_merge_function"
        assert statements[0].type == SQLStatementType.FUNCTION

        # Check for essential function components in the SQL
        sql_text = statements[0].sql
        # Convert SQLAlchemy object to string to fix Boolean clause error
        sql_text_str = str(sql_text)

        # Use the schema from mock_config
        expected_schema = mock_config.DB_SCHEMA
        assert (
            f"CREATE OR REPLACE FUNCTION {expected_schema}.merge_test_table_record"
            in sql_text_str
        )
        assert "data jsonb" in sql_text_str
        assert "RETURNS jsonb" in sql_text_str
        assert "primary_keys text[] :=" in sql_text_str
        assert "unique_constraints text[][] :=" in sql_text_str
        assert f"MERGE INTO {expected_schema}.test_table AS target" in sql_text_str
        assert "WHEN MATCHED" in sql_text_str
        assert "WHEN NOT MATCHED THEN" in sql_text_str
        # Check for proper handling of action field - note the SQL will have single {} not double
        assert (
            "jsonb_set(result_record, '{_action}', to_jsonb(action_performed))"
            in sql_text_str
        )
        assert "LANGUAGE plpgsql" in sql_text_str

    def test_generate_sql_with_table_and_unique_constraints(self, mock_config):
        """Test that the emitter generates correct SQL with a table that has unique constraints."""
        # Create a table with a unique constraint
        metadata = MetaData()
        unique_table = Table(
            "unique_table",
            metadata,
            Column("id", String, primary_key=True),
            Column("email", String, unique=True),
            Column("code", String, unique=True),
            Column("name", String),
        )

        # Create a connection config with the expected schema
        from uno.database.config import ConnectionConfig

        # Explicitly initialize the connection_config with the test schema
        from unittest.mock import patch

        with patch("uno.settings.uno_settings", mock_config):
            connection_config = ConnectionConfig(
                db_name=mock_config.DB_NAME,
                db_schema=mock_config.DB_SCHEMA,
                db_user_pw=mock_config.DB_USER_PW,
                db_driver=mock_config.DB_SYNC_DRIVER,
            )

        # Create the emitter with mocked config, connection_config and table
        emitter = TableMergeFunction(
            config=mock_config, connection_config=connection_config, table=unique_table
        )

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result
        assert len(statements) == 1

        # Verify unique constraints are included
        sql_text = statements[0].sql
        # Convert SQLAlchemy object to string to fix Boolean clause error
        sql_text_str = str(sql_text)
        assert "unique_constraints text[][] :=" in sql_text_str
        # Note: We can't easily check for exact constraint columns here
        # as SQLAlchemy's in-memory constraints don't fully mirror DB constraints
        # without reflection, but we can check the general structure

    def test_generate_sql_without_table(self, mock_config):
        """Test that the emitter returns empty list when no table is provided."""
        # Create a connection config with the expected schema
        from uno.database.config import ConnectionConfig

        # Explicitly initialize the connection_config with the test schema
        from unittest.mock import patch

        with patch("uno.settings.uno_settings", mock_config):
            connection_config = ConnectionConfig(
                db_name=mock_config.DB_NAME,
                db_schema=mock_config.DB_SCHEMA,
                db_user_pw=mock_config.DB_USER_PW,
                db_driver=mock_config.DB_SYNC_DRIVER,
            )

        # Create the emitter with mocked config and connection_config but no table
        emitter = TableMergeFunction(
            config=mock_config, connection_config=connection_config
        )

        # Generate SQL statements
        statements = emitter.generate_sql()

        # Verify the result is empty since there's no table
        assert len(statements) == 0


class TestSQLEmitterBase:
    """Tests for the base SQLEmitter class."""

    def test_format_template_simple(self, mock_config):
        """Test basic template formatting with direct string formatting."""
        # Create a test template
        template = "CREATE TABLE {schema_name}.test ({db_name} TEXT);"

        # Format with default values
        format_args = {
            "schema_name": mock_config.DB_SCHEMA,
            "db_name": mock_config.DB_NAME,
        }
        formatted = template.format(**format_args)

        assert formatted == "CREATE TABLE test_schema.test (test_db TEXT);"

        # Format with custom values
        format_args = {"schema_name": "custom_schema", "db_name": "custom_db"}
        formatted = template.format(**format_args)

        assert formatted == "CREATE TABLE custom_schema.test (custom_db TEXT);"

    def test_get_function_builder(self, mock_config):
        """Test that get_function_builder returns a properly configured builder."""
        # Create a basic emitter
        emitter = SQLEmitter(config=mock_config)

        # Get a function builder
        builder = emitter.get_function_builder()

        # Build a simple function to verify the builder works
        function_sql = (
            builder.with_schema("test_schema")
            .with_name("test_function")
            .with_body("BEGIN RETURN NULL; END;")
            .build()
        )

        # Check that the built SQL contains expected elements
        assert "CREATE OR REPLACE FUNCTION test_schema.test_function()" in function_sql
        assert "RETURNS TRIGGER" in function_sql
        assert "SET ROLE test_db_admin;" in function_sql
        assert "BEGIN" in function_sql
        assert "RETURN NULL;" in function_sql
        assert "END;" in function_sql
