"""
Batch operations for common database patterns.

This module provides high-performance batch operations for common database patterns,
optimized for PostgreSQL's batch processing capabilities.
"""

from typing import (
    TypeVar,
    Generic,
    List,
    Dict,
    Any,
    Optional,
    Union,
    Tuple,
    Type,
    Callable,
    Sequence,
)
import asyncio
import logging
import time
import json
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
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Temporarily comment out core caching imports while we fix circular dependencies
# from uno.core.caching import (
#     generate_cache_key,
#     get_cache_manager,
#     query_cached,
# )
from uno.database.enhanced_session import enhanced_async_session
from uno.database.pooled_session import pooled_async_session
from uno.database.streaming import stream_query, StreamingMode
from uno.domain.base.model import BaseModel as Model
from uno.queries.optimized_queries import OptimizedModelQuery, QueryHints
from uno.queries.common_patterns import CommonQueryPatterns, QueryPattern


T = TypeVar("T", bound=Model)


class BatchSize(Enum):
    """
    Predefined batch sizes for different operations.

    These sizes are optimized based on PostgreSQL performance characteristics
    for different types of operations.
    """

    SMALL = 100  # For complex record operations (e.g., with many relations)
    MEDIUM = 500  # Default for most operations
    LARGE = 1000  # For simple record operations
    XLARGE = 5000  # For very simple operations with minimal overhead


class BatchExecutionStrategy(Enum):
    """
    Strategies for executing batch operations.
    """

    SINGLE_QUERY = "single_query"  # Execute as a single query with all records
    CHUNKED = "chunked"  # Execute in chunks of specified size
    PARALLEL = "parallel"  # Execute chunks in parallel
    PIPELINED = "pipelined"  # Execute in a pipeline with preprocessing
    OPTIMISTIC = "optimistic"  # Try single query first, fall back to chunked if failed


@dataclass
class BatchConfig:
    """
    Configuration for batch operations.

    This controls how batch operations are executed and optimized.
    """

    batch_size: int = BatchSize.MEDIUM.value
    max_workers: int = 4
    collect_metrics: bool = False
    log_progress: bool = False
    timeout: Optional[float] = None
    retry_count: int = 3
    retry_delay: float = 0.5
    execution_strategy: BatchExecutionStrategy = BatchExecutionStrategy.CHUNKED
    pre_process_fn: Optional[Callable] = None
    post_process_fn: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    optimize_for_size: bool = (
        True  # Automatically adjust batch size based on record size
    )


@dataclass
class BatchMetrics:
    """
    Metrics for batch operations.
    """

    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    chunks_processed: int = 0
    retries: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def elapsed_time(self) -> float:
        """Total elapsed time in seconds."""
        if self.end_time == 0:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def records_per_second(self) -> float:
        """Records processed per second."""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0
        return self.processed_records / elapsed


