# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Any
from psycopg import sql
from pydantic import BaseModel, ConfigDict


lookups = {
    "equal": "t.val = '{val}'",
    "not_equal": "t.val <> '{val}'",
    "gt": "t.val > '{val}'",
    "gte": "t.val >= '{val}'",
    "lt": "t.val < '{val}'",
    "lte": "t.val <= '{val}'",
    "in": "t.val IN ({val})",
    "not_in": "t.val NOT IN ({val})",
    "null": "NOT EXISTS(t.val)",
    "not_null": "EXISTS(t.val)",
    "contains": "t.val CONTAINS '{val}'",
    "i_contains": "t.val =~ '(?i){val}'",
    "not_contains": "t.val NOT CONTAINS '{val}'",
    "not_i_contains": "t.val NOT =~ '(?i){val}'",
    "starts_with": "t.val STARTS WITH '{val}'",
    "i_starts_with": "t.val =~ '^(?i){val}'",
    "ends_with": "t.val ENDS WITH '{val}'",
    "i_ends_with": "t.val =~ '(?i){val}$'",
    "after": "t.val < '{val}'",
    "at_or_after": "t.val <= '{val}'",
    "before": "t.val > '{val}'",
    "at_or_before": "t.val >= '{val}'",
}

boolean_lookups = ["equal", "not_equal", "null", "not_null"]

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

string_lookups = [
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

    def __str__(self) -> str:
        return self.path()

    def __repr__(self) -> str:
        return f"<UnoFilter: {self.source_path_fragment}->{self.target_path_fragment}>"

    def path(self, parent: "UnoFilter" = None) -> str:
        if parent:
            return f"{parent.source_path_fragment}-{self.middle_path_fragment}->{self.target_path_fragment}"
        return f"{self.source_path_fragment}->{self.target_path_fragment}"

    def children(self, model: "UnoModel") -> list["UnoFilter"]:
        """Return a list of child filters."""
        return [child for child in model.filters.values()]

    def cypher_query(self, value: Any, lookup: str) -> str:
        if self.data_type == "bool":
            val = str(value).lower()
        elif self.data_type in ["datetime", "date", "time"]:
            try:
                val = value.timestamp()
            except AttributeError:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            print(val)
        else:
            val = str(value)

        where_clause = lookups.get(lookup)

        return (
            sql.SQL(
                """
        * FROM cypher('graph', $subq$
            MATCH {path}
            WHERE {where_clause}
            RETURN DISTINCT s.id
        $subq$) AS (id TEXT)
        """
            )
            .format(
                path=sql.SQL(self.path()),
                where_clause=sql.SQL(where_clause),
                value=sql.SQL(str(val)),
            )
            .as_string()
        )


class FilterParam(BaseModel):
    """FilterParam is used to validate the filter parameters for the ListRouter."""

    model_config = ConfigDict(extra="forbid")
