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
    ]

except ImportError:
    # In case some enhanced query components aren't available yet
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
    ]