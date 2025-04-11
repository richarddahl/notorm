"""
Base entity service implementation for Uno framework.

This module provides a bridge between the UnoObj business logic layer
and the dependency injection service pattern.
"""

import logging
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, cast

from uno.obj import UnoObj

T = TypeVar("T", bound=UnoObj)


class UnoEntityService(Generic[T]):
    """
    Service for working with UnoObj entities.
    
    This service provides a bridge between the UnoObj pattern and
    the dependency injection service pattern, allowing UnoObj classes
    to be used with the dependency injection system.
    """
    
    def __init__(self, entity_class: Type[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the entity service.
        
        Args:
            entity_class: The UnoObj class to create a service for
            logger: Optional logger instance
        """
        self.entity_class = entity_class
        self.logger = logger or logging.getLogger(__name__)
        
    async def get(self, **kwargs) -> Optional[T]:
        """
        Get an entity by attributes.
        
        Args:
            **kwargs: Attributes to filter by (e.g., id="123")
            
        Returns:
            The entity if found, None otherwise
        """
        try:
            return await self.entity_class.get(**kwargs)
        except Exception as e:
            self.logger.error(f"Error getting {self.entity_class.__name__}: {str(e)}")
            return None
    
    async def filter(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        Filter entities by attributes.
        
        Args:
            filters: Dictionary of attributes to filter by
            
        Returns:
            List of entities matching the filter
        """
        try:
            return await self.entity_class.filter(filters=filters)
        except Exception as e:
            self.logger.error(f"Error filtering {self.entity_class.__name__}: {str(e)}")
            return []
    
    async def create(self, **data) -> Optional[T]:
        """
        Create a new entity.
        
        Args:
            **data: Entity data
            
        Returns:
            The created entity
        """
        try:
            entity = self.entity_class(**data)
            model = await entity.save()
            # Reload entity with the saved model data
            return self.entity_class(**model.model_dump())
        except Exception as e:
            self.logger.error(f"Error creating {self.entity_class.__name__}: {str(e)}")
            return None
    
    async def update(self, id: str, **data) -> Optional[T]:
        """
        Update an existing entity.
        
        Args:
            id: Entity ID
            **data: Data to update
            
        Returns:
            The updated entity
        """
        try:
            entity = await self.get(id=id)
            if not entity:
                return None
            
            # Update fields
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            # Save changes
            model = await entity.save()
            return self.entity_class(**model.model_dump())
        except Exception as e:
            self.logger.error(f"Error updating {self.entity_class.__name__}: {str(e)}")
            return None
    
    async def delete(self, id: str) -> bool:
        """
        Delete an entity.
        
        Args:
            id: Entity ID
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        try:
            entity = await self.get(id=id)
            if entity:
                await entity.delete()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting {self.entity_class.__name__}: {str(e)}")
            return False
    
    async def merge(self, **data) -> tuple[Any, str]:
        """
        Merge an entity.
        
        This method attempts to find an existing entity matching the provided
        data. If found, it updates the entity. If not found, it creates a new one.
        
        Args:
            **data: Entity data
            
        Returns:
            Tuple of (model, action) where action is "insert" or "update"
        """
        try:
            entity = self.entity_class(**data)
            return await entity.merge()
        except Exception as e:
            self.logger.error(f"Error merging {self.entity_class.__name__}: {str(e)}")
            raise
    
    def get_schema_manager(self):
        """
        Get the schema manager for the entity class.
        
        Returns:
            The schema manager
        """
        instance = self.entity_class()
        return instance.schema_manager
    
    def get_filter_manager(self):
        """
        Get the filter manager for the entity class.
        
        Returns:
            The filter manager
        """
        instance = self.entity_class()
        return instance.filter_manager


class UnoEntityServiceFactory:
    """
    Factory for creating entity services.
    
    This factory creates services for UnoObj classes, providing
    a consistent way to access them through dependency injection.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the factory.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._services: Dict[Type[UnoObj], UnoEntityService] = {}
    
    def create_service(self, entity_class: Type[T]) -> UnoEntityService[T]:
        """
        Create a service for an entity class.
        
        Args:
            entity_class: UnoObj class to create a service for
            
        Returns:
            An entity service for the class
        """
        if entity_class not in self._services:
            self.logger.debug(f"Creating service for {entity_class.__name__}")
            self._services[entity_class] = UnoEntityService(
                entity_class, 
                self.logger.getChild(entity_class.__name__)
            )
        
        return cast(UnoEntityService[T], self._services[entity_class])