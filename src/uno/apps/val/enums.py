# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


class ValueType(str, enum.Enum):
    ATTRIBUTE = "attribute"
    # CALCULATION = "calculation"
    METHOD = "method"
    PROPERTY = "property"
    RELATIONSHIP = "relationship"
    RECORD = "record"
    REPORT = "report"


class DataType(str, enum.Enum):
    BOOLEAN = "bool"
    DATETIME = "datetime"
    DATE = "date"
    DECIMAL = "Decimal"
    JSON = "json"
    INTEGER = "int"
    RECORD = "record"
    TEXT = "str"
    TIME = "time"


class Lookup(str, enum.Enum):
    """
    Enumeration class for UnoRecord lookup operations.

    This class defines the available lookup operations that can be used in the UnoRecord framework.
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
    BEFORE = "__lt__"
    AFTER = "__gt__"
    ON_OR_BEFORE = "__le__"
    ON_OR_AFTER = "__ge__"


object_lookups = [
    Lookup.EQUAL.name,
    Lookup.NOT_EQUAL.name,
    Lookup.NULL.name,
    Lookup.NOT_NULL.name,
    Lookup.IN.name,
    Lookup.NOT_IN.name,
]

boolean_lookups = [
    Lookup.EQUAL.name,
    Lookup.NOT_EQUAL.name,
    Lookup.NULL.name,
    Lookup.NOT_NULL.name,
]

numeric_lookups = [
    Lookup.EQUAL.name,
    Lookup.NOT_EQUAL.name,
    Lookup.BETWEEN.name,
    Lookup.GREATER_THAN.name,
    Lookup.GREATER_THAN_OR_EQUAL.name,
    Lookup.LESS_THAN.name,
    Lookup.LESS_THAN_OR_EQUAL.name,
    Lookup.NULL.name,
    Lookup.NOT_NULL.name,
    Lookup.IN.name,
    Lookup.NOT_IN.name,
]

date_lookups = [
    Lookup.EQUAL.name,
    Lookup.NOT_EQUAL.name,
    Lookup.BETWEEN.name,
    Lookup.BEFORE.name,
    Lookup.ON_OR_BEFORE.name,
    Lookup.AFTER.name,
    Lookup.ON_OR_AFTER.name,
    Lookup.NULL.name,
    Lookup.NOT_NULL.name,
    Lookup.IN.name,
    Lookup.NOT_IN.name,
]

text_lookups = [
    Lookup.EQUAL.name,
    Lookup.NOT_EQUAL.name,
    Lookup.LIKE.name,
    Lookup.NOT_LIKE.name,
    Lookup.ILIKE.name,
    Lookup.NOT_ILIKE.name,
    Lookup.STARTS_WITH.name,
    Lookup.ENDS_WITH.name,
    Lookup.CONTAINS.name,
    Lookup.NULL.name,
    Lookup.NOT_NULL.name,
]
