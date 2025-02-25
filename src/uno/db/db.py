# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Any

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
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection

from pydantic import BaseModel

from uno.db.enums import SelectResultType
from uno.val.enums import Lookup
from uno.fltr.enums import Include, Match
from uno.config import settings


DB_ROLE = f"{settings.DB_NAME}_login"
DB_ASYNC_DRIVER = settings.DB_ASYNC_DRIVER
DB_USER_PW = settings.DB_USER_PW
DB_HOST = settings.DB_HOST
DB_NAME = settings.DB_NAME
DB_SCHEMA = settings.DB_SCHEMA

async_engine = create_async_engine(
    f"{DB_ASYNC_DRIVER}://{DB_ROLE}:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
)

engine = create_engine(
    f"{DB_ASYNC_DRIVER}://{DB_ROLE}:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
)


class UnoDB:
    """Provides a set of methods for interacting with a database table.

    UnoDB methods transparently expose the underlying SQLAlchemy methods for interacting with a database table.

    """

    db_table: Table
    table_name: str
    metadata: Any
    # async_engine: AsyncConnection

    def __init__(self, db_table: Table) -> None:
        self.db_table = db_table
        self.table_name = db_table.fullname
        self.metadata = db_table.metadata
        # self.async_engine = get_connection()

    def connection(self) -> Connection:
        return engine.connect()

    async def async_connection() -> AsyncConnection:
        async with async_engine.connect() as conn:
            yield conn

    def where(
        self,
        field_name: str,
        value: Any,
        include: str = Include.INCLUDE,
        lookup: str = Lookup.EQUAL,
    ) -> Any:
        """
        Filters the table based on the specified field name, value, include option, and lookup method.

        Args:
            field_name (str): The name of the field to filter on.
            value (Any): The value to filter for.
            include (str, optional): The include option. Defaults to Include.INCLUDE.
            lookup (str, optional): The lookup method. Defaults to Lookup.EQUAL.

        Returns:
            Any: The filtered operation.

        Raises:
            Exception: If the specified column does not exist in the table.
            Exception: If the specified column does not have the specified lookup method.
        """
        try:
            column = self.db_table.c.get(field_name)
        except AttributeError as e:
            raise Exception(
                f"Column {field_name} does not exist in table {self.db_table}"
            ) from e

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

    def select(self, values: dict[str, Any]) -> bool | None:
        with self.connection() as conn:
            conn.execute(text("SET ROLE uno_dev_reader"))
            stmt = select(self.db_table)
            result = conn.execute(stmt)
            return result.fetchone()

    def insert(self, schema: BaseModel) -> None:
        with self.connection() as conn:
            conn.execute(insert(self.db_table).values(schema.model_dump()))
            conn.commit()
            conn.close()

    """
    async def select(
        self,
        # columns: list[str] | None = None,
        values: dict[str, Any],
        result_type: SelectResultType = SelectResultType.FIRST,
        column_names: list[str] | None = None,
    ) -> bool | None:
        # if columns is None:
        #    column_names = list(self.db_table.columns.keys())
        column_names = self.validate_columns(
            list(values.keys()), self.db_table.columns.keys()
        )
        columns = (self.db_table.c.get(field_name) for field_name in column_names)

        # Create the statement
        where_clauses = [
            self.where(key, val) for key, val in values.items() if key in column_names
        ]
        stmt = select(*columns).where(and_(*where_clauses))  # type: ignore

        # Run the query
        async with self.async_engine.begin() as conn:
            result = await conn.execute(stmt)
        return getattr(result, result_type)()

    def exists(
        self,
        values: dict[str, Any],
    ) -> bool | None:
        unique_values = self.get_unique_fields_from_values(values)
        columns = (
            self.db_table.c.get(field_name) for field_name in unique_values.keys()
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
            self.db_table.c.get(field_name) for field_name in unique_values.keys()
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
            await conn.execute(insert(self.db_table).values(values))

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
            conn.execute(insert(self.db_table).values(values))
            conn.commit()
            conn.close()
    
    async def update(self, values: dict[str, Any], where: dict[str, Any]) -> None:
        with engine.connect() as conn:
            conn.execute(update(self.db_table).values(values).where(where))
            conn.commit()
            conn.close()

    async def delete(self, where: dict[str, Any]) -> None:
        with engine.connect() as conn:
            conn.execute(delete(self.db_table).where(where))
            conn.commit()
            conn.close()
    """
