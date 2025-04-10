# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the database configuration.

These tests verify the behavior of the ConnectionConfig class, focusing on
initialization, validation, and URI construction.
"""

import pytest
from unittest.mock import patch

from uno.database.config import ConnectionConfig
from uno.settings import uno_settings


class TestConnectionConfig:
    """Tests for the ConnectionConfig class and edge cases."""
    
    def test_initialization_with_defaults(self):
        """Test initialization with defaults from settings."""
        # Create config with minimal parameters
        config = ConnectionConfig()
        
        # Verify defaults from settings were applied
        assert config.db_role == f"{uno_settings.DB_NAME}_login"
        assert config.db_name == uno_settings.DB_NAME
        assert config.db_user_pw == uno_settings.DB_USER_PW
        assert config.db_host == uno_settings.DB_HOST
        assert config.db_port == uno_settings.DB_PORT
        assert config.db_driver == uno_settings.DB_ASYNC_DRIVER
        assert config.db_schema == uno_settings.DB_SCHEMA
        
        # Verify default pool settings
        assert config.pool_size == 5
        assert config.max_overflow == 0
        assert config.pool_timeout == 30
        assert config.pool_recycle == 90
        assert config.connect_args is None
    
    def test_initialization_with_custom_values(self):
        """Test initialization with custom values."""
        # Create config with custom parameters
        config = ConnectionConfig(
            db_role="custom_role",
            db_name="custom_db",
            db_user_pw="custom_password",
            db_host="custom.host",
            db_port=1234,
            db_driver="custom_driver",
            db_schema="custom_schema",
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
            pool_recycle=180,
            connect_args={"ssl": True}
        )
        
        # Verify custom values were applied
        assert config.db_role == "custom_role"
        assert config.db_name == "custom_db"
        assert config.db_user_pw == "custom_password"
        assert config.db_host == "custom.host"
        assert config.db_port == 1234
        assert config.db_driver == "custom_driver"
        assert config.db_schema == "custom_schema"
        
        # Verify custom pool settings
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 60
        assert config.pool_recycle == 180
        assert config.connect_args == {"ssl": True}
    
    def test_immutability(self):
        """Test that ConnectionConfig is immutable."""
        config = ConnectionConfig()
        
        # Attempt to modify a field
        with pytest.raises(Exception) as exc_info:
            config.db_name = "new_db_name"
        
        # Verify error about immutability
        assert "frozen" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower()
    
    @patch('urllib.parse.quote_plus')
    def test_get_uri_postgresql(self, mock_quote_plus):
        """Test getting a PostgreSQL URI."""
        # Setup mock for password encoding
        mock_quote_plus.return_value = "encoded_password"
        
        # Create config for PostgreSQL
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test@password",
            db_driver="postgresql+psycopg2"
        )
        
        # Get URI
        uri = config.get_uri()
        
        # Verify password was encoded
        mock_quote_plus.assert_called_once_with("test@password")
        
        # Verify URI format
        assert uri == "postgresql+psycopg2://test_role:encoded_password@localhost:5432/test_db"
    
    @patch('urllib.parse.quote_plus')
    def test_get_uri_async_postgresql(self, mock_quote_plus):
        """Test getting an async PostgreSQL URI."""
        # Setup mock for password encoding
        mock_quote_plus.return_value = "encoded_password"
        
        # Create config for async PostgreSQL
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test@password",
            db_driver="postgresql+asyncpg"
        )
        
        # Get URI
        uri = config.get_uri()
        
        # Verify password was encoded
        mock_quote_plus.assert_called_once_with("test@password")
        
        # Verify URI format
        assert uri == "asyncpg://test_role:encoded_password@localhost:5432/test_db"
    
    @patch('urllib.parse.quote_plus')
    def test_get_uri_with_postgresql_prefix(self, mock_quote_plus):
        """Test getting a URI with postgresql+ prefix in driver name."""
        # Setup mock for password encoding
        mock_quote_plus.return_value = "encoded_password"
        
        # Create config with postgresql+ prefix
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test@password",
            db_driver="postgresql+psycopg2"  # Has postgresql+ prefix
        )
        
        # Get URI
        uri = config.get_uri()
        
        # Verify URI format doesn't duplicate postgresql+
        assert uri == "postgresql+psycopg2://test_role:encoded_password@localhost:5432/test_db"
    
    @patch('urllib.parse.quote_plus')
    def test_get_uri_other_driver(self, mock_quote_plus):
        """Test getting a URI for a non-PostgreSQL driver."""
        # Setup mock for password encoding
        mock_quote_plus.return_value = "encoded_password"
        
        # Create config for a different driver
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test@password",
            db_driver="mysql+pymysql"  # Non-PostgreSQL driver
        )
        
        # Get URI
        uri = config.get_uri()
        
        # Verify password was encoded
        mock_quote_plus.assert_called_once_with("test@password")
        
        # Verify URI format
        assert uri == "mysql+pymysql://test_role:encoded_password@localhost:5432/test_db"
        
    @patch('urllib.parse.quote_plus')
    def test_connection_config_with_special_characters(self, mock_quote_plus):
        """Test ConnectionConfig handles special characters in passwords."""
        # Create config with special characters in password
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="p@$$w0rd!+%^*",  # Password with special characters
            db_driver="postgresql+psycopg2"
        )
        
        # Setup mock for password encoding
        mock_quote_plus.return_value = "encoded_special_password"
        
        # Get URI with encoded password
        uri = config.get_uri()
        
        # Verify quote_plus was called with the special password
        mock_quote_plus.assert_called_once_with("p@$$w0rd!+%^*")
        
        # Verify URI contains the encoded password
        assert uri == "postgresql+psycopg2://test_role:encoded_special_password@localhost:5432/test_db"
    
    def test_connection_config_driver_specific_args(self):
        """Test ConnectionConfig with driver-specific connect_args."""
        # Create config with connect_args
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+psycopg2",
            connect_args={
                "ssl": True,
                "application_name": "test_app",
                "keepalives": 1
            }
        )
        
        # Verify connect_args are stored correctly
        assert config.connect_args == {
            "ssl": True,
            "application_name": "test_app",
            "keepalives": 1
        }
        
        # Verify connect_args are accessible
        assert config.connect_args.get("ssl") is True
        assert config.connect_args.get("application_name") == "test_app"
        assert config.connect_args.get("keepalives") == 1