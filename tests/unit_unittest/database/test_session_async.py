# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the database session async functionality.

These tests verify the behavior of the async_session context manager.
"""

import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.session import AsyncSessionFactory, async_session
from uno.database.config import ConnectionConfig


class AsyncMockContextManager:
    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestAsyncSession(IsolatedAsyncioTestCase):
    """Tests for the async_session context manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
    
    async def test_async_session_regular(self):
        """Test regular async session."""
        # Setup mocks
        mock_factory = MagicMock()
        
        # Create a regular session mock with close as AsyncMock
        mock_session = MagicMock()
        # Only make close awaitable since that's what gets awaited in the code
        mock_session.close = AsyncMock()
        mock_factory.create_session = MagicMock(return_value=mock_session)
        
        # Patch the factory class
        with patch('uno.database.session.AsyncSessionFactory', return_value=mock_factory):
            # Use async_session
            async with async_session(
                db_driver="postgresql+asyncpg",
                db_name="test_db",
                db_user_pw="test_password",
                db_role="test_role",
                db_host="localhost",
                db_port=5432,
                factory=mock_factory,
                scoped=False
            ) as session:
                # Verify session was yielded
                self.assertEqual(session, mock_session)
            
            # Verify factory used with correct config
            config_arg = mock_factory.create_session.call_args[0][0]
            self.assertEqual(config_arg.db_driver, "postgresql+asyncpg")
            self.assertEqual(config_arg.db_name, "test_db")
            self.assertEqual(config_arg.db_user_pw, "test_password")
            self.assertEqual(config_arg.db_role, "test_role")
            self.assertEqual(config_arg.db_host, "localhost")
            self.assertEqual(config_arg.db_port, 5432)
            
            # Verify session was closed
            mock_session.close.assert_called_once()
    
    async def test_async_session_scoped(self):
        """Test scoped async session."""
        # Setup mocks
        mock_factory = MagicMock()
        
        # Create a scoped session mock
        mock_scoped_session = MagicMock()
        
        # Create a regular session mock
        mock_session = MagicMock()
        mock_scoped_session.return_value = mock_session
        mock_factory.get_scoped_session = MagicMock(return_value=mock_scoped_session)
        
        # Patch the factory class
        with patch('uno.database.session.AsyncSessionFactory', return_value=mock_factory):
            # Use async_session with scoped=True
            async with async_session(
                db_driver="postgresql+asyncpg",
                db_name="test_db",
                db_user_pw="test_password",
                db_role="test_role",
                db_host="localhost",
                db_port=5432,
                factory=mock_factory,
                scoped=True
            ) as session:
                # Verify session was yielded
                self.assertEqual(session, mock_session)
            
            # Verify get_scoped_session was called with correct config
            config_arg = mock_factory.get_scoped_session.call_args[0][0]
            self.assertEqual(config_arg.db_driver, "postgresql+asyncpg")
            self.assertEqual(config_arg.db_name, "test_db")
            self.assertEqual(config_arg.db_user_pw, "test_password")
            self.assertEqual(config_arg.db_role, "test_role")
            self.assertEqual(config_arg.db_host, "localhost")
            self.assertEqual(config_arg.db_port, 5432)
            
            # Verify scoped session was created
            mock_scoped_session.assert_called_once()
            
            # Verify session was NOT closed (scoped sessions are managed separately)
            mock_session.close.assert_not_called()