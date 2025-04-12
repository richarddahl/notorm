"""
Tests for the resource management components.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from uno.core.resources import (
    ResourceRegistry,
    ConnectionPool,
    CircuitBreaker,
    BackgroundTask,
    get_resource_registry,
)
from uno.core.resource_monitor import (
    ResourceMonitor,
    ResourceHealth,
    ResourceType,
    get_resource_monitor,
)
from uno.core.resource_management import (
    ResourceManager,
    get_resource_manager,
    managed_connection_pool,
    managed_background_task,
)


class TestResourceRegistry:
    """Tests for the ResourceRegistry class."""

    @pytest.mark.asyncio
    async def test_register_and_get(self):
        """Test registering and getting a resource."""
        registry = ResourceRegistry()
        resource = {"test": "resource"}
        
        # Register the resource
        await registry.register("test", resource)
        
        # Get the resource
        result = await registry.get("test")
        
        # Verify
        assert result is resource
        assert "test" in registry.get_all_resources()
    
    @pytest.mark.asyncio
    async def test_unregister(self):
        """Test unregistering a resource."""
        registry = ResourceRegistry()
        resource = {"test": "resource"}
        
        # Register the resource
        await registry.register("test", resource)
        
        # Unregister the resource
        await registry.unregister("test")
        
        # Verify
        assert "test" not in registry.get_all_resources()
        
        # Trying to get the resource should raise ValueError
        with pytest.raises(ValueError):
            await registry.get("test")
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing all resources."""
        registry = ResourceRegistry()
        
        # Create mock resources with close methods
        resource1 = AsyncMock()
        resource2 = AsyncMock()
        
        # Register the resources
        await registry.register("test1", resource1)
        await registry.register("test2", resource2)
        
        # Close the registry
        await registry.close()
        
        # Verify
        resource1.close.assert_called_once()
        resource2.close.assert_called_once()
        assert not registry.get_all_resources()
    
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting resource metrics."""
        registry = ResourceRegistry()
        
        # Create a resource with a get_metrics method
        resource = AsyncMock()
        resource.get_metrics.return_value = {"test": "metrics"}
        
        # Register the resource
        await registry.register("test", resource)
        
        # Get metrics
        metrics = registry.get_metrics()
        
        # Verify
        assert "test" in metrics
        assert metrics["test"] == {"test": "metrics"}


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed(self):
        """Test circuit breaker in closed state."""
        # Create a circuit breaker
        circuit = CircuitBreaker(
            name="test",
            failure_threshold=3,
        )
        
        # Verify initial state
        assert circuit.state.name == "CLOSED"
        
        # Create a mock function
        mock_func = AsyncMock(return_value="success")
        
        # Call the function through the circuit breaker
        result = await circuit(mock_func, "arg", kwarg="value")
        
        # Verify
        assert result == "success"
        mock_func.assert_called_once_with("arg", kwarg="value")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open(self):
        """Test circuit breaker in open state."""
        # Create a circuit breaker with a low threshold
        circuit = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.2,  # Short timeout for testing
        )
        
        # Create a mock function that raises an exception
        mock_func = AsyncMock(side_effect=ValueError("test error"))
        
        # Call the function through the circuit breaker
        # It should fail the first time
        with pytest.raises(ValueError):
            await circuit(mock_func)
        
        # Call again to hit the threshold
        with pytest.raises(ValueError):
            await circuit(mock_func)
        
        # Verify circuit is open
        assert circuit.state.name == "OPEN"
        
        # Call again - should raise CircuitBreakerOpenError
        from uno.core.resources import CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await circuit(mock_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(0.3)
        
        # Now in half-open state, should try again
        mock_func.reset_mock()
        mock_func.return_value = "success"  # Make it succeed this time
        
        # Call should work now
        result = await circuit(mock_func)
        
        # Verify
        assert result == "success"
        mock_func.assert_called_once()
        
        # Circuit should be closed again after successful call
        assert circuit.state.name == "CLOSED"


class TestConnectionPool:
    """Tests for the ConnectionPool class."""

    @pytest.mark.asyncio
    async def test_connection_pool(self):
        """Test connection pool functionality."""
        # Create mock functions
        mock_factory = AsyncMock(return_value={"id": 1})
        mock_close = AsyncMock()
        mock_validate = AsyncMock(return_value=True)
        
        # Create a connection pool
        pool = ConnectionPool(
            name="test",
            factory=mock_factory,
            close_func=mock_close,
            validate_func=mock_validate,
            max_size=3,
            min_size=1,
        )
        
        # Start the pool
        await pool.start()
        
        # Verify min_size connections were created
        assert mock_factory.call_count == 1
        
        # Acquire a connection
        conn = await pool.acquire()
        
        # Verify
        assert conn == {"id": 1}
        
        # Release the connection
        await pool.release(conn)
        
        # Acquire again - should reuse the connection
        mock_factory.reset_mock()
        conn2 = await pool.acquire()
        
        # Verify factory not called again
        assert mock_factory.call_count == 0
        
        # Close the pool
        await pool.close()
        
        # Verify close called for all connections
        assert mock_close.call_count == 1
    
    @pytest.mark.asyncio
    async def test_connection_pool_validation(self):
        """Test connection pool validation."""
        # Create mock functions
        mock_factory = AsyncMock(side_effect=[{"id": 1}, {"id": 2}])
        mock_close = AsyncMock()
        mock_validate = AsyncMock(side_effect=[False, True])  # First validation fails
        
        # Create a connection pool
        pool = ConnectionPool(
            name="test",
            factory=mock_factory,
            close_func=mock_close,
            validate_func=mock_validate,
            max_size=3,
            min_size=1,
            validation_interval=0.1,  # Short interval for testing
        )
        
        # Start the pool
        await pool.start()
        
        # Wait for validation
        await asyncio.sleep(0.2)
        
        # Acquire a connection - should get a new one since first failed validation
        conn = await pool.acquire()
        
        # Verify
        assert conn == {"id": 2}
        assert mock_factory.call_count == 2
        assert mock_close.call_count == 1  # First connection was closed due to failed validation
        
        # Close the pool
        await pool.close()


class TestBackgroundTask:
    """Tests for the BackgroundTask class."""

    @pytest.mark.asyncio
    async def test_background_task(self):
        """Test background task functionality."""
        # Create a mock coroutine
        mock_coro = AsyncMock()
        
        # Create a background task
        task = BackgroundTask(
            coro=mock_coro,
            name="test_task",
        )
        
        # Start the task
        await task.start()
        
        # Verify task is running
        assert task.is_running()
        
        # Wait a bit for the task to run
        await asyncio.sleep(0.1)
        
        # Verify coro was called
        mock_coro.assert_called_once()
        
        # Stop the task
        await task.stop()
        
        # Verify task is stopped
        assert not task.is_running()
    
    @pytest.mark.asyncio
    async def test_background_task_restart(self):
        """Test background task restart functionality."""
        # Create a coroutine that raises an exception
        call_count = 0
        
        async def failing_coro():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("test error")
            await asyncio.sleep(0.1)
        
        # Create a background task with restart
        task = BackgroundTask(
            coro=failing_coro,
            name="test_task",
            restart_on_failure=True,
            max_restarts=1,
            restart_delay=0.1,
        )
        
        # Start the task
        await task.start()
        
        # Wait for restart to happen
        await asyncio.sleep(0.4)
        
        # Verify called twice (initial + 1 restart)
        assert call_count == 2
        
        # Stop the task
        await task.stop()


class TestResourceManager:
    """Tests for the ResourceManager class."""

    @pytest.mark.asyncio
    async def test_singleton(self):
        """Test ResourceManager is a singleton."""
        # Get instance
        manager1 = get_resource_manager()
        
        # Get again
        manager2 = get_resource_manager()
        
        # Verify
        assert manager1 is manager2
        
        # Try to create directly
        with pytest.raises(RuntimeError):
            ResourceManager()
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test initializing the resource manager."""
        # Mock dependencies
        with patch("uno.core.resource_management.get_async_manager") as mock_async_manager, \
             patch("uno.core.resource_management.get_resource_registry") as mock_registry:
            
            # Set up mocks
            mock_registry.return_value = AsyncMock()
            
            # Get resource manager
            manager = ResourceManager(logger=MagicMock())
            
            # Initialize
            await manager.initialize()
            
            # Verify
            assert manager._initialized
            mock_async_manager.return_value.add_startup_hook.assert_called_once()
            mock_async_manager.return_value.add_shutdown_hook.assert_called_once()
            mock_registry.return_value.register.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_managers(self):
        """Test resource context managers."""
        # Mock resources
        mock_pool = AsyncMock()
        mock_pool_factory = AsyncMock(return_value=mock_pool)
        
        mock_task = AsyncMock()
        mock_task_coro = AsyncMock()
        
        # Mock registry
        with patch("uno.core.resource_management.get_resource_registry") as mock_registry:
            mock_registry.return_value = AsyncMock()
            
            # Test managed_connection_pool
            async with managed_connection_pool("test_pool", mock_pool_factory) as pool:
                assert pool is mock_pool
                mock_pool.start.assert_called_once()
                mock_registry.return_value.register.assert_called_once_with("test_pool", mock_pool)
            
            # Verify cleanup
            mock_pool.close.assert_called_once()
            mock_registry.return_value.unregister.assert_called_once()
            
            # Reset mocks
            mock_registry.return_value.reset_mock()
            
            # Mock BackgroundTask creation
            with patch("uno.core.resource_management.BackgroundTask") as mock_bg_task:
                mock_bg_task.return_value = mock_task
                
                # Test managed_background_task
                async with managed_background_task("test_task", mock_task_coro) as task:
                    assert task is mock_task
                    mock_task.start.assert_called_once()
                    mock_registry.return_value.register.assert_called_once_with("test_task", mock_task)
                
                # Verify cleanup
                mock_task.stop.assert_called_once()
                mock_registry.return_value.unregister.assert_called_once()