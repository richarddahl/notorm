"""Cache monitoring module.

This module provides tools for monitoring cache performance and health.
"""

from typing import Any, Dict, List, Optional, Union
import time
import threading
import logging
import asyncio
import gc
from dataclasses import dataclass
from datetime import datetime, timedelta
import concurrent.futures


logger = logging.getLogger("uno.caching.monitoring")


@dataclass
class CacheEvent:
    """Represents a cache event for monitoring purposes."""

    cache_name: str
    event_type: str  # "hit", "miss", "error", ...
    timestamp: float
    details: dict[str, Any] | None = None


class CacheMonitor:
    """Monitoring tool for cache performance and health.

    This class collects statistics on cache operations, maintains a rolling
    window of recent events, and provides methods for analyzing cache performance.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        local_cache: Optional[Any] = None,
        distributed_cache: Optional[Any] = None,
    ):
        """Initialize the cache monitor.

        Args:
            config: Optional configuration for the monitor.
            local_cache: Optional reference to the local cache.
            distributed_cache: Optional reference to the distributed cache.
        """
        self.config = config or {}
        self.local_cache = local_cache
        self.distributed_cache = distributed_cache

        # Cache stats
        self._stats = {
            "hits": {"local": 0, "distributed": 0},
            "misses": {"local": 0, "distributed": 0},
            "errors": {"local": 0, "distributed": 0},
            "insertions": {"local": 0, "distributed": 0},
            "deletions": {"local": 0, "distributed": 0},
            "created_at": time.time(),
        }

        # Cache events (rolling window)
        self.events: list[CacheEvent] = []
        self._max_events = self.config.get("max_events", 1000)  # Default to 1000 events
        self._lock = threading.RLock()

        # Alert thresholds
        self._hit_rate_threshold = self.config.get("hit_rate_threshold", 0.5)
        self._memory_usage_threshold = self.config.get("memory_usage_threshold", 0.9)
        self._latency_threshold = self.config.get("latency_threshold", 50.0)  # ms

        # Enable Prometheus export if configured
        if self.config.get("prometheus_export", False):
            self._setup_prometheus_exporter()

    def record_hit(self, cache_type: str) -> None:
        """Record a cache hit.

        Args:
            cache_type: The type of cache ("local" or "distributed").
        """
        with self._lock:
            self._stats["hits"][cache_type] += 1

            if self.config.get("detailed_stats", False):
                self._add_event(cache_type, "hit")

    def record_miss(self, cache_type: str) -> None:
        """Record a cache miss.

        Args:
            cache_type: The type of cache ("local" or "distributed").
        """
        with self._lock:
            self._stats["misses"][cache_type] += 1

            if self.config.get("detailed_stats", False):
                self._add_event(cache_type, "miss")

    def record_error(self, cache_type: str, operation: str, error_message: str) -> None:
        """Record a cache error.

        Args:
            cache_type: The type of cache ("local" or "distributed").
            operation: The operation that failed (e.g., "get", "set", "delete").
            error_message: The error message.
        """
        with self._lock:
            self._stats["errors"][cache_type] += 1

            if self.config.get("detailed_stats", False):
                details = {"operation": operation, "error": error_message}
                self._add_event(cache_type, "error", details)

            # Log the error
            log_level = self.config.get("log_level", "INFO")
            if log_level == "DEBUG":
                logger.debug(
                    f"Cache error ({cache_type}, {operation}): {error_message}"
                )
            elif log_level == "INFO":
                logger.info(f"Cache error ({cache_type}, {operation}): {error_message}")
            elif log_level == "WARNING":
                logger.warning(
                    f"Cache error ({cache_type}, {operation}): {error_message}"
                )
            else:
                logger.error(
                    f"Cache error ({cache_type}, {operation}): {error_message}"
                )

    def record_latency(
        self, cache_type: str, operation: str, latency_ms: float
    ) -> None:
        """Record the latency of a cache operation.

        Args:
            cache_type: The type of cache ("local" or "distributed").
            operation: The operation (e.g., "get", "set", "delete").
            latency_ms: The latency in milliseconds.
        """
        with self._lock:
            if "latencies" not in self._stats:
                self._stats["latencies"] = {}

            if cache_type not in self._stats["latencies"]:
                self._stats["latencies"][cache_type] = {}

            if operation not in self._stats["latencies"][cache_type]:
                self._stats["latencies"][cache_type][operation] = {
                    "count": 0,
                    "sum": 0.0,
                    "min": float("inf"),
                    "max": 0.0,
                }

            # Update latency stats
            latency_stats = self._stats["latencies"][cache_type][operation]
            latency_stats["count"] += 1
            latency_stats["sum"] += latency_ms
            latency_stats["min"] = min(latency_stats["min"], latency_ms)
            latency_stats["max"] = max(latency_stats["max"], latency_ms)

            # Check if latency exceeds threshold
            if latency_ms > self._latency_threshold:
                logger.warning(
                    f"Cache latency threshold exceeded: {cache_type}.{operation} = {latency_ms} ms"
                )

            if self.config.get("detailed_stats", False):
                details = {"operation": operation, "latency_ms": latency_ms}
                self._add_event(cache_type, "latency", details)

    def record_size(self, cache_type: str, size: int) -> None:
        """Record the size of the cache.

        Args:
            cache_type: The type of cache ("local" or "distributed").
            size: The size of the cache in bytes or number of items.
        """
        with self._lock:
            if "size" not in self._stats:
                self._stats["size"] = {}

            self._stats["size"][cache_type] = size

    def record_metric(
        self,
        name: str,
        value: Union[int, float, str],
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record a custom metric.

        Args:
            name: The name of the metric.
            value: The value of the metric.
            labels: Optional labels for the metric.
        """
        with self._lock:
            if "metrics" not in self._stats:
                self._stats["metrics"] = {}

            if name not in self._stats["metrics"]:
                self._stats["metrics"][name] = []

            metric = {"value": value, "timestamp": time.time()}

            if labels:
                metric["labels"] = labels

            self._stats["metrics"][name].append(metric)

            # Only keep the last 100 metrics
            if len(self._stats["metrics"][name]) > 100:
                self._stats["metrics"][name] = self._stats["metrics"][name][-100:]

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            A dictionary with cache statistics.
        """
        with self._lock:
            # Copy stats
            stats = {}
            for key, value in self._stats.items():
                if isinstance(value, dict):
                    stats[key] = value.copy()
                else:
                    stats[key] = value

            # Calculate hit rates
            stats["hit_rate"] = {}
            for cache_type in ["local", "distributed"]:
                hits = self._stats["hits"].get(cache_type, 0)
                misses = self._stats["misses"].get(cache_type, 0)
                total = hits + misses

                if total > 0:
                    stats["hit_rate"][cache_type] = hits / total
                else:
                    stats["hit_rate"][cache_type] = 0.0

            # Calculate overall hit rate
            total_hits = sum(self._stats["hits"].values())
            total_misses = sum(self._stats["misses"].values())
            total_requests = total_hits + total_misses

            if total_requests > 0:
                stats["hit_rate"]["overall"] = total_hits / total_requests
            else:
                stats["hit_rate"]["overall"] = 0.0

            # Calculate average latencies
            if "latencies" in self._stats:
                stats["avg_latency"] = {}

                for cache_type, operations in self._stats["latencies"].items():
                    stats["avg_latency"][cache_type] = {}

                    for operation, latency_stats in operations.items():
                        if latency_stats["count"] > 0:
                            avg_latency = latency_stats["sum"] / latency_stats["count"]
                            stats["avg_latency"][cache_type][operation] = avg_latency

            # Add uptime
            stats["uptime"] = time.time() - self._stats["created_at"]

            # Get cache-specific stats
            if self.local_cache and hasattr(self.local_cache, "get_stats"):
                try:
                    local_stats = self.local_cache.get_stats()
                    stats["local_cache"] = local_stats
                except Exception as e:
                    logger.warning(f"Error getting local cache stats: {e}")

            if self.distributed_cache and hasattr(self.distributed_cache, "get_stats"):
                try:
                    distributed_stats = self.distributed_cache.get_stats()
                    stats["distributed_cache"] = distributed_stats
                except Exception as e:
                    logger.warning(f"Error getting distributed cache stats: {e}")

            # Check alerts
            stats["alerts"] = self._check_alerts()

            return stats

    async def get_stats_async(self) -> dict[str, Any]:
        """Get cache statistics asynchronously.

        Returns:
            A dictionary with cache statistics.
        """
        # Use a thread to avoid blocking the event loop
        return await asyncio.to_thread(self.get_stats)

    def analyze_performance(
        self, time_window: Optional[float] = None
    ) -> dict[str, Any]:
        """Analyze cache performance over a time window.

        Args:
            time_window: Optional time window in seconds. If not provided,
                        analyze all available data.

        Returns:
            A dictionary with performance metrics.
        """
        with self._lock:
            # Determine the time window
            if time_window is None:
                # Use all available data
                start_time = 0.0
            else:
                # Use the specified time window
                start_time = time.time() - time_window

            # Filter events by time window
            events = [event for event in self.events if event.timestamp >= start_time]

            # Count hits and misses by cache type
            hits = {"local": 0, "distributed": 0}
            misses = {"local": 0, "distributed": 0}
            errors = {"local": 0, "distributed": 0}

            for event in events:
                if event.event_type == "hit":
                    hits[event.cache_name] += 1
                elif event.event_type == "miss":
                    misses[event.cache_name] += 1
                elif event.event_type == "error":
                    errors[event.cache_name] += 1

            # Calculate hit rates
            hit_rates = {}
            for cache_type in ["local", "distributed"]:
                total = hits[cache_type] + misses[cache_type]
                if total > 0:
                    hit_rates[cache_type] = hits[cache_type] / total
                else:
                    hit_rates[cache_type] = 0.0

            # Calculate overall hit rate
            total_hits = sum(hits.values())
            total_misses = sum(misses.values())
            total_requests = total_hits + total_misses

            if total_requests > 0:
                hit_rates["overall"] = total_hits / total_requests
            else:
                hit_rates["overall"] = 0.0

            # Calculate error rates
            error_rates = {}
            for cache_type in ["local", "distributed"]:
                total = hits[cache_type] + misses[cache_type] + errors[cache_type]
                if total > 0:
                    error_rates[cache_type] = errors[cache_type] / total
                else:
                    error_rates[cache_type] = 0.0

            # Calculate overall error rate
            total_errors = sum(errors.values())
            if total_requests + total_errors > 0:
                error_rates["overall"] = total_errors / (total_requests + total_errors)
            else:
                error_rates["overall"] = 0.0

            # Analyze latencies
            latencies = {"local": [], "distributed": []}

            for event in events:
                if event.event_type == "latency" and event.details:
                    latencies[event.cache_name].append(event.details["latency_ms"])

            # Calculate latency statistics
            latency_stats = {}
            for cache_type in ["local", "distributed"]:
                if latencies[cache_type]:
                    latency_stats[cache_type] = {
                        "count": len(latencies[cache_type]),
                        "avg": sum(latencies[cache_type]) / len(latencies[cache_type]),
                        "min": min(latencies[cache_type]),
                        "max": max(latencies[cache_type]),
                        "p95": percentile(latencies[cache_type], 95),
                        "p99": percentile(latencies[cache_type], 99),
                    }
                else:
                    latency_stats[cache_type] = {
                        "count": 0,
                        "avg": 0.0,
                        "min": 0.0,
                        "max": 0.0,
                        "p95": 0.0,
                        "p99": 0.0,
                    }

            # Prepare result
            result = {
                "time_window": time_window,
                "hits": hits,
                "misses": misses,
                "errors": errors,
                "hit_rates": hit_rates,
                "error_rates": error_rates,
                "latency_stats": latency_stats,
                "event_count": len(events),
            }

            return result

    async def analyze_performance_async(
        self, time_window: Optional[float] = None
    ) -> dict[str, Any]:
        """Analyze cache performance asynchronously.

        Args:
            time_window: Optional time window in seconds. If not provided,
                        analyze all available data.

        Returns:
            A dictionary with performance metrics.
        """
        # Use a thread to avoid blocking the event loop
        return await asyncio.to_thread(self.analyze_performance, time_window)

    def check_health(self) -> dict[str, bool]:
        """Check the health of the cache.

        Returns:
            A dictionary with health status for each component.
        """
        health = {}

        # Check local cache health
        if self.local_cache and hasattr(self.local_cache, "check_health"):
            try:
                health["local"] = self.local_cache.check_health()
            except Exception as e:
                logger.warning(f"Error checking local cache health: {e}")
                health["local"] = False
        else:
            health["local"] = True  # Assume healthy if no check_health method

        # Check distributed cache health
        if self.distributed_cache and hasattr(self.distributed_cache, "check_health"):
            try:
                health["distributed"] = self.distributed_cache.check_health()
            except Exception as e:
                logger.warning(f"Error checking distributed cache health: {e}")
                health["distributed"] = False
        else:
            health["distributed"] = True  # Assume healthy if no check_health method

        # Check hit rate health
        stats = self.get_stats()
        hit_rate = stats.get("hit_rate", {}).get("overall", 0.0)
        health["hit_rate"] = hit_rate >= self._hit_rate_threshold

        # Add overall health status
        health["overall"] = all(health.values())

        return health

    async def check_health_async(self) -> dict[str, bool]:
        """Check the health of the cache asynchronously.

        Returns:
            A dictionary with health status for each component.
        """
        # Use a thread to avoid blocking the event loop
        return await asyncio.to_thread(self.check_health)

    def clear_stats(self) -> None:
        """Clear cache statistics."""
        with self._lock:
            # Reset stats
            self._stats = {
                "hits": {"local": 0, "distributed": 0},
                "misses": {"local": 0, "distributed": 0},
                "errors": {"local": 0, "distributed": 0},
                "insertions": {"local": 0, "distributed": 0},
                "deletions": {"local": 0, "distributed": 0},
                "created_at": time.time(),
            }

            # Clear events
            self.events = []

    def shutdown(self) -> None:
        """Shutdown the cache monitor and release resources."""
        if hasattr(self, "_executor") and self._executor is not None:
            self._executor.shutdown(wait=True)

    def _add_event(
        self, cache_name: str, event_type: str, details: dict[str, Any] | None = None
    ) -> None:
        """Add an event to the events list.

        Args:
            cache_name: The name of the cache.
            event_type: The type of the event.
            details: Optional details about the event.
        """
        # Add the event
        event = CacheEvent(
            cache_name=cache_name,
            event_type=event_type,
            timestamp=time.time(),
            details=details,
        )

        self.events.append(event)

        # Trim events list if it's too long
        if len(self.events) > self._max_events:
            self.events = self.events[-self._max_events :]

    def _check_alerts(self) -> dict[str, bool]:
        """Check for alert conditions.

        Returns:
            A dictionary mapping alert names to booleans indicating if the alert is active.
        """
        alerts = {}

        # Check hit rate alert
        for cache_type in ["local", "distributed", "overall"]:
            hit_rate = self._stats.get("hit_rate", {}).get(cache_type, 0.0)
            alert_name = f"low_hit_rate_{cache_type}"
            alerts[alert_name] = hit_rate < self._hit_rate_threshold

            if alerts[alert_name]:
                logger.warning(f"Low hit rate alert: {cache_type} = {hit_rate:.2f}")

        # Check latency alert
        if "avg_latency" in self._stats:
            for cache_type, operations in self._stats["avg_latency"].items():
                for operation, latency in operations.items():
                    alert_name = f"high_latency_{cache_type}_{operation}"
                    alerts[alert_name] = latency > self._latency_threshold

                    if alerts[alert_name]:
                        logger.warning(
                            f"High latency alert: {cache_type}.{operation} = {latency:.2f} ms"
                        )

        # Check memory usage alert (only for local cache)
        if "size" in self._stats and "local" in self._stats["size"]:
            local_size = self._stats["size"]["local"]

            if self.local_cache and hasattr(self.local_cache, "max_size"):
                max_size = getattr(self.local_cache, "max_size")
                if max_size > 0:
                    memory_usage = local_size / max_size
                    alert_name = "high_memory_usage_local"
                    alerts[alert_name] = memory_usage > self._memory_usage_threshold

                    if alerts[alert_name]:
                        logger.warning(
                            f"High memory usage alert: local = {memory_usage:.2f}"
                        )

        return alerts

    def _setup_prometheus_exporter(self) -> None:
        """Set up a Prometheus exporter for cache metrics."""
        try:
            from prometheus_client import Counter, Gauge, Histogram, start_http_server

            # Only import if available
            export_port = self.config.get("export_port", 9090)

            # Define metrics
            self._prom_hits = Counter(
                "cache_hits_total", "Total number of cache hits", ["cache_type"]
            )
            self._prom_misses = Counter(
                "cache_misses_total", "Total number of cache misses", ["cache_type"]
            )
            self._prom_errors = Counter(
                "cache_errors_total", "Total number of cache errors", ["cache_type"]
            )

            self._prom_hit_rate = Gauge(
                "cache_hit_rate", "Cache hit rate", ["cache_type"]
            )
            self._prom_size = Gauge("cache_size", "Cache size", ["cache_type"])

            self._prom_latency = Histogram(
                "cache_operation_latency_milliseconds",
                "Latency of cache operations in milliseconds",
                ["cache_type", "operation"],
                buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
            )

            # Start exporter server
            start_http_server(export_port)
            logger.info(f"Started Prometheus exporter on port {export_port}")

            # Start background thread to export metrics
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            self._executor.submit(self._export_metrics_loop)
        except ImportError:
            logger.warning(
                "Prometheus client library not available. Install with `pip install prometheus-client`."
            )

    def _export_metrics_loop(self) -> None:
        """Background thread to export metrics to Prometheus."""
        while True:
            try:
                # Export metrics
                with self._lock:
                    # Export hit counts
                    for cache_type, hits in self._stats["hits"].items():
                        self._prom_hits.labels(cache_type).inc(hits)

                    # Export miss counts
                    for cache_type, misses in self._stats["misses"].items():
                        self._prom_misses.labels(cache_type).inc(misses)

                    # Export error counts
                    for cache_type, errors in self._stats["errors"].items():
                        self._prom_errors.labels(cache_type).inc(errors)

                    # Export hit rates
                    if "hit_rate" in self._stats:
                        for cache_type, rate in self._stats["hit_rate"].items():
                            self._prom_hit_rate.labels(cache_type).set(rate)

                    # Export sizes
                    if "size" in self._stats:
                        for cache_type, size in self._stats["size"].items():
                            self._prom_size.labels(cache_type).set(size)

                    # Reset counters to avoid double-counting
                    self._stats["hits"] = {"local": 0, "distributed": 0}
                    self._stats["misses"] = {"local": 0, "distributed": 0}
                    self._stats["errors"] = {"local": 0, "distributed": 0}
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")

            # Sleep for 15 seconds
            time.sleep(15)


def percentile(values: list[float], p: float) -> float:
    """Calculate the p-th percentile of a list of values.

    Args:
        values: The list of values.
        p: The percentile (0-100).

    Returns:
        The p-th percentile of the values.
    """
    if not values:
        return 0.0

    # Sort values
    sorted_values = sorted(values)

    # Calculate index
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = k - f

    if f + 1 < len(sorted_values):
        return sorted_values[f] + c * (sorted_values[f + 1] - sorted_values[f])
    else:
        return sorted_values[f]
