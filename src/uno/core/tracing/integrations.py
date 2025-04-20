# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integrations for the distributed tracing framework.

This module provides integration points between the tracing framework and
other components of the UNO system, such as logging, metrics, and error handling.
"""

import asyncio
import functools
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Union, TypeVar, cast

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.logging.framework import (
    get_logger,
    LogConfig,
    add_context as add_logging_context,
)
from uno.core.metrics.framework import (
    timed,
    MetricsMiddleware,
    get_metrics_registry,
    MetricsConfig,
)
from uno.core.errors.framework import ErrorContext, add_error_context

from .framework import (
    Tracer,
    Span,
    SpanKind,
    TracingConfig,
    TracingMiddleware,
    get_tracer,
    get_current_span,
    get_current_trace_id,
    PropagationContext,
    extract_context,
)

# Type variables
F = TypeVar("F", bound=Callable[..., Any])


def register_logging_integration(tracer: Optional[Tracer] = None) -> None:
    """
    Register integration between tracing and logging.

    This sets up logging to include trace context in log messages.

    Args:
        tracer: Tracer to integrate with (defaults to global tracer)
    """
    tracer = tracer or get_tracer()
    logger = get_logger("uno.tracing.integrations")

    # Create a span processor that adds trace context to logs
    class LoggingIntegrationProcessor:
        """
        Span processor that adds trace context to log messages.

        This processor ensures trace IDs are included in log messages.
        """

        async def on_start(self, span: Span) -> None:
            """
            Process a span when it starts.

            Adds trace context to the logging context.

            Args:
                span: The span that started
            """
            # Add trace context to logging
            add_logging_context(
                trace_id=span.trace_id,
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
            )

    # Register the processor with the tracer
    tracer.add_processor(LoggingIntegrationProcessor())
    logger.info("Registered logging integration for tracing")


def register_metrics_integration(tracer: Optional[Tracer] = None) -> None:
    """
    Register integration between tracing and metrics.

    This sets up metrics collection for traces and spans.

    Args:
        tracer: Tracer to integrate with (defaults to global tracer)
    """
    tracer = tracer or get_tracer()
    logger = get_logger("uno.tracing.integrations")
    metrics_registry = get_metrics_registry()

    # Create a span processor that records metrics
    class MetricsIntegrationProcessor:
        """
        Span processor that records metrics for spans.

        This processor tracks span counts, duration, and error rates.
        """

        def __init__(self):
            """Initialize metrics."""
            # Create task to initialize metrics
            self._setup_task = asyncio.create_task(self._setup_metrics())

        async def _setup_metrics(self):
            """Set up metrics for tracking spans."""
            self.span_counter = await metrics_registry.get_or_create_counter(
                name="tracing.spans.count", description="Number of spans created"
            )

            self.span_duration = await metrics_registry.get_or_create_histogram(
                name="tracing.spans.duration",
                description="Duration of spans in milliseconds",
                unit="ms",
            )

            self.span_error_counter = await metrics_registry.get_or_create_counter(
                name="tracing.spans.errors", description="Number of spans with errors"
            )

        async def on_start(self, span: Span) -> None:
            """
            Process a span when it starts.

            Args:
                span: The span that started
            """
            # Increment span counter
            await self.span_counter.increment()

        async def on_end(self, span: Span) -> None:
            """
            Process a span when it ends.

            Args:
                span: The span that ended
            """
            # Record span duration
            await self.span_duration.observe(span.duration)

            # Record errors
            if span.status_code == "error":
                await self.span_error_counter.increment()

    # Register the processor with the tracer
    tracer.add_processor(MetricsIntegrationProcessor())
    logger.info("Registered metrics integration for tracing")


def register_error_integration(tracer: Optional[Tracer] = None) -> None:
    """
    Register integration between tracing and error handling.

    This sets up error context to include trace information.

    Args:
        tracer: Tracer to integrate with (defaults to global tracer)
    """
    tracer = tracer or get_tracer()
    logger = get_logger("uno.tracing.integrations")

    # Create a span processor that adds trace context to error context
    class ErrorIntegrationProcessor:
        """
        Span processor that adds trace context to error context.

        This processor ensures errors include trace information.
        """

        async def on_start(self, span: Span) -> None:
            """
            Process a span when it starts.

            Adds trace context to the error context.

            Args:
                span: The span that started
            """
            # Add trace context to error context
            add_error_context(trace_id=span.trace_id, span_id=span.span_id)

    # Register the processor with the tracer
    tracer.add_processor(ErrorIntegrationProcessor())
    logger.info("Registered error integration for tracing")


def create_request_middleware(
    app: FastAPI,
    tracer: Optional[Tracer] = None,
    excluded_paths: list[str] | None = None,
) -> BaseHTTPMiddleware:
    """
    Create middleware for HTTP request tracing.

    This middleware traces HTTP requests and adds trace context to responses.

    Args:
        app: FastAPI application
        tracer: Tracer to use (defaults to global tracer)
        excluded_paths: Paths to exclude from tracing

    Returns:
        Tracing middleware
    """
    tracer = tracer or get_tracer()

    # Create and configure the middleware
    middleware = TracingMiddleware(app, tracer=tracer, excluded_paths=excluded_paths)

    return middleware


def create_database_integration(
    tracer: Optional[Tracer] = None,
) -> Callable[[F], F]:
    """
    Create integration for database operations.

    This decorator traces database operations and adds context information.

    Args:
        tracer: Tracer to use (defaults to global tracer)

    Returns:
        Decorator for database operations
    """
    tracer = tracer or get_tracer()

    def decorator(func: F) -> F:
        """
        Decorator for tracing database operations.

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip if tracing is disabled
            if not tracer.config.enabled:
                return await func(*args, **kwargs)

            # Create span attributes
            attributes = {
                "db.type": "postgresql",
                "db.operation": func.__name__,
            }

            # Get query from function arguments (safely)
            for arg_name, arg_value in kwargs.items():
                if arg_name in ["query", "statement", "sql"]:
                    if isinstance(arg_value, str):
                        attributes["db.statement"] = arg_value[
                            :1000
                        ]  # Truncate long queries

            # Get database name from args if possible
            if hasattr(args[0], "database"):
                attributes["db.name"] = getattr(args[0], "database")

            # Create and execute span
            async with tracer.create_span(
                name=f"db.operation.{func.__name__}",
                attributes=attributes,
                kind=SpanKind.CLIENT,
            ) as span:
                try:
                    # Execute the database operation
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    end_time = time.time()

                    # Record row count if available
                    if hasattr(result, "rowcount"):
                        span.attributes["db.result.rows"] = result.rowcount
                    elif hasattr(result, "__len__"):
                        try:
                            span.attributes["db.result.rows"] = len(result)
                        except (TypeError, ValueError):
                            pass

                    # Record execution time
                    span.attributes["db.execution_time_ms"] = (
                        end_time - start_time
                    ) * 1000

                    return result
                except Exception as e:
                    # Record error details
                    span.set_status("error", str(e))
                    span.attributes["db.error.type"] = type(e).__name__
                    span.attributes["db.error.message"] = str(e)

                    # Re-raise the exception
                    raise

        # For non-async functions (unlikely for database operations)
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip if tracing is disabled
            if not tracer.config.enabled:
                return func(*args, **kwargs)

            # Run in an event loop
            return asyncio.run(async_wrapper(*args, **kwargs))

        # Choose the appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
