"""
Read Model performance optimization components.

This module provides performance optimizations for the Read Model pattern in uno,
including:

1. Materialized views - Database-level optimized read models 
2. Multi-level caching - Efficient caching for read models
3. Batch processing - Processing multiple read model operations at once
4. Read model denormalization - Performance-optimized data structures
5. Projection optimization - Efficient projection and event processing
"""

import asyncio
import logging
import pickle
import time
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, Tuple, Type, TypeVar, Union
)

from uno.core.result import Result, Success, Failure, Error
from uno.read_model import (
    ReadModel, ReadModelId, ReadModelRepository, 
    Projection, Projector, ProjectorConfiguration
)
from uno.database.enhanced_db import EnhancedDB
from uno.database.repository import Repository
from uno.domain.event_store import EventStore

# Type variables for generic classes
T = TypeVar('T')
TReadModel = TypeVar('TReadModel', bound=ReadModel)
TEvent = TypeVar('TEvent')

# Configure logger
logger = logging.getLogger(__name__)


class MaterializedViewController:
    """
    Controller for managing database materialized views.
    
    Materialized views are database objects that store the result of a query,
    providing significantly faster read access for complex queries at the cost
    of some write overhead and data staleness.
    
    Use this when:
    1. You have complex, expensive queries that are executed frequently
    2. You can tolerate some level of data staleness
    3. You need consistent, predictable query performance
    """

    def __init__(self, db_provider: EnhancedDB):
        """
        Initialize the materialized view controller.

        Args:
            db_provider: Database provider
        """
        self.db = db_provider
        self.views: Dict[str, Dict[str, Any]] = {}

    async def create_view(
        self,
        name: str,
        query: str,
        schema: str = "public",
        index_columns: Optional[List[str]] = None,
        refresh_interval_seconds: Optional[int] = None
    ) -> None:
        """
        Create a materialized view.

        Args:
            name: View name
            query: SQL query that defines the view
            schema: Database schema
            index_columns: Optional columns to index
            refresh_interval_seconds: How often to refresh automatically (None for manual)
        """
        try:
            # Create materialized view
            create_sql = f"""
            CREATE MATERIALIZED VIEW IF NOT EXISTS {schema}.{name}
            AS {query}
            WITH DATA
            """
            await self.db.execute_query(create_sql, [])
            logger.info(f"Created materialized view: {schema}.{name}")
            
            # Create indexes if specified
            if index_columns:
                for column in index_columns:
                    index_name = f"{name}_{column}_idx"
                    index_sql = f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {schema}.{name} ({column})
                    """
                    await self.db.execute_query(index_sql, [])
                    logger.info(f"Created index {index_name} on {schema}.{name}")
            
            # Store view info
            self.views[name] = {
                "name": name,
                "schema": schema,
                "query": query,
                "index_columns": index_columns or [],
                "refresh_interval": refresh_interval_seconds,
                "last_refresh": datetime.now(UTC),
                "refresh_in_progress": False
            }
            
            # Set up automatic refresh if interval is specified
            if refresh_interval_seconds:
                asyncio.create_task(self._schedule_refresh(name, refresh_interval_seconds))
                
        except Exception as e:
            logger.exception(f"Error creating materialized view {name}: {e}")
            raise

    async def refresh_view(self, name: str, concurrently: bool = True) -> None:
        """
        Refresh a materialized view.

        Args:
            name: View name
            concurrently: Whether to refresh concurrently (allowing queries during refresh)
        """
        if name not in self.views:
            raise ValueError(f"Materialized view {name} not found")
        
        view_info = self.views[name]
        
        # Skip if refresh already in progress
        if view_info["refresh_in_progress"]:
            logger.info(f"Refresh already in progress for {name}, skipping")
            return
        
        try:
            view_info["refresh_in_progress"] = True
            concurrently_text = "CONCURRENTLY" if concurrently else ""
            
            refresh_sql = f"""
            REFRESH MATERIALIZED VIEW {concurrently_text} {view_info['schema']}.{name}
            """
            
            start_time = time.time()
            await self.db.execute_query(refresh_sql, [])
            duration = time.time() - start_time
            
            # Update last refresh time
            view_info["last_refresh"] = datetime.now(UTC)
            logger.info(f"Refreshed materialized view {name} in {duration:.2f} seconds")
            
        except Exception as e:
            logger.exception(f"Error refreshing materialized view {name}: {e}")
            raise
        finally:
            view_info["refresh_in_progress"] = False

    async def refresh_all_views(self, concurrently: bool = True) -> Dict[str, bool]:
        """
        Refresh all materialized views.

        Args:
            concurrently: Whether to refresh concurrently

        Returns:
            Dictionary of view names and success status
        """
        results = {}
        
        for name in self.views.keys():
            try:
                await self.refresh_view(name, concurrently)
                results[name] = True
            except Exception:
                results[name] = False
        
        return results

    async def drop_view(self, name: str, cascade: bool = False) -> None:
        """
        Drop a materialized view.

        Args:
            name: View name
            cascade: Whether to cascade the drop operation
        """
        if name not in self.views:
            raise ValueError(f"Materialized view {name} not found")
        
        view_info = self.views[name]
        cascade_text = "CASCADE" if cascade else ""
        
        drop_sql = f"""
        DROP MATERIALIZED VIEW IF EXISTS {view_info['schema']}.{name} {cascade_text}
        """
        
        await self.db.execute_query(drop_sql, [])
        del self.views[name]
        logger.info(f"Dropped materialized view {name}")

    async def get_view_status(self, name: str) -> Dict[str, Any]:
        """
        Get the status of a materialized view.

        Args:
            name: View name

        Returns:
            Dictionary with view status information
        """
        if name not in self.views:
            raise ValueError(f"Materialized view {name} not found")
        
        view_info = self.views[name]
        schema = view_info["schema"]
        
        # Get size information
        size_sql = """
        SELECT
            pg_size_pretty(pg_relation_size($1)) AS size,
            pg_size_pretty(pg_indexes_size($1)) AS index_size,
            pg_size_pretty(pg_total_relation_size($1)) AS total_size
        """
        size_result = await self.db.execute_query(size_sql, [f"{schema}.{name}"])
        
        # Get row count
        count_sql = f"SELECT COUNT(*) FROM {schema}.{name}"
        count_result = await self.db.execute_query(count_sql, [])
        
        status = {
            **view_info,
            "size": size_result[0]["size"],
            "index_size": size_result[0]["index_size"],
            "total_size": size_result[0]["total_size"],
            "row_count": count_result[0]["count"],
            "age": (datetime.now(UTC) - view_info["last_refresh"]).total_seconds(),
        }
        
        return status

    async def get_all_view_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all materialized views.

        Returns:
            Dictionary of view names and their statuses
        """
        results = {}
        
        for name in self.views.keys():
            try:
                results[name] = await self.get_view_status(name)
            except Exception as e:
                logger.error(f"Error getting status for {name}: {e}")
                results[name] = {"error": str(e)}
        
        return results

    async def _schedule_refresh(self, name: str, interval_seconds: int) -> None:
        """
        Schedule automatic refresh for a view.

        Args:
            name: View name
            interval_seconds: Refresh interval in seconds
        """
        while name in self.views and self.views[name]["refresh_interval"] == interval_seconds:
            try:
                await asyncio.sleep(interval_seconds)
                await self.refresh_view(name)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during scheduled refresh of {name}: {e}")
                # Sleep briefly to avoid tight loop in case of persistent errors
                await asyncio.sleep(10)


