# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

import datetime
import decimal
from typing import Optional
from typing_extensions import Self
from pydantic import BaseModel, model_validator
from sqlalchemy import Table, Column

from uno.utilities import (
    snake_to_title,
    snake_to_camel,
    snake_to_caps_snake,
)
from uno.enums import (
    Include,
    Match,
    Lookup,
    object_lookups,
    numeric_lookups,
    text_lookups,
)
from uno.config import settings


class UnoFilter(BaseModel):
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
        self.display = snake_to_title(self.label)
        self.source_path = f"(:{self.source_node})-[:{self.label}]->"
        self.destination_path = f"(:{self.destination_node} {{val: %s}})"
        return self

    def __str__(self) -> str:
        return f"{self.source_node}-{self.label}->{self.destination_node}"

    def __repr__(self) -> str:
        return f"<UnoFilter: {self.source_path}->{self.destination_path}>"

    # def edit_data(self) -> dict:
    #    return UnoFilter(**self.edit_schema(**self.model_dump()).model_dump())


def create_filters(table: Table) -> list[UnoFilter]:

    def create_filter_for_column(
        column: Column,
        table_name: str,
        edge: str = "edge",
    ) -> UnoFilter:
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
                source_node = snake_to_camel(
                    list(column.foreign_keys)[0].column.table.name
                )
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
