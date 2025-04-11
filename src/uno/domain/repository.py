"""
Repository pattern implementation for the Uno framework.

This module provides a repository pattern implementation for the domain layer,
abstracting the data access and persistence logic from the domain models.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type

from uno.domain.core import Entity, AggregateRoot


T = TypeVar('T', bound=Entity)


class Repository(Generic[T], ABC):
    """
    Abstract base class for repositories.
    
    Repositories provide data access for domain entities and aggregates, hiding the
    complexity of data retrieval and persistence behind a collection-like interface.
    """
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        List entities with optional filtering, ordering, and pagination.
        
        Args:
            filters: Filters to apply, typically field=value pairs
            order_by: Fields to order by, with optional direction (e.g., ['name', '-created_at'])
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the criteria
        """
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        Add a new entity to the repository.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity, typically with generated IDs and timestamps
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity in the repository.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        pass
    
    @abstractmethod
    async def remove(self, entity: T) -> None:
        """
        Remove an entity from the repository.
        
        Args:
            entity: The entity to remove
        """
        pass
    
    @abstractmethod
    async def remove_by_id(self, id: str) -> bool:
        """
        Remove an entity by ID.
        
        Args:
            id: The ID of the entity to remove
            
        Returns:
            True if the entity was removed, False if it wasn't found
        """
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: The ID to check
            
        Returns:
            True if an entity with the given ID exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching the given filters.
        
        Args:
            filters: Filters to apply
            
        Returns:
            The number of entities matching the criteria
        """
        pass


class UnoDBRepository(Repository[T]):
    """
    Repository implementation using UnoDB.
    
    This implementation uses the UnoDB database layer to persist and retrieve
    domain entities.
    """
    
    def __init__(self, entity_type: Type[T], db_factory=None):
        """
        Initialize the repository.
        
        Args:
            entity_type: The type of entity this repository manages
            db_factory: The database factory to use
        """
        self.entity_type = entity_type
        self.db_factory = db_factory
        
        # Lazy-loaded db
        self._db = None
    
    @property
    def db(self):
        """Get the database instance, creating it if necessary."""
        if self._db is None:
            from uno.database.db import UnoDBFactory
            from uno.model import UnoModel
            # Convert domain entity to UnoModel wrapper if needed
            model_type = getattr(self.entity_type, '__uno_model__', None)
            model_instance = model_type() if model_type else UnoModel()
            self._db = self.db_factory or UnoDBFactory(model_instance)
        return self._db
    
    async def get(self, id: str) -> Optional[T]:
        """Get an entity by ID."""
        try:
            result = await self.db.get(id=id)
            if result:
                return self._convert_to_entity(result)
            return None
        except Exception as e:
            from uno.database.db import NotFoundException
            if isinstance(e, NotFoundException):
                return None
            raise
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """List entities with filtering, ordering, and pagination."""
        from uno.database.db import FilterParam
        
        # Convert filters to FilterParam objects if provided
        filter_params = None
        if filters:
            filter_params = []
            for key, value in filters.items():
                if isinstance(value, dict) and 'lookup' in value and 'val' in value:
                    filter_params.append(FilterParam(
                        label=key,
                        lookup=value['lookup'],
                        val=value['val']
                    ))
                else:
                    filter_params.append(FilterParam(
                        label=key,
                        lookup='eq',
                        val=value
                    ))
            
            # Add ordering parameters if provided
            if order_by:
                for field in order_by:
                    if field.startswith('-'):
                        filter_params.append(FilterParam(
                            label='order_by',
                            lookup='desc',
                            val=field[1:]
                        ))
                    else:
                        filter_params.append(FilterParam(
                            label='order_by',
                            lookup='asc',
                            val=field
                        ))
                        
            # Add pagination parameters if provided
            if limit is not None:
                filter_params.append(FilterParam(
                    label='limit',
                    lookup='eq',
                    val=limit
                ))
                
            if offset is not None:
                filter_params.append(FilterParam(
                    label='offset',
                    lookup='eq',
                    val=offset
                ))
        
        try:
            results = await self.db.filter(filter_params)
            return [self._convert_to_entity(result) for result in results]
        except Exception as e:
            # Log error and return empty list
            import logging
            logging.getLogger(__name__).error(f"Error in repository list: {e}")
            return []
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        try:
            model_data = self._convert_to_model_data(entity)
            result, created = await self.db.create(model_data)
            if not created:
                raise DomainException("Failed to create entity", "CREATE_FAILED")
            return self._convert_to_entity(result)
        except Exception as e:
            from uno.database.db import UniqueViolationError
            if isinstance(e, UniqueViolationError):
                raise DomainException("Entity already exists", "ALREADY_EXISTS")
            raise DomainException(f"Error creating entity: {str(e)}", "CREATE_ERROR")
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            # Ensure entity exists before updating
            if not await self.exists(entity.id):
                raise DomainException(f"Entity with ID {entity.id} not found", "NOT_FOUND")
            
            model_data = self._convert_to_model_data(entity)
            result = await self.db.update(model_data)
            return self._convert_to_entity(result)
        except Exception as e:
            from uno.database.db import UniqueViolationError, NotFoundException
            if isinstance(e, UniqueViolationError):
                raise DomainException("Unique constraint violation", "CONSTRAINT_VIOLATED")
            if isinstance(e, NotFoundException):
                raise DomainException(f"Entity with ID {entity.id} not found", "NOT_FOUND")
            raise DomainException(f"Error updating entity: {str(e)}", "UPDATE_ERROR")
    
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        await self.remove_by_id(entity.id)
    
    async def remove_by_id(self, id: str) -> bool:
        """Remove an entity by ID."""
        try:
            result = await self.db.delete(id=id)
            return result
        except Exception as e:
            # If entity doesn't exist, return False rather than raising an exception
            from uno.database.db import NotFoundException
            if isinstance(e, NotFoundException):
                return False
            raise DomainException(f"Error removing entity: {str(e)}", "DELETE_ERROR")
    
    async def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        try:
            # Try to get the entity - if it exists, return True
            result = await self.db.get(id=id)
            return result is not None
        except Exception as e:
            from uno.database.db import NotFoundException
            if isinstance(e, NotFoundException):
                return False
            # For other errors, propagate the exception
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        try:
            # Use list method with a limit of 0 to just get count
            entities = await self.list(filters=filters, limit=0)
            return len(entities)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in repository count: {e}")
            return 0
    
    def _convert_to_entity(self, data: Dict[str, Any]) -> T:
        """Convert database result to a domain entity."""
        if isinstance(data, dict):
            # Remove any database-specific fields not needed in domain entity
            # Convert to appropriate types where needed
            return self.entity_type(**data)
        else:
            # Handle case where data is already a model or mapping
            data_dict = data._mapping if hasattr(data, '_mapping') else data
            return self.entity_type(**dict(data_dict))
    
    def _convert_to_model_data(self, entity: T) -> Dict[str, Any]:
        """Convert domain entity to data for database model."""
        # Get model data excluding private fields
        model_data = entity.model_dump(exclude={"_events", "_child_entities"})
        
        # Process any special conversions needed for the database
        # For example, converting datetime objects to strings
        return model_data


from uno.domain.core import DomainException