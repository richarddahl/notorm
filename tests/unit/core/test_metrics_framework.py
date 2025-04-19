# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the uno.core.metrics.framework module.
"""

import asyncio
import json
import time
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.metrics.framework import (
    MetricType,
    MetricUnit,
    MetricValue,
    MetricsConfig,
    MetricsContext,
    Counter,
    Gauge,
    Histogram,
    Timer,
    TimerContext,
    MetricsRegistry,
    PrometheusExporter,
    LoggingExporter,
    MetricsMiddleware,
    configure_metrics,
    get_metrics_registry,
    counter,
    gauge,
    histogram,
    timer,
    timed,
    with_metrics_context,
    add_metrics_context,
    get_metrics_context,
    clear_metrics_context,
)


class TestMetricUnit:
    """Tests for the MetricUnit enum."""
    
    def test_from_string(self):
        """Test converting string to MetricUnit."""
        assert MetricUnit.from_string("COUNT") == MetricUnit.COUNT
        assert MetricUnit.from_string("milliseconds") == MetricUnit.MILLISECONDS
        
        with pytest.raises(ValueError):
            MetricUnit.from_string("INVALID")


class TestMetricValue:
    """Tests for the MetricValue class."""
    
    def test_with_tags(self):
        """Test adding tags to a metric value."""
        value = MetricValue(
            name="test",
            value=42,
            type=MetricType.COUNTER,
            tags={"a": "1"}
        )
        
        # Add more tags
        new_value = value.with_tags(b="2", c="3")
        
        assert new_value.name == "test"
        assert new_value.value == 42
        assert new_value.type == MetricType.COUNTER
        assert new_value.tags == {"a": "1", "b": "2", "c": "3"}


class TestMetricsContext:
    """Tests for the MetricsContext class."""
    
    def test_to_dict(self):
        """Test converting context to dictionary."""
        context = MetricsContext(
            trace_id="123",
            service_name="test_service",
            environment="test",
            additional_tags={"custom": "value"}
        )
        
        result = context.to_dict()
        assert result["trace_id"] == "123"
        assert result["service_name"] == "test_service"
        assert result["environment"] == "test"
        assert result["custom"] == "value"
    
    def test_merge(self):
        """Test merging contexts."""
        context1 = MetricsContext(
            trace_id="123",
            service_name="service1",
            additional_tags={"a": 1, "b": 2}
        )
        
        context2 = MetricsContext(
            service_name="service2",  # Should override
            environment="test",
            additional_tags={"b": 3, "c": 4}  # Should override b and add c
        )
        
        merged = context1.merge(context2)
        
        assert merged.trace_id == "123"
        assert merged.service_name == "service2"  # From context2
        assert merged.environment == "test"  # From context2
        assert merged.additional_tags["a"] == 1  # From context1
        assert merged.additional_tags["b"] == 3  # From context2
        assert merged.additional_tags["c"] == 4  # From context2
    
    def test_merge_with_dict(self):
        """Test merging with a dictionary."""
        context = MetricsContext(
            trace_id="123",
            service_name="service1",
            additional_tags={"a": 1}
        )
        
        # Merge with dictionary
        merged = context.merge({
            "service_name": "service2",
            "b": 2,
            "c": 3
        })
        
        assert merged.trace_id == "123"
        assert merged.service_name == "service2"
        assert merged.additional_tags["a"] == 1
        assert merged.additional_tags["b"] == 2
        assert merged.additional_tags["c"] == 3


class TestMetricsConfig:
    """Tests for the MetricsConfig class."""
    
    def test_from_config(self):
        """Test creating MetricsConfig from a configuration provider."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "metrics.enabled": True,
            "service.name": "test-service",
            "environment": "test",
            "metrics.export_interval": 30.0,
            "metrics.console_export": True,
            "metrics.prometheus_export": True,
            "metrics.prometheus_namespace": "test",
            "metrics.include_trace_id": True,
            "metrics.default_tags": '{"region": "us-west", "version": "1.0.0"}',
        }.get(key, default)
        
        config = MetricsConfig.from_config(mock_config)
        
        assert config.enabled is True
        assert config.service_name == "test-service"
        assert config.environment == "test"
        assert config.export_interval == 30.0
        assert config.console_export is True
        assert config.prometheus_export is True
        assert config.prometheus_namespace == "test"
        assert config.include_trace_id is True
        assert config.default_tags == {"region": "us-west", "version": "1.0.0"}
    
    def test_from_config_invalid_tags(self):
        """Test handling invalid JSON in default_tags."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "metrics.default_tags": '{invalid json}',
        }.get(key, default)
        
        config = MetricsConfig.from_config(mock_config)
        
        # Should use empty dict for invalid JSON
        assert config.default_tags == {}


@pytest.fixture
def reset_registry():
    """Reset the metrics registry before and after tests."""
    # Save original registry
    orig_registry = getattr(get_metrics_registry, "_metrics_registry", None)
    
    # Reset registry
    get_metrics_registry._metrics_registry = None
    
    yield
    
    # Restore original registry
    get_metrics_registry._metrics_registry = orig_registry


class TestCounter:
    """Tests for the Counter class."""
    
    @pytest.mark.asyncio
    async def test_increment(self):
        """Test incrementing a counter."""
        counter = Counter("test_counter", "Test counter", MetricUnit.COUNT)
        
        # Initial value should be 0
        assert counter.get_value().value == 0
        
        # Increment by 1
        await counter.increment()
        assert counter.get_value().value == 1
        
        # Increment by a specific amount
        await counter.increment(5)
        assert counter.get_value().value == 6
    
    @pytest.mark.asyncio
    async def test_increment_negative(self):
        """Test incrementing a counter with a negative value."""
        counter = Counter("test_counter", "Test counter", MetricUnit.COUNT)
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            await counter.increment(-1)


class TestGauge:
    """Tests for the Gauge class."""
    
    @pytest.mark.asyncio
    async def test_set(self):
        """Test setting a gauge value."""
        gauge = Gauge("test_gauge", "Test gauge", MetricUnit.NONE)
        
        # Initial value should be 0.0
        assert gauge.get_value().value == 0.0
        
        # Set to specific value
        await gauge.set(42.5)
        assert gauge.get_value().value == 42.5
    
    @pytest.mark.asyncio
    async def test_increment_decrement(self):
        """Test incrementing and decrementing a gauge."""
        gauge = Gauge("test_gauge", "Test gauge", MetricUnit.NONE)
        
        # Initial value should be 0.0
        assert gauge.get_value().value == 0.0
        
        # Increment
        await gauge.increment(5.5)
        assert gauge.get_value().value == 5.5
        
        # Decrement
        await gauge.decrement(2.5)
        assert gauge.get_value().value == 3.0
    
    @pytest.mark.asyncio
    async def test_set_to_current_time(self):
        """Test setting a gauge to the current time."""
        gauge = Gauge("test_gauge", "Test gauge", MetricUnit.SECONDS)
        
        # Set to current time
        now = time.time()
        await gauge.set_to_current_time()
        
        # Value should be close to current time
        assert abs(gauge.get_value().value - now) < 1.0
    
    @pytest.mark.asyncio
    async def test_track_inprogress(self):
        """Test tracking in-progress operations with a gauge."""
        gauge = Gauge("in_progress", "In-progress operations", MetricUnit.COUNT)
        
        # Initial value should be 0.0
        assert gauge.get_value().value == 0.0
        
        # Use context manager to track in-progress operations
        async with await gauge.track_inprogress():
            assert gauge.get_value().value == 1.0
        
        # After context exit, value should be back to 0.0
        assert gauge.get_value().value == 0.0


class TestHistogram:
    """Tests for the Histogram class."""
    
    @pytest.mark.asyncio
    async def test_observe(self):
        """Test observing values in a histogram."""
        histogram = Histogram("test_histogram", "Test histogram", MetricUnit.MILLISECONDS)
        
        # Initial values should be empty
        assert histogram.get_value().value == []
        
        # Observe values
        await histogram.observe(10.0)
        await histogram.observe(20.0)
        await histogram.observe(30.0)
        
        # Values should be recorded
        assert histogram.get_value().value == [10.0, 20.0, 30.0]
    
    @pytest.mark.asyncio
    async def test_max_size(self):
        """Test histogram max size limitation."""
        histogram = Histogram("test_histogram", "Test histogram", max_size=2)
        
        # Observe more values than max_size
        await histogram.observe(10.0)
        await histogram.observe(20.0)
        await histogram.observe(30.0)
        
        # Only the most recent values should be kept
        assert histogram.get_value().value == [20.0, 30.0]
    
    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting statistics from a histogram."""
        histogram = Histogram("test_histogram", "Test histogram")
        
        # Empty histogram should return default statistics
        stats = await histogram.get_statistics()
        assert stats["count"] == 0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["mean"] == 0.0
        
        # Add values
        await histogram.observe(10.0)
        await histogram.observe(20.0)
        await histogram.observe(30.0)
        
        # Check statistics
        stats = await histogram.get_statistics()
        assert stats["count"] == 3
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
        assert stats["mean"] == 20.0
        assert stats["median"] == 20.0
        assert stats["p95"] == 30.0
        assert stats["p99"] == 30.0


