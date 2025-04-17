"""
Enhanced async session system with connection pooling.

This module provides a high-performance async session system that integrates
with our enhanced connection pool for optimal database performance.

Features:
- Dynamic connection pool sizing
- Intelligent connection lifecycle management
- Health checking and circuit breaker pattern
- Comprehensive metrics collection
- Different connection strategies for different workloads
"""

from typing import Optional, AsyncIterator, Dict, Any, List, Type, TypeVar, cast
import logging
import contextlib
import asyncio
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.session import _AsyncSessionContextManager
from sqlalchemy.orm.session import Session

from uno.database.config import ConnectionConfig
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    ConnectionPoolStrategy,
    EnhancedConnectionPool,
    EnhancedAsyncEnginePool,
    get_connection_manager,
)
from uno.database.enhanced_session import EnhancedAsyncSessionFactory, EnhancedAsyncSessionContext
from uno.core.resources import ResourceRegistry, get_resource_registry
from uno.core.protocols import DatabaseSessionProtocol, DatabaseSessionFactoryProtocol
from uno.core.async_utils import AsyncLock, timeout, TaskGroup
from uno.core.async_integration import AsyncCache, retry, cancellable
from uno.settings import uno_settings


T = TypeVar('T')


@dataclass
class SessionPoolConfig:
    """
    Configuration for the session pool.
    
    Controls behavior of session pooling, reuse strategies, and lifecycle.
    """
    
    # Session pool sizing
    min_sessions: int = 5
    max_sessions: int = 50
    target_free_sessions: int = 3
    
    # Session lifecycle
    idle_timeout: float = 60.0  # 1 minute
    max_lifetime: float = 1800.0  # 30 minutes
    
    # Connection pool config
    connection_pool_config: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
    
    # Misc options
    log_sessions: bool = False
    session_validation_enabled: bool = True
    use_enhanced_connection_pool: bool = True


