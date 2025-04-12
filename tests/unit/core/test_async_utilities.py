"""
Tests for the core async utilities.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

from uno.core.async import (
    TaskManager,
    TaskGroup,
    AsyncLock,
    AsyncSemaphore,
    AsyncEvent,
    Limiter,
    RateLimiter,
    timeout,
    AsyncContextGroup,
    AsyncExitStack,
)
from uno.core.async_integration import (
    cancellable,
    timeout_handler,
    retry,
    rate_limited,
    concurrent_limited,
    AsyncBatcher,
    AsyncCache,
)
from uno.core.async_manager import (
    AsyncManager,
    get_async_manager,
    as_task,
    run_application,
)


@pytest.mark.asyncio
async def test_task_group():
    """Test the TaskGroup class."""
    # Create a task group
    group = TaskGroup(name="test_group")
    
    # Test context manager
    async with group:
        # Create some tasks
        task1 = group.create_task(asyncio.sleep(0.01, result=1), name="task1")
        task2 = group.create_task(asyncio.sleep(0.02, result=2), name="task2")
        
        # Verify tasks were created
        assert len(group.tasks) == 2
        assert task1 in group.tasks
        assert task2 in group.tasks
        
        # Wait for tasks to complete
        results = []
        for task in [task1, task2]:
            result = await task
            results.append(result)
        
        # Verify results
        assert 1 in results
        assert 2 in results
    
    # Verify tasks are done
    for task in group.tasks:
        assert task.done()


@pytest.mark.asyncio
async def test_task_group_error_handling():
    """Test TaskGroup error handling."""
    # Create a task group
    group = TaskGroup(name="test_group", cancel_on_error=True)
    
    # Define tasks
    async def success_task():
        await asyncio.sleep(0.05)
        return "success"
    
    async def error_task():
        await asyncio.sleep(0.01)
        raise ValueError("Task error")
    
    # Use the group
    with pytest.raises(ValueError, match="Task error"):
        async with group:
            # Create tasks
            task1 = group.create_task(success_task(), name="success")
            task2 = group.create_task(error_task(), name="error")
            
            # Wait for tasks
            await asyncio.gather(*group.tasks, return_exceptions=True)
    
    # Verify all tasks are done
    assert all(task.done() for task in group.tasks)
    
    # Verify the success task was cancelled
    assert task1.cancelled()


@pytest.mark.asyncio
async def test_async_lock():
    """Test the AsyncLock class."""
    # Create a lock
    lock = AsyncLock(name="test_lock")
    
    # Test acquiring the lock
    async with lock:
        # Lock should be acquired
        assert lock.locked()
        
        # Try to acquire it again (should work because it's reentrant)
        async with lock:
            assert lock.locked()
            assert lock._depth == 2  # Acquired twice
        
        # Depth should be decremented
        assert lock._depth == 1
    
    # Lock should be released
    assert not lock.locked()
    assert lock._depth == 0
    assert lock._owner is None


@pytest.mark.asyncio
async def test_async_semaphore():
    """Test the AsyncSemaphore class."""
    # Create a semaphore with 2 permits
    sem = AsyncSemaphore(value=2, name="test_sem")
    
    # Test acquiring the semaphore
    async with sem:
        # Semaphore should have one permit left
        assert sem._value == 1
        
        # Acquire again
        async with sem:
            # No permits left
            assert sem._value == 0
            
            # Create a task that will wait for a permit
            async def wait_for_permit():
                async with sem:
                    return "acquired"
            
            # Start the task
            task = asyncio.create_task(wait_for_permit())
            
            # Wait a bit, task should be waiting
            await asyncio.sleep(0.01)
            assert not task.done()
        
        # After releasing one permit, the task should complete
        await asyncio.sleep(0.01)
        assert task.done()
        assert await task == "acquired"
    
    # Semaphore should be fully released
    assert sem._value == 2


@pytest.mark.asyncio
async def test_limiter():
    """Test the Limiter class."""
    # Create a limiter with 2 concurrent operations
    limiter = Limiter(max_concurrent=2, name="test_limiter")
    
    # Test acquiring the limiter
    async with limiter:
        # Should have one permit left
        assert limiter._semaphore._value == 1
        
        # Acquire again
        async with limiter:
            # No permits left
            assert limiter._semaphore._value == 0
            
            # Create a task that will wait for a permit
            async def wait_for_permit():
                async with limiter:
                    return "acquired"
            
            # Start the task
            task = asyncio.create_task(wait_for_permit())
            
            # Wait a bit, task should be waiting
            await asyncio.sleep(0.01)
            assert not task.done()
        
        # After releasing one permit, the task should complete
        await asyncio.sleep(0.01)
        assert task.done()
        assert await task == "acquired"
    
    # Limiter should be fully released
    assert limiter._semaphore._value == 2
    
    # Test waiting with timeout
    with pytest.raises(asyncio.TimeoutError):
        async with limiter:
            async with limiter:
                # No permits left
                
                # Try to acquire with timeout
                async with timeout(0.05, "Timeout waiting for limiter"):
                    async with limiter:
                        assert False, "Should not reach here"


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test the RateLimiter class."""
    # Create a rate limiter with 10 ops/second
    limiter = RateLimiter(operations_per_second=10, name="test_limiter")
    
    # Test acquiring the limiter multiple times
    start_time = time.time()
    
    # Acquire 5 times quickly
    for _ in range(5):
        async with limiter:
            pass
    
    # Shouldn't have taken much time
    assert time.time() - start_time < 0.1
    
    # Now try to acquire 10 more times
    for _ in range(10):
        async with limiter:
            pass
    
    # Should have taken at least 0.5 seconds due to rate limiting
    assert time.time() - start_time >= 0.5


