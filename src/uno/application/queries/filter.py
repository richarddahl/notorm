# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
This module defines the `UnoFilter` class and provides a set of predefined lookup SQL templates for constructing
dynamic queries. The `UnoFilter` class represents a filter object that can be used to generate Cypher queries
for graph databases. It includes methods for constructing Cypher paths, generating Cypher queries, and managing
child filters.

The `lookups` dictionary contains predefined SQL templates for various comparison and filtering operations.
These templates are used to dynamically construct WHERE clauses in Cypher queries based on the provided lookup
type and value. The `lookups` dictionary supports operations such as equality, inequality, greater than, less
than, containment, and more. Each lookup is represented as a key-value pair, where the key is the lookup name
(e.g., "equal", "contains") and the value is the corresponding SQL template.

Classes:
    UnoFilter: A Pydantic model that represents a filter object for constructing Cypher queries.

Attributes:
    lookups (dict): A dictionary of predefined SQL templates for various lookup operations.
    boolean_lookups (list): A list of lookup names applicable to boolean data types.
    numeric_lookups (list): A list of lookup names applicable to numeric data types.
    datetime_lookups (list): A list of lookup names applicable to datetime data types.
    text_lookups (list): A list of lookup names applicable to text data types.
"""

from typing import Any, ClassVar, Dict, List, Optional, TYPE_CHECKING, Type, Tuple
from psycopg import sql
from pydantic import BaseModel

from uno.core.protocols.filter_protocols import UnoFilterProtocol
from uno.core.types import FilterItem

# Define UnoDB for type annotations without creating circular imports
if TYPE_CHECKING:
    from uno.database.db_manager import UnoDB

# This dictionary contains predefined SQL templates for various lookup operations.
# Each key represents a lookup name, and the corresponding value is the SQL template.
# The templates can be used to construct WHERE clauses in Cypher queries.
# The SQL templates are designed to be compatible with the Cypher query language.
# The placeholders `{val}` will be replaced with the actual value during query construction
# in the `cypher_query` method of the `UnoFilter` class.
lookups = {
    "equal": sql.SQL("t.val = '{val}'"),
    "not_equal": sql.SQL("t.val <> '{val}'"),
    "gt": sql.SQL("t.val > '{val}'"),
    "gte": sql.SQL("t.val >= '{val}'"),
    "lt": sql.SQL("t.val < '{val}'"),
    "lte": sql.SQL("t.val <= '{val}'"),
    "in": sql.SQL("t.val IN ({val})"),
    "not_in": sql.SQL("t.val NOT IN ({val})"),
    "null": sql.SQL("NOT EXISTS(t.val)"),
    "not_null": sql.SQL("EXISTS(t.val)"),
    "contains": sql.SQL("t.val CONTAINS '{val}'"),
    "i_contains": sql.SQL("t.val =~ '(?i){val}'"),
    "not_contains": sql.SQL("t.val NOT CONTAINS '{val}'"),
    "not_i_contains": sql.SQL("t.val NOT =~ '(?i){val}'"),
    "starts_with": sql.SQL("t.val STARTS WITH '{val}'"),
    "i_starts_with": sql.SQL("t.val =~ '^(?i){val}'"),
    "ends_with": sql.SQL("t.val ENDS WITH '{val}'"),
    "i_ends_with": sql.SQL("t.val =~ '(?i){val}$'"),
    "after": sql.SQL("t.val < '{val}'"),
    "at_or_after": sql.SQL("t.val <= '{val}'"),
    "before": sql.SQL("t.val > '{val}'"),
    "at_or_before": sql.SQL("t.val >= '{val}'"),
}

# These lists define the lookup names applicable to different data types.
# Each list contains the lookup names that can be used for filtering data of the corresponding type.
# The lists are used to categorize the lookups based on the data type of the filter.

# The `boolean_lookups` list contains lookup names applicable to boolean data types.
boolean_lookups = ["equal", "not_equal", "null", "not_null"]

# The `numeric_lookups` list contains lookup names applicable to numeric data types.
numeric_lookups = [
    "equal",
    "not_equal",
    "null",
    "not_null",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in",
]

# The `datetime_lookups` list contains lookup names applicable to datetime data types.
datetime_lookups = [
    "equal",
    "not_equal",
    "null",
    "not_null",
    "after",
    "at_or_after",
    "before",
    "at_or_before",
    "in",
    "not_in",
]

# The `text_lookups` list contains lookup names applicable to text data types.
text_lookups = [
    "equal",
    "not_equal",
    "null",
    "not_null",
    "contains",
    "i_contains",
    "not_contains",
    "not_i_contains",
    "starts_with",
    "i_starts_with",
    "ends_with",
    "i_ends_with",
]


class UnoFilter(BaseModel):
    """
    UnoFilter is a base model class that represents a filter used in the Uno application. It provides
    methods for constructing Cypher paths, generating Cypher queries, and managing child filters.

    Attributes:
        db (ClassVar["UnoDB"]): A class-level variable that holds a database instance for the obj.
        source_node_label (str): The label of the source node in the graph.
        source_meta_type_id (str): The meta type ID of the source node.
        label (str): The label of the filter.
        target_node_label (str): The label of the target node in the graph.
        target_meta_type_id (str): The meta type ID of the target node.
        data_type (str): The data type of the filter.
        raw_data_type (type): The raw Python type of the filter's data.
        lookups (list[str]): A list of lookup operations supported by the filter.
        source_path_fragment (str): The source path fragment used in Cypher queries.
        middle_path_fragment (str): The middle path fragment used in Cypher queries.
        target_path_fragment (str): The target path fragment used in Cypher queries.
        documentation (str): Documentation or description of the filter.

    Methods:
        __subclass_init__(cls, *args, **kwargs):
            Initializes the subclass and sets up the database instance for the obj.

        __str__() -> str:
            Returns a string representation of the filter's Cypher path.

        __repr__() -> str:
            Returns a string representation of the filter in the format:
            "<UnoFilter: source_path_fragment->target_path_fragment>".

        cypher_path(parent=None, for_cypher: bool = False) -> str:
            Constructs a formatted Cypher path string based on the provided fragments and an optional parent.
            Escapes certain characters when `for_cypher` is True to prevent SQL interpretation issues.

        children(entity: Any) -> list["UnoFilter"]:
            Returns a list of child filters associated with the given domain entity.

        cypher_query(value: Any, lookup: str) -> str:
            Generates a Cypher query string based on the filter's configuration, the provided value, and lookup type.
            Handles different data types and formats the query accordingly.
    """

    db: ClassVar[Any]  # Use Any for ClassVar to avoid import issues

    source_node_label: str
    source_meta_type_id: str
    label: str
    target_node_label: str
    target_meta_type_id: str
    data_type: str
    raw_data_type: type
    lookups: list[str]
    source_path_fragment: str
    middle_path_fragment: str
    target_path_fragment: str
    documentation: str

    def __subclass_init__(cls, *args, **kwargs):
        """
        Initializes a subclass by invoking the parent class's `__subclass_init__` method
        and setting up a database factory for the subclass.

        This method is automatically called when a new subclass is created. It ensures
        that the subclass is associated with a database factory instance (`UnoDBFactory`)
        using the subclass itself as the obj.

        Args:
            cls (type): The class being initialized as a subclass.
            *args: Variable length argument list passed to the parent class's initializer.
            **kwargs: Arbitrary keyword arguments passed to the parent class's initializer.
        """
        super().__subclass_init__(*args, **kwargs)
        # Import here to avoid circular imports
        from uno.database.db_manager import UnoDBFactory

        cls.db = UnoDBFactory(obj=cls)

    def __str__(self) -> str:
        """
        Returns the string representation of the object.

        This method overrides the default `__str__` method to provide
        a custom string representation by invoking the `cypher_path` method.

        Returns:
            str: The string representation of the object.
        """
        return self.cypher_path()

    def __repr__(self) -> str:
        """
        Provide a string representation of the UnoFilter object.

        Returns:
            str: A string in the format "<UnoFilter: source_path_fragment->target_path_fragment>",
            where `source_path_fragment` and `target_path_fragment` represent the respective
            attributes of the UnoFilter instance.
        """
        return f"<UnoFilter: {self.source_path_fragment}->{self.target_path_fragment}>"

    def cypher_path(self, parent=None, for_cypher: bool = False) -> str:
        """
        Constructs a formatted cypher_path string based on the provided fragments and an optional parent.
        Args:
            parent (Optional): An optional object that provides a `source_path_fragment`.
                If provided, the resulting cypher_path will include the parent's source cypher_path fragment.

            for_cypher (bool): A flag indicating whether to escape certain characters in the resulting
                cypher_path string to prevent interpretation as SQL placeholders in cypher queries.
        Returns:
            str: A formatted cypher_path string. If `parent` is provided, the cypher_path will include
            the parent's source cypher_path fragment, the middle cypher_path fragment, and the target
            cypher_path fragment, separated by `-` and `->`. If `parent` is not provided, the
            cypher_path will only include the source and target cypher_path fragments separated by `->`.
        Notes:
            - The method escapes occurrences of `[:` and `(:` in the resulting cypher_path string
              by replacing them with `[\\:` and `(\\:`, respectively. This is done to
              prevent sqlalchemy from interpreting these characters as SQL placeholders when
              used as part of a cypher query.
        """
        # If a parent is provided, construct the Cypher path by including the parent's source path fragment,
        # the current filter's middle path fragment, and the target path fragment.
        if parent:
            if for_cypher:
                # If `for_cypher` is True, escape occurrences of `[:` and `(:` to prevent SQL interpretation issues.
                return f"{parent.source_path_fragment}-{self.middle_path_fragment}->{self.target_path_fragment}".replace(
                    "[:", "[\\:"
                ).replace(
                    "(:", "(\\:"
                )
            # If `for_cypher` is False, return the Cypher path without escaping.
            return f"{parent.source_path_fragment}-{self.middle_path_fragment}->{self.target_path_fragment}"

        # If no parent is provided, construct the Cypher path using only the source and target path fragments.
        if for_cypher:
            # If `for_cypher` is True, escape occurrences of `[:` and `(:` to prevent SQL interpretation issues.
            return f"{self.source_path_fragment}->{self.target_path_fragment}".replace(
                "[:", "[\\:"
            ).replace("(:", "(\\:")

        # If `for_cypher` is False, return the Cypher path without escaping.
        return f"{self.source_path_fragment}->{self.target_path_fragment}"

    def children(self, entity: Any) -> list["UnoFilter"]:
        """
        Retrieve a list of child filters associated with the given domain entity.

        Args:
            entity: The domain entity containing filters to retrieve.

        Returns:
            list[UnoFilter]: A list of child filters extracted from the entity's filters.
        """
        # Return a list of child filters if the entity has filters
        if hasattr(entity, "filters") and isinstance(entity.filters, dict):
            return [child for child in entity.filters.values()]
        return []

    def cypher_query(self, value: Any, lookup: str, condition: str = "AND") -> str:
        """
        Constructs a Cypher query for filtering data based on the provided value and lookup.

        Args:
            value (Any): The value to filter by. Its type depends on the `data_type` attribute.
            lookup (str): The lookup operator to use for filtering (e.g., '=', '!=', '<', etc.).
            condition (str): The condition type ("AND" or "OR") for combining filters. Defaults to "AND".

        Returns:
            str: A formatted Cypher query string.

        Raises:
            TypeError: If the `data_type` is "datetime", "date", or "time" and the `value` does not
                       have a `timestamp` method.

        Notes:
            - The `data_type` attribute determines how the `value` is processed:
                - "bool": The value is converted to a lowercase string.
                - "datetime", "date", "time": The value's `timestamp` method is used.
                - Other types: The value is converted to a string.
            - The `lookups` dictionary is expected to map `lookup` strings to Cypher WHERE clause templates.
            - The `cypher_path` method is used to generate the Cypher path for the query.
            - When condition is "OR", the query will be structured to allow for OR combinations with other filters.
        """

        if self.data_type == "bool":
            val = str(value).lower()
        elif self.data_type in ["datetime", "date", "time"]:
            # If the data type is one of "datetime", "date", or "time", attempt to convert the value to a timestamp.
            try:
                # Use the `timestamp` method to get a numeric representation of the datetime value.
                # This is necessary for Cypher queries as Apache AGE does not support datetime types.
                val = value.timestamp()
            except AttributeError:
                # Raise a TypeError if the value does not have a `timestamp` method, indicating an invalid type.
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
        else:
            val = str(value)

        # Construct the where clause using the provided lookup and value.
        # The `lookups` dictionary is used to get the appropriate SQL template for the lookup.
        # The template is formatted with the provided value.
        # The `sql.SQL` function is used to safely format the SQL query.
        where_clause = (
            lookups.get(lookup, "t.val = '{val}'").format(val=sql.SQL(val)).as_string()
        )

        # Standard AND condition query
        if condition.upper() == "AND":
            return (
                sql.SQL(
                    """
            * FROM cypher('graph', $subq$
                MATCH {cypher_path}
                WHERE {where_clause}
                RETURN DISTINCT s.id
            $subq$) AS (id TEXT)
            """
                )
                .format(
                    cypher_path=sql.SQL(self.cypher_path(for_cypher=True)),
                    where_clause=sql.SQL(where_clause),
                )
                .as_string()
            )

        # OR condition query - different format that allows combining with other filters
        return (
            sql.SQL(
                """
            * FROM cypher('graph', $subq$
                MATCH {cypher_path}
                WITH s
                WHERE {where_clause}
                RETURN DISTINCT s.id
            $subq$) AS (id TEXT)
            """
            )
            .format(
                cypher_path=sql.SQL(self.cypher_path(for_cypher=True)),
                where_clause=sql.SQL(where_clause),
            )
            .as_string()
        )

    def combined_cypher_query(self, filters: List[Tuple[Any, str, str]]) -> str:
        """
        Creates a combined Cypher query from multiple filters with support for OR conditions.

        Args:
            filters: A list of tuples containing (value, lookup, condition)
                for each filter to be combined.

        Returns:
            str: A formatted Cypher query string that combines all filters.
        """
        # Group filters by condition type
        and_filters = []
        or_filters = []

        for val, lookup, condition in filters:
            if condition.upper() == "OR":
                or_filters.append((val, lookup))
            else:
                and_filters.append((val, lookup))

        # Build the query
        if not or_filters and not and_filters:
            # No filters, return all nodes
            return (
                sql.SQL(
                    """
                * FROM cypher('graph', $subq$
                    MATCH {cypher_path}
                    RETURN DISTINCT s.id
                $subq$) AS (id TEXT)
                """
                )
                .format(
                    cypher_path=sql.SQL(self.cypher_path(for_cypher=True)),
                )
                .as_string()
            )

        # Handle only AND filters
        if and_filters and not or_filters:
            where_clauses = []
            for val, lookup in and_filters:
                if self.data_type == "bool":
                    processed_val = str(val).lower()
                elif self.data_type in ["datetime", "date", "time"]:
                    try:
                        processed_val = val.timestamp()
                    except AttributeError:
                        raise TypeError(
                            f"Value {val} is not of type {self.raw_data_type}"
                        )
                else:
                    processed_val = str(val)

                clause = (
                    lookups.get(lookup, "t.val = '{val}'")
                    .format(val=sql.SQL(processed_val))
                    .as_string()
                )
                where_clauses.append(clause)

            combined_where = " AND ".join(where_clauses)

            return (
                sql.SQL(
                    """
                * FROM cypher('graph', $subq$
                    MATCH {cypher_path}
                    WHERE {where_clause}
                    RETURN DISTINCT s.id
                $subq$) AS (id TEXT)
                """
                )
                .format(
                    cypher_path=sql.SQL(self.cypher_path(for_cypher=True)),
                    where_clause=sql.SQL(combined_where),
                )
                .as_string()
            )

        # Handle only OR filters
        if or_filters and not and_filters:
            where_clauses = []
            for val, lookup in or_filters:
                if self.data_type == "bool":
                    processed_val = str(val).lower()
                elif self.data_type in ["datetime", "date", "time"]:
                    try:
                        processed_val = val.timestamp()
                    except AttributeError:
                        raise TypeError(
                            f"Value {val} is not of type {self.raw_data_type}"
                        )
                else:
                    processed_val = str(val)

                clause = (
                    lookups.get(lookup, "t.val = '{val}'")
                    .format(val=sql.SQL(processed_val))
                    .as_string()
                )
                where_clauses.append(clause)

            combined_where = " OR ".join(where_clauses)

            return (
                sql.SQL(
                    """
                * FROM cypher('graph', $subq$
                    MATCH {cypher_path}
                    WHERE {where_clause}
                    RETURN DISTINCT s.id
                $subq$) AS (id TEXT)
                """
                )
                .format(
                    cypher_path=sql.SQL(self.cypher_path(for_cypher=True)),
                    where_clause=sql.SQL(combined_where),
                )
                .as_string()
            )

        # Handle mixed AND and OR filters (most complex case)
        and_clauses = []
        for val, lookup in and_filters:
            if self.data_type == "bool":
                processed_val = str(val).lower()
            elif self.data_type in ["datetime", "date", "time"]:
                try:
                    processed_val = val.timestamp()
                except AttributeError:
                    raise TypeError(f"Value {val} is not of type {self.raw_data_type}")
            else:
                processed_val = str(val)

            clause = (
                lookups.get(lookup, "t.val = '{val}'")
                .format(val=sql.SQL(processed_val))
                .as_string()
            )
            and_clauses.append(clause)

        or_clauses = []
        for val, lookup in or_filters:
            if self.data_type == "bool":
                processed_val = str(val).lower()
            elif self.data_type in ["datetime", "date", "time"]:
                try:
                    processed_val = val.timestamp()
                except AttributeError:
                    raise TypeError(f"Value {val} is not of type {self.raw_data_type}")
            else:
                processed_val = str(val)

            clause = (
                lookups.get(lookup, "t.val = '{val}'")
                .format(val=sql.SQL(processed_val))
                .as_string()
            )
            or_clauses.append(clause)

        # Combine the conditions properly
        combined_and = " AND ".join(and_clauses)
        combined_or = " OR ".join(or_clauses)

        # Structure the query with proper precedence: (AND conditions) OR (OR conditions)
        if and_clauses and or_clauses:
            final_where = f"({combined_and}) OR ({combined_or})"
        elif and_clauses:
            final_where = combined_and
        else:
            final_where = combined_or

        return (
            sql.SQL(
                """
            * FROM cypher('graph', $subq$
                MATCH {cypher_path}
                WHERE {where_clause}
                RETURN DISTINCT s.id
            $subq$) AS (id TEXT)
            """
            )
            .format(
                cypher_path=sql.SQL(self.cypher_path(for_cypher=True)),
                where_clause=sql.SQL(final_where),
            )
            .as_string()
        )


# Alias UnoFilter as Filter for backward compatibility
Filter = UnoFilter

# Remove this class as it's now properly defined in uno.core.types
