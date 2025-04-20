# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Health dashboard for the Uno application.

This module provides a specialized dashboard for monitoring the health status
of the application, services, and resources. It includes:

1. Interactive health status visualization
2. Health history tracking
3. Health check group management
4. Resource health integration
5. Real-time health status updates
"""

from typing import Dict, List, Any, Optional, Set, Callable, Awaitable, Tuple, Union
import asyncio
import time
import logging
import json
import datetime
from pathlib import Path
import os
from functools import wraps

from fastapi import FastAPI, APIRouter, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.websockets import WebSocketState
from pydantic import BaseModel, Field

from uno.core.logging import get_logger
from uno.core.health.framework import (
    HealthRegistry,
    HealthStatus,
    get_health_registry,
    HealthConfig,
)


class HealthDashboardConfig(BaseModel):
    """Configuration for the health dashboard."""

    enabled: bool = True
    route_prefix: str = "/health/dashboard"
    api_prefix: str = "/health/api"
    require_auth: bool = False
    update_interval: float = 5.0  # seconds
    templates_dir: str | None = None
    static_dir: str | None = None
    history_size: int = 100  # number of historical status points to keep
    show_on_sidebar: bool = True
    auto_refresh: bool = True


class HealthDashboard:
    """
    Health dashboard for the Uno application.

    This class provides a web-based dashboard for monitoring health status.
    """

    def __init__(
        self,
        app: FastAPI,
        config: Optional[HealthDashboardConfig] = None,
        health_config: Optional[HealthConfig] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the health dashboard.

        Args:
            app: FastAPI application
            config: Dashboard configuration
            health_config: Health check configuration
            logger: Logger to use
        """
        self.app = app
        self.config = config or HealthDashboardConfig()
        self.health_config = health_config or HealthConfig()
        self.logger = logger or get_logger("uno.health.dashboard")

        # Get health registry
        self.health_registry = get_health_registry()

        # Active WebSocket connections
        self._active_connections: Set[WebSocket] = set()

        # Health status history
        self._status_history: list[dict[str, Any]] = []

        # Health check status cache
        self._last_status: dict[str, Any] | None = None
        self._last_check_time: float = 0

        # Update task
        self._update_task: Optional[asyncio.Task] = None

        # Templates directory
        module_dir = Path(__file__).parent
        self.templates_dir = self.config.templates_dir or str(module_dir / "templates")
        self.static_dir = self.config.static_dir or str(module_dir / "static")

        # Create templates object
        self.templates = Jinja2Templates(directory=self.templates_dir)

        # Setup dashboard
        self._setup()

    def _setup(self) -> None:
        """Set up the dashboard routes and middleware."""
        # Skip if disabled
        if not self.config.enabled:
            return

        # Create routers
        dashboard_router = APIRouter(prefix=self.config.route_prefix)
        api_router = APIRouter(prefix=self.config.api_prefix)

        # Setup authentication if required
        # (This would be replaced with your actual auth implementation)
        auth_dependency = []
        if self.config.require_auth:
            # Just a placeholder - use your actual auth system
            from fastapi import Depends, HTTPException, status
            from fastapi.security import APIKeyHeader

            api_key_header = APIKeyHeader(name="X-API-Key")

            async def verify_api_key(api_key: str = Depends(api_key_header)):
                # This would check against your actual API keys
                if api_key != "your-api-key":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                    )
                return api_key

            auth_dependency = [Depends(verify_api_key)]

        # Dashboard UI routes
        @dashboard_router.get("", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main health dashboard page."""
            return self.templates.TemplateResponse(
                "health_dashboard.html",
                {
                    "request": request,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                    "auto_refresh": self.config.auto_refresh,
                },
            )

        @dashboard_router.get("/groups", response_class=HTMLResponse)
        async def groups_dashboard(request: Request):
            """Health groups dashboard page."""
            return self.templates.TemplateResponse(
                "health_groups.html",
                {
                    "request": request,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                    "auto_refresh": self.config.auto_refresh,
                },
            )

        @dashboard_router.get("/history", response_class=HTMLResponse)
        async def history_dashboard(request: Request):
            """Health history dashboard page."""
            return self.templates.TemplateResponse(
                "health_history.html",
                {
                    "request": request,
                    "update_interval": self.config.update_interval,
                    "ws_url": f"{self.config.api_prefix}/ws",
                    "auto_refresh": self.config.auto_refresh,
                },
            )

        # API routes
        @api_router.get("/status", dependencies=auth_dependency)
        async def status_api(force: bool = False):
            """Get current health status."""
            status = await self.health_registry.get_status(force)
            return {
                "status": status.name.lower(),
                "timestamp": time.time(),
            }

        @api_router.get("/report", dependencies=auth_dependency)
        async def report_api(force: bool = False):
            """Get detailed health report."""
            return await self.health_registry.get_health_report(force)

        @api_router.get("/history", dependencies=auth_dependency)
        async def history_api():
            """Get health status history."""
            return {
                "history": self._status_history,
                "history_size": len(self._status_history),
                "max_size": self.config.history_size,
            }

        @api_router.get("/groups", dependencies=auth_dependency)
        async def groups_api():
            """Get health check groups."""
            async with self.health_registry._lock:
                groups = list(self.health_registry._groups.keys())

            group_details = []
            for group in groups:
                status = await self.health_registry.get_group_status(group)
                group_details.append(
                    {
                        "name": group,
                        "status": status.name.lower(),
                    }
                )

            return {"groups": group_details}

        @api_router.get("/groups/{group}", dependencies=auth_dependency)
        async def group_details_api(group: str, force: bool = False):
            """Get details for a specific health check group."""
            status = await self.health_registry.get_group_status(group, force)
            results = await self.health_registry.check_group(group, force)

            # Process results
            checks = []
            for check_id, result in results.items():
                check = self.health_registry._checks.get(check_id)
                if not check:
                    continue

                checks.append(
                    {
                        "id": check_id,
                        "name": check.name,
                        "description": check.description,
                        "tags": check.tags,
                        "critical": check.critical,
                        "result": result.to_dict(),
                    }
                )

            return {
                "group": group,
                "status": status.name.lower(),
                "checks": checks,
                "checks_count": len(checks),
                "timestamp": time.time(),
            }

        # Health check action endpoints
        @api_router.post("/trigger", dependencies=auth_dependency)
        async def trigger_health_checks():
            """Trigger all health checks."""
            await self.health_registry.check_all(force=True)
            return {"status": "triggered", "timestamp": time.time()}

        @api_router.post("/groups/{group}/trigger", dependencies=auth_dependency)
        async def trigger_group_checks(group: str):
            """Trigger health checks for a specific group."""
            await self.health_registry.check_group(group, force=True)
            return {"status": "triggered", "group": group, "timestamp": time.time()}

        # WebSocket connection
        @api_router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time health updates."""
            await websocket.accept()
            self._active_connections.add(websocket)

            try:
                # Send initial status
                status = await self.health_registry.get_status()
                await websocket.send_json(
                    {
                        "type": "status",
                        "status": status.name.lower(),
                        "timestamp": time.time(),
                    }
                )

                # Keep connection alive and handle commands
                while True:
                    # Wait for message
                    message = await websocket.receive_json()

                    # Handle commands
                    command = message.get("command")
                    if command == "trigger":
                        # Trigger health checks
                        await self.health_registry.check_all(force=True)
                        status = await self.health_registry.get_status()
                        await websocket.send_json(
                            {
                                "type": "status",
                                "status": status.name.lower(),
                                "timestamp": time.time(),
                            }
                        )
                    elif command == "trigger_group":
                        # Trigger health checks for a group
                        group = message.get("group")
                        if group:
                            await self.health_registry.check_group(group, force=True)
                            status = await self.health_registry.get_group_status(group)
                            await websocket.send_json(
                                {
                                    "type": "group_status",
                                    "group": group,
                                    "status": status.name.lower(),
                                    "timestamp": time.time(),
                                }
                            )
                    elif command == "get_report":
                        # Send full health report
                        report = await self.health_registry.get_health_report()
                        await websocket.send_json(
                            {
                                "type": "report",
                                "report": report,
                            }
                        )
                    elif command == "get_history":
                        # Send health history
                        await websocket.send_json(
                            {
                                "type": "history",
                                "history": self._status_history,
                            }
                        )
                    elif command == "get_groups":
                        # Send health check groups
                        async with self.health_registry._lock:
                            groups = list(self.health_registry._groups.keys())

                        group_details = []
                        for group in groups:
                            status = await self.health_registry.get_group_status(group)
                            group_details.append(
                                {
                                    "name": group,
                                    "status": status.name.lower(),
                                }
                            )

                        await websocket.send_json(
                            {
                                "type": "groups",
                                "groups": group_details,
                            }
                        )

            except WebSocketDisconnect:
                self._active_connections.remove(websocket)

            except Exception as e:
                self.logger.error(f"WebSocket error: {str(e)}")
                if websocket in self._active_connections:
                    self._active_connections.remove(websocket)

        # Add static files
        if os.path.exists(self.static_dir):
            self.app.mount(
                f"{self.config.route_prefix}/static",
                StaticFiles(directory=self.static_dir),
                name="health_dashboard_static",
            )

        # Include routers
        self.app.include_router(dashboard_router)
        self.app.include_router(api_router)

        # Start update task
        self._start_update_task()

    def _start_update_task(self) -> None:
        """Start the background task for updating health status."""
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.create_task(self._update_loop())

    async def _update_loop(self) -> None:
        """Background task for updating health status."""
        try:
            while True:
                # Wait for update interval
                await asyncio.sleep(self.config.update_interval)

                # Check health status
                try:
                    # Get current health status
                    status = await self.health_registry.get_status()
                    status_str = status.name.lower()

                    # Record in history
                    self._status_history.append(
                        {
                            "status": status_str,
                            "timestamp": time.time(),
                        }
                    )

                    # Trim history if needed
                    while len(self._status_history) > self.config.history_size:
                        self._status_history.pop(0)

                    # Send to all WebSocket clients
                    if self._active_connections:
                        await asyncio.gather(
                            *[
                                self._send_status_update(ws, status_str)
                                for ws in self._active_connections
                            ],
                            return_exceptions=True,
                        )

                except Exception as e:
                    self.logger.error(f"Error updating health status: {str(e)}")

        except asyncio.CancelledError:
            # Task was cancelled, just exit
            pass

        except Exception as e:
            self.logger.error(
                f"Unexpected error in health status update loop: {str(e)}"
            )

    async def _send_status_update(self, websocket: WebSocket, status: str) -> None:
        """
        Send status update to a WebSocket client.

        Args:
            websocket: WebSocket connection
            status: Health status
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(
                    {
                        "type": "status",
                        "status": status,
                        "timestamp": time.time(),
                    }
                )
            except Exception as e:
                self.logger.error(f"Error sending status update: {str(e)}")
                # Remove bad connection
                if websocket in self._active_connections:
                    self._active_connections.remove(websocket)

    async def shutdown(self) -> None:
        """
        Shutdown the health dashboard.

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


def setup_health_dashboard(
    app: FastAPI,
    config: Optional[HealthDashboardConfig] = None,
    health_config: Optional[HealthConfig] = None,
) -> HealthDashboard:
    """
    Set up the health dashboard for a FastAPI application.

    Args:
        app: FastAPI application
        config: Dashboard configuration
        health_config: Health check configuration

    Returns:
        The configured HealthDashboard instance
    """
    # Create dashboard
    dashboard = HealthDashboard(
        app=app,
        config=config,
        health_config=health_config,
    )

    # Register shutdown handler
    @app.on_event("shutdown")
    async def shutdown_dashboard():
        await dashboard.shutdown()

    return dashboard
