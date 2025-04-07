# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json
import asyncio
import datetime
import decimal
import enum

from typing import Annotated

from psycopg import sql
from asyncpg.exceptions import UniqueViolationError  # type: ignore

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    MetaData,
    select,
    delete,
    update,
    text,
    func,
    create_engine,
    UniqueConstraint,
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
from sqlalchemy.sql import bindparam
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


class UnoModel(AsyncAttrs, DeclarativeBase):
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


def UnoDBFactory(obj: BaseModel):
    class UnoDB:

        @classmethod
        def table_keys(cls) -> tuple[list[str], list[list[str]]]:
            """
            Retrieve a dictionary of table keys, including primary keys and unique constraints.

            This method gathers information about the primary keys and unique constraints
            defined in the table schema of the associated model. It checks for unique constraints
            defined in `__table_args__` as well as unique constraints on individual columns.

            Returns:
                dict[str, list[str]]: A dictionary where the keys are the names of the constraints
                (e.g., "pk" for primary key or the name of the unique constraint) and the values
                are lists of column names that make up the constraint.
            """

            # Initialize a dictionary to store table keys, starting with the primary key columns
            pk_fields = obj.model.__table__.primary_key.columns.keys()
            uq_fields = []

            # Check for unique constraints defined in the `__table_args__` attribute of the model
            if hasattr(cls.obj.model, "__table_args__"):
                for constraint in cls.obj.model.__table_args__:
                    # If the constraint is a UniqueConstraint, process it
                    if isinstance(constraint, UniqueConstraint):
                        # Add the unique constraint to the table_keys dictionary
                        uq_fields.append(constraint.columns.keys())

            # Check for unique constraints defined on individual columns of the table
            for column in cls.obj.model.__table__.columns:
                if column.unique is not None and column.name not in pk_fields:
                    uq_fields.append([column.name])

            return pk_fields, uq_fields

        @classmethod
        async def merge(cls, data):
            """
            Call the PostgreSQL merge_record function with escaped colons in the data values.
            """
            # pk_fields, unique_constraints = cls.table_keys()
            table_name = f"{obj.model.__table__.schema}.{cls.table_name}"

            # Create a deep copy of the data to avoid modifying the original
            import copy

            data_copy = copy.deepcopy(data)

            # Function to escape colons in string values
            def escape_colons(value):
                if isinstance(value, str):
                    # Escape colons with backslashes
                    return value.replace(":", "\\:")
                return value

            # Process all values in the data dictionary
            for key, value in data_copy.items():
                data_copy[key] = escape_colons(value)

            data_json = json.dumps(data_copy)

            # Prepare unique constraints
            # uc = (
            #    unique_constraints[0]
            #    if unique_constraints and len(unique_constraints) > 0
            #    else []
            # )

            # Format arrays as PostgreSQL literals
            # pk_array_str = "ARRAY[" + ",".join(f"'{pk}'" for pk in pk_fields) + "]"
            # uc_array_str = "ARRAY[" + ",".join(f"'{uc_field}'" for uc_field in uc) + "]"

            # Create raw SQL with the E'' string syntax for proper escape handling
            raw_sql = (
                sql.SQL("SELECT merge_record('{table_name}', E'{data_json}'::jsonb)")
                .format(table_name=sql.SQL(table_name), data_json=sql.SQL(data_json))
                .as_string()
            )
            # raw_sql = f"""
            #    SELECT merge_record(
            #        '{table_name}',
            #        E'{data_json}'::jsonb,
            #        {pk_array_str},
            #        {uc_array_str}
            #    )
            # """

            try:
                async with scoped_session() as session:
                    await session.execute(func.set_role("writer"))

                    # Execute raw SQL
                    result = await session.execute(text(raw_sql))
                    await session.commit()
                    return result.fetchone()
            except Exception as e:
                print(f"Error in merge_or_update_record_sa: {e}")
                print(f"SQL: {raw_sql}")
                raise

        @classmethod
        async def merge_or_create(
            cls, data: dict[str, str]
        ) -> tuple[BaseModel, bool] | tuple[BaseModel, list[str]]:

            obj.set_schemas()
            pk_fields, uq_field_sets = cls.table_keys()
            print(f"pk_fields: {pk_fields}")
            print(f"uq_field_sets: {uq_field_sets}")

            # Remove None values from the data dictionary
            data = {k: v for k, v in data.items() if v is not None}
            # Convert the data dictionary to a JSON string
            data_json = json.dumps(data)
            # Ensure uq_field_sets is a list of lists
            uq_field_sets_list = [list(uq_field_set) for uq_field_set in uq_field_sets]

            async with scoped_session() as session:
                await session.execute(func.set_role("writer"))
                try:
                    '''
                    query = text(
                        """
                        SELECT * FROM merge_record(
                            :table_name\\:\\:text,
                            :data\\:\\:jsonb,
                            :pk_cols\\:\\:text[],
                            :uq_cols\\:\\:text[]
                        )
                        """
                    )
                    result = await session.execute(
                        query,
                        {
                            "table_name": cls.table_name,
                            "data": data_json,
                            "pk_cols": pk_fields,
                            "uq_cols": uq_field_sets_list,
                        },
                    )
                    '''
                    query = text(
                        """
                        SELECT * FROM merge_record(
                            :table_name\\:\\:text, 
                            :data\\:\\:jsonb,
                            :pk_cols\\:\\:text[],
                            :uq_cols\\:\\:text[]
                        )
                        """
                    )
                    result = await session.execute(
                        query,
                        {
                            "table_name": cls.table_name,
                            "data": data_json,
                            "pk_cols": pk_fields,
                            "uq_cols": uq_field_sets_list,
                        },
                    )
                    result = result.fetchone()
                    return result["result"], True

                    result = result.fetchone()
                    return result["result"], True
                except Exception as e:
                    raise
                    await session.rollback()
                    return "HERE", False

        @classmethod
        async def get_or_create(
            cls, to_db_model: BaseModel = None, **kwargs
        ) -> tuple[BaseModel, bool]:
            table_keys = cls.table_keys()
            async with scoped_session() as session:
                await session.execute(func.set_role("writer"))
                try:
                    result = await cls.create(to_db_model)
                    return result
                except UniqueViolationError:
                    # Handle the case where the object already exists
                    await session.rollback()
                    await session.execute(func.set_role("reader"))
                    result = await cls.get(
                        cypher_path=to_db_model.cypher_path,  # kwargs sent to get must be natural db key
                    )
                    return result, False
                    # Re-raise the IntegrityError if it's not a UniqueViolationError
                    raise

        @classmethod
        async def create(
            cls,
            to_db_model: BaseModel,
        ) -> tuple[BaseModel, bool]:
            try:
                async with scoped_session() as session:
                    await session.execute(func.set_role("writer"))
                    session.add(to_db_model)
                    await session.commit()
                    return to_db_model, True

            except IntegrityError as e:
                # This is the only way I can find to check for a unique constraint violation
                # As the asyncpg.UniqueViolationError gets wrapped in a SQLAlchemy IntegrityError
                # And isinstance(e.orig, UniqueViolationError) doesn't work
                if "duplicate key value violates unique constraint" in str(e):
                    # Handle the case where the object already exists
                    raise UniqueViolationError
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

        @classmethod
        async def update(
            cls,
            to_db_model: BaseModel,
            **kwargs,
        ) -> UnoModel:
            try:
                obj = await cls.get(to_db_model=to_db_model, **kwargs)
                async with scoped_session() as session:
                    await session.execute(func.set_role("writer"))
                    session.add(to_db_model)
                    await session.commit()
                    return to_db_model

            except IntegrityError as e:
                # This is the only way I can find to check for a unique constraint violation
                # As the asyncpg.UniqueViolationError gets wrapped in a SQLAlchemy IntegrityError
                # And isinstance(e.orig, UniqueViolationError) doesn't work
                if "duplicate key value violates unique constraint" in str(e):
                    # Handle the case where the object already exists
                    raise UniqueViolationError
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

        @classmethod
        async def get(cls, **kwargs) -> UnoModel:
            column_names = obj.model.__table__.columns.keys()
            stmt = select(obj.model.__table__.c[*column_names])

            if kwargs:
                for key, val in kwargs.items():
                    if key == "to_db_model":
                        continue
                    if key in column_names:
                        stmt = stmt.where(getattr(obj.model, key) == val)
                    else:
                        raise ValueError(
                            f"Invalid natural key field provided in kwargs: {key}"
                        )

            try:
                async with scoped_session() as session:
                    await session.execute(func.set_role("reader"))
                    result = await session.execute(stmt)
                    rows = result.fetchall()
                    row_count = len(rows)
                    if row_count == 0:
                        raise NotFoundException(
                            f"Record not found for the provided natural key: {kwargs}"
                        )
                    if row_count > 1:
                        # This should never happen, but if it does, raise an exception
                        raise IntegrityConflictException(
                            f"Multiple records found for the provided natural key: {kwargs}"
                        )
                    row = rows[0]
                    return row._mapping if row is not None else None
            except Exception as e:
                raise UnoError(
                    f"Unhandled error occurred: {e}", error_code="SELECT_ERROR"
                ) from e

        @classmethod
        async def filter(cls, filters: FilterParam = None) -> UnoModel:
            limit = 25
            offset = 0
            order_by = None
            order = "asc"
            column_names = obj.model.__table__.columns.keys()
            stmt = select(obj.model.__table__.c[*column_names])

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
                filter = obj.filters.get(label)
                cypher_query = filter.cypher_query(fltr.val, fltr.lookup)
                print(cypher_query)
                stmt = stmt.where(obj.model.id.in_(select(text(cypher_query))))

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
            if order_by:
                if order == "desc":
                    stmt = stmt.order_by(getattr(obj.model, order_by).desc())
                else:
                    stmt = stmt.order_by(getattr(obj.model, order_by).asc())

            try:
                async with scoped_session() as session:
                    await session.execute(func.set_role("reader"))
                    result = await session.execute(stmt)
                return result.mappings().all()
            except Exception as e:
                raise UnoError(
                    f"Unhandled error occurred: {e}", error_code="SELECT_ERROR"
                ) from e

    UnoDB.obj = obj
    UnoDB.table_name = obj.model.__table__.name
    return UnoDB
