# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum
# Filter Enumerations


class GraphType(str, enum.Enum):
    """
    Enumeration class for querying the database.

    This class represents the two type of fields that can be used in a query.

    Attributes:
        VERTEX (str): The field is a vertex.
        EDGE (str): The field is an edge.
        PROPERTY (str): The field is a property of a vertex or edge.
    """

    EDGE = "Edge"
    VERTEX = "Vertex"
    PROPERTY = "Property"


class EdgeDirection(str, enum.Enum):
    """
    Enumeration class for querying the database.

    This class represents the direction of an edge to a vertex.

    Attributes:
        FROM (str): The edge is from the vertex.
        TO (str): The edge is to the vertex.
    """

    FROM = "From"
    TO = "To"


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
    Lookup.EQUAL.name,
    Lookup.NOT_EQUAL.name,
    Lookup.NULL.name,
    Lookup.NOT_NULL.name,
    Lookup.IN.name,
    Lookup.NOT_IN.name,
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

string_lookups = [
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
