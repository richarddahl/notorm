"""
Unified database provider for Uno.

This module provides a centralized access point for database connections,
supporting both synchronous and asynchronous access patterns.
"""

import logging
from typing import Optional, AsyncContextManager, ContextManager, Dict, Any
from contextlib import asynccontextmanager, contextmanager

import asyncpg
import psycopg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import NullPool

from uno.database.config import ConnectionConfig


class DatabaseProvider:
    """
    Central database connection provider for Uno.
    
    This class manages database connections and sessions for both
    synchronous and asynchronous operations. It is the single entry point
    for database access in Uno applications.
    """
    
    def __init__(
        self, 
        config: ConnectionConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the database provider with connection configuration.
        
        Args:
            config: Database connection configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Engine instances - lazy initialized
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_engine: Optional[Engine] = None
        
        # Session factories - lazy initialized
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._sync_session_factory: Optional[sessionmaker] = None
        
        # Connection pools for direct access - lazy initialized
        self._async_pool: Optional[asyncpg.Pool] = None
        self._sync_pool: Optional[psycopg.Connection] = None
    
    def _get_async_engine(self) -> AsyncEngine:
        """
        Get or create the SQLAlchemy async engine.
        
        Returns:
            SQLAlchemy AsyncEngine instance
        """
        if self._async_engine is None:
            self.logger.debug("Creating async SQLAlchemy engine")
            
            # Create the async engine
            self._async_engine = create_async_engine(
                self.config.get_uri(),
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False,
                connect_args=self.config.connect_args or {},
            )
            
        return self._async_engine
    
    def _get_sync_engine(self) -> Engine:
        """
        Get or create the SQLAlchemy sync engine.
        
        Returns:
            SQLAlchemy Engine instance
        """
        if self._sync_engine is None:
            self.logger.debug("Creating sync SQLAlchemy engine")
            
            # Create the sync engine
            sync_uri = self.config.get_uri().replace("+asyncpg", "+psycopg")
            self._sync_engine = create_engine(
                sync_uri,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False,
                connect_args=self.config.connect_args or {},
            )
            
        return self._sync_engine
    
    def _get_async_session_factory(self) -> async_sessionmaker:
        """
        Get or create the SQLAlchemy async session factory.
        
        Returns:
            SQLAlchemy async_sessionmaker instance
        """
        if self._async_session_factory is None:
            self.logger.debug("Creating async SQLAlchemy session factory")
            
            # Create the async session factory
            engine = self._get_async_engine()
            self._async_session_factory = async_sessionmaker(
                engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            
        return self._async_session_factory
    
    def _get_sync_session_factory(self) -> sessionmaker:
        """
        Get or create the SQLAlchemy sync session factory.
        
        Returns:
            SQLAlchemy sessionmaker instance
        """
        if self._sync_session_factory is None:
            self.logger.debug("Creating sync SQLAlchemy session factory")
            
            # Create the sync session factory
            engine = self._get_sync_engine()
            self._sync_session_factory = sessionmaker(
                engine,
                expire_on_commit=False,
                class_=Session
            )
            
        return self._sync_session_factory
    
    async def _get_async_pool(self) -> asyncpg.Pool:
        """
        Get or create the asyncpg connection pool.
        
        Returns:
            asyncpg connection pool
        """
        if self._async_pool is None:
            self.logger.debug("Creating asyncpg connection pool")
            
            # Create the asyncpg pool
            self._async_pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_role,
                password=self.config.db_user_pw,
                database=self.config.db_name,
                min_size=2,
                max_size=self.config.pool_size,
                command_timeout=self.config.pool_timeout,
                max_inactive_connection_lifetime=self.config.pool_recycle,
                server_settings=self.config.connect_args or {}
            )
            
        return self._async_pool
    
    def _get_sync_pool(self) -> psycopg.Connection:
        """
        Get a psycopg connection.
        
        Returns:
            psycopg connection
        """
        # Unlike asyncpg, psycopg doesn't have a built-in pooling API
        # so we just create a new connection each time
        self.logger.debug("Creating psycopg connection")
        
        # Create the psycopg connection
        conn = psycopg.connect(
            host=self.config.db_host,
            port=self.config.db_port,
            user=self.config.db_role,
            password=self.config.db_user_pw,
            dbname=self.config.db_name,
            # No direct connection parameter mapping for pool settings
            # Use separate connection pooling if needed
        )
        
        return conn
    
    @asynccontextmanager
    async def async_session(self) -> AsyncContextManager[AsyncSession]:
        """
        Get an async session for ORM operations.
        
        This method provides a context manager for using an async session.
        
        Yields:
            AsyncSession: SQLAlchemy async session
        """
        session_factory = self._get_async_session_factory()
        session = session_factory()
        
        try:
            yield session
        finally:
            await session.close()
    
    @contextmanager
    def sync_session(self) -> ContextManager[Session]:
        """
        Get a sync session for ORM operations.
        
        This method provides a context manager for using a sync session.
        
        Yields:
            Session: SQLAlchemy sync session
        """
        session_factory = self._get_sync_session_factory()
        session = session_factory()
        
        try:
            yield session
        finally:
            session.close()
    
    @asynccontextmanager
    async def async_connection(self) -> AsyncContextManager[asyncpg.Connection]:
        """
        Get a raw async connection from the pool.
        
        This method provides a context manager for using a raw asyncpg connection.
        Useful for operations that require features specific to asyncpg.
        
        Yields:
            asyncpg.Connection: Raw asyncpg connection
        """
        pool = await self._get_async_pool()
        conn = await pool.acquire()
        
        try:
            yield conn
        finally:
            await pool.release(conn)
    
    @contextmanager
    def sync_connection(self) -> ContextManager[psycopg.Connection]:
        """
        Get a raw sync connection.
        
        This method provides a context manager for using a raw psycopg connection.
        Useful for DDL operations and other tasks that require synchronous access.
        
        Yields:
            psycopg.Connection: Raw psycopg connection
        """
        conn = self._get_sync_pool()
        
        try:
            yield conn
        finally:
            conn.close()
    
    async def health_check(self) -> bool:
        """
        Check the health of database connections.
        
        This method verifies that the database is accessible and functioning
        correctly by performing a simple query.
        
        Returns:
            bool: True if the database is healthy, False otherwise
        """
        try:
            async with self.async_connection() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return False
    
    async def close(self) -> None:
        """
        Close all database connections and pools.
        
        This method should be called when shutting down the application
        to release all database resources.
        """
        # Close the async engine
        if self._async_engine is not None:
            self.logger.debug("Closing async SQLAlchemy engine")
            await self._async_engine.dispose()
            self._async_engine = None
        
        # Close the sync engine
        if self._sync_engine is not None:
            self.logger.debug("Closing sync SQLAlchemy engine")
            self._sync_engine.dispose()
            self._sync_engine = None
        
        # Close the asyncpg pool
        if self._async_pool is not None:
            self.logger.debug("Closing asyncpg connection pool")
            await self._async_pool.close()
            self._async_pool = None
        
        # The sync pool is created on-demand, so nothing to close there