"""
Resource management for the Uno framework.

This module provides utilities for managing resources with proper lifecycle 
management, including connection pooling, circuit breakers, and cleanup.
"""

from typing import TypeVar, Generic, Dict, List, Any, Optional, Callable, Awaitable, Union, cast
import asyncio
import logging
import time
import contextlib
import functools
from datetime import datetime, timedelta
from enum import Enum

from uno.core.async_utils import (
    AsyncLock,
    AsyncEvent,
    AsyncSemaphore,
    TaskGroup,
    timeout,
    AsyncContextGroup,
    AsyncExitStack,
)
from uno.core.async_integration import (
    cancellable,
    retry,
    timeout_handler,
    AsyncResourcePool,
)


T = TypeVar('T')
R = TypeVar('R')


class CircuitState(Enum):
    """
    Possible states for a circuit breaker.
    
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is broken, requests fail fast
    - HALF_OPEN: Testing if the service is healthy again
    """
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker for protecting external resources.
    
    A circuit breaker prevents cascading failures by stopping requests
    to a failing service after a threshold of failures is reached.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        exception_types: Optional[List[type]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a circuit breaker.
        
        Args:
            name: Name of the circuit breaker for logging and metrics
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds to wait before trying recovery
            half_open_max_calls: Maximum calls allowed in half-open state
            exception_types: Types of exceptions to count as failures
            logger: Optional logger instance
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.exception_types = exception_types or [Exception]
        self.logger = logger or logging.getLogger(__name__)
        
        # Initial state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._successful_calls = 0
        self._lock = AsyncLock()
        self._state_change_event = AsyncEvent()
        
        # Metrics
        self._total_failures = 0
        self._total_successes = 0
        self._last_state_change_time: Optional[float] = None
    
    @property
    def state(self) -> CircuitState:
        """Get the current state of the circuit breaker."""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if the circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if the circuit is open (failing fast)."""
        return self._state == CircuitState.OPEN
    
    @property
    def failure_count(self) -> int:
        """Get the current failure count."""
        return self._failure_count
    
    async def __call__(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Call the protected function.
        
        Args:
            func: The function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function
            
        Raises:
            CircuitBreakerOpenError: If the circuit is open
            Any exception raised by the function
        """
        async with self._lock:
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                now = time.time()
                if self._last_failure_time and now - self._last_failure_time >= self.recovery_timeout:
                    # Transition to half-open
                    await self._transition_to_state(CircuitState.HALF_OPEN)
                else:
                    # Circuit is open, fail fast
                    self.logger.warning(
                        f"Circuit breaker '{self.name}' is open. Failing fast."
                    )
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open."
                    )
            
            # Check if circuit is half-open and at max calls
            if (
                self._state == CircuitState.HALF_OPEN
                and self._successful_calls >= self.half_open_max_calls
            ):
                # Transition to closed
                await self._transition_to_state(CircuitState.CLOSED)
        
        # Release the lock for the actual call
        try:
            # Call the function
            result = await func(*args, **kwargs)
            
            # Record successful call
            await self._record_success()
            
            return result
        
        except tuple(self.exception_types) as e:
            # Record failure
            await self._record_failure()
            
            # Re-raise the exception
            raise
    
    async def _transition_to_state(self, new_state: CircuitState) -> None:
        """
        Transition to a new circuit state.
        
        Args:
            new_state: The new state to transition to
        """
        if self._state == new_state:
            return
        
        old_state = self._state
        self._state = new_state
        self._last_state_change_time = time.time()
        
        # Reset counters based on new state
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._successful_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._successful_calls = 0
        
        # Log the transition
        self.logger.info(
            f"Circuit breaker '{self.name}' state changed from {old_state.value} to {new_state.value}"
        )
        
        # Notify listeners
        self._state_change_event.set()
        self._state_change_event.clear()
    
    async def _record_success(self) -> None:
        """Record a successful call through the circuit breaker."""
        async with self._lock:
            self._total_successes += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._successful_calls += 1
                
                # Check if we should close the circuit
                if self._successful_calls >= self.half_open_max_calls:
                    await self._transition_to_state(CircuitState.CLOSED)
    
    async def _record_failure(self) -> None:
        """Record a failed call through the circuit breaker."""
        async with self._lock:
            self._total_failures += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.CLOSED:
                self._failure_count += 1
                
                # Check if we should open the circuit
                if self._failure_count >= self.failure_threshold:
                    await self._transition_to_state(CircuitState.OPEN)
            
            elif self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open state opens the circuit again
                await self._transition_to_state(CircuitState.OPEN)
    
    async def reset(self) -> None:
        """
        Reset the circuit breaker to closed state.
        
        This is mainly for testing or manual intervention.
        """
        async with self._lock:
            await self._transition_to_state(CircuitState.CLOSED)
    
    def __str__(self) -> str:
        """Get a string representation of the circuit breaker."""
        return f"CircuitBreaker(name={self.name}, state={self._state.value})"


