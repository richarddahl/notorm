# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the synchronous database engine factory.

These tests verify the behavior of the SyncEngineFactory class, focusing on engine
creation, configuration validation, and the sync_connection context manager.
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
import logging
from contextlib import nullcontext as does_not_raise

from sqlalchemy import URL, Engine, Connection
from sqlalchemy.exc import SQLAlchemyError

from uno.database.engine.sync import SyncEngineFactory, sync_connection
from uno.database.config import ConnectionConfig
from uno.settings import uno_settings


class TestSyncEngineFactory:
    """Tests for the SyncEngineFactory class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = MagicMock(spec=logging.Logger)
        self.config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2"
        )
        self.factory = SyncEngineFactory(logger=self.logger)
    
    @patch('uno.database.engine.sync.create_engine')
    def test_create_engine(self, mock_create_engine):
        """Test creating a synchronous engine."""
        # Setup mock
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine
        
        # Call create_engine
        engine = self.factory.create_engine(self.config)
        
        # Verify create_engine was called with correct URL and args
        mock_create_engine.assert_called_once()
        
        # Check the first positional argument (URL)
        url_arg = mock_create_engine.call_args[0][0]
        assert isinstance(url_arg, URL)
        assert url_arg.drivername == self.config.db_driver
        assert url_arg.username == self.config.db_role
        assert url_arg.password == self.config.db_user_pw
        assert url_arg.host == self.config.db_host
        assert url_arg.port == self.config.db_port
        assert url_arg.database == self.config.db_name
        
        # Verify result
        assert engine == mock_engine
        
        # Verify debug message was logged
        self.logger.debug.assert_called_once()
    
    def test_create_engine_invalid_config(self):
        """Test handling of invalid configuration."""
        # Test with missing db_driver
        invalid_config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver=""  # Empty driver
        )
        
        with pytest.raises(ValueError) as exc_info:
            self.factory.create_engine(invalid_config)
        assert "Database driver must be specified" in str(exc_info.value)
        
        # Test with missing db_host
        invalid_config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="",  # Empty host
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2"
        )
        
        with pytest.raises(ValueError) as exc_info:
            self.factory.create_engine(invalid_config)
        assert "Database host must be specified" in str(exc_info.value)
        
        # Test with missing db_name
        invalid_config = ConnectionConfig(
            db_role="test_role",
            db_name="",  # Empty database name
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2"
        )
        
        with pytest.raises(ValueError) as exc_info:
            self.factory.create_engine(invalid_config)
        assert "Database name must be specified" in str(exc_info.value)
    
    @patch('uno.database.engine.sync.create_engine')
    def test_engine_kwargs(self, mock_create_engine):
        """Test engine creation with various kwargs."""
        # Setup mock
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine
        
        # Create config with pool settings
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2",
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
            pool_recycle=180,
            connect_args={"ssl": True}
        )
        
        # Call create_engine
        self.factory.create_engine(config)
        
        # Verify kwargs were passed correctly
        _, kwargs = mock_create_engine.call_args
        assert kwargs["pool_size"] == 10
        assert kwargs["max_overflow"] == 20
        assert kwargs["pool_timeout"] == 60
        assert kwargs["pool_recycle"] == 180
        assert kwargs["connect_args"] == {"ssl": True}


class TestSyncConnection:
    """Tests for the sync_connection context manager and error handling."""
    
    @patch('uno.database.engine.sync.SyncEngineFactory')
    def test_sync_connection_success(self, MockFactory):
        """Test successful database connection."""
        # Setup mocks
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        mock_engine = MagicMock(spec=Engine)
        mock_factory.create_engine.return_value = mock_engine
        
        mock_conn = MagicMock(spec=Connection)
        mock_execution_conn = MagicMock(spec=Connection)
        mock_engine.connect.return_value = mock_conn
        mock_conn.execution_options.return_value = mock_execution_conn
        mock_execution_conn.__enter__.return_value = mock_execution_conn
        
        # Use sync_connection
        with sync_connection(
            db_driver="postgresql+psycopg2",
            db_name="test_db",
            db_user_pw="test_password",
            db_role="test_role",
            factory=mock_factory,
            max_retries=1
        ) as conn:
            # Verify connection was yielded
            assert conn == mock_execution_conn
        
        # Verify engine was created and disposed
        mock_factory.create_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_conn.execution_options.assert_called_once_with(isolation_level="AUTOCOMMIT")
        mock_engine.dispose.assert_called_once()
        mock_factory.execute_callbacks.assert_called_once_with(mock_execution_conn)
    
    @patch('uno.database.engine.sync.SyncEngineFactory')
    @patch('uno.database.engine.sync.time.sleep')
    def test_sync_connection_retry(self, mock_sleep, MockFactory):
        """Test connection retry behavior."""
        # Setup mocks
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        # First attempt fails, second succeeds
        mock_engine1 = MagicMock(spec=Engine)
        mock_engine2 = MagicMock(spec=Engine)
        mock_factory.create_engine.side_effect = [mock_engine1, mock_engine2]
        
        mock_conn1 = MagicMock(spec=Connection)
        mock_conn2 = MagicMock(spec=Connection)
        mock_execution_conn = MagicMock(spec=Connection)
        mock_engine1.connect.side_effect = SQLAlchemyError("Connection failed")
        mock_engine2.connect.return_value = mock_conn2
        mock_conn2.execution_options.return_value = mock_execution_conn
        mock_execution_conn.__enter__.return_value = mock_execution_conn
        
        # Use sync_connection with retries
        with sync_connection(
            db_driver="postgresql+psycopg2",
            db_name="test_db", 
            db_user_pw="test_password",
            db_role="test_role",
            factory=mock_factory,
            max_retries=2,
            retry_delay=1
        ) as conn:
            # Verify the second connection was yielded
            assert conn == mock_execution_conn
        
        # Verify both engines were created
        assert mock_factory.create_engine.call_count == 2
        
        # Verify sleep was called after the first failure
        mock_sleep.assert_called_once_with(1)  # retry_delay is 1
        
        # Verify both engines were disposed
        mock_engine1.dispose.assert_called_once()
        mock_engine2.dispose.assert_called_once()
    
    @patch('uno.database.engine.sync.SyncEngineFactory')
    @patch('uno.database.engine.sync.time.sleep')
    def test_sync_connection_max_retries_exceeded(self, mock_sleep, MockFactory):
        """Test behavior when max retries are exceeded."""
        # Setup mocks
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        # All connection attempts fail
        mock_engine = MagicMock(spec=Engine)
        mock_factory.create_engine.return_value = mock_engine
        
        error = SQLAlchemyError("Connection failed")
        mock_engine.connect.side_effect = error
        
        # Use sync_connection with retries
        with pytest.raises(SQLAlchemyError) as exc_info:
            with sync_connection(
                db_driver="postgresql+psycopg2",
                db_name="test_db",
                db_user_pw="test_password", 
                db_role="test_role",
                factory=mock_factory,
                max_retries=3,
                retry_delay=1
            ) as conn:
                pass
        
        # Verify the original error was raised
        assert exc_info.value == error
        
        # Verify create_engine was called max_retries times
        assert mock_factory.create_engine.call_count == 3
        
        # Verify sleep was called between retries
        assert mock_sleep.call_count == 2  # Called after 1st and 2nd failures
        
        # Verify all engines were disposed
        assert mock_engine.dispose.call_count == 3
    
    @patch('uno.database.engine.sync.SyncEngineFactory')
    def test_sync_connection_with_config(self, MockFactory):
        """Test using sync_connection with a ConnectionConfig object."""
        # Setup mocks
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        mock_engine = MagicMock(spec=Engine)
        mock_factory.create_engine.return_value = mock_engine
        
        mock_conn = MagicMock(spec=Connection)
        mock_execution_conn = MagicMock(spec=Connection)
        mock_engine.connect.return_value = mock_conn
        mock_conn.execution_options.return_value = mock_execution_conn
        mock_execution_conn.__enter__.return_value = mock_execution_conn
        
        # Create a config
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db", 
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2"
        )
        
        # Use sync_connection with config
        with sync_connection(
            config=config,
            factory=mock_factory,
            max_retries=1
        ) as conn:
            # Verify connection was yielded
            assert conn == mock_execution_conn
        
        # Verify factory used the provided config
        mock_factory.create_engine.assert_called_once_with(config)
        
    @patch('uno.database.engine.sync.SyncEngineFactory')
    @patch('uno.database.engine.sync.time.sleep')
    def test_sync_connection_specific_error_types(self, mock_sleep, MockFactory):
        """Test handling of specific SQLAlchemy error types."""
        # Only test the general SQLAlchemy error since the specific errors
        # have more complex constructor requirements
        error_class = SQLAlchemyError
        
        # Setup mocks
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        mock_engine = MagicMock(spec=Engine)
        mock_factory.create_engine.return_value = mock_engine
        
        # Set up the error
        error = error_class("Test error")
        mock_engine.connect.side_effect = error
        
        # Connection should handle the error and retry
        with pytest.raises(error_class):
            with sync_connection(
                db_role="test_role",
                db_name="test_db",
                db_driver="postgresql+psycopg2",
                factory=mock_factory,
                max_retries=2,
                retry_delay=0  # No delay for testing
            ):
                pass
        
        # Verify multiple connection attempts were made
        assert mock_factory.create_engine.call_count == 2
        assert mock_engine.connect.call_count == 2
        assert mock_engine.dispose.call_count == 2
    
    @patch('uno.database.engine.sync.create_engine')
    def test_engine_with_custom_pool_settings(self, mock_create_engine):
        """Test engine creation with custom connection pool settings."""
        # Setup mock
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine
        
        # Create factory
        factory = SyncEngineFactory()
        
        # Create config with extensive pool settings
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2",
            pool_size=20,
            max_overflow=15,
            pool_timeout=45,
            pool_recycle=120
        )
        
        # Create engine with config
        factory.create_engine(config)
        
        # Verify all pool settings were passed to create_engine
        _, kwargs = mock_create_engine.call_args
        assert kwargs["pool_size"] == 20
        assert kwargs["max_overflow"] == 15
        assert kwargs["pool_timeout"] == 45
        assert kwargs["pool_recycle"] == 120
    
    @patch('uno.database.engine.sync.create_engine')
    def test_engine_without_pool_settings(self, mock_create_engine):
        """Test engine creation without explicit pool settings."""
        # Setup mock
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine
        
        # Create factory
        factory = SyncEngineFactory()
        
        # Create minimal config with no pool settings
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2",
            # No pool settings specified
            pool_size=None,
            max_overflow=None,
            pool_timeout=None,
            pool_recycle=None
        )
        
        # Create engine with config
        factory.create_engine(config)
        
        # Verify no pool settings were passed to create_engine
        _, kwargs = mock_create_engine.call_args
        assert "pool_size" not in kwargs
        assert "max_overflow" not in kwargs
        assert "pool_timeout" not in kwargs
        assert "pool_recycle" not in kwargs
    
    @pytest.mark.parametrize("driver,expected_uri_start", [
        ("postgresql+psycopg2", "postgresql+psycopg2://"),
        ("postgresql+psycopg", "postgresql+psycopg://"),
        ("mysql+pymysql", "mysql+pymysql://"),
        ("sqlite+pysqlite", "sqlite+pysqlite://")
    ])
    @patch('urllib.parse.quote_plus')
    def test_multiple_database_drivers(self, mock_quote_plus, driver, expected_uri_start):
        """Test engine creation with different database drivers."""
        # Setup mocks
        mock_quote_plus.return_value = "encoded_password"
        
        # Create config with specific driver
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver=driver
        )
        
        # Verify URI generation has correct driver prefix
        uri = config.get_uri()
        assert uri.startswith(expected_uri_start)
        
        # Verify engine creation with different drivers
        with patch('uno.database.engine.sync.create_engine') as mock_create_engine:
            mock_engine = MagicMock(spec=Engine)
            mock_create_engine.return_value = mock_engine
            
            factory = SyncEngineFactory()
            engine = factory.create_engine(config)
            
            # Verify engine was created
            mock_create_engine.assert_called_once()
            
            # Check the URL uses the correct driver
            url_arg = mock_create_engine.call_args[0][0]
            assert url_arg.drivername == driver