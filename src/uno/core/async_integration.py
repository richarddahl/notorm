"""
Async integration utilities for the Uno framework.

This module provides ready-to-use integrations for common async patterns
to make it easy to adopt the async-first architecture throughout the codebase.
"""

from typing import Any, Callable, TypeVar, Optional, List, Dict, Union, Type, Awaitable, cast, Generic, AsyncIterator
import asyncio
import inspect
import functools
import logging
import contextlib
from contextlib import AbstractAsyncContextManager

from uno.core.async_utils import (
    TaskManager,
    TaskGroup,
    AsyncLock,
    AsyncSemaphore,
    AsyncEvent,
    Limiter,
    RateLimiter,
    timeout,
    AsyncContextGroup,
)

T = TypeVar('T')
R = TypeVar('R')


def cancellable(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to make an async function properly handle cancellation.
    
    This decorator ensures that when a task is cancelled, resources are
    properly cleaned up and cancellation is propagated correctly.
    
    Args:
        func: The async function to decorate
        
    Returns:
        A wrapped function that handles cancellation properly
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except asyncio.CancelledError:
            # Log the cancellation
            logging.getLogger(func.__module__).debug(
                f"Function {func.__name__} was cancelled"
            )
            # Re-raise the cancellation
            raise
    
    return wrapper


def timeout_handler(
    timeout_seconds: Optional[float],
    timeout_message: str = "Operation timed out",
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator factory to add timeout handling to an async function.
    
    Args:
        timeout_seconds: Timeout in seconds, or None for no timeout
        timeout_message: Message to include in the timeout error
        
    Returns:
        A decorator that applies the timeout to the decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if timeout_seconds is None:
                return await func(*args, **kwargs)
            
            async with timeout(timeout_seconds, timeout_message):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def retry(
    max_attempts: int = 3,
    retry_exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    base_delay: float = 0.1,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator factory to add retry logic to an async function.
    
    Args:
        max_attempts: Maximum number of attempts
        retry_exceptions: Exception or list of exceptions to retry on
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        backoff_factor: Factor to multiply delay by on each attempt
        logger: Optional logger instance
        
    Returns:
        A decorator that applies retry logic to the decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            log = logger or logging.getLogger(func.__module__)
            
            # Convert single exception to list
            exceptions = retry_exceptions
            if not isinstance(exceptions, list):
                exceptions = [exceptions]
            
            attempt = 0
            last_error = None
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_error = e
                    attempt += 1
                    
                    if attempt >= max_attempts:
                        log.warning(
                            f"Function {func.__name__} failed after {max_attempts} attempts. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                    
                    log.debug(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {delay:.2f}s... Error: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
            
            # This should never happen, but added for type safety
            assert last_error is not None
            raise last_error
        
        return wrapper
    
    return decorator


def rate_limited(
    operations_per_second: float,
    burst_limit: Optional[int] = None,
    limiter: Optional[RateLimiter] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator factory to add rate limiting to an async function.
    
    Args:
        operations_per_second: Maximum operations per second
        burst_limit: Optional burst limit
        limiter: Optional pre-configured rate limiter
        
    Returns:
        A decorator that applies rate limiting to the decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        # Create or use a rate limiter
        nonlocal limiter
        if limiter is None:
            limiter = RateLimiter(
                operations_per_second=operations_per_second,
                burst_limit=burst_limit,
                name=f"{func.__name__}_limiter"
            )
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async with limiter:
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def concurrent_limited(
    max_concurrent: int,
    limiter: Optional[Limiter] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator factory to limit concurrent executions of an async function.
    
    Args:
        max_concurrent: Maximum number of concurrent executions
        limiter: Optional pre-configured concurrency limiter
        
    Returns:
        A decorator that limits concurrent executions of the decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        # Create or use a concurrency limiter
        nonlocal limiter
        if limiter is None:
            limiter = Limiter(
                max_concurrent=max_concurrent,
                name=f"{func.__name__}_limiter"
            )
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async with limiter:
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class AsyncBatcher(Generic[T, R]):
    """
    Utility for batching async operations.
    
    This class batches individual operation requests together to improve efficiency,
    especially for database or API operations.
    """
    
    def __init__(
        self,
        batch_operation: Callable[[List[T]], Awaitable[List[R]]],
        max_batch_size: int = 100,
        max_wait_time: float = 0.1,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the async batcher.
        
        Args:
            batch_operation: Function that processes a batch of items
            max_batch_size: Maximum batch size
            max_wait_time: Maximum time to wait for a batch to fill
            logger: Optional logger instance
        """
        self.batch_operation = batch_operation
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.logger = logger or logging.getLogger(__name__)
        self.items: List[T] = []
        self.futures: List[asyncio.Future[R]] = []
        self.batch_lock = AsyncLock()
        self.batch_event = AsyncEvent()
        self.is_processing = False
        self.processor_task: Optional[asyncio.Task] = None
    
    async def add_item(self, item: T) -> R:
        """
        Add an item to the batch and get its result when processed.
        
        Args:
            item: The item to add to the batch
            
        Returns:
            The result for this item after batch processing
        """
        # Create a future for this item's result
        future: asyncio.Future[R] = asyncio.Future()
        
        # Add the item and its future to the batch
        async with self.batch_lock:
            self.items.append(item)
            self.futures.append(future)
            
            # Start the processor task if not running
            if not self.is_processing:
                self.is_processing = True
                self.processor_task = asyncio.create_task(
                    self._process_batches(),
                    name=f"batch_processor_{id(self)}"
                )
            
            # Signal that a new item is available
            self.batch_event.set()
        
        # Wait for this item's result
        try:
            return await future
        except asyncio.CancelledError:
            # If the caller is cancelled, try to remove the item from the batch
            async with self.batch_lock:
                try:
                    idx = self.futures.index(future)
                    self.items.pop(idx)
                    self.futures.pop(idx)
                except (ValueError, IndexError):
                    # Item might already be processing
                    pass
            raise
    
    async def _process_batches(self) -> None:
        """Process batches of items as they become available."""
        try:
            while True:
                # Wait for items or timeout
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self.batch_event.wait(), self.max_wait_time)
                
                # Get items to process
                async with self.batch_lock:
                    # Clear the event flag
                    self.batch_event.clear()
                    
                    # Check if we have items to process
                    if not self.items:
                        # No items, so stop processing
                        self.is_processing = False
                        return
                    
                    # Get a batch of items
                    batch_items = self.items[:self.max_batch_size]
                    batch_futures = self.futures[:self.max_batch_size]
                    
                    # Remove the items from the queues
                    self.items = self.items[self.max_batch_size:]
                    self.futures = self.futures[self.max_batch_size:]
                    
                    # If more items remain, keep the event set
                    if self.items:
                        self.batch_event.set()
                
                # Process the batch
                try:
                    results = await self.batch_operation(batch_items)
                    
                    # Set results in futures
                    if len(results) != len(batch_futures):
                        err = ValueError(
                            f"Batch operation returned {len(results)} results "
                            f"but expected {len(batch_futures)}"
                        )
                        for future in batch_futures:
                            if not future.done():
                                future.set_exception(err)
                    else:
                        for future, result in zip(batch_futures, results):
                            if not future.done():
                                future.set_result(result)
                
                except Exception as e:
                    # Propagate error to all futures
                    for future in batch_futures:
                        if not future.done():
                            future.set_exception(e)
        
        except asyncio.CancelledError:
            # If the processor is cancelled, cancel all pending futures
            async with self.batch_lock:
                for future in self.futures:
                    if not future.done():
                        future.cancel()
                self.items = []
                self.futures = []
                self.is_processing = False
            raise
        
        except Exception as e:
            # Log unexpected errors
            self.logger.error(f"Error in batch processor: {str(e)}", exc_info=e)
            
            # Cancel all pending futures
            async with self.batch_lock:
                for future in self.futures:
                    if not future.done():
                        future.set_exception(e)
                self.items = []
                self.futures = []
                self.is_processing = False
    
    async def shutdown(self) -> None:
        """Shutdown the batcher and cancel any pending operations."""
        # Cancel the processor task
        if self.processor_task is not None:
            self.processor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.processor_task
            self.processor_task = None
        
        # Cancel all pending futures
        async with self.batch_lock:
            for future in self.futures:
                if not future.done():
                    future.cancel()
            self.items = []
            self.futures = []
            self.is_processing = False


class AsyncCache(Generic[T, R]):
    """
    Generic async cache with timeout and background refresh.
    
    This class provides:
    - Async-aware caching with TTL
    - Background refresh of cache entries
    - Proper cancellation handling
    - Resource cleanup
    """
    
    def __init__(
        self,
        ttl: float,
        refresh_before_expiry: Optional[float] = None,
        max_size: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the async cache.
        
        Args:
            ttl: Time-to-live for cache entries in seconds
            refresh_before_expiry: Time before expiry to trigger refresh
            max_size: Maximum cache size (None for unlimited)
            logger: Optional logger instance
        """
        self.ttl = ttl
        self.refresh_ahead = refresh_before_expiry or (ttl * 0.8)
        self.max_size = max_size
        self.logger = logger or logging.getLogger(__name__)
        self.cache: Dict[T, Dict[str, Any]] = {}
        self.cache_lock = AsyncLock()
        self.refresh_tasks: Dict[T, asyncio.Task] = {}
    
    async def get(
        self,
        key: T,
        fetch_func: Callable[[T], Awaitable[R]],
        force_refresh: bool = False,
    ) -> R:
        """
        Get a value from the cache, fetching it if not present.
        
        Args:
            key: Cache key
            fetch_func: Function to fetch the value if not in cache
            force_refresh: Whether to force a refresh
            
        Returns:
            The cached or freshly fetched value
        """
        async with self.cache_lock:
            # Check if key is in cache and not expired
            now = asyncio.get_event_loop().time()
            if (
                not force_refresh
                and key in self.cache
                and now < self.cache[key]["expiry"]
            ):
                # If approaching expiry, trigger background refresh
                if (
                    now > self.cache[key]["expiry"] - self.refresh_ahead
                    and key not in self.refresh_tasks
                ):
                    self._start_refresh_task(key, fetch_func)
                
                # Return cached value
                return cast(R, self.cache[key]["value"])
            
            # Fetch the value
            try:
                value = await fetch_func(key)
                
                # Store in cache
                expiry = now + self.ttl
                self.cache[key] = {
                    "value": value,
                    "expiry": expiry,
                    "last_refresh": now,
                }
                
                # Enforce max size if specified
                if self.max_size is not None and len(self.cache) > self.max_size:
                    # Remove oldest entries
                    excess = len(self.cache) - self.max_size
                    if excess > 0:
                        sorted_keys = sorted(
                            self.cache.keys(),
                            key=lambda k: self.cache[k]["last_refresh"]
                        )
                        for old_key in sorted_keys[:excess]:
                            del self.cache[old_key]
                
                return value
            
            except Exception as e:
                # If fetch fails and we have a cached value, use it
                if key in self.cache:
                    self.logger.warning(
                        f"Failed to refresh cache for key {key}: {str(e)}. "
                        f"Using stale value."
                    )
                    return cast(R, self.cache[key]["value"])
                
                # Otherwise, propagate the error
                raise
    
    def _start_refresh_task(
        self,
        key: T,
        fetch_func: Callable[[T], Awaitable[R]],
    ) -> None:
        """
        Start a background task to refresh a cache entry.
        
        Args:
            key: Cache key to refresh
            fetch_func: Function to fetch the fresh value
        """
        # Create a refresh function
        async def refresh_cache_entry() -> None:
            try:
                # Fetch the new value
                value = await fetch_func(key)
                
                # Update the cache
                async with self.cache_lock:
                    now = asyncio.get_event_loop().time()
                    expiry = now + self.ttl
                    
                    self.cache[key] = {
                        "value": value,
                        "expiry": expiry,
                        "last_refresh": now,
                    }
            
            except asyncio.CancelledError:
                # Propagate cancellation
                raise
            
            except Exception as e:
                # Log refresh error but don't fail
                self.logger.warning(f"Failed to refresh cache for key {key}: {str(e)}")
            
            finally:
                # Remove task from tracking
                async with self.cache_lock:
                    if key in self.refresh_tasks:
                        del self.refresh_tasks[key]
        
        # Start the refresh task
        task = asyncio.create_task(
            refresh_cache_entry(),
            name=f"cache_refresh_{hash(key)}"
        )
        self.refresh_tasks[key] = task
    
    async def invalidate(self, key: T) -> None:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        async with self.cache_lock:
            # Cancel any refresh task
            if key in self.refresh_tasks:
                self.refresh_tasks[key].cancel()
                del self.refresh_tasks[key]
            
            # Remove from cache
            if key in self.cache:
                del self.cache[key]
    
    async def clear(self) -> None:
        """Clear the entire cache."""
        async with self.cache_lock:
            # Cancel all refresh tasks
            for task in self.refresh_tasks.values():
                task.cancel()
            
            # Clear dictionaries
            self.refresh_tasks.clear()
            self.cache.clear()


class AsyncResource(AbstractAsyncContextManager[T]):
    """
    Base class for async resources that need lifecycle management.
    
    This class provides:
    - Proper initialization and cleanup
    - Resource pooling
    - Error handling
    """
    
    def __init__(self, name: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the async resource.
        
        Args:
            name: Optional name for the resource
            logger: Optional logger instance
        """
        self.name = name or f"{self.__class__.__name__}_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        self._initialized = False
        self._closed = False
        self._lock = AsyncLock()
    
    async def _initialize(self) -> None:
        """Initialize the resource. Override in subclasses."""
        pass
    
    async def _cleanup(self) -> None:
        """Clean up the resource. Override in subclasses."""
        pass
    
    async def __aenter__(self) -> T:
        """Enter the async context, initializing the resource."""
        async with self._lock:
            if self._closed:
                raise RuntimeError(f"Resource {self.name} is closed")
            
            if not self._initialized:
                try:
                    await self._initialize()
                    self._initialized = True
                except Exception as e:
                    self.logger.error(f"Failed to initialize resource {self.name}: {str(e)}")
                    await self._cleanup()
                    self._closed = True
                    raise
        
        return cast(T, self)
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context, cleaning up the resource."""
        async with self._lock:
            if not self._closed:
                try:
                    await self._cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up resource {self.name}: {str(e)}")
                finally:
                    self._closed = True
    
    async def close(self) -> None:
        """Explicitly close the resource."""
        await self.__aexit__(None, None, None)


class AsyncResourcePool(Generic[T]):
    """
    Pool of async resources.
    
    This class provides:
    - Resource pooling with lazy initialization
    - Automatic resource cleanup
    - Proper cancellation handling
    """
    
    def __init__(
        self,
        factory: Callable[[], Awaitable[T]],
        max_size: int = 10,
        min_size: int = 0,
        max_idle: int = 2,
        ttl: float = 60.0,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the async resource pool.
        
        Args:
            factory: Factory function to create resources
            max_size: Maximum pool size
            min_size: Minimum pool size
            max_idle: Maximum number of idle resources
            ttl: Time-to-live for idle resources in seconds
            name: Optional name for the pool
            logger: Optional logger instance
        """
        self.factory = factory
        self.max_size = max_size
        self.min_size = min_size
        self.max_idle = max_idle
        self.ttl = ttl
        self.name = name or f"resource_pool_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        
        self.resources: List[Dict[str, Any]] = []
        self.pool_lock = AsyncLock()
        self.resource_available = AsyncEvent()
        self.closed = False
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def acquire(self) -> T:
        """
        Acquire a resource from the pool.
        
        Returns:
            A resource from the pool
        
        Raises:
            RuntimeError: If the pool is closed
        """
        if self.closed:
            raise RuntimeError(f"Resource pool {self.name} is closed")
        
        while True:
            async with self.pool_lock:
                # Check for available resources
                available = [
                    r for r in self.resources
                    if not r["in_use"] and not r["closing"]
                ]
                
                if available:
                    # Use an available resource
                    resource_info = available[0]
                    resource_info["in_use"] = True
                    resource_info["last_used"] = asyncio.get_event_loop().time()
                    return cast(T, resource_info["resource"])
                
                # If pool is not at max size, create a new resource
                if len(self.resources) < self.max_size:
                    try:
                        # Create a new resource
                        resource = await self.factory()
                        
                        # Add to pool
                        now = asyncio.get_event_loop().time()
                        self.resources.append({
                            "resource": resource,
                            "in_use": True,
                            "created": now,
                            "last_used": now,
                            "closing": False,
                        })
                        
                        return resource
                    
                    except Exception as e:
                        self.logger.error(f"Failed to create resource: {str(e)}")
                        # Wait a bit before retrying
                        await asyncio.sleep(0.5)
                        continue
                
                # Clear the event before waiting
                self.resource_available.clear()
            
            # Wait for a resource to become available
            try:
                await asyncio.wait_for(self.resource_available.wait(), 5.0)
            except asyncio.TimeoutError:
                # Check if pool is closed
                if self.closed:
                    raise RuntimeError(f"Resource pool {self.name} is closed")
                # Retry
                continue
    
    async def release(self, resource: T) -> None:
        """
        Release a resource back to the pool.
        
        Args:
            resource: The resource to release
        """
        async with self.pool_lock:
            # Find the resource
            for resource_info in self.resources:
                if resource_info["resource"] is resource:
                    # Update resource info
                    resource_info["in_use"] = False
                    resource_info["last_used"] = asyncio.get_event_loop().time()
                    
                    # Signal that a resource is available
                    self.resource_available.set()
                    
                    return
            
            # Resource not found in pool
            self.logger.warning(f"Released resource not found in pool {self.name}")
    
    async def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(
                self._cleanup_idle_resources(),
                name=f"{self.name}_cleanup"
            )
    
    async def _cleanup_idle_resources(self) -> None:
        """Periodically clean up idle resources."""
        try:
            while not self.closed:
                await asyncio.sleep(min(30.0, self.ttl / 2))
                
                await self._perform_cleanup()
        
        except asyncio.CancelledError:
            # Propagate cancellation
            raise
        
        except Exception as e:
            # Log unexpected errors
            self.logger.error(f"Error in cleanup task: {str(e)}", exc_info=e)
    
    async def _perform_cleanup(self) -> None:
        """Perform a cleanup of idle resources."""
        to_close = []
        
        async with self.pool_lock:
            now = asyncio.get_event_loop().time()
            
            # Count idle resources
            idle_resources = [
                r for r in self.resources
                if not r["in_use"] and not r["closing"]
            ]
            
            # If we have more idle resources than needed
            if len(idle_resources) > self.max_idle:
                # Sort by last used time
                idle_resources.sort(key=lambda r: r["last_used"])
                
                # Mark excess resources for closing
                excess = len(idle_resources) - self.max_idle
                for resource_info in idle_resources[:excess]:
                    resource_info["closing"] = True
                    to_close.append(resource_info)
            
            # Check for expired resources
            for resource_info in self.resources:
                if (
                    not resource_info["in_use"]
                    and not resource_info["closing"]
                    and now - resource_info["last_used"] > self.ttl
                ):
                    resource_info["closing"] = True
                    to_close.append(resource_info)
        
        # Close the resources outside the lock
        for resource_info in to_close:
            try:
                resource = resource_info["resource"]
                
                # Close the resource
                if hasattr(resource, "close") and callable(resource.close):
                    await resource.close()
                elif hasattr(resource, "__aexit__") and callable(resource.__aexit__):
                    await resource.__aexit__(None, None, None)
            
            except Exception as e:
                self.logger.warning(f"Error closing resource: {str(e)}")
            
            finally:
                # Remove from pool
                async with self.pool_lock:
                    self.resources = [
                        r for r in self.resources
                        if r["resource"] is not resource_info["resource"]
                    ]
    
    async def close(self) -> None:
        """Close the resource pool and all resources."""
        if self.closed:
            return
        
        self.closed = True
        
        # Cancel cleanup task
        if self.cleanup_task is not None:
            self.cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.cleanup_task
            self.cleanup_task = None
        
        # Close all resources
        resources_to_close = []
        
        async with self.pool_lock:
            # Get all resources
            resources_to_close = [r["resource"] for r in self.resources]
            self.resources = []
            
            # Signal any waiters
            self.resource_available.set()
        
        # Close resources outside the lock
        for resource in resources_to_close:
            try:
                if hasattr(resource, "close") and callable(resource.close):
                    await resource.close()
                elif hasattr(resource, "__aexit__") and callable(resource.__aexit__):
                    await resource.__aexit__(None, None, None)
            except Exception as e:
                self.logger.warning(f"Error closing resource: {str(e)}")
    
    @contextlib.asynccontextmanager
    async def get(self) -> AsyncIterator[T]:
        """Context manager to get and automatically release a resource."""
        resource = await self.acquire()
        try:
            yield resource
        finally:
            await self.release(resource)