class CircuitBreakerOpenError(Exception):
    """
    Error raised when a circuit breaker is open.
    
    This error indicates that the circuit breaker is preventing
    requests to a failing service to avoid cascading failures.
    """
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConnectionPool(Generic[T]):
    """
    Pool of managed connections with health checks and monitoring.
    
    This class extends AsyncResourcePool with:
    - Health checking
    - Connection validation
    - Metrics collection
    - Graceful shutdown
    """
    
    def __init__(
        self,
        name: str,
        factory: Callable[[], Awaitable[T]],
        close_func: Callable[[T], Awaitable[None]],
        validate_func: Optional[Callable[[T], Awaitable[bool]]] = None,
        max_size: int = 10,
        min_size: int = 0,
        max_idle: int = 2,
        ttl: float = 60.0,
        validation_interval: float = 30.0,
        retry_backoff: float = 1.0,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the connection pool.
        
        Args:
            name: Name of the pool for logging and metrics
            factory: Factory function to create new connections
            close_func: Function to close a connection
            validate_func: Optional function to validate a connection
            max_size: Maximum number of connections
            min_size: Minimum number of connections
            max_idle: Maximum number of idle connections
            ttl: Time-to-live for connections in seconds
            validation_interval: Time between validation checks
            retry_backoff: Base delay for retry backoff
            logger: Optional logger instance
        """
        self.name = name
        self.factory = factory
        self.close_func = close_func
        self.validate_func = validate_func
        self.max_size = max_size
        self.min_size = min_size
        self.max_idle = max_idle
        self.ttl = ttl
        self.validation_interval = validation_interval
        self.retry_backoff = retry_backoff
        self.logger = logger or logging.getLogger(__name__)
        
        # Pool state
        self._connections: List[Dict[str, Any]] = []
        self._pool_lock = AsyncLock()
        self._connection_available = AsyncEvent()
        self._closed = False
        
        # Tasks
        self._maintenance_task: Optional[asyncio.Task] = None
        self._validation_task: Optional[asyncio.Task] = None
        
        # Metrics
        self._created_connections = 0
        self._closed_connections = 0
        self._connection_errors = 0
        self._validation_failures = 0
        self._start_time = time.time()
    
    async def start(self) -> None:
        """
        Start the connection pool.
        
        This initializes the minimum number of connections and
        starts the maintenance and validation tasks.
        """
        if self._closed:
            raise RuntimeError(f"Connection pool {self.name} is closed")
        
        # Initialize minimum connections
        async with self._pool_lock:
            # Create minimum connections
            for _ in range(self.min_size):
                try:
                    conn = await self._create_connection()
                    now = time.time()
                    self._connections.append({
                        "connection": conn,
                        "in_use": False,
                        "created": now,
                        "last_used": now,
                        "validated": now,
                    })
                except Exception as e:
                    self.logger.error(
                        f"Error creating initial connection in pool {self.name}: {str(e)}"
                    )
        
        # Start maintenance task
        self._maintenance_task = asyncio.create_task(
            self._maintenance_loop(),
            name=f"{self.name}_maintenance"
        )
        
        # Start validation task if validation function is provided
        if self.validate_func:
            self._validation_task = asyncio.create_task(
                self._validation_loop(),
                name=f"{self.name}_validation"
            )
    
    async def _create_connection(self) -> T:
        """
        Create a new connection.
        
        Returns:
            A new connection object
        
        Raises:
            Exception: If connection creation fails
        """
        try:
            connection = await self.factory()
            self._created_connections += 1
            self.logger.debug(f"Created new connection in pool {self.name}")
            return connection
        except Exception as e:
            self._connection_errors += 1
            self.logger.error(f"Error creating connection in pool {self.name}: {str(e)}")
            raise
    
    async def _close_connection(self, connection: T) -> None:
        """
        Close a connection.
        
        Args:
            connection: The connection to close
        """
        try:
            await self.close_func(connection)
            self._closed_connections += 1
            self.logger.debug(f"Closed connection in pool {self.name}")
        except Exception as e:
            self.logger.warning(
                f"Error closing connection in pool {self.name}: {str(e)}"
            )
    
    async def _validate_connection(self, connection: T) -> bool:
        """
        Validate a connection.
        
        Args:
            connection: The connection to validate
            
        Returns:
            True if the connection is valid, False otherwise
        """
        if not self.validate_func:
            return True
        
        try:
            return await self.validate_func(connection)
        except Exception as e:
            self._validation_failures += 1
            self.logger.warning(
                f"Error validating connection in pool {self.name}: {str(e)}"
            )
            return False
    
    async def acquire(self) -> T:
        """
        Acquire a connection from the pool.
        
        Returns:
            A connection from the pool
            
        Raises:
            RuntimeError: If the pool is closed
        """
        if self._closed:
            raise RuntimeError(f"Connection pool {self.name} is closed")
        
        while not self._closed:
            async with self._pool_lock:
                # Check for available connections
                available = [
                    c for c in self._connections
                    if not c["in_use"]
                ]
                
                if available:
                    # Use an available connection
                    conn_info = available[0]
                    conn_info["in_use"] = True
                    conn_info["last_used"] = time.time()
                    return cast(T, conn_info["connection"])
                
                # If pool is not at max size, create a new connection
                if len(self._connections) < self.max_size:
                    try:
                        # Create a new connection
                        connection = await self._create_connection()
                        
                        # Add to pool
                        now = time.time()
                        conn_info = {
                            "connection": connection,
                            "in_use": True,
                            "created": now,
                            "last_used": now,
                            "validated": now,
                        }
                        self._connections.append(conn_info)
                        
                        return connection
                    
                    except Exception as e:
                        self.logger.error(
                            f"Failed to create connection in pool {self.name}: {str(e)}"
                        )
                        # If we can't create a connection, wait and try again
                        await asyncio.sleep(self.retry_backoff)
                        continue
                
                # Clear the event before waiting
                self._connection_available.clear()
            
            # Wait for a connection to become available
            try:
                await asyncio.wait_for(
                    self._connection_available.wait(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                # Check if pool is closed
                if self._closed:
                    raise RuntimeError(f"Connection pool {self.name} is closed")
                # Otherwise, try again
                continue
        
        raise RuntimeError(f"Connection pool {self.name} is closed")
    
    async def release(self, connection: T) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: The connection to release
        """
        async with self._pool_lock:
            # Find the connection info
            for conn_info in self._connections:
                if conn_info["connection"] is connection:
                    # Mark as not in use
                    conn_info["in_use"] = False
                    conn_info["last_used"] = time.time()
                    
                    # Signal that a connection is available
                    self._connection_available.set()
                    
                    return
            
            # If connection not found, close it
            self.logger.warning(
                f"Released connection not found in pool {self.name}, closing it"
            )
            await self._close_connection(connection)
    
    async def _maintenance_loop(self) -> None:
        """
        Periodically clean up idle connections and ensure minimum pool size.
        """
        try:
            while not self._closed:
                await asyncio.sleep(min(30.0, self.ttl / 2))
                
                if self._closed:
                    break
                
                await self._perform_maintenance()
        
        except asyncio.CancelledError:
            # Expected during shutdown
            pass
        
        except Exception as e:
            self.logger.error(
                f"Error in maintenance task for pool {self.name}: {str(e)}",
                exc_info=True
            )
    
    async def _perform_maintenance(self) -> None:
        """
        Perform maintenance on the connection pool.
        
        This includes:
        - Closing excess idle connections
        - Closing expired connections
        - Creating new connections to maintain minimum pool size
        """
        to_close = []
        to_create = 0
        
        async with self._pool_lock:
            now = time.time()
            
            # Count idle and in-use connections
            idle_connections = [
                c for c in self._connections
                if not c["in_use"]
            ]
            in_use_connections = [
                c for c in self._connections
                if c["in_use"]
            ]
            
            # If we have more idle connections than needed, close the excess
            if len(idle_connections) > self.max_idle:
                # Sort by last used time (oldest first)
                idle_connections.sort(key=lambda c: c["last_used"])
                
                # Mark excess connections for closing
                excess = len(idle_connections) - self.max_idle
                for conn_info in idle_connections[:excess]:
                    to_close.append(conn_info)
                    self._connections.remove(conn_info)
            
            # Check for expired connections
            expired = [
                c for c in self._connections
                if not c["in_use"] and now - c["created"] > self.ttl
            ]
            
            for conn_info in expired:
                if conn_info not in to_close:  # Avoid duplicates
                    to_close.append(conn_info)
                    self._connections.remove(conn_info)
            
            # Calculate how many new connections we need
            current_size = len(self._connections) - len(to_close)
            if current_size < self.min_size:
                to_create = self.min_size - current_size
        
        # Close connections outside the lock
        for conn_info in to_close:
            await self._close_connection(conn_info["connection"])
        
        # Create new connections if needed
        for _ in range(to_create):
            try:
                conn = await self._create_connection()
                
                async with self._pool_lock:
                    # Add to pool if not closed
                    if not self._closed:
                        now = time.time()
                        self._connections.append({
                            "connection": conn,
                            "in_use": False,
                            "created": now,
                            "last_used": now,
                            "validated": now,
                        })
                    else:
                        # Pool closed while creating connection
                        await self._close_connection(conn)
                
            except Exception as e:
                self.logger.error(
                    f"Failed to create connection during maintenance for pool {self.name}: {str(e)}"
                )
    
    async def _validation_loop(self) -> None:
        """
        Periodically validate connections in the pool.
        """
        try:
            while not self._closed and self.validate_func:
                await asyncio.sleep(self.validation_interval)
                
                if self._closed:
                    break
                
                await self._perform_validation()
        
        except asyncio.CancelledError:
            # Expected during shutdown
            pass
        
        except Exception as e:
            self.logger.error(
                f"Error in validation task for pool {self.name}: {str(e)}",
                exc_info=True
            )
    
    async def _perform_validation(self) -> None:
        """
        Validate connections in the pool.
        
        Invalid connections are closed and removed from the pool.
        """
        to_validate = []
        invalid = []
        
        # Get connections to validate
        async with self._pool_lock:
            # Only validate idle connections
            idle_connections = [
                c for c in self._connections
                if not c["in_use"]
            ]
            
            # Add to validation list
            to_validate = list(idle_connections)
        
        # Validate connections outside the lock
        for conn_info in to_validate:
            valid = await self._validate_connection(conn_info["connection"])
            
            if not valid:
                invalid.append(conn_info)
            else:
                # Update validation timestamp
                conn_info["validated"] = time.time()
        
        # Remove invalid connections
        async with self._pool_lock:
            for conn_info in invalid:
                if conn_info in self._connections:
                    self._connections.remove(conn_info)
        
        # Close invalid connections outside the lock
        for conn_info in invalid:
            await self._close_connection(conn_info["connection"])
    
    async def close(self) -> None:
        """
        Close the connection pool.
        
        This closes all connections and stops maintenance tasks.
        """
        if self._closed:
            return
        
        self._closed = True
        
        # Cancel maintenance and validation tasks
        for task in [self._maintenance_task, self._validation_task]:
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        
        # Get all connections
        connections_to_close = []
        
        async with self._pool_lock:
            # Get all connections
            connections_to_close = [
                c["connection"] for c in self._connections
            ]
            self._connections = []
            
            # Signal any waiters
            self._connection_available.set()
        
        # Close connections outside the lock
        for connection in connections_to_close:
            await self._close_connection(connection)
        
        self.logger.info(
            f"Connection pool {self.name} closed. "
            f"Created: {self._created_connections}, "
            f"Closed: {self._closed_connections}, "
            f"Errors: {self._connection_errors}, "
            f"Validation failures: {self._validation_failures}"
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the connection pool.
        
        Returns:
            Dictionary of metrics
        """
        total_connections = len(self._connections)
        in_use_connections = sum(1 for c in self._connections if c["in_use"])
        idle_connections = total_connections - in_use_connections
        
        return {
            "name": self.name,
            "total_connections": total_connections,
            "in_use_connections": in_use_connections,
            "idle_connections": idle_connections,
            "max_size": self.max_size,
            "min_size": self.min_size,
            "created_connections": self._created_connections,
            "closed_connections": self._closed_connections,
            "connection_errors": self._connection_errors,
            "validation_failures": self._validation_failures,
            "uptime": time.time() - self._start_time,
        }
    
    @contextlib.asynccontextmanager
    async def connection(self) -> Any:
        """
        Context manager for acquiring and releasing a connection.
        
        Yields:
            A connection from the pool
        """
        connection = await self.acquire()
        try:
            yield connection
        finally:
            await self.release(connection)


class ResourceRegistry:
    """
    Registry for tracking and managing resources.
    
    This class provides centralized management of resources
    like connection pools and circuit breakers.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the resource registry.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._resources: Dict[str, Any] = {}
        self._resource_lock = AsyncLock()
        self._closed = False
    
    async def register(self, name: str, resource: Any) -> None:
        """
        Register a resource with the registry.
        
        Args:
            name: Name of the resource
            resource: The resource to register
            
        Raises:
            ValueError: If a resource with the same name already exists
            RuntimeError: If the registry is closed
        """
        if self._closed:
            raise RuntimeError("Resource registry is closed")
        
        async with self._resource_lock:
            if name in self._resources:
                raise ValueError(f"Resource '{name}' already exists")
            
            self._resources[name] = resource
            self.logger.debug(f"Registered resource: {name}")
    
    async def unregister(self, name: str) -> None:
        """
        Unregister a resource from the registry.
        
        Args:
            name: Name of the resource
            
        Raises:
            ValueError: If the resource doesn't exist
        """
        async with self._resource_lock:
            if name not in self._resources:
                raise ValueError(f"Resource '{name}' not found")
            
            resource = self._resources.pop(name)
            self.logger.debug(f"Unregistered resource: {name}")
            
            # Close the resource if it has a close method
            if hasattr(resource, "close") and callable(resource.close):
                try:
                    await resource.close()
                except Exception as e:
                    self.logger.warning(
                        f"Error closing resource '{name}': {str(e)}"
                    )
    
    async def get(self, name: str) -> Any:
        """
        Get a resource by name.
        
        Args:
            name: Name of the resource
            
        Returns:
            The resource
            
        Raises:
            ValueError: If the resource doesn't exist
            RuntimeError: If the registry is closed
        """
        if self._closed:
            raise RuntimeError("Resource registry is closed")
        
        async with self._resource_lock:
            if name not in self._resources:
                raise ValueError(f"Resource '{name}' not found")
            
            return self._resources[name]
    
    async def close(self) -> None:
        """
        Close all resources in the registry.
        """
        if self._closed:
            return
        
        self._closed = True
        
        resources_to_close = {}
        
        async with self._resource_lock:
            resources_to_close = dict(self._resources)
            self._resources = {}
        
        # Close resources outside the lock
        for name, resource in resources_to_close.items():
            if hasattr(resource, "close") and callable(resource.close):
                try:
                    await resource.close()
                    self.logger.debug(f"Closed resource: {name}")
                except Exception as e:
                    self.logger.warning(
                        f"Error closing resource '{name}': {str(e)}"
                    )
        
        self.logger.info(f"Resource registry closed ({len(resources_to_close)} resources)")
    
    def get_all_resources(self) -> Dict[str, Any]:
        """
        Get all registered resources.
        
        Returns:
            Dictionary of resources
        """
        return dict(self._resources)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about all resources.
        
        Returns:
            Dictionary of metrics for each resource
        """
        metrics = {}
        
        for name, resource in self._resources.items():
            if hasattr(resource, "get_metrics") and callable(resource.get_metrics):
                try:
                    metrics[name] = resource.get_metrics()
                except Exception as e:
                    self.logger.warning(
                        f"Error getting metrics for resource '{name}': {str(e)}"
                    )
                    metrics[name] = {"error": str(e)}
            else:
                metrics[name] = {"type": type(resource).__name__}
        
        return metrics


def get_resource_registry() -> ResourceRegistry:
    """
    Get an instance of the ResourceRegistry from the DI container.
    
    This function should only be used at application startup or in legacy code.
    New code should use direct dependency injection instead.
    
    Returns:
        A ResourceRegistry instance
    """
    from uno.dependencies.modern_provider import get_service, register_singleton
    
    try:
        # Try to get from the DI container
        return get_service(ResourceRegistry)
    except Exception:
        # If not available, create a new instance
        instance = ResourceRegistry()
        
        # Register in the DI container for future use
        register_singleton(ResourceRegistry, instance)
        return instance


@contextlib.asynccontextmanager
async def managed_resource(resource: Any, name: Optional[str] = None) -> Any:
    """
    Context manager for automatically registering and unregistering a resource.
    
    Args:
        resource: The resource to manage
        name: Optional name for the resource
        
    Yields:
        The resource
    """
    registry = get_resource_registry()
    
    # Generate a name if not provided
    if name is None:
        name = f"{type(resource).__name__}_{id(resource)}"
    
    # Register the resource
    await registry.register(name, resource)
    
    try:
        yield resource
    finally:
        # Unregister the resource
        try:
            await registry.unregister(name)
        except ValueError:
            # Resource might have been unregistered already
            pass


class BackgroundTask:
    """
    Background task that can be managed by the resource registry.
    
    This class wraps a coroutine as a manageable resource with
    lifecycle management and error handling.
    """
    
    def __init__(
        self,
        coro: Callable[[], Awaitable[None]],
        name: str,
        restart_on_failure: bool = False,
        max_restarts: int = 3,
        restart_delay: float = 1.0,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a background task.
        
        Args:
            coro: Coroutine function to run
            name: Name of the task
            restart_on_failure: Whether to restart the task on failure
            max_restarts: Maximum number of restarts
            restart_delay: Delay between restarts in seconds
            logger: Optional logger instance
        """
        self.coro = coro
        self.name = name
        self.restart_on_failure = restart_on_failure
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.logger = logger or logging.getLogger(__name__)
        
        self._task: Optional[asyncio.Task] = None
        self._restart_count = 0
        self._start_time: Optional[float] = None
        self._stop_event = AsyncEvent()
        self._stopped = False
    
    async def start(self) -> None:
        """
        Start the background task.
        
        Raises:
            RuntimeError: If the task is already running or stopped
        """
        if self._task is not None and not self._task.done():
            raise RuntimeError(f"Task {self.name} is already running")
        
        if self._stopped:
            raise RuntimeError(f"Task {self.name} has been stopped")
        
        self._restart_count = 0
        self._start_time = time.time()
        self._stop_event.clear()
        
        # Create the task
        self._task = asyncio.create_task(
            self._run(),
            name=self.name
        )
        
        self.logger.debug(f"Started background task: {self.name}")
    
    async def _run(self) -> None:
        """
        Run the background task with error handling and restart logic.
        """
        while not self._stopped:
            try:
                # Run the coroutine
                await self.coro()
                
                # If we get here, the coroutine completed normally
                self.logger.debug(f"Background task {self.name} completed")
                
                # Exit the loop unless restart_on_failure is True
                if not self.restart_on_failure:
                    break
            
            except asyncio.CancelledError:
                self.logger.debug(f"Background task {self.name} was cancelled")
                break
            
            except Exception as e:
                self.logger.error(
                    f"Error in background task {self.name}: {str(e)}",
                    exc_info=True
                )
                
                # Check if we should restart
                if not self.restart_on_failure:
                    break
                
                self._restart_count += 1
                
                if self._restart_count > self.max_restarts:
                    self.logger.error(
                        f"Background task {self.name} exceeded maximum restarts "
                        f"({self.max_restarts}), stopping"
                    )
                    break
                
                # Wait before restarting
                self.logger.info(
                    f"Restarting background task {self.name} in {self.restart_delay} seconds "
                    f"(attempt {self._restart_count}/{self.max_restarts})"
                )
                
                try:
                    # Wait for restart delay or stop event
                    async with timeout(self.restart_delay):
                        await self._stop_event.wait()
                        
                        # If stop event is set, exit the loop
                        if self._stop_event.is_set():
                            break
                
                except asyncio.TimeoutError:
                    # Restart delay elapsed, continue with the loop
                    pass
    
    async def stop(self) -> None:
        """
        Stop the background task.
        """
        self._stopped = True
        self._stop_event.set()
        
        if self._task and not self._task.done():
            self._task.cancel()
            
            try:
                await self._task
            except asyncio.CancelledError:
                # Expected when cancelling
                pass
            except Exception as e:
                self.logger.warning(
                    f"Error while stopping background task {self.name}: {str(e)}"
                )
        
        self.logger.debug(f"Stopped background task: {self.name}")
    
    async def close(self) -> None:
        """
        Close the background task (alias for stop).
        """
        await self.stop()
    
    def is_running(self) -> bool:
        """
        Check if the task is running.
        
        Returns:
            True if the task is running, False otherwise
        """
        return self._task is not None and not self._task.done()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the background task.
        
        Returns:
            Dictionary of metrics
        """
        uptime = 0.0
        if self._start_time is not None:
            uptime = time.time() - self._start_time
        
        return {
            "name": self.name,
            "running": self.is_running(),
            "restart_count": self._restart_count,
            "uptime": uptime,
        }