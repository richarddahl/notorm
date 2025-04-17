# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain provider for the Database module.

This module provides dependency injection configuration for the Database module,
registering repositories and services.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Type, cast

import inject

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.database.entities import (
    ConnectionConfig, ConnectionPoolConfig, ConnectionPoolStrategy, 
    OptimizationConfig, OptimizationLevel, CacheConfig, CacheStrategy
)
from uno.database.domain_repositories import (
    DatabaseSessionRepositoryProtocol,
    DatabaseTransactionRepositoryProtocol,
    QueryStatisticsRepositoryProtocol,
    QueryPlanRepositoryProtocol,
    IndexRecommendationRepositoryProtocol,
    QueryCacheRepositoryProtocol,
    PoolStatisticsRepositoryProtocol,
    SqlAlchemyDatabaseSessionRepository,
    SqlAlchemyDatabaseTransactionRepository,
    InMemoryQueryStatisticsRepository,
    InMemoryQueryPlanRepository,
    InMemoryIndexRecommendationRepository,
    InMemoryQueryCacheRepository,
    InMemoryPoolStatisticsRepository
)
from uno.database.domain_services import (
    DatabaseManagerServiceProtocol,
    QueryExecutionServiceProtocol,
    QueryOptimizerServiceProtocol,
    QueryCacheServiceProtocol,
    TransactionServiceProtocol,
    ConnectionPoolServiceProtocol,
    DatabaseManagerService,
    QueryExecutionService,
    QueryOptimizerService,
    QueryCacheService,
    TransactionService,
    ConnectionPoolService
)


