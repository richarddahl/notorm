"""
Base service implementations for the Uno framework.

This module provides abstract base classes that implement the service protocols,
serving as the foundation for concrete service implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from uno.core.errors.base import UnoError
from uno.core.errors.result import Result, Success, Failure
from uno.core.events import EventBus
from uno.infrastructure.repositories import (
    Repository,
    UnitOfWork,
    RepositoryProtocol
)
from uno.infrastructure.services.protocols import (
    ServiceProtocol,
    CrudServiceProtocol,
    AggregateCrudServiceProtocol,
    QueryServiceProtocol,
    ApplicationServiceProtocol,
    DomainEventPublisherProtocol
)

# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
InputT = TypeVar("InputT")  # Input type
OutputT = TypeVar("OutputT")  # Output type
ParamsT = TypeVar("ParamsT")  # Parameters type


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


class Service(Generic[InputT, OutputT], ServiceProtocol[InputT, OutputT], ABC):
    """
    Abstract base class for services.
    
    This class implements the ServiceProtocol and provides a foundation
    for all service implementations.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the service.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the service operation.
        
        This method provides error handling and validation for the service
        operation, delegating to _execute_internal for the actual implementation.
        
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
            
            # Execute the operation
            return await self._execute_internal(input_data)
            
        except UnoError as e:
            # Domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))
            
        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(
                f"Unexpected error in {self.__class__.__name__}: {str(e)}",
                exc_info=True
            )
            return Failure(str(e))
    
    async def validate(self, input_data: InputT) -> Optional[Result[OutputT]]:
        """
        Validate the input data before execution.
        
        This method can be overridden by derived classes to implement
        input validation logic. Return None if validation passes,
        or a Failure result if validation fails.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            None if validation passes, or a Failure result if validation fails
        """
        return None
    
    @abstractmethod
    async def _execute_internal(self, input_data: InputT) -> Result[OutputT]:
        """
        Internal implementation of the service operation.
        
        This method should be implemented by derived classes to provide
        the specific service operation logic.
        
        Args:
            input_data: The input data for the operation
            
        Returns:
            A Result containing either the operation result or error information
        """
        pass


class TransactionalService(Service[InputT, OutputT], ABC):
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
                
        except UnoError as e:
            # Domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))
            
        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(
                f"Unexpected error in {self.__class__.__name__}: {str(e)}",
                exc_info=True
            )
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
                limit_offset=(limit, offset) if limit is not None else None
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


