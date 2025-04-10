# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
import enum
from typing import Optional, ClassVar, Annotated

from pydantic import BaseModel, ConfigDict, computed_field
from fastapi import (
    FastAPI,
    status,
    APIRouter,
    HTTPException,
    Response,
    Request,
    Body,
    Depends,
    Query,
)

from uno.schema.schema import UnoSchema
from uno.errors import UnoRegistryError
from uno.settings import uno_settings


class UnoRouter(BaseModel, ABC):
    model: type[BaseModel]
    response_model: type[BaseModel] | None = None
    body_model: type[BaseModel] | None = None
    path_suffix: str
    method: str
    path_prefix: str = "/api"
    api_version: str = uno_settings.API_VERSION
    include_in_schema: bool = True
    tags: list[str | enum.StrEnum] | None = None
    return_list: bool = False
    app: FastAPI = None
    status_code: int = status.HTTP_200_OK

    model_config: dict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint_factory()
        router = APIRouter()
        router.add_api_route(
            f"{self.path_prefix}/{self.api_version}/{self.model.__name__.lower()}{self.path_suffix}",
            endpoint=self.endpoint,
            methods=[self.method],
            include_in_schema=self.include_in_schema,
            tags=[self.model.display_name_plural],
            summary=self.summary,
            description=self.description,
            status_code=self.status_code,
            response_model_exclude_none=True,
        )
        self.app.include_router(router)

    @abstractmethod
    def endpoint_factory(self):
        raise NotImplementedError


class ListRouter(UnoRouter):
    path_suffix: str = ""
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    return_list: bool = True
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"List {self.model.display_name_plural}"

    @computed_field
    def description(self) -> str:
        return f"Returns a list of {self.model.display_name_plural} with the __{self.model.__name__.title()}View__ schema."

    def endpoint_factory(self) -> None:
        filter_params = self.model.create_filter_params()

        async def endpoint(
            self,
            filter_params: Annotated[filter_params, Query()] = None,
        ) -> list[BaseModel]:

            # Validate the filters
            filters = self.model.validate_filter_params(filter_params)
            results = await self.model.filter(filters=filters)
            return results

        endpoint.__annotations__["return"] = list[self.response_model]
        setattr(self.__class__, "endpoint", endpoint)


class ImportRouter(UnoRouter):
    path_suffix: str = ""
    method: str = "PUT"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None

    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Import a new {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"""
            Import a new {self.model.display_name} to the database.
            This will overwrite the all of the object's fields.
            Generally, this is used to import data from another
            instance of the database. The {self.model.display_name} 
            data must be in the format of the
            __{self.model.__name__.title()}Insert__ schema.   
        """

    def endpoint_factory(self):

        async def endpoint(self, body: BaseModel):
            result = await self.model.save(body, importing=True)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class InsertRouter(UnoRouter):
    path_suffix: str = ""
    method: str = "POST"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Create a new {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Create a new {self.model.display_name} using the __{self.model.__name__.title()}Insert__ schema."

    def endpoint_factory(self):

        async def endpoint(self, body: BaseModel, response: Response) -> BaseModel:
            response.status_code = status.HTTP_201_CREATED
            result = await self.model.save(body)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class SelectRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Select a {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Select a {self.model.display_name}, by its ID. Returns the __{self.model.__name__.title()}Select__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str) -> BaseModel:
            result = await self.model.get(id=id)
            if result is None:
                raise HTTPException(status_code=404, detail="Object not found")
            return result

        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class UpdateRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "PATCH"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Update a new {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Update a {self.model.display_name}, by its ID, using the __{self.model.__name__.title()}Update__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str, body: BaseModel):
            result = await self.model.save(body)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class DeleteRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Delete a {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Delete a {self.model.display_name}, by its ID, using the __{self.model.__name__.title()}Delete__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str) -> BaseModel:
            result = await self.model.delete_(id)
            return {"message": "delete"}

        endpoint.__annotations__["return"] = bool
        setattr(self.__class__, "endpoint", endpoint)


class UnoEndpoint(BaseModel):
    registry: ClassVar[dict[str, "UnoEndpoint"]] = {}

    model: type[BaseModel]
    router: UnoRouter
    body_model: Optional[str | None] = None
    response_model: Optional[str]
    include_in_schema: bool = True
    status_code: int = 200

    model_config: ConfigDict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, app: FastAPI, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Retrieve schemas from the model's schema_manager
        if self.body_model is not None:
            # Ensure that the schemas have been created
            body_schema = self.model.schema_manager.get_schema(self.body_model)
            if body_schema is None:
                raise Exception(
                    f"Body schema '{self.body_model}' not found in schema manager for {self.model.__name__}"
                )
        else:
            body_schema = None

        if self.response_model is not None:
            response_schema = self.model.schema_manager.get_schema(self.response_model)
            if response_schema is None:
                raise Exception(
                    f"Response schema '{self.response_model}' not found in schema manager"
                )
        else:
            response_schema = None

        self.router(
            app=app,
            model=self.model,
            body_model=body_schema,
            response_model=response_schema,
            include_in_schema=self.include_in_schema,
            status_code=self.status_code,
        )

    def __init_subclass__(cls, **kwargs) -> None:

        super().__init_subclass__(**kwargs)
        # Don't add the UnoEndpoint class itself to the registry
        if cls is UnoEndpoint:
            return
        # Add the subclass to the registry if it is not already there
        if cls.__name__ not in cls.registry:
            cls.registry.update({cls.__name__: cls})
        else:
            raise UnoRegistryError(
                f"An Endpoint class with the name {cls.__name__} already exists in the registry.",
                "DUPLICATE_ENDPOINT",
            )


class CreateEndpoint(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoSchema = "edit_schema"
    response_model: UnoSchema = "view_schema"
    status_code: int = status.HTTP_201_CREATED


class ViewEndpoint(UnoEndpoint):
    router: UnoRouter = SelectRouter
    body_model: UnoSchema = None
    response_model: UnoSchema = "view_schema"


class ListEndpoint(UnoEndpoint):
    router: UnoRouter = ListRouter
    body_model: UnoSchema = None
    response_model: UnoSchema = "view_schema"


class UpdateEndpoint(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoSchema = "edit_schema"
    response_model: UnoSchema = "view_schema"


class DeleteEndpoint(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    body_model: UnoSchema = None
    response_model: UnoSchema = None


class ImportEndpoint(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoSchema = "view_schema"
    response_model: UnoSchema = "view_schema"
    status_code: int = status.HTTP_201_CREATED
