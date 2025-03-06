# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Any, List

from psycopg.sql import SQL, Identifier, Literal, Placeholder

from sqlalchemy import (
    Table,
    Column,
    inspect,
    select,
    exists,
    insert,
    update,
    delete,
    and_,
    or_,
    not_,
    create_engine,
    text,
    alias,
)
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

from pydantic import BaseModel

from uno.storage.conn import sync_engine, engine
from uno.record.enums import SelectResultType
from uno.storage.management.sql_emitters import SetRole, DB_NAME
from uno.apps.val.enums import Lookup
from uno.apps.fltr.enums import Include, Match
from uno.config import settings


class UnoDB:
    """Provides a set of methods for interacting with a database table.

    UnoDB methods transparently expose the underlying SQLAlchemy methods for interacting with a database table.

    """

    obj_class: BaseModel
    table_name: str

    def __init__(self, obj_class: BaseModel) -> None:
        self.obj_class = obj_class
        self.table_name = self.obj_class.table.fullname

    def sync_connection(self) -> Connection:
        return sync_engine.connect()

    def connection(self) -> AsyncConnection:
        connection = engine.connect()
        yield connection

    def set_role_text(self, role_name: str) -> str:
        return (
            SQL("SET ROLE {db_name}_{role_name};")
            .format(
                db_name=DB_NAME,
                role_name=SQL(role_name),
            )
            .as_string()
        )

    def where(
        self,
        field_name: str,
        value: Any,
        include: str = Include.INCLUDE,
        lookup: str = Lookup.EQUAL,
    ) -> Any:
        column = self.obj_class.table_alias.c.get(field_name)
        try:
            operation = getattr(column, lookup)(value)
        except AttributeError as e:
            raise Exception(
                f"Column {field_name} does not have a {lookup} method"
            ) from e

        if include == Include.INCLUDE:
            return operation
        else:
            return ~operation

    def add_join(self, stmt: Any, response_model: BaseModel) -> Any:
        for f_idx, f_name in enumerate(response_model.model_fields.keys()):
            if f_name in self.obj_class.related_objects.keys():
                rel_obj = self.obj_class.related_objects.get(f_name)
                if f_idx == 0:
                    stmt = stmt.select_from(
                        rel_obj.local_table_alias.join(
                            rel_obj.remote_table_alias,
                            onclause=rel_obj.local_column_alias
                            == rel_obj.remote_column_alias,
                            isouter=True,
                        )
                    )
                else:
                    stmt = stmt.join(
                        rel_obj.remote_table_alias,
                        onclause=rel_obj.local_column_alias
                        == rel_obj.remote_column_alias,
                        isouter=True,
                    )
        return stmt

    async def list(self, schema: BaseModel = None) -> list[BaseModel]:
        if schema is None:
            schema = self.obj_class.summary_schema
        columns = [
            self.obj_class.table.c.get(field_name)
            for field_name in schema.model_fields.keys()
        ]
        async with engine.connect() as conn:
            await conn.execute(text(self.set_role_text("reader")))
            stmt = select(self.obj_class.local_table).with_only_columns(*columns)
            result = await conn.execute(stmt)
        await conn.close()
        return result.mappings().all()

    async def insert(
        self,
        body_model: BaseModel = None,
        response_model: BaseModel = None,
    ) -> None:
        if body_model is None:
            body_model = self.obj_class.edit_model
        if response_model is None:
            response_model = self.obj_class.edit_model

        response_columns = [
            self.obj_class.table.c.get(field_name)
            for field_name in response_model.model_fields.keys()
        ]

        async with engine.begin() as conn:
            await conn.execute(text(self.set_role_text("writer")))
            result = await conn.execute(
                insert(self.obj_class.table)
                .values(body_model.model_dump())
                .returning(*response_columns)
            )
            await conn.commit()
        await conn.close()
        return result.fetchone()._mapping

    async def select(
        self,
        response_model: BaseModel,
        columns: List[Column],
        id: str | None = None,
        result_type: SelectResultType = SelectResultType.FETCH_ALL,
    ) -> bool | None:
        stmt = select(*columns)
        stmt = self.add_join(stmt, response_model)
        if id is not None:
            stmt = stmt.where(and_(self.where("id", id)))
            result_type = SelectResultType.FETCH_ONE
        async with engine.begin() as conn:
            await conn.execute(text(self.set_role_text("reader")))
            result = await conn.execute(stmt)
        await conn.close()
        if result_type == SelectResultType.FETCH_ONE:
            row = result.fetchone()
            return row._mapping if row is not None else None
        row = result.fetchall()
        return [r._mapping for r in row if row is not None]

    """
    def exists(
        self,
        values: dict[str, Any],
    ) -> bool | None:
        unique_values = self.get_unique_fields_from_values(values)
        columns = (
            self.obj_class.table.c.get(field_name) for field_name in unique_values.keys()
        )

        # Create the statement
        where_clauses = [self.where(key, val) for key, val in values.items()]
        stmt = select(*columns).where(and_(*where_clauses))  # type: ignore

        # Run the query
        with self.connection.connect() as conn:
            result = conn.execute(select(exists(stmt)))
        return result.scalar()
    async def exists(
        self,
        values: dict[str, Any],
    ) -> bool | None:
        unique_values = await self.get_unique_fields_from_values(values)
        columns = (
            self.obj_class.table.c.get(field_name) for field_name in unique_values.keys()
        )

        # Create the statement
        where_clauses = [self.where(key, val) for key, val in values.items()]
        stmt = select(*columns).where(and_(*where_clauses))  # type: ignore

        # Run the query
        async with self.async_engine.begin() as conn:
            result = await conn.execute(select(exists(stmt)))
        return result.scalar()

    async def insert(self, values: dict[str, Any]) -> None:
        if await self.exists(values):
            raise Exception("Record already exists")
        async with self.async_engine.begin() as conn:
            await conn.execute(insert(self.obj_class.table).values(values))

    async def select(
        self,
        statement: Any | None = None,
        value: Any = None,
        field_name: str = "id",
        result_type: UnoSelectResultType = UnoSelectResultType.FIRST,
        limit: int = settings.DEFAULT_LIMIT,
        offset: int = settings.DEFAULT_OFFSET,
        match: str = Match.AND,
        include: str = Include.INCLUDE,
        lookup: str = Lookup.EQUAL,
        filters: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ):
        with engine.connect() as conn:
            conn.execute(insert(self.obj_class.table).values(values))
            conn.commit()
            conn.close()
    
    async def update(self, values: dict[str, Any], where: dict[str, Any]) -> None:
        with engine.connect() as conn:
            conn.execute(update(self.obj_class.table).values(values).where(where))
            conn.commit()
            conn.close()

    async def delete(self, where: dict[str, Any]) -> None:
        with engine.connect() as conn:
            conn.execute(delete(self.obj_class.table).where(where))
            conn.commit()
            conn.close()
    """
