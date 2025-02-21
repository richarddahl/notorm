# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from enum import Enum
from decimal import Decimal

from typing import AsyncIterator, Annotated, ClassVar, Any

from sqlalchemy import MetaData, create_engine, inspect, Connection
from sqlalchemy.orm import registry, DeclarativeBase
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    BIGINT,
    BOOLEAN,
    BYTEA,
    DATE,
    ENUM,
    NUMERIC,
    TIME,
    TIMESTAMP,
    VARCHAR,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncAttrs,
)

from pydantic import BaseModel

from fastapi import FastAPI

from uno.db.sql_emitters import SQLEmitter, AlterGrantSQL
from uno.schemas import SchemaDef
from uno.graphs import Vertex, Edge, Property
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


bytea = Annotated[bytes, BYTEA]
decimal = Annotated[Decimal, 19]
str_26 = Annotated[str, 26]
str_63 = Annotated[str, 63]
str_64 = Annotated[str, 64]
str_128 = Annotated[str, 128]
str_255 = Annotated[str, 255]
str_list_255 = Annotated[list[str], 255]


class Base(AsyncAttrs, DeclarativeBase):
    registry = registry(
        type_annotation_map={
            bool: BOOLEAN,
            bytes: BYTEA,
            datetime.datetime: TIMESTAMP(timezone=True),
            datetime.date: DATE,
            datetime.time: TIME,
            decimal: NUMERIC,
            Enum: ENUM,
            int: BIGINT,
            list: ARRAY,
            str: VARCHAR,
            str_list_255: ARRAY(VARCHAR(255)),
            str_26: VARCHAR(26),
            str_63: VARCHAR(63),
            str_64: VARCHAR(64),
            str_128: VARCHAR(128),
            str_255: VARCHAR(255),
        }
    )
    metadata = metadata

    # Metadata attributes
    display_name: ClassVar[str]
    display_name_plural: ClassVar[str]

    # SQL attributes
    sql_emitters: ClassVar[list[SQLEmitter]] = [AlterGrantSQL]

    # Graph attributes
    include_in_graph: ClassVar[bool] = True
    vertex: ClassVar[Vertex] = None
    edges: ClassVar[dict[str, Edge]] = {}
    graph_properties: ClassVar[dict[str, Property]] = {}
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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        sql_emitters = []
        for kls in cls.mro():
            if hasattr(kls, "sql_emitters"):
                for sql_emitter in kls.sql_emitters:
                    if sql_emitter not in sql_emitters:
                        sql_emitters.append(sql_emitter)
        cls.sql_emitters = sql_emitters

    @classmethod
    def relationships(cls) -> list[Any]:
        return [relationship for relationship in inspect(cls).relationships]

    @classmethod
    def set_schemas(cls, app: FastAPI) -> None:
        for schema_def in cls.schema_defs:
            schema_def.init_schema(cls, app)

    @classmethod
    def configure_base(cls, app: FastAPI) -> None:
        cls.set_schemas(app)
        cls.set_graph()

    @classmethod
    def set_graph(cls) -> None:
        """
        Sets the graph attributes for the class.

        This method initializes the `vertex` attribute as a `Vertex` object
        with the class as the `klass` attribute. It then calls the `set_edges` method
        to set the edges for the class.

        Returns:
            None
        """
        if not cls.include_in_graph:
            return
        cls.set_properties()
        cls.vertex = Vertex(klass=cls)
        cls.set_edges()

    @classmethod
    def set_properties(cls) -> None:
        """ """
        cls.graph_properties = {}
        if not cls.vertex:
            return
        for column in cls.__table__.columns:
            if column.name in cls.exclude_from_properties:
                continue
            if column.foreign_keys and not column.primary_key:
                continue
            data_type = column.type.python_type.__name__
            cls.graph_properties[column.name] = Property(
                klass=cls,
                accessor=column.name,
                data_type=data_type,
            )

    @classmethod
    def set_edges(cls) -> None:
        """
        Sets edges for the class based on its relationships.

        This method initializes the `edges` attribute as an empty dictionary.
        It then iterates over the class's relationships, filtering out relationships
        that are not to a class that is included in the graph. For each remaining
        relationship, it creates a `Edge` object, which is added to the `edges`
        dictionary.

        Returns:
            None
        """
        cls.edges = {}
        if not cls.vertex:
            return
        for rel in cls.relationships():
            if not rel.mapper.class_.vertex:
                continue
            edge = Edge(
                klass=cls,
                destination_meta_type=rel.mapper.class_.__table__.name,
                label=rel.info.get("edge"),
                secondary=rel.secondary,
                accessor=rel.key,
            )
            cls.edges[rel.key] = edge

    @classmethod
    def set_filters(cls) -> None:
        cls.filters = {}
        if not cls.vertex:
            return
        for property in cls.graph_properties:
            cls.filters[property.display] = {
                "data_type": property.data_type,
                "name": property.name,
                # "accessor": property.accessor,
                "lookups": property.lookups,
            }
        for edge in cls.edges:
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
    def emit_sql_emitters(cls, conn: Connection = None) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(conn=conn, table_name=cls.__tablename__).emit_sql()