class AggregateCrudService(CrudService[T, ID], AggregateCrudServiceProtocol[T, ID]):
    """
    Base implementation for aggregate CRUD services.
    
    This class extends the standard CRUD service with operations specific
    to aggregate roots, such as version-based optimistic concurrency control.
    """
    
    def __init__(
        self,
        aggregate_type: Type[T],
        repository: RepositoryProtocol[T, ID],
        unit_of_work: UnitOfWork,
        event_publisher: Optional[DomainEventPublisherProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the aggregate CRUD service.
        
        Args:
            aggregate_type: The type of aggregate this service manages
            repository: Repository for data access
            unit_of_work: Unit of work for transaction management
            event_publisher: Optional event publisher for domain events
            logger: Optional logger for diagnostic information
        """
        super().__init__(aggregate_type, repository, event_publisher, logger)
        self.unit_of_work = unit_of_work
    
    async def create(self, data: Dict[str, Any]) -> Result[T]:
        """
        Create a new aggregate.
        
        This method overrides the base create method to ensure that
        the operation is performed within a transaction.
        
        Args:
            data: Aggregate data
            
        Returns:
            Result containing the created aggregate
        """
        try:
            async with self.unit_of_work:
                # Create aggregate instance
                aggregate = self._create_entity(data)
                
                # Apply changes to ensure invariants and increment version
                if hasattr(aggregate, "apply_changes") and callable(getattr(aggregate, "apply_changes")):
                    getattr(aggregate, "apply_changes")()
                
                # Save to repository
                saved_aggregate = await self.repository.add(aggregate)
                
                # Collect events if available
                events = []
                if hasattr(saved_aggregate, "clear_events") and callable(getattr(saved_aggregate, "clear_events")):
                    events = getattr(saved_aggregate, "clear_events")()
                
                # Commit transaction
                await self.unit_of_work.commit()
                
                # Publish events after successful commit
                if self.event_publisher and events:
                    self.event_publisher.publish_events(events)
                
                return Success(saved_aggregate)
        except Exception as e:
            self.logger.error(f"Error creating aggregate: {str(e)}")
            return Failure(str(e))
    
    async def update(self, id: ID, data: Dict[str, Any]) -> Result[T]:
        """
        Update an existing aggregate.
        
        This method overrides the base update method to ensure that
        the operation is performed within a transaction.
        
        Args:
            id: Aggregate ID
            data: Updated aggregate data
            
        Returns:
            Result containing the updated aggregate
        """
        try:
            async with self.unit_of_work:
                # Get existing aggregate
                aggregate = await self.repository.get(id)
                if not aggregate:
                    return Failure(f"Aggregate with ID {id} not found")
                
                # Update fields
                updated_aggregate = self._update_entity(aggregate, data)
                
                # Apply changes to ensure invariants and increment version
                if hasattr(updated_aggregate, "apply_changes") and callable(getattr(updated_aggregate, "apply_changes")):
                    getattr(updated_aggregate, "apply_changes")()
                
                # Save to repository
                saved_aggregate = await self.repository.update(updated_aggregate)
                
                # Collect events if available
                events = []
                if hasattr(saved_aggregate, "clear_events") and callable(getattr(saved_aggregate, "clear_events")):
                    events = getattr(saved_aggregate, "clear_events")()
                
                # Commit transaction
                await self.unit_of_work.commit()
                
                # Publish events after successful commit
                if self.event_publisher and events:
                    self.event_publisher.publish_events(events)
                
                return Success(saved_aggregate)
        except Exception as e:
            self.logger.error(f"Error updating aggregate: {str(e)}")
            return Failure(str(e))
    
    async def update_with_version(
        self, id: ID, version: int, data: Dict[str, Any]
    ) -> Result[T]:
        """
        Update an aggregate with optimistic concurrency control.
        
        Args:
            id: Aggregate ID
            version: Expected current version for concurrency control
            data: Updated aggregate data
            
        Returns:
            Result containing the updated aggregate
        """
        try:
            async with self.unit_of_work:
                # Get existing aggregate
                aggregate = await self.repository.get(id)
                if not aggregate:
                    return Failure(f"Aggregate with ID {id} not found")
                
                # Check version for optimistic concurrency
                if hasattr(aggregate, "version") and getattr(aggregate, "version") != version:
                    return Failure(
                        f"Concurrency conflict: expected version {version}, found {getattr(aggregate, 'version')}"
                    )
                
                # Update fields
                updated_aggregate = self._update_entity(aggregate, data)
                
                # Apply changes to ensure invariants and increment version
                if hasattr(updated_aggregate, "apply_changes") and callable(getattr(updated_aggregate, "apply_changes")):
                    getattr(updated_aggregate, "apply_changes")()
                
                # Save to repository
                saved_aggregate = await self.repository.update(updated_aggregate)
                
                # Collect events if available
                events = []
                if hasattr(saved_aggregate, "clear_events") and callable(getattr(saved_aggregate, "clear_events")):
                    events = getattr(saved_aggregate, "clear_events")()
                
                # Commit transaction
                await self.unit_of_work.commit()
                
                # Publish events after successful commit
                if self.event_publisher and events:
                    self.event_publisher.publish_events(events)
                
                return Success(saved_aggregate)
        except Exception as e:
            self.logger.error(f"Error updating aggregate with version: {str(e)}")
            return Failure(str(e))
    
    async def delete(self, id: ID) -> Result[bool]:
        """
        Delete an aggregate.
        
        This method overrides the base delete method to ensure that
        the operation is performed within a transaction.
        
        Args:
            id: Aggregate ID
            
        Returns:
            Result indicating success or failure
        """
        try:
            async with self.unit_of_work:
                # Get existing aggregate
                aggregate = await self.repository.get(id)
                if not aggregate:
                    return Failure(f"Aggregate with ID {id} not found")
                
                # Generate deletion event before removing
                from uno.core.events import UnoEvent
                
                event = UnoEvent(
                    event_type=f"{self.entity_type.__name__.lower()}_deleted",
                    aggregate_id=str(getattr(aggregate, "id")),
                    aggregate_type=self.entity_type.__name__,
                )
                
                # Remove from repository
                await self.repository.delete(aggregate)
                
                # Commit transaction
                await self.unit_of_work.commit()
                
                # Publish deletion event
                if self.event_publisher:
                    self.event_publisher.publish_event(event)
                
                return Success(True)
        except Exception as e:
            self.logger.error(f"Error deleting aggregate: {str(e)}")
            return Failure(str(e))
    
    async def delete_with_version(self, id: ID, version: int) -> Result[bool]:
        """
        Delete an aggregate with optimistic concurrency control.
        
        Args:
            id: Aggregate ID
            version: Expected current version for concurrency control
            
        Returns:
            Result indicating success or failure
        """
        try:
            async with self.unit_of_work:
                # Get existing aggregate
                aggregate = await self.repository.get(id)
                if not aggregate:
                    return Failure(f"Aggregate with ID {id} not found")
                
                # Check version for optimistic concurrency
                if hasattr(aggregate, "version") and getattr(aggregate, "version") != version:
                    return Failure(
                        f"Concurrency conflict: expected version {version}, found {getattr(aggregate, 'version')}"
                    )
                
                # Generate deletion event before removing
                from uno.core.events import UnoEvent
                
                event = UnoEvent(
                    event_type=f"{self.entity_type.__name__.lower()}_deleted",
                    aggregate_id=str(getattr(aggregate, "id")),
                    aggregate_type=self.entity_type.__name__,
                )
                
                # Remove from repository
                await self.repository.delete(aggregate)
                
                # Commit transaction
                await self.unit_of_work.commit()
                
                # Publish deletion event
                if self.event_publisher:
                    self.event_publisher.publish_event(event)
                
                return Success(True)
        except Exception as e:
            self.logger.error(f"Error deleting aggregate with version: {str(e)}")
            return Failure(str(e))


class QueryService(Generic[ParamsT, OutputT], QueryServiceProtocol[ParamsT, OutputT]):
    """
    Base implementation for query services.
    
    Query services handle read-only operations, retrieving and transforming data
    without modifying domain state.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the query service.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute_query(self, params: ParamsT) -> Result[OutputT]:
        """
        Execute a query operation.
        
        Args:
            params: Query parameters
            
        Returns:
            Result containing the query results
        """
        try:
            # Execute the query
            return await self._execute_query_internal(params)
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            return Failure(str(e))
    
    @abstractmethod
    async def _execute_query_internal(self, params: ParamsT) -> Result[OutputT]:
        """
        Internal implementation of the query operation.
        
        This method should be implemented by derived classes to provide
        the specific query logic.
        
        Args:
            params: Query parameters
            
        Returns:
            Result containing the query results
        """
        pass
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count entities matching filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Result containing the count
        """
        try:
            # Execute the count query
            return await self._count_internal(filters)
        except Exception as e:
            self.logger.error(f"Error counting entities: {str(e)}")
            return Failure(str(e))
    
    @abstractmethod
    async def _count_internal(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Internal implementation of the count operation.
        
        This method should be implemented by derived classes to provide
        the specific count logic.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Result containing the count
        """
        pass


class RepositoryQueryService(QueryService[ParamsT, List[T]], Generic[T, ID, ParamsT]):
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
        limit_offset = self._get_limit_offset(params)
        
        # Execute the query
        entities = await self.repository.list(
            filters=filters,
            order_by=order_by,
            limit_offset=limit_offset
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
        count = await self.repository.count(filters)
        return Success(count)
    
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
    
    def _get_limit_offset(self, params: ParamsT) -> Optional[tuple[int, int]]:
        """
        Get limit and offset from params.
        
        This method can be overridden by derived classes to customize
        the extraction of limit and offset from query parameters.
        
        Args:
            params: Query parameters
            
        Returns:
            Tuple of (limit, offset) or None
        """
        limit = None
        offset = 0
        
        # Try to get limit and offset from params
        if isinstance(params, dict):
            if "limit" in params:
                limit = params["limit"]
            if "offset" in params:
                offset = params["offset"]
        elif hasattr(params, "limit") and hasattr(params, "offset"):
            limit = getattr(params, "limit")
            offset = getattr(params, "offset")
        
        # Return tuple if limit is provided, otherwise None
        return (limit, offset) if limit is not None else None


class ApplicationService(Service[InputT, OutputT], ApplicationServiceProtocol[InputT, OutputT]):
    """
    Base implementation for application services.
    
    Application services coordinate complex operations that may involve
    multiple domain services, external systems, or infrastructure components.
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: Optional[DomainEventPublisherProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the application service.
        
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
        Execute the application service operation.
        
        This method provides error handling, validation, and transactional
        boundaries for the application service operation.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            Result containing the operation result
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
                
        except UnoError as e:
            # Domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))
            
        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(
                f"Unexpected error in {self.__class__.__name__}: {str(e)}",
                exc_info=True
            )
            return Failure(str(e))