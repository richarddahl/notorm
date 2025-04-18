"""
Monitoring dashboard for the Uno application.

This module provides a web-based dashboard for monitoring the health,
performance, and resources of the Uno application.
"""

from typing import Dict, List, Any, Optional, Set, Union, Callable
import asyncio
import logging
import json
import time
import datetime
from pathlib import Path
import os

from fastapi import FastAPI, APIRouter, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.websockets import WebSocketState

from uno.core.monitoring.config import MonitoringConfig, get_monitoring_config
from uno.core.monitoring.health import HealthRegistry, HealthStatus, get_health_registry
from uno.core.monitoring.metrics import (
    MetricsRegistry,
    get_metrics_registry,
    MetricValue,
    MetricType,
)
from uno.core.monitoring.events import EventLogger, get_event_logger, EventLevel
from uno.core.resource_monitor import (
    ResourceMonitor,
    get_resource_monitor,
    ResourceHealth,
)
from uno.core.errors import BaseError


# Dashboard configuration
class DashboardConfig:
    """Configuration for the monitoring dashboard."""

    def __init__(
        self,
        enabled: bool = True,
        route_prefix: str = "/monitoring/dashboard",
        api_prefix: str = "/monitoring/api",
        require_api_key: bool = False,
        api_key: Optional[str] = None,
        update_interval: float = 5.0,
        templates_dir: Optional[str] = None,
        static_dir: Optional[str] = None,
    ):
        """
        Initialize dashboard configuration.

        Args:
            enabled: Whether the dashboard is enabled
            route_prefix: URL prefix for dashboard routes
            api_prefix: URL prefix for dashboard API routes
            require_api_key: Whether to require API key for access
            api_key: API key for dashboard access
            update_interval: Interval for dashboard updates in seconds
            templates_dir: Directory for dashboard templates
            static_dir: Directory for dashboard static files
        """
        self.enabled = enabled
        self.route_prefix = route_prefix
        self.api_prefix = api_prefix
        self.require_api_key = require_api_key
        self.api_key = api_key or os.environ.get("UNO_DASHBOARD_API_KEY", "")
        self.update_interval = update_interval

        # Resolve template and static directories
        module_dir = Path(__file__).parent

        self.templates_dir = templates_dir or str(module_dir / "templates")
        self.static_dir = static_dir or str(module_dir / "static")


