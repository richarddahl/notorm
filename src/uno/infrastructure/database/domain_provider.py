# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain provider for the Database module.

This module provides dependency injection configuration for the Database module,
registering repositories and services.
"""

import logging
from uno.database.entities import (
    ConnectionConfig,
    ConnectionPoolConfig,
    OptimizationConfig,
    CacheConfig,
)
from uno.database.domain_repositories import (
    SqlAlchemyDatabaseSessionRepository,
    SqlAlchemyDatabaseTransactionRepository,
    InMemoryQueryStatisticsRepository,
    InMemoryQueryPlanRepository,
    InMemoryIndexRecommendationRepository,
    InMemoryQueryCacheRepository,
    InMemoryPoolStatisticsRepository,
)
from uno.database.domain_services import (
    DatabaseManagerService,
    QueryExecutionService,
    QueryOptimizerService,
    QueryCacheService,
    TransactionService,
    ConnectionPoolService,
)
from uno.dependencies.modern_provider import ServiceLifecycle

# NOTE: All dependency registration and resolution must go through the DI container passed to
# configure_database_services. Do NOT use inject or ad hoc provider methods. For test overrides,
# use the central DI provider's configuration mechanism (e.g., uno.core.di.provider.configure_services).


def configure_database_services(container):
    """
    Configure database services in the DI container.
    All dependency registration must go through this function.
    For test overrides, use the central DI provider's configuration mechanism.
    """
    logger = logging.getLogger("uno.database")

    # Register repositories
    container.register(
        SqlAlchemyDatabaseSessionRepository,
        lambda c: SqlAlchemyDatabaseSessionRepository(
            config=c.resolve(ConnectionConfig), logger=logger
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        SqlAlchemyDatabaseTransactionRepository,
        lambda c: SqlAlchemyDatabaseTransactionRepository(
            session_repository=c.resolve(SqlAlchemyDatabaseSessionRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        InMemoryQueryStatisticsRepository, lifecycle=ServiceLifecycle.SCOPED
    )
    container.register(InMemoryQueryPlanRepository, lifecycle=ServiceLifecycle.SCOPED)
    container.register(
        InMemoryIndexRecommendationRepository, lifecycle=ServiceLifecycle.SCOPED
    )
    container.register(
        InMemoryQueryCacheRepository,
        lambda c: InMemoryQueryCacheRepository(
            max_size=c.resolve(CacheConfig).max_size
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        InMemoryPoolStatisticsRepository, lifecycle=ServiceLifecycle.SCOPED
    )

    # Register services
    container.register(
        DatabaseManagerService,
        lambda c: DatabaseManagerService(
            session_repository=c.resolve(SqlAlchemyDatabaseSessionRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        QueryCacheService,
        lambda c: QueryCacheService(
            cache_repository=c.resolve(InMemoryQueryCacheRepository),
            config=c.resolve(CacheConfig),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        QueryOptimizerService,
        lambda c: QueryOptimizerService(
            session_repository=c.resolve(SqlAlchemyDatabaseSessionRepository),
            plan_repository=c.resolve(InMemoryQueryPlanRepository),
            recommendation_repository=c.resolve(InMemoryIndexRecommendationRepository),
            config=c.resolve(OptimizationConfig),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        QueryExecutionService,
        lambda c: QueryExecutionService(
            session_repository=c.resolve(SqlAlchemyDatabaseSessionRepository),
            cache_service=c.resolve(QueryCacheService),
            optimizer_service=c.resolve(QueryOptimizerService),
            stats_repository=c.resolve(InMemoryQueryStatisticsRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        TransactionService,
        lambda c: TransactionService(
            transaction_repository=c.resolve(SqlAlchemyDatabaseTransactionRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        ConnectionPoolService,
        lambda c: ConnectionPoolService(
            pool_stats_repository=c.resolve(InMemoryPoolStatisticsRepository),
            pool_config=c.resolve(ConnectionPoolConfig),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )

    # LEGACY/CLASS-BASED PROVIDER REMOVED: All DI is now managed via ServiceProvider and get_database_provider()

    """Dependency provider for the Database module."""

    def __init__(
        self,
        connection_config: ConnectionConfig,
        pool_config: ConnectionPoolConfig | None = None,
        optimization_config: OptimizationConfig | None = None,
        cache_config: CacheConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the database provider.

        Args:
            connection_config: Database connection configuration
            pool_config: Optional connection pool configuration
            optimization_config: Optional query optimization configuration
            cache_config: Optional query cache configuration
            logger: Optional logger
        """
