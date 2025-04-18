"""
Tests for the enhanced async concurrency primitives.

This module tests the functionality of AsyncLock, AsyncSemaphore, AsyncEvent,
Limiter, RateLimiter, and other concurrency utilities.
"""

import asyncio
import logging
import pytest
import time
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from uno.core.asynchronous.concurrency import (
    AsyncLock,
    AsyncSemaphore,
    AsyncEvent,
    Limiter,
    RateLimiter,
    TimeoutError,
    timeout,
)


# =============================================================================
# Test Utilities
# =============================================================================

async def wait_and_release(lock, delay=0.1):
    """Helper to wait then release a lock."""
    await asyncio.sleep(delay)
    lock.release()


async def sleep_and_set(event, delay=0.1):
    """Helper to wait then set an event."""
    await asyncio.sleep(delay)
    event.set()


# =============================================================================
# Test Cases
# =============================================================================

class TestTimeout:
    """Tests for the timeout context manager."""
    
    @pytest.mark.asyncio
    async def test_timeout_not_reached(self):
        """Test timeout when operation completes in time."""
        # Arrange
        result = None
        
        # Act
        async with timeout(1.0, "Test operation"):
            result = "success"
            await asyncio.sleep(0.1)
        
        # Assert
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_reached(self):
        """Test timeout when operation takes too long."""
        # Arrange & Act & Assert
        with pytest.raises(TimeoutError) as exc_info:
            async with timeout(0.1, "Test operation"):
                await asyncio.sleep(0.5)
        
        # Check error details
        assert "Test operation timed out after 0.1 seconds" in str(exc_info.value)
        assert exc_info.value.operation == "Test operation"
        assert exc_info.value.timeout == 0.1
    
    @pytest.mark.asyncio
    async def test_timeout_none(self):
        """Test timeout with None value (no timeout)."""
        # Arrange
        result = None
        
        # Act
        async with timeout(None, "Test operation"):
            result = "success"
            await asyncio.sleep(0.1)
        
        # Assert
        assert result == "success"


class TestAsyncLock:
    """Tests for the AsyncLock class."""
    
    @pytest.mark.asyncio
    async def test_async_lock_acquire_release(self):
        """Test basic acquire and release functionality."""
        # Arrange
        lock = AsyncLock(name="TestLock")
        
        # Act & Assert
        assert not lock.locked()
        
        await lock.acquire()
        assert lock.locked()
        
        lock.release()
        assert not lock.locked()
    
    @pytest.mark.asyncio
    async def test_async_lock_context_manager(self):
        """Test using AsyncLock as a context manager."""
        # Arrange
        lock = AsyncLock(name="TestLock")
        
        # Act & Assert
        assert not lock.locked()
        
        async with lock:
            assert lock.locked()
        
        assert not lock.locked()
    
    @pytest.mark.asyncio
    async def test_async_lock_timeout(self):
        """Test AsyncLock with timeout."""
        # Arrange
        lock = AsyncLock(name="TestLock")
        await lock.acquire()  # Lock is now held
        
        # Act & Assert
        with pytest.raises(TimeoutError) as exc_info:
            await lock.acquire(timeout=0.1)
        
        assert f"Lock acquisition '{lock.name}' timed out after 0.1 seconds" in str(exc_info.value)
        
        # Release the lock for cleanup
        lock.release()
    
    @pytest.mark.asyncio
    async def test_async_lock_reentrant(self):
        """Test AsyncLock reentrant behavior (same task can acquire multiple times)."""
        # Arrange
        lock = AsyncLock(name="TestLock")
        
        # Act
        await lock.acquire()
        depth1 = lock._depth
        
        await lock.acquire()
        depth2 = lock._depth
        
        await lock.acquire()
        depth3 = lock._depth
        
        # Assert
        assert lock.locked()
        assert depth1 == 1
        assert depth2 == 2
        assert depth3 == 3
        
        # Release and check depths
        lock.release()
        assert lock.locked()
        assert lock._depth == 2
        
        lock.release()
        assert lock.locked()
        assert lock._depth == 1
        
        lock.release()
        assert not lock.locked()
        assert lock._depth == 0
    
    @pytest.mark.asyncio
    async def test_async_lock_owner_info(self):
        """Test AsyncLock owner information tracking."""
        # Arrange
        lock = AsyncLock(name="TestLock")
        
        # Act & Assert
        assert lock.owner_info is None
        
        await lock.acquire()
        
        # Assert owner info was captured
        info = lock.owner_info
        assert info is not None
        assert "owner" in info
        assert "locked_at" in info
        assert "depth" in info
        assert info["depth"] == 1
        
        # Release for cleanup
        lock.release()
        assert lock.owner_info is None


