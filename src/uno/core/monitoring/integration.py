# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integration for the monitoring and observability framework.

This module provides integration with FastAPI and other frameworks.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.monitoring.config import MonitoringConfig, get_monitoring_config
from uno.core.monitoring.metrics import (
    MetricsRegistry,
    PrometheusExporter,
    LoggingExporter,
    MetricsMiddleware,
    get_metrics_registry,
)
from uno.core.monitoring.tracing import (
    Tracer,
    TracingMiddleware,
    LoggingSpanProcessor,
    get_tracer,
)
from uno.core.monitoring.health import (
    HealthRegistry,
    HealthEndpoint,
    get_health_registry,
)
from uno.core.monitoring.events import (
    EventLogger,
    EventLevel,
    EventType,
    get_event_logger,
)
from uno.core.monitoring.dashboard import (
    MonitoringDashboard,
    DashboardConfig,
    setup_monitoring_dashboard,
)
from uno.core.resource_monitor import get_resource_monitor


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring HTTP requests.

    This middleware:
    1. Logs requests and responses
    2. Tracks request metrics
    3. Records distributed traces
    4. Adds monitoring headers to responses
    """

    def __init__(
        self,
        app: FastAPI,
        config: Optional[MonitoringConfig] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the monitoring middleware.

        Args:
            app: FastAPI application
            config: Monitoring configuration
            logger: Logger to use
        """
        super().__init__(app)
        self.config = config or get_monitoring_config()
        self.logger = logger or logging.getLogger(__name__)
        self.event_logger = get_event_logger()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request with monitoring.

        Args:
            request: The HTTP request
            call_next: Function to call the next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip monitoring for excluded paths
        path = request.url.path
        if path in self.config.metrics.excluded_paths:
            return await call_next(request)

        # Process the request
        start_time = asyncio.get_event_loop().time()

        try:
            # Process the request
            response = await call_next(request)

            # Log successful request
            asyncio.create_task(
                self.event_logger.info(
                    name="http_request",
                    message=f"{request.method} {path} {response.status_code}",
                    event_type=EventType.TECHNICAL,
                    data={
                        "method": request.method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": (asyncio.get_event_loop().time() - start_time)
                        * 1000,
                    },
                )
            )

            return response

        except Exception as e:
            # Log failed request
            asyncio.create_task(
                self.event_logger.error(
                    name="http_request_error",
                    message=f"{request.method} {path} failed: {str(e)}",
                    event_type=EventType.TECHNICAL,
                    data={
                        "method": request.method,
                        "path": path,
                        "error": str(e),
                        "duration_ms": (asyncio.get_event_loop().time() - start_time)
                        * 1000,
                    },
                    exception=e,
                )
            )

            # Re-raise the exception
            raise


def setup_monitoring(
    app: FastAPI,
    config: Optional[MonitoringConfig] = None,
    dashboard_config: Optional[DashboardConfig] = None,
) -> None:
    """
    Set up monitoring for a FastAPI application.

    This function:
    1. Configures metrics collection
    2. Sets up distributed tracing
    3. Adds health check endpoints
    4. Configures structured logging
    5. Sets up event logging
    6. Sets up the monitoring dashboard

    Args:
        app: FastAPI application
        config: Monitoring configuration
        dashboard_config: Dashboard configuration
    """
    # Get configuration
    config = config or get_monitoring_config()

    # Set up metrics
    if config.metrics.enabled:
        # Configure metrics registry
        metrics_registry = get_metrics_registry()
        prometheus_exporter = PrometheusExporter(namespace=config.service_name)

        # Add default exporters
        asyncio.create_task(
            metrics_registry.setup(
                export_interval=config.metrics.export_interval,
                exporters=[prometheus_exporter, LoggingExporter()],
            )
        )

        # Add metrics middleware
        app.add_middleware(
            MetricsMiddleware,
            metrics_path=config.metrics.metrics_path,
            registry=metrics_registry,
            excluded_paths=config.metrics.excluded_paths,
        )

        # Add metrics endpoint
        @app.get(config.metrics.metrics_path, include_in_schema=False)
        async def metrics():
            """Get Prometheus metrics."""
            return Response(
                content=metrics_registry.get_prometheus_metrics(),
                media_type="text/plain",
            )

    # Set up tracing
    if config.tracing.enabled:
        # Configure tracer
        tracer = get_tracer()
        tracer.service_name = config.tracing.service_name

        # Add span processor
        if config.tracing.log_spans:
            tracer.add_processor(LoggingSpanProcessor())

        # Configure sampling
        if config.tracing.sampling_rate < 1.0:
            # Create a sampler function
            def sampler(trace_id: str, parent_id: str | None, name: str) -> bool:
                # Always sample if parent is sampled
                if parent_id is not None:
                    return True

                # Sample based on rate
                import random

                return random.random() < config.tracing.sampling_rate

            tracer.set_sampler(sampler)

        # Add tracing middleware
        app.add_middleware(
            TracingMiddleware,
            tracer=tracer,
            excluded_paths=config.tracing.excluded_paths,
        )

    # Set up health checks
    if config.health.enabled:
        # Configure health registry
        health_registry = get_health_registry()

        # Add health endpoints
        HealthEndpoint.setup(
            app=app,
            prefix=config.health.path_prefix,
            tags=config.health.tags,
            include_details=config.health.include_details,
            register_resource_checks=config.health.register_resource_checks,
        )

    # Set up event logging
    if config.events.enabled:
        # Configure event logger
        event_logger = get_event_logger()

        # Set minimum level
        event_logger.min_level = EventLevel.from_string(config.events.min_level)

    # Add monitoring middleware
    app.add_middleware(MonitoringMiddleware, config=config)

    # Set up monitoring dashboard
    if dashboard_config is None:
        # Default to enabled dashboard
        dashboard_config = DashboardConfig(enabled=True)

    if dashboard_config.enabled:
        setup_monitoring_dashboard(app, dashboard_config, config)


