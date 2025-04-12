"""
Tests for the enhanced async database operations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from uno.database.engine.enhanced_async import (
    EnhancedAsyncEngineFactory,
    connect_with_retry,
    AsyncConnectionContext,
    enhanced_async_connection,
    DatabaseOperationGroup,
)
from uno.database.enhanced_session import (
    EnhancedAsyncSessionFactory,
    EnhancedAsyncSessionContext,
    enhanced_async_session,
    SessionOperationGroup,
)
from uno.core.async import TaskGroup, AsyncLock, AsyncContextGroup, AsyncExitStack


@pytest.mark.asyncio
async def test_enhanced_async_engine_factory():
    """Test the EnhancedAsyncEngineFactory."""
    factory = EnhancedAsyncEngineFactory()
    
    # Test connection limiter
    assert factory.connection_limiter is not None
    assert factory.connection_limiter.max_concurrent == 10
    
    # Test getting connection lock
    config = MagicMock()
    config.db_role = "test_role"
    config.db_host = "test_host"
    config.db_name = "test_db"
    
    lock1 = factory.get_connection_lock(config)
    assert isinstance(lock1, AsyncLock)
    
    # Getting the same lock for the same config
    lock2 = factory.get_connection_lock(config)
    assert lock1 is lock2  # Should be the same instance


@pytest.mark.asyncio
async def test_connect_with_retry():
    """Test the connect_with_retry function."""
    # Mock connection config and factory
    config = MagicMock()
    factory = MagicMock()
    
    # Mock the connection lock
    lock_mock = AsyncMock()
    factory.get_connection_lock.return_value = lock_mock
    
    # Mock the connection limiter
    limiter_mock = AsyncMock()
    factory.connection_limiter = limiter_mock
    
    # Mock engine and connection
    engine_mock = MagicMock()
    connection_mock = AsyncMock()
    
    # Setup the mocks to return values
    factory.create_engine.return_value = engine_mock
    engine_mock.connect.return_value = AsyncMock()
    engine_mock.connect.return_value.__aenter__.return_value = connection_mock
    
    # Test successful connection on first try
    with patch("asyncio.Task.current_task", return_value=MagicMock(get_name=lambda: "task1")):
        result = await connect_with_retry(config, factory)
    
    # Verify the result
    assert result == connection_mock
    
    # Verify method calls
    factory.get_connection_lock.assert_called_once_with(config)
    lock_mock.__aenter__.assert_called_once()
    lock_mock.__aexit__.assert_called_once()
    limiter_mock.__aenter__.assert_called_once()
    limiter_mock.__aexit__.assert_called_once()
    factory.create_engine.assert_called_once_with(config)
    engine_mock.connect.assert_called_once()
    connection_mock.execution_options.assert_called_once()
    factory.execute_callbacks.assert_called_once_with(connection_mock)


@pytest.mark.asyncio
async def test_async_connection_context():
    """Test the AsyncConnectionContext."""
    # Mock connection config and factory
    config = MagicMock()
    factory = MagicMock()
    
    # Mock connection
    connection_mock = AsyncMock()
    
    # Setup the mocks to use patch
    with patch("uno.database.engine.enhanced_async.connect_with_retry", 
              return_value=connection_mock) as mock_connect:
        # Create and use the context
        context = AsyncConnectionContext(
            db_role="test_role",
            db_name="test_db",
            factory=factory
        )
        
        async with context as connection:
            # Verify we got the mocked connection
            assert connection == connection_mock
            
            # Verify connect_with_retry was called
            mock_connect.assert_called_once()
            
        # Verify connection was closed
        connection_mock.close.assert_called_once()


@pytest.mark.asyncio
async def test_database_operation_group():
    """Test the DatabaseOperationGroup."""
    # Create a group
    group = DatabaseOperationGroup(name="test_group")
    
    # Verify initial state
    assert group.name == "test_group"
    assert isinstance(group.task_group, TaskGroup)
    assert isinstance(group.context_group, AsyncContextGroup)
    assert isinstance(group.exit_stack, AsyncExitStack)
    
    # Set up mock for execute_in_transaction
    session_mock = AsyncMock()
    operation1 = AsyncMock(return_value="result1")
    operation2 = AsyncMock(return_value="result2")
    
    # Use the group
    async with group:
        # Test execute_in_transaction
        result = await group.execute_in_transaction(
            session_mock,
            [operation1, operation2]
        )
        
        # Verify results
        assert result == ["result1", "result2"]
        
        # Verify operations were called
        operation1.assert_called_once_with(session_mock)
        operation2.assert_called_once_with(session_mock)
        
        # Test run_operation
        task_result = await group.run_operation(
            lambda: asyncio.sleep(0.01, result="task_result")
        )
        
        # Verify task result
        assert task_result == "task_result"


@pytest.mark.asyncio
async def test_enhanced_async_session_factory():
    """Test the EnhancedAsyncSessionFactory."""
    # Create factory
    factory = EnhancedAsyncSessionFactory()
    
    # Verify initial state
    assert factory.session_limiter is not None
    assert factory.session_limiter.max_concurrent == 20
    assert isinstance(factory._session_locks, dict)
    assert isinstance(factory._sessionmakers, dict)
    assert isinstance(factory._scoped_sessions, dict)
    assert isinstance(factory._active_sessions, dict)
    
    # Test get_session_lock
    config = MagicMock()
    config.db_role = "test_role"
    config.db_host = "test_host"
    config.db_name = "test_db"
    
    lock = factory.get_session_lock(config)
    assert isinstance(lock, AsyncLock)
    
    # Test create_sessionmaker
    with patch("uno.database.enhanced_session.async_sessionmaker") as mock_sessionmaker:
        # Run the method
        factory.create_sessionmaker(config)
        
        # Verify engine was created
        assert mock_sessionmaker.called


@pytest.mark.asyncio
async def test_session_operation_group():
    """Test the SessionOperationGroup."""
    # Create a group
    group = SessionOperationGroup(name="test_group")
    
    # Verify initial state
    assert group.name == "test_group"
    assert isinstance(group.task_group, TaskGroup)
    assert isinstance(group.context_group, AsyncContextGroup)
    assert isinstance(group.exit_stack, AsyncExitStack)
    assert isinstance(group.sessions, list)
    
    # Set up mock for create_session
    session_mock = AsyncMock()
    
    # Mock the EnhancedAsyncSessionContext
    with patch("uno.database.enhanced_session.EnhancedAsyncSessionContext") as mock_context:
        # Setup the context mock
        context_instance = AsyncMock()
        mock_context.return_value = context_instance
        context_instance.__aenter__.return_value = session_mock
        
        # Use the group
        async with group:
            # Test create_session
            session = await group.create_session(
                db_role="test_role",
                db_name="test_db"
            )
            
            # Verify session was created
            assert session == session_mock
            assert session in group.sessions
            
            # Test run_operation
            operation_mock = AsyncMock(return_value="op_result")
            
            result = await group.run_operation(
                session,
                operation_mock,
                "arg1",
                kwarg1="value1"
            )
            
            # Verify operation was called
            operation_mock.assert_called_once_with(session, "arg1", kwarg1="value1")
            assert result == "op_result"
            
            # Test run_in_transaction
            op1 = AsyncMock(return_value="result1")
            op2 = AsyncMock(return_value="result2")
            
            results = await group.run_in_transaction(
                session,
                [op1, op2]
            )
            
            # Verify transaction was used
            session.begin.assert_called_once()
            assert isinstance(results, list)
            assert len(results) == 2
            assert "result1" in results
            assert "result2" in results