"""
Resource management integration for the Uno framework.

This module provides utilities for integrating resource management with 
the application lifecycle, including startup and shutdown hooks.
"""

from typing import Dict, Any, Optional, List, Set, Union, TypeVar, Callable, Awaitable
import asyncio
import logging
import time
import signal
import contextlib
import functools

from uno.core.async_manager import (
    get_async_manager,
    AsyncManager,
)
from uno.core.resources import (
    ResourceRegistry,
    get_resource_registry,
    ConnectionPool,
    CircuitBreaker,
    BackgroundTask,
    managed_resource,
)
from uno.core.resource_monitor import (
    ResourceMonitor,
    get_resource_monitor,
    start_resource_monitoring,
    stop_resource_monitoring,
)
from uno.database.engine.pooled_async import (
    PooledAsyncEngineFactory,
)
from uno.database.pooled_session import (
    PooledAsyncSessionFactory,
)
from uno.settings import uno_settings


T = TypeVar('T')


# Module-level singleton instance
_resource_manager_instance: Optional['ResourceManager'] = None


def get_resource_manager(logger: Optional[logging.Logger] = None) -> 'ResourceManager':
    """
    Get the global resource manager.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        The resource manager instance
    """
    global _resource_manager_instance
    
    if _resource_manager_instance is None:
        _resource_manager_instance = ResourceManager(logger)
    
    return _resource_manager_instance


class ResourceManager:
    """
    Resource manager for the Uno framework.
    
    This class provides centralized resource management, including:
    - Lifecycle management (startup/shutdown)
    - Resource registration
    - Monitoring integration
    - Graceful shutdown handling
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the resource manager.
        
        Args:
            logger: Optional logger instance
        """
        
        # Initialize components
        self.logger = logger or logging.getLogger(__name__)
        self.async_manager = get_async_manager()
        self.resource_registry = get_resource_registry()
        self.resource_monitor = get_resource_monitor()
        
        # Track initialization
        self._initialized = False
        self._shutting_down = False
        self._startup_hooks: List[Callable[[], Awaitable[None]]] = []
        self._shutdown_hooks: List[Callable[[], Awaitable[None]]] = []
    
    async def initialize(self) -> None:
        """
        Initialize the resource manager.
        
        This sets up signal handlers, integrates with the async manager,
        and registers with the resource registry.
        """
        if self._initialized:
            return
        
        # Register startup and shutdown hooks with async manager
        self.async_manager.add_startup_hook(self._on_startup)
        self.async_manager.add_shutdown_hook(self._on_shutdown)
        
        # Register with resource registry
        await self.resource_registry.register("resource_manager", self)
        
        self._initialized = True
        self.logger.info("Resource manager initialized")
    
    async def _on_startup(self) -> None:
        """
        Handle application startup.
        
        This starts the resource monitor and runs startup hooks.
        """
        self.logger.info("Starting resource management")
        
        # Start resource monitoring
        await start_resource_monitoring()
        
        # Run startup hooks
        for hook in self._startup_hooks:
            try:
                await hook()
            except Exception as e:
                self.logger.error(f"Error in startup hook: {str(e)}", exc_info=True)
    
    async def _on_shutdown(self) -> None:
        """
        Handle application shutdown.
        
        This performs graceful shutdown, runs shutdown hooks,
        and stops resource monitoring.
        """
        if self._shutting_down:
            return
        
        self._shutting_down = True
        self.logger.info("Shutting down resource management")
        
        # Run shutdown hooks in reverse order
        for hook in reversed(self._shutdown_hooks):
            try:
                await hook()
            except Exception as e:
                self.logger.error(f"Error in shutdown hook: {str(e)}", exc_info=True)
        
        # Stop resource monitoring
        try:
            await stop_resource_monitoring()
        except Exception as e:
            self.logger.warning(f"Error stopping resource monitor: {str(e)}")
        
        # Close resource registry (this closes all registered resources)
        try:
            await self.resource_registry.close()
        except Exception as e:
            self.logger.warning(f"Error closing resource registry: {str(e)}")
        
        self.logger.info("Resource management shutdown complete")
    
    def add_startup_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """
        Add a hook to run during startup.
        
        Args:
            hook: Async function to run during startup
        """
        self._startup_hooks.append(hook)
    
    def add_shutdown_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """
        Add a hook to run during shutdown.
        
        Args:
            hook: Async function to run during shutdown
        """
        self._shutdown_hooks.append(hook)
    
    async def create_database_pools(self) -> Dict[str, ConnectionPool]:
        """
        Create database connection pools.
        
        This creates connection pools for common database roles.
        
        Returns:
            Dictionary of connection pools
        """
        # Create engine factory
        engine_factory = PooledAsyncEngineFactory(
            resource_registry=self.resource_registry,
            logger=self.logger,
        )
        
        # Register with resource registry
        await self.resource_registry.register(
            "pooled_engine_factory",
            engine_factory
        )
        
        # Create pools for common roles
        pools = {}
        roles = [
            f"{uno_settings.DB_NAME}_login",
            f"{uno_settings.DB_NAME}_admin",
            f"{uno_settings.DB_NAME}_app",
        ]
        
        for role in roles:
            try:
                # Create engine pool
                pool = await engine_factory.create_engine_pool(
                    config=self._get_db_config(role),
                    pool_size=10,
                    min_size=2,
                )
                
                pools[role] = pool
                self.logger.info(f"Created connection pool for role '{role}'")
            
            except Exception as e:
                self.logger.error(
                    f"Error creating connection pool for role '{role}': {str(e)}"
                )
        
        return pools
    
    async def create_session_factory(self) -> PooledAsyncSessionFactory:
        """
        Create a pooled session factory.
        
        Returns:
            Pooled async session factory
        """
        # Create engine factory
        engine_factory = PooledAsyncEngineFactory(
            resource_registry=self.resource_registry,
            logger=self.logger,
        )
        
        # Create session factory
        session_factory = PooledAsyncSessionFactory(
            engine_factory=engine_factory,
            resource_registry=self.resource_registry,
            logger=self.logger,
        )
        
        # Register with resource registry
        await self.resource_registry.register(
            "pooled_session_factory",
            session_factory
        )
        
        self.logger.info("Created pooled session factory")
        return session_factory
    
    def _get_db_config(self, role: str) -> 'uno.database.config.ConnectionConfig':
        """
        Get database configuration for a role.
        
        Args:
            role: Database role
            
        Returns:
            Connection configuration
        """
        from uno.database.config import ConnectionConfig
        
        return ConnectionConfig(
            db_role=role,
            db_name=uno_settings.DB_NAME,
            db_host=uno_settings.DB_HOST,
            db_user_pw=uno_settings.DB_USER_PW,
            db_driver=uno_settings.DB_ASYNC_DRIVER,
            db_port=uno_settings.DB_PORT,
        )


