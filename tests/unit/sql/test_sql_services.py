# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for SQL services.

These tests verify the functionality of the SQL emitter factory and
execution services.
"""

import logging
import pytest
from unittest.mock import MagicMock, patch

from uno.sql.services import SQLEmitterFactoryService, SQLExecutionService
from uno.dependencies.interfaces import UnoConfigProtocol, SQLEmitterFactoryProtocol
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.database.config import ConnectionConfig


class MockEmitter(SQLEmitter):
    """Mock SQL emitter for testing."""
    
    def generate_sql(self):
        """Generate SQL statements."""
        return [
            SQLStatement(
                name="test_statement",
                type=SQLStatementType.FUNCTION,
                sql="CREATE FUNCTION test_func() RETURNS void AS $$ BEGIN END; $$ LANGUAGE plpgsql;"
            )
        ]


class MockConfig(UnoConfigProtocol):
    """Mock configuration for testing."""
    
    def get_value(self, key, default=None):
        """Get a configuration value."""
        values = {
            "DB_NAME": "test_db",
            "DB_ROLE": "test_role",
            "DB_USER_PW": "test_password",
            "DB_HOST": "localhost",
            "DB_PORT": 5432,
            "DB_SYNC_DRIVER": "postgresql+psycopg2",
            "DB_SCHEMA": "public"
        }
        return values.get(key, default)
    
    def all(self):
        """Get all configuration values."""
        return {
            "DB_NAME": "test_db",
            "DB_ROLE": "test_role",
            "DB_USER_PW": "test_password",
            "DB_HOST": "localhost",
            "DB_PORT": 5432,
            "DB_SYNC_DRIVER": "postgresql+psycopg2",
            "DB_SCHEMA": "public"
        }


class TestSQLEmitterFactoryService:
    """Tests for SQLEmitterFactoryService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = MagicMock(spec=logging.Logger)
        self.config = MockConfig()
        self.factory = SQLEmitterFactoryService(
            config=self.config,
            logger=self.logger
        )
    
    def test_initialization(self):
        """Test initialization of the factory."""
        assert self.factory.config == self.config
        assert self.factory.logger == self.logger
        assert self.factory._emitter_registry == {}
    
    def test_register_emitter(self):
        """Test registering an emitter."""
        # Register an emitter
        self.factory.register_emitter("test", MockEmitter)
        
        # Verify it was registered
        assert "test" in self.factory._emitter_registry
        assert self.factory._emitter_registry["test"] == MockEmitter
    
    def test_get_emitter(self):
        """Test getting an emitter."""
        # Register an emitter
        self.factory.register_emitter("test", MockEmitter)
        
        # Get the emitter
        emitter = self.factory.get_emitter("test")
        
        # Verify the emitter
        assert isinstance(emitter, MockEmitter)
        assert emitter.logger == self.logger
        
        # Test with connection config
        conn_config = ConnectionConfig(
            db_name="custom_db",
            db_role="custom_role",
            db_user_pw="custom_password",
            db_host="custom_host",
            db_port=5433,
            db_driver="postgresql+psycopg2",
            db_schema="custom_schema"
        )
        
        emitter = self.factory.get_emitter("test", connection_config=conn_config)
        assert emitter.connection_config == conn_config
    
    def test_get_emitter_not_registered(self):
        """Test getting an unregistered emitter."""
        # Try to get an unregistered emitter
        with pytest.raises(ValueError):
            self.factory.get_emitter("not_registered")
    
    def test_create_emitter_instance(self):
        """Test creating an emitter instance."""
        # Create an emitter instance
        emitter = self.factory.create_emitter_instance(MockEmitter)
        
        # Verify the emitter
        assert isinstance(emitter, MockEmitter)
        assert emitter.logger == self.logger
    
    def test_register_core_emitters(self):
        """Test registering core emitters."""
        # Call register_core_emitters
        with patch('uno.sql.services.SQLEmitterFactoryService.register_emitter') as mock_register:
            self.factory.register_core_emitters()
            
            # Verify calls to register_emitter
            assert mock_register.call_count >= 5
    
    def test_protocol_compliance(self):
        """Test that the service complies with the protocol."""
        # Verify that the service implements the protocol
        service: SQLEmitterFactoryProtocol = self.factory
        
        # Just checking that these methods exist on the service
        assert hasattr(service, 'register_emitter')
        assert hasattr(service, 'get_emitter')
        assert hasattr(service, 'create_emitter_instance')
        assert hasattr(service, 'register_core_emitters')


class TestSQLExecutionService:
    """Tests for SQLExecutionService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = MagicMock(spec=logging.Logger)
        self.service = SQLExecutionService(logger=self.logger)
    
    def test_initialization(self):
        """Test initialization of the service."""
        assert self.service.logger == self.logger
    
    @patch('uno.dependencies.database.get_db_manager')
    def test_execute_ddl(self, mock_get_db_manager):
        """Test executing DDL."""
        # Setup mock db_manager
        mock_db_manager = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        
        # Execute DDL
        ddl = "CREATE TABLE test (id INT);"
        self.service.execute_ddl(ddl)
        
        # Verify db_manager.execute_ddl was called
        mock_db_manager.execute_ddl.assert_called_once_with(ddl)
    
    @patch('uno.dependencies.database.get_db_manager')
    def test_execute_script(self, mock_get_db_manager):
        """Test executing a script."""
        # Setup mock db_manager
        mock_db_manager = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        
        # Execute script
        script = "CREATE TABLE test1 (id INT);\nCREATE TABLE test2 (id INT);"
        self.service.execute_script(script)
        
        # Verify db_manager.execute_script was called
        mock_db_manager.execute_script.assert_called_once_with(script)
    
    @patch('uno.dependencies.database.get_db_manager')
    def test_execute_emitter(self, mock_get_db_manager):
        """Test executing an emitter."""
        # Setup mock db_manager
        mock_db_manager = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        
        # Create a mock emitter
        mock_emitter = MockEmitter()
        
        # Execute emitter
        self.service.execute_emitter(mock_emitter)
        
        # Verify db_manager.execute_from_emitter was called
        mock_db_manager.execute_from_emitter.assert_called_once_with(mock_emitter)
    
    @patch('uno.dependencies.database.get_db_manager')
    def test_execute_emitter_dry_run(self, mock_get_db_manager):
        """Test executing an emitter in dry run mode."""
        # Setup mock db_manager
        mock_db_manager = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        
        # Create a mock emitter with known output
        mock_emitter = MockEmitter()
        expected_statements = mock_emitter.generate_sql()
        
        # Execute emitter in dry run mode
        statements = self.service.execute_emitter(mock_emitter, dry_run=True)
        
        # Verify db_manager.execute_from_emitter was not called
        mock_db_manager.execute_from_emitter.assert_not_called()
        
        # Verify the returned statements
        assert statements == expected_statements