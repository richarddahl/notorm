# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain services for the Database module.

This module defines service interfaces and implementations for the Database module,
providing business logic for database operations, query management, optimization,
and connection pooling.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import (
    Protocol,
    Generic,
    TypeVar,
    Dict,
    List,
    Any,
    Optional,
    Union,
    Type,
    AsyncIterator,
    Iterator,
    Tuple,
    cast,
)
import logging
import time
from datetime import datetime, UTC, timedelta
import re
import json
import hashlib

from sqlalchemy import text, Select, Table, Column, MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.engine import Result, Row
import asyncpg

from uno.core.errors.result import Result as UnoResult, Success, Failure, ErrorDetails
from uno.database.entities import (
    DatabaseId,
    ConnectionConfig,
    Transaction,
    TransactionId,
    TransactionIsolationLevel,
    QueryStatistics,
    QueryId,
    QueryPlan,
    IndexRecommendation,
    IndexType,
    ConnectionPoolConfig,
    PoolStatistics,
    CachedResult,
    CacheKey,
    CacheConfig,
    CacheStrategy,
    OptimizationConfig,
    OptimizationLevel,
    QueryComplexity,
    QueryRewrite,
    OptimizerMetricsSnapshot,
    QueryRequest,
    QueryResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
    OptimizationRequest,
    OptimizationResponse,
    TransactionRequest,
    TransactionResponse,
)
from uno.database.domain_repositories import (
    DatabaseSessionRepositoryProtocol,
    DatabaseTransactionRepositoryProtocol,
    QueryStatisticsRepositoryProtocol,
    QueryPlanRepositoryProtocol,
    IndexRecommendationRepositoryProtocol,
    QueryCacheRepositoryProtocol,
    PoolStatisticsRepositoryProtocol,
)


# Service Protocols


class DatabaseManagerServiceProtocol(Protocol):
    """Service protocol for database management operations."""

    async def test_connection(
        self, config: ConnectionConfig
    ) -> UnoResult[ConnectionTestResponse, ErrorDetails]:
        """
        Test a database connection.

        Args:
            config: Database connection configuration

        Returns:
            Result containing the connection test response
        """
        ...

    async def create_database(
        self, config: ConnectionConfig
    ) -> UnoResult[bool, ErrorDetails]:
        """
        Create a new database.

        Args:
            config: Database connection configuration

        Returns:
            Result indicating success
        """
        ...

    async def drop_database(
        self, config: ConnectionConfig
    ) -> UnoResult[bool, ErrorDetails]:
        """
        Drop a database.

        Args:
            config: Database connection configuration

        Returns:
            Result indicating success
        """
        ...

    async def execute_script(self, script: str) -> UnoResult[None, ErrorDetails]:
        """
        Execute a SQL script.

        Args:
            script: SQL script to execute

        Returns:
            Result indicating success
        """
        ...

    async def create_extension(
        self, extension_name: str, schema: str | None = None
    ) -> UnoResult[None, ErrorDetails]:
        """
        Create a database extension.

        Args:
            extension_name: Extension name
            schema: Optional schema name

        Returns:
            Result indicating success
        """
        ...


class QueryExecutionServiceProtocol(Protocol):
    """Service protocol for query execution."""

    async def execute_query(
        self, request: QueryRequest
    ) -> UnoResult[QueryResponse, ErrorDetails]:
        """
        Execute a database query.

        Args:
            request: Query request

        Returns:
            Result containing the query response
        """
        ...

    async def execute_batch_queries(
        self, requests: list[QueryRequest]
    ) -> UnoResult[list[QueryResponse], ErrorDetails]:
        """
        Execute multiple queries in batch.

        Args:
            requests: List of query requests

        Returns:
            Result containing the query responses
        """
        ...


class QueryOptimizerServiceProtocol(Protocol):
    """Service protocol for query optimization."""

    async def optimize_query(
        self, request: OptimizationRequest
    ) -> UnoResult[OptimizationResponse, ErrorDetails]:
        """
        Optimize a query.

        Args:
            request: Optimization request

        Returns:
            Result containing the optimization response
        """
        ...

    async def analyze_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> UnoResult[QueryPlan, ErrorDetails]:
        """
        Analyze a query to get its execution plan.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            Result containing the query plan
        """
        ...

    async def get_index_recommendations(
        self, table_name: str | None = None, limit: int = 10
    ) -> UnoResult[list[IndexRecommendation], ErrorDetails]:
        """
        Get index recommendations.

        Args:
            table_name: Optional table to get recommendations for
            limit: Maximum number of recommendations

        Returns:
            Result containing index recommendations
        """
        ...

    async def apply_index_recommendation(
        self, recommendation: IndexRecommendation
    ) -> UnoResult[bool, ErrorDetails]:
        """
        Apply an index recommendation.

        Args:
            recommendation: Index recommendation to apply

        Returns:
            Result indicating success
        """
        ...

    async def get_optimizer_metrics(
        self,
    ) -> UnoResult[OptimizerMetricsSnapshot, ErrorDetails]:
        """
        Get optimizer metrics.

        Returns:
            Result containing optimizer metrics
        """
        ...


class QueryCacheServiceProtocol(Protocol):
    """Service protocol for query caching."""

    async def get_cached_result(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> UnoResult[Optional[Any], ErrorDetails]:
        """
        Get a cached query result.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            Result containing the cached result if found
        """
        ...

    async def cache_result(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]],
        result: Any,
        ttl_seconds: Optional[int] = None,
    ) -> UnoResult[None, ErrorDetails]:
        """
        Cache a query result.

        Args:
            query: SQL query
            parameters: Query parameters
            result: Query result
            ttl_seconds: Optional TTL in seconds

        Returns:
            Result indicating success
        """
        ...

    async def invalidate_cache(
        self, table_names: list[str] | None = None
    ) -> UnoResult[int, ErrorDetails]:
        """
        Invalidate cache entries.

        Args:
            table_names: Optional list of tables to invalidate cache for

        Returns:
            Result containing the number of invalidated entries
        """
        ...

    async def get_cache_statistics(self) -> UnoResult[Dict[str, Any], ErrorDetails]:
        """
        Get cache statistics.

        Returns:
            Result containing cache statistics
        """
        ...


