# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


# DB Enums
class SelectResultType(enum.StrEnum):
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


class SQLOperation(enum.StrEnum):
    """
    SQLOperation is an enumeration that represents different types of sql.SQL operations.

    Attributes:
        INSERT (str): Represents a sql.SQL INSERT operation.
        SELECT (str): Represents a sql.SQL SELECT operation.
        UPDATE (str): Represents a sql.SQL UPDATE operation.
        DELETE (str): Represents a sql.SQL DELETE operation.
        TRUNCATE (str): Represents a sql.SQL TRUNCATE operation.
    """

    INSERT = "Insert"
    SELECT = "Select"
    UPDATE = "Update"
    DELETE = "Delete"
    TRUNCATE = "Truncate"


class Include(enum.StrEnum):
    """
    Enumeration class for querying the database.

    This class represents the options for including or excluding something in a query.

    Attributes:
        Include (str): The query should include the specified value.
        Exclude (str): The query should exclude the specified value.
    """

    INCLUDE = "Include"
    EXCLUDE = "Exclude"


class Match(enum.StrEnum):
    """
    Enumeration class for UnoBase match types.

    The Match class represents the different match types in db queries.

    Attributes:
        AND (str): Represents the 'AND' match type.
        OR (str): Represents the 'OR' match type.
        NOT (str): Represents the 'NOT' match type.
    """

    AND = "AND"
    OR = "OR"
    NOT = "NOT"


#  Auth Enums
class TenantType(enum.StrEnum):
    """
    Enumeration class representing the types of Tenants.

    Each tenant type corresponds to a specific customer group.
    Tenants are a key concept in the UnoBase library.
    They represent an individual or a group of users that may share permissions and access to data.
    Tenant Types can be configured via the settings to restrict the number of database
    objects, users, and or user groups allowed.

    Attributes:
        INDIVIDUAL (str)
        PROFESSIONAL (str)
        TEAM (str)
        CORPORATE (str)
        ENTERPRISE (str)
    """

    INDIVIDUAL = "Individual"
    PROFESSIONAL = "Business"
    TEAM = "Team"
    CORPORATE = "Corporate"
    ENTERPRISE = "Enterprise"


# Message Enums
class MessageImportance(enum.StrEnum):
    INFORMATION = "Information"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# Report Enumerations
class Status(enum.StrEnum):
    CLOSED = "Closed"
    OPEN = "Open"
    AT_RISK = "At Risk"
    OVERDUE = "Overdue"


class State(enum.StrEnum):
    PENDING = "Pending"
    COMPLETE = "Complete"
    CANCELLED = "Cancelled"
    DEFERRED = "Deferred"


class Flag(enum.StrEnum):
    INFORMATION = "Information"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ValueType(enum.StrEnum):
    ATTRIBUTE = "attribute"
    # CALCULATION = "calculation"
    METHOD = "method"
    PROPERTY = "property"
    RELATIONSHIP = "relationship"
    RECORD = "record"
    REPORT = "report"


class DataType(enum.StrEnum):
    BOOLEAN = "bool"
    DATETIME = "datetime"
    DATE = "date"
    DECIMAL = "Decimal"
    JSON = "json"
    INTEGER = "int"
    RECORD = "record"
    TEXT = "str"
    TIME = "time"
    ENUM = "enum"


class ComparisonOperator(enum.StrEnum):
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
    I_LIKE = "ilike"
    NOT_LIKE = "notlike"
    NOT_I_LIKE = "notilike"
    STARTS_WITH = "startswith"
    I_STARTS_WITH = "istartswith"
    ENDS_WITH = "endswith"
    I_ENDS_WITH = "iendswith"
    CONTAINS = "contains"
    I_CONTAINS = "icontains"


object_comparison_operators = [
    ComparisonOperator.EQUAL.name,
    ComparisonOperator.NOT_EQUAL.name,
    ComparisonOperator.NULL.name,
    ComparisonOperator.NOT_NULL.name,
    ComparisonOperator.IN.name,
    ComparisonOperator.NOT_IN.name,
]

graph_boolean_comparison_operators = [
    ComparisonOperator.EQUAL.name,
    ComparisonOperator.NOT_EQUAL.name,
    ComparisonOperator.NULL.name,
    ComparisonOperator.NOT_NULL.name,
]

numeric_comparison_operators = [
    ComparisonOperator.EQUAL.name,
    ComparisonOperator.NOT_EQUAL.name,
    ComparisonOperator.BETWEEN.name,
    ComparisonOperator.GREATER_THAN.name,
    ComparisonOperator.GREATER_THAN_OR_EQUAL.name,
    ComparisonOperator.LESS_THAN.name,
    ComparisonOperator.LESS_THAN_OR_EQUAL.name,
    ComparisonOperator.NULL.name,
    ComparisonOperator.NOT_NULL.name,
    ComparisonOperator.IN.name,
    ComparisonOperator.NOT_IN.name,
]

text_comparison_operators = [
    ComparisonOperator.EQUAL.name,
    ComparisonOperator.NOT_EQUAL.name,
    ComparisonOperator.LIKE.name,
    ComparisonOperator.I_LIKE.name,
    ComparisonOperator.NOT_LIKE.name,
    ComparisonOperator.NOT_I_LIKE.name,
    ComparisonOperator.STARTS_WITH.name,
    ComparisonOperator.I_STARTS_WITH.name,
    ComparisonOperator.ENDS_WITH.name,
    ComparisonOperator.I_ENDS_WITH.name,
    ComparisonOperator.CONTAINS.name,
    ComparisonOperator.I_CONTAINS.name,
    ComparisonOperator.NULL.name,
    ComparisonOperator.NOT_NULL.name,
]


class GraphLookup(enum.StrEnum):
    EQUAL = "="
    NOTEQUAL = "<>"
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "IN"
    NOTIN = "NOT IN"
    NULL = "IS NULL"
    NOTNULL = "IS NOT NULL"
    CONTAINS = "=~"
    ICONTAINS = "=~"
    NOTCONTAINS = "=~"
    NOTICONTAINS = "=~"
    STARTSWITH = "=~"
    ISTARTSWITH = "=~"
    ENDSWITH = "=~"
    IENDSWITH = "=~"


graph_boolean_comparison_operators = [
    GraphLookup.EQUAL.name,
    GraphLookup.NOTEQUAL.name,
    GraphLookup.NULL.name,
    GraphLookup.NOTNULL.name,
]

graph_numeric_comparison_operators = [
    GraphLookup.EQUAL.name,
    GraphLookup.NOTEQUAL.name,
    GraphLookup.GT.name,
    GraphLookup.GTE.name,
    GraphLookup.LT.name,
    GraphLookup.LTE.name,
    GraphLookup.NULL.name,
    GraphLookup.NOTNULL.name,
    GraphLookup.IN.name,
    GraphLookup.NOTIN.name,
]

graph_text_comparison_operators = [
    GraphLookup.EQUAL.name,
    GraphLookup.NOTEQUAL.name,
    GraphLookup.CONTAINS.name,
    GraphLookup.ICONTAINS.name,
    GraphLookup.STARTSWITH.name,
    GraphLookup.ISTARTSWITH.name,
    GraphLookup.ENDSWITH.name,
    GraphLookup.IENDSWITH.name,
    GraphLookup.NULL.name,
    GraphLookup.NOTNULL.name,
]


# Workflow Enums


class WorkflowDBEvent(enum.StrEnum):
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"


class WorkflowTrigger(enum.StrEnum):
    DB_EVENT = "DB Event"
    SCHEDULE = "Schedule"
    USER = "User"
