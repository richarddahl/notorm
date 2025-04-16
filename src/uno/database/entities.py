# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain entities for the Database module.

This module defines the core domain entities, value objects, and aggregates for database
operations, including connection configurations, session management, query optimization,
and transaction handling.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any, Set, Union, Type
import uuid


# Value Objects

@dataclass(frozen=True)
class DatabaseId:
    """Value object representing a unique identifier for a database resource."""
    
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("DatabaseId cannot be empty")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ConnectionString:
    """Value object representing a database connection string."""
    
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("ConnectionString cannot be empty")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TransactionId:
    """Value object representing a transaction identifier."""
    
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("TransactionId cannot be empty")
    
    @classmethod
    def generate(cls) -> 'TransactionId':
        """Generate a new unique transaction ID."""
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class QueryId:
    """Value object representing a query identifier."""
    
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("QueryId cannot be empty")
    
    @classmethod
    def generate(cls) -> 'QueryId':
        """Generate a new unique query ID."""
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


# Enums

class ConnectionPoolStrategy(Enum):
    """Strategy for connection pool management."""
    
    STANDARD = auto()      # Standard connection pooling
    ADAPTIVE = auto()      # Adaptive connection pooling that scales with load
    BOUNDED = auto()       # Bounded connection pooling with strict limits
    TRANSACTION = auto()   # Pool specialized for transaction management


class QueryComplexity(Enum):
    """Complexity classification for database queries."""
    
    SIMPLE = auto()        # Simple, well-optimized queries
    MODERATE = auto()      # Moderately complex queries
    COMPLEX = auto()       # Complex queries that may need optimization
    CRITICAL = auto()      # Critical queries that need special attention


class OptimizationLevel(Enum):
    """Level of query optimization to apply."""
    
    NONE = auto()          # No optimization
    BASIC = auto()         # Basic optimization techniques
    AGGRESSIVE = auto()    # Aggressive optimization with potential trade-offs
    MAXIMUM = auto()       # Maximum optimization regardless of trade-offs


class IndexType(Enum):
    """Type of database index."""
    
    BTREE = auto()         # B-tree index for equality and range queries
    HASH = auto()          # Hash index for equality queries
    GIN = auto()           # GIN index for full-text search
    GIST = auto()          # GiST index for geometric and custom data types
    BRIN = auto()          # BRIN index for large tables with correlated data
    CUSTOM = auto()        # Custom index type


class TransactionIsolationLevel(Enum):
    """Transaction isolation levels."""
    
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class CacheStrategy(Enum):
    """Strategy for query result caching."""
    
    TIME_BASED = auto()    # Cache with time-based expiration
    LRU = auto()           # Least Recently Used eviction strategy
    FIFO = auto()          # First In First Out eviction strategy
    ADAPTIVE = auto()      # Adaptive strategy based on query patterns


# Entities and Aggregates

@dataclass
class ConnectionConfig:
    """Configuration for database connections."""
    
    db_role: str
    db_name: str
    db_host: str
    db_port: int
    db_user_pw: str
    db_driver: str
    db_schema: Optional[str] = None
    pool_size: int = 5
    max_overflow: int = 0
    pool_timeout: int = 30
    pool_recycle: int = 90
    connect_args: Dict[str, Any] = field(default_factory=dict)
    
    def get_uri(self) -> ConnectionString:
        """
        Construct a database URI from the connection config.
        
        Returns:
            A connection string value object
        """
        import urllib.parse
        
        # URL encode the password to handle special characters
        encoded_pw = urllib.parse.quote_plus(self.db_user_pw)
        
        # Determine driver to use - strip any 'postgresql+' prefix to avoid duplication
        driver = self.db_driver
        if driver.startswith("postgresql+"):
            driver = driver.replace("postgresql+", "")
        
        # Build the connection string
        if "psycopg" in driver or "postgresql" in driver:
            # PostgreSQL URI format
            uri = f"postgresql+{driver}://{self.db_role}:{encoded_pw}@{self.db_host}:{self.db_port}/{self.db_name}"
            return ConnectionString(uri)
        else:
            # Generic SQLAlchemy URI format
            uri = f"{driver}://{self.db_role}:{encoded_pw}@{self.db_host}:{self.db_port}/{self.db_name}"
            return ConnectionString(uri)
    
    def for_admin_connection(self) -> 'ConnectionConfig':
        """
        Create a connection config for admin operations.
        
        Returns:
            A connection config suitable for administrative operations
        """
        return ConnectionConfig(
            db_role=self.db_role,
            db_name="postgres",  # Connect to postgres database
            db_host=self.db_host,
            db_port=self.db_port,
            db_user_pw=self.db_user_pw,
            db_driver=self.db_driver,
            pool_size=1,
            max_overflow=0,
            pool_timeout=10,
            pool_recycle=60
        )


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pool management."""
    
    strategy: ConnectionPoolStrategy = ConnectionPoolStrategy.STANDARD
    pool_size: int = 5
    max_overflow: int = 0
    pool_timeout: int = 30
    pool_recycle: int = 90
    pool_pre_ping: bool = True
    max_idle_time: int = 60
    health_check_interval: int = 30


@dataclass
class PoolStatistics:
    """Statistics for a connection pool."""
    
    pool_size: int
    active_connections: int
    idle_connections: int
    max_overflow: int
    overflow_count: int
    checked_out: int
    checkins: int
    checkouts: int
    connection_errors: int
    timeout_errors: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    @property
    def utilization_rate(self) -> float:
        """Calculate the pool utilization rate."""
        if self.pool_size == 0:
            return 0.0
        return self.active_connections / self.pool_size
    
    @property
    def is_under_pressure(self) -> bool:
        """Check if the pool is under pressure."""
        return self.active_connections > self.pool_size * 0.8 or self.overflow_count > 0


@dataclass
class QueryStatistics:
    """Statistics for query execution."""
    
    query_id: QueryId
    query_text: str
    execution_time: float
    row_count: int
    complexity: QueryComplexity
    start_time: datetime
    end_time: datetime
    table_scans: int = 0
    index_scans: int = 0
    temp_files: int = 0
    temp_bytes: int = 0
    
    @property
    def duration(self) -> float:
        """Calculate the execution duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def is_slow_query(self) -> bool:
        """Check if this is a slow query (over 1 second)."""
        return self.duration > 1.0


