"""
Tests for the enhanced pool session module.

These tests verify the functionality of the enhanced pool session system.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine

from uno.database.config import ConnectionConfig
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    get_connection_manager,
)
from uno.database.enhanced_pool_session import (
    SessionPoolConfig,
    EnhancedPooledSessionFactory,
    EnhancedPooledSessionContext,
    enhanced_pool_session,
    EnhancedPooledSessionOperationGroup,
)


class MockEngine:
    """Mock SQLAlchemy AsyncEngine."""
    
    def __init__(self):
        self.dispose = AsyncMock()
        self.connect = AsyncMock()


class MockConnection:
    """Mock SQLAlchemy AsyncConnection."""
    
    def __init__(self, engine):
        self.engine = engine
        self.close = AsyncMock()
        self.execute = AsyncMock()
        self.execution_options = AsyncMock(return_value=None)


class MockSession:
    """Mock SQLAlchemy AsyncSession."""
    
    def __init__(self):
        self.close = AsyncMock()
        self.begin = AsyncMock(return_value=self)
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


# Test session factory
@pytest.mark.asyncio
async def test_enhanced_pooled_session_factory():
    """Test EnhancedPooledSessionFactory class."""
    # Create mock AsyncEngine and AsyncSession factories
    with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine, \
         patch("sqlalchemy.ext.asyncio.async_sessionmaker") as mock_session_maker:
        
        # Set up mocks
        mock_engine = MockEngine()
        mock_create_engine.return_value = mock_engine
        
        mock_session = MockSession()
        mock_session_maker.return_value = MagicMock(return_value=mock_session)
        
        # Create session factory
        factory = EnhancedPooledSessionFactory(
            session_pool_config=SessionPoolConfig(
                min_sessions=1,
                max_sessions=2,
            )
        )
        
        # Create connection config
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_user_pw="password",
            db_driver="postgresql+asyncpg",
        )
        
        # Test storing connection config
        config_key = factory.store_connection_config(config)
        assert config_key == "test_role@localhost/test_db"
        
        # Mock the AsyncCache.get method to return the session maker directly
        factory._session_cache.get = AsyncMock(return_value=mock_session_maker.return_value)
        
        # Create a pooled session
        session = await factory.create_pooled_session_async(config)
        
        # Verify we got the mock session
        assert session is mock_session
        
        # Test tracking
        assert factory._active_sessions.get(config_key, 0) > 0
        
        # Test closing session
        await session.close()
        
        # Verify tracking updated
        assert factory._active_sessions.get(config_key, 0) == 0


# Test session context
@pytest.mark.asyncio
async def test_enhanced_pooled_session_context():
    """Test EnhancedPooledSessionContext class."""
    # Create mock factory
    mock_factory = MagicMock(spec=EnhancedPooledSessionFactory)
    mock_factory.create_pooled_session_async = AsyncMock(return_value=MockSession())
    mock_factory.create_session = MagicMock(return_value=MockSession())
    mock_factory.get_scoped_session = MagicMock(return_value=MagicMock(return_value=MockSession()))
    
    # Test non-scoped session
    context = EnhancedPooledSessionContext(
        factory=mock_factory,
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
    )
    
    async with context as session:
        assert isinstance(session, MockSession)
        mock_factory.create_pooled_session_async.assert_awaited_once()
    
    # Test scoped session
    context = EnhancedPooledSessionContext(
        factory=mock_factory,
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
        scoped=True,
    )
    
    async with context as session:
        assert isinstance(session, MockSession)
        mock_factory.get_scoped_session.assert_called_once()


# Test session context manager function
@pytest.mark.asyncio
async def test_enhanced_pool_session():
    """Test enhanced_pool_session function."""
    # Create mock factory
    mock_factory = MagicMock(spec=EnhancedPooledSessionFactory)
    mock_factory.create_pooled_session_async = AsyncMock(return_value=MockSession())
    mock_factory.create_session = MagicMock(return_value=MockSession())
    mock_factory.get_scoped_session = MagicMock(return_value=MagicMock(return_value=MockSession()))
    
    # Test session context manager
    async with enhanced_pool_session(
        factory=mock_factory,
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
    ) as session:
        assert isinstance(session, MockSession)
        mock_factory.create_pooled_session_async.assert_awaited_once()


# Test session operation group
@pytest.mark.asyncio
async def test_enhanced_pooled_session_operation_group():
    """Test EnhancedPooledSessionOperationGroup class."""
    # Create mock factory to replace the real one
    mock_factory = MagicMock(spec=EnhancedPooledSessionFactory)
    
    # Set up mocks for creating sessions
    mock_session = MockSession()
    
    # Create the operation group
    group = EnhancedPooledSessionOperationGroup(
        name="test_group",
        session_pool_config=SessionPoolConfig(
            min_sessions=1,
            max_sessions=2,
        ),
    )
    
    # Replace the factory with our mock
    group.factory = mock_factory
    mock_factory.create_pooled_session_async = AsyncMock(return_value=mock_session)
    
    # Enter the group context
    async with group as g:
        assert g is group
        
        # Create a session
        session = await group.create_session(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
        )
        
        # Should have session in tracked sessions
        assert session in group.sessions
        
        # Test run_operation
        test_op = AsyncMock(return_value="test_result")
        result = await group.run_operation(session, test_op, "arg1", arg2="arg2")
        
        assert result == "test_result"
        test_op.assert_awaited_once_with(session, "arg1", arg2="arg2")
        
        # Test run_in_transaction
        test_op1 = AsyncMock(return_value="result1")
        test_op2 = AsyncMock(return_value="result2")
        
        results = await group.run_in_transaction(session, [
            lambda s: test_op1(s),
            lambda s: test_op2(s),
        ])
        
        assert results == ["result1", "result2"]
        test_op1.assert_awaited_once_with(session)
        test_op2.assert_awaited_once_with(session)
        
        # Test run_parallel_operations
        test_op3 = AsyncMock(return_value="result3")
        test_op4 = AsyncMock(return_value="result4")
        
        results = await group.run_parallel_operations(session, [
            lambda s: test_op3(s),
            lambda s: test_op4(s),
        ])
        
        assert results == ["result3", "result4"]
        test_op3.assert_awaited_once_with(session)
        test_op4.assert_awaited_once_with(session)
    
    # After context exit, session should be closed
    mock_session.close.assert_awaited_once()


# Test integration with connection manager
@pytest.mark.asyncio
async def test_integration_with_connection_manager():
    """Test integration between session system and connection manager."""
    # Create mock AsyncEngine factory
    with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine, \
         patch("sqlalchemy.ext.asyncio.async_sessionmaker") as mock_session_maker:
        
        # Set up mocks
        mock_engine = MockEngine()
        mock_connection = MockConnection(mock_engine)
        mock_engine.connect = AsyncMock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        mock_session = MockSession()
        mock_session_maker.return_value = MagicMock(return_value=mock_session)
        
        # Get the connection manager
        manager = get_connection_manager()
        
        # Configure the connection pool
        pool_config = ConnectionPoolConfig(
            initial_size=1,
            min_size=1,
            max_size=2,
        )
        manager.configure_pool(
            role="test_role",
            config=pool_config,
        )
        
        # Create a session factory
        factory = EnhancedPooledSessionFactory(
            session_pool_config=SessionPoolConfig(
                min_sessions=1,
                max_sessions=2,
                connection_pool_config=pool_config,
            )
        )
        
        # Mock the AsyncCache.get method to return the session maker directly
        factory._session_cache.get = AsyncMock(return_value=mock_session_maker.return_value)
        
        # Create a session
        session = await factory.create_pooled_session_async(
            ConnectionConfig(
                db_role="test_role",
                db_name="test_db",
                db_host="localhost",
                db_user_pw="password",
                db_driver="postgresql+asyncpg",
            )
        )
        
        # Verify we got the mock session
        assert session is mock_session
        
        # Close session for cleanup
        await session.close()
        
        # Close manager for cleanup
        await manager.close()