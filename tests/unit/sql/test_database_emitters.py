# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the SQL database emitters module.

These tests verify the functionality of the database-level SQL emitters, ensuring
they correctly generate SQL statements for database operations.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
from typing import List, Dict, Any

from pydantic import BaseModel, Field
from uno.core.errors import UnoError

from uno.sql.emitters.database import (
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    SetRole,
    DropDatabaseAndRoles,
)
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.database.config import ConnectionConfig


class MockSettings(BaseModel):
    """Mock settings for testing."""
    DB_NAME: str = "test_db"
    DB_SCHEMA: str = "test_schema"
    DB_USER_PW: str = "test_password"
    UNO_ROOT: str = "/test/path"
    DB_SYNC_DRIVER: str = "psycopg2"
    DB_ASYNC_DRIVER: str = "asyncpg"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432


@pytest.fixture
def connection_config():
    """Create a connection config for testing."""
    return ConnectionConfig(
        db_name="test_db",
        db_user_pw="test_password",
        db_driver="psycopg2"
    )


class TestCreateRolesAndDatabase:
    """Tests for the CreateRolesAndDatabase emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = CreateRolesAndDatabase(config=self.config)
    
    def test_generate_sql(self):
        """Test SQL generation for roles and database creation."""
        statements = self.emitter.generate_sql()
        
        # Verify number of statements
        assert len(statements) == 2
        
        # Verify statement types
        assert statements[0].type == SQLStatementType.ROLE
        assert statements[0].name == "create_roles"
        assert statements[1].type == SQLStatementType.DATABASE
        assert statements[1].name == "create_database"
        
        # Check SQL content for roles
        role_sql = statements[0].sql
        assert "CREATE ROLE test_db_base_role" in role_sql
        assert "CREATE ROLE test_db_login NOINHERIT LOGIN PASSWORD 'test_password'" in role_sql
        assert "CREATE ROLE test_db_reader INHERIT IN ROLE test_db_base_role" in role_sql
        assert "CREATE ROLE test_db_writer INHERIT IN ROLE test_db_base_role" in role_sql
        assert "CREATE ROLE test_db_admin INHERIT IN ROLE test_db_base_role" in role_sql
        assert "GRANT test_db_reader, test_db_writer, test_db_admin TO test_db_login" in role_sql
        
        # Check SQL content for database
        db_sql = statements[1].sql
        assert "CREATE DATABASE test_db WITH OWNER = test_db_admin" in db_sql


class TestCreateSchemasAndExtensions:
    """Tests for the CreateSchemasAndExtensions emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = CreateSchemasAndExtensions(config=self.config)
    
    def test_generate_sql(self):
        """Test SQL generation for schemas and extensions."""
        statements = self.emitter.generate_sql()
        
        # Verify number of statements
        assert len(statements) == 2
        
        # Verify statement types
        assert statements[0].type == SQLStatementType.SCHEMA
        assert statements[0].name == "create_schemas"
        assert statements[1].type == SQLStatementType.EXTENSION
        assert statements[1].name == "create_extensions"
        
        # Check SQL content for schemas
        schema_sql = statements[0].sql
        assert "CREATE SCHEMA IF NOT EXISTS test_schema AUTHORIZATION test_db_admin" in schema_sql
        
        # Check SQL content for extensions
        extensions_sql = statements[1].sql
        assert "SET search_path TO test_schema" in extensions_sql
        assert "CREATE EXTENSION IF NOT EXISTS btree_gist" in extensions_sql
        assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in extensions_sql
        assert "CREATE EXTENSION IF NOT EXISTS pgjwt" in extensions_sql
        assert "CREATE EXTENSION IF NOT EXISTS age" in extensions_sql
        assert "SELECT * FROM ag_catalog.create_graph('graph')" in extensions_sql
        assert "ALTER TABLE graph._ag_label_edge OWNER TO test_db_admin" in extensions_sql


