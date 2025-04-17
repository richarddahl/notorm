"""
Distributed query execution system.

This module provides a distributed query execution framework that can 
distribute queries across multiple database nodes for improved performance 
and horizontal scaling.
"""

import asyncio
import time
import logging
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Set, Callable, Tuple, TypeVar, Generic

from sqlalchemy import text, Table, Column, select, MetaData, inspect
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, AsyncConnection
from sqlalchemy.sql import Select, Executable

from uno.database.query_optimizer import (
    QueryComplexity,
    OptimizationLevel,
    QueryPlan,
    QueryStatistics,
    OptimizationConfig,
    QueryOptimizer,
)
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    EnhancedConnectionPool,
    EnhancedAsyncEnginePool,
    get_connection_manager,
)
from uno.core.errors.result import Result as OpResult, Success, Failure


class DistributionStrategy(Enum):
    """
    Strategies for distributing queries across nodes.
    
    Determines how queries and data are distributed.
    """
    
    ROUND_ROBIN = "round_robin"       # Distribute queries in round-robin fashion
    SHARD_KEY = "shard_key"           # Distribute based on a shard key
    HASH = "hash"                     # Distribute based on a hash function
    LOCALITY = "locality"             # Distribute based on data locality
    LOAD_BALANCED = "load_balanced"   # Distribute based on node load
    REPLICATED = "replicated"         # Execute on all nodes with replicated data
    CUSTOM = "custom"                 # Use custom distribution logic


class NodeRole(Enum):
    """
    Roles for database nodes in a distributed system.
    
    Determines what types of operations a node can handle.
    """
    
    PRIMARY = "primary"         # Primary node (read/write)
    REPLICA = "replica"         # Read replica (read-only)
    SHARD = "shard"             # Shard (portion of data)
    ANALYTICS = "analytics"     # Analytics node (optimized for complex queries)
    ARCHIVE = "archive"         # Archive node (historical data)


class NodeStatus(Enum):
    """
    Status of a database node.
    
    Indicates the current operational state of a node.
    """
    
    ONLINE = "online"           # Node is online and available
    OFFLINE = "offline"         # Node is offline or unavailable
    DEGRADED = "degraded"       # Node is online but degraded
    MAINTENANCE = "maintenance" # Node is in maintenance mode
    SYNCING = "syncing"         # Node is syncing data


class QueryType(Enum):
    """
    Types of database queries.
    
    Used for routing queries to appropriate nodes.
    """
    
    READ = "read"               # Read-only query
    WRITE = "write"             # Write query
    MIXED = "mixed"             # Mixed read/write query
    ANALYTICS = "analytics"     # Analytics query
    METADATA = "metadata"       # Metadata query
    SYSTEM = "system"           # System administration query


@dataclass
class DBNode:
    """
    Database node in a distributed system.
    
    Represents a single database instance.
    """
    
    # Node identity
    id: str
    name: str
    role: NodeRole
    
    # Connection info
    connection_string: str
    engine: Optional[AsyncEngine] = None
    session_factory: Optional[Callable[[], AsyncSession]] = None
    
    # Status
    status: NodeStatus = NodeStatus.OFFLINE
    last_heartbeat: float = field(default_factory=time.time)
    
    # Capabilities
    read_only: bool = False
    supports_transactions: bool = True
    supports_sharding: bool = False
    
    # Performance
    performance_score: float = 1.0  # Relative performance (higher is better)
    current_load: float = 0.0       # Current load (0.0-1.0)
    
    # Sharding
    shard_keys: List[str] = field(default_factory=list)
    shard_range: Optional[Tuple[Any, Any]] = None
    
    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def can_execute(self, query_type: QueryType) -> bool:
        """
        Check if the node can execute a query type.
        
        Args:
            query_type: The type of query
            
        Returns:
            Whether the node can execute the query
        """
        if self.status != NodeStatus.ONLINE:
            return False
        
        if self.read_only and query_type in (QueryType.WRITE, QueryType.MIXED):
            return False
        
        if query_type == QueryType.ANALYTICS and self.role != NodeRole.ANALYTICS:
            # Only analytics nodes can run analytics queries
            # (regular nodes might time out or impact performance)
            return False
        
        return True
    
    async def initialize(self) -> bool:
        """
        Initialize the node's connections.
        
        Returns:
            True if initialization was successful
        """
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            
            # Create engine
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                pool_pre_ping=True,
            )
            
            # Create session factory
            async_session_factory = sessionmaker(
                self.engine, expire_on_commit=False, class_=AsyncSession
            )
            self.session_factory = async_session_factory
            
            # Update status
            self.status = NodeStatus.ONLINE
            self.last_heartbeat = time.time()
            
            return True
            
        except Exception as e:
            logging.error(f"Error initializing node {self.name}: {e}")
            self.status = NodeStatus.OFFLINE
            return False
    
    async def check_health(self) -> bool:
        """
        Check if the node is healthy.
        
        Returns:
            True if the node is healthy
        """
        if not self.engine:
            return False
        
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
                
                # Update status
                self.status = NodeStatus.ONLINE
                self.last_heartbeat = time.time()
                
                return True
                
        except Exception as e:
            logging.error(f"Node {self.name} health check failed: {e}")
            self.status = NodeStatus.OFFLINE
            return False
    
    async def get_session(self) -> Optional[AsyncSession]:
        """
        Get a session for this node.
        
        Returns:
            AsyncSession if available, None otherwise
        """
        if self.session_factory and self.status == NodeStatus.ONLINE:
            return self.session_factory()
        return None