@dataclass
class QueryPlan:
    """Execution plan for a database query."""
    
    query_id: QueryId
    plan_text: str
    estimated_cost: float
    actual_cost: Optional[float] = None
    estimated_rows: int = 0
    actual_rows: Optional[int] = None
    sequential_scans: int = 0
    index_scans: int = 0
    analyze_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    @property
    def cost_accuracy(self) -> Optional[float]:
        """Calculate how accurate the cost estimation was."""
        if self.actual_cost is None:
            return None
        if self.estimated_cost == 0:
            return 0.0
        return self.actual_cost / self.estimated_cost


@dataclass
class IndexRecommendation:
    """Recommendation for database index creation."""
    
    table_name: str
    column_names: List[str]
    index_type: IndexType = IndexType.BTREE
    estimated_improvement: float = 0.0
    creation_sql: Optional[str] = None
    rationale: str = ""
    priority: int = 0  # Higher number means higher priority
    
    def to_sql(self) -> str:
        """
        Generate SQL for creating the recommended index.
        
        Returns:
            SQL statement for index creation
        """
        if self.creation_sql:
            return self.creation_sql
        
        columns = ", ".join(self.column_names)
        index_name = f"idx_{self.table_name}_{'_'.join(self.column_names)}"
        
        index_type_str = ""
        if self.index_type == IndexType.BTREE:
            index_type_str = "USING btree"
        elif self.index_type == IndexType.HASH:
            index_type_str = "USING hash"
        elif self.index_type == IndexType.GIN:
            index_type_str = "USING gin"
        elif self.index_type == IndexType.GIST:
            index_type_str = "USING gist"
        elif self.index_type == IndexType.BRIN:
            index_type_str = "USING brin"
        
        return f"CREATE INDEX {index_name} ON {self.table_name} {index_type_str} ({columns})"


@dataclass
class QueryRewrite:
    """Rewritten version of a query for optimization."""
    
    original_query: str
    rewritten_query: str
    optimization_level: OptimizationLevel
    estimated_improvement: float = 0.0
    rationale: str = ""
    verified: bool = False
    
    @property
    def has_significant_improvement(self) -> bool:
        """Check if the rewrite offers significant improvement."""
        return self.estimated_improvement > 0.2  # 20% improvement


@dataclass
class CacheKey:
    """Key for a cached query result."""
    
    query_hash: str
    parameter_hash: str
    
    @property
    def combined_key(self) -> str:
        """Get the combined cache key."""
        return f"{self.query_hash}:{self.parameter_hash}"
    
    @classmethod
    def from_query(cls, query: str, parameters: Optional[Dict[str, Any]] = None) -> 'CacheKey':
        """
        Create a cache key from a query and parameters.
        
        Args:
            query: The SQL query
            parameters: Query parameters
            
        Returns:
            A cache key
        """
        import hashlib
        
        # Hash the query
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Hash the parameters
        if parameters:
            param_str = str(sorted(parameters.items()))
            param_hash = hashlib.md5(param_str.encode()).hexdigest()
        else:
            param_hash = "empty"
        
        return cls(query_hash, param_hash)


