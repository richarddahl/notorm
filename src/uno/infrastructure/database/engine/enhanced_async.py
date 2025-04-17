"""
Enhanced async database engine with improved cancellation handling.

This module extends the base async database engine with:
- Improved cancellation handling
- Integration with the task management system
- Structured concurrency for database operations
- Enhanced connection retry logic
"""

from typing import Optional, AsyncIterator, TypeVar, Callable, Any, List
import logging
import asyncio
from contextlib import AbstractAsyncContextManager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection, AsyncSession

from uno.database.config import ConnectionConfig
from uno.database.engine.asynceng import AsyncEngineFactory
from uno.core.async_utils import (
    TaskGroup,
    AsyncLock,
    Limiter,
    timeout,
    AsyncContextGroup,
    AsyncExitStack,
)

T = TypeVar("T")


class EnhancedAsyncEngineFactory(AsyncEngineFactory):
    """
    Enhanced factory for asynchronous database engines with better concurrency control.

    This factory extends AsyncEngineFactory with:
    - Connection pooling limits to prevent connection exhaustion
    - Instrumentation for monitoring connection usage
    - Integration with the task management system
    """

    def __init__(
        self,
        connection_limiter: Optional[Limiter] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced async engine factory.

        Args:
            connection_limiter: Optional limiter to control the number of concurrent connections
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self.connection_limiter = connection_limiter or Limiter(
            max_concurrent=10, name="db_connection_limiter"
        )
        self._connection_locks = {}  # Per-connection config locks

    def get_connection_lock(self, config: ConnectionConfig) -> AsyncLock:
        """
        Get a lock for a specific connection configuration.

        This ensures that connection attempts for the same configuration
        are properly serialized to avoid race conditions.

        Args:
            config: The connection configuration

        Returns:
            An async lock for this connection configuration
        """
        # Create a key from connection details
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"

        # Create a lock if one doesn't exist
        if conn_key not in self._connection_locks:
            self._connection_locks[conn_key] = AsyncLock(name=f"conn_lock_{conn_key}")

        return self._connection_locks[conn_key]


async def connect_with_retry(
    config: ConnectionConfig,
    factory: Optional[EnhancedAsyncEngineFactory] = None,
    max_retries: int = 3,
    base_retry_delay: float = 1.0,
    isolation_level: str = "AUTOCOMMIT",
    logger: Optional[logging.Logger] = None,
) -> AsyncConnection:
    """
    Connect to the database with retry logic and timeout.

    Args:
        config: Connection configuration
        factory: Optional engine factory
        max_retries: Maximum number of connection attempts
        base_retry_delay: Base delay between retries (will be multiplied by attempt number)
        isolation_level: SQL transaction isolation level
        logger: Optional logger instance

    Returns:
        An open database connection

    Raises:
        SQLAlchemyError: If connection failed after all retries
    """
    # Use provided factory or create a new one
    engine_factory = factory or EnhancedAsyncEngineFactory(logger=logger)
    log = logger or logging.getLogger(__name__)

    # Get or create the connection lock for this config
    conn_lock = engine_factory.get_connection_lock(config)

    # Get the connection limiter
    conn_limiter = engine_factory.connection_limiter

    attempt = 0
    last_error = None
    engine = None
    connection = None

    # Try to acquire the connection lock first
    async with conn_lock:
        # Then try to acquire a connection slot from the limiter
        async with conn_limiter:
            while attempt < max_retries:
                try:
                    # Create engine with proper timeouts
                    engine = engine_factory.create_engine(config)

                    # Attempt to connect with timeout
                    async with timeout(10.0, "Database connection timeout"):
                        connection = await engine.connect()

                    # Set isolation level
                    await connection.execution_options(isolation_level=isolation_level)

                    # Execute callbacks on successful connection
                    engine_factory.execute_callbacks(connection)

                    # Log successful connection
                    log.debug(
                        f"Connected to {config.db_role}@{config.db_host}/{config.db_name} "
                        f"(attempt {attempt+1}/{max_retries})"
                    )

                    # Return the open connection
                    return connection

                except (SQLAlchemyError, asyncio.TimeoutError) as e:
                    last_error = e
                    attempt += 1

                    # Dispose of the engine if created
                    if engine is not None:
                        await engine.dispose()
                        engine = None

                    # Close the connection if created
                    if connection is not None:
                        await connection.close()
                        connection = None

                    # If we have more attempts, wait and retry
                    if attempt < max_retries:
                        # Exponential backoff with jitter
                        delay = base_retry_delay * (2 ** (attempt - 1))
                        # Add some randomness to avoid thundering herd
                        jitter = asyncio.Task.current_task().get_name()[-1:]
                        delay += float(ord(jitter[0]) % 10) / 10 if jitter else 0

                        log.warning(
                            f"Database connection attempt {attempt}/{max_retries} "
                            f"failed. Retrying in {delay:.2f}s... Error: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        log.error(
                            f"Failed to connect after {max_retries} attempts. "
                            f"Last error: {str(e)}"
                        )

    # If we've exhausted all attempts, raise the last error
    if last_error is not None:
        raise last_error

    # This should never happen, but added for type safety
    raise RuntimeError("Failed to connect to database for unknown reason")


class AsyncConnectionContext(AbstractAsyncContextManager[AsyncConnection]):
    """
    Enhanced async connection context manager with improved error handling.

    This context manager provides:
    - Automatic connection retry
    - Proper connection disposal on errors
    - Integration with the task management system
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
        factory: Optional[EnhancedAsyncEngineFactory] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        logger: Optional[logging.Logger] = None,
        **kwargs: Any,
    ):
        """Initialize the async connection context."""
        # Use provided ConnectionConfig or create one from parameters
        self.config = config
        if self.config is None:
            self.config = ConnectionConfig(
                db_role=db_role,
                db_name=db_name,
                db_host=db_host,
                db_user_pw=db_user_pw,
                db_driver=db_driver,
                db_port=db_port,
                **kwargs,
            )

        self.isolation_level = isolation_level
        self.factory = factory or EnhancedAsyncEngineFactory(logger=logger)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or logging.getLogger(__name__)
        self.connection: Optional[AsyncConnection] = None
        self.engine: Optional[AsyncEngine] = None

    async def __aenter__(self) -> AsyncConnection:
        """Enter the async context, returning a database connection."""
        try:
            # Connect with retry logic
            self.connection = await connect_with_retry(
                config=self.config,
                factory=self.factory,
                max_retries=self.max_retries,
                base_retry_delay=self.retry_delay,
                isolation_level=self.isolation_level,
                logger=self.logger,
            )

            # Store the engine for cleanup
            self.engine = self.connection.engine

            return self.connection

        except Exception as e:
            # Clean up any resources on error
            await self.__aexit__(type(e), e, e.__traceback__)
            raise

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context, closing the connection and disposing of the engine."""
        # Close the connection if open
        if self.connection is not None:
            try:
                await self.connection.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None

        # Dispose of the engine if created
        if self.engine is not None:
            try:
                await self.engine.dispose()
            except Exception as e:
                self.logger.warning(f"Error disposing engine: {str(e)}")
            finally:
                self.engine = None


async def enhanced_async_connection(
    db_role: str,
    db_name: Optional[str] = None,
    db_host: Optional[str] = None,
    db_user_pw: Optional[str] = None,
    db_driver: Optional[str] = None,
    db_port: Optional[int] = None,
    config: Optional[ConnectionConfig] = None,
    isolation_level: str = "AUTOCOMMIT",
    factory: Optional[EnhancedAsyncEngineFactory] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any,
) -> AsyncIterator[AsyncConnection]:
    """
    Enhanced context manager for asynchronous database connections.

    This function provides:
    - Improved connection retry logic
    - Better resource cleanup
    - Integration with the task management system

    Args:
        db_role: Database role/username
        db_name: Database name
        db_host: Database host
        db_user_pw: Database password
        db_driver: Database driver (e.g., 'postgresql+asyncpg')
        db_port: Database port
        config: Optional pre-configured ConnectionConfig
        isolation_level: SQL transaction isolation level
        factory: Optional engine factory
        max_retries: Maximum connection attempts
        retry_delay: Base delay between retries
        logger: Optional logger
        **kwargs: Additional connection parameters

    Yields:
        AsyncConnection: An open database connection
    """
    # Create and use the connection context
    context = AsyncConnectionContext(
        db_role=db_role,
        db_name=db_name,
        db_host=db_host,
        db_user_pw=db_user_pw,
        db_driver=db_driver,
        db_port=db_port,
        config=config,
        isolation_level=isolation_level,
        factory=factory,
        max_retries=max_retries,
        retry_delay=retry_delay,
        logger=logger,
        **kwargs,
    )

    async with context as connection:
        yield connection


class DatabaseOperationGroup:
    """
    Group for coordinating multiple database operations.

    This class provides:
    - Coordination of multiple connections/sessions
    - Proper cleanup even if operations are cancelled
    - Automatic transaction management
    """

    def __init__(
        self,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a database operation group.

        Args:
            name: Optional name for the group (for logging)
            logger: Optional logger instance
        """
        self.name = name or f"db_op_group_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        self.task_group = TaskGroup(name=self.name, logger=self.logger)
        self.context_group = AsyncContextGroup()
        self.exit_stack = AsyncExitStack()

    async def __aenter__(self) -> "DatabaseOperationGroup":
        """Enter the database operation group context."""
        await self.exit_stack.__aenter__()
        await self.exit_stack.enter_async_context(self.task_group)
        await self.exit_stack.enter_async_context(self.context_group)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the database operation group context, cleaning up all resources."""
        await self.exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def execute_in_transaction(
        self,
        session: AsyncSession,
        operations: List[Callable[[AsyncSession], Any]],
    ) -> List[Any]:
        """
        Execute multiple operations in a single database transaction.

        Args:
            session: The async database session
            operations: List of callables that take a session and return a coroutine

        Returns:
            List of results from each operation
        """
        results = []
        async with session.begin():
            for operation in operations:
                result = await operation(session)
                results.append(result)
        return results

    async def run_operation(
        self,
        operation: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Run a database operation in the task group.

        Args:
            operation: The async operation to run
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the operation
        """
        return await self.task_group.create_task(
            operation(*args, **kwargs),
            name=f"{self.name}_{operation.__name__}",
        )