@dataclass
class DistributedQueryConfig:
    """
    Configuration for distributed query execution.
    
    Controls distribution strategy and execution behavior.
    """
    
    # Distribution strategy
    strategy: DistributionStrategy = DistributionStrategy.ROUND_ROBIN
    custom_distributor: Optional[Callable] = None
    
    # Sharding configuration
    shard_key: Optional[str] = None
    shard_function: Optional[Callable[[Any], str]] = None
    
    # Execution options
    parallel_execution: bool = True
    use_read_replicas: bool = True
    timeout: float = 30.0
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 0.5
    
    # Consistency options
    consistency_level: str = "eventual"  # eventual, session, strong
    include_in_flight_data: bool = False
    
    # Query transformation
    transform_queries: bool = False
    
    # Metrics collection
    collect_metrics: bool = True
    log_slow_queries: bool = True
    slow_query_threshold: float = 1.0


@dataclass
class QueryContext:
    """
    Context for a distributed query execution.
    
    Contains all information needed for query execution and coordination.
    """
    
    # Query info
    query: Union[str, Executable]
    params: Optional[Dict[str, Any]] = None
    query_type: QueryType = QueryType.READ
    shard_key_value: Optional[Any] = None
    
    # Execution context
    transaction_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    consistency_level: Optional[str] = None
    
    # Routing info
    target_nodes: List[str] = field(default_factory=list)
    preferred_node: Optional[str] = None
    
    # Execution options
    timeout: Optional[float] = None
    fetch_all: bool = True
    transform_result: bool = True
    
    # Query identification
    query_id: str = field(default_factory=lambda: hashlib.md5(str(time.time()).encode()).hexdigest())
    query_hash: Optional[str] = None
    
    # Performance tracking
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    
    def __post_init__(self):
        """Post-initialization to compute derived fields."""
        if self.query_hash is None:
            # Compute query hash for caching and tracking
            if isinstance(self.query, str):
                self.query_hash = hashlib.md5(self.query.encode()).hexdigest()
            else:
                # For SQLAlchemy Executable
                query_str = str(self.query)
                self.query_hash = hashlib.md5(query_str.encode()).hexdigest()
    
    def complete(self, execution_time: Optional[float] = None):
        """
        Mark the query as complete.
        
        Args:
            execution_time: Optional explicit execution time
        """
        self.end_time = time.time()
        if execution_time is not None:
            self.execution_time = execution_time
        else:
            self.execution_time = self.end_time - self.start_time


