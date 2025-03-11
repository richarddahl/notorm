# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, ClassVar

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from fastapi import FastAPI

from uno.model.model import UnoModel
from uno.model.schema import UnoSchema
from uno.api.router import UnoRouter
from uno.errors import UnoRegistryError


class UnoEndpoint(BaseModel):
    registry: ClassVar[dict[str, "UnoEndpoint"]] = {}

    obj_class: type[UnoModel]
    router: UnoRouter
    body_model: Optional[str | None] = None
    response_model: Optional[str]
    include_in_schema: bool = True
    status_code: int = 200

    model_config: ConfigDict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, app: FastAPI, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.body_model is not None:
            body_model = getattr(self.obj_class, self.body_model)
        else:
            body_model = None
        if self.response_model is not None:
            response_model = getattr(self.obj_class, self.response_model)
        else:
            response_model = None
        self.router(
            app=app,
            obj_class=self.obj_class,
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
                "ENDPOINT_CLASS_EXISTS_IN_REGISTRY",
            )
