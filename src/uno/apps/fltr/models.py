# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from typing_extensions import Self
from pydantic import model_validator
from sqlalchemy import Table, Column

from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.apps.auth.mixins import RecordAuditMixin
from uno.apps.fltr.bases import FilterBase, FilterPathBase, FilterValueBase, QueryBase
from uno.apps.meta.models import Meta, MetaType
from uno.utilities import (
    snake_to_title,
    snake_to_camel,
    snake_to_caps_snake,
)
from uno.db.enums import Include, Match
from uno.apps.val.enums import object_lookups, numeric_lookups, text_lookups
from uno.apps.val.enums import Lookup
from uno.config import settings


class Filter(UnoModel):
    # Class variables
    base = FilterBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "source_path",
                "destination_path",
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
    source_node: Optional[str] = None
    label_string: Optional[str] = None
    label: Optional[str] = None
    destination_node: Optional[str] = None
    data_type: str = "str"
    lookups: list[str]
    display: Optional[str] = None
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    id: Optional[int] = None

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        # acronyms is a dictionary of acronyms to be used in the display name, e.g. "id" -> "ID"
        self.display = snake_to_title(self.label)
        self.source_path = f"(:{self.source_node})-[:{self.label}]->"
        self.destination_path = f"(:{self.destination_node} {{val: %s}})"
        return self

    def __str__(self) -> str:
        return f"{self.source_node}-{self.label}->{self.destination_node}"

    def __repr__(self) -> str:
        return f"<Filter: {self.source_path}->{self.destination_path}>"

    def edit_data(self) -> dict:
        self.set_schemas()
        return FilterBase(**self.edit_schema(**self.model_dump()).model_dump())


def create_filter_for_column(
    column: Column,
    table_name: str,
    edge: str = "edge",
) -> Filter:
    if column.type.python_type in [str, bytes]:
        lookups = text_lookups
    elif column.type.python_type in [int, Decimal, float, date, datetime, time]:
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
            source_node = snake_to_camel(list(column.foreign_keys)[0].column.table.name)
            destination_node = snake_to_camel(
                column.info.get("reverse_node_label", column.table.name)
            )
            label = snake_to_caps_snake(
                column.info.get(edge, column.name.replace("_id", ""))
            )
    else:
        source_node = snake_to_camel(table_name)
        destination_node = snake_to_camel(column.name)
        label = snake_to_caps_snake(
            column.info.get(edge, column.name.replace("_id", ""))
        )
    return Filter(
        source_node=source_node,
        label=label,
        destination_node=destination_node,
        data_type=column.type.python_type.__name__,
        lookups=lookups,
    )


def create_filters(table: Table) -> list[Filter]:
    filters = {}
    if "id" in table.columns.keys():
        fltr = Filter(
            source_node=snake_to_camel(table.name),
            label=snake_to_caps_snake(table.columns["id"].info.get("edge", table.name)),
            destination_node="Meta",
            data_type="str",
            lookups=object_lookups,
        )
        filter_key = f"{fltr.source_node}{fltr.label}{fltr.destination_node}"
        filters[filter_key] = fltr
    for column in table.columns.values():
        if column.info.get("graph_excludes", False):
            continue
        fltr = create_filter_for_column(column, table.name)
        filter_key = f"{fltr.source_node}{fltr.label}{fltr.destination_node}"
        if filter_key not in filters.keys():
            filters[filter_key] = fltr
        if column.info.get("reverse_edge", False):
            fltr = create_filter_for_column(
                column,
                table.name,
                edge="reverse_edge",
            )
        fltr_key = f"{fltr.source_node}{fltr.label}{fltr.destination_node}"
        if fltr_key not in filters.keys():
            filters[fltr_key] = fltr
    return filters.values()


class FilterPath(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = FilterPathBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "values",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
            ],
        ),
    }
    endpoint_tags = ["Search"]

    # Fields
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    values: Optional[list["FilterValue"]] = []

    def __str__(self) -> str:
        return self.name


class FilterValue(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = FilterValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                # "filter_path",
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
    filter_path_id: Optional[int] = None
    # filter_path: Optional[FilterPath] = None
    include: Optional[Include] = Include.INCLUDE
    match: Optional[Match] = Match.AND
    lookup: Optional[Lookup] = Lookup.EQUAL
    values: Optional[list[Meta]] = []
    queries: Optional[list["Query"]] = []


class Query(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = QueryBase
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
    terminate_filters = True
    endpoint_tags = ["Search"]

    # Fields
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    query_meta_type_id: Optional[str] = None
    query_meta_type: Optional[MetaType] = None
    include_values: Optional[Include] = Include.INCLUDE
    match_values: Optional[Match] = Match.AND
    include_queries: Optional[Include] = Include.INCLUDE
    match_queries: Optional[Match] = Match.AND

    def __str__(self) -> str:
        return self.name