def create_monitoring_endpoints(
    app: FastAPI,
    prefix: str = "/management",
    tags: list[str] = ["management"],
    config: Optional[MonitoringConfig] = None,
) -> None:
    """
    Create monitoring endpoints for a FastAPI application.

    This function adds endpoints for:
    1. Metrics
    2. Health checks
    3. Resource monitoring
    4. Runtime information

    Args:
        app: FastAPI application
        prefix: URL prefix for endpoints
        tags: OpenAPI tags for endpoints
        config: Monitoring configuration
    """
    # Get configuration
    config = config or get_monitoring_config()

    # Create router
    from fastapi import APIRouter

    router = APIRouter(prefix=prefix, tags=tags)

    # Add metrics endpoint (if not already added)
    if config.metrics.enabled and config.metrics.metrics_path == f"{prefix}/metrics":

        @router.get("/metrics", include_in_schema=False)
        async def metrics():
            """Get Prometheus metrics."""
            metrics_registry = get_metrics_registry()
            return Response(
                content=metrics_registry.get_prometheus_metrics(),
                media_type="text/plain",
            )

    # Add resource monitoring endpoints
    @router.get("/resources", summary="List all resources")
    async def list_resources(include_history: bool = False):
        """
        List all managed resources.

        Args:
            include_history: Whether to include historical metrics

        Returns:
            Resource metrics
        """
        monitor = get_resource_monitor()
        return await monitor.get_metrics(include_history=include_history)

    @router.get("/resources/{name}", summary="Get resource details")
    async def get_resource(name: str, include_history: bool = False):
        """
        Get details for a specific resource.

        Args:
            name: Name of the resource
            include_history: Whether to include historical metrics

        Returns:
            Resource metrics
        """
        monitor = get_resource_monitor()
        metrics = await monitor.get_metrics(
            resource_name=name,
            include_history=include_history,
        )

        if name not in metrics["resources"]:
            return {"error": f"Resource '{name}' not found"}, 404

        return metrics["resources"][name]

    # Add runtime information endpoint
    @router.get("/info", summary="Get runtime information")
    async def runtime_info():
        """
        Get runtime information.

        Returns information about the runtime environment.
        """
        import sys
        import platform
        import os

        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            memory_usage = {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "shared": getattr(memory_info, "shared", 0),
                "text": getattr(memory_info, "text", 0),
                "lib": getattr(memory_info, "lib", 0),
                "data": getattr(memory_info, "data", 0),
            }
            cpu_info = {
                "system": psutil.cpu_percent(),
                "process": process.cpu_percent(),
                "cores": psutil.cpu_count(),
            }
        except (ImportError, Exception):
            memory_usage = {"error": "psutil not available"}
            cpu_info = {"error": "psutil not available"}

        return {
            "service": config.service_name,
            "environment": config.environment,
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler(),
                "path": sys.path,
                "executable": sys.executable,
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "process": {
                "pid": os.getpid(),
                "ppid": os.getppid(),
                "memory": memory_usage,
                "cpu": cpu_info,
                "uptime": (
                    time.time() - psutil.Process().create_time()
                    if "psutil" in sys.modules
                    else 0
                ),
            },
        }

    # Register the router
    app.include_router(router)
