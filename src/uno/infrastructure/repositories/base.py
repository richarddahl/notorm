"""
Base repository implementations for the Uno framework.

This module provides abstract base classes implementing the repository protocols,
serving as the foundation for concrete repository implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, cast,
    AsyncIterator
)
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Select

from uno.core.errors.result import Result, Success, Failure
from uno.core.events import DomainEventProtocol
from uno.domain.core import Entity, AggregateRoot
from uno.domain.specifications import Specification
from uno.infrastructure.repositories.protocols import (
    RepositoryProtocol,
    SpecificationRepositoryProtocol,
    BatchRepositoryProtocol,
    StreamingRepositoryProtocol,
    EventCollectingRepositoryProtocol,
    FilterType
)


# Type variables
T = TypeVar("T")  # Entity type
E = TypeVar("E", bound=Entity)  # Entity type with Entity constraint
A = TypeVar("A", bound=AggregateRoot)  # Aggregate type
ID = TypeVar("ID")  # ID type


class Repository(Generic[T, ID], ABC):
    """
    Abstract base repository implementation.
    
    Provides common functionality for all repositories, regardless of the
    underlying data store.
    """
    
    def __init__(
        self, 
        entity_type: Type[T], 
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            entity_type: The type of entity this repository manages
            logger: Optional logger for diagnostic output
        """
        self.entity_type = entity_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def get(self, id: ID) -> Optional[T]:
        """Get an entity by ID."""
        pass
    
    async def get_or_fail(self, id: ID) -> Result[T]:
        """
        Get an entity by ID or return a failure result.
        
        Args:
            id: Entity ID
            
        Returns:
            Success result with entity or Failure if not found
        """
        entity = await self.get(id)
        if entity is None:
            return Failure(f"Entity with ID {id} not found")
        return Success(entity)
    
    @abstractmethod
    async def list(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[T]:
        """List entities matching filter criteria."""
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        pass
    
    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: Entity ID
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    async def delete_by_id(self, id: ID) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted, False if not found
        """
        entity = await self.get(id)
        if entity is None:
            return False
        
        await self.delete(entity)
        return True
    
    async def save(self, entity: T) -> T:
        """
        Save an entity (create or update).
        
        Args:
            entity: The entity to save
            
        Returns:
            The saved entity
        """
        # Check if entity exists by ID
        entity_id = getattr(entity, "id", None)
        if entity_id and await self.exists(entity_id):
            return await self.update(entity)
        else:
            return await self.add(entity)


class SpecificationRepository(Repository[T, ID], Generic[T, ID], ABC):
    """
    Repository implementation supporting the Specification pattern.
    
    Extends the base repository with methods for querying using specifications.
    """
    
    @abstractmethod
    async def find(self, specification: Specification[T]) -> List[T]:
        """Find entities matching a specification."""
        pass
    
    @abstractmethod
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """Find a single entity matching a specification."""
        pass
    
    @abstractmethod
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """Count entities matching a specification."""
        pass


class BatchRepository(Repository[T, ID], Generic[T, ID], ABC):
    """
    Repository implementation supporting batch operations.
    
    Extends the base repository with methods for operating on multiple entities.
    """
    
    @abstractmethod
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """Add multiple entities."""
        pass
    
    @abstractmethod
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """Update multiple entities."""
        pass
    
    @abstractmethod
    async def delete_many(self, entities: Iterable[T]) -> None:
        """Delete multiple entities."""
        pass
    
    @abstractmethod
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """Delete entities by their IDs."""
        pass


class StreamingRepository(Repository[T, ID], Generic[T, ID], ABC):
    """
    Repository implementation supporting streaming large result sets.
    
    Extends the base repository with methods for handling large data volumes.
    """
    
    @abstractmethod
    async def stream(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """Stream entities matching filter criteria."""
        pass


class EventCollectingRepository(Repository[T, ID], Generic[T, ID], ABC):
    """
    Repository implementation that collects domain events.
    
    Useful for aggregate repositories that need to track domain events.
    """
    
    def __init__(
        self, 
        entity_type: Type[T], 
        logger: Optional[logging.Logger] = None
    ):
        """Initialize with empty events collection."""
        super().__init__(entity_type, logger)
        self._pending_events: List[DomainEventProtocol] = []
    
    def collect_events(self) -> List[DomainEventProtocol]:
        """
        Collect and clear pending domain events.
        
        Returns:
            List of pending domain events
        """
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
    
    def _collect_events_from_entity(self, entity: Any) -> None:
        """
        Collect events from an entity that supports event collection.
        
        Args:
            entity: The entity to collect events from
        """
        if hasattr(entity, "clear_events") and callable(entity.clear_events):
            events = entity.clear_events()
            self._pending_events.extend(events)
        
        # Collect from child entities if this is an aggregate
        if hasattr(entity, "get_child_entities") and callable(entity.get_child_entities):
            for child in entity.get_child_entities():
                self._collect_events_from_entity(child)


class AggregateRepository(EventCollectingRepository[A, ID], Generic[A, ID], ABC):
    """
    Repository specifically for aggregate roots.
    
    Provides specialized handling for aggregates, including version checks and event collection.
    """
    
    async def save(self, aggregate: A) -> A:
        """
        Save an aggregate (create or update) with event collection.
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            The saved aggregate
        """
        # Apply changes to ensure invariants and increment version if needed
        if hasattr(aggregate, "apply_changes") and callable(aggregate.apply_changes):
            aggregate.apply_changes()
        
        # Collect events before saving
        self._collect_events_from_entity(aggregate)
        
        # Save using standard save method
        return await super().save(aggregate)
    
    async def update(self, aggregate: A) -> A:
        """
        Update an aggregate with version checking.
        
        Args:
            aggregate: The aggregate to update
            
        Returns:
            The updated aggregate
        """
        # Collect events before updating
        self._collect_events_from_entity(aggregate)
        
        # Delegate to implementation
        return await super().update(aggregate)


class CompleteRepository(
    SpecificationRepository[T, ID],
    BatchRepository[T, ID],
    StreamingRepository[T, ID],
    EventCollectingRepository[T, ID],
    Generic[T, ID],
    ABC
):
    """
    A complete repository implementing all repository capabilities.
    
    This class combines all repository features into a single implementation.
    Use this when you need a repository with all capabilities.
    """
    pass