# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from uno.config import settings

from uno.db.management.db_manager import DBManager
from uno.db.base import Base


tags_metadata = [
    {
        "name": "0kui",
        "description": "Zero Knowledge User Interface routers.",
        "externalDocs": {
            "description": "uno 0kui docs",
            "url": "http://localhost:8001/okui/",
        },
    },
    {
        "name": "authorization",
        "description": "Manage Users, Roles, Groups etc...",
        "externalDocs": {
            "description": "uno auth docs",
            "url": "http://localhost:8001/authorization/models",
        },
    },
]
app = FastAPI(
    openapi_tags=tags_metadata,
    title="Uno is not an ORM",
    summary="fasterAPI.",
    # description="""
    #    Build fastAPI apps faster and DRYer.
    #    uno leverages sqlalchemy, postgreSQL, apacheAGE, supa-audit, and pydantic to:
    #        Provide authorization and auditing
    #        Generate routes
    #        Provide a simple mechanism for complex filtering and sorting data
    #    So developers can focus on business logic.
    #    """,
    # version="0.0.1",
    # terms_of_service="http://example.com/terms/",
    # contact={
    #    "name": "Richard Dahl",
    #    "url": "https://notorm.tech",
    #    "email": "info@notorm.tech",
    # },
    # license_info={
    #    "name": "MIT",
    #    "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    # },
)


for base in Base.registry.mappers:
    for router in base.class_.routers:
        router.add_to_app(app=app)

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
