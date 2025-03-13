# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT


import asyncio

from psycopg.sql import SQL
from pydantic import BaseModel
from sqlalchemy import select, insert, delete, update, text, func, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)
from sqlalchemy.pool import NullPool

from uno.db.base import UnoBase
from uno.db.enums import SelectResultType
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


class IntegrityConflictException(Exception):
    pass


class NotFoundException(Exception):
    pass


def UnoDBFactory(base: UnoBase):
    class UnoDB:
        @classmethod
        async def create(
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
            id_column: str = "id",
            result_type: SelectResultType = SelectResultType.FETCH_ALL,
        ) -> UnoBase:
            try:
                stmt = select(cls.base)
                if id is not None:
                    stmt = stmt.where(base.__table__.c.id == id)
                    result_type = SelectResultType.FETCH_ONE
                    # stmt = stmt.where(getattr(base, id_column) == id)
                async with engine.begin() as conn:
                    await conn.execute(
                        text(
                            SQL("SET ROLE {reader_role};")
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
                return [r._mapping for r in row if row is not None]
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

    UnoDB.base = base
    return UnoDB
