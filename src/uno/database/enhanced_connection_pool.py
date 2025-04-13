"""
Enhanced connection pool for high-performance database operations.

This module provides an enhanced connection pool with advanced features:
- Dynamic pool sizing based on load
- Intelligent connection allocation and lifecycle management
- Comprehensive health checking and circuit breaking
- Detailed metrics collection and monitoring
- Connection pooling strategies for different workloads
"""

from typing import TypeVar, Generic, Dict, List, Any, Optional, Callable, Awaitable, Union, cast, Set, Tuple
import asyncio
import logging
import time
import contextlib
import uuid
from enum import Enum
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError

from uno.database.config import ConnectionConfig
from uno.core.resources import (
    ConnectionPool,
    CircuitBreaker,
    ResourceRegistry,
    get_resource_registry,
    managed_resource,
)
from uno.core.async_utils import (
    timeout,
    AsyncLock,
    Limiter,
    TaskGroup,
)
from uno.core.async_integration import (
    cancellable,
    retry,
    AsyncCache,
)
from uno.settings import uno_settings


T = TypeVar('T')


class ConnectionPoolStrategy(Enum):
    """
    Strategies for connection pool behavior.
    
    Different strategies optimize for different workloads:
    - BALANCED: Default balanced approach
    - HIGH_THROUGHPUT: Optimized for high query throughput
    - LOW_LATENCY: Optimized for minimal latency
    - DYNAMIC: Automatically adjusts based on load
    """
    
    BALANCED = "balanced"
    HIGH_THROUGHPUT = "high_throughput"
    LOW_LATENCY = "low_latency"
    DYNAMIC = "dynamic"


@dataclass
class ConnectionPoolConfig:
    """
    Configuration for enhanced connection pool.
    
    Advanced configuration options for optimizing connection pool behavior.
    """
    
    # Pool sizing
    initial_size: int = 5
    min_size: int = 2
    max_size: int = 20
    target_free_connections: int = 3
    
    # Connection lifecycle
    idle_timeout: float = 300.0  # 5 minutes
    max_lifetime: float = 3600.0  # 1 hour
    connection_timeout: float = 10.0  # 10 seconds
    
    # Pool behavior
    strategy: ConnectionPoolStrategy = ConnectionPoolStrategy.BALANCED
    allow_overflow: bool = True
    max_overflow: int = 5
    
    # Health checking
    validation_interval: float = 60.0
    failover_enabled: bool = True
    
    # Dynamic scaling
    dynamic_scaling_enabled: bool = True
    scale_up_threshold: float = 0.8  # Scale up when 80% utilized
    scale_down_threshold: float = 0.3  # Scale down when below 30% utilized
    scaling_cool_down: float = 30.0  # Minimum time between scaling operations
    
    # Retry/backoff
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    
    # Circuit breaking
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery: float = 30.0
    health_check_interval: float = 10.0
    
    # Miscellaneous
    log_connections: bool = False
    stats_enabled: bool = True
    stats_emit_interval: float = 60.0


@dataclass
class ConnectionMetrics:
    """
    Metrics for a single database connection.
    
    Tracks performance and usage statistics for a connection.
    """
    
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    last_validated_at: float = field(default_factory=time.time)
    usage_count: int = 0
    error_count: int = 0
    query_count: int = 0
    total_query_time: float = 0.0
    max_query_time: float = 0.0
    validation_count: int = 0
    validation_failures: int = 0
    reset_count: int = 0
    transaction_count: int = 0
    transaction_rollbacks: int = 0
    
    def update_usage(self) -> None:
        """Update usage metrics when connection is used."""
        self.last_used_at = time.time()
        self.usage_count += 1
    
    def record_query(self, duration: float) -> None:
        """Record a query execution."""
        self.query_count += 1
        self.total_query_time += duration
        self.max_query_time = max(self.max_query_time, duration)
    
    def record_error(self) -> None:
        """Record a connection error."""
        self.error_count += 1
    
    def record_validation(self, success: bool) -> None:
        """Record a connection validation."""
        self.validation_count += 1
        self.last_validated_at = time.time()
        if not success:
            self.validation_failures += 1
    
    def record_reset(self) -> None:
        """Record a connection reset."""
        self.reset_count += 1
    
    def record_transaction(self, success: bool) -> None:
        """Record a transaction."""
        self.transaction_count += 1
        if not success:
            self.transaction_rollbacks += 1
    
    @property
    def age(self) -> float:
        """Get the age of the connection in seconds."""
        return time.time() - self.created_at
    
    @property
    def idle_time(self) -> float:
        """Get the idle time of the connection in seconds."""
        return time.time() - self.last_used_at
    
    @property
    def avg_query_time(self) -> float:
        """Get the average query time in seconds."""
        if self.query_count == 0:
            return 0.0
        return self.total_query_time / self.query_count
    
    @property
    def validation_failure_rate(self) -> float:
        """Get the validation failure rate."""
        if self.validation_count == 0:
            return 0.0
        return self.validation_failures / self.validation_count
    
    @property
    def rollback_rate(self) -> float:
        """Get the transaction rollback rate."""
        if self.transaction_count == 0:
            return 0.0
        return self.transaction_rollbacks / self.transaction_count


