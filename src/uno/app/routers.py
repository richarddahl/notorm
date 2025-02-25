# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from enum import Enum
from typing import Any

from sqlalchemy import select, func, Table
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, ConfigDict, computed_field

from fastapi import APIRouter, FastAPI, HTTPException, Request, Header, Depends

from uno.config import settings


get_db = None


class SchemaRouter(BaseModel):
    klass: Any
    path_suffix: str
    method: str
    endpoint: str
    path_prefix: str = "/api"
    api_version: str = settings.API_VERSION
    include_in_schema: bool = True
    tags: list[str | Enum] | None = None
    return_list: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def table(self) -> Table:
        return self.klass.table

    def add_to_app(self, schema: BaseModel, app: FastAPI):
        router = APIRouter()
        router.add_api_route(
            f"{self.path_prefix}/{self.api_version}/{self.klass.table.name}{self.path_suffix}",
            response_model=schema if not self.return_list else list[schema],
            endpoint=getattr(self, self.endpoint),
            methods=[self.method],
            include_in_schema=self.include_in_schema,
            tags=[self.klass.display_name],
            summary=self.summary,
            description=self.description,
        )
        app.include_router(router)


class PostRouter(SchemaRouter):
    path_suffix: str = ""
    method: str = "POST"
    endpoint: str = "post"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field
    # table: Table | None = None <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Create a new {self.klass.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Create a new {self.klass.display_name} in the database"

    @computed_field
    def response_model(self) -> BaseModel:
        return self.klass.insert_schema

    async def post(
        self,
        request: Request,
    ) -> dict:
        data = await request.json()
        return self.response_model


class ListRouter(SchemaRouter):
    path_suffix: str = ""
    method: str = "GET"
    endpoint: str = "list_"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    return_list: bool = True
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field
    # table: Table | None = None <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"List {self.klass.display_name}"

    @computed_field
    def description(self) -> str:
        return f"List {self.klass.display_name} from the database"

    @computed_field
    def response_model(self) -> BaseModel:
        return self.klass.list_schema

    async def list_(self) -> list["ListSchemaBase"]:
        results = await self.klass.db.list(schema=self.response_model)
        return results


class PutRouter(SchemaRouter):
    path_suffix: str = ""
    method: str = "PUT"
    endpoint: str = "put"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    response_model: BaseModel | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field
    # table: Table | None = None <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Import a new {self.klass.display_name}"

    @computed_field
    def description(self) -> str:
        return f"""
            Import a new {self.klass.display_name} to the database.
            This will overwrite the all of the object's fields.
            Generally, this is used to import data from another
            instance of the database.
        """

    def put(self):
        return self.response_model


class PatchRouter(SchemaRouter):
    path_suffix: str = "/{id}"
    method: str = "PATCH"
    endpoint: str = "patch"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    response_model: BaseModel | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field
    # table: Table | None = None <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Update a new {self.klass.display_name} by its id"

    @computed_field
    def description(self) -> str:
        return f"Update a new {self.klass.display_name} by its id in the database"

    def patch(self):
        return self.response_model


class DeleteRouter(SchemaRouter):
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    endpoint: str = "delete"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    response_model: BaseModel | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field
    # table: Table | None = None <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Delete a {self.klass.display_name} by its id"

    @computed_field
    def description(self) -> str:
        return f"Delete a {self.klass.display_name} by its id from the database"

    def delete(self):
        return {"message": "delete"}


class SelectRouter(SchemaRouter):
    path_suffix: str = "/{id}"
    method: str = "GET"
    endpoint: str = "get_by_id"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    response_model: BaseModel | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field
    # table: Table | None = None <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Select a {self.klass.display_name} by its id"

    @computed_field
    def description(self) -> str:
        return f"Select a {self.klass.display_name} by its id from the database"

    async def get_by_id(
        self,
        id: str,
    ):
        result = await db.execute(select(self.table).filter_by(id=id))
        obj = result.scalar()
        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")
        return self.response_model
