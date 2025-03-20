# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from typing_extensions import Self
from pydantic import model_validator

from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.apps.auth.mixins import RecordAuditMixin
from uno.apps.fltr.bases import FilterBase, FilterValueBase, QueryBase
from uno.apps.meta.models import Meta, MetaType
from uno.utilities import (
    convert_snake_to_title,
    convert_snake_to_camel,
    convert_snake_to_all_caps_snake,
)
from uno.acronyms import acronyms
from uno.db.enums import Include, Match
from uno.db.base import UnoBase
from uno.apps.val.enums import object_lookups, numeric_lookups, text_lookups
from uno.apps.val.enums import Lookup
from uno.config import settings


class Filter(UnoModel):
    # Class variables
    base = FilterBase
    table_name = "filter"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "prepend_path",
                "append_path",
                "path",
                "display",
            ]
        ),
        "edit_schema": UnoSchemaConfig(
            exclude_fields=[
                "id",
                "label_string",
            ]
        ),
    }
    endpoints = ["List"]
    endpoint_tags = ["Search"]

    # Fields
    source_meta_type_id: Optional[str] = None
    label_string: Optional[str] = None
    remote_meta_type_id: Optional[str] = None
    data_type: str = "str"
    lookups: list[str]
    display: Optional[str] = None
    path: Optional[str] = None
    prepend_path: Optional[str] = None
    append_path: Optional[str] = None
    id: Optional[int] = None

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        self.display = acronyms.get(
            self.label_string, convert_snake_to_title(self.label_string)
        )
        source_node = convert_snake_to_camel(self.source_meta_type_id)
        remote_node = convert_snake_to_camel(self.remote_meta_type_id)
        label = convert_snake_to_title(self.label_string)
        self.path = f"{source_node}-[:{label}]->(:{remote_node} {{val: %s}})"
        self.prepend_path = f"{source_node}-[:{label}]->(:{remote_node})"
        self.append_path = f"-[:{label}]->(:{remote_node} {{val: %s}})"
        return self

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"<Filter: {self.path} >"

    async def edit_data(self) -> dict:
        return FilterBase(**self.edit_schema(**self.model_dump()).model_dump())


async def create_filters(base: UnoBase) -> None:
    print(f"Filters for {base.__tablename__}")
    source_model = UnoModel.registry[base.__tablename__]
    if source_model.exclude_from_filters:
        return []
    filters = []
    for column_name, column in base.__table__.columns.items():
        if column_name in source_model.filter_excludes:
            continue
        if column.type.python_type in [str, bytes]:
            lookups = text_lookups
        elif column.type.python_type in [int, Decimal, float, date, datetime, time]:
            lookups = numeric_lookups
        else:
            lookups = object_lookups
        filter = Filter(
            source_meta_type_id=base.__tablename__,
            label_string=column_name,
            remote_meta_type_id=base.__tablename__,
            data_type=column.type.python_type.__name__,
            lookups=lookups,
        )
        filters.append(filter)

    for relationship in source_model.relationships():
        if relationship.key in source_model.filter_excludes:
            continue
        filter = Filter(
            source_meta_type_id=base.__tablename__,
            label_string=relationship.key,
            remote_meta_type_id=relationship.mapper.class_.__tablename__,
            data_type="str",
            lookups=object_lookups,
        )
        filters.append(filter)
    return filters


class FilterValue(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = FilterValueBase
    table_name = "filter_value"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "filter",
                "values",
                "queries",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "include",
                "match",
                "lookup",
            ],
        ),
    }
    endpoint_tags = ["Search"]

    # Fields
    id: Optional[str] = None
    filter_id: Optional[int] = None
    filter: Optional[Filter] = None
    include: Optional[Include] = Include.INCLUDE
    match: Optional[Match] = Match.AND
    lookup: Optional[Lookup] = Lookup.EQUAL
    values: Optional[list[Meta]] = []
    queries: Optional[list["Query"]] = []


class Query(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = QueryBase
    table_name = "query"
    display_name_plural = "Queries"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
            ],
        ),
    }
    filter_excludes = [
        "created_by_id",
        "modified_by_id",
        "deleted_by_id",
    ]
    terminate_filters = True
    endpoint_tags = ["Search"]

    # Fields
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    queries_meta_type_id: Optional[str] = None
    queries_meta_type: Optional[MetaType] = None
    include_values: Optional[Include] = Include.INCLUDE
    match_values: Optional[Match] = Match.AND
    include_queries: Optional[Include] = Include.INCLUDE
    match_queries: Optional[Match] = Match.AND

    def __str__(self) -> str:
        return self.name
