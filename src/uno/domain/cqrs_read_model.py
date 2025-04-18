"""
Integration between CQRS and Read Model components.

This module provides integration points between the CQRS system and the
Read Model system, enabling a complete implementation of the CQRS pattern
with read model projections.
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    Protocol,
    cast,
    Callable,
)
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

from uno.core.cqrs import (
    Command,
    CommandHandler,
    Query,
    QueryHandler,
    CommandResult,
    QueryResult,
    MessageBus,
    CommandBus,
    QueryBus,
    Mediator,
    TransactionalCommandHandler,
)
from uno.domain.event_store import EventStore, EventSourcedRepository
from uno.core.events import UnoEvent
from uno.read_model.read_model import ReadModel, ReadModelRepository
from uno.read_model.query_service import (
    ReadModelQueryService,
    EnhancedQueryService,
    GetByIdQuery,
    FindByQuery,
    PaginatedQuery,
    SearchQuery,
    AggregateQuery,
    GraphQuery,
    HybridQuery,
)
from uno.read_model.projector import Projection, Projector
from uno.core.uow import UnitOfWork, AbstractUnitOfWork

# Type variables
T = TypeVar("T")
TCommand = TypeVar("TCommand", bound=Command)
TQuery = TypeVar("TQuery", bound=Query)
TReadModel = TypeVar("TReadModel", bound=ReadModel)
TEvent = TypeVar("TEvent", bound=UnoEvent)
TResult = TypeVar("TResult")


class ReadModelIntegrationConfig(BaseModel):
    """
    Configuration for CQRS and Read Model integration.

    Attributes:
        enable_projections: Whether to enable read model projections
        async_projections: Whether to process projections asynchronously
        projection_batch_size: Batch size for projection processing
        enable_snapshot_rebuilding: Whether to enable snapshot-based rebuilding
        snapshot_frequency: How often to create snapshots (in events)
        enable_metrics: Whether to enable performance metrics
    """

    model_config = ConfigDict(frozen=False)

    enable_projections: bool = True
    async_projections: bool = True
    projection_batch_size: int = 100
    enable_snapshot_rebuilding: bool = True
    snapshot_frequency: int = 1000
    enable_metrics: bool = True


class ReadModelQueryHandlerConfig(BaseModel):
    """
    Configuration for read model query handlers.

    Attributes:
        enable_caching: Whether to enable query result caching
        cache_ttl_seconds: Default TTL for cached query results
        enable_metrics: Whether to enable performance metrics
        enable_fallback: Whether to enable fallback to database queries
    """

    model_config = ConfigDict(frozen=False)

    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    enable_metrics: bool = True
    enable_fallback: bool = True


class ReadModelCommandHandlerConfig(BaseModel):
    """
    Configuration for read model command handlers.

    Attributes:
        invalidate_cache: Whether to invalidate cache on commands
        sync_read_models: Whether to synchronously update read models
        enable_metrics: Whether to enable performance metrics
    """

    model_config = ConfigDict(frozen=False)

    invalidate_cache: bool = True
    sync_read_models: bool = False
    enable_metrics: bool = True


class ReadModelQueryHandlerBase(
    QueryHandler[TQuery, TResult], Generic[TQuery, TResult, TReadModel]
):
    """
    Base class for query handlers that use read models.

    This handler delegates queries to a read model query service, providing
    a bridge between domain queries and read model queries.
    """

    def __init__(
        self,
        read_model_type: Type[TReadModel],
        query_service: ReadModelQueryService[TReadModel],
        config: Optional[ReadModelQueryHandlerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the query handler.

        Args:
            read_model_type: The type of read model
            query_service: The query service for retrieving read models
            config: Optional configuration
            logger: Optional logger for diagnostics
        """
        self.read_model_type = read_model_type
        self.query_service = query_service
        self.config = config or ReadModelQueryHandlerConfig()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
        self.metrics_enabled = self.config.enable_metrics

    async def handle(self, query: TQuery) -> TResult:
        """
        Handle a domain query by delegating to the read model query service.

        Args:
            query: The domain query

        Returns:
            The query result
        """
        # Convert domain query to read model query
        read_model_query = self.to_read_model_query(query)

        try:
            # Execute query against read model service
            result = await self.query_service.handle_query(read_model_query)

            # Convert the result back to the expected domain result type
            return self.convert_result(result)

        except Exception as e:
            self.logger.error(f"Error handling query {query}: {e}")
            if self.config.enable_fallback:
                # Attempt fallback to direct database query
                return await self.fallback_query(query)
            raise

    @abstractmethod
    def to_read_model_query(self, query: TQuery) -> Any:
        """
        Convert a domain query to a read model query.

        Args:
            query: The domain query

        Returns:
            A read model query
        """
        pass

    @abstractmethod
    def convert_result(self, read_model_result: Any) -> TResult:
        """
        Convert a read model result to a domain result.

        Args:
            read_model_result: The read model query result

        Returns:
            A domain query result
        """
        pass

    async def fallback_query(self, query: TQuery) -> TResult:
        """
        Execute a fallback query directly against the database.

        This method is called when the read model query fails and fallback is enabled.

        Args:
            query: The domain query

        Returns:
            The query result
        """
        self.logger.warning(f"Executing fallback query for {query}")
        # To be implemented by subclasses
        raise NotImplementedError("Fallback query not implemented")