class MonitoringDashboard:
    """
    Web-based dashboard for monitoring.

    This class provides a web dashboard for monitoring the health,
    performance, and resources of the application.
    """

    def __init__(
        self,
        app: FastAPI,
        config: Optional[DashboardConfig] = None,
        monitoring_config: Optional[MonitoringConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the monitoring dashboard.

        Args:
            app: FastAPI application
            config: Dashboard configuration
            monitoring_config: Monitoring configuration
            logger: Logger to use
        """
        self.app = app
        self.config = config or DashboardConfig()
        self.monitoring_config = monitoring_config or get_monitoring_config()
        self.logger = logger or logging.getLogger(__name__)

        # Dependencies
        self.health_registry = get_health_registry()
        self.metrics_registry = get_metrics_registry()
        self.resource_monitor = get_resource_monitor()
        self.event_logger = get_event_logger()

        # Active WebSocket connections
        self._active_connections: Set[WebSocket] = set()

        # Templates
        self.templates = Jinja2Templates(directory=self.config.templates_dir)

        # Update task
        self._update_task: Optional[asyncio.Task] = None

        # Setup routes and middleware
        self._setup()

    def _setup(self) -> None:
        """Set up the dashboard routes and middleware."""
        # Skip if disabled
        if not self.config.enabled:
            return

        # Create routers
        dashboard_router = APIRouter(prefix=self.config.route_prefix)
        api_router = APIRouter(prefix=self.config.api_prefix)

        # Setup API key security if required
        api_key_header = None
        if self.config.require_api_key:
            api_key_header = APIKeyHeader(name="X-API-Key")

            # Dependency for API key validation
            async def validate_api_key(api_key: str = Depends(api_key_header)):
                if api_key != self.config.api_key:
                    raise BaseError(
                        "Invalid API key", status_code=401, error_code="UNAUTHORIZED"
                    )
                return api_key

            # Middleware for UI access
            class APIKeyMiddleware(BaseHTTPMiddleware):
                async def dispatch(self, request: Request, call_next):
                    # Skip API routes (they have their own security)
                    if request.url.path.startswith(self.config.api_prefix):
                        return await call_next(request)

                    # Check if dashboard route
                    if request.url.path.startswith(self.config.route_prefix):
                        # Check for API key in header or cookie
                        api_key = request.headers.get("X-API-Key")
                        if not api_key:
                            api_key = request.cookies.get("dashboard_api_key")

                        # Validate API key
                        if api_key != self.config.api_key:
                            # Redirect to login page
                            from fastapi.responses import RedirectResponse

                            return RedirectResponse(
                                url=f"{self.config.route_prefix}/login", status_code=302
                            )

                    return await call_next(request)

            # Add middleware if required
            if self.config.require_api_key:
                self.app.add_middleware(APIKeyMiddleware)

                # Add login page
                @dashboard_router.get("/login", response_class=HTMLResponse)
                async def login(request: Request):
                    return self.templates.TemplateResponse(
                        "login.html", {"request": request}
                    )

                @dashboard_router.post("/login")
                async def login_post(request: Request):
                    form_data = await request.form()
                    api_key = form_data.get("api_key")

                    if api_key != self.config.api_key:
                        return self.templates.TemplateResponse(
                            "login.html",
                            {"request": request, "error": "Invalid API key"},
                        )

                    # Success - redirect to dashboard with cookie
                    response = RedirectResponse(
                        url=self.config.route_prefix, status_code=302
                    )
                    response.set_cookie(
                        key="dashboard_api_key",
                        value=api_key,
                        httponly=True,
                        max_age=3600 * 24 * 30,  # 30 days
                    )
                    return response

        # Dashboard UI routes
        @dashboard_router.get("", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "service_name": self.monitoring_config.service_name,
                    "environment": self.monitoring_config.environment,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                },
            )

        @dashboard_router.get("/health", response_class=HTMLResponse)
        async def health_dashboard(request: Request):
            """Health dashboard page."""
            return self.templates.TemplateResponse(
                "health.html",
                {
                    "request": request,
                    "service_name": self.monitoring_config.service_name,
                    "environment": self.monitoring_config.environment,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                },
            )

        @dashboard_router.get("/metrics", response_class=HTMLResponse)
        async def metrics_dashboard(request: Request):
            """Metrics dashboard page."""
            return self.templates.TemplateResponse(
                "metrics.html",
                {
                    "request": request,
                    "service_name": self.monitoring_config.service_name,
                    "environment": self.monitoring_config.environment,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                },
            )

        @dashboard_router.get("/resources", response_class=HTMLResponse)
        async def resources_dashboard(request: Request):
            """Resources dashboard page."""
            return self.templates.TemplateResponse(
                "resources.html",
                {
                    "request": request,
                    "service_name": self.monitoring_config.service_name,
                    "environment": self.monitoring_config.environment,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                },
            )

        @dashboard_router.get("/events", response_class=HTMLResponse)
        async def events_dashboard(request: Request):
            """Events dashboard page."""
            return self.templates.TemplateResponse(
                "events.html",
                {
                    "request": request,
                    "service_name": self.monitoring_config.service_name,
                    "environment": self.monitoring_config.environment,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                },
            )

        # API routes
        api_deps = [Depends(validate_api_key)] if self.config.require_api_key else []

        @api_router.get("/health", dependencies=api_deps)
        async def health_api():
            """Get health data."""
            report = await self.health_registry.get_health_report(force=True)
            return report

        @api_router.get("/metrics", dependencies=api_deps)
        async def metrics_api():
            """Get metrics data."""
            metrics = await self.metrics_registry.get_all_metrics()
            # Convert metrics to simplified format
            simplified = {}
            for metric in metrics:
                name = metric.name
                type_name = metric.type.name.lower()

                if name not in simplified:
                    simplified[name] = {
                        "name": name,
                        "type": type_name,
                        "unit": metric.unit.name.lower(),
                        "description": metric.description,
                        "values": [],
                    }

                # Add value with tags
                simplified[name]["values"].append(
                    {
                        "value": (
                            metric.value if not isinstance(metric.value, list) else None
                        ),
                        "histogram": (
                            metric.value if isinstance(metric.value, list) else None
                        ),
                        "tags": metric.tags,
                        "timestamp": metric.timestamp,
                    }
                )

            return {"metrics": list(simplified.values())}

        @api_router.get("/resources", dependencies=api_deps)
        async def resources_api(include_history: bool = False):
            """Get resources data."""
            return await self.resource_monitor.get_metrics(
                include_history=include_history
            )

        @api_router.get("/events", dependencies=api_deps)
        async def events_api(limit: int = 50, level: str = "INFO"):
            """Get recent events."""
            # Convert string level to enum
            try:
                min_level = EventLevel[level.upper()]
            except KeyError:
                min_level = EventLevel.INFO

            events = await self.event_logger.get_recent_events(limit, min_level)
            return {"events": events}

        @api_router.get("/overview", dependencies=api_deps)
        async def overview_api():
            """Get overview data."""
            # Collect data for overview
            try:
                # Get health status
                health = await self.health_registry.get_status(force=False)
                health_str = health.name.lower()

                # Get resource summary
                resources = await self.resource_monitor.get_health_summary()

                # Get recent events count by level
                events = await self.event_logger.get_event_counts()

                # Get basic metrics
                metrics = {}
                try:
                    all_metrics = await self.metrics_registry.get_all_metrics()
                    # Extract a few key metrics for the overview
                    for metric in all_metrics:
                        if metric.name in [
                            "http_requests_total",
                            "http_error_rate",
                            "system_cpu",
                            "system_memory",
                        ]:
                            metrics[metric.name] = {
                                "value": metric.value,
                                "unit": metric.unit.name.lower(),
                            }
                except Exception as e:
                    self.logger.error(f"Error getting metrics: {str(e)}")

                # Build overview
                overview = {
                    "timestamp": time.time(),
                    "service": self.monitoring_config.service_name,
                    "environment": self.monitoring_config.environment,
                    "health": {
                        "status": health_str,
                        "resources": resources.get("resource_count", 0),
                        "healthy": resources.get("healthy_count", 0),
                        "degraded": resources.get("degraded_count", 0),
                        "unhealthy": resources.get("unhealthy_count", 0),
                    },
                    "events": events,
                    "metrics": metrics,
                }

                return overview

            except Exception as e:
                self.logger.error(f"Error generating overview: {str(e)}")
                return {"error": str(e)}

        # WebSocket connection
        @api_router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates."""
            await websocket.accept()
            self._active_connections.add(websocket)

            try:
                # Keep connection alive and handle messages
                while True:
                    # Wait for message (this prevents the task from blocking)
                    # We don't actually need to do anything with the messages
                    data = await websocket.receive_text()
                    # Could implement commands here if needed

            except WebSocketDisconnect:
                self._active_connections.remove(websocket)

            except Exception as e:
                self.logger.error(f"WebSocket error: {str(e)}")
                if websocket in self._active_connections:
                    self._active_connections.remove(websocket)

        # Add static files
        if os.path.exists(self.config.static_dir):
            self.app.mount(
                f"{self.config.route_prefix}/static",
                StaticFiles(directory=self.config.static_dir),
                name="dashboard_static",
            )

        # Include routers
        self.app.include_router(dashboard_router)
        self.app.include_router(api_router)

        # Start update task
        self._start_update_task()

    def _start_update_task(self) -> None:
        """Start the background task for sending updates."""
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.create_task(
                self._update_loop(), name="dashboard_updates"
            )

    async def _update_loop(self) -> None:
        """Background task for sending dashboard updates."""
        try:
            while True:
                # Wait for the update interval
                await asyncio.sleep(self.config.update_interval)

                # Skip if no connections
                if not self._active_connections:
                    continue

                # Gather update data
                try:
                    # Get a simple overview
                    overview = await self._get_overview_data()

                    # Send to all clients
                    update_data = json.dumps({"type": "update", "data": overview})

                    # Use gather with return_exceptions
                    await asyncio.gather(
                        *[
                            self._send_to_client(ws, update_data)
                            for ws in self._active_connections
                        ],
                        return_exceptions=True,
                    )

                except Exception as e:
                    self.logger.error(f"Error in update loop: {str(e)}")

        except asyncio.CancelledError:
            # Expected during shutdown
            pass

        except Exception as e:
            self.logger.error(f"Unexpected error in update loop: {str(e)}")

    async def _send_to_client(self, websocket: WebSocket, data: str) -> None:
        """
        Send data to a WebSocket client.

        Args:
            websocket: WebSocket connection
            data: Data to send
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(data)
            except Exception as e:
                self.logger.error(f"Error sending to client: {str(e)}")
                # Remove bad connection
                if websocket in self._active_connections:
                    self._active_connections.remove(websocket)

    async def _get_overview_data(self) -> Dict[str, Any]:
        """
        Get simplified overview data for updates.

        Returns:
            Dictionary with overview data
        """
        try:
            # Get health status
            health = await self.health_registry.get_status(force=False)
            health_str = health.name.lower()

            # Get resource counts
            resource_summary = await self.resource_monitor.get_health_summary()

            # Get a few key metrics
            # Just examples - real implementation would be more comprehensive
            cpu_usage = 0
            memory_usage = 0
            http_requests = 0
            response_time = 0

            # No need for complete data - WebSocket updates should be lightweight
            return {
                "timestamp": time.time(),
                "health_status": health_str,
                "resources": {
                    "healthy": resource_summary.get("healthy_count", 0),
                    "degraded": resource_summary.get("degraded_count", 0),
                    "unhealthy": resource_summary.get("unhealthy_count", 0),
                },
                "system": {
                    "cpu": cpu_usage,
                    "memory": memory_usage,
                },
                "http": {
                    "requests": http_requests,
                    "response_time": response_time,
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting overview data: {str(e)}")
            return {"error": str(e)}

    async def shutdown(self) -> None:
        """
        Shutdown the dashboard.

        This stops the update task and closes WebSocket connections.
        """
        # Cancel update task
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket connections
        for websocket in list(self._active_connections):
            try:
                await websocket.close()
            except Exception:
                pass

            self._active_connections.remove(websocket)


def setup_monitoring_dashboard(
    app: FastAPI,
    config: Optional[DashboardConfig] = None,
    monitoring_config: Optional[MonitoringConfig] = None,
) -> MonitoringDashboard:
    """
    Set up the monitoring dashboard for a FastAPI application.

    Args:
        app: FastAPI application
        config: Dashboard configuration
        monitoring_config: Monitoring configuration

    Returns:
        The configured MonitoringDashboard instance
    """
    # Create and return the dashboard
    dashboard = MonitoringDashboard(
        app=app,
        config=config,
        monitoring_config=monitoring_config,
    )

    # Register startup event to initialize resource monitoring
    @app.on_event("startup")
    async def startup_dashboard():
        # Ensure resource monitor is started
        monitor = get_resource_monitor()
        await monitor.start()

    # Register shutdown event
    @app.on_event("shutdown")
    async def shutdown_dashboard():
        await dashboard.shutdown()

    return dashboard
