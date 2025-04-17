"""
Read Model module for the Uno framework.

This module implements the read model functionality for CQRS applications,
providing projection and query capability for efficient read operations.
"""

from uno.read_model.entities import (
    ReadModelId, ProjectionId, QueryId,
    CacheLevel, ProjectionType, QueryType,
    ReadModel, Projection, Query, QueryResult, CacheEntry,
    ProjectorConfiguration
)

from uno.read_model.domain_repositories import (
    ReadModelRepositoryProtocol, ProjectionRepositoryProtocol,
    QueryRepositoryProtocol, CacheRepositoryProtocol,
    ProjectorConfigurationRepositoryProtocol,
    InMemoryReadModelRepository, InMemoryProjectionRepository,
    InMemoryQueryRepository, InMemoryCacheRepository,
    InMemoryProjectorConfigurationRepository,
    DatabaseReadModelRepository, RedisCacheRepository
)

from uno.read_model.repository_implementations import (
    PostgresReadModelRepository, PostgresProjectionRepository,
    PostgresQueryRepository, PostgresProjectorConfigurationRepository,
    HybridReadModelRepository
)

from uno.read_model.domain_services import (
    ReadModelServiceProtocol, ProjectionServiceProtocol,
    CacheServiceProtocol, QueryServiceProtocol, ProjectorServiceProtocol,
    ReadModelService, ProjectionService, CacheService,
    QueryService, ProjectorService, ProjectionHandler
)

from uno.read_model.domain_provider import ReadModelProvider
from uno.read_model.domain_endpoints import (
    ReadModelEndpoints, ProjectionEndpoints, create_read_model_endpoints
)

# Import enhanced query service components
from uno.read_model.read_model import ReadModel, ReadModelRepository
from uno.read_model.cache_service import ReadModelCache
from uno.read_model.query_service import (
    ReadModelQueryService, EnhancedQueryService,
    GetByIdQuery, FindByQuery, PaginatedQuery,
    SearchQuery, AggregateQuery, GraphQuery, HybridQuery,
    PaginatedResult, QueryMetrics, ReadModelQueryHandler
)
from uno.read_model.age_integration import (
    AGEGraphService, ReadModelGraphAdapter, 
    GraphQueryConfiguration, create_age_graph_service
)

# Public API
__all__ = [
    # Entities
    "ReadModelId", "ProjectionId", "QueryId",
    "CacheLevel", "ProjectionType", "QueryType",
    "ReadModel", "Projection", "Query", "QueryResult", "CacheEntry",
    "ProjectorConfiguration",
    
    # Repositories
    "ReadModelRepositoryProtocol", "ProjectionRepositoryProtocol",
    "QueryRepositoryProtocol", "CacheRepositoryProtocol",
    "ProjectorConfigurationRepositoryProtocol",
    "InMemoryReadModelRepository", "InMemoryProjectionRepository",
    "InMemoryQueryRepository", "InMemoryCacheRepository",
    "InMemoryProjectorConfigurationRepository",
    "DatabaseReadModelRepository", "RedisCacheRepository",
    
    # Repository Implementations
    "PostgresReadModelRepository", "PostgresProjectionRepository",
    "PostgresQueryRepository", "PostgresProjectorConfigurationRepository",
    "HybridReadModelRepository",
    
    # Services
    "ReadModelServiceProtocol", "ProjectionServiceProtocol",
    "CacheServiceProtocol", "QueryServiceProtocol", "ProjectorServiceProtocol",
    "ReadModelService", "ProjectionService", "CacheService",
    "QueryService", "ProjectorService", "ProjectionHandler",
    
    # Provider
    "ReadModelProvider",
    
    # Endpoints
    "ReadModelEndpoints", "ProjectionEndpoints", "create_read_model_endpoints",
    
    # Enhanced Query Service
    "ReadModelQueryService", "EnhancedQueryService",
    "GetByIdQuery", "FindByQuery", "PaginatedQuery",
    "SearchQuery", "AggregateQuery", "GraphQuery", "HybridQuery",
    "PaginatedResult", "QueryMetrics", "ReadModelQueryHandler",
    
    # AGE Integration
    "AGEGraphService", "ReadModelGraphAdapter", 
    "GraphQueryConfiguration", "create_age_graph_service",
    
    # Base Components
    "ReadModel", "ReadModelRepository", "ReadModelCache"
]