class TransactionServiceProtocol(Protocol):
    """Service protocol for transaction management."""

    async def begin_transaction(
        self, request: TransactionRequest
    ) -> UnoResult[TransactionResponse, ErrorDetails]:
        """
        Begin a new transaction.

        Args:
            request: Transaction request

        Returns:
            Result containing the transaction response
        """
        ...

    async def commit_transaction(
        self, transaction_id: TransactionId
    ) -> UnoResult[TransactionResponse, ErrorDetails]:
        """
        Commit a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            Result containing the transaction response
        """
        ...

    async def rollback_transaction(
        self, transaction_id: TransactionId
    ) -> UnoResult[TransactionResponse, ErrorDetails]:
        """
        Rollback a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            Result containing the transaction response
        """
        ...

    @asynccontextmanager
    async def transaction_context(
        self,
        isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED,
        read_only: bool = False,
    ) -> AsyncIterator[Transaction]:
        """
        Context manager for transaction management.

        Args:
            isolation_level: Transaction isolation level
            read_only: Whether the transaction is read-only

        Yields:
            A transaction object
        """
        ...


class ConnectionPoolServiceProtocol(Protocol):
    """Service protocol for connection pool management."""

    async def get_pool_statistics(self) -> UnoResult[PoolStatistics, ErrorDetails]:
        """
        Get current pool statistics.

        Returns:
            Result containing pool statistics
        """
        ...

    async def get_historical_statistics(
        self, limit: int = 100
    ) -> UnoResult[list[PoolStatistics], ErrorDetails]:
        """
        Get historical pool statistics.

        Args:
            limit: Maximum number of statistics to return

        Returns:
            Result containing historical pool statistics
        """
        ...

    async def optimize_pool_size(self) -> UnoResult[ConnectionPoolConfig, ErrorDetails]:
        """
        Optimize the connection pool size based on usage.

        Returns:
            Result containing the optimized pool configuration
        """
        ...

    async def reset_pool(self) -> UnoResult[None, ErrorDetails]:
        """
        Reset the connection pool.

        Returns:
            Result indicating success
        """
        ...


# Service Implementations