class GetByIdQueryHandler(
    ReadModelQueryHandlerBase[TQuery, Optional[TReadModel], TReadModel]
):
    """
    Query handler for retrieving a read model by ID.

    This handler is used for simple get-by-id queries against read models.
    """

    def to_read_model_query(self, query: TQuery) -> GetByIdQuery:
        """
        Convert a domain get-by-id query to a read model query.

        Args:
            query: The domain query

        Returns:
            A GetByIdQuery
        """
        # Extract ID from the query
        if hasattr(query, "id"):
            id_value = getattr(query, "id")
            return GetByIdQuery(id=str(id_value))

        # If query doesn't have an ID field, try common patterns
        for attr in ["entity_id", "model_id", "aggregate_id", "key"]:
            if hasattr(query, attr):
                id_value = getattr(query, attr)
                return GetByIdQuery(id=str(id_value))

        raise ValueError(f"Query {query} does not have an identifiable ID field")

    def convert_result(
        self, read_model_result: Optional[TReadModel]
    ) -> Optional[TReadModel]:
        """
        Return the read model result directly.

        Args:
            read_model_result: The read model

        Returns:
            The read model
        """
        return read_model_result


class FindQueryHandler(ReadModelQueryHandlerBase[TQuery, List[TReadModel], TReadModel]):
    """
    Query handler for finding read models by criteria.

    This handler is used for search queries against read models.
    """

    def __init__(
        self,
        read_model_type: Type[TReadModel],
        query_service: ReadModelQueryService[TReadModel],
        criteria_mapping: Dict[str, str],
        config: Optional[ReadModelQueryHandlerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the query handler.

        Args:
            read_model_type: The type of read model
            query_service: The query service for retrieving read models
            criteria_mapping: Mapping from domain query attributes to read model fields
            config: Optional configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(read_model_type, query_service, config, logger)
        self.criteria_mapping = criteria_mapping

    def to_read_model_query(self, query: TQuery) -> FindByQuery:
        """
        Convert a domain find query to a read model query.

        Args:
            query: The domain query

        Returns:
            A FindByQuery
        """
        # Extract criteria from the query using the mapping
        criteria = {}

        for domain_attr, read_model_field in self.criteria_mapping.items():
            if hasattr(query, domain_attr):
                value = getattr(query, domain_attr)
                if value is not None:  # Skip None values
                    criteria[read_model_field] = value

        return FindByQuery(criteria=criteria)

    def convert_result(self, read_model_result: List[TReadModel]) -> List[TReadModel]:
        """
        Return the read model result list directly.

        Args:
            read_model_result: The list of read models

        Returns:
            The list of read models
        """
        return read_model_result


class SearchQueryHandler(ReadModelQueryHandlerBase[TQuery, Any, TReadModel]):
    """
    Query handler for search queries.

    This handler is used for text search queries against read models,
    optionally using vector search capabilities.
    """

    def __init__(
        self,
        read_model_type: Type[TReadModel],
        query_service: EnhancedQueryService[TReadModel],
        text_field: str = "query",
        fields_mapping: Optional[Dict[str, str]] = None,
        filters_mapping: Optional[Dict[str, str]] = None,
        config: Optional[ReadModelQueryHandlerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the query handler.

        Args:
            read_model_type: The type of read model
            query_service: The enhanced query service for searching read models
            text_field: Field in the domain query containing the search text
            fields_mapping: Mapping from domain query fields to read model fields
            filters_mapping: Mapping from domain query filters to read model fields
            config: Optional configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(read_model_type, query_service, config, logger)
        self.text_field = text_field
        self.fields_mapping = fields_mapping or {}
        self.filters_mapping = filters_mapping or {}

    def to_read_model_query(self, query: TQuery) -> SearchQuery:
        """
        Convert a domain search query to a read model search query.

        Args:
            query: The domain query

        Returns:
            A SearchQuery
        """
        # Extract text from the query
        if not hasattr(query, self.text_field):
            raise ValueError(f"Query {query} does not have a {self.text_field} field")

        text = getattr(query, self.text_field)

        # Extract fields to search in
        fields = None
        if hasattr(query, "fields"):
            domain_fields = getattr(query, "fields")
            if domain_fields:
                fields = [self.fields_mapping.get(f, f) for f in domain_fields]

        # Extract filters
        filters = {}
        for domain_attr, read_model_field in self.filters_mapping.items():
            if hasattr(query, domain_attr):
                value = getattr(query, domain_attr)
                if value is not None:  # Skip None values
                    filters[read_model_field] = value

        # Extract pagination and sorting
        page = getattr(query, "page", 1)
        page_size = getattr(query, "page_size", 20)
        sort_by = getattr(query, "sort_by", None)
        sort_direction = getattr(query, "sort_direction", "asc")

        # Map sort field if needed
        if sort_by and sort_by in self.fields_mapping:
            sort_by = self.fields_mapping[sort_by]

        return SearchQuery(
            text=text,
            fields=fields,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def convert_result(self, read_model_result: Any) -> Any:
        """
        Return the search result directly.

        Args:
            read_model_result: The search result

        Returns:
            The search result
        """
        return read_model_result


class GraphQueryHandler(
    ReadModelQueryHandlerBase[TQuery, List[TReadModel], TReadModel]
):
    """
    Query handler for graph queries.

    This handler is used for graph-based queries against read models,
    leveraging Apache AGE knowledge graph capabilities.
    """

    def __init__(
        self,
        read_model_type: Type[TReadModel],
        query_service: EnhancedQueryService[TReadModel],
        path_field: str = "path_pattern",
        start_node_field: str = "start_node",
        mapping: Optional[Dict[str, str]] = None,
        config: Optional[ReadModelQueryHandlerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the query handler.

        Args:
            read_model_type: The type of read model
            query_service: The enhanced query service for graph queries
            path_field: Field in the domain query containing the path pattern
            start_node_field: Field in the domain query containing the start node
            mapping: Mapping from domain query attributes to graph query fields
            config: Optional configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(read_model_type, query_service, config, logger)
        self.path_field = path_field
        self.start_node_field = start_node_field
        self.mapping = mapping or {}

    def to_read_model_query(self, query: TQuery) -> GraphQuery:
        """
        Convert a domain graph query to a read model graph query.

        Args:
            query: The domain query

        Returns:
            A GraphQuery
        """
        # Extract path pattern from the query
        if not hasattr(query, self.path_field):
            raise ValueError(f"Query {query} does not have a {self.path_field} field")

        path_pattern = getattr(query, self.path_field)

        # Extract start node from the query
        if not hasattr(query, self.start_node_field):
            raise ValueError(
                f"Query {query} does not have a {self.start_node_field} field"
            )

        start_node = getattr(query, self.start_node_field)

        # Extract max depth
        max_depth = getattr(query, "max_depth", 3)

        # Extract filters
        filters = {}
        for domain_attr, graph_field in self.mapping.items():
            if hasattr(query, domain_attr):
                value = getattr(query, domain_attr)
                if value is not None:  # Skip None values
                    filters[graph_field] = value

        return GraphQuery(
            path_pattern=path_pattern,
            start_node=start_node,
            max_depth=max_depth,
            filters=filters,
        )

    def convert_result(self, read_model_result: List[TReadModel]) -> List[TReadModel]:
        """
        Return the graph query result directly.

        Args:
            read_model_result: The list of read models

        Returns:
            The list of read models
        """
        return read_model_result


class HybridQueryHandler(ReadModelQueryHandlerBase[TQuery, Any, TReadModel]):
    """
    Query handler for hybrid queries.

    This handler is used for hybrid queries that combine vector search
    and graph traversal for enhanced results.
    """

    def __init__(
        self,
        read_model_type: Type[TReadModel],
        query_service: EnhancedQueryService[TReadModel],
        text_field: str = "query",
        path_field: Optional[str] = "path_pattern",
        mapping: Optional[Dict[str, str]] = None,
        config: Optional[ReadModelQueryHandlerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the query handler.

        Args:
            read_model_type: The type of read model
            query_service: The enhanced query service for hybrid queries
            text_field: Field in the domain query containing the search text
            path_field: Optional field in the domain query containing the path pattern
            mapping: Mapping from domain query attributes to query fields
            config: Optional configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(read_model_type, query_service, config, logger)
        self.text_field = text_field
        self.path_field = path_field
        self.mapping = mapping or {}

    def to_read_model_query(self, query: TQuery) -> HybridQuery:
        """
        Convert a domain hybrid query to a read model hybrid query.

        Args:
            query: The domain query

        Returns:
            A HybridQuery
        """
        # Extract text from the query
        if not hasattr(query, self.text_field):
            raise ValueError(f"Query {query} does not have a {self.text_field} field")

        text = getattr(query, self.text_field)

        # Extract path pattern if specified
        path_pattern = None
        if self.path_field and hasattr(query, self.path_field):
            path_pattern = getattr(query, self.path_field)

        # Extract vector and graph weights
        vector_weight = getattr(query, "vector_weight", 0.5)
        graph_weight = getattr(query, "graph_weight", 0.5)

        # Extract filters
        filters = {}
        for domain_attr, query_field in self.mapping.items():
            if hasattr(query, domain_attr):
                value = getattr(query, domain_attr)
                if value is not None:  # Skip None values
                    filters[query_field] = value

        # Extract pagination
        page = getattr(query, "page", 1)
        page_size = getattr(query, "page_size", 20)

        return HybridQuery(
            text=text,
            path_pattern=path_pattern,
            vector_weight=vector_weight,
            graph_weight=graph_weight,
            filters=filters,
            page=page,
            page_size=page_size,
        )

    def convert_result(self, read_model_result: Any) -> Any:
        """
        Return the hybrid query result directly.

        Args:
            read_model_result: The hybrid query result

        Returns:
            The hybrid query result
        """
        return read_model_result


class ProjectionEventHandler(Generic[TEvent, TReadModel]):
    """
    Event handler that updates read models based on domain events.

    This handler processes domain events and updates read models through
    projections, enabling the read side of the CQRS pattern.
    """

    def __init__(
        self,
        event_type: Type[TEvent],
        read_model_type: Type[TReadModel],
        projection: Projection[TReadModel, TEvent],
        repository: ReadModelRepository[TReadModel],
        config: Optional[ReadModelIntegrationConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the event handler.

        Args:
            event_type: The type of event this handler processes
            read_model_type: The type of read model
            projection: The projection for transforming events to read models
            repository: The repository for storing read models
            config: Optional configuration
            logger: Optional logger for diagnostics
        """
        self.event_type = event_type
        self.read_model_type = read_model_type
        self.projection = projection
        self.repository = repository
        self.config = config or ReadModelIntegrationConfig()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
        self.pending_events: List[TEvent] = []

    async def handle_event(self, event: TEvent) -> None:
        """
        Handle a domain event by updating read models.

        Args:
            event: The domain event
        """
        if not self.config.enable_projections:
            return

        if self.config.async_projections:
            # Store event for batch processing
            self.pending_events.append(event)

            # Process if batch size is reached
            if len(self.pending_events) >= self.config.projection_batch_size:
                await self.process_pending_events()
        else:
            # Process event synchronously
            await self._process_event(event)

    async def process_pending_events(self) -> None:
        """Process all pending events in batch."""
        if not self.pending_events:
            return

        try:
            # Process events in batch
            for event in self.pending_events:
                await self._process_event(event)
        finally:
            # Clear pending events
            self.pending_events.clear()

    async def _process_event(self, event: TEvent) -> None:
        """
        Process a single event.

        Args:
            event: The domain event
        """
        try:
            # Apply projection to event
            read_model = await self.projection.apply(event)

            if read_model:
                # Save the updated read model
                await self.repository.save(read_model)

        except Exception as e:
            self.logger.error(f"Error processing event {event}: {e}")


class EventSourcingReadModelCommandHandler(
    TransactionalCommandHandler[TCommand, TResult]
):
    """
    Command handler that combines event sourcing with read model updates.

    This handler processes commands, stores events in the event store,
    and optionally updates read models synchronously.
    """

    def __init__(
        self,
        unit_of_work_factory: Callable[[], AbstractUnitOfWork],
        event_store: EventStore,
        event_handlers: Optional[
            Dict[Type[UnoEvent], List[Callable[[UnoEvent], Any]]]
        ] = None,
        config: Optional[ReadModelCommandHandlerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the command handler.

        Args:
            unit_of_work_factory: Factory for creating unit of work
            event_store: Event store for storing events
            event_handlers: Mapping from event types to handler functions
            config: Optional configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(unit_of_work_factory)
        self.event_store = event_store
        self.event_handlers = event_handlers or {}
        self.config = config or ReadModelCommandHandlerConfig()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
        self.metrics_enabled = self.config.enable_metrics
        self.events: List[UnoEvent] = []

    def add_event(self, event: UnoEvent) -> None:
        """
        Add an event to be published after the command is handled.

        Args:
            event: The domain event
        """
        self.events.append(event)

    async def _handle(self, command: TCommand, uow: AbstractUnitOfWork) -> TResult:
        """
        Handle a command with event sourcing.

        Args:
            command: The command to handle
            uow: The unit of work for the transaction

        Returns:
            The command result
        """
        # Clear events from previous command
        self.events.clear()

        # Execute command logic (to be implemented by subclasses)
        result = await self.execute_command(command, uow)

        # Store events in event store
        if self.events:
            for event in self.events:
                await self.event_store.append(event)

        # Process events synchronously if enabled
        if self.config.sync_read_models and self.events:
            for event in self.events:
                await self._process_event(event)

        return result

    @abstractmethod
    async def execute_command(
        self, command: TCommand, uow: AbstractUnitOfWork
    ) -> TResult:
        """
        Execute command logic.

        Args:
            command: The command to execute
            uow: The unit of work for the transaction

        Returns:
            The command result
        """
        pass

    async def _process_event(self, event: UnoEvent) -> None:
        """
        Process an event using registered handlers.

        Args:
            event: The domain event
        """
        # Find handlers for this event type
        handlers = []
        for event_type, event_handlers in self.event_handlers.items():
            if isinstance(event, event_type):
                handlers.extend(event_handlers)

        # Execute handlers
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self.logger.error(f"Error in event handler for {event}: {e}")


# Integration utilities


def register_projection_event_handlers(
    event_bus: Any,
    projections: List[
        Tuple[
            Type[UnoEvent],
            Projection[TReadModel, Any],
            ReadModelRepository[TReadModel],
        ]
    ],
    config: Optional[ReadModelIntegrationConfig] = None,
) -> List[ProjectionEventHandler]:
    """
    Register projection event handlers with an event bus.

    Args:
        event_bus: The event bus to register handlers with
        projections: List of (event_type, projection, repository) tuples
        config: Optional configuration

    Returns:
        List of created projection event handlers
    """
    handlers = []

    for event_type, projection, repository in projections:
        # Create handler
        handler = ProjectionEventHandler(
            event_type=event_type,
            read_model_type=projection.read_model_type,
            projection=projection,
            repository=repository,
            config=config,
        )

        # Register with event bus
        event_bus.register(event_type, handler.handle_event)

        handlers.append(handler)

    return handlers


def create_query_handler(
    query_type: Type[TQuery],
    read_model_type: Type[TReadModel],
    query_service: ReadModelQueryService[TReadModel],
    query_bus: QueryBus,
    handler_type: Type[ReadModelQueryHandlerBase] = GetByIdQueryHandler,
    **kwargs,
) -> ReadModelQueryHandlerBase:
    """
    Create and register a query handler.

    Args:
        query_type: Type of query to handle
        read_model_type: Type of read model
        query_service: Query service for retrieving read models
        query_bus: Query bus to register the handler with
        handler_type: Type of handler to create
        **kwargs: Additional arguments for the handler constructor

    Returns:
        The created query handler
    """
    # Create handler
    handler = handler_type(
        read_model_type=read_model_type, query_service=query_service, **kwargs
    )

    # Register with query bus
    query_bus.register(query_type, handler.handle)

    return handler
