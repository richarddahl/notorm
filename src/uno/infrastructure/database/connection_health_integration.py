# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Connection health monitoring integration with enhanced connection pool.

This module provides the integration between the connection health monitoring
system and the enhanced connection pool, enabling automatic health monitoring
and connection recycling for database connections.
"""

from typing import (
    Dict,
    List,
    Set,
    Optional,
    Any,
    Callable,
    Awaitable,
    Tuple,
    Union,
    TypeVar,
    cast,
)
import asyncio
import logging
import time
import contextlib
import uuid
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection

from uno.database.connection_health import (
    ConnectionHealthMonitor,
    ConnectionRecycler,
    ConnectionHealthState,
    ConnectionHealthMetrics,
    ConnectionIssue,
    ConnectionHealthAssessment,
    setup_connection_health_monitoring,
)
from uno.database.enhanced_connection_pool import (
    EnhancedConnectionPool,
    EnhancedAsyncEnginePool,
    EnhancedAsyncConnectionManager,
)
from uno.core.asynchronous import AsyncLock


class HealthAwareConnectionPool(EnhancedConnectionPool):
    """
    Health-aware connection pool with integrated health monitoring.

    This enhanced connection pool integrates with the connection health
    monitoring system to automatically detect and remediate connection
    health issues, ensuring optimal database performance.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the health-aware connection pool.

        Takes the same arguments as EnhancedConnectionPool, with additional
        health monitoring related configuration options.
        """
        # Extract health monitoring options
        health_check_interval = kwargs.pop("health_check_interval", 60.0)
        recycling_interval = kwargs.pop("recycling_interval", 300.0)

        # Initialize base class
        super().__init__(*args, **kwargs)

        # Health monitoring components
        self._health_monitor: Optional[ConnectionHealthMonitor] = None
        self._connection_recycler: Optional[ConnectionRecycler] = None

        # Health monitoring configuration
        self._health_check_interval = health_check_interval
        self._recycling_interval = recycling_interval

        # Connection health tracking
        self._health_states: dict[str, ConnectionHealthState] = {}

        # Synchronization
        self._health_lock = AsyncLock()

    async def start(self) -> None:
        """
        Start the connection pool with health monitoring.

        Initializes both the pool and the health monitoring components.
        """
        # Start the pool
        await super().start()

        # Create and start health monitoring
        await self._setup_health_monitoring()

    async def _setup_health_monitoring(self) -> None:
        """
        Set up the health monitoring system.

        Creates and configures the connection health monitor and recycler.
        """

        # Create a connection provider for monitoring
        async def connection_provider() -> AsyncConnection:
            # Get a connection from the pool
            conn_id, connection = await self.acquire()
            try:
                # For AsyncConnection objects
                if hasattr(connection, "connection"):
                    return connection
                # For other connection types, wrap in a context manager
                # that returns the connection itself
                return _ConnectionWrapper(conn_id, connection, self)
            except:
                # Release the connection on error
                await self.release(conn_id)
                raise

        # Create the health monitor and recycler
        health_monitor, recycler = await setup_connection_health_monitoring(
            pool_name=self.name,
            recycling_callback=self._handle_connection_recycling,
            connection_provider=connection_provider,
            logger=self.logger,
        )

        self._health_monitor = health_monitor
        self._connection_recycler = recycler

        # Register health change callback
        health_monitor.register_health_change_callback(self._handle_health_change)

        # Register issue detection callback
        health_monitor.register_issue_detected_callback(self._handle_issue_detected)

        # Log initialization
        self.logger.info(
            f"Initialized health monitoring for pool {self.name} "
            f"with check interval: {self._health_check_interval}s, "
            f"recycling interval: {self._recycling_interval}s"
        )

    async def _handle_health_change(
        self,
        connection_id: str,
        old_state: ConnectionHealthState,
        new_state: ConnectionHealthState,
    ) -> None:
        """
        Handle a connection health state change.

        Args:
            connection_id: ID of the connection
            old_state: Previous health state
            new_state: New health state
        """
        # Update health state tracking
        async with self._health_lock:
            self._health_states[connection_id] = new_state

        # Log the change
        self.logger.info(
            f"Connection {connection_id} health changed: "
            f"{old_state.value} -> {new_state.value}"
        )

        # Take action based on the new state
        if new_state == ConnectionHealthState.UNHEALTHY:
            # Mark for immediate recycling if unhealthy
            if self._connection_recycler:
                await self._connection_recycler.mark_for_recycling(
                    connection_id,
                    f"Health state changed to UNHEALTHY from {old_state.value}",
                )

    async def _handle_issue_detected(
        self, connection_id: str, issue: ConnectionIssue
    ) -> None:
        """
        Handle a detected connection issue.

        Args:
            connection_id: ID of the connection
            issue: The detected issue
        """
        # Log the issue
        self.logger.warning(
            f"Issue detected for connection {connection_id}: "
            f"{issue.issue_type.value} - {issue.description} "
            f"(severity: {issue.severity:.2f})"
        )

        # For high severity issues, mark for recycling
        if issue.severity > 0.7 and self._connection_recycler:
            await self._connection_recycler.mark_for_recycling(
                connection_id,
                f"High severity issue: {issue.issue_type.value} - {issue.description}",
            )

    async def _handle_connection_recycling(
        self, connection_id: str, reason: str
    ) -> None:
        """
        Handle a connection recycling request.

        Args:
            connection_id: ID of the connection to recycle
            reason: Reason for recycling
        """
        self.logger.info(f"Recycling connection {connection_id}: {reason}")

        # Check if connection exists and is still in the pool
        async with self._pool_lock:
            if connection_id not in self._connections:
                self.logger.info(f"Connection {connection_id} not found for recycling")
                return

            # Check if connection is in use
            if self._connections[connection_id]["in_use"]:
                self.logger.info(
                    f"Connection {connection_id} is in use, marking for recycling when released"
                )
                # We'll close it when it's released
                # Flag in the connection info that it should be recycled
                self._connections[connection_id]["recycle_on_release"] = True
                return

            # Remove from available set
            self._available_conn_ids.discard(connection_id)

        # Close the connection outside the lock
        await self._close_connection(connection_id)

        # Add a new connection to maintain pool size
        await self._add_connection()

    async def release(self, conn_id: str) -> None:
        """
        Release a connection back to the pool.

        Args:
            conn_id: ID of the connection to release

        Raises:
            ValueError: If the connection is not found in the pool
        """
        if self._closed:
            # If pool is closed, close the connection instead of returning to pool
            await self._close_connection(conn_id)
            return

        recycle_connection = False

        # Check if connection needs recycling
        async with self._pool_lock:
            if conn_id in self._connections:
                # Check if connection is marked for recycling
                if self._connections[conn_id].get("recycle_on_release", False):
                    recycle_connection = True

                # Check health state
                health_state = self._health_states.get(
                    conn_id, ConnectionHealthState.UNKNOWN
                )
                if health_state == ConnectionHealthState.UNHEALTHY:
                    recycle_connection = True

        if recycle_connection:
            # Recycle the connection (close and create a new one)
            self.logger.info(f"Recycling connection {conn_id} on release")
            await self._close_connection(conn_id)
            await self._add_connection()
            return

        # Otherwise, release normally
        await super().release(conn_id)

        # Record usage for health monitoring
        if self._health_monitor:
            await self._health_monitor.record_connection_usage(conn_id)

    async def acquire(self) -> Tuple[str, Any]:
        """
        Acquire a connection from the pool.

        Returns:
            Tuple of (connection_id, connection)
        """
        conn_id, connection = await super().acquire()

        # Record connection usage for health monitoring
        if self._health_monitor:
            await self._health_monitor.record_connection_usage(conn_id)

        return conn_id, connection

    async def _execute_with_connection(
        self, conn_id: str, func: Callable[[Any], Awaitable[T]]
    ) -> T:
        """
        Execute a function with a connection, with health monitoring.

        Args:
            conn_id: ID of the connection
            func: Function to execute with the connection

        Returns:
            Result of the function
        """
        start_time = time.time()
        error_type = None

        try:
            # Execute the function
            result = await func()

            # Record query execution
            if self._health_monitor:
                await self._health_monitor.record_query(
                    conn_id, time.time() - start_time
                )

            return result

        except Exception as e:
            # Record error
            if self._health_monitor:
                # Determine error type
                error_str = str(e)
                if "timeout" in error_str.lower():
                    error_type = "timeout"
                elif "deadlock" in error_str.lower():
                    error_type = "deadlock"

                await self._health_monitor.record_error(conn_id, error_type)

            raise

    async def close(self) -> None:
        """
        Close the connection pool.

        Stops health monitoring and closes all connections.
        """
        # Stop health monitoring components
        if self._health_monitor:
            await self._health_monitor.stop_monitoring()

        if self._connection_recycler:
            await self._connection_recycler.stop_recycling()

        # Close the pool
        await super().close()

    def get_health_metrics(self) -> dict[str, Any]:
        """
        Get health metrics for the connection pool.

        Returns:
            Dictionary of health metrics
        """
        metrics = {
            "health_states": {
                conn_id: state.value for conn_id, state in self._health_states.items()
            },
        }

        # Add monitor metrics
        if self._health_monitor:
            metrics["monitor"] = self._health_monitor.get_metrics()

        # Add recycler metrics
        if self._connection_recycler:
            metrics["recycler"] = self._connection_recycler.get_metrics()

        return metrics

    def get_detailed_metrics(self) -> dict[str, Any]:
        """
        Get detailed metrics for the connection pool.

        Returns:
            Dictionary of detailed metrics including health information
        """
        # Get base metrics
        metrics = super().get_detailed_metrics()

        # Add health metrics
        health_metrics = self.get_health_metrics()
        metrics["health"] = health_metrics

        return metrics


class _ConnectionWrapper:
    """
    A simple wrapper for connections to be used with health monitoring.

    This wrapper ensures connections are returned to the pool after
    being used by the health monitoring system.
    """

    def __init__(self, conn_id: str, connection: Any, pool: EnhancedConnectionPool):
        """
        Initialize the connection wrapper.

        Args:
            conn_id: ID of the connection
            connection: The connection object
            pool: The connection pool
        """
        self.conn_id = conn_id
        self.connection = connection
        self.pool = pool

    async def __aenter__(self):
        """Enter async context, return the connection."""
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context, return connection to pool."""
        await self.pool.release(self.conn_id)


