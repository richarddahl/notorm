# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the uno.core.tracing.framework module.
"""

import asyncio
import base64
import json
import time
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.tracing.framework import (
    Span,
    SpanKind,
    TracingContext,
    PropagationContext,
    SpanProcessor,
    SpanExporter,
    LoggingSpanProcessor,
    LoggingSpanExporter,
    BatchSpanProcessor,
    Tracer,
    TracingConfig,
    TracingMiddleware,
    configure_tracing,
    get_tracer,
    get_current_span,
    get_current_trace_id,
    get_current_span_id,
    trace,
    inject_context,
    extract_context,
)


class TestPropagationContext:
    """Tests for PropagationContext."""
    
    def test_to_dict(self):
        """Test converting propagation context to dict."""
        context = PropagationContext(
            trace_id="1234",
            span_id="5678",
            parent_span_id="9012",
            sampled=True,
            baggage={"foo": "bar"}
        )
        
        result = context.to_dict()
        
        assert result["trace_id"] == "1234"
        assert result["span_id"] == "5678"
        assert result["parent_span_id"] == "9012"
        assert result["sampled"] is True
        assert result["baggage"] == {"foo": "bar"}
    
    def test_from_dict(self):
        """Test creating propagation context from dict."""
        data = {
            "trace_id": "1234",
            "span_id": "5678",
            "parent_span_id": "9012",
            "sampled": True,
            "baggage": {"foo": "bar"}
        }
        
        context = PropagationContext.from_dict(data)
        
        assert context.trace_id == "1234"
        assert context.span_id == "5678"
        assert context.parent_span_id == "9012"
        assert context.sampled is True
        assert context.baggage == {"foo": "bar"}


class TestSpan:
    """Tests for Span."""
    
    def test_duration(self):
        """Test span duration calculation."""
        # Create a span with start and end times
        span = Span(
            name="test",
            trace_id="1234",
            span_id="5678",
            start_time=100.0,
            end_time=100.5  # 500ms later
        )
        
        # Duration should be in milliseconds
        assert span.duration == 500.0
        
        # When end_time is None, duration should be 0
        span.end_time = None
        assert span.duration == 0
    
    def test_add_event(self):
        """Test adding events to spans."""
        span = Span(name="test", trace_id="1234", span_id="5678")
        
        # Add an event with attributes
        span.add_event("test_event", {"foo": "bar"}, 123.45)
        
        # Check the event
        assert len(span.events) == 1
        assert span.events[0]["name"] == "test_event"
        assert span.events[0]["attributes"] == {"foo": "bar"}
        assert span.events[0]["timestamp"] == 123.45
        
        # Add an event without optional parameters
        span.add_event("another_event")
        
        # Check the event
        assert len(span.events) == 2
        assert span.events[1]["name"] == "another_event"
        assert span.events[1]["attributes"] == {}
        assert "timestamp" in span.events[1]  # Should have auto-generated timestamp
    
    def test_set_status(self):
        """Test setting span status."""
        span = Span(name="test", trace_id="1234", span_id="5678")
        
        # Initial status should be "ok"
        assert span.status_code == "ok"
        assert span.status_message is None
        
        # Set error status
        span.set_status("error", "Something went wrong")
        
        assert span.status_code == "error"
        assert span.status_message == "Something went wrong"
    
    def test_finish(self):
        """Test finishing a span."""
        span = Span(name="test", trace_id="1234", span_id="5678")
        
        # Initially, end_time should be None
        assert span.end_time is None
        
        # Finish with auto-generated end time
        span.finish()
        
        # end_time should now be set
        assert span.end_time is not None
        
        # Finish with explicit end time
        specific_time = 200.0
        span.finish(specific_time)
        
        # end_time should be the specified value
        assert span.end_time == specific_time
    
    def test_to_dict(self):
        """Test converting span to dict."""
        span = Span(
            name="test_span",
            trace_id="1234",
            span_id="5678",
            parent_span_id="9012",
            start_time=100.0,
            end_time=100.5,
            attributes={"foo": "bar"},
            kind=SpanKind.SERVER
        )
        
        span.add_event("test_event", {"event_attr": "value"})
        span.set_status("error", "Test error")
        
        result = span.to_dict()
        
        assert result["name"] == "test_span"
        assert result["trace_id"] == "1234"
        assert result["span_id"] == "5678"
        assert result["parent_span_id"] == "9012"
        assert result["start_time"] == 100.0
        assert result["end_time"] == 100.5
        assert result["duration_ms"] == 500.0
        assert result["attributes"] == {"foo": "bar"}
        assert len(result["events"]) == 1
        assert result["events"][0]["name"] == "test_event"
        assert result["events"][0]["attributes"] == {"event_attr": "value"}
        assert result["kind"] == "server"
        assert result["status"]["code"] == "error"
        assert result["status"]["message"] == "Test error"


@pytest.fixture
def reset_span_context():
    """Reset the current span context before and after tests."""
    from uno.core.tracing.framework import _current_span
    
    # Save original token
    original = _current_span.get()
    
    # Reset to None
    _current_span.set(None)
    
    yield
    
    # Restore original value
    _current_span.set(original)


class TestSpanContext:
    """Tests for current span context functions."""
    
    def test_get_current_span(self, reset_span_context):
        """Test getting the current span."""
        # Initially there should be no current span
        assert get_current_span() is None
        
        # Set a current span
        from uno.core.tracing.framework import _current_span
        
        span = Span(name="test", trace_id="1234", span_id="5678")
        _current_span.set(span)
        
        # Now we should get the span
        assert get_current_span() is span
    
    def test_get_trace_and_span_ids(self, reset_span_context):
        """Test getting trace and span IDs."""
        # Initially there should be no IDs
        assert get_current_trace_id() is None
        assert get_current_span_id() is None
        
        # Set a current span
        from uno.core.tracing.framework import _current_span
        
        span = Span(name="test", trace_id="1234", span_id="5678")
        _current_span.set(span)
        
        # Now we should get the IDs
        assert get_current_trace_id() == "1234"
        assert get_current_span_id() == "5678"


class TestTracingContext:
    """Tests for TracingContext."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self, reset_span_context):
        """Test using TracingContext as a context manager."""
        # Create a mock tracer
        mock_tracer = MagicMock()
        mock_span = Span(name="test", trace_id="1234", span_id="5678")
        
        mock_tracer.start_span = MagicMock(return_value=mock_span)
        mock_tracer.end_span = MagicMock()
        
        # Use the context manager
        async with TracingContext(mock_tracer, "test_span", {"foo": "bar"}, SpanKind.CLIENT) as span:
            # Check that we got the span
            assert span is mock_span
            
            # Check that the span was started
            mock_tracer.start_span.assert_called_once_with(
                name="test_span",
                attributes={"foo": "bar"},
                kind=SpanKind.CLIENT
            )
            
            # Check that the span was set as current
            assert get_current_span() is mock_span
        
        # Check that the span was ended
        mock_tracer.end_span.assert_called_once_with(mock_span)
        
        # Check that the current span was reset
        assert get_current_span() is None
    
    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self, reset_span_context):
        """Test TracingContext handling exceptions."""
        # Create a mock tracer
        mock_tracer = MagicMock()
        mock_span = Span(name="test", trace_id="1234", span_id="5678")
        
        mock_tracer.start_span = MagicMock(return_value=mock_span)
        mock_tracer.end_span = MagicMock()
        
        # Use the context manager with an exception
        try:
            async with TracingContext(mock_tracer, "test_span") as span:
                # Check that we got the span
                assert span is mock_span
                
                # Raise an exception
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Check that the span was ended and marked with error
        mock_tracer.end_span.assert_called_once_with(mock_span)
        assert mock_span.status_code == "error"
        assert mock_span.status_message == "Test error"
        assert "exception.type" in mock_span.attributes
        assert mock_span.attributes["exception.type"] == "ValueError"
        assert "exception.message" in mock_span.attributes
        assert mock_span.attributes["exception.message"] == "Test error"


