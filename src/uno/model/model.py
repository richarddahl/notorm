# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from datetime import date, datetime, time
from decimal import Decimal
from typing import ClassVar, Literal, Any
from pydantic import BaseModel, ConfigDict
from fastapi import FastAPI
from sqlalchemy.inspection import inspect

from uno.db.enums import object_lookups, numeric_lookups, text_lookups
from uno.db.base import UnoBase
from uno.model.schema import UnoSchemaConfig, UnoSchema
from uno.api.endpoint import (
    CreateEndpoint,
    ViewEndpoint,
    SummaryEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
    ImportEndpoint,
)
from uno.apps.fltr.models import Filter
from uno.errors import UnoRegistryError
from uno.utilities import convert_snake_to_title
from uno.config import settings


class UnoModel(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    registry: ClassVar[dict[str, "UnoModel"]] = {}
    base: ClassVar[UnoBase] = None
    table_name: ClassVar[str] = None
    display_name: ClassVar[str] = None
    display_name_plural: ClassVar[str] = None
    schema_configs: ClassVar[dict[str, "UnoSchemaConfig"]] = {}
    view_schema: ClassVar[UnoSchema] = None
    edit_schema: ClassVar[UnoSchema] = None
    summary_schema: ClassVar[UnoSchema] = None
    endpoints: ClassVar[list[str]] = [
        "Create",
        "View",
        "Summary",
        "Update",
        "Delete",
        "Import",
    ]
    filters: ClassVar[dict[str, Filter]] = {}
    filter_excludes: ClassVar[list[str]] = []

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

    # End of __init_subclass__

    @classmethod
    def relationships(cls) -> list[Any]:
        return [relationship for relationship in inspect(cls.base).relationships]

    @classmethod
    def configure(cls, app: FastAPI) -> None:
        """Configure the UnoModel class"""
        cls.set_schemas()
        cls.set_endpoints(app)
        cls.set_filters()

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

    @classmethod
    def set_endpoints(cls, app: FastAPI) -> None:

        for endpoint in cls.endpoints:
            if endpoint == "Create":
                CreateEndpoint(obj_class=cls, app=app)
            elif endpoint == "View":
                ViewEndpoint(obj_class=cls, app=app)
            elif endpoint == "Summary":
                SummaryEndpoint(obj_class=cls, app=app)
            elif endpoint == "Update":
                UpdateEndpoint(obj_class=cls, app=app)
            elif endpoint == "Delete":
                DeleteEndpoint(obj_class=cls, app=app)
            elif endpoint == "Import":
                ImportEndpoint(obj_class=cls, app=app)

    @classmethod
    def set_filters(cls) -> None:
        filters = {}
        if not hasattr(cls.base, "__table__"):
            return
        for field_name, field in cls.base.__table__.columns.items():
            if field_name in cls.filter_excludes:
                continue
            if field.type.python_type in [str, bytes]:
                lookups = text_lookups
            elif field.type.python_type in [int, Decimal, float, date, datetime, time]:
                lookups = numeric_lookups
            else:
                lookups = object_lookups
            filters.update(
                {
                    field_name: UnoFilter(
                        label=field_name.replace("_", " ").title(),
                        accessor=field_name,
                        filter_type="Property",
                        lookups=lookups,
                    )
                }
            )

        for relationship in cls.relationships():
            if relationship.key in cls.filter_excludes:
                continue
            if not relationship.info.get("edge", False):
                continue
            filters.update(
                {
                    relationship.key: UnoFilter(
                        label=relationship.key.replace("_id", "")
                        .replace("_", " ")
                        .title(),
                        accessor=relationship.info.get("edge", "MISSING_EDGE"),
                        filter_type="Edge",
                        lookups=object_lookups,
                        remote_table_name=relationship.mapper.class_.__tablename__,
                    )
                }
            )
        setattr(cls, "filters", filters)
