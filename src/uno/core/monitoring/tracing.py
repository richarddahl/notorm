# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Distributed tracing for the Uno application.

This module provides utilities for distributed tracing, allowing tracking of
requests across multiple services and components.
"""

from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic, Union, Set
import asyncio
import time
import logging
import functools
import uuid
import json
import base64
import contextlib
import contextvars
import inspect
from enum import Enum
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.errors import get_error_context, add_error_context, with_error_context


# Type variables
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class SpanKind(Enum):
    """Type of span in a trace."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class PropagationContext:
    """Context for propagating trace information across service boundaries."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    sampled: bool = True
    baggage: Dict[str, str] = field(default_factory=dict)


@dataclass
class Span:
    """
    A single operation within a trace.

    A span represents a unit of work or operation. It tracks the operation
    timing, and relationship to other spans.
    """

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    kind: SpanKind = SpanKind.INTERNAL
    status_code: str = "ok"
    status_message: str | None = None

    @property
    def duration(self) -> float:
        """Get the span duration in milliseconds."""
        if self.end_time is None:
            return 0
        return (self.end_time - self.start_time) * 1000

    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """
        Add an event to the span.

        Args:
            name: Name of the event
            attributes: Attributes for the event
            timestamp: Timestamp for the event (defaults to now)
        """
        self.events.append(
            {
                "name": name,
                "attributes": attributes or {},
                "timestamp": timestamp or time.time(),
            }
        )

    def set_status(self, code: str, message: str | None = None) -> None:
        """
        Set the status of the span.

        Args:
            code: Status code (ok, error)
            message: Status message
        """
        self.status_code = code
        self.status_message = message

    def finish(self, end_time: Optional[float] = None) -> None:
        """
        Mark the span as finished.

        Args:
            end_time: End time for the span (defaults to now)
        """
        self.end_time = end_time or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the span to a dictionary.

        Returns:
            Dictionary representation of the span
        """
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration,
            "attributes": self.attributes,
            "events": self.events,
            "kind": self.kind.value,
            "status": {"code": self.status_code, "message": self.status_message},
        }


# Context variable for tracking the current span
_current_span = contextvars.ContextVar[Optional[Span]]("current_span", default=None)