class TestSpanProcessor:
    """Tests for span processors."""
    
    @pytest.mark.asyncio
    async def test_logging_span_processor(self):
        """Test LoggingSpanProcessor."""
        # Create a mock logger
        mock_logger = MagicMock()
        
        # Create a processor
        processor = LoggingSpanProcessor(logger=mock_logger)
        
        # Create a span
        span = Span(
            name="test",
            trace_id="1234",
            span_id="5678",
            parent_span_id="9012",
            start_time=100.0,
            end_time=100.5
        )
        
        # Process the span
        await processor.on_end(span)
        
        # Check that the span was logged
        mock_logger.info.assert_called_once()
        args, kwargs = mock_logger.info.call_args
        
        # Check that the message includes span info
        message = args[0]
        assert "test" in message
        assert "1234" in message
        assert "5678" in message
        assert "9012" in message
        assert "500.0" in message  # Duration
        
        # Check that the span was included in extras
        assert "span" in kwargs["extra"]
        assert kwargs["extra"]["span"] == span.to_dict()
    
    @pytest.mark.asyncio
    async def test_batch_span_processor(self):
        """Test BatchSpanProcessor."""
        # Create a mock exporter
        mock_exporter = MagicMock(spec=SpanExporter)
        mock_exporter.export_spans = MagicMock()
        mock_exporter.shutdown = MagicMock()
        
        # Create a processor with small batch size
        processor = BatchSpanProcessor(
            exporter=mock_exporter,
            max_batch_size=2,
            export_interval=5.0
        )
        
        # Process spans
        span1 = Span(name="test1", trace_id="1", span_id="1")
        span2 = Span(name="test2", trace_id="2", span_id="2")
        span3 = Span(name="test3", trace_id="3", span_id="3")
        
        # Process first span
        await processor.on_end(span1)
        
        # No export should have happened yet
        mock_exporter.export_spans.assert_not_called()
        
        # Process second span (should trigger export)
        await processor.on_end(span2)
        
        # Wait a bit for the async task to run
        await asyncio.sleep(0.1)
        
        # Check that export was called with both spans
        mock_exporter.export_spans.assert_called_once()
        args, _ = mock_exporter.export_spans.call_args
        assert len(args[0]) == 2
        assert args[0][0] is span1
        assert args[0][1] is span2
        
        # Reset the mock
        mock_exporter.export_spans.reset_mock()
        
        # Process third span
        await processor.on_end(span3)
        
        # No export should have happened yet (need one more span)
        mock_exporter.export_spans.assert_not_called()
        
        # Shutdown the processor
        await processor.shutdown()
        
        # Export should have been called with the remaining span
        mock_exporter.export_spans.assert_called_once()
        args, _ = mock_exporter.export_spans.call_args
        assert len(args[0]) == 1
        assert args[0][0] is span3
        
        # Exporter should have been shut down
        mock_exporter.shutdown.assert_called_once()


