"""
Tests for the enhanced connection pool module.

These tests verify the functionality of the enhanced connection pool system.
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection

from uno.database.config import ConnectionConfig
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    ConnectionPoolStrategy,
    ConnectionMetrics,
    PoolMetrics,
    EnhancedConnectionPool,
    EnhancedAsyncEnginePool,
    EnhancedAsyncConnectionManager,
    get_connection_manager,
    enhanced_async_engine,
    enhanced_async_connection,
)
from uno.core.async_utils import AsyncLock, timeout
from uno.core.resources import ResourceRegistry


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
        

# Test connection metrics
def test_connection_metrics():
    """Test ConnectionMetrics class."""
    metrics = ConnectionMetrics()
    
    # Test initial state
    assert metrics.usage_count == 0
    assert metrics.error_count == 0
    assert metrics.query_count == 0
    assert metrics.validation_count == 0
    
    # Test update methods
    metrics.update_usage()
    assert metrics.usage_count == 1
    
    metrics.record_error()
    assert metrics.error_count == 1
    
    metrics.record_query(0.5)
    assert metrics.query_count == 1
    assert metrics.total_query_time == 0.5
    assert metrics.max_query_time == 0.5
    
    metrics.record_validation(True)
    assert metrics.validation_count == 1
    assert metrics.validation_failures == 0
    
    metrics.record_validation(False)
    assert metrics.validation_count == 2
    assert metrics.validation_failures == 1
    
    metrics.record_reset()
    assert metrics.reset_count == 1
    
    metrics.record_transaction(True)
    assert metrics.transaction_count == 1
    assert metrics.transaction_rollbacks == 0
    
    metrics.record_transaction(False)
    assert metrics.transaction_count == 2
    assert metrics.transaction_rollbacks == 1
    
    # Test properties
    assert metrics.avg_query_time == 0.5
    assert metrics.validation_failure_rate == 0.5
    assert metrics.rollback_rate == 0.5
    assert metrics.age > 0
    assert metrics.idle_time > 0


# Test pool metrics
def test_pool_metrics():
    """Test PoolMetrics class."""
    metrics = PoolMetrics()
    
    # Test initial state
    assert metrics.connections_created == 0
    assert metrics.connections_closed == 0
    assert metrics.current_size == 0
    
    # Create some connections
    metrics.record_connection_created("conn1")
    metrics.record_connection_created("conn2")
    
    assert metrics.connections_created == 2
    assert metrics.current_size == 2
    assert "conn1" in metrics.connection_metrics
    assert "conn2" in metrics.connection_metrics
    
    # Test connection checkout/checkin
    metrics.record_connection_checkout("conn1")
    assert metrics.active_connections == 1
    
    metrics.record_connection_checkin("conn1")
    assert metrics.active_connections == 0
    assert metrics.idle_connections == 1
    
    # Test load sampling
    metrics.record_load_sample(0.5)
    assert len(metrics.load_samples) == 1
    assert len(metrics.load_sample_times) == 1
    
    assert metrics.get_current_load() == 0  # 0 active / 2 total
    
    metrics.record_connection_checkout("conn1")
    metrics.record_connection_checkout("conn2")
    
    assert metrics.get_current_load() == 1.0  # 2 active / 2 total
    
    # Test wait time metrics
    metrics.record_wait_time(0.1)
    metrics.record_wait_time(0.3)
    
    assert metrics.wait_count == 2
    assert metrics.wait_time_total == 0.4
    assert metrics.avg_wait_time == 0.2
    assert metrics.max_wait_time == 0.3
    
    # Test close connection
    metrics.record_connection_closed("conn1")
    assert metrics.connections_closed == 1
    assert metrics.current_size == 1
    assert "conn1" not in metrics.connection_metrics
    
    # Test health check metrics
    metrics.record_health_check(True)
    metrics.record_health_check(True)
    metrics.record_health_check(False)
    
    assert metrics.health_check_count == 3
    assert metrics.health_check_failures == 1
    assert metrics.health_check_failure_rate == 1/3
    
    # Test circuit breaker metrics
    metrics.record_circuit_breaker_trip()
    assert metrics.circuit_breaker_trips == 1
    
    metrics.record_circuit_breaker_reset()
    assert metrics.circuit_breaker_resets == 1
    
    # Test summary
    summary = metrics.get_summary()
    assert "size" in summary
    assert "health" in summary
    assert "performance" in summary
    assert summary["size"]["current"] == 1
    assert summary["health"]["validation_failures"] == 0
    assert "uptime" in summary


# Test connection pool
@pytest.mark.asyncio
async def test_enhanced_connection_pool():
    """Test EnhancedConnectionPool class."""
    # Create mock functions
    factory = AsyncMock(return_value="connection")
    close_func = AsyncMock()
    validate_func = AsyncMock(return_value=True)
    reset_func = AsyncMock()
    
    # Create resource registry mock
    resource_registry = MagicMock()
    resource_registry.register = AsyncMock()
    
    # Create config with small values for testing
    config = ConnectionPoolConfig(
        initial_size=2,
        min_size=1,
        max_size=3,
        idle_timeout=1.0,
        max_lifetime=5.0,
        validation_interval=1.0,
        health_check_interval=1.0,
        stats_emit_interval=1.0,
    )
    
    # Create pool
    pool = EnhancedConnectionPool(
        name="test_pool",
        factory=factory,
        close_func=close_func,
        validate_func=validate_func,
        reset_func=reset_func,
        config=config,
        resource_registry=resource_registry,
    )
    
    # Start the pool
    await pool.start()
    
    # Verify resource registry registration
    resource_registry.register.assert_awaited()
    
    # Verify factory called for initial connections
    assert factory.await_count == 2
    
    # Verify pool metrics
    assert pool.metrics.connections_created == 2
    assert pool.metrics.current_size == 2
    assert len(pool._connections) == 2
    assert len(pool._available_conn_ids) == 2
    
    # Test acquire connection
    conn_id, connection = await pool.acquire()
    
    assert connection == "connection"
    assert conn_id in pool._connections
    assert conn_id not in pool._available_conn_ids
    assert pool._connections[conn_id]["in_use"] == True
    assert pool.metrics.active_connections == 1
    
    # Test release connection
    await pool.release(conn_id)
    
    assert conn_id in pool._available_conn_ids
    assert pool._connections[conn_id]["in_use"] == False
    assert pool.metrics.active_connections == 0
    
    # Test context manager
    async with pool.connection() as conn:
        assert conn == "connection"
        # Pool should have one active connection
        assert pool.metrics.active_connections == 1
    
    # After context manager, connection should be released
    assert pool.metrics.active_connections == 0
    
    # Test clear pool
    await pool.clear()
    
    assert len(pool._connections) == 2  # Reset to initial size
    assert close_func.await_count >= 2  # Should have closed all connections
    
    # Test close pool
    await pool.close()
    
    assert pool._closed == True
    assert close_func.await_count >= 4  # Should have closed all connections


# Test engine pool
@pytest.mark.asyncio
async def test_enhanced_async_engine_pool():
    """Test EnhancedAsyncEnginePool class."""
    # Create mock AsyncEngine factory
    with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine:
        mock_engine = MockEngine()
        mock_create_engine.return_value = mock_engine
        
        # Create connection config
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_user_pw="password",
            db_driver="postgresql+asyncpg",
        )
        
        # Create pool config
        pool_config = ConnectionPoolConfig(
            initial_size=1,
            min_size=1,
            max_size=2,
        )
        
        # Create resource registry mock
        resource_registry = MagicMock()
        resource_registry.register = AsyncMock()
        
        # Create engine pool
        engine_pool = EnhancedAsyncEnginePool(
            name="test_engine_pool",
            config=config,
            pool_config=pool_config,
            resource_registry=resource_registry,
        )
        
        # Start the pool
        await engine_pool.start()
        
        # Verify engine created
        mock_create_engine.assert_called_once()
        
        # Acquire engine
        engine = await engine_pool.acquire()
        
        assert engine is mock_engine
        
        # Release engine
        await engine_pool.release(engine)
        
        # Test context manager
        async with engine_pool.engine() as engine:
            assert engine is mock_engine
        
        # Close pool
        await engine_pool.close()


# Test connection manager
@pytest.mark.asyncio
async def test_enhanced_async_connection_manager():
    """Test EnhancedAsyncConnectionManager class."""
    # Create mock AsyncEngine factory
    with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine:
        mock_engine = MockEngine()
        mock_connection = MockConnection(mock_engine)
        mock_engine.connect = AsyncMock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        # Create connection config
        config = ConnectionConfig(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_user_pw="password",
            db_driver="postgresql+asyncpg",
        )
        
        # Create resource registry mock
        resource_registry = MagicMock()
        resource_registry.register = AsyncMock()
        
        # Create connection manager
        manager = EnhancedAsyncConnectionManager(
            resource_registry=resource_registry,
        )
        
        # Configure pool
        pool_config = ConnectionPoolConfig(
            initial_size=1,
            min_size=1,
            max_size=2,
        )
        manager.configure_pool(
            role="test_role",
            config=pool_config,
        )
        
        # Get engine pool
        engine_pool = await manager.get_engine_pool(config)
        
        assert engine_pool.name == "test_role@localhost/test_db"
        assert engine_pool.config is config
        
        # Should cache the pool
        engine_pool2 = await manager.get_engine_pool(config)
        assert engine_pool2 is engine_pool
        
        # Test engine context manager
        async with manager.engine(config) as engine:
            assert engine is mock_engine
        
        # Test connection context manager
        async with manager.connection(config) as connection:
            assert connection is mock_connection
            mock_connection.execution_options.assert_awaited_once()
        
        # Close manager
        await manager.close()
        
        # Verify metrics collection
        metrics = manager.get_metrics()
        assert "test_role@localhost/test_db" in metrics


# Test global connection manager functions
@pytest.mark.asyncio
async def test_global_connection_manager():
    """Test global connection manager functions."""
    # Create mock AsyncEngine factory
    with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine:
        mock_engine = MockEngine()
        mock_connection = MockConnection(mock_engine)
        mock_engine.connect = AsyncMock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        # Get global connection manager
        manager1 = get_connection_manager()
        manager2 = get_connection_manager()
        
        # Verify singleton
        assert manager1 is manager2
        
        # Test enhanced_async_engine
        async with enhanced_async_engine(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_user_pw="password",
            db_driver="postgresql+asyncpg",
        ) as engine:
            assert engine is mock_engine
        
        # Test enhanced_async_connection
        async with enhanced_async_connection(
            db_role="test_role",
            db_name="test_db",
            db_host="localhost",
            db_user_pw="password",
            db_driver="postgresql+asyncpg",
        ) as connection:
            assert connection is mock_connection
        
        # Close manager for cleanup
        await manager1.close()