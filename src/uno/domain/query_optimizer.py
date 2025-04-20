"""
Query optimization for domain-driven design queries.

This module provides tools for optimizing queries and monitoring performance
of the graph-based query system, providing insights and improvements for
complex domain queries.
"""

import time
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable, Awaitable, TypeVar, Union
from datetime import datetime, timedelta

from uno.database.session import async_session
from sqlalchemy import text, func
from sqlalchemy.exc import SQLAlchemyError


T = TypeVar("T")
QueryCallback = Callable[[], Awaitable[T]]


class QueryPerformanceMetric:
    """
    Represents performance metrics for a specific query path.

    Tracks execution times and provides statistical analysis for
    query performance monitoring.
    """

    def __init__(self, name: str):
        """
        Initialize performance metrics for a query.

        Args:
            name: The name or identifier for this query
        """
        self.name = name
        self.execution_times: list[float] = []
        self.last_execution_time: Optional[datetime] = None
        self.min_time: Optional[float] = None
        self.max_time: Optional[float] = None
        self.avg_time: Optional[float] = None
        self.median_time: Optional[float] = None
        self.p95_time: Optional[float] = None
        self.call_count: int = 0

    def add_execution(self, duration: float) -> None:
        """
        Add an execution time to the metrics.

        Args:
            duration: The execution time in seconds
        """
        self.execution_times.append(duration)
        self.last_execution_time = datetime.now()
        self.call_count += 1

        # Update statistics
        self._update_statistics()

    def _update_statistics(self) -> None:
        """Update statistical metrics based on execution times."""
        if not self.execution_times:
            return

        # Basic statistics
        self.min_time = min(self.execution_times)
        self.max_time = max(self.execution_times)
        self.avg_time = sum(self.execution_times) / len(self.execution_times)

        # More complex statistics
        sorted_times = sorted(self.execution_times)

        # Median
        mid = len(sorted_times) // 2
        self.median_time = (
            sorted_times[mid]
            if len(sorted_times) % 2 == 1
            else (sorted_times[mid - 1] + sorted_times[mid]) / 2
        )

        # 95th percentile
        if len(sorted_times) >= 20:  # Only calculate if we have enough samples
            idx_95 = int(len(sorted_times) * 0.95)
            self.p95_time = sorted_times[idx_95]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert metrics to a dictionary representation.

        Returns:
            Dictionary with metric data
        """
        return {
            "name": self.name,
            "call_count": self.call_count,
            "last_execution": (
                self.last_execution_time.isoformat()
                if self.last_execution_time
                else None
            ),
            "min_time": self.min_time,
            "max_time": self.max_time,
            "avg_time": self.avg_time,
            "median_time": self.median_time,
            "p95_time": self.p95_time,
        }


class QueryPerformanceTracker:
    """
    Tracks and reports query performance metrics.

    This class provides tools for monitoring the performance of queries,
    particularly for comparing graph-based queries with SQL-based alternatives.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the performance tracker.

        Args:
            logger: Optional logger for diagnostic output
        """
        self.metrics: dict[str, QueryPerformanceMetric] = {}
        self.logger = logger or logging.getLogger(__name__)

    async def track_query(self, query_key: str, callback: QueryCallback[T]) -> T:
        """
        Track execution time of a query.

        Args:
            query_key: A unique identifier for the query
            callback: Async function that executes the query

        Returns:
            The results from the query callback
        """
        start_time = time.time()

        try:
            # Execute the query
            results = await callback()

            # Calculate execution time
            duration = time.time() - start_time

            # Track the metrics
            if query_key not in self.metrics:
                self.metrics[query_key] = QueryPerformanceMetric(query_key)

            self.metrics[query_key].add_execution(duration)

            # Log performance for monitoring
            self.logger.debug(f"Query: {query_key} - Duration: {duration:.4f}s")

            return results

        except Exception as e:
            # Calculate duration even for failed queries
            duration = time.time() - start_time

            # Log the error with performance information
            self.logger.error(
                f"Query error: {query_key} - Duration: {duration:.4f}s - Error: {e}"
            )

            # Re-raise the exception
            raise

    def get_metrics(
        self, query_key: str | None = None
    ) -> Union[dict[str, Any], list[dict[str, Any]]]:
        """
        Get performance metrics for queries.

        Args:
            query_key: Optional key for a specific query's metrics

        Returns:
            Dictionary of metrics or list of metric dictionaries
        """
        if query_key:
            if query_key in self.metrics:
                return self.metrics[query_key].to_dict()
            return {}

        # Return all metrics
        return [metric.to_dict() for metric in self.metrics.values()]

    def reset_metrics(self, query_key: str | None = None) -> None:
        """
        Reset performance metrics.

        Args:
            query_key: Optional key for a specific query's metrics to reset
        """
        if query_key:
            if query_key in self.metrics:
                del self.metrics[query_key]
        else:
            self.metrics.clear()

    def get_slow_queries(self, threshold: float = 1.0) -> list[dict[str, Any]]:
        """
        Get metrics for queries that exceed a performance threshold.

        Args:
            threshold: Time threshold in seconds

        Returns:
            List of metric dictionaries for slow queries
        """
        slow_queries = []

        for metric in self.metrics.values():
            if metric.avg_time and metric.avg_time > threshold:
                slow_queries.append(metric.to_dict())

        # Sort by average time, slowest first
        return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)


class QueryResultCache:
    """
    Caches query results with time-to-live expiration.

    This cache allows frequently executed queries to reuse results
    within a configurable time window, reducing database load.
    """

    def __init__(
        self,
        ttl_seconds: int = 300,
        max_entries: int = 1000,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the query cache.

        Args:
            ttl_seconds: Default time-to-live for cache entries in seconds
            max_entries: Maximum number of entries to store in the cache
            logger: Optional logger for diagnostic output
        """
        self.cache: dict[str, dict[str, Any]] = {}
        self.default_ttl = ttl_seconds
        self.max_entries = max_entries
        self.logger = logger or logging.getLogger(__name__)
        self.hits = 0
        self.misses = 0
        self._cleanup_task = None
        self._running = False

    async def get_or_execute(
        self,
        cache_key: str,
        query_fn: QueryCallback[T],
        ttl_seconds: int | None = None,
    ) -> T:
        """
        Get from cache or execute query if not cached or expired.

        Args:
            cache_key: The unique key for this query
            query_fn: Async function that executes the query
            ttl_seconds: Optional specific TTL for this query

        Returns:
            The query results from cache or fresh execution
        """
        now = time.time()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        # Clean cache if too many entries
        if len(self.cache) > self.max_entries:
            self._cleanup_expired()

        # Check if in cache and not expired
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if entry["expires"] > now:
                self.hits += 1
                self.logger.debug(f"Cache hit: {cache_key}")
                return entry["results"]

        # Cache miss, execute query
        self.misses += 1
        self.logger.debug(f"Cache miss: {cache_key}")

        results = await query_fn()
        self.cache[cache_key] = {
            "results": results,
            "expires": now + ttl,
            "created_at": now,
        }

        return results

    def invalidate(self, cache_key: str | None = None) -> None:
        """
        Invalidate cache entries.

        Args:
            cache_key: Optional specific key to invalidate, or all if None
        """
        if cache_key:
            if cache_key in self.cache:
                del self.cache[cache_key]
                self.logger.debug(f"Cache invalidated: {cache_key}")
        else:
            self.cache.clear()
            self.logger.debug("Cache fully invalidated")

    def _cleanup_expired(self) -> None:
        """Remove expired entries from the cache."""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if v["expires"] <= now]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")

    async def start_cleanup_task(self, interval_seconds: int = 60) -> None:
        """
        Start a background task that periodically cleans up expired entries.

        Args:
            interval_seconds: How often to run the cleanup
        """
        if self._running:
            return

        self._running = True

        async def cleanup_loop():
            while self._running:
                self._cleanup_expired()
                await asyncio.sleep(interval_seconds)

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._running and self._cleanup_task:
            self._running = False
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": (
                self.hits / (self.hits + self.misses)
                if (self.hits + self.misses) > 0
                else 0
            ),
            "max_size": self.max_entries,
            "default_ttl": self.default_ttl,
        }


