# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio

from typing import Any

from psycopg.sql import SQL, Identifier, Literal, Placeholder

from sqlalchemy import (
    Table,
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
)
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

from pydantic import BaseModel

from uno.db.conn import sync_engine, engine
from uno.db.enums import SelectResultType
from uno.db.management.sql_emitters import SetRole, DB_NAME
from uno.val.enums import Lookup
from uno.fltr.enums import Include, Match
from uno.config import settings


class UnoDB:
    """Provides a set of methods for interacting with a database table.

    UnoDB methods transparently expose the underlying SQLAlchemy methods for interacting with a database table.

    def is_table_empty(self) -> bool:
        """Check if the table is empty using the pg_class system catalog."""
        query = SQL(
            "SELECT reltuples = 0 FROM pg_class WHERE oid = %s::regclass"
        ).format(Identifier(self.table_name))

        with self.sync_connection() as conn:
            result = conn.execute(query, (self.table_name,))
            return result.scalar()

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
        column = self.obj_class.table.c.get(field_name)
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

    async def list(self, schema: BaseModel = None) -> list[BaseModel]:
        if schema is None:
            schema = self.obj_class.list_schema
        columns = [
            self.obj_class.table.c.get(field_name)
            for field_name in schema.model_fields.keys()
        ]
        async with engine.connect() as conn:
            await conn.execute(text(self.set_role_text("reader")))
            stmt = select(self.obj_class.table).with_only_columns(*columns)
            result = await conn.execute(stmt)
            return result.mappings().all()

    async def insert(
        self, request_schema: BaseModel = None, response_schema: BaseModel = None
    ) -> None:
        if request_schema is None:
            request_schema = self.obj_class.insert_schema
        if response_schema is None:
            response_schema = self.obj_class.select_schema

        response_columns = [
            self.obj_class.table.c.get(field_name)
            for field_name in response_schema.model_fields.keys()
        ]

        async with engine.begin() as conn:
            await conn.execute(text(self.set_role_text("writer")))
            result = await conn.execute(
                insert(self.obj_class.table)
                .values(request_schema.model_dump())
                .returning(*response_columns)
            )
            await conn.commit()
        return result.fetchone()

    async def select(
        self,
        id: str,
        request_schema: BaseModel = None,
        response_schema: BaseModel = None,
    ) -> bool | None:
        if request_schema is None:
            request_schema = self.obj_class.select_schema
        if response_schema is None:
            response_schema = self.obj_class.select_schema

        columns = [
            self.obj_class.table.c.get(field_name)
            for field_name in self.obj_class.select_schema.model_fields.keys()
        ]

        stmt = select(*columns).where(and_(self.where("id", id)))

        async with self.async_connection.connect() as conn:
            await conn.execute(text(self.set_role_text("reader")))
            result = await conn.execute(stmt)
            row = result.fetchone()
        return row._mapping if row else None

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
