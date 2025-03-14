# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import importlib

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uno.db.base import UnoBase
from uno.api.endpoint import UnoEndpoint
from uno.model.model import UnoModel
from uno.apps.fltr.models import UnoFilter
from uno.api.app_def import app
from uno.config import settings

from uno.apps.auth.models import User, Group, Tenant, Role

for module in settings.LOAD_MODULES:
    globals()[f"{module.split('.')[2]}._bases"] = importlib.import_module(
        f"{module}.bases"
    )

for model in UnoModel.registry.values():
    if hasattr(model, "configure"):
        model.configure(app)


templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get("/app", response_class=HTMLResponse, tags=["0KUI"])
async def app_base(
    request: Request,  # , settings: Annotated[settings, Depends(get_settings)]
):
    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "authentication_url": "/api/auth/login",
            "site_name": settings.SITE_NAME,
        },
    )


@app.get(
    "/app/filters/{object_name}",
    tags=["0KUI"],
    summary="Get filters for an object by object name",
)
def get_filters(object_name: str) -> list[UnoFilter]:
    """Retrieve the generated OpenAPI schema."""
    filters = UnoModel.registry[object_name.title()].filters
    keys = list(filters.keys())
    keys.sort()
    f = {key: filters[key] for key in keys}
    return f.values()


def generate_openapi_schema():
    """Generate the OpenAPI schema for the FastAPI application."""
    return get_openapi(
        title="My API",
        version="1.0.0",
        description="UNO API",
        routes=app.routes,
    )


@app.get(
    "/app/schema",
    response_class=JSONResponse,
    tags=["0KUI"],
    summary="Get the OpenAPI schema",
    description="Retrieve the generated OpenAPI schema.",
)
def get_openapi_endpoint():
    """Retrieve the generated OpenAPI schema."""
    return JSONResponse(content=generate_openapi_schema())


@app.get(
    "/app/schema/{schema_name}",
    response_class=JSONResponse,
    tags=["0KUI"],
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
