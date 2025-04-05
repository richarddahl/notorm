# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import importlib

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uno.obj import UnoObj
from uno.apidef import app
from uno.config import settings

from uno.attr import objects as attr_models
from uno.auth import objects as auth_models
from uno.qry import models as fltr_models
from uno.meta import objects as meta_models
from uno.msg import objects as msg_models
from uno.rprt import objects as rpt_models
from uno.val import objects as val_models

# from uno.wkflw import models as wkflw_models


for model in UnoObj.registry.values():
    if hasattr(model, "configure"):
        model.configure(app)


templates = Jinja2Templates(directory="src/templates")

app.mount(
    "/static",
    StaticFiles(directory="src/static"),
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
