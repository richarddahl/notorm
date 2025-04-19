# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Transaction metrics collection and monitoring for the Uno application.

This module provides specialized classes and functions for monitoring database
transaction performance, including execution time, success rates, rollback rates,
and transaction isolation statistics. It integrates with the metrics framework.
"""

import asyncio
import time
import statistics
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Callable

from uno.core.logging.framework import get_logger
from uno.core.metrics.framework import (
    MetricType, 
    MetricUnit,
    MetricValue,
    MetricsRegistry,
    get_metrics_registry,
    Timer,
    Counter,
    Histogram,
)


@dataclass
class TransactionMetrics:
    """
    Metrics for a specific transaction.
    
    This class tracks detailed metrics for an individual transaction,
    including execution time, query count, row count, and success/failure.
    """
    
    transaction_id: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    success: bool = False
    query_count: int = 0
    row_count: int = 0
    isolation_level: str = "READ COMMITTED"
    savepoints: int = 0
    rollbacks_to_savepoint: int = 0
    error_message: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        """Get the transaction duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    @property
    def is_completed(self) -> bool:
        """Check if the transaction is completed."""
        return self.end_time is not None
    
    def record_query(self, rows: int = 0) -> None:
        """
        Record a query execution.
        
        Args:
            rows: Number of rows affected/returned
        """
        self.query_count += 1
        self.row_count += rows
    
    def record_savepoint(self) -> None:
        """Record a savepoint creation."""
        self.savepoints += 1
    
    def record_rollback_to_savepoint(self) -> None:
        """Record a rollback to savepoint."""
        self.rollbacks_to_savepoint += 1
    
    def complete(self, success: bool, error: Optional[str] = None) -> None:
        """
        Mark the transaction as complete.
        
        Args:
            success: Whether the transaction succeeded
            error: Optional error message for failed transactions
        """
        self.end_time = time.time()
        self.success = success
        self.error_message = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction metrics to a dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "query_count": self.query_count,
            "row_count": self.row_count,
            "isolation_level": self.isolation_level,
            "savepoints": self.savepoints,
            "rollbacks_to_savepoint": self.rollbacks_to_savepoint,
            "error_message": self.error_message,
        }


