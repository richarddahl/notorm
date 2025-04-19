# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Metrics collection and export for the Uno application.

This module provides utilities for collecting and exporting application metrics,
including counters, gauges, histograms, and timers with integration with the
logging and error frameworks.
"""

import asyncio
import functools
import inspect
import json
import logging
import statistics
import time
import contextvars
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Union, Set, Awaitable, cast

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

from uno.core.errors.framework import ErrorContext, get_error_context, error_to_dict
from uno.core.logging.framework import get_logger, LogContext, add_context, get_context, clear_context
from uno.dependencies.interfaces import ConfigProtocol

# Type variables
T = TypeVar('T')
N = TypeVar('N', int, float)
F = TypeVar('F', bound=Callable[..., Any])

# Context variable for metrics context
_metrics_context = contextvars.ContextVar[Dict[str, Any]]("metrics_context", default={})


class MetricType(str, Enum):
    """Type of metric."""
    
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricUnit(str, Enum):
    """Unit of measurement for metrics."""
    
    NONE = "none"
    BYTES = "bytes"
    MILLISECONDS = "ms"
    SECONDS = "s"
    COUNT = "count"
    PERCENT = "percent"
    OPERATIONS = "ops"
    ERRORS = "errors"
    
    @classmethod
    def from_string(cls, unit_str: str) -> "MetricUnit":
        """Convert string to MetricUnit."""
        try:
            return cls[unit_str.upper()]
        except KeyError:
            valid_units = ", ".join([u.name for u in cls])
            raise ValueError(f"Invalid metric unit: {unit_str}. Valid units are: {valid_units}")


@dataclass
class MetricValue:
    """Value of a metric with metadata."""
    
    name: str
    value: Union[int, float, List[float]]
    type: MetricType
    unit: MetricUnit = MetricUnit.NONE
    tags: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    timestamp: float = field(default_factory=lambda: time.time())
    
    def with_tags(self, **tags: str) -> 'MetricValue':
        """Add tags to the metric value."""
        combined_tags = {**self.tags, **tags}
        return MetricValue(
            name=self.name,
            value=self.value,
            type=self.type,
            unit=self.unit,
            tags=combined_tags,
            description=self.description,
            timestamp=self.timestamp
        )


@dataclass
class MetricsContext:
    """
    Context information for metrics collection.
    
    This class collects additional information about the context in which metrics
    are collected, which can be helpful for filtering and analysis.
    """
    
    trace_id: Optional[str] = None
    service_name: Optional[str] = None
    environment: Optional[str] = None
    component: Optional[str] = None
    instance_id: Optional[str] = None
    region: Optional[str] = None
    zone: Optional[str] = None
    additional_tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a dictionary."""
        result = {}
        
        # Add fields that are not None
        for key, value in self.__dict__.items():
            if value is not None and key != "additional_tags":
                result[key] = value
        
        # Add additional tags
        result.update(self.additional_tags)
        
        return result
    
    def merge(self, other: Union["MetricsContext", Dict[str, Any]]) -> "MetricsContext":
        """
        Merge with another context.
        
        Args:
            other: Another MetricsContext or dictionary
            
        Returns:
            New MetricsContext with merged properties
        """
        if isinstance(other, dict):
            other_dict = other
        else:
            other_dict = other.to_dict()
        
        this_dict = self.to_dict()
        merged = {**this_dict, **other_dict}
        
        # Create a new instance with the merged data
        result = MetricsContext()
        
        # Set direct properties
        for key in ["trace_id", "service_name", "environment", "component", 
                    "instance_id", "region", "zone"]:
            if key in merged:
                setattr(result, key, merged.pop(key))
        
        # Set remaining keys as additional tags
        result.additional_tags = merged
        
        return result


@dataclass
class MetricsConfig:
    """
    Configuration for metrics collection.
    
    This class provides a structured way to configure metrics collection
    with sensible defaults.
    """
    
    enabled: bool = True
    service_name: str = "uno"
    environment: str = "development"
    export_interval: float = 60.0  # seconds
    console_export: bool = True
    prometheus_export: bool = True
    prometheus_namespace: str = "uno"
    include_trace_id: bool = True
    default_tags: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_config(cls, config: ConfigProtocol) -> "MetricsConfig":
        """
        Create MetricsConfig from ConfigProtocol.
        
        Args:
            config: Configuration provider
            
        Returns:
            MetricsConfig instance
        """
        # Get default tags from config
        default_tags_str = config.get("metrics.default_tags", "{}")
        try:
            default_tags = json.loads(default_tags_str) if isinstance(default_tags_str, str) else {}
        except json.JSONDecodeError:
            default_tags = {}
        
        return cls(
            enabled=config.get("metrics.enabled", True),
            service_name=config.get("service.name", "uno"),
            environment=config.get("environment", "development"),
            export_interval=config.get("metrics.export_interval", 60.0),
            console_export=config.get("metrics.console_export", True),
            prometheus_export=config.get("metrics.prometheus_export", True),
            prometheus_namespace=config.get("metrics.prometheus_namespace", "uno"),
            include_trace_id=config.get("metrics.include_trace_id", True),
            default_tags=default_tags,
        )


