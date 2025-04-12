"""
SQL query debugging and tracking utilities.

This module provides tools to track, log, and analyze SQL queries executed by Uno applications.
"""

import time
import logging
import functools
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass
from contextlib import contextmanager

from uno.database.db_manager import get_db_manager


logger = logging.getLogger("uno.debug.sql")


@dataclass
class SQLQueryInfo:
    """Information about an executed SQL query."""
    
    query: str
    parameters: Optional[Union[tuple, dict]] = None
    duration_ms: float = 0.0
    timestamp: float = 0.0
    context: Optional[str] = None
    source_location: Optional[str] = None


class SQLQueryTracker:
    """Tracks SQL queries executed by the application."""
    
    def __init__(self):
        """Initialize the SQL query tracker."""
        self.queries: List[SQLQueryInfo] = []
        self.enabled = True
        self.track_context = True
        self.track_source = True
    
    def clear(self) -> None:
        """Clear the tracked queries."""
        self.queries = []
    
    def add_query(self, query_info: SQLQueryInfo) -> None:
        """Add a query to the tracker.
        
        Args:
            query_info: Information about the executed query
        """
        if self.enabled:
            self.queries.append(query_info)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the tracked queries.
        
        Returns:
            Dictionary with query statistics
        """
        if not self.queries:
            return {
                "count": 0,
                "total_time_ms": 0,
                "avg_time_ms": 0,
                "min_time_ms": 0,
                "max_time_ms": 0,
                "select_count": 0,
                "insert_count": 0,
                "update_count": 0,
                "delete_count": 0,
                "other_count": 0,
            }
        
        # Calculate timings
        total_time = sum(q.duration_ms for q in self.queries)
        min_time = min(q.duration_ms for q in self.queries)
        max_time = max(q.duration_ms for q in self.queries)
        avg_time = total_time / len(self.queries)
        
        # Count query types
        select_count = sum(1 for q in self.queries if q.query.strip().lower().startswith("select"))
        insert_count = sum(1 for q in self.queries if q.query.strip().lower().startswith("insert"))
        update_count = sum(1 for q in self.queries if q.query.strip().lower().startswith("update"))
        delete_count = sum(1 for q in self.queries if q.query.strip().lower().startswith("delete"))
        other_count = len(self.queries) - select_count - insert_count - update_count - delete_count
        
        return {
            "count": len(self.queries),
            "total_time_ms": total_time,
            "avg_time_ms": avg_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "select_count": select_count,
            "insert_count": insert_count,
            "update_count": update_count,
            "delete_count": delete_count,
            "other_count": other_count,
        }
    
    def get_slow_queries(self, threshold_ms: float = 100.0) -> List[SQLQueryInfo]:
        """Get queries that took longer than the threshold.
        
        Args:
            threshold_ms: Minimum duration in milliseconds to consider a query slow
            
        Returns:
            List of slow queries
        """
        return [q for q in self.queries if q.duration_ms >= threshold_ms]
    
    def get_queries_by_type(self, query_type: str) -> List[SQLQueryInfo]:
        """Get queries of a specific type.
        
        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            
        Returns:
            List of queries of the specified type
        """
        query_type = query_type.upper()
        return [q for q in self.queries if q.query.strip().upper().startswith(query_type)]
    
    def get_duplicate_queries(self) -> Dict[str, List[SQLQueryInfo]]:
        """Get queries that were executed multiple times.
        
        Returns:
            Dictionary mapping normalized query patterns to lists of query instances
        """
        # Normalize queries (remove specific values)
        normalized_queries: Dict[str, List[SQLQueryInfo]] = {}
        
        for query_info in self.queries:
            normalized = self._normalize_query(query_info.query)
            if normalized not in normalized_queries:
                normalized_queries[normalized] = []
            normalized_queries[normalized].append(query_info)
        
        # Filter to only queries that appear more than once
        return {k: v for k, v in normalized_queries.items() if len(v) > 1}
    
    def _normalize_query(self, query: str) -> str:
        """Normalize a SQL query by removing specific values.
        
        Args:
            query: The SQL query to normalize
            
        Returns:
            Normalized query
        """
        # Replace numeric literals
        query = re.sub(r'\b\d+\b', '?', query)
        
        # Replace string literals
        query = re.sub(r"'[^']*'", "'?'", query)
        
        # Replace named parameters
        query = re.sub(r":\w+", ":?", query)
        
        # Replace positional parameters
        query = re.sub(r"\$\d+", "$?", query)
        
        return query


# Global query tracker instance
_query_tracker = SQLQueryTracker()


def get_query_tracker() -> SQLQueryTracker:
    """Get the global query tracker instance.
    
    Returns:
        The global SQLQueryTracker instance
    """
    return _query_tracker


class SQLQueryDebugger:
    """Debug SQL queries in Uno applications."""
    
    def __init__(self, tracker: Optional[SQLQueryTracker] = None):
        """Initialize the SQL query debugger.
        
        Args:
            tracker: Optional custom query tracker
        """
        self.tracker = tracker or _query_tracker
    
    def patch_db_manager(self) -> None:
        """Patch the database manager to track SQL queries."""
        db_manager = get_db_manager()
        
        # Patch execute method if available
        if hasattr(db_manager, "execute"):
            original_execute = db_manager.execute
            
            @functools.wraps(original_execute)
            def patched_execute(query, *args, **kwargs):
                source_location = None
                if self.tracker.track_source:
                    import inspect
                    stack = inspect.stack()
                    if len(stack) > 1:
                        frame = stack[1]
                        source_location = f"{frame.filename}:{frame.lineno}"
                
                context = None
                if self.tracker.track_context:
                    import inspect
                    stack = inspect.stack()
                    for frame in stack[1:]:
                        if frame.function != "execute" and not frame.function.startswith("_"):
                            context = f"{frame.function} in {frame.filename}:{frame.lineno}"
                            break
                
                start_time = time.time()
                try:
                    return original_execute(query, *args, **kwargs)
                finally:
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    # Determine parameters
                    params = args[0] if args else kwargs.get("parameters")
                    
                    query_info = SQLQueryInfo(
                        query=str(query),
                        parameters=params,
                        duration_ms=duration_ms,
                        timestamp=start_time,
                        context=context,
                        source_location=source_location,
                    )
                    
                    self.tracker.add_query(query_info)
                    
                    if duration_ms > 100:
                        logger.warning(
                            f"Slow SQL query ({duration_ms:.2f}ms): {query}",
                            extra={"params": params, "source": source_location}
                        )
            
            db_manager.execute = patched_execute
        
        # Patch engine execute if available
        if hasattr(db_manager, "engine") and hasattr(db_manager.engine, "execute"):
            original_engine_execute = db_manager.engine.execute
            
            @functools.wraps(original_engine_execute)
            def patched_engine_execute(query, *args, **kwargs):
                source_location = None
                if self.tracker.track_source:
                    import inspect
                    stack = inspect.stack()
                    if len(stack) > 1:
                        frame = stack[1]
                        source_location = f"{frame.filename}:{frame.lineno}"
                
                context = None
                if self.tracker.track_context:
                    import inspect
                    stack = inspect.stack()
                    for frame in stack[1:]:
                        if frame.function != "execute" and not frame.function.startswith("_"):
                            context = f"{frame.function} in {frame.filename}:{frame.lineno}"
                            break
                
                start_time = time.time()
                try:
                    return original_engine_execute(query, *args, **kwargs)
                finally:
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    # Determine parameters
                    params = args[0] if args else kwargs.get("parameters")
                    
                    query_info = SQLQueryInfo(
                        query=str(query),
                        parameters=params,
                        duration_ms=duration_ms,
                        timestamp=start_time,
                        context=context,
                        source_location=source_location,
                    )
                    
                    self.tracker.add_query(query_info)
                    
                    if duration_ms > 100:
                        logger.warning(
                            f"Slow SQL query ({duration_ms:.2f}ms): {query}",
                            extra={"params": params, "source": source_location}
                        )
            
            db_manager.engine.execute = patched_engine_execute
    
    def unpatch_db_manager(self) -> None:
        """Remove patches from the database manager."""
        # Not implemented for safety - restarting the app is safer
        pass
    
    @contextmanager
    def capture_queries(self, clear_previous: bool = True) -> SQLQueryTracker:
        """Context manager to capture queries within a specific scope.
        
        Args:
            clear_previous: Whether to clear previously captured queries
            
        Returns:
            The query tracker
        """
        if clear_previous:
            self.tracker.clear()
        
        try:
            yield self.tracker
        finally:
            pass  # Queries are already tracked
    
    def analyze_queries(self) -> Dict[str, Any]:
        """Analyze captured queries and provide optimization suggestions.
        
        Returns:
            Dictionary with analysis results and suggestions
        """
        stats = self.tracker.get_stats()
        slow_queries = self.tracker.get_slow_queries()
        duplicates = self.tracker.get_duplicate_queries()
        
        analysis = {
            "stats": stats,
            "slow_query_count": len(slow_queries),
            "duplicate_pattern_count": len(duplicates),
            "total_duplicate_queries": sum(len(v) for v in duplicates.values()),
            "suggestions": [],
        }
        
        # Add suggestions
        if slow_queries:
            analysis["suggestions"].append(
                f"Found {len(slow_queries)} slow queries (>100ms). Consider adding indexes "
                f"or optimizing these queries."
            )
        
        if duplicates:
            analysis["suggestions"].append(
                f"Found {len(duplicates)} query patterns executed multiple times. "
                f"Consider using query caching or batching."
            )
        
        if stats["count"] > 10 and stats["select_count"] > 5:
            analysis["suggestions"].append(
                "Multiple SELECT queries detected. Consider using JOINs or DataLoader "
                "to reduce the number of database roundtrips."
            )
        
        return analysis


def setup_sql_tracking() -> SQLQueryTracker:
    """Set up SQL query tracking for the application.
    
    Returns:
        The SQL query tracker
    """
    debugger = SQLQueryDebugger()
    debugger.patch_db_manager()
    return debugger.tracker