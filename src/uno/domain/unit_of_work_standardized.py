"""
Unit of Work pattern implementation for the domain layer.

This module provides a standardized Unit of Work pattern implementation that coordinates
operations across multiple repositories and manages transactions, ensuring that multiple
operations either all succeed or all fail together.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    Dict, Generic, TypeVar, Type, Optional, Any, List, 
    Callable, AsyncContextManager, cast
)
from contextlib import AsyncExitStack, asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.core import Entity, AggregateRoot, DomainEvent
from uno.domain.repository import (
    Repository, AggregateRepository, 
    SQLAlchemyRepository, SQLAlchemyAggregateRepository, 
    InMemoryRepository, InMemoryAggregateRepository
)
from uno.core.errors.result import Result, Success, Failure


T = TypeVar("T", bound=Entity)
A = TypeVar("A", bound=AggregateRoot)


class UnitOfWork(AsyncContextManager, ABC):
    """
    Abstract Unit of Work base class.
    
    The Unit of Work pattern coordinates operations across multiple repositories
    and manages transactions.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the unit of work.
        
        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self._repositories: Dict[Type[Entity], Repository] = {}
        self._committed = False
        self._pending_events: List[DomainEvent] = []
    
    async def __aenter__(self) -> "UnitOfWork":
        """Enter the async context manager."""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager."""
        if exc_type:
            self.logger.error(f"Rolling back due to error: {exc_val}")
            await self.rollback()
        else:
            try:
                await self.commit()
            except Exception as e:
                self.logger.error(f"Error during commit: {e}")
                await self.rollback()
                raise
    
    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        self._committed = True
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        self._committed = False
    
    def register_repository(self, entity_type: Type[T], repository: Repository[T]) -> None:
        """
        Register a repository with the unit of work.
        
        Args:
            entity_type: The entity type the repository manages
            repository: The repository instance
        """
        self._repositories[entity_type] = repository
    
    def get_repository(self, entity_type: Type[T]) -> Repository[T]:
        """
        Get a repository by entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            The repository for the entity type
            
        Raises:
            KeyError: If no repository is registered for the entity type
        """
        if entity_type not in self._repositories:
            raise KeyError(f"No repository registered for entity type {entity_type.__name__}")
        
        return cast(Repository[T], self._repositories[entity_type])
    
    async def collect_events(self) -> List[DomainEvent]:
        """
        Collect events from all aggregate repositories.
        
        Returns:
            The collected events
        """
        collected_events = list(self._pending_events)
        self._pending_events.clear()
        
        # Collect from aggregate repositories
        for repo in self._repositories.values():
            if isinstance(repo, AggregateRepository):
                collected_events.extend(repo.collect_events())
        
        return collected_events
    
    @property
    def committed(self) -> bool:
        """Check if this unit of work was committed."""
        return self._committed


class SQLAlchemyUnitOfWork(UnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.
    
    This unit of work coordinates operations with SQLAlchemy repositories
    and manages database transactions.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the SQLAlchemy unit of work.
        
        Args:
            session: The SQLAlchemy session
            logger: Optional logger for diagnostic output
        """
        super().__init__(logger)
        self.session = session
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        # Start transaction if not already in one
        if not self.session.in_transaction():
            await self.session.begin()
        self.logger.debug("Started SQLAlchemy transaction")
    
    async def commit(self) -> None:
        """Commit the transaction."""
        await self.session.commit()
        await super().commit()
        self.logger.debug("Committed SQLAlchemy transaction")
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        await self.session.rollback()
        await super().rollback()
        self.logger.debug("Rolled back SQLAlchemy transaction")
    
    def repository_factory(self, entity_type: Type[T], model_class: Any) -> SQLAlchemyRepository[T, Any]:
        """
        Create a SQLAlchemy repository.
        
        Args:
            entity_type: The entity type
            model_class: The SQLAlchemy model class
            
        Returns:
            A SQLAlchemy repository
        """
        if issubclass(entity_type, AggregateRoot):
            repository = SQLAlchemyAggregateRepository(
                cast(Type[AggregateRoot], entity_type),
                self.session,
                model_class,
                self.logger,
            )
        else:
            repository = SQLAlchemyRepository(
                entity_type,
                self.session,
                model_class,
                self.logger,
            )
        
        self.register_repository(entity_type, repository)
        return repository


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory implementation of the Unit of Work pattern.
    
    This unit of work is useful for testing, with in-memory repositories
    and simulated transactions.
    """
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        self._committed = False
        self.logger.debug("Started in-memory transaction")
    
    async def commit(self) -> None:
        """Commit the transaction."""
        await super().commit()
        self.logger.debug("Committed in-memory transaction")
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        await super().rollback()
        self.logger.debug("Rolled back in-memory transaction")
    
    def repository_factory(self, entity_type: Type[T]) -> InMemoryRepository[T]:
        """
        Create an in-memory repository.
        
        Args:
            entity_type: The entity type
            
        Returns:
            An in-memory repository
        """
        if issubclass(entity_type, AggregateRoot):
            repository = InMemoryAggregateRepository(
                cast(Type[AggregateRoot], entity_type),
                self.logger,
            )
        else:
            repository = InMemoryRepository(
                entity_type,
                self.logger,
            )
        
        self.register_repository(entity_type, repository)
        return repository


@asynccontextmanager
async def create_unit_of_work(
    factory: Callable[[], UnitOfWork]
) -> AsyncContextManager[UnitOfWork]:
    """
    Create a unit of work with proper context management.
    
    Args:
        factory: Factory function to create the unit of work
        
    Yields:
        The unit of work
    """
    async with factory() as uow:
        yield uow


class UnitOfWorkManager:
    """
    Manager for multiple units of work.
    
    This manager coordinates multiple units of work, ensuring they are
    properly committed or rolled back together.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the unit of work manager.
        
        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self._uow_factories: Dict[str, Callable[[], UnitOfWork]] = {}
    
    def register_factory(self, name: str, factory: Callable[[], UnitOfWork]) -> None:
        """
        Register a unit of work factory.
        
        Args:
            name: The name of the unit of work
            factory: The factory function to create the unit of work
        """
        self._uow_factories[name] = factory
    
    @asynccontextmanager
    async def use_unit_of_work(self, name: str) -> AsyncContextManager[UnitOfWork]:
        """
        Use a registered unit of work.
        
        Args:
            name: The name of the unit of work
            
        Yields:
            The unit of work
            
        Raises:
            KeyError: If no unit of work is registered with the name
        """
        if name not in self._uow_factories:
            raise KeyError(f"No unit of work registered with name '{name}'")
        
        async with create_unit_of_work(self._uow_factories[name]) as uow:
            yield uow
    
    @asynccontextmanager
    async def use_multiple(self, *names: str) -> AsyncContextManager[Dict[str, UnitOfWork]]:
        """
        Use multiple units of work together.
        
        This ensures that all units of work are committed together or
        all rolled back if any fails.
        
        Args:
            *names: The names of the units of work to use
            
        Yields:
            Dictionary mapping names to units of work
            
        Raises:
            KeyError: If any name is not registered
        """
        for name in names:
            if name not in self._uow_factories:
                raise KeyError(f"No unit of work registered with name '{name}'")
        
        uows: Dict[str, UnitOfWork] = {}
        async with AsyncExitStack() as stack:
            for name in names:
                uow = await stack.enter_async_context(create_unit_of_work(self._uow_factories[name]))
                uows[name] = uow
            
            yield uows


async def execute_with_unit_of_work(
    uow: UnitOfWork,
    operation: Callable[[UnitOfWork], Any]
) -> Result[Any]:
    """
    Execute an operation with a unit of work.
    
    This function handles transaction management and error handling.
    
    Args:
        uow: The unit of work to use
        operation: The operation to execute with the unit of work
        
    Returns:
        A Result object with the operation result or error
    """
    try:
        await uow.begin()
        result = await operation(uow)
        await uow.commit()
        return Success(result)
    except Exception as e:
        await uow.rollback()
        return Failure(str(e))
"""