class DatabaseManagerService:
    """Service for database management operations."""

    def __init__(
        self,
        session_repository: DatabaseSessionRepositoryProtocol,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the service.

        Args:
            session_repository: Database session repository
            logger: Optional logger
        """
        self.session_repository = session_repository
        self.logger = logger or logging.getLogger(__name__)

    async def test_connection(
        self, config: ConnectionConfig
    ) -> UnoResult[ConnectionTestResponse, ErrorDetails]:
        """
        Test a database connection.

        Args:
            config: Database connection configuration

        Returns:
            Result containing the connection test response
        """
        try:
            import asyncpg

            start_time = time.time()

            # Try to connect
            conn = await asyncpg.connect(
                host=config.db_host,
                port=config.db_port,
                user=config.db_role,
                password=config.db_user_pw,
                database=config.db_name,
            )

            # Get server version
            version_row = await conn.fetchrow("SELECT version()")
            version = version_row[0] if version_row else None

            # Close the connection
            await conn.close()

            # Calculate connection time
            connection_time = (time.time() - start_time) * 1000  # in milliseconds

            # Create response
            response = ConnectionTestResponse(
                success=True,
                message="Connection successful",
                connection_time=connection_time,
                database_version=version,
            )

            return Success(response)
        except Exception as e:
            self.logger.error(f"Error testing connection: {str(e)}")

            # Create error response
            response = ConnectionTestResponse(
                success=False,
                message="Connection failed",
                connection_time=0,
                error=str(e),
            )

            return Success(response)

    async def create_database(
        self, config: ConnectionConfig
    ) -> UnoResult[bool, ErrorDetails]:
        """
        Create a new database.

        Args:
            config: Database connection configuration

        Returns:
            Result indicating success
        """
        try:
            import asyncpg

            # Connect to postgres database
            admin_config = config.for_admin_connection()

            admin_conn = await asyncpg.connect(
                host=admin_config.db_host,
                port=admin_config.db_port,
                user=admin_config.db_role,
                password=admin_config.db_user_pw,
                database=admin_config.db_name,
            )

            try:
                # Close existing connections
                await admin_conn.execute(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config.db_name}'
                    AND pid <> pg_backend_pid()
                """
                )

                # Drop the database if it exists
                await admin_conn.execute(f"DROP DATABASE IF EXISTS {config.db_name}")

                # Create the database
                await admin_conn.execute(f"CREATE DATABASE {config.db_name}")

                self.logger.info(f"Created database {config.db_name}")
            finally:
                # Close the admin connection
                await admin_conn.close()

            # Connect to the new database to initialize schemas and extensions
            db_conn = await asyncpg.connect(
                host=config.db_host,
                port=config.db_port,
                user=config.db_role,
                password=config.db_user_pw,
                database=config.db_name,
            )

            try:
                # Create the main schema
                if config.db_schema:
                    await db_conn.execute(
                        f"CREATE SCHEMA IF NOT EXISTS {config.db_schema}"
                    )

                # Create essential extensions
                await db_conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
                await db_conn.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp")
                await db_conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            finally:
                # Close the database connection
                await db_conn.close()

            self.logger.info(f"Initialized database {config.db_name}")
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error creating database: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="DATABASE_CREATION_ERROR",
                    message=f"Error creating database: {str(e)}",
                )
            )

    async def drop_database(
        self, config: ConnectionConfig
    ) -> UnoResult[bool, ErrorDetails]:
        """
        Drop a database.

        Args:
            config: Database connection configuration

        Returns:
            Result indicating success
        """
        try:
            import asyncpg

            # Connect to postgres database
            admin_config = config.for_admin_connection()

            admin_conn = await asyncpg.connect(
                host=admin_config.db_host,
                port=admin_config.db_port,
                user=admin_config.db_role,
                password=admin_config.db_user_pw,
                database=admin_config.db_name,
            )

            try:
                # Close existing connections
                await admin_conn.execute(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config.db_name}'
                    AND pid <> pg_backend_pid()
                """
                )

                # Drop the database
                await admin_conn.execute(f"DROP DATABASE IF EXISTS {config.db_name}")

                self.logger.info(f"Dropped database {config.db_name}")
                return Success(True)
            finally:
                # Close the admin connection
                await admin_conn.close()
        except Exception as e:
            self.logger.error(f"Error dropping database: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="DATABASE_DROP_ERROR",
                    message=f"Error dropping database: {str(e)}",
                )
            )

    async def execute_script(self, script: str) -> UnoResult[None, ErrorDetails]:
        """
        Execute a SQL script.

        Args:
            script: SQL script to execute

        Returns:
            Result indicating success
        """
        try:
            # Execute the script
            result = await self.session_repository.execute(script)

            if isinstance(result, Failure):
                return result

            return Success(None)
        except Exception as e:
            self.logger.error(f"Error executing script: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="SCRIPT_EXECUTION_ERROR",
                    message=f"Error executing script: {str(e)}",
                )
            )

    async def create_extension(
        self, extension_name: str, schema: str | None = None
    ) -> UnoResult[None, ErrorDetails]:
        """
        Create a database extension.

        Args:
            extension_name: Extension name
            schema: Optional schema name

        Returns:
            Result indicating success
        """
        try:
            # Build the CREATE EXTENSION statement
            schema_clause = f"SCHEMA {schema}" if schema else ""
            sql = f"CREATE EXTENSION IF NOT EXISTS {extension_name} {schema_clause}"

            # Execute the statement
            result = await self.session_repository.execute(sql)

            if isinstance(result, Failure):
                return result

            self.logger.info(f"Created extension {extension_name}")
            return Success(None)
        except Exception as e:
            self.logger.error(f"Error creating extension: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="EXTENSION_CREATION_ERROR",
                    message=f"Error creating extension {extension_name}: {str(e)}",
                )
            )


class QueryExecutionService:
    """Service for query execution."""

    def __init__(
        self,
        session_repository: DatabaseSessionRepositoryProtocol,
        cache_service: Optional[QueryCacheServiceProtocol] = None,
        optimizer_service: Optional[QueryOptimizerServiceProtocol] = None,
        stats_repository: Optional[QueryStatisticsRepositoryProtocol] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the service.

        Args:
            session_repository: Database session repository
            cache_service: Optional query cache service
            optimizer_service: Optional query optimizer service
            stats_repository: Optional query statistics repository
            logger: Optional logger
        """
        self.session_repository = session_repository
        self.cache_service = cache_service
        self.optimizer_service = optimizer_service
        self.stats_repository = stats_repository
        self.logger = logger or logging.getLogger(__name__)

    async def execute_query(
        self, request: QueryRequest
    ) -> UnoResult[QueryResponse, ErrorDetails]:
        """
        Execute a database query.

        Args:
            request: Query request

        Returns:
            Result containing the query response
        """
        query_id = QueryId.generate()
        start_time = time.time()
        start_datetime = datetime.now(UTC)

        # Try to get cached result if caching is enabled
        if request.use_cache and self.cache_service:
            cached_result = await self.cache_service.get_cached_result(
                request.query, request.parameters
            )

            if isinstance(cached_result, Success) and cached_result.value is not None:
                # Return cached result
                execution_time = (time.time() - start_time) * 1000  # in milliseconds

                return Success(
                    QueryResponse(
                        success=True,
                        rows=cached_result.value,
                        row_count=(
                            len(cached_result.value)
                            if isinstance(cached_result.value, list)
                            else 1
                        ),
                        execution_time=execution_time,
                        cached=True,
                    )
                )

        # Optimize query if requested
        optimized_query = request.query
        query_plan = None

        if request.optimize and self.optimizer_service:
            optimization_request = OptimizationRequest(
                query=request.query,
                parameters=request.parameters,
                level=OptimizationLevel.BASIC,
                include_plan=True,
            )

            optimization_result = await self.optimizer_service.optimize_query(
                optimization_request
            )

            if isinstance(optimization_result, Success):
                # Use optimized query if available
                optimized_query = (
                    optimization_result.value.optimized_query or request.query
                )
                query_plan = optimization_result.value.plan_after

        try:
            # Execute the query
            result = await self.session_repository.fetch_all(
                optimized_query, request.parameters
            )

            end_time = time.time()
            end_datetime = datetime.now(UTC)
            execution_time = (end_time - start_time) * 1000  # in milliseconds

            if isinstance(result, Failure):
                # Create error response
                response = QueryResponse(
                    success=False,
                    rows=None,
                    row_count=0,
                    execution_time=execution_time,
                    cached=False,
                    error=result.error.message,
                    query_plan=query_plan,
                )

                return Success(response)

            rows = result.value
            row_count = len(rows)

            # Cache the result if caching is enabled
            if request.use_cache and self.cache_service and row_count > 0:
                await self.cache_service.cache_result(
                    request.query, request.parameters, rows, request.cache_ttl
                )

            # Record query statistics if available
            if self.stats_repository:
                stats = QueryStatistics(
                    query_id=query_id,
                    query_text=request.query,
                    execution_time=execution_time / 1000,  # convert to seconds
                    row_count=row_count,
                    complexity=QueryComplexity.SIMPLE,  # simplified
                    start_time=start_datetime,
                    end_time=end_datetime,
                )

                await self.stats_repository.save_statistics(stats)

            # Create success response
            response = QueryResponse(
                success=True,
                rows=rows,
                row_count=row_count,
                execution_time=execution_time,
                cached=False,
                query_plan=query_plan,
            )

            return Success(response)
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")

            # Calculate execution time even for errors
            execution_time = (time.time() - start_time) * 1000  # in milliseconds

            # Create error response
            response = QueryResponse(
                success=False,
                rows=None,
                row_count=0,
                execution_time=execution_time,
                cached=False,
                error=str(e),
                query_plan=query_plan,
            )

            return Success(response)

    async def execute_batch_queries(
        self, requests: list[QueryRequest]
    ) -> UnoResult[list[QueryResponse], ErrorDetails]:
        """
        Execute multiple queries in batch.

        Args:
            requests: List of query requests

        Returns:
            Result containing the query responses
        """
        responses = []

        for request in requests:
            response = await self.execute_query(request)

            if isinstance(response, Success):
                responses.append(response.value)
            else:
                # Return error for the entire batch
                return Failure(response.error)

        return Success(responses)


