# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Connection health monitoring and management.

This module provides advanced connection health monitoring, diagnostics,
and automatic recovery strategies for database connections.
"""

from typing import Dict, List, Set, Optional, Any, Callable, Awaitable, Tuple, Union, TypeVar
import asyncio
import logging
import time
import enum
import dataclasses
from dataclasses import dataclass, field
import contextlib

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
from sqlalchemy import select, text

from uno.database.errors import (
    DatabaseConnectionError, 
    DatabaseTransactionError,
    DatabaseQueryError
)
from uno.core.asynchronous import (
    AsyncLock, 
    timeout,
    TaskGroup
)
from uno.core.resource_management import ResourceMonitor

T = TypeVar('T')


class ConnectionHealthState(enum.Enum):
    """Health states for a database connection."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ConnectionIssueType(enum.Enum):
    """Types of issues that can affect a database connection."""
    
    LATENCY = "latency"             # High latency
    ERRORS = "errors"               # Repeated errors
    TIMEOUTS = "timeouts"           # Query timeouts
    DEADLOCKS = "deadlocks"         # Repeated deadlocks
    DISCONNECTIONS = "disconnections"  # Unexpected disconnections
    IDLE_IN_TX = "idle_in_tx"       # Idle in transaction
    BLOCKING = "blocking"           # Blocking other connections
    RESOURCE_USAGE = "resource_usage"  # High resource usage
    LOCKS = "locks"                 # Holding locks for too long
    STALE_STATISTICS = "stale_statistics"  # Out-of-date statistics
    CONNECTION_LEAK = "connection_leak"  # Connection not returned to pool
    POOL_EXHAUSTION = "pool_exhaustion"  # Pool running out of connections


@dataclass
class ConnectionHealthMetrics:
    """Detailed health metrics for a database connection."""
    
    # Timestamps
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    last_checked_at: float = field(default_factory=time.time)
    
    # Usage counts
    query_count: int = 0
    transaction_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    deadlock_count: int = 0
    
    # Query performance
    total_query_time: float = 0.0
    max_query_time: float = 0.0
    last_query_time: float = 0.0
    
    # Latency metrics (in milliseconds)
    ping_times: List[float] = field(default_factory=list)
    
    # Resource usage
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    
    # Transaction metrics
    transactions_rolled_back: int = 0
    max_transaction_time: float = 0.0
    current_transaction_start: Optional[float] = None
    
    # Network metrics
    packet_loss: float = 0.0
    network_latency: float = 0.0
    
    # Database-specific metrics
    deadlocks_detected: int = 0
    locks_held: int = 0
    blocking_sessions: int = 0
    
    def update_usage(self) -> None:
        """Update usage metrics when connection is used."""
        self.last_used_at = time.time()
    
    def record_query(self, duration: float) -> None:
        """Record a query execution."""
        self.query_count += 1
        self.total_query_time += duration
        self.last_query_time = duration
        self.max_query_time = max(self.max_query_time, duration)
    
    def record_error(self, error_type: Optional[str] = None) -> None:
        """Record a connection error."""
        self.error_count += 1
        if error_type == "timeout":
            self.timeout_count += 1
        elif error_type == "deadlock":
            self.deadlock_count += 1
    
    def record_transaction_start(self) -> None:
        """Record the start of a transaction."""
        self.current_transaction_start = time.time()
    
    def record_transaction_end(self, success: bool = True) -> None:
        """Record the end of a transaction."""
        self.transaction_count += 1
        
        if not success:
            self.transactions_rolled_back += 1
        
        if self.current_transaction_start:
            duration = time.time() - self.current_transaction_start
            self.max_transaction_time = max(self.max_transaction_time, duration)
            self.current_transaction_start = None
    
    def record_ping(self, latency: float) -> None:
        """Record a ping latency measurement (in milliseconds)."""
        self.ping_times.append(latency)
        # Keep the most recent 100 measurements
        if len(self.ping_times) > 100:
            self.ping_times.pop(0)
        self.network_latency = sum(self.ping_times) / len(self.ping_times) if self.ping_times else 0
    
    def get_avg_query_time(self) -> float:
        """Get the average query time in seconds."""
        if self.query_count == 0:
            return 0.0
        return self.total_query_time / self.query_count
    
    def get_error_rate(self) -> float:
        """Get the error rate (errors per query)."""
        if self.query_count == 0:
            return 0.0
        return self.error_count / self.query_count
    
    def get_timeout_rate(self) -> float:
        """Get the timeout rate (timeouts per query)."""
        if self.query_count == 0:
            return 0.0
        return self.timeout_count / self.query_count
    
    def get_deadlock_rate(self) -> float:
        """Get the deadlock rate (deadlocks per transaction)."""
        if self.transaction_count == 0:
            return 0.0
        return self.deadlock_count / self.transaction_count
    
    def get_rollback_rate(self) -> float:
        """Get the transaction rollback rate."""
        if self.transaction_count == 0:
            return 0.0
        return self.transactions_rolled_back / self.transaction_count
    
    def get_age(self) -> float:
        """Get the age of the connection in seconds."""
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """Get the idle time of the connection in seconds."""
        return time.time() - self.last_used_at


@dataclass
class ConnectionIssue:
    """An identified issue with a database connection."""
    
    # Basic information
    connection_id: str
    issue_type: ConnectionIssueType
    severity: float  # 0.0 to 1.0
    description: str
    detected_at: float = field(default_factory=time.time)
    
    # Resolution status
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution_action: Optional[str] = None
    
    # Contextual information
    context: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self, action: str) -> None:
        """
        Mark the issue as resolved.
        
        Args:
            action: Description of the action taken to resolve the issue
        """
        self.resolved = True
        self.resolved_at = time.time()
        self.resolution_action = action
    
    @property
    def time_to_resolve(self) -> Optional[float]:
        """Time taken to resolve the issue, if resolved."""
        if not self.resolved or not self.resolved_at:
            return None
        return self.resolved_at - self.detected_at


@dataclass
class ConnectionHealthAssessment:
    """Assessment of a database connection's health."""
    
    # Basic information
    connection_id: str
    state: ConnectionHealthState
    score: float  # 0.0 to 1.0 (higher is better)
    timestamp: float = field(default_factory=time.time)
    
    # Issues
    issues: List[ConnectionIssue] = field(default_factory=list)
    
    # Metrics snapshot
    metrics: Optional[ConnectionHealthMetrics] = None
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    
    @property
    def has_issues(self) -> bool:
        """Check if the assessment includes any unresolved issues."""
        return any(not issue.resolved for issue in self.issues)
    
    @property
    def most_severe_issue(self) -> Optional[ConnectionIssue]:
        """Get the most severe unresolved issue, if any."""
        unresolved = [issue for issue in self.issues if not issue.resolved]
        return max(unresolved, key=lambda i: i.severity) if unresolved else None