class TestTimer:
    """Tests for the Timer class."""
    
    @pytest.mark.asyncio
    async def test_record(self):
        """Test recording durations directly."""
        timer = Timer("test_timer", "Test timer")
        
        # Record durations
        await timer.record(100.0)
        await timer.record(200.0)
        await timer.record(300.0)
        
        # Value should be the mean of recorded durations
        assert timer.get_value().value == 200.0
    
    def test_time_context_manager(self):
        """Test using timer as a context manager."""
        timer = Timer("test_timer", "Test timer")
        
        # Use context manager to time an operation
        with timer.time():
            # Simulate some work
            time.sleep(0.01)
        
        # Value should be non-zero after timing
        assert timer.get_value().value > 0.0
    
    @pytest.mark.asyncio
    async def test_timer_context(self):
        """Test using TimerContext for async operations."""
        timer = Timer("test_timer", "Test timer")
        
        # Use async context manager to time an operation
        async with TimerContext(timer):
            # Simulate some work
            await asyncio.sleep(0.01)
        
        # Value should be non-zero after timing
        assert timer.get_value().value > 0.0
    
    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting statistics from a timer."""
        timer = Timer("test_timer", "Test timer")
        
        # Record durations
        await timer.record(100.0)
        await timer.record(200.0)
        await timer.record(300.0)
        
        # Check statistics
        stats = await timer.get_statistics()
        assert stats["count"] == 3
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0
        assert stats["mean"] == 200.0


class TestTimedDecorator:
    """Tests for the timed decorator."""
    
    @pytest.mark.asyncio
    async def test_timed_async_function(self, reset_registry):
        """Test timed decorator on an async function."""
        registry = get_metrics_registry()
        
        # Define a timed async function
        @timed("test.async_function", description="Test async function", registry=registry)
        async def test_async_function(delay: float) -> str:
            await asyncio.sleep(delay)
            return "Done"
        
        # Call the function
        result = await test_async_function(0.01)
        assert result == "Done"
        
        # Check that metrics were recorded
        metrics = await registry.get_all_metrics()
        timer_metrics = [m for m in metrics if m.name == "test.async_function"]
        assert len(timer_metrics) == 1
        assert timer_metrics[0].type == MetricType.TIMER
        assert timer_metrics[0].value > 0  # Should have recorded a duration
    
    def test_timed_sync_function(self, reset_registry):
        """Test timed decorator on a synchronous function."""
        registry = get_metrics_registry()
        
        # Define a timed sync function
        @timed("test.sync_function", description="Test sync function", registry=registry)
        def test_sync_function(delay: float) -> str:
            time.sleep(delay)
            return "Done"
        
        # Call the function
        result = test_sync_function(0.01)
        assert result == "Done"
        
        # Check that metrics were recorded (need to access registry asynchronously)
        async def check_metrics():
            metrics = await registry.get_all_metrics()
            timer_metrics = [m for m in metrics if m.name == "test.sync_function"]
            assert len(timer_metrics) == 1
            assert timer_metrics[0].type == MetricType.TIMER
            assert timer_metrics[0].value > 0  # Should have recorded a duration
        
        # Run async check
        asyncio.run(check_metrics())


class TestMetricsContextManagement:
    """Tests for metrics context management functions."""
    
    def test_add_get_clear_metrics_context(self):
        """Test adding, getting, and clearing metrics context."""
        clear_metrics_context()  # Start with a clean slate
        
        # Add context
        add_metrics_context(service="test", component="component1")
        
        # Get context
        context = get_metrics_context()
        assert context["service"] == "test"
        assert context["component"] == "component1"
        
        # Add more context
        add_metrics_context(instance="instance1")
        context = get_metrics_context()
        assert context["service"] == "test"
        assert context["component"] == "component1"
        assert context["instance"] == "instance1"
        
        # Clear context
        clear_metrics_context()
        assert get_metrics_context() == {}
    
    @pytest.mark.asyncio
    async def test_with_metrics_context_decorator(self):
        """Test the with_metrics_context decorator."""
        clear_metrics_context()  # Start with a clean slate
        
        # Define a function with the decorator
        @with_metrics_context
        async def test_function(param1, param2):
            # Inside the function, context should be set
            context = get_metrics_context()
            assert "function" in context
            assert context["function"] == "test_function"
            assert "module" in context
            assert "args" in context
            assert context["args"]["param1"] == param1
            assert context["args"]["param2"] == param2
            
            return "Success"
        
        # Call the function
        result = await test_function("a", "b")
        assert result == "Success"
        
        # Context should be cleared after function call
        assert "function" not in get_metrics_context()
    
    @pytest.mark.asyncio
    async def test_with_metrics_context_static(self):
        """Test with_metrics_context decorator with static context."""
        clear_metrics_context()  # Start with a clean slate
        
        # Define a function with the decorator
        @with_metrics_context(component="test_component", operation="test_op")
        async def test_function():
            # Inside the function, context should be set
            context = get_metrics_context()
            assert context["component"] == "test_component"
            assert context["operation"] == "test_op"
            
            return "Success"
        
        # Call the function
        result = await test_function()
        assert result == "Success"
        
        # Context should be cleared after function call
        assert "component" not in get_metrics_context()


class TestPrometheusExporter:
    """Tests for the PrometheusExporter class."""
    
    def test_format_metrics(self):
        """Test formatting metrics in Prometheus format."""
        exporter = PrometheusExporter(namespace="test")
        
        # Create some test metrics
        metrics = [
            # Counter
            MetricValue(
                name="requests_total",
                value=42,
                type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                tags={"method": "GET", "path": "/api"},
                description="Total requests"
            ),
            # Gauge
            MetricValue(
                name="connections",
                value=15.5,
                type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                tags={"server": "main"},
                description="Active connections"
            ),
            # Timer
            MetricValue(
                name="request_duration",
                value=123.45,
                type=MetricType.TIMER,
                unit=MetricUnit.MILLISECONDS,
                description="Request duration"
            ),
            # Histogram (simplified for testing)
            MetricValue(
                name="response_size",
                value=[100.0, 200.0, 300.0],
                type=MetricType.HISTOGRAM,
                unit=MetricUnit.BYTES,
                description="Response size"
            ),
        ]
        
        # Format metrics
        result = exporter.format_metrics(metrics)
        
        # Check output
        assert "# TYPE test_requests_total counter" in result
        assert "# HELP test_requests_total Total requests" in result
        assert 'test_requests_total{method="GET",path="/api"} 42' in result
        
        assert "# TYPE test_connections gauge" in result
        assert "# HELP test_connections Active connections" in result
        assert 'test_connections{server="main"} 15.5' in result
        
        assert "# TYPE test_request_duration timer" in result
        assert "# HELP test_request_duration Request duration" in result
        assert "test_request_duration 123.45" in result
        
        assert "# TYPE test_response_size histogram" in result
        assert "# HELP test_response_size Response size" in result
        assert "test_response_size_count 3" in result
        assert "test_response_size_sum 600.0" in result


class TestLoggingExporter:
    """Tests for the LoggingExporter class."""
    
    @pytest.mark.asyncio
    async def test_export_metrics(self):
        """Test exporting metrics to logs."""
        mock_logger = MagicMock()
        exporter = LoggingExporter(logger=mock_logger)
        
        # Create some test metrics
        metrics = [
            MetricValue(
                name="test_counter",
                value=42,
                type=MetricType.COUNTER,
                tags={"tag1": "value1"}
            ),
            MetricValue(
                name="test_counter",
                value=43,
                type=MetricType.COUNTER,
                tags={"tag2": "value2"}
            ),
            MetricValue(
                name="test_gauge",
                value=15.5,
                type=MetricType.GAUGE
            ),
        ]
        
        # Export metrics
        await exporter.export_metrics(metrics)
        
        # Logger should have been called twice (once per unique metric name)
        assert mock_logger.info.call_count == 2
        
        # First call should log the counter
        args, kwargs = mock_logger.info.call_args_list[0]
        assert "test_counter" in args[0]
        assert "counter" in args[0]
        assert "metrics" in kwargs["extra"]
        
        # Second call should log the gauge
        args, kwargs = mock_logger.info.call_args_list[1]
        assert "test_gauge" in args[0]
        assert "gauge" in args[0]
        assert "metrics" in kwargs["extra"]


@pytest.mark.asyncio
class TestMetricsRegistry:
    """Tests for the MetricsRegistry class."""
    
    async def test_setup_with_exporters(self, reset_registry):
        """Test setting up the registry with exporters."""
        mock_exporter1 = MagicMock(spec=LoggingExporter)
        mock_exporter2 = MagicMock(spec=PrometheusExporter)
        
        registry = MetricsRegistry()
        await registry.setup(exporters=[mock_exporter1, mock_exporter2])
        
        # Exporters should be registered
        assert len(registry._exporters) == 2
        assert registry._exporters[0] == mock_exporter1
        assert registry._exporters[1] == mock_exporter2
        
        # Background task should be started
        assert registry._export_task is not None
        
        # Cleanup
        await registry.shutdown()
    
    async def test_export_metrics(self, reset_registry):
        """Test exporting metrics to exporters."""
        mock_exporter = MagicMock(spec=LoggingExporter)
        
        registry = MetricsRegistry()
        registry._exporters.append(mock_exporter)
        
        # Create some metrics
        counter = await registry.get_or_create_counter("test_counter")
        await counter.increment()
        
        gauge = await registry.get_or_create_gauge("test_gauge")
        await gauge.set(15.5)
        
        # Export metrics
        await registry._export_metrics()
        
        # Exporter's export_metrics should have been called once
        mock_exporter.export_metrics.assert_called_once()
        
        # Get the metrics that were exported
        args, kwargs = mock_exporter.export_metrics.call_args
        exported_metrics = args[0]
        
        # Should have two metrics
        assert len(exported_metrics) == 2
        
        # Check counter
        counter_metrics = [m for m in exported_metrics if m.name == "test_counter"]
        assert len(counter_metrics) == 1
        assert counter_metrics[0].value == 1
        
        # Check gauge
        gauge_metrics = [m for m in exported_metrics if m.name == "test_gauge"]
        assert len(gauge_metrics) == 1
        assert gauge_metrics[0].value == 15.5
        
        # Cleanup
        await registry.shutdown()
    
    async def test_get_or_create_metrics(self, reset_registry):
        """Test getting or creating metrics."""
        registry = MetricsRegistry()
        
        # Create metrics
        counter1 = await registry.get_or_create_counter("test_counter")
        counter2 = await registry.get_or_create_counter("test_counter")
        
        # Should get the same instance
        assert counter1 is counter2
        
        # Create metrics with different tags
        gauge1 = await registry.get_or_create_gauge("test_gauge", tags={"tag1": "value1"})
        gauge2 = await registry.get_or_create_gauge("test_gauge", tags={"tag2": "value2"})
        
        # Should get different instances
        assert gauge1 is not gauge2
        
        # Create a histogram
        histogram = await registry.get_or_create_histogram("test_histogram")
        assert histogram.name == "test_histogram"
        
        # Create a timer
        timer = await registry.get_or_create_timer("test_timer")
        assert timer.name == "test_timer"
        
        # Cleanup
        await registry.shutdown()
    
    async def test_prometheus_metrics(self, reset_registry):
        """Test getting metrics in Prometheus format."""
        registry = MetricsRegistry()
        
        # Create a counter and increment it
        counter = await registry.get_or_create_counter("test_counter")
        await counter.increment(42)
        
        # Get metrics in Prometheus format
        prometheus_metrics = registry.get_prometheus_metrics()
        
        # Should contain the counter
        assert "# TYPE uno_test_counter counter" in prometheus_metrics
        assert "uno_test_counter 42" in prometheus_metrics
        
        # Cleanup
        await registry.shutdown()
    
    async def test_disabled_metrics(self, reset_registry):
        """Test behavior when metrics are disabled."""
        config = MetricsConfig(enabled=False)
        registry = MetricsRegistry(config=config)
        
        # Create metrics (should be no-ops)
        counter = await registry.get_or_create_counter("test_counter")
        await counter.increment()
        
        # Get metrics
        metrics = await registry.get_all_metrics()
        
        # Should be empty
        assert metrics == []
        
        # Get Prometheus metrics
        prometheus_metrics = registry.get_prometheus_metrics()
        
        # Should indicate metrics are disabled
        assert "# Metrics collection is disabled" in prometheus_metrics
    
    async def test_default_tags(self, reset_registry):
        """Test that default tags are applied to metrics."""
        config = MetricsConfig(
            default_tags={"service": "test-service", "environment": "test"}
        )
        registry = MetricsRegistry(config=config)
        
        # Create a counter
        counter = await registry.get_or_create_counter("test_counter")
        
        # Check that default tags are applied
        counter_value = counter.get_value()
        assert counter_value.tags["service"] == "test-service"
        assert counter_value.tags["environment"] == "test"
        
        # Create a counter with custom tags
        counter_with_tags = await registry.get_or_create_counter(
            "test_counter_with_tags",
            tags={"component": "test-component"}
        )
        
        # Check that both default and custom tags are applied
        counter_with_tags_value = counter_with_tags.get_value()
        assert counter_with_tags_value.tags["service"] == "test-service"
        assert counter_with_tags_value.tags["environment"] == "test"
        assert counter_with_tags_value.tags["component"] == "test-component"
        
        # Cleanup
        await registry.shutdown()


class TestMetricsMiddleware:
    """Tests for the MetricsMiddleware."""
    
    @pytest.mark.asyncio
    async def test_middleware_setup(self, reset_registry):
        """Test middleware initialization."""
        app = FastAPI()
        registry = get_metrics_registry()
        
        middleware = MetricsMiddleware(
            app,
            metrics_path="/metrics",
            registry=registry,
            excluded_paths=["/health"]
        )
        
        # Metrics path should be set
        assert middleware.metrics_path == "/metrics"
        
        # Excluded paths should be set
        assert middleware.excluded_paths == ["/metrics", "/health"]
        
        # Setup task should be created
        assert middleware._setup_task is not None
        
        # Wait for setup task to complete
        await asyncio.sleep(0.1)
        
        # Metrics should be initialized
        assert middleware.request_counter is not None
        assert middleware.request_duration is not None
        assert middleware.request_in_progress is not None
        assert middleware.response_size is not None
        assert middleware.error_counter is not None
    
    @pytest.mark.asyncio
    async def test_middleware_excluded_path(self, reset_registry):
        """Test middleware skips excluded paths."""
        app = FastAPI()
        registry = get_metrics_registry()
        
        middleware = MetricsMiddleware(
            app,
            metrics_path="/metrics",
            registry=registry,
            excluded_paths=["/health"]
        )
        
        # Wait for setup task to complete
        await asyncio.sleep(0.1)
        
        # Create mock request for excluded path
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        
        # Create mock response
        mock_response = MagicMock()
        
        # Create mock call_next function
        async def mock_call_next(request):
            return mock_response
        
        # Call middleware
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should return mock response directly
        assert response is mock_response
    
    @pytest.mark.asyncio
    async def test_middleware_metrics_collection(self, reset_registry):
        """Test middleware collects metrics for non-excluded paths."""
        app = FastAPI()
        registry = get_metrics_registry()
        
        middleware = MetricsMiddleware(
            app,
            metrics_path="/metrics",
            registry=registry,
            excluded_paths=["/health"]
        )
        
        # Wait for setup task to complete
        await asyncio.sleep(0.1)
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.scope = {"path_params": {}}
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}
        
        # Create mock call_next function
        async def mock_call_next(request):
            return mock_response
        
        # Call middleware
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should return mock response
        assert response is mock_response
        
        # Get all metrics
        metrics = await registry.get_all_metrics()
        
        # Should have request metrics
        counter_metrics = [m for m in metrics if m.name == "http.requests.total"]
        assert len(counter_metrics) > 0
        assert counter_metrics[0].value >= 1
        
        # Should have duration metrics
        duration_metrics = [m for m in metrics if m.name == "http.request.duration"]
        assert len(duration_metrics) > 0
        
        # Should have response size metrics
        size_metrics = [m for m in metrics if m.name == "http.response.size"]
        assert len(size_metrics) > 0
        
        # Should not have error metrics
        error_metrics = [m for m in metrics if m.name == "http.errors.total"]
        assert len(error_metrics) > 0
        assert error_metrics[0].value == 0
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self, reset_registry):
        """Test middleware handles errors correctly."""
        app = FastAPI()
        registry = get_metrics_registry()
        
        middleware = MetricsMiddleware(
            app,
            metrics_path="/metrics",
            registry=registry,
            excluded_paths=["/health"]
        )
        
        # Wait for setup task to complete
        await asyncio.sleep(0.1)
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/error"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.scope = {"path_params": {}}
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        
        # Create mock call_next function that raises an exception
        test_exception = ValueError("Test error")
        async def mock_call_next(request):
            raise test_exception
        
        # Call middleware
        with pytest.raises(ValueError) as excinfo:
            await middleware.dispatch(mock_request, mock_call_next)
        
        # Should propagate the exception
        assert excinfo.value is test_exception
        
        # Get all metrics
        metrics = await registry.get_all_metrics()
        
        # Should have request metrics
        counter_metrics = [m for m in metrics if m.name == "http.requests.total"]
        assert len(counter_metrics) > 0
        assert counter_metrics[0].value >= 1
        
        # Should have duration metrics
        duration_metrics = [m for m in metrics if m.name == "http.request.duration"]
        assert len(duration_metrics) > 0
        
        # Should have error metrics
        error_metrics = [m for m in metrics if m.name == "http.errors.total"]
        assert len(error_metrics) > 0
        assert error_metrics[0].value >= 1