# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import importlib
import logging
from logging.config import dictConfig

# Configure logging first
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": "uno.log",
            "mode": "a",
        },
    },
    "loggers": {
        "uno": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
dictConfig(logging_config)
logger = logging.getLogger("uno")

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uno.settings import uno_settings

# Import the service provider, but don't use it yet
from uno.dependencies.modern_provider import get_service_provider

# Import the app, but we need to redefine it with our lifespan
from uno.api.apidef import app as api_app

# Add modern lifespan event handlers for FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    try:
        # === STARTUP ===
        logger.info("Starting application initialization")
        
        # Initialize the modern dependency injection system
        from uno.dependencies.modern_provider import initialize_services
        await initialize_services()
        logger.info("Modern DI Service Provider initialized")

        # Register services using automatic discovery (optional)
        from uno.dependencies.discovery import register_services_in_package
        try:
            # Discover and register services in the application
            register_services_in_package("uno.domain")
            register_services_in_package("uno.entity_services")
            logger.info("Service discovery completed")
        except Exception as e:
            logger.error(f"Error during service discovery: {e}")
            
        # Import models after initialization
        logger.debug("Loading UnoObj models")
        from uno.attributes import objs as attr_models
        from uno.authorization import objs as auth_models
        from uno.queries import models as fltr_models
        from uno.meta import objs as meta_models
        from uno.messaging import objs as msg_models
        from uno.reports import objs as rpt_models
        from uno.values import objs as val_models
        from uno.workflows import models as wkflw_models
        
        # Use the UnoRegistry singleton instance
        from uno.registry import get_registry
        registry = get_registry()
        
        # Configure models with the app
        logger.debug("Configuring UnoObj models with app")
        for obj_name, obj in registry.get_all().items():
            if hasattr(obj, "configure"):
                obj.configure(api_app)
                
        logger.info("All UnoObj models loaded and configured")
        
        # Set up API routers
        logger.info("Setting up API routers")
        
        # Authorization endpoints
        from uno.authorization.endpoints import router as auth_router
        api_app.include_router(auth_router)
        logger.debug("Authorization router included")

        # Meta endpoints
        from uno.meta.endpoints import router as meta_router
        api_app.include_router(meta_router)
        logger.debug("Meta router included")

        # Vector search endpoints (if available)
        try:
            from uno.vector_search.endpoints import router as vector_router
            api_app.include_router(vector_router)
            logger.info("Vector search router included")
        except ImportError:
            logger.debug("Vector search router not available")
            
        # Domain endpoints for Queries module
        try:
            from uno.queries.domain_endpoints import (
                query_path_router,
                query_value_router,
                query_router
            )
            api_app.include_router(query_path_router.router)
            api_app.include_router(query_value_router.router)
            api_app.include_router(query_router)
            logger.info("Queries module domain routers included")
        except ImportError:
            logger.debug("Queries module domain routers not available")
            
        # Domain endpoints for Reports module
        try:
            from uno.reports.domain_endpoints import (
                field_definition_router,
                template_router,
                trigger_router,
                output_router,
                execution_router,
                output_execution_router
            )
            api_app.include_router(field_definition_router.router)
            api_app.include_router(template_router.router)
            api_app.include_router(trigger_router.router)
            api_app.include_router(output_router.router)
            api_app.include_router(execution_router.router)
            api_app.include_router(output_execution_router)
            logger.info("Reports module domain routers included")
        except ImportError:
            logger.debug("Reports module domain routers not available")

        # Admin UI
        try:
            from uno.api.admin_ui import AdminUIRouter
            admin_ui = AdminUIRouter(api_app)
            logger.info("Admin UI router included")
        except ImportError:
            logger.debug("Admin UI router not available")
            
        # Set up the workflow module
        try:
            from uno.workflows.app_integration import setup_workflow_module
            setup_workflow_module(api_app)
            logger.info("Workflow module setup complete")
        except ImportError:
            logger.debug("Workflow module not available")
        except Exception as e:
            logger.error(f"Error setting up workflow module: {e}", exc_info=True)

        # Example domain endpoints using modern dependency injection
        # try:
        #     from uno.domain.api_example import router as example_router
        #     api_app.include_router(example_router)
        #     logger.info("Example domain router included")
        # except ImportError:
        #     logger.debug("Example domain router not available")
        
        logger.info("API routers setup complete")
        logger.info("Application startup complete")
        
        # Yield control back to FastAPI
        yield
        
        # === SHUTDOWN ===
        logger.info("Starting application shutdown")
        
        # Shut down the modern dependency injection system
        from uno.dependencies.modern_provider import shutdown_services
        await shutdown_services()
        logger.info("DI Service Provider shut down")
        
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during application lifecycle: {e}", exc_info=True)
        raise

# Modify the existing app instead of creating a new one
# This ensures all OpenAPI metadata is preserved
api_app.router.lifespan_context = lifespan

# We no longer need to copy these settings since we're using the original app

templates = Jinja2Templates(directory="src/templates")

# Make sure static files are properly mounted
if "/static" not in [route.path for route in api_app.routes]:
    api_app.mount(
        "/static",
        StaticFiles(directory="src/static"),
        name="static",
    )

# Configure the modern dependency injection system with FastAPI
from uno.dependencies.fastapi_integration import configure_fastapi
configure_fastapi(api_app)

# Example of an endpoint using the new dependency injection system
from uno.dependencies.decorators import inject_params
from uno.dependencies.interfaces import UnoConfigProtocol

@api_app.get("/app", response_class=HTMLResponse, tags=["0KUI"])
async def app_base(request: Request):
    """Render the main application page."""
    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "authentication_url": "/api/auth/login",
            "site_name": "Uno Application",
        },
    )