class GraphQueryOptimizer:
    """
    Optimizes cypher queries based on graph statistics and performance data.

    This class analyzes graph node and relationship cardinality to optimize
    query paths, improving performance of graph queries.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the query optimizer.

        Args:
            logger: Optional logger for diagnostic output
        """
        self.cardinality_stats: dict[str, int] = {}
        self.logger = logger or logging.getLogger(__name__)
        self.last_stats_update: Optional[datetime] = None

    async def update_statistics(self) -> None:
        """
        Update node and relationship cardinality statistics from the graph.

        This method queries the graph database to get counts of nodes by label
        and relationships by type, storing them for query optimization.
        """
        try:
            async with async_session() as session:
                # Query for node counts by label
                node_query = """
                SELECT * FROM cypher('graph', $$
                    MATCH (n)
                    RETURN labels(n)[0] AS label, count(n) AS count
                $$) AS (label text, count bigint)
                """
                result = await session.execute(text(node_query))
                node_stats = result.fetchall()

                # Query for relationship counts by type
                rel_query = """
                SELECT * FROM cypher('graph', $$
                    MATCH ()-[r]->()
                    RETURN type(r) AS label, count(r) AS count
                $$) AS (label text, count bigint)
                """
                result = await session.execute(text(rel_query))
                rel_stats = result.fetchall()

                # Combine statistics
                self.cardinality_stats = {}
                for row in node_stats:
                    self.cardinality_stats[f"node:{row.label}"] = row.count

                for row in rel_stats:
                    self.cardinality_stats[f"rel:{row.label}"] = row.count

                self.last_stats_update = datetime.now()
                self.logger.info(
                    f"Updated graph statistics: {len(self.cardinality_stats)} entries"
                )

        except SQLAlchemyError as e:
            self.logger.error(f"Error updating graph statistics: {e}")

    def optimize_path(self, cypher_path: str) -> str:
        """
        Optimize a cypher path expression based on cardinality statistics.

        This method analyzes a cypher path and reorders the pattern to start
        with the most selective node or relationship patterns.

        Args:
            cypher_path: The original cypher path expression

        Returns:
            Optimized cypher path
        """
        # If we don't have statistics, return the original path
        if not self.cardinality_stats:
            return cypher_path

        # Simple optimization for now - more complex parsing would be needed
        # for a full-featured optimizer

        # This is a placeholder for more complex optimization logic
        # that would parse the path and reorder nodes/relationships

        # For now, we'll just return the original path
        return cypher_path

    def optimize_query(self, cypher_query: str) -> str:
        """
        Optimize a full cypher query based on cardinality statistics.

        This method rewrites the MATCH clauses to start with the most selective
        patterns, and adjusts WHERE clauses for better performance.

        Args:
            cypher_query: The original cypher query

        Returns:
            Optimized cypher query
        """
        # If we don't have statistics, return the original query
        if not self.cardinality_stats:
            return cypher_query

        # Simple optimization for now - more complex parsing would be needed
        # for a full-featured optimizer

        # This is a placeholder for more complex optimization logic
        return cypher_query

    def get_statistics(self) -> dict[str, Any]:
        """
        Get the current graph statistics.

        Returns:
            Dictionary with graph statistics
        """
        return {
            "statistics": self.cardinality_stats,
            "last_update": (
                self.last_stats_update.isoformat() if self.last_stats_update else None
            ),
            "node_count": sum(
                count
                for label, count in self.cardinality_stats.items()
                if label.startswith("node:")
            ),
            "relationship_count": sum(
                count
                for label, count in self.cardinality_stats.items()
                if label.startswith("rel:")
            ),
        }