class HealthAwareAsyncEnginePool(EnhancedAsyncEnginePool):
    """
    Health-aware pool for AsyncEngine instances.

    Provides a specialized connection pool for SQLAlchemy AsyncEngine
    instances with integrated health monitoring.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the health-aware async engine pool.

        Takes the same arguments as EnhancedAsyncEnginePool, with additional
        health monitoring related configuration options.
        """
        # Extract health monitoring options
        health_check_interval = kwargs.pop("health_check_interval", 60.0)
        recycling_interval = kwargs.pop("recycling_interval", 300.0)

        # Initialize base class
        super().__init__(*args, **kwargs)

        # Health monitoring configuration
        self._health_check_interval = health_check_interval
        self._recycling_interval = recycling_interval

    async def start(self) -> None:
        """
        Start the engine pool with health monitoring.

        Initializes the pool with a health-aware connection pool.
        """
        if self.pool is not None:
            return

        # Create factory function
        async def engine_factory() -> AsyncEngine:
            from sqlalchemy.ext.asyncio import create_async_engine

            # Create connection string
            conn_str = (
                f"{self.config.db_driver}://{self.config.db_role}:{self.config.db_user_pw}"
                f"@{self.config.db_host}:{self.config.db_port or 5432}/{self.config.db_name}"
            )

            # Create the engine with SQLAlchemy's connection pooling disabled
            engine = create_async_engine(
                conn_str,
                echo=False,
                future=True,
                poolclass=None,  # Disable SQLAlchemy's connection pooling
                connect_args={
                    "command_timeout": self.pool_config.connection_timeout,
                },
                **self.config.kwargs,
            )

            return engine

        # Create close function
        async def engine_close(engine: AsyncEngine) -> None:
            await engine.dispose()

        # Create validation function
        async def engine_validate(engine: AsyncEngine) -> bool:
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                    return True
            except Exception as e:
                self.logger.warning(f"Engine validation failed: {str(e)}")
                return False

        # Create reset function
        async def engine_reset(engine: AsyncEngine) -> None:
            # Just dispose and let SQLAlchemy create a new connection
            await engine.dispose()

        # Create the pool as a health-aware pool
        self.pool = HealthAwareConnectionPool(
            name=f"engine_pool_{self.name}",
            factory=engine_factory,
            close_func=engine_close,
            validate_func=engine_validate,
            reset_func=engine_reset,
            config=self.pool_config,
            resource_registry=self.resource_registry,
            logger=self.logger,
            health_check_interval=self._health_check_interval,
            recycling_interval=self._recycling_interval,
        )

        # Start the pool
        await self.pool.start()

    def get_health_metrics(self) -> dict[str, Any]:
        """
        Get health metrics for the engine pool.

        Returns:
            Dictionary of health metrics
        """
        if not self.pool or not isinstance(self.pool, HealthAwareConnectionPool):
            return {}

        return self.pool.get_health_metrics()


