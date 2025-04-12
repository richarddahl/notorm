"""
Async manager for coordinating async resources and tasks.

This module provides a central manager for:
- Coordinating async operations throughout the application
- Managing task lifecycle and cancellation
- Handling startup and shutdown sequences
- Integrating with signal handlers
"""

from typing import List, Dict, Any, Optional, Set, Callable, Awaitable, TypeVar, cast
import asyncio
import signal
import logging
import contextlib
import functools
import time
from datetime import datetime

from uno.core.async import (
    TaskGroup,
    TaskManager,
    AsyncLock,
    AsyncEvent,
    AsyncSemaphore,
)

T = TypeVar('T')


class AsyncManager:
    """
    Central manager for async resources and tasks.
    
    This class provides:
    - Lifecycle management for the entire application
    - Graceful shutdown handling
    - Signal handling integration
    - Resource cleanup coordination
    """
    
    # Class instance for global access
    _instance: Optional['AsyncManager'] = None
    
    @classmethod
    def get_instance(cls) -> 'AsyncManager':
        """
        Get the singleton instance of the AsyncManager.
        
        Returns:
            The AsyncManager instance
        """
        if cls._instance is None:
            cls._instance = AsyncManager()
        return cls._instance
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        shutdown_timeout: float = 30.0,
    ):
        """
        Initialize the async manager.
        
        Args:
            logger: Optional logger instance
            shutdown_timeout: Maximum time to wait for shutdown in seconds
        """
        # Only allow one instance
        if AsyncManager._instance is not None:
            raise RuntimeError("AsyncManager is a singleton. Use get_instance() instead.")
        
        AsyncManager._instance = self
        
        self.logger = logger or logging.getLogger(__name__)
        self.shutdown_timeout = shutdown_timeout
        
        # Task management
        self.task_manager = TaskManager(logger=self.logger)
        self.shutdown_event = AsyncEvent()
        
        # Resource tracking
        self._resources: Dict[str, Any] = {}
        self._resource_lock = AsyncLock()
        
        # Lifecycle hooks
        self._startup_hooks: List[Callable[[], Awaitable[None]]] = []
        self._shutdown_hooks: List[Callable[[], Awaitable[None]]] = []
        
        # State tracking
        self._started = False
        self._shutdown_initiated = False
        self._shutdown_complete = False
        
        # Statistics
        self._start_time: Optional[float] = None
        self._shutdown_time: Optional[float] = None
    
    async def start(self) -> None:
        """
        Start the async manager and all registered resources.
        
        This method:
        - Sets up signal handlers
        - Runs startup hooks
        - Initializes resources
        """
        if self._started:
            return
        
        self._start_time = time.time()
        self.logger.info("Starting AsyncManager")
        
        # Set up signal handlers
        self._setup_signal_handlers()
        
        # Start the task manager
        await self.task_manager.start()
        
        # Run startup hooks
        for hook in self._startup_hooks:
            try:
                await hook()
            except Exception as e:
                self.logger.error(f"Error in startup hook: {str(e)}", exc_info=e)
        
        self._started = True
        self.logger.info("AsyncManager started")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        # Get the event loop
        loop = asyncio.get_event_loop()
        
        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_signal(s))
            )
    
    async def _handle_signal(self, sig: signal.Signals) -> None:
        """
        Handle a shutdown signal.
        
        Args:
            sig: The signal that was received
        """
        self.logger.info(f"Received signal {sig.name}, initiating shutdown")
        await self.shutdown()
    
    async def shutdown(self) -> None:
        """
        Shut down the async manager and all managed resources.
        
        This method:
        - Sets the shutdown event
        - Runs shutdown hooks
        - Cancels all tasks
        - Cleans up resources
        """
        if self._shutdown_initiated:
            # Wait for shutdown to complete
            if not self._shutdown_complete:
                await self.shutdown_event.wait()
            return
        
        self._shutdown_initiated = True
        self._shutdown_time = time.time()
        self.logger.info("Initiating AsyncManager shutdown")
        
        try:
            # Run shutdown hooks
            for hook in reversed(self._shutdown_hooks):
                try:
                    await hook()
                except Exception as e:
                    self.logger.error(f"Error in shutdown hook: {str(e)}", exc_info=e)
            
            # Shut down all resources
            await self._shutdown_resources()
            
            # Shut down the task manager with timeout
            await asyncio.wait_for(
                self.task_manager.shutdown(),
                timeout=self.shutdown_timeout,
            )
            
            # Calculate uptime
            if self._start_time is not None and self._shutdown_time is not None:
                uptime = self._shutdown_time - self._start_time
                self.logger.info(f"Application uptime: {uptime:.2f} seconds")
            
            self.logger.info("AsyncManager shutdown complete")
        
        except asyncio.TimeoutError:
            self.logger.error(
                f"Shutdown timed out after {self.shutdown_timeout} seconds. "
                f"Some resources may not have been cleaned up properly."
            )
        
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}", exc_info=e)
        
        finally:
            self._shutdown_complete = True
            self.shutdown_event.set()
    
    async def _shutdown_resources(self) -> None:
        """Shut down all registered resources."""
        async with self._resource_lock:
            # Get all resources
            resources = list(self._resources.items())
            
            # Clear the resources dict
            self._resources = {}
        
        # Shut down resources outside the lock
        for name, resource in resources:
            try:
                self.logger.debug(f"Shutting down resource: {name}")
                
                # Find the appropriate shutdown method
                if hasattr(resource, "shutdown") and callable(resource.shutdown):
                    await resource.shutdown()
                elif hasattr(resource, "close") and callable(resource.close):
                    await resource.close()
                elif hasattr(resource, "__aexit__") and callable(resource.__aexit__):
                    await resource.__aexit__(None, None, None)
                else:
                    self.logger.warning(
                        f"No shutdown method found for resource {name}"
                    )
            
            except Exception as e:
                self.logger.error(
                    f"Error shutting down resource {name}: {str(e)}",
                    exc_info=e
                )
    
    async def wait_for_shutdown(self) -> None:
        """Wait for the shutdown event to be set."""
        await self.shutdown_event.wait()
    
    def create_task(self, coro: Awaitable[T], name: Optional[str] = None) -> asyncio.Task[T]:
        """
        Create a managed task.
        
        Args:
            coro: The coroutine to run as a task
            name: Optional name for the task
            
        Returns:
            The created task
        """
        return self.task_manager.create_task(coro, name=name)
    
    async def register_resource(
        self,
        resource: Any,
        name: Optional[str] = None,
    ) -> None:
        """
        Register a resource to be managed.
        
        Args:
            resource: The resource to manage
            name: Optional name for the resource
        """
        resource_name = name or f"{type(resource).__name__}_{id(resource):x}"
        
        async with self._resource_lock:
            self._resources[resource_name] = resource
    
    async def unregister_resource(
        self,
        resource: Any,
        name: Optional[str] = None,
    ) -> None:
        """
        Unregister a managed resource.
        
        Args:
            resource: The resource to unmanage
            name: Optional name for the resource
        """
        resource_name = name or f"{type(resource).__name__}_{id(resource):x}"
        
        async with self._resource_lock:
            if resource_name in self._resources:
                del self._resources[resource_name]
    
    def add_startup_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """
        Add a startup hook function.
        
        Args:
            hook: The hook function to call during startup
        """
        self._startup_hooks.append(hook)
    
    def add_shutdown_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """
        Add a shutdown hook function.
        
        Args:
            hook: The hook function to call during shutdown
        """
        self._shutdown_hooks.append(hook)
    
    def is_shutting_down(self) -> bool:
        """
        Check if the manager is shutting down.
        
        Returns:
            True if shutdown has been initiated
        """
        return self._shutdown_initiated
    
    @contextlib.asynccontextmanager
    async def task_group(self, name: Optional[str] = None) -> AsyncIterator[TaskGroup]:
        """
        Create a new task group within the manager.
        
        Args:
            name: Optional name for the task group
            
        Yields:
            A TaskGroup instance
        """
        group = TaskGroup(name=name, logger=self.logger)
        
        try:
            await group.__aenter__()
            yield group
        finally:
            await group.__aexit__(None, None, None)
    
    @property
    def uptime(self) -> float:
        """
        Get the application uptime in seconds.
        
        Returns:
            The uptime in seconds
        """
        if self._start_time is None:
            return 0.0
        
        end_time = self._shutdown_time or time.time()
        return end_time - self._start_time
    
    @property
    def start_datetime(self) -> Optional[datetime]:
        """
        Get the start time as a datetime.
        
        Returns:
            The start datetime or None if not started
        """
        if self._start_time is None:
            return None
        
        return datetime.fromtimestamp(self._start_time)


