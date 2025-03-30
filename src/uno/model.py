# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

import decimal
import datetime
from typing import ClassVar, Optional, Any
from pydantic import BaseModel, ConfigDict

from fastapi import FastAPI
from sqlalchemy import Column

from uno.db import UnoDBFactory
from uno.db import UnoBase
from uno.schema import UnoSchemaConfig, UnoSchema
from uno.endpoint import (
    CreateEndpoint,
    ViewEndpoint,
    ListEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
    ImportEndpoint,
)
from uno.errors import UnoRegistryError
from uno.utilities import (
    snake_to_title,
    snake_to_camel,
    snake_to_caps_snake,
)
from uno.enums import (
    object_lookups,
    numeric_lookups,
    text_lookups,
)
from uno.filter import UnoFilter


class UnoModel(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    registry: ClassVar[dict[str, "UnoModel"]] = {}
    db: ClassVar["UnoDB"]
    base: ClassVar[type[UnoBase]]
    # table_name: ClassVar[str] = None
    exclude_from_filters: ClassVar[bool] = False
    terminate_filters: ClassVar[bool] = False
    display_name: ClassVar[str] = None
    display_name_plural: ClassVar[str] = None
    schema_configs: ClassVar[dict[str, "UnoSchemaConfig"]] = {}
    view_schema: ClassVar[UnoSchema] = None
    edit_schema: ClassVar[UnoSchema] = None
    view_schema: ClassVar[UnoSchema] = None
    endpoints: ClassVar[list[str]] = [
        "Create",
        "View",
        "List",
        "Update",
        "Delete",
        "Import",
    ]
    endpoint_tags: ClassVar[list[str]] = []
    filters: ClassVar[dict[str, UnoFilter]] = {}
    terminate_field_filters: ClassVar[list[str]] = []

    def __init_subclass__(cls, **kwargs) -> None:

        super().__init_subclass__(**kwargs)
        # Don't add the UnoModel class itself to the registry
        if cls is UnoModel:
            return
        # Add the subclass to the registry if it is not already there
        if cls.base.__tablename__ not in cls.registry:
            cls.registry.update({cls.base.__tablename__: cls})
        else:
            raise UnoRegistryError(
                f"A Model class with the table name {cls.base.__tablename__} already exists in the registry.",
                "DUPLICATE_MODEL",
            )
        cls.set_display_names()
        cls.db = UnoDBFactory(base=cls.base, model=cls)

    # End of __init_subclass__

    @classmethod
    def configure(cls, app: FastAPI) -> None:
        """Configure the UnoModel class"""
        cls.set_filters()
        cls.set_schemas()
        cls.set_endpoints(app)

    @classmethod
    def set_display_names(cls) -> None:
        cls.display_name = (
            snake_to_title(cls.base.__table__.name)
            if cls.display_name is None
            else cls.display_name
        )
        cls.display_name_plural = (
            f"{snake_to_title(cls.base.__table__.name)}s"
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
                CreateEndpoint(model=cls, app=app)
            elif endpoint == "View":
                ViewEndpoint(model=cls, app=app)
            elif endpoint == "List":
                ListEndpoint(model=cls, app=app)
            elif endpoint == "Update":
                UpdateEndpoint(model=cls, app=app)
            elif endpoint == "Delete":
                DeleteEndpoint(model=cls, app=app)
            elif endpoint == "Import":
                ImportEndpoint(model=cls, app=app)

    @classmethod
    def set_filters(cls) -> None:
        table = cls.base.__table__

        def create_filter_for_column(
            column: Column,
            edge: str = "edge",
        ) -> UnoFilter:
            if column.type.python_type in [str, bytes]:
                lookups = text_lookups
            elif column.type.python_type in [
                int,
                decimal.Decimal,
                float,
                datetime.date,
                datetime.datetime,
                datetime.time,
            ]:
                lookups = numeric_lookups
            else:
                lookups = object_lookups
            if column.foreign_keys:
                if edge == "edge":
                    source_node = snake_to_camel(column.table.name)
                    destination_node = snake_to_camel(
                        list(column.foreign_keys)[0].column.table.name
                    )
                    label = snake_to_caps_snake(
                        column.info.get(edge, column.name.replace("_id", ""))
                    )
                else:
                    return None
            else:
                source_node = snake_to_camel(table.name)
                destination_node = snake_to_camel(column.name)
                label = snake_to_caps_snake(
                    column.info.get(edge, column.name.replace("_id", ""))
                )
            return UnoFilter(
                source_node=source_node,
                label=label,
                destination_node=destination_node,
                data_type=column.type.python_type.__name__,
                lookups=lookups,
            )

        filters = {}
        if "id" in table.columns.keys():
            fltr = UnoFilter(
                source_node=snake_to_camel(table.name),
                label=snake_to_caps_snake(
                    table.columns["id"].info.get("edge", table.name)
                ),
                destination_node="MetaRecord",
                data_type="str",
                lookups=object_lookups,
            )
            filter_key = f"{fltr.source_node}{fltr.label}{fltr.destination_node}"
            filters[filter_key] = fltr
        for column in table.columns.values():
            if column.info.get("graph_excludes", False):
                continue
            if fltr := create_filter_for_column(column):
                filter_key = f"{fltr.source_node}{fltr.label}{fltr.destination_node}"
                if filter_key not in filters.keys():
                    filters[filter_key] = fltr
        cls.filters = filters