class TracingContext:
    """
    Context manager for tracing.

    This context manager creates a span and sets it as the current span
    for the duration of the context.
    """

    def __init__(
        self,
        tracer: "Tracer",
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ):
        """
        Initialize a tracing context.

        Args:
            tracer: The tracer to use
            name: Name of the span
            attributes: Attributes for the span
            kind: Kind of span
        """
        self.tracer = tracer
        self.name = name
        self.attributes = attributes or {}
        self.kind = kind
        self.span: Optional[Span] = None
        self.token: Optional[contextvars.Token] = None

    async def __aenter__(self) -> Span:
        """Start the span and set it as the current span."""
        self.span = await self.tracer.start_span(
            name=self.name, attributes=self.attributes, kind=self.kind
        )
        self.token = _current_span.set(self.span)
        return self.span

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Finish the span and restore the previous current span."""
        if self.span:
            # Set status based on exception
            if exc_type:
                self.span.set_status("error", str(exc_value))
                if hasattr(exc_value, "__dict__"):
                    # Add exception details as attributes
                    for key, value in exc_value.__dict__.items():
                        if isinstance(value, (str, int, float, bool, type(None))):
                            self.span.attributes[f"exception.{key}"] = value

            # Finish the span
            await self.tracer.end_span(self.span)

        # Restore the previous current span
        if self.token:
            _current_span.reset(self.token)


def get_current_span() -> Optional[Span]:
    """
    Get the current span from the context.

    Returns:
        The current span, or None if no span is active
    """
    return _current_span.get()


def get_current_trace_id() -> Optional[str]:
    """
    Get the current trace ID from the context.

    Returns:
        The current trace ID, or None if no span is active
    """
    span = get_current_span()
    return span.trace_id if span else None


def get_current_span_id() -> Optional[str]:
    """
    Get the current span ID from the context.

    Returns:
        The current span ID, or None if no span is active
    """
    span = get_current_span()
    return span.span_id if span else None


class SpanProcessor:
    """
    Interface for processing spans.

    Span processors are called when spans are started and ended,
    allowing for exporting spans to observability systems.
    """

    async def on_start(self, span: Span) -> None:
        """
        Process a span when it starts.

        Args:
            span: The span that started
        """
        pass

    async def on_end(self, span: Span) -> None:
        """
        Process a span when it ends.

        Args:
            span: The span that ended
        """
        pass

    async def shutdown(self) -> None:
        """Shut down the span processor."""
        pass


class LoggingSpanProcessor(SpanProcessor):
    """
    Span processor that logs spans.

    This processor logs spans when they end, useful for debugging.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the logging span processor.

        Args:
            logger: Logger to use
        """
        self.logger = logger or logging.getLogger(__name__)

    async def on_end(self, span: Span) -> None:
        """
        Log a span when it ends.

        Args:
            span: The span that ended
        """
        self.logger.info(
            f"Span {span.name} ended: trace_id={span.trace_id}, "
            f"span_id={span.span_id}, parent_span_id={span.parent_span_id}, "
            f"duration={span.duration:.2f}ms"
        )


class BatchSpanProcessor(SpanProcessor):
    """
    Span processor that batches spans for export.

    This processor collects spans and exports them in batches.
    """

    def __init__(
        self,
        exporter: "SpanExporter",
        max_batch_size: int = 100,
        export_interval: float = 5.0,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the batch span processor.

        Args:
            exporter: Exporter to use for spans
            max_batch_size: Maximum number of spans per batch
            export_interval: Interval in seconds between exports
            logger: Logger to use
        """
        self.exporter = exporter
        self.max_batch_size = max_batch_size
        self.export_interval = export_interval
        self.logger = logger or logging.getLogger(__name__)
        self._spans: list[Span] = []
        self._lock = asyncio.Lock()
        self._export_task: Optional[asyncio.Task] = None
        self._shutting_down = False

    async def start(self) -> None:
        """Start the batch processor."""
        if not self._export_task:
            self._export_task = asyncio.create_task(
                self._export_loop(), name="span_export"
            )

    async def on_end(self, span: Span) -> None:
        """
        Process a span when it ends.

        Args:
            span: The span that ended
        """
        async with self._lock:
            self._spans.append(span)

            # Export immediately if we've reached the batch size
            if len(self._spans) >= self.max_batch_size:
                asyncio.create_task(self._export_batch())

    async def _export_loop(self) -> None:
        """Background task for exporting spans at regular intervals."""
        try:
            while not self._shutting_down:
                # Wait for the export interval
                await asyncio.sleep(self.export_interval)

                # Export any spans
                await self._export_batch()

        except asyncio.CancelledError:
            # Expected during shutdown
            pass

        except Exception as e:
            self.logger.error(f"Error in span export loop: {str(e)}", exc_info=True)

    async def _export_batch(self) -> None:
        """Export a batch of spans."""
        spans_to_export = []

        async with self._lock:
            if not self._spans:
                return

            # Get spans to export
            spans_to_export = self._spans
            self._spans = []

        if spans_to_export:
            try:
                await self.exporter.export_spans(spans_to_export)
            except Exception as e:
                self.logger.error(f"Error exporting spans: {str(e)}", exc_info=True)

    async def shutdown(self) -> None:
        """
        Shut down the span processor.

        This exports any remaining spans and stops the export task.
        """
        self._shutting_down = True

        if self._export_task and not self._export_task.done():
            # Cancel the export task
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass

        # Export any remaining spans
        await self._export_batch()

        # Shut down the exporter
        await self.exporter.shutdown()


class SpanExporter:
    """
    Interface for exporting spans.

    Span exporters send spans to an observability system for analysis.
    """

    async def export_spans(self, spans: list[Span]) -> None:
        """
        Export spans to the observability system.

        Args:
            spans: Spans to export
        """
        pass

    async def shutdown(self) -> None:
        """Shut down the exporter."""
        pass


class LoggingSpanExporter(SpanExporter):
    """
    Span exporter that logs spans.

    This exporter logs spans for debugging purposes.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the logging span exporter.

        Args:
            logger: Logger to use
        """
        self.logger = logger or logging.getLogger(__name__)

    async def export_spans(self, spans: list[Span]) -> None:
        """
        Export spans by logging them.

        Args:
            spans: Spans to export
        """
        for span in spans:
            span_dict = span.to_dict()
            self.logger.info(f"Span: {json.dumps(span_dict)}")