@dataclass
class QueryResult:
    """
    Result of a distributed query execution.
    
    Contains both result data and execution metadata.
    """
    
    # Result data
    data: Any
    node_id: str
    success: bool = True
    row_count: int = 0
    
    # Additional context
    error: Optional[Exception] = None
    query_context: Optional[QueryContext] = None
    
    # Performance stats
    execution_time: float = 0.0
    
    # Node routing info
    tried_nodes: List[str] = field(default_factory=list)
    
    @property
    def is_error(self) -> bool:
        """Check if the result is an error."""
        return not self.success or self.error is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with result details
        """
        return {
            "success": self.success,
            "node_id": self.node_id,
            "row_count": self.row_count,
            "execution_time": self.execution_time,
            "error": str(self.error) if self.error else None,
            "tried_nodes": self.tried_nodes,
        }


@dataclass
class DistributedQueryMetrics:
    """
    Metrics for distributed query execution.
    
    Tracks performance and distribution statistics.
    """
    
    # Query counts
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    
    # Node distribution
    queries_by_node: Dict[str, int] = field(default_factory=dict)
    queries_by_type: Dict[QueryType, int] = field(default_factory=dict)
    
    # Performance metrics
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    max_execution_time: float = 0.0
    slow_queries: int = 0
    
    # Retries and failovers
    total_retries: int = 0
    successful_failovers: int = 0
    
    # Distribution
    distribution_by_strategy: Dict[DistributionStrategy, int] = field(default_factory=dict)
    
    # Timeouts and errors
    timeout_errors: int = 0
    connection_errors: int = 0
    
    def record_query(self, result: QueryResult, context: QueryContext, retries: int = 0):
        """
        Record query metrics.
        
        Args:
            result: Query execution result
            context: Query execution context
            retries: Number of retries performed
        """
        # Update query counts
        self.total_queries += 1
        if result.success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        # Update node distribution
        if result.node_id not in self.queries_by_node:
            self.queries_by_node[result.node_id] = 0
        self.queries_by_node[result.node_id] += 1
        
        # Update query type distribution
        if context.query_type not in self.queries_by_type:
            self.queries_by_type[context.query_type] = 0
        self.queries_by_type[context.query_type] += 1
        
        # Update performance metrics
        self.total_execution_time += result.execution_time
        self.avg_execution_time = self.total_execution_time / self.total_queries
        
        if result.execution_time > self.max_execution_time:
            self.max_execution_time = result.execution_time
        
        # Check for slow query
        if result.execution_time > 1.0:  # 1 second threshold
            self.slow_queries += 1
        
        # Record retries
        self.total_retries += retries
        
        # Record failovers (retries with different nodes)
        if retries > 0 and result.success and len(result.tried_nodes) > 1:
            self.successful_failovers += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary representation.
        
        Returns:
            Dictionary with metrics
        """
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "queries_by_node": self.queries_by_node,
            "queries_by_type": {k.value: v for k, v in self.queries_by_type.items()},
            "avg_execution_time": self.avg_execution_time,
            "max_execution_time": self.max_execution_time,
            "slow_queries": self.slow_queries,
            "total_retries": self.total_retries,
            "successful_failovers": self.successful_failovers,
            "timeout_errors": self.timeout_errors,
            "connection_errors": self.connection_errors,
        }