class HealthAwareAsyncConnectionManager(EnhancedAsyncConnectionManager):
    """
    Health-aware manager for AsyncEngine and AsyncConnection pools.

    Provides centralized management of database connections with
    integrated health monitoring.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the health-aware async connection manager.

        Takes the same arguments as EnhancedAsyncConnectionManager.
        """
        super().__init__(*args, **kwargs)

        # Replace engine pools with health-aware pools
        self._engine_pools: dict[str, HealthAwareAsyncEnginePool] = {}

    async def get_engine_pool(
        self,
        config: Any,  # ConnectionConfig
    ) -> HealthAwareAsyncEnginePool:
        """
        Get or create a health-aware engine pool for a connection configuration.

        Args:
            config: Connection configuration

        Returns:
            Health-aware engine pool
        """
        # Create a pool name
        pool_name = f"{config.db_role}@{config.db_host}/{config.db_name}"

        async with self._manager_lock:
            # Check if pool exists
            if pool_name in self._engine_pools:
                return self._engine_pools[pool_name]

            # Get the pool configuration
            pool_config = self.get_pool_config(config.db_role)

            # Create the health-aware pool
            pool = HealthAwareAsyncEnginePool(
                name=pool_name,
                config=config,
                pool_config=pool_config,
                resource_registry=self.resource_registry,
                logger=self.logger,
            )

            # Start the pool
            await pool.start()

            # Store in dictionary
            self._engine_pools[pool_name] = pool

            return pool

    def get_health_metrics(self) -> dict[str, Any]:
        """
        Get health metrics for all pools.

        Returns:
            Dictionary of health metrics by pool name
        """
        metrics = {}

        for name, pool in self._engine_pools.items():
            metrics[name] = pool.get_health_metrics()

        return metrics


