"""
Repository implementations for the domain entity framework.

This module provides concrete repository implementations that work with domain entities
and support the Specification pattern for querying.
"""

from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Generic, TypeVar

from uno.core.entity import ID
from uno.core.errors.result import Result
from uno.domain.entity.base import EntityBase
from uno.domain.entity.specification.base import Specification

T = TypeVar("T", bound=EntityBase)  # Entity type


class EntityRepository(Generic[T]):
    """
    Base repository implementation for entity operations.
    """
    
    def __init__(self, entity_type: type[T], optional_fields: list[str] | None = None):
        self.entity_type = entity_type
        self.optional_fields = optional_fields or []
    
    @abstractmethod
    async def get(self, id: ID) -> Result[T | None, str]:
        """
        Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Result containing the entity if found or None, or a Failure with error message
        """
        pass
    
    async def get_or_fail(self, id: ID) -> Result[T, str]:
        """
        Get an entity by ID or return a failure result.
        
        Args:
            id: Entity ID
            
        Returns:
            Success result with entity or Failure if not found
        """
        result = await self.get(id)
        if result.is_failure():
            return Result.failure(result.error())
            
        entity = result.value()
        if entity is None:
            return Result.failure(f"Entity with ID {id} not found")
            
        return Result.success(entity)
    
    @abstractmethod
    async def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = 0,
    ) -> Result[list[T], str]:
        """
        List entities matching filter criteria.
        
        Args:
            filters: Optional filter criteria as a dictionary
            order_by: Optional list of fields to order by
            limit: Optional limit on number of results
            offset: Optional offset for pagination
            
        Returns:
            Result containing a list of entities matching criteria or an error message
        """
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> Result[T, str]:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            Result containing the added entity with any generated values (e.g., ID) or an error message
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> Result[T, str]:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            Result containing the updated entity or an error message
        """
        pass
    
    @abstractmethod
    async def delete(self, entity: T) -> Result[bool, str]:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
            
        Returns:
            Result indicating success (True) or failure with an error message
        """
        pass
    
    @abstractmethod
    async def exists(self, id: ID) -> Result[bool, str]:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: Entity ID
            
        Returns:
            Result containing True if entity exists, False otherwise
        """
        pass
    
    async def delete_by_id(self, id: ID) -> Result[bool, str]:
        """
        Delete an entity by ID.
        
        Args:
            id: ID of the entity to delete
            
        Returns:
            Result containing True if entity was deleted or an error message
        """
        result = await self.get(id)
        if result.is_failure():
            return Result.failure(result.error())
        
        if result.value() is None:
            return Result.failure(f"Entity with ID {id} not found")
        
        result = await self.delete(result.value())
        if result.is_failure():
            return Result.failure(result.error())
        
        return Result.success(result.value())
    
    async def save(self, entity: T) -> Result[T, str]:
        """
        Save an entity (create or update).
        
        Args:
            entity: The entity to save
            
        Returns:
            Result containing the saved entity with any generated values or an error message
        """
        if hasattr(entity, "id") and entity.id is not None:
            return await self.update(entity)
        else:
            return await self.add(entity)
    
    @abstractmethod
    async def find(
        self, specification: Specification | None = None
    ) -> Result[list[T], str]:
        """
        Find all entities matching the specification.
        
        Args:
            specification: Optional specification to filter entities
            
        Returns:
            Result containing list of matching entities or an error message
        """
        pass
    
    @abstractmethod
    async def find_one(
        self, specification: Specification | None = None
    ) -> Result[T | None, str]:
        """
        Find a single entity matching the specification.
        
        Args:
            specification: Optional specification to filter entities
            
        Returns:
            Result containing matching entity or None if not found
        """
        pass
    
    @abstractmethod
    async def count(
        self, specification: Specification | None = None
    ) -> Result[int, str]:
        """
        Count entities matching the specification.
        
        Args:
            specification: Optional specification to filter entities
            
        Returns:
            Result containing count of matching entities or an error message
        """
        pass
    
    @abstractmethod
    async def bulk_add(self, entities: list[T]) -> Result[list[T], str]:
        """
        Add multiple entities in bulk.
        
        Args:
            entities: List of entities to add
            
        Returns:
            Result containing list of added entities with generated values or an error message
        """
        pass
    
    @abstractmethod
    async def bulk_update(self, entities: list[T]) -> Result[list[T], str]:
        """
        Update multiple entities in bulk.
        
        Args:
            entities: List of entities to update
            
        Returns:
            Result containing list of updated entities or an error message
        """
        pass
    
    @abstractmethod
    async def bulk_delete(self, entities: list[T]) -> Result[bool, str]:
        """
        Delete multiple entities in bulk.
        
        Args:
            entities: List of entities to delete
            
        Returns:
            Result indicating success (True) or failure with an error message
        """
        pass
    
    @abstractmethod
    async def bulk_delete_by_ids(self, ids: list[ID]) -> Result[list[ID], str]:
        """
        Delete multiple entities by their IDs.
        
        Args:
            ids: List of entity IDs to delete
            
        Returns:
            Result containing list of IDs that were successfully deleted or an error message
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        specification: Specification | None = None,
        order_by: list[str] | None = None,
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