class TestSpanExporter:
    """Tests for span exporters."""
    
    @pytest.mark.asyncio
    async def test_logging_span_exporter(self):
        """Test LoggingSpanExporter."""
        # Create a mock logger
        mock_logger = MagicMock()
        
        # Create an exporter
        exporter = LoggingSpanExporter(logger=mock_logger)
        
        # Create spans
        span1 = Span(name="test1", trace_id="1", span_id="1")
        span2 = Span(name="test2", trace_id="2", span_id="2")
        
        # Export the spans
        await exporter.export_spans([span1, span2])
        
        # Check that both spans were logged
        assert mock_logger.info.call_count == 2
        
        # Check that the spans were included in the logs
        for i, call_args in enumerate(mock_logger.info.call_args_list):
            args, kwargs = call_args
            assert f"test{i+1}" in args[0]
            assert "span" in kwargs["extra"]
            span_dict = kwargs["extra"]["span"]
            assert span_dict["name"] == f"test{i+1}"
            assert span_dict["trace_id"] == str(i+1)
            assert span_dict["span_id"] == str(i+1)


@pytest.fixture
def reset_tracer():
    """Reset the global tracer before and after tests."""
    from uno.core.tracing.framework import _tracer
    
    # Save original tracer
    original = _tracer
    
    # Reset to None
    _tracer = None
    
    yield
    
    # Restore original tracer
    from uno.core.tracing.framework import _tracer
    _tracer = original