class TestAsyncSemaphore:
    """Tests for the AsyncSemaphore class."""
    
    @pytest.mark.asyncio
    async def test_async_semaphore_basic(self):
        """Test basic semaphore functionality."""
        # Arrange
        sem = AsyncSemaphore(value=2, name="TestSemaphore")
        
        # Act & Assert
        assert sem.value == 2
        
        await sem.acquire()
        assert sem.value == 1
        
        await sem.acquire()
        assert sem.value == 0
        
        sem.release()
        assert sem.value == 1
        
        sem.release()
        assert sem.value == 2
    
    @pytest.mark.asyncio
    async def test_async_semaphore_context_manager(self):
        """Test using AsyncSemaphore as a context manager."""
        # Arrange
        sem = AsyncSemaphore(value=2, name="TestSemaphore")
        
        # Act & Assert
        assert sem.value == 2
        
        async with sem:
            assert sem.value == 1
            
            async with sem:
                assert sem.value == 0
            
            assert sem.value == 1
        
        assert sem.value == 2
    
    @pytest.mark.asyncio
    async def test_async_semaphore_timeout(self):
        """Test AsyncSemaphore with timeout."""
        # Arrange
        sem = AsyncSemaphore(value=1, name="TestSemaphore")
        await sem.acquire()  # Semaphore is now exhausted
        
        # Act & Assert
        with pytest.raises(TimeoutError) as exc_info:
            await sem.acquire(timeout=0.1)
        
        assert f"Semaphore acquisition '{sem.name}' timed out after 0.1 seconds" in str(exc_info.value)
        
        # Release for cleanup
        sem.release()
    
    @pytest.mark.asyncio
    async def test_async_semaphore_holders(self):
        """Test AsyncSemaphore holder tracking."""
        # Arrange
        sem = AsyncSemaphore(value=2, name="TestSemaphore")
        
        # Act
        await sem.acquire()
        
        # Assert
        assert len(sem.holders) == 1
        
        # Acquire again
        await sem.acquire()
        assert len(sem.holders) == 2
        
        # Release
        sem.release()
        assert len(sem.holders) == 1
        
        sem.release()
        assert len(sem.holders) == 0


class TestAsyncEvent:
    """Tests for the AsyncEvent class."""
    
    @pytest.mark.asyncio
    async def test_async_event_set_clear(self):
        """Test basic event set and clear."""
        # Arrange
        event = AsyncEvent(name="TestEvent")
        
        # Act & Assert
        assert not event.is_set()
        
        event.set()
        assert event.is_set()
        
        event.clear()
        assert not event.is_set()
    
    @pytest.mark.asyncio
    async def test_async_event_wait(self):
        """Test waiting for an event."""
        # Arrange
        event = AsyncEvent(name="TestEvent")
        
        # Schedule event to be set after a short delay
        asyncio.create_task(sleep_and_set(event, 0.1))
        
        # Act
        start_time = time.time()
        await event.wait()
        elapsed = time.time() - start_time
        
        # Assert
        assert event.is_set()
        assert elapsed >= 0.1
    
    @pytest.mark.asyncio
    async def test_async_event_wait_timeout(self):
        """Test event wait with timeout."""
        # Arrange
        event = AsyncEvent(name="TestEvent")
        
        # Act
        result = await event.wait(timeout=0.1)
        
        # Assert
        assert not result  # Wait timed out
        assert not event.is_set()
    
    @pytest.mark.asyncio
    async def test_async_event_wait_already_set(self):
        """Test waiting for an already set event."""
        # Arrange
        event = AsyncEvent(name="TestEvent")
        event.set()
        
        # Act
        result = await event.wait()
        
        # Assert
        assert result  # Wait completed immediately
        assert event.is_set()
    
    @pytest.mark.asyncio
    async def test_async_event_state_info(self):
        """Test event state information."""
        # Arrange
        event = AsyncEvent(name="TestEvent")
        
        # Act & Assert
        info = event.state_info
        assert info["name"] == "TestEvent"
        assert not info["is_set"]
        assert info["set_at"] is None
        assert info["set_by"] is None
        
        # Set the event
        event.set()
        
        # Check updated info
        info = event.state_info
        assert info["is_set"]
        assert info["set_at"] is not None
        assert info["set_by"] is not None
    
    @pytest.mark.asyncio
    async def test_async_event_context_manager(self):
        """Test using AsyncEvent as a context manager."""
        # Arrange & Act
        async with AsyncEvent(name="TestEvent") as event:
            # Assert
            assert not event.is_set()
            event.set()
            assert event.is_set()