@dataclass
class CachedResult:
    """Cached result of a database query."""
    
    key: CacheKey
    result: Any
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if the cached result has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at
    
    @property
    def age(self) -> timedelta:
        """Get the age of the cached result."""
        return datetime.now(UTC) - self.created_at
    
    def increment_hit_count(self) -> None:
        """Increment the hit count for this cached result."""
        self.hit_count += 1


@dataclass
class CacheConfig:
    """Configuration for query caching."""
    
    strategy: CacheStrategy = CacheStrategy.TIME_BASED
    ttl_seconds: int = 300  # 5 minutes
    max_size: int = 1000
    enable_adaptive_ttl: bool = False
    min_ttl_seconds: int = 60
    max_ttl_seconds: int = 3600
    
    def get_ttl_for_query(self, query: str, complexity: QueryComplexity) -> int:
        """
        Calculate TTL for a specific query based on its complexity.
        
        Args:
            query: The SQL query
            complexity: Query complexity classification
            
        Returns:
            TTL in seconds
        """
        if not self.enable_adaptive_ttl:
            return self.ttl_seconds
        
        # Adjust TTL based on query complexity
        if complexity == QueryComplexity.SIMPLE:
            return self.max_ttl_seconds
        elif complexity == QueryComplexity.MODERATE:
            return (self.min_ttl_seconds + self.max_ttl_seconds) // 2
        elif complexity == QueryComplexity.COMPLEX:
            return self.min_ttl_seconds
        elif complexity == QueryComplexity.CRITICAL:
            return self.min_ttl_seconds // 2
        
        return self.ttl_seconds


@dataclass
class CacheStatistics:
    """Statistics for query cache performance."""
    
    hits: int = 0
    misses: int = 0
    size: int = 0
    evictions: int = 0
    total_queries: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate the cache hit rate."""
        if self.total_queries == 0:
            return 0.0
        return self.hits / self.total_queries


@dataclass
class Transaction:
    """Representation of a database transaction."""
    
    id: TransactionId
    isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED
    read_only: bool = False
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    is_completed: bool = False
    is_successful: bool = False
    query_count: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate the transaction duration in seconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    def complete(self, success: bool) -> None:
        """
        Mark the transaction as complete.
        
        Args:
            success: Whether the transaction completed successfully
        """
        self.is_completed = True
        self.is_successful = success
        self.end_time = datetime.now(UTC)


@dataclass
class OptimizationConfig:
    """Configuration for query optimization."""
    
    level: OptimizationLevel = OptimizationLevel.BASIC
    enable_auto_index_recommendations: bool = True
    enable_query_rewriting: bool = True
    slow_query_threshold: float = 1.0  # seconds
    collect_statistics: bool = True
    apply_hints: bool = True


@dataclass
class OptimizerMetricsSnapshot:
    """Snapshot of optimizer metrics."""
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    query_count: int = 0
    slow_query_count: int = 0
    average_execution_time: float = 0.0
    max_execution_time: float = 0.0
    total_rows_processed: int = 0
    index_recommendations: int = 0
    query_rewrites: int = 0


# Request/Response Models (for API)

@dataclass
class ConnectionTestRequest:
    """Request for testing a database connection."""
    
    config: ConnectionConfig


@dataclass
class ConnectionTestResponse:
    """Response from testing a database connection."""
    
    success: bool
    message: str
    connection_time: float  # in milliseconds
    database_version: Optional[str] = None
    error: Optional[str] = None


@dataclass
class QueryRequest:
    """Request for executing a database query."""
    
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    use_cache: bool = False
    cache_ttl: Optional[int] = None
    optimize: bool = True


@dataclass
class QueryResponse:
    """Response from executing a database query."""
    
    success: bool
    rows: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    execution_time: float = 0.0  # in milliseconds
    cached: bool = False
    error: Optional[str] = None
    query_plan: Optional[QueryPlan] = None


@dataclass
class OptimizationRequest:
    """Request for query optimization."""
    
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    level: OptimizationLevel = OptimizationLevel.BASIC
    include_plan: bool = True
    generate_recommendations: bool = True


@dataclass
class OptimizationResponse:
    """Response from query optimization."""
    
    original_query: str
    optimized_query: Optional[str] = None
    plan_before: Optional[QueryPlan] = None
    plan_after: Optional[QueryPlan] = None
    recommendations: List[IndexRecommendation] = field(default_factory=list)
    estimated_improvement: float = 0.0  # percentage
    error: Optional[str] = None


@dataclass
class TransactionRequest:
    """Request for starting a transaction."""
    
    isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED
    read_only: bool = False
    timeout: Optional[int] = None  # in seconds


@dataclass
class TransactionResponse:
    """Response from transaction operations."""
    
    success: bool
    transaction_id: Optional[TransactionId] = None
    error: Optional[str] = None