class DistributedQueryManager:
    """
    Manager for distributed query execution.
    
    Coordinates query distribution, execution, and result handling across nodes.
    """
    
    def __init__(
        self,
        config: Optional[DistributedQueryConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the distributed query manager.
        
        Args:
            config: Optional configuration
            logger: Optional logger instance
        """
        self.config = config or DistributedQueryConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # Node registry
        self.nodes: Dict[str, DBNode] = {}
        
        # Node selection state
        self._current_node_index = 0
        
        # Query stats
        self.metrics = DistributedQueryMetrics()
        
        # Query optimizer
        self.optimizer = None
    
    def add_node(self, node: DBNode) -> bool:
        """
        Add a database node to the manager.
        
        Args:
            node: The database node to add
            
        Returns:
            True if the node was added successfully
        """
        if node.id in self.nodes:
            self.logger.warning(f"Node {node.id} already exists, overwriting")
        
        self.nodes[node.id] = node
        return True
    
    def remove_node(self, node_id: str) -> bool:
        """
        Remove a database node from the manager.
        
        Args:
            node_id: The ID of the node to remove
            
        Returns:
            True if the node was removed successfully
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False
    
    async def initialize_nodes(self) -> Dict[str, bool]:
        """
        Initialize all registered nodes.
        
        Returns:
            Dictionary mapping node IDs to initialization success
        """
        results = {}
        
        for node_id, node in self.nodes.items():
            results[node_id] = await node.initialize()
        
        return results
    
    async def check_node_health(self, node_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Check the health of nodes.
        
        Args:
            node_id: Optional specific node to check
            
        Returns:
            Dictionary mapping node IDs to health status
        """
        results = {}
        
        if node_id:
            # Check specific node
            if node_id in self.nodes:
                results[node_id] = await self.nodes[node_id].check_health()
            else:
                results[node_id] = False
        else:
            # Check all nodes
            for node_id, node in self.nodes.items():
                results[node_id] = await node.check_health()
        
        return results
    
    def get_available_nodes(self, query_type: QueryType) -> List[DBNode]:
        """
        Get available nodes for a query type.
        
        Args:
            query_type: The type of query
            
        Returns:
            List of available nodes
        """
        return [
            node for node in self.nodes.values()
            if node.status == NodeStatus.ONLINE and node.can_execute(query_type)
        ]
    
    def _select_node_round_robin(self, context: QueryContext) -> Optional[DBNode]:
        """
        Select a node using round-robin strategy.
        
        Args:
            context: The query context
            
        Returns:
            Selected node or None if no suitable node found
        """
        available_nodes = self.get_available_nodes(context.query_type)
        if not available_nodes:
            return None
        
        # Find the next available node
        node = available_nodes[self._current_node_index % len(available_nodes)]
        self._current_node_index += 1
        
        return node
    
    def _select_node_shard_key(self, context: QueryContext) -> Optional[DBNode]:
        """
        Select a node based on shard key.
        
        Args:
            context: The query context
            
        Returns:
            Selected node or None if no suitable node found
        """
        if not context.shard_key_value or not self.config.shard_key:
            # Fall back to round-robin if no shard key
            return self._select_node_round_robin(context)
        
        # Find a node that handles this shard key value
        for node in self.nodes.values():
            if node.status != NodeStatus.ONLINE or not node.can_execute(context.query_type):
                continue
                
            if node.supports_sharding and self.config.shard_key in node.shard_keys:
                # Check shard range if available
                if node.shard_range:
                    min_val, max_val = node.shard_range
                    if min_val <= context.shard_key_value <= max_val:
                        return node
                else:
                    # No range specified, assume this node handles all values
                    return node
        
        # No suitable node found
        return None
    
    def _select_node_hash(self, context: QueryContext) -> Optional[DBNode]:
        """
        Select a node based on hash of the shard key.
        
        Args:
            context: The query context
            
        Returns:
            Selected node or None if no suitable node found
        """
        if not context.shard_key_value:
            return self._select_node_round_robin(context)
        
        available_nodes = self.get_available_nodes(context.query_type)
        if not available_nodes:
            return None
        
        # Hash the shard key value
        if self.config.shard_function:
            node_index = self.config.shard_function(context.shard_key_value)
        else:
            # Simple hash function
            shard_key_str = str(context.shard_key_value)
            hash_value = sum(ord(c) for c in shard_key_str)
            node_index = hash_value % len(available_nodes)
        
        return available_nodes[node_index]
    
    def _select_node_load_balanced(self, context: QueryContext) -> Optional[DBNode]:
        """
        Select a node based on current load.
        
        Args:
            context: The query context
            
        Returns:
            Selected node or None if no suitable node found
        """
        available_nodes = self.get_available_nodes(context.query_type)
        if not available_nodes:
            return None
        
        # First try to find a node with less than 50% load
        low_load_nodes = [node for node in available_nodes if node.current_load < 0.5]
        if low_load_nodes:
            # Sort by load and performance score
            sorted_nodes = sorted(
                low_load_nodes,
                key=lambda n: (n.current_load, -n.performance_score)
            )
            return sorted_nodes[0]
        
        # Otherwise, find the node with the lowest load
        sorted_nodes = sorted(
            available_nodes,
            key=lambda n: (n.current_load, -n.performance_score)
        )
        return sorted_nodes[0]
    
    def _select_node_locality(self, context: QueryContext) -> Optional[DBNode]:
        """
        Select a node based on data locality.
        
        Args:
            context: The query context
            
        Returns:
            Selected node or None if no suitable node found
        """
        # This is a simplified implementation
        # In a real system, this would use data access patterns and locality awareness
        
        # Check if we have a preferred node
        if context.preferred_node and context.preferred_node in self.nodes:
            node = self.nodes[context.preferred_node]
            if node.status == NodeStatus.ONLINE and node.can_execute(context.query_type):
                return node
        
        # Check if we have any target nodes
        if context.target_nodes:
            for node_id in context.target_nodes:
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    if node.status == NodeStatus.ONLINE and node.can_execute(context.query_type):
                        return node
        
        # Fall back to round-robin
        return self._select_node_round_robin(context)
    
    def _select_node_custom(self, context: QueryContext) -> Optional[DBNode]:
        """
        Select a node using custom distributor.
        
        Args:
            context: The query context
            
        Returns:
            Selected node or None if no suitable node found
        """
        if not self.config.custom_distributor:
            return self._select_node_round_robin(context)
        
        available_nodes = self.get_available_nodes(context.query_type)
        if not available_nodes:
            return None
        
        try:
            # Call custom distributor
            selected = self.config.custom_distributor(context, available_nodes)
            if selected and isinstance(selected, DBNode):
                return selected
                
            # If custom distributor returned a node ID, find the node
            if isinstance(selected, str) and selected in self.nodes:
                node = self.nodes[selected]
                if node.status == NodeStatus.ONLINE and node.can_execute(context.query_type):
                    return node
        except Exception as e:
            self.logger.error(f"Error in custom node distributor: {e}")
        
        # Fall back to round-robin
        return self._select_node_round_robin(context)
    
    def select_node(self, context: QueryContext) -> Optional[DBNode]:
        """
        Select a node for query execution.
        
        Args:
            context: The query context
            
        Returns:
            Selected node or None if no suitable node found
        """
        # Use the appropriate strategy
        strategy = self.config.strategy
        
        if strategy == DistributionStrategy.ROUND_ROBIN:
            return self._select_node_round_robin(context)
        elif strategy == DistributionStrategy.SHARD_KEY:
            return self._select_node_shard_key(context)
        elif strategy == DistributionStrategy.HASH:
            return self._select_node_hash(context)
        elif strategy == DistributionStrategy.LOAD_BALANCED:
            return self._select_node_load_balanced(context)
        elif strategy == DistributionStrategy.LOCALITY:
            return self._select_node_locality(context)
        elif strategy == DistributionStrategy.CUSTOM:
            return self._select_node_custom(context)
        elif strategy == DistributionStrategy.REPLICATED:
            # For replicated strategy, we'll use read replicas for read queries
            if context.query_type == QueryType.READ and self.config.use_read_replicas:
                read_nodes = [
                    node for node in self.nodes.values()
                    if node.status == NodeStatus.ONLINE 
                    and node.role == NodeRole.REPLICA
                    and node.can_execute(context.query_type)
                ]
                if read_nodes:
                    # Use round-robin among read replicas
                    return read_nodes[self._current_node_index % len(read_nodes)]
            
            # Fall back to primary node for writes or if no read replicas
            primary_nodes = [
                node for node in self.nodes.values()
                if node.status == NodeStatus.ONLINE 
                and node.role == NodeRole.PRIMARY
                and node.can_execute(context.query_type)
            ]
            if primary_nodes:
                return primary_nodes[0]
        
        # If we get here, no suitable node was found
        return None
    
    async def execute_on_node(
        self,
        node: DBNode,
        context: QueryContext,
    ) -> QueryResult:
        """
        Execute a query on a specific node.
        
        Args:
            node: The node to execute on
            context: The query context
            
        Returns:
            Query result
        """
        session = None
        start_time = time.time()
        tried_nodes = [node.id]
        
        try:
            # Get a session
            session = await node.get_session()
            if not session:
                return QueryResult(
                    data=None,
                    node_id=node.id,
                    success=False,
                    error=Exception(f"Could not get session for node {node.id}"),
                    query_context=context,
                    execution_time=time.time() - start_time,
                    tried_nodes=tried_nodes,
                )
            
            # Execute the query
            if isinstance(context.query, str):
                # Execute raw SQL
                result = await session.execute(text(context.query), context.params or {})
            else:
                # Execute SQLAlchemy query
                result = await session.execute(context.query, context.params or {})
            
            # Process the result
            if context.fetch_all:
                if result.returns_rows:
                    rows = result.fetchall()
                    row_count = len(rows)
                    
                    # Transform result if requested
                    if context.transform_result:
                        # Convert to list of dictionaries
                        if hasattr(result, "keys") and callable(result.keys):
                            keys = result.keys()
                            data = [dict(zip(keys, row)) for row in rows]
                        else:
                            data = rows
                    else:
                        data = rows
                else:
                    # No rows returned (e.g., INSERT, UPDATE)
                    row_count = result.rowcount if hasattr(result, "rowcount") else 0
                    data = {"affected_rows": row_count}
            else:
                # Don't fetch all, just return the result object
                # This is useful for streaming large results
                data = result
                row_count = 0
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Update node metrics
            node.current_load = min(node.current_load + 0.1, 1.0)  # Simulate load increase
            
            # Create result
            query_result = QueryResult(
                data=data,
                node_id=node.id,
                success=True,
                row_count=row_count,
                query_context=context,
                execution_time=execution_time,
                tried_nodes=tried_nodes,
            )
            
            # Update context
            context.complete(execution_time)
            
            return query_result
            
        except asyncio.TimeoutError:
            self.metrics.timeout_errors += 1
            return QueryResult(
                data=None,
                node_id=node.id,
                success=False,
                error=asyncio.TimeoutError(f"Query timed out on node {node.id}"),
                query_context=context,
                execution_time=time.time() - start_time,
                tried_nodes=tried_nodes,
            )
            
        except Exception as e:
            if "connection" in str(e).lower():
                self.metrics.connection_errors += 1
                # Mark node as offline on connection errors
                node.status = NodeStatus.OFFLINE
            
            return QueryResult(
                data=None,
                node_id=node.id,
                success=False,
                error=e,
                query_context=context,
                execution_time=time.time() - start_time,
                tried_nodes=tried_nodes,
            )
            
        finally:
            # Clean up the session
            if session and not context.fetch_all:
                await session.close()
            
            # Simulate load decrease
            if node.current_load > 0:
                node.current_load = max(node.current_load - 0.05, 0.0)
    
    async def execute_with_retry(
        self,
        context: QueryContext,
    ) -> QueryResult:
        """
        Execute a query with retry logic.
        
        Args:
            context: The query context
            
        Returns:
            Query result
        """
        retries = 0
        tried_nodes = []
        last_error = None
        
        # Set timeout from context or config
        timeout_value = context.timeout or self.config.timeout
        
        while retries <= self.config.max_retries:
            # Select a node
            node = self.select_node(context)
            
            if not node:
                return QueryResult(
                    data=None,
                    node_id="none",
                    success=False,
                    error=Exception("No suitable node found for query"),
                    query_context=context,
                    execution_time=0.0,
                    tried_nodes=tried_nodes,
                )
            
            # Skip nodes we've already tried
            if node.id in tried_nodes:
                retries += 1
                continue
            
            # Add to tried nodes
            tried_nodes.append(node.id)
            
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.execute_on_node(node, context),
                    timeout=timeout_value
                )
                
                # Return if successful
                if result.success:
                    # Record metrics
                    self.metrics.record_query(result, context, retries)
                    return result
                
                # Store error for later
                last_error = result.error
                
            except asyncio.TimeoutError:
                self.metrics.timeout_errors += 1
                last_error = asyncio.TimeoutError(f"Query timed out on node {node.id}")
                
            except Exception as e:
                last_error = e
            
            # Increment retry count
            retries += 1
            
            # Wait before retry
            if retries <= self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * retries)
        
        # All retries failed
        execution_time = time.time() - context.start_time
        context.complete(execution_time)
        
        result = QueryResult(
            data=None,
            node_id=tried_nodes[-1] if tried_nodes else "none",
            success=False,
            error=last_error or Exception("All retries failed"),
            query_context=context,
            execution_time=execution_time,
            tried_nodes=tried_nodes,
        )
        
        # Record metrics
        self.metrics.record_query(result, context, retries)
        
        return result
    
    async def execute_query(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
        query_type: QueryType = QueryType.READ,
        shard_key_value: Optional[Any] = None,
        fetch_all: bool = True,
        transform_result: bool = True,
        timeout: Optional[float] = None,
        target_nodes: Optional[List[str]] = None,
        preferred_node: Optional[str] = None,
    ) -> QueryResult:
        """
        Execute a query on the distributed database.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            query_type: Type of query
            shard_key_value: Optional shard key value for routing
            fetch_all: Whether to fetch all results
            transform_result: Whether to transform the result
            timeout: Optional query timeout
            target_nodes: Optional list of target node IDs
            preferred_node: Optional preferred node ID
            
        Returns:
            Query result
        """
        # Create query context
        context = QueryContext(
            query=query,
            params=params,
            query_type=query_type,
            shard_key_value=shard_key_value,
            timeout=timeout,
            fetch_all=fetch_all,
            transform_result=transform_result,
            target_nodes=target_nodes or [],
            preferred_node=preferred_node,
        )
        
        # Execute the query with retry logic
        return await self.execute_with_retry(context)
    
    async def execute_on_all_nodes(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
        query_type: QueryType = QueryType.READ,
        node_filter: Optional[Callable[[DBNode], bool]] = None,
        parallel: bool = True,
    ) -> List[QueryResult]:
        """
        Execute a query on all nodes in parallel.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            query_type: Type of query
            node_filter: Optional filter for selecting nodes
            parallel: Whether to execute in parallel
            
        Returns:
            List of query results
        """
        # Get all available nodes
        available_nodes = self.get_available_nodes(query_type)
        
        # Apply node filter if provided
        if node_filter:
            available_nodes = [node for node in available_nodes if node_filter(node)]
        
        if not available_nodes:
            return []
        
        # Create contexts for each node
        contexts = []
        for node in available_nodes:
            context = QueryContext(
                query=query,
                params=params,
                query_type=query_type,
                target_nodes=[node.id],
            )
            contexts.append((node, context))
        
        # Execute on all nodes
        results = []
        
        if parallel and self.config.parallel_execution:
            # Execute in parallel
            tasks = []
            for node, context in contexts:
                task = asyncio.create_task(self.execute_on_node(node, context))
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    node_id = contexts[i][0].id
                    results[i] = QueryResult(
                        data=None,
                        node_id=node_id,
                        success=False,
                        error=result,
                        query_context=contexts[i][1],
                        execution_time=0.0,
                        tried_nodes=[node_id],
                    )
                
                # Record metrics
                self.metrics.record_query(results[i], contexts[i][1], 0)
        else:
            # Execute sequentially
            for node, context in contexts:
                result = await self.execute_on_node(node, context)
                results.append(result)
                
                # Record metrics
                self.metrics.record_query(result, context, 0)
        
        return results
    
    async def execute_query_with_optimization(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
        query_type: QueryType = QueryType.READ,
        shard_key_value: Optional[Any] = None,
    ) -> QueryResult:
        """
        Execute a query with optimization.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            query_type: Type of query
            shard_key_value: Optional shard key value for routing
            
        Returns:
            Query result
        """
        # Initialize optimizer if not already done
        if self.optimizer is None and self.config.transform_queries:
            from uno.database.query_optimizer import QueryOptimizer
            self.optimizer = QueryOptimizer()
        
        # Apply optimization if enabled
        optimized_query = query
        if self.optimizer and self.config.transform_queries:
            # For SQL strings
            if isinstance(query, str):
                # Try to rewrite the query
                rewrite_result = await self.optimizer.rewrite_query(query, params)
                if rewrite_result.is_success:
                    rewrite = rewrite_result.value
                    optimized_query = rewrite.rewritten_query
                    self.logger.info(
                        f"Query optimized with {rewrite.rewrite_type}. "
                        f"Est. improvement: {rewrite.estimated_improvement or 0:.2f}"
                    )
            
            # For SQLAlchemy queries (Executable)
            elif hasattr(query, "options"):
                # Add any optimizations specific to SQLAlchemy
                # This is simplified; in practice, you would analyze the query structure
                pass
        
        # Execute the optimized query
        return await self.execute_query(
            query=optimized_query,
            params=params,
            query_type=query_type,
            shard_key_value=shard_key_value,
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for distributed query execution.
        
        Returns:
            Dictionary with metrics
        """
        return self.metrics.to_dict()
    
    def get_node_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all nodes.
        
        Returns:
            Dictionary mapping node IDs to status information
        """
        status = {}
        
        for node_id, node in self.nodes.items():
            status[node_id] = {
                "id": node.id,
                "name": node.name,
                "role": node.role.value,
                "status": node.status.value,
                "last_heartbeat": node.last_heartbeat,
                "current_load": node.current_load,
                "performance_score": node.performance_score,
                "read_only": node.read_only,
                "supports_sharding": node.supports_sharding,
            }
        
        return status


# Helper function to create a distributed query manager
async def create_distributed_query_manager(
    connection_strings: Dict[str, str],
    config: Optional[DistributedQueryConfig] = None,
) -> DistributedQueryManager:
    """
    Create a distributed query manager with nodes from connection strings.
    
    Args:
        connection_strings: Dictionary mapping node IDs to connection strings
        config: Optional configuration
        
    Returns:
        Initialized distributed query manager
    """
    # Create manager
    manager = DistributedQueryManager(config=config)
    
    # Create and add nodes
    for node_id, conn_str in connection_strings.items():
        node = DBNode(
            id=node_id,
            name=f"Node-{node_id}",
            role=NodeRole.PRIMARY if node_id.startswith("primary") else NodeRole.REPLICA,
            connection_string=conn_str,
            read_only=not node_id.startswith("primary"),
        )
        manager.add_node(node)
    
    # Initialize nodes
    await manager.initialize_nodes()
    
    # Check health
    await manager.check_node_health()
    
    return manager


# Helper function to execute a distributed query
async def execute_distributed_query(
    query: Union[str, Executable],
    connection_strings: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    query_type: QueryType = QueryType.READ,
    config: Optional[DistributedQueryConfig] = None,
) -> QueryResult:
    """
    Execute a query on a distributed database.
    
    Args:
        query: SQL query string or SQLAlchemy executable
        connection_strings: Dictionary mapping node IDs to connection strings
        params: Optional query parameters
        query_type: Type of query
        config: Optional configuration
        
    Returns:
        Query result
    """
    # Create manager
    manager = await create_distributed_query_manager(connection_strings, config)
    
    # Execute query
    return await manager.execute_query(query, params, query_type)


# Distributed query executor class for direct use in applications
class DistributedQueryExecutor:
    """
    Executor for distributed queries.
    
    Provides a simplified interface for distributed query execution.
    """
    
    def __init__(
        self,
        manager: DistributedQueryManager,
    ):
        """
        Initialize the distributed query executor.
        
        Args:
            manager: The distributed query manager
        """
        self.manager = manager
    
    async def execute(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
        query_type: QueryType = QueryType.READ,
        shard_key_value: Optional[Any] = None,
    ) -> Any:
        """
        Execute a distributed query.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            query_type: Type of query
            shard_key_value: Optional shard key value for routing
            
        Returns:
            Query result data
            
        Raises:
            Exception: On query execution failure
        """
        result = await self.manager.execute_query(
            query=query,
            params=params,
            query_type=query_type,
            shard_key_value=shard_key_value,
        )
        
        if not result.success:
            raise result.error or Exception(f"Query execution failed on nodes: {result.tried_nodes}")
        
        return result.data
    
    async def execute_all(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
        query_type: QueryType = QueryType.READ,
    ) -> Dict[str, Any]:
        """
        Execute a query on all nodes.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            query_type: Type of query
            
        Returns:
            Dictionary mapping node IDs to result data
        """
        results = await self.manager.execute_on_all_nodes(
            query=query,
            params=params,
            query_type=query_type,
        )
        
        # Create dictionary of results
        data = {}
        for result in results:
            if result.success:
                data[result.node_id] = result.data
        
        return data
    
    async def execute_optimized(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
        query_type: QueryType = QueryType.READ,
        shard_key_value: Optional[Any] = None,
    ) -> Any:
        """
        Execute an optimized distributed query.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            query_type: Type of query
            shard_key_value: Optional shard key value for routing
            
        Returns:
            Query result data
            
        Raises:
            Exception: On query execution failure
        """
        result = await self.manager.execute_query_with_optimization(
            query=query,
            params=params,
            query_type=query_type,
            shard_key_value=shard_key_value,
        )
        
        if not result.success:
            raise result.error or Exception(f"Query execution failed on nodes: {result.tried_nodes}")
        
        return result.data
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get execution metrics.
        
        Returns:
            Dictionary with metrics
        """
        return self.manager.get_metrics()
    
    def get_node_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get node status information.
        
        Returns:
            Dictionary with node status
        """
        return self.manager.get_node_status()
    
    async def close(self) -> None:
        """
        Close the executor and release resources.
        """
        # Nothing to do for now
        pass