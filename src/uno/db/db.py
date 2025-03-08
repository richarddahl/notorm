# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT


import asyncio
from typing import AsyncIterator

from sqlalchemy import select, insert, delete, update, text, create_engine

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)
from sqlalchemy.pool import NullPool

from uno.model.model import UnoModel
from uno.db.base import UnoBase
from uno.model.model import UnoModel
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


def UnoDBFactory(record: UnoBase):
    class UnoDB:
        @classmethod
        async def create(
            cls,
            to_db_model: UnoModel,
            from_db_model: UnoModel,
        ) -> UnoBase:
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(cls.set_role_text("writer")))
                    result = await conn.execute(
                        insert(record.table)
                        .values(**to_db_model.model_dump())
                        .returning(*from_db_model.model_fields.keys())
                    )
                    await conn.commit()
                    await conn.close()
                    return cls.record(**result.fetchone()._mapping)
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{to_db_model.__name__} conflicts with existing data.",
                )
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

        @classmethod
        async def select(
            cls,
            to_db_model: UnoModel,
            from_db_model: UnoModel,
            id_: str = None,
            id_column: str = "id",
            result_type: SelectResultType = SelectResultType.FETCH_ONE,
        ) -> UnoBase:
            try:
                stmt = select(*from_db_model.model_fields.keys())
                if id_ is not None:
                    stmt = stmt.where(record.table.c.id == id)
                    stmt = stmt.where(getattr(record, id_column) == id_)
                async with engine.begin() as conn:
                    await conn.execute(text(cls.set_role_text("reader")))
                    result = await conn.execute(stmt)
                await conn.close()
                if result_type == SelectResultType.FETCH_ONE:
                    row = result.fetchone()
                    return record(**row._mapping) if row is not None else None
                row = result.fetchall()
                return [r._mapping for r in row if row is not None]
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{to_db_model.__name__} conflicts with existing data.",
                )
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

    UnoDB.record = record
    return UnoDB