class TestRevokeAndGrantPrivilegesAndSetSearchPaths:
    """Tests for the RevokeAndGrantPrivilegesAndSetSearchPaths emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = RevokeAndGrantPrivilegesAndSetSearchPaths(config=self.config)
    
    def test_generate_sql(self):
        """Test SQL generation for privileges and search paths."""
        statements = self.emitter.generate_sql()
        
        # Verify number of statements
        assert len(statements) == 3
        
        # Verify statement types
        assert statements[0].type == SQLStatementType.GRANT
        assert statements[0].name == "revoke_privileges"
        assert statements[1].type == SQLStatementType.GRANT
        assert statements[1].name == "set_search_paths"
        assert statements[2].type == SQLStatementType.GRANT
        assert statements[2].name == "grant_schema_privileges"
        
        # Check SQL content for revoke privileges
        revoke_sql = statements[0].sql
        assert "REVOKE ALL ON SCHEMA audit, graph, ag_catalog, test_schema" in revoke_sql
        assert "REVOKE ALL ON ALL TABLES IN SCHEMA audit, graph, ag_catalog, test_schema" in revoke_sql
        assert "REVOKE CONNECT ON DATABASE test_db FROM public" in revoke_sql
        
        # Check SQL content for search paths
        search_paths_sql = statements[1].sql
        assert "ALTER ROLE test_db_base_role SET search_path TO test_schema, audit, graph, ag_catalog" in search_paths_sql
        assert "ALTER ROLE test_db_admin SET search_path TO test_schema, audit, graph, ag_catalog" in search_paths_sql
        
        # Check SQL content for grant privileges
        grant_sql = statements[2].sql
        assert "ALTER SCHEMA test_schema OWNER TO test_db_admin" in grant_sql
        assert "GRANT CONNECT ON DATABASE test_db TO test_db_login" in grant_sql
        assert "GRANT USAGE ON SCHEMA audit, graph, ag_catalog, test_schema" in grant_sql
        assert "GRANT CREATE ON SCHEMA audit, graph, test_schema TO test_db_admin" in grant_sql
        assert "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit, graph, ag_catalog, test_schema" in grant_sql


class TestCreatePGULID:
    """Tests for the CreatePGULID emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = CreatePGULID(config=self.config)
    
    @patch("builtins.open", new_callable=mock_open, read_data="CREATE FUNCTION {schema_name}.pgulid() RETURNS TEXT...")
    def test_generate_sql(self, mock_file):
        """Test SQL generation for PGULID function."""
        statements = self.emitter.generate_sql()
        
        # Verify file was opened with correct path
        mock_file.assert_called_once_with("/test/path/uno/sql/pgulid.sql", "r")
        
        # Verify number of statements
        assert len(statements) == 1
        
        # Verify statement type
        assert statements[0].type == SQLStatementType.FUNCTION
        assert statements[0].name == "create_pgulid"
        
        # Check SQL content has schema name substitution
        pgulid_sql = statements[0].sql
        assert "CREATE FUNCTION test_schema.pgulid() RETURNS TEXT" in pgulid_sql
    
    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_generate_sql_file_not_found(self, mock_file):
        """Test SQL generation with missing PGULID file."""
        # Expect UnoError when file is not found
        with pytest.raises(UnoError) as exc_info:
            self.emitter.generate_sql()
        
        # Verify the error
        assert "Failed to read PGULID SQL file" in str(exc_info.value)
        assert exc_info.value.error_code == "SQL_FILE_READ_ERROR"


