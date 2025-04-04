# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Any, ClassVar
from psycopg import sql
from pydantic import BaseModel

from uno.db import UnoDBFactory


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

    db: ClassVar["UnoDB"]

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
        super().__subclass_init__(*args, **kwargs)
        cls.db = UnoDBFactory(model=cls)

    def __str__(self) -> str:
        return self.cypher_path()

    def __repr__(self) -> str:
        return f"<UnoFilter: {self.source_path_fragment}->{self.target_path_fragment}>"

    def cypher_path(self, parent=None, for_cypher: bool = False) -> str:
        """
        Constructs a formatted cypher_path string based on the provided fragments and an optional parent.
        Args:
            parent (Optional): An optional object that provides a `source_path_fragment`.
                If provided, the resulting cypher_path will include the parent's source cypher_path fragment.
        Returns:
            str: A formatted cypher_path string. If `parent` is provided, the cypher_path will include
            the parent's source cypher_path fragment, the middle cypher_path fragment, and the target
            cypher_path fragment, separated by `-` and `->`. If `parent` is not provided, the
            cypher_path will only include the source and target cypher_path fragments separated by `->`.
        Notes:
            - The method escapes occurrences of `[:` and `(:` in the resulting cypher_path string
              by replacing them with `[\\:` and `(\\:`, respectively. This is done to
              prevent sqlalchemy from interpreting these characters as SQL placeholders when
              used as part of a cypher query.  This is indicated by passing for_cypher=True
              when calling the function.
        """

        if parent:
            if for_cypher:
                return f"{parent.source_path_fragment}-{self.middle_path_fragment}->{self.target_path_fragment}".replace(
                    "[:", "[\\:"
                ).replace(
                    "(:", "(\\:"
                )
            return f"{parent.source_path_fragment}-{self.middle_path_fragment}->{self.target_path_fragment}"
        if for_cypher:
            return f"{self.source_path_fragment}->{self.target_path_fragment}".replace(
                "[:", "[\\:"
            ).replace("(:", "(\\:")
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
        else:
            val = str(value)

        where_clause = lookups.get(lookup, "t.val = '{val}'")

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
                value=sql.SQL(str(val)),
            )
            .as_string()
        )