@dataclass
class PoolMetrics:
    """
    Comprehensive metrics for a connection pool.
    
    Tracks performance, utilization, and health statistics.
    """
    
    # General stats
    created_at: float = field(default_factory=time.time)
    connections_created: int = 0
    connections_closed: int = 0
    connection_errors: int = 0
    validation_failures: int = 0
    
    # Pool stats
    current_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    overflow_connections: int = 0
    pending_acquisitions: int = 0
    wait_time_total: float = 0.0
    wait_count: int = 0
    
    # Health stats
    health_check_count: int = 0
    health_check_failures: int = 0
    circuit_breaker_trips: int = 0
    circuit_breaker_resets: int = 0
    
    # Timing stats
    last_scaling_time: Optional[float] = None
    max_wait_time: float = 0.0
    
    # Connection stats
    connection_metrics: Dict[str, ConnectionMetrics] = field(default_factory=dict)
    
    # Load stats
    load_samples: List[float] = field(default_factory=list)
    load_sample_times: List[float] = field(default_factory=list)
    
    def record_connection_created(self, conn_id: str) -> None:
        """Record a connection creation."""
        self.connections_created += 1
        self.current_size += 1
        self.connection_metrics[conn_id] = ConnectionMetrics()
    
    def record_connection_closed(self, conn_id: str) -> None:
        """Record a connection closure."""
        self.connections_closed += 1
        self.current_size = max(0, self.current_size - 1)
        self.connection_metrics.pop(conn_id, None)
    
    def record_connection_error(self) -> None:
        """Record a connection error."""
        self.connection_errors += 1
    
    def record_validation_failure(self, conn_id: str) -> None:
        """Record a validation failure."""
        self.validation_failures += 1
        if conn_id in self.connection_metrics:
            self.connection_metrics[conn_id].record_validation(False)
    
    def record_validation_success(self, conn_id: str) -> None:
        """Record a validation success."""
        if conn_id in self.connection_metrics:
            self.connection_metrics[conn_id].record_validation(True)
    
    def record_connection_checkout(self, conn_id: str) -> None:
        """Record a connection checkout."""
        self.active_connections += 1
        self.idle_connections = max(0, self.idle_connections - 1)
        if conn_id in self.connection_metrics:
            self.connection_metrics[conn_id].update_usage()
    
    def record_connection_checkin(self, conn_id: str) -> None:
        """Record a connection checkin."""
        self.active_connections = max(0, self.active_connections - 1)
        self.idle_connections += 1
    
    def record_wait_time(self, wait_time: float) -> None:
        """Record connection acquisition wait time."""
        self.wait_time_total += wait_time
        self.wait_count += 1
        self.max_wait_time = max(self.max_wait_time, wait_time)
    
    def record_health_check(self, success: bool) -> None:
        """Record a health check."""
        self.health_check_count += 1
        if not success:
            self.health_check_failures += 1
    
    def record_circuit_breaker_trip(self) -> None:
        """Record a circuit breaker trip."""
        self.circuit_breaker_trips += 1
    
    def record_circuit_breaker_reset(self) -> None:
        """Record a circuit breaker reset."""
        self.circuit_breaker_resets += 1
    
    def record_scaling(self) -> None:
        """Record a scaling operation."""
        self.last_scaling_time = time.time()
    
    def record_query(self, conn_id: str, duration: float) -> None:
        """Record a query execution."""
        if conn_id in self.connection_metrics:
            self.connection_metrics[conn_id].record_query(duration)
    
    def record_load_sample(self, load: float) -> None:
        """Record a load sample."""
        now = time.time()
        self.load_samples.append(load)
        self.load_sample_times.append(now)
        
        # Trim old samples (keep last hour)
        while self.load_sample_times and now - self.load_sample_times[0] > 3600:
            self.load_samples.pop(0)
            self.load_sample_times.pop(0)
    
    def get_average_load(self, window: float = 300.0) -> float:
        """
        Get the average load over a time window.
        
        Args:
            window: Time window in seconds (default: 5 minutes)
            
        Returns:
            Average load (0.0-1.0)
        """
        if not self.load_samples:
            return 0.0
        
        now = time.time()
        recent_samples = [
            load for load, sample_time in zip(self.load_samples, self.load_sample_times)
            if now - sample_time <= window
        ]
        
        if not recent_samples:
            return 0.0
        
        return sum(recent_samples) / len(recent_samples)
    
    def get_current_load(self) -> float:
        """
        Get the current load of the pool.
        
        Returns:
            Current load (0.0-1.0)
        """
        if self.current_size == 0:
            return 0.0
        return self.active_connections / self.current_size
    
    @property
    def avg_wait_time(self) -> float:
        """Get the average wait time in seconds."""
        if self.wait_count == 0:
            return 0.0
        return self.wait_time_total / self.wait_count
    
    @property
    def uptime(self) -> float:
        """Get the uptime in seconds."""
        return time.time() - self.created_at
    
    @property
    def health_check_failure_rate(self) -> float:
        """Get the health check failure rate."""
        if self.health_check_count == 0:
            return 0.0
        return self.health_check_failures / self.health_check_count
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the pool metrics.
        
        Returns:
            Dictionary of summarized metrics
        """
        return {
            "size": {
                "current": self.current_size,
                "active": self.active_connections,
                "idle": self.idle_connections,
                "total_created": self.connections_created,
                "total_closed": self.connections_closed,
            },
            "health": {
                "validation_failures": self.validation_failures,
                "connection_errors": self.connection_errors,
                "health_check_failure_rate": self.health_check_failure_rate,
                "circuit_breaker_trips": self.circuit_breaker_trips,
            },
            "performance": {
                "avg_wait_time": self.avg_wait_time,
                "max_wait_time": self.max_wait_time,
                "current_load": self.get_current_load(),
                "avg_load_5m": self.get_average_load(300.0),
                "avg_load_15m": self.get_average_load(900.0),
            },
            "uptime": self.uptime,
        }


class EnhancedConnectionPool(Generic[T]):
    """
    Enhanced connection pool with advanced features.
    
    Features:
    - Dynamic pool sizing based on load
    - Intelligent connection allocation and lifecycle management
    - Comprehensive health checking and circuit breaking
    - Detailed metrics collection and monitoring
    - Connection pooling strategies for different workloads
    """
    
    def __init__(
        self,
        name: str,
        factory: Callable[[], Awaitable[T]],
        close_func: Callable[[T], Awaitable[None]],
        validate_func: Optional[Callable[[T], Awaitable[bool]]] = None,
        reset_func: Optional[Callable[[T], Awaitable[None]]] = None,
        config: Optional[ConnectionPoolConfig] = None,
        resource_registry: Optional[ResourceRegistry] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced connection pool.
        
        Args:
            name: Name of the pool for identification
            factory: Factory function to create connections
            close_func: Function to close connections
            validate_func: Function to validate connections
            reset_func: Function to reset connections
            config: Pool configuration
            resource_registry: Resource registry for registration
            logger: Logger instance
        """
        self.name = name
        self.factory = factory
        self.close_func = close_func
        self.validate_func = validate_func
        self.reset_func = reset_func
        self.config = config or ConnectionPoolConfig()
        self.resource_registry = resource_registry or get_resource_registry()
        self.logger = logger or logging.getLogger(__name__)
        
        # Connection storage
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._available_conn_ids: Set[str] = set()
        self._pending_acquisitions: int = 0
        
        # Synchronization
        self._pool_lock = AsyncLock()
        self._connection_available = asyncio.Event()
        self._maintenance_complete = asyncio.Event()
        self._scaling_lock = AsyncLock()
        
        # State
        self._closed = False
        self._started = False
        self._circuit_breaker: Optional[CircuitBreaker] = None
        
        # Tasks
        self._maintenance_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._stats_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = PoolMetrics()
        
        # Cache for connection validation results
        self._validation_cache = AsyncCache[str, bool](
            ttl=min(30.0, self.config.validation_interval / 2),
            logger=self.logger,
        )
    
    async def start(self) -> None:
        """
        Start the connection pool.
        
        Initializes the pool with the initial number of connections
        and starts maintenance tasks.
        """
        if self._closed:
            raise RuntimeError(f"Connection pool {self.name} is closed")
        
        if self._started:
            return
        
        self._started = True
        
        # Create circuit breaker if not already created
        if self._circuit_breaker is None:
            await self._create_circuit_breaker()
        
        # Initialize connections
        try:
            await self._initialize_connections()
        except Exception as e:
            self.logger.error(f"Error initializing connections for pool {self.name}: {str(e)}")
            raise
        
        # Start maintenance task
        self._maintenance_task = asyncio.create_task(
            self._maintenance_loop(),
            name=f"{self.name}_maintenance"
        )
        
        # Start health check task
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name=f"{self.name}_health_check"
        )
        
        # Start stats task if enabled
        if self.config.stats_enabled:
            self._stats_task = asyncio.create_task(
                self._stats_loop(),
                name=f"{self.name}_stats"
            )
        
        # Register with resource registry
        await self.resource_registry.register(
            f"enhanced_pool_{self.name}",
            self
        )
        
        self.logger.info(
            f"Started enhanced connection pool {self.name} with "
            f"initial_size={self.config.initial_size}, "
            f"min_size={self.config.min_size}, "
            f"max_size={self.config.max_size}, "
            f"strategy={self.config.strategy.value}"
        )
    
    async def _create_circuit_breaker(self) -> None:
        """
        Create a circuit breaker for the pool.
        """
        self._circuit_breaker = CircuitBreaker(
            name=f"db_circuit_{self.name}",
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery,
            logger=self.logger,
        )
        
        # Register with resource registry
        await self.resource_registry.register(
            f"db_circuit_{self.name}",
            self._circuit_breaker
        )
    
    async def _initialize_connections(self) -> None:
        """
        Initialize the pool with the initial number of connections.
        """
        # Reset metrics
        self.metrics = PoolMetrics()
        
        # Clear state
        async with self._pool_lock:
            self._connections = {}
            self._available_conn_ids = set()
            self._pending_acquisitions = 0
        
        # Create initial connections
        initial_size = self.config.initial_size
        
        # Create in batch for efficiency
        async with TaskGroup(name=f"{self.name}_init") as group:
            for _ in range(initial_size):
                group.create_task(self._add_connection())
        
        # Set events
        self._connection_available.set()
        self._maintenance_complete.set()
    
    async def _add_connection(self) -> Optional[str]:
        """
        Add a new connection to the pool.
        
        Returns:
            Connection ID if successful, None otherwise
        """
        # Check if the pool is closed
        if self._closed:
            return None
            
        # Check if we're at max capacity
        async with self._pool_lock:
            current_size = len(self._connections)
            if current_size >= self.config.max_size:
                if not self.config.allow_overflow:
                    return None
                    
                overflow = current_size - self.config.max_size
                if overflow >= self.config.max_overflow:
                    return None
        
        try:
            # Create new connection with circuit breaker protection
            connection = await self._create_connection()
            
            # Add to pool
            conn_id = str(uuid.uuid4())
            now = time.time()
            
            async with self._pool_lock:
                self._connections[conn_id] = {
                    "connection": connection,
                    "created_at": now,
                    "last_used": now,
                    "last_validated": now,
                    "in_use": False,
                }
                self._available_conn_ids.add(conn_id)
                
                # Update metrics
                self.metrics.record_connection_created(conn_id)
                
                # Adjust size determination
                if len(self._connections) > self.config.max_size:
                    self.metrics.overflow_connections += 1
                
                # Set event if we have available connections
                if self._available_conn_ids:
                    self._connection_available.set()
                
                if self.config.log_connections:
                    self.logger.debug(
                        f"Added connection {conn_id} to pool {self.name}, "
                        f"current size: {len(self._connections)}"
                    )
            
            return conn_id
            
        except Exception as e:
            self.metrics.record_connection_error()
            self.logger.error(f"Error creating connection for pool {self.name}: {str(e)}")
            return None
    
    async def _create_connection(self) -> T:
        """
        Create a new connection with circuit breaker protection.
        
        Returns:
            A new connection
            
        Raises:
            Exception: If connection creation fails
        """
        # Use circuit breaker if available
        if self._circuit_breaker:
            try:
                with contextlib.suppress(asyncio.TimeoutError):
                    async with timeout(self.config.connection_timeout):
                        return await self._circuit_breaker(self.factory)
            except Exception as e:
                self.metrics.record_connection_error()
                self.logger.error(
                    f"Error creating connection for pool {self.name} with circuit breaker: {str(e)}"
                )
                raise
        
        # Otherwise create directly with timeout
        with contextlib.suppress(asyncio.TimeoutError):
            async with timeout(self.config.connection_timeout):
                return await self.factory()
    
    async def _close_connection(self, conn_id: str) -> None:
        """
        Close a connection and remove it from the pool.
        
        Args:
            conn_id: ID of the connection to close
        """
        connection = None
        
        # Remove from pool
        async with self._pool_lock:
            if conn_id in self._connections:
                connection = self._connections[conn_id]["connection"]
                del self._connections[conn_id]
                self._available_conn_ids.discard(conn_id)
                
                # Update metrics
                self.metrics.record_connection_closed(conn_id)
                
                if self.config.log_connections:
                    self.logger.debug(
                        f"Removed connection {conn_id} from pool {self.name}, "
                        f"current size: {len(self._connections)}"
                    )
        
        # Close connection outside the lock
        if connection:
            try:
                await self.close_func(connection)
            except Exception as e:
                self.logger.warning(f"Error closing connection {conn_id}: {str(e)}")
    
    async def _validate_connection(self, conn_id: str) -> bool:
        """
        Validate a connection.
        
        Args:
            conn_id: ID of the connection to validate
            
        Returns:
            True if the connection is valid, False otherwise
        """
        if not self.validate_func:
            return True
        
        # Check cache first
        cache_key = f"validation_{conn_id}"
        
        # Try to get from cache
        cached_result = await self._validation_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        connection = None
        
        # Get the connection
        async with self._pool_lock:
            if conn_id not in self._connections:
                return False
                
            conn_info = self._connections[conn_id]
            connection = conn_info["connection"]
        
        # Validate the connection
        try:
            # Set a timeout to prevent hanging
            with contextlib.suppress(asyncio.TimeoutError):
                async with timeout(self.config.connection_timeout):
                    result = await self.validate_func(connection)
            
            # Update metrics
            if result:
                self.metrics.record_validation_success(conn_id)
            else:
                self.metrics.record_validation_failure(conn_id)
            
            # Update cache
            await self._validation_cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            self.metrics.record_validation_failure(conn_id)
            self.logger.warning(f"Error validating connection {conn_id}: {str(e)}")
            
            # Update cache with failure
            await self._validation_cache.set(cache_key, False)
            
            return False
    
    async def _reset_connection(self, conn_id: str) -> bool:
        """
        Reset a connection to a clean state.
        
        Args:
            conn_id: ID of the connection to reset
            
        Returns:
            True if the reset was successful, False otherwise
        """
        if not self.reset_func:
            return True
        
        connection = None
        
        # Get the connection
        async with self._pool_lock:
            if conn_id not in self._connections:
                return False
                
            conn_info = self._connections[conn_id]
            connection = conn_info["connection"]
        
        # Reset the connection
        try:
            # Set a timeout to prevent hanging
            with contextlib.suppress(asyncio.TimeoutError):
                async with timeout(self.config.connection_timeout):
                    await self.reset_func(connection)
            
            # Update connection metrics
            if conn_id in self.metrics.connection_metrics:
                self.metrics.connection_metrics[conn_id].record_reset()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error resetting connection {conn_id}: {str(e)}")
            return False
    
    async def _health_check(self) -> bool:
        """
        Perform a health check on the pool.
        
        Returns:
            True if the pool is healthy, False otherwise
        """
        healthy = True
        
        try:
            # Check we can create a connection
            connection = await self._create_connection()
            
            # Validate the connection
            if self.validate_func:
                valid = await self.validate_func(connection)
                if not valid:
                    healthy = False
            
            # Close the connection
            await self.close_func(connection)
            
        except Exception as e:
            self.logger.warning(f"Health check failed for pool {self.name}: {str(e)}")
            healthy = False
        
        # Update metrics
        self.metrics.record_health_check(healthy)
        
        return healthy
    
    async def _maintenance_loop(self) -> None:
        """
        Maintenance loop for the connection pool.
        
        Periodically:
        - Removes expired connections
        - Validates idle connections
        - Maintains minimum pool size
        """
        try:
            while not self._closed:
                # Signal maintenance is starting
                self._maintenance_complete.clear()
                
                # Perform maintenance
                await self._perform_maintenance()
                
                # Signal maintenance is complete
                self._maintenance_complete.set()
                
                # Sleep until next maintenance cycle, but check for pool closure
                for _ in range(int(min(30.0, self.config.validation_interval / 2) * 2)):
                    if self._closed:
                        break
                    await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            # Normal task cancellation during shutdown
            pass
            
        except Exception as e:
            self.logger.error(
                f"Unexpected error in maintenance loop for pool {self.name}: {str(e)}",
                exc_info=True
            )
    
    async def _health_check_loop(self) -> None:
        """
        Health check loop for the connection pool.
        
        Periodically checks the health of the pool and triggers circuit breaker if needed.
        """
        try:
            while not self._closed:
                # Perform health check
                healthy = await self._health_check()
                
                if not healthy and self._circuit_breaker:
                    # Trigger circuit breaker if configured
                    if self.config.failover_enabled:
                        if self._circuit_breaker.state.is_closed:
                            # Track metric
                            self.metrics.record_circuit_breaker_trip()
                            
                            # Force circuit breaker to open to protect resources
                            await self._circuit_breaker._record_failure()
                            await self._circuit_breaker._record_failure()
                            await self._circuit_breaker._record_failure()
                            await self._circuit_breaker._record_failure()
                            await self._circuit_breaker._record_failure()
                
                # Sleep until next health check, but check for pool closure
                for _ in range(int(self.config.health_check_interval * 2)):
                    if self._closed:
                        break
                    await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            # Normal task cancellation during shutdown
            pass
            
        except Exception as e:
            self.logger.error(
                f"Unexpected error in health check loop for pool {self.name}: {str(e)}",
                exc_info=True
            )
    
    async def _stats_loop(self) -> None:
        """
        Statistics collection loop for the connection pool.
        
        Periodically:
        - Collects and logs pool metrics
        - Updates load statistics
        """
        try:
            while not self._closed:
                # Update load statistics
                async with self._pool_lock:
                    current_load = self.metrics.get_current_load()
                    self.metrics.record_load_sample(current_load)
                    
                    # Update pending acquisitions count in metrics
                    self.metrics.pending_acquisitions = self._pending_acquisitions
                
                # Log statistics if configured
                if self.config.stats_enabled:
                    summary = self.metrics.get_summary()
                    self.logger.debug(
                        f"Pool {self.name} stats: "
                        f"size={summary['size']['current']}, "
                        f"active={summary['size']['active']}, "
                        f"idle={summary['size']['idle']}, "
                        f"load={summary['performance']['current_load']:.2f}"
                    )
                
                # Sleep until next stats collection, but check for pool closure
                for _ in range(int(self.config.stats_emit_interval * 2)):
                    if self._closed:
                        break
                    await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            # Normal task cancellation during shutdown
            pass
            
        except Exception as e:
            self.logger.error(
                f"Unexpected error in stats loop for pool {self.name}: {str(e)}",
                exc_info=True
            )
    
    async def _perform_maintenance(self) -> None:
        """
        Perform maintenance on the connection pool.
        
        This includes:
        - Removing expired connections (exceeded max lifetime)
        - Closing idle connections above minimum size
        - Validating idle connections
        - Maintaining minimum pool size
        - Dynamic scaling based on load
        """
        to_close = []
        to_validate = []
        
        # Step 1: Identify connections to close and validate
        async with self._pool_lock:
            now = time.time()
            
            # 1.1: Check for expired connections (max lifetime exceeded)
            for conn_id, conn_info in list(self._connections.items()):
                # Skip if in use
                if conn_info["in_use"]:
                    continue
                
                # Check for max lifetime
                if now - conn_info["created_at"] > self.config.max_lifetime:
                    to_close.append(conn_id)
                    self._connections.pop(conn_id)
                    self._available_conn_ids.discard(conn_id)
                    continue
                
                # Check for idle timeout
                if now - conn_info["last_used"] > self.config.idle_timeout:
                    # Only close if we have more than min_size connections
                    if len(self._connections) - len(to_close) > self.config.min_size:
                        to_close.append(conn_id)
                        self._connections.pop(conn_id)
                        self._available_conn_ids.discard(conn_id)
                        continue
                
                # Add to validation list if not recently validated
                if (now - conn_info["last_validated"] > self.config.validation_interval
                        and conn_id not in to_close):
                    to_validate.append(conn_id)
        
        # Step 2: Validate connections outside the lock
        invalid_connections = []
        
        # Validate in parallel with a limit to avoid overwhelming the database
        max_concurrent = min(5, len(to_validate))
        async with TaskGroup(name=f"{self.name}_validation", max_concurrency=max_concurrent) as group:
            for conn_id in to_validate:
                group.create_task(self._validate_connection_task(conn_id, invalid_connections))
        
        # Step 3: Close connections outside the lock
        close_tasks = []
        
        # Add invalid connections to close list
        to_close.extend(invalid_connections)
        
        # Close connections in parallel
        async with TaskGroup(name=f"{self.name}_close", max_concurrency=5) as group:
            for conn_id in to_close:
                group.create_task(self._close_connection(conn_id))
        
        # Step 4: Check if we need to create new connections to maintain min_size
        need_to_create = 0
        
        async with self._pool_lock:
            current_size = len(self._connections)
            if current_size < self.config.min_size:
                need_to_create = self.config.min_size - current_size
        
        # Create new connections if needed
        if need_to_create > 0:
            async with TaskGroup(name=f"{self.name}_create", max_concurrency=5) as group:
                for _ in range(need_to_create):
                    group.create_task(self._add_connection())
        
        # Step 5: Dynamic scaling based on load
        if self.config.dynamic_scaling_enabled:
            await self._perform_dynamic_scaling()
    
    async def _validate_connection_task(self, conn_id: str, invalid_list: List[str]) -> None:
        """
        Validate a connection and add to invalid list if needed.
        
        Args:
            conn_id: Connection ID to validate
            invalid_list: List to add invalid connection IDs to
        """
        valid = await self._validate_connection(conn_id)
        
        if not valid:
            # Remove from pool
            async with self._pool_lock:
                if conn_id in self._connections:
                    self._connections.pop(conn_id)
                    self._available_conn_ids.discard(conn_id)
                    invalid_list.append(conn_id)
        else:
            # Update validation timestamp
            async with self._pool_lock:
                if conn_id in self._connections:
                    self._connections[conn_id]["last_validated"] = time.time()
    
    async def _perform_dynamic_scaling(self) -> None:
        """
        Perform dynamic scaling of the pool based on load.
        
        Scales up when load is high, scales down when load is low.
        """
        # Skip if dynamic scaling is disabled
        if not self.config.dynamic_scaling_enabled:
            return
        
        # Skip if we're in a scaling cooldown period
        if (self.metrics.last_scaling_time and 
                time.time() - self.metrics.last_scaling_time < self.config.scaling_cool_down):
            return
        
        # Get current load
        current_load = self.metrics.get_current_load()
        recent_load = self.metrics.get_average_load(window=60.0)  # 1 minute average
        
        # Use the higher of current and recent load
        load = max(current_load, recent_load)
        
        # Check if we need to scale
        async with self._scaling_lock:
            async with self._pool_lock:
                current_size = len(self._connections)
                pending_count = self._pending_acquisitions
                available_count = len(self._available_conn_ids)
            
            # Determine if we need to scale up (high load + pending acquisitions)
            scale_up = (
                load >= self.config.scale_up_threshold or
                pending_count > 0 or
                available_count < self.config.target_free_connections
            )
            
            # Determine if we need to scale down (low load + excess connections)
            scale_down = (
                load <= self.config.scale_down_threshold and
                available_count > self.config.target_free_connections + 2 and  # Extra margin
                current_size > self.config.min_size
            )
            
            if scale_up and current_size < self.config.max_size:
                # Calculate how many connections to add
                to_add = min(
                    self.config.max_size - current_size,
                    max(1, pending_count),  # At least one
                    5  # Cap at 5 at a time for stability
                )
                
                self.logger.info(
                    f"Scaling up pool {self.name} by {to_add} connections (load: {load:.2f})"
                )
                
                # Create new connections
                async with TaskGroup(name=f"{self.name}_scale_up", max_concurrency=5) as group:
                    for _ in range(to_add):
                        group.create_task(self._add_connection())
                
                # Update metrics
                self.metrics.record_scaling()
                
            elif scale_down:
                # Calculate how many connections to remove
                available_excess = available_count - self.config.target_free_connections
                size_excess = current_size - self.config.min_size
                to_remove = min(
                    available_excess,
                    size_excess,
                    3  # Cap at 3 at a time for stability
                )
                
                if to_remove > 0:
                    self.logger.info(
                        f"Scaling down pool {self.name} by {to_remove} connections (load: {load:.2f})"
                    )
                    
                    # Get connections to remove
                    connections_to_remove = []
                    
                    async with self._pool_lock:
                        # Get idle connections sorted by idle time (oldest first)
                        idle_connections = [
                            (conn_id, self._connections[conn_id])
                            for conn_id in self._available_conn_ids
                        ]
                        
                        idle_connections.sort(key=lambda x: x[1]["last_used"])
                        
                        # Take the oldest connections
                        for i in range(min(to_remove, len(idle_connections))):
                            conn_id, _ = idle_connections[i]
                            connections_to_remove.append(conn_id)
                            
                            # Remove from pool
                            self._connections.pop(conn_id)
                            self._available_conn_ids.discard(conn_id)
                    
                    # Close connections
                    async with TaskGroup(name=f"{self.name}_scale_down", max_concurrency=5) as group:
                        for conn_id in connections_to_remove:
                            group.create_task(self._close_connection(conn_id))
                    
                    # Update metrics
                    self.metrics.record_scaling()
    
    @cancellable
    @retry(max_attempts=3, base_delay=0.2, max_delay=2.0)
    async def acquire(self) -> Tuple[str, T]:
        """
        Acquire a connection from the pool.
        
        Returns:
            Tuple of (connection_id, connection)
            
        Raises:
            RuntimeError: If the pool is closed
            TimeoutError: If connection acquisition times out
        """
        if self._closed:
            raise RuntimeError(f"Connection pool {self.name} is closed")
        
        # Track acquisition start time for metrics
        start_time = time.time()
        
        # Increment pending acquisitions counter
        async with self._pool_lock:
            self._pending_acquisitions += 1
        
        try:
            # Try to get a connection
            conn_id, connection = await self._try_acquire_connection()
            
            # Record wait time for metrics
            wait_time = time.time() - start_time
            self.metrics.record_wait_time(wait_time)
            
            return conn_id, connection
            
        finally:
            # Decrement pending acquisitions counter
            async with self._pool_lock:
                self._pending_acquisitions = max(0, self._pending_acquisitions - 1)
    
    async def _try_acquire_connection(self) -> Tuple[str, T]:
        """
        Try to acquire a connection, with waiting if needed.
        
        Returns:
            Tuple of (connection_id, connection)
            
        Raises:
            RuntimeError: If the pool is closed
            TimeoutError: If acquisition times out
        """
        # Max wait time
        max_wait = 30.0  # 30 seconds
        start_time = time.time()
        
        while not self._closed:
            # Check for timeout
            if time.time() - start_time > max_wait:
                raise asyncio.TimeoutError(
                    f"Timeout waiting for connection from pool {self.name}"
                )
            
            # Wait for maintenance to complete
            if not self._maintenance_complete.is_set():
                try:
                    # Don't wait too long
                    async with timeout(1.0):
                        await self._maintenance_complete.wait()
                except asyncio.TimeoutError:
                    # Continue anyway
                    pass
            
            # Try to get an available connection
            async with self._pool_lock:
                # Check for available connections
                if self._available_conn_ids:
                    conn_id = self._available_conn_ids.pop()
                    conn_info = self._connections[conn_id]
                    
                    # Mark as in use
                    conn_info["in_use"] = True
                    conn_info["last_used"] = time.time()
                    
                    # Update metrics
                    self.metrics.record_connection_checkout(conn_id)
                    
                    # Clear event if no more connections available
                    if not self._available_conn_ids:
                        self._connection_available.clear()
                    
                    # Return the connection
                    return conn_id, conn_info["connection"]
                
                # If we can create a new connection, do so
                current_size = len(self._connections)
                can_create_new = current_size < self.config.max_size
                
                # Check overflow allowance
                if (not can_create_new and 
                        self.config.allow_overflow and 
                        current_size - self.config.max_size < self.config.max_overflow):
                    can_create_new = True
            
            # Try to create a new connection if allowed
            if can_create_new:
                conn_id = await self._add_connection()
                
                # If successful, mark as in use and return
                if conn_id:
                    async with self._pool_lock:
                        if conn_id in self._connections:
                            conn_info = self._connections[conn_id]
                            conn_info["in_use"] = True
                            
                            # Update metrics
                            self.metrics.record_connection_checkout(conn_id)
                            
                            return conn_id, conn_info["connection"]
            
            # Wait for a connection to become available
            try:
                # Use a reasonable timeout to avoid waiting forever
                async with timeout(5.0):
                    await self._connection_available.wait()
            except asyncio.TimeoutError:
                # Check if pool is closed
                if self._closed:
                    raise RuntimeError(f"Connection pool {self.name} is closed")
                # Continue and try again
        
        raise RuntimeError(f"Connection pool {self.name} is closed")
    
    async def release(self, conn_id: str) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            conn_id: ID of the connection to release
            
        Raises:
            ValueError: If the connection is not found in the pool
        """
        if self._closed:
            # If pool is closed, close the connection instead of returning to pool
            await self._close_connection(conn_id)
            return
        
        async with self._pool_lock:
            # Check if connection exists in the pool
            if conn_id not in self._connections:
                raise ValueError(f"Connection {conn_id} not found in pool {self.name}")
            
            conn_info = self._connections[conn_id]
            
            # Update metrics
            self.metrics.record_connection_checkin(conn_id)
            
            # Schedule connection reset if needed
            needs_reset = False
            
            # Determine if reset is needed based on strategy
            if self.reset_func:
                # Always reset for LOW_LATENCY strategy
                if self.config.strategy == ConnectionPoolStrategy.LOW_LATENCY:
                    needs_reset = True
                # For other strategies, reset after certain number of queries
                elif (conn_id in self.metrics.connection_metrics and
                      self.metrics.connection_metrics[conn_id].query_count > 100):
                    needs_reset = True
            
            if needs_reset:
                # Mark as in use during reset
                conn_info["in_use"] = True
                
                # Create reset task
                asyncio.create_task(
                    self._reset_and_return_connection(conn_id),
                    name=f"{self.name}_reset_{conn_id}"
                )
            else:
                # Mark as available immediately
                conn_info["in_use"] = False
                conn_info["last_used"] = time.time()
                
                # Add to available set
                self._available_conn_ids.add(conn_id)
                
                # Signal that a connection is available
                self._connection_available.set()
    
    async def _reset_and_return_connection(self, conn_id: str) -> None:
        """
        Reset a connection and return it to the available pool.
        
        Args:
            conn_id: ID of the connection to reset
        """
        try:
            # Reset the connection
            reset_ok = await self._reset_connection(conn_id)
            
            if not reset_ok:
                # If reset failed, close and don't return to pool
                await self._close_connection(conn_id)
                return
            
            # Return to pool
            async with self._pool_lock:
                if conn_id in self._connections:
                    conn_info = self._connections[conn_id]
                    conn_info["in_use"] = False
                    conn_info["last_used"] = time.time()
                    
                    # Add to available set
                    self._available_conn_ids.add(conn_id)
                    
                    # Signal that a connection is available
                    self._connection_available.set()
        
        except Exception as e:
            self.logger.error(f"Error in reset_and_return for connection {conn_id}: {str(e)}")
            
            # Close the connection on error
            await self._close_connection(conn_id)
    
    @contextlib.asynccontextmanager
    async def connection(self) -> T:
        """
        Get a connection from the pool for the duration of the context.
        
        Yields:
            A database connection
            
        Raises:
            RuntimeError: If the pool is closed
            TimeoutError: If connection acquisition times out
        """
        conn_id, connection = await self.acquire()
        
        try:
            yield connection
        finally:
            await self.release(conn_id)
    
    async def clear(self) -> None:
        """
        Clear the connection pool.
        
        Closes all connections and resets the pool to its initial state.
        """
        if self._closed:
            return
        
        # Get all connections
        connections_to_close = []
        
        async with self._pool_lock:
            # Get all connections
            connections_to_close = list(self._connections.keys())
            
            # Reset state
            self._connections = {}
            self._available_conn_ids = set()
            self._pending_acquisitions = 0
            
            # Signal any waiters
            self._connection_available.set()
        
        # Close connections outside the lock
        for conn_id in connections_to_close:
            await self._close_connection(conn_id)
        
        # Reset metrics
        self.metrics = PoolMetrics()
        
        # Reinitialize the pool
        await self._initialize_connections()
    
    async def close(self) -> None:
        """
        Close the connection pool.
        
        Closes all connections and stops all maintenance tasks.
        """
        if self._closed:
            return
        
        self._closed = True
        
        # Cancel maintenance tasks
        tasks = [self._maintenance_task, self._health_check_task, self._stats_task]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        
        # Get all connections
        connections_to_close = list(self._connections.keys())
        
        # Reset state
        async with self._pool_lock:
            self._connections = {}
            self._available_conn_ids = set()
            
            # Signal any waiters
            self._connection_available.set()
        
        # Close connections outside the lock
        for conn_id in connections_to_close:
            await self._close_connection(conn_id)
        
        # Log summary
        self.logger.info(
            f"Closed connection pool {self.name}: "
            f"created={self.metrics.connections_created}, "
            f"closed={self.metrics.connections_closed}, "
            f"errors={self.metrics.connection_errors}"
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the connection pool.
        
        Returns:
            Dictionary of metrics
        """
        return self.metrics.get_summary()
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """
        Get detailed metrics for the connection pool.
        
        Returns:
            Dictionary of detailed metrics including per-connection stats
        """
        summary = self.metrics.get_summary()
        
        # Add connection-specific metrics
        connection_metrics = {}
        
        for conn_id, metrics in self.metrics.connection_metrics.items():
            connection_metrics[conn_id] = {
                "age": metrics.age,
                "idle_time": metrics.idle_time,
                "usage_count": metrics.usage_count,
                "query_count": metrics.query_count,
                "avg_query_time": metrics.avg_query_time,
                "max_query_time": metrics.max_query_time,
                "validation_failure_rate": metrics.validation_failure_rate,
            }
        
        # Add to summary
        summary["connections"] = connection_metrics
        
        # Add configuration
        summary["config"] = {
            "min_size": self.config.min_size,
            "max_size": self.config.max_size,
            "strategy": self.config.strategy.value,
            "dynamic_scaling": self.config.dynamic_scaling_enabled,
        }
        
        # Add circuit breaker state if available
        if self._circuit_breaker:
            summary["circuit_breaker"] = {
                "state": self._circuit_breaker.state.value,
                "failure_count": self._circuit_breaker.failure_count,
            }
        
        return summary
    
    @property
    def size(self) -> int:
        """Get the current size of the pool."""
        return len(self._connections)
    
    @property
    def active_connections(self) -> int:
        """Get the number of active connections."""
        return self.metrics.active_connections
    
    @property
    def idle_connections(self) -> int:
        """Get the number of idle connections."""
        return self.metrics.idle_connections


