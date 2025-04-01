# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT


import asyncio
import datetime
import decimal
import enum

from typing import Annotated

from psycopg import sql

from pydantic import BaseModel
from sqlalchemy import (
    MetaData,
    select,
    insert,
    delete,
    update,
    func,
    text,
    create_engine,
)
from sqlalchemy.orm import (
    registry,
    DeclarativeBase,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
    AsyncAttrs,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.dialects.postgresql import (
    BIGINT,
    TIMESTAMP,
    DATE,
    TIME,
    VARCHAR,
    ENUM,
    BOOLEAN,
    ARRAY,
    NUMERIC,
    INTERVAL,
    UUID,
    JSONB,
)

from uno.enums import SelectResultType
from uno.errors import UnoError
from uno.config import settings


DB_ROLE = f"{settings.DB_NAME}_login"
DB_SYNC_DRIVER = settings.DB_SYNC_DRIVER
DB_ASYNC_DRIVER = settings.DB_ASYNC_DRIVER
DB_USER_PW = settings.DB_USER_PW
DB_HOST = settings.DB_HOST
DB_NAME = settings.DB_NAME
DB_SCHEMA = settings.DB_SCHEMA


sync_engine = create_engine(
    f"{DB_SYNC_DRIVER}://{DB_ROLE}:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
    # echo=True,
)


engine = create_async_engine(
    # f"{DB_SYNC_DRIVER}://{DB_ROLE}:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
    f"{DB_ASYNC_DRIVER}://{DB_ROLE}:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
    poolclass=NullPool,
    # echo=True,
)

session_maker = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def current_task():
    return asyncio.current_task()


scoped_session = async_scoped_session(
    session_maker,
    scopefunc=current_task,
)

# configures the naming convention for the database implicit constraints and indexes
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


meta_data = MetaData(
    naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION,
    schema=settings.DB_SCHEMA,
)

str_26 = Annotated[VARCHAR, 26]
str_63 = Annotated[VARCHAR, 63]
str_128 = Annotated[VARCHAR, 128]
str_255 = Annotated[VARCHAR, 255]
str_uuid = Annotated[str, 36]
dec = Annotated[decimal.Decimal, 19]
datetime_tz = Annotated[TIMESTAMP, ()]
date_ = Annotated[datetime.date, ()]
time_ = Annotated[datetime.time, ()]
interval = Annotated[datetime.timedelta, ()]
json_ = Annotated[dict, ()]


class UnoBase(AsyncAttrs, DeclarativeBase):
    registry = registry(
        type_annotation_map={
            int: BIGINT,
            str: VARCHAR,
            enum.StrEnum: ENUM,
            bool: BOOLEAN,
            list: ARRAY,
            datetime_tz: TIMESTAMP(timezone=True),
            date_: DATE,
            time_: TIME,
            interval: INTERVAL,
            dec: NUMERIC,
            str_26: VARCHAR(26),
            str_63: VARCHAR(63),
            str_128: VARCHAR(128),
            str_255: VARCHAR(255),
            str_uuid: UUID,
            json_: JSONB,
        }
    )
    metadata = meta_data


class IntegrityConflictException(Exception):
    pass


class NotFoundException(Exception):
    pass


def UnoDBFactory(model: BaseModel):
    class UnoDB:

        @classmethod
        def set_role(cls, role_name: str) -> str:
            return (
                sql.SQL(
                    """
                SET ROLE {db_name}_{role};
                """
                )
                .format(
                    db_name=sql.SQL(DB_NAME),
                    role=sql.SQL(role_name),
                )
                .as_string()
            )

        @classmethod
        async def insert_(
            cls,
            to_db_model: BaseModel,
            from_db_model: BaseModel,
        ) -> UnoBase:
            try:
                async with scoped_session() as session:
                    await session.execute(text(cls.set_role("writer")))
                    result = await session.execute(
                        insert(model.base.table)
                        .values(**to_db_model.model_dump())
                        .returning(*from_db_model.model_fields.keys())
                    )
                    await session.commit()
                    return cls.base(**result.fetchone()._mapping)
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{to_db_model.__name__} conflicts with existing data.",
                )
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

        @classmethod
        async def select_(
            cls,
            id: str = None,
            result_type: SelectResultType = SelectResultType.FETCH_ALL,
            limit: int = 25,
            offset: int = 0,
            filters: dict = {},
            **kwargs,
        ) -> UnoBase:
            column_names = model.base.__table__.columns.keys()
            stmt = select(model.base.__table__.c[*column_names])

            if filters:
                for key, fltr in filters.items():
                    value = fltr.get("val", None)
                    comparison_operator = fltr.get(
                        "comparison_operator", "EQUAL"
                    ).upper()
                    if key not in model.filters.keys():
                        raise UnoError(
                            f"Filter key '{key}' not found in filters.",
                        )
                    if value is None:
                        raise UnoError(
                            f"Filter value for '{key}' cannot be None.",
                        )
                    filter = model.filters[key]
                    cypher_query = filter.cypher_query_string(
                        value, comparison_operator=comparison_operator
                    )
                    subquery = select(text(cypher_query)).scalar_subquery()
                    stmt = stmt.where(model.base.id.in_(subquery))

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            try:
                if id is not None:
                    stmt = stmt.where(model.base.id == id)
                    result_type = SelectResultType.FETCH_ONE
                async with scoped_session() as session:
                    await session.execute(text(cls.set_role("reader")))
                    result = await session.execute(stmt)
                if result_type == SelectResultType.FETCH_ONE:
                    row = result.fetchone()
                    return row._mapping if row is not None else None
                return result.mappings().all()
            except Exception as e:
                raise UnoError(
                    f"Unhandled error occurred: {e}", error_code="SELECT_ERROR"
                ) from e

    UnoDB.model = model
    return UnoDB