class MaterializedQueryView:
    """
    Maintains a materialized view of a query result.

    This class implements a materialized view pattern for query results,
    automatically refreshing the results on a schedule or on demand.
    """

    def __init__(
        self,
        query_fn: QueryCallback[T],
        name: str,
        refresh_interval: int = 3600,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the materialized view.

        Args:
            query_fn: Async function that executes the query
            name: Name for this materialized view
            refresh_interval: Seconds between automatic refreshes
            logger: Optional logger for diagnostic output
        """
        self.query_fn = query_fn
        self.name = name
        self.refresh_interval = refresh_interval
        self.logger = logger or logging.getLogger(__name__)
        self.last_refresh: Optional[datetime] = None
        self.results: Optional[T] = None
        self.is_refreshing = False
        self.refresh_task = None
        self._running = False

    async def refresh(self, force: bool = False) -> None:
        """
        Refresh the materialized view if needed.

        Args:
            force: Whether to force a refresh even if not expired
        """
        now = datetime.now()

        # Check if refresh is needed
        needs_refresh = (
            force
            or self.results is None
            or self.last_refresh is None
            or (now - self.last_refresh) > timedelta(seconds=self.refresh_interval)
        )

        if needs_refresh and not self.is_refreshing:
            self.is_refreshing = True
            try:
                self.logger.debug(f"Refreshing materialized view: {self.name}")
                self.results = await self.query_fn()
                self.last_refresh = now
                self.logger.debug(f"Refreshed materialized view: {self.name}")
            except Exception as e:
                self.logger.error(
                    f"Error refreshing materialized view {self.name}: {e}"
                )
                # Don't update last_refresh if there was an error
            finally:
                self.is_refreshing = False

    async def get_results(self) -> T:
        """
        Get results, refreshing if needed.

        Returns:
            The query results
        """
        await self.refresh()
        return self.results

    async def start_refresh_task(self) -> None:
        """Start a background task that periodically refreshes the view."""
        if self._running:
            return

        self._running = True

        async def refresh_loop():
            # Initial refresh
            await self.refresh(force=True)

            while self._running:
                await asyncio.sleep(self.refresh_interval)
                await self.refresh()

        self.refresh_task = asyncio.create_task(refresh_loop())

    async def stop_refresh_task(self) -> None:
        """Stop the background refresh task."""
        if self._running and self.refresh_task:
            self._running = False
            self.refresh_task.cancel()
            try:
                await self.refresh_task
            except asyncio.CancelledError:
                pass
            self.refresh_task = None

    def get_metadata(self) -> dict[str, Any]:
        """
        Get metadata about this materialized view.

        Returns:
            Dictionary with view metadata
        """
        return {
            "name": self.name,
            "last_refresh": (
                self.last_refresh.isoformat() if self.last_refresh else None
            ),
            "refresh_interval": self.refresh_interval,
            "is_refreshing": self.is_refreshing,
            "has_results": self.results is not None,
            "refresh_task_active": self._running,
        }