class EnhancedAsyncEnginePool:
    """
    Enhanced pool for AsyncEngine instances.
    
    Provides a specialized connection pool for SQLAlchemy AsyncEngine
    instances with advanced features for performance and reliability.
    """
    
    def __init__(
        self,
        name: str,
        config: ConnectionConfig,
        pool_config: Optional[ConnectionPoolConfig] = None,
        resource_registry: Optional[ResourceRegistry] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced async engine pool.
        
        Args:
            name: Name of the pool
            config: Database connection configuration
            pool_config: Pool configuration
            resource_registry: Resource registry
            logger: Logger instance
        """
        self.name = name
        self.config = config
        self.pool_config = pool_config or ConnectionPoolConfig()
        self.resource_registry = resource_registry or get_resource_registry()
        self.logger = logger or logging.getLogger(__name__)
        
        # Create the connection pool
        self.pool: Optional[EnhancedConnectionPool[AsyncEngine]] = None
    
    async def start(self) -> None:
        """
        Start the engine pool.
        """
        if self.pool is not None:
            return
        
        # Create factory function
        async def engine_factory() -> AsyncEngine:
            from sqlalchemy.ext.asyncio import create_async_engine
            
            # Create connection string
            conn_str = (
                f"{self.config.db_driver}://{self.config.db_role}:{self.config.db_user_pw}"
                f"@{self.config.db_host}:{self.config.db_port or 5432}/{self.config.db_name}"
            )
            
            # Create the engine with SQLAlchemy's connection pooling disabled
            # (we're managing our own connection pool)
            engine = create_async_engine(
                conn_str,
                echo=False,
                future=True,
                poolclass=None,  # Disable SQLAlchemy's connection pooling
                connect_args={
                    "command_timeout": self.pool_config.connection_timeout,
                },
                **self.config.kwargs
            )
            
            return engine
        
        # Create close function
        async def engine_close(engine: AsyncEngine) -> None:
            await engine.dispose()
        
        # Create validation function
        async def engine_validate(engine: AsyncEngine) -> bool:
            try:
                async with engine.connect() as conn:
                    await conn.execute("SELECT 1")
                    return True
            except Exception as e:
                self.logger.warning(f"Engine validation failed: {str(e)}")
                return False
        
        # Create reset function
        async def engine_reset(engine: AsyncEngine) -> None:
            # Just dispose and let SQLAlchemy create a new connection
            await engine.dispose()
        
        # Create the pool
        self.pool = EnhancedConnectionPool(
            name=f"engine_pool_{self.name}",
            factory=engine_factory,
            close_func=engine_close,
            validate_func=engine_validate,
            reset_func=engine_reset,
            config=self.pool_config,
            resource_registry=self.resource_registry,
            logger=self.logger,
        )
        
        # Start the pool
        await self.pool.start()
    
    async def acquire(self) -> AsyncEngine:
        """
        Acquire an engine from the pool.
        
        Returns:
            AsyncEngine instance
            
        Raises:
            RuntimeError: If the pool is not started
        """
        if self.pool is None:
            await self.start()
        
        # Get a connection from the pool
        _, engine = await self.pool.acquire()
        return engine
    
    async def release(self, engine: AsyncEngine) -> None:
        """
        Release an engine back to the pool.
        
        Args:
            engine: Engine to release
            
        Raises:
            RuntimeError: If the pool is not started
            ValueError: If the engine is not found in the pool
        """
        if self.pool is None:
            raise RuntimeError(f"Engine pool {self.name} is not started")
        
        # Find the connection ID for the engine
        conn_id = None
        
        async with self.pool._pool_lock:
            for cid, conn_info in self.pool._connections.items():
                if conn_info["connection"] is engine:
                    conn_id = cid
                    break
        
        if conn_id is None:
            raise ValueError(f"Engine not found in pool {self.name}")
        
        # Release back to the pool
        await self.pool.release(conn_id)
    
    @contextlib.asynccontextmanager
    async def engine(self) -> AsyncEngine:
        """
        Context manager for acquiring an engine from the pool.
        
        Yields:
            AsyncEngine instance
        """
        engine = await self.acquire()
        
        try:
            yield engine
        finally:
            await self.release(engine)
    
    async def close(self) -> None:
        """
        Close the engine pool.
        """
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


class EnhancedAsyncConnectionManager:
    """
    Manager for AsyncEngine and AsyncConnection pools.
    
    Provides centralized management of database connections with
    configuration per connection type, with intelligent routing
    and connection lifecycle management.
    """
    
    def __init__(
        self,
        resource_registry: Optional[ResourceRegistry] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced async connection manager.
        
        Args:
            resource_registry: Resource registry
            logger: Logger instance
        """
        self.resource_registry = resource_registry or get_resource_registry()
        self.logger = logger or logging.getLogger(__name__)
        
        # Connection pools by name
        self._engine_pools: Dict[str, EnhancedAsyncEnginePool] = {}
        
        # Connection pool configurations
        self._default_config = ConnectionPoolConfig()
        self._role_configs: Dict[str, ConnectionPoolConfig] = {}
        
        # Synchronization
        self._manager_lock = AsyncLock()
    
    def configure_pool(
        self,
        role: Optional[str] = None,
        config: ConnectionPoolConfig = None,
    ) -> None:
        """
        Configure a connection pool.
        
        Args:
            role: Database role (None for default)
            config: Pool configuration
        """
        if config is None:
            config = ConnectionPoolConfig()
        
        if role is None:
            self._default_config = config
        else:
            self._role_configs[role] = config
    
    def get_pool_config(self, role: str) -> ConnectionPoolConfig:
        """
        Get the configuration for a pool.
        
        Args:
            role: Database role
            
        Returns:
            Pool configuration
        """
        return self._role_configs.get(role, self._default_config)
    
    async def get_engine_pool(
        self,
        config: ConnectionConfig,
    ) -> EnhancedAsyncEnginePool:
        """
        Get or create an engine pool for a connection configuration.
        
        Args:
            config: Connection configuration
            
        Returns:
            Engine pool
        """
        # Create a pool name
        pool_name = f"{config.db_role}@{config.db_host}/{config.db_name}"
        
        async with self._manager_lock:
            # Check if pool exists
            if pool_name in self._engine_pools:
                return self._engine_pools[pool_name]
            
            # Get the pool configuration
            pool_config = self.get_pool_config(config.db_role)
            
            # Create the pool
            pool = EnhancedAsyncEnginePool(
                name=pool_name,
                config=config,
                pool_config=pool_config,
                resource_registry=self.resource_registry,
                logger=self.logger,
            )
            
            # Start the pool
            await pool.start()
            
            # Store in dictionary
            self._engine_pools[pool_name] = pool
            
            return pool
    
    @contextlib.asynccontextmanager
    async def engine(
        self,
        config: ConnectionConfig,
    ) -> AsyncEngine:
        """
        Get an engine from a pool.
        
        Args:
            config: Connection configuration
            
        Yields:
            AsyncEngine instance
        """
        # Get the pool
        pool = await self.get_engine_pool(config)
        
        # Use the pool
        async with pool.engine() as engine:
            yield engine
    
    @contextlib.asynccontextmanager
    async def connection(
        self,
        config: ConnectionConfig,
        isolation_level: str = "AUTOCOMMIT",
    ) -> AsyncConnection:
        """
        Get a connection.
        
        Args:
            config: Connection configuration
            isolation_level: SQL transaction isolation level
            
        Yields:
            AsyncConnection instance
        """
        # Get an engine
        async with self.engine(config) as engine:
            # Create a connection
            async with engine.connect() as connection:
                # Set isolation level
                await connection.execution_options(isolation_level=isolation_level)
                
                # Yield the connection
                yield connection
    
    async def close(self) -> None:
        """
        Close all connection pools.
        """
        async with self._manager_lock:
            # Close all pools
            for pool in self._engine_pools.values():
                await pool.close()
            
            # Clear dictionaries
            self._engine_pools = {}
        
        self.logger.info("Closed all connection pools")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for all pools.
        
        Returns:
            Dictionary of metrics by pool name
        """
        metrics = {}
        
        for name, pool in self._engine_pools.items():
            if pool.pool is not None:
                metrics[name] = pool.pool.get_metrics()
        
        return metrics


# Global connection manager
_connection_manager: Optional[EnhancedAsyncConnectionManager] = None


def get_connection_manager() -> EnhancedAsyncConnectionManager:
    """
    Get the global connection manager.
    
    Returns:
        Global connection manager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = EnhancedAsyncConnectionManager()
    return _connection_manager


@contextlib.asynccontextmanager
async def enhanced_async_engine(
    db_driver: str = uno_settings.DB_ASYNC_DRIVER,
    db_name: str = uno_settings.DB_NAME,
    db_user_pw: str = uno_settings.DB_USER_PW,
    db_role: str = f"{uno_settings.DB_NAME}_login",
    db_host: Optional[str] = uno_settings.DB_HOST,
    db_port: Optional[int] = uno_settings.DB_PORT,
    **kwargs: Any,
) -> AsyncEngine:
    """
    Context manager for enhanced async engines.
    
    Args:
        db_driver: Database driver
        db_name: Database name
        db_user_pw: Database password
        db_role: Database role
        db_host: Database host
        db_port: Database port
        **kwargs: Additional connection parameters
        
    Yields:
        AsyncEngine instance
    """
    # Create connection config
    config = ConnectionConfig(
        db_role=db_role,
        db_name=db_name,
        db_host=db_host,
        db_user_pw=db_user_pw,
        db_driver=db_driver,
        db_port=db_port,
        **kwargs,
    )
    
    # Get connection manager
    manager = get_connection_manager()
    
    # Get engine from pool
    async with manager.engine(config) as engine:
        yield engine


@contextlib.asynccontextmanager
async def enhanced_async_connection(
    db_driver: str = uno_settings.DB_ASYNC_DRIVER,
    db_name: str = uno_settings.DB_NAME,
    db_user_pw: str = uno_settings.DB_USER_PW,
    db_role: str = f"{uno_settings.DB_NAME}_login",
    db_host: Optional[str] = uno_settings.DB_HOST,
    db_port: Optional[int] = uno_settings.DB_PORT,
    isolation_level: str = "AUTOCOMMIT",
    **kwargs: Any,
) -> AsyncConnection:
    """
    Context manager for enhanced async connections.
    
    Args:
        db_driver: Database driver
        db_name: Database name
        db_user_pw: Database password
        db_role: Database role
        db_host: Database host
        db_port: Database port
        isolation_level: SQL transaction isolation level
        **kwargs: Additional connection parameters
        
    Yields:
        AsyncConnection instance
    """
    # Create connection config
    config = ConnectionConfig(
        db_role=db_role,
        db_name=db_name,
        db_host=db_host,
        db_user_pw=db_user_pw,
        db_driver=db_driver,
        db_port=db_port,
        **kwargs,
    )
    
    # Get connection manager
    manager = get_connection_manager()
    
    # Get connection
    async with manager.connection(
        config=config,
        isolation_level=isolation_level,
    ) as connection:
        yield connection