class HealthClassifier:
    """
    Classifier for connection health states.
    
    Uses configurable thresholds to classify connections as healthy,
    degraded, or unhealthy based on metrics and detected issues.
    """
    
    def __init__(
        self,
        # Latency thresholds (query time)
        latency_warning_threshold: float = 0.5,  # 500ms
        latency_critical_threshold: float = 1.0,  # 1s
        
        # Error rate thresholds (% of operations)
        error_warning_threshold: float = 0.01,   # 1%
        error_critical_threshold: float = 0.05,  # 5%
        
        # Timeout thresholds (% of queries)
        timeout_warning_threshold: float = 0.01,  # 1%
        timeout_critical_threshold: float = 0.03, # 3%
        
        # Deadlock thresholds (per transaction)
        deadlock_warning_threshold: float = 0.05,  # 5%
        deadlock_critical_threshold: float = 0.10, # 10%
        
        # Transaction metrics
        rollback_warning_threshold: float = 0.20,  # 20%
        rollback_critical_threshold: float = 0.40, # 40%
        
        # Network health
        network_latency_warning_threshold: float = 50.0,  # 50ms
        network_latency_critical_threshold: float = 100.0, # 100ms
        
        # Idle connection thresholds
        idle_warning_threshold: float = 600.0,  # 10 minutes
        idle_critical_threshold: float = 1800.0, # 30 minutes
        
        # Age thresholds
        age_warning_threshold: float = 3600.0,  # 1 hour
        age_critical_threshold: float = 7200.0, # 2 hours
        
        # Scoring weights
        latency_weight: float = 0.25,
        error_weight: float = 0.25,
        timeout_weight: float = 0.15,
        deadlock_weight: float = 0.10,
        rollback_weight: float = 0.10,
        network_weight: float = 0.15,
    ):
        """
        Initialize the health classifier with thresholds.
        
        Args:
            latency_warning_threshold: Query time threshold for warning (seconds)
            latency_critical_threshold: Query time threshold for critical (seconds)
            error_warning_threshold: Error rate threshold for warning
            error_critical_threshold: Error rate threshold for critical
            timeout_warning_threshold: Timeout rate threshold for warning
            timeout_critical_threshold: Timeout rate threshold for critical
            deadlock_warning_threshold: Deadlock rate threshold for warning
            deadlock_critical_threshold: Deadlock rate threshold for critical
            rollback_warning_threshold: Rollback rate threshold for warning
            rollback_critical_threshold: Rollback rate threshold for critical
            network_latency_warning_threshold: Network latency for warning (ms)
            network_latency_critical_threshold: Network latency for critical (ms)
            idle_warning_threshold: Idle time threshold for warning (seconds)
            idle_critical_threshold: Idle time threshold for critical (seconds)
            age_warning_threshold: Age threshold for warning (seconds)
            age_critical_threshold: Age threshold for critical (seconds)
            latency_weight: Weight for latency in health score calculation
            error_weight: Weight for errors in health score calculation
            timeout_weight: Weight for timeouts in health score calculation
            deadlock_weight: Weight for deadlocks in health score calculation
            rollback_weight: Weight for rollbacks in health score calculation
            network_weight: Weight for network health in health score calculation
        """
        # Store thresholds
        self.thresholds = {
            "latency": (latency_warning_threshold, latency_critical_threshold),
            "error": (error_warning_threshold, error_critical_threshold),
            "timeout": (timeout_warning_threshold, timeout_critical_threshold),
            "deadlock": (deadlock_warning_threshold, deadlock_critical_threshold),
            "rollback": (rollback_warning_threshold, rollback_critical_threshold),
            "network_latency": (network_latency_warning_threshold, network_latency_critical_threshold),
            "idle": (idle_warning_threshold, idle_critical_threshold),
            "age": (age_warning_threshold, age_critical_threshold),
        }
        
        # Store weights
        self.weights = {
            "latency": latency_weight,
            "error": error_weight,
            "timeout": timeout_weight,
            "deadlock": deadlock_weight,
            "rollback": rollback_weight,
            "network": network_weight,
        }
    
    def classify_metrics(self, metrics: ConnectionHealthMetrics) -> Tuple[ConnectionHealthState, float, List[ConnectionIssue]]:
        """
        Classify metrics and determine health state.
        
        Args:
            metrics: Connection health metrics
            
        Returns:
            Tuple of (health_state, health_score, list_of_issues)
        """
        issues = []
        scores = {}
        
        # Check latency
        avg_query_time = metrics.get_avg_query_time()
        warning, critical = self.thresholds["latency"]
        
        if avg_query_time >= critical:
            severity = min(1.0, avg_query_time / (critical * 2))
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.LATENCY,
                severity=severity,
                description=f"High query latency detected: {avg_query_time:.3f}s (critical threshold: {critical:.3f}s)",
                context={"avg_query_time": avg_query_time, "threshold": critical},
            ))
            scores["latency"] = 1.0 - severity
        elif avg_query_time >= warning:
            severity = (avg_query_time - warning) / (critical - warning) * 0.5
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.LATENCY,
                severity=severity,
                description=f"Elevated query latency detected: {avg_query_time:.3f}s (warning threshold: {warning:.3f}s)",
                context={"avg_query_time": avg_query_time, "threshold": warning},
            ))
            scores["latency"] = 1.0 - severity
        else:
            scores["latency"] = 1.0
        
        # Check error rate
        error_rate = metrics.get_error_rate()
        warning, critical = self.thresholds["error"]
        
        if error_rate >= critical:
            severity = min(1.0, error_rate / (critical * 2))
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.ERRORS,
                severity=severity,
                description=f"High error rate detected: {error_rate:.1%} (critical threshold: {critical:.1%})",
                context={"error_rate": error_rate, "threshold": critical},
            ))
            scores["error"] = 1.0 - severity
        elif error_rate >= warning:
            severity = (error_rate - warning) / (critical - warning) * 0.5
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.ERRORS,
                severity=severity,
                description=f"Elevated error rate detected: {error_rate:.1%} (warning threshold: {warning:.1%})",
                context={"error_rate": error_rate, "threshold": warning},
            ))
            scores["error"] = 1.0 - severity
        else:
            scores["error"] = 1.0
        
        # Check timeout rate
        timeout_rate = metrics.get_timeout_rate()
        warning, critical = self.thresholds["timeout"]
        
        if timeout_rate >= critical:
            severity = min(1.0, timeout_rate / (critical * 2))
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.TIMEOUTS,
                severity=severity,
                description=f"High timeout rate detected: {timeout_rate:.1%} (critical threshold: {critical:.1%})",
                context={"timeout_rate": timeout_rate, "threshold": critical},
            ))
            scores["timeout"] = 1.0 - severity
        elif timeout_rate >= warning:
            severity = (timeout_rate - warning) / (critical - warning) * 0.5
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.TIMEOUTS,
                severity=severity,
                description=f"Elevated timeout rate detected: {timeout_rate:.1%} (warning threshold: {warning:.1%})",
                context={"timeout_rate": timeout_rate, "threshold": warning},
            ))
            scores["timeout"] = 1.0 - severity
        else:
            scores["timeout"] = 1.0
        
        # Check deadlock rate
        deadlock_rate = metrics.get_deadlock_rate()
        warning, critical = self.thresholds["deadlock"]
        
        if deadlock_rate >= critical:
            severity = min(1.0, deadlock_rate / (critical * 2))
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.DEADLOCKS,
                severity=severity,
                description=f"High deadlock rate detected: {deadlock_rate:.1%} (critical threshold: {critical:.1%})",
                context={"deadlock_rate": deadlock_rate, "threshold": critical},
            ))
            scores["deadlock"] = 1.0 - severity
        elif deadlock_rate >= warning:
            severity = (deadlock_rate - warning) / (critical - warning) * 0.5
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.DEADLOCKS,
                severity=severity,
                description=f"Elevated deadlock rate detected: {deadlock_rate:.1%} (warning threshold: {warning:.1%})",
                context={"deadlock_rate": deadlock_rate, "threshold": warning},
            ))
            scores["deadlock"] = 1.0 - severity
        else:
            scores["deadlock"] = 1.0
        
        # Check rollback rate
        rollback_rate = metrics.get_rollback_rate()
        warning, critical = self.thresholds["rollback"]
        
        if rollback_rate >= critical:
            severity = min(1.0, rollback_rate / (critical * 2))
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.ERRORS,
                severity=severity,
                description=f"High transaction rollback rate detected: {rollback_rate:.1%} (critical threshold: {critical:.1%})",
                context={"rollback_rate": rollback_rate, "threshold": critical},
            ))
            scores["rollback"] = 1.0 - severity
        elif rollback_rate >= warning:
            severity = (rollback_rate - warning) / (critical - warning) * 0.5
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.ERRORS,
                severity=severity,
                description=f"Elevated transaction rollback rate detected: {rollback_rate:.1%} (warning threshold: {warning:.1%})",
                context={"rollback_rate": rollback_rate, "threshold": warning},
            ))
            scores["rollback"] = 1.0 - severity
        else:
            scores["rollback"] = 1.0
        
        # Check network latency
        network_latency = metrics.network_latency
        warning, critical = self.thresholds["network_latency"]
        
        if network_latency >= critical:
            severity = min(1.0, network_latency / (critical * 2))
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.LATENCY,
                severity=severity,
                description=f"High network latency detected: {network_latency:.1f}ms (critical threshold: {critical:.1f}ms)",
                context={"network_latency": network_latency, "threshold": critical},
            ))
            scores["network"] = 1.0 - severity
        elif network_latency >= warning:
            severity = (network_latency - warning) / (critical - warning) * 0.5
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.LATENCY,
                severity=severity,
                description=f"Elevated network latency detected: {network_latency:.1f}ms (warning threshold: {warning:.1f}ms)",
                context={"network_latency": network_latency, "threshold": warning},
            ))
            scores["network"] = 1.0 - severity
        else:
            scores["network"] = 1.0
        
        # Check idle time
        idle_time = metrics.get_idle_time()
        warning, critical = self.thresholds["idle"]
        
        if idle_time >= critical:
            severity = min(1.0, idle_time / (critical * 2))
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.CONNECTION_LEAK,
                severity=severity,
                description=f"Connection has been idle for {idle_time:.1f}s (critical threshold: {critical:.1f}s)",
                context={"idle_time": idle_time, "threshold": critical},
            ))
        elif idle_time >= warning:
            severity = (idle_time - warning) / (critical - warning) * 0.5
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.CONNECTION_LEAK,
                severity=severity,
                description=f"Connection has been idle for {idle_time:.1f}s (warning threshold: {warning:.1f}s)",
                context={"idle_time": idle_time, "threshold": warning},
            ))
        
        # Check age
        age = metrics.get_age()
        warning, critical = self.thresholds["age"]
        
        if age >= critical:
            severity = min(0.8, age / (critical * 2))  # Lower severity for age issues
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.RESOURCE_USAGE,
                severity=severity,
                description=f"Connection age is {age:.1f}s (critical threshold: {critical:.1f}s)",
                context={"age": age, "threshold": critical},
            ))
        elif age >= warning:
            severity = (age - warning) / (critical - warning) * 0.4  # Lower severity for age issues
            issues.append(ConnectionIssue(
                connection_id="",  # Will be filled by caller
                issue_type=ConnectionIssueType.RESOURCE_USAGE,
                severity=severity,
                description=f"Connection age is {age:.1f}s (warning threshold: {warning:.1f}s)",
                context={"age": age, "threshold": warning},
            ))
        
        # Calculate overall health score
        total_weight = sum(self.weights.values())
        score = sum(scores.get(k, 1.0) * w for k, w in self.weights.items()) / total_weight
        
        # Determine health state
        if score < 0.5:
            state = ConnectionHealthState.UNHEALTHY
        elif score < 0.8:
            state = ConnectionHealthState.DEGRADED
        else:
            state = ConnectionHealthState.HEALTHY
        
        return state, score, issues


