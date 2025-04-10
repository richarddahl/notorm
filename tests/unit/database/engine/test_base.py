# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the base database engine factory.

These tests verify the behavior of the EngineFactory base class, focusing on
connection callbacks, registration, and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch
import logging

from uno.database.engine.base import EngineFactory
from uno.database.config import ConnectionConfig


class MockEngineFactory(EngineFactory):
    """Mock implementation of EngineFactory for testing."""
    
    def create_engine(self, config):
        """Create a mock engine."""
        return MagicMock()


class TestEngineFactory:
    """Tests for the base EngineFactory class."""
    
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
        self.factory = MockEngineFactory(logger=self.logger)
    
    def test_initialization(self):
        """Test engine factory initialization."""
        # Verify initial state
        assert self.factory.logger == self.logger
        assert self.factory.connection_callbacks == {}
    
    def test_register_callback(self):
        """Test registering a connection callback."""
        # Create a test callback
        callback = MagicMock()
        
        # Register the callback
        self.factory.register_callback("test_callback", callback)
        
        # Verify callback was registered
        assert "test_callback" in self.factory.connection_callbacks
        assert self.factory.connection_callbacks["test_callback"] == callback
    
    def test_unregister_callback(self):
        """Test unregistering a connection callback."""
        # Create and register a test callback
        callback = MagicMock()
        self.factory.register_callback("test_callback", callback)
        
        # Verify callback was registered
        assert "test_callback" in self.factory.connection_callbacks
        
        # Unregister the callback
        self.factory.unregister_callback("test_callback")
        
        # Verify callback was removed
        assert "test_callback" not in self.factory.connection_callbacks
    
    def test_unregister_nonexistent_callback(self):
        """Test unregistering a callback that doesn't exist."""
        # Unregister a nonexistent callback
        self.factory.unregister_callback("nonexistent")
        
        # Verify no errors occurred
        assert "nonexistent" not in self.factory.connection_callbacks
    
    def test_execute_callbacks(self):
        """Test executing connection callbacks."""
        # Create and register multiple test callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()
        self.factory.register_callback("callback1", callback1)
        self.factory.register_callback("callback2", callback2)
        
        # Create a mock connection
        connection = MagicMock()
        
        # Execute callbacks
        self.factory.execute_callbacks(connection)
        
        # Verify callbacks were called with the connection
        callback1.assert_called_once_with(connection)
        callback2.assert_called_once_with(connection)
    
    def test_execute_callbacks_with_exception(self):
        """Test handling of exceptions in callbacks."""
        # Create and register a callback that raises an exception
        error_callback = MagicMock(side_effect=Exception("Test exception"))
        normal_callback = MagicMock()
        
        self.factory.register_callback("error_callback", error_callback)
        self.factory.register_callback("normal_callback", normal_callback)
        
        # Create a mock connection
        connection = MagicMock()
        
        # Execute callbacks
        self.factory.execute_callbacks(connection)
        
        # Verify error was logged
        self.logger.error.assert_called_once()
        assert "Test exception" in str(self.logger.error.call_args)
        
        # Verify normal callback was still called
        normal_callback.assert_called_once_with(connection)
    
    def test_create_engine_abstract(self):
        """Test create_engine is an abstract method."""
        # Verify that we can't instantiate EngineFactory directly
        with pytest.raises(TypeError) as exc_info:
            factory = EngineFactory(logger=self.logger)
        
        # Verify the error mentions the abstract method
        assert "abstract method 'create_engine'" in str(exc_info.value)