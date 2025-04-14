# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Database package for the Uno framework.

This package provides database connectivity, ORM integration, and session management.
"""

# Import the enhanced connection pool components
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    ConnectionPoolStrategy,
    EnhancedConnectionPool,
    EnhancedAsyncEnginePool,
    EnhancedAsyncConnectionManager,
    get_connection_manager,
    enhanced_async_engine,
    enhanced_async_connection,
)

# Import the enhanced pool session components
from uno.database.enhanced_pool_session import (
    SessionPoolConfig,
    EnhancedPooledSessionFactory,
    EnhancedPooledSessionContext,
    enhanced_pool_session,
    EnhancedPooledSessionOperationGroup,
)

# Import base session utilities
from uno.database.session import (
    AsyncSessionFactory,
    AsyncSessionContext,
    async_session,
)

# Import enhanced session utilities
from uno.database.enhanced_session import (
    EnhancedAsyncSessionFactory,
    EnhancedAsyncSessionContext,
    enhanced_async_session,
    SessionOperationGroup,
)

# Import pooled session utilities
from uno.database.pooled_session import (
    PooledAsyncSessionFactory,
    PooledAsyncSessionContext,
    pooled_async_session,
    PooledSessionOperationGroup,
)

# Import query cache components
from uno.database.query_cache import (
    CacheBackend,
    CacheStrategy,
    QueryCacheConfig,
    QueryCacheStats,
    QueryCacheKey,
    CachedResult,
    QueryCache,
    cached,
    cached_query,
    get_named_cache,
    set_default_cache,
    clear_all_caches,
)

# Import query optimizer components
from uno.database.query_optimizer import (
    QueryComplexity,
    OptimizationLevel,
    IndexType,
    QueryPlan,
    IndexRecommendation,
    QueryRewrite,
    QueryStatistics,
    OptimizationConfig,
    QueryOptimizer,
    optimize_query,
    optimized_query,
)

# Import PostgreSQL-specific optimizer components
from uno.database.pg_optimizer_strategies import (
    PgIndexRecommendation,
    PgOptimizationStrategies,
    PgQueryOptimizer,
    add_pg_strategies,
    create_pg_optimizer,
)

# Import optimizer metrics components
from uno.database.optimizer_metrics import (
    OptimizerMetricsSnapshot,
    OptimizerMetricsCollector,
    OptimizerMetricsMiddleware,
    track_query_performance,
    with_query_metrics,
    get_metrics_collector,
    set_metrics_collector,
    collect_optimizer_metrics,
)

# Import database configuration
from uno.database.config import ConnectionConfig

# Import DB manager
from uno.database.db_manager import DBManager

# Import error types
from uno.database.errors import (
    DatabaseErrorCode,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    DatabaseConnectionPoolExhaustedError,
    DatabaseQueryError,
    DatabaseQueryTimeoutError,
    DatabaseQuerySyntaxError,
    DatabaseTransactionError,
    DatabaseTransactionRollbackError,
    DatabaseTransactionConflictError,
    DatabaseIntegrityError,
    DatabaseUniqueViolationError,
    DatabaseForeignKeyViolationError,
    DatabaseResourceNotFoundError,
    DatabaseResourceAlreadyExistsError,
    DatabaseTableNotFoundError,
    DatabaseColumnNotFoundError,
    DatabaseSessionError,
    DatabaseSessionExpiredError,
    DatabaseConfigError,
    DatabaseOperationalError,
    DatabaseNotSupportedError,
    register_database_errors,
)

# Register database errors
register_database_errors()

__all__ = [
    # Enhanced connection pool
    'ConnectionPoolConfig',
    'ConnectionPoolStrategy',
    'EnhancedConnectionPool',
    'EnhancedAsyncEnginePool',
    'EnhancedAsyncConnectionManager',
    'get_connection_manager',
    'enhanced_async_engine',
    'enhanced_async_connection',
    
    # Enhanced pool session
    'SessionPoolConfig',
    'EnhancedPooledSessionFactory',
    'EnhancedPooledSessionContext',
    'enhanced_pool_session',
    'EnhancedPooledSessionOperationGroup',
    
    # Base session
    'AsyncSessionFactory',
    'AsyncSessionContext',
    'async_session',
    
    # Enhanced session
    'EnhancedAsyncSessionFactory',
    'EnhancedAsyncSessionContext',
    'enhanced_async_session',
    'SessionOperationGroup',
    
    # Pooled session
    'PooledAsyncSessionFactory',
    'PooledAsyncSessionContext',
    'pooled_async_session',
    'PooledSessionOperationGroup',
    
    # Query cache
    'CacheBackend',
    'CacheStrategy',
    'QueryCacheConfig',
    'QueryCacheStats',
    'QueryCacheKey',
    'CachedResult',
    'QueryCache',
    'cached',
    'cached_query',
    'get_named_cache',
    'set_default_cache',
    'clear_all_caches',
    
    # Query optimizer
    'QueryComplexity',
    'OptimizationLevel',
    'IndexType',
    'QueryPlan',
    'IndexRecommendation',
    'QueryRewrite',
    'QueryStatistics',
    'OptimizationConfig',
    'QueryOptimizer',
    'optimize_query',
    'optimized_query',
    
    # PostgreSQL specific optimizer
    'PgIndexRecommendation',
    'PgOptimizationStrategies',
    'PgQueryOptimizer',
    'add_pg_strategies',
    'create_pg_optimizer',
    
    # Optimizer metrics
    'OptimizerMetricsSnapshot',
    'OptimizerMetricsCollector',
    'OptimizerMetricsMiddleware',
    'track_query_performance',
    'with_query_metrics',
    'get_metrics_collector',
    'set_metrics_collector',
    'collect_optimizer_metrics',
    
    # Configuration
    'ConnectionConfig',
    
    # DB Manager
    'DBManager',
    
    # Error types
    'DatabaseErrorCode',
    'DatabaseConnectionError',
    'DatabaseConnectionTimeoutError',
    'DatabaseConnectionPoolExhaustedError',
    'DatabaseQueryError',
    'DatabaseQueryTimeoutError',
    'DatabaseQuerySyntaxError',
    'DatabaseTransactionError',
    'DatabaseTransactionRollbackError',
    'DatabaseTransactionConflictError',
    'DatabaseIntegrityError',
    'DatabaseUniqueViolationError',
    'DatabaseForeignKeyViolationError',
    'DatabaseResourceNotFoundError',
    'DatabaseResourceAlreadyExistsError',
    'DatabaseTableNotFoundError',
    'DatabaseColumnNotFoundError',
    'DatabaseSessionError',
    'DatabaseSessionExpiredError',
    'DatabaseConfigError',
    'DatabaseOperationalError',
    'DatabaseNotSupportedError',
]