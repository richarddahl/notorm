# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Metrics collection and export for the Uno application.

This module provides utilities for collecting and exporting application metrics,
including counters, gauges, histograms, and timers.
"""

from typing import (
    Dict,
    List,
    Any,
    Optional,
    Callable,
    TypeVar,
    Generic,
    Union,
    Set,
    Awaitable,
)
import asyncio
import time
import logging
import functools
import json
import statistics
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.errors import get_error_context, with_error_context


# Type variables
T = TypeVar("T")
N = TypeVar("N", int, float)


class MetricType(Enum):
    """Type of metric."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricUnit(Enum):
    """Unit of measurement for metrics."""

    NONE = "none"
    BYTES = "bytes"
    MILLISECONDS = "ms"
    SECONDS = "s"
    COUNT = "count"
    PERCENT = "percent"


@dataclass
class MetricValue:
    """Value of a metric with metadata."""

    name: str
    value: Union[int, float, list[float]]
    type: MetricType
    unit: MetricUnit = MetricUnit.NONE
    tags: dict[str, str] = field(default_factory=dict)
    description: str | None = None
    timestamp: float = field(default_factory=time.time)

    def with_tags(self, **tags: str) -> "MetricValue":
        """Add tags to the metric value."""
        combined_tags = {**self.tags, **tags}
        return MetricValue(
            name=self.name,
            value=self.value,
            type=self.type,
            unit=self.unit,
            tags=combined_tags,
            description=self.description,
            timestamp=self.timestamp,
        )


