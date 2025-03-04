# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.fields import Field

from fastapi import FastAPI

from uno.app.routers import UnoRouter


class UnoModel(BaseModel, ABC):
    uno_obj: ClassVar[BaseModel]
    modelname: ClassVar[str]

    @abstractmethod
    def before_db_operation(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def after_db_operation(self) -> None:
        raise NotImplementedError


class UnoEndpoint(BaseModel):
    obj_class: type[BaseModel]
    app: FastAPI
    router: UnoRouter  # = Field(default_factory=set_router)
    body_model: Optional[UnoModel]
    response_model: UnoModel
    include_in_api: bool = True
    status_code: int = 200

    model_config: ConfigDict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.router(
            obj_class=self.obj_class,
            response_model=self.response_model,
            body_model=self.body_model,
            app=self.app,
            include_in_schema=self.include_in_api,
            status_code=self.status_code,
        )
