# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the database session management.

These tests verify the behavior of the AsyncSessionFactory class and the
async_session context manager.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, async_scoped_session

from uno.database.session import AsyncSessionFactory, async_session
from uno.database.config import ConnectionConfig
from uno.database.engine.asynceng import AsyncEngineFactory


class TestAsyncSessionFactory:
    """Tests for the AsyncSessionFactory class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = MagicMock(spec=logging.Logger)
        self.engine_factory = MagicMock(spec=AsyncEngineFactory)
        self.session_factory = AsyncSessionFactory(
            engine_factory=self.engine_factory,
            logger=self.logger
        )
        
        self.config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_port=5432,
            db_user_pw="test_password",
            db_driver="postgresql+asyncpg"
        )
    
    def test_initialization(self):
        """Test session factory initialization."""
        # Verify initial state
        assert self.session_factory.engine_factory == self.engine_factory
        assert self.session_factory.logger == self.logger
        assert self.session_factory._sessionmakers == {}
        assert self.session_factory._scoped_sessions == {}
        
        # Test initialization without explicit engine factory
        with patch('uno.database.session.AsyncEngineFactory') as MockFactory:
            mock_factory = MagicMock()
            MockFactory.return_value = mock_factory
            
            session_factory = AsyncSessionFactory(logger=self.logger)
            
            # Verify default engine factory was created
            assert session_factory.engine_factory == mock_factory
    
    @patch('uno.database.session.async_sessionmaker')
    def test_create_sessionmaker(self, mock_async_sessionmaker):
        """Test creating a session maker."""
        # Setup mocks
        mock_engine = MagicMock()
        self.engine_factory.create_engine.return_value = mock_engine
        
        mock_sessionmaker = MagicMock(spec=async_sessionmaker)
        mock_async_sessionmaker.return_value = mock_sessionmaker
        
        # Call create_sessionmaker
        result = self.session_factory.create_sessionmaker(self.config)
        
        # Verify engine was created
        self.engine_factory.create_engine.assert_called_once_with(self.config)
        
        # Verify sessionmaker was created with correct args
        mock_async_sessionmaker.assert_called_once_with(
            mock_engine, expire_on_commit=False, class_=AsyncSession
        )
        
        # Verify result
        assert result == mock_sessionmaker
        
        # Verify sessionmaker was cached
        conn_key = f"{self.config.db_role}@{self.config.db_host}/{self.config.db_name}"
        assert self.session_factory._sessionmakers[conn_key] == mock_sessionmaker
        
        # Verify cached sessionmaker is returned on subsequent calls
        self.engine_factory.create_engine.reset_mock()
        mock_async_sessionmaker.reset_mock()
        
        result2 = self.session_factory.create_sessionmaker(self.config)
        
        # Verify no new engine or sessionmaker was created
        self.engine_factory.create_engine.assert_not_called()
        mock_async_sessionmaker.assert_not_called()
        
        # Verify cached result was returned
        assert result2 == mock_sessionmaker
    
    @patch('uno.database.session.async_sessionmaker')
    def test_create_session(self, mock_async_sessionmaker):
        """Test creating a session."""
        # Setup mocks
        mock_engine = MagicMock()
        self.engine_factory.create_engine.return_value = mock_engine
        
        mock_sessionmaker = MagicMock(spec=async_sessionmaker)
        mock_async_sessionmaker.return_value = mock_sessionmaker
        
        mock_session = MagicMock(spec=AsyncSession)
        mock_sessionmaker.return_value = mock_session
        
        # Call create_session
        result = self.session_factory.create_session(self.config)
        
        # Verify sessionmaker was created and called
        self.engine_factory.create_engine.assert_called_once_with(self.config)
        mock_async_sessionmaker.assert_called_once()
        mock_sessionmaker.assert_called_once_with()
        
        # Verify result
        assert result == mock_session
    
    @patch('uno.database.session.async_sessionmaker')
    @patch('uno.database.session.async_scoped_session')
    @patch('uno.database.session.current_task')
    def test_get_scoped_session(self, mock_current_task, mock_async_scoped_session, mock_async_sessionmaker):
        """Test getting a scoped session."""
        # Setup mocks
        mock_engine = MagicMock()
        self.engine_factory.create_engine.return_value = mock_engine
        
        mock_sessionmaker = MagicMock(spec=async_sessionmaker)
        mock_async_sessionmaker.return_value = mock_sessionmaker
        
        mock_scoped_session = MagicMock(spec=async_scoped_session)
        mock_async_scoped_session.return_value = mock_scoped_session
        
        # Call get_scoped_session
        result = self.session_factory.get_scoped_session(self.config)
        
        # Verify sessionmaker was created
        self.engine_factory.create_engine.assert_called_once_with(self.config)
        mock_async_sessionmaker.assert_called_once()
        
        # Verify scoped session was created with correct args
        mock_async_scoped_session.assert_called_once_with(
            mock_sessionmaker, scopefunc=mock_current_task
        )
        
        # Verify result
        assert result == mock_scoped_session
        
        # Verify scoped session was cached
        conn_key = f"{self.config.db_role}@{self.config.db_host}/{self.config.db_name}"
        assert self.session_factory._scoped_sessions[conn_key] == mock_scoped_session
        
        # Verify cached scoped session is returned on subsequent calls
        self.engine_factory.create_engine.reset_mock()
        mock_async_sessionmaker.reset_mock()
        mock_async_scoped_session.reset_mock()
        
        result2 = self.session_factory.get_scoped_session(self.config)
        
        # Verify no new engine, sessionmaker, or scoped session was created
        self.engine_factory.create_engine.assert_not_called()
        mock_async_sessionmaker.assert_not_called()
        mock_async_scoped_session.assert_not_called()
        
        # Verify cached result was returned
        assert result2 == mock_scoped_session
    
    @pytest.mark.asyncio
    async def test_remove_all_scoped_sessions(self):
        """Test removing all scoped sessions."""
        # Setup mock scoped sessions
        scoped_session1 = AsyncMock(spec=async_scoped_session)
        scoped_session2 = AsyncMock(spec=async_scoped_session)
        
        self.session_factory._scoped_sessions = {
            "conn1": scoped_session1,
            "conn2": scoped_session2
        }
        
        # Call remove_all_scoped_sessions
        await self.session_factory.remove_all_scoped_sessions()
        
        # Verify remove was called on all scoped sessions
        scoped_session1.remove.assert_called_once()
        scoped_session2.remove.assert_called_once()


@pytest.mark.asyncio
class TestAsyncSession:
    """Tests for the async_session context manager."""
    
    @patch('uno.database.session.AsyncSessionFactory')
    async def test_async_session_regular(self, MockFactory):
        """Test regular async session."""
        # Setup mocks
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory.create_session.return_value = mock_session
        
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
            assert session == mock_session
        
        # Verify factory used the correct config
        config_arg = mock_factory.create_session.call_args[0][0]
        assert config_arg.db_driver == "postgresql+asyncpg"
        assert config_arg.db_name == "test_db"
        assert config_arg.db_user_pw == "test_password"
        assert config_arg.db_role == "test_role"
        assert config_arg.db_host == "localhost"
        assert config_arg.db_port == 5432
        
        # Verify session was closed
        mock_session.close.assert_called_once()
    
    @patch('uno.database.session.AsyncSessionFactory')
    async def test_async_session_scoped(self, MockFactory):
        """Test scoped async session."""
        # Setup mocks
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        mock_scoped_session = MagicMock()
        mock_factory.get_scoped_session.return_value = mock_scoped_session
        
        mock_session = AsyncMock(spec=AsyncSession)
        mock_scoped_session.return_value = mock_session
        
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
            assert session == mock_session
        
        # Verify get_scoped_session was called with correct config
        config_arg = mock_factory.get_scoped_session.call_args[0][0]
        assert config_arg.db_driver == "postgresql+asyncpg"
        assert config_arg.db_name == "test_db"
        assert config_arg.db_user_pw == "test_password"
        assert config_arg.db_role == "test_role"
        assert config_arg.db_host == "localhost"
        assert config_arg.db_port == 5432
        
        # Verify scoped session was created
        mock_scoped_session.assert_called_once()
        
        # Verify session was NOT closed (scoped sessions are managed separately)
        mock_session.close.assert_not_called()