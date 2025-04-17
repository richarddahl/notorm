"""
CQRS monitoring and observability components.

This module provides monitoring and observability features for the CQRS pattern in uno, 
including:

1. Metrics collection for commands and queries
2. Performance tracking
3. Health checks for CQRS components
4. Logging and tracing integration
5. Alerting for anomalies
"""

import logging
import time
import asyncio
import json
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union, 
    Awaitable
)

from uno.core.cqrs import (
    Command, Query, CommandHandler, QueryHandler, CommandBus, QueryBus, 
    Mediator, get_mediator
)
from uno.core.result import Result, Success, Failure, Error
from uno.domain.event_store import EventStore

# Type variables for generic classes
TCommand = TypeVar('TCommand', bound=Command)
TResult = TypeVar('TResult')
TQuery = TypeVar('TQuery', bound=Query)

# Configure logger
logger = logging.getLogger(__name__)


class MetricsProvider:
    """
    Abstract interface for metrics providers.
    
    This allows for plugging in different metrics backends (Prometheus, StatsD, etc.).
    """
    
    def counter(
        self, 
        name: str, 
        description: str, 
        labels: List[str] = None
    ) -> 'Counter':
        """
        Create a counter metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names
            
        Returns:
            Counter metric
        """
        raise NotImplementedError()
    
    def gauge(
        self, 
        name: str, 
        description: str, 
        labels: List[str] = None
    ) -> 'Gauge':
        """
        Create a gauge metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names
            
        Returns:
            Gauge metric
        """
        raise NotImplementedError()
    
    def histogram(
        self, 
        name: str, 
        description: str, 
        labels: List[str] = None,
        buckets: List[float] = None
    ) -> 'Histogram':
        """
        Create a histogram metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names
            buckets: Optional histogram buckets
            
        Returns:
            Histogram metric
        """
        raise NotImplementedError()


class Counter:
    """Interface for counter metrics."""
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """
        Increment the counter.
        
        Args:
            value: Value to increment by
            labels: Optional labels
        """
        raise NotImplementedError()
    
    def labels(self, **kwargs) -> 'Counter':
        """
        Create a counter with labels.
        
        Args:
            **kwargs: Label values
            
        Returns:
            Labeled counter
        """
        raise NotImplementedError()