# Function already defined above


async def initialize_resources() -> None:
    """
    Initialize application resources.
    
    This initializes the resource manager and creates common resources.
    """
    # Initialize resource manager
    manager = get_resource_manager()
    await manager.initialize()
    
    # Add startup hooks
    manager.add_startup_hook(_create_database_resources)


async def _create_database_resources() -> None:
    """
    Create common database resources during startup.
    """
    manager = get_resource_manager()
    
    # Create database pools
    await manager.create_database_pools()
    
    # Create session factory
    await manager.create_session_factory()


@contextlib.asynccontextmanager
async def managed_connection_pool(
    name: str,
    factory: Callable[[], Awaitable[ConnectionPool]],
) -> ConnectionPool:
    """
    Context manager for a managed connection pool.
    
    Args:
        name: Name for the pool
        factory: Function to create the pool
        
    Yields:
        Connection pool
    """
    # Create the pool
    pool = await factory()
    
    # Register with resource registry
    registry = get_resource_registry()
    await registry.register(name, pool)
    
    try:
        # Start the pool
        await pool.start()
        
        yield pool
    finally:
        # Close the pool
        await pool.close()
        
        # Unregister from registry
        try:
            await registry.unregister(name)
        except ValueError:
            # Pool might already be unregistered
            pass


@contextlib.asynccontextmanager
async def managed_background_task(
    name: str,
    coro: Callable[[], Awaitable[None]],
    restart_on_failure: bool = False,
) -> BackgroundTask:
    """
    Context manager for a managed background task.
    
    Args:
        name: Name for the task
        coro: Coroutine function to run
        restart_on_failure: Whether to restart on failure
        
    Yields:
        Background task
    """
    # Create the task
    task = BackgroundTask(
        coro=coro,
        name=name,
        restart_on_failure=restart_on_failure,
    )
    
    # Register with resource registry
    registry = get_resource_registry()
    await registry.register(name, task)
    
    try:
        # Start the task
        await task.start()
        
        yield task
    finally:
        # Stop the task
        await task.stop()
        
        # Unregister from registry
        try:
            await registry.unregister(name)
        except ValueError:
            # Task might already be unregistered
            pass