class BatchProcessor:
    """
    Core batch processing engine.

    This class provides the foundation for all batch operations,
    handling chunking, parallel execution, retries, and metrics.
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        config: Optional[BatchConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the batch processor.

        Args:
            session: Database session to use
            config: Batch configuration
            logger: Logger instance
        """
        self.session = session
        self.config = config or BatchConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.metrics = BatchMetrics()

    async def process_batch(
        self, records: Sequence[Any], operation_fn: Callable, **kwargs
    ) -> Tuple[List[Any], BatchMetrics]:
        """
        Process a batch of records.

        Args:
            records: Records to process
            operation_fn: Function to process each chunk
            **kwargs: Additional arguments to pass to operation_fn

        Returns:
            Tuple of (results, metrics)
        """
        # Start metrics
        self.metrics = BatchMetrics()
        self.metrics.start_time = time.time()
        self.metrics.total_records = len(records)

        # If no records, return empty results
        if not records:
            self.metrics.end_time = time.time()
            return [], self.metrics

        # Optimize batch size if needed
        batch_size = self._get_optimal_batch_size(records)

        # Determine execution strategy
        strategy = self.config.execution_strategy

        # Apply pre-processing if configured
        if self.config.pre_process_fn:
            records = self.config.pre_process_fn(records)

        # Execute based on strategy
        results = []

        if strategy == BatchExecutionStrategy.SINGLE_QUERY:
            results = await self._execute_single_query(records, operation_fn, **kwargs)

        elif strategy == BatchExecutionStrategy.CHUNKED:
            results = await self._execute_chunked(
                records, operation_fn, batch_size, **kwargs
            )

        elif strategy == BatchExecutionStrategy.PARALLEL:
            results = await self._execute_parallel(
                records, operation_fn, batch_size, **kwargs
            )

        elif strategy == BatchExecutionStrategy.PIPELINED:
            results = await self._execute_pipelined(
                records, operation_fn, batch_size, **kwargs
            )

        elif strategy == BatchExecutionStrategy.OPTIMISTIC:
            try:
                # Try single query first
                results = await self._execute_single_query(
                    records, operation_fn, **kwargs
                )
            except Exception as e:
                self.logger.warning(
                    f"Single query execution failed: {e}. Falling back to chunked execution."
                )
                # Fall back to chunked
                results = await self._execute_chunked(
                    records, operation_fn, batch_size, **kwargs
                )

        # Apply post-processing if configured
        if self.config.post_process_fn:
            results = self.config.post_process_fn(results)

        # Finalize metrics
        self.metrics.end_time = time.time()
        self.metrics.successful_records = len(results)

        return results, self.metrics

    def _get_optimal_batch_size(self, records: Sequence[Any]) -> int:
        """
        Determine the optimal batch size based on record characteristics.

        Args:
            records: Sample of records to analyze

        Returns:
            Optimal batch size
        """
        if not self.config.optimize_for_size:
            return self.config.batch_size

        # Sample a few records to estimate size
        sample_size = min(10, len(records))
        sample = records[:sample_size]

        try:
            # Estimate average record size in bytes
            avg_size = sum(len(json.dumps(r)) for r in sample) / sample_size

            # Adjust batch size based on record size
            if avg_size > 10000:  # Very large records
                return min(BatchSize.SMALL.value, self.config.batch_size)
            elif avg_size > 5000:  # Large records
                return min(BatchSize.MEDIUM.value, self.config.batch_size)
            elif avg_size > 1000:  # Medium records
                return min(BatchSize.LARGE.value, self.config.batch_size)
            else:  # Small records
                return min(BatchSize.XLARGE.value, self.config.batch_size)
        except Exception:
            # If estimation fails, use configured batch size
            return self.config.batch_size

    async def _execute_single_query(
        self, records: Sequence[Any], operation_fn: Callable, **kwargs
    ) -> List[Any]:
        """
        Execute operation as a single query.

        Args:
            records: Records to process
            operation_fn: Operation function
            **kwargs: Additional arguments for operation_fn

        Returns:
            Operation results
        """
        try:
            # Execute operation with all records
            results = await operation_fn(records, **kwargs)

            # Update metrics
            self.metrics.processed_records = len(records)
            self.metrics.chunks_processed = 1

            return results
        except Exception as e:
            # Handle error
            error_info = {
                "error": str(e),
                "record_count": len(records),
                "context": "single_query_execution",
            }
            self.metrics.errors.append(error_info)

            if self.config.error_callback:
                self.config.error_callback(e, error_info)

            # Re-raise the exception
            raise

    async def _execute_chunked(
        self, records: Sequence[Any], operation_fn: Callable, batch_size: int, **kwargs
    ) -> List[Any]:
        """
        Execute operation in chunks.

        Args:
            records: Records to process
            operation_fn: Operation function
            batch_size: Size of each chunk
            **kwargs: Additional arguments for operation_fn

        Returns:
            Combined operation results
        """
        results = []
        record_count = len(records)

        # Process in chunks
        for i in range(0, record_count, batch_size):
            chunk = records[i : i + batch_size]
            chunk_size = len(chunk)
            retry_count = 0

            while retry_count <= self.config.retry_count:
                try:
                    # Log progress if enabled
                    if self.config.log_progress:
                        processed = i + chunk_size
                        progress = processed / record_count * 100
                        self.logger.info(
                            f"Processing {processed}/{record_count} records ({progress:.1f}%)"
                        )

                    # Execute operation for this chunk
                    chunk_results = await operation_fn(chunk, **kwargs)
                    results.extend(chunk_results)

                    # Update metrics
                    self.metrics.processed_records += chunk_size
                    self.metrics.chunks_processed += 1

                    # Break retry loop on success
                    break

                except Exception as e:
                    retry_count += 1
                    self.metrics.retries += 1

                    # Add error to metrics
                    error_info = {
                        "error": str(e),
                        "chunk_index": i,
                        "chunk_size": chunk_size,
                        "retry": retry_count,
                    }
                    self.metrics.errors.append(error_info)

                    # Call error callback if configured
                    if self.config.error_callback:
                        self.config.error_callback(e, error_info)

                    # Log the error
                    self.logger.warning(
                        f"Error processing chunk {i}:{i+chunk_size} (retry {retry_count}/{self.config.retry_count}): {e}"
                    )

                    # If we've exhausted retries, re-raise the exception
                    if retry_count > self.config.retry_count:
                        raise

                    # Wait before retrying
                    await asyncio.sleep(self.config.retry_delay)

        return results

    async def _execute_parallel(
        self, records: Sequence[Any], operation_fn: Callable, batch_size: int, **kwargs
    ) -> List[Any]:
        """
        Execute operation in parallel chunks.

        Args:
            records: Records to process
            operation_fn: Operation function
            batch_size: Size of each chunk
            **kwargs: Additional arguments for operation_fn

        Returns:
            Combined operation results
        """
        results = []
        record_count = len(records)
        chunks = [
            records[i : i + batch_size] for i in range(0, record_count, batch_size)
        ]

        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.config.max_workers)

        async def process_chunk(chunk_idx, chunk):
            """Process a single chunk with retry logic."""
            async with semaphore:
                chunk_size = len(chunk)
                retry_count = 0

                while retry_count <= self.config.retry_count:
                    try:
                        # Log progress if enabled
                        if self.config.log_progress:
                            start_idx = chunk_idx * batch_size
                            processed = start_idx + chunk_size
                            progress = processed / record_count * 100
                            self.logger.info(
                                f"Processing {processed}/{record_count} records ({progress:.1f}%)"
                            )

                        # Execute operation for this chunk
                        chunk_results = await operation_fn(chunk, **kwargs)

                        # Update metrics
                        self.metrics.processed_records += chunk_size
                        self.metrics.chunks_processed += 1

                        return chunk_results

                    except Exception as e:
                        retry_count += 1
                        self.metrics.retries += 1

                        # Add error to metrics
                        error_info = {
                            "error": str(e),
                            "chunk_index": chunk_idx,
                            "chunk_size": chunk_size,
                            "retry": retry_count,
                        }
                        self.metrics.errors.append(error_info)

                        # Call error callback if configured
                        if self.config.error_callback:
                            self.config.error_callback(e, error_info)

                        # Log the error
                        self.logger.warning(
                            f"Error processing chunk {chunk_idx} (retry {retry_count}/{self.config.retry_count}): {e}"
                        )

                        # If we've exhausted retries, re-raise the exception
                        if retry_count > self.config.retry_count:
                            raise

                        # Wait before retrying
                        await asyncio.sleep(self.config.retry_delay)

        # Process all chunks in parallel
        tasks = []
        for i, chunk in enumerate(chunks):
            task = asyncio.create_task(process_chunk(i, chunk))
            tasks.append(task)

        # Wait for all tasks to complete
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results, handling any exceptions
        for result in chunk_results:
            if isinstance(result, Exception):
                # Log the exception but continue processing
                self.logger.error(
                    f"Unhandled exception in parallel execution: {result}"
                )
                self.metrics.failed_records += batch_size
            else:
                # Add successful results
                results.extend(result)

        return results

    async def _execute_pipelined(
        self, records: Sequence[Any], operation_fn: Callable, batch_size: int, **kwargs
    ) -> List[Any]:
        """
        Execute operation in a pipeline.

        This processes records in stages:
        1. Preprocessing (eg. validation, enrichment)
        2. Execution in batches
        3. Postprocessing

        Args:
            records: Records to process
            operation_fn: Operation function
            batch_size: Size of each execution batch
            **kwargs: Additional arguments for operation_fn

        Returns:
            Combined operation results
        """
        # Pipeline configuration
        pipeline_config = kwargs.pop("pipeline_config", {})
        preprocess_fn = pipeline_config.get("preprocess_fn")
        postprocess_fn = pipeline_config.get("postprocess_fn")
        filter_fn = pipeline_config.get("filter_fn")

        # Initialize pipeline stages
        record_count = len(records)
        preprocessed_records = []

        # Stage 1: Preprocessing
        if preprocess_fn:
            for record in records:
                try:
                    processed = await preprocess_fn(record)
                    if processed is not None:
                        preprocessed_records.append(processed)
                except Exception as e:
                    self.logger.warning(f"Error preprocessing record: {e}")
                    # Track error
                    self.metrics.errors.append(
                        {"error": str(e), "stage": "preprocessing", "record": record}
                    )
        else:
            preprocessed_records = list(records)

        # Apply filtering if provided
        if filter_fn:
            preprocessed_records = [r for r in preprocessed_records if filter_fn(r)]

        # Stage 2: Batch execution
        # Use chunked execution for the actual operation
        execution_results = await self._execute_chunked(
            preprocessed_records, operation_fn, batch_size, **kwargs
        )

        # Stage 3: Postprocessing
        final_results = []
        if postprocess_fn:
            for result in execution_results:
                try:
                    processed = await postprocess_fn(result)
                    if processed is not None:
                        final_results.append(processed)
                except Exception as e:
                    self.logger.warning(f"Error postprocessing result: {e}")
                    # Track error
                    self.metrics.errors.append(
                        {"error": str(e), "stage": "postprocessing", "result": result}
                    )
        else:
            final_results = execution_results

        return final_results


