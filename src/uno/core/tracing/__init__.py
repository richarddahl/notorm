# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Distributed tracing framework for the Uno application.

This module provides a comprehensive distributed tracing system with integration
with the logging and metrics frameworks, enabling end-to-end visibility of
request flows across services and components.
"""

from .framework import (
    Tracer,
    Span,
    SpanKind,
    TracingContext,
    SpanProcessor,
    SpanExporter,
    PropagationContext,
    BatchSpanProcessor,
    LoggingSpanProcessor,
    LoggingSpanExporter,
    TracingConfig,
    configure_tracing,
    get_tracer,
    get_current_span,
    get_current_trace_id,
    get_current_span_id,
    trace,
    inject_context,
    extract_context,
    TracingMiddleware,
)

from .integrations import (
    register_logging_integration,
    register_metrics_integration,
    register_error_integration,
    create_request_middleware,
    create_database_integration,
)

__all__ = [
    # Core tracing
    "Tracer",
    "Span",
    "SpanKind",
    "TracingContext",
    "SpanProcessor",
    "SpanExporter",
    "PropagationContext",
    "BatchSpanProcessor",
    "LoggingSpanProcessor",
    "LoggingSpanExporter",
    "TracingConfig",
    "configure_tracing",
    "get_tracer",
    "get_current_span",
    "get_current_trace_id",
    "get_current_span_id",
    "trace",
    "inject_context",
    "extract_context",
    "TracingMiddleware",
    
    # Integrations
    "register_logging_integration",
    "register_metrics_integration",
    "register_error_integration",
    "create_request_middleware",
    "create_database_integration",
]