class TestTracer:
    """Tests for Tracer."""
    
    @pytest.mark.asyncio
    async def test_start_span(self, reset_span_context):
        """Test starting a span."""
        # Create a tracer
        tracer = Tracer(TracingConfig(service_name="test-service"))
        
        # Start a span
        span = await tracer.start_span(
            name="test_span",
            attributes={"foo": "bar"},
            kind=SpanKind.CLIENT
        )
        
        # Check the span properties
        assert span.name == "test_span"
        assert span.attributes["foo"] == "bar"
        assert span.attributes["service.name"] == "test-service"
        assert span.attributes["service.environment"] == "development"
        assert span.kind == SpanKind.CLIENT
        
        # Start a child span
        from uno.core.tracing.framework import _current_span
        _current_span.set(span)
        
        child_span = await tracer.start_span(
            name="child_span",
            attributes={"child": "true"}
        )
        
        # Check the child span properties
        assert child_span.name == "child_span"
        assert child_span.trace_id == span.trace_id
        assert child_span.parent_span_id == span.span_id
        assert child_span.attributes["child"] == "true"
    
    @pytest.mark.asyncio
    async def test_disabled_tracer(self):
        """Test tracer with tracing disabled."""
        # Create a disabled tracer
        tracer = Tracer(TracingConfig(enabled=False))
        
        # Add a processor (should be skipped)
        processor = MagicMock(spec=SpanProcessor)
        tracer.add_processor(processor)
        
        # Start a span
        span = await tracer.start_span("test_span")
        
        # Should return a non-recording span
        assert span.name == "test_span"
        assert not span.attributes  # Empty attributes
        
        # End the span
        await tracer.end_span(span)
        
        # Processor should not have been called
        processor.on_start.assert_not_called()
        processor.on_end.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_span_processors(self):
        """Test span processors in tracer."""
        # Create a tracer
        tracer = Tracer(TracingConfig(service_name="test-service"))
        
        # Add processors
        processor1 = MagicMock(spec=SpanProcessor)
        processor2 = MagicMock(spec=SpanProcessor)
        
        tracer.add_processor(processor1)
        tracer.add_processor(processor2)
        
        # Start a span
        span = await tracer.start_span("test_span")
        
        # Check that processors were called
        processor1.on_start.assert_called_once_with(span)
        processor2.on_start.assert_called_once_with(span)
        
        # End the span
        await tracer.end_span(span)
        
        # Check that processors were called
        processor1.on_end.assert_called_once_with(span)
        processor2.on_end.assert_called_once_with(span)
    
    @pytest.mark.asyncio
    async def test_create_span(self):
        """Test creating a span context manager."""
        # Create a tracer
        tracer = Tracer(TracingConfig(service_name="test-service"))
        
        # Create a span context
        context = tracer.create_span(
            name="test_span",
            attributes={"foo": "bar"},
            kind=SpanKind.CLIENT
        )
        
        # Check the context
        assert isinstance(context, TracingContext)
        assert context.name == "test_span"
        assert context.attributes == {"foo": "bar"}
        assert context.kind == SpanKind.CLIENT
    
    @pytest.mark.asyncio
    async def test_custom_sampler(self):
        """Test custom sampling function."""
        # Create a tracer
        tracer = Tracer(TracingConfig(service_name="test-service"))
        
        # Define a custom sampler
        def custom_sampler(trace_id, parent_id, name):
            # Only sample spans with "important" in the name
            return "important" in name
        
        # Set the sampler
        tracer.set_sampler(custom_sampler)
        
        # Start spans
        important_span = await tracer.start_span("important_span")
        unimportant_span = await tracer.start_span("unimportant_span")
        
        # The important span should have attributes
        assert important_span.attributes != {}
        
        # The unimportant span should have no attributes (non-recording)
        assert unimportant_span.attributes == {}
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test shutting down the tracer."""
        # Create a tracer
        tracer = Tracer(TracingConfig(service_name="test-service"))
        
        # Add processors
        processor1 = MagicMock(spec=SpanProcessor)
        processor2 = MagicMock(spec=SpanProcessor)
        
        tracer.add_processor(processor1)
        tracer.add_processor(processor2)
        
        # Shut down the tracer
        await tracer.shutdown()
        
        # Check that processors were shut down
        processor1.shutdown.assert_called_once()
        processor2.shutdown.assert_called_once()


class TestGlobalTracer:
    """Tests for global tracer functions."""
    
    def test_get_tracer(self, reset_tracer):
        """Test getting the global tracer."""
        # Get the tracer
        tracer = get_tracer()
        
        # Should return a Tracer instance
        assert isinstance(tracer, Tracer)
        
        # Getting it again should return the same instance
        tracer2 = get_tracer()
        assert tracer2 is tracer
    
    def test_configure_tracing(self, reset_tracer):
        """Test configuring the global tracer."""
        # Configure tracing
        config = TracingConfig(
            service_name="test-service",
            environment="test",
            console_export=True
        )
        
        tracer = configure_tracing(config)
        
        # Should return a configured Tracer instance
        assert isinstance(tracer, Tracer)
        assert tracer.config is config
        assert tracer.config.service_name == "test-service"
        assert tracer.config.environment == "test"
        
        # Should have a logging processor if console_export is True
        assert any(isinstance(p, LoggingSpanProcessor) for p in tracer._processors)
        
        # Getting the tracer again should return the same instance
        tracer2 = get_tracer()
        assert tracer2 is tracer
        
        # Configure again with new config
        new_config = TracingConfig(service_name="new-service")
        new_tracer = configure_tracing(new_config)
        
        # Should update the existing tracer
        assert new_tracer is tracer
        assert tracer.config is new_config
        assert tracer.config.service_name == "new-service"


class TestTraceDecorator:
    """Tests for the trace decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function(self, reset_tracer, reset_span_context):
        """Test tracing an async function."""
        # Configure tracing
        tracer = configure_tracing(TracingConfig(
            service_name="test-service",
            include_all_attributes=True
        ))
        
        # Create a processor to track spans
        processor = MagicMock(spec=SpanProcessor)
        tracer.add_processor(processor)
        
        # Define a traced async function
        @trace(name="test_operation", attributes={"source": "test"})
        async def test_function(param1, param2=None):
            # Check that we have a current span
            assert get_current_span() is not None
            assert get_current_span().name == "test_operation"
            
            # Return a result
            return {"param1": param1, "param2": param2}
        
        # Call the function
        result = await test_function("value1", param2="value2")
        
        # Check the result
        assert result["param1"] == "value1"
        assert result["param2"] == "value2"
        
        # Check that a span was created and ended
        assert processor.on_start.call_count == 1
        assert processor.on_end.call_count == 1
        
        # Get the span that was created
        span = processor.on_start.call_args[0][0]
        
        # Check the span properties
        assert span.name == "test_operation"
        assert span.attributes["source"] == "test"
        assert span.attributes["arg.param1"] == "value1"
        assert span.attributes["arg.param2"] == "value2"
        assert "result" in span.attributes  # Result should be recorded
    
    def test_sync_function(self, reset_tracer, reset_span_context):
        """Test tracing a synchronous function."""
        # Configure tracing
        tracer = configure_tracing(TracingConfig(
            service_name="test-service",
            include_all_attributes=True
        ))
        
        # Create a processor to track spans
        processor = MagicMock(spec=SpanProcessor)
        tracer.add_processor(processor)
        
        # Define a traced sync function
        @trace()
        def test_function(param1, param2=None):
            # The current span should be set (through asyncio.run)
            current_span = get_current_span()
            assert current_span is not None
            assert current_span.name == "test_function"  # Use function name as default
            
            # Return a result
            return {"param1": param1, "param2": param2}
        
        # Call the function
        result = test_function("value1", param2="value2")
        
        # Check the result
        assert result["param1"] == "value1"
        assert result["param2"] == "value2"
        
        # Check that a span was created and ended
        assert processor.on_start.call_count == 1
        assert processor.on_end.call_count == 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, reset_tracer, reset_span_context):
        """Test error handling in traced functions."""
        # Configure tracing
        tracer = configure_tracing(TracingConfig(
            service_name="test-service",
            include_all_attributes=True
        ))
        
        # Create a processor to track spans
        processor = MagicMock(spec=SpanProcessor)
        tracer.add_processor(processor)
        
        # Define a traced function that raises an exception
        @trace()
        async def failing_function():
            raise ValueError("Test error")
        
        # Call the function (should raise)
        with pytest.raises(ValueError):
            await failing_function()
        
        # Check that a span was created and ended
        assert processor.on_start.call_count == 1
        assert processor.on_end.call_count == 1
        
        # Get the span that was created
        span = processor.on_start.call_args[0][0]
        
        # Check that the span was marked with error status
        assert span.status_code == "error"
        assert span.status_message == "Test error"
        assert span.attributes["exception.type"] == "ValueError"
        assert span.attributes["exception.message"] == "Test error"


