"""
Enhanced query system for domain objects.

This module extends the basic query system with optimizations for performance
and flexibility, integrating with the graph database for complex queries.
It provides efficient data retrieval capabilities for the domain model.
"""

import logging
import json
import time
import hashlib
from typing import (
    Dict,
    List,
    Any,
    Optional,
    TypeVar,
    Generic,
    Union,
    Set,
    Type,
    Tuple,
    Callable,
    Awaitable,
)
from datetime import datetime

from sqlalchemy import text, func
from sqlalchemy.exc import SQLAlchemyError

from uno.domain.core import Entity
from uno.core.base.respository import Repository
from uno.domain.query import QuerySpecification, QueryResult
from uno.database.session import async_session
from uno.domain.query_optimizer import (
    QueryPerformanceTracker,
    QueryResultCache,
    GraphQueryOptimizer,
    MaterializedQueryView,
)


T = TypeVar("T", bound=Entity)
Q = TypeVar("Q", bound=QuerySpecification)


class QueryMetadata:
    """
    Metadata for tracking queries and their execution.

    Provides context for query execution including performance data
    and optimization hints.
    """

    def __init__(self, query_path: str, filters: Optional[Dict[str, Any]] = None):
        """
        Initialize query metadata.

        Args:
            query_path: The query path being executed
            filters: Filter parameters for the query
        """
        self.query_path = query_path
        self.filters = filters or {}
        self.execution_time: Optional[float] = None
        self.execution_started: Optional[datetime] = None
        self.execution_completed: Optional[datetime] = None
        self.record_count: Optional[int] = None
        self.query_source: Optional[str] = None
        self.optimizations: List[str] = []
        self.cache_hit: Optional[bool] = None

    def start_execution(self) -> None:
        """Mark the start of query execution."""
        self.execution_started = datetime.now()

    def complete_execution(self, record_count: int, source: str) -> None:
        """
        Mark the completion of query execution.

        Args:
            record_count: Number of records returned
            source: Source of the results (e.g., "cache", "graph", "relational")
        """
        self.execution_completed = datetime.now()
        if self.execution_started:
            delta = self.execution_completed - self.execution_started
            self.execution_time = delta.total_seconds()
        self.record_count = record_count
        self.query_source = source

    def add_optimization(self, optimization: str) -> None:
        """
        Add an optimization that was applied to the query.

        Args:
            optimization: Description of the optimization
        """
        self.optimizations.append(optimization)

    def set_cache_hit(self, is_hit: bool) -> None:
        """
        Set whether the query was served from cache.

        Args:
            is_hit: Whether the query was a cache hit
        """
        self.cache_hit = is_hit

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_path": self.query_path,
            "filters": self.filters,
            "execution_time": self.execution_time,
            "execution_started": (
                self.execution_started.isoformat() if self.execution_started else None
            ),
            "execution_completed": (
                self.execution_completed.isoformat()
                if self.execution_completed
                else None
            ),
            "record_count": self.record_count,
            "query_source": self.query_source,
            "optimizations": self.optimizations,
            "cache_hit": self.cache_hit,
        }


