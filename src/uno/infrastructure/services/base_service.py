"""
Extended service implementations for the Uno framework.

This module provides concrete service implementations that build upon the
core base service classes.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast

from uno.core.errors.result import Result, Success, Failure
from uno.core.events import EventBus, DomainEventProtocol
from uno.core.base.service import (
    BaseService,
    BaseQueryService,
    ServiceProtocol,
    CrudServiceProtocol,
    QueryServiceProtocol
)
from uno.core.base.repository import RepositoryProtocol
from uno.infrastructure.repositories.unit_of_work import UnitOfWork


# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
InputT = TypeVar("InputT")  # Input type
OutputT = TypeVar("OutputT")  # Output type
ParamsT = TypeVar("ParamsT")  # Parameters type


class DomainEventPublisherProtocol:
    """
    Protocol for publishing domain events.
    
    This protocol defines the operations for publishing domain events.
    """
    
    def publish_event(self, event: Any) -> None:
        """
        Publish a domain event.
        
        Args:
            event: The domain event to publish
        """
        ...
    
    def publish_events(self, events: List[Any]) -> None:
        """
        Publish multiple domain events.
        
        Args:
            events: The domain events to publish
        """
        ...


class EventPublisher(DomainEventPublisherProtocol):
    """
    Implementation of the domain event publisher.
    
    This class is responsible for collecting and publishing domain events
    to interested subscribers using the event bus.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize the event publisher.
        
        Args:
            event_bus: The event bus for publishing events
        """
        self.event_bus = event_bus
    
    def publish_event(self, event: Any) -> None:
        """
        Publish a domain event.
        
        Args:
            event: The domain event to publish
        """
        self.event_bus.publish(event)
    
    def publish_events(self, events: List[Any]) -> None:
        """
        Publish multiple domain events.
        
        Args:
            events: The domain events to publish
        """
        for event in events:
            self.publish_event(event)


class TransactionalService(BaseService[InputT, OutputT], ABC):
    """
    Abstract base class for transactional services.
    
    This class extends the base Service with transactional capabilities,
    ensuring that operations either complete successfully or are rolled back.
    """
    
    def __init__(
        self, 
        unit_of_work: UnitOfWork,
        event_publisher: Optional[DomainEventPublisherProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the transactional service.
        
        Args:
            unit_of_work: Unit of work for transaction management
            event_publisher: Optional event publisher for domain events
            logger: Optional logger for diagnostic information
        """
        super().__init__(logger)
        self.unit_of_work = unit_of_work
        self.event_publisher = event_publisher
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the service operation within a transaction.
        
        This method extends the base execute method with transactional
        boundaries, ensuring that operations either succeed completely
        or are rolled back.
        
        Args:
            input_data: The input data for the operation
            
        Returns:
            A Result containing either the operation result or error information
        """
        try:
            # Validate input data
            validation_result = await self.validate(input_data)
            if validation_result is not None:
                return validation_result
            
            # Execute the operation within a transaction
            async with self.unit_of_work:
                # Execute the operation
                result = await self._execute_internal(input_data)
                
                # If successful, commit and publish events
                if result.is_success:
                    # Collect events from all repositories
                    events = self.unit_of_work.collect_events()
                    
                    # Commit the transaction
                    await self.unit_of_work.commit()
                    
                    # Publish events after successful commit
                    if self.event_publisher and events:
                        self.event_publisher.publish_events(events)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error in transactional service: {str(e)}", exc_info=True)
            return Failure(str(e))


class CrudService(Generic[T, ID], CrudServiceProtocol[T, ID]):
    """
    Base implementation for CRUD services.
    
    This class provides standard CRUD operations for domain entities,
    using a repository for data access.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        repository: RepositoryProtocol[T, ID],
        event_publisher: Optional[DomainEventPublisherProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the CRUD service.
        
        Args:
            entity_type: The type of entity this service manages
            repository: Repository for data access
            event_publisher: Optional event publisher for domain events
            logger: Optional logger for diagnostic information
        """
        self.entity_type = entity_type
        self.repository = repository
        self.event_publisher = event_publisher
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get(self, id: ID) -> Result[Optional[T]]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            Result containing the entity or None if not found
        """
        try:
            entity = await self.repository.get(id)
            return Success(entity)
        except Exception as e:
            self.logger.error(f"Error retrieving entity by ID: {str(e)}")
            return Failure(str(e))
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Result[List[T]]:
        """
        List entities with optional filtering, ordering, and pagination.
        
        Args:
            filters: Optional filters to apply
            order_by: Optional ordering
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            Result containing the list of matching entities
        """
        try:
            entities = await self.repository.list(
                filters=filters,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
            return Success(entities)
        except Exception as e:
            self.logger.error(f"Error listing entities: {str(e)}")
            return Failure(str(e))
    
    async def create(self, data: Dict[str, Any]) -> Result[T]:
        """
        Create a new entity.
        
        Args:
            data: Entity data
            
        Returns:
            Result containing the created entity
        """
        try:
            # Create entity instance
            entity = self._create_entity(data)
            
            # Save to repository
            saved_entity = await self.repository.add(entity)
            
            # Publish events if available
            if self.event_publisher and hasattr(saved_entity, "get_events"):
                events = getattr(saved_entity, "get_events")()
                if events:
                    self.event_publisher.publish_events(events)
            
            return Success(saved_entity)
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            return Failure(str(e))
    
    async def update(self, id: ID, data: Dict[str, Any]) -> Result[T]:
        """
        Update an existing entity.
        
        Args:
            id: Entity ID
            data: Updated entity data
            
        Returns:
            Result containing the updated entity
        """
        try:
            # Get existing entity
            entity = await self.repository.get(id)
            if not entity:
                return Failure(f"Entity with ID {id} not found")
            
            # Update fields
            updated_entity = self._update_entity(entity, data)
            
            # Save to repository
            saved_entity = await self.repository.update(updated_entity)
            
            # Publish events if available
            if self.event_publisher and hasattr(saved_entity, "get_events"):
                events = getattr(saved_entity, "get_events")()
                if events:
                    self.event_publisher.publish_events(events)
            
            return Success(saved_entity)
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            return Failure(str(e))
    
    async def delete(self, id: ID) -> Result[bool]:
        """
        Delete an entity.
        
        Args:
            id: Entity ID
            
        Returns:
            Result indicating success or failure
        """
        try:
            # Get existing entity
            entity = await self.repository.get(id)
            if not entity:
                return Failure(f"Entity with ID {id} not found")
            
            # Delete from repository
            await self.repository.delete(entity)
            
            # Publish deletion event if applicable
            if self.event_publisher and hasattr(entity, "id"):
                # Create a generic deletion event
                from uno.core.events import UnoEvent
                
                event = UnoEvent(
                    event_type=f"{self.entity_type.__name__.lower()}_deleted",
                    aggregate_id=str(getattr(entity, "id")),
                    aggregate_type=self.entity_type.__name__,
                )
                self.event_publisher.publish_event(event)
            
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error deleting entity: {str(e)}")
            return Failure(str(e))
    
    def _create_entity(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity instance from data.
        
        This method can be overridden by derived classes to customize
        entity creation logic.
        
        Args:
            data: Entity data
            
        Returns:
            New entity instance
        """
        return self.entity_type(**data)
    
    def _update_entity(self, entity: T, data: Dict[str, Any]) -> T:
        """
        Update an entity with new data.
        
        This method can be overridden by derived classes to customize
        entity update logic.
        
        Args:
            entity: Existing entity
            data: Updated entity data
            
        Returns:
            Updated entity
        """
        # Update fields
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        # Update timestamp if applicable
        if hasattr(entity, "update") and callable(getattr(entity, "update")):
            getattr(entity, "update")()
        
        return entity


class RepositoryQueryService(BaseQueryService[ParamsT, List[T]], Generic[T, ID, ParamsT]):
    """
    Query service implementation using a repository.
    
    This class provides a query service implementation that uses a repository
    for data access, making it easy to implement query operations based on
    repository operations.
    """
    
    def __init__(
        self,
        repository: RepositoryProtocol[T, ID],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository query service.
        
        Args:
            repository: Repository for data access
            logger: Optional logger for diagnostic information
        """
        super().__init__(logger)
        self.repository = repository
    
    async def _execute_query_internal(self, params: ParamsT) -> Result[List[T]]:
        """
        Internal implementation of the query operation.
        
        This method converts the query parameters to repository filters
        and executes the query using the repository.
        
        Args:
            params: Query parameters
            
        Returns:
            Result containing the query results
        """
        # Convert params to filters
        filters = self._params_to_filters(params)
        
        # Get order_by, limit, and offset from params if available
        order_by = self._get_order_by(params)
        limit = self._get_limit(params)
        offset = self._get_offset(params)
        
        # Execute the query
        entities = await self.repository.list(
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        
        return Success(entities)
    
    async def _count_internal(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Internal implementation of the count operation.
        
        This method counts entities matching the filters using the repository.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Result containing the count
        """
        # Use count method if available
        if hasattr(self.repository, "count"):
            count = await self.repository.count(filters)
            return Success(count)
        
        # Fall back to fetching and counting all entities
        entities = await self.repository.list(filters=filters)
        return Success(len(entities))
    
    def _params_to_filters(self, params: ParamsT) -> Dict[str, Any]:
        """
        Convert query parameters to repository filters.
        
        This method can be overridden by derived classes to customize
        the conversion of query parameters to repository filters.
        
        Args:
            params: Query parameters
            
        Returns:
            Repository filters
        """
        # By default, try to convert params to a dictionary
        if isinstance(params, dict):
            return cast(Dict[str, Any], params)
        elif hasattr(params, "__dict__"):
            return params.__dict__
        else:
            return {}
    
    def _get_order_by(self, params: ParamsT) -> Optional[List[str]]:
        """
        Get order_by from params.
        
        This method can be overridden by derived classes to customize
        the extraction of order_by from query parameters.
        
        Args:
            params: Query parameters
            
        Returns:
            Order by fields or None
        """
        if isinstance(params, dict) and "order_by" in params:
            return params["order_by"]
        elif hasattr(params, "order_by"):
            return getattr(params, "order_by")
        else:
            return None
    
    def _get_limit(self, params: ParamsT) -> Optional[int]:
        """
        Get limit from params.
        
        This method can be overridden by derived classes to customize
        the extraction of limit from query parameters.
        
        Args:
            params: Query parameters
            
        Returns:
            Limit or None
        """
        if isinstance(params, dict) and "limit" in params:
            return params["limit"]
        elif hasattr(params, "limit"):
            return getattr(params, "limit")
        else:
            return None
    
    def _get_offset(self, params: ParamsT) -> Optional[int]:
        """
        Get offset from params.
        
        This method can be overridden by derived classes to customize
        the extraction of offset from query parameters.
        
        Args:
            params: Query parameters
            
        Returns:
            Offset or 0
        """
        if isinstance(params, dict) and "offset" in params:
            return params["offset"]
        elif hasattr(params, "offset"):
            return getattr(params, "offset")
        else:
            return 0


# No backward compatibility needed