class QueryOptimizerService:
    """Service for query optimization."""

    def __init__(
        self,
        session_repository: DatabaseSessionRepositoryProtocol,
        plan_repository: Optional[QueryPlanRepositoryProtocol] = None,
        recommendation_repository: Optional[
            IndexRecommendationRepositoryProtocol
        ] = None,
        config: OptimizationConfig = OptimizationConfig(),
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the service.

        Args:
            session_repository: Database session repository
            plan_repository: Optional query plan repository
            recommendation_repository: Optional index recommendation repository
            config: Optimization configuration
            logger: Optional logger
        """
        self.session_repository = session_repository
        self.plan_repository = plan_repository
        self.recommendation_repository = recommendation_repository
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Metrics
        self.metrics = OptimizerMetricsSnapshot()

    async def optimize_query(
        self, request: OptimizationRequest
    ) -> UnoResult[OptimizationResponse, ErrorDetails]:
        """
        Optimize a query.

        Args:
            request: Optimization request

        Returns:
            Result containing the optimization response
        """
        query_id = QueryId.generate()

        # Initialize response
        response = OptimizationResponse(original_query=request.query)

        # Get the execution plan for the original query
        if request.include_plan:
            plan_result = await self.analyze_query(request.query, request.parameters)

            if isinstance(plan_result, Success):
                response.plan_before = plan_result.value
            else:
                return Failure(plan_result.error)

        # Optimize the query based on the requested level
        optimized_query = request.query
        estimated_improvement = 0.0

        if request.level != OptimizationLevel.NONE:
            # Apply basic optimization techniques
            optimized_query = self._apply_basic_optimizations(request.query)

            # Apply more advanced techniques for higher optimization levels
            if request.level in [
                OptimizationLevel.AGGRESSIVE,
                OptimizationLevel.MAXIMUM,
            ]:
                optimized_query = self._apply_advanced_optimizations(optimized_query)

            # Apply query hints if configured
            if self.config.apply_hints and request.level == OptimizationLevel.MAXIMUM:
                optimized_query = self._apply_optimizer_hints(optimized_query)

        # Set the optimized query in the response
        if optimized_query != request.query:
            response.optimized_query = optimized_query

        # Get the execution plan for the optimized query
        if request.include_plan and response.optimized_query:
            plan_result = await self.analyze_query(
                response.optimized_query, request.parameters
            )

            if isinstance(plan_result, Success):
                response.plan_after = plan_result.value

                # Calculate estimated improvement
                if response.plan_before and response.plan_after:
                    if response.plan_before.estimated_cost > 0:
                        improvement = (
                            response.plan_before.estimated_cost
                            - response.plan_after.estimated_cost
                        ) / response.plan_before.estimated_cost
                        estimated_improvement = max(
                            0, improvement * 100
                        )  # as percentage

        # Generate index recommendations if requested
        if request.generate_recommendations and self.recommendation_repository:
            # Parse the query to identify tables
            tables = self._extract_tables_from_query(request.query)

            # Generate recommendations for each table
            for table in tables:
                recommendation = self._generate_index_recommendation(
                    table, request.query
                )

                if recommendation:
                    # Save the recommendation
                    if self.recommendation_repository:
                        await self.recommendation_repository.save_recommendation(
                            recommendation
                        )

                    # Add to response
                    response.recommendations.append(recommendation)

        # Set the estimated improvement
        response.estimated_improvement = estimated_improvement

        # Update metrics
        self.metrics.query_count += 1
        if response.optimized_query:
            self.metrics.query_rewrites += 1
        if response.recommendations:
            self.metrics.index_recommendations += len(response.recommendations)

        return Success(response)

    async def analyze_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> UnoResult[QueryPlan, ErrorDetails]:
        """
        Analyze a query to get its execution plan.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            Result containing the query plan
        """
        query_id = QueryId.generate()

        try:
            # Create EXPLAIN query
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"

            # Execute the EXPLAIN query
            result = await self.session_repository.fetch_one(explain_query, parameters)

            if isinstance(result, Failure):
                return Failure(
                    ErrorDetails(
                        code="EXPLAIN_ERROR",
                        message=f"Error explaining query: {result.error.message}",
                    )
                )

            # Parse the explain output
            explain_output = result.value
            if not explain_output or not isinstance(explain_output, dict):
                return Failure(
                    ErrorDetails(
                        code="INVALID_EXPLAIN_OUTPUT", message="Invalid EXPLAIN output"
                    )
                )

            # Extract plan details
            plan_json = json.dumps(explain_output.get("QUERY PLAN", [{}])[0])

            # Create query plan object
            plan = QueryPlan(
                query_id=query_id,
                plan_text=plan_json,
                estimated_cost=self._extract_cost_from_plan(plan_json),
                actual_cost=self._extract_actual_cost_from_plan(plan_json),
                estimated_rows=self._extract_rows_from_plan(plan_json),
                actual_rows=self._extract_actual_rows_from_plan(plan_json),
                sequential_scans=self._count_sequential_scans(plan_json),
                index_scans=self._count_index_scans(plan_json),
            )

            # Save the plan if repository available
            if self.plan_repository:
                await self.plan_repository.save_plan(plan)

            return Success(plan)
        except Exception as e:
            self.logger.error(f"Error analyzing query: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="QUERY_ANALYSIS_ERROR",
                    message=f"Error analyzing query: {str(e)}",
                )
            )

    async def get_index_recommendations(
        self, table_name: str | None = None, limit: int = 10
    ) -> UnoResult[list[IndexRecommendation], ErrorDetails]:
        """
        Get index recommendations.

        Args:
            table_name: Optional table to get recommendations for
            limit: Maximum number of recommendations

        Returns:
            Result containing index recommendations
        """
        if not self.recommendation_repository:
            return Success([])

        result = await self.recommendation_repository.list_recommendations(
            table_name, limit
        )
        return result

    async def apply_index_recommendation(
        self, recommendation: IndexRecommendation
    ) -> UnoResult[bool, ErrorDetails]:
        """
        Apply an index recommendation.

        Args:
            recommendation: Index recommendation to apply

        Returns:
            Result indicating success
        """
        try:
            # Generate the SQL statement
            sql = recommendation.to_sql()

            # Execute the statement
            result = await self.session_repository.execute(sql)

            if isinstance(result, Failure):
                return Failure(
                    ErrorDetails(
                        code="INDEX_CREATION_ERROR",
                        message=f"Error creating index: {result.error.message}",
                    )
                )

            return Success(True)
        except Exception as e:
            self.logger.error(f"Error applying index recommendation: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="INDEX_CREATION_ERROR",
                    message=f"Error applying index recommendation: {str(e)}",
                )
            )

    async def get_optimizer_metrics(
        self,
    ) -> UnoResult[OptimizerMetricsSnapshot, ErrorDetails]:
        """
        Get optimizer metrics.

        Returns:
            Result containing optimizer metrics
        """
        # Update the timestamp
        self.metrics.timestamp = datetime.now(UTC)
        return Success(self.metrics)

    def _apply_basic_optimizations(self, query: str) -> str:
        """
        Apply basic query optimizations.

        Args:
            query: SQL query

        Returns:
            Optimized query
        """
        # Convert query to lowercase for easier manipulation
        lower_query = query.lower()

        # Optimize SELECT * queries
        if "select *" in lower_query:
            # In a real implementation, we would parse the query and extract only needed columns
            # This is a simplified implementation
            pass

        # Optimize LIKE queries with leading wildcards
        like_pattern = r"(\w+)\s+like\s+'%([^']+)'"
        if re.search(like_pattern, lower_query):
            # In a real implementation, we would suggest using a trigram index or full-text search
            # This is a simplified implementation
            pass

        # Remove unnecessary ORDER BY in subqueries
        order_by_pattern = r"(\(select.*order\s+by\s+\w+(\s+(asc|desc))?.*\))"
        if re.search(order_by_pattern, lower_query):
            # In a real implementation, we would remove unnecessary ORDER BY clauses
            # This is a simplified implementation
            pass

        # Optimize IN clauses with a large number of values
        in_pattern = r"(\w+)\s+in\s+\(\s*(('\w+'|\d+)\s*,\s*){10,}\s*('\w+'|\d+)\s*\)"
        if re.search(in_pattern, lower_query):
            # In a real implementation, we would suggest using a temporary table or unnesting
            # This is a simplified implementation
            pass

        # For this simplified implementation, return the original query
        return query

    def _apply_advanced_optimizations(self, query: str) -> str:
        """
        Apply advanced query optimizations.

        Args:
            query: SQL query

        Returns:
            Optimized query
        """
        # Convert query to lowercase for easier manipulation
        lower_query = query.lower()

        # Optimize self-joins
        self_join_pattern = r"from\s+(\w+)(?:\s+\w+)?\s+join\s+\1"
        if re.search(self_join_pattern, lower_query):
            # In a real implementation, we would optimize self-joins
            # This is a simplified implementation
            pass

        # Optimize subqueries that can be converted to JOINs
        subquery_pattern = r"where\s+\w+\s+in\s+\(select"
        if re.search(subquery_pattern, lower_query):
            # In a real implementation, we would convert subqueries to JOINs
            # This is a simplified implementation
            pass

        # Optimize aggregations
        aggregation_pattern = r"(sum|avg|min|max|count)\s*\("
        if re.search(aggregation_pattern, lower_query) and "group by" in lower_query:
            # In a real implementation, we would optimize aggregations
            # This is a simplified implementation
            pass

        # For this simplified implementation, return the original query
        return query

    def _apply_optimizer_hints(self, query: str) -> str:
        """
        Apply optimizer hints to a query.

        Args:
            query: SQL query

        Returns:
            Query with optimizer hints
        """
        # This is a simplified implementation
        # In a real implementation, we would analyze the query and add specific hints
        return query

    def _extract_tables_from_query(self, query: str) -> list[str]:
        """
        Extract table names from a query.

        Args:
            query: SQL query

        Returns:
            List of table names
        """
        # This is a simplified implementation
        # In a real implementation, we would use a SQL parser

        lower_query = query.lower()
        tables = []

        # Extract tables from FROM clause
        from_pattern = r"from\s+([a-zA-Z0-9_\.]+)"
        from_matches = re.findall(from_pattern, lower_query)
        tables.extend(from_matches)

        # Extract tables from JOIN clauses
        join_pattern = r"join\s+([a-zA-Z0-9_\.]+)"
        join_matches = re.findall(join_pattern, lower_query)
        tables.extend(join_matches)

        # Remove duplicates and schema qualifiers
        unique_tables = []
        for table in tables:
            # Remove schema qualifier if present
            if "." in table:
                _, table = table.split(".", 1)

            if table not in unique_tables:
                unique_tables.append(table)

        return unique_tables

    def _generate_index_recommendation(
        self, table_name: str, query: str
    ) -> Optional[IndexRecommendation]:
        """
        Generate an index recommendation for a table based on a query.

        Args:
            table_name: Table name
            query: SQL query

        Returns:
            Index recommendation or None
        """
        # This is a simplified implementation
        # In a real implementation, we would analyze the query and suggest specific indexes

        lower_query = query.lower()

        # Check for WHERE conditions
        where_pattern = (
            rf"where\s+([a-zA-Z0-9_\s\.=<>!]+{table_name}[a-zA-Z0-9_\s\.=<>!]+)"
        )
        where_matches = re.findall(where_pattern, lower_query)

        if where_matches:
            # Extract columns from WHERE conditions
            columns = []
            for condition in where_matches:
                column_pattern = rf"{table_name}\.([a-zA-Z0-9_]+)"
                column_matches = re.findall(column_pattern, condition)
                columns.extend(column_matches)

            if columns:
                # Create index recommendation
                return IndexRecommendation(
                    table_name=table_name,
                    column_names=columns,
                    index_type=IndexType.BTREE,
                    estimated_improvement=0.2,  # 20% improvement (simplified)
                    rationale=f"Query contains filter conditions on {', '.join(columns)}",
                )

        # Check for JOIN conditions
        join_pattern = rf"join\s+{table_name}\s+on\s+([a-zA-Z0-9_\s\.=<>!]+)"
        join_matches = re.findall(join_pattern, lower_query)

        if join_matches:
            # Extract columns from JOIN conditions
            columns = []
            for condition in join_matches:
                column_pattern = rf"{table_name}\.([a-zA-Z0-9_]+)"
                column_matches = re.findall(column_pattern, condition)
                columns.extend(column_matches)

            if columns:
                # Create index recommendation
                return IndexRecommendation(
                    table_name=table_name,
                    column_names=columns,
                    index_type=IndexType.BTREE,
                    estimated_improvement=0.3,  # 30% improvement (simplified)
                    rationale=f"Query contains join conditions on {', '.join(columns)}",
                )

        # No recommendation
        return None

    def _extract_cost_from_plan(self, plan_json: str) -> float:
        """
        Extract estimated cost from an execution plan.

        Args:
            plan_json: JSON execution plan

        Returns:
            Estimated cost
        """
        # This is a simplified implementation
        # In a real implementation, we would parse the JSON properly
        try:
            plan_data = json.loads(plan_json)
            return float(plan_data.get("Plan", {}).get("Total Cost", 0))
        except:
            return 0.0

    def _extract_actual_cost_from_plan(self, plan_json: str) -> Optional[float]:
        """
        Extract actual cost from an execution plan.

        Args:
            plan_json: JSON execution plan

        Returns:
            Actual cost
        """
        # This is a simplified implementation
        # In a real implementation, we would parse the JSON properly
        try:
            plan_data = json.loads(plan_json)
            return float(plan_data.get("Plan", {}).get("Actual Total Time", 0))
        except:
            return None

    def _extract_rows_from_plan(self, plan_json: str) -> int:
        """
        Extract estimated rows from an execution plan.

        Args:
            plan_json: JSON execution plan

        Returns:
            Estimated rows
        """
        try:
            plan_data = json.loads(plan_json)
            return int(plan_data.get("Plan", {}).get("Plan Rows", 0))
        except:
            return 0

    def _extract_actual_rows_from_plan(self, plan_json: str) -> Optional[int]:
        """
        Extract actual rows from an execution plan.

        Args:
            plan_json: JSON execution plan

        Returns:
            Actual rows
        """
        try:
            plan_data = json.loads(plan_json)
            return int(plan_data.get("Plan", {}).get("Actual Rows", 0))
        except:
            return None

    def _count_sequential_scans(self, plan_json: str) -> int:
        """
        Count sequential scans in an execution plan.

        Args:
            plan_json: JSON execution plan

        Returns:
            Number of sequential scans
        """
        try:
            plan_data = json.loads(plan_json)

            # This is a simplified implementation
            # In a real implementation, we would recursively traverse the plan
            plan_type = plan_data.get("Plan", {}).get("Node Type", "")
            if plan_type == "Seq Scan":
                return 1
            return 0
        except:
            return 0

    def _count_index_scans(self, plan_json: str) -> int:
        """
        Count index scans in an execution plan.

        Args:
            plan_json: JSON execution plan

        Returns:
            Number of index scans
        """
        try:
            plan_data = json.loads(plan_json)

            # This is a simplified implementation
            # In a real implementation, we would recursively traverse the plan
            plan_type = plan_data.get("Plan", {}).get("Node Type", "")
            if plan_type in ["Index Scan", "Index Only Scan", "Bitmap Index Scan"]:
                return 1
            return 0
        except:
            return 0


class QueryCacheService:
    """Service for query caching."""

    def __init__(
        self,
        cache_repository: QueryCacheRepositoryProtocol,
        config: CacheConfig = CacheConfig(),
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the service.

        Args:
            cache_repository: Query cache repository
            config: Cache configuration
            logger: Optional logger
        """
        self.cache_repository = cache_repository
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.total_queries = 0

    async def get_cached_result(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> UnoResult[Optional[Any], ErrorDetails]:
        """
        Get a cached query result.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            Result containing the cached result if found
        """
        self.total_queries += 1

        # Create cache key
        key = CacheKey.from_query(query, parameters)

        # Get from cache
        result = await self.cache_repository.get_cached_result(key)

        if isinstance(result, Failure):
            self.logger.error(f"Error getting cached result: {result.error.message}")
            self.misses += 1
            return Success(None)

        cached_result = result.value

        if cached_result is None:
            # Cache miss
            self.misses += 1
            return Success(None)

        # Cache hit
        self.hits += 1
        return Success(cached_result.result)

    async def cache_result(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]],
        result: Any,
        ttl_seconds: Optional[int] = None,
    ) -> UnoResult[None, ErrorDetails]:
        """
        Cache a query result.

        Args:
            query: SQL query
            parameters: Query parameters
            result: Query result
            ttl_seconds: Optional TTL in seconds

        Returns:
            Result indicating success
        """
        # Create cache key
        key = CacheKey.from_query(query, parameters)

        # Determine complexity and TTL
        complexity = self._determine_query_complexity(query)
        ttl = ttl_seconds or self.config.get_ttl_for_query(query, complexity)

        # Calculate expiration time
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)

        # Create cached result
        cached_result = CachedResult(key=key, result=result, expires_at=expires_at)

        # Store in cache
        store_result = await self.cache_repository.set_cached_result(cached_result)

        if isinstance(store_result, Failure):
            self.logger.error(f"Error caching result: {store_result.error.message}")
            return store_result

        return Success(None)

    async def invalidate_cache(
        self, table_names: list[str] | None = None
    ) -> UnoResult[int, ErrorDetails]:
        """
        Invalidate cache entries.

        Args:
            table_names: Optional list of tables to invalidate cache for

        Returns:
            Result containing the number of invalidated entries
        """
        if not table_names:
            # Invalidate all
            result = await self.cache_repository.invalidate_cache()

            if isinstance(result, Failure):
                self.logger.error(f"Error invalidating cache: {result.error.message}")
                return result

            return result

        # In a real implementation, we would selectively invalidate based on table names
        # This would require parsing queries to identify affected tables
        # For this simplified implementation, invalidate all
        result = await self.cache_repository.invalidate_cache()

        if isinstance(result, Failure):
            self.logger.error(f"Error invalidating cache: {result.error.message}")
            return result

        return result

    async def get_cache_statistics(self) -> UnoResult[Dict[str, Any], ErrorDetails]:
        """
        Get cache statistics.

        Returns:
            Result containing cache statistics
        """
        try:
            # Get cache size
            size_result = await self.cache_repository.get_cache_size()

            if isinstance(size_result, Failure):
                self.logger.error(
                    f"Error getting cache size: {size_result.error.message}"
                )
                return Failure(size_result.error)

            cache_size = size_result.value

            # Calculate hit rate
            hit_rate = 0.0
            if self.total_queries > 0:
                hit_rate = self.hits / self.total_queries

            # Create statistics
            statistics = {
                "hits": self.hits,
                "misses": self.misses,
                "total_queries": self.total_queries,
                "hit_rate": hit_rate,
                "size": cache_size,
                "max_size": self.config.max_size,
                "strategy": self.config.strategy.name,
                "ttl_seconds": self.config.ttl_seconds,
            }

            return Success(statistics)
        except Exception as e:
            self.logger.error(f"Error getting cache statistics: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="CACHE_STATISTICS_ERROR",
                    message=f"Error getting cache statistics: {str(e)}",
                )
            )

    def _determine_query_complexity(self, query: str) -> QueryComplexity:
        """
        Determine the complexity of a query.

        Args:
            query: SQL query

        Returns:
            Query complexity
        """
        lower_query = query.lower()

        # Count joins
        join_count = lower_query.count(" join ")

        # Check for aggregation
        has_aggregation = any(
            keyword in lower_query
            for keyword in [
                "group by",
                "having",
                "count(",
                "sum(",
                "avg(",
                "min(",
                "max(",
            ]
        )

        # Check for window functions
        has_window_functions = "over (" in lower_query or "partition by" in lower_query

        # Check for subqueries
        has_subqueries = "(" in lower_query and "select" in lower_query.split("(")[1]

        # Determine complexity
        if (
            has_window_functions
            or (has_subqueries and has_aggregation)
            or join_count >= 3
        ):
            return QueryComplexity.COMPLEX
        elif has_aggregation or has_subqueries or join_count >= 1:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE


