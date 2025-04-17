from typing import Optional, AsyncIterator, Dict, Any, AsyncContextManager
import contextlib
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    async_scoped_session,
    AsyncEngine
)
from asyncio import current_task

from uno.database.config import ConnectionConfig
from uno.database.engine.asynceng import AsyncEngineFactory
from uno.settings import uno_settings
from uno.core.protocols import DatabaseSessionProtocol, DatabaseSessionFactoryProtocol, DatabaseSessionContextProtocol


class AsyncSessionFactory(DatabaseSessionFactoryProtocol):
    """
    Factory for creating asynchronous SQLAlchemy ORM sessions.

    Supports scoped sessions that can be tied to web request lifecycles
    using SQLAlchemy's async_scoped_session.
    
    Implements the DatabaseSessionFactoryProtocol.
    """

    def __init__(
        self,
        engine_factory: Optional[AsyncEngineFactory] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the session factory."""
        self.engine_factory = engine_factory or AsyncEngineFactory(logger=logger)
        self.logger = logger or logging.getLogger(__name__)
        self._sessionmakers: Dict[str, async_sessionmaker] = {}
        self._scoped_sessions: Dict[str, async_scoped_session] = {}

    def create_sessionmaker(self, config: ConnectionConfig) -> async_sessionmaker:
        """Create or retrieve a cached async sessionmaker."""
        # Create a connection key to identify this configuration
        conn_key = f"{config.db_role}@{config.db_host}/{config.db_name}"

        # Return cached sessionmaker if available
        if conn_key in self._sessionmakers:
            return self._sessionmakers[conn_key]

        # Create new engine and sessionmaker
        engine = self.engine_factory.create_engine(config)

        # Create sessionmaker with the engine
        session_maker = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )

        # Cache the sessionmaker
        self._sessionmakers[conn_key] = session_maker

        return session_maker

    def create_session(self, config: ConnectionConfig) -> AsyncSession:
        """Create a new async session."""
        session_maker = self.create_sessionmaker(config)
        return session_maker()

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


class AsyncSessionContext(DatabaseSessionContextProtocol):
    """Context manager for async database sessions, implementing DatabaseSessionContextProtocol."""
    
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
        **kwargs: Any
    ):
        """Initialize the async session context."""
        self.db_driver = db_driver
        self.db_name = db_name
        self.db_user_pw = db_user_pw
        self.db_role = db_role
        self.db_host = db_host
        self.db_port = db_port
        self.factory = factory or AsyncSessionFactory(logger=logger)
        self.logger = logger or logging.getLogger(__name__)
        self.scoped = scoped
        self.kwargs = kwargs
        self.session: Optional[DatabaseSessionProtocol] = None
        
    async def __aenter__(self) -> DatabaseSessionProtocol:
        """Enter the async context, returning a database session."""
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
        
        if self.scoped:
            # Get a scoped session
            scoped_session = self.factory.get_scoped_session(config)
            self.session = scoped_session()
        else:
            # Create a regular session
            self.session = self.factory.create_session(config)
            
        return self.session
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context, closing the session if needed."""
        if not self.scoped and self.session:
            await self.session.close()
            self.session = None


@contextlib.asynccontextmanager
async def async_session(
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
) -> AsyncIterator[DatabaseSessionProtocol]:
    """
    Context manager for asynchronous database sessions.

    Args:
        db_driver:
        db_name:
        db_user_pw:
        db_role:
        db_host:
        db_port:
        factory: Optional session factory
        logger: Optional logger
        scoped: Whether to use a scoped session tied to the current async task
        **kwargs: Additional connection parameters

    Yields:
        AsyncSession: The database session
    """
    # Use the new AsyncSessionContext class
    context = AsyncSessionContext(
        db_driver=db_driver,
        db_name=db_name,
        db_user_pw=db_user_pw,
        db_role=db_role,
        db_host=db_host,
        db_port=db_port,
        factory=factory,
        logger=logger,
        scoped=scoped,
        **kwargs
    )
    
    async with context as session:
        yield session


@contextlib.asynccontextmanager
async def get_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """
    Context manager that creates a new AsyncSession from an engine.
    
    Args:
        engine: The AsyncEngine to create a session from
        
    Yields:
        AsyncSession: A new database session
    """
    # Create a session
    async_session = AsyncSession(engine, expire_on_commit=False)
    
    try:
        yield async_session
    finally:
        await async_session.close()
