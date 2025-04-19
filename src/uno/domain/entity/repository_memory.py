"""
In-memory repository implementation for domain entities.

This module provides an in-memory repository implementation that is useful
for testing and prototyping.
"""

import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, AsyncIterator, cast

from uno.core.errors.result import Result, Success, Failure
from uno.domain.entity.base import EntityBase
from uno.domain.entity.specification.base import Specification
from uno.domain.entity.repository import EntityRepository

# Type variables
T = TypeVar("T", bound=EntityBase)  # Entity type
ID = TypeVar("ID")  # ID type


class InMemoryRepository(EntityRepository[T, ID], Generic[T, ID]):
    """
    In-memory repository implementation for domain entities.
    
    This class provides an implementation of the EntityRepository interface
    that stores entities in memory. It is useful for testing and prototyping.
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
        super().__init__(entity_type, logger)
        self._entities: Dict[ID, T] = {}
    
    async def get(self, id: ID) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        return deepcopy(self._entities.get(id))
    
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
        # Convert values to list
        entities = list(self._entities.values())
        
        # Apply filters if provided
        if filters:
            entities = [
                e for e in entities 
                if all(
                    getattr(e, key) == value 
                    for key, value in filters.items() 
                    if hasattr(e, key)
                )
            ]
        
        # Apply ordering if provided
        if order_by:
            for field in reversed(order_by):
                reverse = False
                if field.startswith('-'):
                    field = field[1:]
                    reverse = True
                
                entities.sort(
                    key=lambda e: getattr(e, field) if hasattr(e, field) else None,
                    reverse=reverse
                )
        
        # Apply pagination
        if offset:
            entities = entities[offset:]
        if limit:
            entities = entities[:limit]
        
        # Return deep copies to prevent modification
        return [deepcopy(e) for e in entities]
    
    async def add(self, entity: T) -> T:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity with any generated values
        """
        # Ensure entity has an ID
        if entity.id is None:
            raise ValueError("Entity must have an ID")
        
        # Check if entity already exists
        if entity.id in self._entities:
            raise ValueError(f"Entity with ID {entity.id} already exists")
        
        # Set created/updated timestamps if not set
        now = datetime.now()
        if not hasattr(entity, 'created_at') or entity.created_at is None:
            entity.created_at = now
        if not hasattr(entity, 'updated_at') or entity.updated_at is None:
            entity.updated_at = now
        
        # Store a deep copy to prevent modification of the original
        self._entities[entity.id] = deepcopy(entity)
        
        return deepcopy(entity)
    
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        # Ensure entity has an ID
        if entity.id is None:
            raise ValueError("Entity must have an ID")
        
        # Check if entity exists
        if entity.id not in self._entities:
            raise ValueError(f"Entity with ID {entity.id} does not exist")
        
        # Update timestamp
        entity.updated_at = datetime.now()
        
        # Store a deep copy to prevent modification of the original
        self._entities[entity.id] = deepcopy(entity)
        
        return deepcopy(entity)
    
    async def delete(self, entity: T) -> None:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
        """
        # Ensure entity has an ID
        if entity.id is None:
            raise ValueError("Entity must have an ID")
        
        # Check if entity exists
        if entity.id not in self._entities:
            raise ValueError(f"Entity with ID {entity.id} does not exist")
        
        # Remove entity
        del self._entities[entity.id]
    
    async def exists(self, id: ID) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: Entity ID
            
        Returns:
            True if exists, False otherwise
        """
        return id in self._entities
    
    async def find(self, specification: Specification[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            List of entities matching the specification
        """
        return [
            deepcopy(e) 
            for e in self._entities.values() 
            if specification.is_satisfied_by(e)
        ]
    
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            The first entity matching the specification, or None if none found
        """
        for entity in self._entities.values():
            if specification.is_satisfied_by(entity):
                return deepcopy(entity)
        return None
    
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: Optional specification to match against
            
        Returns:
            Number of entities matching the specification
        """
        if specification is None:
            return len(self._entities)
        
        return len([
            e for e in self._entities.values() 
            if specification.is_satisfied_by(e)
        ])
    
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """
        Add multiple entities.
        
        Args:
            entities: Iterable of entities to add
            
        Returns:
            List of added entities with any generated values
        """
        added = []
        for entity in entities:
            added.append(await self.add(entity))
        return added
    
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """
        Update multiple entities.
        
        Args:
            entities: Iterable of entities to update
            
        Returns:
            List of updated entities
        """
        updated = []
        for entity in entities:
            updated.append(await self.update(entity))
        return updated
    
    async def delete_many(self, entities: Iterable[T]) -> None:
        """
        Delete multiple entities.
        
        Args:
            entities: Iterable of entities to delete
        """
        for entity in entities:
            await self.delete(entity)
    
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """
        Delete entities by their IDs.
        
        Args:
            ids: Iterable of entity IDs to delete
            
        Returns:
            Number of entities deleted
        """
        count = 0
        for id in ids:
            if id in self._entities:
                del self._entities[id]
                count += 1
        return count
    
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
            batch_size: Size of batches to fetch (ignored in in-memory implementation)
            
        Returns:
            Async iterator of entities matching the specification
        """
        # Get entities matching specification
        entities = list(self._entities.values())
        if specification:
            entities = [e for e in entities if specification.is_satisfied_by(e)]
        
        # Apply ordering if provided
        if order_by:
            for field in reversed(order_by):
                reverse = False
                if field.startswith('-'):
                    field = field[1:]
                    reverse = True
                
                entities.sort(
                    key=lambda e: getattr(e, field) if hasattr(e, field) else None,
                    reverse=reverse
                )
        
        # Yield entities one by one
        for entity in entities:
            yield deepcopy(entity)
    
    def clear(self) -> None:
        """
        Clear all entities from the repository.
        
        This method is useful for testing to reset the repository state.
        """
        self._entities.clear()