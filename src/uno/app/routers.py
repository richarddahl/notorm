# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from pydantic import BaseModel, computed_field

from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Response,
    status,
)

from uno.config import settings


class UnoRouter(BaseModel, ABC):
    obj_class: type[BaseModel]
    response_model: type[BaseModel] | None = None
    body_model: type[BaseModel] | None = None
    path_suffix: str
    method: str
    path_prefix: str = "/api"
    api_version: str = settings.API_VERSION
    include_in_schema: bool = True
    tags: list[str | Enum] | None = None
    return_list: bool = False
    app: FastAPI = None
    status_code: int = status.HTTP_200_OK

    model_config: dict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint_factory()
        router = APIRouter()
        router.add_api_route(
            f"{self.path_prefix}/{self.api_version}/{self.obj_class.table.name}{self.path_suffix}",
            endpoint=self.endpoint,
            methods=[self.method],
            include_in_schema=self.include_in_schema,
            tags=[self.obj_class.display_name],
            summary=self.summary,
            description=self.description,
            status_code=self.status_code,
        )
        self.app.include_router(router)

    @abstractmethod
    def endpoint_factory(self):
        raise NotImplementedError


class SummaryRouter(UnoRouter):
    path_suffix: str = "summary"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    return_list: bool = True
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"List {self.obj_class.display_name} Summary"

    @computed_field
    def description(self) -> str:
        return f"Returns a list of {self.obj_class.display_name_plural} with the __{self.obj_class.__name__.title()}Summary__ schema."

    def endpoint_factory(self):

        async def endpoint(self) -> list[BaseModel]:
            results = await self.obj_class.select(response_model=self.response_model)
            return results

        endpoint.__annotations__["return"] = list[self.response_model]
        setattr(self.__class__, "endpoint", endpoint)


class ImportRouter(UnoRouter):
    path_suffix: str = ""
    method: str = "PUT"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None

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

    def endpoint_factory(self):

        async def endpoint(self, body: BaseModel):
            result = await self.obj_class.db.import_(body)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class InsertRouter(UnoRouter):
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

    def endpoint_factory(self):

        async def endpoint(self, body: BaseModel, response: Response) -> BaseModel:
            response.status_code = status.HTTP_201_CREATED
            result = await self.obj_class.db.insert(body)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class SelectRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Select a {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Select a {self.obj_class.display_name}, by its ID. Returns the __{self.obj_class.__name__.title()}Select__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str) -> BaseModel:
            result = await self.obj_class.select(self.response_model, id=id)
            if result is None:
                raise HTTPException(status_code=404, detail="Object not found")
            return result

        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class UpdateRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "PATCH"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Update a new {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Update a {self.obj_class.display_name}, by its ID, using the __{self.obj_class.__name__.title()}Update__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str, body: BaseModel):
            result = await self.obj_class().update_by_id(id, body)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class DeleteRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    path_prefix: str = "/api"
    tags: list[str | Enum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Delete a {self.obj_class.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Delete a {self.obj_class.display_name}, by its ID, using the __{self.obj_class.__name__.title()}Delete__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str) -> BaseModel:
            result = await self.obj_class().delete_by_id(id)
            return {"message": "delete"}

        endpoint.__annotations__["return"] = bool
        setattr(self.__class__, "endpoint", endpoint)
