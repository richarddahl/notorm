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
            enum.Enum: ENUM,
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


def UnoDBFactory(base: UnoBase, model: BaseModel):
    class UnoDB:
        @classmethod
        async def insert(
            cls,
            to_db_model: BaseModel,
            from_db_model: BaseModel,
        ) -> UnoBase:
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(cls.set_role(text("writer"))))
                    result = await conn.execute(
                        insert(base.table)
                        .values(**to_db_model.model_dump())
                        .returning(*from_db_model.model_fields.keys())
                    )
                    await conn.commit()
                    await conn.close()
                    return cls.base(**result.fetchone()._mapping)
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{to_db_model.__name__} conflicts with existing data.",
                )
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

        @classmethod
        async def select(
            cls,
            from_db_model: BaseModel,
            id: str = None,
            result_type: SelectResultType = SelectResultType.FETCH_ALL,
            limit: int = 25,
            offset: int = 0,
            include_fields: list[str] = [],
            exclude_fields: list[str] = [],
            **kwargs,
        ) -> UnoBase:
            # for key, value in kwargs.items():
            #    if key not in base.__table__.columns:
            #        raise UnoError(f"Invalid filter key: {key}", error_code=400)
            column_names = base.__table__.columns.keys()
            if include_fields:
                column_names = [col for col in include_fields if col in column_names]
            elif exclude_fields:
                column_names = [
                    col
                    for col in base.__table__.columns.keys()
                    if col not in exclude_fields
                ]
            stmt = select(base.__table__.c[*column_names])

            try:
                if id is not None:
                    stmt = stmt.where(base.__table__.c.id == id)
                    result_type = SelectResultType.FETCH_ONE
                async with engine.begin() as conn:
                    await conn.execute(
                        text(
                            sql.SQL("SET ROLE {reader_role};")
                            .format(reader_role=f"{DB_NAME}_reader")
                            .as_string()
                        )
                    )
                    result = await conn.execute(stmt)
                await conn.close()
                if result_type == SelectResultType.FETCH_ONE:
                    row = result.fetchone()
                    return from_db_model(**row._mapping) if row is not None else None
                row = result.fetchall()
                return [
                    r._mapping
                    for r in row
                    if row is not None  # and r._mapping.name in column_names
                ]
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

    UnoDB.base = base
    return UnoDB
