"""
Domain layer for the Uno framework.

This module implements a domain-driven design (DDD) approach for the Uno framework,
providing a clear separation of concerns and a rich domain model.
"""

# Core domain concepts
from uno.domain.core import (
    Entity, 
    ValueObject, 
    AggregateRoot, 
    DomainEvent,
    DomainException
)

# Data access
from uno.domain.repository import Repository

# Business logic
from uno.domain.service import DomainService

# Event sourcing and event store
try:
    from uno.domain.events import (
        DomainEvent,
        EventHandler,
        EventBus,
        EventStore,
        InMemoryEventStore,
        EventPublisher,
        get_event_bus,
        get_event_store,
        get_event_publisher
    )
    
    from uno.domain.event_store import (
        EventStore as EventStoreBase,
        PostgresEventStore,
        EventSourcedRepository
    )
    
    from uno.domain.event_store_manager import EventStoreManager
    
    from uno.domain.event_store_integration import (
        EventStoreIntegration,
        get_event_store_integration,
        get_event_sourced_repository
    )
    
    has_event_store = True
except ImportError:
    has_event_store = False

# Query system
try:
    from uno.domain.query import (
        QuerySpecification,
        QueryResult,
        QueryExecutor,
        RepositoryQueryExecutor,
        FilterQueryExecutor,
        QueryService
    )

    # Enhanced query system
    from uno.domain.enhanced_query import (
        QueryMetadata,
        EnhancedQueryExecutor
    )

    from uno.domain.query_optimizer import (
        QueryPerformanceTracker,
        QueryPerformanceMetric,
        QueryResultCache,
        GraphQueryOptimizer,
        MaterializedQueryView
    )

    from uno.domain.selective_updater import (
        GraphChangeEvent,
        SelectiveGraphUpdater,
        GraphSynchronizer
    )

    from uno.domain.graph_path_query import (
        PathQuerySpecification,
        GraphPathQuery,
        GraphPathQueryService
    )

    event_store_components = []
    if has_event_store:
        event_store_components = [
            # Event sourcing
            "EventHandler",
            "EventBus",
            "EventStore",
            "InMemoryEventStore",
            "EventPublisher",
            "get_event_bus",
            "get_event_store",
            "get_event_publisher",
            
            # Event store
            "EventStoreBase",
            "PostgresEventStore",
            "EventSourcedRepository",
            "EventStoreManager",
            
            # Event store integration
            "EventStoreIntegration",
            "get_event_store_integration",
            "get_event_sourced_repository"
        ]
    
    __all__ = [
        # Core domain concepts
        "Entity",
        "ValueObject",
        "AggregateRoot",
        "DomainEvent",
        "DomainException",
        
        # Data access
        "Repository",
        
        # Business logic
        "DomainService",
        
        # Query system
        "QuerySpecification",
        "QueryResult",
        "QueryExecutor",
        "RepositoryQueryExecutor",
        "FilterQueryExecutor",
        "QueryService",
        
        # Enhanced query system
        "QueryMetadata",
        "EnhancedQueryExecutor",
        "QueryPerformanceTracker",
        "QueryPerformanceMetric",
        "QueryResultCache",
        "GraphQueryOptimizer",
        "MaterializedQueryView",
        "GraphChangeEvent",
        "SelectiveGraphUpdater",
        "GraphSynchronizer",
        "PathQuerySpecification",
        "GraphPathQuery",
        "GraphPathQueryService"
    ] + event_store_components

except ImportError:
    # In case some enhanced query components aren't available yet
    event_store_components = []
    if has_event_store:
        event_store_components = [
            # Event sourcing
            "EventHandler",
            "EventBus",
            "EventStore",
            "InMemoryEventStore",
            "EventPublisher",
            "get_event_bus",
            "get_event_store",
            "get_event_publisher",
            
            # Event store
            "EventStoreBase",
            "PostgresEventStore",
            "EventSourcedRepository",
            "EventStoreManager",
            
            # Event store integration
            "EventStoreIntegration",
            "get_event_store_integration",
            "get_event_sourced_repository"
        ]
    
    __all__ = [
        # Core domain concepts
        "Entity",
        "ValueObject",
        "AggregateRoot",
        "DomainEvent",
        "DomainException",
        
        # Data access
        "Repository",
        
        # Business logic
        "DomainService",
    ] + event_store_components