# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


class ColumnSecurity(str, enum.Enum):
    """
    Enumeration class representing the security levels for Schema FieldDefinitions.

    Attributes:
        PUBLIC (str): The column is publicly accessible (in accordance with row-level security enforcement).
        PRIVATE (str): The column is accessible only to the created_by, the tenant admin (if used), and superusers.
        ADMIN (str): The column is accessible only to the tenant admin (if used) and superusers.
        SECRET (str): The column is accessible only to superusers.

    """

    PUBLIC = "public"
    OWNER = "created_by"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class SelectResultType(str, enum.Enum):
    """
    Enumeration representing the result types for database select operations.

    Attributes:
        FETCH_ONE (str): Fetches a single row from the result set.
        FETCH_MANY (str): Fetches multiple rows from the result set.
        FETCH_ALL (str): Fetches all rows from the result set.
        FIRST (str): Fetches the first row from the result set.
        COUNT (str): Returns the count of rows in the result set.
        KEYS (str): Returns the keys of the result set.
        SCALAR (str): Returns a single value from the result set.
    """

    FETCH_ONE = "one"
    FETCH_MANY = "many"
    FETCH_ALL = "all"
    FIRST = "first"
    COUNT = "count"
    KEYS = "keys"
    SCALAR = "scalar"


class SQLOperation(str, enum.Enum):
    """
    SQLOperation is an enumeration that represents different types of SQL operations.

    Attributes:
        INSERT (str): Represents a SQL INSERT operation.
        SELECT (str): Represents a SQL SELECT operation.
        UPDATE (str): Represents a SQL UPDATE operation.
        DELETE (str): Represents a SQL DELETE operation.
        TRUNCATE (str): Represents a SQL TRUNCATE operation.
    """

    INSERT = "Insert"
    SELECT = "Select"
    UPDATE = "Update"
    DELETE = "Delete"
    TRUNCATE = "Truncate"