# Create a function to get the global instance
def get_async_manager() -> AsyncManager:
    """
    Get the global AsyncManager instance.
    
    Returns:
        The AsyncManager instance
    """
    return AsyncManager.get_instance()


# Create a decorator to run a function as a managed task
def as_task(name: Optional[str] = None) -> Callable:
    """
    Decorator to run a function as a managed task.
    
    Args:
        name: Optional name for the task
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., asyncio.Task[T]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> asyncio.Task[T]:
            manager = get_async_manager()
            return manager.create_task(
                func(*args, **kwargs),
                name=name or func.__name__
            )
        return wrapper
    return decorator


# Create a function to run the application with the async manager
async def run_application(
    startup_func: Callable[[], Awaitable[None]],
    cleanup_func: Optional[Callable[[], Awaitable[None]]] = None,
) -> None:
    """
    Run an application with the AsyncManager.
    
    Args:
        startup_func: Function to run at startup
        cleanup_func: Optional function to run at shutdown
    """
    manager = get_async_manager()
    
    # Add hooks
    manager.add_startup_hook(startup_func)
    if cleanup_func is not None:
        manager.add_shutdown_hook(cleanup_func)
    
    # Start the manager
    await manager.start()
    
    # Wait for shutdown signal
    await manager.wait_for_shutdown()