class CacheLevel(Enum):
    """Enum for cache levels in multi-level cache."""
    MEMORY = 1
    REDIS = 2
    DATABASE = 3


class MultiLevelReadModelCache(Generic[T]):
    """
    Multi-level caching for read models.
    
    Provides a tiered caching approach that balances performance and consistency:
    1. Level 1: In-memory cache (fastest, but local to the process)
    2. Level 2: Redis cache (fast, shared across processes)
    3. Level 3: Database (slower, but always consistent)
    
    Use this when:
    1. You need high-performance access to read models
    2. You have multiple application instances accessing the same data
    3. You want to balance performance with consistency
    """

    def __init__(
        self,
        memory_cache_size: int = 1000,
        memory_ttl_seconds: int = 60,
        redis_client = None,
        redis_ttl_seconds: int = 300,
        redis_prefix: str = "rm:"
    ):
        """
        Initialize the multi-level cache.

        Args:
            memory_cache_size: Maximum number of items in memory cache
            memory_ttl_seconds: TTL for memory cache in seconds
            redis_client: Redis client (if None, Redis level is disabled)
            redis_ttl_seconds: TTL for Redis cache in seconds
            redis_prefix: Prefix for Redis keys
        """
        self.memory_cache: Dict[str, Tuple[T, datetime]] = {}
        self.memory_cache_size = memory_cache_size
        self.memory_ttl_seconds = memory_ttl_seconds
        self.memory_access_times: Dict[str, datetime] = {}
        
        self.redis_client = redis_client
        self.redis_ttl_seconds = redis_ttl_seconds
        self.redis_prefix = redis_prefix
        
        self.stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "misses": 0,
            "writes": 0,
            "invalidations": 0
        }

    async def get(self, key: str, level_limit: Optional[CacheLevel] = None) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: Cache key
            level_limit: Optional maximum cache level to check

        Returns:
            The cached value or None if not found
        """
        now = datetime.now(UTC)
        
        # Check memory cache (Level 1)
        if level_limit is None or level_limit.value >= CacheLevel.MEMORY.value:
            if key in self.memory_cache:
                value, expiry = self.memory_cache[key]
                if expiry > now:
                    # Update access time for LRU
                    self.memory_access_times[key] = now
                    self.stats["memory_hits"] += 1
                    return value
                else:
                    # Expired, remove from cache
                    del self.memory_cache[key]
                    if key in self.memory_access_times:
                        del self.memory_access_times[key]
        
        # Check Redis cache (Level 2)
        if (level_limit is None or level_limit.value >= CacheLevel.REDIS.value) and self.redis_client:
            redis_key = f"{self.redis_prefix}{key}"
            redis_value = await self.redis_client.get(redis_key)
            
            if redis_value:
                # Deserialize value
                value = pickle.loads(redis_value)
                
                # Store in memory cache
                expiry = now + timedelta(seconds=self.memory_ttl_seconds)
                self._set_memory_cache(key, value, expiry)
                
                self.stats["redis_hits"] += 1
                return value
        
        # Not found in any cache
        self.stats["misses"] += 1
        return None

    async def set(
        self, 
        key: str, 
        value: T, 
        memory_ttl_seconds: Optional[int] = None,
        redis_ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            memory_ttl_seconds: Optional custom TTL for memory cache
            redis_ttl_seconds: Optional custom TTL for Redis cache
        """
        now = datetime.now(UTC)
        self.stats["writes"] += 1
        
        # Set in memory cache
        memory_ttl = memory_ttl_seconds or self.memory_ttl_seconds
        expiry = now + timedelta(seconds=memory_ttl)
        self._set_memory_cache(key, value, expiry)
        
        # Set in Redis cache
        if self.redis_client:
            redis_key = f"{self.redis_prefix}{key}"
            redis_ttl = redis_ttl_seconds or self.redis_ttl_seconds
            
            # Serialize value
            serialized = pickle.dumps(value)
            
            # Store in Redis
            await self.redis_client.set(redis_key, serialized, ex=redis_ttl)

    async def invalidate(self, key: str) -> None:
        """
        Invalidate a cache entry.

        Args:
            key: Cache key to invalidate
        """
        self.stats["invalidations"] += 1
        
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            if key in self.memory_access_times:
                del self.memory_access_times[key]
        
        # Remove from Redis cache
        if self.redis_client:
            redis_key = f"{self.redis_prefix}{key}"
            await self.redis_client.delete(redis_key)

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Pattern to match keys against

        Returns:
            Number of keys invalidated
        """
        count = 0
        
        # Invalidate from memory cache
        memory_keys = [k for k in self.memory_cache.keys() if self._matches_pattern(k, pattern)]
        for key in memory_keys:
            del self.memory_cache[key]
            if key in self.memory_access_times:
                del self.memory_access_times[key]
            count += 1
        
        # Invalidate from Redis cache
        if self.redis_client:
            redis_pattern = f"{self.redis_prefix}{pattern}"
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=redis_pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
        
        self.stats["invalidations"] += count
        return count

    async def clear(self) -> None:
        """Clear all cache entries."""
        # Clear memory cache
        self.memory_cache.clear()
        self.memory_access_times.clear()
        
        # Clear Redis cache
        if self.redis_client:
            redis_pattern = f"{self.redis_prefix}*"
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=redis_pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
        
        # Reset stats
        self.stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "misses": 0,
            "writes": 0,
            "invalidations": 0
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        total_hits = self.stats["memory_hits"] + self.stats["redis_hits"]
        total_requests = total_hits + self.stats["misses"]
        
        if total_requests > 0:
            hit_rate = total_hits / total_requests
            memory_hit_rate = self.stats["memory_hits"] / total_requests
            redis_hit_rate = self.stats["redis_hits"] / total_requests
        else:
            hit_rate = 0
            memory_hit_rate = 0
            redis_hit_rate = 0
        
        return {
            **self.stats,
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_limit": self.memory_cache_size,
            "hit_rate": hit_rate,
            "memory_hit_rate": memory_hit_rate,
            "redis_hit_rate": redis_hit_rate,
            "total_requests": total_requests
        }

    def _set_memory_cache(self, key: str, value: T, expiry: datetime) -> None:
        """
        Set a value in the memory cache with eviction if full.

        Args:
            key: Cache key
            value: Value to cache
            expiry: Expiry timestamp
        """
        # Evict if cache is full
        if key not in self.memory_cache and len(self.memory_cache) >= self.memory_cache_size:
            self._evict_lru()
        
        # Store value
        self.memory_cache[key] = (value, expiry)
        self.memory_access_times[key] = datetime.now(UTC)

    def _evict_lru(self) -> None:
        """Evict the least recently used item from memory cache."""
        if not self.memory_access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.memory_access_times.items(), key=lambda x: x[1])[0]
        
        # Remove from cache
        del self.memory_cache[lru_key]
        del self.memory_access_times[lru_key]

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """
        Check if a key matches a pattern.

        Args:
            key: Cache key
            pattern: Pattern to match against

        Returns:
            True if the key matches the pattern
        """
        import re
        # Convert glob pattern to regex
        pattern_regex = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{pattern_regex}$", key))


class BatchReadModelRepository(Generic[T]):
    """
    Batch-optimized repository for read models.
    
    Provides efficient operations for working with multiple read models at once:
    1. Batch retrieval by ID
    2. Batch insertion
    3. Batch update
    4. Batch deletion
    
    Use this when:
    1. You need to perform operations on multiple read models at once
    2. You want to minimize database round-trips
    3. You need to optimize throughput for high-volume operations
    """

    def __init__(
        self,
        delegate: ReadModelRepository[T],
        default_batch_size: int = 100
    ):
        """
        Initialize the batch repository.

        Args:
            delegate: The repository to delegate to
            default_batch_size: Default batch size for operations
        """
        self.delegate = delegate
        self.default_batch_size = default_batch_size

    async def get_by_ids(
        self, 
        ids: List[ReadModelId]
    ) -> Dict[ReadModelId, Optional[T]]:
        """
        Get multiple read models by their IDs.

        Args:
            ids: List of read model IDs

        Returns:
            Dictionary mapping IDs to read models (or None if not found)
        """
        if not ids:
            return {}
        
        # Split into batches if necessary
        if len(ids) > self.default_batch_size:
            result = {}
            
            for i in range(0, len(ids), self.default_batch_size):
                batch_ids = ids[i:i + self.default_batch_size]
                batch_result = await self._get_batch(batch_ids)
                result.update(batch_result)
            
            return result
        else:
            return await self._get_batch(ids)

    async def save_batch(self, models: List[T]) -> None:
        """
        Save multiple read models.

        Args:
            models: List of read models to save
        """
        if not models:
            return
        
        # Split into batches if necessary
        if len(models) > self.default_batch_size:
            for i in range(0, len(models), self.default_batch_size):
                batch = models[i:i + self.default_batch_size]
                await self._save_batch(batch)
        else:
            await self._save_batch(models)

    async def delete_by_ids(self, ids: List[ReadModelId]) -> None:
        """
        Delete multiple read models by their IDs.

        Args:
            ids: List of read model IDs to delete
        """
        if not ids:
            return
        
        # Split into batches if necessary
        if len(ids) > self.default_batch_size:
            for i in range(0, len(ids), self.default_batch_size):
                batch_ids = ids[i:i + self.default_batch_size]
                await self._delete_batch(batch_ids)
        else:
            await self._delete_batch(ids)

    async def _get_batch(self, ids: List[ReadModelId]) -> Dict[ReadModelId, Optional[T]]:
        """
        Internal method to get a batch of read models.

        Args:
            ids: List of read model IDs

        Returns:
            Dictionary mapping IDs to read models
        """
        # Convert to dictionary for efficient lookup
        result = {id_obj: None for id_obj in ids}
        
        # Use the most efficient batch mechanism if available
        if hasattr(self.delegate, "get_by_ids"):
            # Delegate has native batch support
            batch_result = await self.delegate.get_by_ids(ids)
            result.update(batch_result)
        else:
            # Fall back to individual gets, but in parallel
            tasks = []
            
            for id_obj in ids:
                task = asyncio.create_task(self.delegate.get_by_id(id_obj))
                tasks.append((id_obj, task))
            
            # Wait for all tasks to complete
            for id_obj, task in tasks:
                try:
                    model = await task
                    result[id_obj] = model
                except Exception as e:
                    logger.error(f"Error retrieving read model {id_obj.value}: {e}")
        
        return result

    async def _save_batch(self, models: List[T]) -> None:
        """
        Internal method to save a batch of read models.

        Args:
            models: List of read models to save
        """
        # Use the most efficient batch mechanism if available
        if hasattr(self.delegate, "save_batch"):
            # Delegate has native batch support
            await self.delegate.save_batch(models)
        else:
            # Fall back to individual saves, but in parallel
            tasks = []
            
            for model in models:
                task = asyncio.create_task(self.delegate.save(model))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

    async def _delete_batch(self, ids: List[ReadModelId]) -> None:
        """
        Internal method to delete a batch of read models.

        Args:
            ids: List of read model IDs to delete
        """
        # Use the most efficient batch mechanism if available
        if hasattr(self.delegate, "delete_by_ids"):
            # Delegate has native batch support
            await self.delegate.delete_by_ids(ids)
        else:
            # Fall back to individual deletes, but in parallel
            tasks = []
            
            for id_obj in ids:
                task = asyncio.create_task(self.delegate.delete(id_obj))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)


class DenormalizedReadModel(ReadModel):
    """
    A read model with denormalized data for performance optimization.
    
    Denormalization is a technique that duplicates data to avoid expensive joins,
    improving read performance at the cost of increased storage and write complexity.
    
    Use this when:
    1. You need to optimize read performance for complex data structures
    2. Your read models involve data from multiple related entities
    3. You can tolerate the additional complexity in the write path
    """

    def __init__(
        self,
        id: ReadModelId,
        version: int,
        created_at: datetime,
        updated_at: datetime,
        data: Dict[str, Any],
        denormalized_data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize the denormalized read model.

        Args:
            id: Read model ID
            version: Version number
            created_at: Creation timestamp
            updated_at: Last update timestamp
            data: Primary data
            denormalized_data: Denormalized data from related entities
            metadata: Optional metadata
        """
        super().__init__(
            id=id,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
            data=data,
            metadata=metadata or {}
        )
        self.denormalized_data = denormalized_data or {}

    def update(self, data_updates: Dict[str, Any]) -> 'DenormalizedReadModel':
        """
        Update the read model with new data.

        Args:
            data_updates: Updates to apply to the data

        Returns:
            Updated read model
        """
        # Extract denormalized data updates
        denormalized_updates = {}
        regular_updates = {}
        
        for key, value in data_updates.items():
            if key.startswith("denormalized_"):
                # Strip the prefix for denormalized keys
                real_key = key[13:]
                denormalized_updates[real_key] = value
            else:
                regular_updates[key] = value
        
        # Apply regular updates
        new_data = {**self.data}
        new_data.update(regular_updates)
        
        # Apply denormalized updates
        new_denormalized = {**self.denormalized_data}
        new_denormalized.update(denormalized_updates)
        
        return DenormalizedReadModel(
            id=self.id,
            version=self.version + 1,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
            data=new_data,
            denormalized_data=new_denormalized,
            metadata=self.metadata
        )

    def get_all_data(self) -> Dict[str, Any]:
        """
        Get all data, including denormalized data.

        Returns:
            Combined data dictionary
        """
        return {
            **self.data,
            **{f"denormalized_{k}": v for k, v in self.denormalized_data.items()}
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        base_dict = super().to_dict()
        base_dict["denormalized_data"] = self.denormalized_data
        return base_dict


class BatchProjector(Projector):
    """
    Projector that processes events in batches for improved performance.
    
    Batch processing of events can significantly improve throughput by:
    1. Reducing overhead of individual event processing
    2. Enabling more efficient database operations
    3. Minimizing the number of transactions
    
    Use this when:
    1. You need to process a large volume of events
    2. Your projections update multiple read models
    3. Throughput is more important than latency
    """

    def __init__(
        self,
        event_store: EventStore,
        projection_service: Any,
        projector_config_repository: Any,
        config_name: str = "batch_projector",
        batch_size: int = 100,
        checkpoint_interval: int = 1000
    ):
        """
        Initialize the batch projector.

        Args:
            event_store: Event store to read events from
            projection_service: Service for applying projections
            projector_config_repository: Repository for projector configuration
            config_name: Configuration name
            batch_size: Number of events to process in a batch
            checkpoint_interval: How often to save a checkpoint
        """
        super().__init__(
            event_store=event_store,
            projection_service=projection_service,
            projector_config_repository=projector_config_repository,
            config_name=config_name
        )
        self.batch_size = batch_size
        self.checkpoint_interval = checkpoint_interval
        self.processed_count = 0

    async def process_events(
        self, 
        max_events: int = None
    ) -> int:
        """
        Process events in batches.

        Args:
            max_events: Maximum number of events to process (None for unlimited)

        Returns:
            Number of events processed
        """
        # Load configuration
        config = await self._load_configuration()
        
        # Calculate how many events to process
        events_to_process = max_events or -1
        total_processed = 0
        
        while events_to_process != 0:
            # Determine batch size
            current_batch_size = min(self.batch_size, events_to_process) if events_to_process > 0 else self.batch_size
            
            # Get events to process
            events = await self.event_store.get_events_after_position(
                position=config.last_position,
                limit=current_batch_size
            )
            
            if not events:
                break
            
            # Process events in batch
            last_position = await self._process_batch(events)
            
            # Update counters
            batch_count = len(events)
            total_processed += batch_count
            self.processed_count += batch_count
            
            # Update configuration
            config.last_position = last_position
            
            # Save checkpoint if needed
            if self.processed_count >= self.checkpoint_interval:
                await self._save_configuration(config)
                self.processed_count = 0
                logger.info(f"Saved checkpoint at position {config.last_position}")
            
            # Update events_to_process
            if events_to_process > 0:
                events_to_process -= batch_count
        
        # Save final configuration
        if total_processed > 0:
            await self._save_configuration(config)
        
        return total_processed

    async def _process_batch(self, events: List[Any]) -> int:
        """
        Process a batch of events.

        Args:
            events: List of events to process

        Returns:
            Position of the last processed event
        """
        # Group events by type for more efficient processing
        events_by_type = {}
        last_position = 0
        
        for event in events:
            event_type = event.event_type
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            
            events_by_type[event_type].append(event)
            last_position = max(last_position, event.position)
        
        # Process each event type in parallel
        tasks = []
        
        for event_type, type_events in events_by_type.items():
            task = asyncio.create_task(
                self._process_events_of_type(event_type, type_events)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        return last_position

    async def _process_events_of_type(self, event_type: str, events: List[Any]) -> None:
        """
        Process events of a specific type.

        Args:
            event_type: Event type
            events: List of events to process
        """
        # Get projections for this event type
        projections = await self.projection_service.get_projections_for_event_type(event_type)
        
        if not projections:
            return
        
        # Process each projection
        for projection in projections:
            try:
                # Apply events to the projection
                if hasattr(projection, "apply_batch"):
                    # Projection supports batch processing
                    await projection.apply_batch(events)
                else:
                    # Fall back to individual processing
                    for event in events:
                        await projection.apply(event)
            except Exception as e:
                logger.exception(f"Error applying events to projection {projection.__class__.__name__}: {e}")


class SnapshotProjection(Generic[TReadModel, TEvent], Projection[TReadModel, TEvent]):
    """
    A projection that creates and uses snapshots for improved performance.
    
    Snapshots are point-in-time captures of an aggregate's state, allowing for
    faster rebuilding without replaying all events from the beginning.
    
    Use this when:
    1. Your aggregates have a large number of events
    2. Rebuilding from all events is becoming slow
    3. You need to optimize the read model building process
    """

    def __init__(
        self,
        repository: Repository[TReadModel],
        snapshot_repository: Repository[Dict[str, Any]],
        snapshot_interval: int = 100
    ):
        """
        Initialize the snapshot projection.

        Args:
            repository: Read model repository
            snapshot_repository: Repository for storing snapshots
            snapshot_interval: How many events to process before creating a snapshot
        """
        super().__init__(repository)
        self.snapshot_repository = snapshot_repository
        self.snapshot_interval = snapshot_interval
        self.event_counts: Dict[str, int] = {}

    async def apply(self, event: TEvent) -> Optional[TReadModel]:
        """
        Apply an event to the projection.

        Args:
            event: Event to apply

        Returns:
            Updated read model
        """
        # Get aggregate ID from event
        aggregate_id = getattr(event, "aggregate_id", None)
        if not aggregate_id:
            logger.warning(f"Event {event.__class__.__name__} has no aggregate_id, skipping")
            return None
        
        # Try to get existing model first from snapshot, then from repository
        read_model = await self._get_with_snapshot(aggregate_id)
        
        # Apply event to read model
        updated_model = await self._apply_event(event, read_model)
        
        if updated_model:
            # Save the updated model
            await self.repository.save(updated_model)
            
            # Update event count and create snapshot if needed
            if aggregate_id not in self.event_counts:
                self.event_counts[aggregate_id] = 0
            
            self.event_counts[aggregate_id] += 1
            
            if self.event_counts[aggregate_id] >= self.snapshot_interval:
                await self._create_snapshot(aggregate_id, updated_model)
                self.event_counts[aggregate_id] = 0
        
        return updated_model

    async def _get_with_snapshot(self, aggregate_id: str) -> Optional[TReadModel]:
        """
        Get a read model, using snapshot if available.

        Args:
            aggregate_id: Aggregate ID

        Returns:
            Read model
        """
        # Try to get the latest snapshot
        snapshot = await self.snapshot_repository.get_by_id(aggregate_id)
        
        if snapshot:
            # Deserialize the snapshot
            return self._deserialize_snapshot(snapshot)
        
        # No snapshot, get from repository
        read_model_id = ReadModelId(value=aggregate_id)
        return await self.repository.get_by_id(read_model_id)

    async def _create_snapshot(self, aggregate_id: str, model: TReadModel) -> None:
        """
        Create a snapshot of a read model.

        Args:
            aggregate_id: Aggregate ID
            model: Read model to snapshot
        """
        # Serialize the model
        snapshot_data = self._serialize_snapshot(model)
        
        # Save the snapshot
        await self.snapshot_repository.save_or_update(aggregate_id, snapshot_data)
        logger.debug(f"Created snapshot for aggregate {aggregate_id}")

    def _serialize_snapshot(self, model: TReadModel) -> Dict[str, Any]:
        """
        Serialize a model for snapshot storage.

        Args:
            model: Read model to serialize

        Returns:
            Serialized snapshot data
        """
        # Default implementation uses model.to_dict()
        return model.to_dict()

    def _deserialize_snapshot(self, snapshot: Dict[str, Any]) -> TReadModel:
        """
        Deserialize a snapshot into a read model.

        Args:
            snapshot: Snapshot data

        Returns:
            Deserialized read model
        """
        # Default implementation for ReadModel
        return ReadModel(
            id=ReadModelId(value=snapshot.get("id")),
            version=snapshot.get("version", 1),
            created_at=snapshot.get("created_at"),
            updated_at=snapshot.get("updated_at"),
            data=snapshot.get("data", {}),
            metadata=snapshot.get("metadata", {})
        )

    @abstractmethod
    async def _apply_event(self, event: TEvent, model: Optional[TReadModel]) -> Optional[TReadModel]:
        """
        Apply an event to a read model.

        Args:
            event: Event to apply
            model: Existing read model or None

        Returns:
            Updated read model
        """
        pass


class ParallelProjector(Projector):
    """
    Projector that processes events in parallel for improved performance.
    
    Parallel processing can significantly improve throughput by:
    1. Utilizing multiple CPU cores
    2. Processing independent event streams concurrently
    3. Reducing overall processing time
    
    Use this when:
    1. You have a high volume of events to process
    2. Your events are for different aggregates (can be processed independently)
    3. You have multiple CPU cores available
    """

    def __init__(
        self,
        event_store: EventStore,
        projection_service: Any,
        projector_config_repository: Any,
        config_name: str = "parallel_projector",
        worker_count: int = 4,
        batch_size: int = 100
    ):
        """
        Initialize the parallel projector.

        Args:
            event_store: Event store
            projection_service: Projection service
            projector_config_repository: Repository for configuration
            config_name: Configuration name
            worker_count: Number of worker tasks
            batch_size: Batch size for each worker
        """
        super().__init__(
            event_store=event_store,
            projection_service=projection_service,
            projector_config_repository=projector_config_repository,
            config_name=config_name
        )
        self.worker_count = worker_count
        self.batch_size = batch_size
        self.queue = asyncio.Queue()
        self.workers = []
        self.running = False

    async def start(self) -> None:
        """Start the projector workers."""
        if self.running:
            return
        
        self.running = True
        
        # Start workers
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start event loader
        self.event_loader = asyncio.create_task(self._event_loader())
        
        logger.info(f"Started parallel projector with {self.worker_count} workers")

    async def stop(self) -> None:
        """Stop the projector workers."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel event loader
        self.event_loader.cancel()
        
        # Send stop signal to workers
        for _ in range(self.worker_count):
            await self.queue.put(None)
        
        # Wait for workers to complete
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []
        
        logger.info("Stopped parallel projector")

    async def _event_loader(self) -> None:
        """Load events from the event store and queue them for processing."""
        try:
            # Load configuration
            config = await self._load_configuration()
            last_position = config.last_position
            
            while self.running:
                # Get events
                events = await self.event_store.get_events_after_position(
                    position=last_position,
                    limit=self.batch_size
                )
                
                if not events:
                    # No events, wait and try again
                    await asyncio.sleep(1)
                    continue
                
                # Queue events by aggregate
                events_by_aggregate = {}
                
                for event in events:
                    aggregate_id = getattr(event, "aggregate_id", None)
                    if not aggregate_id:
                        continue
                    
                    if aggregate_id not in events_by_aggregate:
                        events_by_aggregate[aggregate_id] = []
                    
                    events_by_aggregate[aggregate_id].append(event)
                    last_position = max(last_position, event.position)
                
                # Queue each aggregate's events
                for aggregate_id, aggregate_events in events_by_aggregate.items():
                    await self.queue.put(aggregate_events)
                
                # Update configuration
                config.last_position = last_position
                await self._save_configuration(config)
                
        except asyncio.CancelledError:
            logger.info("Event loader cancelled")
        except Exception as e:
            logger.exception(f"Error in event loader: {e}")

    async def _worker(self, worker_id: str) -> None:
        """
        Worker task for processing events.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")
        
        try:
            while self.running:
                # Get the next batch of events
                events = await self.queue.get()
                
                # Check for stop signal
                if events is None:
                    logger.info(f"Worker {worker_id} received stop signal")
                    break
                
                try:
                    # Process the events
                    for event in events:
                        await self._process_event(event)
                except Exception as e:
                    logger.exception(f"Error processing events in worker {worker_id}: {e}")
                finally:
                    # Mark the batch as done
                    self.queue.task_done()
        
        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} cancelled")
        except Exception as e:
            logger.exception(f"Error in worker {worker_id}: {e}")
        
        logger.info(f"Worker {worker_id} stopped")

    async def _process_event(self, event: Any) -> None:
        """
        Process a single event.

        Args:
            event: Event to process
        """
        # Get projections for this event type
        event_type = event.event_type
        projections = await self.projection_service.get_projections_for_event_type(event_type)
        
        if not projections:
            return
        
        # Apply event to each projection
        for projection in projections:
            try:
                await projection.apply(event)
            except Exception as e:
                logger.exception(f"Error applying event to projection {projection.__class__.__name__}: {e}")


class StreamingReadModelRepository(Generic[T]):
    """
    Repository that supports streaming large result sets.
    
    Traditional repositories load all results into memory, which can be problematic
    for large result sets. Streaming allows processing results incrementally without
    loading everything at once.
    
    Use this when:
    1. You need to process large result sets
    2. You want to minimize memory usage
    3. You need to start processing results before all data is available
    """

    def __init__(
        self,
        db_provider: EnhancedDB,
        model_type: Type[T],
        table_name: str,
        schema: str = "public",
        batch_size: int = 100
    ):
        """
        Initialize the streaming repository.

        Args:
            db_provider: Database provider
            model_type: Type of read model
            table_name: Table name
            schema: Database schema
            batch_size: Batch size for streaming
        """
        self.db = db_provider
        self.model_type = model_type
        self.table_name = table_name
        self.schema = schema
        self.batch_size = batch_size

    async def stream(
        self,
        filters: Dict[str, Any] = None,
        order_by: List[str] = None,
        offset: int = 0
    ) -> AsyncIterator[T]:
        """
        Stream read models matching the filter criteria.

        Args:
            filters: Optional filter criteria
            order_by: Optional sort columns
            offset: Starting offset

        Yields:
            Read models matching the criteria
        """
        # Build query
        query, params = self._build_query(filters, order_by, self.batch_size, offset)
        
        current_offset = offset
        while True:
            # Execute query
            results = await self.db.execute_query(query, params)
            
            if not results:
                break
            
            # Yield read models
            for row in results:
                yield self._create_model_from_row(row)
            
            # Update offset for next batch
            current_offset += len(results)
            
            if len(results) < self.batch_size:
                # End of results
                break
            
            # Update parameters for next batch
            params[-1] = current_offset

    async def stream_process(
        self,
        processor: Callable[[T], Awaitable[None]],
        filters: Dict[str, Any] = None,
        order_by: List[str] = None,
        parallel_processing: bool = False,
        max_concurrency: int = 10
    ) -> int:
        """
        Stream and process read models.

        Args:
            processor: Function to process each read model
            filters: Optional filter criteria
            order_by: Optional sort columns
            parallel_processing: Whether to process in parallel
            max_concurrency: Maximum concurrency for parallel processing

        Returns:
            Number of read models processed
        """
        if parallel_processing:
            return await self._stream_process_parallel(
                processor, filters, order_by, max_concurrency
            )
        else:
            return await self._stream_process_sequential(
                processor, filters, order_by
            )

    async def _stream_process_sequential(
        self,
        processor: Callable[[T], Awaitable[None]],
        filters: Dict[str, Any] = None,
        order_by: List[str] = None
    ) -> int:
        """
        Process read models sequentially.

        Args:
            processor: Function to process each read model
            filters: Optional filter criteria
            order_by: Optional sort columns

        Returns:
            Number of read models processed
        """
        count = 0
        
        async for model in self.stream(filters, order_by):
            await processor(model)
            count += 1
        
        return count

    async def _stream_process_parallel(
        self,
        processor: Callable[[T], Awaitable[None]],
        filters: Dict[str, Any] = None,
        order_by: List[str] = None,
        max_concurrency: int = 10
    ) -> int:
        """
        Process read models in parallel.

        Args:
            processor: Function to process each read model
            filters: Optional filter criteria
            order_by: Optional sort columns
            max_concurrency: Maximum concurrency

        Returns:
            Number of read models processed
        """
        count = 0
        semaphore = asyncio.Semaphore(max_concurrency)
        tasks = []
        
        async for model in self.stream(filters, order_by):
            async def process_with_semaphore(model):
                async with semaphore:
                    await processor(model)
            
            task = asyncio.create_task(process_with_semaphore(model))
            tasks.append(task)
            count += 1
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        return count

    def _build_query(
        self,
        filters: Dict[str, Any] = None,
        order_by: List[str] = None,
        limit: int = None,
        offset: int = 0
    ) -> Tuple[str, List[Any]]:
        """
        Build a query for streaming.

        Args:
            filters: Optional filter criteria
            order_by: Optional sort columns
            limit: Maximum number of results
            offset: Starting offset

        Returns:
            Tuple of (query, parameters)
        """
        # Build query
        query = f"SELECT * FROM {self.schema}.{self.table_name}"
        params = []
        
        # Add filters
        if filters:
            conditions = []
            param_index = 1
            
            for key, value in filters.items():
                if isinstance(value, dict):
                    # Handle operators like $eq, $gt, $lt, etc.
                    for op, op_value in value.items():
                        op_sql = self._get_operator_sql(op, key)
                        conditions.append(f"{op_sql} ${param_index}")
                        params.append(op_value)
                        param_index += 1
                else:
                    # Simple equality
                    conditions.append(f"{key} = ${param_index}")
                    params.append(value)
                    param_index += 1
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        # Add order by
        if order_by:
            query += " ORDER BY " + ", ".join(order_by)
        else:
            # Default order by
            query += " ORDER BY id"
        
        # Add limit and offset
        if limit:
            query += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        
        query += f" OFFSET ${len(params) + 1}"
        params.append(offset)
        
        return query, params

    def _get_operator_sql(self, op: str, field: str) -> str:
        """
        Get SQL for a filter operator.

        Args:
            op: Operator
            field: Field name

        Returns:
            SQL for the operator
        """
        op_mapping = {
            "$eq": f"{field} =",
            "$neq": f"{field} <>",
            "$gt": f"{field} >",
            "$gte": f"{field} >=",
            "$lt": f"{field} <",
            "$lte": f"{field} <=",
            "$in": f"{field} = ANY",
            "$nin": f"{field} != ALL",
            "$like": f"{field} LIKE",
            "$ilike": f"{field} ILIKE",
            "$contains": f"{field} @>",
            "$contained": f"{field} <@",
            "$has_key": f"{field} ? ",
            "$has_keys": f"{field} ?& ",
            "$has_any_keys": f"{field} ?| "
        }
        
        if op not in op_mapping:
            raise ValueError(f"Unsupported operator: {op}")
        
        return op_mapping[op]

    def _create_model_from_row(self, row: Dict[str, Any]) -> T:
        """
        Create a read model from a database row.

        Args:
            row: Database row

        Returns:
            Read model
        """
        # Default implementation for ReadModel
        if self.model_type == ReadModel:
            return ReadModel(
                id=ReadModelId(value=row.get("id")),
                version=row.get("version", 1),
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
                data=row.get("data", {}),
                metadata=row.get("metadata", {})
            )
        
        # For other model types, use named constructor if available
        if hasattr(self.model_type, "from_row"):
            return self.model_type.from_row(row)
        
        # Fall back to dictionary constructor
        return self.model_type(**row)