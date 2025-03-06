# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json

from typing import ClassVar, Any

from abc import ABC, abstractmethod

from psycopg.sql import SQL, Identifier, Literal, Placeholder

from pydantic import BaseModel, computed_field, ConfigDict

from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from uno.storage.sql.sql_emitter import (
    TableSQLEmitter,
    DB_SCHEMA,
    ADMIN_ROLE,
    WRITER_ROLE,
)
from uno.apps.val.enums import (
    Lookup,
    numeric_lookups,
    text_lookups,
    object_lookups,
    boolean_lookups,
)
from uno.storage.sql.graph_sql_emitters import (
    GraphSQLEmitter,
    NodeSQLEmitter,
    PropertySQLEmitter,
    EdgeSQLEmitter,
)
from uno.utilities import (
    convert_snake_to_camel,
    convert_snake_to_title,
)


class GraphBase(BaseModel, ABC):
    obj_class: type[BaseModel] = None

    sql_emitter: ClassVar[GraphSQLEmitter] = None

    @abstractmethod
    def _emit_sql(self, conn: Connection):
        raise NotImplementedError


class GraphProperty(GraphBase):
    source_meta_type: str
    accessor: str
    data_type: str
    # label: str <- computed_field
    # lookups: Lookup <- computed_field

    sql_emitter = PropertySQLEmitter

    @computed_field
    def label(self) -> str:
        return convert_snake_to_title(self.accessor)

    @computed_field
    def lookups(self) -> Lookup:
        if self.data_type in [
            "datetime",
            "date",
            "Decimal",
            "int",
            "time",
        ]:
            return numeric_lookups
        if self.data_type in ["str"]:
            return text_lookups
        if self.data_type in ["bool"]:
            return boolean_lookups
        return object_lookups

    def _emit_sql(self, conn):
        self.sql_emitter()._emit_sql(conn)


class GraphNode(GraphBase):

    sql_emitter = NodeSQLEmitter

    @computed_field
    def source_meta_type(self) -> str:
        return self.obj_class.__name__

    @computed_field
    def label(self) -> str:
        return convert_snake_to_camel(self.source_meta_type)

    @computed_field
    def properties(self) -> dict[str, GraphProperty]:
        props = {}
        for column in self.obj_class.table.columns:
            if column.name in self.obj_class.exclude_from_properties:
                continue
            data_type = column.type.python_type.__name__
            props.update(
                {
                    column.name: GraphProperty(
                        source_meta_type=self.source_meta_type,
                        accessor=column.name,
                        data_type=data_type,
                    )
                }
            )
        return props

    def _emit_sql(self, conn: Connection):
        self.sql_emitter(obj_class=self.obj_class, node=self)._emit_sql(conn)


class GraphEdge(GraphBase):
    obj_class: Any = None
    source_table: str
    source_column_name: str
    destination_column_name: str
    label: str
    lookups: list[Lookup] = object_lookups

    sql_emitter = EdgeSQLEmitter

    def _emit_sql(self, conn: Connection):
        self.sql_emitter(edge=self)._emit_sql(conn)


class EdgeDef(GraphBase):
    # obj_class: type[DeclarativeBase] <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    label: str
    destination_meta_type: str
    accessor: str
    secondary: Table | None
    lookups: list[Lookup] = object_lookups
    # properties: dict[str, PropertySQLEmitter] <- computed_field
    # label: str <- computed_field
    # nullable: bool = False <- computed_field

    model_config = ConfigDict(arbitrary_types_allowed=True)
    """
    @computed_field
    def label(self) -> str:
        return f"{convert_snake_to_title(self.accessor)} ({convert_snake_to_title(self.destination_meta_type)})"

    @computed_field
    def source_meta_type(self) -> str:
        return self.obj_class.tablename

    @computed_field
    def properties(self) -> dict[str, GraphProperty]:
        if not isinstance(self.secondary, Table):
            return {}
        props = {}
        for column in self.secondary.columns:
            if column.foreign_keys and column.primary_key:
                continue
            data_type = column.type.python_type.__name__
            for base in self.obj_class.registry.mappers:
                if base.class_.__tablename__ == self.secondary.name:
                    obj_class = base.class_
                    break
            props.update(
                {
                    column.name: GraphProperty(
                        obj_class=obj_class,
                        accessor=column.name,
                        data_type=data_type,
                    )
                }
            )
        return props
    """
