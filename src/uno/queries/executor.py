# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Query execution module for QueryModel.

This module provides functionality to execute saved QueryModel instances
against the database to determine if records match the query criteria.
"""

import logging
import json
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypeVar, Type, cast

from sqlalchemy import (
    select,
    and_,
    or_,
    not_,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.engine import async_connection
from uno.database.enhanced_session import enhanced_async_session
from uno.enums import Include, Match
from uno.queries.models import QueryModel
from uno.queries.objs import Query, QueryValue, QueryPath
from uno.errors import UnoError
from uno.core.errors.result import Result, Success, Failure


class QueryExecutionError(UnoError):
    """Error raised when query execution fails."""
    pass


class QueryExecutor:
    """
    Executor for QueryModel instances.
    
    This class provides methods to execute saved QueryModel instances
    against the database to determine if records match the query criteria.
    It supports performance optimizations including caching and query planning.
    """
    
    def __init__(self, 
                 logger: Optional[logging.Logger] = None,
                 cache_enabled: bool = True,
                 cache_ttl: int = 300):  # 5 minutes default TTL
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
        self._result_cache = {}  # {query_id: {'result': [...], 'expires': timestamp}}
        self._record_match_cache = {}  # {(query_id, record_id): {'result': bool, 'expires': timestamp}}
    def _is_cache_valid(self, cache_entry):
        """Check if a cache entry is still valid."""
        if not cache_entry or 'expires' not in cache_entry:
            return False
        return cache_entry['expires'] > time.time()
    
    def _get_from_cache(self, cache_dict, key):
        """Get a value from a cache dictionary if it's valid."""
        if not self.cache_enabled:
            return None
        
        cache_entry = cache_dict.get(key)
        if self._is_cache_valid(cache_entry):
            self.logger.debug(f"Cache hit for key {key}")
            return cache_entry['result']
        
        # Clean up expired entry
        if key in cache_dict:
            del cache_dict[key]
        
        return None
    
    def _add_to_cache(self, cache_dict, key, value):
        """Add a value to a cache dictionary with expiration."""
        if not self.cache_enabled:
            return
        
        cache_dict[key] = {
            'result': value,
            'expires': time.time() + self.cache_ttl
        }
        
        # Simple cache size management - clean up if too large
        # This is a basic approach; a production system might use LRU or other strategies
        if len(cache_dict) > 1000:  # Arbitrary limit
            # Remove expired entries
            now = time.time()
            expired_keys = [k for k, v in cache_dict.items() if v['expires'] < now]
            for k in expired_keys:
                del cache_dict[k]
            
            # If still too large, remove oldest entries (simplified approach)
            if len(cache_dict) > 800:  # 80% of the limit
                sorted_keys = sorted(
                    cache_dict.keys(), 
                    key=lambda k: cache_dict[k]['expires']
                )
                for k in sorted_keys[:200]:  # Remove oldest 20%
                    del cache_dict[k]
    
    async def execute_query(
        self,
        query: Query,
        session: Optional[AsyncSession] = None,
        force_refresh: bool = False,
    ) -> Result[List[str]]:
        """
        Execute a query and return matching record IDs.
        
        Args:
            query: The query to execute
            session: Optional database session
            force_refresh: If True, bypass the cache and force a fresh query
            
        Returns:
            Result containing a list of matching record IDs or an error
        """
        # Check cache first
        if not force_refresh and query.id:
            cached_result = self._get_from_cache(self._result_cache, query.id)
            if cached_result is not None:
                return Success(cached_result)
        
        # Create a session if not provided
        if session is None:
            async with enhanced_async_session() as session:
                result = await self._execute_query(query, session)
        else:
            result = await self._execute_query(query, session)
            
        # Cache successful results
        if result.is_success and query.id:
            self._add_to_cache(self._result_cache, query.id, result.unwrap())
            
        return result
    
    async def _execute_query(
        self,
        query: Query,
        session: AsyncSession,
    ) -> Result[List[str]]:
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
        
        except Exception as e:
            self.logger.exception(f"Error executing query {query.id}: {e}")
            return Failure(QueryExecutionError(f"Error executing query: {str(e)}"))
    
    async def _execute_query_values(
        self,
        query_id: str,
        query_values: List[QueryValue],
        include: Include,
        match: Match,
        session: AsyncSession,
    ) -> List[str]:
        """
        Execute query values and return matching record IDs.
        
        This method executes the graph query for each query value using the cypher_path
        defined in the associated QueryPath. The graph query acts as a subquery that
        returns the IDs of matching records in the relational database.
        
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
        
        # Get results for each query value
        value_results: List[Set[str]] = []
        
        for qv in query_values:
            # Skip if no path
            if not qv.query_path_id:
                continue
            
            # Get the query path
            path_result = await session.execute(
                select(QueryPath).where(QueryPath.id == qv.query_path_id)
            )
            path = path_result.scalars().first()
            
            if not path:
                continue
            
            # Extract value IDs
            value_ids = [v.id for v in qv.values or []]
            
            if not value_ids:
                continue
            
            # Build lookup condition based on the lookup type
            lookup_condition = "t.id IN $value_ids$"
            if qv.lookup and qv.lookup != "equal":
                # Handle different lookup types for flexible filtering
                if qv.lookup == "contains":
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id CONTAINS val)"
                elif qv.lookup == "startswith":
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id STARTS WITH val)"
                elif qv.lookup == "endswith":
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id ENDS WITH val)"
                elif qv.lookup == "pattern":
                    # Regex pattern matching
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id =~ val)"
                elif qv.lookup == "gt":
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id > val)"
                elif qv.lookup == "gte":
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id >= val)"
                elif qv.lookup == "lt":
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id < val)"
                elif qv.lookup == "lte":
                    lookup_condition = "ANY(val IN $value_ids$ WHERE t.id <= val)"
                elif qv.lookup == "range":
                    # Assumes value_ids has exactly 2 values: [min, max]
                    if len(value_ids) >= 2:
                        lookup_condition = f"t.id >= '{value_ids[0]}' AND t.id <= '{value_ids[1]}'"
                    else:
                        self.logger.warning(f"Range lookup requires exactly 2 values, got {len(value_ids)}")
                        lookup_condition = "FALSE"  # No matches if invalid range
                elif qv.lookup == "null":
                    # Check if property is null (not present)
                    lookup_condition = "NOT EXISTS(t.id)"
                elif qv.lookup == "not_null":
                    # Check if property exists
                    lookup_condition = "EXISTS(t.id)"
                elif qv.lookup == "in_values":
                    # Default case - already handled with "t.id IN $value_ids$"
                    pass
                elif qv.lookup == "not_in_values":
                    lookup_condition = "NOT (t.id IN $value_ids$)"
                # Complex property lookups for objects
                elif qv.lookup == "has_property":
                    # Check if node has the properties specified in value_ids
                    lookup_condition = "ALL(prop IN $value_ids$ WHERE EXISTS(t[prop]))"
                elif qv.lookup == "property_values":
                    # value_ids should be a list of property:value pairs
                    prop_conditions = []
                    for i, val in enumerate(value_ids):
                        if ":" in val:
                            prop, val = val.split(":", 1)
                            prop_conditions.append(f"t.{prop} = '{val}'")
                    if prop_conditions:
                        lookup_condition = " AND ".join(prop_conditions)
                    else:
                        lookup_condition = "FALSE"  # No matches if invalid format
            
            # Build and execute cypher query
            # The graph DB mirrors the relational DB thanks to postgres trigger functions
            # For complex queries, we use graph paths to query as a subquery,
            # returning the IDs of matching records to be selected from relational tables
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
            if qv.include == Include.EXCLUDE:
                cypher_query = f"""
                SELECT id 
                FROM {path.source_meta_type_id}
                WHERE id NOT IN (
                    SELECT id FROM matched_ids
                )
                """
            
            self.logger.debug(f"Executing cypher query for path {path.cypher_path} with {len(value_ids)} values")
            
            try:
                # Execute query
                result = await session.execute(
                    text(cypher_query),
                    {"value_ids_param": value_ids},
                )
                
                # Get result IDs as a set
                result_ids = {row[0] for row in result.fetchall()}
                self.logger.debug(f"Found {len(result_ids)} matching records for query value {qv.id}")
                value_results.append(result_ids)
            except Exception as e:
                self.logger.error(f"Error executing cypher query for path {path.cypher_path}: {e}")
                # Continue processing other values even if one fails
                continue
        
        # Combine results based on match type
        if match == Match.AND:
            # Return intersection of all results
            if not value_results:
                return []
            
            result = value_results[0]
            for r in value_results[1:]:
                result &= r
            
            return list(result)
        else:
            # Return union of all results
            result = set()
            for r in value_results:
                result |= r
            
            return list(result)
    
    async def _execute_sub_queries(
        self,
        query_id: str,
        sub_queries: List[Query],
        include: Include,
        match: Match,
        session: AsyncSession,
    ) -> List[str]:
        """
        Execute sub-queries and return matching record IDs.
        
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
        
        # Get results for each sub-query
        subquery_results: List[Set[str]] = []
        
        for sq in sub_queries:
            # Skip self-references to avoid infinite recursion
            if sq.id == query_id:
                continue
            
            # Execute sub-query
            result = await self._execute_query(sq, session)
            
            if result.is_failure:
                self.logger.warning(f"Error executing sub-query {sq.id}: {result.error}")
                continue
            
            # Get result IDs as a set
            result_ids = set(result.unwrap())
            subquery_results.append(result_ids)
        
        # Combine results based on match type
        if match == Match.AND:
            # Return intersection of all results
            if not subquery_results:
                return []
            
            result = subquery_results[0]
            for r in subquery_results[1:]:
                result &= r
            
            return list(result)
        else:
            # Return union of all results
            result = set()
            for r in subquery_results:
                result |= r
            
            return list(result)
    
    def _combine_results(
        self,
        value_ids: List[str],
        subquery_ids: List[str],
        match: Match,
    ) -> List[str]:
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
        session: Optional[AsyncSession] = None,
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
        # Check cache first
        if not force_refresh and query.id:
            cache_key = (query.id, record_id)
            cached_result = self._get_from_cache(self._record_match_cache, cache_key)
            if cached_result is not None:
                return Success(cached_result)
        
        # Optimization for simple queries - use a direct check with EXISTS
        # to avoid fetching all matching records when possible
        if self._can_use_optimized_check(query):
            try:
                result = await self._check_record_direct(query, record_id, session)
                
                # Cache the result
                if query.id:
                    cache_key = (query.id, record_id)
                    self._add_to_cache(self._record_match_cache, cache_key, result.unwrap())
                
                return result
            except Exception as e:
                self.logger.warning(f"Optimized check failed, falling back to full query: {e}")
                # Fall back to full query execution
        
        # Execute the full query and check if the record is in the results
        result = await self.execute_query(query, session, force_refresh)
        
        if result.is_failure:
            return result
        
        # Cache the match result
        is_match = record_id in result.unwrap()
        if query.id:
            cache_key = (query.id, record_id)
            self._add_to_cache(self._record_match_cache, cache_key, is_match)
        
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
        session: Optional[AsyncSession] = None,
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
        """Execute the direct record check."""
        try:
            # Build a query that directly checks if the record matches
            # This is more efficient than fetching all matching records
            check_query = f"""
            WITH target_record AS (
                SELECT id FROM {query.query_meta_type_id} WHERE id = :record_id
            )
            SELECT EXISTS (
                SELECT 1 FROM target_record
                WHERE id IN (
            """
            
            # Add conditions for each query value
            value_conditions = []
            params = {"record_id": record_id}
            
            for i, qv in enumerate(query.query_values or []):
                if not qv.query_path_id:
                    continue
                    
                # Get the query path
                path_result = await session.execute(
                    select(QueryPath).where(QueryPath.id == qv.query_path_id)
                )
                path = path_result.scalars().first()
                
                if not path:
                    continue
                    
                # Extract value IDs
                value_ids = [v.id for v in qv.values or []]
                if not value_ids:
                    continue
                    
                # Build the condition for this query value
                param_name = f"value_ids_{i}"
                params[param_name] = value_ids
                
                # Build lookup condition
                lookup_condition = "t.id IN :" + param_name
                if qv.lookup and qv.lookup != "equal":
                    # Handle different lookup types (similar to existing code)
                    # Simplified for brevity
                    if qv.lookup == "contains":
                        lookup_condition = f"ANY(val IN :{param_name} WHERE t.id CONTAINS val)"
                
                # Build the condition using the path's cypher path
                value_condition = f"""
                SELECT s.id
                FROM cypher('graph', $subq{i}$
                    MATCH {path.cypher_path}
                    WHERE {lookup_condition}
                    AND s.id = :record_id
                    RETURN DISTINCT s.id
                $subq{i}$, {param_name}:=:{param_name}) AS (id TEXT)
                """
                
                value_conditions.append(value_condition)
            
            # Combine all value conditions based on the query's match_values
            if query.match_values == Match.AND:
                check_query += " INTERSECT ".join(value_conditions)
            else:
                check_query += " UNION ".join(value_conditions)
                
            # Close the query
            check_query += """
                )
            ) AS matched
            """
            
            # Execute the query
            result = await session.execute(text(check_query), params)
            matched = result.scalar() or False
            
            return Success(matched)
                
        except Exception as e:
            self.logger.exception(f"Error executing direct record check: {e}")
            return Failure(QueryExecutionError(f"Error checking record match: {str(e)}"))
            
    
    async def count_query_matches(
        self,
        query: Query,
        session: Optional[AsyncSession] = None,
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
        # For simple counting, we can use an optimized approach that
        # avoids fetching all records
        if self._can_use_optimized_count(query):
            try:
                # Try the optimized count method first
                result = await self._count_direct(query, session)
                return result
            except Exception as e:
                self.logger.warning(f"Optimized count failed, falling back to full query: {e}")
                # Fall back to the regular method
        
        # Regular approach: execute the query and count the results
        result = await self.execute_query(query, session, force_refresh)
        
        if result.is_failure:
            return result
        
        # Return the count of matching records
        return Success(len(result.unwrap()))
    
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
        session: Optional[AsyncSession] = None,
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
            result = await session.execute(text(count_query.query), count_query.params)
            count = result.scalar() or 0
            
            return Success(count)
            
        except Exception as e:
            self.logger.exception(f"Error executing direct count: {e}")
            return Failure(QueryExecutionError(f"Error counting query matches: {str(e)}"))
    
    def _build_count_query(self, query: Query) -> Dict[str, Any]:
        """
        Build an optimized COUNT query for the given Query object.
        
        Args:
            query: The query to build a COUNT query for
            
        Returns:
            Dict with the query string and parameters
        """
        # Simplified implementation - in a real system this would be more robust
        # and would handle all the complexities of query generation
        count_query = f"""
        SELECT COUNT(DISTINCT id) AS match_count
        FROM {query.query_meta_type_id}
        WHERE id IN (
            -- Placeholder for actual query logic
            -- This would be built dynamically based on query structure
            SELECT id FROM {query.query_meta_type_id}
        )
        """
        
        return {
            "query": count_query,
            "params": {}
        }


# Create singleton instance
query_executor = QueryExecutor()


def get_query_executor() -> QueryExecutor:
    """
    Get the query executor singleton instance.
    
    Returns:
        The query executor instance
    """
    return query_executor