class TestCreateTokenSecret:
    """Tests for the CreateTokenSecret emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = CreateTokenSecret(config=self.config)
    
    def test_generate_sql(self):
        """Test SQL generation for token secret table and trigger."""
        statements = self.emitter.generate_sql()
        
        # Verify number of statements
        assert len(statements) == 1
        
        # Verify statement type
        assert statements[0].type == SQLStatementType.TABLE
        assert statements[0].name == "create_token_secret_table"
        
        # Check SQL content
        token_sql = statements[0].sql
        assert "SET ROLE test_db_admin" in token_sql
        assert "DROP TABLE IF EXISTS audit.token_secret CASCADE" in token_sql
        assert "CREATE TABLE audit.token_secret" in token_sql
        assert "token_secret TEXT PRIMARY KEY" in token_sql
        assert "CREATE OR REPLACE FUNCTION audit.set_token_secret()" in token_sql
        assert "CREATE TRIGGER set_token_secret_trigger" in token_sql
        assert "EXECUTE FUNCTION audit.set_token_secret()" in token_sql


class TestGrantPrivileges:
    """Tests for the GrantPrivileges emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = GrantPrivileges(config=self.config)
    
    def test_generate_sql(self):
        """Test SQL generation for granting privileges."""
        statements = self.emitter.generate_sql()
        
        # Verify number of statements
        assert len(statements) == 1
        
        # Verify statement type
        assert statements[0].type == SQLStatementType.GRANT
        assert statements[0].name == "grant_schema_privileges"
        
        # Check SQL content
        grant_sql = statements[0].sql
        assert "SET ROLE test_db_admin" in grant_sql
        assert "GRANT SELECT ON ALL TABLES IN SCHEMA audit, graph, ag_catalog, test_schema" in grant_sql
        assert "TO test_db_reader, test_db_writer" in grant_sql
        assert "GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON ALL TABLES" in grant_sql
        assert "GRANT ALL ON ALL TABLES IN SCHEMA audit, graph, ag_catalog TO test_db_admin" in grant_sql
        assert "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA" in grant_sql


class TestSetRole:
    """Tests for the SetRole emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = SetRole(config=self.config)
    
    def test_generate_sql(self):
        """Test SQL generation for set_role function."""
        statements = self.emitter.generate_sql()
        
        # Verify number of statements
        assert len(statements) == 2
        
        # Verify statement types
        assert statements[0].type == SQLStatementType.FUNCTION
        assert statements[0].name == "create_set_role"
        assert statements[1].type == SQLStatementType.GRANT
        assert statements[1].name == "set_role_permissions"
        
        # Check SQL content for set_role function
        function_sql = statements[0].sql
        assert "SET ROLE test_db_admin" in function_sql
        assert "CREATE OR REPLACE FUNCTION set_role(role_name TEXT)" in function_sql
        assert "RETURNS VOID" in function_sql
        assert "LANGUAGE plpgsql" in function_sql
        assert "current_database()" in function_sql
        assert "CONCAT(db_name, '_', role_name)" in function_sql
        
        # Check SQL content for set_role permissions
        permissions_sql = statements[1].sql
        assert "REVOKE EXECUTE ON FUNCTION set_role(TEXT) FROM public" in permissions_sql
        assert "GRANT EXECUTE ON FUNCTION set_role(TEXT)" in permissions_sql
        assert "TO test_db_login, test_db_reader, test_db_writer" in permissions_sql


class TestDropDatabaseAndRoles:
    """Tests for the DropDatabaseAndRoles emitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockSettings()
        self.emitter = DropDatabaseAndRoles(config=self.config)
    
    def test_generate_sql(self):
        """Test SQL generation for dropping database and roles."""
        statements = self.emitter.generate_sql()
        
        # Verify number of statements
        assert len(statements) == 3
        
        # Verify statement types
        assert statements[0].type == SQLStatementType.FUNCTION
        assert statements[0].name == "terminate_connections"
        assert statements[1].type == SQLStatementType.DATABASE
        assert statements[1].name == "drop_database"
        assert statements[2].type == SQLStatementType.ROLE
        assert statements[2].name == "drop_roles"
        
        # Check SQL content for terminate connections
        terminate_sql = statements[0].sql
        assert "SELECT pg_terminate_backend(pid)" in terminate_sql
        assert "FROM pg_stat_activity" in terminate_sql
        assert "WHERE datname = 'test_db'" in terminate_sql
        
        # Check SQL content for drop database
        drop_db_sql = statements[1].sql
        assert "DROP DATABASE IF EXISTS test_db" in drop_db_sql
        
        # Check SQL content for drop roles
        drop_roles_sql = statements[2].sql
        assert "DROP ROLE IF EXISTS test_db_admin" in drop_roles_sql
        assert "DROP ROLE IF EXISTS test_db_writer" in drop_roles_sql
        assert "DROP ROLE IF EXISTS test_db_reader" in drop_roles_sql
        assert "DROP ROLE IF EXISTS test_db_login" in drop_roles_sql
        assert "DROP ROLE IF EXISTS test_db_base_role" in drop_roles_sql