# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from uno.settings import uno_settings
from uno.dependencies import inject
from uno.dependencies.interfaces import UnoRepositoryProtocol
from uno.authorization.services import UserAuthorizationService

class AdminUIRouter:
    """Router for the admin UI pages."""
    
    def __init__(self, app):
        """Initialize the admin UI router.
        
        Args:
            app: The FastAPI application
        """
        self.app = app
        self.templates = Jinja2Templates(directory="src/templates")
        self.router = APIRouter(tags=["Admin UI"])
        
        # Register routes
        self.register_routes()
        self.app.include_router(self.router)
    
    def register_routes(self):
        """Register all admin UI routes."""
        
        @self.router.get("/admin", response_class=HTMLResponse)
        async def admin_page(
            request: Request, 
            user_auth_service: UserAuthorizationService = Depends(inject.get_instance(UserAuthorizationService))
        ):
            """Render the admin UI page."""
            try:
                # In a real app, you would check authentication and authorization here
                # current_user = await user_auth_service.get_current_user(request)
                # if not current_user or not user_auth_service.has_admin_access(current_user):
                #     raise HTTPException(status_code=403, detail="Not authorized to access admin interface")
                
                return self.templates.TemplateResponse(
                    "admin.html", 
                    {
                        "request": request,
                        "site_name": uno_settings.SITE_NAME
                    }
                )
            except Exception as e:
                # In development mode, re-raise for easier debugging
                if uno_settings.ENVIRONMENT == "development":
                    raise
                # In production, show a generic error
                return self.templates.TemplateResponse(
                    "base.html", 
                    {
                        "request": request,
                        "error": "An error occurred loading the admin interface."
                    }
                )
        
        # API routes for the admin UI

        @self.router.get("/api/admin/modules", tags=["Admin API"])
        async def get_modules():
            """Get all available modules for the admin UI."""
            # In a real app, these would be dynamically generated based on
            # registered modules and user permissions
            return {
                "modules": [
                    {
                        "id": "dashboard",
                        "name": "Admin Dashboard",
                        "icon": "speedometer",
                        "description": "System overview and status",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "statistics", "name": "Statistics"},
                            {"id": "activity", "name": "Activity Log"}
                        ]
                    },
                    {
                        "id": "authorization",
                        "name": "Role Management",
                        "icon": "shield-lock",
                        "description": "User roles and permissions",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "roles", "name": "Roles"},
                            {"id": "permissions", "name": "Permissions"},
                            {"id": "assignments", "name": "User Assignments"}
                        ]
                    },
                    {
                        "id": "monitoring",
                        "name": "System Monitor",
                        "icon": "graph-up",
                        "description": "System health and performance",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "metrics", "name": "Metrics"},
                            {"id": "health", "name": "Health Checks"},
                            {"id": "logs", "name": "Logs"},
                            {"id": "alerts", "name": "Alerts"},
                            {"id": "tracing", "name": "Tracing"}
                        ]
                    },
                    {
                        "id": "vector-search",
                        "name": "Vector Search",
                        "icon": "search",
                        "description": "Semantic search interface",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "search", "name": "Search"},
                            {"id": "stats", "name": "Vector Stats"},
                            {"id": "settings", "name": "Settings"}
                        ]
                    },
                    {
                        "id": "reports",
                        "name": "Reports",
                        "icon": "file-earmark-bar-graph",
                        "description": "Report generation and management",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "create", "name": "Create Report"},
                            {"id": "list", "name": "All Reports"},
                            {"id": "templates", "name": "Templates"},
                            {"id": "scheduled", "name": "Scheduled Reports"}
                        ]
                    }
                ]
            }

        @self.router.get("/api/admin/system-stats", tags=["Admin API"])
        async def get_system_stats():
            """Get system statistics for the admin dashboard."""
            # Mock data - in a real app, this would come from monitoring services
            return {
                "uptimeHours": 24 * 7,
                "requestsPerMinute": 257,
                "activeUsers": 42,
                "errorRate": 0.5,
                "cpuUsage": 32,
                "memoryUsage": 68,
                "databaseConnections": 15,
                "databaseSize": "4.2 GB",
                "latestVersion": "1.2.0",
                "currentVersion": "1.2.0",
                "healthStatus": "healthy"
            }