@pytest.mark.asyncio
async def test_timeout_context():
    """Test the timeout context manager."""
    # Test successful completion within timeout
    async with timeout(1.0, "Test timeout"):
        await asyncio.sleep(0.01)
    
    # Test timeout
    with pytest.raises(asyncio.TimeoutError, match="Test timeout"):
        async with timeout(0.05, "Test timeout"):
            await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_async_context_group():
    """Test the AsyncContextGroup class."""
    # Create mock context managers
    ctx1 = AsyncMock()
    ctx1.__aenter__.return_value = "result1"
    ctx2 = AsyncMock()
    ctx2.__aenter__.return_value = "result2"
    
    # Create a context group
    group = AsyncContextGroup()
    
    # Use the group
    async with group:
        # Add contexts
        result1 = await group.enter_async_context(ctx1)
        result2 = await group.enter_async_context(ctx2)
        
        # Verify results
        assert result1 == "result1"
        assert result2 == "result2"
    
    # Verify contexts were exited in reverse order
    ctx2.__aexit__.assert_called_once()
    ctx1.__aexit__.assert_called_once()
    
    # Check the order of calls
    assert ctx2.__aexit__.call_count >= 1
    assert ctx1.__aexit__.call_count >= 1


@pytest.mark.asyncio
async def test_cancellable_decorator():
    """Test the cancellable decorator."""
    called = False
    
    @cancellable
    async def cancelable_func():
        nonlocal called
        try:
            await asyncio.sleep(0.1)
            return "completed"
        except asyncio.CancelledError:
            called = True
            raise
    
    # Start the function
    task = asyncio.create_task(cancelable_func())
    
    # Cancel it
    await asyncio.sleep(0.01)
    task.cancel()
    
    # Wait for it to complete (should raise CancelledError)
    with pytest.raises(asyncio.CancelledError):
        await task
    
    # Verify the except block was executed
    assert called


@pytest.mark.asyncio
async def test_timeout_handler_decorator():
    """Test the timeout_handler decorator."""
    # Define a function with timeout
    @timeout_handler(timeout_seconds=0.05, timeout_message="Function timed out")
    async def slow_function():
        await asyncio.sleep(0.1)
        return "completed"
    
    # Test timeout
    with pytest.raises(asyncio.TimeoutError, match="Function timed out"):
        await slow_function()
    
    # Define a function that completes in time
    @timeout_handler(timeout_seconds=0.1)
    async def fast_function():
        await asyncio.sleep(0.01)
        return "completed"
    
    # Test successful completion
    result = await fast_function()
    assert result == "completed"


@pytest.mark.asyncio
async def test_retry_decorator():
    """Test the retry decorator."""
    attempts = 0
    
    # Define a function that fails the first 2 times
    @retry(max_attempts=3, base_delay=0.01)
    async def flaky_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError(f"Attempt {attempts} failed")
        return "success"
    
    # Call the function
    result = await flaky_function()
    
    # Verify it was retried and succeeded
    assert attempts == 3
    assert result == "success"
    
    # Define a function that always fails
    @retry(max_attempts=2, base_delay=0.01)
    async def always_fails():
        raise ValueError("Always fails")
    
    # Test that it gives up after max attempts
    with pytest.raises(ValueError, match="Always fails"):
        await always_fails()


@pytest.mark.asyncio
async def test_rate_limited_decorator():
    """Test the rate_limited decorator."""
    # Define a rate-limited function
    @rate_limited(operations_per_second=10)
    async def limited_function():
        return "done"
    
    # Call it multiple times and measure the time
    start_time = time.time()
    
    for _ in range(15):
        await limited_function()
    
    # Should have taken at least 0.5 seconds due to rate limiting
    assert time.time() - start_time >= 0.5


@pytest.mark.asyncio
async def test_concurrent_limited_decorator():
    """Test the concurrent_limited decorator."""
    # Track concurrent executions
    active = 0
    max_active = 0
    
    # Define a function with concurrency limit
    @concurrent_limited(max_concurrent=2)
    async def limited_function():
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.05)
        active -= 1
        return "done"
    
    # Run multiple tasks concurrently
    tasks = [asyncio.create_task(limited_function()) for _ in range(5)]
    
    # Wait for all tasks
    await asyncio.gather(*tasks)
    
    # Verify max concurrency was respected
    assert max_active == 2