class ConnectionHealthMonitor:
    """
    Connection health monitoring and management.
    
    Monitors the health of database connections, detects issues, and provides
    remediation options to maintain connection health.
    """
    
    def __init__(
        self,
        pool_name: str,
        check_interval: float = 60.0,  # 1 minute
        resource_monitor: Optional[ResourceMonitor] = None,
        classifier: Optional[HealthClassifier] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the connection health monitor.
        
        Args:
            pool_name: Name of the connection pool to monitor
            check_interval: Interval between health checks (seconds)
            resource_monitor: Optional resource monitor for tracking resources
            classifier: Optional health classifier for customized thresholds
            logger: Optional logger for monitoring events
        """
        self.pool_name = pool_name
        self.check_interval = check_interval
        self.resource_monitor = resource_monitor
        self.classifier = classifier or HealthClassifier()
        self.logger = logger or logging.getLogger(__name__)
        
        # Connection metrics
        self._metrics: Dict[str, ConnectionHealthMetrics] = {}
        self._connection_states: Dict[str, ConnectionHealthState] = {}
        
        # Issue tracking
        self._issues: Dict[str, List[ConnectionIssue]] = {}
        self._remediation_actions: Dict[ConnectionIssueType, List[str]] = self._initialize_remediation_actions()
        
        # Health history for trend analysis
        self._health_history: Dict[str, List[ConnectionHealthAssessment]] = {}
        
        # Lock for concurrent access
        self._lock = AsyncLock()
        
        # Monitoring and assessment tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._diagnostic_queries: Dict[str, str] = self._initialize_diagnostic_queries()
        
        # Database connection provider function
        self._connection_provider: Optional[Callable[[], Awaitable[AsyncConnection]]] = None
        
        # Callbacks for different events
        self._health_change_callbacks: List[Callable[[str, ConnectionHealthState, ConnectionHealthState], Awaitable[None]]] = []
        self._issue_detected_callbacks: List[Callable[[str, ConnectionIssue], Awaitable[None]]] = []
        self._issue_resolved_callbacks: List[Callable[[str, ConnectionIssue], Awaitable[None]]] = []
        
        # Counters for metrics
        self.total_checks = 0
        self.issues_detected = 0
        self.issues_resolved = 0
        self.connections_monitored = 0
        self.automatic_remediations = 0
    
    def _initialize_remediation_actions(self) -> Dict[ConnectionIssueType, List[str]]:
        """Initialize remediation actions for different issue types."""
        return {
            ConnectionIssueType.LATENCY: [
                "reconnect",
                "reset_connection",
                "notify_administrator",
            ],
            ConnectionIssueType.ERRORS: [
                "reconnect",
                "reset_connection",
                "reset_session_state",
                "notify_administrator",
            ],
            ConnectionIssueType.TIMEOUTS: [
                "reconnect",
                "reset_connection",
                "increase_timeout",
                "notify_administrator",
            ],
            ConnectionIssueType.DEADLOCKS: [
                "reconnect",
                "reset_connection",
                "adjust_retry_strategy",
                "notify_administrator",
            ],
            ConnectionIssueType.DISCONNECTIONS: [
                "reconnect",
                "notify_administrator",
            ],
            ConnectionIssueType.IDLE_IN_TX: [
                "rollback_transaction",
                "reset_connection",
                "notify_administrator",
            ],
            ConnectionIssueType.BLOCKING: [
                "abort_blocking_operation",
                "reset_connection",
                "notify_administrator",
            ],
            ConnectionIssueType.RESOURCE_USAGE: [
                "reconnect",
                "reset_connection",
                "notify_administrator",
            ],
            ConnectionIssueType.LOCKS: [
                "release_locks",
                "reset_connection",
                "notify_administrator",
            ],
            ConnectionIssueType.STALE_STATISTICS: [
                "analyze_table",
                "reconnect",
                "notify_administrator",
            ],
            ConnectionIssueType.CONNECTION_LEAK: [
                "close_connection",
                "reconnect",
                "notify_administrator",
            ],
            ConnectionIssueType.POOL_EXHAUSTION: [
                "increase_pool_size",
                "close_idle_connections",
                "notify_administrator",
            ],
        }
    
    def _initialize_diagnostic_queries(self) -> Dict[str, str]:
        """Initialize diagnostic queries for different aspects of connection health."""
        return {
            "connection_info": """
                SELECT 
                    current_catalog as database,
                    current_user,
                    current_schema,
                    inet_server_addr() as server_ip,
                    inet_server_port() as server_port,
                    version() as server_version
            """,
            "idle_in_transaction": """
                SELECT 
                    pid, 
                    usename, 
                    datname, 
                    state, 
                    query, 
                    backend_start, 
                    xact_start, 
                    EXTRACT(EPOCH FROM now() - xact_start) as transaction_seconds,
                    wait_event_type,
                    wait_event
                FROM pg_stat_activity 
                WHERE pid = pg_backend_pid() 
                  AND state = 'idle in transaction'
            """,
            "transaction_locks": """
                WITH locks AS (
                    SELECT pid, locktype, relation::regclass as table_name, mode, granted
                    FROM pg_locks l 
                    LEFT JOIN pg_database d ON l.database = d.oid 
                    WHERE pid = pg_backend_pid()
                )
                SELECT * FROM locks
            """,
            "blocking_sessions": """
                SELECT blocked.pid as blocked_pid, 
                       blocked.usename as blocked_user,
                       blocking.pid as blocking_pid,
                       blocking.usename as blocking_user,
                       blocked.query as blocked_query,
                       blocking.query as blocking_query
                FROM pg_stat_activity blocked
                JOIN pg_stat_activity blocking ON blocking.pid != blocked.pid
                WHERE blocked.pid = pg_backend_pid() 
                  AND (blocked.state = 'active' OR blocked.state = 'idle in transaction')
                  AND blocked.wait_event_type = 'Lock'
                  AND blocked.wait_event = 'transactionid'
            """,
            "connection_stats": """
                SELECT 
                    backend_start,
                    xact_start,
                    query_start,
                    state_change,
                    wait_event_type,
                    wait_event,
                    state,
                    backend_xid,
                    backend_xmin,
                    query
                FROM pg_stat_activity 
                WHERE pid = pg_backend_pid()
            """,
            "session_parameters": """
                SELECT name, setting, unit 
                FROM pg_settings 
                WHERE name IN (
                    'statement_timeout', 
                    'idle_in_transaction_session_timeout', 
                    'lock_timeout', 
                    'deadlock_timeout',
                    'search_path',
                    'idle_session_timeout',
                    'client_encoding',
                    'client_min_messages'
                )
            """,
            "ping": """
                SELECT 1
            """,
        }
    
    def set_connection_provider(self, provider: Callable[[], Awaitable[AsyncConnection]]) -> None:
        """
        Set a provider function for database connections.
        
        Args:
            provider: Async function that returns a database connection
        """
        self._connection_provider = provider
    
    def register_health_change_callback(
        self,
        callback: Callable[[str, ConnectionHealthState, ConnectionHealthState], Awaitable[None]]
    ) -> None:
        """
        Register a callback for connection health state changes.
        
        Args:
            callback: Async function called with (connection_id, old_state, new_state)
        """
        self._health_change_callbacks.append(callback)
    
    def register_issue_detected_callback(
        self,
        callback: Callable[[str, ConnectionIssue], Awaitable[None]]
    ) -> None:
        """
        Register a callback for issue detection.
        
        Args:
            callback: Async function called with (connection_id, issue)
        """
        self._issue_detected_callbacks.append(callback)
    
    def register_issue_resolved_callback(
        self,
        callback: Callable[[str, ConnectionIssue], Awaitable[None]]
    ) -> None:
        """
        Register a callback for issue resolution.
        
        Args:
            callback: Async function called with (connection_id, issue)
        """
        self._issue_resolved_callbacks.append(callback)
    
    async def record_query(self, connection_id: str, duration: float) -> None:
        """
        Record a query execution for a connection.
        
        Args:
            connection_id: ID of the connection
            duration: Query execution time in seconds
        """
        async with self._lock:
            if connection_id not in self._metrics:
                self._metrics[connection_id] = ConnectionHealthMetrics()
            
            self._metrics[connection_id].record_query(duration)
    
    async def record_error(
        self, 
        connection_id: str, 
        error_type: Optional[str] = None
    ) -> None:
        """
        Record an error for a connection.
        
        Args:
            connection_id: ID of the connection
            error_type: Type of error (timeout, deadlock, etc.)
        """
        async with self._lock:
            if connection_id not in self._metrics:
                self._metrics[connection_id] = ConnectionHealthMetrics()
            
            self._metrics[connection_id].record_error(error_type)
    
    async def record_transaction_start(self, connection_id: str) -> None:
        """
        Record the start of a transaction.
        
        Args:
            connection_id: ID of the connection
        """
        async with self._lock:
            if connection_id not in self._metrics:
                self._metrics[connection_id] = ConnectionHealthMetrics()
            
            self._metrics[connection_id].record_transaction_start()
    
    async def record_transaction_end(
        self,
        connection_id: str,
        success: bool = True
    ) -> None:
        """
        Record the end of a transaction.
        
        Args:
            connection_id: ID of the connection
            success: Whether the transaction was successful (not rolled back)
        """
        async with self._lock:
            if connection_id not in self._metrics:
                self._metrics[connection_id] = ConnectionHealthMetrics()
            
            self._metrics[connection_id].record_transaction_end(success)
    
    async def record_connection_usage(self, connection_id: str) -> None:
        """
        Record connection usage.
        
        Args:
            connection_id: ID of the connection
        """
        async with self._lock:
            if connection_id not in self._metrics:
                self._metrics[connection_id] = ConnectionHealthMetrics()
            
            self._metrics[connection_id].update_usage()
    
    async def ping_connection(
        self,
        connection: AsyncConnection,
        attempts: int = 3
    ) -> Tuple[bool, float]:
        """
        Ping a database connection to measure latency.
        
        Args:
            connection: Database connection to ping
            attempts: Number of ping attempts
            
        Returns:
            Tuple of (success, latency_ms)
        """
        latencies = []
        success = False
        
        for _ in range(attempts):
            start_time = time.time()
            
            try:
                # Use a simple SELECT 1 query with a short timeout
                with contextlib.suppress(asyncio.TimeoutError):
                    async with timeout(2.0):
                        await connection.execute(text(self._diagnostic_queries["ping"]))
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000.0
                latencies.append(latency_ms)
                success = True
            except Exception as e:
                self.logger.warning(f"Ping failed: {str(e)}")
                success = False
        
        # Calculate average latency
        avg_latency = sum(latencies) / len(latencies) if latencies else float('inf')
        
        return success, avg_latency
    
    async def run_diagnostic_query(
        self,
        connection: AsyncConnection,
        query_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Run a diagnostic query on a connection.
        
        Args:
            connection: Database connection
            query_name: Name of the diagnostic query
            
        Returns:
            Query results as a dictionary, or None if the query fails
        """
        if query_name not in self._diagnostic_queries:
            self.logger.warning(f"Unknown diagnostic query: {query_name}")
            return None
        
        query = self._diagnostic_queries[query_name]
        
        try:
            # Execute with timeout to prevent hanging
            with contextlib.suppress(asyncio.TimeoutError):
                async with timeout(5.0):
                    result = await connection.execute(text(query))
                    rows = await result.fetchall()
                    
                    if not rows:
                        return {}
                    
                    # Convert to dictionary
                    keys = result.keys()
                    
                    if len(rows) == 1:
                        # Single row result
                        return dict(zip(keys, rows[0]))
                    else:
                        # Multiple rows
                        return {
                            "rows": [dict(zip(keys, row)) for row in rows]
                        }
        except Exception as e:
            self.logger.warning(f"Diagnostic query {query_name} failed: {str(e)}")
            return None
    
    async def run_diagnostics(
        self,
        connection: AsyncConnection,
        query_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run a set of diagnostic queries on a connection.
        
        Args:
            connection: Database connection
            query_names: List of diagnostic query names to run (all if None)
            
        Returns:
            Dictionary of query results by query name
        """
        if query_names is None:
            query_names = list(self._diagnostic_queries.keys())
        
        results = {}
        
        for query_name in query_names:
            result = await self.run_diagnostic_query(connection, query_name)
            if result is not None:
                results[query_name] = result
        
        return results
    
    async def check_connection_health(
        self,
        connection_id: str,
        connection: AsyncConnection
    ) -> ConnectionHealthAssessment:
        """
        Check the health of a database connection.
        
        Args:
            connection_id: ID of the connection
            connection: Database connection to check
            
        Returns:
            Health assessment for the connection
        """
        # Get existing metrics, or create if doesn't exist
        async with self._lock:
            if connection_id not in self._metrics:
                self._metrics[connection_id] = ConnectionHealthMetrics()
            
            metrics = self._metrics[connection_id]
            metrics.last_checked_at = time.time()
        
        # Run ping test
        ping_success, ping_latency = await self.ping_connection(connection)
        
        if ping_success:
            metrics.record_ping(ping_latency)
        
        # Run diagnostics
        diagnostics = await self.run_diagnostics(connection, [
            "connection_info",
            "connection_stats",
            "session_parameters",
            "idle_in_transaction",
            "transaction_locks",
            "blocking_sessions",
        ])
        
        # Check for idle in transaction
        if (diagnostics.get("idle_in_transaction") and 
                diagnostics["idle_in_transaction"].get("transaction_seconds")):
            transaction_seconds = float(diagnostics["idle_in_transaction"]["transaction_seconds"])
            
            if transaction_seconds > 60.0:  # More than 1 minute idle in transaction
                severity = min(1.0, transaction_seconds / 600.0)  # Scale up to 10 minutes
                
                issue = ConnectionIssue(
                    connection_id=connection_id,
                    issue_type=ConnectionIssueType.IDLE_IN_TX,
                    severity=severity,
                    description=f"Connection idle in transaction for {transaction_seconds:.1f} seconds",
                    context={"transaction_seconds": transaction_seconds},
                )
                
                async with self._lock:
                    if connection_id not in self._issues:
                        self._issues[connection_id] = []
                    
                    self._issues[connection_id].append(issue)
                    self.issues_detected += 1
                
                # Notify callbacks
                for callback in self._issue_detected_callbacks:
                    asyncio.create_task(callback(connection_id, issue))
        
        # Check for locks
        if diagnostics.get("transaction_locks") and "rows" in diagnostics["transaction_locks"]:
            lock_count = len(diagnostics["transaction_locks"]["rows"])
            
            if lock_count > 5:  # More than 5 locks held
                severity = min(0.8, lock_count / 20.0)  # Scale up to 20 locks
                
                issue = ConnectionIssue(
                    connection_id=connection_id,
                    issue_type=ConnectionIssueType.LOCKS,
                    severity=severity,
                    description=f"Connection holding {lock_count} locks",
                    context={"lock_count": lock_count},
                )
                
                async with self._lock:
                    if connection_id not in self._issues:
                        self._issues[connection_id] = []
                    
                    self._issues[connection_id].append(issue)
                    self.issues_detected += 1
                
                # Notify callbacks
                for callback in self._issue_detected_callbacks:
                    asyncio.create_task(callback(connection_id, issue))
        
        # Check for blocking
        if diagnostics.get("blocking_sessions") and "rows" in diagnostics["blocking_sessions"]:
            blocking_count = len(diagnostics["blocking_sessions"]["rows"])
            
            if blocking_count > 0:
                severity = min(0.9, blocking_count / 5.0)  # Scale up to 5 blocked sessions
                
                issue = ConnectionIssue(
                    connection_id=connection_id,
                    issue_type=ConnectionIssueType.BLOCKING,
                    severity=severity,
                    description=f"Connection is blocking {blocking_count} sessions",
                    context={"blocking_count": blocking_count},
                )
                
                async with self._lock:
                    if connection_id not in self._issues:
                        self._issues[connection_id] = []
                    
                    self._issues[connection_id].append(issue)
                    self.issues_detected += 1
                
                # Notify callbacks
                for callback in self._issue_detected_callbacks:
                    asyncio.create_task(callback(connection_id, issue))
        
        # Classify health based on metrics
        state, score, issues = self.classifier.classify_metrics(metrics)
        
        # Fill in connection_id for issues
        for issue in issues:
            issue.connection_id = connection_id
        
        # Record new issues
        async with self._lock:
            if connection_id not in self._issues:
                self._issues[connection_id] = []
            
            # Filter out issues that are already in the list (by type and description)
            existing_issues = {
                (issue.issue_type, issue.description) 
                for issue in self._issues[connection_id] 
                if not issue.resolved
            }
            
            new_issues = [
                issue for issue in issues
                if (issue.issue_type, issue.description) not in existing_issues
            ]
            
            self._issues[connection_id].extend(new_issues)
            self.issues_detected += len(new_issues)
            
            # Check for state change
            old_state = self._connection_states.get(connection_id, ConnectionHealthState.UNKNOWN)
            
            if state != old_state:
                self._connection_states[connection_id] = state
                
                # Notify health change callbacks
                for callback in self._health_change_callbacks:
                    asyncio.create_task(callback(connection_id, old_state, state))
        
        # Generate recommended actions
        recommended_actions = []
        
        if state == ConnectionHealthState.UNHEALTHY:
            recommended_actions.append("reconnect")
            recommended_actions.append("reset_connection")
        elif state == ConnectionHealthState.DEGRADED:
            # Add specific recommendations based on issue types
            for issue in issues:
                if issue.issue_type in self._remediation_actions:
                    actions = self._remediation_actions[issue.issue_type]
                    recommended_actions.extend(actions[:2])  # Add first two actions
        
        # Create health assessment
        assessment = ConnectionHealthAssessment(
            connection_id=connection_id,
            state=state,
            score=score,
            issues=issues,
            metrics=metrics,
            recommended_actions=list(set(recommended_actions)),  # Remove duplicates
        )
        
        # Record in history
        async with self._lock:
            if connection_id not in self._health_history:
                self._health_history[connection_id] = []
            
            self._health_history[connection_id].append(assessment)
            
            # Limit history size
            while len(self._health_history[connection_id]) > 100:
                self._health_history[connection_id].pop(0)
        
        return assessment
    
    async def get_health_assessment(self, connection_id: str) -> Optional[ConnectionHealthAssessment]:
        """
        Get the most recent health assessment for a connection.
        
        Args:
            connection_id: ID of the connection
            
        Returns:
            Most recent health assessment, or None if not available
        """
        async with self._lock:
            history = self._health_history.get(connection_id, [])
            return history[-1] if history else None
    
    async def get_health_history(
        self, 
        connection_id: str,
        limit: int = 100
    ) -> List[ConnectionHealthAssessment]:
        """
        Get the health history for a connection.
        
        Args:
            connection_id: ID of the connection
            limit: Maximum number of assessments to return
            
        Returns:
            List of health assessments, newest first
        """
        async with self._lock:
            history = self._health_history.get(connection_id, [])
            return list(reversed(history[-limit:]))
    
    async def get_issues(
        self, 
        connection_id: str,
        include_resolved: bool = False
    ) -> List[ConnectionIssue]:
        """
        Get issues for a connection.
        
        Args:
            connection_id: ID of the connection
            include_resolved: Whether to include resolved issues
            
        Returns:
            List of issues
        """
        async with self._lock:
            issues = self._issues.get(connection_id, [])
            
            if not include_resolved:
                issues = [issue for issue in issues if not issue.resolved]
            
            return issues
    
    async def resolve_issue(
        self,
        connection_id: str,
        issue_index: int,
        action: str
    ) -> bool:
        """
        Resolve an issue for a connection.
        
        Args:
            connection_id: ID of the connection
            issue_index: Index of the issue in the issues list
            action: Description of the action taken to resolve the issue
            
        Returns:
            True if the issue was resolved, False otherwise
        """
        async with self._lock:
            issues = self._issues.get(connection_id, [])
            
            if not issues or issue_index >= len(issues):
                return False
            
            issue = issues[issue_index]
            
            if issue.resolved:
                return False
            
            issue.resolve(action)
            self.issues_resolved += 1
            
            # Notify callbacks
            for callback in self._issue_resolved_callbacks:
                asyncio.create_task(callback(connection_id, issue))
            
            return True
    
    async def auto_remediate(
        self,
        connection_id: str,
        connection: AsyncConnection
    ) -> List[str]:
        """
        Attempt automatic remediation for connection issues.
        
        Args:
            connection_id: ID of the connection
            connection: Database connection
            
        Returns:
            List of actions taken
        """
        actions_taken = []
        
        # Get health assessment
        assessment = await self.get_health_assessment(connection_id)
        
        if not assessment or assessment.state == ConnectionHealthState.HEALTHY:
            return actions_taken
        
        # Get unresolved issues
        issues = await self.get_issues(connection_id, include_resolved=False)
        
        if not issues:
            return actions_taken
        
        # Sort issues by severity (highest first)
        issues.sort(key=lambda i: i.severity, reverse=True)
        
        for i, issue in enumerate(issues):
            if issue.issue_type == ConnectionIssueType.IDLE_IN_TX:
                # Rollback any idle transactions
                try:
                    await connection.rollback()
                    actions_taken.append("rollback_transaction")
                    await self.resolve_issue(connection_id, i, "rollback_transaction")
                except Exception as e:
                    self.logger.warning(f"Error rolling back transaction: {str(e)}")
            
            elif issue.issue_type == ConnectionIssueType.LOCKS:
                # Try to release locks with a rollback
                try:
                    await connection.rollback()
                    actions_taken.append("release_locks")
                    await self.resolve_issue(connection_id, i, "release_locks")
                except Exception as e:
                    self.logger.warning(f"Error releasing locks: {str(e)}")
        
        # Count remediations
        self.automatic_remediations += len(actions_taken)
        
        return actions_taken
    
    async def start_monitoring(self) -> None:
        """Start the connection health monitoring task."""
        if self._monitoring_task is not None:
            return
        
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(),
            name=f"health_monitor_{self.pool_name}"
        )
        
        self.logger.info(f"Started connection health monitoring for pool {self.pool_name}")
    
    async def stop_monitoring(self) -> None:
        """Stop the connection health monitoring task."""
        if self._monitoring_task is None:
            return
        
        self._monitoring_task.cancel()
        
        with contextlib.suppress(asyncio.CancelledError):
            await self._monitoring_task
        
        self._monitoring_task = None
        
        self.logger.info(f"Stopped connection health monitoring for pool {self.pool_name}")
    
    async def _monitoring_loop(self) -> None:
        """
        Connection health monitoring loop.
        
        Periodically checks the health of all monitored connections.
        """
        try:
            while True:
                # Wait for check interval
                await asyncio.sleep(self.check_interval)
                
                # Skip if no connection provider
                if not self._connection_provider:
                    continue
                
                try:
                    # Get a connection for diagnostics
                    connection = await self._connection_provider()
                    
                    # Run comprehensive diagnostics
                    await self._check_database_health(connection)
                    
                    # Auto-remediate any issues
                    conn_id = f"system_connection_{self.pool_name}"
                    await self.auto_remediate(conn_id, connection)
                    
                except Exception as e:
                    self.logger.error(f"Error in health monitoring loop: {str(e)}")
                
                # Update counters
                self.total_checks += 1
                
        except asyncio.CancelledError:
            # Normal task cancellation
            pass
        
        except Exception as e:
            self.logger.error(
                f"Unexpected error in monitoring loop for pool {self.pool_name}: {str(e)}",
                exc_info=True
            )
    
    async def _check_database_health(self, connection: AsyncConnection) -> None:
        """
        Check overall database health using a connection.
        
        Args:
            connection: Database connection
        """
        conn_id = f"system_connection_{self.pool_name}"
        
        # Check connection health
        assessment = await self.check_connection_health(conn_id, connection)
        
        # Log results
        if assessment.state != ConnectionHealthState.HEALTHY:
            self.logger.warning(
                f"Database health check for pool {self.pool_name}: "
                f"{assessment.state.value} (score: {assessment.score:.2f})"
            )
            
            for issue in assessment.issues:
                self.logger.warning(
                    f"Issue detected: {issue.description} "
                    f"(severity: {issue.severity:.2f})"
                )
        else:
            self.logger.debug(
                f"Database health check for pool {self.pool_name}: "
                f"{assessment.state.value} (score: {assessment.score:.2f})"
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the health monitor.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "pool_name": self.pool_name,
            "total_checks": self.total_checks,
            "issues_detected": self.issues_detected,
            "issues_resolved": self.issues_resolved,
            "connections_monitored": self.connections_monitored,
            "automatic_remediations": self.automatic_remediations,
            "connection_states": {
                conn_id: state.value
                for conn_id, state in self._connection_states.items()
            },
        }


class ConnectionRecycler:
    """
    Connection recycling service.
    
    Automatically recycles database connections based on health assessments,
    age, and usage patterns to maintain connection quality.
    """
    
    def __init__(
        self,
        health_monitor: ConnectionHealthMonitor,
        recycling_interval: float = 300.0,  # 5 minutes
        unhealthy_threshold: float = 0.5,   # Recycle if health score below this
        age_threshold: float = 3600.0,      # Recycle connections older than this (1 hour)
        usage_threshold: int = 10000,       # Recycle after this many queries
        error_threshold: int = 5,           # Recycle after this many errors
        error_rate_threshold: float = 0.01, # Recycle if error rate above this (1%)
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the connection recycler.
        
        Args:
            health_monitor: Connection health monitor
            recycling_interval: Interval between recycling checks (seconds)
            unhealthy_threshold: Health score threshold for recycling
            age_threshold: Connection age threshold for recycling (seconds)
            usage_threshold: Query count threshold for recycling
            error_threshold: Error count threshold for recycling
            error_rate_threshold: Error rate threshold for recycling
            logger: Optional logger for recycling events
        """
        self.health_monitor = health_monitor
        self.recycling_interval = recycling_interval
        self.unhealthy_threshold = unhealthy_threshold
        self.age_threshold = age_threshold
        self.usage_threshold = usage_threshold
        self.error_threshold = error_threshold
        self.error_rate_threshold = error_rate_threshold
        self.logger = logger or logging.getLogger(__name__)
        
        # Recycling task
        self._recycling_task: Optional[asyncio.Task] = None
        
        # Dictionary of connections pending recycling
        self._pending_recycling: Dict[str, str] = {}
        
        # Callbacks
        self._connection_recycled_callbacks: List[Callable[[str, str], Awaitable[None]]] = []
        
        # Metrics
        self.total_recycled = 0
        self.recycling_attempts = 0
        self.recycling_failures = 0
    
    def register_connection_recycled_callback(
        self,
        callback: Callable[[str, str], Awaitable[None]]
    ) -> None:
        """
        Register a callback for connection recycling events.
        
        Args:
            callback: Async function called with (connection_id, reason)
        """
        self._connection_recycled_callbacks.append(callback)
    
    async def mark_for_recycling(
        self,
        connection_id: str,
        reason: str
    ) -> None:
        """
        Mark a connection for recycling.
        
        Args:
            connection_id: ID of the connection
            reason: Reason for recycling
        """
        self._pending_recycling[connection_id] = reason
        self.logger.info(f"Marked connection {connection_id} for recycling: {reason}")
    
    async def start_recycling(self) -> None:
        """Start the connection recycling task."""
        if self._recycling_task is not None:
            return
        
        self._recycling_task = asyncio.create_task(
            self._recycling_loop(),
            name=f"recycler_{self.health_monitor.pool_name}"
        )
        
        self.logger.info(f"Started connection recycling for pool {self.health_monitor.pool_name}")
    
    async def stop_recycling(self) -> None:
        """Stop the connection recycling task."""
        if self._recycling_task is None:
            return
        
        self._recycling_task.cancel()
        
        with contextlib.suppress(asyncio.CancelledError):
            await self._recycling_task
        
        self._recycling_task = None
        
        self.logger.info(f"Stopped connection recycling for pool {self.health_monitor.pool_name}")
    
    async def _recycling_loop(self) -> None:
        """
        Connection recycling loop.
        
        Periodically checks for connections that need recycling.
        """
        try:
            while True:
                # Wait for recycling interval
                await asyncio.sleep(self.recycling_interval)
                
                try:
                    # Check for connections to recycle
                    await self._check_connections_for_recycling()
                    
                    # Process pending recycling
                    await self._process_pending_recycling()
                    
                except Exception as e:
                    self.logger.error(f"Error in recycling loop: {str(e)}")
                    
                # Update metrics
                self.recycling_attempts += 1
                
        except asyncio.CancelledError:
            # Normal task cancellation
            pass
        
        except Exception as e:
            self.logger.error(
                f"Unexpected error in recycling loop for pool {self.health_monitor.pool_name}: {str(e)}",
                exc_info=True
            )
    
    async def _check_connections_for_recycling(self) -> None:
        """Check for connections that need recycling based on health metrics."""
        # Get all connection IDs with metrics
        async with self.health_monitor._lock:
            connection_ids = list(self.health_monitor._metrics.keys())
        
        for conn_id in connection_ids:
            # Skip if already pending recycling
            if conn_id in self._pending_recycling:
                continue
            
            # Get health assessment
            assessment = await self.health_monitor.get_health_assessment(conn_id)
            
            if not assessment:
                continue
            
            # Check health score
            if assessment.score < self.unhealthy_threshold:
                await self.mark_for_recycling(
                    conn_id,
                    f"Unhealthy connection (score: {assessment.score:.2f})"
                )
                continue
            
            # Get metrics
            metrics = assessment.metrics
            
            if not metrics:
                continue
            
            # Check age
            age = metrics.get_age()
            if age > self.age_threshold:
                await self.mark_for_recycling(
                    conn_id,
                    f"Connection too old (age: {age:.1f}s)"
                )
                continue
            
            # Check query count
            if metrics.query_count > self.usage_threshold:
                await self.mark_for_recycling(
                    conn_id,
                    f"High query count (count: {metrics.query_count})"
                )
                continue
            
            # Check error count and rate
            if metrics.error_count > self.error_threshold:
                await self.mark_for_recycling(
                    conn_id,
                    f"Too many errors (count: {metrics.error_count})"
                )
                continue
            
            error_rate = metrics.get_error_rate()
            if error_rate > self.error_rate_threshold:
                await self.mark_for_recycling(
                    conn_id,
                    f"High error rate (rate: {error_rate:.1%})"
                )
                continue
    
    async def _process_pending_recycling(self) -> None:
        """Process connections pending recycling."""
        # Make a copy to avoid modification during iteration
        pending = dict(self._pending_recycling)
        
        for conn_id, reason in pending.items():
            # Notify callbacks
            for callback in self._connection_recycled_callbacks:
                try:
                    await callback(conn_id, reason)
                    
                    # Remove from pending
                    self._pending_recycling.pop(conn_id, None)
                    
                    # Update metrics
                    self.total_recycled += 1
                    
                    self.logger.info(f"Recycled connection {conn_id}: {reason}")
                    
                except Exception as e:
                    self.logger.error(f"Error recycling connection {conn_id}: {str(e)}")
                    self.recycling_failures += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the connection recycler.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "pool_name": self.health_monitor.pool_name,
            "total_recycled": self.total_recycled,
            "recycling_attempts": self.recycling_attempts,
            "recycling_failures": self.recycling_failures,
            "pending_recycling": len(self._pending_recycling),
        }


async def setup_connection_health_monitoring(
    pool_name: str,
    recycling_callback: Callable[[str, str], Awaitable[None]],
    connection_provider: Callable[[], Awaitable[AsyncConnection]],
    logger: Optional[logging.Logger] = None,
) -> Tuple[ConnectionHealthMonitor, ConnectionRecycler]:
    """
    Set up connection health monitoring and recycling.
    
    Args:
        pool_name: Name of the connection pool
        recycling_callback: Callback for connection recycling events
        connection_provider: Provider for database connections
        logger: Optional logger for monitoring events
        
    Returns:
        Tuple of (health_monitor, recycler)
    """
    # Create the health monitor
    health_monitor = ConnectionHealthMonitor(
        pool_name=pool_name,
        logger=logger,
    )
    
    # Set connection provider
    health_monitor.set_connection_provider(connection_provider)
    
    # Create the recycler
    recycler = ConnectionRecycler(
        health_monitor=health_monitor,
        logger=logger,
    )
    
    # Register recycling callback
    recycler.register_connection_recycled_callback(recycling_callback)
    
    # Start monitoring and recycling
    await health_monitor.start_monitoring()
    await recycler.start_recycling()
    
    return health_monitor, recycler