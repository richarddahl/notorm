"""
Pooled asynchronous database session management.

This module extends the enhanced session management with connection pooling,
health checking, and circuit breaker pattern.
"""

from typing import (
    Optional,
    AsyncIterator,
    Dict,
    Any,
    TypeVar,
    cast,
)
import contextlib
import logging
import asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from uno.database.config import ConnectionConfig
from uno.database.engine.pooled_async import PooledAsyncEngineFactory
from uno.database.enhanced_session import (
    EnhancedAsyncSessionFactory,
    EnhancedAsyncSessionContext,
    SessionOperationGroup,
)
from uno.settings import uno_settings
from uno.core.protocols import (
    DatabaseSessionProtocol,
    DatabaseSessionFactoryProtocol,
)
from uno.core.async_utils import (
    AsyncLock,
    Limiter,
    timeout,
)
from uno.core.async_integration import (
    AsyncCache,
    cancellable,
    retry,
)
from uno.core.resources import (
    CircuitBreaker,
    ResourceRegistry,
    get_resource_registry,
)


T = TypeVar("T")
R = TypeVar("R")


class PooledAsyncSessionFactory(EnhancedAsyncSessionFactory):
    """
    Factory for creating pooled asynchronous SQLAlchemy ORM sessions.

    Extends the enhanced async session factory with:
    - Connection pooling
    - Health checking
    - Circuit breaker pattern
    - Resource registry integration
    """

    def __init__(
        self,
        engine_factory: Optional[PooledAsyncEngineFactory] = None,
        session_limiter: Optional[Limiter] = None,
        resource_registry: Optional[ResourceRegistry] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the pooled async session factory.

        Args:
            engine_factory: Optional engine factory
            session_limiter: Optional limiter for controlling concurrent sessions
            resource_registry: Optional resource registry
            logger: Optional logger instance
        """
        # Initialize the parent class
        super().__init__(
            engine_factory=engine_factory or PooledAsyncEngineFactory(logger=logger),
            session_limiter=session_limiter,
            logger=logger,
        )

        # Store additional attributes
        self.resource_registry = resource_registry or get_resource_registry()
        self._session_circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._registry_lock = AsyncLock()

        # Cache for session makers
        self.sessionmaker_cache = AsyncCache[str, async_sessionmaker](
            ttl=3600.0,  # 1 hour TTL
            logger=logger,
        )

    async def get_circuit_breaker(
        self,
        config: ConnectionConfig,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> CircuitBreaker:
        """
        Get a circuit breaker for a session configuration.

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
            if conn_key in self._session_circuit_breakers:
                return self._session_circuit_breakers[conn_key]

            # Create the circuit breaker
            circuit_breaker = CircuitBreaker(
                name=f"session_circuit_{conn_key}",
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                logger=self.logger,
            )

            # Register the circuit breaker with the registry
            await self.resource_registry.register(
                f"session_circuit_{conn_key}", circuit_breaker
            )

            # Store in our internal dictionary
            self._session_circuit_breakers[conn_key] = circuit_breaker

            return circuit_breaker

    async def create_pooled_sessionmaker(
        self,
        config: ConnectionConfig,
        pool_size: int = 10,
        min_size: int = 2,
    ) -> async_sessionmaker:
        """
        Create or retrieve a cached async sessionmaker with pooled connections.

        Args:
            config: Connection configuration
            pool_size: Maximum pool size
            min_size: Minimum pool size

        Returns:
            An async sessionmaker
        """
        # Create a connection key to identify this configuration
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"
        cache_key = f"{conn_key}:{pool_size}:{min_size}"

        # Define a function to create the sessionmaker
        async def create_pooled_sessionmaker() -> async_sessionmaker:
            # Get the pooled engine factory
            engine_factory = cast(PooledAsyncEngineFactory, self.engine_factory)

            # Get the engine pool
            await engine_factory.create_engine_pool(
                config,
                pool_size=pool_size,
                min_size=min_size,
            )

            # Create a session maker that uses the pooled connections
            # The engine is acquired from the pool when a session is created
            session_maker = async_sessionmaker(
                lambda: engine_factory.get_pooled_engine(
                    config,
                    pool_size=pool_size,
                    min_size=min_size,
                ),
                expire_on_commit=False,
                class_=AsyncSession,
            )

            return session_maker

        # Get from cache or create
        return await self.sessionmaker_cache.get(
            key=cache_key, fetch_func=lambda _: create_pooled_sessionmaker()
        )

    @cancellable
    @retry(max_attempts=3, retry_exceptions=[asyncio.TimeoutError])
    async def create_pooled_session(
        self,
        config: ConnectionConfig,
        pool_size: int = 10,
        min_size: int = 2,
    ) -> AsyncSession:
        """
        Create a new async session using pooled connections.

        Args:
            config: Connection configuration
            pool_size: Maximum pool size
            min_size: Minimum pool size

        Returns:
            An AsyncSession
        """
        # Get the circuit breaker
        circuit_breaker = await self.get_circuit_breaker(config)

        # Create a session maker
        session_maker = await self.create_pooled_sessionmaker(
            config,
            pool_size=pool_size,
            min_size=min_size,
        )

        # Create a connection key to identify this configuration
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"

        # Get the session lock
        session_lock = self.get_session_lock(config)

        # Acquire the session limiter
        async with self.session_limiter:
            # Create the session with circuit breaker
            session = await circuit_breaker(session_maker)

            # Track the session
            async with session_lock:
                self._active_sessions[conn_key] = (
                    self._active_sessions.get(conn_key, 0) + 1
                )

            # Register cleanup to decrement counter when session is closed
            original_close = session.close

            async def enhanced_close() -> None:
                """Enhanced close method that updates tracking."""
                # Call the original close method
                await original_close()

                # Decrement the active session counter
                async with session_lock:
                    self._active_sessions[conn_key] = max(
                        0, self._active_sessions.get(conn_key, 0) - 1
                    )

            # Replace the close method
            session.close = enhanced_close  # type: ignore

            return session

    async def close(self) -> None:
        """
        Close the session factory and all associated resources.
        """
        # Get all circuit breakers
        async with self._registry_lock:
            circuit_breakers = list(self._session_circuit_breakers.values())
            self._session_circuit_breakers = {}

        # No need to close circuit breakers as they don't have resources

        # Clear the cache
        await self.sessionmaker_cache.clear()

        self.logger.info(
            f"Closed session factory and all associated resources ({len(circuit_breakers)} circuit breakers)"
        )


class PooledAsyncSessionContext(EnhancedAsyncSessionContext):
    """
    Context manager for pooled async database sessions.

    Implements DatabaseSessionContextProtocol with:
    - Connection pooling
    - Health checking
    - Circuit breaker pattern
    """

    def __init__(
        self,
        db_driver: str = uno_settings.DB_ASYNC_DRIVER,
        db_name: str = uno_settings.DB_NAME,
        db_user_pw: str = uno_settings.DB_USER_PW,
        db_role: str = f"{uno_settings.DB_NAME}_login",
        db_host: Optional[str] = uno_settings.DB_HOST,
        db_port: Optional[int] = uno_settings.DB_PORT,
        factory: Optional[DatabaseSessionFactoryProtocol] = None,
        logger: Optional[logging.Logger] = None,
        scoped: bool = False,
        timeout_seconds: Optional[float] = None,
        pool_size: int = 10,
        min_size: int = 2,
        **kwargs: Any,
    ):
        """
        Initialize the pooled async session context.

        Args:
            db_driver: Database driver
            db_name: Database name
            db_user_pw: Database password
            db_role: Database role
            db_host: Database host
            db_port: Database port
            factory: Optional session factory
            logger: Optional logger
            scoped: Whether to use a scoped session
            timeout_seconds: Optional timeout for session operations
            pool_size: Maximum pool size
            min_size: Minimum pool size
            **kwargs: Additional connection parameters
        """
        # Initialize the parent class
        super().__init__(
            db_driver=db_driver,
            db_name=db_name,
            db_user_pw=db_user_pw,
            db_role=db_role,
            db_host=db_host,
            db_port=db_port,
            factory=factory or PooledAsyncSessionFactory(logger=logger),
            logger=logger,
            scoped=scoped,
            timeout_seconds=timeout_seconds,
            **kwargs,
        )

        # Store additional parameters
        self.pool_size = pool_size
        self.min_size = min_size

    async def __aenter__(self) -> DatabaseSessionProtocol:
        """
        Enter the async context, returning a database session.

        Returns:
            A database session
        """
        await self.exit_stack.__aenter__()

        # Create config object from parameters
        config = ConnectionConfig(
            db_role=self.db_role,
            db_name=self.db_name,
            db_host=self.db_host,
            db_user_pw=self.db_user_pw,
            db_driver=self.db_driver,
            db_port=self.db_port,
            **self.kwargs,
        )

        try:
            # Apply timeout if specified
            if self.timeout_seconds is not None:
                # Register the timeout context
                await self.exit_stack.enter_async_context(
                    timeout(self.timeout_seconds, "Database session creation timeout")
                )

            # Get or create session based on scope
            if self.scoped:
                # Get a scoped session
                scoped_session = self.factory.get_scoped_session(config)
                self.session = scoped_session()
            else:
                # Create a pooled async session
                if isinstance(self.factory, PooledAsyncSessionFactory):
                    self.session = await self.factory.create_pooled_session(
                        config,
                        pool_size=self.pool_size,
                        min_size=self.min_size,
                    )
                else:
                    # Fallback for non-pooled factories
                    self.session = self.factory.create_session(config)

                # Register session for cleanup
                self.exit_stack.push_async_callback(self._cleanup_session)

            return self.session

        except Exception as e:
            # Clean up resources on error
            await self.exit_stack.__aexit__(type(e), e, e.__traceback__)
            raise


@contextlib.asynccontextmanager
async def pooled_async_session(
    db_driver: str = uno_settings.DB_ASYNC_DRIVER,
    db_name: str = uno_settings.DB_NAME,
    db_user_pw: str = uno_settings.DB_USER_PW,
    db_role: str = f"{uno_settings.DB_NAME}_login",
    db_host: Optional[str] = uno_settings.DB_HOST,
    db_port: Optional[int] = uno_settings.DB_PORT,
    factory: Optional[DatabaseSessionFactoryProtocol] = None,
    logger: Optional[logging.Logger] = None,
    scoped: bool = False,
    timeout_seconds: Optional[float] = None,
    pool_size: int = 10,
    min_size: int = 2,
    **kwargs,
) -> AsyncIterator[DatabaseSessionProtocol]:
    """
    Context manager for pooled asynchronous database sessions.

    Args:
        db_driver: Database driver
        db_name: Database name
        db_user_pw: Database password
        db_role: Database role
        db_host: Database host
        db_port: Database port
        factory: Optional session factory
        logger: Optional logger
        scoped: Whether to use a scoped session
        timeout_seconds: Optional timeout for session operations
        pool_size: Maximum pool size
        min_size: Minimum pool size
        **kwargs: Additional connection parameters

    Yields:
        A database session
    """
    # Use the pooled session context
    context = PooledAsyncSessionContext(
        db_driver=db_driver,
        db_name=db_name,
        db_user_pw=db_user_pw,
        db_role=db_role,
        db_host=db_host,
        db_port=db_port,
        factory=factory,
        logger=logger,
        scoped=scoped,
        timeout_seconds=timeout_seconds,
        pool_size=pool_size,
        min_size=min_size,
        **kwargs,
    )

    async with context as session:
        yield session


class PooledSessionOperationGroup(SessionOperationGroup):
    """
    Group for coordinating multiple database session operations.

    Extends the base SessionOperationGroup with connection pooling.
    """

    async def create_session(
        self,
        db_driver: str = uno_settings.DB_ASYNC_DRIVER,
        db_name: str = uno_settings.DB_NAME,
        db_user_pw: str = uno_settings.DB_USER_PW,
        db_role: str = f"{uno_settings.DB_NAME}_login",
        db_host: Optional[str] = uno_settings.DB_HOST,
        db_port: Optional[int] = uno_settings.DB_PORT,
        factory: Optional[DatabaseSessionFactoryProtocol] = None,
        pool_size: int = 10,
        min_size: int = 2,
        **kwargs,
    ) -> AsyncSession:
        """
        Create a new session managed by this group.

        Args:
            db_driver: Database driver
            db_name: Database name
            db_user_pw: Database password
            db_role: Database role
            db_host: Database host
            db_port: Database port
            factory: Optional session factory
            pool_size: Maximum pool size
            min_size: Minimum pool size
            **kwargs: Additional connection parameters

        Returns:
            A new session that will be automatically closed
        """
        # Create a new session
        session_context = PooledAsyncSessionContext(
            db_driver=db_driver,
            db_name=db_name,
            db_user_pw=db_user_pw,
            db_role=db_role,
            db_host=db_host,
            db_port=db_port,
            factory=factory,
            logger=self.logger,
            pool_size=pool_size,
            min_size=min_size,
            **kwargs,
        )

        # Enter the session context
        session = await self.exit_stack.enter_async_context(session_context)

        # Store the session for cleanup
        self.sessions.append(cast(AsyncSession, session))

        return cast(AsyncSession, session)