class TransactionMetricsTracker:
    """
    Tracker for transaction metrics.
    
    This class provides methods for tracking transaction metrics
    and reporting them to a metrics registry.
    """
    
    def __init__(
        self,
        registry: Optional[MetricsRegistry] = None,
    ):
        """
        Initialize the transaction metrics tracker.
        
        Args:
            registry: Metrics registry to use
        """
        self.registry = registry or get_metrics_registry()
        self.logger = get_logger("uno.metrics.transaction")
        self._current_transactions: Dict[str, TransactionMetrics] = {}
        self._transaction_history: List[TransactionMetrics] = []
        self._max_history_size = 1000
        self._lock = asyncio.Lock()
        
        # Initialize metrics
        self._setup_task = asyncio.create_task(self._setup_metrics())
    
    async def _setup_metrics(self) -> None:
        """Set up the metrics counters and timers."""
        self.transaction_timer = await self.registry.get_or_create_timer(
            name="db.transaction.duration",
            description="Database transaction duration in milliseconds",
        )
        
        self.transaction_counter = await self.registry.get_or_create_counter(
            name="db.transaction.count",
            description="Total number of database transactions",
        )
        
        self.transaction_success_counter = await self.registry.get_or_create_counter(
            name="db.transaction.success",
            description="Number of successful database transactions",
        )
        
        self.transaction_failure_counter = await self.registry.get_or_create_counter(
            name="db.transaction.failure",
            description="Number of failed database transactions",
        )
        
        self.query_counter = await self.registry.get_or_create_counter(
            name="db.query.count",
            description="Total number of database queries",
        )
        
        self.row_histogram = await self.registry.get_or_create_histogram(
            name="db.query.rows",
            description="Number of rows affected/returned by database queries",
        )
        
        self.isolation_level_counter = await self.registry.get_or_create_counter(
            name="db.transaction.isolation_level",
            description="Number of transactions by isolation level",
        )
        
        self.savepoint_counter = await self.registry.get_or_create_counter(
            name="db.transaction.savepoint",
            description="Number of savepoints created",
        )
        
        self.rollback_to_savepoint_counter = await self.registry.get_or_create_counter(
            name="db.transaction.rollback_to_savepoint",
            description="Number of rollbacks to savepoint",
        )
    
    async def start_transaction(
        self,
        transaction_id: str,
        isolation_level: str = "READ COMMITTED",
    ) -> TransactionMetrics:
        """
        Start tracking a transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
            isolation_level: Transaction isolation level
            
        Returns:
            Transaction metrics object
        """
        metrics = TransactionMetrics(
            transaction_id=transaction_id,
            isolation_level=isolation_level,
        )
        
        async with self._lock:
            self._current_transactions[transaction_id] = metrics
        
        # Record isolation level
        await self.isolation_level_counter.increment()
        
        self.logger.debug(f"Started tracking transaction: {transaction_id}")
        return metrics
    
    async def end_transaction(
        self,
        transaction_id: str,
        success: bool,
        error: Optional[str] = None,
    ) -> Optional[TransactionMetrics]:
        """
        End tracking a transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
            success: Whether the transaction succeeded
            error: Optional error message for failed transactions
            
        Returns:
            Transaction metrics object or None if not found
        """
        metrics = None
        
        async with self._lock:
            if transaction_id in self._current_transactions:
                metrics = self._current_transactions[transaction_id]
                metrics.complete(success, error)
                
                # Record metrics
                await self.transaction_counter.increment()
                await self.transaction_timer.record(metrics.duration_ms)
                await self.query_counter.increment(metrics.query_count)
                
                if metrics.row_count > 0:
                    await self.row_histogram.observe(metrics.row_count)
                
                if metrics.savepoints > 0:
                    await self.savepoint_counter.increment(metrics.savepoints)
                
                if metrics.rollbacks_to_savepoint > 0:
                    await self.rollback_to_savepoint_counter.increment(
                        metrics.rollbacks_to_savepoint
                    )
                
                if success:
                    await self.transaction_success_counter.increment()
                else:
                    await self.transaction_failure_counter.increment()
                
                # Store in history and remove from current
                self._transaction_history.append(metrics)
                del self._current_transactions[transaction_id]
                
                # Trim history if needed
                if len(self._transaction_history) > self._max_history_size:
                    self._transaction_history = self._transaction_history[-self._max_history_size:]
                
                self.logger.debug(
                    f"Ended tracking transaction: {transaction_id}, "
                    f"success: {success}, duration: {metrics.duration_ms:.2f}ms"
                )
        
        return metrics
    
    async def record_query(
        self,
        transaction_id: str,
        rows: int = 0,
    ) -> None:
        """
        Record a query execution within a transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
            rows: Number of rows affected/returned
        """
        async with self._lock:
            if transaction_id in self._current_transactions:
                self._current_transactions[transaction_id].record_query(rows)
    
    async def record_savepoint(self, transaction_id: str) -> None:
        """
        Record a savepoint creation within a transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
        """
        async with self._lock:
            if transaction_id in self._current_transactions:
                self._current_transactions[transaction_id].record_savepoint()
    
    async def record_rollback_to_savepoint(self, transaction_id: str) -> None:
        """
        Record a rollback to savepoint within a transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
        """
        async with self._lock:
            if transaction_id in self._current_transactions:
                self._current_transactions[transaction_id].record_rollback_to_savepoint()
    
    async def get_transaction_metrics(
        self,
        transaction_id: str,
    ) -> Optional[TransactionMetrics]:
        """
        Get metrics for a specific transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
            
        Returns:
            Transaction metrics object or None if not found
        """
        async with self._lock:
            if transaction_id in self._current_transactions:
                return self._current_transactions[transaction_id]
            
            # Check history
            for metrics in reversed(self._transaction_history):
                if metrics.transaction_id == transaction_id:
                    return metrics
        
        return None
    
    async def get_active_transactions(self) -> List[TransactionMetrics]:
        """
        Get metrics for all active transactions.
        
        Returns:
            List of transaction metrics objects
        """
        async with self._lock:
            return list(self._current_transactions.values())
    
    async def get_recent_transactions(self, limit: int = 100) -> List[TransactionMetrics]:
        """
        Get metrics for recent transactions.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction metrics objects
        """
        async with self._lock:
            return self._transaction_history[-limit:]
    
    async def get_transaction_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all tracked transactions.
        
        Returns:
            Dictionary of transaction statistics
        """
        recent_transactions = await self.get_recent_transactions()
        
        if not recent_transactions:
            return {
                "count": 0,
                "avg_duration_ms": 0.0,
                "max_duration_ms": 0.0,
                "min_duration_ms": 0.0,
                "success_rate": 0.0,
                "avg_queries_per_transaction": 0.0,
                "isolation_levels": {},
            }
        
        # Calculate statistics
        durations = [t.duration_ms for t in recent_transactions if t.is_completed]
        succeeded = [t for t in recent_transactions if t.success]
        
        # Count by isolation level
        isolation_levels: Dict[str, int] = {}
        for t in recent_transactions:
            level = t.isolation_level
            isolation_levels[level] = isolation_levels.get(level, 0) + 1
        
        return {
            "count": len(recent_transactions),
            "active_count": len(await self.get_active_transactions()),
            "avg_duration_ms": statistics.mean(durations) if durations else 0.0,
            "max_duration_ms": max(durations) if durations else 0.0,
            "min_duration_ms": min(durations) if durations else 0.0,
            "success_rate": len(succeeded) / len(recent_transactions) if recent_transactions else 0.0,
            "avg_queries_per_transaction": statistics.mean([t.query_count for t in recent_transactions]),
            "isolation_levels": isolation_levels,
        }


# Global transaction metrics tracker
_transaction_metrics_tracker: Optional[TransactionMetricsTracker] = None


def get_transaction_metrics_tracker() -> TransactionMetricsTracker:
    """
    Get the global transaction metrics tracker.
    
    Returns:
        The global transaction metrics tracker
    """
    global _transaction_metrics_tracker
    if _transaction_metrics_tracker is None:
        _transaction_metrics_tracker = TransactionMetricsTracker()
    return _transaction_metrics_tracker


class TransactionContext:
    """
    Context manager for tracking a database transaction.
    
    This class provides a context manager that automatically tracks
    transaction metrics, integrating with both the database session
    and the metrics framework.
    
    Example:
        async with TransactionContext(session, "my-transaction") as ctx:
            await session.execute(text("INSERT INTO ..."))
            # Metrics automatically tracked
    """
    
    def __init__(
        self,
        session: Any,
        transaction_id: Optional[str] = None,
        isolation_level: str = "READ COMMITTED",
        tracker: Optional[TransactionMetricsTracker] = None,
    ):
        """
        Initialize a transaction context.
        
        Args:
            session: Database session
            transaction_id: Unique identifier for the transaction (auto-generated if None)
            isolation_level: Transaction isolation level
            tracker: Transaction metrics tracker to use
        """
        self.session = session
        self.transaction_id = transaction_id or f"tx-{time.time()}-{id(session)}"
        self.isolation_level = isolation_level
        self.tracker = tracker or get_transaction_metrics_tracker()
        self.transaction = None
        self.metrics = None
        self.success = False
        self.error = None
        self.logger = get_logger("uno.db.transaction")
    
    async def __aenter__(self) -> 'TransactionContext':
        """Start the transaction and metrics tracking."""
        # Start transaction
        self.transaction = await self.session.begin()
        
        # Start metrics tracking
        self.metrics = await self.tracker.start_transaction(
            transaction_id=self.transaction_id,
            isolation_level=self.isolation_level,
        )
        
        self.logger.debug(f"Started transaction: {self.transaction_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        End the transaction and metrics tracking.
        
        Args:
            exc_type: Exception type, if any
            exc_val: Exception value, if any
            exc_tb: Exception traceback, if any
            
        Returns:
            True if the exception was handled, False otherwise
        """
        if exc_type is not None:
            # An exception occurred, roll back the transaction
            await self.transaction.rollback()
            self.success = False
            self.error = str(exc_val)
            self.logger.warning(
                f"Rolling back transaction {self.transaction_id} due to error: {self.error}"
            )
        else:
            # No exception, commit the transaction
            await self.transaction.commit()
            self.success = True
            self.logger.debug(f"Committed transaction: {self.transaction_id}")
        
        # End metrics tracking
        await self.tracker.end_transaction(
            transaction_id=self.transaction_id,
            success=self.success,
            error=self.error,
        )
        
        # Don't suppress exceptions
        return False
    
    async def record_query(self, rows: int = 0) -> None:
        """
        Record a query execution.
        
        Args:
            rows: Number of rows affected/returned
        """
        await self.tracker.record_query(
            transaction_id=self.transaction_id,
            rows=rows,
        )
    
    async def savepoint(self, name: Optional[str] = None) -> Any:
        """
        Create a savepoint.
        
        Args:
            name: Optional savepoint name
            
        Returns:
            Savepoint object
        """
        savepoint = await self.transaction.begin_nested()
        await self.tracker.record_savepoint(self.transaction_id)
        self.logger.debug(f"Created savepoint in transaction: {self.transaction_id}")
        return savepoint
    
    async def rollback_to_savepoint(self, savepoint: Any) -> None:
        """
        Roll back to a savepoint.
        
        Args:
            savepoint: Savepoint to roll back to
        """
        await savepoint.rollback()
        await self.tracker.record_rollback_to_savepoint(self.transaction_id)
        self.logger.debug(f"Rolled back to savepoint in transaction: {self.transaction_id}")