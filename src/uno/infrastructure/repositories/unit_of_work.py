"""
Unit of Work pattern implementation for the Uno framework.

This module provides implementations of the Unit of Work pattern, which
manages transaction boundaries and coordinates the work of multiple repositories.

DEPRECATED: This implementation is deprecated in favor of the new unified
implementation in uno.core.uow. Use AbstractUnitOfWork, DatabaseUnitOfWork, and
related classes from uno.core.uow instead.
"""

import logging
import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, cast

from sqlalchemy.ext.asyncio import AsyncSession

from uno.infrastructure.repositories.protocols import UnitOfWorkProtocol


warnings.warn(
    "The UnitOfWork implementation in uno.infrastructure.repositories.unit_of_work is deprecated. "
    "Use AbstractUnitOfWork, DatabaseUnitOfWork, and related classes from uno.core.uow instead.",
    DeprecationWarning,
    stacklevel=2
)


# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type


class UnitOfWork(UnitOfWorkProtocol, ABC):
    """
    Abstract base class for unit of work implementations.
    
    The Unit of Work pattern maintains a list of objects affected by a business
    transaction and coordinates the writing out of changes and resolving concurrency problems.
    
    DEPRECATED: Use AbstractUnitOfWork from uno.core.uow instead.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the unit of work.
        
        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.repositories: List[Any] = []
    
    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        pass
    
    async def __aenter__(self) -> "UnitOfWork":
        """Enter the unit of work context."""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the unit of work context."""
        if exc_type:
            # An exception occurred, roll back the transaction
            self.logger.error(f"Transaction failed: {exc_val}")
            await self.rollback()
        # else:
            # No exception, but don't commit automatically
            # This is intentional - the caller should explicitly commit
            # await self.commit()
    
    def register_repository(self, repository: Any) -> None:
        """
        Register a repository with this unit of work.
        
        Args:
            repository: The repository to register
        """
        self.repositories.append(repository)


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory implementation of the Unit of Work pattern.
    
    This implementation is useful for testing and does not provide actual
    transaction boundaries since in-memory repositories don't support transactions.
    
    DEPRECATED: Use InMemoryUnitOfWork from uno.core.uow instead.
    """
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        # No actual transaction in memory
        pass
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        # No actual transaction in memory
        # Publish events from repositories
        self._publish_events()
    
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        # No actual transaction in memory
        pass
    
    def _publish_events(self) -> None:
        """Publish events from all registered repositories."""
        from uno.core.events import publish_event
        
        for repository in self.repositories:
            if hasattr(repository, "collect_events") and callable(repository.collect_events):
                events = repository.collect_events()
                for event in events:
                    publish_event(event)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.
    
    This implementation provides transaction boundaries using SQLAlchemy sessions.
    
    DEPRECATED: Use SqlAlchemyUnitOfWork from uno.core.uow instead.
    """
    
    def __init__(
        self, 
        session: AsyncSession,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQLAlchemy unit of work.
        
        Args:
            session: SQLAlchemy async session
            logger: Optional logger for diagnostic output
        """
        super().__init__(logger)
        self.session = session
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        # Start a new transaction if not already in one
        await self.session.begin()
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        try:
            # Commit the transaction
            await self.session.commit()
            
            # Publish events after successful commit
            self._publish_events()
        except Exception as e:
            self.logger.error(f"Error committing transaction: {e}")
            await self.rollback()
            raise
    
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self.session.rollback()
    
    def _publish_events(self) -> None:
        """Publish events from all registered repositories."""
        from uno.core.events import publish_event
        
        for repository in self.repositories:
            if hasattr(repository, "collect_events") and callable(repository.collect_events):
                events = repository.collect_events()
                for event in events:
                    publish_event(event)