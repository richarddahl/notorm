# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from datetime import date, datetime, time
from decimal import Decimal
from typing import ClassVar, Any
from pydantic import BaseModel, ConfigDict, create_model
from fastapi import FastAPI
from sqlalchemy.inspection import inspect

from uno.db.db import UnoDBFactory
from uno.apps.val.enums import (
    object_lookups,
    numeric_lookups,
    text_lookups,
)
from uno.db.base import UnoBase
from uno.model.schema import UnoSchemaConfig, UnoSchema
from uno.api.endpoint import (
    CreateEndpoint,
    ViewEndpoint,
    ListEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
    ImportEndpoint,
)
from uno.apps.fltr.filter import Filter
from uno.errors import UnoRegistryError
from uno.utilities import (
    convert_snake_to_title,
    convert_snake_to_all_caps_snake,
    convert_snake_to_camel,
)
from uno.config import settings


class UnoModel(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    registry: ClassVar[dict[str, "UnoModel"]] = {}
    db: ClassVar["UnoDB"]
    base: ClassVar[UnoBase]
    table_name: ClassVar[str] = None
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
    filters: ClassVar[dict[str, BaseModel]] = {}
    filter_excludes: ClassVar[list[str]] = []
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
                "MODEL_CLASS_EXISTS_IN_REGISTRY",
            )
        cls.set_display_names()
        cls.db = UnoDBFactory(base=cls.base, model=cls)

    # End of __init_subclass__

    @classmethod
    def relationships(cls) -> list[Any]:
        return [relationship for relationship in inspect(cls.base).relationships]

    @classmethod
    def configure(cls, app: FastAPI) -> None:
        """Configure the UnoModel class"""
        cls.set_schemas()
        cls.set_endpoints(app)
        # cls.set_filters()

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
    def set_filters(cls, parent: Filter = None) -> None:
        if parent is None:
            klass = cls
        else:
            klass = parent.source_model
        filters = {}
        if not hasattr(klass.base, "__table__"):
            return
        for column_name, column in klass.base.__table__.columns.items():
            if column_name in klass.filter_excludes:
                continue
            if column.type.python_type in [str, bytes]:
                lookups = text_lookups
            elif column.type.python_type in [int, Decimal, float, date, datetime, time]:
                lookups = numeric_lookups
            else:
                lookups = object_lookups
            filters.update(
                {
                    column_name: Filter(
                        source_model=UnoModel.registry[klass.base.__tablename__],
                        remote_model=UnoModel.registry[klass.base.__tablename__],
                        label=convert_snake_to_all_caps_snake(column_name),
                        data_type=column.type.python_type.__name__,
                        source_table_name=klass.base.__tablename__,
                        source_node=convert_snake_to_camel(klass.base.__tablename__),
                        source_column_name="id",
                        remote_table_name=klass.base.__tablename__,
                        remote_column_name=column_name,
                        remote_node=convert_snake_to_camel(column_name),
                        accessor=column_name,
                        filter_type="Column",
                        lookups=lookups,
                    )
                }
            )

        for relationship in klass.relationships():
            if relationship.key in klass.filter_excludes:
                continue
            if not relationship.info.get("edge", False):
                continue
            accessor = relationship.info.get("edge")
            filter = Filter(
                source_model=UnoModel.registry[klass.base.__tablename__],
                remote_model=UnoModel.registry[
                    relationship.mapper.class_.__tablename__
                ],
                label=convert_snake_to_all_caps_snake(relationship.info.get("edge")),
                data_type="str",
                source_table_name=klass.base.__tablename__,
                source_node=convert_snake_to_camel(klass.base.__tablename__),
                source_column_name=relationship.info.get("column"),
                # source_column_name="id",
                remote_table_name=relationship.mapper.class_.__tablename__,
                remote_column_name=relationship.info.get("remote_column"),
                remote_node=convert_snake_to_camel(
                    relationship.mapper.class_.__tablename__
                ),
                accessor=accessor,
                filter_type="Relationship",
                lookups=object_lookups,
            )
            filters.update({accessor: filter})
            print(filter.source_model)
            print(filter.source_column_name)
            print(filter.remote_model)
            print(filter.remote_column_name)
            print(filter.label)
            if parent is None or parent.source_column_name != filter.remote_column_name:
                filters.update(cls.set_filters(parent=filter))
        # setattr(cls, "filters", filters)
        return filters
