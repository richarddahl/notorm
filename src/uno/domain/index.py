"""
Domain layer package for the Uno framework.

This package contains the core domain-driven design components for implementing
business logic, including entities, value objects, services, and repositories.
"""

# Core domain components
from uno.domain.core import Entity, ValueObject, UnoEvent, AggregateRoot
from uno.core.base.respository import Repository
from uno.domain.service import DomainService
from uno.domain.factory import Factory

# Event handling - using the new unified event system
from uno.core.events import Event, AsyncEventBus as EventBus, EventStore, EventPublisher
from uno.core.protocols.event import EventHandler, EventBusProtocol, EventStoreProtocol
from uno.domain.event_import_fix import EventDispatcher, domain_event_handler

# Query system
from uno.domain.query import (
    QuerySpecification,
    QueryResult,
    QueryExecutor,
    RepositoryQueryExecutor,
    FilterQueryExecutor,
    QueryService,
)

# Enhanced query system
from uno.domain.enhanced_query import (
    QueryMetadata,
    EnhancedQueryExecutor,
    GraphPathQuery,
)

from uno.domain.query_optimizer import (
    QueryPerformanceTracker,
    QueryPerformanceMetric,
    QueryResultCache,
    GraphQueryOptimizer,
    MaterializedQueryView,
)

from uno.domain.selective_updater import (
    GraphChangeEvent,
    SelectiveGraphUpdater,
    GraphSynchronizer,
)

from uno.domain.graph_path_query import (
    PathQuerySpecification,
    GraphPathQuery,
    GraphPathQueryService,
)

__all__ = [
    # Core domain
    "Entity",
    "ValueObject",
    "UnoEvent",
    "AggregateRoot",
    "Repository",
    "DomainService",
    "Factory",
    # Event handling
    "Event",
    "EventBus",
    "EventStore", 
    "EventPublisher",
    "EventHandler",
    "EventBusProtocol",
    "EventStoreProtocol",
    "EventDispatcher",
    "domain_event_handler",
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
    "GraphPathQuery",
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
    "GraphPathQueryService",
]