class BatchOperations(Generic[T]):
    """
    High-performance batch operations for database entities.

    This class extends CommonQueryPatterns with optimized implementations
    of batch operations, taking advantage of PostgreSQL's efficient batch processing
    capabilities.
    """

    def __init__(
        self,
        model_class: Type[T],
        session: Optional[AsyncSession] = None,
        use_cache: bool = True,
        cache_ttl: Optional[float] = 60.0,
        collect_metrics: bool = False,
        logger: Optional[logging.Logger] = None,
        batch_config: Optional[BatchConfig] = None,
    ):
        """
        Initialize batch operations.

        Args:
            model_class: Model class
            session: Database session
            use_cache: Whether to use caching
            cache_ttl: Cache TTL in seconds
            collect_metrics: Whether to collect metrics
            logger: Logger instance
            batch_config: Batch processing configuration
        """
        self.model_class = model_class
        self.session = session
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.collect_metrics = collect_metrics
        self.logger = logger or logging.getLogger(__name__)

        # Create common query patterns
        self.query_patterns = CommonQueryPatterns(
            model_class=model_class,
            session=session,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
            collect_metrics=collect_metrics,
            logger=logger,
        )

        # Create optimized query builder
        self.query_builder = OptimizedModelQuery(
            model_class=model_class,
            session=session,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
            logger=logger,
        )

        # Create batch processor
        self.batch_processor = BatchProcessor(
            session=session,
            config=batch_config or BatchConfig(),
            logger=logger,
        )

    async def batch_get(
        self,
        id_values: List[Any],
        load_relations: Optional[Union[bool, List[str]]] = None,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> List[T]:
        """
        Get multiple entities by ID in batch.

        Args:
            id_values: List of IDs to retrieve
            load_relations: Relationships to load
            batch_size: Size of each batch
            parallel: Whether to execute in parallel

        Returns:
            List of entities
        """
        # If no IDs, return empty list
        if not id_values:
            return []

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Define operation function for the batch processor
        async def operation_fn(batch_ids, **kwargs):
            return await self.query_patterns.get_by_ids(
                batch_ids, load_relations=load_relations
            )

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            id_values, operation_fn
        )

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch get metrics: {metrics.__dict__}")

        return results

    async def batch_insert(
        self,
        records: List[Dict[str, Any]],
        return_models: bool = False,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> Union[int, List[T]]:
        """
        Insert multiple records in batch.

        Args:
            records: Records to insert
            return_models: Whether to return the inserted models
            batch_size: Size of each batch
            parallel: Whether to execute in parallel

        Returns:
            Number of inserted records or list of inserted models
        """
        # If no records, return empty result
        if not records:
            return [] if return_models else 0

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Define operation function for the batch processor
        async def operation_fn(batch_records, **kwargs):
            return await self.query_builder.bulk_insert(
                batch_records, return_models=return_models
            )

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            records, operation_fn
        )

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch insert metrics: {metrics.__dict__}")

        # Return models or count based on return_models flag
        if return_models:
            return results

        return metrics.processed_records

    async def batch_update(
        self,
        records: List[Dict[str, Any]],
        id_field: str = "id",
        fields_to_update: Optional[List[str]] = None,
        return_models: bool = False,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> Union[int, List[T]]:
        """
        Update multiple records in batch.

        Args:
            records: Records to update (must include id_field)
            id_field: Field to use as ID
            fields_to_update: Fields to update (if None, update all fields except ID)
            return_models: Whether to return the updated models
            batch_size: Size of each batch
            parallel: Whether to execute in parallel

        Returns:
            Number of updated records or list of updated models
        """
        # If no records, return empty result
        if not records:
            return [] if return_models else 0

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Define operation function for the batch processor
        async def operation_fn(batch_records, **kwargs):
            updates = []

            for record in batch_records:
                # Get ID
                id_value = record.get(id_field)
                if not id_value:
                    continue

                # Create update values
                update_values = {}

                if fields_to_update:
                    # Only update specified fields
                    for field in fields_to_update:
                        if field in record and field != id_field:
                            update_values[field] = record[field]
                else:
                    # Update all fields except ID
                    for field, value in record.items():
                        if field != id_field:
                            update_values[field] = value

                # Execute update
                result = await self.query_patterns.batch_update(
                    id_values=[id_value],
                    field_values=update_values,
                    return_models=return_models,
                )

                # Add to results
                if return_models and isinstance(result, list):
                    updates.extend(result)
                elif not return_models:
                    updates.append(result)

            return updates

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            records, operation_fn
        )

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch update metrics: {metrics.__dict__}")

        # Return models or count based on return_models flag
        if return_models:
            return results

        return sum(results)

    async def batch_upsert(
        self,
        records: List[Dict[str, Any]],
        constraint_columns: List[str],
        update_columns: Optional[List[str]] = None,
        return_models: bool = False,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> Union[int, List[T]]:
        """
        Upsert multiple records in batch.

        Args:
            records: Records to upsert
            constraint_columns: Columns for the constraint
            update_columns: Columns to update on conflict
            return_models: Whether to return the upserted models
            batch_size: Size of each batch
            parallel: Whether to execute in parallel

        Returns:
            Number of upserted records or list of upserted models
        """
        # If no records, return empty result
        if not records:
            return [] if return_models else 0

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Define operation function for the batch processor
        async def operation_fn(batch_records, **kwargs):
            return await self.query_patterns.batch_upsert(
                records=batch_records,
                constraint_columns=constraint_columns,
                update_columns=update_columns,
                return_models=return_models,
            )

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            records, operation_fn
        )

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch upsert metrics: {metrics.__dict__}")

        # Return models or count based on return_models flag
        if return_models:
            return results

        return metrics.processed_records

    async def batch_delete(
        self,
        id_values: List[Any],
        return_models: bool = False,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> Union[int, List[T]]:
        """
        Delete multiple records in batch.

        Args:
            id_values: IDs of records to delete
            return_models: Whether to return the deleted models
            batch_size: Size of each batch
            parallel: Whether to execute in parallel

        Returns:
            Number of deleted records or list of deleted models
        """
        # If no IDs, return empty result
        if not id_values:
            return [] if return_models else 0

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Define operation function for the batch processor
        async def operation_fn(batch_ids, **kwargs):
            return await self.query_patterns.batch_delete(
                id_values=batch_ids, return_models=return_models
            )

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            id_values, operation_fn
        )

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch delete metrics: {metrics.__dict__}")

        # Return models or count based on return_models flag
        if return_models:
            return results

        return metrics.processed_records

    async def batch_compute(
        self,
        id_values: List[Any],
        compute_fn: Callable[[T], Any],
        load_relations: Optional[Union[bool, List[str]]] = None,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> List[Any]:
        """
        Compute a function across multiple records in batch.

        Args:
            id_values: IDs of records to process
            compute_fn: Function to compute for each record
            load_relations: Relationships to load
            batch_size: Size of each batch
            parallel: Whether to execute in parallel

        Returns:
            List of computed results
        """
        # If no IDs, return empty result
        if not id_values:
            return []

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Define operation function for the batch processor
        async def operation_fn(batch_ids, **kwargs):
            # Get entities for this batch
            entities = await self.query_patterns.get_by_ids(
                batch_ids, load_relations=load_relations
            )

            # Apply compute function to each entity
            results = []
            for entity in entities:
                result = compute_fn(entity)
                results.append(result)

            return results

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            id_values, operation_fn
        )

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch compute metrics: {metrics.__dict__}")

        return results

    async def batch_execute_sql(
        self,
        sql_template: str,
        parameters: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> List[Any]:
        """
        Execute raw SQL for multiple parameter sets in batch.

        Args:
            sql_template: SQL template with parameter placeholders
            parameters: List of parameter dictionaries
            batch_size: Size of each batch
            parallel: Whether to execute in parallel

        Returns:
            List of results
        """
        # If no parameters, return empty result
        if not parameters:
            return []

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Define operation function for the batch processor
        async def operation_fn(batch_params, **kwargs):
            # Use session or create one
            session_provided = self.session is not None

            if not session_provided:
                session_context = pooled_async_session()
                session = await session_context.__aenter__()
            else:
                session = self.session

            try:
                # For a small number of parameters, execute individually
                if len(batch_params) <= 10:
                    results = []
                    for params in batch_params:
                        # Execute SQL
                        result = await session.execute(text(sql_template), params)
                        rows = result.fetchall()
                        results.extend(rows)
                    return results

                # For larger batches, use more efficient methods
                # Construct a bulk query with all parameters
                placeholders = []
                all_params = {}

                for i, params in enumerate(batch_params):
                    # Create placeholders for this parameter set
                    param_placeholders = []
                    for key, value in params.items():
                        param_key = f"{key}_{i}"
                        all_params[param_key] = value
                        param_placeholders.append(f":{param_key}")

                    # Add to placeholder list
                    placeholders.append(f"({', '.join(param_placeholders)})")

                # Replace the first placeholder in the template with our bulk placeholders
                bulk_sql = sql_template.replace(
                    "(?)", f"VALUES {', '.join(placeholders)}", 1
                )

                # Execute the bulk query
                result = await session.execute(text(bulk_sql), all_params)
                return result.fetchall()

            finally:
                # Close session if we created it
                if not session_provided:
                    await session_context.__aexit__(None, None, None)

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            parameters, operation_fn
        )

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch SQL metrics: {metrics.__dict__}")

        return results

    async def batch_import(
        self,
        records: List[Dict[str, Any]],
        unique_fields: List[str],
        update_on_conflict: bool = True,
        return_stats: bool = True,
        batch_size: Optional[int] = None,
        parallel: bool = False,
        pre_process_fn: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Import data in batch with duplicate handling.

        Args:
            records: Records to import
            unique_fields: Fields that determine uniqueness
            update_on_conflict: Whether to update on conflict
            return_stats: Whether to return statistics
            batch_size: Size of each batch
            parallel: Whether to execute in parallel
            pre_process_fn: Function to preprocess records

        Returns:
            Import statistics
        """
        # If no records, return empty stats
        if not records:
            return {
                "total": 0,
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
                "errors": 0,
                "elapsed_time": 0,
            }

        # Configure batch processing
        batch_config = self.batch_processor.config
        if batch_size:
            batch_config.batch_size = batch_size

        if parallel:
            batch_config.execution_strategy = BatchExecutionStrategy.PARALLEL
        else:
            batch_config.execution_strategy = BatchExecutionStrategy.CHUNKED

        # Preprocess records if needed
        if pre_process_fn:
            processed_records = []
            for record in records:
                try:
                    processed = pre_process_fn(record)
                    if processed:
                        processed_records.append(processed)
                except Exception as e:
                    self.logger.warning(f"Error preprocessing record: {e}")
            records = processed_records

        # Track statistics
        start_time = time.time()
        stats = {
            "total": len(records),
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

        # Define operation function for the batch processor
        async def operation_fn(batch_records, **kwargs):
            if update_on_conflict:
                # Use upsert
                update_columns = None  # Update all columns

                # Perform upsert
                result = await self.query_patterns.batch_upsert(
                    records=batch_records,
                    constraint_columns=unique_fields,
                    update_columns=update_columns,
                    return_models=False,
                )

                # Update stats
                stats["inserted"] += result

                return batch_records
            else:
                # Check for existing records
                existing_ids = set()

                # For each unique field combination, check if it exists
                for record in batch_records:
                    # Build filter condition
                    filter_cond = {
                        field: record.get(field)
                        for field in unique_fields
                        if field in record
                    }

                    # Skip if missing any unique fields
                    if len(filter_cond) != len(unique_fields):
                        stats["skipped"] += 1
                        continue

                    # Check if exists
                    existing = await self.query_patterns.find_by_fields(
                        filter_cond, limit=1
                    )
                    if existing:
                        existing_ids.add(
                            tuple(record.get(field) for field in unique_fields)
                        )
                        stats["skipped"] += 1

                # Filter out existing records
                new_records = [
                    record
                    for record in batch_records
                    if tuple(record.get(field) for field in unique_fields)
                    not in existing_ids
                ]

                # Insert new records
                if new_records:
                    result = await self.query_patterns.batch_insert(
                        new_records, return_models=False
                    )
                    stats["inserted"] += result

                return new_records

        # Process the batch
        results, metrics = await self.batch_processor.process_batch(
            records, operation_fn
        )

        # Finalize stats
        stats["elapsed_time"] = time.time() - start_time
        stats["errors"] = len(metrics.errors)

        # Log metrics if collecting
        if self.collect_metrics:
            self.logger.debug(f"Batch import metrics: {metrics.__dict__}")

        if return_stats:
            return stats

        return results

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from all batch operations.

        Returns:
            Dictionary of metrics
        """
        if not self.collect_metrics:
            return {"error": "Metrics collection is disabled"}

        # Combine metrics from query patterns and batch processor
        metrics = {
            "query_patterns": await self.query_patterns.get_metrics(),
            "last_batch": self.batch_processor.metrics.__dict__,
        }

        return metrics
