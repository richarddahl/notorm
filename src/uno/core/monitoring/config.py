# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Configuration for the monitoring and observability framework.

This module provides configuration objects and utilities for
configuring the monitoring and observability framework.
"""

from typing import Dict, List, Any, Optional, Set, Union
import logging
from dataclasses import dataclass, field

from uno.core.monitoring.metrics import MetricUnit
from uno.core.monitoring.events import EventLevel
from uno.core.monitoring.tracing import SpanKind


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""

    enabled: bool = True
    export_interval: float = 60.0
    prometheus_enabled: bool = True
    metrics_path: str = "/metrics"
    default_labels: Dict[str, str] = field(default_factory=dict)
    excluded_paths: list[str] = field(default_factory=list)
    histogram_buckets: Dict[str, list[float]] = field(default_factory=dict)

    def __post_init__(self):
        """Set default values."""
        if not self.excluded_paths:
            self.excluded_paths = ["/metrics", "/health"]

        if not self.default_labels:
            self.default_labels = {"service": "uno"}


@dataclass
class TracingConfig:
    """Configuration for distributed tracing."""

    enabled: bool = True
    service_name: str = "uno"
    sampling_rate: float = 1.0
    log_spans: bool = False
    excluded_paths: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Set default values."""
        if not self.excluded_paths:
            self.excluded_paths = ["/metrics", "/health"]


@dataclass
class LoggingConfig:
    """Configuration for structured logging."""

    level: str = "INFO"
    json_format: bool = True
    log_to_console: bool = True
    log_to_file: bool = False
    log_file_path: str | None = None
    include_context: bool = True
    include_trace_info: bool = True


@dataclass
class HealthConfig:
    """Configuration for health checking."""

    enabled: bool = True
    include_details: bool = True
    path_prefix: str = "/health"
    tags: list[str] = field(default_factory=lambda: ["health"])
    register_resource_checks: bool = True


@dataclass
class EventsConfig:
    """Configuration for event logging."""

    enabled: bool = True
    min_level: str = "INFO"
    log_events: bool = True
    audit_trail_enabled: bool = True


@dataclass
class MonitoringConfig:
    """
    Configuration for the monitoring and observability framework.

    This class provides a central configuration for all monitoring
    components.
    """

    service_name: str = "uno"
    environment: str = "development"
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    events: EventsConfig = field(default_factory=EventsConfig)

    def __post_init__(self):
        """Update service name and validate."""
        # Update service name in sub-configs
        self.metrics.default_labels["service"] = self.service_name
        self.tracing.service_name = self.service_name

        # Add environment to metric labels
        self.metrics.default_labels["environment"] = self.environment


# Global monitoring configuration
monitoring_config: Optional[MonitoringConfig] = None


def get_monitoring_config() -> MonitoringConfig:
    """
    Get the global monitoring configuration.

    Returns:
        The global monitoring configuration
    """
    global monitoring_config
    if monitoring_config is None:
        monitoring_config = MonitoringConfig()
    return monitoring_config


def configure_monitoring(config: MonitoringConfig) -> None:
    """
    Configure the monitoring framework.

    Args:
        config: Monitoring configuration
    """
    global monitoring_config
    monitoring_config = config

    # Configure logging
    if config.logging.log_to_console or config.logging.log_to_file:
        # Set up Python logging
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.logging.level))

        # Create formatter
        if config.logging.json_format:
            formatter = _create_json_formatter(config)
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )

        # Console handler
        if config.logging.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File handler
        if config.logging.log_to_file and config.logging.log_file_path:
            file_handler = logging.FileHandler(config.logging.log_file_path)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)


def _create_json_formatter(config: MonitoringConfig) -> logging.Formatter:
    """
    Create a JSON formatter for structured logging.

    Args:
        config: Monitoring configuration

    Returns:
        JSON formatter for logging
    """
    import json

    class JsonFormatter(logging.Formatter):
        """Format logs as JSON."""

        def format(self, record: logging.LogRecord) -> str:
            """Format a log record as JSON."""
            log_data = {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "service": config.service_name,
                "environment": config.environment,
            }

            # Add exception info
            if record.exc_info:
                log_data["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": self.formatException(record.exc_info),
                }

            # Add extra fields
            if hasattr(record, "event"):
                log_data["event"] = record.event

            if hasattr(record, "extra"):
                for key, value in record.extra.items():
                    log_data[key] = value

            # Include trace info if available
            if config.logging.include_trace_info:
                from uno.core.monitoring.tracing import (
                    get_current_trace_id,
                    get_current_span_id,
                )

                trace_id = get_current_trace_id()
                span_id = get_current_span_id()

                if trace_id:
                    log_data["trace_id"] = trace_id
                if span_id:
                    log_data["span_id"] = span_id

            # Include error context if available
            if config.logging.include_context:
                from uno.core.errors import get_error_context

                error_context = get_error_context()

                if error_context:
                    log_data["context"] = error_context

            return json.dumps(log_data, default=str)

    return JsonFormatter()