class TestLimiter:
    """Tests for the Limiter class."""
    
    @pytest.mark.asyncio
    async def test_limiter_basic(self):
        """Test basic limiter functionality."""
        # Arrange
        limiter = Limiter(max_concurrent=2, name="TestLimiter")
        tasks_running = []
        
        # Define task function
        async def task(delay):
            async with limiter.acquire():
                tasks_running.append(1)
                await asyncio.sleep(delay)
                tasks_running.pop()
        
        # Act
        # Start two tasks (should run concurrently)
        task1 = asyncio.create_task(task(0.2))
        task2 = asyncio.create_task(task(0.3))
        
        # Wait for them to start
        await asyncio.sleep(0.1)
        
        # Assert
        assert len(tasks_running) == 2
        assert limiter.active_count == 2
        assert limiter.available == 0
        
        # Try to start a third task (should be limited)
        start_time = time.time()
        task3 = asyncio.create_task(task(0.1))
        
        # Wait for all tasks to complete
        await asyncio.gather(task1, task2, task3)
        elapsed = time.time() - start_time
        
        # Assert
        assert len(tasks_running) == 0
        assert limiter.active_count == 0
        assert limiter.available == 2
        assert elapsed >= 0.2  # Task3 had to wait for at least one other task
    
    @pytest.mark.asyncio
    async def test_limiter_timeout(self):
        """Test limiter with timeout."""
        # Arrange
        limiter = Limiter(max_concurrent=1, name="TestLimiter")
        
        # Acquire the limiter
        async with limiter.acquire():
            # Assert
            assert limiter.active_count == 1
            assert limiter.available == 0
            
            # Try to acquire again with timeout
            with pytest.raises(TimeoutError):
                async with limiter.acquire(timeout=0.1):
                    pass


class TestRateLimiter:
    """Tests for the RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiter functionality."""
        # Arrange
        limiter = RateLimiter(rate=10, burst=2, name="TestRateLimiter")
        times = []
        
        # Act
        # Burst of 2 operations should be immediate
        start_time = time.time()
        
        async with limiter.acquire():
            times.append(time.time() - start_time)
            
            async with limiter.acquire():
                times.append(time.time() - start_time)
                
                # Third operation should be rate-limited (wait ~0.1s)
                async with limiter.acquire():
                    times.append(time.time() - start_time)
        
        # Assert
        assert times[0] < 0.01  # First operation immediate
        assert times[1] < 0.01  # Second operation immediate (burst)
        assert times[2] >= 0.1  # Third operation rate-limited
    
    @pytest.mark.asyncio
    async def test_rate_limiter_timeout(self):
        """Test rate limiter with timeout."""
        # Arrange - very low rate of 1 per second
        limiter = RateLimiter(rate=1, burst=1, name="TestRateLimiter")
        
        # Act
        # First operation uses the burst
        async with limiter.acquire():
            # Try to do another operation with a short timeout
            with pytest.raises(TimeoutError):
                async with limiter.acquire(timeout=0.1):
                    pass
    
    @pytest.mark.asyncio
    async def test_rate_limiter_tokens(self):
        """Test rate limiter token management."""
        # Arrange
        limiter = RateLimiter(rate=10, burst=5, name="TestRateLimiter")
        
        # Act & Assert
        # Initially should have full tokens
        assert limiter.available_tokens == 5
        
        # Use 3 tokens
        async with limiter.acquire(tokens=3):
            # Should have 2 tokens left
            assert limiter.available_tokens == 2
            
            # Wait for tokens to refill (0.2s = 2 more tokens at rate=10)
            await asyncio.sleep(0.2)
            
            # Should have ~4 tokens now
            assert limiter.available_tokens >= 3.9
    
    @pytest.mark.asyncio
    async def test_rate_limiter_exceed_burst(self):
        """Test rate limiter when requesting more tokens than burst allows."""
        # Arrange
        limiter = RateLimiter(rate=10, burst=3, name="TestRateLimiter")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot acquire 4 tokens"):
            async with limiter.acquire(tokens=4):
                pass