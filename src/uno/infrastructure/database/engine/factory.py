"""
Factory for creating SQLAlchemy engines.

This module provides a factory for creating SQLAlchemy engines
with appropriate configuration.
"""

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine.url import URL

from uno.database.config import ConnectionConfig


class AsyncEngineFactory:
    """
    Factory for creating SQLAlchemy async engines.
    
    This class provides methods for creating and managing SQLAlchemy
    async engines with appropriate configuration.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the engine factory.
        
        Args:
            logger: Optional logger instance
        """
        self.engine = None
        self.logger = logger
    
    def create_engine(self, config: ConnectionConfig) -> AsyncEngine:
        """
        Create a SQLAlchemy async engine with the given configuration.
        
        Args:
            config: Connection configuration
        
        Returns:
            AsyncEngine: SQLAlchemy async engine
        """
        # Construct the connection URL
        url = URL.create(
            drivername=config.db_driver,
            username=config.db_role,
            password=config.db_user_pw,
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
        )
        
        # Create the engine with the specified parameters
        engine = create_async_engine(
            url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            connect_args=config.connect_args or {},
        )
        
        # Store the engine for later use
        self.engine = engine
        return engine