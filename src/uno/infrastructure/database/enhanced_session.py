"""
Enhanced asynchronous database session management.

This module extends the base session management with:
- Improved error handling and cancellation
- Integration with the task management system
- Connection pooling controls
- Resource cleanup on task cancellation
"""

from typing import Optional, AsyncIterator, Dict, Any, List, TypeVar, Generic, Type, cast
import contextlib
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    async_scoped_session,
)
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio.session import _AsyncSessionContextManager
from sqlalchemy.orm import sessionmaker
from asyncio import current_task

from uno.database.config import ConnectionConfig
from uno.database.engine.enhanced_async import (
    EnhancedAsyncEngineFactory,
    DatabaseOperationGroup,
)
from uno.settings import uno_settings
from uno.core.protocols import DatabaseSessionProtocol, DatabaseSessionFactoryProtocol, DatabaseSessionContextProtocol
from uno.core.async_utils import (
    TaskGroup,
    AsyncLock,
    Limiter,
    AsyncContextGroup,
    AsyncExitStack,
    timeout,
    run_task,
)

T = TypeVar('T')
R = TypeVar('R')


class EnhancedAsyncSessionFactory(DatabaseSessionFactoryProtocol):
    """
    Enhanced factory for creating asynchronous SQLAlchemy ORM sessions.
    
    Extends the base AsyncSessionFactory with:
    - Improved cancellation handling
    - Connection pool management
    - Resource cleanup on task cancellation
    - Session usage monitoring
    """
    
    def __init__(
        self,
        engine_factory: Optional[EnhancedAsyncEngineFactory] = None,
        session_limiter: Optional[Limiter] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced async session factory.
        
        Args:
            engine_factory: Optional engine factory
            session_limiter: Optional limiter for controlling concurrent sessions
            logger: Optional logger instance
        """
        self.engine_factory = engine_factory or EnhancedAsyncEngineFactory(logger=logger)
        self.session_limiter = session_limiter or Limiter(
            max_concurrent=20,
            name="db_session_limiter"
        )
        self.logger = logger or logging.getLogger(__name__)
        self._session_locks: Dict[str, AsyncLock] = {}
        self._sessionmakers: Dict[str, async_sessionmaker] = {}
        self._scoped_sessions: Dict[str, async_scoped_session] = {}
        self._active_sessions: Dict[str, int] = {}
    
    def get_session_lock(self, config: ConnectionConfig) -> AsyncLock:
        """
        Get a lock for a specific session configuration.
        
        Args:
            config: The connection configuration
            
        Returns:
            An async lock for this session configuration
        """
        # Create a key from connection details
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"
        
        # Create a lock if one doesn't exist
        if conn_key not in self._session_locks:
            self._session_locks[conn_key] = AsyncLock(name=f"session_lock_{conn_key}")
            
        return self._session_locks[conn_key]
    
    def create_sessionmaker(self, config: ConnectionConfig) -> async_sessionmaker:
        """
        Create or retrieve a cached async sessionmaker.
        
        Args:
            config: Connection configuration
            
        Returns:
            An async sessionmaker
        """
        # Create a connection key to identify this configuration
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"

        # Return cached sessionmaker if available
        if conn_key in self._sessionmakers:
            return self._sessionmakers[conn_key]

        # Get session lock to ensure thread-safe creation
        session_lock = self.get_session_lock(config)
        
        # Create an async session maker creator to be run with the lock
        async def create_session_maker() -> async_sessionmaker:
            # Check again in case another task created it while waiting
            if conn_key in self._sessionmakers:
                return self._sessionmakers[conn_key]
            
            # Create new engine with timeout handling
            engine = await run_task(
                lambda: self.engine_factory.create_engine(config),
                name=f"create_engine_{conn_key}"
            )

            # Create sessionmaker with the engine and improved options
            session_maker = async_sessionmaker(
                engine, 
                expire_on_commit=False,
                class_=AsyncSession,
            )

            # Cache the sessionmaker
            self._sessionmakers[conn_key] = session_maker
            
            # Initialize session counter
            self._active_sessions[conn_key] = 0

            return session_maker
        
        # Run the creation in a synchronized context
        session_maker = self._sessionmakers.get(conn_key)
        if session_maker is None:
            # This is a synchronous API, so we need to create the session maker
            # without using the lock. In real usage, prefer the async methods.
            engine = self.engine_factory.create_engine(config)
            session_maker = async_sessionmaker(
                engine, 
                expire_on_commit=False,
                class_=AsyncSession,
            )
            self._sessionmakers[conn_key] = session_maker
            self._active_sessions[conn_key] = 0
        
        return session_maker
    
    async def create_session_async(self, config: ConnectionConfig) -> AsyncSession:
        """
        Create a new async session asynchronously.
        
        Args:
            config: Connection configuration
            
        Returns:
            An AsyncSession
        """
        # Create a connection key to identify this configuration
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"
        
        # Get the session lock
        session_lock = self.get_session_lock(config)
        
        # Acquire the session limiter
        async with self.session_limiter:
            # Create the sessionmaker if needed (with the lock)
            async with session_lock:
                if conn_key not in self._sessionmakers:
                    await run_task(
                        lambda: self.create_sessionmaker(config),
                        name=f"create_sessionmaker_{conn_key}"
                    )
                
                # Get the session maker
                session_maker = self._sessionmakers[conn_key]
                
                # Increment the active session counter
                self._active_sessions[conn_key] = self._active_sessions.get(conn_key, 0) + 1
            
            # Create a new session
            session = session_maker()
            
            # Register cleanup to decrement counter when session is closed
            original_close = session.close
            
            async def enhanced_close() -> None:
                """Enhanced close method that updates tracking."""
                # Call the original close method
                await original_close()
                
                # Decrement the active session counter
                async with session_lock:
                    self._active_sessions[conn_key] = max(0, self._active_sessions.get(conn_key, 0) - 1)
            
            # Replace the close method
            session.close = enhanced_close  # type: ignore
            
            return session
    
    def create_session(self, config: ConnectionConfig) -> AsyncSession:
        """
        Create a new async session.
        
        Note: This is a synchronous API, and should only be used when starting up.
        For normal operations, use create_session_async instead.
        
        Args:
            config: Connection configuration
            
        Returns:
            An AsyncSession
        """
        session_maker = self.create_sessionmaker(config)
        
        # Create a connection key to identify this configuration
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"
        
        # Increment session counter (no lock in sync context)
        self._active_sessions[conn_key] = self._active_sessions.get(conn_key, 0) + 1
        
        # Create the session
        session = session_maker()
        
        # Register cleanup to decrement counter when session is closed
        original_close = session.close
        
        async def enhanced_close() -> None:
            """Enhanced close method that updates tracking."""
            # Call the original close method
            await original_close()
            
            # Decrement the active session counter (no lock in async context)
            self._active_sessions[conn_key] = max(0, self._active_sessions.get(conn_key, 0) - 1)
        
        # Replace the close method
        session.close = enhanced_close  # type: ignore
        
        return session
    
    def get_scoped_session(self, config: ConnectionConfig) -> async_scoped_session:
        """
        Get a scoped session factory for the given configuration.
        
        The scoped session is tied to the current async task (like a web request)
        and will be reused if requested again with the same configuration.
        
        Args:
            config: Connection configuration
        
        Returns:
            An async_scoped_session that provides session instances scoped to the current task
        """
        # Create a connection key to identify this configuration
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"

        # Return cached scoped_session if available
        if conn_key in self._scoped_sessions:
            return self._scoped_sessions[conn_key]

        # Create a new sessionmaker
        session_maker = self.create_sessionmaker(config)

        # Create a scoped session that uses the current asyncio task as the scope
        scoped_session = async_scoped_session(session_maker, scopefunc=current_task)

        # Cache the scoped session
        self._scoped_sessions[conn_key] = scoped_session

        return scoped_session
    
    async def remove_all_scoped_sessions(self) -> None:
        """
        Remove all scoped sessions for the current async task.
        
        Should be called at the end of a request lifecycle to clean up resources.
        """
        for scoped_session in self._scoped_sessions.values():
            await scoped_session.remove()
    
    async def get_active_session_count(self, config: Optional[ConnectionConfig] = None) -> Dict[str, int]:
        """
        Get the number of active sessions.
        
        Args:
            config: Optional connection configuration to filter by
            
        Returns:
            A dictionary of connection keys to active session counts
        """
        if config is not None:
            # Return count for a specific configuration
            conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"
            return {conn_key: self._active_sessions.get(conn_key, 0)}
        
        # Return counts for all configurations
        return dict(self._active_sessions)


class EnhancedAsyncSessionContext(DatabaseSessionContextProtocol):
    """
    Enhanced context manager for async database sessions.
    
    Implements DatabaseSessionContextProtocol with improved:
    - Cancellation handling
    - Resource cleanup
    - Error reporting
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
        **kwargs: Any
    ):
        """Initialize the enhanced async session context."""
        self.db_driver = db_driver
        self.db_name = db_name
        self.db_user_pw = db_user_pw
        self.db_role = db_role
        self.db_host = db_host
        self.db_port = db_port
        self.factory = factory or EnhancedAsyncSessionFactory(logger=logger)
        self.logger = logger or logging.getLogger(__name__)
        self.scoped = scoped
        self.timeout_seconds = timeout_seconds
        self.kwargs = kwargs
        self.session: Optional[DatabaseSessionProtocol] = None
        self.exit_stack = AsyncExitStack()
        
    async def __aenter__(self) -> DatabaseSessionProtocol:
        """Enter the async context, returning a database session."""
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
                # Create an enhanced async session
                if isinstance(self.factory, EnhancedAsyncSessionFactory):
                    self.session = await self.factory.create_session_async(config)
                else:
                    # Fallback for non-enhanced factories
                    self.session = self.factory.create_session(config)
                
                # Register session for cleanup
                self.exit_stack.push_async_callback(self._cleanup_session)
            
            return self.session
        
        except Exception as e:
            # Clean up resources on error
            await self.exit_stack.__aexit__(type(e), e, e.__traceback__)
            raise
    
    async def _cleanup_session(self) -> None:
        """Clean up the session resources."""
        if not self.scoped and self.session:
            await self.session.close()
            self.session = None
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context, cleaning up all resources."""
        await self.exit_stack.__aexit__(exc_type, exc_val, exc_tb)


@contextlib.asynccontextmanager
async def enhanced_async_session(
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
    **kwargs,
) -> AsyncIterator[DatabaseSessionProtocol]:
    """
    Enhanced context manager for asynchronous database sessions.
    
    Args:
        db_driver: Database driver name
        db_name: Database name
        db_user_pw: Database password
        db_role: Database role/username
        db_host: Database host
        db_port: Database port
        factory: Optional session factory
        logger: Optional logger
        scoped: Whether to use a scoped session tied to the current async task
        timeout_seconds: Optional timeout for session operations
        **kwargs: Additional connection parameters
    
    Yields:
        AsyncSession: The database session
    """
    # Use the new EnhancedAsyncSessionContext class
    context = EnhancedAsyncSessionContext(
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
    
    async with context as session:
        yield session


def get_enhanced_session(
    db_driver: str = uno_settings.DB_ASYNC_DRIVER,
    db_name: str = uno_settings.DB_NAME,
    db_user_pw: str = uno_settings.DB_USER_PW,
    db_role: str = f"{uno_settings.DB_NAME}_login",
    db_host: Optional[str] = uno_settings.DB_HOST,
    db_port: Optional[int] = uno_settings.DB_PORT,
    factory: Optional[DatabaseSessionFactoryProtocol] = None,
    logger: Optional[logging.Logger] = None,
    scoped: bool = False,
    **kwargs,
) -> AsyncSession:
    """
    Get an enhanced async session directly.
    
    This is a convenience function for getting a session without using a context manager.
    The caller is responsible for closing the session when done.
    
    Args:
        db_driver: Database driver name
        db_name: Database name
        db_user_pw: Database password
        db_role: Database role/username
        db_host: Database host
        db_port: Database port
        factory: Optional session factory
        logger: Optional logger
        scoped: Whether to use a scoped session tied to the current async task
        **kwargs: Additional connection parameters
    
    Returns:
        AsyncSession: The database session
    """
    factory = factory or EnhancedAsyncSessionFactory(logger=logger)
    
    # Create config object from parameters
    config = ConnectionConfig(
        db_role=db_role,
        db_name=db_name,
        db_host=db_host,
        db_user_pw=db_user_pw,
        db_driver=db_driver,
        db_port=db_port,
        **kwargs,
    )
    
    # Get or create session based on scope
    if scoped:
        # Get a scoped session
        scoped_session = factory.get_scoped_session(config)
        return scoped_session()
    else:
        # Synchronous API, so use create_session
        return factory.create_session(config)


class SessionOperationGroup:
    """
    Group for coordinating multiple database session operations.
    
    This class provides:
    - Coordination of multiple sessions
    - Proper cleanup even if operations are cancelled
    - Automatic transaction management
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a session operation group.
        
        Args:
            name: Optional name for the group (for logging)
            logger: Optional logger instance
        """
        self.name = name or f"session_op_group_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        self.task_group = TaskGroup(name=self.name, logger=self.logger)
        self.context_group = AsyncContextGroup()
        self.exit_stack = AsyncExitStack()
        self.sessions: List[AsyncSession] = []
        
    async def __aenter__(self) -> 'SessionOperationGroup':
        """Enter the session operation group context."""
        await self.exit_stack.__aenter__()
        await self.exit_stack.enter_async_context(self.task_group)
        await self.exit_stack.enter_async_context(self.context_group)
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
        factory: Optional[DatabaseSessionFactoryProtocol] = None,
        **kwargs,
    ) -> AsyncSession:
        """
        Create a new session managed by this group.
        
        Args:
            db_driver: Database driver name
            db_name: Database name
            db_user_pw: Database password
            db_role: Database role/username
            db_host: Database host
            db_port: Database port
            factory: Optional session factory
            **kwargs: Additional connection parameters
            
        Returns:
            AsyncSession: A new session that will be automatically closed
        """
        # Create a new session
        session_context = EnhancedAsyncSessionContext(
            db_driver=db_driver,
            db_name=db_name,
            db_user_pw=db_user_pw,
            db_role=db_role,
            db_host=db_host,
            db_port=db_port,
            factory=factory,
            logger=self.logger,
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
        operation,
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