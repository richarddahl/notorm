# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Monitoring and observability framework for the Uno application.

This module provides a comprehensive monitoring and observability system,
including metrics collection, distributed tracing, and structured logging.
"""

from uno.core.monitoring.metrics import (
    MetricsRegistry,
    Counter,
    Gauge,
    Histogram,
    Timer,
    MetricsExporter,
    PrometheusExporter,
    MetricsMiddleware,
    metrics_registry,
    get_metrics_registry,
    counter,
    gauge,
    histogram,
    timer,
)

from uno.core.monitoring.tracing import (
    TracingContext,
    Span,
    Tracer,
    trace,
    get_current_trace_id,
    get_current_span_id,
    get_tracer,
    TracingMiddleware,
    PropagationContext,
    extract_context,
    inject_context,
)

from uno.core.monitoring.health import (
    HealthStatus,
    HealthCheck,
    HealthRegistry,
    HealthCheckResult,
    health_registry,
    get_health_registry,
    register_health_check,
    get_health_status,
    HealthEndpoint,
)

from uno.core.monitoring.events import (
    EventLogger,
    EventContext,
    EventLevel,
    EventType,
    event_logger,
    get_event_logger,
    log_event,
    EventFilter,
    EventHandler,
)

from uno.core.monitoring.config import (
    MonitoringConfig,
    TracingConfig,
    MetricsConfig,
    LoggingConfig,
    monitoring_config,
    configure_monitoring,
)

from uno.core.monitoring.integration import (
    setup_monitoring,
    create_monitoring_endpoints,
    MonitoringMiddleware,
)

__all__ = [
    # Metrics
    "MetricsRegistry",
    "Counter",
    "Gauge",
    "Histogram",
    "Timer",
    "MetricsExporter",
    "PrometheusExporter",
    "MetricsMiddleware",
    "metrics_registry",
    "get_metrics_registry",
    "counter",
    "gauge",
    "histogram",
    "timer",
    
    # Tracing
    "TracingContext",
    "Span",
    "Tracer",
    "trace",
    "get_current_trace_id",
    "get_current_span_id",
    "get_tracer",
    "TracingMiddleware",
    "PropagationContext",
    "extract_context",
    "inject_context",
    
    # Health
    "HealthStatus",
    "HealthCheck",
    "HealthRegistry",
    "HealthCheckResult",
    "health_registry",
    "get_health_registry",
    "register_health_check",
    "get_health_status",
    "HealthEndpoint",
    
    # Events
    "EventLogger",
    "EventContext",
    "EventLevel",
    "EventType",
    "event_logger",
    "get_event_logger",
    "log_event",
    "EventFilter",
    "EventHandler",
    
    # Configuration
    "MonitoringConfig",
    "TracingConfig",
    "MetricsConfig",
    "LoggingConfig",
    "monitoring_config",
    "configure_monitoring",
    
    # Integration
    "setup_monitoring",
    "create_monitoring_endpoints",
    "MonitoringMiddleware",
]