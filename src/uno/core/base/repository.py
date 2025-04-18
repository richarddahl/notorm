"""
Base repository protocols and classes for the Uno framework.

This module defines the core repository interfaces and base implementation classes
that form the foundation of the repository pattern in the Uno framework.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, 
    AsyncIterator, Protocol, runtime_checkable
)

from uno.core.errors.result import Result, Success, Failure

# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type


@runtime_checkable
class FilterProtocol(Protocol):
    """Protocol for filter objects that can be converted to dict form."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary form."""
        ...


# Type alias for filter arguments
FilterType = Dict[str, Any]


@runtime_checkable
class RepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol defining the standard repository interface.
    
    This protocol defines the basic operations that all repositories must support.
    """
    
    async def get(self, id: ID) -> Optional[T]:
        """Get an entity by ID."""
        ...
    
    async def list(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        """List entities matching filter criteria."""
        ...
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        ...
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        ...
    
    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        ...
    
    async def exists(self, id: ID) -> bool:
        """Check if an entity with the given ID exists."""
        ...


@runtime_checkable
class SpecificationRepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol for the Specification pattern.
    
    This protocol defines operations for repositories that support the Specification pattern.
    """
    
    async def find(self, specification: Any) -> List[T]:
        """Find entities matching a specification."""
        ...
    
    async def find_one(self, specification: Any) -> Optional[T]:
        """Find a single entity matching a specification."""
        ...
    
    async def count(self, specification: Optional[Any] = None) -> int:
        """Count entities matching a specification."""
        ...


@runtime_checkable
class BatchRepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol for batch operations.
    
    This protocol defines operations for repositories that support batch operations.
    """
    
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """Add multiple entities."""
        ...
    
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """Update multiple entities."""
        ...
    
    async def delete_many(self, entities: Iterable[T]) -> None:
        """Delete multiple entities."""
        ...
    
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """Delete entities by their IDs."""
        ...


@runtime_checkable
class StreamingRepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol for streaming large result sets.
    
    This protocol defines operations for repositories that support streaming data.
    """
    
    async def stream(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """Stream entities matching filter criteria."""
        ...


class BaseRepository(Generic[T, ID], ABC):
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


class SpecificationRepository(BaseRepository[T, ID], Generic[T, ID], ABC):
    """
    Repository implementation supporting the Specification pattern.
    
    Extends the base repository with methods for querying using specifications.
    """
    
    @abstractmethod
    async def find(self, specification: Any) -> List[T]:
        """Find entities matching a specification."""
        pass
    
    @abstractmethod
    async def find_one(self, specification: Any) -> Optional[T]:
        """Find a single entity matching a specification."""
        pass
    
    @abstractmethod
    async def count(self, specification: Optional[Any] = None) -> int:
        """Count entities matching a specification."""
        pass


class BatchRepository(BaseRepository[T, ID], Generic[T, ID], ABC):
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


class StreamingRepository(BaseRepository[T, ID], Generic[T, ID], ABC):
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


class CompleteRepository(
    SpecificationRepository[T, ID],
    BatchRepository[T, ID],
    StreamingRepository[T, ID],
    Generic[T, ID],
    ABC
):
    """
    A complete repository implementing all repository capabilities.
    
    This class combines all repository features into a single implementation.
    Use this when you need a repository with all capabilities.
    """
    pass