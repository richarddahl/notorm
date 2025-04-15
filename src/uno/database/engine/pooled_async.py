"""
Pooled async database engine with resource management.

This module extends the enhanced async database engine with:
- Connection pooling
- Health checking
- Circuit breaker pattern
- Resource registry integration
"""

from typing import Optional, AsyncIterator, TypeVar, Dict, Any, List, cast
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.engine.enhanced_async import (
    EnhancedAsyncEngineFactory,
    AsyncConnectionContext,
)
from uno.core.resources import (
    ConnectionPool,
    CircuitBreaker,
    ResourceRegistry,
    get_resource_registry,
)
from uno.core.async_utils import (
    timeout,
    AsyncLock,
    Limiter,
)
from uno.core.async_integration import (
    cancellable,
    retry,
)
from uno.settings import uno_settings


T = TypeVar("T")


class PooledAsyncEngineFactory(EnhancedAsyncEngineFactory):
    """
    Factory for creating pooled asynchronous database engines.

    This factory extends the enhanced async engine factory with:
    - Connection pooling
    - Health checking
    - Circuit breaker pattern
    """

    def __init__(
        self,
        resource_registry: Optional[ResourceRegistry] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the pooled async engine factory.

        Args:
            resource_registry: Optional resource registry
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self.resource_registry = resource_registry or get_resource_registry()
        self._engine_pools: Dict[str, ConnectionPool[AsyncEngine]] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._registry_lock = AsyncLock()

    async def create_engine_pool(
        self,
        config: ConnectionConfig,
        pool_size: int = 10,
        min_size: int = 2,
        max_idle: int = 3,
        ttl: float = 600.0,
        validation_interval: float = 60.0,
    ) -> ConnectionPool[AsyncEngine]:
        """
        Create or get a connection pool for a configuration.

        Args:
            config: Connection configuration
            pool_size: Maximum pool size
            min_size: Minimum pool size
            max_idle: Maximum idle connections
            ttl: Time-to-live for connections
            validation_interval: Time between validation checks

        Returns:
            A connection pool for the configuration
        """
        # Create a key from connection details
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"

        # Check if pool already exists
        async with self._registry_lock:
            if conn_key in self._engine_pools:
                return self._engine_pools[conn_key]

            # Create a factory function for the pool
            async def engine_factory() -> AsyncEngine:
                return self.create_engine(config)

            # Create a close function for the pool
            async def engine_close(engine: AsyncEngine) -> None:
                await engine.dispose()

            # Create a validation function for the pool
            async def engine_validate(engine: AsyncEngine) -> bool:
                try:
                    async with timeout(5.0, "Engine validation timeout"):
                        async with engine.connect() as conn:
                            # Execute a simple query to verify connection
                            await conn.execute("SELECT 1")
                            return True
                except Exception as e:
                    self.logger.warning(
                        f"Engine validation failed for {conn_key}: {str(e)}"
                    )
                    return False

            # Create the pool
            pool = ConnectionPool(
                name=f"engine_pool_{conn_key}",
                factory=engine_factory,
                close_func=engine_close,
                validate_func=engine_validate,
                max_size=pool_size,
                min_size=min_size,
                max_idle=max_idle,
                ttl=ttl,
                validation_interval=validation_interval,
                logger=self.logger,
            )

            # Start the pool
            await pool.start()

            # Register the pool with the registry
            await self.resource_registry.register(f"engine_pool_{conn_key}", pool)

            # Store in our internal dictionary
            self._engine_pools[conn_key] = pool

            return pool

    async def get_circuit_breaker(
        self,
        config: ConnectionConfig,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> CircuitBreaker:
        """
        Get a circuit breaker for a configuration.

        Args:
            config: Connection configuration
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds to wait before trying recovery

        Returns:
            A circuit breaker for the configuration
        """
        # Create a key from connection details
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"

        # Check if circuit breaker already exists
        async with self._registry_lock:
            if conn_key in self._circuit_breakers:
                return self._circuit_breakers[conn_key]

            # Create the circuit breaker
            circuit_breaker = CircuitBreaker(
                name=f"db_circuit_{conn_key}",
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                exception_types=[
                    SQLAlchemyError,
                    asyncio.TimeoutError,
                    ConnectionError,
                    OSError,
                ],
                logger=self.logger,
            )

            # Register the circuit breaker with the registry
            await self.resource_registry.register(
                f"db_circuit_{conn_key}", circuit_breaker
            )

            # Store in our internal dictionary
            self._circuit_breakers[conn_key] = circuit_breaker

            return circuit_breaker

    @cancellable
    @retry(max_attempts=3, base_delay=1.0, max_delay=10.0)
    async def get_pooled_engine(
        self,
        config: ConnectionConfig,
        pool_size: int = 10,
        min_size: int = 2,
    ) -> AsyncEngine:
        """
        Get an engine from a connection pool.

        Args:
            config: Connection configuration
            pool_size: Maximum pool size
            min_size: Minimum pool size

        Returns:
            An engine from the pool

        Raises:
            Exception: If engine acquisition fails
        """
        # Get the pool
        pool = await self.create_engine_pool(
            config,
            pool_size=pool_size,
            min_size=min_size,
        )

        # Get the circuit breaker
        circuit_breaker = await self.get_circuit_breaker(config)

        # Use the circuit breaker to get an engine
        return await circuit_breaker(pool.acquire)

    async def close(self) -> None:
        """
        Close all engine pools and circuit breakers.
        """
        # Get all pools and circuit breakers
        async with self._registry_lock:
            pools = list(self._engine_pools.values())
            circuit_breakers = list(self._circuit_breakers.values())
            self._engine_pools = {}
            self._circuit_breakers = {}

        # Close all pools
        for pool in pools:
            try:
                await pool.close()
            except Exception as e:
                self.logger.warning(f"Error closing engine pool: {str(e)}")

        # No need to close circuit breakers as they don't have resources

        self.logger.info(
            f"Closed all engine pools ({len(pools)}) and circuit breakers ({len(circuit_breakers)})"
        )


class PooledAsyncConnectionContext(AsyncConnectionContext):
    """
    Context manager for pooled asynchronous database connections.

    This context manager extends the async connection context with
    connection pooling and circuit breaker support.
    """

    def __init__(
        self,
        db_role: str,
        db_name: Optional[str] = None,
        db_host: Optional[str] = None,
        db_user_pw: Optional[str] = None,
        db_driver: Optional[str] = None,
        db_port: Optional[int] = None,
        config: Optional[ConnectionConfig] = None,
        isolation_level: str = "AUTOCOMMIT",
        factory: Optional[PooledAsyncEngineFactory] = None,
        pool_size: int = 10,
        min_size: int = 2,
        logger: Optional[logging.Logger] = None,
        **kwargs: Any,
    ):
        """
        Initialize the pooled async connection context.

        Args:
            db_role: Database role
            db_name: Database name
            db_host: Database host
            db_user_pw: Database password
            db_driver: Database driver
            db_port: Database port
            config: Optional connection configuration
            isolation_level: SQL transaction isolation level
            factory: Optional engine factory
            pool_size: Maximum pool size
            min_size: Minimum pool size
            logger: Optional logger instance
            **kwargs: Additional connection parameters
        """
        # Initialize the parent class
        super().__init__(
            db_role=db_role,
            db_name=db_name,
            db_host=db_host,
            db_user_pw=db_user_pw,
            db_driver=db_driver,
            db_port=db_port,
            config=config,
            isolation_level=isolation_level,
            factory=factory or PooledAsyncEngineFactory(logger=logger),
            logger=logger,
            **kwargs,
        )

        # Store additional parameters
        self.pool_size = pool_size
        self.min_size = min_size
        self.engine_pool: Optional[ConnectionPool[AsyncEngine]] = None

    async def __aenter__(self) -> AsyncConnection:
        """
        Enter the async context, returning a database connection.

        Returns:
            A database connection

        Raises:
            Exception: If connection acquisition fails
        """
        # Get the engine factory
        engine_factory = cast(PooledAsyncEngineFactory, self.factory)

        try:
            # Get the engine pool
            self.engine_pool = await engine_factory.create_engine_pool(
                self.config,
                pool_size=self.pool_size,
                min_size=self.min_size,
            )

            # Get the circuit breaker
            circuit_breaker = await engine_factory.get_circuit_breaker(self.config)

            # Use the circuit breaker to get an engine
            self.engine = await circuit_breaker(lambda: self.engine_pool.acquire())

            # Create a connection
            self.connection = await self.engine.connect()
            await self.connection.execution_options(
                isolation_level=self.isolation_level
            )

            # Execute callbacks
            engine_factory.execute_callbacks(self.connection)

            return self.connection

        except Exception as e:
            # Clean up any resources on error
            await self.__aexit__(type(e), e, e.__traceback__)
            raise

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the async context, closing the connection and returning the engine to the pool.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        # Close the connection if open
        if self.connection is not None:
            try:
                await self.connection.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None

        # Return the engine to the pool
        if self.engine is not None and self.engine_pool is not None:
            try:
                await self.engine_pool.release(self.engine)
            except Exception as e:
                self.logger.warning(f"Error returning engine to pool: {str(e)}")
            finally:
                self.engine = None


async def pooled_async_connection(
    db_role: str,
    db_name: Optional[str] = None,
    db_host: Optional[str] = None,
    db_user_pw: Optional[str] = None,
    db_driver: Optional[str] = None,
    db_port: Optional[int] = None,
    config: Optional[ConnectionConfig] = None,
    isolation_level: str = "AUTOCOMMIT",
    factory: Optional[PooledAsyncEngineFactory] = None,
    pool_size: int = 10,
    min_size: int = 2,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any,
) -> AsyncIterator[AsyncConnection]:
    """
    Context manager for pooled asynchronous database connections.

    This function provides:
    - Connection pooling
    - Health checking
    - Circuit breaker pattern

    Args:
        db_role: Database role
        db_name: Database name
        db_host: Database host
        db_user_pw: Database password
        db_driver: Database driver
        db_port: Database port
        config: Optional connection configuration
        isolation_level: SQL transaction isolation level
        factory: Optional engine factory
        pool_size: Maximum pool size
        min_size: Minimum pool size
        logger: Optional logger instance
        **kwargs: Additional connection parameters

    Yields:
        A database connection
    """
    # Create the connection context
    context = PooledAsyncConnectionContext(
        db_role=db_role,
        db_name=db_name,
        db_host=db_host,
        db_user_pw=db_user_pw,
        db_driver=db_driver,
        db_port=db_port,
        config=config,
        isolation_level=isolation_level,
        factory=factory,
        pool_size=pool_size,
        min_size=min_size,
        logger=logger,
        **kwargs,
    )

    # Use the connection context
    async with context as connection:
        yield connection