class Metric(ABC, Generic[T]):
    """Base class for all metrics."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a metric.
        
        Args:
            name: Name of the metric
            description: Description of the metric
            unit: Unit of measurement
            tags: Tags to attach to the metric
        """
        self.name = name
        self.description = description
        self.unit = unit
        self.tags = tags or {}
        self._type: MetricType
    
    @abstractmethod
    def get_value(self) -> MetricValue:
        """Get the current value of the metric."""
        pass


class Counter(Metric[int]):
    """
    Counter metric that can only increase.
    
    Counters are useful for tracking things like number of requests,
    errors, or operations performed.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.COUNT,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a counter.
        
        Args:
            name: Name of the counter
            description: Description of the counter
            unit: Unit of measurement
            tags: Tags to attach to the counter
        """
        super().__init__(name, description, unit, tags)
        self._type = MetricType.COUNTER
        self._value = 0
        self._lock = asyncio.Lock()
    
    async def increment(self, value: int = 1) -> None:
        """
        Increment the counter.
        
        Args:
            value: Amount to increment by (default 1)
        
        Raises:
            ValueError: If value is negative
        """
        if value < 0:
            raise ValueError("Cannot decrement a counter. Use gauge instead.")
        
        async with self._lock:
            self._value += value
    
    def get_value(self) -> MetricValue:
        """Get the current value of the counter."""
        return MetricValue(
            name=self.name,
            value=self._value,
            type=self._type,
            unit=self.unit,
            tags=self.tags,
            description=self.description
        )


class Gauge(Metric[float]):
    """
    Gauge metric that can increase or decrease.
    
    Gauges are useful for tracking things like current connections,
    memory usage, or queue size.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a gauge.
        
        Args:
            name: Name of the gauge
            description: Description of the gauge
            unit: Unit of measurement
            tags: Tags to attach to the gauge
        """
        super().__init__(name, description, unit, tags)
        self._type = MetricType.GAUGE
        self._value = 0.0
        self._lock = asyncio.Lock()
    
    async def set(self, value: float) -> None:
        """
        Set the gauge to a specific value.
        
        Args:
            value: Value to set
        """
        async with self._lock:
            self._value = value
    
    async def increment(self, value: float = 1.0) -> None:
        """
        Increment the gauge.
        
        Args:
            value: Amount to increment by (default 1.0)
        """
        async with self._lock:
            self._value += value
    
    async def decrement(self, value: float = 1.0) -> None:
        """
        Decrement the gauge.
        
        Args:
            value: Amount to decrement by (default 1.0)
        """
        async with self._lock:
            self._value -= value
    
    async def set_to_current_time(self) -> None:
        """Set the gauge to the current timestamp."""
        await self.set(time.time())
    
    async def track_inprogress(self) -> 'MetricsContext':
        """
        Track in-progress operations with the gauge.
        
        Returns:
            A context manager that increments the gauge on entry and
            decrements it on exit.
        """
        return GaugeTracker(self)
    
    def get_value(self) -> MetricValue:
        """Get the current value of the gauge."""
        return MetricValue(
            name=self.name,
            value=self._value,
            type=self._type,
            unit=self.unit,
            tags=self.tags,
            description=self.description
        )


class GaugeTracker:
    """Context manager for tracking in-progress operations with a gauge."""
    
    def __init__(self, gauge: Gauge):
        """
        Initialize a gauge tracker.
        
        Args:
            gauge: The gauge to track with
        """
        self.gauge = gauge
    
    async def __aenter__(self) -> 'GaugeTracker':
        """Increment the gauge on entry."""
        await self.gauge.increment()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Decrement the gauge on exit."""
        await self.gauge.decrement()


class Histogram(Metric[List[float]]):
    """
    Histogram metric for tracking distributions.
    
    Histograms are useful for tracking things like request duration,
    response size, or other values that you want to analyze statistically.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[Dict[str, str]] = None,
        max_size: int = 1000,
    ):
        """
        Initialize a histogram.
        
        Args:
            name: Name of the histogram
            description: Description of the histogram
            unit: Unit of measurement
            tags: Tags to attach to the histogram
            max_size: Maximum number of values to track
        """
        super().__init__(name, description, unit, tags)
        self._type = MetricType.HISTOGRAM
        self._values: List[float] = []
        self._lock = asyncio.Lock()
        self._max_size = max_size
    
    async def observe(self, value: float) -> None:
        """
        Record a value in the histogram.
        
        Args:
            value: Value to record
        """
        async with self._lock:
            self._values.append(value)
            # Trim if necessary
            if len(self._values) > self._max_size:
                self._values = self._values[-self._max_size:]
    
    def get_value(self) -> MetricValue:
        """Get the current values in the histogram."""
        return MetricValue(
            name=self.name,
            value=self._values.copy(),
            type=self._type,
            unit=self.unit,
            tags=self.tags,
            description=self.description
        )
    
    async def get_statistics(self) -> Dict[str, float]:
        """
        Get statistical measures from the histogram.
        
        Returns:
            Dictionary of statistical measures
        """
        async with self._lock:
            if not self._values:
                return {
                    "count": 0,
                    "min": 0.0,
                    "max": 0.0,
                    "mean": 0.0,
                    "median": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                }
            
            values = sorted(self._values)
            count = len(values)
            
            return {
                "count": count,
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p95": values[int(count * 0.95) - 1] if count >= 20 else values[-1],
                "p99": values[int(count * 0.99) - 1] if count >= 100 else values[-1],
            }


