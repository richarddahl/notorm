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
