"""
Domain services for the Read Model module.

This module defines the service interfaces and implementations for the Read Model module,
providing business logic for managing read models, projections, and caching.
"""

import logging
import time
import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from typing import (
    Dict, List, Optional, Any, Generic, Type, TypeVar, Union, Protocol, 
    cast, Callable, Awaitable, Set
)

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails
from uno.domain.core import Entity
from uno.domain.events import DomainEvent, EventBus, EventStore, EventHandler

from uno.read_model.entities import (
    ReadModel, ReadModelId, Projection, ProjectionId, 
    Query, QueryId, QueryResult, CacheEntry, 
    ProjectorConfiguration, CacheLevel, ProjectionType, QueryType
)
from uno.read_model.domain_repositories import (
    ReadModelRepositoryProtocol, ProjectionRepositoryProtocol,
    QueryRepositoryProtocol, CacheRepositoryProtocol,
    ProjectorConfigurationRepositoryProtocol
)

# Type variables
T = TypeVar('T', bound=ReadModel)
P = TypeVar('P', bound=Projection)
Q = TypeVar('Q', bound=Query)
EventT = TypeVar('EventT', bound=DomainEvent)

# Service Protocols

class ReadModelServiceProtocol(Protocol[T]):
    """Protocol defining operations for read model services."""
    
    async def get_by_id(self, id: ReadModelId) -> Result[Optional[T]]:
        """
        Get a read model by ID, with caching if available.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing the read model if found, None otherwise
        """
        ...
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[T]]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            Result containing list of matching read models
        """
        ...
    
    async def save(self, model: T) -> Result[T]:
        """
        Save a read model and update cache if available.
        
        Args:
            model: The read model to save
            
        Returns:
            Result containing the saved read model
        """
        ...
    
    async def delete(self, id: ReadModelId) -> Result[bool]:
        """
        Delete a read model and remove from cache if available.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the read model was deleted, False otherwise
        """
        ...


class ProjectionServiceProtocol(Protocol[P]):
    """Protocol defining operations for projection services."""
    
    async def get_by_id(self, id: ProjectionId) -> Result[Optional[P]]:
        """
        Get a projection by ID.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing the projection if found, None otherwise
        """
        ...
    
    async def get_by_event_type(self, event_type: str) -> Result[List[P]]:
        """
        Get projections by event type.
        
        Args:
            event_type: The event type
            
        Returns:
            Result containing list of projections for the event type
        """
        ...
    
    async def save(self, projection: P) -> Result[P]:
        """
        Save a projection.
        
        Args:
            projection: The projection to save
            
        Returns:
            Result containing the saved projection
        """
        ...
    
    async def delete(self, id: ProjectionId) -> Result[bool]:
        """
        Delete a projection.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing True if the projection was deleted, False otherwise
        """
        ...
    
    async def apply_event(self, event: DomainEvent, projection: P) -> Result[Optional[T]]:
        """
        Apply an event using a projection to create or update a read model.
        
        Args:
            event: The event to apply
            projection: The projection to use
            
        Returns:
            Result containing the created or updated read model, or None if no action was taken
        """
        ...


class CacheServiceProtocol(Protocol):
    """Protocol defining operations for cache services."""
    
    async def get(self, key: str, model_type: str) -> Result[Optional[Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing the cached value if found, None otherwise
        """
        ...
    
    async def set(
        self, key: str, value: Any, model_type: str, 
        read_model_id: Optional[ReadModelId] = None, 
        ttl_seconds: Optional[int] = None
    ) -> Result[bool]:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            model_type: The model type
            read_model_id: Optional read model ID associated with this cache entry
            ttl_seconds: Optional time-to-live in seconds
            
        Returns:
            Result containing True if the operation was successful
        """
        ...
    
    async def delete(self, key: str, model_type: str) -> Result[bool]:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing True if the cache entry was deleted, False otherwise
        """
        ...
    
    async def clear(self, model_type: Optional[str] = None) -> Result[bool]:
        """
        Clear cache entries.
        
        Args:
            model_type: Optional model type to clear entries for. If None, clears all entries.
            
        Returns:
            Result containing True if the operation was successful
        """
        ...