class Gauge:
    """Interface for gauge metrics."""
    
    def set(self, value: float, labels: Dict[str, str] = None) -> None:
        """
        Set the gauge value.
        
        Args:
            value: Value to set
            labels: Optional labels
        """
        raise NotImplementedError()
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """
        Increment the gauge.
        
        Args:
            value: Value to increment by
            labels: Optional labels
        """
        raise NotImplementedError()
    
    def dec(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """
        Decrement the gauge.
        
        Args:
            value: Value to decrement by
            labels: Optional labels
        """
        raise NotImplementedError()
    
    def labels(self, **kwargs) -> 'Gauge':
        """
        Create a gauge with labels.
        
        Args:
            **kwargs: Label values
            
        Returns:
            Labeled gauge
        """
        raise NotImplementedError()


class Histogram:
    """Interface for histogram metrics."""
    
    def observe(self, value: float, labels: Dict[str, str] = None) -> None:
        """
        Observe a value.
        
        Args:
            value: Value to observe
            labels: Optional labels
        """
        raise NotImplementedError()
    
    def labels(self, **kwargs) -> 'Histogram':
        """
        Create a histogram with labels.
        
        Args:
            **kwargs: Label values
            
        Returns:
            Labeled histogram
        """
        raise NotImplementedError()


class InMemoryMetricsProvider(MetricsProvider):
    """
    In-memory implementation of metrics provider for testing and simple usage.
    
    This provider stores metrics in memory and allows for retrieval for display
    or testing purposes.
    """
    
    def __init__(self):
        """Initialize the in-memory metrics provider."""
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
    
    def counter(
        self, 
        name: str, 
        description: str, 
        labels: List[str] = None
    ) -> Counter:
        """Create an in-memory counter."""
        if name not in self.counters:
            counter = InMemoryCounter(name, description, labels or [])
            self.counters[name] = counter
        return self.counters[name]
    
    def gauge(
        self, 
        name: str, 
        description: str, 
        labels: List[str] = None
    ) -> Gauge:
        """Create an in-memory gauge."""
        if name not in self.gauges:
            gauge = InMemoryGauge(name, description, labels or [])
            self.gauges[name] = gauge
        return self.gauges[name]
    
    def histogram(
        self, 
        name: str, 
        description: str, 
        labels: List[str] = None,
        buckets: List[float] = None
    ) -> Histogram:
        """Create an in-memory histogram."""
        if name not in self.histograms:
            histogram = InMemoryHistogram(
                name, description, labels or [], buckets or [0.01, 0.05, 0.1, 0.5, 1, 5]
            )
            self.histograms[name] = histogram
        return self.histograms[name]
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all metrics.
        
        Returns:
            Dictionary with all metrics
        """
        result = {
            "counters": {name: counter.get_data() for name, counter in self.counters.items()},
            "gauges": {name: gauge.get_data() for name, gauge in self.gauges.items()},
            "histograms": {name: histogram.get_data() for name, histogram in self.histograms.items()}
        }
        return result


class InMemoryCounter(Counter):
    """In-memory counter implementation."""
    
    def __init__(self, name: str, description: str, label_names: List[str]):
        """
        Initialize the counter.
        
        Args:
            name: Counter name
            description: Counter description
            label_names: Label names
        """
        self.name = name
        self.description = description
        self.label_names = label_names
        self.values = {}  # Label values -> count
        self.default_value = 0
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Increment the counter."""
        if labels:
            label_key = self._label_key(labels)
            self.values[label_key] = self.values.get(label_key, 0) + value
        else:
            self.default_value += value
    
    def labels(self, **kwargs) -> Counter:
        """Create a labeled counter."""
        return LabeledCounter(self, kwargs)
    
    def _label_key(self, labels: Dict[str, str]) -> str:
        """Create a key from labels."""
        parts = []
        for name in self.label_names:
            if name in labels:
                parts.append(f"{name}={labels[name]}")
        return ";".join(parts)
    
    def get_data(self) -> Dict[str, Any]:
        """Get counter data."""
        return {
            "name": self.name,
            "description": self.description,
            "default_value": self.default_value,
            "values": self.values
        }


class LabeledCounter(Counter):
    """Counter with predefined labels."""
    
    def __init__(self, parent: InMemoryCounter, labels: Dict[str, str]):
        """
        Initialize the labeled counter.
        
        Args:
            parent: Parent counter
            labels: Label values
        """
        self.parent = parent
        self.labels = labels
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Increment the counter."""
        combined_labels = dict(self.labels)
        if labels:
            combined_labels.update(labels)
        self.parent.inc(value, combined_labels)
    
    def labels(self, **kwargs) -> Counter:
        """Create a counter with additional labels."""
        combined_labels = dict(self.labels)
        combined_labels.update(kwargs)
        return LabeledCounter(self.parent, combined_labels)


class InMemoryGauge(Gauge):
    """In-memory gauge implementation."""
    
    def __init__(self, name: str, description: str, label_names: List[str]):
        """
        Initialize the gauge.
        
        Args:
            name: Gauge name
            description: Gauge description
            label_names: Label names
        """
        self.name = name
        self.description = description
        self.label_names = label_names
        self.values = {}  # Label values -> value
        self.default_value = 0
    
    def set(self, value: float, labels: Dict[str, str] = None) -> None:
        """Set the gauge value."""
        if labels:
            label_key = self._label_key(labels)
            self.values[label_key] = value
        else:
            self.default_value = value
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Increment the gauge."""
        if labels:
            label_key = self._label_key(labels)
            self.values[label_key] = self.values.get(label_key, 0) + value
        else:
            self.default_value += value
    
    def dec(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Decrement the gauge."""
        if labels:
            label_key = self._label_key(labels)
            self.values[label_key] = self.values.get(label_key, 0) - value
        else:
            self.default_value -= value
    
    def labels(self, **kwargs) -> Gauge:
        """Create a labeled gauge."""
        return LabeledGauge(self, kwargs)
    
    def _label_key(self, labels: Dict[str, str]) -> str:
        """Create a key from labels."""
        parts = []
        for name in self.label_names:
            if name in labels:
                parts.append(f"{name}={labels[name]}")
        return ";".join(parts)
    
    def get_data(self) -> Dict[str, Any]:
        """Get gauge data."""
        return {
            "name": self.name,
            "description": self.description,
            "default_value": self.default_value,
            "values": self.values
        }


class LabeledGauge(Gauge):
    """Gauge with predefined labels."""
    
    def __init__(self, parent: InMemoryGauge, labels: Dict[str, str]):
        """
        Initialize the labeled gauge.
        
        Args:
            parent: Parent gauge
            labels: Label values
        """
        self.parent = parent
        self.labels = labels
    
    def set(self, value: float, labels: Dict[str, str] = None) -> None:
        """Set the gauge value."""
        combined_labels = dict(self.labels)
        if labels:
            combined_labels.update(labels)
        self.parent.set(value, combined_labels)
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Increment the gauge."""
        combined_labels = dict(self.labels)
        if labels:
            combined_labels.update(labels)
        self.parent.inc(value, combined_labels)
    
    def dec(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Decrement the gauge."""
        combined_labels = dict(self.labels)
        if labels:
            combined_labels.update(labels)
        self.parent.dec(value, combined_labels)
    
    def labels(self, **kwargs) -> Gauge:
        """Create a gauge with additional labels."""
        combined_labels = dict(self.labels)
        combined_labels.update(kwargs)
        return LabeledGauge(self.parent, combined_labels)


class InMemoryHistogram(Histogram):
    """In-memory histogram implementation."""
    
    def __init__(
        self,
        name: str,
        description: str,
        label_names: List[str],
        buckets: List[float]
    ):
        """
        Initialize the histogram.
        
        Args:
            name: Histogram name
            description: Histogram description
            label_names: Label names
            buckets: Histogram buckets
        """
        self.name = name
        self.description = description
        self.label_names = label_names
        self.buckets = sorted(buckets)
        self.observations = {}  # Label values -> list of observations
        self.default_observations = []
    
    def observe(self, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a value."""
        if labels:
            label_key = self._label_key(labels)
            if label_key not in self.observations:
                self.observations[label_key] = []
            self.observations[label_key].append(value)
        else:
            self.default_observations.append(value)
    
    def labels(self, **kwargs) -> Histogram:
        """Create a labeled histogram."""
        return LabeledHistogram(self, kwargs)
    
    def _label_key(self, labels: Dict[str, str]) -> str:
        """Create a key from labels."""
        parts = []
        for name in self.label_names:
            if name in labels:
                parts.append(f"{name}={labels[name]}")
        return ";".join(parts)
    
    def get_data(self) -> Dict[str, Any]:
        """Get histogram data."""
        default_buckets = self._calculate_buckets(self.default_observations)
        labeled_buckets = {}
        
        for label_key, observations in self.observations.items():
            labeled_buckets[label_key] = self._calculate_buckets(observations)
        
        return {
            "name": self.name,
            "description": self.description,
            "buckets": self.buckets,
            "default_buckets": default_buckets,
            "labeled_buckets": labeled_buckets,
            "default_observations": self.default_observations,
            "observations": self.observations
        }
    
    def _calculate_buckets(self, observations: List[float]) -> Dict[float, int]:
        """Calculate histogram buckets."""
        result = {bucket: 0 for bucket in self.buckets}
        result[float('inf')] = 0
        
        for value in observations:
            for bucket in self.buckets:
                if value <= bucket:
                    result[bucket] += 1
            result[float('inf')] += 1
        
        return result


class LabeledHistogram(Histogram):
    """Histogram with predefined labels."""
    
    def __init__(self, parent: InMemoryHistogram, labels: Dict[str, str]):
        """
        Initialize the labeled histogram.
        
        Args:
            parent: Parent histogram
            labels: Label values
        """
        self.parent = parent
        self.labels = labels
    
    def observe(self, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a value."""
        combined_labels = dict(self.labels)
        if labels:
            combined_labels.update(labels)
        self.parent.observe(value, combined_labels)
    
    def labels(self, **kwargs) -> Histogram:
        """Create a histogram with additional labels."""
        combined_labels = dict(self.labels)
        combined_labels.update(kwargs)
        return LabeledHistogram(self.parent, combined_labels)


class CQRSMetrics:
    """
    Metrics collector for CQRS operations.
    
    This class collects metrics for CQRS operations (commands and queries)
    and provides methods for accessing and analyzing them.
    """
    
    def __init__(self, metrics_provider: MetricsProvider):
        """
        Initialize the CQRS metrics collector.
        
        Args:
            metrics_provider: Metrics provider implementation
        """
        self.metrics_provider = metrics_provider
        
        # Command metrics
        self.command_count = metrics_provider.counter(
            name="cqrs_commands_total",
            description="Total number of commands executed",
            labels=["command_type", "success"]
        )
        
        self.command_duration = metrics_provider.histogram(
            name="cqrs_command_duration_seconds",
            description="Command execution duration in seconds",
            labels=["command_type"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 5]
        )
        
        self.command_active = metrics_provider.gauge(
            name="cqrs_commands_active",
            description="Number of commands currently being processed",
            labels=["command_type"]
        )
        
        # Query metrics
        self.query_count = metrics_provider.counter(
            name="cqrs_queries_total",
            description="Total number of queries executed",
            labels=["query_type", "success", "cached"]
        )
        
        self.query_duration = metrics_provider.histogram(
            name="cqrs_query_duration_seconds",
            description="Query execution duration in seconds",
            labels=["query_type", "cached"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1]
        )
        
        self.query_active = metrics_provider.gauge(
            name="cqrs_queries_active",
            description="Number of queries currently being processed",
            labels=["query_type"]
        )
        
        self.query_result_size = metrics_provider.histogram(
            name="cqrs_query_result_size",
            description="Number of items returned by queries",
            labels=["query_type"],
            buckets=[0, 1, 10, 100, 1000, 10000]
        )
        
        # Event metrics
        self.event_count = metrics_provider.counter(
            name="cqrs_events_total",
            description="Total number of events processed",
            labels=["event_type", "success"]
        )
        
        self.event_processing_duration = metrics_provider.histogram(
            name="cqrs_event_processing_seconds",
            description="Event processing duration in seconds",
            labels=["event_type"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1]
        )
        
        self.event_queue_size = metrics_provider.gauge(
            name="cqrs_event_queue_size",
            description="Number of events waiting to be processed",
            labels=["queue_name"]
        )
    
    def record_command_execution(
        self, 
        command_type: str, 
        duration: float, 
        success: bool
    ) -> None:
        """
        Record command execution metrics.
        
        Args:
            command_type: Type of command
            duration: Execution duration in seconds
            success: Whether the command was successful
        """
        self.command_count.labels(
            command_type=command_type,
            success=str(success)
        ).inc()
        
        self.command_duration.labels(
            command_type=command_type
        ).observe(duration)
    
    def record_command_start(self, command_type: str) -> None:
        """
        Record command start.
        
        Args:
            command_type: Type of command
        """
        self.command_active.labels(
            command_type=command_type
        ).inc()
    
    def record_command_end(self, command_type: str) -> None:
        """
        Record command end.
        
        Args:
            command_type: Type of command
        """
        self.command_active.labels(
            command_type=command_type
        ).dec()
    
    def record_query_execution(
        self, 
        query_type: str, 
        duration: float, 
        success: bool, 
        cached: bool,
        result_size: int = 0
    ) -> None:
        """
        Record query execution metrics.
        
        Args:
            query_type: Type of query
            duration: Execution duration in seconds
            success: Whether the query was successful
            cached: Whether the result was from cache
            result_size: Size of the result (items count)
        """
        self.query_count.labels(
            query_type=query_type,
            success=str(success),
            cached=str(cached)
        ).inc()
        
        self.query_duration.labels(
            query_type=query_type,
            cached=str(cached)
        ).observe(duration)
        
        if success and result_size > 0:
            self.query_result_size.labels(
                query_type=query_type
            ).observe(result_size)
    
    def record_query_start(self, query_type: str) -> None:
        """
        Record query start.
        
        Args:
            query_type: Type of query
        """
        self.query_active.labels(
            query_type=query_type
        ).inc()
    
    def record_query_end(self, query_type: str) -> None:
        """
        Record query end.
        
        Args:
            query_type: Type of query
        """
        self.query_active.labels(
            query_type=query_type
        ).dec()
    
    def record_event_processed(
        self, 
        event_type: str, 
        duration: float, 
        success: bool
    ) -> None:
        """
        Record event processing metrics.
        
        Args:
            event_type: Type of event
            duration: Processing duration in seconds
            success: Whether processing was successful
        """
        self.event_count.labels(
            event_type=event_type,
            success=str(success)
        ).inc()
        
        self.event_processing_duration.labels(
            event_type=event_type
        ).observe(duration)
    
    def update_event_queue_size(self, queue_name: str, size: int) -> None:
        """
        Update event queue size.
        
        Args:
            queue_name: Name of the queue
            size: Current queue size
        """
        self.event_queue_size.labels(
            queue_name=queue_name
        ).set(size)
    
    def get_command_stats(self) -> Dict[str, Any]:
        """
        Get command statistics.
        
        Returns:
            Dictionary with command statistics
        """
        if isinstance(self.metrics_provider, InMemoryMetricsProvider):
            metrics = self.metrics_provider.get_metrics()
            
            command_count = metrics["counters"].get("cqrs_commands_total", {})
            command_duration = metrics["histograms"].get("cqrs_command_duration_seconds", {})
            
            return {
                "count": command_count,
                "duration": command_duration
            }
        
        return {}
    
    def get_query_stats(self) -> Dict[str, Any]:
        """
        Get query statistics.
        
        Returns:
            Dictionary with query statistics
        """
        if isinstance(self.metrics_provider, InMemoryMetricsProvider):
            metrics = self.metrics_provider.get_metrics()
            
            query_count = metrics["counters"].get("cqrs_queries_total", {})
            query_duration = metrics["histograms"].get("cqrs_query_duration_seconds", {})
            query_result_size = metrics["histograms"].get("cqrs_query_result_size", {})
            
            return {
                "count": query_count,
                "duration": query_duration,
                "result_size": query_result_size
            }
        
        return {}
    
    def get_event_stats(self) -> Dict[str, Any]:
        """
        Get event statistics.
        
        Returns:
            Dictionary with event statistics
        """
        if isinstance(self.metrics_provider, InMemoryMetricsProvider):
            metrics = self.metrics_provider.get_metrics()
            
            event_count = metrics["counters"].get("cqrs_events_total", {})
            event_duration = metrics["histograms"].get("cqrs_event_processing_seconds", {})
            event_queue_size = metrics["gauges"].get("cqrs_event_queue_size", {})
            
            return {
                "count": event_count,
                "duration": event_duration,
                "queue_size": event_queue_size
            }
        
        return {}


class TracingCommandBus(CommandBus):
    """
    Command bus that tracks execution metrics and provides tracing.
    
    This command bus wraps an existing command bus and:
    1. Records metrics for command execution
    2. Logs command execution details
    3. Supports distributed tracing (through an optional tracer)
    """
    
    def __init__(
        self, 
        delegate: CommandBus,
        metrics: CQRSMetrics,
        tracer = None  # Optional tracing provider (OpenTelemetry, etc.)
    ):
        """
        Initialize the tracing command bus.
        
        Args:
            delegate: Command bus to delegate to
            metrics: CQRS metrics collector
            tracer: Optional tracing provider
        """
        super().__init__()
        self.delegate = delegate
        self.metrics = metrics
        self.tracer = tracer
        
        # Copy handlers from delegate
        if hasattr(delegate, "_handlers"):
            self._handlers = delegate._handlers
    
    async def execute(self, command: Command) -> Result[Any]:
        """
        Execute a command with tracing.
        
        Args:
            command: Command to execute
            
        Returns:
            Result from command execution
        """
        command_type = command.__class__.__name__
        command_id = getattr(command, "command_id", None)
        
        # Record command start
        self.metrics.record_command_start(command_type)
        
        # Start tracing span if tracer available
        span = None
        if self.tracer:
            span = self.tracer.start_span(
                name=f"command.{command_type}",
                attributes={
                    "command.type": command_type,
                    "command.id": str(command_id) if command_id else "",
                }
            )
        
        # Log command start
        logger.debug(f"Executing command {command_type} with ID {command_id}")
        
        start_time = time.time()
        try:
            # Execute command
            result = await self.delegate.execute(command)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            success = result.is_success()
            self.metrics.record_command_execution(
                command_type=command_type,
                duration=duration,
                success=success
            )
            
            # Update span if available
            if span:
                span.set_attribute("command.success", success)
                span.set_attribute("command.duration", duration)
                
                if not success and result.error:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", result.error.message)
                    span.set_attribute("error.code", result.error.code)
            
            # Log command completion
            if success:
                logger.debug(
                    f"Command {command_type} with ID {command_id} completed successfully "
                    f"in {duration:.3f}s"
                )
            else:
                logger.warning(
                    f"Command {command_type} with ID {command_id} failed in {duration:.3f}s: "
                    f"{result.error.message if result.error else 'Unknown error'}"
                )
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics for exception
            self.metrics.record_command_execution(
                command_type=command_type,
                duration=duration,
                success=False
            )
            
            # Update span if available
            if span:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
            
            # Log exception
            logger.exception(
                f"Exception executing command {command_type} with ID {command_id}: {str(e)}"
            )
            
            # Re-raise exception
            raise
            
        finally:
            # Record command end
            self.metrics.record_command_end(command_type)
            
            # End span if available
            if span:
                span.end()
    
    def register_handler(
        self, 
        command_type: Type[Command], 
        handler: CommandHandler
    ) -> None:
        """
        Register a command handler.
        
        Args:
            command_type: Type of command
            handler: Command handler
        """
        # Register with delegate
        self.delegate.register_handler(command_type, handler)
        
        # Update local handler registry
        if not hasattr(self, "_handlers"):
            self._handlers = {}
        self._handlers[command_type] = handler


class TracingQueryBus(QueryBus):
    """
    Query bus that tracks execution metrics and provides tracing.
    
    This query bus wraps an existing query bus and:
    1. Records metrics for query execution
    2. Logs query execution details
    3. Supports distributed tracing (through an optional tracer)
    """
    
    def __init__(
        self, 
        delegate: QueryBus,
        metrics: CQRSMetrics,
        tracer = None  # Optional tracing provider (OpenTelemetry, etc.)
    ):
        """
        Initialize the tracing query bus.
        
        Args:
            delegate: Query bus to delegate to
            metrics: CQRS metrics collector
            tracer: Optional tracing provider
        """
        super().__init__()
        self.delegate = delegate
        self.metrics = metrics
        self.tracer = tracer
        
        # Copy handlers from delegate
        if hasattr(delegate, "_handlers"):
            self._handlers = delegate._handlers
    
    async def execute(self, query: Query) -> Result[Any]:
        """
        Execute a query with tracing.
        
        Args:
            query: Query to execute
            
        Returns:
            Result from query execution
        """
        query_type = query.__class__.__name__
        query_id = getattr(query, "query_id", None)
        
        # Record query start
        self.metrics.record_query_start(query_type)
        
        # Start tracing span if tracer available
        span = None
        if self.tracer:
            span = self.tracer.start_span(
                name=f"query.{query_type}",
                attributes={
                    "query.type": query_type,
                    "query.id": str(query_id) if query_id else "",
                }
            )
        
        # Log query start
        logger.debug(f"Executing query {query_type} with ID {query_id}")
        
        start_time = time.time()
        try:
            # Execute query
            result = await self.delegate.execute(query)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Determine if result was cached (simplified detection)
            # In a real system, this would be communicated by the handler
            was_cached = hasattr(result, "from_cache") and result.from_cache
            
            # Determine result size (if applicable)
            result_size = 0
            if result.is_success():
                if isinstance(result.value, list):
                    result_size = len(result.value)
                elif hasattr(result.value, "items") and isinstance(result.value.items, list):
                    result_size = len(result.value.items)
            
            # Record metrics
            success = result.is_success()
            self.metrics.record_query_execution(
                query_type=query_type,
                duration=duration,
                success=success,
                cached=was_cached,
                result_size=result_size
            )
            
            # Update span if available
            if span:
                span.set_attribute("query.success", success)
                span.set_attribute("query.duration", duration)
                span.set_attribute("query.cached", was_cached)
                span.set_attribute("query.result_size", result_size)
                
                if not success and result.error:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", result.error.message)
                    span.set_attribute("error.code", result.error.code)
            
            # Log query completion
            if success:
                logger.debug(
                    f"Query {query_type} with ID {query_id} completed successfully "
                    f"in {duration:.3f}s (cached: {was_cached}, result size: {result_size})"
                )
            else:
                logger.warning(
                    f"Query {query_type} with ID {query_id} failed in {duration:.3f}s: "
                    f"{result.error.message if result.error else 'Unknown error'}"
                )
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics for exception
            self.metrics.record_query_execution(
                query_type=query_type,
                duration=duration,
                success=False,
                cached=False,
                result_size=0
            )
            
            # Update span if available
            if span:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
            
            # Log exception
            logger.exception(
                f"Exception executing query {query_type} with ID {query_id}: {str(e)}"
            )
            
            # Re-raise exception
            raise
            
        finally:
            # Record query end
            self.metrics.record_query_end(query_type)
            
            # End span if available
            if span:
                span.end()
    
    def register_handler(
        self, 
        query_type: Type[Query], 
        handler: QueryHandler
    ) -> None:
        """
        Register a query handler.
        
        Args:
            query_type: Type of query
            handler: Query handler
        """
        # Register with delegate
        self.delegate.register_handler(query_type, handler)
        
        # Update local handler registry
        if not hasattr(self, "_handlers"):
            self._handlers = {}
        self._handlers[query_type] = handler


class TracingMediator(Mediator):
    """
    Mediator that provides tracing and metrics for CQRS operations.
    
    This mediator wraps the command and query buses with tracing versions.
    """
    
    def __init__(
        self, 
        command_bus: Optional[CommandBus] = None,
        query_bus: Optional[QueryBus] = None,
        metrics: Optional[CQRSMetrics] = None,
        tracer = None
    ):
        """
        Initialize the tracing mediator.
        
        Args:
            command_bus: Optional command bus (creates default if None)
            query_bus: Optional query bus (creates default if None)
            metrics: Optional CQRS metrics collector (creates default if None)
            tracer: Optional tracing provider
        """
        # Create default components if not provided
        if metrics is None:
            metrics = CQRSMetrics(InMemoryMetricsProvider())
        
        # Create command bus if not provided
        if command_bus is None:
            command_bus = CommandBus()
        
        # Create query bus if not provided
        if query_bus is None:
            query_bus = QueryBus()
        
        # Wrap buses with tracing versions
        traced_command_bus = TracingCommandBus(command_bus, metrics, tracer)
        traced_query_bus = TracingQueryBus(query_bus, metrics, tracer)
        
        # Initialize base mediator
        super().__init__(traced_command_bus, traced_query_bus)
        
        # Store additional fields
        self.metrics = metrics
        self.tracer = tracer


class HealthStatus:
    """
    Health status for a CQRS component.
    
    This class represents the health status of a CQRS component,
    including its current state and any relevant details.
    """
    
    def __init__(
        self, 
        component: str,
        status: str,  # "healthy", "unhealthy", "degraded"
        details: Dict[str, Any] = None
    ):
        """
        Initialize the health status.
        
        Args:
            component: Component name
            status: Component status ("healthy", "unhealthy", "degraded")
            details: Optional status details
        """
        self.component = component
        self.status = status
        self.details = details or {}
        self.timestamp = datetime.now(UTC)
    
    def is_healthy(self) -> bool:
        """
        Check if the component is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return self.status == "healthy"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "component": self.component,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class HealthCheck:
    """
    Base class for health checks.
    
    Health checks monitor the health of CQRS components and report
    their status for monitoring and alerting.
    """
    
    async def check_health(self) -> HealthStatus:
        """
        Check the health of a component.
        
        Returns:
            Health status
        """
        raise NotImplementedError()


class CommandBusHealthCheck(HealthCheck):
    """
    Health check for command bus.
    
    This health check monitors the command bus by executing a simple
    test command and measuring its performance.
    """
    
    def __init__(self, command_bus: CommandBus):
        """
        Initialize the command bus health check.
        
        Args:
            command_bus: Command bus to check
        """
        self.command_bus = command_bus
    
    async def check_health(self) -> HealthStatus:
        """
        Check command bus health.
        
        Returns:
            Health status
        """
        try:
            # Create a simple ping command
            from uno.core.cqrs import Command
            
            class PingCommand(Command[str]):
                """Ping command for health check."""
                pass
            
            # Measure execution time
            start_time = time.time()
            
            # Execute the command (will fail if no handler registered)
            # In a real implementation, you would register a handler for this command
            try:
                _ = await self.command_bus.execute(PingCommand())
                has_handler = True
            except Exception:
                has_handler = False
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Create health status
            return HealthStatus(
                component="command_bus",
                status="healthy",
                details={
                    "latency_ms": round(duration * 1000, 2),
                    "has_handler": has_handler,
                    "handler_count": len(getattr(self.command_bus, "_handlers", {}))
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="command_bus",
                status="unhealthy",
                details={"error": str(e)}
            )


class QueryBusHealthCheck(HealthCheck):
    """
    Health check for query bus.
    
    This health check monitors the query bus by executing a simple
    test query and measuring its performance.
    """
    
    def __init__(self, query_bus: QueryBus):
        """
        Initialize the query bus health check.
        
        Args:
            query_bus: Query bus to check
        """
        self.query_bus = query_bus
    
    async def check_health(self) -> HealthStatus:
        """
        Check query bus health.
        
        Returns:
            Health status
        """
        try:
            # Create a simple ping query
            from uno.core.cqrs import Query
            
            class PingQuery(Query[str]):
                """Ping query for health check."""
                pass
            
            # Measure execution time
            start_time = time.time()
            
            # Execute the query (will fail if no handler registered)
            # In a real implementation, you would register a handler for this query
            try:
                _ = await self.query_bus.execute(PingQuery())
                has_handler = True
            except Exception:
                has_handler = False
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Create health status
            return HealthStatus(
                component="query_bus",
                status="healthy",
                details={
                    "latency_ms": round(duration * 1000, 2),
                    "has_handler": has_handler,
                    "handler_count": len(getattr(self.query_bus, "_handlers", {}))
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="query_bus",
                status="unhealthy",
                details={"error": str(e)}
            )


class EventStoreHealthCheck(HealthCheck):
    """
    Health check for event store.
    
    This health check monitors the event store by checking its
    connectivity and performance.
    """
    
    def __init__(self, event_store: EventStore):
        """
        Initialize the event store health check.
        
        Args:
            event_store: Event store to check
        """
        self.event_store = event_store
    
    async def check_health(self) -> HealthStatus:
        """
        Check event store health.
        
        Returns:
            Health status
        """
        try:
            # Measure execution time
            start_time = time.time()
            
            # Check if event store is accessible
            # This will vary depending on the event store implementation
            # Here we just get events for a test aggregate
            try:
                _ = await self.event_store.get_events("health-check-aggregate", limit=1)
                is_accessible = True
            except Exception:
                is_accessible = False
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Create health status
            status = "healthy" if is_accessible else "unhealthy"
            
            return HealthStatus(
                component="event_store",
                status=status,
                details={
                    "latency_ms": round(duration * 1000, 2),
                    "is_accessible": is_accessible,
                    "implementation": self.event_store.__class__.__name__
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="event_store",
                status="unhealthy",
                details={"error": str(e)}
            )


class CQRSHealthMonitor:
    """
    Health monitor for CQRS components.
    
    This monitor performs regular health checks on CQRS components
    and maintains their health status for reporting and alerting.
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize the health monitor.
        
        Args:
            check_interval_seconds: Interval between health checks in seconds
        """
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_status: Dict[str, HealthStatus] = {}
        self.check_interval_seconds = check_interval_seconds
        self.monitor_task = None
        self.status_change_callbacks: List[Callable[[str, HealthStatus, HealthStatus], Awaitable[None]]] = []
    
    def register_health_check(self, name: str, check: HealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            name: Health check name
            check: Health check implementation
        """
        self.health_checks[name] = check
    
    def register_status_change_callback(
        self, 
        callback: Callable[[str, HealthStatus, HealthStatus], Awaitable[None]]
    ) -> None:
        """
        Register a callback for health status changes.
        
        Args:
            callback: Callback function
        """
        self.status_change_callbacks.append(callback)
    
    async def start_monitoring(self) -> None:
        """Start health monitoring."""
        if self.monitor_task is not None:
            return
        
        # Create monitoring task
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        if self.monitor_task is None:
            return
        
        # Cancel monitoring task
        self.monitor_task.cancel()
        
        try:
            await self.monitor_task
        except asyncio.CancelledError:
            pass
        
        self.monitor_task = None
    
    async def check_health(self, name: Optional[str] = None) -> Dict[str, HealthStatus]:
        """
        Check health of components.
        
        Args:
            name: Optional component name to check
            
        Returns:
            Dictionary of health statuses
        """
        if name is not None:
            # Check a specific component
            if name not in self.health_checks:
                raise ValueError(f"No health check registered for {name}")
            
            status = await self.health_checks[name].check_health()
            self._update_health_status(name, status)
            
            return {name: status}
        else:
            # Check all components
            results = {}
            
            for check_name, check in self.health_checks.items():
                try:
                    status = await check.check_health()
                    self._update_health_status(check_name, status)
                    results[check_name] = status
                except Exception as e:
                    logger.exception(f"Error checking health for {check_name}: {e}")
                    
                    # Create unhealthy status for exception
                    status = HealthStatus(
                        component=check_name,
                        status="unhealthy",
                        details={"error": str(e)}
                    )
                    
                    self._update_health_status(check_name, status)
                    results[check_name] = status
            
            return results
    
    def get_health_status(self, name: Optional[str] = None) -> Union[Dict[str, HealthStatus], HealthStatus, None]:
        """
        Get current health status.
        
        Args:
            name: Optional component name to get status for
            
        Returns:
            Dictionary of health statuses, single health status, or None if not found
        """
        if name is not None:
            return self.health_status.get(name)
        else:
            return self.health_status
    
    def is_healthy(self, name: Optional[str] = None) -> bool:
        """
        Check if component(s) are healthy.
        
        Args:
            name: Optional component name to check
            
        Returns:
            True if healthy, False otherwise
        """
        if name is not None:
            # Check a specific component
            status = self.health_status.get(name)
            return status is not None and status.is_healthy()
        else:
            # Check all components
            return all(
                status.is_healthy() 
                for status in self.health_status.values()
            )
    
    def get_overall_status(self) -> Dict[str, Any]:
        """
        Get overall health status.
        
        Returns:
            Dictionary with overall health status
        """
        components = {
            name: status.to_dict()
            for name, status in self.health_status.items()
        }
        
        overall_healthy = self.is_healthy()
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "components": components
        }
    
    async def _monitoring_loop(self) -> None:
        """Monitoring loop for periodic health checks."""
        while True:
            try:
                # Check health of all components
                await self.check_health()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in health monitoring loop: {e}")
                
                # Wait before retrying
                await asyncio.sleep(5)
    
    def _update_health_status(self, name: str, status: HealthStatus) -> None:
        """
        Update health status for a component.
        
        Args:
            name: Component name
            status: New health status
        """
        # Get previous status
        previous_status = self.health_status.get(name)
        
        # Update status
        self.health_status[name] = status
        
        # Check for status change
        if (previous_status is None or 
            previous_status.status != status.status):
            
            # Log status change
            if previous_status is None:
                logger.info(f"Health status for {name}: {status.status}")
            else:
                logger.info(
                    f"Health status for {name} changed from "
                    f"{previous_status.status} to {status.status}"
                )
            
            # Notify status change callbacks
            for callback in self.status_change_callbacks:
                try:
                    asyncio.create_task(
                        callback(name, previous_status, status)
                    )
                except Exception as e:
                    logger.error(
                        f"Error in status change callback for {name}: {e}"
                    )


def get_tracing_mediator(metrics_provider: Optional[MetricsProvider] = None) -> TracingMediator:
    """
    Get a tracing mediator instance.
    
    This function creates or returns a tracing mediator instance with metrics
    collection and tracing capabilities.
    
    Args:
        metrics_provider: Optional metrics provider implementation
        
    Returns:
        TracingMediator instance
    """
    # Create metrics provider if not provided
    if metrics_provider is None:
        metrics_provider = InMemoryMetricsProvider()
    
    # Create metrics collector
    metrics = CQRSMetrics(metrics_provider)
    
    # Get base mediator
    base_mediator = get_mediator()
    
    # Create tracing mediator
    tracing_mediator = TracingMediator(
        command_bus=base_mediator.command_bus,
        query_bus=base_mediator.query_bus,
        metrics=metrics
    )
    
    return tracing_mediator