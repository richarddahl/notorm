# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Performance metrics for Uno applications.

This module provides a class for collecting and analyzing performance
metrics for Uno applications.
"""

import time
import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast
import functools

from uno.testing.performance.benchmark import _get_benchmark_dir, _get_caller_info

# Type variable for generic function
F = TypeVar("F", bound=Callable)


@dataclass
class PerformanceMetrics:
    """
    Container for performance metrics.
    
    This class stores performance metrics collected during test execution,
    such as response times, database query counts, and memory usage.
    
    Example:
        ```python
        metrics = PerformanceMetrics(name="api-endpoint")
        
        # Record a response time
        metrics.record_response_time(0.125)
        
        # Record a database query
        metrics.record_db_query("SELECT * FROM users", 0.045)
        
        # Save the metrics
        metrics.save()
        ```
    """
    
    name: str
    response_times: List[float] = field(default_factory=list)
    db_queries: List[Dict[str, Any]] = field(default_factory=list)
    memory_samples: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    custom_metrics: Dict[str, List[float]] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    
    def record_response_time(self, duration: float) -> None:
        """
        Record a response time measurement.
        
        Args:
            duration: Response time in seconds
        """
        self.response_times.append(duration)
    
    def record_db_query(
        self, query: str, duration: float, rows_affected: Optional[int] = None
    ) -> None:
        """
        Record a database query.
        
        Args:
            query: SQL query string
            duration: Query execution time in seconds
            rows_affected: Number of rows affected by the query
        """
        self.db_queries.append({
            "query": query,
            "duration": duration,
            "rows_affected": rows_affected,
            "timestamp": time.time() - self.start_time
        })
    
    def record_memory_usage(self, usage: int, label: Optional[str] = None) -> None:
        """
        Record memory usage.
        
        Args:
            usage: Memory usage in bytes
            label: Optional label for the measurement
        """
        self.memory_samples.append({
            "usage": usage,
            "label": label,
            "timestamp": time.time() - self.start_time
        })
    
    def record_event(self, event_type: str, data: Any = None) -> None:
        """
        Record a custom event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        self.events.append({
            "type": event_type,
            "data": data,
            "timestamp": time.time() - self.start_time
        })
    
    def record_custom_metric(self, name: str, value: float) -> None:
        """
        Record a custom metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
        """
        if name not in self.custom_metrics:
            self.custom_metrics[name] = []
        
        self.custom_metrics[name].append(value)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics for the recorded metrics.
        
        Returns:
            Dictionary with statistics for all metrics
        """
        stats = {}
        
        # Response time statistics
        if self.response_times:
            stats["response_time"] = {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "stdev": statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0.0,
                "count": len(self.response_times)
            }
        
        # DB query statistics
        if self.db_queries:
            query_durations = [q["duration"] for q in self.db_queries]
            
            stats["db_queries"] = {
                "count": len(self.db_queries),
                "total_duration": sum(query_durations),
                "min_duration": min(query_durations),
                "max_duration": max(query_durations),
                "mean_duration": statistics.mean(query_durations),
                "median_duration": statistics.median(query_durations)
            }
        
        # Memory usage statistics
        if self.memory_samples:
            usage_values = [s["usage"] for s in self.memory_samples]
            
            stats["memory"] = {
                "min": min(usage_values),
                "max": max(usage_values),
                "mean": statistics.mean(usage_values),
                "samples": len(usage_values)
            }
        
        # Custom metrics statistics
        if self.custom_metrics:
            stats["custom_metrics"] = {}
            
            for metric_name, values in self.custom_metrics.items():
                if not values:
                    continue
                
                stats["custom_metrics"][metric_name] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "count": len(values)
                }
        
        # Event statistics
        if self.events:
            event_types = set(e["type"] for e in self.events)
            
            stats["events"] = {
                "count": len(self.events),
                "types": list(event_types)
            }
        
        return stats
    
    def save(self, file_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save metrics to a file.
        
        Args:
            file_path: Optional path to save the metrics to
            
        Returns:
            Path to the saved metrics file
        """
        if file_path is None:
            # Auto-generate a path
            caller_info = _get_caller_info()
            benchmark_dir = _get_benchmark_dir()
            
            # Create a filename based on the caller information
            module_part = caller_info["module"]
            class_part = f"{caller_info['class']}_" if caller_info["class"] else ""
            func_part = caller_info["function"]
            name_part = f"_{self.name}" if self.name else ""
            
            filename = f"{module_part}_{class_part}{func_part}{name_part}.metrics.json"
            
            # Create module-specific subdirectory
            module_dir = benchmark_dir / module_part
            module_dir.mkdir(exist_ok=True)
            
            file_path = module_dir / filename
        else:
            file_path = Path(file_path)
        
        # Calculate statistics
        stats = self.get_statistics()
        timestamp = datetime.now().isoformat()
        
        # Prepare data for saving
        data = {
            "timestamp": timestamp,
            "name": self.name,
            "stats": stats,
            "raw_data": {
                "response_times": self.response_times,
                "db_queries": self.db_queries,
                "memory_samples": self.memory_samples,
                "events": self.events,
                "custom_metrics": self.custom_metrics
            }
        }
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return Path(file_path)
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> "PerformanceMetrics":
        """
        Load metrics from a file.
        
        Args:
            file_path: Path to the metrics file
            
        Returns:
            Loaded PerformanceMetrics instance
        """
        file_path = Path(file_path)
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Create a new instance
        metrics = PerformanceMetrics(name=data["name"])
        
        # Load raw data
        raw_data = data.get("raw_data", {})
        metrics.response_times = raw_data.get("response_times", [])
        metrics.db_queries = raw_data.get("db_queries", [])
        metrics.memory_samples = raw_data.get("memory_samples", [])
        metrics.events = raw_data.get("events", [])
        metrics.custom_metrics = raw_data.get("custom_metrics", {})
        
        return metrics


