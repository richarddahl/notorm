# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT


import asyncio
import datetime
import decimal
import enum

from typing import Annotated

from psycopg import sql

from asyncpg.exceptions import UniqueViolationError
import asyncpg

from pydantic import BaseModel, ConfigDict
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
    Query,
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
    ARRAY,
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
    BYTEA,
    TEXT,
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

str_12 = Annotated[VARCHAR, 12]
str_26 = Annotated[VARCHAR, 26]
str_63 = Annotated[VARCHAR, 63]
str_64 = Annotated[VARCHAR, 64]
str_128 = Annotated[VARCHAR, 128]
str_255 = Annotated[VARCHAR, 255]
str_uuid = Annotated[str, 36]
dec = Annotated[decimal.Decimal, 19]
datetime_tz = Annotated[TIMESTAMP, ()]
date_ = Annotated[datetime.date, ()]
time_ = Annotated[datetime.time, ()]
interval = Annotated[datetime.timedelta, ()]
json_ = Annotated[dict, ()]
bytea = Annotated[bytes, ()]


class UnoBase(AsyncAttrs, DeclarativeBase):
    registry = registry(
        type_annotation_map={
            int: BIGINT,
            str: TEXT,
            enum.StrEnum: ENUM,
            bool: BOOLEAN,
            bytea: BYTEA,
            list: ARRAY,
            datetime_tz: TIMESTAMP(timezone=True),
            date_: DATE,
            time_: TIME,
            interval: INTERVAL,
            dec: NUMERIC,
            str_12: VARCHAR(12),
            str_26: VARCHAR(26),
            str_63: VARCHAR(63),
            str_64: VARCHAR(64),
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


class FilterParam(BaseModel):
    """FilterParam is used to validate the filter parameters for the ListRouter."""

    model_config = ConfigDict(extra="forbid")


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
        async def get_or_create(cls, to_db_model: BaseModel) -> tuple[BaseModel, bool]:
            async with scoped_session() as session:
                await session.execute(text(cls.set_role("writer")))
                try:
                    obj = await cls.insert_(to_db_model)
                    return obj, True
                except IntegrityError as e:
                    print("HERE")
                    print(e.orig)
                    print(type(e.orig))
                    if isinstance(e.orig, UniqueViolationError):
                        print("THERE")
                        print(f"get_or_create: {to_db_model.path} already exists")
                        # Handle the case where the object already exists
                        await session.rollback()
                        await session.execute(text(cls.set_role("reader")))
                        obj = await cls.select_(
                            to_db_model=to_db_model,
                            result_type=SelectResultType.FETCH_ONE,
                            filters=[
                                FilterParam(label="path", val=to_db_model.path),
                            ],
                        )
                        return obj, False
                    else:
                        # Re-raise the IntegrityError if it's not a UniqueViolationError
                        raise

        @classmethod
        async def insert_(
            cls,
            to_db_model: BaseModel,
            # from_db_model: BaseModel,
        ) -> UnoBase:
            # try:
            async with scoped_session() as session:
                await session.execute(text(cls.set_role("writer")))
                session.add(to_db_model)
                await session.commit()
                return to_db_model

        # except IntegrityError:
        #     raise IntegrityConflictException(
        #         f"{to_db_model.__name__} conflicts with existing data.",
        #     )
        # except Exception as e:
        #     raise UnoError(f"Unknown error occurred: {e}") from e

        @classmethod
        async def select_(
            cls,
            id: str = None,
            result_type: SelectResultType = SelectResultType.FETCH_ALL,
            filters: FilterParam = None,
        ) -> UnoBase:
            """
            Perform a database query to select records based on the provided parameters.

            Args:
                cls: The class on which the method is called.
                id (str, optional): The ID of the record to fetch. If provided, only a single record
                with the matching ID will be retrieved.
                result_type (SelectResultType, optional): Specifies the type of result to return.
                Defaults to SelectResultType.FETCH_ALL. Use SelectResultType.FETCH_ONE to fetch
                a single record.
                filters (FilterParam, optional): A list of filters to apply to the query. Filters
                can include parameters like "limit", "offset", "order_by", and "order", as well
                as custom filters defined in the model.

            Returns:
                UnoBase: The result of the query. If `result_type` is FETCH_ONE, a single record
                is returned as a mapping. If `result_type` is FETCH_ALL, a list of mappings
                is returned.

            Raises:
                UnoError: If an unhandled error occurs during query execution. The error will
                include a message and an error code "SELECT_ERROR".

            Notes:
                - The method constructs a SQLAlchemy query using the provided filters and executes
                  it asynchronously.
                - If `id` is provided, the query is restricted to a single record with the matching ID.
                - The method uses a scoped session to execute the query and ensures the database role
                  is set to "reader" for the operation.
            """
            limit = None
            offset = None
            order_by = None
            order = "asc"

            column_names = model.base.__table__.columns.keys()
            stmt = select(model.base.__table__.c[*column_names])

            if filters:
                for fltr in filters:
                    if fltr.label in ["limit", "offset", "order_by"]:
                        if fltr.label == "limit":
                            limit = fltr.val
                            continue
                        if fltr.label == "offset":
                            offset = fltr.val
                            continue
                        if fltr.label == "order_by":
                            order_by = fltr.val
                            continue
                    label = fltr.label.split(".")[0]
                    filter = model.filters.get(label)
                    cypher_query = filter.cypher_query(fltr.val, fltr.lookup)
                    stmt = stmt.where(model.base.id.in_(select(text(cypher_query))))

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
            if order_by:
                if order == "desc":
                    stmt = stmt.order_by(getattr(model.base, order_by).desc())
                else:
                    stmt = stmt.order_by(getattr(model.base, order_by).asc())

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