class DatabaseProvider:
    """Dependency provider for the Database module."""
    
    def __init__(
        self,
        connection_config: ConnectionConfig,
        pool_config: Optional[ConnectionPoolConfig] = None,
        optimization_config: Optional[OptimizationConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        logger: Optional[logging.Logger] = None
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
        self.connection_config = connection_config
        self.pool_config = pool_config or ConnectionPoolConfig()
        self.optimization_config = optimization_config or OptimizationConfig()
        self.cache_config = cache_config or CacheConfig()
        self.logger = logger or logging.getLogger(__name__)
    
    def configure(self) -> None:
        """Configure dependency injection for the Database module."""
        def config(binder: inject.Binder) -> None:
            # Configure repositories
            session_repo = SqlAlchemyDatabaseSessionRepository(
                config=self.connection_config,
                logger=self.logger
            )
            
            binder.bind(
                DatabaseSessionRepositoryProtocol,
                session_repo
            )
            
            binder.bind(
                DatabaseTransactionRepositoryProtocol,
                SqlAlchemyDatabaseTransactionRepository(
                    session_repository=session_repo,
                    logger=self.logger
                )
            )
            
            # Configure optional repositories
            query_stats_repo = InMemoryQueryStatisticsRepository()
            binder.bind(QueryStatisticsRepositoryProtocol, query_stats_repo)
            
            query_plan_repo = InMemoryQueryPlanRepository()
            binder.bind(QueryPlanRepositoryProtocol, query_plan_repo)
            
            index_recommendation_repo = InMemoryIndexRecommendationRepository()
            binder.bind(IndexRecommendationRepositoryProtocol, index_recommendation_repo)
            
            query_cache_repo = InMemoryQueryCacheRepository(max_size=self.cache_config.max_size)
            binder.bind(QueryCacheRepositoryProtocol, query_cache_repo)
            
            pool_stats_repo = InMemoryPoolStatisticsRepository()
            binder.bind(PoolStatisticsRepositoryProtocol, pool_stats_repo)
            
            # Configure services
            binder.bind(
                DatabaseManagerServiceProtocol,
                DatabaseManagerService(
                    session_repository=session_repo,
                    logger=self.logger
                )
            )
            
            # Configure query cache service
            cache_service = QueryCacheService(
                cache_repository=query_cache_repo,
                config=self.cache_config,
                logger=self.logger
            )
            binder.bind(QueryCacheServiceProtocol, cache_service)
            
            # Configure query optimizer service
            optimizer_service = QueryOptimizerService(
                session_repository=session_repo,
                plan_repository=query_plan_repo,
                recommendation_repository=index_recommendation_repo,
                config=self.optimization_config,
                logger=self.logger
            )
            binder.bind(QueryOptimizerServiceProtocol, optimizer_service)
            
            # Configure query execution service with caching and optimization
            binder.bind(
                QueryExecutionServiceProtocol,
                QueryExecutionService(
                    session_repository=session_repo,
                    cache_service=cache_service,
                    optimizer_service=optimizer_service,
                    stats_repository=query_stats_repo,
                    logger=self.logger
                )
            )
            
            # Configure transaction service
            binder.bind(
                TransactionServiceProtocol,
                TransactionService(
                    transaction_repository=inject.instance(DatabaseTransactionRepositoryProtocol),
                    logger=self.logger
                )
            )
            
            # Configure connection pool service
            binder.bind(
                ConnectionPoolServiceProtocol,
                ConnectionPoolService(
                    pool_config=self.pool_config,
                    stats_repository=pool_stats_repo,
                    engine_factory=session_repo,  # Pass session repo as engine factory
                    logger=self.logger
                )
            )
        
        inject.configure(config)
    
    @staticmethod
    def get_database_manager() -> DatabaseManagerServiceProtocol:
        """
        Get the database manager service instance.
        
        Returns:
            The database manager service instance
        """
        return inject.instance(DatabaseManagerServiceProtocol)
    
    @staticmethod
    def get_query_execution() -> QueryExecutionServiceProtocol:
        """
        Get the query execution service instance.
        
        Returns:
            The query execution service instance
        """
        return inject.instance(QueryExecutionServiceProtocol)
    
    @staticmethod
    def get_query_optimizer() -> QueryOptimizerServiceProtocol:
        """
        Get the query optimizer service instance.
        
        Returns:
            The query optimizer service instance
        """
        return inject.instance(QueryOptimizerServiceProtocol)
    
    @staticmethod
    def get_query_cache() -> QueryCacheServiceProtocol:
        """
        Get the query cache service instance.
        
        Returns:
            The query cache service instance
        """
        return inject.instance(QueryCacheServiceProtocol)
    
    @staticmethod
    def get_transaction() -> TransactionServiceProtocol:
        """
        Get the transaction service instance.
        
        Returns:
            The transaction service instance
        """
        return inject.instance(TransactionServiceProtocol)
    
    @staticmethod
    def get_connection_pool() -> ConnectionPoolServiceProtocol:
        """
        Get the connection pool service instance.
        
        Returns:
            The connection pool service instance
        """
        return inject.instance(ConnectionPoolServiceProtocol)


class TestingDatabaseProvider:
    """Testing provider for the Database module."""
    
    @staticmethod
    def configure_with_mocks(
        session_repository: Optional[DatabaseSessionRepositoryProtocol] = None,
        transaction_repository: Optional[DatabaseTransactionRepositoryProtocol] = None,
        query_stats_repository: Optional[QueryStatisticsRepositoryProtocol] = None,
        query_plan_repository: Optional[QueryPlanRepositoryProtocol] = None,
        index_recommendation_repository: Optional[IndexRecommendationRepositoryProtocol] = None,
        query_cache_repository: Optional[QueryCacheRepositoryProtocol] = None,
        pool_stats_repository: Optional[PoolStatisticsRepositoryProtocol] = None,
        database_manager_service: Optional[DatabaseManagerServiceProtocol] = None,
        query_execution_service: Optional[QueryExecutionServiceProtocol] = None,
        query_optimizer_service: Optional[QueryOptimizerServiceProtocol] = None,
        query_cache_service: Optional[QueryCacheServiceProtocol] = None,
        transaction_service: Optional[TransactionServiceProtocol] = None,
        connection_pool_service: Optional[ConnectionPoolServiceProtocol] = None
    ) -> None:
        """
        Configure the Database module with mock implementations for testing.
        
        Args:
            session_repository: Mock session repository
            transaction_repository: Mock transaction repository
            query_stats_repository: Mock query statistics repository
            query_plan_repository: Mock query plan repository
            index_recommendation_repository: Mock index recommendation repository
            query_cache_repository: Mock query cache repository
            pool_stats_repository: Mock pool statistics repository
            database_manager_service: Mock database manager service
            query_execution_service: Mock query execution service
            query_optimizer_service: Mock query optimizer service
            query_cache_service: Mock query cache service
            transaction_service: Mock transaction service
            connection_pool_service: Mock connection pool service
        """
        def config(binder: inject.Binder) -> None:
            # Bind repositories
            if session_repository:
                binder.bind(DatabaseSessionRepositoryProtocol, session_repository)
            
            if transaction_repository:
                binder.bind(DatabaseTransactionRepositoryProtocol, transaction_repository)
            
            if query_stats_repository:
                binder.bind(QueryStatisticsRepositoryProtocol, query_stats_repository)
            
            if query_plan_repository:
                binder.bind(QueryPlanRepositoryProtocol, query_plan_repository)
            
            if index_recommendation_repository:
                binder.bind(IndexRecommendationRepositoryProtocol, index_recommendation_repository)
            
            if query_cache_repository:
                binder.bind(QueryCacheRepositoryProtocol, query_cache_repository)
            
            if pool_stats_repository:
                binder.bind(PoolStatisticsRepositoryProtocol, pool_stats_repository)
            
            # Bind services
            if database_manager_service:
                binder.bind(DatabaseManagerServiceProtocol, database_manager_service)
            
            if query_execution_service:
                binder.bind(QueryExecutionServiceProtocol, query_execution_service)
            
            if query_optimizer_service:
                binder.bind(QueryOptimizerServiceProtocol, query_optimizer_service)
            
            if query_cache_service:
                binder.bind(QueryCacheServiceProtocol, query_cache_service)
            
            if transaction_service:
                binder.bind(TransactionServiceProtocol, transaction_service)
            
            if connection_pool_service:
                binder.bind(ConnectionPoolServiceProtocol, connection_pool_service)
        
        inject.configure(config)
    
    @staticmethod
    def cleanup() -> None:
        """Clean up the testing configuration."""
        inject.clear()