class Tracer:
    """
    Tracer for managing spans.

    This class creates and manages spans within traces.
    """

    def __init__(
        self,
        service_name: str,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the tracer.

        Args:
            service_name: Name of the service
            logger: Logger to use
        """
        self.service_name = service_name
        self.logger = logger or logging.getLogger(__name__)
        self._processors: list[SpanProcessor] = []
        self._sampler_func: Callable[[str, Optional[str], str], bool] = (
            lambda trace_id, parent_id, name: True
        )

    async def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        links: Optional[list[dict[str, Any]]] = None,
    ) -> Span:
        """
        Start a new span.

        Args:
            name: Name of the span
            attributes: Attributes for the span
            kind: Kind of span
            links: Links to other spans

        Returns:
            The new span
        """
        # Get the current span to use as parent
        current = get_current_span()

        # Generate trace and span IDs
        trace_id = current.trace_id if current else str(uuid.uuid4())
        parent_id = current.span_id if current else None
        span_id = str(uuid.uuid4())

        # Check if we should sample this span
        if not self._sampler_func(trace_id, parent_id, name):
            # Create a non-recording span
            return Span(
                name=name,
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_id,
                attributes={},
                kind=kind,
            )

        # Create span attributes
        span_attributes = {
            "service.name": self.service_name,
        }

        # Add custom attributes
        if attributes:
            span_attributes.update(attributes)

        # Add error context
        error_context = get_error_context()
        if error_context:
            for key, value in error_context.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    span_attributes[f"error_context.{key}"] = value

        # Create the span
        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_id,
            attributes=span_attributes,
            kind=kind,
        )

        # Add links
        if links:
            for link in links:
                span.attributes[f"link.{link['trace_id']}.{link['span_id']}"] = (
                    link.get("attributes", {})
                )

        # Notify processors
        for processor in self._processors:
            try:
                await processor.on_start(span)
            except Exception as e:
                self.logger.error(f"Error in span processor: {str(e)}", exc_info=True)

        return span

    async def end_span(self, span: Span) -> None:
        """
        End a span.

        Args:
            span: The span to end
        """
        if span.end_time is None:
            span.finish()

        # Notify processors
        for processor in self._processors:
            try:
                await processor.on_end(span)
            except Exception as e:
                self.logger.error(f"Error in span processor: {str(e)}", exc_info=True)

    async def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ) -> TracingContext:
        """
        Create a span context manager.

        Args:
            name: Name of the span
            attributes: Attributes for the span
            kind: Kind of span

        Returns:
            A context manager that creates and manages the span
        """
        return TracingContext(self, name, attributes, kind)

    def add_processor(self, processor: SpanProcessor) -> None:
        """
        Add a span processor.

        Args:
            processor: The processor to add
        """
        self._processors.append(processor)

    def set_sampler(self, sampler: Callable[[str, Optional[str], str], bool]) -> None:
        """
        Set the sampling function.

        Args:
            sampler: Function that decides if a span should be sampled
        """
        self._sampler_func = sampler

    async def shutdown(self) -> None:
        """
        Shut down the tracer.

        This shuts down all span processors.
        """
        for processor in self._processors:
            try:
                await processor.shutdown()
            except Exception as e:
                self.logger.error(
                    f"Error shutting down span processor: {str(e)}", exc_info=True
                )


# Global tracer
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """
    Get the global tracer.

    Returns:
        The global tracer
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name="uno")
    return _tracer


