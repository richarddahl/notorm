"""
Domain provider for the Read Model module.

This module configures dependency injection for the Read Model module,
providing factory functions for repositories and services.
"""

import logging
from typing import Any, Dict, Optional, Type, TypeVar, cast

import inject

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails
from uno.domain.events import EventBus, EventStore
from uno.database.provider import DatabaseProvider
from uno.dependencies.interfaces import (
    ProviderProtocol, UnoServiceProtocol, UnoRepositoryProtocol
)

from uno.read_model.entities import (
    ReadModel, Projection, Query, ProjectorConfiguration, CacheLevel
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
    QueryService, ProjectorService
)

# Type variables
T = TypeVar('T', bound=ReadModel)
P = TypeVar('P', bound=Projection)
Q = TypeVar('Q', bound=Query)


class ReadModelProvider(ProviderProtocol):
    """
    Provider for read model dependencies.
    
    This class configures dependency injection for the Read Model module,
    providing factory functions for repositories and services.
    """
    
    def __init__(
        self,
        use_database: bool = True,
        use_redis_cache: bool = False,
        redis_client: Any = None,
        async_processing: bool = True,
        batch_size: int = 100,
        cache_ttl_seconds: int = 3600,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the provider.
        
        Args:
            use_database: Whether to use database repositories
            use_redis_cache: Whether to use Redis for caching
            redis_client: Redis client (required if use_redis_cache is True)
            async_processing: Whether to use async processing for projections
            batch_size: Batch size for async processing
            cache_ttl_seconds: Default cache TTL in seconds
            logger: Optional logger instance
        """
        self.use_database = use_database
        self.use_redis_cache = use_redis_cache
        self.redis_client = redis_client
        self.async_processing = async_processing
        self.batch_size = batch_size
        self.cache_ttl_seconds = cache_ttl_seconds
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Validate that Redis client is provided if Redis cache is enabled
        if use_redis_cache and redis_client is None:
            raise ValueError("Redis client must be provided when use_redis_cache is True")
    
    def configure(self, binder: inject.Binder) -> None:
        """
        Configure dependency injection bindings.
        
        Args:
            binder: The inject binder
        """
        # Bind base implementations
        binder.bind_to_provider(CacheRepositoryProtocol, self.provide_cache_repository)
        binder.bind_to_provider(ProjectorConfigurationRepositoryProtocol, self.provide_projector_config_repository)
        binder.bind_to_provider(CacheServiceProtocol, self.provide_cache_service)
        binder.bind_to_provider(ProjectorServiceProtocol, self.provide_projector_service)
    
    def provide_read_model_repository(
        self, model_type: Type[T], table_name: Optional[str] = None
    ) -> ReadModelRepositoryProtocol[T]:
        """
        Provide a read model repository for the specified model type.
        
        Args:
            model_type: The read model type
            table_name: Optional table name
            
        Returns:
            A repository for the specified model type
        """
        if self.use_database:
            db_provider = inject.instance(DatabaseProvider)
            return DatabaseReadModelRepository(
                model_type=model_type,
                db_provider=db_provider,
                table_name=table_name,
                logger=self.logger
            )
        else:
            return InMemoryReadModelRepository(
                model_type=model_type,
                logger=self.logger
            )
    
    def provide_projection_repository(
        self, model_type: Type[P]
    ) -> ProjectionRepositoryProtocol[P]:
        """
        Provide a projection repository for the specified model type.
        
        Args:
            model_type: The projection type
            
        Returns:
            A repository for the specified model type
        """
        return InMemoryProjectionRepository(
            model_type=model_type,
            logger=self.logger
        )
    
    def provide_query_repository(
        self, model_type: Type[Q]
    ) -> QueryRepositoryProtocol[Q]:
        """
        Provide a query repository for the specified model type.
        
        Args:
            model_type: The query type
            
        Returns:
            A repository for the specified model type
        """
        return InMemoryQueryRepository(
            model_type=model_type,
            logger=self.logger
        )
    
    def provide_cache_repository(self) -> CacheRepositoryProtocol:
        """
        Provide a cache repository.
        
        Returns:
            A cache repository
        """
        if self.use_redis_cache:
            return RedisCacheRepository(
                redis_client=self.redis_client,
                logger=self.logger
            )
        else:
            return InMemoryCacheRepository(
                logger=self.logger
            )
    
    def provide_projector_config_repository(self) -> ProjectorConfigurationRepositoryProtocol:
        """
        Provide a projector configuration repository.
        
        Returns:
            A projector configuration repository
        """
        return InMemoryProjectorConfigurationRepository(
            logger=self.logger
        )
    
    def provide_read_model_service(
        self, model_type: Type[T], table_name: Optional[str] = None
    ) -> ReadModelServiceProtocol[T]:
        """
        Provide a read model service for the specified model type.
        
        Args:
            model_type: The read model type
            table_name: Optional table name
            
        Returns:
            A service for the specified model type
        """
        repository = self.provide_read_model_repository(model_type, table_name)
        cache_service = inject.instance(CacheServiceProtocol)
        
        return ReadModelService(
            repository=repository,
            model_type=model_type,
            cache_service=cache_service,
            logger=self.logger
        )
    
    def provide_projection_service(
        self, projection_type: Type[P], read_model_type: Type[T]
    ) -> ProjectionServiceProtocol[P]:
        """
        Provide a projection service for the specified types.
        
        Args:
            projection_type: The projection type
            read_model_type: The read model type
            
        Returns:
            A projection service for the specified types
        """
        projection_repository = self.provide_projection_repository(projection_type)
        read_model_repository = self.provide_read_model_repository(read_model_type)
        
        return ProjectionService(
            projection_repository=projection_repository,
            read_model_repository=read_model_repository,
            read_model_type=read_model_type,
            projection_type=projection_type,
            logger=self.logger
        )
    
    def provide_cache_service(self) -> CacheServiceProtocol:
        """
        Provide a cache service.
        
        Returns:
            A cache service
        """
        cache_repository = inject.instance(CacheRepositoryProtocol)
        
        return CacheService(
            cache_repository=cache_repository,
            default_ttl_seconds=self.cache_ttl_seconds,
            logger=self.logger
        )
    
    def provide_query_service(
        self, query_type: Type[Q], model_type: Type[T]
    ) -> QueryServiceProtocol[Q, T]:
        """
        Provide a query service for the specified types.
        
        Args:
            query_type: The query type
            model_type: The read model type
            
        Returns:
            A query service for the specified types
        """
        repository = self.provide_read_model_repository(model_type)
        cache_service = inject.instance(CacheServiceProtocol)
        
        return QueryService(
            repository=repository,
            query_type=query_type,
            model_type=model_type,
            cache_service=cache_service,
            logger=self.logger
        )
    
    def provide_projector_service(self) -> ProjectorServiceProtocol:
        """
        Provide a projector service.
        
        Returns:
            A projector service
        """
        # Get dependencies from the container
        event_bus = inject.instance(EventBus)
        event_store = inject.instance(EventStore)
        
        # This will need to be customized for the specific projection types
        # being used, or could use a dynamic lookup mechanism
        projection_service = inject.instance(ProjectionServiceProtocol)
        projector_config_repository = inject.instance(ProjectorConfigurationRepositoryProtocol)
        
        return ProjectorService(
            event_bus=event_bus,
            event_store=event_store,
            projection_service=projection_service,
            projector_config_repository=projector_config_repository,
            async_processing=self.async_processing,
            batch_size=self.batch_size,
            logger=self.logger
        )