"""
Performance metric collectors for Uno applications.

This module provides collectors for gathering performance metrics from various sources
such as SQL queries, HTTP endpoints, and memory usage.
"""

import time
import logging
import threading
import statistics
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class QueryMetric:
    """Metric for a SQL query."""
    
    query: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    stacktrace: Optional[List[str]] = None
    db_name: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    rows_affected: Optional[int] = None
    rows_returned: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "params": self.params,
            "stacktrace": self.stacktrace,
            "db_name": self.db_name,
            "success": self.success,
            "error": self.error,
            "rows_affected": self.rows_affected,
            "rows_returned": self.rows_returned,
        }


@dataclass
class EndpointMetric:
    """Metric for an HTTP endpoint."""
    
    path: str
    method: str
    duration: float
    status_code: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    query_count: Optional[int] = None
    query_time: Optional[float] = None
    response_size: Optional[int] = None
    client_ip: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "method": self.method,
            "duration": self.duration,
            "status_code": self.status_code,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "request_id": self.request_id,
            "params": self.params,
            "query_count": self.query_count,
            "query_time": self.query_time,
            "response_size": self.response_size,
            "client_ip": self.client_ip,
        }


@dataclass
class MemoryMetric:
    """Metric for memory usage."""
    
    total: int
    available: int
    percent: float
    used: int
    free: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    process_rss: Optional[int] = None
    process_vms: Optional[int] = None
    process_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total": self.total,
            "available": self.available,
            "percent": self.percent,
            "used": self.used,
            "free": self.free,
            "timestamp": self.timestamp.isoformat(),
            "process_rss": self.process_rss,
            "process_vms": self.process_vms,
            "process_percent": self.process_percent,
        }


@dataclass
class CPUMetric:
    """Metric for CPU usage."""
    
    percent: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    system: Optional[float] = None
    user: Optional[float] = None
    idle: Optional[float] = None
    process_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "percent": self.percent,
            "timestamp": self.timestamp.isoformat(),
            "system": self.system,
            "user": self.user,
            "idle": self.idle,
            "process_percent": self.process_percent,
        }


@dataclass
class FunctionMetric:
    """Metric for function execution."""
    
    name: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    module: Optional[str] = None
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    stacktrace: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "module": self.module,
            "args": str(self.args) if self.args else None,
            "kwargs": str(self.kwargs) if self.kwargs else None,
            "result": str(self.result) if self.result is not None else None,
            "error": self.error,
            "stacktrace": self.stacktrace,
        }


class MetricCollector:
    """
    Base class for metric collectors.
    
    This class provides a foundation for collecting and storing metrics
    with optional periodic reporting and storage capabilities.
    """
    
    def __init__(
        self,
        name: str,
        capacity: int = 1000,
        report_interval: Optional[int] = None,
        report_callback: Optional[Callable[[List[Any]], None]] = None,
    ):
        """
        Initialize the collector.
        
        Args:
            name: Name of the collector
            capacity: Maximum number of metrics to store
            report_interval: Interval in seconds for reporting metrics
            report_callback: Callback function for reporting metrics
        """
        self.name = name
        self.capacity = capacity
        self.metrics: List[Any] = []
        self.lock = threading.RLock()
        self.report_interval = report_interval
        self.report_callback = report_callback
        self.reporting_thread = None
        self.stop_reporting = threading.Event()
        
        # Start reporting if interval is provided
        if report_interval and report_callback:
            self._start_reporting()
    
    def add_metric(self, metric: Any) -> None:
        """
        Add a metric to the collector.
        
        Args:
            metric: Metric to add
        """
        with self.lock:
            self.metrics.append(metric)
            
            # Remove oldest metrics if capacity is exceeded
            if len(self.metrics) > self.capacity:
                self.metrics = self.metrics[-self.capacity:]
    
    def get_metrics(self) -> List[Any]:
        """
        Get all metrics.
        
        Returns:
            List of metrics
        """
        with self.lock:
            return self.metrics.copy()
    
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        with self.lock:
            self.metrics = []
    
    def _start_reporting(self) -> None:
        """Start periodic reporting."""
        if self.reporting_thread and self.reporting_thread.is_alive():
            return
        
        self.stop_reporting.clear()
        self.reporting_thread = threading.Thread(
            target=self._reporting_loop,
            daemon=True,
            name=f"{self.name}-reporter",
        )
        self.reporting_thread.start()
    
    def _stop_reporting(self) -> None:
        """Stop periodic reporting."""
        if self.reporting_thread and self.reporting_thread.is_alive():
            self.stop_reporting.set()
            self.reporting_thread.join(timeout=1.0)
    
    def _reporting_loop(self) -> None:
        """Reporting loop."""
        while not self.stop_reporting.is_set():
            time.sleep(self.report_interval)
            
            with self.lock:
                metrics = self.metrics.copy()
                self.metrics = []
            
            if metrics and self.report_callback:
                try:
                    self.report_callback(metrics)
                except Exception as e:
                    logger.exception(f"Error in reporting callback: {e}")
    
    def __del__(self) -> None:
        """Cleanup resources."""
        self._stop_reporting()


