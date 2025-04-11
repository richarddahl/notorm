# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import importlib
import logging
import asyncio

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uno.registry import UnoRegistry
from uno.api.apidef import app
from uno.settings import uno_settings

from uno.attributes import objs as attr_models
from uno.authorization import objs as auth_models
from uno.queries import models as fltr_models
from uno.meta import objs as meta_models
from uno.messaging import objs as msg_models
from uno.reports import objs as rpt_models
from uno.values import objs as val_models
from uno.workflows import models as wkflw_models

# Configure the modern dependency injection system with FastAPI
from uno.dependencies.fastapi_integration import configure_fastapi
configure_fastapi(app)

# Add lifespan event handlers for FastAPI
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    # Initialize the modern dependency injection system
    from uno.dependencies.modern_provider import initialize_services
    await initialize_services()
    logging.info("Modern DI Service Provider initialized")

    # Register services using automatic discovery (optional)
    from uno.dependencies.discovery import register_services_in_package
    try:
        # Discover and register services in the application
        register_services_in_package("uno.domain")
        register_services_in_package("uno.entity_services")
        logging.info("Service discovery completed")
    except Exception as e:
        logging.error(f"Error during service discovery: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on application shutdown."""
    # Shut down the modern dependency injection system
    from uno.dependencies.modern_provider import shutdown_services
    await shutdown_services()
    logging.info("DI Service Provider shut down")

# Get registry from Service Provider
from uno.dependencies.modern_provider import get_service_provider
provider = get_service_provider()

# Wait for the provider to be initialized
async def ensure_provider_initialized():
    """Ensure the service provider is initialized."""
    if not provider.is_initialized():
        await initialize_services()
    return provider

# Create a synchronous version for use in the main application
def get_initialized_provider():
    """Get the initialized service provider."""
    if not provider.is_initialized():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(initialize_services())
        loop.close()
    return provider

# Get the initialized provider
provider = get_initialized_provider()
registry = provider.get_service(UnoRegistry)

# Load all models
for obj_name, obj in registry.get_all().items():
    if hasattr(obj, "configure"):
        obj.configure(app)

# Include endpoints implemented with dependency injection pattern
# These endpoints demonstrate the DI pattern as an alternative to UnoObj

# Authorization endpoints
from uno.authorization.endpoints import router as auth_router
app.include_router(auth_router)

# Meta endpoints
from uno.meta.endpoints import router as meta_router
app.include_router(meta_router)

# Vector search endpoints (if available)
try:
    from uno.vector_search.endpoints import router as vector_router
    app.include_router(vector_router)
    logging.info("Vector search endpoints included")
except ImportError:
    logging.debug("Vector search endpoints not available")

# Example domain endpoints using modern dependency injection
try:
    from uno.domain.api_example import router as example_router
    app.include_router(example_router)
    logging.info("Example domain endpoints included")
except ImportError:
    logging.debug("Example domain endpoints not available")

templates = Jinja2Templates(directory="src/templates")

app.mount(
    "/static",
    StaticFiles(directory="src/static"),
    name="static",
)

# Example of an endpoint using the new dependency injection system
from uno.dependencies.decorators import inject_params
from uno.dependencies.interfaces import UnoConfigProtocol

@app.get("/app", response_class=HTMLResponse, tags=["0KUI"])
@inject_params()
async def app_base(
    request: Request, 
    config: UnoConfigProtocol
):
    """Render the main application page."""
    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "authentication_url": "/api/auth/login",
            "site_name": config.get_value("SITE_NAME", "Uno Application"),
        },
    )

def generate_openapi_schema():
    """Generate the OpenAPI schema for the FastAPI application."""
    return get_openapi(
        title="My API",
        version="1.0.0",
        description="Uno API",
        routes=app.routes,
    )

@app.get(
    "/api/v1.0/schema",
    response_class=JSONResponse,
    tags=["Schemas"],
    summary="Get the OpenAPI schema",
    description="Retrieve the generated OpenAPI schema.",
)
def get_openapi_endpoint():
    """Retrieve the generated OpenAPI schema."""
    return JSONResponse(content=generate_openapi_schema())

@app.get(
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
        routes=app.routes,
    )

    schemas = openapi_schema.get("components", {}).get("schemas", {})

    if schema_name not in schemas:
        raise HTTPException(status_code=404, detail="Schema not found")

    schema = schemas[schema_name]

    return JSONResponse(content=schema)
