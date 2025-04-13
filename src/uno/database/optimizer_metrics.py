"""
Metrics collection and monitoring for the query optimizer.

This module provides tools to collect, aggregate, and visualize metrics 
from the query optimizer for performance monitoring and improvement tracking.
"""

from typing import Dict, Any, List, Optional, Union, Set, Tuple, TypeVar, Generic, Callable
import time
import json
import logging
import asyncio
import datetime
from dataclasses import dataclass, field
from enum import Enum
import statistics
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.query_optimizer import (
    QueryComplexity,
    OptimizationLevel,
    QueryPlan,
    QueryStatistics,
    OptimizationConfig,
    QueryOptimizer,
)
from uno.core.monitoring.metrics import MetricsRegistry as MetricsManager, MetricType


class MetricSource(Enum):
    """Source of query optimizer metrics."""
    
    OPTIMIZER = "optimizer"           # General optimizer metrics
    QUERY_EXECUTION = "execution"     # Query execution statistics
    INDEX_USAGE = "index_usage"       # Index usage statistics
    RECOMMENDATIONS = "recommendations"  # Optimizer recommendations
    REWRITES = "rewrites"             # Query rewrites
    TABLE_STATS = "table_stats"       # Table statistics


@dataclass
class OptimizerMetricsSnapshot:
    """
    Snapshot of query optimizer metrics.
    
    Contains aggregated metrics from the optimizer.
    """
    
    # Timestamp
    timestamp: float = field(default_factory=time.time)
    
    # Query statistics
    query_count: int = 0
    slow_query_count: int = 0
    very_slow_query_count: int = 0
    avg_execution_time: float = 0.0
    p50_execution_time: float = 0.0
    p90_execution_time: float = 0.0
    p95_execution_time: float = 0.0
    p99_execution_time: float = 0.0
    
    # Complexity distribution
    simple_queries: int = 0
    moderate_queries: int = 0
    complex_queries: int = 0
    very_complex_queries: int = 0
    
    # Optimizer recommendations
    index_recommendations: int = 0
    implemented_indexes: int = 0
    query_rewrites: int = 0
    applied_rewrites: int = 0
    
    # Table statistics
    tables_analyzed: int = 0
    maintenance_recommendations: int = 0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_optimizer(cls, optimizer: QueryOptimizer) -> "OptimizerMetricsSnapshot":
        """
        Create a metrics snapshot from an optimizer instance.
        
        Args:
            optimizer: The query optimizer to collect metrics from
            
        Returns:
            Metrics snapshot with data from the optimizer
        """
        snapshot = cls()
        
        # Query statistics
        query_stats = optimizer.get_statistics()
        snapshot.query_count = len(query_stats)
        
        # Extract execution times for percentile calculations
        execution_times = []
        
        for query_hash, stats in query_stats.items():
            execution_times.append(stats.avg_execution_time)
            
            # Classify by complexity
            if stats.latest_plan:
                complexity = stats.latest_plan.complexity
                if complexity == QueryComplexity.SIMPLE:
                    snapshot.simple_queries += 1
                elif complexity == QueryComplexity.MODERATE:
                    snapshot.moderate_queries += 1
                elif complexity == QueryComplexity.COMPLEX:
                    snapshot.complex_queries += 1
                elif complexity == QueryComplexity.VERY_COMPLEX:
                    snapshot.very_complex_queries += 1
        
        # Calculate execution time statistics if we have data
        if execution_times:
            snapshot.avg_execution_time = sum(execution_times) / len(execution_times)
            
            # Calculate percentiles
            execution_times.sort()
            snapshot.p50_execution_time = cls._percentile(execution_times, 50)
            snapshot.p90_execution_time = cls._percentile(execution_times, 90)
            snapshot.p95_execution_time = cls._percentile(execution_times, 95)
            snapshot.p99_execution_time = cls._percentile(execution_times, 99)
        
        # Slow query statistics
        snapshot.slow_query_count = len(optimizer.get_slow_queries())
        snapshot.very_slow_query_count = len(
            optimizer.get_slow_queries(optimizer.config.very_slow_query_threshold)
        )
        
        # Recommendations
        snapshot.index_recommendations = len(optimizer._index_recommendations)
        snapshot.implemented_indexes = sum(
            1 for rec in optimizer._index_recommendations if rec.implemented
        )
        snapshot.query_rewrites = len(optimizer._query_rewrites)
        
        return snapshot
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """
        Calculate a percentile from a sorted list.
        
        Args:
            data: Sorted list of values
            percentile: The percentile to calculate (0-100)
            
        Returns:
            The percentile value
        """
        if not data:
            return 0.0
        
        index = (len(data) - 1) * percentile / 100
        if index.is_integer():
            return data[int(index)]
        else:
            lower = data[int(index)]
            upper = data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class OptimizerMetricsCollector:
    """
    Metrics collector for the query optimizer.
    
    Collects and aggregates metrics from query optimizer usage.
    """
    
    def __init__(
        self,
        metrics_manager: Optional[MetricsManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the metrics collector.
        
        Args:
            metrics_manager: Optional metrics manager for reporting
            logger: Optional logger instance
        """
        self.metrics_manager = metrics_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # Metrics snapshots
        self._snapshots: List[OptimizerMetricsSnapshot] = []
        self._snapshot_interval = 300  # 5 minutes
        self._max_snapshots = 288  # 24 hours at 5-minute intervals
        
        # Metrics registration
        if self.metrics_manager:
            self._register_metrics()
    
    def _register_metrics(self) -> None:
        """Register metrics with the metrics manager."""
        prefix = "query_optimizer"
        
        # Query counts
        self.metrics_manager.register_metric(
            f"{prefix}.query_count",
            "Number of unique queries tracked by the optimizer",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.slow_query_count",
            "Number of slow queries detected",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.very_slow_query_count",
            "Number of very slow queries detected",
            MetricType.GAUGE,
        )
        
        # Execution times
        self.metrics_manager.register_metric(
            f"{prefix}.avg_execution_time",
            "Average query execution time in seconds",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.p90_execution_time",
            "90th percentile query execution time in seconds",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.p95_execution_time",
            "95th percentile query execution time in seconds",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.p99_execution_time",
            "99th percentile query execution time in seconds",
            MetricType.GAUGE,
        )
        
        # Complexity distribution
        self.metrics_manager.register_metric(
            f"{prefix}.simple_queries",
            "Number of simple queries",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.complex_queries",
            "Number of complex queries",
            MetricType.GAUGE,
        )
        
        # Recommendations
        self.metrics_manager.register_metric(
            f"{prefix}.index_recommendations",
            "Number of index recommendations",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.implemented_indexes",
            "Number of implemented index recommendations",
            MetricType.GAUGE,
        )
        self.metrics_manager.register_metric(
            f"{prefix}.query_rewrites",
            "Number of query rewrites",
            MetricType.GAUGE,
        )
    
    def collect_metrics(self, optimizer: QueryOptimizer) -> OptimizerMetricsSnapshot:
        """
        Collect metrics from an optimizer instance.
        
        Args:
            optimizer: The query optimizer to collect metrics from
            
        Returns:
            Metrics snapshot
        """
        # Create a snapshot
        snapshot = OptimizerMetricsSnapshot.from_optimizer(optimizer)
        
        # Store snapshot
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)  # Remove oldest snapshot
        
        # Report metrics if metrics manager is available
        if self.metrics_manager:
            self._report_metrics(snapshot)
        
        return snapshot
    
    def _report_metrics(self, snapshot: OptimizerMetricsSnapshot) -> None:
        """
        Report metrics to the metrics manager.
        
        Args:
            snapshot: The metrics snapshot to report
        """
        prefix = "query_optimizer"
        
        # Query counts
        self.metrics_manager.record_metric(
            f"{prefix}.query_count", snapshot.query_count
        )
        self.metrics_manager.record_metric(
            f"{prefix}.slow_query_count", snapshot.slow_query_count
        )
        self.metrics_manager.record_metric(
            f"{prefix}.very_slow_query_count", snapshot.very_slow_query_count
        )
        
        # Execution times
        self.metrics_manager.record_metric(
            f"{prefix}.avg_execution_time", snapshot.avg_execution_time
        )
        self.metrics_manager.record_metric(
            f"{prefix}.p90_execution_time", snapshot.p90_execution_time
        )
        self.metrics_manager.record_metric(
            f"{prefix}.p95_execution_time", snapshot.p95_execution_time
        )
        self.metrics_manager.record_metric(
            f"{prefix}.p99_execution_time", snapshot.p99_execution_time
        )
        
        # Complexity distribution
        self.metrics_manager.record_metric(
            f"{prefix}.simple_queries", snapshot.simple_queries
        )
        self.metrics_manager.record_metric(
            f"{prefix}.moderate_queries", snapshot.moderate_queries
        )
        self.metrics_manager.record_metric(
            f"{prefix}.complex_queries", snapshot.complex_queries
        )
        self.metrics_manager.record_metric(
            f"{prefix}.very_complex_queries", snapshot.very_complex_queries
        )
        
        # Recommendations
        self.metrics_manager.record_metric(
            f"{prefix}.index_recommendations", snapshot.index_recommendations
        )
        self.metrics_manager.record_metric(
            f"{prefix}.implemented_indexes", snapshot.implemented_indexes
        )
        self.metrics_manager.record_metric(
            f"{prefix}.query_rewrites", snapshot.query_rewrites
        )
    
    def get_snapshots(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[OptimizerMetricsSnapshot]:
        """
        Get metrics snapshots for a time range.
        
        Args:
            start_time: Optional start time (epoch seconds)
            end_time: Optional end time (epoch seconds)
            
        Returns:
            List of metrics snapshots
        """
        if start_time is None and end_time is None:
            return list(self._snapshots)
        
        filtered_snapshots = []
        for snapshot in self._snapshots:
            if start_time is not None and snapshot.timestamp < start_time:
                continue
            if end_time is not None and snapshot.timestamp > end_time:
                continue
            filtered_snapshots.append(snapshot)
        
        return filtered_snapshots
    
    def get_latest_snapshot(self) -> Optional[OptimizerMetricsSnapshot]:
        """
        Get the latest metrics snapshot.
        
        Returns:
            Latest metrics snapshot or None if no snapshots
        """
        if not self._snapshots:
            return None
        return self._snapshots[-1]
    
    def generate_report(
        self,
        optimizer: Optional[QueryOptimizer] = None,
        time_range: Optional[Tuple[float, float]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a metrics report.
        
        Args:
            optimizer: Optional optimizer to include current metrics
            time_range: Optional time range as (start_time, end_time)
            
        Returns:
            Dictionary with metrics report
        """
        # Get snapshots for the time range
        if time_range:
            start_time, end_time = time_range
            snapshots = self.get_snapshots(start_time, end_time)
        else:
            snapshots = self._snapshots
        
        # Include current metrics if optimizer provided
        if optimizer:
            current_snapshot = OptimizerMetricsSnapshot.from_optimizer(optimizer)
            snapshots = snapshots + [current_snapshot]
        
        if not snapshots:
            return {"error": "No metrics available for the specified time range"}
        
        # Generate the report
        report = {
            "time_range": {
                "start": snapshots[0].timestamp,
                "end": snapshots[-1].timestamp,
                "duration_hours": (snapshots[-1].timestamp - snapshots[0].timestamp) / 3600,
            },
            "snapshot_count": len(snapshots),
        }
        
        # Latest metrics
        latest = snapshots[-1]
        report["latest"] = {
            "timestamp": latest.timestamp,
            "query_count": latest.query_count,
            "slow_query_count": latest.slow_query_count,
            "very_slow_query_count": latest.very_slow_query_count,
            "avg_execution_time": latest.avg_execution_time,
            "complexity_distribution": {
                "simple": latest.simple_queries,
                "moderate": latest.moderate_queries,
                "complex": latest.complex_queries,
                "very_complex": latest.very_complex_queries,
            },
            "recommendations": {
                "index_recommendations": latest.index_recommendations,
                "implemented_indexes": latest.implemented_indexes,
                "query_rewrites": latest.query_rewrites,
                "applied_rewrites": latest.applied_rewrites,
            }
        }
        
        # Historical trends
        if len(snapshots) > 1:
            # Calculate changes over time
            first = snapshots[0]
            report["trends"] = {
                "query_count_change": latest.query_count - first.query_count,
                "slow_query_change": latest.slow_query_count - first.slow_query_count,
                "very_slow_query_change": latest.very_slow_query_count - first.very_slow_query_count,
                "avg_execution_time_change": latest.avg_execution_time - first.avg_execution_time,
                "index_recommendations_change": latest.index_recommendations - first.index_recommendations,
                "implemented_indexes_change": latest.implemented_indexes - first.implemented_indexes,
            }
            
            # Calculate percentage changes
            if first.query_count > 0:
                report["trends"]["query_count_pct_change"] = (
                    (latest.query_count - first.query_count) / first.query_count * 100
                )
            
            if first.slow_query_count > 0:
                report["trends"]["slow_query_pct_change"] = (
                    (latest.slow_query_count - first.slow_query_count) / first.slow_query_count * 100
                )
            
            if first.avg_execution_time > 0:
                report["trends"]["avg_execution_time_pct_change"] = (
                    (latest.avg_execution_time - first.avg_execution_time) / first.avg_execution_time * 100
                )
        
        return report


class OptimizerMetricsMiddleware:
    """
    Middleware for collecting query optimizer metrics.
    
    Can be used with FastAPI or other frameworks to collect metrics
    from query optimizer usage.
    """
    
    def __init__(
        self,
        metrics_collector: OptimizerMetricsCollector,
        optimizer_factory: Callable[[], QueryOptimizer],
    ):
        """
        Initialize the metrics middleware.
        
        Args:
            metrics_collector: The metrics collector
            optimizer_factory: Function that returns the optimizer instance
        """
        self.metrics_collector = metrics_collector
        self.optimizer_factory = optimizer_factory
        self.collection_interval = 60  # 1 minute
        self._last_collection_time = 0
    
    async def __call__(self, request, call_next):
        """
        Process a request and collect metrics.
        
        Args:
            request: The request
            call_next: Function to call the next middleware
            
        Returns:
            Response
        """
        # Process the request
        response = await call_next(request)
        
        # Check if it's time to collect metrics
        current_time = time.time()
        if current_time - self._last_collection_time >= self.collection_interval:
            # Collect metrics asynchronously to avoid blocking
            asyncio.create_task(self._collect_metrics())
            self._last_collection_time = current_time
        
        return response
    
    async def _collect_metrics(self):
        """Collect metrics from the optimizer."""
        try:
            optimizer = self.optimizer_factory()
            self.metrics_collector.collect_metrics(optimizer)
        except Exception as e:
            logging.error(f"Error collecting optimizer metrics: {e}")


def track_query_performance(
    metrics_collector: OptimizerMetricsCollector,
    optimizer: QueryOptimizer,
):
    """
    Decorator that tracks query performance in a function.
    
    Args:
        metrics_collector: The metrics collector
        optimizer: The query optimizer
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record execution time for the function's query
            # This is a simplified approach - in a real implementation,
            # we would need to extract the actual query
            query_hash = f"func:{func.__name__}"
            if query_hash not in optimizer._query_stats:
                optimizer._query_stats[query_hash] = QueryStatistics(
                    query_hash=query_hash,
                    query_text=f"Function: {func.__name__}",
                )
            
            optimizer._query_stats[query_hash].record_execution(execution_time, 0)
            
            # Collect metrics periodically
            current_time = time.time()
            if not hasattr(track_query_performance, "_last_collection_time") or \
               current_time - track_query_performance._last_collection_time >= 60:
                metrics_collector.collect_metrics(optimizer)
                track_query_performance._last_collection_time = current_time
            
            return result
        
        return wrapper
    
    return decorator


def with_query_metrics(
    optimizer: QueryOptimizer,
    metrics_collector: Optional[OptimizerMetricsCollector] = None,
):
    """
    Decorator that collects metrics for a query function.
    
    Args:
        optimizer: The query optimizer
        metrics_collector: Optional metrics collector
        
    Returns:
        Decorator function
    """
    # Create a metrics collector if none provided
    if metrics_collector is None:
        metrics_collector = OptimizerMetricsCollector()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find session in args or kwargs
            session = None
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break
            
            if session is None and "session" in kwargs:
                session = kwargs["session"]
            
            # Execute the function with optimizer if session is available
            if session and optimizer.session != session:
                # Update optimizer session
                optimizer.session = session
            
            # Execute the query function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record metrics
            function_name = func.__name__
            if hasattr(func, "__qualname__"):
                function_name = func.__qualname__
            
            # Add metadata for the collector
            metrics_collector.collect_metrics(optimizer).metadata.update({
                "last_function": function_name,
                "last_execution_time": execution_time,
                "timestamp": time.time(),
            })
            
            return result
        
        return wrapper
    
    return decorator


# Global metrics collector instance
_default_metrics_collector = OptimizerMetricsCollector()

def get_metrics_collector() -> OptimizerMetricsCollector:
    """
    Get the default metrics collector.
    
    Returns:
        Default metrics collector
    """
    return _default_metrics_collector


def set_metrics_collector(collector: OptimizerMetricsCollector) -> None:
    """
    Set the default metrics collector.
    
    Args:
        collector: The new default metrics collector
    """
    global _default_metrics_collector
    _default_metrics_collector = collector


async def collect_optimizer_metrics(
    optimizer: QueryOptimizer,
    metrics_collector: Optional[OptimizerMetricsCollector] = None,
) -> OptimizerMetricsSnapshot:
    """
    Collect metrics from an optimizer instance.
    
    Args:
        optimizer: The query optimizer to collect metrics from
        metrics_collector: Optional metrics collector (uses default if None)
        
    Returns:
        Metrics snapshot
    """
    collector = metrics_collector or _default_metrics_collector
    return collector.collect_metrics(optimizer)