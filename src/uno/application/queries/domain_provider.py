"""Dependency injection provider for the Queries module."""

import logging
from functools import lru_cache

from uno.dependencies.interfaces import ServiceLifecycle
from uno.dependencies.modern_provider import ServiceProvider, get_service
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
from uno.application.queries.queries_interfaces import (
    IQueryPathRepository,
    IQueryValueRepository,
    IQueryRepository,
    IQueryPathService,
    IQueryValueService,
    IQueryService,
)
from uno.queries.filter_manager import get_filter_manager
from uno.queries.executor import get_query_executor


def configure_queries_services(container):
    """Configure Queries module services in the DI container."""
    logger = logging.getLogger("uno.queries")

    # Register repositories by interface
    container.register(IQueryPathRepository, QueryPathRepository, lifecycle=ServiceLifecycle.SCOPED)
    container.register(IQueryValueRepository, QueryValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    container.register(IQueryRepository, QueryRepository, lifecycle=ServiceLifecycle.SCOPED)

    # Register services by interface
    container.register(
        IQueryPathService,
        lambda c: QueryPathService(
            repository=c.resolve(IQueryPathRepository)
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        IQueryValueService,
        lambda c: QueryValueService(
            repository=c.resolve(IQueryValueRepository)
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        IQueryService,
        lambda c: QueryService(
            repository=c.resolve(IQueryRepository),
            query_value_service=c.resolve(IQueryValueService),
            query_path_service=c.resolve(IQueryPathService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )

    # Optionally, keep registering concrete classes for legacy compatibility (if needed)
    # container.register(QueryPathRepository, ...)
    # container.register(QueryPathService, ...)
    # etc.


