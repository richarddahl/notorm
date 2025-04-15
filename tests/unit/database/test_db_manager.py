# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the database/db_manager.py module.

These tests verify the functionality of the DBManager class,
focusing on DDL operations and SQL emitter integration.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch, call
from contextlib import contextmanager
import sqlite3

import psycopg
from sqlalchemy import text

from uno.database.db_manager import DBManager
from uno.database.config import ConnectionConfig
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType


class MockSQLEmitter(SQLEmitter):
    """Mock SQLEmitter for testing."""
    
    def __init__(self, statements=None):
        super().__init__()
        self._statements = statements or []
    
    def generate_sql(self):
        """Generate SQL statements."""
        return self._statements


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock(spec=logging.Logger)


@pytest.fixture
def mock_statements():
    """Create mock SQL statements for testing."""
    return [
        SQLStatement(name="stmt1", type=SQLStatementType.FUNCTION, sql="CREATE FUNCTION test();"),
        SQLStatement(name="stmt2", type=SQLStatementType.TABLE, sql="CREATE TABLE test (id INT);"),
    ]


class TestDBManager:
    """Tests for the DBManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = MagicMock(spec=logging.Logger)
        
        # Create mocks for connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        
        # Configure mock cursor to be returned by connection
        mock_cursor_cm = MagicMock()
        mock_cursor_cm.__enter__.return_value = self.mock_cursor
        self.mock_conn.cursor.return_value = mock_cursor_cm
        
        # Configure connection context manager
        mock_conn_cm = MagicMock()
        mock_conn_cm.__enter__.return_value = self.mock_conn
        
        # Create a deterministic connection provider function
        def mock_get_connection():
            return mock_conn_cm
        
        self.db_manager = DBManager(
            connection_provider=mock_get_connection,
            logger=self.logger,
            environment="development"
        )
    
    def test_initialization(self):
        """Test DBManager initialization."""
        # Verify initial state
        assert self.db_manager.logger == self.logger
        assert self.db_manager.get_connection is not None
    
    def test_execute_ddl(self):
        """Test executing a DDL statement."""
        # Run the method
        self.db_manager.execute_ddl("CREATE TABLE test (id INT);")
        
        # Verify cursor execute was called with the correct SQL
        self.mock_cursor.execute.assert_called_once_with("CREATE TABLE test (id INT);")
    
    def test_execute_ddl_validation(self):
        """Test DDL statement validation."""
        # Create a manager with production environment
        prod_db_manager = DBManager(
            connection_provider=self.db_manager.get_connection,
            logger=self.logger,
            environment="production"
        )
        
        # Test disallowed destructive operations on production databases
        with pytest.raises(ValueError) as excinfo:
            prod_db_manager.execute_ddl("DROP TABLE test;")
        
        # Check that the error message contains the expected text
        assert "not allowed in production environment" in str(excinfo.value)
        
        # Test allowed operations in development
        self.db_manager.execute_ddl("DROP DATABASE test_db;")
        
        # Test allowed drops for non-production databases
        self.db_manager.execute_ddl("DROP DATABASE test_db;")
        self.mock_cursor.execute.assert_called_with("DROP DATABASE test_db;")
    
    def test_execute_script(self):
        """Test executing a SQL script."""
        script = "CREATE TABLE test1 (id INT);\nCREATE TABLE test2 (id INT);"
        
        # Run the method
        self.db_manager.execute_script(script)
        
        # Verify cursor execute was called with the script
        self.mock_cursor.execute.assert_called_once_with(script)
    
    def test_execute_script_validation(self):
        """Test script validation."""
        # Create a manager with production environment
        prod_db_manager = DBManager(
            connection_provider=self.db_manager.get_connection,
            logger=self.logger,
            environment="production"
        )
        
        # Test disallowed destructive operations for production databases
        with pytest.raises(ValueError) as excinfo:
            prod_db_manager.execute_script("""
            CREATE TABLE test (id INT);
            DROP TABLE other_test;
            """)
        
        # Check that the error message contains the expected text
        assert "not allowed in production environment" in str(excinfo.value)
        
        # Test allowed operations in development
        self.db_manager.execute_script("""
            CREATE TABLE test (id INT);
            DROP DATABASE test_db;
        """)
    
    def test_execute_from_emitter(self, mock_statements):
        """Test executing SQL from an emitter."""
        # Create a mock emitter with test statements
        emitter = MockSQLEmitter(statements=mock_statements)
        
        # Mock the execute_ddl method
        self.db_manager.execute_ddl = MagicMock()
        
        # Run the method
        self.db_manager.execute_from_emitter(emitter)
        
        # Verify execute_ddl was called for each statement
        assert self.db_manager.execute_ddl.call_count == 2
        self.db_manager.execute_ddl.assert_has_calls([
            call("CREATE FUNCTION test();"),
            call("CREATE TABLE test (id INT);"),
        ])
    
    def test_execute_from_emitters(self, mock_statements):
        """Test executing SQL from multiple emitters."""
        # Create multiple mock emitters
        emitter1 = MockSQLEmitter(statements=mock_statements[:1])
        emitter2 = MockSQLEmitter(statements=mock_statements[1:])
        
        # Mock the execute_from_emitter method
        self.db_manager.execute_from_emitter = MagicMock()
        
        # Run the method
        self.db_manager.execute_from_emitters([emitter1, emitter2])
        
        # Verify execute_from_emitter was called for each emitter
        assert self.db_manager.execute_from_emitter.call_count == 2
        self.db_manager.execute_from_emitter.assert_any_call(emitter1)
        self.db_manager.execute_from_emitter.assert_any_call(emitter2)
    
    def test_create_schema(self):
        """Test creating a schema."""
        # Mock the execute_ddl method
        self.db_manager.execute_ddl = MagicMock()
        
        # Run the method
        self.db_manager.create_schema("test_schema")
        
        # Verify execute_ddl was called with correct SQL
        self.db_manager.execute_ddl.assert_called_once_with(
            "CREATE SCHEMA IF NOT EXISTS test_schema"
        )
    
    def test_drop_schema(self):
        """Test dropping a schema."""
        # Mock the execute_ddl method
        self.db_manager.execute_ddl = MagicMock()
        
        # Run the method without cascade
        self.db_manager.drop_schema("test_schema")
        
        # Verify execute_ddl was called with correct SQL
        self.db_manager.execute_ddl.assert_called_once_with(
            "DROP SCHEMA IF EXISTS test_schema "
        )
        
        # Reset mock
        self.db_manager.execute_ddl.reset_mock()
        
        # Run the method with cascade
        self.db_manager.drop_schema("test_schema", cascade=True)
        
        # Verify execute_ddl was called with correct SQL including CASCADE
        self.db_manager.execute_ddl.assert_called_once_with(
            "DROP SCHEMA IF EXISTS test_schema CASCADE"
        )
    
    def test_create_extension(self):
        """Test creating an extension."""
        # Mock the execute_ddl method
        self.db_manager.execute_ddl = MagicMock()
        
        # Run the method without schema
        self.db_manager.create_extension("pg_trgm")
        
        # Verify execute_ddl was called with correct SQL
        self.db_manager.execute_ddl.assert_called_once_with(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm "
        )
        
        # Reset mock
        self.db_manager.execute_ddl.reset_mock()
        
        # Run the method with schema
        self.db_manager.create_extension("pg_trgm", schema="public")
        
        # Verify execute_ddl was called with correct SQL including schema
        self.db_manager.execute_ddl.assert_called_once_with(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA public"
        )
    
    def test_table_exists(self):
        """Test checking if a table exists."""
        # Setup mock cursor with return value
        self.mock_cursor.fetchone.return_value = (True,)
        
        # Run the method without schema
        result = self.db_manager.table_exists("test_table")
        
        # Verify the result and SQL execution
        assert result is True
        self.mock_cursor.execute.assert_called_once()
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "SELECT EXISTS" in sql_called
        assert "table_name = 'test_table'" in sql_called
        
        # Reset mocks
        self.mock_cursor.execute.reset_mock()
        
        # Run the method with schema
        result = self.db_manager.table_exists("test_table", schema="public")
        
        # Verify SQL includes schema clause
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "AND table_schema = 'public'" in sql_called
    
    def test_function_exists(self):
        """Test checking if a function exists."""
        # Setup mock cursor with return value
        self.mock_cursor.fetchone.return_value = (True,)
        
        # Run the method without schema
        result = self.db_manager.function_exists("test_function")
        
        # Verify the result and SQL execution
        assert result is True
        self.mock_cursor.execute.assert_called_once()
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "SELECT EXISTS" in sql_called
        assert "p.proname = 'test_function'" in sql_called
        
        # Reset mocks
        self.mock_cursor.execute.reset_mock()
        
        # Run the method with schema
        result = self.db_manager.function_exists("test_function", schema="public")
        
        # Verify SQL includes schema clause
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "AND n.nspname = 'public'" in sql_called
    
    def test_type_exists(self):
        """Test checking if a type exists."""
        # Setup mock cursor with return value
        self.mock_cursor.fetchone.return_value = (True,)
        
        # Run the method without schema
        result = self.db_manager.type_exists("test_type")
        
        # Verify the result and SQL execution
        assert result is True
        self.mock_cursor.execute.assert_called_once()
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "SELECT EXISTS" in sql_called
        assert "t.typname = 'test_type'" in sql_called
        
        # Reset mocks
        self.mock_cursor.execute.reset_mock()
        
        # Run the method with schema
        result = self.db_manager.type_exists("test_type", schema="public")
        
        # Verify SQL includes schema clause
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "AND n.nspname = 'public'" in sql_called
    
    def test_trigger_exists(self):
        """Test checking if a trigger exists."""
        # Setup mock cursor with return value
        self.mock_cursor.fetchone.return_value = (True,)
        
        # Run the method without schema
        result = self.db_manager.trigger_exists("test_trigger", "test_table")
        
        # Verify the result and SQL execution
        assert result is True
        self.mock_cursor.execute.assert_called_once()
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "SELECT EXISTS" in sql_called
        assert "t.tgname = 'test_trigger'" in sql_called
        assert "c.relname = 'test_table'" in sql_called
        
        # Reset mocks
        self.mock_cursor.execute.reset_mock()
        
        # Run the method with schema
        result = self.db_manager.trigger_exists("test_trigger", "test_table", schema="public")
        
        # Verify SQL includes schema clause
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "AND n.nspname = 'public'" in sql_called
    
    def test_policy_exists(self):
        """Test checking if a policy exists."""
        # Setup mock cursor with return value
        self.mock_cursor.fetchone.return_value = (True,)
        
        # Run the method without schema
        result = self.db_manager.policy_exists("test_policy", "test_table")
        
        # Verify the result and SQL execution
        assert result is True
        self.mock_cursor.execute.assert_called_once()
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "SELECT EXISTS" in sql_called
        assert "p.polname = 'test_policy'" in sql_called
        assert "c.relname = 'test_table'" in sql_called
        
        # Reset mocks
        self.mock_cursor.execute.reset_mock()
        
        # Run the method with schema
        result = self.db_manager.policy_exists("test_policy", "test_table", schema="public")
        
        # Verify SQL includes schema clause
        sql_called = self.mock_cursor.execute.call_args[0][0]
        assert "AND n.nspname = 'public'" in sql_called
    
    @patch('psycopg.connect')
    def test_initialize_database(self, mock_connect):
        """Test initializing a database."""
        # Setup mock admin connection with cursor context manager
        mock_admin_conn = MagicMock()
        mock_admin_cursor = MagicMock()
        
        # Setup cursor context manager
        mock_admin_cursor_cm = MagicMock()
        mock_admin_cursor_cm.__enter__.return_value = mock_admin_cursor
        mock_admin_conn.cursor.return_value = mock_admin_cursor_cm
        
        mock_connect.return_value = mock_admin_conn
        
        # Create test config
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2",
            db_schema="public"
        )
        
        # Run the method
        self.db_manager.initialize_database(config)
        
        # Verify admin connection was used to create database
        mock_connect.assert_called_once()
        
        # Verify SQL operations on admin connection
        # The cursor execute should have been called with SQL commands
        assert mock_admin_cursor.execute.call_count >= 3  # At least terminate, drop, and create
        exec_calls = [call[0][0] for call in mock_admin_cursor.execute.call_args_list]
        
        # Check for expected SQL operations (partial match is fine)
        terminate_calls = [c for c in exec_calls if "pg_terminate_backend" in c]
        assert len(terminate_calls) > 0, "Expected pg_terminate_backend call"
        
        drop_calls = [c for c in exec_calls if "DROP DATABASE IF EXISTS test_db" in c]
        assert len(drop_calls) > 0, "Expected DROP DATABASE call"
        
        create_calls = [c for c in exec_calls if "CREATE DATABASE test_db" in c]
        assert len(create_calls) > 0, "Expected CREATE DATABASE call"
        
        # Verify extensions were created on regular connection
        assert self.mock_cursor.execute.call_count >= 3  # schema and at least 2 extensions
        regular_exec_calls = [call[0][0] for call in self.mock_cursor.execute.call_args_list]
        
        schema_calls = [c for c in regular_exec_calls if "CREATE SCHEMA IF NOT EXISTS public" in c]
        assert len(schema_calls) > 0, "Expected CREATE SCHEMA call"
        
        extension_calls = [c for c in regular_exec_calls if "CREATE EXTENSION IF NOT EXISTS" in c]
        assert len(extension_calls) >= 3, "Expected at least 3 CREATE EXTENSION calls"
    
    @patch('psycopg.connect')
    def test_drop_database(self, mock_connect):
        """Test dropping a database."""
        # Setup mock admin connection with cursor context manager
        mock_admin_conn = MagicMock()
        mock_admin_cursor = MagicMock()
        
        # Setup cursor context manager
        mock_admin_cursor_cm = MagicMock()
        mock_admin_cursor_cm.__enter__.return_value = mock_admin_cursor
        mock_admin_conn.cursor.return_value = mock_admin_cursor_cm
        
        mock_connect.return_value = mock_admin_conn
        
        # Create test config
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2",
            db_schema="public"
        )
        
        # Run the method
        self.db_manager.drop_database(config)
        
        # Verify admin connection was used to drop database
        mock_connect.assert_called_once()
        
        # Verify SQL operations on admin connection
        # The cursor execute should have been called with SQL commands
        assert mock_admin_cursor.execute.call_count >= 2  # At least terminate and drop
        exec_calls = [call[0][0] for call in mock_admin_cursor.execute.call_args_list]
        
        # Check for expected SQL operations (partial match is fine)
        terminate_calls = [c for c in exec_calls if "pg_terminate_backend" in c]
        assert len(terminate_calls) > 0, "Expected pg_terminate_backend call"
        
        drop_calls = [c for c in exec_calls if "DROP DATABASE IF EXISTS test_db" in c]
        assert len(drop_calls) > 0, "Expected DROP DATABASE call"
    
    def test_create_user(self):
        """Test creating a database user."""
        # Run the method
        self.db_manager.create_user("test_user", "test_password", is_superuser=False)
        
        # Verify SQL execution
        self.mock_cursor.execute.assert_called_once()
        execution_sql = self.mock_cursor.execute.call_args[0][0]
        assert "CREATE USER test_user" in execution_sql
        assert "NOSUPERUSER" in execution_sql
        assert "PASSWORD 'test_password'" in execution_sql
        
        # Reset mock
        self.mock_cursor.execute.reset_mock()
        
        # Test with superuser=True
        self.db_manager.create_user("super_user", "super_password", is_superuser=True)
        
        # Verify SQL includes SUPERUSER
        execution_sql = self.mock_cursor.execute.call_args[0][0]
        assert "CREATE USER super_user" in execution_sql
        assert "SUPERUSER" in execution_sql
    
    def test_create_role(self):
        """Test creating a database role."""
        # Run the method without granted roles
        self.db_manager.create_role("test_role")
        
        # Verify SQL execution
        self.mock_cursor.execute.assert_called_once()
        execution_sql = self.mock_cursor.execute.call_args[0][0]
        assert "CREATE ROLE test_role" in execution_sql
        
        # Reset mock
        self.mock_cursor.execute.reset_mock()
        
        # Test with granted roles
        self.db_manager.create_role("child_role", granted_roles=["parent_role1", "parent_role2"])
        
        # First call should create the role
        assert "CREATE ROLE child_role" in self.mock_cursor.execute.call_args_list[0][0][0]
        # Subsequent calls should grant roles
        assert self.mock_cursor.execute.call_count >= 2  # At least one CREATE + one GRANT
        grant_calls = [call for call in self.mock_cursor.execute.call_args_list 
                     if "GRANT " in call[0][0]]
        assert len(grant_calls) == 2  # Two GRANT calls
    
    def test_grant_privileges(self):
        """Test granting privileges to a role."""
        # Run the method without schema
        self.db_manager.grant_privileges(
            privileges=["SELECT", "INSERT"], 
            on_object="test_table", 
            to_role="test_role"
        )
        
        # Verify SQL execution
        self.mock_cursor.execute.assert_called_once()
        execution_sql = self.mock_cursor.execute.call_args[0][0]
        assert "GRANT SELECT, INSERT ON TABLE test_table TO test_role" in execution_sql
        
        # Reset mock
        self.mock_cursor.execute.reset_mock()
        
        # Test with schema and different object type
        self.db_manager.grant_privileges(
            privileges=["USAGE"], 
            on_object="test_schema", 
            to_role="test_role",
            object_type="SCHEMA",
            schema="public"
        )
        
        # Verify SQL execution with schema
        self.mock_cursor.execute.assert_called_once()
        execution_sql = self.mock_cursor.execute.call_args[0][0]
        assert "GRANT USAGE ON SCHEMA public.test_schema TO test_role" in execution_sql