# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL statement representations with metadata."""

from enum import Enum
from typing import List
from pydantic import BaseModel


class SQLStatementType(Enum):
    """Types of SQL statements that can be emitted."""

    FUNCTION = "function"
    TRIGGER = "trigger"
    INDEX = "index"
    CONSTRAINT = "constraint"
    GRANT = "grant"
    VIEW = "view"
    PROCEDURE = "procedure"
    TABLE = "table"
    ROLE = "role"
    SCHEMA = "schema"
    EXTENSION = "extension"
    DATABASE = "database"
    INSERT = "insert"


class SQLStatement(BaseModel):
    """A SQL statement with metadata.

    This class represents a SQL statement along with metadata about
    the statement including its name, type, and dependencies.

    Attributes:
        name: Unique identifier for the statement
        type: Type of SQL statement (function, trigger, etc.)
        sql: The actual SQL statement to execute
        depends_on: List of statement names this statement depends on
    """

    name: str
    type: SQLStatementType
    sql: str
    depends_on: list[str] = []