# Global health-aware connection manager
_health_aware_connection_manager: Optional[HealthAwareAsyncConnectionManager] = None


def get_health_aware_connection_manager() -> HealthAwareAsyncConnectionManager:
    """
    Get the global health-aware connection manager.

    Returns:
        Global health-aware connection manager instance
    """
    global _health_aware_connection_manager
    if _health_aware_connection_manager is None:
        _health_aware_connection_manager = HealthAwareAsyncConnectionManager()
    return _health_aware_connection_manager


@contextlib.asynccontextmanager
async def health_aware_async_engine(
    db_driver: str = "postgresql+asyncpg",
    db_name: str = "uno",
    db_user_pw: str = "password",
    db_role: str = "uno_login",
    db_host: str | None = "localhost",
    db_port: Optional[int] = 5432,
    **kwargs: Any,
) -> AsyncEngine:
    """
    Context manager for health-aware async engines.

    This context manager provides a health-monitored AsyncEngine
    with automatic connection recycling and health checks.

    Args:
        db_driver: Database driver
        db_name: Database name
        db_user_pw: Database password
        db_role: Database role
        db_host: Database host
        db_port: Database port
        **kwargs: Additional connection parameters

    Yields:
        AsyncEngine instance
    """
    # Import inside function to avoid circular imports
    from uno.database.config import ConnectionConfig

    # Create connection config
    config = ConnectionConfig(
        db_role=db_role,
        db_name=db_name,
        db_host=db_host,
        db_user_pw=db_user_pw,
        db_driver=db_driver,
        db_port=db_port,
        **kwargs,
    )

    # Get connection manager
    manager = get_health_aware_connection_manager()

    # Get engine from pool
    async with manager.engine(config) as engine:
        yield engine


@contextlib.asynccontextmanager
async def health_aware_async_connection(
    db_driver: str = "postgresql+asyncpg",
    db_name: str = "uno",
    db_user_pw: str = "password",
    db_role: str = "uno_login",
    db_host: str | None = "localhost",
    db_port: Optional[int] = 5432,
    isolation_level: str = "AUTOCOMMIT",
    **kwargs: Any,
) -> AsyncConnection:
    """
    Context manager for health-aware async connections.

    This context manager provides a health-monitored AsyncConnection
    with automatic connection recycling and health checks.

    Args:
        db_driver: Database driver
        db_name: Database name
        db_user_pw: Database password
        db_role: Database role
        db_host: Database host
        db_port: Database port
        isolation_level: SQL transaction isolation level
        **kwargs: Additional connection parameters

    Yields:
        AsyncConnection instance
    """
    # Import inside function to avoid circular imports
    from uno.database.config import ConnectionConfig

    # Create connection config
    config = ConnectionConfig(
        db_role=db_role,
        db_name=db_name,
        db_host=db_host,
        db_user_pw=db_user_pw,
        db_driver=db_driver,
        db_port=db_port,
        **kwargs,
    )

    # Get connection manager
    manager = get_health_aware_connection_manager()

    # Get connection
    async with manager.connection(
        config=config,
        isolation_level=isolation_level,
    ) as connection:
        yield connection