class QueryServiceProtocol(Protocol[Q, T]):
    """Protocol defining operations for query services."""
    
    async def execute(self, query: Q) -> Result[Union[T, List[T], None]]:
        """
        Execute a query to retrieve read models.
        
        Args:
            query: The query to execute
            
        Returns:
            Result containing the query result (a read model, list of read models, or None)
        """
        ...
    
    async def execute_with_metrics(self, query: Q) -> Result[QueryResult]:
        """
        Execute a query with execution metrics.
        
        Args:
            query: The query to execute
            
        Returns:
            Result containing query result with execution metrics
        """
        ...


class ProjectorServiceProtocol(Protocol):
    """Protocol defining operations for projector services."""
    
    async def register_projection(self, projection: Projection) -> Result[bool]:
        """
        Register a projection with the projector.
        
        Args:
            projection: The projection to register
            
        Returns:
            Result containing True if the projection was registered successfully
        """
        ...
    
    async def unregister_projection(self, projection_id: ProjectionId) -> Result[bool]:
        """
        Unregister a projection from the projector.
        
        Args:
            projection_id: The projection ID
            
        Returns:
            Result containing True if the projection was unregistered successfully
        """
        ...
    
    async def rebuild_all(self) -> Result[bool]:
        """
        Rebuild all read models by replaying events from the event store.
        
        Returns:
            Result containing True if the rebuild was successful
        """
        ...
    
    async def start(self) -> Result[bool]:
        """
        Start the projector to begin processing events.
        
        Returns:
            Result containing True if the projector was started successfully
        """
        ...
    
    async def stop(self) -> Result[bool]:
        """
        Stop the projector.
        
        Returns:
            Result containing True if the projector was stopped successfully
        """
        ...


# Service Implementations

