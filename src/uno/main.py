# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uno.config import settings


import uno.glbl.tables as glbl_tables
import uno.attr.tables as attrs_tables
import uno.auth.tables as auth_tables

import uno.msg.tables as comms_tables
import uno.fltr.tables as fltrs_tables

import uno.rprt.tables as rprts_tables
import uno.wkflw.tables as wrkflws_tables


tags_metadata = [
    {
        "name": "0KUI",
        "description": "Zero Knowledge User Interface.",
        "externalDocs": {
            "description": "uno 0kui docs",
            "url": "http://localhost:8001/okui/",
        },
    },
    {
        "name": "auth",
        "description": "Manage Users, Roles, Groups etc...",
        "externalDocs": {
            "description": "uno auth docs",
            "url": "http://localhost:8001/auth/models",
        },
    },
]
app = FastAPI(
    openapi_tags=tags_metadata,
    title="Uno is not an ORM",
)


auth_tables.User.configure_base(app)
auth_tables.Tenant.configure_base(app)
auth_tables.Role.configure_base(app)
auth_tables.Group.configure_base(app)

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
    response_class=JSONResponse,
    tags=["0KUI"],
    summary="Get filters for an object by object name",
)
def get_filters():
    """Retrieve the generated OpenAPI schema."""
    auth_tables.User.filters
    return JSONResponse(content=auth_tables.User.filters)


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
