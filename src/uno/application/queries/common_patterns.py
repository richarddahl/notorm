"""
Common query patterns with optimized implementations.

This module provides pre-built, optimized implementations of common database
query patterns, automatically selecting the most efficient execution strategy
based on query characteristics and database capabilities.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    TypeVar,
    Generic,
    Type,
    cast,
    Callable,
)
import logging
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import (
    select,
    insert,
    update,
    delete,
    join,
    outerjoin,
    func,
    text,
    Table,
    Column,
    and_,
    or_,
    not_,
    exists,
    case,
)
from sqlalchemy.ext.asyncio import AsyncSession

# Fix for sqlalchemy.sql imports
from sqlalchemy.sql import Select, Insert, Update, Delete, Join, Alias
from sqlalchemy.sql.expression import Exists
from sqlalchemy.sql.expression import ColumnElement, BinaryExpression, TextClause

# Temporarily comment out core caching imports while we fix circular dependencies
# from uno.core.caching import (
#     generate_cache_key,
#     get_cache_manager,
#     query_cached,
# )
from uno.database.enhanced_session import enhanced_async_session
from uno.database.pooled_session import pooled_async_session
from uno.domain.base.model import ModelBase
from uno.queries.optimized_queries import OptimizedModelQuery, QueryHints


T = TypeVar("T", bound=ModelBase)


class QueryPattern(Enum):
    """
    Common query patterns that can be optimized.

    These patterns represent frequently used query types that can benefit
    from specialized optimizations.
    """

    # Basic CRUD operations
    FIND_BY_ID = "find_by_id"
    FIND_ALL = "find_all"
    FIND_BY_FIELD = "find_by_field"
    FIND_BY_FIELDS = "find_by_fields"
    COUNT = "count"

    # Relationship queries
    FIND_RELATED = "find_related"
    FIND_RELATED_MANY = "find_related_many"

    # Advanced queries
    PAGINATED = "paginated"
    FILTERED = "filtered"
    SORTED = "sorted"
    FULL_TEXT_SEARCH = "full_text_search"
    COMPLEX_FILTER = "complex_filter"

    # Aggregation queries
    COUNT_BY_FIELD = "count_by_field"
    SUM_BY_FIELD = "sum_by_field"
    AVG_BY_FIELD = "avg_by_field"
    MIN_BY_FIELD = "min_by_field"
    MAX_BY_FIELD = "max_by_field"
    GROUP_BY = "group_by"

    # Batch operations
    BATCH_INSERT = "batch_insert"
    BATCH_UPDATE = "batch_update"
    BATCH_DELETE = "batch_delete"
    BATCH_UPSERT = "batch_upsert"

    # JSON queries
    JSON_FIELD_QUERY = "json_field_query"
    JSON_FIELD_UPDATE = "json_field_update"

    # Special queries
    WINDOW_FUNCTION = "window_function"
    RECURSIVE_CTE = "recursive_cte"
    LATERAL_JOIN = "lateral_join"


@dataclass
class QueryMetrics:
    """
    Metrics for query execution performance.

    This class tracks query execution metrics to identify optimization
    opportunities and guide query planning decisions.
    """

    total_time: float = 0.0
    execution_count: int = 0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    total_rows: int = 0
    avg_rows: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def record_execution(
        self, time_ms: float, row_count: int, from_cache: bool = False
    ) -> None:
        """
        Record a query execution.

        Args:
            time_ms: Execution time in milliseconds
            row_count: Number of rows returned
            from_cache: Whether the result was from cache
        """
        self.total_time += time_ms
        self.execution_count += 1
        self.avg_time = self.total_time / self.execution_count
        self.min_time = min(self.min_time, time_ms)
        self.max_time = max(self.max_time, time_ms)
        self.total_rows += row_count
        self.avg_rows = self.total_rows / self.execution_count

        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1


class QueryPlan:
    """
    Query execution plan with optimization strategies.

    This class analyzes query characteristics and selects the most
    efficient execution strategy.
    """

    def __init__(
        self,
        pattern: QueryPattern,
        model_class: Type[T],
        metrics: Optional[QueryMetrics] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the query plan.

        Args:
            pattern: Query pattern
            model_class: ModelBase class
            metrics: Optional metrics for tracking
            logger: Optional logger
        """
        self.pattern = pattern
        self.model_class = model_class
        self.metrics = metrics or QueryMetrics()
        self.logger = logger or logging.getLogger(__name__)

        # Get table info
        self.table = model_class.__table__
        self.table_name = self.table.name
        self.primary_key = next(iter(self.table.primary_key.columns))
        self.columns = self.table.columns

        # Catalog of available indexes
        self.available_indexes = self._get_available_indexes()

        # Optimal hint settings for this pattern
        self.optimal_hints = self._get_optimal_hints()

    def _get_available_indexes(self) -> Dict[str, list[str]]:
        """
        Get available indexes for the model's table.

        Returns:
            Dictionary mapping index names to column names
        """
        # This would typically query the database to get index information
        # For now, we'll return a placeholder
        return {}

    def _get_optimal_hints(self) -> QueryHints:
        """
        Get optimal query hints for the pattern.

        Returns:
            QueryHints instance with optimal settings
        """
        # Optimize based on pattern
        if self.pattern in (QueryPattern.FIND_BY_ID, QueryPattern.FIND_BY_FIELD):
            # Point lookups benefit from index scans
            return QueryHints(
                enable_seqscan=False,
                parallel_workers=1,  # No parallelism needed for point lookups
            )

        elif self.pattern == QueryPattern.FIND_ALL:
            # Full table scans benefit from parallelism and seq scans
            return QueryHints(
                enable_seqscan=True,
                parallel_workers=4,
                work_mem="32MB",
            )

        elif self.pattern == QueryPattern.PAGINATED:
            # Pagination benefits from optimized sorts
            return QueryHints(
                work_mem="64MB",  # More memory for sorting
                enable_seqscan=False,
                parallel_workers=2,
            )

        elif self.pattern in (
            QueryPattern.FULL_TEXT_SEARCH,
            QueryPattern.COMPLEX_FILTER,
        ):
            # Complex queries benefit from more resources
            return QueryHints(
                work_mem="128MB",
                parallel_workers=4,
                use_nestloop=False,
                use_hashjoin=True,
            )

        elif self.pattern in (QueryPattern.GROUP_BY, QueryPattern.COUNT_BY_FIELD):
            # Aggregations benefit from hash joins and more memory
            return QueryHints(
                work_mem="64MB",
                use_hashjoin=True,
                parallel_workers=2,
            )

        elif self.pattern in (QueryPattern.BATCH_INSERT, QueryPattern.BATCH_UPDATE):
            # Batch operations benefit from more workers
            return QueryHints(
                parallel_workers=4,
                work_mem="64MB",
            )

        # Default hints for other patterns
        return QueryHints()

    def should_use_cache(self, params: Dict[str, Any]) -> bool:
        """
        Determine if a query should use caching.

        Args:
            params: Query parameters

        Returns:
            True if caching should be used
        """
        # Don't cache write operations
        if self.pattern in (
            QueryPattern.BATCH_INSERT,
            QueryPattern.BATCH_UPDATE,
            QueryPattern.BATCH_DELETE,
            QueryPattern.BATCH_UPSERT,
        ):
            return False

        # Don't cache large result sets
        if self.pattern == QueryPattern.FIND_ALL and not params.get("limit"):
            return False

        # Cache point lookups and small result sets
        if self.pattern in (
            QueryPattern.FIND_BY_ID,
            QueryPattern.FIND_BY_FIELD,
            QueryPattern.COUNT,
        ):
            return True

        # Cache paginated queries for better UX
        if self.pattern == QueryPattern.PAGINATED:
            return True

        # Default to caching for read operations
        return True

    def select_join_strategy(self, params: Dict[str, Any]) -> str:
        """
        Select the optimal join strategy for a query.

        Args:
            params: Query parameters

        Returns:
            Join strategy: 'nested_loop', 'hash', or 'merge'
        """
        # Simple point lookups and small result sets benefit from nested loops
        if self.pattern in (
            QueryPattern.FIND_BY_ID,
            QueryPattern.FIND_BY_FIELD,
        ):
            return "nested_loop"

        # Large joins benefit from hash joins
        if self.pattern in (
            QueryPattern.FIND_RELATED_MANY,
            QueryPattern.COMPLEX_FILTER,
        ):
            return "hash"

        # Sorted data benefits from merge joins
        if self.pattern == QueryPattern.SORTED:
            return "merge"

        # Default to hash join for most cases
        return "hash"

    def should_use_prepared_statement(self, params: Dict[str, Any]) -> bool:
        """
        Determine if a query should use prepared statements.

        Args:
            params: Query parameters

        Returns:
            True if prepared statements should be used
        """
        # Prepared statements are beneficial for repeated queries
        # with different parameters
        if self.pattern in (
            QueryPattern.FIND_BY_ID,
            QueryPattern.FIND_BY_FIELD,
        ):
            return True

        # Prepared statements are not beneficial for complex or dynamic queries
        if self.pattern in (
            QueryPattern.COMPLEX_FILTER,
            QueryPattern.FULL_TEXT_SEARCH,
        ):
            return False

        # Default to using prepared statements
        return True

    def get_optimal_fetch_size(self, params: Dict[str, Any]) -> int:
        """
        Get the optimal fetch size for a query.

        Args:
            params: Query parameters

        Returns:
            Optimal fetch size
        """
        # Use small fetch size for point lookups
        if self.pattern in (
            QueryPattern.FIND_BY_ID,
            QueryPattern.FIND_BY_FIELD,
        ):
            return 1

        # Use medium fetch size for paginated queries
        if self.pattern == QueryPattern.PAGINATED:
            page_size = params.get("limit", 25)
            return page_size

        # Use large fetch size for batch operations
        if self.pattern in (
            QueryPattern.BATCH_INSERT,
            QueryPattern.BATCH_UPDATE,
        ):
            return 1000

        # Default fetch size
        return 100


