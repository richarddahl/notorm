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

# Event handling
from uno.domain.event_store import EventStore
from uno.domain.event_dispatcher import EventDispatcher, EventHandler
from uno.domain.event_store_manager import EventStoreManager
from uno.core.events import register_event_handler

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
    "EventStore",
    "EventDispatcher",
    "EventHandler",
    "EventStoreManager",
    "register_event_handler",
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
