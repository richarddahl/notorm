# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT


from typing import List

from sqlalchemy import select, insert, delete, update, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine, AsyncEngine

from uno.storage.session import sync_engine, engine
from uno.model.model import UnoModel
from uno.record.record import UnoRecord
from uno.model.model import UnoModel
from uno.record.enums import SelectResultType
from uno.errors import UnoError


class IntegrityConflictException(Exception):
    pass


class NotFoundException(Exception):
    pass


def UnoDBFactory(record: UnoRecord):
    class UnoDB:
        @classmethod
        async def create(
            cls,
            to_db_model: UnoModel,
            from_db_model: UnoModel,
        ) -> UnoRecord:
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
        ) -> UnoRecord:
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