class TestTracePropagation:
    """Tests for trace context propagation."""
    
    def test_inject_context(self, reset_span_context):
        """Test injecting trace context into headers."""
        # Create a span and set as current
        from uno.core.tracing.framework import _current_span
        
        span = Span(
            name="test",
            trace_id="1234",
            span_id="5678",
            parent_span_id="9012"
        )
        _current_span.set(span)
        
        # Inject context into headers
        headers = {}
        inject_context(headers)
        
        # Check that trace context was added
        assert "X-Trace-Context" in headers
        assert "X-Trace-ID" in headers
        assert headers["X-Trace-ID"] == "1234"
        
        # Decode the trace context
        context_b64 = headers["X-Trace-Context"]
        context_json = base64.b64decode(context_b64).decode()
        context_dict = json.loads(context_json)
        
        # Check the context
        assert context_dict["trace_id"] == "1234"
        assert context_dict["span_id"] == "5678"
        assert context_dict["parent_span_id"] == "9012"
    
    def test_extract_context(self):
        """Test extracting trace context from headers."""
        # Create context data
        context_dict = {
            "trace_id": "1234",
            "span_id": "5678",
            "parent_span_id": "9012",
            "sampled": True,
            "baggage": {"foo": "bar"}
        }
        
        # Encode as Base64
        context_json = json.dumps(context_dict)
        context_b64 = base64.b64encode(context_json.encode()).decode()
        
        # Add to headers
        headers = {"X-Trace-Context": context_b64}
        
        # Extract context
        context = extract_context(headers)
        
        # Check the context
        assert context is not None
        assert context.trace_id == "1234"
        assert context.span_id == "5678"
        assert context.parent_span_id == "9012"
        assert context.sampled is True
        assert context.baggage == {"foo": "bar"}
    
    def test_extract_context_from_trace_id(self):
        """Test extracting context from trace ID header."""
        # Add trace ID to headers
        headers = {"X-Trace-ID": "1234"}
        
        # Extract context
        context = extract_context(headers)
        
        # Check the context
        assert context is not None
        assert context.trace_id == "1234"
        assert context.span_id != "1234"  # Should generate a new span ID
        assert context.parent_span_id is None
    
    def test_extract_context_invalid(self):
        """Test extracting context with invalid data."""
        # Add invalid trace context to headers
        headers = {"X-Trace-Context": "invalid-base64-}"}
        
        # Extract context should return None
        context = extract_context(headers)
        assert context is None


