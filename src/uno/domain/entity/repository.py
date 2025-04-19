"""
Repository implementations for the domain entity framework.

This module provides concrete repository implementations that work with domain entities
and support the Specification pattern for querying.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, 
    AsyncIterator, Protocol, runtime_checkable, cast
)

from uno.core.errors.result import Result, Success, Failure
from uno.domain.entity.base import EntityBase
from uno.domain.entity.specification.base import Specification

# Type variables
T = TypeVar("T", bound=EntityBase)  # Entity type
ID = TypeVar("ID")  # ID type


class EntityRepository(Generic[T, ID], ABC):
    """
    Repository implementation for domain entities.
    
    This class provides base functionality for repositories that work with domain entities,
    including support for specifications.
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
        """
        Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            The entity if found, None otherwise
        """
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
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[T]:
        """
        List entities matching filter criteria.
        
        Args:
            filters: Optional filter criteria as a dictionary
            order_by: Optional list of fields to order by
            limit: Optional limit on number of results
            offset: Optional offset for pagination
            
        Returns:
            List of entities matching criteria
        """
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity with any generated values (e.g., ID)
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        pass
    
    @abstractmethod
    async def delete(self, entity: T) -> None:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
        """
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
    
    @abstractmethod
    async def find(self, specification: Specification[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            List of entities matching the specification
        """
        pass
    
    @abstractmethod
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            The first entity matching the specification, or None if none found
        """
        pass
    
    @abstractmethod
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: Optional specification to match against
            
        Returns:
            Number of entities matching the specification
        """
        pass
    
    @abstractmethod
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """
        Add multiple entities.
        
        Args:
            entities: Iterable of entities to add
            
        Returns:
            List of added entities with any generated values
        """
        pass
    
    @abstractmethod
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """
        Update multiple entities.
        
        Args:
            entities: Iterable of entities to update
            
        Returns:
            List of updated entities
        """
        pass
    
    @abstractmethod
    async def delete_many(self, entities: Iterable[T]) -> None:
        """
        Delete multiple entities.
        
        Args:
            entities: Iterable of entities to delete
        """
        pass
    
    @abstractmethod
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """
        Delete entities by their IDs.
        
        Args:
            ids: Iterable of entity IDs to delete
            
        Returns:
            Number of entities deleted
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        specification: Optional[Specification[T]] = None,
        order_by: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """
        Stream entities matching a specification.
        
        Args:
            specification: Optional specification to match against
            order_by: Optional list of fields to order by
            batch_size: Size of batches to fetch
            
        Returns:
            Async iterator of entities matching the specification
        """
        pass