@pytest.mark.asyncio
async def test_async_batcher():
    """Test the AsyncBatcher class."""
    # Define a batch operation
    async def batch_operation(items):
        await asyncio.sleep(0.01)  # Simulate processing
        return [f"processed_{item}" for item in items]
    
    # Create a batcher
    batcher = AsyncBatcher(
        batch_operation=batch_operation,
        max_batch_size=3,
        max_wait_time=0.1
    )
    
    # Add items concurrently
    async def add_item(item):
        return await batcher.add_item(item)
    
    # Create tasks
    tasks = [asyncio.create_task(add_item(i)) for i in range(5)]
    
    # Wait for all tasks
    results = await asyncio.gather(*tasks)
    
    # Verify results
    for i, result in enumerate(results):
        assert result == f"processed_{i}"
    
    # Shutdown the batcher
    await batcher.shutdown()


@pytest.mark.asyncio
async def test_async_cache():
    """Test the AsyncCache class."""
    fetch_count = 0
    
    # Define a fetch function
    async def fetch_func(key):
        nonlocal fetch_count
        fetch_count += 1
        await asyncio.sleep(0.01)  # Simulate fetch
        return f"value_{key}"
    
    # Create a cache with 0.1s TTL
    cache = AsyncCache(ttl=0.1)
    
    # Get a value (should fetch)
    result1 = await cache.get("key1", fetch_func)
    assert result1 == "value_key1"
    assert fetch_count == 1
    
    # Get the same value again (should use cache)
    result2 = await cache.get("key1", fetch_func)
    assert result2 == "value_key1"
    assert fetch_count == 1  # No additional fetch
    
    # Wait for TTL to expire
    await asyncio.sleep(0.15)
    
    # Get the value again (should fetch again)
    result3 = await cache.get("key1", fetch_func)
    assert result3 == "value_key1"
    assert fetch_count == 2  # Fetched again
    
    # Test invalidation
    await cache.invalidate("key1")
    
    # Get the value again (should fetch again)
    result4 = await cache.get("key1", fetch_func)
    assert result4 == "value_key1"
    assert fetch_count == 3  # Fetched again
    
    # Clear the cache
    await cache.clear()


@pytest.mark.asyncio
async def test_async_manager():
    """Test the AsyncManager class."""
    # Get the singleton instance
    manager = get_async_manager()
    
    # Verify it's the same instance
    assert manager is AsyncManager._instance
    
    # Test starting the manager
    await manager.start()
    assert manager._started
    assert manager._start_time is not None
    
    # Test creating a task
    task = manager.create_task(asyncio.sleep(0.01), name="test_task")
    await task
    
    # Test registering a resource
    resource = AsyncMock()
    await manager.register_resource(resource, name="test_resource")
    
    # Test unregistering a resource
    await manager.unregister_resource(resource, name="test_resource")
    
    # Test task group context manager
    async with manager.task_group("test_group") as group:
        assert isinstance(group, TaskGroup)
        task = group.create_task(asyncio.sleep(0.01), name="group_task")
        await task
    
    # Test shutdown
    await manager.shutdown()
    assert manager._shutdown_initiated
    assert manager._shutdown_complete
    assert manager._shutdown_time is not None
    
    # Reset the singleton for other tests
    AsyncManager._instance = None


@pytest.mark.asyncio
async def test_as_task_decorator():
    """Test the as_task decorator."""
    # Mock the async manager
    mock_manager = AsyncMock()
    mock_task = MagicMock()
    mock_manager.create_task.return_value = mock_task
    
    # Patch the get_async_manager function
    with patch("uno.core.async_manager.get_async_manager", return_value=mock_manager):
        # Define a function with the decorator
        @as_task("test_task")
        async def decorated_func(arg, kwarg=None):
            return f"{arg}_{kwarg}"
        
        # Call the function
        result = decorated_func("arg1", kwarg="kwarg1")
        
        # Verify it returned the task
        assert result == mock_task
        
        # Verify create_task was called
        mock_manager.create_task.assert_called_once()
        args, kwargs = mock_manager.create_task.call_args
        assert kwargs["name"] == "test_task"


@pytest.mark.asyncio
async def test_run_application():
    """Test the run_application function."""
    # Mock the async manager
    mock_manager = AsyncMock()
    
    # Define startup and cleanup functions
    startup_called = False
    cleanup_called = False
    
    async def startup():
        nonlocal startup_called
        startup_called = True
    
    async def cleanup():
        nonlocal cleanup_called
        cleanup_called = True
    
    # Patch the get_async_manager function
    with patch("uno.core.async_manager.get_async_manager", return_value=mock_manager):
        # Call run_application
        task = asyncio.create_task(
            run_application(startup_func=startup, cleanup_func=cleanup)
        )
        
        # Wait a bit
        await asyncio.sleep(0.01)
        
        # Verify startup was called
        assert startup_called
        
        # Verify methods were called on the manager
        mock_manager.add_startup_hook.assert_called_once_with(startup)
        mock_manager.add_shutdown_hook.assert_called_once_with(cleanup)
        mock_manager.start.assert_called_once()
        mock_manager.wait_for_shutdown.assert_called_once()
        
        # Cancel the task
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task