class EnhancedQueryExecutor(Generic[T, Q]):
    """
    Enhanced query executor with performance optimizations.

    This executor uses multiple strategies to optimize query performance,
    including caching, selective execution, and performance tracking.
    """

    def __init__(
        self,
        entity_type: Type[T],
        repository: Repository[T],
        performance_tracker: Optional[QueryPerformanceTracker] = None,
        cache: Optional[QueryResultCache] = None,
        optimizer: Optional[GraphQueryOptimizer] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced query executor.

        Args:
            entity_type: The type of entity this executor queries
            repository: Repository for data access
            performance_tracker: Optional performance tracker
            cache: Optional query cache
            optimizer: Optional query optimizer
            logger: Optional logger for diagnostic output
        """
        self.entity_type = entity_type
        self.repository = repository
        self.performance_tracker = performance_tracker or QueryPerformanceTracker()
        self.cache = cache or QueryResultCache()
        self.optimizer = optimizer or GraphQueryOptimizer()
        self.logger = logger or logging.getLogger(__name__)
        self.materialized_views: Dict[str, MaterializedQueryView] = {}

    def _generate_cache_key(self, query: Q) -> str:
        """
        Generate a cache key for a query.

        Args:
            query: The query specification

        Returns:
            A cache key string
        """
        # Convert query to a string representation
        query_dict = query.model_dump(exclude_unset=True)
        query_str = json.dumps(query_dict, sort_keys=True)

        # Generate a hash for the query string
        key = hashlib.md5(query_str.encode()).hexdigest()
        return f"{self.entity_type.__name__}:{key}"

    async def execute(self, query: Q) -> Tuple[QueryResult[T], QueryMetadata]:
        """
        Execute a query with optimizations and tracking.

        Args:
            query: The query specification

        Returns:
            A tuple of (query result, query metadata)
        """
        # Initialize query metadata
        metadata = QueryMetadata(
            query_path=self.entity_type.__name__, filters=query.filters
        )

        # Generate cache key
        cache_key = self._generate_cache_key(query)

        # Check for a materialized view first
        if cache_key in self.materialized_views:
            metadata.start_execution()
            results = await self.materialized_views[cache_key].get_results()
            metadata.add_optimization("materialized_view")
            metadata.complete_execution(
                record_count=len(results.items), source="materialized_view"
            )
            return results, metadata

        # Define the query function
        async def query_fn() -> QueryResult[T]:
            # Start timing execution
            metadata.start_execution()

            try:
                # First, try using the graph query path if appropriate
                if self._should_use_graph_query(query):
                    try:
                        result = await self._execute_graph_query(query)
                        metadata.add_optimization("graph_query")
                        metadata.complete_execution(
                            record_count=len(result.items), source="graph"
                        )
                        return result
                    except Exception as e:
                        # Log the error but fall back to repository query
                        self.logger.warning(
                            f"Graph query failed, falling back to repository: {e}"
                        )
                        metadata.add_optimization("graph_fallback")

                # Use repository if graph query isn't appropriate or failed
                result = await self._execute_repository_query(query)
                metadata.complete_execution(
                    record_count=len(result.items), source="repository"
                )
                return result

            except Exception as e:
                self.logger.error(f"Query execution error: {e}")
                # Complete metadata with failure information
                metadata.complete_execution(record_count=0, source="error")
                # Re-raise the exception
                raise

        # Use the cache with tracking
        async def tracked_query() -> QueryResult[T]:
            # Use the performance tracker
            return await self.performance_tracker.track_query(
                query_key=cache_key, callback=query_fn
            )

        # Try to get from cache or execute
        result = await self.cache.get_or_execute(
            cache_key=cache_key,
            query_fn=tracked_query,
            ttl_seconds=self._get_cache_ttl(query),
        )

        # Set cache hit status in metadata
        metadata.set_cache_hit(self.cache.hits > 0)

        return result, metadata

    def _should_use_graph_query(self, query: Q) -> bool:
        """
        Determine if a graph query should be used.

        Args:
            query: The query specification

        Returns:
            Whether to use a graph query
        """
        # Simple heuristic: use graph for complex filters
        if not query.filters:
            return False

        # Consider using graph if there are relationship filters
        # or multiple filter conditions
        return len(query.filters) >= 2

    def _get_cache_ttl(self, query: Q) -> int:
        """
        Determine an appropriate TTL for caching query results.

        Args:
            query: The query specification

        Returns:
            TTL in seconds
        """
        # Simple heuristic: more complex queries get longer TTL
        if not query.filters:
            return 60  # 1 minute for simple queries

        if len(query.filters) >= 3:
            return 600  # 10 minutes for complex queries

        return 300  # 5 minutes default

    async def _execute_repository_query(self, query: Q) -> QueryResult[T]:
        """
        Execute a query using the repository.

        Args:
            query: The query specification

        Returns:
            Query results
        """
        # Get items from the repository
        items = await self.repository.list(
            filters=query.filters,
            order_by=query.order_by,
            limit=query.limit,
            offset=query.offset,
        )

        # Get total count for pagination
        total_count = await self.repository.count(filters=query.filters)

        # Calculate pagination metadata
        page_size = query.limit
        page = None
        total_pages = None

        if page_size:
            page = (query.offset or 0) // page_size + 1
            total_pages = (total_count + page_size - 1) // page_size

        # Filter fields if needed
        if query.include or query.exclude:
            items = self._filter_entity_fields(items, query.include, query.exclude)

        return QueryResult(
            items=items,
            total_count=total_count,
            page_size=page_size,
            page=page,
            total_pages=total_pages,
        )

    async def _execute_graph_query(self, query: Q) -> QueryResult[T]:
        """
        Execute a query using the graph database.

        Args:
            query: The query specification

        Returns:
            Query results
        """
        try:
            # Convert filters to cypher WHERE clauses
            cypher_where = self._build_cypher_where_clauses(query.filters)

            # Build the cypher query
            node_label = self.entity_type.__name__
            cypher_query = f"""
            MATCH (n:{node_label})
            WHERE {cypher_where}
            RETURN n.id AS id
            """

            # Optimize the query if possible
            optimized_query = self.optimizer.optimize_query(cypher_query)

            # Execute the cypher query
            async with async_session() as session:
                result = await session.execute(
                    text(
                        f"""
                    SELECT * FROM cypher('graph', $$ {optimized_query} $$) AS (id TEXT)
                    """
                    )
                )

                # Get matching IDs
                entity_ids = [row.id for row in result.fetchall()]

                if not entity_ids:
                    return QueryResult(items=[], total_count=0)

                # Apply pagination
                total_count = len(entity_ids)
                offset = query.offset or 0

                if query.limit:
                    paginated_ids = entity_ids[offset : offset + query.limit]
                else:
                    paginated_ids = entity_ids[offset:]

                # Fetch full entities using the repository
                items = []
                for entity_id in paginated_ids:
                    entity = await self.repository.get(entity_id)
                    if entity:
                        items.append(entity)

                # Calculate pagination metadata
                page_size = query.limit
                page = None
                total_pages = None

                if page_size:
                    page = offset // page_size + 1
                    total_pages = (total_count + page_size - 1) // page_size

                # Filter fields if needed
                if query.include or query.exclude:
                    items = self._filter_entity_fields(
                        items, query.include, query.exclude
                    )

                return QueryResult(
                    items=items,
                    total_count=total_count,
                    page_size=page_size,
                    page=page,
                    total_pages=total_pages,
                )

        except SQLAlchemyError as e:
            self.logger.error(f"Error executing graph query: {e}")
            raise

    def _build_cypher_where_clauses(self, filters: Optional[Dict[str, Any]]) -> str:
        """
        Build cypher WHERE clauses from filters.

        Args:
            filters: Query filters

        Returns:
            Cypher WHERE clause string
        """
        if not filters:
            return "true"  # Default match everything

        where_clauses = []

        for field, value in filters.items():
            # Handle different filter formats
            if isinstance(value, dict) and "lookup" in value and "val" in value:
                lookup = value["lookup"]
                val = value["val"]
            else:
                lookup = "eq"
                val = value

            # Map lookups to cypher conditions
            if lookup == "eq":
                where_clauses.append(f"n.properties->'{field}' = '{val}'")
            elif lookup == "neq":
                where_clauses.append(f"n.properties->'{field}' <> '{val}'")
            elif lookup == "gt":
                where_clauses.append(f"n.properties->'{field}' > '{val}'")
            elif lookup == "gte":
                where_clauses.append(f"n.properties->'{field}' >= '{val}'")
            elif lookup == "lt":
                where_clauses.append(f"n.properties->'{field}' < '{val}'")
            elif lookup == "lte":
                where_clauses.append(f"n.properties->'{field}' <= '{val}'")
            elif lookup == "contains":
                where_clauses.append(f"n.properties->'{field}' CONTAINS '{val}'")
            elif lookup == "starts_with":
                where_clauses.append(f"n.properties->'{field}' STARTS WITH '{val}'")
            elif lookup == "ends_with":
                where_clauses.append(f"n.properties->'{field}' ENDS WITH '{val}'")
            elif lookup == "in":
                # Handle list of values
                if isinstance(val, list):
                    val_list = "', '".join(str(v) for v in val)
                    where_clauses.append(f"n.properties->'{field}' IN ['{val_list}']")
                else:
                    where_clauses.append(f"n.properties->'{field}' IN ['{val}']")
            elif lookup == "is_null":
                where_clauses.append(f"n.properties->'{field}' IS NULL")
            elif lookup == "not_null":
                where_clauses.append(f"n.properties->'{field}' IS NOT NULL")
            else:
                # Default to equality
                where_clauses.append(f"n.properties->'{field}' = '{val}'")

        # Join all conditions with AND
        return " AND ".join(where_clauses)

    def _filter_entity_fields(
        self,
        items: List[T],
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> List[T]:
        """
        Filter fields from a list of entities.

        Args:
            items: List of entities to filter fields from
            include: Optional list of fields to include
            exclude: Optional list of fields to exclude

        Returns:
            Entities with filtered fields
        """
        if not (include or exclude):
            return items

        filtered_items = []
        for item in items:
            # Convert to dictionary
            item_dict = item.model_dump()

            # Apply include/exclude filters
            if include:
                item_dict = {k: v for k, v in item_dict.items() if k in include}
            elif exclude:
                item_dict = {k: v for k, v in item_dict.items() if k not in exclude}

            # Create new entity with filtered fields
            filtered_item = self.entity_type.model_validate(item_dict)
            filtered_items.append(filtered_item)

        return filtered_items

    def create_materialized_view(
        self, name: str, query: Q, refresh_interval: int = 3600
    ) -> MaterializedQueryView:
        """
        Create a materialized view for a frequently-used query.

        Args:
            name: Name for the materialized view
            query: Query specification
            refresh_interval: Seconds between refreshes

        Returns:
            The created materialized view
        """
        # Generate cache key from the query
        cache_key = self._generate_cache_key(query)

        # Define the query function
        async def query_fn() -> QueryResult[T]:
            # Execute the query directly (bypass cache)
            if self._should_use_graph_query(query):
                try:
                    return await self._execute_graph_query(query)
                except Exception:
                    pass

            return await self._execute_repository_query(query)

        # Create the materialized view
        view = MaterializedQueryView(
            query_fn=query_fn,
            name=name,
            refresh_interval=refresh_interval,
            logger=self.logger,
        )

        # Store in the views dictionary
        self.materialized_views[cache_key] = view

        # Start the refresh task
        asyncio.create_task(view.start_refresh_task())

        return view

    async def invalidate_cache(self, query: Optional[Q] = None) -> None:
        """
        Invalidate cache entries for queries.

        Args:
            query: Optional specific query to invalidate
        """
        if query:
            cache_key = self._generate_cache_key(query)
            self.cache.invalidate(cache_key)
        else:
            self.cache.invalidate()


class GraphPathQuery:
    """
    Query handler for graph path-based queries.

    This class executes queries based on defined graph paths,
    which can represent complex traversals through the domain model.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the path query handler.

        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self.performance_tracker = QueryPerformanceTracker(logger=logger)
        self.cache = QueryResultCache(logger=logger)

    async def execute_path_query(
        self,
        path: str,
        params: Dict[str, Any] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> Tuple[List[str], QueryMetadata]:
        """
        Execute a query using a defined path and parameters.

        Args:
            path: The cypher path expression
            params: Parameters for the query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (matching IDs, query metadata)
        """
        # Initialize query metadata
        metadata = QueryMetadata(query_path=path, filters=params)

        # Generate cache key
        params_str = json.dumps(params or {}, sort_keys=True)
        cache_key = f"path:{path}:{params_str}:{limit}:{offset}"

        # Define the query function
        async def query_fn() -> List[str]:
            metadata.start_execution()

            try:
                # Build the cypher query
                cypher_query = self._build_path_query(path, params, limit, offset)

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

                    return entity_ids

            except Exception as e:
                self.logger.error(f"Path query execution error: {e}")
                metadata.complete_execution(record_count=0, source="error")
                raise

        # Use tracking and caching
        async def tracked_query() -> List[str]:
            return await self.performance_tracker.track_query(
                query_key=cache_key, callback=query_fn
            )

        # Try to get from cache or execute
        result = await self.cache.get_or_execute(
            cache_key=cache_key, query_fn=tracked_query
        )

        # Set cache hit status in metadata
        metadata.set_cache_hit(self.cache.hits > 0)

        return result, metadata

    def _build_path_query(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> str:
        """
        Build a cypher query from a path and parameters.

        Args:
            path: The cypher path expression
            params: Parameters for the query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Cypher query string
        """
        # Extract source node from path (assumes format like '(s:Type)-[:REL]->')
        source_match = path.split(")-")[0] + ")"

        # Build WHERE clauses from params
        where_clauses = []
        if params:
            for key, value in params.items():
                # Determine target based on parameter key
                # For simple parameters, apply to source node
                target = "s"
                property_path = key

                # For path-based parameters (e.g., user.name),
                # target the appropriate node in the path
                if "." in key:
                    parts = key.split(".")
                    if len(parts) == 2:
                        # Simple node.property format
                        target = parts[0]
                        property_path = parts[1]

                # Format the value based on its type
                if isinstance(value, str):
                    formatted_value = f"'{value}'"
                elif value is None:
                    formatted_value = "NULL"
                else:
                    formatted_value = str(value)

                where_clauses.append(f"{target}.{property_path} = {formatted_value}")

        # Construct the full query
        query = f"MATCH {path}"

        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"

        query += " RETURN s.id AS id"

        # Add ordering, if applicable
        # This is simplified; in a real implementation, you might want to
        # parameterize the order by clause

        # Add pagination
        if offset:
            query += f" SKIP {offset}"
        if limit:
            query += f" LIMIT {limit}"

        return query
