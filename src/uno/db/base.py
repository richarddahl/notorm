# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from enum import Enum
from decimal import Decimal
from typing import AsyncIterator, Annotated, ClassVar

from sqlalchemy import MetaData
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

from uno.routers import Router, RouterDef

from uno.db.sql_emitters import SQLEmitter

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
    verbose_name: ClassVar[str]
    verbose_name_plural: ClassVar[str]

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Router related attributes
    routers: ClassVar[list[Router]] = []
    router_defs: ClassVar[dict[str, RouterDef]] = {
        "Insert": RouterDef(
            method="POST",
            router="post",
        ),
        "List": RouterDef(
            method="GET",
            router="get",
            multiple=True,
        ),
        "Update": RouterDef(
            path_suffix="{id}",
            method="PUT",
            router="put",
        ),
        "Select": RouterDef(
            path_suffix="{id}",
            method="GET",
            router="get_by_id",
        ),
        "Delete": RouterDef(
            path_suffix="{id}",
            method="DELETE",
            router="delete",
        ),
    }

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.create_graph()
        cls.create_vectors()
        cls.create_routers()

    @classmethod
    def create_graph(cls) -> None:
        pass

    @classmethod
    def create_vectors(cls) -> None:
        pass

    @classmethod
    def create_routers(cls) -> None:
        for router_def in cls.router_defs.values():
            cls.routers.append(
                Router(
                    table=cls.__table__,
                    model=cls,
                    method=router_def.method,
                    router=router_def.router,
                    path_objs="",
                    path_module=cls.__tablename__,
                    path_suffix=router_def.path_suffix,
                    multiple=router_def.multiple,
                    include_in_schema=router_def.include_in_schema,
                    tags=[cls.__class__.__name__],
                    summary=router_def.summary,
                    description=router_def.description,
                )
            )

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
