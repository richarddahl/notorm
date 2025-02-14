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
)
from uno.enumerations import (
    UnoSelectResultType,
    Include,
    Lookup,
)  # type: ignore
from uno.db import metadata, engine, async_engine  # type: ignore
from config import settings  # type: ignore


class UnoDB:
    """Provides a set of methods for interacting with a database table.

    UnoDB methods transparently expose the underlying SQLAlchemy methods for interacting with a database table.

    """

    db_table: Table
    table_name: str
    db_tables: dict[str, Table]
    DB_NAME: str
    pk_fields: list[str]

    def __init__(self, table_name) -> None:
        """
        Initializes a new instance of the UnoDB class.

        Args:
            table_name (str): The name of the table in the database.

        Raises:
            Exception: If the specified table does not exist in the database.
        """
        self.table_name = table_name
        self.db_tables = metadata.tables
        self.engine = engine
        self.async_engine = async_engine
        self.pk_fields = []
        self.DB_NAME = settings.DB_SCHEMA
        try:
            self.db_table = self.db_tables[table_name]
        except KeyError as e:
            raise Exception(f"Table {table_name} does not exist in the database") from e
        for column in self.db_table.columns:
            if column.primary_key:
                self.pk_fields.append(column.name)

    def server_default_columns(self) -> list[str]:
        """
        Retrieves the columns with server defaults for the table associated with the given class.

        Returns:
            A list of columns with server defaults for the table.
        """
        return [
            column.name for column in self.db_table.columns if column.#server_default
        ]

    def unique_constraints(self) -> list[str]:
        """
        Retrieves the unique constraints defined for the table associated with the given class.

        Returns:
            A list of unique constraints for the table.
        """
        insp = inspect(self.engine)
        # The fully schema qualified table name cannot be used by the inspector
        # The table name must be stripped of the schema name and they must be passed as separate arguments
        # TODO - Determine if this is a hack that can be fixed?
        table_name = self.table_name.replace(f"{settings.DB_SCHEMA}.", "")
        #server_default_columns = self.#server_default_columns()
        pks_ = insp.get_pk_constraint(table_name, schema=settings.DB_SCHEMA)
        pks = [
            pk_name
            for pk_name in pks_.get("constrained_columns", [])
            if pk_name not in #server_default_columns
        ]  # type: ignore
        uniques_ = insp.get_unique_constraints(table_name, schema=settings.DB_SCHEMA)
        uniques = [
            u
            for unique in uniques_
            for u in unique.get("column_names", [])
            if unique not in #server_default_columns
        ]  # type: ignore
        if pks and uniques:
            return pks + uniques
        if uniques and not pks:
            return uniques
        if pks and not uniques:
            return pks
        return list(self.db_table.columns.keys())

    def validate_columns(
        self, value_keys: list[str], column_names: list[str] | None
    ) -> list[str]:
        """
        Validates the provided value keys against the column names.

        Args:
            value_keys (list[str]): The list of value keys to validate.
            column_names (list[str]): The list of column names to compare against.

        Raises:
            Exception: If no valid fields are provided or if a column is missing.

        Returns:
            list[str]: The validated column names.
        """
        if not column_names:
            column_names = list(self.db_table.columns.keys())
        missing_columns = set(value_keys) - set(column_names)
        if missing_columns:
            raise Exception(
                f"Column {missing_columns} is not in the column names provided."
            )
        return column_names

    async def get_unique_fields_from_values(
        self, values: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Retrieves the unique fields from the provided values.

        Args:
            values (dict[str, Any]): The values to retrieve the unique fields from.

        Returns:
            list[str]: The unique fields.
        """
        unique_constraint_field_names = self.unique_constraints()
        unique_fields = {}
        for key, val in values.items():
            if key in unique_constraint_field_names:
                unique_fields[key] = val
        return unique_fields

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

    async def select(
        self,
        # columns: list[str] | None = None,
        values: dict[str, Any],
        result_type: UnoSelectResultType = UnoSelectResultType.FIRST,
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
        """
        Inserts a row into the table.

        Args:
            values: A dictionary containing the column names and their corresponding values.

        Returns:
            None
        """
        if await self.exists(values):
            raise Exception("Record already exists")
        async with self.async_engine.begin() as conn:
            await conn.execute(insert(self.db_table).values(values))
            # conn.commit()
            # conn.close()

    """
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