def performance_test(
    name: Optional[str] = None,
    track_db_queries: bool = True,
    track_memory: bool = False,
    save_metrics: bool = True,
) -> Callable[[F], F]:
    """
    Decorator for measuring the performance of a test function.
    
    This decorator collects performance metrics during test execution
    and saves them to a file for later analysis.
    
    Args:
        name: Optional name for the test
        track_db_queries: Whether to track database queries
        track_memory: Whether to track memory usage
        save_metrics: Whether to save metrics to a file
        
    Returns:
        Decorated function
        
    Example:
        ```python
        @performance_test(name="list-users", track_db_queries=True)
        def test_list_users():
            response = client.get("/users/")
            assert response.status_code == 200
        ```
    """
    def decorator(func: F) -> F:
        test_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create performance metrics
            metrics = PerformanceMetrics(name=test_name)
            
            # Start memory tracking if requested
            memory_tracker = None
            if track_memory:
                try:
                    import psutil
                    process = psutil.Process()
                    
                    def sample_memory():
                        metrics.record_memory_usage(process.memory_info().rss)
                    
                    sample_memory()  # Initial sample
                except ImportError:
                    pass
            
            # Start DB query tracking if requested
            if track_db_queries:
                # This would need to hook into the database layer
                # For now, we'll leave this as a placeholder
                pass
            
            # Execute the function and measure time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            # Record response time
            duration = end_time - start_time
            metrics.record_response_time(duration)
            
            # Take a final memory sample if tracking
            if track_memory and memory_tracker:
                sample_memory()
            
            # Save metrics if requested
            if save_metrics:
                metrics.save()
            
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create performance metrics
            metrics = PerformanceMetrics(name=test_name)
            
            # Start memory tracking if requested
            if track_memory:
                try:
                    import psutil
                    process = psutil.Process()
                    
                    def sample_memory():
                        metrics.record_memory_usage(process.memory_info().rss)
                    
                    sample_memory()  # Initial sample
                except ImportError:
                    pass
            
            # Start DB query tracking if requested
            if track_db_queries:
                # This would need to hook into the database layer
                # For now, we'll leave this as a placeholder
                pass
            
            # Execute the function and measure time
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            
            # Record response time
            duration = end_time - start_time
            metrics.record_response_time(duration)
            
            # Take a final memory sample if tracking
            if track_memory:
                try:
                    sample_memory()
                except Exception:
                    pass
            
            # Save metrics if requested
            if save_metrics:
                metrics.save()
            
            return result
        
        # Determine if the function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, wrapper)
    
    return decorator