class CommonQueryPatterns:
    """
    Implementation of common query patterns with optimizations.

    This class provides pre-built, optimized implementations of common
    database query patterns.
    """

    def __init__(
        self,
        model_class: Type[T],
        session: AsyncSession | None = None,
        use_cache: bool = True,
        cache_ttl: Optional[float] = 60.0,
        collect_metrics: bool = False,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the common query patterns.

        Args:
            model_class: ModelBase class
            session: Optional session to use
            use_cache: Whether to cache query results
            cache_ttl: Time-to-live for cache entries
            collect_metrics: Whether to collect query metrics
            logger: Optional logger
        """
        self.model_class = model_class
        self.session = session
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.collect_metrics = collect_metrics
        self.logger = logger or logging.getLogger(__name__)

        # Create optimized query builder
        self.query_builder = OptimizedModelQuery(
            model_class=model_class,
            session=session,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
            logger=logger,
        )

        # Metrics for each pattern
        self.metrics: Dict[QueryPattern, QueryMetrics] = {
            pattern: QueryMetrics() for pattern in QueryPattern
        }

    async def find_by_id(
        self,
        id_value: Any,
        load_relations: Optional[Union[bool, list[str]]] = None,
    ) -> Optional[T]:
        """
        Find a model by ID.

        Args:
            id_value: ID value
            load_relations: Which relationships to load
                - None/False: Load no relationships
                - True: Load all relationships
                - list[str]: Load only specified relationships

        Returns:
            ModelBase instance or None
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.FIND_BY_ID,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.FIND_BY_ID],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Build query with optimal hints
        query = self.query_builder.build_select(
            where=plan.primary_key == id_value,
            hints=plan.optimal_hints,
        )

        # Get result from cache or database
        use_cache = plan.should_use_cache({"id": id_value})

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Check if we got a result
            if result and len(result) > 0:
                model = result[0]
            else:
                model = None

            # If relations are requested and model was found, load them
            if model and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships
                loader = RelationshipLoader(self.model_class)
                model = await loader.load_relationships(
                    model, load_relations, self.session
                )
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Check if we got a result
            if result.rowcount > 0:
                # Get the model
                model = result.scalars().first()

                # If relations are requested and model was found, load them
                if model and load_relations:
                    # Import on demand to avoid circular imports
                    from uno.database.relationship_loader import RelationshipLoader

                    # Create loader and load relationships
                    loader = RelationshipLoader(self.model_class)
                    model = await loader.load_relationships(
                        model, load_relations, self.session
                    )
            else:
                model = None

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=1 if model else 0,
                from_cache=use_cache,
            )

        return model

    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[list[Any]] = None,
        load_relations: Optional[Union[bool, list[str]]] = None,
    ) -> list[T]:
        """
        Find all models.

        Args:
            limit: Maximum number of models to return
            offset: Number of models to skip
            order_by: Order by specification
            load_relations: Which relationships to load
                - None/False: Load no relationships
                - True: Load all relationships
                - list[str]: Load only specified relationships

        Returns:
            List of model instances
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.FIND_ALL,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.FIND_ALL],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Build query with optimal hints
        query = self.query_builder.build_select(
            order_by=order_by,
            limit=limit,
            offset=offset,
            hints=plan.optimal_hints,
        )

        # Get result from cache or database
        params = {
            "limit": limit,
            "offset": offset,
            "order_by": order_by,
        }

        use_cache = plan.should_use_cache(params)

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = len(result) if result else 0

            # If relations are requested and models were found, load them
            if result and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                result = await loader.load_relationships_batch(
                    result, load_relations, self.session
                )

            models = result
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = result.rowcount

            # Get the models
            models = list(result.scalars().all())

            # If relations are requested and models were found, load them
            if models and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                models = await loader.load_relationships_batch(
                    models, load_relations, self.session
                )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=use_cache,
            )

        return models

    async def find_by_field(
        self,
        field_name: str,
        field_value: Any,
        load_relations: Optional[Union[bool, list[str]]] = None,
    ) -> list[T]:
        """
        Find models by field value.

        Args:
            field_name: Field name
            field_value: Field value
            load_relations: Which relationships to load
                - None/False: Load no relationships
                - True: Load all relationships
                - list[str]: Load only specified relationships

        Returns:
            List of model instances
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.FIND_BY_FIELD,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.FIND_BY_FIELD],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Check if field exists
        if field_name not in plan.columns:
            raise ValueError(
                f"Field {field_name} does not exist on {self.model_class.__name__}"
            )

        # Get field column
        field_column = plan.columns[field_name]

        # Build query with optimal hints
        query = self.query_builder.build_select(
            where=field_column == field_value,
            hints=plan.optimal_hints,
        )

        # Get result from cache or database
        params = {
            "field_name": field_name,
            "field_value": field_value,
        }

        use_cache = plan.should_use_cache(params)

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = len(result) if result else 0

            # If relations are requested and models were found, load them
            if result and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                result = await loader.load_relationships_batch(
                    result, load_relations, self.session
                )

            models = result
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = result.rowcount

            # Get the models
            models = list(result.scalars().all())

            # If relations are requested and models were found, load them
            if models and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                models = await loader.load_relationships_batch(
                    models, load_relations, self.session
                )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=use_cache,
            )

        return models

    async def find_by_fields(
        self,
        field_values: Dict[str, Any],
        match_all: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[list[Any]] = None,
        load_relations: Optional[Union[bool, list[str]]] = None,
    ) -> list[T]:
        """
        Find models matching multiple field values.

        Args:
            field_values: Field name to value mapping
            match_all: Whether all fields must match (AND) or any field (OR)
            limit: Maximum number of models to return
            offset: Number of models to skip
            order_by: Order by specification
            load_relations: Which relationships to load
                - None/False: Load no relationships
                - True: Load all relationships
                - list[str]: Load only specified relationships

        Returns:
            List of model instances
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.FIND_BY_FIELDS,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.FIND_BY_FIELDS],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Build conditions
        conditions = []

        for field_name, field_value in field_values.items():
            # Check if field exists
            if field_name not in plan.columns:
                raise ValueError(
                    f"Field {field_name} does not exist on {self.model_class.__name__}"
                )

            # Get field column
            field_column = plan.columns[field_name]

            # Add condition
            conditions.append(field_column == field_value)

        # Combine conditions
        if match_all:
            # AND conditions
            where = and_(*conditions)
        else:
            # OR conditions
            where = or_(*conditions)

        # Build query with optimal hints
        query = self.query_builder.build_select(
            where=where,
            order_by=order_by,
            limit=limit,
            offset=offset,
            hints=plan.optimal_hints,
        )

        # Get result from cache or database
        params = {
            "field_values": field_values,
            "match_all": match_all,
            "limit": limit,
            "offset": offset,
            "order_by": order_by,
        }

        use_cache = plan.should_use_cache(params)

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = len(result) if result else 0

            # If relations are requested and models were found, load them
            if result and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                result = await loader.load_relationships_batch(
                    result, load_relations, self.session
                )

            models = result
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = result.rowcount

            # Get the models
            models = list(result.scalars().all())

            # If relations are requested and models were found, load them
            if models and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                models = await loader.load_relationships_batch(
                    models, load_relations, self.session
                )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=use_cache,
            )

        return models

    async def count(
        self,
        where: Optional[Union[BinaryExpression, list[BinaryExpression]]] = None,
    ) -> int:
        """
        Count models matching criteria.

        Args:
            where: WHERE conditions

        Returns:
            Number of matching models
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.COUNT,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.COUNT],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Build query with optimal hints
        query = select(func.count()).select_from(self.model_class.__table__)

        # Add WHERE conditions
        if where is not None:
            if isinstance(where, list):
                query = query.where(and_(*where))
            else:
                query = query.where(where)

        # Add hints
        query = query.prefix_with(plan.optimal_hints.to_sql())

        # Get result from cache or database
        params = {
            "where": str(where) if where else None,
        }

        use_cache = plan.should_use_cache(params)

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Get count
            count = result[0][0] if result and len(result) > 0 else 0
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Get count
            count = result.scalar() or 0

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=1,  # Count queries only return one row
                from_cache=use_cache,
            )

        return count

    async def count_by_field(
        self,
        field_name: str,
        distinct: bool = True,
    ) -> Dict[Any, int]:
        """
        Count models grouped by a field.

        Args:
            field_name: Field to group by
            distinct: Count distinct values

        Returns:
            Dictionary mapping field values to counts
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.COUNT_BY_FIELD,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.COUNT_BY_FIELD],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Check if field exists
        if field_name not in plan.columns:
            raise ValueError(
                f"Field {field_name} does not exist on {self.model_class.__name__}"
            )

        # Get field column
        field_column = plan.columns[field_name]

        # Build query with optimal hints
        if distinct:
            query = select(
                field_column,
                func.count(func.distinct(plan.primary_key)),
            ).group_by(field_column)
        else:
            query = select(
                field_column,
                func.count(plan.primary_key),
            ).group_by(field_column)

        # Add hints
        query = query.prefix_with(plan.optimal_hints.to_sql())

        # Get result from cache or database
        params = {
            "field_name": field_name,
            "distinct": distinct,
        }

        use_cache = plan.should_use_cache(params)

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = len(result) if result else 0

            # Convert to dictionary
            counts = {row[0]: row[1] for row in result}
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = result.rowcount

            # Convert to dictionary
            counts = {row[0]: row[1] for row in result}

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=use_cache,
            )

        return counts

    async def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get query metrics.

        Returns:
            Dictionary of metrics by pattern
        """
        if not self.collect_metrics:
            return {"error": "Metrics collection is disabled"}

        metrics = {}

        for pattern, pattern_metrics in self.metrics.items():
            # Skip patterns with no executions
            if pattern_metrics.execution_count == 0:
                continue

            metrics[pattern.value] = {
                "execution_count": pattern_metrics.execution_count,
                "avg_time_ms": pattern_metrics.avg_time,
                "min_time_ms": (
                    pattern_metrics.min_time
                    if pattern_metrics.min_time != float("inf")
                    else 0
                ),
                "max_time_ms": pattern_metrics.max_time,
                "total_rows": pattern_metrics.total_rows,
                "avg_rows": pattern_metrics.avg_rows,
                "cache_hits": pattern_metrics.cache_hits,
                "cache_misses": pattern_metrics.cache_misses,
                "cache_hit_rate": (
                    pattern_metrics.cache_hits / pattern_metrics.execution_count
                    if pattern_metrics.execution_count > 0
                    else 0
                ),
            }

        return metrics

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 25,
        where: Optional[Union[BinaryExpression, list[BinaryExpression]]] = None,
        order_by: Optional[list[Any]] = None,
        load_relations: Optional[Union[bool, list[str]]] = None,
    ) -> Tuple[list[T], int, int]:
        """
        Paginate models.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            where: WHERE conditions
            order_by: Order by specification
            load_relations: Which relationships to load
                - None/False: Load no relationships
                - True: Load all relationships
                - list[str]: Load only specified relationships

        Returns:
            Tuple of (models, total_count, total_pages)
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.PAGINATED,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.PAGINATED],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total_count = await self.count(where=where)

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        # Build query with optimal hints
        query = self.query_builder.build_select(
            where=where,
            order_by=order_by,
            limit=page_size,
            offset=offset,
            hints=plan.optimal_hints,
        )

        # Get result from cache or database
        params = {
            "page": page,
            "page_size": page_size,
            "where": str(where) if where else None,
            "order_by": str(order_by) if order_by else None,
        }

        use_cache = plan.should_use_cache(params)

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = len(result) if result else 0

            # If relations are requested and models were found, load them
            if result and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                result = await loader.load_relationships_batch(
                    result, load_relations, self.session
                )

            models = result
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = result.rowcount

            # Get the models
            models = list(result.scalars().all())

            # If relations are requested and models were found, load them
            if models and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                models = await loader.load_relationships_batch(
                    models, load_relations, self.session
                )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=use_cache,
            )

        return models, total_count, total_pages

    async def fts_search(
        self,
        search_text: str,
        search_fields: list[str],
        limit: Optional[int] = 25,
        offset: Optional[int] = None,
        order_by: Optional[list[Any]] = None,
        load_relations: Optional[Union[bool, list[str]]] = None,
    ) -> list[T]:
        """
        Perform a full-text search.

        Args:
            search_text: Text to search for
            search_fields: Fields to search in
            limit: Maximum number of models to return
            offset: Number of models to skip
            order_by: Order by specification
            load_relations: Which relationships to load
                - None/False: Load no relationships
                - True: Load all relationships
                - list[str]: Load only specified relationships

        Returns:
            List of matching models
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.FULL_TEXT_SEARCH,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.FULL_TEXT_SEARCH],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Process search text
        # Convert to tsquery format
        search_text = search_text.replace("'", "''")
        search_tokens = search_text.split()
        tsquery = " & ".join(token + ":*" for token in search_tokens)

        # Build conditions for each field
        conditions = []

        for field_name in search_fields:
            # Check if field exists
            if field_name not in plan.columns:
                raise ValueError(
                    f"Field {field_name} does not exist on {self.model_class.__name__}"
                )

            # Get field column
            field_column = plan.columns[field_name]

            # Add condition using to_tsvector for full-text search
            tscolumn = text(f"to_tsvector('english', {field_name})")
            condition = text(f"{tscolumn} @@ to_tsquery('english', '{tsquery}')")
            conditions.append(condition)

        # Combine with OR
        where = or_(*conditions)

        # Build query with optimal hints
        query = self.query_builder.build_select(
            where=where,
            order_by=order_by,
            limit=limit,
            offset=offset,
            hints=plan.optimal_hints,
        )

        # Get result from cache or database
        params = {
            "search_text": search_text,
            "search_fields": search_fields,
            "limit": limit,
            "offset": offset,
            "order_by": order_by,
        }

        use_cache = plan.should_use_cache(params)

        if use_cache:
            # Use cache
            result = await self.query_builder.execute(
                query=query,
                use_cache=True,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = len(result) if result else 0

            # If relations are requested and models were found, load them
            if result and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                result = await loader.load_relationships_batch(
                    result, load_relations, self.session
                )

            models = result
        else:
            # Execute directly
            result = await self.query_builder.execute(
                query=query,
                use_cache=False,
            )

            # Store result count for metrics
            if self.collect_metrics:
                row_count = result.rowcount

            # Get the models
            models = list(result.scalars().all())

            # If relations are requested and models were found, load them
            if models and load_relations:
                # Import on demand to avoid circular imports
                from uno.database.relationship_loader import RelationshipLoader

                # Create loader and load relationships in batch
                loader = RelationshipLoader(self.model_class)
                models = await loader.load_relationships_batch(
                    models, load_relations, self.session
                )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=use_cache,
            )

        return models

    async def batch_update(
        self,
        id_values: list[Any],
        field_values: Dict[str, Any],
        return_models: bool = False,
    ) -> Union[int, list[T]]:
        """
        Update multiple models by ID.

        Args:
            id_values: IDs of models to update
            field_values: Field values to update
            return_models: Whether to return updated models

        Returns:
            Number of updated models or updated models
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.BATCH_UPDATE,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.BATCH_UPDATE],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Skip if no IDs
        if not id_values:
            return [] if return_models else 0

        # Build query
        where = plan.primary_key.in_(id_values)

        # Execute update
        result = await self.query_builder.update(
            values=field_values,
            where=where,
            return_models=return_models,
        )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Get row count
            if return_models:
                row_count = len(result)
            else:
                row_count = result

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=False,  # Updates are never cached
            )

        return result

    async def batch_delete(
        self,
        id_values: list[Any],
        return_models: bool = False,
    ) -> Union[int, list[T]]:
        """
        Delete multiple models by ID.

        Args:
            id_values: IDs of models to delete
            return_models: Whether to return deleted models

        Returns:
            Number of deleted models or deleted models
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.BATCH_DELETE,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.BATCH_DELETE],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Skip if no IDs
        if not id_values:
            return [] if return_models else 0

        # Build query
        where = plan.primary_key.in_(id_values)

        # Execute delete
        result = await self.query_builder.delete(
            where=where,
            return_models=return_models,
        )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Get row count
            if return_models:
                row_count = len(result)
            else:
                row_count = result

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=False,  # Deletes are never cached
            )

        return result

    async def batch_upsert(
        self,
        records: list[dict[str, Any]],
        constraint_columns: list[str],
        update_columns: list[str] | None = None,
        return_models: bool = False,
    ) -> Union[int, list[T]]:
        """
        Upsert multiple models.

        Args:
            records: Records to upsert
            constraint_columns: Columns for the constraint
            update_columns: Columns to update on conflict
            return_models: Whether to return upserted models

        Returns:
            Number of upserted models or upserted models
        """
        # Create query plan
        plan = QueryPlan(
            pattern=QueryPattern.BATCH_UPSERT,
            model_class=self.model_class,
            metrics=self.metrics[QueryPattern.BATCH_UPSERT],
            logger=self.logger,
        )

        # Start timing
        start_time = time.time()

        # Skip if no records
        if not records:
            return [] if return_models else 0

        # Execute upsert
        result = await self.query_builder.bulk_upsert(
            values=records,
            constraint_columns=constraint_columns,
            update_columns=update_columns,
            return_models=return_models,
        )

        # Record metrics if enabled
        if self.collect_metrics:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Get row count
            if return_models:
                row_count = len(result)
            else:
                row_count = result

            # Record execution
            plan.metrics.record_execution(
                time_ms=execution_time,
                row_count=row_count,
                from_cache=False,  # Upserts are never cached
            )

        return result
