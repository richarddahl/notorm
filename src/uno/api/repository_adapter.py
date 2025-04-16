# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Repository adapter for integrating domain repositories with API endpoints.

This module provides adapter classes that bridge domain repositories with the API endpoint system,
allowing endpoints to work with domain entities and repositories in a consistent way.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union, Protocol
from dataclasses import is_dataclass

from pydantic import BaseModel

from uno.core.protocols import Repository, FilterManagerProtocol, Entity
from uno.core.errors import ValidationContext
from uno.core.errors.result import Result
from uno.queries.filter_manager import UnoFilterManager, get_filter_manager

# Type variables
T = TypeVar('T')
EntityT = TypeVar('EntityT', bound=Entity)
SchemaT = TypeVar('SchemaT', bound=BaseModel)


class RepositoryAdapter(Generic[EntityT, SchemaT]):
    """
    Adapter to bridge domain repositories with API endpoints.
    
    This class wraps a domain repository, providing methods with signatures
    compatible with the API endpoint system while using domain-driven practices underneath.
    
    Type Parameters:
        EntityT: The domain entity type
        SchemaT: The schema model type for API endpoints
    """
    
    def __init__(
        self,
        repository: Repository,
        entity_type: Type[EntityT],
        schema_manager: Any,
        filter_manager: Optional[FilterManagerProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository adapter.
        
        Args:
            repository: The domain repository to adapt
            entity_type: The type of entity this repository works with
            schema_manager: The schema manager for converting between entities and DTOs
            filter_manager: Optional filter manager for query filtering
            logger: Optional logger for diagnostic output
        """
        self.repository = repository
        self.entity_type = entity_type
        self.schema_manager = schema_manager
        self.filter_manager = filter_manager or get_filter_manager()
        self.logger = logger or logging.getLogger(__name__)
        
        # Derive display names from entity type for OpenAPI docs
        entity_name = getattr(entity_type, '__name__', 'Entity')
        self.display_name = getattr(entity_type, 'display_name', entity_name)
        self.display_name_plural = getattr(
            entity_type, 'display_name_plural', f"{self.display_name}s"
        )
        
        # Set these as class vars for compatibility with the endpoint system
        self.__class__.display_name = self.display_name
        self.__class__.display_name_plural = self.display_name_plural
        
    async def get(self, id: str, **kwargs) -> Optional[EntityT]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            **kwargs: Additional parameters to pass to the repository
            
        Returns:
            The entity if found, None otherwise
        """
        try:
            # Use the repository to get the entity
            result = await self.repository.get_by_id(id)
            return result
        except Exception as e:
            self.logger.error(f"Error getting entity by ID {id}: {str(e)}")
            return None
    
    async def filter(
        self,
        filters: Optional[Any] = None,
        page: int = 1,
        page_size: int = 50,
        **kwargs
    ) -> Union[List[EntityT], Dict[str, Any]]:
        """
        Filter entities based on criteria.
        
        Args:
            filters: Filter criteria
            page: Page number (1-indexed)
            page_size: Number of items per page
            **kwargs: Additional parameters to pass to the repository
            
        Returns:
            List of entities or paginated response dict with items and metadata
        """
        try:
            # Convert filter parameters if needed
            options = {
                "pagination": {
                    "limit": page_size,
                    "offset": (page - 1) * page_size
                }
            }
            
            # Add sorting if provided in kwargs
            if "order_by" in kwargs:
                field = kwargs["order_by"]
                direction = kwargs.get("order_direction", "asc")
                options["sorting"] = [{"field": field, "direction": direction}]
            
            # Call the repository with filters and options
            results = await self.repository.list(filters=filters, options=options)
            
            # Check if we need to return paginated results
            if kwargs.get("paginated", True):
                # Create paginated response
                return {
                    "items": results,
                    "page": page,
                    "page_size": page_size,
                    "total": len(results) if len(results) < page_size else None  # None if we don't know the total
                }
            
            # Return simple list if pagination not requested
            return results
        except Exception as e:
            self.logger.error(f"Error filtering entities: {str(e)}")
            return []
    
    async def save(self, data: Union[Dict[str, Any], BaseModel], importing: bool = False) -> Optional[EntityT]:
        """
        Save an entity (create or update).
        
        Args:
            data: The data to save, either as a dict or Pydantic model
            importing: Whether this is an import operation
            
        Returns:
            The saved entity if successful, None otherwise
        """
        try:
            # Convert to dict if it's a Pydantic model
            if isinstance(data, BaseModel):
                data_dict = data.model_dump()
            else:
                data_dict = data
            
            # Check if this is an update (has ID) or create
            entity_id = data_dict.get('id')
            
            if entity_id:
                # Get existing entity
                existing = await self.repository.get_by_id(entity_id)
                if not existing:
                    self.logger.warning(f"Entity with ID {entity_id} not found for update")
                    return None
                
                # Create entity from data
                entity = self._create_entity_from_dict(data_dict)
                
                # Update entity
                updated = await self.repository.update(entity)
                return updated
            else:
                # Create entity from data
                entity = self._create_entity_from_dict(data_dict)
                
                # Add to repository
                created = await self.repository.add(entity)
                return created
        except Exception as e:
            self.logger.error(f"Error saving entity: {str(e)}")
            return None
    
    async def delete_(self, id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete via repository
            result = await self.repository.delete(id)
            return result
        except Exception as e:
            self.logger.error(f"Error deleting entity with ID {id}: {str(e)}")
            return False
    
    def _create_entity_from_dict(self, data: Dict[str, Any]) -> EntityT:
        """
        Create an entity instance from a dictionary.
        
        Args:
            data: The data dictionary
            
        Returns:
            An entity instance
            
        Raises:
            ValueError: If the entity cannot be created
        """
        # Check if schema manager has a method for this
        if hasattr(self.schema_manager, 'create_entity'):
            return self.schema_manager.create_entity(self.entity_type, data)
        
        # Handle dataclass entities
        if is_dataclass(self.entity_type):
            return self.entity_type(**data)
        
        # Handle other entity types
        if hasattr(self.entity_type, 'from_dict'):
            return self.entity_type.from_dict(data)
        
        raise ValueError(f"Unable to create entity of type {self.entity_type.__name__}")
    
    def create_filter_params(self) -> Optional[Type[BaseModel]]:
        """
        Create filter parameters model for API endpoints.
        
        Returns:
            A Pydantic model class for filter parameters, or None if not available
        """
        if hasattr(self.filter_manager, 'create_filter_params'):
            try:
                return self.filter_manager.create_filter_params(self.entity_type)
            except Exception as e:
                self.logger.error(f"Error creating filter parameters: {str(e)}")
        return None
    
    def validate_filter_params(self, filter_params: Optional[BaseModel]) -> List[Any]:
        """
        Validate filter parameters.
        
        Args:
            filter_params: The filter parameters to validate
            
        Returns:
            A list of validated filter tuples
        """
        if filter_params is None:
            return []
            
        if hasattr(self.filter_manager, 'validate_filter_params'):
            try:
                return self.filter_manager.validate_filter_params(
                    filter_params, self.entity_type
                )
            except Exception as e:
                self.logger.error(f"Error validating filter parameters: {str(e)}")
        
        return []


class ReadOnlyRepositoryAdapter(RepositoryAdapter[EntityT, SchemaT]):
    """
    A read-only adapter for repositories that don't support write operations.
    
    This adapter overrides write methods to return appropriate errors.
    """
    
    async def save(self, data: Union[Dict[str, Any], BaseModel], importing: bool = False) -> None:
        """
        Attempt to save entity - always fails for read-only repository.
        
        Args:
            data: The data to save
            importing: Whether this is an import operation
            
        Returns:
            None, as the operation is not supported
        """
        self.logger.warning("Attempted to save to a read-only repository")
        return None
    
    async def delete_(self, id: str) -> bool:
        """
        Attempt to delete entity - always fails for read-only repository.
        
        Args:
            id: The entity ID
            
        Returns:
            False, as the operation is not supported
        """
        self.logger.warning(f"Attempted to delete entity {id} from a read-only repository")
        return False


class BatchRepositoryAdapter(RepositoryAdapter[EntityT, SchemaT]):
    """
    Adapter for repositories that support batch operations.
    
    This adapter adds methods for batch create, update, and delete operations.
    """
    
    async def batch_save(self, items: List[Union[Dict[str, Any], BaseModel]]) -> List[EntityT]:
        """
        Save multiple entities in a batch operation.
        
        Args:
            items: List of items to save
            
        Returns:
            List of saved entities
        """
        if not hasattr(self.repository, 'batch_add') or not hasattr(self.repository, 'batch_update'):
            self.logger.warning("Repository does not support batch operations")
            # Fall back to individual save operations
            results = []
            for item in items:
                result = await self.save(item)
                if result:
                    results.append(result)
            return results
        
        try:
            # Separate updates and creates
            creates = []
            updates = []
            
            for item in items:
                # Convert to dict if it's a Pydantic model
                if isinstance(item, BaseModel):
                    data = item.model_dump()
                else:
                    data = item
                
                # Check if this is an update (has ID) or create
                if 'id' in data and data['id']:
                    # Create entity for update
                    entity = self._create_entity_from_dict(data)
                    updates.append(entity)
                else:
                    # Create entity for create
                    entity = self._create_entity_from_dict(data)
                    creates.append(entity)
            
            # Process creates and updates
            created = await self.repository.batch_add(creates) if creates else []
            updated = await self.repository.batch_update(updates) if updates else []
            
            # Combine results
            return created + updated
            
        except Exception as e:
            self.logger.error(f"Error in batch save operation: {str(e)}")
            return []
    
    async def batch_delete(self, ids: List[str]) -> List[str]:
        """
        Delete multiple entities in a batch operation.
        
        Args:
            ids: List of entity IDs to delete
            
        Returns:
            List of successfully deleted IDs
        """
        if not hasattr(self.repository, 'batch_delete'):
            self.logger.warning("Repository does not support batch delete")
            # Fall back to individual delete operations
            results = []
            for id in ids:
                if await self.delete_(id):
                    results.append(id)
            return results
        
        try:
            # Use batch delete if available
            return await self.repository.batch_delete(ids)
        except Exception as e:
            self.logger.error(f"Error in batch delete operation: {str(e)}")
            return []