class ReadModelService(Generic[T], ReadModelServiceProtocol[T]):
    """
    Implementation of the read model service.
    
    This service provides business logic for read model management,
    with optional caching support.
    """
    
    def __init__(
        self,
        repository: ReadModelRepositoryProtocol[T],
        model_type: Type[T],
        cache_service: Optional[CacheServiceProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            repository: The repository for read models
            model_type: The type of read model this service manages
            cache_service: Optional cache service
            logger: Optional logger instance
        """
        self.repository = repository
        self.model_type = model_type
        self.cache_service = cache_service
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_by_id(self, id: ReadModelId) -> Result[Optional[T]]:
        """
        Get a read model by ID, with caching if available.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing the read model if found, None otherwise
        """
        # Try to get from cache first
        if self.cache_service:
            cache_result = await self.cache_service.get(id.value, self.model_type.__name__)
            
            if cache_result.is_success() and cache_result.value is not None:
                self.logger.debug(f"Cache hit for read model {id.value}")
                return Success(cache_result.value)
        
        # Get from repository
        result = await self.repository.get_by_id(id)
        
        if not result.is_success():
            return result
        
        # Cache the result if found and cache service is available
        if result.value and self.cache_service:
            cache_result = await self.cache_service.set(
                id.value, 
                result.value, 
                self.model_type.__name__,
                read_model_id=id
            )
            if not cache_result.is_success():
                self.logger.warning(f"Failed to cache read model {id.value}: {cache_result.error}")
        
        return result
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[T]]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            Result containing list of matching read models
        """
        # Currently we don't cache find results, as it would be complex
        # to invalidate them correctly
        return await self.repository.find(criteria)
    
    async def save(self, model: T) -> Result[T]:
        """
        Save a read model and update cache if available.
        
        Args:
            model: The read model to save
            
        Returns:
            Result containing the saved read model
        """
        # Save to repository
        result = await self.repository.save(model)
        
        if not result.is_success():
            return result
        
        # Update cache if available
        if self.cache_service:
            cache_result = await self.cache_service.set(
                model.id.value, 
                result.value, 
                self.model_type.__name__,
                read_model_id=model.id
            )
            if not cache_result.is_success():
                self.logger.warning(f"Failed to update cache for read model {model.id.value}: {cache_result.error}")
        
        return result
    
    async def delete(self, id: ReadModelId) -> Result[bool]:
        """
        Delete a read model and remove from cache if available.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the read model was deleted, False otherwise
        """
        # Delete from repository
        result = await self.repository.delete(id)
        
        if not result.is_success():
            return result
        
        # Remove from cache if available
        if result.value and self.cache_service:
            cache_result = await self.cache_service.delete(id.value, self.model_type.__name__)
            if not cache_result.is_success():
                self.logger.warning(f"Failed to remove read model {id.value} from cache: {cache_result.error}")
        
        return result


class ProjectionService(Generic[P, T], ProjectionServiceProtocol[P]):
    """
    Implementation of the projection service.
    
    This service provides business logic for projection management and event application.
    """
    
    def __init__(
        self,
        projection_repository: ProjectionRepositoryProtocol[P],
        read_model_repository: ReadModelRepositoryProtocol[T],
        read_model_type: Type[T],
        projection_type: Type[P],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            projection_repository: The repository for projections
            read_model_repository: The repository for read models
            read_model_type: The type of read model this service manages
            projection_type: The type of projection this service manages
            logger: Optional logger instance
        """
        self.projection_repository = projection_repository
        self.read_model_repository = read_model_repository
        self.read_model_type = read_model_type
        self.projection_type = projection_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_by_id(self, id: ProjectionId) -> Result[Optional[P]]:
        """
        Get a projection by ID.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing the projection if found, None otherwise
        """
        return await self.projection_repository.get_by_id(id)
    
    async def get_by_event_type(self, event_type: str) -> Result[List[P]]:
        """
        Get projections by event type.
        
        Args:
            event_type: The event type
            
        Returns:
            Result containing list of projections for the event type
        """
        return await self.projection_repository.get_by_event_type(event_type)
    
    async def save(self, projection: P) -> Result[P]:
        """
        Save a projection.
        
        Args:
            projection: The projection to save
            
        Returns:
            Result containing the saved projection
        """
        return await self.projection_repository.save(projection)
    
    async def delete(self, id: ProjectionId) -> Result[bool]:
        """
        Delete a projection.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing True if the projection was deleted, False otherwise
        """
        return await self.projection_repository.delete(id)
    
    async def apply_event(self, event: DomainEvent, projection: P) -> Result[Optional[T]]:
        """
        Apply an event using a projection to create or update a read model.
        
        Args:
            event: The event to apply
            projection: The projection to use
            
        Returns:
            Result containing the created or updated read model, or None if no action was taken
        """
        try:
            # Check if projection is active
            if not projection.is_active:
                return Success(None)
            
            # Check if the event type matches the projection
            if not event.event_type == projection.event_type:
                return Failure(
                    ErrorCode.INVALID_OPERATION,
                    ErrorDetails(
                        message=f"Event type {event.event_type} doesn't match projection event type {projection.event_type}",
                        context={"event_id": event.event_id, "projection_id": projection.id.value}
                    )
                )
            
            # Apply the event to create or update a read model
            # This would be implemented by subclasses with specific business logic
            read_model = await self._apply_event_logic(event, projection)
            
            if read_model:
                # Save the read model
                save_result = await self.read_model_repository.save(read_model)
                if not save_result.is_success():
                    return Failure(
                        ErrorCode.REPOSITORY_ERROR,
                        ErrorDetails(
                            message=f"Failed to save read model after applying event: {save_result.error.message}",
                            context={"event_id": event.event_id, "projection_id": projection.id.value}
                        )
                    )
                
                return Success(save_result.value)
            
            return Success(None)
        except Exception as e:
            self.logger.error(f"Error applying event {event.event_type} ({event.event_id}): {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Error applying event: {str(e)}",
                    context={"event_id": event.event_id, "projection_id": projection.id.value}
                )
            )
    
    async def _apply_event_logic(self, event: DomainEvent, projection: P) -> Optional[T]:
        """
        Apply the event to create or update a read model.
        
        This method should be overridden by subclasses to implement
        specific projection logic.
        
        Args:
            event: The event to apply
            projection: The projection to use
            
        Returns:
            The created or updated read model, or None if no action was taken
        """
        # Default implementation does nothing
        # Subclasses should override this method with specific logic
        return None


class CacheService(CacheServiceProtocol):
    """
    Implementation of the cache service.
    
    This service provides caching functionality for read models and other data.
    """
    
    def __init__(
        self,
        cache_repository: CacheRepositoryProtocol,
        default_ttl_seconds: Optional[int] = 3600,  # 1 hour default
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            cache_repository: The repository for cache entries
            default_ttl_seconds: Optional default time-to-live in seconds
            logger: Optional logger instance
        """
        self.cache_repository = cache_repository
        self.default_ttl_seconds = default_ttl_seconds
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get(self, key: str, model_type: str) -> Result[Optional[Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing the cached value if found, None otherwise
        """
        result = await self.cache_repository.get(key, model_type)
        
        if not result.is_success():
            return result
        
        if result.value:
            # Return the value from the cache entry
            return Success(result.value.value)
        
        return Success(None)
    
    async def set(
        self, key: str, value: Any, model_type: str, 
        read_model_id: Optional[ReadModelId] = None, 
        ttl_seconds: Optional[int] = None
    ) -> Result[bool]:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            model_type: The model type
            read_model_id: Optional read model ID associated with this cache entry
            ttl_seconds: Optional time-to-live in seconds
            
        Returns:
            Result containing True if the operation was successful
        """
        try:
            # Calculate expiry time if TTL is provided
            expires_at = None
            if ttl_seconds is not None or self.default_ttl_seconds is not None:
                ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
                if ttl is not None:
                    expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
            
            # Create cache entry
            entry = CacheEntry(
                id=str(uuid.uuid4()),
                read_model_id=read_model_id or ReadModelId(value=key),
                read_model_type=model_type,
                key=key,
                value=value,
                level=CacheLevel.MEMORY,  # This could be configurable
                created_at=datetime.now(UTC),
                expires_at=expires_at
            )
            
            # Save to repository
            result = await self.cache_repository.set(entry)
            
            if not result.is_success():
                return Failure(
                    ErrorCode.CACHE_ERROR,
                    ErrorDetails(
                        message=f"Failed to set cache entry: {result.error.message}",
                        context={"key": key, "model_type": model_type}
                    )
                )
            
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error setting cache entry {key}, {model_type}: {str(e)}")
            return Failure(
                ErrorCode.CACHE_ERROR,
                ErrorDetails(
                    message=f"Error setting cache entry: {str(e)}",
                    context={"key": key, "model_type": model_type}
                )
            )
    
    async def delete(self, key: str, model_type: str) -> Result[bool]:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing True if the cache entry was deleted, False otherwise
        """
        return await self.cache_repository.delete(key, model_type)
    
    async def clear(self, model_type: Optional[str] = None) -> Result[bool]:
        """
        Clear cache entries.
        
        Args:
            model_type: Optional model type to clear entries for. If None, clears all entries.
            
        Returns:
            Result containing True if the operation was successful
        """
        return await self.cache_repository.clear(model_type)


class QueryService(Generic[Q, T], QueryServiceProtocol[Q, T]):
    """
    Implementation of the query service.
    
    This service executes queries to retrieve read models, with optional caching.
    """
    
    def __init__(
        self,
        repository: ReadModelRepositoryProtocol[T],
        query_type: Type[Q],
        model_type: Type[T],
        cache_service: Optional[CacheServiceProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            repository: The repository for read models
            query_type: The type of query this service handles
            model_type: The type of read model this service returns
            cache_service: Optional cache service
            logger: Optional logger instance
        """
        self.repository = repository
        self.query_type = query_type
        self.model_type = model_type
        self.cache_service = cache_service
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute(self, query: Q) -> Result[Union[T, List[T], None]]:
        """
        Execute a query to retrieve read models.
        
        Args:
            query: The query to execute
            
        Returns:
            Result containing the query result (a read model, list of read models, or None)
        """
        try:
            # Handle different query types
            if query.query_type == QueryType.GET_BY_ID:
                # Handle get by ID query
                if not query.has_id_parameter:
                    return Failure(
                        ErrorCode.INVALID_QUERY,
                        ErrorDetails(
                            message="GET_BY_ID query must have an id parameter",
                            context={"query_id": query.id.value}
                        )
                    )
                
                model_id = ReadModelId(value=query.parameters["id"])
                
                # Try to get from cache first
                if self.cache_service:
                    cache_key = f"id:{model_id.value}"
                    cache_result = await self.cache_service.get(cache_key, self.model_type.__name__)
                    
                    if cache_result.is_success() and cache_result.value:
                        return Success(cache_result.value)
                
                # Get from repository
                result = await self.repository.get_by_id(model_id)
                
                if not result.is_success():
                    return result
                
                # Cache the result if found and cache service is available
                if result.value and self.cache_service:
                    cache_key = f"id:{model_id.value}"
                    await self.cache_service.set(
                        cache_key, 
                        result.value, 
                        self.model_type.__name__,
                        read_model_id=model_id
                    )
                
                return result
            
            elif query.query_type == QueryType.FIND:
                # Handle find query
                if not query.has_criteria_parameter:
                    return Failure(
                        ErrorCode.INVALID_QUERY,
                        ErrorDetails(
                            message="FIND query must have a criteria parameter",
                            context={"query_id": query.id.value}
                        )
                    )
                
                criteria = query.parameters["criteria"]
                return await self.repository.find(criteria)
            
            elif query.query_type == QueryType.LIST:
                # Handle list query (gets all)
                return await self.repository.find({})
            
            elif query.query_type == QueryType.CUSTOM:
                # Handle custom query - this would be implemented by subclasses
                return await self._execute_custom_query(query)
            
            else:
                return Failure(
                    ErrorCode.INVALID_QUERY,
                    ErrorDetails(
                        message=f"Unsupported query type: {query.query_type}",
                        context={"query_id": query.id.value}
                    )
                )
        except Exception as e:
            self.logger.error(f"Error executing query {query.id.value}: {str(e)}")
            return Failure(
                ErrorCode.QUERY_EXECUTION_ERROR,
                ErrorDetails(
                    message=f"Error executing query: {str(e)}",
                    context={"query_id": query.id.value}
                )
            )
    
    async def execute_with_metrics(self, query: Q) -> Result[QueryResult]:
        """
        Execute a query with execution metrics.
        
        Args:
            query: The query to execute
            
        Returns:
            Result containing query result with execution metrics
        """
        try:
            # Record start time
            start_time = time.time()
            
            # Execute the query
            result = await self.execute(query)
            
            # Record end time and calculate duration
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            
            # Create query result
            if not result.is_success():
                return Failure(
                    result.error.code,
                    ErrorDetails(
                        message=f"Query execution failed: {result.error.message}",
                        context={"query_id": query.id.value}
                    )
                )
            
            # Convert results to list if needed
            if isinstance(result.value, list):
                results = result.value
                result_count = len(results)
            elif result.value is not None:
                results = result.value
                result_count = 1
            else:
                results = None
                result_count = 0
            
            query_result = QueryResult(
                id=str(uuid.uuid4()),
                query_id=query.id,
                execution_time_ms=execution_time_ms,
                result_count=result_count,
                results=results,
                created_at=datetime.now(UTC),
                is_cached=False  # This could be updated based on cache hit/miss
            )
            
            return Success(query_result)
        except Exception as e:
            self.logger.error(f"Error executing query with metrics {query.id.value}: {str(e)}")
            return Failure(
                ErrorCode.QUERY_EXECUTION_ERROR,
                ErrorDetails(
                    message=f"Error executing query with metrics: {str(e)}",
                    context={"query_id": query.id.value}
                )
            )
    
    async def _execute_custom_query(self, query: Q) -> Result[Union[T, List[T], None]]:
        """
        Execute a custom query.
        
        This method should be overridden by subclasses to implement
        custom query logic.
        
        Args:
            query: The query to execute
            
        Returns:
            Result containing the query result
        """
        # Default implementation returns an error
        return Failure(
            ErrorCode.NOT_IMPLEMENTED,
            ErrorDetails(
                message="Custom query execution not implemented",
                context={"query_id": query.id.value}
            )
        )


class ProjectionHandler(EventHandler[EventT]):
    """
    Event handler that delegates to a projection service.
    
    This class bridges the gap between the event system and projection services.
    """
    
    def __init__(
        self,
        event_type: Type[EventT],
        projection_service: ProjectionServiceProtocol,
        projection: Projection,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the handler.
        
        Args:
            event_type: The type of event this handler processes
            projection_service: The projection service to delegate to
            projection: The projection to use
            logger: Optional logger instance
        """
        super().__init__(event_type)
        self.projection_service = projection_service
        self.projection = projection
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def handle(self, event: EventT) -> None:
        """
        Handle an event by delegating to the projection service.
        
        Args:
            event: The event to handle
        """
        try:
            self.logger.debug(f"Handling event {event.event_type} ({event.event_id})")
            
            # Apply the event using the projection service
            result = await self.projection_service.apply_event(event, self.projection)
            
            if not result.is_success():
                self.logger.error(f"Error applying event {event.event_type} ({event.event_id}): {result.error.message}")
            elif result.value:
                self.logger.debug(f"Applied event {event.event_type} ({event.event_id}) to read model {result.value.id.value}")
        except Exception as e:
            self.logger.error(f"Error handling event {event.event_type} ({event.event_id}): {str(e)}")


class ProjectorService(ProjectorServiceProtocol):
    """
    Implementation of the projector service.
    
    This service manages projections and ensures that domain events
    are processed to keep read models up-to-date.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        event_store: Optional[EventStore],
        projection_service: ProjectionServiceProtocol,
        projector_config_repository: ProjectorConfigurationRepositoryProtocol,
        config_name: str = "default",
        async_processing: bool = True,
        batch_size: int = 100,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            event_bus: The event bus to subscribe to
            event_store: Optional event store for replaying events
            projection_service: The projection service to use
            projector_config_repository: Repository for projector configurations
            config_name: The name of this projector's configuration
            async_processing: Whether to process events asynchronously
            batch_size: Maximum number of events to process in a batch
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.event_store = event_store
        self.projection_service = projection_service
        self.projector_config_repository = projector_config_repository
        self.config_name = config_name
        self.async_processing = async_processing
        self.batch_size = batch_size
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self._handlers: Dict[Type[DomainEvent], ProjectionHandler] = {}
        self._projections: Dict[str, Projection] = {}  # ProjectionId -> Projection
        self._running = False
        self._queue: Optional[asyncio.Queue[DomainEvent]] = None
        self._worker_task: Optional[asyncio.Task] = None
    
    async def load_configuration(self) -> Result[ProjectorConfiguration]:
        """
        Load the projector configuration from the repository.
        
        Returns:
            Result containing the projector configuration
        """
        try:
            # Try to get the configuration by name
            result = await self.projector_config_repository.get_by_name(self.config_name)
            
            if not result.is_success():
                return result
            
            config = result.value
            
            if not config:
                # Create a new configuration if one doesn't exist
                config = ProjectorConfiguration(
                    id=str(uuid.uuid4()),
                    name=self.config_name,
                    async_processing=self.async_processing,
                    batch_size=self.batch_size,
                    cache_enabled=True,
                    cache_ttl_seconds=3600,
                    rebuild_on_startup=False
                )
                
                save_result = await self.projector_config_repository.save(config)
                
                if not save_result.is_success():
                    return Failure(
                        ErrorCode.REPOSITORY_ERROR,
                        ErrorDetails(
                            message=f"Failed to save new projector configuration: {save_result.error.message}",
                            context={"config_name": self.config_name}
                        )
                    )
                
                config = save_result.value
            
            # Update local settings from configuration
            self.async_processing = config.async_processing
            self.batch_size = config.batch_size
            
            # Apply registered projections
            for projection in config.projections:
                await self.register_projection(projection)
            
            return Success(config)
        except Exception as e:
            self.logger.error(f"Error loading projector configuration: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Error loading projector configuration: {str(e)}",
                    context={"config_name": self.config_name}
                )
            )
    
    async def register_projection(self, projection: Projection) -> Result[bool]:
        """
        Register a projection with the projector.
        
        Args:
            projection: The projection to register
            
        Returns:
            Result containing True if the projection was registered successfully
        """
        try:
            # Check if projection is already registered
            if projection.id.value in self._projections:
                self.logger.debug(f"Projection {projection.id.value} already registered")
                return Success(True)
            
            # Store the projection
            self._projections[projection.id.value] = projection
            
            # Create an event handler for this projection
            event_type = projection.event_type
            
            handler = ProjectionHandler(
                event_type=event_type.__class__,
                projection_service=self.projection_service,
                projection=projection,
                logger=self.logger
            )
            
            self._handlers[handler.event_type] = handler
            
            # Subscribe the handler to the event bus
            self.event_bus.subscribe(
                handler=handler,
                event_type=handler.event_type,
            )
            
            self.logger.debug(f"Registered projection {projection.id.value} for event type {event_type}")
            
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error registering projection {projection.id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Error registering projection: {str(e)}",
                    context={"projection_id": projection.id.value}
                )
            )
    
    async def unregister_projection(self, projection_id: ProjectionId) -> Result[bool]:
        """
        Unregister a projection from the projector.
        
        Args:
            projection_id: The projection ID
            
        Returns:
            Result containing True if the projection was unregistered successfully
        """
        try:
            # Check if projection is registered
            if projection_id.value not in self._projections:
                self.logger.debug(f"Projection {projection_id.value} not registered")
                return Success(False)
            
            projection = self._projections[projection_id.value]
            event_type = projection.event_type
            
            # Get the handler
            handler = self._handlers.get(event_type.__class__)
            
            if handler:
                # Unsubscribe the handler from the event bus
                self.event_bus.unsubscribe(
                    handler=handler,
                    event_type=handler.event_type,
                )
                
                # Remove the handler
                del self._handlers[handler.event_type]
            
            # Remove the projection
            del self._projections[projection_id.value]
            
            self.logger.debug(f"Unregistered projection {projection_id.value}")
            
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error unregistering projection {projection_id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Error unregistering projection: {str(e)}",
                    context={"projection_id": projection_id.value}
                )
            )
    
    async def rebuild_all(self) -> Result[bool]:
        """
        Rebuild all read models by replaying events from the event store.
        
        Returns:
            Result containing True if the rebuild was successful
        """
        if not self.event_store:
            return Failure(
                ErrorCode.INVALID_OPERATION,
                ErrorDetails(
                    message="Cannot rebuild read models: no event store provided"
                )
            )
        
        try:
            self.logger.info("Rebuilding all read models...")
            
            # Get all events from the event store
            events = await self.event_store.get_events()
            
            # Process events in order
            for event in events:
                event_type = type(event)
                
                # Get handler for this event type
                handler = self._handlers.get(event_type)
                
                if handler:
                    # Apply the event using the handler
                    await handler.handle(event)
            
            self.logger.info("Rebuild complete")
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error rebuilding read models: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Error rebuilding read models: {str(e)}"
                )
            )
    
    async def start(self) -> Result[bool]:
        """
        Start the projector to begin processing events.
        
        Returns:
            Result containing True if the projector was started successfully
        """
        try:
            if self._running:
                return Success(True)
            
            # Load configuration
            config_result = await self.load_configuration()
            
            if not config_result.is_success():
                return Failure(
                    ErrorCode.APPLICATION_ERROR,
                    ErrorDetails(
                        message=f"Failed to start projector: could not load configuration: {config_result.error.message}"
                    )
                )
            
            config = config_result.value
            
            self._running = True
            
            # Rebuild read models if configured to do so
            if config.rebuild_on_startup and self.event_store:
                rebuild_result = await self.rebuild_all()
                
                if not rebuild_result.is_success():
                    self.logger.warning(f"Failed to rebuild read models on startup: {rebuild_result.error.message}")
            
            # Start async processing if enabled
            if self.async_processing:
                self._queue = asyncio.Queue()
                self._worker_task = asyncio.create_task(self._worker())
            
            self.logger.info("Projector started")
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error starting projector: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Error starting projector: {str(e)}"
                )
            )
    
    async def stop(self) -> Result[bool]:
        """
        Stop the projector.
        
        Returns:
            Result containing True if the projector was stopped successfully
        """
        try:
            if not self._running:
                return Success(True)
            
            self._running = False
            
            # Stop the worker task if it's running
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
                
                self._worker_task = None
            
            # Clear the queue
            if self._queue:
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except asyncio.QueueEmpty:
                        break
            
            self.logger.info("Projector stopped")
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error stopping projector: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Error stopping projector: {str(e)}"
                )
            )
    
    async def _worker(self) -> None:
        """Worker that processes events from the queue."""
        while self._running and self._queue:
            try:
                # Get events up to batch size
                events = []
                for _ in range(self.batch_size):
                    try:
                        event = self._queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break
                
                if not events:
                    # If no events, wait for one
                    event = await self._queue.get()
                    events = [event]
                
                # Process events
                await self._process_events(events)
                
                # Mark tasks as done
                for _ in events:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in projector worker: {str(e)}")
    
    async def _process_events(self, events: List[DomainEvent]) -> None:
        """
        Process a batch of events.
        
        Args:
            events: The events to process
        """
        for event in events:
            event_type = type(event)
            
            # Get handler for this event type
            handler = self._handlers.get(event_type)
            
            if handler:
                # Apply the event using the handler
                await handler.handle(event)