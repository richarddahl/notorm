# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL index builder."""

from typing import List, Optional


class SQLIndexBuilder:
    """Builder for SQL indexes.

    This class provides a fluent interface for building SQL index
    statements with proper validation and formatting.

    Example:
        ```python
        index_sql = (
            SQLIndexBuilder()
            .with_schema("public")
            .with_table("users")
            .with_name("users_email_idx")
            .with_columns(["email"])
            .unique()
            .build()
        )
        ```
    """

    def __init__(self):
        """Initialize the SQL index builder."""
        self.schema = None
        self.table_name = None
        self.index_name = None
        self.columns = []
        self.is_unique = False
        self.index_method = "btree"
        self.nulls_distinct = True
        self.include_columns = []
        self.where_clause = None

    def with_schema(self, schema: str) -> "SQLIndexBuilder":
        """Set the schema for the index.

        Args:
            schema: Schema name

        Returns:
            Self for method chaining
        """
        self.schema = schema
        return self

    def with_table(self, table_name: str) -> "SQLIndexBuilder":
        """Set the table for the index.

        Args:
            table_name: Table name

        Returns:
            Self for method chaining
        """
        self.table_name = table_name
        return self

    def with_name(self, index_name: str) -> "SQLIndexBuilder":
        """Set the name of the index.

        Args:
            index_name: Index name

        Returns:
            Self for method chaining
        """
        self.index_name = index_name
        return self

    def with_columns(self, columns: list[str]) -> "SQLIndexBuilder":
        """Set the columns for the index.

        Args:
            columns: List of column names

        Returns:
            Self for method chaining
        """
        self.columns = columns
        return self

    def with_method(self, method: str) -> "SQLIndexBuilder":
        """Set the index method.

        Args:
            method: Index method (btree, hash, gist, etc.)

        Returns:
            Self for method chaining
        """
        self.index_method = method
        return self

    def unique(self, is_unique: bool = True) -> "SQLIndexBuilder":
        """Set the index to be unique.

        Args:
            is_unique: Whether the index is unique

        Returns:
            Self for method chaining
        """
        self.is_unique = is_unique
        return self

    def with_nulls_not_distinct(self) -> "SQLIndexBuilder":
        """Set NULLS NOT DISTINCT for the index.

        Returns:
            Self for method chaining
        """
        self.nulls_distinct = False
        return self

    def include(self, columns: list[str]) -> "SQLIndexBuilder":
        """Add columns to include in the index but not in the key.

        Args:
            columns: List of column names to include

        Returns:
            Self for method chaining
        """
        self.include_columns = columns
        return self

    def where(self, condition: str) -> "SQLIndexBuilder":
        """Add a WHERE clause to the index.

        Args:
            condition: WHERE condition

        Returns:
            Self for method chaining
        """
        self.where_clause = condition
        return self

    def build(self) -> str:
        """Build the SQL index statement.

        Returns:
            SQL index statement

        Raises:
            ValueError: If required parameters are missing
        """
        if (
            not self.schema
            or not self.table_name
            or not self.index_name
            or not self.columns
        ):
            raise ValueError("Schema, table name, index name, and columns are required")

        unique = "UNIQUE " if self.is_unique else ""

        nulls_clause = ""
        if self.is_unique and not self.nulls_distinct:
            nulls_clause = "NULLS NOT DISTINCT "

        include_clause = ""
        if self.include_columns:
            include_clause = f" INCLUDE ({', '.join(self.include_columns)})"

        where_clause = ""
        if self.where_clause:
            where_clause = f" WHERE {self.where_clause}"

        return f"""
            CREATE {unique}INDEX {self.index_name}
            ON {self.schema}.{self.table_name} USING {self.index_method} ({', '.join(self.columns)})
            {nulls_clause}{include_clause}{where_clause};
        """
