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
    
    # Services
    "ReadModelServiceProtocol", "ProjectionServiceProtocol",
    "CacheServiceProtocol", "QueryServiceProtocol", "ProjectorServiceProtocol",
    "ReadModelService", "ProjectionService", "CacheService",
    "QueryService", "ProjectorService", "ProjectionHandler",
    
    # Provider
    "ReadModelProvider",
    
    # Endpoints
    "ReadModelEndpoints", "ProjectionEndpoints", "create_read_model_endpoints"
]