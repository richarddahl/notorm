# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json

from psycopg.sql import SQL, Identifier, Literal, Placeholder

from pydantic import BaseModel, computed_field, ConfigDict

from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from uno.db.sql.sql_emitter import (
    TableSQLEmitter,
    DB_SCHEMA,
    ADMIN_ROLE,
    WRITER_ROLE,
)
from uno.val.enums import (
    Lookup,
    numeric_lookups,
    text_lookups,
    object_lookups,
    boolean_lookups,
)
from uno.utilities import (
    convert_snake_to_camel,
    convert_snake_to_title,
)


class GraphDef(BaseModel):

    @computed_field
    def source_meta_type(self) -> str:
        return self.kls.__tablename__


class PropertyDef(GraphDef):
    # kls: type[DeclarativeBase] <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    accessor: str
    data_type: str
    # display: str <- computed_field
    # destination_meta_type: str <- computed_field
    # lookups: Lookup <- computed_field

    @computed_field
    def display(self) -> str:
        return convert_snake_to_title(self.accessor)

    @computed_field
    def destination_meta_type(self) -> str:
        return self.source_meta_type

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


class NodeDef(GraphDef):
    # kls: type[DeclarativeBase] <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    # properties: dict[str, PropertySQLEmitter] <- computed_field
    # label: str <- computed_field

    @computed_field
    def properties(self) -> dict[str, PropertyDef]:
        return self.kls.graph_properties

    @computed_field
    def label(self) -> str:
        return convert_snake_to_camel(self.source_meta_type)


class Edge(BaseModel):
    source: str
    destination: str
    label: str
    # accessor: str
    lookups: list[Lookup] = object_lookups

    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)


class EdgeDef(GraphDef):
    # kls: type[DeclarativeBase] <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    label: str
    destination_meta_type: str
    accessor: str
    secondary: Table | None
    lookups: list[Lookup] = object_lookups
    # properties: dict[str, PropertySQLEmitter] <- computed_field
    # display: str <- computed_field
    # nullable: bool = False <- computed_field

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def display(self) -> str:
        return f"{convert_snake_to_title(self.accessor)} ({convert_snake_to_title(self.destination_meta_type)})"

    @computed_field
    def source_meta_type(self) -> str:
        return self.kls.tablename

    @computed_field
    def properties(self) -> dict[str, PropertyDef]:
        if not isinstance(self.secondary, Table):
            return {}
        props = {}
        for column in self.secondary.columns:
            if column.foreign_keys and column.primary_key:
                continue
            data_type = column.type.python_type.__name__
            for base in self.kls.registry.mappers:
                if base.class_.__tablename__ == self.secondary.name:
                    kls = base.class_
                    break
            props.update(
                {
                    column.name: PropertyDef(
                        kls=kls,
                        accessor=column.name,
                        data_type=data_type,
                    )
                }
            )
        return props
