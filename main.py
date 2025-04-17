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

# Import error handling utilities
from uno.core.fastapi_error_handlers import (
    setup_error_handlers,
    ErrorHandlingMiddleware,
)

from uno.settings import uno_settings

# Import the service provider, but don't use it yet
from uno.dependencies.modern_provider import get_service_provider

# Import the app, but we need to redefine it with our lifespan
from uno.api.apidef import app as api_app
from uno.core.feature_factory import FeatureFactory

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
            logger.info("Service discovery completed")
        except Exception as e:
            logger.error(f"Error during service discovery: {e}")

        # Import domain models after initialization
        logger.debug("Loading domain models")
        # Import domain models as needed

        logger.info("All domain models loaded and configured")

        # Set up API routers
        logger.info("Setting up API routers")

        # Dynamically include feature routers based on Domain-Driven layouts
        for feat in [
            "authorization",
            "meta",
            "database",
            "messaging",
            "queries",
            "reports",
            "values",
            "workflows",
        ]:
            try:
                ff = FeatureFactory(feat)
                for router in ff.get_routers():
                    api_app.include_router(router)
                    logger.info(f"{feat} router included")
            except ModuleNotFoundError:
                logger.debug(f"{feat} module not available")
            except AttributeError as e:
                logger.debug(f"{feat} domain_endpoints missing router: {e}")

        # Example domain endpoints using modern dependency injection
        # try:
        #     from uno.domain.api_example import router as example_router
        #     api_app.include_router(example_router)
        #     logger.info("Example domain router included")
        # except ImportError:
        #     logger.debug("Example domain router not available")

        # Include error handling example endpoints
        try:
            from uno.core.errors.examples import router as error_examples_router

            api_app.include_router(error_examples_router)
            logger.info("Error examples router included")
        except ImportError:
            logger.debug("Error examples router not available")

        # Set up error handlers for FastAPI
        logger.info("Setting up error handlers")
        setup_error_handlers(api_app, include_tracebacks=uno_settings.debug)
        logger.info("Error handlers setup complete")

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

# Add middleware for error handling (can be used instead of or in addition to exception handlers)
# Uncomment if you prefer middleware approach for error handling
# api_app.add_middleware(
#     ErrorHandlingMiddleware,
#     include_tracebacks=uno_settings.debug
# )

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

        routes.append(
            {
                "path": route.path,
                "name": route.name,
                "methods": methods,
                "include_in_schema": getattr(route, "include_in_schema", "N/A"),
            }
        )

    return {"routes": routes}


# Add admin routes directly for testing
@api_app.get(
    "/admin", response_class=HTMLResponse, tags=["0KUI"], include_in_schema=False
)
async def admin_page(request: Request):
    """Admin dashboard page"""
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "site_name": "UNO Admin",
            "component": "okui-admin-dashboard",
        },
    )


@api_app.get("/admin-direct", response_class=HTMLResponse, tags=["0KUI"])
async def admin_direct(request: Request):
    """Direct admin page for testing"""
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "site_name": "UNO Admin (Direct)",
            "component": "okui-admin-dashboard",
        },
    )


# Add sub-admin routes for direct access
@api_app.get(
    "/admin/{module}",
    response_class=HTMLResponse,
    tags=["0KUI"],
    include_in_schema=False,
)
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
        "monitoring": "okui-system-monitor",
    }

    component = component_map.get(module, "okui-admin-dashboard")

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "site_name": f"UNO Admin: {module.title()}",
            "component": component,
        },
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
