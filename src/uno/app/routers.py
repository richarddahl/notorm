# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Type

from pydantic import BaseModel, computed_field

from fastapi import APIRouter, FastAPI, HTTPException, Request, Header, Depends, Body

from uno.db.enums import SelectResultType
from uno.config import settings


get_db = None


class SchemaRouter(BaseModel, ABC):
    obj_class: type[BaseModel]
    reponse_model: type[BaseModel]
    path_suffix: str
    method: str
    path_prefix: str = "/api"
    api_version: str = settings.API_VERSION
    include_in_schema: bool = True
    tags: list[str | Enum] | None = None
    return_list: bool = False

    def add_to_app(self, app: FastAPI):
        router = APIRouter()
        router.add_api_route(
            f"{self.path_prefix}/{self.api_version}/{self.obj_class.table.name}{self.path_suffix}",
            response_model=(
                self.reponse_model if not self.return_list else list[self.reponse_model]
            ),
            endpoint=self.endpoint,
            methods=[self.method],
            include_in_schema=self.include_in_schema,
            tags=[self.obj_class.display_name],
            summary=self.summary,
            description=self.description,
        )
        app.include_router(router)

    @abstractmethod
    def endpoint_factory(self, schema: type[BaseModel]):
        raise NotImplementedError


class InsertRouter(SchemaRouter):
    path_suffix: str = ""
    method: str = "POST"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Create a new {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Create a new {self.obj_class.display_name} using the __{self.obj_class.__name__.title()}Insert__ schema."

    @computed_field
    def response_model(self) -> BaseModel:
        return self.obj_class.insert_schema

    @classmethod
    def endpoint_factory(cls, body: type[BaseModel], response_model: type[BaseModel]):

        async def endpoint(self, object: BaseModel):
            return cls.response_model

        setattr(cls, "endpoint", endpoint)


class ListRouter(SchemaRouter):
    path_suffix: str = ""
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    return_list: bool = True
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"List {self.obj_class.display_name_plural}"

    @computed_field
    def description(self) -> str:
        return f"Returns a list of {self.obj_class.display_name_plural} in the __{self.obj_class.__name__.title()}List__ schema."

    @computed_field
    def response_model(self) -> BaseModel:
        return self.obj_class.list_schema

    @classmethod
    def endpoint_factory(cls, body: type[BaseModel], response_model: type[BaseModel]):

        async def endpoint(self) -> list[BaseModel]:
            results = await self.obj_class.db.list(schema=self.response_model)
            return results

        setattr(cls, "endpoint", endpoint)


class ImportRouter(SchemaRouter):
    path_suffix: str = ""
    method: str = "PUT"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    response_model: BaseModel | None = None

    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Import a new {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"""
            Import a new {self.obj_class.display_name} to the database.
            This will overwrite the all of the object's fields.
            Generally, this is used to import data from another
            instance of the database. The {self.obj_class.display_name} 
            data must be in the format of the
            __{self.obj_class.__name__.title()}Insert__ schema.   
        """

    @classmethod
    def endpoint_factory(cls, body: type[BaseModel], response_model: type[BaseModel]):

        async def endpoint(self, body: BaseModel):
            return cls.response_model

        setattr(cls, "endpoint", endpoint)


class UpdateRouter(SchemaRouter):
    path_suffix: str = "/{id}"
    method: str = "PATCH"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    response_model: BaseModel | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Update a new {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Update a {self.obj_class.display_name}, by its ID, using the __{self.obj_class.__name__.title()}Update__ schema."

    @classmethod
    def endpoint_factory(cls, body: type[BaseModel], response_model: type[BaseModel]):

        async def endpoint(self, id: str, body: BaseModel):
            return cls.response_model

        setattr(cls, "endpoint", endpoint)


class DeleteRouter(SchemaRouter):
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    response_model: BaseModel | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Delete a {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Delete a {self.obj_class.display_name}, by its ID, using the __{self.obj_class.__name__.title()}Delete__ schema."

    @classmethod
    def endpoint_factory(cls, body: type[BaseModel], response_model: type[BaseModel]):

        async def endpoint(self, id: str) -> type[BaseModel]:
            return {"message": "delete"}

        setattr(cls, "endpoint", endpoint)


class SelectRouter(SchemaRouter):
    path_suffix: str = "/{id}"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    # response_model: BaseModel | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Select a {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Select a {self.obj_class.display_name}, by its ID. Returns the __{self.obj_class.__name__.title()}Select__ schema."

    @computed_field
    def response_model(self) -> BaseModel:
        return self.obj_class.list_schema

    @classmethod
    def endpoint_factory(cls, body: type[BaseModel], response_model: type[BaseModel]):

        async def endpoint(
            self,
            id: str,
        ) -> BaseModel:
            result = await self.obj_class.db.select(
                "01JMYNF72N60R5RC1G61E30C1G",
                response_model=response_model,
                result_type=SelectResultType.FIRST,
            )
            if result is None:
                raise HTTPException(status_code=404, detail="Object not found")

            return result

        setattr(cls, "endpoint", endpoint)
