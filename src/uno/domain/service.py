"""
Domain service pattern implementation for the Uno framework.

This module provides a domain service pattern implementation for implementing business
logic that doesn't naturally fit within domain entities.
"""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type

from uno.domain.core import Entity, AggregateRoot
from uno.domain.repository import Repository


T = TypeVar('T', bound=Entity)


class DomainService(Generic[T], ABC):
    """
    Base class for domain services.
    
    Domain services implement business logic that doesn't naturally fit within domain
    entities, especially when the logic operates on multiple aggregates or involves
    complex workflows.
    """
    
    def __init__(self, repository: Repository[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the domain service.
        
        Args:
            repository: The repository for the primary entity type
            logger: Optional logger instance
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        try:
            return await self.repository.get(id)
        except Exception as e:
            self.logger.error(f"Error retrieving entity by ID: {str(e)}")
            return None
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        List entities with filtering and pagination.
        
        Args:
            filters: Optional filters to apply
            order_by: Optional ordering
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the criteria
        """
        try:
            return await self.repository.list(filters, order_by, limit, offset)
        except Exception as e:
            self.logger.error(f"Error listing entities: {str(e)}")
            return []
    
    async def save(self, entity: T) -> Optional[T]:
        """
        Save an entity (create or update).
        
        This method determines whether to create a new entity or update an existing one
        based on whether the entity has an ID.
        
        Args:
            entity: The entity to save
            
        Returns:
            The saved entity with updated IDs and timestamps
        """
        try:
            if entity.id and await self.repository.exists(entity.id):
                return await self.repository.update(entity)
            else:
                return await self.repository.add(entity)
        except Exception as e:
            self.logger.error(f"Error saving entity: {str(e)}")
            return None
    
    async def delete(self, entity: T) -> bool:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        try:
            await self.repository.remove(entity)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting entity: {str(e)}")
            return False
    
    async def delete_by_id(self, id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            id: The ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        try:
            return await self.repository.remove_by_id(id)
        except Exception as e:
            self.logger.error(f"Error deleting entity by ID: {str(e)}")
            return False


class UnoEntityService(DomainService[T]):
    """
    Service implementation for Uno domain entities.
    
    This service provides a standard implementation for domain services
    using the UnoDB repository.
    """
    
    def __init__(
        self, 
        entity_type: Type[T], 
        repository: Optional[Repository[T]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the entity service.
        
        Args:
            entity_type: The type of entity this service manages
            repository: Optional repository for data access
            logger: Optional logger instance
        """
        # If no repository is provided, create a default UnoDB repository
        if repository is None:
            from uno.domain.repository import UnoDBRepository
            repository = UnoDBRepository(entity_type)
            
        super().__init__(repository, logger)
        self.entity_type = entity_type
    
    async def create(self, **data) -> Optional[T]:
        """
        Create a new entity.
        
        Args:
            **data: Entity data
            
        Returns:
            The created entity
        """
        try:
            entity = self.entity_type(**data)
            return await self.save(entity)
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            return None
    
    async def update_by_id(self, id: str, **data) -> Optional[T]:
        """
        Update an entity by ID.
        
        Args:
            id: Entity ID
            **data: Data to update
            
        Returns:
            The updated entity
        """
        try:
            entity = await self.get_by_id(id)
            if not entity:
                return None
            
            # Update entity fields
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            return await self.save(entity)
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            return None