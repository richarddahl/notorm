# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the top-level DatabaseFactory.

These tests verify the integration of specialized database factories and
the overall structure of the database connection management system.
"""

import pytest
from unittest.mock import MagicMock, patch
import logging

from uno.database.engine import (
    DatabaseFactory,
    SyncEngineFactory,
    AsyncEngineFactory
)
from uno.database.session import AsyncSessionFactory


class TestDatabaseFactory:
    """Tests for the top-level DatabaseFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = MagicMock(spec=logging.Logger)
        self.factory = DatabaseFactory(logger=self.logger)
    
    def test_initialization(self):
        """Test factory initialization creates all specialized factories."""
        # Verify all specialized factories were created
        assert isinstance(self.factory.sync_engine_factory, SyncEngineFactory)
        assert isinstance(self.factory.async_engine_factory, AsyncEngineFactory)
        assert isinstance(self.factory.async_session_factory, AsyncSessionFactory)
        
        # Verify logger is shared between all factories
        assert self.factory.sync_engine_factory.logger is self.logger
        assert self.factory.async_engine_factory.logger is self.logger
        assert self.factory.async_session_factory.logger is self.logger
    
    def test_get_sync_engine_factory(self):
        """Test retrieving the sync engine factory."""
        factory = self.factory.get_sync_engine_factory()
        assert factory is self.factory.sync_engine_factory
        assert isinstance(factory, SyncEngineFactory)
    
    def test_get_async_engine_factory(self):
        """Test retrieving the async engine factory."""
        factory = self.factory.get_async_engine_factory()
        assert factory is self.factory.async_engine_factory
        assert isinstance(factory, AsyncEngineFactory)
    
    def test_get_async_session_factory(self):
        """Test retrieving the async session factory."""
        factory = self.factory.get_async_session_factory()
        assert factory is self.factory.async_session_factory
        assert isinstance(factory, AsyncSessionFactory)
    
    def test_factory_callback_isolation(self):
        """Test callbacks registered on one factory don't affect others."""
        # Create callback mocks
        sync_callback = MagicMock()
        async_callback = MagicMock()
        
        # Register callbacks on different factories
        sync_factory = self.factory.get_sync_engine_factory()
        async_factory = self.factory.get_async_engine_factory()
        
        sync_factory.register_callback("sync_test", sync_callback)
        async_factory.register_callback("async_test", async_callback)
        
        # Verify callbacks are only registered on the appropriate factory
        assert "sync_test" in sync_factory.connection_callbacks
        assert "sync_test" not in async_factory.connection_callbacks
        
        assert "async_test" in async_factory.connection_callbacks
        assert "async_test" not in sync_factory.connection_callbacks
    
    def test_custom_factories(self):
        """Test DatabaseFactory works with custom factory implementations."""
        # Create custom factory implementations
        custom_sync_factory = MagicMock(spec=SyncEngineFactory)
        custom_async_factory = MagicMock(spec=AsyncEngineFactory)
        custom_session_factory = MagicMock(spec=AsyncSessionFactory)
        
        # Create a factory directly with custom instances
        factory = DatabaseFactory(logger=self.logger)
        
        # Replace the default factories with our custom ones
        factory.sync_engine_factory = custom_sync_factory
        factory.async_engine_factory = custom_async_factory
        factory.async_session_factory = custom_session_factory
        
        # Verify factory getters return the custom instances
        assert factory.get_sync_engine_factory() is custom_sync_factory
        assert factory.get_async_engine_factory() is custom_async_factory
        assert factory.get_async_session_factory() is custom_session_factory