class EnhancedPooledSessionFactory(EnhancedAsyncSessionFactory):
    """
    Factory for creating pooled async sessions with enhanced connection pools.
    
    This factory extends EnhancedAsyncSessionFactory to use our enhanced
    connection pool system for better performance and reliability.
    """
    
    def __init__(
        self,
        session_pool_config: Optional[SessionPoolConfig] = None,
        resource_registry: Optional[ResourceRegistry] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced pooled session factory.
        
        Args:
            session_pool_config: Configuration for the session pool
            resource_registry: Optional resource registry
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        
        self.session_pool_config = session_pool_config or SessionPoolConfig()
        self.resource_registry = resource_registry or get_resource_registry()
        self.logger = logger or logging.getLogger(__name__)
        
        # Session cache for reuse
        self._session_cache = AsyncCache[str, async_sessionmaker](
            ttl=3600.0,  # 1 hour TTL
            logger=self.logger,
        )
        
        # Connection manager lock
        self._config_lock = AsyncLock()
        
        # Dictionary of connection configurations
        self._connection_configs: Dict[str, ConnectionConfig] = {}
    
    def _get_config_key(self, config: ConnectionConfig) -> str:
        """
        Get a key for a connection configuration.
        
        Args:
            config: Connection configuration
            
        Returns:
            String key for the configuration
        """
        return f"{config.db_role}@{config.db_host}/{config.db_name}"
    
    async def get_connection_config(self, config_key: str) -> Optional[ConnectionConfig]:
        """
        Get a connection configuration by key.
        
        Args:
            config_key: Connection configuration key
            
        Returns:
            Connection configuration if found, None otherwise
        """
        async with self._config_lock:
            return self._connection_configs.get(config_key)
    
    def store_connection_config(self, config: ConnectionConfig) -> str:
        """
        Store a connection configuration.
        
        Args:
            config: Connection configuration
            
        Returns:
            Configuration key
        """
        config_key = self._get_config_key(config)
        
        self._connection_configs[config_key] = config
        
        return config_key
    
    @cancellable
    @retry(max_attempts=3, base_delay=0.5, max_delay=2.0)
    async def create_pooled_session_async(
        self,
        config: ConnectionConfig,
    ) -> AsyncSession:
        """
        Create a new async session using the enhanced connection pool.
        
        Args:
            config: Connection configuration
            
        Returns:
            AsyncSession instance
        """
        # Store the config for future reference
        config_key = self.store_connection_config(config)
        
        # Get the connection manager
        connection_manager = get_connection_manager()
        
        # Configure the connection pool if needed
        connection_manager.configure_pool(
            role=config.db_role,
            config=self.session_pool_config.connection_pool_config,
        )
        
        # Get a cached session maker or create a new one
        try:
            # Define a function to create the session maker
            async def create_session_maker() -> async_sessionmaker:
                # Get an engine for creating the session maker
                async with connection_manager.engine(config) as engine:
                    # Create the session maker
                    session_maker = async_sessionmaker(
                        # Use a lambda to get an engine from the pool for each session
                        lambda: self._get_pool_engine(config),
                        expire_on_commit=False,
                        class_=AsyncSession,
                    )
                    
                    return session_maker
            
            # Get from cache or create new session maker
            session_maker = await self._session_cache.get(
                key=config_key,
                fetch_func=lambda _: create_session_maker()
            )
            
            # Create a session
            session = session_maker()
            
            # Return the session with tracking
            async with self._session_locks.get(config_key, AsyncLock()):
                self._active_sessions[config_key] = self._active_sessions.get(config_key, 0) + 1
            
            # Track session for proper cleanup
            original_close = session.close
            
            async def enhanced_close() -> None:
                """Enhanced close method that updates tracking."""
                # Call the original close method
                await original_close()
                
                # Decrement the active session counter
                async with self._session_locks.get(config_key, AsyncLock()):
                    self._active_sessions[config_key] = max(0, self._active_sessions.get(config_key, 0) - 1)
            
            # Replace the close method
            session.close = enhanced_close  # type: ignore
            
            return session
            
        except Exception as e:
            self.logger.error(f"Error creating pooled session: {str(e)}")
            raise
    
    async def _get_pool_engine(self, config: ConnectionConfig) -> AsyncEngine:
        """
        Get an engine from the connection pool.
        
        Args:
            config: Connection configuration
            
        Returns:
            AsyncEngine instance
        """
        # Get the connection manager
        connection_manager = get_connection_manager()
        
        # Get a pool for the configuration
        pool = await connection_manager.get_engine_pool(config)
        
        # Get an engine from the pool
        return await pool.acquire()


class EnhancedPooledSessionContext(EnhancedAsyncSessionContext):
    """
    Context manager for pooled async sessions.
    
    Uses the enhanced connection pool system for optimal performance.
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
        session_pool_config: Optional[SessionPoolConfig] = None,
        **kwargs: Any
    ):
        """
        Initialize the enhanced pooled session context.
        
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
            session_pool_config: Configuration for the session pool
            **kwargs: Additional connection parameters
        """
        # Create a factory if not provided
        if factory is None:
            factory = EnhancedPooledSessionFactory(
                session_pool_config=session_pool_config,
                logger=logger,
            )
        
        # Initialize parent class
        super().__init__(
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
            **kwargs
        )
        
        # Store additional parameters
        self.session_pool_config = session_pool_config or SessionPoolConfig()
    
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
                if isinstance(self.factory, EnhancedPooledSessionFactory):
                    self.session = await self.factory.create_pooled_session_async(config)
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
async def enhanced_pool_session(
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
    session_pool_config: Optional[SessionPoolConfig] = None,
    **kwargs,
) -> AsyncIterator[DatabaseSessionProtocol]:
    """
    Context manager for enhanced pooled async sessions.
    
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
        session_pool_config: Configuration for the session pool
        **kwargs: Additional connection parameters
    
    Yields:
        AsyncSession: The database session
    """
    # Use the enhanced pooled session context
    context = EnhancedPooledSessionContext(
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
        session_pool_config=session_pool_config,
        **kwargs
    )
    
    async with context as session:
        yield session


class EnhancedPooledSessionOperationGroup:
    """
    Group for coordinating multiple session operations.
    
    Manages multiple sessions and transactions with proper cleanup,
    using the enhanced connection pool for optimal performance.
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        session_pool_config: Optional[SessionPoolConfig] = None,
    ):
        """
        Initialize the session operation group.
        
        Args:
            name: Optional name for the group
            logger: Optional logger instance
            session_pool_config: Configuration for the session pool
        """
        self.name = name or f"pooled_session_op_group_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        self.session_pool_config = session_pool_config or SessionPoolConfig()
        
        # Task group for parallel operations
        self.task_group = TaskGroup(name=self.name, logger=self.logger)
        
        # Exit stack for managing session contexts
        self.exit_stack = contextlib.AsyncExitStack()
        
        # Track sessions for cleanup
        self.sessions: List[AsyncSession] = []
        
        # Factory for creating sessions
        self.factory = EnhancedPooledSessionFactory(
            session_pool_config=self.session_pool_config,
            logger=self.logger,
        )
    
    async def __aenter__(self) -> 'EnhancedPooledSessionOperationGroup':
        """Enter the session operation group context."""
        await self.exit_stack.__aenter__()
        await self.exit_stack.enter_async_context(self.task_group)
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the session operation group context, cleaning up all resources."""
        # Close all sessions
        for session in self.sessions:
            try:
                await session.close()
            except Exception as e:
                self.logger.warning(f"Error closing session: {str(e)}")
        
        # Clean up the exit stack
        await self.exit_stack.__aexit__(exc_type, exc_val, exc_tb)
    
    async def create_session(
        self,
        db_driver: str = uno_settings.DB_ASYNC_DRIVER,
        db_name: str = uno_settings.DB_NAME,
        db_user_pw: str = uno_settings.DB_USER_PW,
        db_role: str = f"{uno_settings.DB_NAME}_login",
        db_host: Optional[str] = uno_settings.DB_HOST,
        db_port: Optional[int] = uno_settings.DB_PORT,
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
            **kwargs: Additional connection parameters
            
        Returns:
            AsyncSession: A new session that will be automatically closed
        """
        # Create a new session context
        session_context = EnhancedPooledSessionContext(
            db_driver=db_driver,
            db_name=db_name,
            db_user_pw=db_user_pw,
            db_role=db_role,
            db_host=db_host,
            db_port=db_port,
            factory=self.factory,
            logger=self.logger,
            session_pool_config=self.session_pool_config,
            **kwargs
        )
        
        # Enter the session context
        session = await self.exit_stack.enter_async_context(session_context)
        
        # Store the session for cleanup
        self.sessions.append(cast(AsyncSession, session))
        
        return cast(AsyncSession, session)
    
    async def run_operation(
        self,
        session: AsyncSession,
        operation: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Run a database operation in the task group.
        
        Args:
            session: The async session to use
            operation: The async operation to run
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            The result of the operation
        """
        return await self.task_group.create_task(
            operation(session, *args, **kwargs),
            name=f"{self.name}_{operation.__name__}",
        )
    
    async def run_in_transaction(
        self,
        session: AsyncSession,
        operations: List[Any],
    ) -> List[Any]:
        """
        Run multiple operations in a single transaction.
        
        Args:
            session: The async session to use
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
    
    async def run_parallel_operations(
        self,
        session: AsyncSession,
        operations: List[Any],
        max_concurrency: int = 5,
    ) -> List[Any]:
        """
        Run multiple operations in parallel.
        
        Args:
            session: The async session to use
            operations: List of callables that take a session and return a coroutine
            max_concurrency: Maximum number of operations to run concurrently
            
        Returns:
            List of results in the order of operations
        """
        results = [None] * len(operations)
        
        async def run_operation(index: int, op: Any) -> None:
            result = await op(session)
            results[index] = result
        
        # Run operations in parallel with limited concurrency
        async with TaskGroup(name=f"{self.name}_parallel", max_concurrency=max_concurrency) as group:
            for i, operation in enumerate(operations):
                group.create_task(
                    run_operation(i, operation),
                    name=f"{self.name}_op_{i}",
                )
        
        return results