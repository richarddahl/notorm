# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, ClassVar
from pydantic import BaseModel, ConfigDict
from fastapi import FastAPI, status

from uno.model.schema import UnoSchema
from uno.api.router import (
    UnoRouter,
    InsertRouter,
    ListRouter,
    SelectRouter,
    UpdateRouter,
    DeleteRouter,
    ImportRouter,
)
from uno.errors import UnoRegistryError


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
        if self.body_model is not None:
            body_model = getattr(self.model, self.body_model)
        else:
            body_model = None
        if self.response_model is not None:
            response_model = getattr(self.model, self.response_model)
        else:
            response_model = None
        self.router(
            app=app,
            model=self.model,
            body_model=body_model,
            response_model=response_model,
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