class TestTracingMiddleware:
    """Tests for TracingMiddleware."""
    
    @pytest.mark.asyncio
    async def test_middleware(self, reset_tracer, reset_span_context):
        """Test tracing middleware."""
        # Configure tracing
        tracer = configure_tracing(TracingConfig(
            service_name="test-service"
        ))
        
        # Create a processor to track spans
        processor = MagicMock(spec=SpanProcessor)
        tracer.add_processor(processor)
        
        # Create app and middleware
        app = FastAPI()
        middleware = TracingMiddleware(app, tracer=tracer)
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.url.scheme = "https"
        mock_request.url.hostname = "example.com"
        mock_request.scope = {"http_version": "1.1"}
        mock_request.client = MagicMock(host="127.0.0.1", port=12345)
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        # Create mock call_next function
        async def mock_call_next(request):
            # Check that a span was created
            assert get_current_span() is not None
            return mock_response
        
        # Process the request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that a span was created and ended
        assert processor.on_start.call_count == 1
        assert processor.on_end.call_count == 1
        
        # Get the span that was created
        span = processor.on_start.call_args[0][0]
        
        # Check the span properties
        assert span.name == "GET /api/test"
        assert span.kind == SpanKind.SERVER
        assert span.attributes["http.method"] == "GET"
        assert span.attributes["http.path"] == "/api/test"
        
        # Check that trace ID was added to response headers
        assert "X-Trace-ID" in mock_response.headers
        assert mock_response.headers["X-Trace-ID"] == span.trace_id
    
    @pytest.mark.asyncio
    async def test_middleware_excluded_path(self, reset_tracer):
        """Test middleware skipping excluded paths."""
        # Configure tracing
        tracer = configure_tracing(TracingConfig(
            service_name="test-service"
        ))
        
        # Create a processor to track spans
        processor = MagicMock(spec=SpanProcessor)
        tracer.add_processor(processor)
        
        # Create app and middleware
        app = FastAPI()
        middleware = TracingMiddleware(app, tracer=tracer, excluded_paths=["/health"])
        
        # Create mock request for excluded path
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.method = "GET"
        mock_request.headers = {}
        
        # Create mock response
        mock_response = MagicMock()
        
        # Create mock call_next function
        async def mock_call_next(request):
            return mock_response
        
        # Process the request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # No span should have been created
        processor.on_start.assert_not_called()
        
        # Should return the response directly
        assert response is mock_response
    
    @pytest.mark.asyncio
    async def test_middleware_trace_propagation(self, reset_tracer, reset_span_context):
        """Test middleware propagates trace context."""
        # Configure tracing
        tracer = configure_tracing(TracingConfig(
            service_name="test-service"
        ))
        
        # Create a processor to track spans
        processor = MagicMock(spec=SpanProcessor)
        tracer.add_processor(processor)
        
        # Create app and middleware
        app = FastAPI()
        middleware = TracingMiddleware(app, tracer=tracer)
        
        # Create trace context
        trace_id = "1234"
        span_id = "5678"
        
        # Create propagation context
        prop_context = PropagationContext(
            trace_id=trace_id,
            span_id=span_id
        )
        
        # Encode as Base64
        context_json = json.dumps(prop_context.to_dict())
        context_b64 = base64.b64encode(context_json.encode()).decode()
        
        # Create mock request with trace context
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {"X-Trace-Context": context_b64}
        mock_request.url.scheme = "https"
        mock_request.url.hostname = "example.com"
        mock_request.scope = {"http_version": "1.1"}
        mock_request.client = MagicMock(host="127.0.0.1", port=12345)
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        # Create mock call_next function
        async def mock_call_next(request):
            # Check that a span was created with the propagated trace ID
            current_span = get_current_span()
            assert current_span is not None
            assert current_span.trace_id == trace_id
            return mock_response
        
        # Process the request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that trace ID was added to response headers
        assert "X-Trace-ID" in mock_response.headers
        assert mock_response.headers["X-Trace-ID"] == trace_id