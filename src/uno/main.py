# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from uno.config import settings


import uno.attr.tables as attrs_tables
import uno.auth.tables as auth_tables
import uno.msg.tables as comms_tables
import uno.grph.tables as fltrs_tables
import uno.obj.tables as objs_tables
import uno.rprt.tables as rprts_tables
import uno.wkflw.tables as wrkflws_tables


tags_metadata = [
    {
        "name": "0kui",
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


templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get("/app", response_class=HTMLResponse, tags=["0kui"])
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


auth_tables.User.create_schemas(app)