class Timer(Metric[float]):
    """
    Timer metric for measuring duration.
    
    Timers are useful for tracking how long operations take.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.MILLISECONDS,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a timer.
        
        Args:
            name: Name of the timer
            description: Description of the timer
            unit: Unit of measurement
            tags: Tags to attach to the timer
        """
        super().__init__(name, description, unit, tags)
        self._type = MetricType.TIMER
        self._histogram = Histogram(
            name=name,
            description=description,
            unit=unit,
            tags=tags
        )
    
    @contextmanager
    def time(self) -> None:
        """
        Measure the execution time of a code block.
        
        Example:
            with timer.time():
                # Code to measure
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to ms
            asyncio.create_task(self._histogram.observe(duration))
    
    async def record(self, duration: float) -> None:
        """
        Record a duration directly.
        
        Args:
            duration: Duration in milliseconds
        """
        await self._histogram.observe(duration)
    
    def get_value(self) -> MetricValue:
        """Get the current value of the timer."""
        # For timers, the value is the mean of recorded durations
        histogram_value = self._histogram.get_value()
        values = histogram_value.value
        
        if not values:
            mean = 0.0
        else:
            mean = statistics.mean(values)
        
        return MetricValue(
            name=self.name,
            value=mean,
            type=self._type,
            unit=self.unit,
            tags=self.tags,
            description=self.description
        )
    
    async def get_statistics(self) -> Dict[str, float]:
        """
        Get statistical measures from the timer.
        
        Returns:
            Dictionary of statistical measures
        """
        return await self._histogram.get_statistics()


class TimerContext:
    """
    Async context manager for timing code blocks.
    
    Example:
        async with TimerContext(timer):
            # Async code to measure
    """
    
    def __init__(self, timer: Timer):
        """
        Initialize a timer context.
        
        Args:
            timer: The timer to use
        """
        self.timer = timer
        self.start_time = 0.0
    
    async def __aenter__(self) -> 'TimerContext':
        """Record the start time."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Calculate duration and record it."""
        duration = (time.time() - self.start_time) * 1000  # Convert to ms
        await self.timer.record(duration)


def timed(
    timer_name: str,
    description: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    registry: Optional['MetricsRegistry'] = None,
) -> Callable[[F], F]:
    """
    Decorator for timing functions.
    
    This decorator can be used to measure the execution time of both
    synchronous and asynchronous functions.
    
    Args:
        timer_name: Name of the timer
        description: Description of the timer
        tags: Tags to attach to the timer
        registry: Metrics registry to use
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get or create timer
            nonlocal registry
            if registry is None:
                registry = get_metrics_registry()
            
            # Include logging context in tags if available
            log_context = get_context()
            merged_tags = {**log_context, **(tags or {})}
            
            timer = await registry.get_or_create_timer(
                name=timer_name,
                description=description,
                tags=merged_tags
            )
            
            # Time the function
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = (time.time() - start_time) * 1000  # Convert to ms
                await timer.record(duration)
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get or create timer
            nonlocal registry
            if registry is None:
                registry = get_metrics_registry()
            
            # Include logging context in tags if available
            log_context = get_context()
            merged_tags = {**log_context, **(tags or {})}
            
            # We need to run this in an event loop
            timer = asyncio.run(registry.get_or_create_timer(
                name=timer_name,
                description=description,
                tags=merged_tags
            ))
            
            # Time the function
            with timer.time():
                return func(*args, **kwargs)
        
        # Choose the right wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
    
    return decorator


def with_metrics_context(func: Optional[F] = None, **context: Any) -> Union[F, Callable[[F], F]]:
    """
    Decorator that adds context to metrics.
    
    This can be used in two ways:
    1. @with_metrics_context: Adds function parameters to metrics context
    2. @with_metrics_context(param1="value"): Adds specified context to metrics
    
    Args:
        func: The function to decorate
        **context: Context key-value pairs
        
    Returns:
        The decorated function
    """
    # Check if called as @with_metrics_context or @with_metrics_context(param="value")
    if func is None:
        # Called as @with_metrics_context(param="value")
        def decorator(f: F) -> F:
            @functools.wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Get the current context
                current_context = _metrics_context.get().copy()
                
                # Add static context provided in the decorator
                new_context = {**current_context, **context}
                
                # Set the new context
                token = _metrics_context.set(new_context)
                
                try:
                    return f(*args, **kwargs)
                finally:
                    # Restore the previous context
                    _metrics_context.reset(token)
            
            return cast(F, wrapper)
        
        return decorator
    
    # Called as @with_metrics_context
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get the signature of the function
        sig = inspect.signature(func)
        
        # Bind the arguments to the signature
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        # Get arguments as a dict, filtering out self/cls for methods
        arg_dict = {}
        for key, value in bound.arguments.items():
            # Skip 'self' and 'cls' parameters
            if key not in ("self", "cls"):
                # Avoid including large objects or sensitive data
                if isinstance(value, (str, int, float, bool)) or value is None:
                    arg_dict[key] = value
                else:
                    # Just include the type for complex objects
                    arg_dict[key] = f"<{type(value).__name__}>"
        
        # Get the current context
        current_context = _metrics_context.get().copy()
        
        # Create a new context with function info and parameters
        new_context = {
            **current_context,
            "function": func.__name__,
            "module": func.__module__,
            "args": arg_dict,
        }
        
        # Set the new context
        token = _metrics_context.set(new_context)
        
        try:
            return func(*args, **kwargs)
        finally:
            # Restore the previous context
            _metrics_context.reset(token)
    
    return cast(F, wrapper)


def add_metrics_context(**context: Any) -> None:
    """
    Add key-value pairs to the current metrics context.
    
    Args:
        **context: Key-value pairs to add to the context
    """
    current = _metrics_context.get().copy()
    current.update(context)
    _metrics_context.set(current)


def get_metrics_context() -> Dict[str, Any]:
    """
    Get the current metrics context.
    
    Returns:
        The current metrics context dictionary
    """
    return _metrics_context.get().copy()


def clear_metrics_context() -> None:
    """Clear the current metrics context."""
    _metrics_context.set({})


class MetricsExporter(ABC):
    """Base class for metrics exporters."""
    
    @abstractmethod
    async def export_metrics(self, metrics: List[MetricValue]) -> None:
        """
        Export metrics to the target system.
        
        Args:
            metrics: List of metrics to export
        """
        pass


class PrometheusExporter(MetricsExporter):
    """
    Exporter for Prometheus monitoring system.
    
    This exporter converts metrics to Prometheus format for scraping.
    """
    
    def __init__(self, namespace: str = "uno"):
        """
        Initialize the Prometheus exporter.
        
        Args:
            namespace: Namespace prefix for metrics
        """
        self.namespace = namespace
        self.logger = get_logger("uno.metrics.prometheus")
    
    async def export_metrics(self, metrics: List[MetricValue]) -> None:
        """
        Export metrics to Prometheus (no-op for scrape-based systems).
        
        Args:
            metrics: List of metrics to export
        """
        # Prometheus uses a pull model, so we don't need to push metrics
        pass
    
    def format_metrics(self, metrics: List[MetricValue]) -> str:
        """
        Format metrics in Prometheus format.
        
        Args:
            metrics: List of metrics to format
            
        Returns:
            Prometheus-formatted metrics
        """
        output = []
        
        # Group metrics by name and type
        grouped: Dict[str, Dict[str, List[MetricValue]]] = {}
        
        for metric in metrics:
            name = metric.name
            type_name = metric.type.value
            
            if name not in grouped:
                grouped[name] = {}
            
            if type_name not in grouped[name]:
                grouped[name][type_name] = []
            
            grouped[name][type_name].append(metric)
        
        # Format each metric
        for name, types in grouped.items():
            prometheus_name = f"{self.namespace}_{name}".replace(".", "_").replace("-", "_")
            
            for type_name, metrics_list in types.items():
                if metrics_list:
                    # Add TYPE comment
                    output.append(f"# TYPE {prometheus_name} {type_name}")
                    
                    # Add HELP comment if we have a description
                    if metrics_list[0].description:
                        output.append(f"# HELP {prometheus_name} {metrics_list[0].description}")
                    
                    # Add metrics
                    for metric in metrics_list:
                        # Format tags
                        tag_str = ""
                        if metric.tags:
                            tag_pairs = [f'{k}="{v}"' for k, v in metric.tags.items()]
                            tag_str = "{" + ",".join(tag_pairs) + "}"
                        
                        # Format value based on type
                        if metric.type == MetricType.HISTOGRAM:
                            # For histograms, we export count, sum, and buckets
                            values = metric.value
                            if values:
                                # Count
                                output.append(f"{prometheus_name}_count{tag_str} {len(values)}")
                                # Sum
                                output.append(f"{prometheus_name}_sum{tag_str} {sum(values)}")
                                # Buckets (simplified)
                                if len(values) >= 100:
                                    sorted_values = sorted(values)
                                    p50 = sorted_values[len(sorted_values) // 2]
                                    p95 = sorted_values[int(len(sorted_values) * 0.95)]
                                    p99 = sorted_values[int(len(sorted_values) * 0.99)]
                                    
                                    output.append(f"{prometheus_name}_bucket{{le=\"50\"{tag_str[1:-1]}}} {len([v for v in values if v <= p50])}")
                                    output.append(f"{prometheus_name}_bucket{{le=\"95\"{tag_str[1:-1]}}} {len([v for v in values if v <= p95])}")
                                    output.append(f"{prometheus_name}_bucket{{le=\"99\"{tag_str[1:-1]}}} {len([v for v in values if v <= p99])}")
                                    output.append(f"{prometheus_name}_bucket{{le=\"+Inf\"{tag_str[1:-1]}}} {len(values)}")
                        else:
                            # Simple value
                            output.append(f"{prometheus_name}{tag_str} {metric.value}")
        
        return "\n".join(output)


class LoggingExporter(MetricsExporter):
    """
    Exporter that logs metrics.
    
    This exporter logs metrics at regular intervals for debugging.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the logging exporter.
        
        Args:
            logger: Logger to use
        """
        self.logger = logger or get_logger("uno.metrics")
    
    async def export_metrics(self, metrics: List[MetricValue]) -> None:
        """
        Export metrics by logging them.
        
        Args:
            metrics: List of metrics to export
        """
        # Group metrics by name
        grouped: Dict[str, Dict[str, Any]] = {}
        
        for metric in metrics:
            name = metric.name
            
            if name not in grouped:
                grouped[name] = {
                    "type": metric.type.value,
                    "unit": metric.unit.value,
                    "values": []
                }
            
            # Add value with tags
            grouped[name]["values"].append({
                "value": metric.value if not isinstance(metric.value, list) else f"[{len(metric.value)} values]",
                "tags": metric.tags
            })
        
        # Log each group
        for name, info in grouped.items():
            self.logger.info(
                f"Metric: {name} ({info['type']}, {info['unit']})",
                extra={"metrics": info}
            )


class MetricsRegistry:
    """
    Registry for application metrics.
    
    This class manages all metrics and handles exporting them.
    """
    
    def __init__(
        self,
        config: Optional[MetricsConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the metrics registry.
        
        Args:
            config: Metrics configuration
            logger: Logger to use
        """
        self.config = config or MetricsConfig()
        self.logger = logger or get_logger("uno.metrics")
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._timers: Dict[str, Timer] = {}
        self._exporters: List[MetricsExporter] = []
        self._lock = asyncio.Lock()
        self._export_task: Optional[asyncio.Task] = None
        self._export_interval = self.config.export_interval
        self._shutting_down = False
        
        # Set up default tags
        self._default_tags = {
            "service": self.config.service_name,
            "environment": self.config.environment,
            **self.config.default_tags
        }
    
    async def setup(
        self,
        exporters: Optional[List[MetricsExporter]] = None,
    ) -> None:
        """
        Set up the metrics registry.
        
        Args:
            exporters: List of exporters to use
        """
        if not self.config.enabled:
            self.logger.info("Metrics collection is disabled")
            return
        
        # Add default exporters if configured
        if self.config.console_export:
            self._exporters.append(LoggingExporter())
        
        if self.config.prometheus_export:
            self._exporters.append(PrometheusExporter(namespace=self.config.prometheus_namespace))
        
        # Add custom exporters
        if exporters:
            self._exporters.extend(exporters)
        
        # Start the export task if we have exporters
        if self._exporters and not self._export_task:
            self._export_task = asyncio.create_task(
                self._export_loop(),
                name="metrics_export"
            )
            
            self.logger.info(
                f"Metrics registry set up with {len(self._exporters)} exporters, "
                f"export interval: {self._export_interval}s"
            )
    
    async def shutdown(self) -> None:
        """
        Shut down the metrics registry.
        
        This stops the export task and performs a final export.
        """
        if not self.config.enabled:
            return
        
        self._shutting_down = True
        
        if self._export_task and not self._export_task.done():
            # Cancel the export task
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
            
            # Do a final export
            await self._export_metrics()
            
            self.logger.info("Metrics registry shut down")
    
    async def _export_loop(self) -> None:
        """Background task for exporting metrics at regular intervals."""
        try:
            while not self._shutting_down:
                # Wait for the export interval
                await asyncio.sleep(self._export_interval)
                
                # Export metrics
                await self._export_metrics()
        
        except asyncio.CancelledError:
            # Expected during shutdown
            pass
        
        except Exception as e:
            self.logger.error(
                f"Error in metrics export loop: {str(e)}",
                exc_info=True
            )
    
    async def _export_metrics(self) -> None:
        """Export all metrics to all exporters."""
        try:
            # Collect all metrics
            metrics = []
            
            async with self._lock:
                # Collect counters
                for counter in self._counters.values():
                    metrics.append(counter.get_value())
                
                # Collect gauges
                for gauge in self._gauges.values():
                    metrics.append(gauge.get_value())
                
                # Collect histograms
                for histogram in self._histograms.values():
                    metrics.append(histogram.get_value())
                
                # Collect timers
                for timer in self._timers.values():
                    metrics.append(timer.get_value())
            
            # Export metrics
            for exporter in self._exporters:
                try:
                    await exporter.export_metrics(metrics)
                except Exception as e:
                    self.logger.error(
                        f"Error exporting metrics to {exporter.__class__.__name__}: {str(e)}",
                        exc_info=True
                    )
        
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {str(e)}", exc_info=True)
    
    def _get_metric_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """
        Get a unique key for a metric based on name and tags.
        
        Args:
            name: Metric name
            tags: Metric tags
            
        Returns:
            Unique key
        """
        if not tags:
            return name
        
        # Sort tags by key for consistent keys
        tag_str = "".join(f"{k}:{tags[k]}" for k in sorted(tags.keys()))
        return f"{name}:{tag_str}"
    
    def _merge_tags(self, tags: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Merge default tags with provided tags.
        
        Args:
            tags: Tags to merge with defaults
            
        Returns:
            Merged tags
        """
        if not tags:
            return self._default_tags.copy()
        
        return {**self._default_tags, **tags}
    
    async def get_or_create_counter(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.COUNT,
        tags: Optional[Dict[str, str]] = None,
    ) -> Counter:
        """
        Get or create a counter.
        
        Args:
            name: Name of the counter
            description: Description of the counter
            unit: Unit of measurement
            tags: Tags to attach to the counter
            
        Returns:
            The counter
        """
        if not self.config.enabled:
            # Return a dummy counter if metrics are disabled
            return Counter(name=name, description=description, unit=unit, tags=tags)
        
        # Merge with default tags
        merged_tags = self._merge_tags(tags)
        
        # Generate a unique key
        key = self._get_metric_key(name, merged_tags)
        
        async with self._lock:
            if key not in self._counters:
                self._counters[key] = Counter(
                    name=name,
                    description=description,
                    unit=unit,
                    tags=merged_tags
                )
            
            return self._counters[key]
    
    async def get_or_create_gauge(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[Dict[str, str]] = None,
    ) -> Gauge:
        """
        Get or create a gauge.
        
        Args:
            name: Name of the gauge
            description: Description of the gauge
            unit: Unit of measurement
            tags: Tags to attach to the gauge
            
        Returns:
            The gauge
        """
        if not self.config.enabled:
            # Return a dummy gauge if metrics are disabled
            return Gauge(name=name, description=description, unit=unit, tags=tags)
        
        # Merge with default tags
        merged_tags = self._merge_tags(tags)
        
        # Generate a unique key
        key = self._get_metric_key(name, merged_tags)
        
        async with self._lock:
            if key not in self._gauges:
                self._gauges[key] = Gauge(
                    name=name,
                    description=description,
                    unit=unit,
                    tags=merged_tags
                )
            
            return self._gauges[key]
    
    async def get_or_create_histogram(
        self,
        name: str,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[Dict[str, str]] = None,
    ) -> Histogram:
        """
        Get or create a histogram.
        
        Args:
            name: Name of the histogram
            description: Description of the histogram
            unit: Unit of measurement
            tags: Tags to attach to the histogram
            
        Returns:
            The histogram
        """
        if not self.config.enabled:
            # Return a dummy histogram if metrics are disabled
            return Histogram(name=name, description=description, unit=unit, tags=tags)
        
        # Merge with default tags
        merged_tags = self._merge_tags(tags)
        
        # Generate a unique key
        key = self._get_metric_key(name, merged_tags)
        
        async with self._lock:
            if key not in self._histograms:
                self._histograms[key] = Histogram(
                    name=name,
                    description=description,
                    unit=unit,
                    tags=merged_tags
                )
            
            return self._histograms[key]
    
    async def get_or_create_timer(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Timer:
        """
        Get or create a timer.
        
        Args:
            name: Name of the timer
            description: Description of the timer
            tags: Tags to attach to the timer
            
        Returns:
            The timer
        """
        if not self.config.enabled:
            # Return a dummy timer if metrics are disabled
            return Timer(name=name, description=description, tags=tags)
        
        # Merge with default tags
        merged_tags = self._merge_tags(tags)
        
        # Generate a unique key
        key = self._get_metric_key(name, merged_tags)
        
        async with self._lock:
            if key not in self._timers:
                self._timers[key] = Timer(
                    name=name,
                    description=description,
                    tags=merged_tags
                )
            
            return self._timers[key]
    
    async def get_all_metrics(self) -> List[MetricValue]:
        """
        Get all metrics.
        
        Returns:
            List of all metric values
        """
        if not self.config.enabled:
            return []
        
        metrics = []
        
        async with self._lock:
            # Collect counters
            for counter in self._counters.values():
                metrics.append(counter.get_value())
            
            # Collect gauges
            for gauge in self._gauges.values():
                metrics.append(gauge.get_value())
            
            # Collect histograms
            for histogram in self._histograms.values():
                metrics.append(histogram.get_value())
            
            # Collect timers
            for timer in self._timers.values():
                metrics.append(timer.get_value())
        
        return metrics
    
    def get_prometheus_metrics(self) -> str:
        """
        Get all metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics
        """
        if not self.config.enabled:
            return "# Metrics collection is disabled"
        
        # Find Prometheus exporter
        prometheus_exporter = next(
            (e for e in self._exporters if isinstance(e, PrometheusExporter)),
            PrometheusExporter(namespace=self.config.prometheus_namespace)
        )
        
        # Get all metrics
        metrics = asyncio.run(self.get_all_metrics())
        
        # Format metrics
        return prometheus_exporter.format_metrics(metrics)


# Global metrics registry
_metrics_registry: Optional[MetricsRegistry] = None


def get_metrics_registry() -> MetricsRegistry:
    """
    Get the global metrics registry.
    
    Returns:
        The global metrics registry
    """
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = MetricsRegistry()
    return _metrics_registry


def configure_metrics(config: Optional[MetricsConfig] = None) -> MetricsRegistry:
    """
    Configure metrics collection.
    
    Args:
        config: Metrics configuration
        
    Returns:
        Configured metrics registry
    """
    global _metrics_registry
    
    # Create or update registry
    if _metrics_registry is None:
        _metrics_registry = MetricsRegistry(config)
    else:
        _metrics_registry.config = config or MetricsConfig()
    
    # Set up the registry
    asyncio.create_task(_metrics_registry.setup())
    
    return _metrics_registry


# Convenience functions for working with metrics
async def counter(
    name: str,
    description: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    registry: Optional[MetricsRegistry] = None,
) -> Counter:
    """
    Get or create a counter.
    
    Args:
        name: Name of the counter
        description: Description of the counter
        tags: Tags to attach to the counter
        registry: Metrics registry to use
        
    Returns:
        The counter
    """
    if registry is None:
        registry = get_metrics_registry()
    
    return await registry.get_or_create_counter(
        name=name,
        description=description,
        tags=tags
    )


async def gauge(
    name: str,
    description: Optional[str] = None,
    unit: MetricUnit = MetricUnit.NONE,
    tags: Optional[Dict[str, str]] = None,
    registry: Optional[MetricsRegistry] = None,
) -> Gauge:
    """
    Get or create a gauge.
    
    Args:
        name: Name of the gauge
        description: Description of the gauge
        unit: Unit of measurement
        tags: Tags to attach to the gauge
        registry: Metrics registry to use
        
    Returns:
        The gauge
    """
    if registry is None:
        registry = get_metrics_registry()
    
    return await registry.get_or_create_gauge(
        name=name,
        description=description,
        unit=unit,
        tags=tags
    )


async def histogram(
    name: str,
    description: Optional[str] = None,
    unit: MetricUnit = MetricUnit.NONE,
    tags: Optional[Dict[str, str]] = None,
    registry: Optional[MetricsRegistry] = None,
) -> Histogram:
    """
    Get or create a histogram.
    
    Args:
        name: Name of the histogram
        description: Description of the histogram
        unit: Unit of measurement
        tags: Tags to attach to the histogram
        registry: Metrics registry to use
        
    Returns:
        The histogram
    """
    if registry is None:
        registry = get_metrics_registry()
    
    return await registry.get_or_create_histogram(
        name=name,
        description=description,
        unit=unit,
        tags=tags
    )


async def timer(
    name: str,
    description: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    registry: Optional[MetricsRegistry] = None,
) -> Timer:
    """
    Get or create a timer.
    
    Args:
        name: Name of the timer
        description: Description of the timer
        tags: Tags to attach to the timer
        registry: Metrics registry to use
        
    Returns:
        The timer
    """
    if registry is None:
        registry = get_metrics_registry()
    
    return await registry.get_or_create_timer(
        name=name,
        description=description,
        tags=tags
    )


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting request metrics.
    
    This middleware collects HTTP request metrics such as request count,
    request duration, and response status codes. It integrates with both
    the logging and error frameworks.
    """
    
    def __init__(
        self,
        app: FastAPI,
        metrics_path: str = "/metrics",
        registry: Optional[MetricsRegistry] = None,
        excluded_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the metrics middleware.
        
        Args:
            app: FastAPI application
            metrics_path: Path for the metrics endpoint
            registry: Metrics registry to use
            excluded_paths: Paths to exclude from metrics collection
        """
        super().__init__(app)
        self.registry = registry or get_metrics_registry()
        self.metrics_path = metrics_path
        self.excluded_paths = excluded_paths or [metrics_path]
        self.logger = get_logger("uno.metrics.middleware")
        
        # Counters for request metrics
        self._setup_task = asyncio.create_task(self._setup_metrics())
        
        # Add metrics endpoint
        @app.get(metrics_path)
        async def metrics():
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=self.registry.get_prometheus_metrics(),
                media_type="text/plain"
            )
        
        self.logger.info(f"Metrics middleware initialized, endpoint: {metrics_path}")
    
    async def _setup_metrics(self) -> None:
        """Set up the metrics counters."""
        self.request_counter = await self.registry.get_or_create_counter(
            name="http.requests.total",
            description="Total number of HTTP requests",
            unit=MetricUnit.COUNT
        )
        
        self.request_duration = await self.registry.get_or_create_histogram(
            name="http.request.duration",
            description="HTTP request duration in milliseconds",
            unit=MetricUnit.MILLISECONDS
        )
        
        self.request_in_progress = await self.registry.get_or_create_gauge(
            name="http.requests.in_progress",
            description="Number of HTTP requests in progress",
            unit=MetricUnit.COUNT
        )
        
        self.response_size = await self.registry.get_or_create_histogram(
            name="http.response.size",
            description="HTTP response size in bytes",
            unit=MetricUnit.BYTES
        )
        
        self.error_counter = await self.registry.get_or_create_counter(
            name="http.errors.total",
            description="Total number of HTTP errors",
            unit=MetricUnit.COUNT
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request and collect metrics.
        
        Args:
            request: The HTTP request
            call_next: Function to call the next middleware/route handler
            
        Returns:
            HTTP response
        """
        # Skip metrics collection for excluded paths
        path = request.url.path
        if path in self.excluded_paths:
            return await call_next(request)
        
        # Add request tags
        method = request.method
        path_template = request.scope.get("path_params", {}).get("path", path)
        
        tags = {
            "method": method,
            "path": path_template
        }
        
        # Get trace ID from headers or generate one
        trace_id = request.headers.get("x-trace-id") or request.headers.get("x-request-id")
        if trace_id:
            tags["trace_id"] = trace_id
        
        # Track request count and in-progress
        await self.request_counter.increment()
        await self.request_in_progress.increment()
        
        # Track request duration
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add status code to tags
            status_code = response.status_code
            status_range = f"{status_code // 100}xx"
            tags.update({
                "status": str(status_code),
                "status_range": status_range
            })
            
            # Track error if 5xx
            if status_code >= 500:
                error_tags = {**tags, "error_type": "server_error"}
                await self.error_counter.increment()
            
            # Track response metrics
            response_size = int(response.headers.get("content-length", 0))
            if response_size > 0:
                await self.response_size.observe(response_size)
            
            return response
        
        except Exception as exc:
            # Track error
            error_tags = {
                **tags,
                "error_type": exc.__class__.__name__
            }
            await self.error_counter.increment()
            
            # Log the error
            self.logger.error(
                f"Error processing request {method} {path}: {str(exc)}",
                exc_info=exc
            )
            
            # Re-raise the exception
            raise
        
        finally:
            # Calculate request duration
            duration = (time.time() - start_time) * 1000  # Convert to ms
            
            # Record request duration
            await self.request_duration.observe(duration)
            
            # Decrement in-progress counter
            await self.request_in_progress.decrement()


class MetricsContext:
    """
    Context manager for tracking metrics in a block of code.
    
    Example:
        async with MetricsContext("operation", registry, tags={"component": "auth"}):
            # Code to measure
    """
    
    def __init__(
        self,
        operation: str,
        registry: Optional[MetricsRegistry] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a metrics context.
        
        Args:
            operation: Name of the operation to track
            registry: Metrics registry to use
            tags: Tags to attach to metrics
        """
        self.operation = operation
        self.registry = registry or get_metrics_registry()
        self.tags = tags or {}
        self.start_time = 0.0
        self.success = True
        self.error: Optional[str] = None
    
    async def __aenter__(self) -> 'MetricsContext':
        """Start tracking metrics."""
        # Record start time
        self.start_time = time.time()
        
        # Get trace ID from logging context if available
        log_context = get_context()
        if "trace_id" in log_context and "trace_id" not in self.tags:
            self.tags["trace_id"] = log_context["trace_id"]
        
        # Track in-progress operation
        operation_gauge = await self.registry.get_or_create_gauge(
            name=f"{self.operation}.in_progress",
            description=f"Number of {self.operation} operations in progress",
            tags=self.tags
        )
        await operation_gauge.increment()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """End tracking metrics."""
        # Calculate duration
        duration = (time.time() - self.start_time) * 1000  # Convert to ms
        
        # Update tags based on outcome
        if exc_type is not None:
            self.success = False
            self.error = exc_val.__class__.__name__
            self.tags["error"] = self.error
        
        outcome = "success" if self.success else "failure"
        self.tags["outcome"] = outcome
        
        # Track operation completion
        operation_counter = await self.registry.get_or_create_counter(
            name=f"{self.operation}.total",
            description=f"Total number of {self.operation} operations",
            tags=self.tags
        )
        await operation_counter.increment()
        
        # Track operation duration
        operation_timer = await self.registry.get_or_create_timer(
            name=f"{self.operation}.duration",
            description=f"Duration of {self.operation} operations in milliseconds",
            tags=self.tags
        )
        await operation_timer.record(duration)
        
        # Track in-progress operation
        operation_gauge = await self.registry.get_or_create_gauge(
            name=f"{self.operation}.in_progress",
            description=f"Number of {self.operation} operations in progress",
            tags={k: v for k, v in self.tags.items() if k not in ["outcome", "error"]}
        )
        await operation_gauge.decrement()