class Metric(ABC, Generic[T]):
    """Base class for all metrics."""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[dict[str, str]] = None,
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
        description: str | None = None,
        unit: MetricUnit = MetricUnit.COUNT,
        tags: Optional[dict[str, str]] = None,
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
            raise ValueError("Cannot decrement a counter")

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
            description=self.description,
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
        description: str | None = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[dict[str, str]] = None,
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

    async def track_inprogress(self) -> "GaugeTracker":
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
            description=self.description,
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

    async def __aenter__(self) -> "GaugeTracker":
        """Increment the gauge on entry."""
        await self.gauge.increment()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Decrement the gauge on exit."""
        await self.gauge.decrement()


class Histogram(Metric[list[float]]):
    """
    Histogram metric for tracking distributions.

    Histograms are useful for tracking things like request duration,
    response size, or other values that you want to analyze statistically.
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[dict[str, str]] = None,
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
        self._values: list[float] = []
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
                self._values = self._values[-self._max_size :]

    def get_value(self) -> MetricValue:
        """Get the current values in the histogram."""
        return MetricValue(
            name=self.name,
            value=self._values.copy(),
            type=self._type,
            unit=self.unit,
            tags=self.tags,
            description=self.description,
        )

    async def get_statistics(self) -> dict[str, float]:
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
        description: str | None = None,
        unit: MetricUnit = MetricUnit.MILLISECONDS,
        tags: Optional[dict[str, str]] = None,
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
            name=name, description=description, unit=unit, tags=tags
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
            description=self.description,
        )

    async def get_statistics(self) -> dict[str, float]:
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

    async def __aenter__(self) -> "TimerContext":
        """Record the start time."""
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Calculate duration and record it."""
        duration = (time.time() - self.start_time) * 1000  # Convert to ms
        await self.timer.record(duration)


def timed(
    timer_name: str,
    description: str | None = None,
    tags: Optional[dict[str, str]] = None,
    registry: Optional["MetricsRegistry"] = None,
) -> Callable[[Callable], Callable]:
    """
    Decorator for timing functions.

    Args:
        timer_name: Name of the timer
        description: Description of the timer
        tags: Tags to attach to the timer
        registry: Metrics registry to use

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get or create timer
            nonlocal registry
            if registry is None:
                registry = get_metrics_registry()

            timer = await registry.get_or_create_timer(
                name=timer_name, description=description, tags=tags
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

            # We need to run this in an event loop
            timer = asyncio.run(
                registry.get_or_create_timer(
                    name=timer_name, description=description, tags=tags
                )
            )

            # Time the function
            with timer.time():
                return func(*args, **kwargs)

        # Choose the right wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class MetricsExporter(ABC):
    """Base class for metrics exporters."""

    @abstractmethod
    async def export_metrics(self, metrics: list[MetricValue]) -> None:
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

    def __init__(self, namespace: str = "app"):
        """
        Initialize the Prometheus exporter.

        Args:
            namespace: Namespace prefix for metrics
        """
        self.namespace = namespace

    async def export_metrics(self, metrics: list[MetricValue]) -> None:
        """
        Export metrics to Prometheus (no-op for scrape-based systems).

        Args:
            metrics: List of metrics to export
        """
        # Prometheus uses a pull model, so we don't need to push metrics
        pass

    def format_metrics(self, metrics: list[MetricValue]) -> str:
        """
        Format metrics in Prometheus format.

        Args:
            metrics: List of metrics to format

        Returns:
            Prometheus-formatted metrics
        """
        output = []

        # Group metrics by name and type
        grouped: dict[str, dict[str, list[MetricValue]]] = {}

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
            prometheus_name = f"{self.namespace}_{name}".replace(".", "_").replace(
                "-", "_"
            )

            for type_name, metrics_list in types.items():
                if metrics_list:
                    # Add TYPE comment
                    output.append(f"# TYPE {prometheus_name} {type_name}")

                    # Add HELP comment if we have a description
                    if metrics_list[0].description:
                        output.append(
                            f"# HELP {prometheus_name} {metrics_list[0].description}"
                        )

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
                                output.append(
                                    f"{prometheus_name}_count{tag_str} {len(values)}"
                                )
                                # Sum
                                output.append(
                                    f"{prometheus_name}_sum{tag_str} {sum(values)}"
                                )
                                # Buckets (simplified)
                                if len(values) >= 100:
                                    sorted_values = sorted(values)
                                    p50 = sorted_values[len(sorted_values) // 2]
                                    p95 = sorted_values[int(len(sorted_values) * 0.95)]
                                    p99 = sorted_values[int(len(sorted_values) * 0.99)]

                                    output.append(
                                        f'{prometheus_name}_bucket{{le="50"{tag_str[1:-1]}}} {len([v for v in values if v <= p50])}'
                                    )
                                    output.append(
                                        f'{prometheus_name}_bucket{{le="95"{tag_str[1:-1]}}} {len([v for v in values if v <= p95])}'
                                    )
                                    output.append(
                                        f'{prometheus_name}_bucket{{le="99"{tag_str[1:-1]}}} {len([v for v in values if v <= p99])}'
                                    )
                                    output.append(
                                        f'{prometheus_name}_bucket{{le="+Inf"{tag_str[1:-1]}}} {len(values)}'
                                    )
                        else:
                            # Simple value
                            output.append(f"{prometheus_name}{tag_str} {metric.value}")

        return "\n".join(output)


class LoggingExporter(MetricsExporter):
    """
    Exporter that logs metrics.

    This exporter logs metrics at regular intervals for debugging.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the logging exporter.

        Args:
            logger: Logger to use
        """
        self.logger = logger or logging.getLogger(__name__)

    async def export_metrics(self, metrics: list[MetricValue]) -> None:
        """
        Export metrics by logging them.

        Args:
            metrics: List of metrics to export
        """
        # Group metrics by name
        grouped: dict[str, dict[str, Any]] = {}

        for metric in metrics:
            name = metric.name

            if name not in grouped:
                grouped[name] = {
                    "type": metric.type.value,
                    "unit": metric.unit.value,
                    "values": [],
                }

            # Add value with tags
            grouped[name]["values"].append(
                {
                    "value": (
                        metric.value
                        if not isinstance(metric.value, list)
                        else f"[{len(metric.value)} values]"
                    ),
                    "tags": metric.tags,
                }
            )

        # Log each group
        for name, info in grouped.items():
            self.logger.info(
                f"Metric: {name} ({info['type']}, {info['unit']}), "
                f"Values: {json.dumps(info['values'])}"
            )


class MetricsRegistry:
    """
    Registry for application metrics.

    This class manages all metrics and handles exporting them.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the metrics registry.

        Args:
            logger: Logger to use
        """
        self.logger = logger or logging.getLogger(__name__)
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._timers: dict[str, Timer] = {}
        self._exporters: list[MetricsExporter] = []
        self._lock = asyncio.Lock()
        self._export_task: Optional[asyncio.Task] = None
        self._export_interval = 60.0  # Export interval in seconds
        self._shutting_down = False

    async def setup(
        self,
        export_interval: float = 60.0,
        exporters: Optional[list[MetricsExporter]] = None,
    ) -> None:
        """
        Set up the metrics registry.

        Args:
            export_interval: Interval in seconds between exports
            exporters: List of exporters to use
        """
        self._export_interval = export_interval

        if exporters:
            self._exporters.extend(exporters)

        # Start the export task if we have exporters
        if self._exporters and not self._export_task:
            self._export_task = asyncio.create_task(
                self._export_loop(), name="metrics_export"
            )

    async def shutdown(self) -> None:
        """
        Shut down the metrics registry.

        This stops the export task and performs a final export.
        """
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
            self.logger.error(f"Error in metrics export loop: {str(e)}", exc_info=True)

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
                        exc_info=True,
                    )

        except Exception as e:
            self.logger.error(f"Error exporting metrics: {str(e)}", exc_info=True)

    async def get_or_create_counter(
        self,
        name: str,
        description: str | None = None,
        unit: MetricUnit = MetricUnit.COUNT,
        tags: Optional[dict[str, str]] = None,
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
        async with self._lock:
            key = name + "".join(f"{k}:{v}" for k, v in (tags or {}).items())

            if key not in self._counters:
                self._counters[key] = Counter(
                    name=name, description=description, unit=unit, tags=tags
                )

            return self._counters[key]

    async def get_or_create_gauge(
        self,
        name: str,
        description: str | None = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[dict[str, str]] = None,
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
        async with self._lock:
            key = name + "".join(f"{k}:{v}" for k, v in (tags or {}).items())

            if key not in self._gauges:
                self._gauges[key] = Gauge(
                    name=name, description=description, unit=unit, tags=tags
                )

            return self._gauges[key]

    async def get_or_create_histogram(
        self,
        name: str,
        description: str | None = None,
        unit: MetricUnit = MetricUnit.NONE,
        tags: Optional[dict[str, str]] = None,
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
        async with self._lock:
            key = name + "".join(f"{k}:{v}" for k, v in (tags or {}).items())

            if key not in self._histograms:
                self._histograms[key] = Histogram(
                    name=name, description=description, unit=unit, tags=tags
                )

            return self._histograms[key]

    async def get_or_create_timer(
        self,
        name: str,
        description: str | None = None,
        tags: Optional[dict[str, str]] = None,
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
        async with self._lock:
            key = name + "".join(f"{k}:{v}" for k, v in (tags or {}).items())

            if key not in self._timers:
                self._timers[key] = Timer(name=name, description=description, tags=tags)

            return self._timers[key]

    async def get_all_metrics(self) -> list[MetricValue]:
        """
        Get all metrics.

        Returns:
            List of all metric values
        """
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
        # Find Prometheus exporter
        prometheus_exporter = next(
            (e for e in self._exporters if isinstance(e, PrometheusExporter)),
            PrometheusExporter(),
        )

        # Get all metrics
        metrics = asyncio.run(self.get_all_metrics())

        # Format metrics
        return prometheus_exporter.format_metrics(metrics)


# Global metrics registry
metrics_registry: Optional[MetricsRegistry] = None


def get_metrics_registry() -> MetricsRegistry:
    """
    Get the global metrics registry.

    Returns:
        The global metrics registry
    """
    global metrics_registry
    if metrics_registry is None:
        metrics_registry = MetricsRegistry()
    return metrics_registry


# Convenience functions for working with metrics
async def counter(
    name: str,
    description: str | None = None,
    tags: Optional[dict[str, str]] = None,
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
        name=name, description=description, tags=tags
    )


async def gauge(
    name: str,
    description: str | None = None,
    unit: MetricUnit = MetricUnit.NONE,
    tags: Optional[dict[str, str]] = None,
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
        name=name, description=description, unit=unit, tags=tags
    )


async def histogram(
    name: str,
    description: str | None = None,
    unit: MetricUnit = MetricUnit.NONE,
    tags: Optional[dict[str, str]] = None,
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
        name=name, description=description, unit=unit, tags=tags
    )


async def timer(
    name: str,
    description: str | None = None,
    tags: Optional[dict[str, str]] = None,
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
        name=name, description=description, tags=tags
    )


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting request metrics.

    This middleware collects HTTP request metrics such as request count,
    request duration, and response status codes.
    """

    def __init__(
        self,
        app: FastAPI,
        metrics_path: str = "/metrics",
        registry: Optional[MetricsRegistry] = None,
        excluded_paths: list[str] | None = None,
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
        self.metrics_path = metrics_path
        self.registry = registry or get_metrics_registry()
        self.excluded_paths = excluded_paths or [metrics_path]

        # Counters for request metrics
        self._setup_task = asyncio.create_task(self._setup_metrics())

    async def _setup_metrics(self) -> None:
        """Set up the metrics counters."""
        self.request_counter = await self.registry.get_or_create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit=MetricUnit.COUNT,
        )

        self.request_duration = await self.registry.get_or_create_histogram(
            name="http_request_duration_milliseconds",
            description="HTTP request duration in milliseconds",
            unit=MetricUnit.MILLISECONDS,
        )

        self.request_in_progress = await self.registry.get_or_create_gauge(
            name="http_requests_in_progress",
            description="Number of HTTP requests in progress",
            unit=MetricUnit.COUNT,
        )

        self.response_size = await self.registry.get_or_create_histogram(
            name="http_response_size_bytes",
            description="HTTP response size in bytes",
            unit=MetricUnit.BYTES,
        )

    @with_error_context
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
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
        tags = {"method": method, "path": path}

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
            tags.update({"status": str(status_code), "status_range": status_range})

            # Track response metrics
            response_size = int(response.headers.get("content-length", 0))
            if response_size > 0:
                await self.response_size.observe(response_size)

            return response

        finally:
            # Calculate request duration
            duration = (time.time() - start_time) * 1000  # Convert to ms

            # Record request duration
            await self.request_duration.observe(duration)

            # Decrement in-progress counter
            await self.request_in_progress.decrement()
