"""
Concrete Unit of Work implementations.

This module defines concrete implementations of the Unit of Work pattern
for different data storage mechanisms.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import (
    Any, Dict, List, Optional, Type, TypeVar, Generic, Callable,
    AsyncContextManager, cast, Protocol, runtime_checkable, Union,
)

from uno.core.uow.base import AbstractUnitOfWork
from uno.core.events import AsyncEventBus, Event


# Type aliases
ConnectionFactory = Callable[[], Any]
UnitOfWorkFactory = Callable[[], AsyncContextManager[AbstractUnitOfWork]]


class DatabaseUnitOfWork(AbstractUnitOfWork):
    """
    Database implementation of the Unit of Work pattern.
    
    This implementation works with database connections and transactions,
    providing transaction boundaries and ensuring consistency across
    multiple repositories.
    """
    
    def __init__(
        self,
        connection_factory: ConnectionFactory,
        event_bus: Optional[AsyncEventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the database Unit of Work.
        
        Args:
            connection_factory: Callable that returns a database connection
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostics
        """
        super().__init__(event_bus, logger)
        self._connection_factory = connection_factory
        self._connection = None
        self._transaction = None
    
    async def begin(self) -> None:
        """
        Begin a new database transaction.
        
        This creates a new connection if needed and begins a transaction.
        """
        if self._connection is None:
            self._connection = await self._connection_factory()
        
        self._transaction = await self._connection.transaction()
        self._logger.debug("Database transaction started")
    
    async def commit(self) -> None:
        """
        Commit the current database transaction.
        
        If no transaction is active, this is a no-op.
        """
        if self._transaction:
            await self._transaction.commit()
            self._transaction = None
            self._logger.debug("Database transaction committed")
    
    async def rollback(self) -> None:
        """
        Rollback the current database transaction.
        
        If no transaction is active, this is a no-op.
        """
        if self._transaction:
            await self._transaction.rollback()
            self._transaction = None
            self._logger.debug("Database transaction rolled back")
    
    async def close(self) -> None:
        """
        Close the database connection.
        
        This is called automatically when the Unit of Work is disposed.
        """
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._logger.debug("Database connection closed")


class InMemoryUnitOfWork(AbstractUnitOfWork):
    """
    In-memory implementation of the Unit of Work pattern.
    
    This implementation is primarily for testing and does not provide
    actual transaction boundaries since in-memory repositories typically
    don't support transactions.
    """
    
    def __init__(
        self,
        event_bus: Optional[AsyncEventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the in-memory Unit of Work.
        
        Args:
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostics
        """
        super().__init__(event_bus, logger)
        self._is_active = False
    
    async def begin(self) -> None:
        """
        Begin a new "transaction".
        
        For in-memory repositories, this simply marks the Unit of Work as active.
        """
        self._is_active = True
        self._logger.debug("In-memory transaction started")
    
    async def commit(self) -> None:
        """
        Commit the current "transaction".
        
        For in-memory repositories, this simply clears the active flag.
        """
        if self._is_active:
            self._is_active = False
            self._logger.debug("In-memory transaction committed")
    
    async def rollback(self) -> None:
        """
        Rollback the current "transaction".
        
        For in-memory repositories, this simply clears the active flag.
        """
        if self._is_active:
            self._is_active = False
            self._logger.debug("In-memory transaction rolled back")


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.
    
    This implementation works with SQLAlchemy sessions, providing transaction
    boundaries and ensuring consistency across multiple repositories.
    """
    
    def __init__(
        self,
        session_factory: Callable[[], Any],
        event_bus: Optional[AsyncEventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the SQLAlchemy Unit of Work.
        
        Args:
            session_factory: Callable that returns a SQLAlchemy session
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostics
        """
        super().__init__(event_bus, logger)
        self._session_factory = session_factory
        self._session = None
    
    async def begin(self) -> None:
        """
        Begin a new SQLAlchemy transaction.
        
        This creates a new session if needed and begins a transaction.
        """
        if self._session is None:
            self._session = self._session_factory()
        
        # Start a transaction if not already in one
        await self._session.begin()
        self._logger.debug("SQLAlchemy transaction started")
    
    async def commit(self) -> None:
        """
        Commit the current SQLAlchemy transaction.
        
        If no session is active, this is a no-op.
        """
        if self._session:
            await self._session.commit()
            self._logger.debug("SQLAlchemy transaction committed")
    
    async def rollback(self) -> None:
        """
        Rollback the current SQLAlchemy transaction.
        
        If no session is active, this is a no-op.
        """
        if self._session:
            await self._session.rollback()
            self._logger.debug("SQLAlchemy transaction rolled back")
    
    async def close(self) -> None:
        """
        Close the SQLAlchemy session.
        
        This is called automatically when the Unit of Work is disposed.
        """
        if self._session:
            await self._session.close()
            self._session = None
            self._logger.debug("SQLAlchemy session closed")