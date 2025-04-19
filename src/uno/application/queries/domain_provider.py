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
from uno.queries.filter_manager import get_filter_manager
from uno.queries.executor import get_query_executor


def configure_queries_services(container):
    """Configure Queries module services in the DI container."""
    logger = logging.getLogger("uno.queries")

    # Register repositories
    container.register(QueryPathRepository, lifecycle=ServiceLifecycle.SCOPED)
    container.register(QueryValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    container.register(QueryRepository, lifecycle=ServiceLifecycle.SCOPED)

    # Register services
    container.register(
        QueryPathService,
        lambda c: QueryPathService(
            repository=c.resolve(QueryPathRepository)
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        QueryValueService,
        lambda c: QueryValueService(
            repository=c.resolve(QueryValueRepository)
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        QueryService,
        lambda c: QueryService(
            repository=c.resolve(QueryRepository),
            query_value_service=c.resolve(QueryValueService),
            query_path_service=c.resolve(QueryPathService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )


