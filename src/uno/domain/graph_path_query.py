"""
Graph path query system for complex relationship traversals.

This module implements an enhanced query system specifically designed for
traversing complex relationships in the graph database using path expressions.
It provides a more expressive and efficient approach for multi-hop queries
compared to traditional filtering.
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, Type, TypeVar, Union

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from uno.database.session import async_session
from uno.domain.enhanced_query import QueryMetadata
from uno.domain.query_optimizer import QueryPerformanceTracker, QueryResultCache
from uno.queries.filter import UnoFilter

T = TypeVar("T")


class PathQuerySpecification:
    """
    Specification for a path-based graph query.

    This class encapsulates the components needed to define a graph path query,
    including path patterns, filters, and pagination controls.
    """

    def __init__(
        self,
        path: Union[str, QueryPath, UnoFilter],
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = "asc",
    ):
        """
        Initialize a path query specification.

        Args:
            path: The path expression to query (can be a string, QueryPath, or UnoFilter)
            params: Parameters for filtering along the path
            limit: Maximum number of results to return
            offset: Number of results to skip
            order_by: Field to order results by
            order_direction: Direction of ordering ("asc" or "desc")
        """
        if isinstance(path, str):
            self.path_expression = path
        elif isinstance(path, (QueryPath, UnoFilter)):
            self.path_expression = str(path)
        else:
            raise TypeError("Path must be a string, QueryPath, or UnoFilter")

        self.params = params or {}
        self.limit = limit
        self.offset = offset or 0
        self.order_by = order_by
        self.order_direction = order_direction

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path_expression": self.path_expression,
            "params": self.params,
            "limit": self.limit,
            "offset": self.offset,
            "order_by": self.order_by,
            "order_direction": self.order_direction,
        }


class GraphPathQuery:
    """
    Executes graph queries using path expressions.

    This class specializes in graph traversal queries using cypher path
    expressions, optimizing for complex relationship traversals.
    """

    def __init__(
        self,
        track_performance: bool = True,
        use_cache: bool = True,
        cache_ttl: int = 300,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the graph path query executor.

        Args:
            track_performance: Whether to track query performance
            use_cache: Whether to cache query results
            cache_ttl: Default TTL for cached results in seconds
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self.track_performance = track_performance
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl

        if track_performance:
            self.performance_tracker = QueryPerformanceTracker(logger=logger)

        if use_cache:
            self.cache = QueryResultCache(ttl_seconds=cache_ttl, logger=logger)

    async def execute(
        self, query: PathQuerySpecification
    ) -> Tuple[List[str], QueryMetadata]:
        """
        Execute a path query against the graph database.

        Args:
            query: The path query specification

        Returns:
            Tuple of (matching entity IDs, query metadata)
        """
        # Initialize query metadata
        metadata = QueryMetadata(query_path=query.path_expression, filters=query.params)

        # Generate cache key if caching is enabled
        cache_key = None
        if self.use_cache:
            cache_key = self._generate_cache_key(query)

        # Define the query function
        async def query_fn() -> List[str]:
            metadata.start_execution()

            try:
                # Build the cypher query
                cypher_query = self._build_path_query(query)

                # Execute the query
                async with async_session() as session:
                    result = await session.execute(
                        text(
                            f"""
                        SELECT * FROM cypher('graph', $$ {cypher_query} $$) AS (id TEXT)
                        """
                        )
                    )

                    # Get matching IDs
                    entity_ids = [row.id for row in result.fetchall()]

                    metadata.complete_execution(
                        record_count=len(entity_ids), source="graph_path"
                    )

                    self.logger.debug(f"Path query returned {len(entity_ids)} results")
                    return entity_ids

            except Exception as e:
                self.logger.error(f"Path query execution error: {e}")
                metadata.complete_execution(record_count=0, source="error")
                raise

        # Execute with performance tracking and caching if enabled
        if self.track_performance and self.use_cache:
            # Use tracking and caching
            async def tracked_query() -> List[str]:
                return await self.performance_tracker.track_query(
                    query_key=cache_key, callback=query_fn
                )

            # Try to get from cache or execute
            result = await self.cache.get_or_execute(
                cache_key=cache_key, query_fn=tracked_query, ttl_seconds=self.cache_ttl
            )

            # Set cache hit status in metadata
            metadata.set_cache_hit(self.cache.hits > 0)

        elif self.track_performance:
            # Only use performance tracking
            result = await self.performance_tracker.track_query(
                query_key=str(hash(query.path_expression)), callback=query_fn
            )

        elif self.use_cache:
            # Only use caching
            result = await self.cache.get_or_execute(
                cache_key=cache_key, query_fn=query_fn, ttl_seconds=self.cache_ttl
            )

            # Set cache hit status in metadata
            metadata.set_cache_hit(self.cache.hits > 0)

        else:
            # Execute directly
            result = await query_fn()

        return result, metadata

    def _generate_cache_key(self, query: PathQuerySpecification) -> str:
        """
        Generate a cache key for a query.

        Args:
            query: The path query specification

        Returns:
            A cache key string
        """
        # Convert query to a dictionary
        query_dict = query.to_dict()

        # Serialize as JSON with sorted keys for consistency
        query_json = json.dumps(query_dict, sort_keys=True)

        # Generate a hash of the JSON
        return f"path_query:{hashlib.md5(query_json.encode()).hexdigest()}"

    def _build_path_query(self, query: PathQuerySpecification) -> str:
        """
        Build a cypher query from a path query specification.

        Args:
            query: The path query specification

        Returns:
            A cypher query string
        """
        # Start with the basic MATCH clause
        cypher_query = f"MATCH {query.path_expression}"

        # Add WHERE clauses from parameters
        where_clauses = []

        for key, value in query.params.items():
            # Determine target variable and property
            target, prop = self._parse_parameter_key(key)

            # Format the value appropriately
            formatted_value = self._format_parameter_value(value)

            # Create the WHERE clause
            where_clauses.append(f"{target}.{prop} = {formatted_value}")

        # Add WHERE clause if there are parameters
        if where_clauses:
            cypher_query += f" WHERE {' AND '.join(where_clauses)}"

        # Add RETURN clause
        cypher_query += " RETURN s.id AS id"

        # Add ORDER BY if specified
        if query.order_by:
            direction = "DESC" if query.order_direction.lower() == "desc" else "ASC"
            cypher_query += f" ORDER BY s.{query.order_by} {direction}"

        # Add pagination
        if query.offset:
            cypher_query += f" SKIP {query.offset}"
        if query.limit:
            cypher_query += f" LIMIT {query.limit}"

        return cypher_query

    def _parse_parameter_key(self, key: str) -> Tuple[str, str]:
        """
        Parse a parameter key into target and property.

        Args:
            key: The parameter key (e.g., "s.name" or "name")

        Returns:
            Tuple of (target, property)
        """
        if "." in key:
            return tuple(key.split(".", 1))

        # Default to source node if not specified
        return "s", key

    def _format_parameter_value(self, value: Any) -> str:
        """
        Format a parameter value for use in a cypher query.

        Args:
            value: The parameter value

        Returns:
            Formatted string representation
        """
        if isinstance(value, str):
            # Escape single quotes in strings
            escaped_value = value.replace("'", "\\'")
            return f"'{escaped_value}'"
        elif value is None:
            return "NULL"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (list, tuple, set)):
            # Format list values
            items = [self._format_parameter_value(item) for item in value]
            return f"[{', '.join(items)}]"
        elif isinstance(value, dict):
            # Handle dictionaries
            if "lookup" in value and "val" in value:
                # This is a lookup dict
                lookup = value["lookup"]
                val = value["val"]

                if lookup == "eq":
                    return f"= {self._format_parameter_value(val)}"
                elif lookup == "neq":
                    return f"<> {self._format_parameter_value(val)}"
                elif lookup == "gt":
                    return f"> {self._format_parameter_value(val)}"
                elif lookup == "gte":
                    return f">= {self._format_parameter_value(val)}"
                elif lookup == "lt":
                    return f"< {self._format_parameter_value(val)}"
                elif lookup == "lte":
                    return f"<= {self._format_parameter_value(val)}"
                elif lookup == "contains":
                    return f"CONTAINS {self._format_parameter_value(val)}"
                elif lookup == "starts_with":
                    return f"STARTS WITH {self._format_parameter_value(val)}"
                elif lookup == "ends_with":
                    return f"ENDS WITH {self._format_parameter_value(val)}"
                elif lookup == "in":
                    return f"IN {self._format_parameter_value(val)}"
                else:
                    return f"= {self._format_parameter_value(val)}"

            # Generic dict formatting
            items = [
                f"{k}: {self._format_parameter_value(v)}" for k, v in value.items()
            ]
            return f"{{{', '.join(items)}}}"
        else:
            # Other types
            return str(value)


class GraphPathQueryService:
    """
    Service for executing graph path queries and returning entity objects.

    This class connects graph path queries with entity repositories to provide
    a complete query service that returns full domain objects.
    """

    def __init__(
        self, path_query: GraphPathQuery, logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the graph path query service.

        Args:
            path_query: The graph path query executor
            logger: Optional logger for diagnostic output
        """
        self.path_query = path_query
        self.logger = logger or logging.getLogger(__name__)

    async def query_entities(
        self, query: PathQuerySpecification, repository: Any, entity_type: Type[T]
    ) -> Tuple[List[T], QueryMetadata]:
        """
        Execute a path query and return the corresponding entity objects.

        Args:
            query: The path query specification
            repository: Repository to fetch entities from
            entity_type: Type of entity to return

        Returns:
            Tuple of (entity objects, query metadata)
        """
        # Execute the path query to get entity IDs
        entity_ids, metadata = await self.path_query.execute(query)

        if not entity_ids:
            return [], metadata

        # Retrieve entities from the repository
        entities: List[T] = []

        for entity_id in entity_ids:
            entity = await repository.get(entity_id)
            if entity:
                entities.append(entity)

        # Update metadata with final count
        metadata.record_count = len(entities)

        return entities, metadata

    async def count_query_results(self, query: PathQuerySpecification) -> int:
        """
        Count the results of a path query without retrieving the entities.

        Args:
            query: The path query specification

        Returns:
            Count of matching entities
        """
        # Create a query without pagination to get all IDs
        count_query = PathQuerySpecification(
            path=query.path_expression, params=query.params
        )

        # Execute the query
        entity_ids, _ = await self.path_query.execute(count_query)
        return len(entity_ids)

    async def query_exists(self, query: PathQuerySpecification) -> bool:
        """
        Check if a path query would return any results.

        Args:
            query: The path query specification

        Returns:
            True if the query would return results, False otherwise
        """
        # Modify the query to return at most 1 result
        exists_query = PathQuerySpecification(
            path=query.path_expression, params=query.params, limit=1
        )

        # Execute the query
        entity_ids, _ = await self.path_query.execute(exists_query)
        return len(entity_ids) > 0
