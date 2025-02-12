# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


class ColumnSecurity(str, enum.Enum):
    """
    Enumeration class representing the security levels for Schema FieldDefinitions.

    Attributes:
        PUBLIC (str): The column is publicly accessible (in accordance with row-level security enforcement).
        PRIVATE (str): The column is accessible only to the owner, the tenant admin (if used), and superusers.
        ADMIN (str): The column is accessible only to the tenant admin (if used) and superusers.
        SECRET (str): The column is accessible only to superusers.

    """

    PUBLIC = "public"
    OWNER = "owner"
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


class SchemaOperationType(str, enum.Enum):
    """
    Enumeration representing the operation types for database schema operations.

    Attributes:
        SELECT (str): Schema used for a SELECT operation.
        INSERT (str): Schema used for an INSERT operation.
        UPDATE (str): Schema used for an UPDATE operation.
        DELETE (str): Schema used for a DELETE operation.
    """

    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class SchemaDataType(str, enum.Enum):
    """
    Enumeration representing the data types for mask configurations.

    Attributes:
        NATIVE (str): Native (python) data.
        STRING (str): Babel formatted (localized) string.
        HTML (str): HTML Form Element JSON.
    """

    NATIVE = "native"
    STRING = "string"
    HTML = "html"


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


class Cardinality(str, enum.Enum):
    """
    Enumeration representing the cardinality types for database relations.

    Attributes:
        ONE_TO_ONE (str): One-to-one relationship.
        ONE_TO_MANY (str): One-to-many relationship.
        MANY_TO_ONE (str): Many-to-one relationship.
        MANY_TO_MANY (str): Many-to-many relationship.
    """

    ONE_TO_ONE = "one_to_one"  # FKDefinition with unique constraint
    ONE_TO_MANY = "one_to_many"  # FKDefinition without unique constraint
    MANY_TO_ONE = "many_to_one"  # Reverse of FKDefinition without unique constraint
    MANY_TO_MANY = "many_to_many"  # To edge of relationship
    REV_MANY_TO_MANY = "rev_many_to_many"  # from edge of many to many relationship