@api_app.get("/routes", response_class=JSONResponse, tags=["0KUI"])
async def list_routes():
    """List all available routes for debugging"""
    routes = []
    for route in api_app.routes:
        if hasattr(route, "methods"):
            methods = list(route.methods)
        else:
            methods = ["N/A"]
        
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": methods,
            "include_in_schema": getattr(route, "include_in_schema", "N/A")
        })
    
    return {"routes": routes}

# Add admin routes directly for testing
@api_app.get("/admin", response_class=HTMLResponse, tags=["0KUI"], include_in_schema=False)
async def admin_page(request: Request):
    """Admin dashboard page"""
    return templates.TemplateResponse(
        "admin.html", 
        {
            "request": request,
            "site_name": "UNO Admin",
            "component": "okui-admin-dashboard"
        }
    )

@api_app.get("/admin-direct", response_class=HTMLResponse, tags=["0KUI"])
async def admin_direct(request: Request):
    """Direct admin page for testing"""
    return templates.TemplateResponse(
        "admin.html", 
        {
            "request": request,
            "site_name": "UNO Admin (Direct)",
            "component": "okui-admin-dashboard"
        }
    )

# Add sub-admin routes for direct access
@api_app.get("/admin/{module}", response_class=HTMLResponse, tags=["0KUI"], include_in_schema=False)
async def admin_module(request: Request, module: str):
    """Admin module page"""
    component_map = {
        "attributes": "okui-attributes-manager",
        "values": "okui-values-manager",
        "queries": "okui-queries-manager",
        "jobs": "okui-job-dashboard",
        "security": "okui-security-admin",
        "workflows": "okui-workflow-dashboard",
        "reports": "okui-report-dashboard",
        "vector-search": "okui-semantic-search",
        "authorization": "okui-role-manager",
        "monitoring": "okui-system-monitor"
    }
    
    component = component_map.get(module, "okui-admin-dashboard")
    
    return templates.TemplateResponse(
        "admin.html", 
        {
            "request": request,
            "site_name": f"UNO Admin: {module.title()}",
            "component": component
        }
    )

def generate_openapi_schema():
    """Generate the OpenAPI schema for the FastAPI application."""
    return get_openapi(
        title="My API",
        version="1.0.0",
        description="Uno API",
        routes=api_app.routes,
    )

@api_app.get(
    "/api/v1.0/schema",
    response_class=JSONResponse,
    tags=["Schemas"],
    summary="Get the OpenAPI schema",
    description="Retrieve the generated OpenAPI schema.",
)
def get_openapi_endpoint():
    """Retrieve the generated OpenAPI schema."""
    return JSONResponse(content=generate_openapi_schema())

@api_app.get(
    "/api/v1.0/schema/{schema_name}",
    response_class=JSONResponse,
    tags=["Schemas"],
    summary="Get a schema by name",
    description="Retrieve a schema by name.",
)
def get_schema(schema_name: str):
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="This is my API description",
        routes=api_app.routes,
    )

    schemas = openapi_schema.get("components", {}).get("schemas", {})

    if schema_name not in schemas:
        raise HTTPException(status_code=404, detail="Schema not found")

    schema = schemas[schema_name]

    return JSONResponse(content=schema)

# Export api_app as app for uvicorn to run it
app = api_app
