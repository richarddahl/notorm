# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

import datetime

from enum import Enum
from decimal import Decimal

from typing import AsyncIterator, Annotated, ClassVar

from sqlalchemy import MetaData, create_engine, ForeignKey
from sqlalchemy.orm import registry, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    BIGINT,
    TIMESTAMP,
    DATE,
    TIME,
    BOOLEAN,
    ENUM,
    NUMERIC,
    ARRAY,
    VARCHAR,
)
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncAttrs,
)

from pydantic import BaseModel

from fastapi import FastAPI

from uno.db.sql_emitters import AlterGrantSQL, InsertObjectTypeRecordSQL
from uno.schemas import SchemaDef
from uno.db.sql_emitters import SQLEmitter
from uno.graphs import GraphNode, GraphEdgeDef, GraphEdge, GraphProperty
from uno.utilities import convert_snake_to_title

from uno.config import settings


# configures the naming convention for the database implicit constraints and indexes
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}

# Creates the metadata object, used to define the database tables
metadata = MetaData(
    naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION,
    schema=settings.DB_NAME,
)

sync_engine = create_engine(settings.DB_URL)
# Create the database engine
engine = create_async_engine(settings.DB_URL)

# Create a sessionmaker factory
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=True,
    class_=AsyncSession,
)


# Dependency to provide a session
async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


str_26 = Annotated[str, 26]
str_64 = Annotated[str, 64]
str_128 = Annotated[str, 128]
str_255 = Annotated[str, 255]
decimal = Annotated[Decimal, 19]


class Base(AsyncAttrs, DeclarativeBase):
    registry = registry(
        type_annotation_map={
            int: BIGINT,
            datetime.datetime: TIMESTAMP(timezone=True),
            datetime.date: DATE,
            datetime.time: TIME,
            str: VARCHAR,
            Enum: ENUM,
            bool: BOOLEAN,
            list: ARRAY,
            str_26: VARCHAR(26),
            str_128: VARCHAR(128),
            str_255: VARCHAR(255),
            decimal: NUMERIC,
        }
    )
    metadata = metadata

    # Metadata attributes
    display_name: ClassVar[str]
    display_name_plural: ClassVar[str]

    # SQL attributes
    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Graph attributes
    include_in_graph: ClassVar[bool] = True
    graph_node: ClassVar[GraphNode] = None
    graph_edge_defs: ClassVar[list[GraphEdgeDef]] = []
    graph_edges: ClassVar[dict[str, GraphEdge]] = {}
    graph_properties: ClassVar[dict[str, GraphProperty]] = []
    exclude_from_properties: ClassVar[list[str]] = []
    filters: ClassVar[dict[str, dict[str, str]]] = {}

    # schema attributes
    schema_defs: ClassVar[list[SchemaDef]] = []
    create_schema: ClassVar[BaseModel] = None
    list_schema: ClassVar[BaseModel] = None
    select_schema: ClassVar[BaseModel] = None
    update_schema: ClassVar[BaseModel] = None
    delete_schema: ClassVar[BaseModel] = None
    import_schema: ClassVar[BaseModel] = None

    @classmethod
    def configure_base(cls, app: FastAPI) -> None:
        cls.set_schemas(app)

        if cls.include_in_graph:
            GraphNode(klass=cls)

        # cls.set_properties()
        # cls.set_filters

    @classmethod
    def set_schemas(cls, app: FastAPI) -> None:
        for schema_def in cls.schema_defs:
            schema_def.init_schema(cls, app)

    @classmethod
    def set_properties(cls) -> None:
        """
        Creates and assigns graph properties to the class.

        This method initializes the `graph_properties` attribute as an empty list.
        It then iterates over the columns of the class's table, filtering out columns
        that are either in the `exclude_from_properties` list or are foreign keys
        but not primary keys. For each remaining column, it determines the data type
        and creates a `GraphProperty` object, which is appended to the `graph_properties` list.

        Returns:
            None
        """
        cls.graph_properties = []
        if not cls.graph_node:
            return
        for column in cls.__table__.columns:
            if column.name in cls.exclude_from_properties:
                continue
            if column.foreign_keys and not column.primary_key:
                continue
            if type(column.type) == NullType:
                data_type = "str"
            else:
                data_type = column.type.python_type.__name__
            cls.graph_properties.append(
                GraphProperty(
                    table_name=cls.__table__.name,
                    name=convert_snake_to_title(column.name),
                    accessor=column.name,
                    data_type=data_type,
                )
            )

    @classmethod
    def set_filters(cls) -> None:
        """
        Sets filters for the class based on its graph properties and edges.

        This method iterates over the class's `graph_properties` and `graph_edges`
        attributes to populate the `filters` dictionary with relevant filter
        configurations.

        For each property in `graph_properties`, a filter is created with the
        following keys:
            - "table_name": The name of the table associated with the property.
            - "filter_type": Set to "PROPERTY".
            - "data_type": The data type of the property.
            - "name": The name of the property.
            - "accessor": The accessor for the property.
            - "lookups": The lookups for the property.

        For each edge in `graph_edges`, a filter is created with the following keys:
            - "table_name": The name of the table associated with the edge.
            - "filter_type": Set to "EDGE".
            - "data_type": Set to "object".
            - "name": The name of the edge.
            - "destination_table_name": The name of the destination table for the edge.
            - "accessor": The accessor for the edge.
            - "lookups": The lookups for the edge.

        Returns:
            None
        """
        cls.filters = {}
        if not cls.graph_node:
            return
        for property in cls.graph_properties:
            cls.filters[property.display] = {
                # "table_name": property.table_name,
                # "filter_type": "PROPERTY",
                "data_type": property.data_type,
                "name": property.name,
                # "accessor": property.accessor,
                "lookups": property.lookups,
            }
        for edge in cls.graph_edges:
            cls.filters[edge.display] = {
                # "table_name": edge.table_name,
                # "filter_type": "EDGE",
                "data_type": "object",
                "name": edge.name,
                # "destination_table_name": edge.destination_table_name,
                # "accessor": edge.accessor,
                "lookups": edge.lookups,
            }

    # @classmethod
    # def create_vectors(cls) -> None:
    #    pass

    @classmethod
    def emit_sql(cls) -> str:
        sql = ""
        sql += "\n".join(
            [
                sql_emitter(
                    table_name=cls.__tablename__,
                    schema=cls.__table__.schema,
                ).emit_sql()
                for sql_emitter in cls.sql_emitters
            ]
        )
        return sql


class RelatedObjectBase(Base):
    """
    Base class for objects that are generically related to other objects.

    Related Objects are used for the pk of many objects in the database,
    allowing for a single point of reference for attributes, queries, workflows, and reports
    """

    __tablename__ = "related_object"
    __table_args__ = {
        "schema": "uno",
        "comment": textwrap.dedent(
            """
            DB Objects are used for the pk of many objects in the database,
            allowing for a single point of reference for attributes, queries, workflows, and reports
            """
        ),
    }
    display_name = "DB Object"
    display_name_plural = "DB Objects"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        AlterGrantSQL,
    ]

    # graph_edge_defs = related_object_edge_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        index=True,
        doc="Primary Key",
    )

    # relationships
    # attributes: Mapped[List["Attribute"]] = relationship(
    #    back_populates="related_object", secondary="uno.attribute__object_value"
    # )
    # attachments: Mapped[List["Attachment"]] = relationship(
    #    back_populates="related_objects", secondary="uno.attribute__object_value"
    # )

    def __str__(self) -> str:
        return f"{self.object_type_id}"
