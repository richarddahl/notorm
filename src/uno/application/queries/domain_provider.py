"""Dependency injection provider for the Queries module."""
import logging
from functools import lru_cache
from typing import Dict, Any, Optional, cast

from uno.dependencies.interfaces import ServiceLifecycle
from uno.dependencies.modern_provider import UnoServiceProvider, get_service
from uno.queries.domain_repositories import (
    QueryPathRepository,
    QueryValueRepository,
    QueryRepository,
)
from uno.queries.domain_services import (
    QueryPathService,
    QueryValueService,
    QueryService,
)
from uno.queries.entities import Query, QueryPath, QueryValue
from uno.queries.filter_manager import get_filter_manager
from uno.queries.executor import get_query_executor


@lru_cache(maxsize=1)
def get_queries_provider() -> UnoServiceProvider:
    """Get the Queries module service provider.
    
    Returns:
        The service provider for the Queries module.
    """
    provider = UnoServiceProvider("queries")
    
    # Get logger
    logger = logging.getLogger("uno.queries")
    
    # Register repositories
    provider.register(QueryPathRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(QueryValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(QueryRepository, lifecycle=ServiceLifecycle.SCOPED)
    
    # Register services
    provider.register(
        QueryPathService,
        factory=lambda container: QueryPathService(
            repository=container.resolve(QueryPathRepository)
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        QueryValueService,
        factory=lambda container: QueryValueService(
            repository=container.resolve(QueryValueRepository)
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        QueryService,
        factory=lambda container: QueryService(
            repository=container.resolve(QueryRepository),
            query_value_service=container.resolve(QueryValueService),
            query_path_service=container.resolve(QueryPathService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider


# Convenience functions for resolving services
def get_query_path_service() -> QueryPathService:
    """Get the query path service.
    
    Returns:
        The query path service.
    """
    return get_service(QueryPathService)


def get_query_value_service() -> QueryValueService:
    """Get the query value service.
    
    Returns:
        The query value service.
    """
    return get_service(QueryValueService)


def get_query_service() -> QueryService:
    """Get the query service.
    
    Returns:
        The query service.
    """
    return get_service(QueryService)


def setup_query_module():
    """Set up the Queries module.
    
    This function ensures that the Queries module is properly set up, including
    registering the module's errors and initializing the filter manager and query
    executor.
    """
    # Ensure that the filter manager is initialized
    filter_manager = get_filter_manager()
    
    # Ensure that the query executor is initialized
    query_executor = get_query_executor()
    
    # Register the module with the service provider
    provider = get_queries_provider()
    
    return {
        "filter_manager": filter_manager,
        "query_executor": query_executor,
        "provider": provider,
    }