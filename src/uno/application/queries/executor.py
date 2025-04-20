# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Query execution module for QueryModel.

This module provides functionality to execute saved QueryModel instances
against the database to determine if records match the query criteria.
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
from collections.abc import Callable
from typing import Any, Optional

from sqlalchemy import select, text

from uno.core.caching import QueryCache, get_cache_manager
from uno.core.errors.result import Result
from uno.enums import Include, Match
from uno.queries.errors import (
    QueryExecutionError,
    QueryPathError,
    QueryValueError,
)
from uno.queries.models import Query
from uno.queries.types import QueryPath, QueryValue

try:
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    AsyncSession = Any


# Stub for enhanced_async_session if undefined (remove if defined elsewhere)
def enhanced_async_session():
    raise NotImplementedError("enhanced_async_session is not implemented")


class QueryExecutor:
    """
    Executor for QueryModel instances.

    This class provides methods to execute saved QueryModel instances
    against the database to determine if records match the query criteria.
    It supports performance optimizations including caching and query planning.
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
    ):  # 5 minutes default TTL
        """
        Initialize the query executor.

        Args:
            logger: Optional logger
            cache_enabled: Whether to enable result caching
            cache_ttl: Time-to-live for cached results in seconds
        """
        self.logger = logger or logging.getLogger(__name__)
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl

        # Initialize cache names
        self._query_cache_name = "query_results"
        self._record_cache_name = "query_record_matches"

    async def get_query_cache(self) -> QueryCache:
        """
        Get or create the query results cache.

        Returns:
            The query cache instance
        """
        cache_manager = get_cache_manager()
        return await cache_manager.get_query_cache(
            name=self._query_cache_name, ttl=self.cache_ttl
        )

    async def get_record_cache(self) -> QueryCache:
        """
        Get or create the record matches cache.

        Returns:
            The record cache instance
        """
        cache_manager = get_cache_manager()
        return await cache_manager.get_query_cache(
            name=self._record_cache_name, ttl=self.cache_ttl
        )

    def _generate_query_cache_key(self, query: Query) -> str:
        """
        Generate a cache key for a query.

        Args:
            query: The query to generate a key for

        Returns:
            The cache key
        """
        if query.id:
            return f"query:{query.id}"

        # For queries without ID, generate a deterministic key
        # based on query content for reliable caching
        query_dict = {
            "meta_type": query.query_meta_type_id,
            "values": [
                {
                    "path_id": qv.query_path_id,
                    "include": qv.include,
                    "lookup": qv.lookup,
                    "values": [v.id for v in (qv.values or [])],
                }
                for qv in (query.query_values or [])
            ],
            "sub_queries": [
                self._generate_query_cache_key(sq) if sq.id else str(id(sq))
                for sq in (query.sub_queries or [])
            ],
            "include_values": query.include_values,
            "match_values": query.match_values,
            "include_queries": query.include_queries,
            "match_queries": query.match_queries,
        }

        # Serialize and hash
        try:
            query_json = json.dumps(query_dict, sort_keys=True)
            return f"query:{hashlib.md5(query_json.encode('utf-8')).hexdigest()}"
        except (TypeError, ValueError):
            # Fallback for non-serializable components
            return f"query:{id(query)}"

    def _generate_record_cache_key(self, query: Query, record_id: str) -> str:
        """
        Generate a cache key for a record match check.

        Args:
            query: The query to check against
            record_id: The record ID to check

        Returns:
            The cache key
        """
        query_key = self._generate_query_cache_key(query)
        return f"{query_key}:record:{record_id}"

    async def execute_query(
        self,
        query: Query,
        session: AsyncSession | None = None,
        force_refresh: bool = False,
    ) -> Result[list[str]]:
        """
        Execute a query and return matching record IDs.

        Args:
            query: The query to execute
            session: Optional database session
            force_refresh: If True, bypass the cache and force a fresh query

        Returns:
            Result containing a list of matching record IDs or an error
        """
        if not self.cache_enabled or force_refresh:
            # Skip cache if disabled or forcing refresh
            return await self._execute_query_fresh(query, session)

        # Generate cache key
        cache_key = self._generate_query_cache_key(query)

        # Try to get from modern cache first
        try:
            query_cache = await self.get_query_cache()
            cached_result = await query_cache.get(cache_key)

            if cached_result is not None:
                self.logger.debug(f"Modern cache hit for query: {cache_key}")
                return Success(cached_result)

        except Exception as e:
            self.logger.warning(f"Error accessing modern cache: {e}")

        # Not cached, execute fresh query
        result = await self._execute_query_fresh(query, session)

        # Cache successful results
        if result.is_success:
            try:
                # Cache in modern cache
                query_cache = await self.get_query_cache()
                tags = [f"meta_type:{query.query_meta_type_id}"]

                # Add tags for dependent meta types from query paths
                query_paths = set()
                for qv in query.query_values or []:
                    if qv.query_path_id:
                        query_paths.add(qv.query_path_id)

                if query_paths:
                    # Get path information for tagging
                    if session is None:
                        async with enhanced_async_session() as tmp_session:
                            for path_id in query_paths:
                                path = await tmp_session.get(QueryPath, path_id)
                                if path and path.target_meta_type_id:
                                    tags.append(f"meta_type:{path.target_meta_type_id}")
                    else:
                        for path_id in query_paths:
                            path = await session.get(QueryPath, path_id)
                            if path and path.target_meta_type_id:
                                tags.append(f"meta_type:{path.target_meta_type_id}")

                # Store in cache with tags for efficient invalidation
                await query_cache.set(
                    key=cache_key, result=result.value, tags=tags, ttl=self.cache_ttl
                )

            except Exception as e:
                self.logger.warning(f"Error storing in modern cache: {e}")

        return result

    async def _execute_query_fresh(
        self,
        query: Query,
        session: AsyncSession | None = None,
    ) -> Result[list[str]]:
        """
        Execute a query without using the cache.

        Args:
            query: The query to execute
            session: Optional database session

        Returns:
            Result containing a list of matching record IDs or an error
        """
        # Create a session if not provided
        if session is None:
            async with enhanced_async_session() as session:
                return await self._execute_query(query, session)
        else:
            return await self._execute_query(query, session)

    async def _execute_query(
        self,
        query: Query,
        session: AsyncSession,
    ) -> Result[list[str]]:
        """
        Implementation of query execution.

        Args:
            query: The query to execute
            session: Database session

        Returns:
            Result containing a list of matching record IDs or an error
        """
        try:
            # If no query values or sub-queries, return empty list
            if not query.query_values and not query.sub_queries:
                return Success([])

            # Get IDs that match query values
            value_ids = await self._execute_query_values(
                query.id,
                query.query_values or [],
                query.include_values,
                query.match_values,
                session,
            )

            # Get IDs that match sub-queries
            subquery_ids = await self._execute_sub_queries(
                query.id,
                query.sub_queries or [],
                query.include_queries,
                query.match_queries,
                session,
            )

            # Combine results based on query configuration
            result_ids = self._combine_results(
                value_ids,
                subquery_ids,
                query.match_values,
            )

            return Success(result_ids)

        except QueryPathError as e:
            # Re-use the existing error with more context
            self.logger.error(f"Path error in query {query.id}: {e}")
            return Failure(e)
        except QueryValueError as e:
            # Re-use the existing error with more context
            self.logger.error(f"Value error in query {query.id}: {e}")
            return Failure(e)
        except Exception as e:
            self.logger.exception(f"Error executing query {query.id}: {e}")
            return Failure(
                QueryExecutionError(
                    reason=str(e),
                    query_id=query.id,
                    original_exception=str(type(e).__name__),
                )
            )

    async def _execute_query_values(
        self,
        query_id: str,
        query_values: list[QueryValue],
        include: Include,
        match: Match,
        session: AsyncSession,
    ) -> list[str]:
        """
        Execute query values and return matching record IDs.

        This method executes the graph query for each query value using the cypher_path
        defined in the associated QueryPath. The graph query acts as a subquery that
        returns the IDs of matching records in the relational database.

        Optimized implementation with:
        - Batched path loading
        - Optimized SQL generation for common query patterns
        - EXISTS-based query optimization for exclusion patterns
        - Fast path for single-value equality matches

        Args:
            query_id: The query ID
            query_values: The query values to execute
            include: Whether to include or exclude matching records
            match: Whether to match all or any values
            session: Database session

        Returns:
            List of matching record IDs
        """
        if not query_values:
            return []

        path_ids = [qv.query_path_id for qv in query_values if qv.query_path_id]
        if not path_ids:
            return []

        paths_result = await session.execute(
            select(QueryPath).where(QueryPath.id.in_(path_ids))
        )
        paths = {path.id: path for path in paths_result.scalars().all()}

        # Try optimized single-value equality
        optimized = await self._try_optimized_single_value(query_values, paths, session)
        if optimized is not None:
            return optimized

        value_results: list[set[str]] = []
        for qv in query_values:
            if not qv.query_path_id or qv.query_path_id not in paths:
                continue
            path = paths[qv.query_path_id]
            value_ids = [v.id for v in qv.values or []]
            if not value_ids:
                continue
            query_strategy = self._choose_query_strategy(qv, path, value_ids)
            lookup_condition = self._build_lookup_condition(qv.lookup, value_ids)
            if query_strategy == "direct":
                cypher_query = self._build_direct_join_query(path, qv, value_ids)
            elif query_strategy == "exists":
                cypher_query = self._build_exists_query(
                    path, qv, lookup_condition, value_ids
                )
            else:
                cypher_query = self._build_standard_cypher_query(
                    path, qv, lookup_condition, value_ids
                )
            self.logger.debug(
                f"Executing {query_strategy} query for path {path.cypher_path} with {len(value_ids)} values"
            )
            try:
                query_params = {"value_ids_param": value_ids}
                if query_strategy == "direct" and len(value_ids) == 1:
                    query_params["value_id"] = value_ids[0]
                result = await session.execute(
                    text(cypher_query),
                    query_params,
                )
                result_ids = {row[0] for row in result.fetchall()}
                self.logger.debug(
                    f"Found {len(result_ids)} matching records for query value {qv.id}"
                )
                value_results.append(result_ids)
            except Exception as e:
                self._log_query_value_error(
                    e, qv, path, value_ids, query_id, query_strategy
                )
                continue
        return self._combine_query_value_results(value_results, match)

    async def _try_optimized_single_value(self, query_values, paths, session):
        if (
            len(query_values) == 1
            and query_values[0].query_path_id in paths
            and (query_values[0].lookup is None or query_values[0].lookup == "equal")
            and query_values[0].include == Include.INCLUDE
        ):
            qv = query_values[0]
            path = paths[qv.query_path_id]
            value_ids = [v.id for v in qv.values or []]
            if len(value_ids) == 1:
                if "(:s)" in path.cypher_path and "(t:" in path.cypher_path:
                    optimized_query = f"""
                    SELECT DISTINCT s.id
                    FROM {path.source_meta_type_id} s
                    JOIN {path.target_meta_type_id} t ON s.{qv.query_path_id.replace('_id', '')}_id = t.id
                    WHERE t.id = :value_id
                    """
                    try:
                        result = await session.execute(
                            text(optimized_query),
                            {"value_id": value_ids[0]},
                        )
                        result_ids = {row[0] for row in result.fetchall()}
                        self.logger.debug(
                            f"Used optimized direct-join query for {qv.id}, found {len(result_ids)} matches"
                        )
                        return list(result_ids)
                    except Exception as e:
                        self.logger.debug(
                            f"Optimized query failed, falling back to standard path: {e}"
                        )
        return None

    def _log_query_value_error(self, e, qv, path, value_ids, query_id, query_strategy):
        self.logger.error(f"Error executing query for path {path.cypher_path}: {e}")
        error_context = {
            "path_id": qv.query_path_id,
            "cypher_path": path.cypher_path,
            "value_count": len(value_ids),
            "lookup_type": qv.lookup,
            "query_id": query_id,
            "value_id": qv.id,
            "query_strategy": query_strategy,
            "error": str(e),
        }
        self.logger.warning(
            f"Path {qv.query_path_id} execution error in query {query_id}",
            extra=error_context,
        )

    def _combine_query_value_results(self, value_results, match):
        """
        Combine the sets of record IDs from each query value according to the match type.
        For AND: intersection, for OR: union. Handles edge cases for empty results.
        """
        if match == Match.AND and not value_results:
            return []
        if match == Match.OR and len(value_results) == 1:
            return list(value_results[0])
        if match == Match.AND:
            result = value_results[0]
            for r in value_results[1:]:
                result &= r
            return list(result)
        # OR or fallback
        result = set()
        for r in value_results:
            result |= r
        return list(result)

    def _choose_query_strategy(
        self, query_value: QueryValue, path: QueryPath, value_ids: list[str]
    ) -> str:
        """
        Choose the best query strategy based on the query value and path.

        Args:
            query_value: The query value to analyze
            path: The query path
            value_ids: The value IDs to filter by

        Returns:
            The query strategy: "direct", "exists", or "standard"
        """
        # For single-value equality on direct relationships, use direct join
        if (
            (query_value.lookup is None or query_value.lookup == "equal")
            and len(value_ids) == 1
            and "(:s)" in path.cypher_path
            and "(t:" in path.cypher_path
        ):
            return "direct"

        # For exclusion patterns, use EXISTS for better performance
        if query_value.include == Include.EXCLUDE:
            return "exists"

        # Default to standard query
        return "standard"

    def _build_lookup_condition(
        self, lookup: Optional[str], value_ids: list[str]
    ) -> str:
        """
        Build a lookup condition based on the lookup type.

        Args:
            lookup: The lookup type
            value_ids: The value IDs to filter by

        Returns:
            The lookup condition
        """
        # Default lookup is equality with the IN operator
        if lookup is None or lookup == "equal":
            return "t.id IN $value_ids$"

        # Handle different lookup types
        lookup_conditions = {
            "contains": "ANY(val IN $value_ids$ WHERE t.id CONTAINS val)",
            "startswith": "ANY(val IN $value_ids$ WHERE t.id STARTS WITH val)",
            "endswith": "ANY(val IN $value_ids$ WHERE t.id ENDS WITH val)",
            "pattern": "ANY(val IN $value_ids$ WHERE t.id =~ val)",
            "gt": "ANY(val IN $value_ids$ WHERE t.id > val)",
            "gte": "ANY(val IN $value_ids$ WHERE t.id >= val)",
            "lt": "ANY(val IN $value_ids$ WHERE t.id < val)",
            "lte": "ANY(val IN $value_ids$ WHERE t.id <= val)",
            "null": "NOT EXISTS(t.id)",
            "not_null": "EXISTS(t.id)",
            "in_values": "t.id IN $value_ids$",
            "not_in_values": "NOT (t.id IN $value_ids$)",
            "has_property": "ALL(prop IN $value_ids$ WHERE EXISTS(t[prop]))",
        }

        # Special case for range lookup
        if lookup == "range" and len(value_ids) >= 2:
            return f"t.id >= '{value_ids[0]}' AND t.id <= '{value_ids[1]}'"
        elif lookup == "range":
            return "FALSE"  # Invalid range

        # Special case for property_values lookup
        if lookup == "property_values":
            prop_conditions = []
            for val in value_ids:
                if ":" in val:
                    prop, val = val.split(":", 1)
                    prop_conditions.append(f"t.{prop} = '{val}'")

            if prop_conditions:
                return " AND ".join(prop_conditions)
            else:
                return "FALSE"  # Invalid format

        # Return the lookup condition or default to equality
        return lookup_conditions.get(lookup, "t.id IN $value_ids$")

    def _build_direct_join_query(
        self, path: QueryPath, query_value: QueryValue, value_ids: list[str]
    ) -> str:
        """
        Build a direct join query for a single value.

        Args:
            path: The query path
            query_value: The query value
            value_ids: The value IDs to filter by (assuming a single value)

        Returns:
            The SQL query string
        """
        # Extract table and relationship information from path
        # This is a simplified approach - in a production system we would
        # have more sophisticated parsing of the path
        rel_field = path.cypher_path.split("-[")[1].split("]")[0].replace(":", "")

        # Build direct join query
        join_query = f"""
        SELECT DISTINCT s.id
        FROM {path.source_meta_type_id} s
        JOIN {path.target_meta_type_id} t ON s.{rel_field}_id = t.id
        WHERE t.id = :value_id
        """

        return join_query

    def _build_exists_query(
        self,
        path: QueryPath,
        query_value: QueryValue,
        lookup_condition: str,
        value_ids: list[str],
    ) -> str:
        """
        Build an EXISTS-based query for exclusion patterns.

        Args:
            path: The query path
            query_value: The query value
            lookup_condition: The lookup condition
            value_ids: The value IDs to filter by

        Returns:
            The SQL query string
        """
        # For exclusion, use NOT EXISTS which can be more efficient
        exists_query = f"""
        SELECT id 
        FROM {path.source_meta_type_id}
        WHERE NOT EXISTS (
            SELECT 1
            FROM cypher('graph', $subq$
                MATCH {path.cypher_path}
                WHERE {lookup_condition}
                RETURN s.id
            $subq$, $value_ids$:=$value_ids_param$) AS (id TEXT)
            WHERE id = {path.source_meta_type_id}.id
        )
        """

        return exists_query

    def _build_standard_cypher_query(
        self,
        path: QueryPath,
        query_value: QueryValue,
        lookup_condition: str,
        value_ids: list[str],
    ) -> str:
        """
        Build a standard cypher-based query.

        Args:
            path: The query path
            query_value: The query value
            lookup_condition: The lookup condition
            value_ids: The value IDs to filter by

        Returns:
            The SQL query string
        """
        # Standard query using cypher subquery
        cypher_query = f"""
        WITH matched_ids AS (
            SELECT DISTINCT s.id
            FROM cypher('graph', $subq$
                MATCH {path.cypher_path}
                WHERE {lookup_condition}
                RETURN DISTINCT s.id
            $subq$, $value_ids$:=$value_ids_param$) AS (id TEXT)
        )
        SELECT id 
        FROM {path.source_meta_type_id}
        WHERE id IN (SELECT id FROM matched_ids)
        """

        # Convert to include/exclude based on query value configuration
        if query_value.include == Include.EXCLUDE:
            cypher_query = f"""
            SELECT id 
            FROM {path.source_meta_type_id}
            WHERE id NOT IN (
                SELECT id FROM matched_ids
            )
            """

        return cypher_query

    async def _execute_sub_queries(
        self,
        query_id: str,
        sub_queries: list[Query],
        include: Include,
        match: Match,
        session: AsyncSession,
    ) -> list[str]:
        """
        Execute sub-queries and return matching record IDs.

        Optimized implementation with:
        - Parallel execution for independent sub-queries
        - Early termination for AND conditions
        - Result size optimization for large queries

        Args:
            query_id: The query ID
            sub_queries: The sub-queries to execute
            include: Whether to include or exclude matching records
            match: Whether to match all or any sub-queries
            session: Database session

        Returns:
            List of matching record IDs
        """
        if not sub_queries:
            return []

        # Filter out self-references to avoid infinite recursion
        valid_sub_queries = [sq for sq in sub_queries if sq.id != query_id]

        if not valid_sub_queries:
            return []

        # Optimization: For AND match, execute sequentially with early termination
        # For OR match, execute in parallel
        if match == Match.AND:
            return await self._execute_and_subqueries(
                query_id, valid_sub_queries, session
            )
        else:
            return await self._execute_or_subqueries(
                query_id, valid_sub_queries, session
            )

    async def _execute_and_subqueries(
        self,
        query_id: str,
        sub_queries: list[Query],
        session: AsyncSession,
    ) -> list[str]:
        """
        Execute sub-queries with AND logic, optimized with early termination.

        Args:
            query_id: The query ID
            sub_queries: The sub-queries to execute (no self-references)
            session: Database session

        Returns:
            List of matching record IDs
        """
        # For AND logic, we can optimize by executing sequentially
        # and terminating early if any sub-query returns empty results
        current_result: Optional[set[str]] = None

        # Sort sub-queries by estimated complexity to execute simpler ones first
        # This increases chances of early termination
        sorted_queries = sorted(
            sub_queries,
            key=lambda sq: len(sq.query_values or []) + len(sq.sub_queries or []),
        )

        for sq in sorted_queries:
            # Execute sub-query
            result = await self._execute_query(sq, session)

            if result.is_failure:
                self.logger.warning(
                    f"Error executing sub-query {sq.id}: {result.error}"
                )
                continue

            # Get result IDs as a set
            result_ids = set(result.value)

            # If result is empty, we can return empty set immediately
            if not result_ids:
                self.logger.debug(
                    f"Early termination for AND sub-queries: sub-query {sq.id} returned no results"
                )
                return []

            # If this is our first result, use it directly
            if current_result is None:
                current_result = result_ids
            else:
                # Otherwise, intersect with current result
                current_result &= result_ids

                # Early termination if intersection becomes empty
                if not current_result:
                    self.logger.debug(
                        f"Early termination for AND sub-queries: intersection is empty after sub-query {sq.id}"
                    )
                    return []

        # Return final result
        return list(current_result or set())

    async def _execute_or_subqueries(
        self,
        query_id: str,
        sub_queries: list[Query],
        session: AsyncSession,
    ) -> list[str]:
        """
        Execute sub-queries with OR logic, optimized with parallel execution.

        Args:
            query_id: The query ID
            sub_queries: The sub-queries to execute (no self-references)
            session: Database session

        Returns:
            List of matching record IDs
        """
        # For OR logic, execute sub-queries in parallel for better performance
        result_futures = []

        # Launch all sub-queries concurrently
        for sq in sub_queries:
            # Create a task for each sub-query
            future = asyncio.create_task(self._execute_query(sq, session))
            result_futures.append((sq.id, future))

        # Collect results
        union_results = set()

        # Wait for all tasks to complete
        for sq_id, future in result_futures:
            try:
                result = await future

                if result.is_failure:
                    self.logger.warning(
                        f"Error executing sub-query {sq_id}: {result.error}"
                    )
                    continue

                # Add to union
                union_results.update(result.value)

            except Exception as e:
                self.logger.error(f"Unexpected error executing sub-query {sq_id}: {e}")

        return list(union_results)

    def _combine_results(
        self,
        value_ids: list[str],
        subquery_ids: list[str],
        match: Match,
    ) -> list[str]:
        """
        Combine results from query values and sub-queries.

        Args:
            value_ids: IDs from query values
            subquery_ids: IDs from sub-queries
            match: Whether to match all or any

        Returns:
            Combined list of record IDs
        """
        # Convert to sets for set operations
        value_set = set(value_ids)
        subquery_set = set(subquery_ids)

        # If either set is empty, return the other
        if not value_set:
            return list(subquery_set)

        if not subquery_set:
            return list(value_set)

        # Combine based on match type
        if match == Match.AND:
            # Return intersection
            return list(value_set & subquery_set)
        else:
            # Return union
            return list(value_set | subquery_set)

    async def check_record_matches_query(
        self,
        query: Query,
        record_id: str,
        session: AsyncSession | None = None,
        force_refresh: bool = False,
    ) -> Result[bool]:
        """
        Check if a specific record matches a query.

        This method is optimized to avoid executing the full query when possible,
        using direct record checking for better performance.

        Args:
            query: The query to check against
            record_id: The record ID to check
            session: Optional database session
            force_refresh: If True, bypass the cache and force a fresh check

        Returns:
            Result containing True if the record matches, False otherwise
        """
        if not self.cache_enabled or force_refresh:
            # Skip cache if disabled or forcing refresh
            return await self._check_record_matches_fresh(query, record_id, session)

        # Generate cache key
        cache_key = self._generate_record_cache_key(query, record_id)

        # Try to get from modern cache first
        try:
            record_cache = await self.get_record_cache()
            cached_result = await record_cache.get(cache_key)

            if cached_result is not None:
                self.logger.debug(f"Modern cache hit for record match: {cache_key}")
                return Success(cached_result)

        except Exception as e:
            self.logger.warning(f"Error accessing modern cache for record match: {e}")

        # Not cached, execute fresh query
        result = await self._check_record_matches_fresh(query, record_id, session)

        # Cache successful results
        if result.is_success:
            try:
                # Cache in modern cache
                record_cache = await self.get_record_cache()
                tags = [f"meta_type:{query.query_meta_type_id}", f"record:{record_id}"]

                # Store in cache with tags for efficient invalidation
                await record_cache.set(
                    key=cache_key, result=result.value, tags=tags, ttl=self.cache_ttl
                )

            except Exception as e:
                self.logger.warning(f"Error storing record match in modern cache: {e}")

        return result

    async def _check_record_matches_fresh(
        self,
        query: Query,
        record_id: str,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """
        Check if a record matches a query without using the cache.

        Args:
            query: The query to check against
            record_id: The record ID to check
            session: Optional database session

        Returns:
            Result containing True if the record matches, False otherwise
        """
        # Optimization for simple queries - use a direct check with EXISTS
        # to avoid fetching all matching records when possible
        if self._can_use_optimized_check(query):
            try:
                return await self._check_record_direct(query, record_id, session)
            except Exception as e:
                self.logger.warning(
                    f"Optimized check failed, falling back to full query: {e}"
                )
                # Fall back to full query execution

        # Execute the full query and check if the record is in the results
        result = await self.execute_query(query, session, force_refresh=True)

        if result.is_failure:
            return result

        # Check if the record is in the results
        is_match = record_id in result.value

        return Success(is_match)

    def _can_use_optimized_check(self, query: Query) -> bool:
        """
        Determine if a query can use the optimized direct record check.

        Args:
            query: The query to analyze

        Returns:
            True if the query can use optimized checking, False otherwise
        """
        # Optimization is only possible for relatively simple queries
        # This is a conservative implementation that can be expanded
        if not query:
            return False

        # If there are no query values, we can't optimize
        if not query.query_values:
            return False

        # If there are sub-queries, we can't optimize (yet)
        if query.sub_queries and len(query.sub_queries) > 0:
            return False

        # If we have too many query values, full query might be more efficient
        if len(query.query_values) > 5:
            return False

        return True

    async def _check_record_direct(
        self,
        query: Query,
        record_id: str,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """
        Check if a record matches a query using a direct EXISTS check.

        This optimized method avoids fetching all matching records when we only
        need to check one specific record.

        Args:
            query: The query to check against
            record_id: The record ID to check
            session: Optional database session

        Returns:
            Result containing True if the record matches, False otherwise
        """
        # Create a session if not provided
        if session is None:
            async with enhanced_async_session() as session:
                return await self._execute_direct_check(query, record_id, session)
        else:
            return await self._execute_direct_check(query, record_id, session)

    async def _execute_direct_check(
        self,
        query: Query,
        record_id: str,
        session: AsyncSession,
    ) -> Result[bool]:
        """
        Execute the direct record check with optimized SQL generation.

        This method uses several optimization strategies:
        1. Batch loading of query paths
        2. Direct join optimization for simple conditions
        3. EXISTS-based query patterns for better performance
        4. Short-circuit evaluation for AND/OR conditions

        Args:
            query: The query to check
            record_id: The record ID to check
            session: The database session

        Returns:
            Result with True if the record matches, False otherwise, or an error
        """
        try:
            # For performance, first check if the record ID is valid
            verify_query = f"""
            SELECT EXISTS (SELECT 1 FROM {query.query_meta_type_id} WHERE id = :record_id)
            """
            result = await session.execute(text(verify_query), {"record_id": record_id})
            record_exists = result.scalar() or False

            if not record_exists:
                # Record doesn't exist, can't match the query
                self.logger.debug(
                    f"Record {record_id} does not exist, skipping match check"
                )
                return Success(False)

            # Batch-load all query paths at once for performance
            path_ids = [
                qv.query_path_id
                for qv in (query.query_values or [])
                if qv.query_path_id
            ]

            if not path_ids:
                # If no path IDs, check if there are sub-queries
                if not query.sub_queries:
                    # Neither query values nor sub-queries, return True (empty query matches everything)
                    return Success(True)

                # Only sub-queries, delegate to sub-query execution with direct record check
                # Optimize: handle sub-queries without loading all matches
                sub_matches = await self._check_record_matches_subqueries(
                    query_id=query.id,
                    sub_queries=query.sub_queries,
                    record_id=record_id,
                    include=query.include_queries,
                    match=query.match_queries,
                    session=session,
                )

                # If only sub-queries, return the sub-query result directly
                return Success(sub_matches)

            # Optimization: Load all paths in one query
            paths_result = await session.execute(
                select(QueryPath).where(QueryPath.id.in_(path_ids))
            )
            paths = {path.id: path for path in paths_result.scalars().all()}

            # Check if any paths are missing
            missing_paths = [path_id for path_id in path_ids if path_id not in paths]
            if missing_paths:
                missing_paths_str = ", ".join(missing_paths)
                return Failure(
                    QueryPathError(
                        reason=f"One or more query paths not found: {missing_paths_str}",
                        path_id=missing_paths[0] if len(missing_paths) == 1 else None,
                        query_id=query.id,
                        all_missing_paths=missing_paths,
                    )
                )

            # Optimization: Special case for single equality check (very common)
            if (
                len(query.query_values) == 1
                and len(query.sub_queries or []) == 0
                and query.query_values[0].query_path_id in paths
                and (
                    query.query_values[0].lookup is None
                    or query.query_values[0].lookup == "equal"
                )
            ):
                qv = query.query_values[0]
                path = paths[qv.query_path_id]
                value_ids = [v.id for v in qv.values or []]

                # Fast path for direct relationships with simple equality - use joins
                if "(:s)" in path.cypher_path and "(t:" in path.cypher_path:
                    # Extract relationship from path
                    try:
                        rel_field = (
                            path.cypher_path.split("-[")[1]
                            .split("]")[0]
                            .replace(":", "")
                        )

                        # Build an optimized join query
                        optimized_query = f"""
                        SELECT EXISTS (
                            SELECT 1
                            FROM {query.query_meta_type_id} s
                            JOIN {path.target_meta_type_id} t ON s.{rel_field}_id = t.id
                            WHERE s.id = :record_id
                            AND t.id IN :value_ids
                        ) AS matched
                        """

                        # Execute query with parameters
                        result = await session.execute(
                            text(optimized_query),
                            {"record_id": record_id, "value_ids": value_ids},
                        )
                        matched = result.scalar() or False

                        # Adjust for include/exclude
                        if qv.include == Include.EXCLUDE:
                            matched = not matched

                        self.logger.debug(
                            f"Used optimized direct join for record check: {record_id} -> {matched}"
                        )
                        return Success(matched)
                    except Exception as e:
                        # If optimization fails, log and fall back to standard path
                        self.logger.debug(
                            f"Direct join optimization failed: {e}, using standard check"
                        )

            # Build an optimized query using EXISTS for performance
            # This avoids the overhead of fetching all matching records
            check_query_parts = []
            params = {"record_id": record_id}

            # Process each query value with optimized SQL generation
            for i, qv in enumerate(query.query_values or []):
                if not qv.query_path_id or qv.query_path_id not in paths:
                    continue

                path = paths[qv.query_path_id]
                value_ids = [v.id for v in qv.values or []]

                if not value_ids:
                    continue

                # Add parameters for this query value
                param_name = f"value_ids_{i}"
                params[param_name] = value_ids

                # Build lookup condition
                lookup_condition = self._build_lookup_condition(qv.lookup, value_ids)

                # Choose the optimal query strategy
                query_strategy = self._choose_check_strategy(qv, path, value_ids)

                # Build the condition using the optimal strategy
                if query_strategy == "direct":
                    # Build a direct join condition for better performance
                    condition = self._build_direct_check_condition(
                        i,
                        path,
                        qv,
                        record_id,
                        param_name,
                        include=(qv.include == Include.INCLUDE),
                    )
                else:
                    # Build a standard cypher-based condition
                    condition = self._build_standard_check_condition(
                        i,
                        path,
                        lookup_condition,
                        record_id,
                        param_name,
                        include=(qv.include == Include.INCLUDE),
                    )

                check_query_parts.append(condition)

            # If no valid conditions, return True if no query values, otherwise False
            if not check_query_parts:
                return Success(True if not query.query_values else False)

            # Combine all conditions based on the query's match_values
            operator = " AND " if query.match_values == Match.AND else " OR "
            combined_condition = f"({operator.join(check_query_parts)})"

            # Check if there are any sub-queries to process
            if query.sub_queries:
                # We need to check sub-queries as well
                # For performance, only do this after checking query values first

                # Execute the query value check first
                values_check_query = f"SELECT {combined_condition} AS matched"
                values_result = await session.execute(text(values_check_query), params)
                values_match = values_result.scalar() or False

                # Short-circuit evaluation based on match type
                if query.match_values == Match.AND and not values_match:
                    # If AND and values don't match, the record can't match
                    return Success(False)
                elif query.match_values == Match.OR and values_match:
                    # If OR and values match, the record matches
                    return Success(True)

                # Need to check sub-queries
                sub_matches = await self._check_record_matches_subqueries(
                    query_id=query.id,
                    sub_queries=query.sub_queries,
                    record_id=record_id,
                    include=query.include_queries,
                    match=query.match_queries,
                    session=session,
                )

                # Combine results based on the query's match type
                if query.match_values == Match.AND:
                    return Success(values_match and sub_matches)
                else:
                    return Success(values_match or sub_matches)
            else:
                # Only query values, execute and return the result
                final_query = f"SELECT {combined_condition} AS matched"
                result = await session.execute(text(final_query), params)
                matched = result.scalar() or False

                return Success(matched)

        except QueryPathError as e:
            # Re-use the existing error
            self.logger.error(f"Path error in record check {query.id}/{record_id}: {e}")
            return Failure(e)
        except Exception as e:
            self.logger.exception(f"Error executing direct record check: {e}")
            return Failure(
                QueryExecutionError(
                    reason=f"Error checking record match: {str(e)}",
                    query_id=query.id,
                    record_id=record_id,
                    operation="check_record",
                    original_exception=str(type(e).__name__),
                )
            )

    def _choose_check_strategy(
        self, query_value: QueryValue, path: QueryPath, value_ids: list[str]
    ) -> str:
        """
        Choose the best query strategy for a direct record check.

        Args:
            query_value: The query value
            path: The query path
            value_ids: The value IDs

        Returns:
            The query strategy: "direct" or "standard"
        """
        # For direct relationships with equality conditions, use direct join
        if query_value.lookup is None or query_value.lookup == "equal":
            if "(:s)" in path.cypher_path and "(t:" in path.cypher_path:
                return "direct"

        # Default to standard query
        return "standard"

    def _build_direct_check_condition(
        self,
        index: int,
        path: QueryPath,
        query_value: QueryValue,
        record_id: str,
        param_name: str,
        include: bool = True,
    ) -> str:
        """
        Build a direct join condition for a record check.

        Args:
            index: The query value index
            path: The query path
            query_value: The query value
            record_id: The record ID
            param_name: The parameter name for value IDs
            include: Whether to include or exclude matching records

        Returns:
            The SQL condition
        """
        # Extract relationship field from path
        rel_field = path.cypher_path.split("-[")[1].split("]")[0].replace(":", "")

        # Build join condition
        condition = f"""
        EXISTS (
            SELECT 1
            FROM {path.target_meta_type_id} t
            WHERE t.id IN :{param_name}
            AND EXISTS (
                SELECT 1
                FROM {path.source_meta_type_id} s
                WHERE s.id = :record_id
                AND s.{rel_field}_id = t.id
            )
        )
        """

        # Handle exclusion
        if not include:
            condition = f"NOT {condition}"

        return condition

    def _build_standard_check_condition(
        self,
        index: int,
        path: QueryPath,
        lookup_condition: str,
        record_id: str,
        param_name: str,
        include: bool = True,
    ) -> str:
        """
        Build a standard cypher-based condition for a record check.

        Args:
            index: The query value index
            path: The query path
            lookup_condition: The lookup condition
            record_id: The record ID
            param_name: The parameter name for value IDs
            include: Whether to include or exclude matching records

        Returns:
            The SQL condition
        """
        # Build cypher condition
        condition = f"""
        EXISTS (
            SELECT 1
            FROM cypher('graph', $cypher_{index}$
                MATCH {path.cypher_path}
                WHERE {lookup_condition}
                AND s.id = '{record_id}'
                RETURN DISTINCT s.id
            $cypher_{index}$, $value_ids$:=:{param_name}) AS (id TEXT)
        )
        """

        # Handle exclusion
        if not include:
            condition = f"NOT {condition}"

        return condition

    async def _check_record_matches_subqueries(
        self,
        query_id: str,
        sub_queries: list[Query],
        record_id: str,
        include: Include,
        match: Match,
        session: AsyncSession,
    ) -> bool:
        """
        Check if a record matches sub-queries.

        Args:
            query_id: The query ID
            sub_queries: The sub-queries to check
            record_id: The record ID to check
            include: Whether to include or exclude matching records
            match: Whether to match all or any sub-queries
            session: The database session

        Returns:
            True if the record matches, False otherwise
        """
        if not sub_queries:
            # No sub-queries means the record matches by default
            return True

        # Filter out self-references to avoid infinite recursion
        valid_sub_queries = [sq for sq in sub_queries if sq.id != query_id]

        if not valid_sub_queries:
            # No valid sub-queries means the record matches by default
            return True

        # For AND match, we can short-circuit if any sub-query doesn't match
        # For OR match, we can short-circuit if any sub-query matches
        if match == Match.AND:
            # Check each sub-query sequentially for early termination
            for sq in valid_sub_queries:
                result = await self.check_record_matches_query(
                    query=sq, record_id=record_id, session=session
                )

                if result.is_failure:
                    self.logger.warning(
                        f"Error checking if record {record_id} matches sub-query {sq.id}: {result.error}"
                    )
                    continue

                if not result.value:
                    # Record doesn't match this sub-query, can't match AND condition
                    return False

            # Record matches all sub-queries
            return True
        else:
            # For OR match, check sub-queries in parallel
            match_futures = []

            # Launch all checks concurrently
            for sq in valid_sub_queries:
                future = asyncio.create_task(
                    self.check_record_matches_query(
                        query=sq, record_id=record_id, session=session
                    )
                )
                match_futures.append((sq.id, future))

            # Wait for results with early termination
            for sq_id, future in match_futures:
                try:
                    result = await future

                    if result.is_failure:
                        self.logger.warning(
                            f"Error checking if record {record_id} matches sub-query {sq_id}: {result.error}"
                        )
                        continue

                    if result.value:
                        # Record matches this sub-query, matches OR condition
                        return True

                except Exception as e:
                    self.logger.error(
                        f"Unexpected error checking if record {record_id} matches sub-query {sq_id}: {e}"
                    )

            # Record doesn't match any sub-queries
            return False

    async def count_query_matches(
        self,
        query: Query,
        session: AsyncSession | None = None,
        force_refresh: bool = False,
    ) -> Result[int]:
        """
        Count the number of records that match a query.

        This method is optimized to use COUNT(*) instead of fetching all records
        when possible, for better performance with large result sets.

        Args:
            query: The query to count matches for
            session: Optional database session
            force_refresh: If True, bypass cache and force a fresh count

        Returns:
            Result containing the count of matching records
        """
        # Generate cache key with count prefix
        cache_key = f"count:{self._generate_query_cache_key(query)}"

        # Try the cache first if enabled and not forcing refresh
        if self.cache_enabled and not force_refresh:
            try:
                query_cache = await self.get_query_cache()
                cached_result = await query_cache.get(cache_key)

                if cached_result is not None:
                    self.logger.debug(f"Cache hit for count: {cache_key}")
                    return Success(cached_result)
            except Exception as e:
                self.logger.warning(f"Error accessing cache for count: {e}")

        # For simple counting, we can use an optimized approach that
        # avoids fetching all records
        if self._can_use_optimized_count(query):
            try:
                # Try the optimized count method first
                result = await self._count_direct(query, session)

                # Cache the result if successful
                if result.is_success and self.cache_enabled:
                    try:
                        query_cache = await self.get_query_cache()
                        tags = [f"meta_type:{query.query_meta_type_id}", "count"]

                        # Add same query result tags
                        query_result_key = self._generate_query_cache_key(query)
                        tags.append(f"query:{query_result_key}")

                        await query_cache.set(
                            key=cache_key,
                            result=result.value,
                            tags=tags,
                            ttl=self.cache_ttl,
                        )
                    except Exception as e:
                        self.logger.warning(f"Error caching count result: {e}")

                return result
            except Exception as e:
                self.logger.warning(
                    f"Optimized count failed, falling back to full query: {e}"
                )
                # Fall back to the regular method

        # Regular approach: execute the query and count the results
        result = await self.execute_query(query, session, force_refresh)

        if result.is_failure:
            return result

        # Count the results
        count = len(result.value)

        # Cache the count result
        if self.cache_enabled:
            try:
                query_cache = await self.get_query_cache()
                tags = [f"meta_type:{query.query_meta_type_id}", "count"]

                # Add same query result tags
                query_result_key = self._generate_query_cache_key(query)
                tags.append(f"query:{query_result_key}")

                await query_cache.set(
                    key=cache_key, result=count, tags=tags, ttl=self.cache_ttl
                )
            except Exception as e:
                self.logger.warning(f"Error caching count result: {e}")

        # Return the count
        return Success(count)

    def _can_use_optimized_count(self, query: Query) -> bool:
        """
        Determine if a query can use the optimized count method.

        Args:
            query: The query to analyze

        Returns:
            True if the query can use optimized counting, False otherwise
        """
        # Similar logic to _can_use_optimized_check, but with COUNT optimizations
        # Conservative implementation that can be expanded
        return self._can_use_optimized_check(query)

    async def _count_direct(
        self,
        query: Query,
        session: AsyncSession | None = None,
    ) -> Result[int]:
        """
        Count matching records using an optimized COUNT query.

        Args:
            query: The query to count matches for
            session: Optional database session

        Returns:
            Result containing the count of matching records
        """
        # Create a session if not provided
        if session is None:
            async with enhanced_async_session() as session:
                return await self._execute_direct_count(query, session)
        else:
            return await self._execute_direct_count(query, session)

    async def _execute_direct_count(
        self,
        query: Query,
        session: AsyncSession,
    ) -> Result[int]:
        """Execute the direct count query."""
        try:
            # Similar to _execute_query_values but with COUNT(*) instead of fetching all IDs
            # This avoids fetching and transferring potentially large result sets
            # when we only need the count
            count_query = self._build_count_query(query)

            # Execute the query
            result = await session.execute(
                text(count_query["query"]), count_query["params"]
            )
            count = result.scalar() or 0

            return Success(count)

        except QueryPathError as e:
            # Re-use the existing error
            self.logger.error(f"Path error in count query {query.id}: {e}")
            return Failure(e)
        except Exception as e:
            self.logger.exception(f"Error executing direct count: {e}")
            return Failure(
                QueryExecutionError(
                    reason=f"Error counting query matches: {str(e)}",
                    query_id=query.id,
                    operation="count",
                    original_exception=str(type(e).__name__),
                )
            )

    def _build_count_query(self, query: Query) -> dict[str, Any]:
        """
        Build an optimized COUNT query for the given Query object.

        Args:
            query: The query to build a COUNT query for

        Returns:
            Dict with the query string and parameters
        """
        # Build an optimized COUNT query based on the query structure
        params = {}

        # Start with base count
        count_query_base = f"""
        SELECT COUNT(DISTINCT s.id) AS match_count
        FROM {query.query_meta_type_id} s
        """

        # Check if this is a simple query with no complex conditions
        if not query.query_values and not query.sub_queries:
            # For queries with no conditions, we can use a fast COUNT directly
            return {"query": count_query_base, "params": params}

        # For queries with values, build a more optimized version using EXISTS
        if query.query_values:
            conditions = []

            # Process each query value
            for idx, qv in enumerate(query.query_values or []):
                if not qv.query_path_id:
                    continue

                # Extract value IDs
                value_ids = [v.id for v in qv.values or []]
                if not value_ids:
                    continue

                # Add parameters for this condition
                param_name = f"value_ids_{idx}"
                params[param_name] = value_ids

                # Determine path details - we'll need this for the condition
                path_condition = f"""
                EXISTS (
                    SELECT 1
                    FROM cypher('graph', $cypher_{idx}$
                        MATCH {qv.query_path_id}
                        WHERE t.id = ANY(:value_ids_{idx})
                        RETURN DISTINCT s.id
                    $cypher_{idx}$, value_ids_{idx}:=:value_ids_{idx}) AS (id TEXT)
                    WHERE id = s.id
                )
                """

                # Handle inclusion/exclusion logic
                if qv.include == "exclude":
                    path_condition = f"NOT {path_condition}"

                conditions.append(path_condition)

            # Combine conditions based on match type
            if conditions:
                operator = " AND " if query.match_values == "all" else " OR "
                where_clause = f"WHERE {operator.join(conditions)}"

                # Complete the query
                count_query = f"{count_query_base} {where_clause}"

                return {"query": count_query, "params": params}

        # For more complex queries (with sub-queries or not covered by above),
        # use a subquery approach
        subquery = f"""
        WITH matched_ids AS (
            SELECT id 
            FROM {query.query_meta_type_id}
            WHERE EXISTS (
                -- This would get the matched IDs using the query's logic
                -- For complex queries, we still need to use the general approach
                SELECT 1 
                FROM {query.query_meta_type_id} sq
                WHERE sq.id = {query.query_meta_type_id}.id
                -- Additional conditions would be added here
            )
        )
        SELECT COUNT(DISTINCT id) AS match_count FROM matched_ids
        """

        return {"query": subquery, "params": params}

    async def invalidate_cache_for_meta_type(self, meta_type_id: str) -> int:
        """
        Invalidate all cached query results for a specific meta type.

        This is useful when records of a certain type are modified,
        to ensure that query results remain consistent.

        Args:
            meta_type_id: The meta type ID to invalidate

        Returns:
            Number of cache entries invalidated
        """
        try:
            # Get cache manager
            cache_manager = get_cache_manager()

            # Invalidate by tag
            tag = f"meta_type:{meta_type_id}"
            count = await cache_manager.invalidate_by_tags(tag)

            self.logger.debug(
                f"Invalidated {count} query cache entries for meta type: {meta_type_id}"
            )
            return count

        except Exception as e:
            self.logger.warning(
                f"Error invalidating query cache for meta type {meta_type_id}: {e}"
            )
            return 0

    async def invalidate_cache_for_record(self, record_id: str) -> int:
        """
        Invalidate all cached record match checks for a specific record.

        This is useful when a record is modified, to ensure that
        record match checks remain consistent.

        Args:
            record_id: The record ID to invalidate

        Returns:
            Number of cache entries invalidated
        """
        try:
            # Get cache manager
            cache_manager = get_cache_manager()

            # Invalidate by tag
            tag = f"record:{record_id}"
            count = await cache_manager.invalidate_by_tags(tag)

            self.logger.debug(
                f"Invalidated {count} record match cache entries for record: {record_id}"
            )
            return count

        except Exception as e:
            self.logger.warning(
                f"Error invalidating record match cache for record {record_id}: {e}"
            )
            return 0

    async def invalidate_cache_for_query(self, query_id: str) -> int:
        """
        Invalidate all cached results for a specific query.

        This is useful when a query is modified, to ensure that
        query results remain consistent.

        Args:
            query_id: The query ID to invalidate

        Returns:
            Number of cache entries invalidated
        """
        try:
            # Get cache manager
            cache_manager = get_cache_manager()

            # Invalidate query results cache
            query_cache = await self.get_query_cache()
            count = await query_cache.invalidate(key=f"query:{query_id}")

            # Invalidate record match cache
            record_cache = await self.get_record_cache()
            count2 = await record_cache.invalidate(key_prefix=f"record:{query_id}")

            total = count + count2
            self.logger.debug(f"Invalidated {total} cache entries for query {query_id}")
            return total

        except Exception as e:
            self.logger.warning(f"Error invalidating cache for query {query_id}: {e}")

            # Try to clean up legacy cache as fallback
            count = 0
            if query_id in self._legacy_result_cache:
                del self._legacy_result_cache[query_id]
                count += 1

            legacy_record_keys = [
                k for k in self._legacy_record_match_cache.keys() if k[0] == query_id
            ]
            for k in legacy_record_keys:
                del self._legacy_record_match_cache[k]
                count += 1

            return count

    async def clear_cache(self) -> int:
        """
        Clear all query caches.

        Returns:
            Number of cache entries cleared
        """
        try:
            # Get the caches
            query_cache = await self.get_query_cache()
            record_cache = await self.get_record_cache()

            # Clear the caches
            count1 = await query_cache.cache.clear()
            count2 = await record_cache.cache.clear()

            total = count1 + count2
            self.logger.debug(f"Cleared {total} cache entries")
            return total

        except Exception as e:
            self.logger.warning(f"Error clearing query caches: {e}")
            return 0

    async def get_cache_stats(self) -> dict[str, Any]:
        """
        Get statistics for the query caches.

        Returns:
            Dictionary of cache statistics
        """
        stats = {
            "query_cache": {},
            "record_cache": {},
        }

        try:
            # Get stats for modern caches
            query_cache = await self.get_query_cache()
            record_cache = await self.get_record_cache()

            stats["query_cache"] = await query_cache.get_stats()
            stats["record_cache"] = await record_cache.get_stats()

        except Exception as e:
            self.logger.warning(f"Error getting cache stats: {e}")
            stats["error"] = str(e)

        return stats


# Create singleton instance
query_executor = QueryExecutor()


def get_query_executor() -> QueryExecutor:
    """
    Get the query executor singleton instance.

    Returns:
        The query executor instance
    """
    return query_executor


# Decorator for query result caching
def cache_query_result(
    ttl: Optional[int] = 300,
    key_prefix: str | None = None,
    tags: list[str] | None = None,
    cache_null_results: bool = True,
    ignore_params: list[str] | None = None,
) -> Callable:
    """
    Decorator for caching query execution results.

    This decorator can be used on methods that execute database queries,
    to cache their results for performance. It integrates with the
    QueryExecutor's caching system.

    Args:
        ttl: Time-to-live for cache entries in seconds (default: 300)
        key_prefix: Optional prefix for cache keys
        tags: Optional list of tags for cache invalidation
        cache_null_results: Whether to cache None/empty results (default: True)
        ignore_params: List of parameter names to ignore when generating cache key

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get query executor
            executor = get_query_executor()

            if not executor.cache_enabled:
                # Caching disabled, just call the function
                return await func(*args, **kwargs)

            # Check for force_refresh parameter
            force_refresh = kwargs.get("force_refresh", False)
            if force_refresh:
                # Skip cache if force_refresh is True
                return await func(*args, **kwargs)

            # Generate cache key
            prefix = key_prefix or func.__qualname__

            # Filter out ignored parameters
            filtered_kwargs = kwargs.copy()
            if ignore_params:
                for param in ignore_params:
                    filtered_kwargs.pop(param, None)

            # Hash the arguments to create a deterministic key
            try:
                # For more efficient caching, special handling for common function patterns
                if func.__name__ == "execute_query" and len(args) >= 1:
                    # For execute_query, base key on query id or query hash
                    query = args[0]
                    if hasattr(query, "id") and query.id:
                        # If query has an ID, use it directly
                        key = f"query:{query.id}"
                    else:
                        # Otherwise generate a hash of the query structure
                        key = executor._generate_query_cache_key(query)
                elif func.__name__ == "check_record_matches_query" and len(args) >= 2:
                    # For record matches, combine query ID/hash with record ID
                    query, record_id = args[0], args[1]
                    query_key = executor._generate_query_cache_key(query)
                    key = f"{query_key}:record:{record_id}"
                else:
                    # Standard key generation for other functions
                    # Convert args and kwargs to JSON for consistent hashing
                    args_str = json.dumps([str(arg) for arg in args], sort_keys=True)
                    kwargs_str = json.dumps(
                        {k: str(v) for k, v in filtered_kwargs.items()}, sort_keys=True
                    )
                    key_str = f"{prefix}:{args_str}:{kwargs_str}"
                    key = f"func:{hashlib.md5(key_str.encode('utf-8')).hexdigest()}"
            except (TypeError, ValueError) as e:
                # Fall back to simple key if args are not JSON serializable
                key = f"func:{prefix}:{id(args)}:{id(kwargs)}"
                logging.getLogger(__name__).warning(
                    f"Using fallback cache key due to: {e}"
                )

            # Try to get from cache
            try:
                query_cache = await executor.get_query_cache()

                cached_result = await query_cache.get(key)
                if cached_result is not None:
                    # Cache hit - log with debug level to avoid excessive logging
                    logger = logging.getLogger(__name__)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Cache hit for {key}")
                    return cached_result
            except Exception as e:
                # Log error but continue with function execution
                logging.getLogger(__name__).warning(f"Error accessing cache: {e}")

            # Cache miss or error, call the function
            start_time = time.monotonic()
            result = await func(*args, **kwargs)
            execution_time = time.monotonic() - start_time

            # Skip caching for empty results if configured that way
            if not cache_null_results and (
                result is None or (isinstance(result, (list, dict)) and not result)
            ):
                return result

            # Store in cache if successful
            try:
                query_cache = await executor.get_query_cache()

                # Construct tags for intelligent cache invalidation
                all_tags = list(tags or [])

                # Add function-specific tags
                if func.__name__ == "execute_query" and len(args) >= 1:
                    query = args[0]
                    # Add meta_type tag for query results
                    if (
                        hasattr(query, "query_meta_type_id")
                        and query.query_meta_type_id
                    ):
                        all_tags.append(f"meta_type:{query.query_meta_type_id}")

                    # Add tags for query path dependencies
                    if hasattr(query, "query_values") and query.query_values:
                        for qv in query.query_values:
                            if qv.query_path_id:
                                all_tags.append(f"path:{qv.query_path_id}")

                elif func.__name__ == "check_record_matches_query" and len(args) >= 2:
                    query, record_id = args[0], args[1]
                    # Add meta_type and record-specific tags
                    if (
                        hasattr(query, "query_meta_type_id")
                        and query.query_meta_type_id
                    ):
                        all_tags.append(f"meta_type:{query.query_meta_type_id}")
                    all_tags.append(f"record:{record_id}")

                # Add generic tags
                if hasattr(args[0], "__class__"):
                    # Add class name as tag if first arg is self
                    all_tags.append(f"class:{args[0].__class__.__name__}")
                all_tags.append(f"func:{func.__name__}")

                # Add performance-based TTL - shorter TTL for faster queries
                # This prevents cache pollution from rarely-used queries
                dynamic_ttl = ttl
                if execution_time < 0.05:  # Very fast queries (<50ms)
                    dynamic_ttl = min(ttl, 600)  # 10 minutes max for very fast queries
                elif execution_time > 1.0:  # Slow queries (>1s)
                    dynamic_ttl = max(ttl, 1800)  # At least 30 minutes for slow queries

                await query_cache.set(
                    key=key, result=result, tags=all_tags, ttl=dynamic_ttl
                )

                # Log cache miss with debug level
                logger = logging.getLogger(__name__)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Cache miss for {key}, stored with TTL={dynamic_ttl}s, tags={all_tags}"
                    )
            except Exception as e:
                # Log error but return the result anyway
                logging.getLogger(__name__).warning(f"Error storing in cache: {e}")

            return result

        # Only works with async functions
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("cache_query_result can only be used with async functions")

        return async_wrapper

    return decorator
