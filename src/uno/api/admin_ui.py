# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Frontend UI routes for the UNO admin interfaces.

This module provides FastAPI route handlers for accessing the UNO admin UI components,
including the component dashboards for attributes, values, queries, jobs, security,
workflows, reports, vector search, and more.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

from uno.settings import uno_settings
from uno.dependencies.interfaces import UnoRepositoryProtocol
# Import get_service for dependency injection
from uno.dependencies.database import get_service

class AdminUIRouter:
    """Router for the admin UI pages."""
    
    def __init__(self, app):
        """Initialize the admin UI router.
        
        Args:
            app: The FastAPI application
        """
        self.app = app
        self.templates = Jinja2Templates(directory="src/templates")
        
        # Create a separate router for UI pages that don't need to appear in API docs
        self.ui_router = APIRouter(tags=["Admin UI"], include_in_schema=False)
        
        # Create a router for API endpoints that will appear in API docs
        self.api_router = APIRouter(tags=["Admin API"], prefix="/api/admin")
        
        # Register routes
        self.register_routes()
        
        # Include both routers
        self.app.include_router(self.ui_router)
        self.app.include_router(self.api_router)
    
    def register_routes(self):
        """Register all admin UI routes."""
        
        @self.ui_router.get("/admin", response_class=HTMLResponse)
        async def admin_page(request: Request):
            """Render the admin UI page."""
            try:
                # Authentication and authorization would be handled here in a real app
                return self.templates.TemplateResponse(
                    "admin.html", 
                    {
                        "request": request,
                        "site_name": uno_settings.SITE_NAME,
                        "component": "okui-admin-dashboard"
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
        
        # Component UI routes
        
        @self.ui_router.get("/admin/attributes", response_class=HTMLResponse)
        async def attributes_manager(request: Request):
            """Render the attributes management interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-attributes-manager"
                }
            )
        
        @self.ui_router.get("/admin/values", response_class=HTMLResponse)
        async def values_manager(request: Request):
            """Render the values management interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-values-manager"
                }
            )
        
        @self.ui_router.get("/admin/queries", response_class=HTMLResponse)
        async def queries_manager(request: Request):
            """Render the queries management interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-queries-manager"
                }
            )
        
        @self.ui_router.get("/admin/jobs", response_class=HTMLResponse)
        async def jobs_dashboard(request: Request):
            """Render the jobs dashboard interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-job-dashboard"
                }
            )
        
        @self.ui_router.get("/admin/security", response_class=HTMLResponse)
        async def security_admin(request: Request):
            """Render the security administration interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-security-admin"
                }
            )
        
        @self.ui_router.get("/admin/workflows", response_class=HTMLResponse)
        async def workflow_admin(request: Request):
            """Render the workflow administration interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-workflow-dashboard"
                }
            )
        
        @self.ui_router.get("/admin/workflows/designer", response_class=HTMLResponse)
        async def workflow_designer(request: Request, workflow_id: str = None):
            """Render the workflow designer interface."""
            props = {"workflow-id": workflow_id} if workflow_id else {}
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-workflow-designer",
                    "props": props
                }
            )
        
        @self.ui_router.get("/admin/workflows/simulator", response_class=HTMLResponse)
        async def workflow_simulator(request: Request, workflow_id: str):
            """Render the workflow simulator interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-workflow-simulator",
                    "props": {"workflow-id": workflow_id}
                }
            )
        
        @self.ui_router.get("/admin/workflows/execution", response_class=HTMLResponse)
        async def workflow_execution_detail(request: Request, workflow_id: str, execution_id: str):
            """Render the workflow execution detail interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-workflow-execution-detail",
                    "props": {"workflow-id": workflow_id, "execution-id": execution_id}
                }
            )
        
        @self.ui_router.get("/admin/reports", response_class=HTMLResponse)
        async def reports_dashboard(request: Request):
            """Render the reports dashboard interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-report-dashboard"
                }
            )
        
        @self.ui_router.get("/admin/reports/builder", response_class=HTMLResponse)
        async def report_builder(request: Request, report_id: str = None):
            """Render the report builder interface."""
            props = {"report-id": report_id} if report_id else {}
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-report-builder",
                    "props": props
                }
            )
        
        @self.ui_router.get("/admin/reports/execution", response_class=HTMLResponse)
        async def report_execution(request: Request, report_id: str = None):
            """Render the report execution interface."""
            props = {"report-id": report_id} if report_id else {}
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-report-execution-manager",
                    "props": props
                }
            )
        
        @self.ui_router.get("/admin/vector-search", response_class=HTMLResponse)
        async def vector_search(request: Request):
            """Render the vector search interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-semantic-search"
                }
            )
        
        @self.ui_router.get("/admin/authorization", response_class=HTMLResponse)
        async def authorization_admin(request: Request):
            """Render the authorization/role management interface."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-role-manager"
                }
            )
        
        @self.ui_router.get("/admin/monitoring", response_class=HTMLResponse)
        async def monitoring_dashboard(request: Request):
            """Render the system monitoring dashboard."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-system-monitor"
                }
            )
        
        @self.ui_router.get("/admin/crud/{entity_type}", response_class=HTMLResponse)
        async def crud_manager(request: Request, entity_type: str):
            """Render the generic CRUD manager interface for a specific entity type."""
            return self.templates.TemplateResponse(
                "admin.html",
                {
                    "request": request, 
                    "site_name": uno_settings.SITE_NAME,
                    "component": "okui-crud-manager",
                    "props": {"entity-type": entity_type, "base-url": f"/api/{entity_type}"}
                }
            )
        
        # Component showcase
        @self.ui_router.get("/components", response_class=HTMLResponse)
        async def component_showcase(request: Request):
            """Render the component showcase page."""
            return self.templates.TemplateResponse(
                "components/index.html",
                {"request": request}
            )
        
        # API routes for the admin UI
        
        @self.api_router.get("/modules")
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
                        "path": "/admin",
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
                        "path": "/admin/authorization",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "roles", "name": "Roles"},
                            {"id": "permissions", "name": "Permissions"},
                            {"id": "assignments", "name": "User Assignments"}
                        ]
                    },
                    {
                        "id": "attributes",
                        "name": "Attributes Manager",
                        "icon": "tag",
                        "description": "Manage entity attributes",
                        "path": "/admin/attributes",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "attributes", "name": "Attributes"},
                            {"id": "schemas", "name": "Schemas"}
                        ]
                    },
                    {
                        "id": "values",
                        "name": "Values Manager",
                        "icon": "database",
                        "description": "Manage entity values",
                        "path": "/admin/values",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "values", "name": "Values"}
                        ]
                    },
                    {
                        "id": "queries",
                        "name": "Queries Manager",
                        "icon": "search",
                        "description": "Manage and execute queries",
                        "path": "/admin/queries",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "queries", "name": "Queries"},
                            {"id": "paths", "name": "Query Paths"},
                            {"id": "execute", "name": "Execute"}
                        ]
                    },
                    {
                        "id": "jobs",
                        "name": "Jobs Dashboard",
                        "icon": "calendar-check",
                        "description": "Monitor and manage background jobs",
                        "path": "/admin/jobs",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "jobs", "name": "All Jobs"},
                            {"id": "failed", "name": "Failed Jobs"},
                            {"id": "scheduled", "name": "Scheduled Jobs"}
                        ]
                    },
                    {
                        "id": "security",
                        "name": "Security Admin",
                        "icon": "lock",
                        "description": "Security settings and tools",
                        "path": "/admin/security",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "encryption", "name": "Encryption"},
                            {"id": "audit", "name": "Audit Logs"},
                            {"id": "policies", "name": "Security Policies"}
                        ]
                    },
                    {
                        "id": "workflows",
                        "name": "Workflows",
                        "icon": "diagram-3",
                        "description": "Workflow management and execution",
                        "path": "/admin/workflows",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "workflows", "name": "All Workflows"},
                            {"id": "executions", "name": "Executions"},
                            {"id": "create", "name": "Create", "path": "/admin/workflows/designer"},
                            {"id": "templates", "name": "Templates"}
                        ]
                    },
                    {
                        "id": "monitoring",
                        "name": "System Monitor",
                        "icon": "graph-up",
                        "description": "System health and performance",
                        "path": "/admin/monitoring",
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
                        "path": "/admin/vector-search",
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
                        "path": "/admin/reports",
                        "views": [
                            {"id": "overview", "name": "Overview"},
                            {"id": "create", "name": "Create Report", "path": "/admin/reports/builder"},
                            {"id": "list", "name": "All Reports"},
                            {"id": "templates", "name": "Templates"},
                            {"id": "scheduled", "name": "Scheduled Reports"}
                        ]
                    }
                ]
            }
        
        @self.api_router.get("/system-stats")
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