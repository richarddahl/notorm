# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum
# Filter Enumerations


class Include(str, enum.Enum):
    """
    Enumeration class for querying the database.

    This class represents the options for including or excluding something in a query.

    Attributes:
        Include (str): The query should include the specified value.
        Exclude (str): The query should exclude the specified value.
    """

    INCLUDE = "Include"
    EXCLUDE = "Exclude"


class Match(str, enum.Enum):
    """
    Enumeration class for Uno match types.

    The Match class represents the different match types in db queries.

    Attributes:
        AND (str): Represents the 'AND' match type.
        OR (str): Represents the 'OR' match type.
        NOT (str): Represents the 'NOT' match type.
    """

    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class GraphType(str, enum.Enum):
    """
    Enumeration class representing the possible field types in the Uno application.

    Attributes:
        ARRAY (str): Represents a list field type.
        BIGINT (str): Represents an integer field type.
        BOOLEAN (str): Represents a boolean field type.
        DATE (str): Represents a date field type.
        DECIMAL (str): Represents a decimal field type.
        ENUM (str): Represents an enumeration field type.
        INTERVAL (str): Represents a time interval field type.
        JSON (str): Represents a JSON field type.
        TEXT (str): Represents a text field type.
        TIME (str): Represents a time field type.
        TIMESTAMP (str): Represents a timestamp field type.
        TEXT (str): Represents a variable-length character field type.

    """

    ARRAY = "list"
    BIGINT = "int"
    BOOLEAN = "bool"
    DATE = "date"
    DECIMAL = "Decimal"
    ENUM = "Enum"
    INTERVAL = "timedelta"
    JSON = "dict"
    TEXT = "str"
    TIME = "time"
    TIMESTAMP = "datetime"
    TEXT = "str"


class Lookup(str, enum.Enum):
    """
    Enumeration class for Uno lookup operations.

    This class defines the available lookup operations that can be used in the Uno framework.
    Each lookup operation is represented by a string value.

    Attributes:
        EQUAL (str): uses the sqlalchemy __eq__ method
        NOT_EQUAL (str): uses the sqlalchemy __ne__ method
        GREATER_THAN (str): uses the sqlalchemy __gt__ method
        GREATER_THAN_OR_EQUAL (str): uses the sqlalchemy __ge__ method
        LESS_THAN (str): uses the sqlalchemy __lt__ method
        LESS_THAN_OR_EQUAL (str): uses the sqlalchemy __le__ method
        BETWEEN (str): uses the sqlalchemy between method
        IN (str): uses the sqlalchemy in_ method
        NOT_IN (str): uses the sqlalchemy not_in method
        NULL (str): uses the sqlalchemy is_ method
        NOT_NULL (str): uses the sqlalchemy is_not method
        LIKE (str): uses the sqlalchemy like method
        ILIKE (str): uses the sqlalchemy ilike method
        NOT_LIKE (str): uses the sqlalchemy notlike method
        NOT_ILIKE (str): uses the sqlalchemy notilike method
        STARTS_WITH (str): uses the sqlalchemy startswith method
        ENDS_WITH (str): uses the sqlalchemy endswith method
        CONTAINS (str): uses the sqlalchemy contains method
    """

    EQUAL = "__eq__"
    NOT_EQUAL = "__ne__"
    GREATER_THAN = "__gt__"
    GREATER_THAN_OR_EQUAL = "__ge__"
    LESS_THAN = "__lt__"
    LESS_THAN_OR_EQUAL = "__le__"
    BETWEEN = "between"
    IN = "in_"
    NOT_IN = "not_in"
    NULL = "is_"
    NOT_NULL = "is_not"
    LIKE = "like"
    ILIKE = "ilike"
    NOT_LIKE = "notlike"
    NOT_ILIKE = "notilike"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    CONTAINS = "contains"


related_lookups = [
    Lookup.EQUAL,
    Lookup.NOT_EQUAL,
    Lookup.NULL,
    Lookup.NOT_NULL,
    Lookup.IN,
    Lookup.NOT_IN,
]

numeric_lookups = [
    Lookup.EQUAL,
    Lookup.NOT_EQUAL,
    Lookup.BETWEEN,
    Lookup.GREATER_THAN,
    Lookup.GREATER_THAN_OR_EQUAL,
    Lookup.LESS_THAN,
    Lookup.LESS_THAN_OR_EQUAL,
    Lookup.NULL,
    Lookup.NOT_NULL,
    Lookup.IN,
    Lookup.NOT_IN,
]

string_lookups = [
    Lookup.EQUAL,
    Lookup.NOT_EQUAL,
    Lookup.LIKE,
    Lookup.NOT_LIKE,
    Lookup.ILIKE,
    Lookup.NOT_ILIKE,
    Lookup.STARTS_WITH,
    Lookup.ENDS_WITH,
    Lookup.CONTAINS,
    Lookup.NULL,
    Lookup.NOT_NULL,
]
