# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


# DB Enums
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
class TenantType(str, enum.Enum):
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


class MessageImportance(str, enum.Enum):
    INFORMATION = "Information"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# Report Enumerations
class Status(str, enum.Enum):
    CLOSED = "Closed"
    OPEN = "Open"
    AT_RISK = "At Risk"
    OVERDUE = "Overdue"


class State(str, enum.Enum):
    PENDING = "Pending"
    COMPLETE = "Complete"
    CANCELLED = "Cancelled"
    DEFERRED = "Deferred"


class Flag(str, enum.Enum):
    INFORMATION = "Information"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


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
    ENUM = "enum"


class Lookup(str, enum.Enum):
    """
    Enumeration class for UnoBase lookup operations.

    This class defines the available lookup operations that can be used in the UnoBase framework.
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


# Workflow Enums


class WorkflowDBEvent(str, enum.Enum):
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"


class WorkflowTrigger(str, enum.Enum):
    DB_EVENT = "DB Event"
    SCHEDULE = "Schedule"
    USER = "User"
