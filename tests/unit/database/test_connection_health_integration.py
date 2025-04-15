"""
Unit tests for the connection health monitoring integration.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

from uno.database.connection_health import (
    ConnectionHealthState,
    ConnectionHealthMonitor,
    ConnectionRecycler,
    ConnectionIssue,
    ConnectionIssueType,
)
from uno.database.connection_health_integration import (
    HealthAwareConnectionPool,
    HealthAwareAsyncEnginePool,
    HealthAwareAsyncConnectionManager,
    _ConnectionWrapper,
    get_health_aware_connection_manager,
)


class TestHealthAwareConnectionPool:
    @pytest.fixture
    async def mock_connection(self):
        """Create a mock connection."""
        connection = AsyncMock()
        return connection
    
    @pytest.fixture
    def mock_factory(self, mock_connection):
        """Create a mock connection factory."""
        async def factory():
            return mock_connection
        return factory
    
    @pytest.fixture
    def mock_close_func(self):
        """Create a mock close function."""
        async def close_func(conn):
            pass
        return close_func
    
    @pytest.fixture
    def mock_validate_func(self):
        """Create a mock validation function."""
        async def validate_func(conn):
            return True
        return validate_func
    
    @pytest.fixture
    def mock_reset_func(self):
        """Create a mock reset function."""
        async def reset_func(conn):
            pass
        return reset_func
    
    @pytest.fixture
    async def health_aware_pool(self, mock_factory, mock_close_func, mock_validate_func, mock_reset_func):
        """Create a health aware connection pool."""
        pool = HealthAwareConnectionPool(
            name="test_pool",
            factory=mock_factory,
            close_func=mock_close_func,
            validate_func=mock_validate_func,
            reset_func=mock_reset_func,
        )
        
        # Mock the health monitoring setup
        pool._setup_health_monitoring = AsyncMock()
        
        # Start the pool
        await pool.start()
        
        yield pool
        
        # Close the pool
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_pool_initialization(self, health_aware_pool):
        """Test that the pool is initialized correctly."""
        assert health_aware_pool.name == "test_pool"
        assert health_aware_pool._health_check_interval == 60.0
        assert health_aware_pool._recycling_interval == 300.0
        assert isinstance(health_aware_pool._health_states, dict)
        assert health_aware_pool._setup_health_monitoring.called
    
    @pytest.mark.asyncio
    async def test_handle_health_change(self, health_aware_pool):
        """Test handling of health state changes."""
        # Mock recycler
        health_aware_pool._connection_recycler = AsyncMock()
        
        # Call the handler
        await health_aware_pool._handle_health_change(
            "conn1",
            ConnectionHealthState.HEALTHY,
            ConnectionHealthState.UNHEALTHY
        )
        
        # Check that the state was updated
        assert health_aware_pool._health_states["conn1"] == ConnectionHealthState.UNHEALTHY
        
        # Check that the recycler was called
        assert health_aware_pool._connection_recycler.mark_for_recycling.called
    
    @pytest.mark.asyncio
    async def test_handle_issue_detected(self, health_aware_pool):
        """Test handling of issue detection."""
        # Mock recycler
        health_aware_pool._connection_recycler = AsyncMock()
        
        # Create a high severity issue
        issue = ConnectionIssue(
            connection_id="conn1",
            issue_type=ConnectionIssueType.ERRORS,
            severity=0.8,
            description="High error rate",
        )
        
        # Call the handler
        await health_aware_pool._handle_issue_detected("conn1", issue)
        
        # Check that the recycler was called
        assert health_aware_pool._connection_recycler.mark_for_recycling.called
        
        # Test with a low severity issue
        issue = ConnectionIssue(
            connection_id="conn1",
            issue_type=ConnectionIssueType.LATENCY,
            severity=0.3,
            description="Slightly elevated latency",
        )
        
        # Reset the mock
        health_aware_pool._connection_recycler.mark_for_recycling.reset_mock()
        
        # Call the handler
        await health_aware_pool._handle_issue_detected("conn1", issue)
        
        # Check that the recycler was not called
        assert not health_aware_pool._connection_recycler.mark_for_recycling.called
    
    @pytest.mark.asyncio
    async def test_handle_connection_recycling_not_found(self, health_aware_pool):
        """Test handling of connection recycling when the connection is not found."""
        # Call the handler
        await health_aware_pool._handle_connection_recycling("nonexistent", "test reason")
        
        # Nothing happens, no exceptions
    
    @pytest.mark.asyncio
    async def test_handle_connection_recycling_in_use(self, health_aware_pool):
        """Test handling of connection recycling when the connection is in use."""
        # Add a connection in use
        health_aware_pool._connections = {
            "conn1": {
                "in_use": True,
                "connection": AsyncMock(),
                "created_at": time.time(),
                "last_used": time.time(),
                "last_validated": time.time(),
            }
        }
        
        # Call the handler
        await health_aware_pool._handle_connection_recycling("conn1", "test reason")
        
        # Check that the connection was marked for recycling on release
        assert health_aware_pool._connections["conn1"]["recycle_on_release"] is True
    
    @pytest.mark.asyncio
    async def test_handle_connection_recycling_available(self, health_aware_pool):
        """Test handling of connection recycling when the connection is available."""
        # Mock needed methods
        health_aware_pool._close_connection = AsyncMock()
        health_aware_pool._add_connection = AsyncMock()
        
        # Add an available connection
        health_aware_pool._connections = {
            "conn1": {
                "in_use": False,
                "connection": AsyncMock(),
                "created_at": time.time(),
                "last_used": time.time(),
                "last_validated": time.time(),
            }
        }
        health_aware_pool._available_conn_ids = {"conn1"}
        
        # Call the handler
        await health_aware_pool._handle_connection_recycling("conn1", "test reason")
        
        # Check that the connection was removed from available set
        assert "conn1" not in health_aware_pool._available_conn_ids
        
        # Check that the connection was closed and a new one was added
        assert health_aware_pool._close_connection.called
        assert health_aware_pool._add_connection.called
    
    @pytest.mark.asyncio
    async def test_release_with_recycling(self, health_aware_pool):
        """Test connection release with recycling."""
        # Mock needed methods
        health_aware_pool._close_connection = AsyncMock()
        health_aware_pool._add_connection = AsyncMock()
        
        # Add a connection marked for recycling
        health_aware_pool._connections = {
            "conn1": {
                "in_use": True,
                "connection": AsyncMock(),
                "created_at": time.time(),
                "last_used": time.time(),
                "last_validated": time.time(),
                "recycle_on_release": True,
            }
        }
        
        # Call release
        await health_aware_pool.release("conn1")
        
        # Check that the connection was closed and a new one was added
        assert health_aware_pool._close_connection.called
        assert health_aware_pool._add_connection.called
    
    @pytest.mark.asyncio
    async def test_release_with_unhealthy_state(self, health_aware_pool):
        """Test connection release with unhealthy state."""
        # Mock needed methods
        health_aware_pool._close_connection = AsyncMock()
        health_aware_pool._add_connection = AsyncMock()
        
        # Add a connection with unhealthy state
        health_aware_pool._connections = {
            "conn1": {
                "in_use": True,
                "connection": AsyncMock(),
                "created_at": time.time(),
                "last_used": time.time(),
                "last_validated": time.time(),
            }
        }
        health_aware_pool._health_states = {
            "conn1": ConnectionHealthState.UNHEALTHY
        }
        
        # Call release
        await health_aware_pool.release("conn1")
        
        # Check that the connection was closed and a new one was added
        assert health_aware_pool._close_connection.called
        assert health_aware_pool._add_connection.called
    
    @pytest.mark.asyncio
    async def test_execute_with_connection(self, health_aware_pool):
        """Test executing a function with a connection."""
        # Mock health monitor
        health_aware_pool._health_monitor = AsyncMock()
        
        # Create a function to execute
        async def test_func():
            return "test result"
        
        # Call the method
        result = await health_aware_pool._execute_with_connection("conn1", test_func)
        
        # Check the result
        assert result == "test result"
        
        # Check that the query was recorded
        assert health_aware_pool._health_monitor.record_query.called
    
    @pytest.mark.asyncio
    async def test_execute_with_connection_error(self, health_aware_pool):
        """Test executing a function with a connection that raises an error."""
        # Mock health monitor
        health_aware_pool._health_monitor = AsyncMock()
        
        # Create a function that raises an error
        async def test_func():
            raise Exception("timeout error")
        
        # Call the method and expect an exception
        with pytest.raises(Exception, match="timeout error"):
            await health_aware_pool._execute_with_connection("conn1", test_func)
        
        # Check that the error was recorded
        assert health_aware_pool._health_monitor.record_error.called
        
        # Verify the error type was detected correctly
        health_aware_pool._health_monitor.record_error.assert_called_with("conn1", "timeout")
    
    @pytest.mark.asyncio
    async def test_get_health_metrics(self, health_aware_pool):
        """Test getting health metrics."""
        # Set up health states
        health_aware_pool._health_states = {
            "conn1": ConnectionHealthState.HEALTHY,
            "conn2": ConnectionHealthState.DEGRADED,
        }
        
        # Mock health monitor and recycler
        health_aware_pool._health_monitor = AsyncMock()
        health_aware_pool._health_monitor.get_metrics.return_value = {"total_checks": 10}
        
        health_aware_pool._connection_recycler = AsyncMock()
        health_aware_pool._connection_recycler.get_metrics.return_value = {"total_recycled": 5}
        
        # Get metrics
        metrics = health_aware_pool.get_health_metrics()
        
        # Check metrics
        assert "health_states" in metrics
        assert metrics["health_states"]["conn1"] == "healthy"
        assert metrics["health_states"]["conn2"] == "degraded"
        assert "monitor" in metrics
        assert metrics["monitor"]["total_checks"] == 10
        assert "recycler" in metrics
        assert metrics["recycler"]["total_recycled"] == 5


class TestConnectionWrapper:
    @pytest.mark.asyncio
    async def test_connection_wrapper(self):
        """Test the connection wrapper."""
        # Create mocks
        conn_id = "test_conn"
        connection = AsyncMock()
        pool = AsyncMock()
        
        # Create the wrapper
        wrapper = _ConnectionWrapper(conn_id, connection, pool)
        
        # Use the wrapper as a context manager
        async with wrapper as conn:
            # Check that the connection is returned
            assert conn is connection
        
        # Check that the connection was released
        pool.release.assert_called_with(conn_id)


class TestHealthAwareAsyncEnginePool:
    @pytest.fixture
    def mock_config(self):
        """Create a mock connection config."""
        config = MagicMock()
        config.db_driver = "postgresql+asyncpg"
        config.db_role = "test_role"
        config.db_user_pw = "test_password"
        config.db_host = "localhost"
        config.db_port = 5432
        config.db_name = "test_db"
        config.kwargs = {}
        return config
    
    @pytest.fixture
    def mock_pool_config(self):
        """Create a mock pool config."""
        pool_config = MagicMock()
        pool_config.connection_timeout = 10.0
        return pool_config
    
    @pytest.fixture
    async def engine_pool(self, mock_config, mock_pool_config):
        """Create a health aware async engine pool."""
        pool = HealthAwareAsyncEnginePool(
            name="test_engine_pool",
            config=mock_config,
            pool_config=mock_pool_config,
        )
        
        # Mock the internal pool
        pool.pool = AsyncMock(spec=HealthAwareConnectionPool)
        
        yield pool
        
        # Close the pool
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_initialization(self, engine_pool):
        """Test that the pool is initialized correctly."""
        assert engine_pool.name == "test_engine_pool"
        assert engine_pool._health_check_interval == 60.0
        assert engine_pool._recycling_interval == 300.0
    
    @pytest.mark.asyncio
    async def test_get_health_metrics(self, engine_pool):
        """Test getting health metrics."""
        # Setup mock return value
        engine_pool.pool.get_health_metrics.return_value = {
            "health_states": {"conn1": "healthy"}
        }
        
        # Get metrics
        metrics = engine_pool.get_health_metrics()
        
        # Check metrics
        assert metrics["health_states"]["conn1"] == "healthy"
        assert engine_pool.pool.get_health_metrics.called


class TestHealthAwareAsyncConnectionManager:
    @pytest.fixture
    def mock_config(self):
        """Create a mock connection config."""
        config = MagicMock()
        config.db_driver = "postgresql+asyncpg"
        config.db_role = "test_role"
        config.db_user_pw = "test_password"
        config.db_host = "localhost"
        config.db_port = 5432
        config.db_name = "test_db"
        config.kwargs = {}
        return config
    
    @pytest.fixture
    def mock_pool_config(self):
        """Create a mock pool config."""
        pool_config = MagicMock()
        return pool_config
    
    @pytest.fixture
    def manager(self):
        """Create a health aware connection manager."""
        manager = HealthAwareAsyncConnectionManager()
        yield manager
    
    @pytest.mark.asyncio
    async def test_get_engine_pool(self, manager, mock_config):
        """Test getting an engine pool."""
        # Mock methods
        manager.get_pool_config = MagicMock()
        manager.get_pool_config.return_value = MagicMock()
        
        # Patch HealthAwareAsyncEnginePool
        with patch('uno.database.connection_health_integration.HealthAwareAsyncEnginePool') as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool
            
            # Get the pool
            pool = await manager.get_engine_pool(mock_config)
            
            # Check that the pool was created and started
            assert pool is mock_pool
            assert mock_pool.start.called
            
            # Check that the pool was stored
            pool_name = f"{mock_config.db_role}@{mock_config.db_host}/{mock_config.db_name}"
            assert manager._engine_pools[pool_name] is mock_pool
    
    def test_get_health_metrics(self, manager):
        """Test getting health metrics."""
        # Setup mock pools
        pool1 = MagicMock()
        pool1.get_health_metrics.return_value = {"health_states": {"conn1": "healthy"}}
        
        pool2 = MagicMock()
        pool2.get_health_metrics.return_value = {"health_states": {"conn2": "degraded"}}
        
        manager._engine_pools = {
            "pool1": pool1,
            "pool2": pool2,
        }
        
        # Get metrics
        metrics = manager.get_health_metrics()
        
        # Check metrics
        assert "pool1" in metrics
        assert "pool2" in metrics
        assert metrics["pool1"]["health_states"]["conn1"] == "healthy"
        assert metrics["pool2"]["health_states"]["conn2"] == "degraded"


def test_get_health_aware_connection_manager():
    """Test the get_health_aware_connection_manager function."""
    # Clear any existing manager
    import uno.database.connection_health_integration as module
    module._health_aware_connection_manager = None
    
    # Get the manager
    manager1 = get_health_aware_connection_manager()
    
    # Check that it's a HealthAwareAsyncConnectionManager
    assert isinstance(manager1, HealthAwareAsyncConnectionManager)
    
    # Get it again
    manager2 = get_health_aware_connection_manager()
    
    # Check that it's the same instance
    assert manager1 is manager2