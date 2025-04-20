"""
Optimized query builders for common query patterns.

This module provides utilities for building optimized queries for common
database operations, taking advantage of PostgreSQL-specific features.
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
)
import asyncio
import logging
import json
from dataclasses import dataclass, field

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

# Temporarily comment out caching imports while we fix circular dependencies
# from uno.core.caching import (
#     generate_cache_key,
#     get_cache_manager,
#     query_cached,
# )
from uno.database.enhanced_session import enhanced_async_session
from uno.database.pooled_session import pooled_async_session
from uno.database.streaming import stream_query, StreamingMode
from uno.domain.base.model import ModelBase


T = TypeVar("T", bound=ModelBase)


@dataclass
class QueryHints:
    """
    Hints for query optimization.

    Attributes:
        use_index: Name of index to use
        parallel_workers: Number of parallel workers
        enable_seqscan: Whether to enable sequential scan
        work_mem: Memory to use for the query (e.g., '100MB')
        use_nestloop: Whether to use nested loop joins
        use_hashjoin: Whether to use hash joins
        use_mergejoin: Whether to use merge joins
        custom_hints: Additional custom hints
    """

    use_index: str | None = None
    parallel_workers: Optional[int] = None
    enable_seqscan: Optional[bool] = None
    work_mem: str | None = None
    use_nestloop: Optional[bool] = None
    use_hashjoin: Optional[bool] = None
    use_mergejoin: Optional[bool] = None
    custom_hints: Dict[str, Any] = field(default_factory=dict)

    def to_sql(self) -> str:
        """
        Convert hints to SQL comment.

        Returns:
            SQL comment with hints
        """
        hints = []

        if self.use_index:
            hints.append(f"IndexScan({self.use_index})")

        if self.parallel_workers is not None:
            hints.append(f"SET parallel_workers = {self.parallel_workers}")

        if self.enable_seqscan is not None:
            hints.append(f"SET enable_seqscan = {str(self.enable_seqscan).lower()}")

        if self.work_mem:
            hints.append(f"SET work_mem = '{self.work_mem}'")

        if self.use_nestloop is not None:
            hints.append(f"SET enable_nestloop = {str(self.use_nestloop).lower()}")

        if self.use_hashjoin is not None:
            hints.append(f"SET enable_hashjoin = {str(self.use_hashjoin).lower()}")

        if self.use_mergejoin is not None:
            hints.append(f"SET enable_mergejoin = {str(self.use_mergejoin).lower()}")

        # Add custom hints
        for key, value in self.custom_hints.items():
            if isinstance(value, bool):
                hints.append(f"SET {key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                hints.append(f"SET {key} = {value}")
            else:
                hints.append(f"SET {key} = '{value}'")

        # Join hints
        if hints:
            return "/*+ " + ", ".join(hints) + " */"

        return ""


class OptimizedQuery:
    """
    Base class for optimized queries.

    This class provides utilities for building and executing optimized queries
    with caching, batching, and streaming support.
    """

    def __init__(
        self,
        session: AsyncSession | None = None,
        use_cache: bool = False,
        cache_ttl: Optional[float] = 60.0,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the optimized query.

        Args:
            session: Optional session to use
            use_cache: Whether to cache query results
            cache_ttl: Time-to-live for cache entries
            logger: Optional logger
        """
        self.session = session
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.logger = logger or logging.getLogger(__name__)

        # Query tracking
        self._query_count = 0
        self._query_times: list[float] = []

    async def execute(
        self,
        query: Any,
        params: Optional[Dict[str, Any]] = None,
        use_cache: Optional[bool] = None,
        stream: bool = False,
        chunks: bool = False,
        chunk_size: int = 1000,
        transform_fn: Optional[Any] = None,
    ) -> Any:
        """
        Execute a query.

        Args:
            query: Query to execute
            params: Parameters for the query
            use_cache: Whether to cache query results
            stream: Whether to stream results
            chunks: Whether to stream results in chunks
            chunk_size: Size of chunks to stream
            transform_fn: Function to transform results

        Returns:
            Query results
        """
        # Temporarily disable caching while we fix circular dependencies
        should_cache = False

        # Handle streaming
        if stream or chunks:
            # Create streaming mode
            mode = StreamingMode.CHUNK if chunks else StreamingMode.CURSOR

            # Stream query
            return await stream_query(
                query=query,
                mode=mode,
                chunk_size=chunk_size,
                transform_fn=transform_fn,
                session=self.session,
                use_pooled_session=True,
                logger=self.logger,
            )

        # Regular execution (caching disabled temporarily)
        return await self._execute_query(query, params)

    async def _execute_query(
        self,
        query: Any,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a query without caching.

        Args:
            query: Query to execute
            params: Parameters for the query

        Returns:
            Query results
        """
        # Use provided session or create a new one
        session_provided = self.session is not None

        if not session_provided:
            session_context = pooled_async_session()
            session = await session_context.__aenter__()
        else:
            session = self.session

        try:
            # Execute query
            if params:
                result = await session.execute(query, params)
            else:
                result = await session.execute(query)

            # Track query
            self._query_count += 1

            return result

        finally:
            # Close session if we created it
            if not session_provided:
                await session_context.__aexit__(None, None, None)

    async def _execute_cached(
        self,
        query: Any,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a query with caching.

        Args:
            query: Query to execute
            params: Parameters for the query

        Returns:
            Query results
        """
        # Temporarily disabled caching while we fix circular dependencies
        # Just use regular execution instead
        return await self._execute_query(query, params)


class OptimizedModelQuery(OptimizedQuery, Generic[T]):
    """
    Optimized query for ModelBase objects.

    This class provides optimized queries for common operations on ModelBase objects,
    with support for caching, batching, and streaming.
    """

    def __init__(
        self,
        model_class: Type[T],
        session: AsyncSession | None = None,
        use_cache: bool = False,
        cache_ttl: Optional[float] = 60.0,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the optimized model query.

        Args:
            model_class: ModelBase class
            session: Optional session to use
            use_cache: Whether to cache query results
            cache_ttl: Time-to-live for cache entries
            logger: Optional logger
        """
        super().__init__(
            session=session,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
            logger=logger,
        )

        self.model_class = model_class
        self.table = model_class.__table__

    def build_select(
        self,
        columns: Optional[list[Column]] = None,
        where: Optional[Union[BinaryExpression, list[BinaryExpression]]] = None,
        order_by: Optional[list[Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        joins: Optional[list[Tuple[Table, BinaryExpression]]] = None,
        group_by: Optional[list[Column]] = None,
        having: Optional[Union[BinaryExpression, list[BinaryExpression]]] = None,
        distinct: bool = False,
        hints: Optional[QueryHints] = None,
        for_update: bool = False,
        with_cte: Optional[Alias] = None,
    ) -> Select:
        """
        Build a SELECT query.

        Args:
            columns: Columns to select
            where: WHERE conditions
            order_by: ORDER BY columns
            limit: LIMIT value
            offset: OFFSET value
            joins: JOIN tables and conditions
            group_by: GROUP BY columns
            having: HAVING conditions
            distinct: Whether to use DISTINCT
            hints: Query hints
            for_update: Whether to use FOR UPDATE
            with_cte: Common Table Expression

        Returns:
            SELECT query
        """
        # Start with table
        query = select(columns or self.model_class)

        # Add FROM clause
        query = query.select_from(self.table)

        # Add hints if provided
        if hints:
            query = query.prefix_with(hints.to_sql())

        # Add CTE if provided
        if with_cte:
            query = query.cte(with_cte)

        # Add joins
        if joins:
            for join_table, join_condition in joins:
                query = query.join(join_table, join_condition)

        # Add WHERE conditions
        if where is not None:
            if isinstance(where, list):
                query = query.where(and_(*where))
            else:
                query = query.where(where)

        # Add GROUP BY
        if group_by:
            query = query.group_by(*group_by)

        # Add HAVING
        if having is not None:
            if isinstance(having, list):
                query = query.having(and_(*having))
            else:
                query = query.having(having)

        # Add ORDER BY
        if order_by:
            query = query.order_by(*order_by)

        # Add LIMIT and OFFSET
        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        # Add DISTINCT
        if distinct:
            query = query.distinct()

        # Add FOR UPDATE
        if for_update:
            query = query.with_for_update()

        return query

    def build_insert(
        self,
        values: Dict[str, Any],
        returning: Optional[list[Column]] = None,
    ) -> Insert:
        """
        Build an INSERT query.

        Args:
            values: Values to insert
            returning: Columns to return

        Returns:
            INSERT query
        """
        # Create insert
        query = insert(self.table).values(values)

        # Add RETURNING
        if returning:
            query = query.returning(*returning)

        return query

    def build_update(
        self,
        values: Dict[str, Any],
        where: Optional[Union[BinaryExpression, list[BinaryExpression]]] = None,
        returning: Optional[list[Column]] = None,
    ) -> Update:
        """
        Build an UPDATE query.

        Args:
            values: Values to update
            where: WHERE conditions
            returning: Columns to return

        Returns:
            UPDATE query
        """
        # Create update
        query = update(self.table).values(values)

        # Add WHERE conditions
        if where is not None:
            if isinstance(where, list):
                query = query.where(and_(*where))
            else:
                query = query.where(where)

        # Add RETURNING
        if returning:
            query = query.returning(*returning)

        return query

    def build_delete(
        self,
        where: Optional[Union[BinaryExpression, list[BinaryExpression]]] = None,
        returning: Optional[list[Column]] = None,
    ) -> Delete:
        """
        Build a DELETE query.

        Args:
            where: WHERE conditions
            returning: Columns to return

        Returns:
            DELETE query
        """
        # Create delete
        query = delete(self.table)

        # Add WHERE conditions
        if where is not None:
            if isinstance(where, list):
                query = query.where(and_(*where))
            else:
                query = query.where(where)

        # Add RETURNING
        if returning:
            query = query.returning(*returning)

        return query

    def build_upsert(
        self,
        values: Dict[str, Any],
        constraint_columns: list[str],
        update_columns: list[str] | None = None,
        returning: Optional[list[Column]] = None,
    ) -> TextClause:
        """
        Build an UPSERT query (INSERT ... ON CONFLICT).

        Args:
            values: Values to insert
            constraint_columns: Columns for the constraint
            update_columns: Columns to update on conflict
            returning: Columns to return

        Returns:
            UPSERT query
        """
        # If no update columns provided, update all except constraint columns
        if update_columns is None:
            update_columns = [
                col.name
                for col in self.table.columns
                if col.name not in constraint_columns
            ]

        # Build column list
        columns = ", ".join(values.keys())

        # Build values list
        placeholders = ", ".join(f":{key}" for key in values.keys())

        # Build constraint
        constraint = ", ".join(constraint_columns)

        # Build update list
        updates = ", ".join(f"{col} = EXCLUDED.{col}" for col in update_columns)

        # Build returning clause
        if returning:
            returning_clause = "RETURNING " + ", ".join(col.name for col in returning)
        else:
            returning_clause = ""

        # Build query
        query_text = f"""
        INSERT INTO {self.table.name} ({columns})
        VALUES ({placeholders})
        ON CONFLICT ({constraint})
        DO UPDATE SET {updates}
        {returning_clause}
        """

        return text(query_text)

    def build_bulk_insert(
        self,
        values: list[dict[str, Any]],
        returning: Optional[list[Column]] = None,
    ) -> Insert:
        """
        Build a bulk INSERT query.

        Args:
            values: List of values to insert
            returning: Columns to return

        Returns:
            Bulk INSERT query
        """
        # Create insert
        query = insert(self.table).values(values)

        # Add RETURNING
        if returning:
            query = query.returning(*returning)

        return query

    def build_bulk_upsert(
        self,
        values: list[dict[str, Any]],
        constraint_columns: list[str],
        update_columns: list[str] | None = None,
        returning: Optional[list[Column]] = None,
    ) -> Any:
        """
        Build a bulk UPSERT query.

        Args:
            values: List of values to insert
            constraint_columns: Columns for the constraint
            update_columns: Columns to update on conflict
            returning: Columns to return

        Returns:
            Bulk UPSERT query
        """
        # If no values, return None
        if not values:
            return None

        # If only one value, use regular upsert
        if len(values) == 1:
            return self.build_upsert(
                values[0],
                constraint_columns,
                update_columns,
                returning,
            )

        # If no update columns provided, update all except constraint columns
        if update_columns is None:
            update_columns = [
                col.name
                for col in self.table.columns
                if col.name not in constraint_columns
            ]

        # Get all columns from first item
        all_columns = list(values[0].keys())

        # Build column list
        columns = ", ".join(all_columns)

        # Build values list for each item
        values_list = []

        for i, item in enumerate(values):
            item_values = []

            # Check that all items have the same keys
            if set(item.keys()) != set(all_columns):
                raise ValueError("All items must have the same keys")

            # Build values for this item
            for col in all_columns:
                item_values.append(f":{col}_{i}")

            values_list.append(f"({', '.join(item_values)})")

        # Build constraint
        constraint = ", ".join(constraint_columns)

        # Build update list
        updates = ", ".join(f"{col} = EXCLUDED.{col}" for col in update_columns)

        # Build returning clause
        if returning:
            returning_clause = "RETURNING " + ", ".join(col.name for col in returning)
        else:
            returning_clause = ""

        # Build query
        query_text = f"""
        INSERT INTO {self.table.name} ({columns})
        VALUES {', '.join(values_list)}
        ON CONFLICT ({constraint})
        DO UPDATE SET {updates}
        {returning_clause}
        """

        # Create parameters dictionary
        params = {}

        for i, item in enumerate(values):
            for col, val in item.items():
                params[f"{col}_{i}"] = val

        return text(query_text), params

    def build_json_query(
        self,
        json_column: Column,
        json_path: str,
        operator: str = "=",
        value: Any = None,
    ) -> BinaryExpression:
        """
        Build a query for JSON columns.

        Args:
            json_column: JSON column
            json_path: JSON path (e.g., 'data.name')
            operator: Operator to use
            value: Value to compare against

        Returns:
            WHERE condition
        """
        # Split path
        parts = json_path.split(".")

        # Build expression
        if len(parts) == 1:
            # Simple path
            if operator == "=":
                return json_column[parts[0]].astext == value
            elif operator == "!=":
                return json_column[parts[0]].astext != value
            elif operator == ">":
                return json_column[parts[0]].astext > value
            elif operator == "<":
                return json_column[parts[0]].astext < value
            elif operator == ">=":
                return json_column[parts[0]].astext >= value
            elif operator == "<=":
                return json_column[parts[0]].astext <= value
            elif operator == "LIKE":
                return json_column[parts[0]].astext.like(value)
            elif operator == "ILIKE":
                return json_column[parts[0]].astext.ilike(value)
            elif operator == "IS NULL":
                return json_column[parts[0]].astext.is_(None)
            elif operator == "IS NOT NULL":
                return json_column[parts[0]].astext.isnot(None)
            elif operator == "IN":
                return json_column[parts[0]].astext.in_(value)
            elif operator == "NOT IN":
                return json_column[parts[0]].astext.notin_(value)
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        else:
            # Complex path
            if operator == "=":
                return json_column[parts[0]][parts[1:]].astext == value
            elif operator == "!=":
                return json_column[parts[0]][parts[1:]].astext != value
            elif operator == ">":
                return json_column[parts[0]][parts[1:]].astext > value
            elif operator == "<":
                return json_column[parts[0]][parts[1:]].astext < value
            elif operator == ">=":
                return json_column[parts[0]][parts[1:]].astext >= value
            elif operator == "<=":
                return json_column[parts[0]][parts[1:]].astext <= value
            elif operator == "LIKE":
                return json_column[parts[0]][parts[1:]].astext.like(value)
            elif operator == "ILIKE":
                return json_column[parts[0]][parts[1:]].astext.ilike(value)
            elif operator == "IS NULL":
                return json_column[parts[0]][parts[1:]].astext.is_(None)
            elif operator == "IS NOT NULL":
                return json_column[parts[0]][parts[1:]].astext.isnot(None)
            elif operator == "IN":
                return json_column[parts[0]][parts[1:]].astext.in_(value)
            elif operator == "NOT IN":
                return json_column[parts[0]][parts[1:]].astext.notin_(value)
            else:
                raise ValueError(f"Unsupported operator: {operator}")

    def build_fts_query(
        self,
        column: Column,
        query_string: str,
    ) -> TextClause:
        """
        Build a full-text search query.

        Args:
            column: Column to search
            query_string: Search query

        Returns:
            WHERE condition
        """
        # Sanitize query string
        query_string = query_string.replace("'", "''")

        # Build query
        return text(f"{column.name} @@ to_tsquery('english', '{query_string}')")

    def build_exists_query(
        self,
        subquery: Select,
    ) -> Exists:
        """
        Build an EXISTS query.

        Args:
            subquery: Subquery

        Returns:
            EXISTS condition
        """
        return exists(subquery)

    def build_case_expression(
        self,
        conditions: list[Tuple[BinaryExpression, Any]],
        else_value: Any = None,
    ) -> case:
        """
        Build a CASE expression.

        Args:
            conditions: List of (condition, value) pairs
            else_value: Value for ELSE

        Returns:
            CASE expression
        """
        # Convert to dict for case
        whens = {cond: value for cond, value in conditions}

        # Create case
        return case(whens, else_=else_value)

    async def get_by_id(
        self,
        id_value: Any,
        id_column: Optional[Column] = None,
        use_cache: Optional[bool] = None,
    ) -> Optional[T]:
        """
        Get a model by ID.

        Args:
            id_value: ID value
            id_column: ID column
            use_cache: Whether to cache query results

        Returns:
            ModelBase instance or None
        """
        # Use provided cache setting or class default
        should_cache = use_cache if use_cache is not None else self.use_cache

        # Get ID column
        if id_column is None:
            id_column = self.table.primary_key.columns.values()[0]

        # Build query
        query = self.build_select(
            where=id_column == id_value,
        )

        # Execute query
        if should_cache:
            # Use cache
            result = await self._execute_cached(query, {})

            # Return first result or None
            if result and len(result) > 0:
                return result[0]

            return None
        else:
            # Execute directly
            result = await self._execute_query(query)

            # Return first result or None
            model = result.scalars().first()
            return model

    async def get_by_ids(
        self,
        id_values: list[Any],
        id_column: Optional[Column] = None,
        use_cache: Optional[bool] = None,
    ) -> list[T]:
        """
        Get models by IDs.

        Args:
            id_values: ID values
            id_column: ID column
            use_cache: Whether to cache query results

        Returns:
            List of model instances
        """
        # If no IDs, return empty list
        if not id_values:
            return []

        # Use provided cache setting or class default
        should_cache = use_cache if use_cache is not None else self.use_cache

        # Get ID column
        if id_column is None:
            id_column = self.table.primary_key.columns.values()[0]

        # Build query
        query = self.build_select(
            where=id_column.in_(id_values),
        )

        # Execute query
        if should_cache:
            # Use cache
            result = await self._execute_cached(query, {})
            return result
        else:
            # Execute directly
            result = await self._execute_query(query)
            return list(result.scalars().all())

    async def insert(
        self,
        values: Dict[str, Any],
        return_model: bool = True,
    ) -> Optional[T]:
        """
        Insert a model.

        Args:
            values: Values to insert
            return_model: Whether to return the model

        Returns:
            Inserted model if return_model is True
        """
        # Build query
        if return_model:
            # Use RETURNING to get model
            query = self.build_insert(
                values=values,
                returning=[self.table],
            )
        else:
            # Simple insert
            query = self.build_insert(
                values=values,
            )

        # Execute query
        result = await self._execute_query(query)

        # Return model if requested
        if return_model:
            return result.scalars().first()

        return None

    async def update(
        self,
        values: Dict[str, Any],
        where: Union[BinaryExpression, list[BinaryExpression]],
        return_models: bool = False,
    ) -> Union[int, list[T]]:
        """
        Update models.

        Args:
            values: Values to update
            where: WHERE conditions
            return_models: Whether to return the models

        Returns:
            Number of updated rows or list of updated models
        """
        # Build query
        if return_models:
            # Use RETURNING to get models
            query = self.build_update(
                values=values,
                where=where,
                returning=[self.table],
            )
        else:
            # Simple update
            query = self.build_update(
                values=values,
                where=where,
            )

        # Execute query
        result = await self._execute_query(query)

        # Return models if requested
        if return_models:
            return list(result.scalars().all())

        # Return number of updated rows
        return result.rowcount

    async def delete(
        self,
        where: Union[BinaryExpression, list[BinaryExpression]],
        return_models: bool = False,
    ) -> Union[int, list[T]]:
        """
        Delete models.

        Args:
            where: WHERE conditions
            return_models: Whether to return the models

        Returns:
            Number of deleted rows or list of deleted models
        """
        # Build query
        if return_models:
            # Use RETURNING to get models
            query = self.build_delete(
                where=where,
                returning=[self.table],
            )
        else:
            # Simple delete
            query = self.build_delete(
                where=where,
            )

        # Execute query
        result = await self._execute_query(query)

        # Return models if requested
        if return_models:
            return list(result.scalars().all())

        # Return number of deleted rows
        return result.rowcount

    async def upsert(
        self,
        values: Dict[str, Any],
        constraint_columns: list[str],
        update_columns: list[str] | None = None,
        return_model: bool = True,
    ) -> Optional[T]:
        """
        Upsert a model.

        Args:
            values: Values to insert
            constraint_columns: Columns for the constraint
            update_columns: Columns to update on conflict
            return_model: Whether to return the model

        Returns:
            Upserted model if return_model is True
        """
        # Build query
        if return_model:
            # Use RETURNING to get model
            query = self.build_upsert(
                values=values,
                constraint_columns=constraint_columns,
                update_columns=update_columns,
                returning=[col for col in self.table.columns],
            )
        else:
            # Simple upsert
            query = self.build_upsert(
                values=values,
                constraint_columns=constraint_columns,
                update_columns=update_columns,
            )

        # Execute query
        result = await self._execute_query(query)

        # Return model if requested
        if return_model:
            row = result.fetchone()
            if row is None:
                return None

            # Convert row to model
            model = self.model_class()
            for key, value in row._mapping.items():
                setattr(model, key, value)

            return model

        return None

    async def bulk_insert(
        self,
        values: list[dict[str, Any]],
        return_models: bool = False,
    ) -> Union[int, list[T]]:
        """
        Bulk insert models.

        Args:
            values: List of values to insert
            return_models: Whether to return the models

        Returns:
            Number of inserted rows or list of inserted models
        """
        # If no values, return empty result
        if not values:
            return [] if return_models else 0

        # Build query
        if return_models:
            # Use RETURNING to get models
            query = self.build_bulk_insert(
                values=values,
                returning=[self.table],
            )
        else:
            # Simple insert
            query = self.build_bulk_insert(
                values=values,
            )

        # Execute query
        result = await self._execute_query(query)

        # Return models if requested
        if return_models:
            return list(result.scalars().all())

        # Return number of inserted rows
        return result.rowcount

    async def bulk_upsert(
        self,
        values: list[dict[str, Any]],
        constraint_columns: list[str],
        update_columns: list[str] | None = None,
        return_models: bool = False,
    ) -> Union[int, list[T]]:
        """
        Bulk upsert models.

        Args:
            values: List of values to insert
            constraint_columns: Columns for the constraint
            update_columns: Columns to update on conflict
            return_models: Whether to return the models

        Returns:
            Number of upserted rows or list of upserted models
        """
        # If no values, return empty result
        if not values:
            return [] if return_models else 0

        # Build query
        if return_models:
            # Use RETURNING to get models
            query = self.build_bulk_upsert(
                values=values,
                constraint_columns=constraint_columns,
                update_columns=update_columns,
                returning=[col for col in self.table.columns],
            )
        else:
            # Simple upsert
            query = self.build_bulk_upsert(
                values=values,
                constraint_columns=constraint_columns,
                update_columns=update_columns,
            )

        # Check if we got both query and params
        if isinstance(query, tuple):
            query_text, params = query

            # Execute query with params
            result = await self._execute_query(query_text, params)
        else:
            # Execute query
            result = await self._execute_query(query)

        # Return models if requested
        if return_models:
            rows = result.fetchall()

            # Convert rows to models
            models = []

            for row in rows:
                model = self.model_class()
                for key, value in row._mapping.items():
                    setattr(model, key, value)

                models.append(model)

            return models

        # Return number of upserted rows
        return result.rowcount
