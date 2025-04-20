"""
Domain entities for the Queries module.

This module provides domain entities for user-definable queries and query paths used to filter
records in the knowledge graph. These entities represent the core domain objects for the
query subsystem, including query paths, query values, and queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Optional

from uno.domain.core import AggregateRoot
from uno.application.result import Result, Success, Failure
from uno.enums import Include, Match, SQLOperation

@dataclass
class QueryPath(AggregateRoot[str]):
    """
    Domain entity for query paths.

    QueryPaths represent paths in the knowledge graph that can be used in queries.
    They define how to navigate the graph from a source node to a target node.
    """

    source_meta_type_id: str
    target_meta_type_id: str
    cypher_path: str
    data_type: str
    source_meta_type: Any | None = field(default=None, repr=False)
    target_meta_type: Any | None = field(default=None, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "QueryPathModel"

    def validate(self) -> Result[None, str]:
        """Validate the query path entity."""
        if not self.source_meta_type_id:
            return Failure[None, str]("Source meta type ID cannot be empty")
        if not self.target_meta_type_id:
            return Failure[None, str]("Target meta type ID cannot be empty")
        if not self.cypher_path:
            return Failure[None, str]("Cypher path cannot be empty")
        if not self.data_type:
            return Failure[None, str]("Data type cannot be empty")
        return Success[None, str](None)

    def __str__(self) -> str:
        """String representation of the query path."""
        return self.cypher_path


@dataclass
class QueryValue(AggregateRoot[str]):
    """
    Domain entity for query values.

    QueryValues represent filter values that can be used in queries.
    They are associated with a query path and contain the actual values to filter by.
    """

    query_path_id: str
    include: Include = Include.INCLUDE
    match: Match = Match.AND
    lookup: str = "equal"
    query_path: QueryPath | None = field(default=None, repr=False)
    values: list[Any] = field(default_factory=list, repr=False)
    queries: list[Query] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "QueryValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the query value entity."""
        if not self.query_path_id:
            return Failure[None, str]("Query path ID cannot be empty")
        if not isinstance(self.include, Include):
            try:
                self.include = (
                    Include[self.include]
                    if isinstance(self.include, str)
                    else Include(self.include)
                )
            except (KeyError, ValueError):
                return Failure[None, str](f"Invalid include value: {self.include}")
        if not isinstance(self.match, Match):
            try:
                self.match = (
                    Match[self.match]
                    if isinstance(self.match, str)
                    else Match(self.match)
                )
            except (KeyError, ValueError):
                return Failure[None, str](f"Invalid match value: {self.match}")
        if not self.values and not self.queries:
            return Failure[None, str]("Query value must have either values or queries")
        return Success[None, str](None)

    def add_value(self, value: Any) -> None:
        """
        Add a value to the query value.

        Args:
            value: The value to add
        """
        if value not in self.values:
            self.values.append(value)

    def remove_value(self, value: Any) -> None:
        """
        Remove a value from the query value.

        Args:
            value: The value to remove
        """
        if value in self.values:
            self.values.remove(value)

    def add_query(self, query: "Query") -> None:
        """
        Add a query to the query value.

        Args:
            query: The query to add
        """
        if query not in self.queries:
            self.queries.append(query)

    def remove_query(self, query: "Query") -> None:
        """
        Remove a query from the query value.

        Args:
            query: The query to remove
        """
        if query in self.queries:
            self.queries.remove(query)


@dataclass
class Query(AggregateRoot[str]):
    """
    Domain entity for queries.

    Queries represent user-defined queries that can be stored and executed.
    They can include query values and sub-queries.
    """

    name: str
    query_meta_type_id: str
    description: Optional[str] = None
    include_values: Include = Include.INCLUDE
    match_values: Match = Match.AND
    include_queries: Include = Include.INCLUDE
    match_queries: Match = Match.AND
    query_meta_type: Any | None = field(default=None, repr=False)
    query_values: list[QueryValue] = field(default_factory=list, repr=False)
    sub_queries: list[Query] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "QueryModel"

    def validate(self) -> Result[None, str]:
        """Validate the query entity."""
        if not self.name:
            return Failure[None, str]("Name cannot be empty")
        if not self.query_meta_type_id:
            return Failure[None, str]("Query meta type ID cannot be empty")
        if not isinstance(self.include_values, Include):
            try:
                self.include_values = (
                    Include[self.include_values]
                    if isinstance(self.include_values, str)
                    else Include(self.include_values)
                )
            except (KeyError, ValueError):
                return Failure[None, str](f"Invalid include_values: {self.include_values}")
        if not isinstance(self.match_values, Match):
            try:
                self.match_values = (
                    Match[self.match_values]
                    if isinstance(self.match_values, str)
                    else Match(self.match_values)
                )
            except (KeyError, ValueError):
                return Failure[None, str](f"Invalid match_values: {self.match_values}")
        if not isinstance(self.include_queries, Include):
            try:
                self.include_queries = (
                    Include[self.include_queries]
                    if isinstance(self.include_queries, str)
                    else Include(self.include_queries)
                )
            except (KeyError, ValueError):
                return Failure[None, str](f"Invalid include_queries: {self.include_queries}")
        if not isinstance(self.match_queries, Match):
            try:
                self.match_queries = (
                    Match[self.match_queries]
                    if isinstance(self.match_queries, str)
                    else Match(self.match_queries)
                )
            except (KeyError, ValueError):
                return Failure[None, str](f"Invalid match_queries: {self.match_queries}")
        return Success[None, str](None)

    def __str__(self) -> str:
        """String representation of the query."""
        return self.name

    def add_query_value(self, query_value: QueryValue) -> None:
        """
        Add a query value to the query.

        Args:
            query_value: The query value to add
        """
        if query_value not in self.query_values:
            self.query_values.append(query_value)
            query_value.add_query(self)

    def remove_query_value(self, query_value: QueryValue) -> None:
        """
        Remove a query value from the query.

        Args:
            query_value: The query value to remove
        """
        if query_value in self.query_values:
            self.query_values.remove(query_value)
            query_value.remove_query(self)

    def add_sub_query(self, sub_query: "Query") -> Result[None, str]:
        """
        Add a sub-query to the query.

        Args:
            sub_query: The sub-query to add
        """
        # Prevent circular references
        if sub_query.id == self.id:
            return Failure[None, str]("Cannot add query as its own sub-query")

        if sub_query not in self.sub_queries:
            self.sub_queries.append(sub_query)
        return Success[None, str](None)

    def remove_sub_query(self, sub_query: "Query") -> None:
        """
        Remove a sub-query from the query.

        Args:
            sub_query: The sub-query to remove
        """
        if sub_query in self.sub_queries:
            self.sub_queries.remove(sub_query)