class QueryCollector(MetricCollector):
    """Collector for SQL query metrics."""
    
    def __init__(
        self,
        capacity: int = 1000,
        report_interval: Optional[int] = None,
        report_callback: Optional[Callable[[List[QueryMetric]], None]] = None,
        slow_query_threshold: float = 1.0,
    ):
        """
        Initialize the collector.
        
        Args:
            capacity: Maximum number of metrics to store
            report_interval: Interval in seconds for reporting metrics
            report_callback: Callback function for reporting metrics
            slow_query_threshold: Threshold in seconds for identifying slow queries
        """
        super().__init__("query-collector", capacity, report_interval, report_callback)
        self.slow_query_threshold = slow_query_threshold
        self.query_patterns: Dict[str, List[float]] = {}
        self.similar_queries: Dict[str, Set[str]] = {}
    
    def add_query(self, query: str, duration: float, **kwargs) -> QueryMetric:
        """
        Add a query metric.
        
        Args:
            query: SQL query
            duration: Query duration in seconds
            **kwargs: Additional query metadata
            
        Returns:
            QueryMetric object
        """
        metric = QueryMetric(query=query, duration=duration, **kwargs)
        self.add_metric(metric)
        
        # Update query patterns
        self._update_patterns(query, duration)
        
        # Log slow queries
        if duration >= self.slow_query_threshold:
            logger.warning(f"Slow query detected ({duration:.3f}s): {query}")
        
        return metric
    
    def _update_patterns(self, query: str, duration: float) -> None:
        """
        Update query patterns.
        
        Args:
            query: SQL query
            duration: Query duration in seconds
        """
        # Simplify query by removing literals
        pattern = self._extract_query_pattern(query)
        
        with self.lock:
            if pattern not in self.query_patterns:
                self.query_patterns[pattern] = []
            
            self.query_patterns[pattern].append(duration)
            
            # Keep only the last 100 durations
            if len(self.query_patterns[pattern]) > 100:
                self.query_patterns[pattern] = self.query_patterns[pattern][-100:]
            
            # Update similar queries
            if pattern not in self.similar_queries:
                self.similar_queries[pattern] = set()
            self.similar_queries[pattern].add(query)
    
    def _extract_query_pattern(self, query: str) -> str:
        """
        Extract query pattern by removing literals.
        
        Args:
            query: SQL query
            
        Returns:
            Query pattern
        """
        # Simple implementation - replace numbers and strings with placeholders
        # A more robust implementation would use a SQL parser
        import re
        pattern = query.strip()
        pattern = re.sub(r"'[^']*'", "'?'", pattern)
        pattern = re.sub(r'"[^"]*"', '"?"', pattern)
        pattern = re.sub(r"\b\d+\b", "?", pattern)
        return pattern
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[QueryMetric]:
        """
        Get slow queries.
        
        Args:
            threshold: Optional threshold in seconds, defaults to self.slow_query_threshold
            
        Returns:
            List of slow query metrics
        """
        if threshold is None:
            threshold = self.slow_query_threshold
        
        with self.lock:
            return [m for m in self.metrics if m.duration >= threshold]
    
    def get_query_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Get query patterns with statistics.
        
        Returns:
            Dictionary of query patterns with statistics
        """
        result = {}
        
        with self.lock:
            for pattern, durations in self.query_patterns.items():
                if not durations:
                    continue
                
                result[pattern] = {
                    "count": len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "avg": sum(durations) / len(durations),
                    "median": statistics.median(durations),
                    "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
                    "similar_queries": list(self.similar_queries.get(pattern, set())),
                }
        
        return result
    
    def analyze_queries(self) -> Dict[str, Any]:
        """
        Analyze queries for patterns and issues.
        
        Returns:
            Dictionary with analysis results
        """
        with self.lock:
            slow_queries = self.get_slow_queries()
            patterns = self.get_query_patterns()
            
            # Find potential N+1 queries
            n_plus_1_candidates = {}
            for pattern, stats in patterns.items():
                if stats["count"] <= 5:
                    continue
                
                # Check for similar patterns with high occurrence count
                similar_patterns = []
                for p, s in patterns.items():
                    if p != pattern and self._are_patterns_similar(p, pattern) and s["count"] > 5:
                        similar_patterns.append((p, s))
                
                if similar_patterns:
                    n_plus_1_candidates[pattern] = {
                        "pattern": pattern,
                        "count": stats["count"],
                        "similar_patterns": [
                            {"pattern": p, "count": s["count"]} for p, s in similar_patterns
                        ],
                    }
            
            return {
                "total_queries": len(self.metrics),
                "unique_patterns": len(patterns),
                "slow_queries": [m.to_dict() for m in slow_queries],
                "patterns": patterns,
                "n_plus_1_candidates": n_plus_1_candidates,
            }
    
    def _are_patterns_similar(self, pattern1: str, pattern2: str) -> bool:
        """
        Check if two query patterns are similar.
        
        Args:
            pattern1: First query pattern
            pattern2: Second query pattern
            
        Returns:
            True if patterns are similar, False otherwise
        """
        # Simple implementation - check if patterns are similar enough
        # A more robust implementation would use a SQL parser
        
        # Remove whitespace and case sensitivity
        p1 = pattern1.lower().strip()
        p2 = pattern2.lower().strip()
        
        # If one is SELECT and one is SELECT COUNT, they're probably related
        if (p1.startswith("select ") and p2.startswith("select count(")) or \
           (p2.startswith("select ") and p1.startswith("select count(")):
            return True
        
        # If they have same WHERE clause structure but different SELECT, might be related
        if "where" in p1 and "where" in p2:
            where1 = p1.split("where", 1)[1]
            where2 = p2.split("where", 1)[1]
            
            # Simple similarity check
            similarity = self._text_similarity(where1, where2)
            return similarity > 0.7
        
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple implementation using Jaccard similarity of words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


class EndpointCollector(MetricCollector):
    """Collector for HTTP endpoint metrics."""
    
    def __init__(
        self,
        capacity: int = 1000,
        report_interval: Optional[int] = None,
        report_callback: Optional[Callable[[List[EndpointMetric]], None]] = None,
        slow_endpoint_threshold: float = 1.0,
    ):
        """
        Initialize the collector.
        
        Args:
            capacity: Maximum number of metrics to store
            report_interval: Interval in seconds for reporting metrics
            report_callback: Callback function for reporting metrics
            slow_endpoint_threshold: Threshold in seconds for identifying slow endpoints
        """
        super().__init__("endpoint-collector", capacity, report_interval, report_callback)
        self.slow_endpoint_threshold = slow_endpoint_threshold
        self.endpoint_stats: Dict[str, Dict[str, Any]] = {}
    
    def add_endpoint_metric(
        self, path: str, method: str, duration: float, status_code: int, **kwargs
    ) -> EndpointMetric:
        """
        Add an endpoint metric.
        
        Args:
            path: Endpoint path
            method: HTTP method
            duration: Request duration in seconds
            status_code: HTTP status code
            **kwargs: Additional metric metadata
            
        Returns:
            EndpointMetric object
        """
        metric = EndpointMetric(
            path=path,
            method=method,
            duration=duration,
            status_code=status_code,
            **kwargs
        )
        self.add_metric(metric)
        
        # Update endpoint statistics
        self._update_stats(path, method, duration, status_code)
        
        # Log slow endpoints
        if duration >= self.slow_endpoint_threshold:
            logger.warning(f"Slow endpoint detected ({duration:.3f}s): {method} {path}")
        
        return metric
    
    def _update_stats(self, path: str, method: str, duration: float, status_code: int) -> None:
        """
        Update endpoint statistics.
        
        Args:
            path: Endpoint path
            method: HTTP method
            duration: Request duration in seconds
            status_code: HTTP status code
        """
        key = f"{method}:{path}"
        
        with self.lock:
            if key not in self.endpoint_stats:
                self.endpoint_stats[key] = {
                    "path": path,
                    "method": method,
                    "count": 0,
                    "durations": [],
                    "status_codes": {},
                    "last_accessed": datetime.utcnow(),
                }
            
            stats = self.endpoint_stats[key]
            stats["count"] += 1
            stats["durations"].append(duration)
            stats["last_accessed"] = datetime.utcnow()
            
            # Keep only the last 100 durations
            if len(stats["durations"]) > 100:
                stats["durations"] = stats["durations"][-100:]
            
            # Update status code counts
            status_str = str(status_code)
            if status_str not in stats["status_codes"]:
                stats["status_codes"][status_str] = 0
            stats["status_codes"][status_str] += 1
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get endpoint statistics.
        
        Returns:
            Dictionary of endpoint statistics
        """
        result = {}
        
        with self.lock:
            for key, stats in self.endpoint_stats.items():
                durations = stats["durations"]
                if not durations:
                    continue
                
                result[key] = {
                    "path": stats["path"],
                    "method": stats["method"],
                    "count": stats["count"],
                    "min": min(durations),
                    "max": max(durations),
                    "avg": sum(durations) / len(durations),
                    "median": statistics.median(durations),
                    "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
                    "status_codes": stats["status_codes"],
                    "last_accessed": stats["last_accessed"].isoformat(),
                }
        
        return result
    
    def get_slow_endpoints(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get slow endpoints.
        
        Args:
            threshold: Optional threshold in seconds, defaults to self.slow_endpoint_threshold
            
        Returns:
            List of slow endpoint statistics
        """
        if threshold is None:
            threshold = self.slow_endpoint_threshold
        
        result = []
        
        with self.lock:
            for key, stats in self.endpoint_stats.items():
                if stats.get("p95", 0) >= threshold:
                    result.append(self.endpoint_stats[key])
        
        return result
    
    def analyze_endpoints(self) -> Dict[str, Any]:
        """
        Analyze endpoints for patterns and issues.
        
        Returns:
            Dictionary with analysis results
        """
        with self.lock:
            endpoint_stats = self.get_endpoint_stats()
            slow_endpoints = self.get_slow_endpoints()
            
            # Find error-prone endpoints
            error_prone_endpoints = []
            for key, stats in endpoint_stats.items():
                total_requests = sum(int(count) for count in stats["status_codes"].values())
                error_count = sum(
                    int(count) for status, count in stats["status_codes"].items()
                    if status.startswith(("4", "5"))
                )
                
                if total_requests > 10 and error_count / total_requests > 0.1:
                    error_prone_endpoints.append({
                        "path": stats["path"],
                        "method": stats["method"],
                        "error_rate": error_count / total_requests,
                        "total_requests": total_requests,
                        "error_count": error_count,
                    })
            
            return {
                "total_endpoints": len(endpoint_stats),
                "total_requests": sum(stats["count"] for stats in endpoint_stats.values()),
                "slow_endpoints": slow_endpoints,
                "error_prone_endpoints": error_prone_endpoints,
                "endpoint_stats": endpoint_stats,
            }


class ResourceCollector(MetricCollector):
    """Collector for system resource metrics."""
    
    def __init__(
        self,
        capacity: int = 1000,
        report_interval: Optional[int] = None,
        report_callback: Optional[Callable[[List[Union[MemoryMetric, CPUMetric]]], None]] = None,
        collect_interval: int = 60,
    ):
        """
        Initialize the collector.
        
        Args:
            capacity: Maximum number of metrics to store
            report_interval: Interval in seconds for reporting metrics
            report_callback: Callback function for reporting metrics
            collect_interval: Interval in seconds for collecting metrics
        """
        super().__init__("resource-collector", capacity, report_interval, report_callback)
        self.collect_interval = collect_interval
        self.collection_thread = None
        self.stop_collection = threading.Event()
    
    def start_collection(self) -> None:
        """Start periodic collection of resource metrics."""
        if self.collection_thread and self.collection_thread.is_alive():
            return
        
        self.stop_collection.clear()
        self.collection_thread = threading.Thread(
            target=self._collection_loop,
            daemon=True,
            name="resource-collector",
        )
        self.collection_thread.start()
    
    def stop_collection(self) -> None:
        """Stop periodic collection of resource metrics."""
        if self.collection_thread and self.collection_thread.is_alive():
            self.stop_collection.set()
            self.collection_thread.join(timeout=1.0)
    
    def _collection_loop(self) -> None:
        """Collection loop."""
        try:
            import psutil
        except ImportError:
            logger.error("psutil is required for resource collection")
            return
        
        while not self.stop_collection.is_set():
            try:
                # Collect memory metrics
                memory = psutil.virtual_memory()
                process = psutil.Process()
                process_memory = process.memory_info()
                
                memory_metric = MemoryMetric(
                    total=memory.total,
                    available=memory.available,
                    percent=memory.percent,
                    used=memory.used,
                    free=memory.free,
                    process_rss=process_memory.rss,
                    process_vms=process_memory.vms,
                    process_percent=process.memory_percent(),
                )
                self.add_metric(memory_metric)
                
                # Collect CPU metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                process_cpu = process.cpu_percent(interval=0.1)
                
                cpu_metric = CPUMetric(
                    percent=cpu_percent,
                    process_percent=process_cpu,
                )
                self.add_metric(cpu_metric)
                
            except Exception as e:
                logger.exception(f"Error collecting resource metrics: {e}")
            
            # Sleep for the rest of the interval
            time.sleep(self.collect_interval)
    
    def get_memory_metrics(self) -> List[MemoryMetric]:
        """
        Get memory metrics.
        
        Returns:
            List of memory metrics
        """
        with self.lock:
            return [m for m in self.metrics if isinstance(m, MemoryMetric)]
    
    def get_cpu_metrics(self) -> List[CPUMetric]:
        """
        Get CPU metrics.
        
        Returns:
            List of CPU metrics
        """
        with self.lock:
            return [m for m in self.metrics if isinstance(m, CPUMetric)]
    
    def analyze_resources(self) -> Dict[str, Any]:
        """
        Analyze resource metrics.
        
        Returns:
            Dictionary with analysis results
        """
        memory_metrics = self.get_memory_metrics()
        cpu_metrics = self.get_cpu_metrics()
        
        if not memory_metrics or not cpu_metrics:
            return {
                "memory": {},
                "cpu": {},
            }
        
        # Calculate memory statistics
        memory_process_percent = [m.process_percent for m in memory_metrics if m.process_percent is not None]
        memory_percent = [m.percent for m in memory_metrics]
        
        # Calculate CPU statistics
        cpu_process_percent = [m.process_percent for m in cpu_metrics if m.process_percent is not None]
        cpu_percent = [m.percent for m in cpu_metrics]
        
        return {
            "memory": {
                "count": len(memory_metrics),
                "latest": memory_metrics[-1].to_dict() if memory_metrics else None,
                "avg_percent": sum(memory_percent) / len(memory_percent) if memory_percent else None,
                "max_percent": max(memory_percent) if memory_percent else None,
                "avg_process_percent": sum(memory_process_percent) / len(memory_process_percent) if memory_process_percent else None,
                "max_process_percent": max(memory_process_percent) if memory_process_percent else None,
            },
            "cpu": {
                "count": len(cpu_metrics),
                "latest": cpu_metrics[-1].to_dict() if cpu_metrics else None,
                "avg_percent": sum(cpu_percent) / len(cpu_percent) if cpu_percent else None,
                "max_percent": max(cpu_percent) if cpu_percent else None,
                "avg_process_percent": sum(cpu_process_percent) / len(cpu_process_percent) if cpu_process_percent else None,
                "max_process_percent": max(cpu_process_percent) if cpu_process_percent else None,
            },
        }


class FunctionCollector(MetricCollector):
    """Collector for function execution metrics."""
    
    def __init__(
        self,
        capacity: int = 1000,
        report_interval: Optional[int] = None,
        report_callback: Optional[Callable[[List[FunctionMetric]], None]] = None,
        slow_function_threshold: float = 0.1,
    ):
        """
        Initialize the collector.
        
        Args:
            capacity: Maximum number of metrics to store
            report_interval: Interval in seconds for reporting metrics
            report_callback: Callback function for reporting metrics
            slow_function_threshold: Threshold in seconds for identifying slow functions
        """
        super().__init__("function-collector", capacity, report_interval, report_callback)
        self.slow_function_threshold = slow_function_threshold
        self.function_stats: Dict[str, Dict[str, Any]] = {}
    
    def add_function_metric(
        self, name: str, duration: float, **kwargs
    ) -> FunctionMetric:
        """
        Add a function metric.
        
        Args:
            name: Function name
            duration: Execution duration in seconds
            **kwargs: Additional metric metadata
            
        Returns:
            FunctionMetric object
        """
        metric = FunctionMetric(name=name, duration=duration, **kwargs)
        self.add_metric(metric)
        
        # Update function statistics
        self._update_stats(name, duration, kwargs.get("module"))
        
        # Log slow functions
        if duration >= self.slow_function_threshold:
            logger.warning(f"Slow function detected ({duration:.3f}s): {name}")
        
        return metric
    
    def _update_stats(self, name: str, duration: float, module: Optional[str] = None) -> None:
        """
        Update function statistics.
        
        Args:
            name: Function name
            duration: Execution duration in seconds
            module: Module name
        """
        key = f"{module}.{name}" if module else name
        
        with self.lock:
            if key not in self.function_stats:
                self.function_stats[key] = {
                    "name": name,
                    "module": module,
                    "count": 0,
                    "durations": [],
                    "last_called": datetime.utcnow(),
                }
            
            stats = self.function_stats[key]
            stats["count"] += 1
            stats["durations"].append(duration)
            stats["last_called"] = datetime.utcnow()
            
            # Keep only the last 100 durations
            if len(stats["durations"]) > 100:
                stats["durations"] = stats["durations"][-100:]
    
    def get_function_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get function statistics.
        
        Returns:
            Dictionary of function statistics
        """
        result = {}
        
        with self.lock:
            for key, stats in self.function_stats.items():
                durations = stats["durations"]
                if not durations:
                    continue
                
                result[key] = {
                    "name": stats["name"],
                    "module": stats["module"],
                    "count": stats["count"],
                    "min": min(durations),
                    "max": max(durations),
                    "avg": sum(durations) / len(durations),
                    "median": statistics.median(durations),
                    "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
                    "last_called": stats["last_called"].isoformat(),
                }
        
        return result
    
    def get_slow_functions(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get slow functions.
        
        Args:
            threshold: Optional threshold in seconds, defaults to self.slow_function_threshold
            
        Returns:
            List of slow function statistics
        """
        if threshold is None:
            threshold = self.slow_function_threshold
        
        result = []
        
        with self.lock:
            for key, stats in self.function_stats.items():
                durations = stats["durations"]
                if durations and max(durations) >= threshold:
                    result.append(self.function_stats[key])
        
        return result
    
    def analyze_functions(self) -> Dict[str, Any]:
        """
        Analyze functions for patterns and issues.
        
        Returns:
            Dictionary with analysis results
        """
        with self.lock:
            function_stats = self.get_function_stats()
            slow_functions = self.get_slow_functions()
            
            # Find hotspot functions
            hotspots = []
            for key, stats in function_stats.items():
                # Consider functions called frequently with high average duration
                if stats["count"] > 10 and stats["avg"] > self.slow_function_threshold / 10:
                    hotspots.append({
                        "name": stats["name"],
                        "module": stats["module"],
                        "count": stats["count"],
                        "avg": stats["avg"],
                        "total_time": stats["avg"] * stats["count"],
                    })
            
            # Sort hotspots by total time
            hotspots.sort(key=lambda x: x["total_time"], reverse=True)
            
            return {
                "total_functions": len(function_stats),
                "total_calls": sum(stats["count"] for stats in function_stats.values()),
                "slow_functions": slow_functions,
                "hotspots": hotspots[:10],  # Top 10 hotspots
                "function_stats": function_stats,
            }
    
    def profile_function(self, func: Callable) -> Callable:
        """
        Decorator for profiling functions.
        
        Args:
            func: Function to profile
            
        Returns:
            Wrapped function
        """
        import functools
        import inspect
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            stacktrace = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                import traceback
                stacktrace = traceback.format_exc().split("\n")
                raise
            finally:
                duration = time.time() - start_time
                
                # Get module name
                module = inspect.getmodule(func)
                module_name = module.__name__ if module else None
                
                # Add metric
                self.add_function_metric(
                    name=func.__name__,
                    duration=duration,
                    module=module_name,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                    error=error,
                    stacktrace=stacktrace,
                )
        
        return wrapper