# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

import datetime

from typing import ClassVar, Optional
from pydantic import BaseModel, ConfigDict

from uno.model.schema import UnoSchemaConfig, UnoSchema
from uno.errors import UnoRegistryError
from uno.utilities import convert_snake_to_title
from uno.config import settings


class UnoModel(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    registry: ClassVar[dict[str, "UnoModel"]] = {}
    table_name: ClassVar[str] = None
    display_name: ClassVar[str] = None
    display_name_plural: ClassVar[str] = None
    schema_configs: ClassVar[dict[str, "UnoSchemaConfig"]] = {}
    view_schema: ClassVar[UnoSchema] = None
    edit_schema: ClassVar[UnoSchema] = None
    summary_schema: ClassVar[UnoSchema] = None

    def __init_subclass__(cls, **kwargs) -> None:

        super().__init_subclass__(**kwargs)
        # Don't add the UnoModel class itself to the registry
        if cls is UnoModel:
            return
        # Add the subclass to the registry if it is not already there
        if cls.__name__ not in cls.registry:
            cls.registry.update({cls.__name__: cls})
        else:
            raise UnoRegistryError(
                f"A Model class with the name {cls.__name__} already exists in the registry.",
                "MODEL_CLASS_EXISTS_IN_REGISTRY",
            )
        cls.set_display_names()

    @classmethod
    def configure(cls) -> None:
        """Configure the UnoModel class"""
        cls.set_schemas()

    # End of __init_subclass__

    @classmethod
    def set_display_names(cls) -> None:

        cls.display_name = (
            convert_snake_to_title(cls.table_name)
            if cls.display_name is None
            else cls.display_name
        )
        cls.display_name_plural = (
            f"{convert_snake_to_title(cls.table_name)}s"
            if cls.display_name_plural is None
            else cls.display_name_plural
        )

    @classmethod
    def set_schemas(cls) -> None:

        for schema_name, schema_config in cls.schema_configs.items():
            setattr(
                cls,
                schema_name,
                schema_config.create_schema(
                    schema_name=schema_name,
                    model=cls,
                ),
            )


class GeneralModelMixin(BaseModel):
    """Mixin for General Objects"""

    id: Optional[str] = None
    is_active: Optional[bool] = True
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime.datetime] = None
    created_by: Optional["User"] = None
    modified_at: Optional[datetime.datetime] = None
    modified_by: Optional["User"] = None
    deleted_at: Optional[datetime.datetime] = None
    deleted_by: Optional["User"] = None