class TransactionService:
    """Service for transaction management."""

    def __init__(
        self,
        transaction_repository: DatabaseTransactionRepositoryProtocol,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the service.

        Args:
            transaction_repository: Database transaction repository
            logger: Optional logger
        """
        self.transaction_repository = transaction_repository
        self.logger = logger or logging.getLogger(__name__)

    async def begin_transaction(
        self, request: TransactionRequest
    ) -> UnoResult[TransactionResponse, ErrorDetails]:
        """
        Begin a new transaction.

        Args:
            request: Transaction request

        Returns:
            Result containing the transaction response
        """
        result = await self.transaction_repository.begin_transaction(
            request.isolation_level, request.read_only
        )

        if isinstance(result, Failure):
            return Failure(result.error)

        transaction = result.value

        return Success(TransactionResponse(success=True, transaction_id=transaction.id))

    async def commit_transaction(
        self, transaction_id: TransactionId
    ) -> UnoResult[TransactionResponse, ErrorDetails]:
        """
        Commit a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            Result containing the transaction response
        """
        result = await self.transaction_repository.commit_transaction(transaction_id)

        if isinstance(result, Failure):
            return Failure(result.error)

        return Success(TransactionResponse(success=True, transaction_id=transaction_id))

    async def rollback_transaction(
        self, transaction_id: TransactionId
    ) -> UnoResult[TransactionResponse, ErrorDetails]:
        """
        Rollback a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            Result containing the transaction response
        """
        result = await self.transaction_repository.rollback_transaction(transaction_id)

        if isinstance(result, Failure):
            return Failure(result.error)

        return Success(TransactionResponse(success=True, transaction_id=transaction_id))

    @asynccontextmanager
    async def transaction_context(
        self,
        isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED,
        read_only: bool = False,
    ) -> AsyncIterator[Transaction]:
        """
        Context manager for transaction management.

        Args:
            isolation_level: Transaction isolation level
            read_only: Whether the transaction is read-only

        Yields:
            A transaction object
        """
        async with self.transaction_repository.transaction(
            isolation_level, read_only
        ) as transaction:
            yield transaction


class ConnectionPoolService:
    """Service for connection pool management."""

    def __init__(
        self,
        pool_config: ConnectionPoolConfig,
        stats_repository: Optional[PoolStatisticsRepositoryProtocol] = None,
        engine_factory: Optional[Any] = None,  # SQLAlchemy engine factory
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the service.

        Args:
            pool_config: Connection pool configuration
            stats_repository: Optional pool statistics repository
            engine_factory: Optional SQLAlchemy engine factory
            logger: Optional logger
        """
        self.pool_config = pool_config
        self.stats_repository = stats_repository
        self.engine_factory = engine_factory
        self.logger = logger or logging.getLogger(__name__)

    async def get_pool_statistics(self) -> UnoResult[PoolStatistics, ErrorDetails]:
        """
        Get current pool statistics.

        Returns:
            Result containing pool statistics
        """
        try:
            if not self.engine_factory or not hasattr(self.engine_factory, "engine"):
                return Failure(
                    ErrorDetails(
                        code="NO_ENGINE", message="No SQLAlchemy engine available"
                    )
                )

            engine = self.engine_factory.engine

            if not hasattr(engine, "pool"):
                return Failure(
                    ErrorDetails(
                        code="NO_POOL", message="Engine does not have a connection pool"
                    )
                )

            pool = engine.pool

            # Create statistics
            stats = PoolStatistics(
                pool_size=pool.size(),
                active_connections=pool._checked_out,
                idle_connections=pool._idle_count,
                max_overflow=self.pool_config.max_overflow,
                overflow_count=max(0, pool._checked_out - pool.size()),
                checked_out=pool._checked_out,
                checkins=getattr(pool, "_checkins", 0),
                checkouts=getattr(pool, "_checkouts", 0),
                connection_errors=getattr(pool, "_connection_errors", 0),
                timeout_errors=getattr(pool, "_timeout_errors", 0),
            )

            # Save statistics if repository available
            if self.stats_repository:
                await self.stats_repository.save_statistics(stats)

            return Success(stats)
        except Exception as e:
            self.logger.error(f"Error getting pool statistics: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="POOL_STATISTICS_ERROR",
                    message=f"Error getting pool statistics: {str(e)}",
                )
            )

    async def get_historical_statistics(
        self, limit: int = 100
    ) -> UnoResult[list[PoolStatistics], ErrorDetails]:
        """
        Get historical pool statistics.

        Args:
            limit: Maximum number of statistics to return

        Returns:
            Result containing historical pool statistics
        """
        if not self.stats_repository:
            return Success([])

        return await self.stats_repository.get_recent_statistics(limit)

    async def optimize_pool_size(self) -> UnoResult[ConnectionPoolConfig, ErrorDetails]:
        """
        Optimize the connection pool size based on usage.

        Returns:
            Result containing the optimized pool configuration
        """
        try:
            # Get historical statistics
            stats_result = await self.get_historical_statistics(100)

            if isinstance(stats_result, Failure):
                return Failure(stats_result.error)

            stats_list = stats_result.value

            if not stats_list:
                return Success(self.pool_config)

            # Calculate peak usage
            peak_usage = max(stat.active_connections for stat in stats_list)

            # Calculate optimal pool size
            optimal_size = int(peak_usage * 1.2)  # 20% buffer

            # Create new configuration
            new_config = ConnectionPoolConfig(
                strategy=self.pool_config.strategy,
                pool_size=optimal_size,
                max_overflow=max(0, int(peak_usage * 0.5)),  # 50% of peak for overflow
                pool_timeout=self.pool_config.pool_timeout,
                pool_recycle=self.pool_config.pool_recycle,
                pool_pre_ping=self.pool_config.pool_pre_ping,
                max_idle_time=self.pool_config.max_idle_time,
                health_check_interval=self.pool_config.health_check_interval,
            )

            return Success(new_config)
        except Exception as e:
            self.logger.error(f"Error optimizing pool size: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="POOL_OPTIMIZATION_ERROR",
                    message=f"Error optimizing pool size: {str(e)}",
                )
            )

    async def reset_pool(self) -> UnoResult[None, ErrorDetails]:
        """
        Reset the connection pool.

        Returns:
            Result indicating success
        """
        try:
            if not self.engine_factory or not hasattr(self.engine_factory, "engine"):
                return Failure(
                    ErrorDetails(
                        code="NO_ENGINE", message="No SQLAlchemy engine available"
                    )
                )

            engine = self.engine_factory.engine

            if not hasattr(engine, "pool") or not hasattr(engine.pool, "dispose"):
                return Failure(
                    ErrorDetails(
                        code="NO_POOL",
                        message="Engine does not have a connection pool or pool cannot be disposed",
                    )
                )

            # Dispose the pool
            await engine.dispose()

            self.logger.info("Connection pool has been reset")
            return Success(None)
        except Exception as e:
            self.logger.error(f"Error resetting pool: {str(e)}")
            return Failure(
                ErrorDetails(
                    code="POOL_RESET_ERROR", message=f"Error resetting pool: {str(e)}"
                )
            )
