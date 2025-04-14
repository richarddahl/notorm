"""
Repository debugging tools for Uno applications.

This module provides utilities for debugging repository operations, including tracking
and analyzing database operations performed by repositories.
"""

import time
import inspect
import logging
import functools
from typing import Any, Dict, List, Optional, Set, Type, Union, Callable
from dataclasses import dataclass, field

from uno.dependencies.repository import UnoRepository


logger = logging.getLogger("uno.debug.repository")


@dataclass
class RepositoryOperation:
    """Information about a repository operation."""

    method: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[Exception] = None
    duration_ms: float = 0.0
    timestamp: float = 0.0
    repository_class: Optional[str] = None
    source_location: Optional[str] = None


class RepositoryTracker:
    """Tracks repository operations."""

    def __init__(self):
        """Initialize the repository tracker."""
        self.operations: List[RepositoryOperation] = []
        self.enabled = True
        self.track_source = True

    def clear(self) -> None:
        """Clear the tracked operations."""
        self.operations = []

    def add_operation(self, operation: RepositoryOperation) -> None:
        """Add an operation to the tracker.

        Args:
            operation: Repository operation information
        """
        if self.enabled:
            self.operations.append(operation)

    def get_operations_by_method(self, method: str) -> List[RepositoryOperation]:
        """Get operations by method name.

        Args:
            method: Method name to filter by

        Returns:
            List of operations with the specified method
        """
        return [op for op in self.operations if op.method == method]

    def get_operations_by_repository(
        self, repository_class: str
    ) -> List[RepositoryOperation]:
        """Get operations by repository class.

        Args:
            repository_class: Repository class name to filter by

        Returns:
            List of operations from the specified repository class
        """
        return [op for op in self.operations if op.repository_class == repository_class]

    def get_slow_operations(
        self, threshold_ms: float = 100.0
    ) -> List[RepositoryOperation]:
        """Get operations that took longer than the threshold.

        Args:
            threshold_ms: Minimum duration in milliseconds to consider an operation slow

        Returns:
            List of slow operations
        """
        return [op for op in self.operations if op.duration_ms >= threshold_ms]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked operations.

        Returns:
            Dictionary with operation statistics
        """
        if not self.operations:
            return {
                "count": 0,
                "total_time_ms": 0,
                "avg_time_ms": 0,
                "min_time_ms": 0,
                "max_time_ms": 0,
                "method_counts": {},
                "repository_counts": {},
                "error_count": 0,
            }

        # Calculate timings
        total_time = sum(op.duration_ms for op in self.operations)
        min_time = min(op.duration_ms for op in self.operations)
        max_time = max(op.duration_ms for op in self.operations)
        avg_time = total_time / len(self.operations)

        # Count methods
        method_counts = {}
        for op in self.operations:
            method_counts[op.method] = method_counts.get(op.method, 0) + 1

        # Count repositories
        repo_counts = {}
        for op in self.operations:
            if op.repository_class:
                repo_counts[op.repository_class] = (
                    repo_counts.get(op.repository_class, 0) + 1
                )

        # Count errors
        error_count = sum(1 for op in self.operations if op.error is not None)

        return {
            "count": len(self.operations),
            "total_time_ms": total_time,
            "avg_time_ms": avg_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "method_counts": method_counts,
            "repository_counts": repo_counts,
            "error_count": error_count,
        }


# Global repository tracker
_repository_tracker = RepositoryTracker()


def get_repository_tracker() -> RepositoryTracker:
    """Get the global repository tracker.

    Returns:
        The global repository tracker
    """
    return _repository_tracker


class RepositoryDebugger:
    """Debug repository operations in Uno applications."""

    def __init__(self, tracker: Optional[RepositoryTracker] = None):
        """Initialize the repository debugger.

        Args:
            tracker: Optional custom repository tracker
        """
        self.tracker = tracker or _repository_tracker

    def patch_repository_class(self, repo_class: Type[UnoRepository]) -> None:
        """Patch a repository class to track operations.

        Args:
            repo_class: Repository class to patch
        """
        # Get public methods to patch
        methods = inspect.getmembers(
            repo_class,
            predicate=lambda m: inspect.isfunction(m)
            and not m.__name__.startswith("_"),
        )

        for name, method in methods:
            # Skip already patched methods
            if hasattr(method, "_repo_debug_patched"):
                continue

            # Create patched method
            @functools.wraps(method)
            def patched_method(self, *args, **kwargs):
                source_location = None
                if self.tracker.track_source:
                    stack = inspect.stack()
                    if len(stack) > 1:
                        frame = stack[1]
                        source_location = f"{frame.filename}:{frame.lineno}"

                start_time = time.time()
                result = None
                error = None

                try:
                    result = method(self, *args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000

                    # Create operation record
                    operation = RepositoryOperation(
                        method=method.__name__,
                        args=args,
                        kwargs=kwargs,
                        result=result,
                        error=error,
                        duration_ms=duration_ms,
                        timestamp=start_time,
                        repository_class=repo_class.__name__,
                        source_location=source_location,
                    )

                    self.tracker.add_operation(operation)

                    if duration_ms > 100:
                        logger.warning(
                            f"Slow repository operation: {repo_class.__name__}.{method.__name__} "
                            f"({duration_ms:.2f}ms)",
                            extra={"source": source_location},
                        )

            # Mark the method as patched
            patched_method._repo_debug_patched = True

            # Replace the original method
            setattr(repo_class, name, patched_method)

    def patch_all_repositories(self) -> None:
        """Patch all repository classes to track operations."""
        # Find all repository classes
        import uno.database.repository

        # Get base repository class
        base_repo = uno.database.repository.UnoRepository

        # Get all repository classes
        repo_classes = []

        # This is a simplified approach - in a real application we'd need to
        # discover all repository classes across all modules
        for attr_name in dir(uno.database.repository):
            attr = getattr(uno.database.repository, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, base_repo)
                and attr is not base_repo
            ):
                repo_classes.append(attr)

        # Patch each repository class
        for repo_class in repo_classes:
            self.patch_repository_class(repo_class)

    def analyze_operations(self) -> Dict[str, Any]:
        """Analyze repository operations and provide optimization suggestions.

        Returns:
            Dictionary with analysis results and suggestions
        """
        stats = self.tracker.get_stats()
        slow_operations = self.tracker.get_slow_operations()

        # Identify N+1 query patterns
        n_plus_one = self._identify_n_plus_one_queries()

        analysis = {
            "stats": stats,
            "slow_operation_count": len(slow_operations),
            "n_plus_one_patterns": len(n_plus_one),
            "suggestions": [],
        }

        # Add suggestions
        if slow_operations:
            analysis["suggestions"].append(
                f"Found {len(slow_operations)} slow operations (>100ms). "
                f"Consider optimizing these operations or adding indexes."
            )

        if n_plus_one:
            analysis["suggestions"].append(
                f"Found {len(n_plus_one)} potential N+1 query patterns. "
                f"Consider using batch loading or eager loading."
            )

        if stats["method_counts"].get("get_by_id", 0) > 5:
            analysis["suggestions"].append(
                "Multiple get_by_id operations detected. "
                "Consider using batch loading with DataLoader."
            )

        return analysis

    def _identify_n_plus_one_queries(self) -> List[Dict[str, Any]]:
        """Identify potential N+1 query patterns in repository operations.

        Returns:
            List of potential N+1 query patterns
        """
        operations = self.tracker.operations
        if not operations:
            return []

        # Group operations by source location
        operations_by_source = {}
        for op in operations:
            if op.source_location:
                if op.source_location not in operations_by_source:
                    operations_by_source[op.source_location] = []
                operations_by_source[op.source_location].append(op)

        # Identify locations with multiple similar operations
        n_plus_one_patterns = []

        for source, source_ops in operations_by_source.items():
            # Skip sources with just one operation
            if len(source_ops) <= 1:
                continue

            # Group by method
            ops_by_method = {}
            for op in source_ops:
                if op.method not in ops_by_method:
                    ops_by_method[op.method] = []
                ops_by_method[op.method].append(op)

            # Check for methods called multiple times
            for method, method_ops in ops_by_method.items():
                if len(method_ops) > 3 and method in (
                    "get_by_id",
                    "get",
                    "find",
                    "find_one",
                    "find_by_id",
                ):
                    n_plus_one_patterns.append(
                        {
                            "source": source,
                            "method": method,
                            "count": len(method_ops),
                            "repository_class": method_ops[0].repository_class,
                        }
                    )

        return n_plus_one_patterns


def debug_repository(repository: UnoRepository) -> None:
    """Enable debugging for a specific repository instance.

    Args:
        repository: Repository instance to debug
    """
    debugger = RepositoryDebugger()
    debugger.patch_repository_class(repository.__class__)
