# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from enum import Enum
from decimal import Decimal

from typing import AsyncIterator, Annotated, ClassVar
from fastapi import FastAPI

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import registry, DeclarativeBase
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
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncAttrs,
)

from uno.db.routers import RouterDef
from uno.db.sql_emitters import SQLEmitter
from uno.db.graphs import VertexDef, EdgeDef
from uno.db.schemas import SchemaDef

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

    # Metadata related attributes
    verbose_name: ClassVar[str]
    verbose_name_plural: ClassVar[str]

    # SQL related attributes
    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Graph related attributes
    include_in_graph: ClassVar[bool] = True
    edge_defs: ClassVar[list[EdgeDef]] = []

    # schema related attributes
    schema_defs: ClassVar[list[SchemaDef]] = []

    # Router related attributes
    router_defs: ClassVar[dict[str, RouterDef]] = {}

    @classmethod
    def create_schemas(cls, app: FastAPI) -> None:
        for schema_def in cls.schema_defs:
            setattr(
                cls,
                schema_def.name,
                schema_def.create_schema(cls.__table__, app),
            )

    @classmethod
    def create_vertex(cls) -> None:
        return VertexDef(
            table_name=cls.__tablename__, label=cls.verbose_name.replace(" ", "")
        ).emit_sql()

    @classmethod
    def create_edges(cls) -> None:
        for edge_def in cls.edge_defs:
            edge_def.emit_sql()

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