def trace(
    name: str | None = None,
    attributes: Optional[Dict[str, Any]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> Callable[[F], F]:
    """
    Decorator for tracing functions.

    Args:
        name: Name of the span (defaults to function name)
        attributes: Attributes for the span
        kind: Kind of span

    Returns:
        A decorator that traces the function
    """

    def decorator(func: F) -> F:
        span_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()

            # Create span attributes from function args
            span_attributes = {}
            if attributes:
                span_attributes.update(attributes)

            # Add function arguments to attributes (safely)
            try:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()

                for param_name, param_value in bound.arguments.items():
                    # Skip 'self' and 'cls'
                    if param_name in ("self", "cls"):
                        continue

                    # Only include simple types
                    if isinstance(param_value, (str, int, float, bool, type(None))):
                        span_attributes[f"arg.{param_name}"] = param_value
                    else:
                        span_attributes[f"arg.{param_name}.type"] = type(
                            param_value
                        ).__name__
            except Exception:
                # Ignore errors in argument processing
                pass

            # Create and execute span
            async with await tracer.create_span(
                name=span_name, attributes=span_attributes, kind=kind
            ) as span:
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we'll need to run the async code in an event loop
            return asyncio.run(async_wrapper(*args, **kwargs))

        # Choose the right wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def inject_context(headers: Dict[str, str]) -> None:
    """
    Inject tracing context into headers.

    This is used when making HTTP requests to propagate trace context.

    Args:
        headers: HTTP headers to inject context into
    """
    span = get_current_span()
    if not span:
        return

    # Create propagation context
    context = PropagationContext(trace_id=span.trace_id, span_id=span.span_id)

    # Encode as Base64
    context_json = json.dumps(
        {
            "trace_id": context.trace_id,
            "span_id": context.span_id,
            "parent_span_id": context.parent_span_id,
            "sampled": context.sampled,
            "baggage": context.baggage,
        }
    )
    context_b64 = base64.b64encode(context_json.encode()).decode()

    # Add to headers
    headers["X-Trace-Context"] = context_b64


def extract_context(headers: Dict[str, str]) -> Optional[PropagationContext]:
    """
    Extract tracing context from headers.

    This is used when receiving HTTP requests to continue traces.

    Args:
        headers: HTTP headers to extract context from

    Returns:
        The extracted propagation context, or None if not found
    """
    context_b64 = headers.get("X-Trace-Context")
    if not context_b64:
        return None

    try:
        # Decode from Base64
        context_json = base64.b64decode(context_b64).decode()
        context_dict = json.loads(context_json)

        # Create propagation context
        return PropagationContext(
            trace_id=context_dict["trace_id"],
            span_id=context_dict["span_id"],
            parent_span_id=context_dict.get("parent_span_id"),
            sampled=context_dict.get("sampled", True),
            baggage=context_dict.get("baggage", {}),
        )

    except Exception:
        # Invalid context
        return None


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling distributed tracing in HTTP requests.

    This middleware creates spans for HTTP requests and propagates
    trace context between services.
    """

    def __init__(
        self,
        app: FastAPI,
        tracer: Optional[Tracer] = None,
        excluded_paths: list[str] | None = None,
    ):
        """
        Initialize the tracing middleware.

        Args:
            app: FastAPI application
            tracer: Tracer to use
            excluded_paths: Paths to exclude from tracing
        """
        super().__init__(app)
        self.tracer = tracer or get_tracer()
        self.excluded_paths = excluded_paths or []

    @with_error_context
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """
        Process a request and create a span.

        Args:
            request: The HTTP request
            call_next: Function to call the next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip tracing for excluded paths
        path = request.url.path
        if path in self.excluded_paths:
            return await call_next(request)

        # Extract context from headers
        headers = dict(request.headers)
        context = extract_context(headers)

        # Create span attributes
        attributes = {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.path": path,
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname or "",
            "http.target": request.url.path,
            "http.flavor": request.scope.get("http_version", ""),
            "http.user_agent": request.headers.get("user-agent", ""),
            "http.request_content_length": request.headers.get("content-length", "0"),
            "net.peer.ip": request.client.host if request.client else "",
            "net.peer.port": request.client.port if request.client else "",
        }

        # Start a span for this request
        span_context = None
        if context:
            # Create a span with extracted context
            current_span = Span(
                name=f"{request.method} {path}",
                trace_id=context.trace_id,
                span_id=context.span_id,
                parent_span_id=context.parent_span_id,
                attributes=attributes,
                kind=SpanKind.SERVER,
            )

            # Set the current span
            token = _current_span.set(current_span)

            # Create a new span for the request handling (child of the extracted span)
            span_context = await self.tracer.create_span(
                name=f"handle {request.method} {path}",
                attributes=attributes,
                kind=SpanKind.INTERNAL,
            )
        else:
            # Create a new span for the request
            span_context = await self.tracer.create_span(
                name=f"{request.method} {path}",
                attributes=attributes,
                kind=SpanKind.SERVER,
            )

        # Process the request with the span
        try:
            async with span_context as span:
                # Add request ID to attributes (also available as trace ID)
                request_id = span.trace_id

                # Add context for error handling
                add_error_context(
                    request_id=request_id, path=path, method=request.method
                )

                # Process the request
                response = await call_next(request)

                # Add response attributes
                span.attributes["http.status_code"] = response.status_code
                span.attributes["http.response_content_length"] = response.headers.get(
                    "content-length", "0"
                )

                # Set span status based on response
                if response.status_code >= 400:
                    span.set_status("error", f"HTTP {response.status_code}")

                # Add trace ID to response headers
                response.headers["X-Trace-ID"] = request_id

                return response
        except Exception as e:
            # Handle exceptions
            span.set_status("error", str(e))
            raise
        finally:
            # Reset context if we extracted it
            if context and token:
                _current_span.reset(token)
