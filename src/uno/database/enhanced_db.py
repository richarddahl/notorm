"""
Enhanced async database operations with improved async patterns.

This module extends the base database operations with:
- Improved cancellation handling
- Structured concurrency for database operations
- Connection pooling with automatic retries
- Resource cleanup on task cancellation
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast, Callable, Awaitable
import logging
import asyncio
import contextlib
from uno.database.errors import (
    DatabaseTransactionError,
    DatabaseTransactionConflictError,
    DatabaseConnectionError,
    DatabaseQueryTimeoutError,
)

from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.enhanced_session import (
    EnhancedAsyncSessionFactory,
    enhanced_async_session,
    SessionOperationGroup,
)
from uno.core.async_integration import (
    cancellable,
    timeout_handler,
    retry,
    AsyncBatcher,
    AsyncCache,
)
from uno.core.async_utils import TaskGroup, timeout
from uno.database.pg_error_handler import (
    with_pg_error_handling,
    is_deadlock_error,
    is_transient_error,
    get_retry_delay_for_error,
)
from uno.model import UnoModel

T = TypeVar('T', bound=UnoModel)
R = TypeVar('R')


class EnhancedUnoDb:
    """
    Enhanced async database operations with improved async patterns.
    
    This class extends UnoDb with:
    - Improved cancellation handling
    - Automatic retries for transient errors
    - Batching for bulk operations
    - Caching for frequent queries
    """
    
    def __init__(
        self,
        session_factory: Optional[EnhancedAsyncSessionFactory] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enhanced database operations.
        
        Args:
            session_factory: Optional enhanced session factory
            logger: Optional logger instance
        """
        super().__init__(session_factory=session_factory, logger=logger)
        
        # Cache for frequently accessed data
        self.query_cache = AsyncCache[str, Any](
            ttl=60.0,  # 1 minute cache TTL
            refresh_before_expiry=10.0,  # Refresh 10 seconds before expiry
            max_size=1000,  # Maximum cache size
            logger=logger,
        )
        
        # Batchers for different operation types
        self.insert_batcher = AsyncBatcher[Dict[str, Any], Dict[str, Any]](
            batch_operation=self._batch_insert,
            max_batch_size=100,
            max_wait_time=0.05,
            logger=logger,
        )
        
        self.update_batcher = AsyncBatcher[Dict[str, Any], bool](
            batch_operation=self._batch_update,
            max_batch_size=50,
            max_wait_time=0.05,
            logger=logger,
        )
    
    @cancellable
    @retry(
        max_attempts=3, 
        retry_exceptions=lambda ex: is_transient_error(ex) or isinstance(ex, asyncio.TimeoutError),
        retry_delay_factory=lambda ex, attempt: get_retry_delay_for_error(ex) * attempt
    )
    @timeout_handler(timeout_seconds=30.0, timeout_message="Database operation timed out")
    @with_pg_error_handling(error_message="Failed to retrieve database record")
    async def get(
        self,
        model_class: Type[T],
        id: str,
        use_cache: bool = False,
    ) -> Optional[T]:
        """
        Get a model instance by ID with enhanced async handling.
        
        Args:
            model_class: The model class
            id: The primary key ID
            use_cache: Whether to use caching
            
        Returns:
            The model instance or None if not found
        """
        if use_cache:
            # Create cache key
            cache_key = f"get:{model_class.__name__}:{id}"
            
            # Get from cache or fetch
            return await self.query_cache.get(
                key=cache_key,
                fetch_func=lambda _: self._fetch_model(model_class, id),
            )
        else:
            return await self._fetch_model(model_class, id)
    
    async def _fetch_model(self, model_class: Type[T], id: str) -> Optional[T]:
        """
        Fetch a model from the database.
        
        Args:
            model_class: The model class
            id: The primary key ID
            
        Returns:
            The model instance or None if not found
        """
        # Get primary key column
        pk_col = model_class.__table__.primary_key.columns.values()[0]
        
        async with enhanced_async_session() as session:
            # Build and execute query
            query = select(model_class).where(pk_col == id)
            result = await session.execute(query)
            return result.scalars().first()
            
    @cancellable
    @retry(
        max_attempts=3, 
        retry_exceptions=lambda ex: is_deadlock_error(ex),
        retry_delay_factory=lambda ex, attempt: get_retry_delay_for_error(ex) * attempt
    )
    @with_pg_error_handling(error_message="Error during transaction execution")
    async def execute_transaction(
        self, 
        operations: Callable[[AsyncSession], Awaitable[T]],
        isolation_level: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> T:
        """
        Execute a series of operations in a transaction with proper error handling.
        
        Args:
            operations: A callable that takes a session and returns a coroutine
            isolation_level: Optional isolation level for the transaction
                ("READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE")
            timeout_seconds: Optional timeout in seconds for the transaction
            
        Returns:
            The result of the operations
            
        Raises:
            DatabaseTransactionError: If the transaction fails
            DatabaseTransactionConflictError: If there is a deadlock or serialization failure
            DatabaseConnectionError: If there is a connection error
            DatabaseQueryTimeoutError: If the transaction times out
        """
        async with enhanced_async_session(factory=self.session_factory) as session:
            # Set isolation level if provided
            if isolation_level:
                await session.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
                
            # Set statement timeout if provided
            if timeout_seconds:
                timeout_ms = int(timeout_seconds * 1000)
                await session.execute(f"SET LOCAL statement_timeout = {timeout_ms}")
            
            # Use the timeout context manager if provided
            timeout_ctx = timeout(timeout_seconds) if timeout_seconds else contextlib.nullcontext()
            async with timeout_ctx:
                try:
                    # Start a new transaction
                    async with session.begin():
                        result = await operations(session)
                        return result
                except asyncio.TimeoutError:
                    # Handle asyncio timeout separately
                    self.logger.error(f"Transaction timed out after {timeout_seconds} seconds")
                    raise DatabaseQueryTimeoutError(
                        timeout_seconds=timeout_seconds,
                        message=f"Transaction timed out after {timeout_seconds} seconds"
                    )
                    
    @cancellable
    @retry(
        max_attempts=3, 
        retry_exceptions=lambda ex: is_deadlock_error(ex),
        retry_delay_factory=lambda ex, attempt: get_retry_delay_for_error(ex) * attempt
    )
    @with_pg_error_handling(error_message="Error during serializable transaction execution")
    async def execute_serializable_transaction(
        self, 
        operations: Callable[[AsyncSession], Awaitable[T]],
        timeout_seconds: Optional[float] = None,
        retry_attempts: int = 3,
    ) -> T:
        """
        Execute a series of operations in a serializable transaction.
        
        This method uses PostgreSQL's SERIALIZABLE isolation level, which provides
        the strictest transaction isolation. If a serialization failure occurs,
        it will automatically retry up to retry_attempts times.
        
        Args:
            operations: A callable that takes a session and returns a coroutine
            timeout_seconds: Optional timeout in seconds for the transaction
            retry_attempts: Number of retry attempts for serialization failures
            
        Returns:
            The result of the operations
            
        Raises:
            DatabaseTransactionError: If the transaction fails
            DatabaseTransactionConflictError: If there is a deadlock or serialization failure
            DatabaseConnectionError: If there is a connection error
            DatabaseQueryTimeoutError: If the transaction times out
        """
        return await self.execute_transaction(
            operations=operations,
            isolation_level="SERIALIZABLE",
            timeout_seconds=timeout_seconds,
        )
    
    @cancellable
    @retry(max_attempts=3, retry_exceptions=[asyncio.TimeoutError])
    @timeout_handler(timeout_seconds=30.0, timeout_message="Database operation timed out")
    async def filter(
        self,
        model_class: Type[T],
        criteria: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List[Any]] = None,
        use_cache: bool = False,
    ) -> List[T]:
        """
        Filter models by criteria with enhanced async handling.
        
        Args:
            model_class: The model class
            criteria: Filter criteria
            limit: Optional result limit
            offset: Optional result offset
            order_by: Optional ordering
            use_cache: Whether to use caching
            
        Returns:
            List of model instances matching the criteria
        """
        if use_cache and limit is not None and offset is not None:
            # Create cache key
            cache_key = (
                f"filter:{model_class.__name__}:"
                f"{repr(criteria)}:{limit}:{offset}:{repr(order_by)}"
            )
            
            # Get from cache or fetch
            return await self.query_cache.get(
                key=cache_key,
                fetch_func=lambda _: self._fetch_filtered_models(
                    model_class, criteria, limit, offset, order_by
                ),
            )
        else:
            return await self._fetch_filtered_models(
                model_class, criteria, limit, offset, order_by
            )
    
    async def _fetch_filtered_models(
        self,
        model_class: Type[T],
        criteria: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List[Any]] = None,
    ) -> List[T]:
        """
        Fetch filtered models from the database.
        
        Args:
            model_class: The model class
            criteria: Filter criteria
            limit: Optional result limit
            offset: Optional result offset
            order_by: Optional ordering
            
        Returns:
            List of model instances matching the criteria
        """
        async with enhanced_async_session() as session:
            # Build query
            query = select(model_class)
            
            # Apply filter criteria
            for key, value in criteria.items():
                column = getattr(model_class, key)
                query = query.where(column == value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(*order_by)
            
            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            
            # Execute query
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def batch_insert(
        self,
        model_class: Type[T],
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add a model to a batch insert operation.
        
        Args:
            model_class: The model class
            data: Model data
            
        Returns:
            The inserted data with generated values
        """
        # Add model class information to the data
        data_with_model = {
            "model_class": model_class.__name__,
            "table_name": model_class.__tablename__,
            "data": data,
        }
        
        # Add to batch and get result
        return await self.insert_batcher.add_item(data_with_model)
    
    async def _batch_insert(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of insert operations.
        
        Args:
            items: List of items to insert
            
        Returns:
            List of inserted items with generated values
        """
        # Group items by model class
        grouped_items: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            model_name = item["model_class"]
            if model_name not in grouped_items:
                grouped_items[model_name] = []
            grouped_items[model_name].append(item["data"])
        
        results = []
        
        # Process each group in a separate transaction
        async with SessionOperationGroup() as op_group:
            session = await op_group.create_session()
            
            async with session.begin():
                for model_name, model_items in grouped_items.items():
                    # Get model class
                    model_class = self._get_model_class_by_name(model_name)
                    
                    # Prepare insert statement
                    stmt = insert(model_class).values(model_items)
                    
                    # Add returning clause for PostgreSQL
                    stmt = stmt.returning(model_class)
                    
                    # Execute statement
                    result = await session.execute(stmt)
                    
                    # Get returned rows
                    inserted_rows = result.fetchall()
                    
                    # Convert to dictionaries
                    for i, row in enumerate(inserted_rows):
                        model_dict = row[0].__dict__
                        # Remove SQLAlchemy internal attributes
                        model_dict = {
                            k: v for k, v in model_dict.items()
                            if not k.startswith("_")
                        }
                        results.append(model_dict)
        
        return results
    
    async def batch_update(
        self,
        model_class: Type[T],
        id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Add a model update to a batch operation.
        
        Args:
            model_class: The model class
            id: The primary key ID
            data: Update data
            
        Returns:
            True if the update succeeded
        """
        # Add model class information to the data
        data_with_model = {
            "model_class": model_class.__name__,
            "table_name": model_class.__tablename__,
            "id": id,
            "data": data,
        }
        
        # Add to batch and get result
        return await self.update_batcher.add_item(data_with_model)
    
    async def _batch_update(
        self,
        items: List[Dict[str, Any]],
    ) -> List[bool]:
        """
        Process a batch of update operations.
        
        Args:
            items: List of items to update
            
        Returns:
            List of success flags
        """
        # Group items by model class
        grouped_items: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            model_name = item["model_class"]
            if model_name not in grouped_items:
                grouped_items[model_name] = []
            grouped_items[model_name].append({
                "id": item["id"],
                "data": item["data"],
            })
        
        results = [False] * len(items)
        
        # Process each group in a separate transaction
        async with SessionOperationGroup() as op_group:
            session = await op_group.create_session()
            
            async with session.begin():
                for model_name, model_items in grouped_items.items():
                    # Get model class
                    model_class = self._get_model_class_by_name(model_name)
                    
                    # Get primary key column
                    pk_col = model_class.__table__.primary_key.columns.values()[0]
                    
                    # Process each update individually
                    for item in model_items:
                        # Prepare update statement
                        stmt = (
                            update(model_class)
                            .where(pk_col == item["id"])
                            .values(item["data"])
                            .returning(func.count())
                        )
                        
                        # Execute statement
                        result = await session.execute(stmt)
                        row_count = result.scalar()
                        
                        # Find the index in the original items
                        for i, original_item in enumerate(items):
                            if (
                                original_item["model_class"] == model_name
                                and original_item["id"] == item["id"]
                            ):
                                # Mark as successful if rows were updated
                                results[i] = row_count > 0
                                break
        
        return results
    
    def _get_model_class_by_name(self, name: str) -> Type[UnoModel]:
        """
        Get a model class by name.
        
        Args:
            name: The model class name
            
        Returns:
            The model class
            
        Raises:
            ValueError: If the model class is not found
        """
        # Import the model registry
        from uno.registry import registry
        
        # Try to find the model class in the registry
        if name in registry.models:
            return registry.models[name]
        
        # If not in registry, try to find by scanning all loaded modules
        import sys
        import inspect
        from uno.model import UnoModel
        
        for module_name, module in sys.modules.items():
            if module_name.startswith('uno.'):
                for obj_name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, UnoModel) and 
                        obj.__name__ == name):
                        return obj
        
        # If we can't find it, raise a more helpful error
        raise ValueError(
            f"Model class {name} not found. Make sure the model is registered "
            f"in the registry or imported before accessing it."
        )
    
    @cancellable
    @retry(
        max_attempts=3, 
        retry_exceptions=lambda ex: is_transient_error(ex) or isinstance(ex, asyncio.TimeoutError),
        retry_delay_factory=lambda ex, attempt: get_retry_delay_for_error(ex) * attempt
    )
    @timeout_handler(timeout_seconds=30.0, timeout_message="Database operation timed out")
    @with_pg_error_handling(error_message="Error executing operations in transaction")
    async def execute_in_transaction(
        self,
        operations: List[Callable[[AsyncSession], Awaitable[Any]]],
    ) -> List[Any]:
        """
        Execute multiple operations in a single transaction.
        
        Args:
            operations: List of operations to execute
            
        Returns:
            List of operation results
        """
        async with SessionOperationGroup() as op_group:
            session = await op_group.create_session()
            return await op_group.run_in_transaction(session, operations)
    
    async def shutdown(self) -> None:
        """Shut down the database operations and clean up resources."""
        # Shut down batchers
        if hasattr(self, 'insert_batcher'):
            await self.insert_batcher.shutdown()
        
        if hasattr(self, 'update_batcher'):
            await self.update_batcher.shutdown()
        
        # Clear caches
        if hasattr(self, 'query_cache'):
            await self.query_cache.clear()