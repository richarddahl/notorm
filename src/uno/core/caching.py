"""
Caching utilities for the Uno framework.

This module provides utilities for caching query results, computed values,
and other expensive operations to improve performance.
"""

from typing import (
    TypeVar,
    Generic,
    Dict,
    Any,
    Optional,
    List,
    Set,
    Callable,
    Awaitable,
    Union,
    cast,
    Tuple,
)
import asyncio
import logging
import time
import hashlib
import json
import pickle
import functools
import inspect
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from uno.core.asynchronous import (
    AsyncLock,
    AsyncEvent,
    AsyncSemaphore,
    TaskGroup,
    timeout,
)
from uno.core.async_integration import (
    cancellable,
    retry,
)
from uno.core.resources import (
    ResourceRegistry,
    get_resource_registry,
)


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class CacheStrategy(Enum):
    """
    Strategy for cache invalidation.

    - LRU: Least Recently Used - remove least recently used items
    - FIFO: First In First Out - remove oldest items
    - LFU: Least Frequently Used - remove least frequently used items
    - TTL: Time To Live - remove items older than TTL
    """

    LRU = "lru"
    FIFO = "fifo"
    LFU = "lfu"
    TTL = "ttl"


@dataclass
class CacheEntry(Generic[T]):
    """
    Entry in a cache.

    Attributes:
        value: The cached value
        created_at: Timestamp when the entry was created
        expires_at: Timestamp when the entry expires
        last_accessed: Timestamp when the entry was last accessed
        access_count: Number of times the entry has been accessed
        size: Size of the entry in bytes (estimated)
        metadata: Additional metadata about the entry
    """

    value: T
    created_at: float
    expires_at: Optional[float] = None
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, now: Optional[float] = None) -> bool:
        """
        Check if the entry is expired.

        Args:
            now: Current timestamp, defaults to time.time()

        Returns:
            True if the entry is expired, False otherwise
        """
        if self.expires_at is None:
            return False

        now = now or time.time()
        return now > self.expires_at

    def access(self) -> None:
        """
        Mark the entry as accessed.

        Updates the last_accessed timestamp and increments access_count.
        """
        self.last_accessed = time.time()
        self.access_count += 1


class Cache(Generic[K, V]):
    """
    Generic cache with multiple invalidation strategies.

    This class provides:
    - Multiple invalidation strategies (LRU, FIFO, LFU, TTL)
    - Size-based eviction
    - Time-based expiration
    - Thread-safe operations
    - Statistics and monitoring
    """

    def __init__(
        self,
        name: str,
        strategy: CacheStrategy = CacheStrategy.LRU,
        max_size: Optional[int] = 1000,
        max_bytes: Optional[int] = None,
        ttl: Optional[float] = 300.0,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the cache.

        Args:
            name: Name of the cache
            strategy: Cache eviction strategy
            max_size: Maximum number of items in the cache
            max_bytes: Maximum size of the cache in bytes
            ttl: Time-to-live for cache entries in seconds
            logger: Optional logger instance
        """
        self.name = name
        self.strategy = strategy
        self.max_size = max_size
        self.max_bytes = max_bytes
        self.ttl = ttl
        self.logger = logger or logging.getLogger(__name__)

        # Cache storage
        self._cache: Dict[K, CacheEntry[V]] = {}
        self._lock = AsyncLock()

        # Cache statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
        self._total_bytes = 0
        self._start_time = time.time()

    async def get(
        self,
        key: K,
        default: Optional[V] = None,
    ) -> Optional[V]:
        """
        Get a value from the cache.

        Args:
            key: The cache key
            default: Default value if key not found or expired

        Returns:
            The cached value or default
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                # Cache miss
                self._misses += 1
                return default

            if entry.is_expired():
                # Entry expired
                self._remove_entry(key)
                self._expirations += 1
                return default

            # Cache hit
            entry.access()
            self._hits += 1
            return entry.value

    async def get_or_set(
        self,
        key: K,
        getter: Callable[[], Awaitable[V]],
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> V:
        """
        Get a value from the cache or set it if not found.

        Args:
            key: The cache key
            getter: Function to get the value if not in cache
            ttl: Time-to-live for this entry, overrides default
            metadata: Additional metadata for this entry

        Returns:
            The cached or retrieved value
        """
        # Try to get from cache first
        value = await self.get(key)

        if value is not None:
            return value

        # Not in cache, get the value
        value = await getter()

        # Set in cache
        await self.set(key, value, ttl, metadata)

        return value

    async def set(
        self,
        key: K,
        value: V,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live for this entry, overrides default
            metadata: Additional metadata for this entry
        """
        now = time.time()
        ttl_value = ttl if ttl is not None else self.ttl
        expires_at = now + ttl_value if ttl_value is not None else None

        # Estimate size
        size = self._estimate_size(value)

        # Create entry
        entry = CacheEntry(
            value=value,
            created_at=now,
            expires_at=expires_at,
            last_accessed=now,
            access_count=0,
            size=size,
            metadata=metadata or {},
        )

        async with self._lock:
            # Check if we need to evict entries
            if self.max_size is not None and len(self._cache) >= self.max_size:
                await self._evict_entries()

            # Check if we need to evict based on size
            if self.max_bytes is not None:
                existing_size = self._total_bytes
                if key in self._cache:
                    existing_size -= self._cache[key].size

                if existing_size + size > self.max_bytes:
                    await self._evict_entries(needed_bytes=size)

            # Update total size
            if key in self._cache:
                self._total_bytes -= self._cache[key].size

            self._total_bytes += size

            # Store in cache
            self._cache[key] = entry

    async def delete(self, key: K) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False if not found
        """
        async with self._lock:
            return self._remove_entry(key)

    def _remove_entry(self, key: K) -> bool:
        """
        Remove an entry from the cache.

        Args:
            key: The cache key

        Returns:
            True if the entry was removed, False if not found
        """
        if key in self._cache:
            # Update total size
            self._total_bytes -= self._cache[key].size

            # Remove from cache
            del self._cache[key]
            return True

        return False

    async def _evict_entries(self, needed_bytes: Optional[int] = None) -> int:
        """
        Evict entries from the cache.

        Args:
            needed_bytes: Number of bytes needed, for size-based eviction

        Returns:
            Number of entries evicted
        """
        if not self._cache:
            return 0

        # Get entries to evict
        entries_to_evict: list[K] = []

        # First, remove expired entries
        now = time.time()
        expired_keys = [k for k, v in self._cache.items() if v.is_expired(now)]

        for key in expired_keys:
            self._remove_entry(key)
            self._expirations += 1

        # If we still need to evict based on strategy
        if (
            (self.max_size is not None and len(self._cache) > self.max_size)
            or (self.max_bytes is not None and self._total_bytes > self.max_bytes)
            or (needed_bytes is not None)
        ):
            # Sort entries based on strategy
            if self.strategy == CacheStrategy.LRU:
                # Least recently used
                sorted_entries = sorted(
                    self._cache.items(), key=lambda x: x[1].last_accessed
                )
            elif self.strategy == CacheStrategy.FIFO:
                # First in, first out
                sorted_entries = sorted(
                    self._cache.items(), key=lambda x: x[1].created_at
                )
            elif self.strategy == CacheStrategy.LFU:
                # Least frequently used
                sorted_entries = sorted(
                    self._cache.items(), key=lambda x: x[1].access_count
                )
            else:
                # Default to LRU
                sorted_entries = sorted(
                    self._cache.items(), key=lambda x: x[1].last_accessed
                )

            # Evict entries until we have enough space
            freed_bytes = 0
            for key, entry in sorted_entries:
                if needed_bytes is not None and freed_bytes >= needed_bytes:
                    break

                if (
                    self.max_size is not None
                    and len(self._cache) - len(entries_to_evict) <= self.max_size
                ):
                    break

                if (
                    self.max_bytes is not None
                    and self._total_bytes - freed_bytes <= self.max_bytes
                ):
                    break

                entries_to_evict.append(key)
                freed_bytes += entry.size

            # Remove evicted entries
            for key in entries_to_evict:
                self._remove_entry(key)
                self._evictions += 1

        return len(expired_keys) + len(entries_to_evict)

    async def clear(self) -> int:
        """
        Clear the cache.

        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._total_bytes = 0
            return count

    async def cleanup(self) -> int:
        """
        Clean up expired entries.

        Returns:
            Number of entries cleaned up
        """
        async with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._cache.items() if v.is_expired(now)]

            for key in expired_keys:
                self._remove_entry(key)
                self._expirations += 1

            return len(expired_keys)

    def _estimate_size(self, value: V) -> int:
        """
        Estimate the size of a value in bytes.

        Args:
            value: The value to estimate

        Returns:
            Estimated size in bytes
        """
        try:
            # Try pickle serialization for accurate size
            serialized = pickle.dumps(value)
            return len(serialized)
        except (pickle.PickleError, TypeError):
            # Fall back to a rough estimate
            if isinstance(value, str):
                return len(value.encode("utf-8"))
            elif isinstance(value, bytes):
                return len(value)
            elif isinstance(value, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v)
                    for k, v in value.items()
                )
            elif isinstance(value, (list, tuple, set)):
                return sum(self._estimate_size(item) for item in value)
            else:
                # Default estimate
                return 100  # Rough estimate for small objects

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        hit_rate = 0.0
        total_operations = self._hits + self._misses
        if total_operations > 0:
            hit_rate = self._hits / total_operations

        async with self._lock:
            return {
                "name": self.name,
                "strategy": self.strategy.value,
                "size": len(self._cache),
                "max_size": self.max_size,
                "bytes": self._total_bytes,
                "max_bytes": self.max_bytes,
                "ttl": self.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "expirations": self._expirations,
                "uptime": time.time() - self._start_time,
            }


class QueryCache(Generic[K, V]):
    """
    Cache for database query results.

    This cache is specialized for database queries with:
    - Query parameter normalization
    - Tag-based invalidation
    - Background refresh
    - Stale-while-revalidate behavior
    """

    def __init__(
        self,
        name: str,
        strategy: CacheStrategy = CacheStrategy.LRU,
        max_size: Optional[int] = 1000,
        max_bytes: Optional[int] = None,
        ttl: Optional[float] = 60.0,
        stale_ttl: Optional[float] = 300.0,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the query cache.

        Args:
            name: Name of the cache
            strategy: Cache eviction strategy
            max_size: Maximum number of items in the cache
            max_bytes: Maximum size of the cache in bytes
            ttl: Time-to-live for cache entries in seconds
            stale_ttl: Time-to-live for stale cache entries in seconds
            logger: Optional logger instance
        """
        self.name = name
        self.ttl = ttl
        self.stale_ttl = stale_ttl or (ttl * 5 if ttl else 300.0)
        self.logger = logger or logging.getLogger(__name__)

        # Create the underlying cache
        self.cache = Cache(
            name=name,
            strategy=strategy,
            max_size=max_size,
            max_bytes=max_bytes,
            ttl=stale_ttl,  # Use stale TTL for the underlying cache
            logger=logger,
        )

        # Query tag mappings for invalidation
        self._tag_to_keys: Dict[str, Set[K]] = {}
        self._key_to_tags: Dict[K, Set[str]] = {}
        self._tag_lock = AsyncLock()

        # Background refresh
        self._refresh_tasks: Dict[K, asyncio.Task] = {}
        self._refresh_lock = AsyncLock()

    async def get(
        self,
        key: K,
        default: Optional[V] = None,
    ) -> Optional[V]:
        """
        Get a query result from the cache.

        Args:
            key: The query key
            default: Default value if key not found

        Returns:
            The cached query result or default
        """
        # Get from cache
        entry = await self.cache.get(key)

        if entry is None:
            return default

        # Check if entry needs refresh
        now = time.time()
        metadata = entry.get("metadata", {})
        expires_at = metadata.get("expires_at")

        if expires_at is not None and now > expires_at:
            # Entry is stale but still usable
            refresh_func = metadata.get("refresh_func")

            if refresh_func is not None:
                # Start background refresh
                await self._start_refresh(key, refresh_func)

        # Return the result
        return entry.get("result")

    async def set(
        self,
        key: K,
        result: V,
        tags: list[str] | None = None,
        ttl: Optional[float] = None,
        refresh_func: Optional[Callable[[], Awaitable[V]]] = None,
    ) -> None:
        """
        Set a query result in the cache.

        Args:
            key: The query key
            result: The query result
            tags: List of tags for invalidation
            ttl: Time-to-live for this entry, overrides default
            refresh_func: Function to refresh the entry when stale
        """
        ttl_value = ttl if ttl is not None else self.ttl
        now = time.time()

        # Create metadata
        metadata = {
            "created_at": now,
            "expires_at": now + ttl_value if ttl_value is not None else None,
            "stale_at": now + self.stale_ttl if self.stale_ttl is not None else None,
            "tags": tags or [],
        }

        # Store refresh function if provided
        if refresh_func is not None:
            metadata["refresh_func"] = refresh_func

        # Create cache entry
        entry = {
            "result": result,
            "metadata": metadata,
        }

        # Store in cache
        await self.cache.set(key, entry)

        # Update tag mappings
        if tags:
            await self._update_tags(key, tags)

    async def invalidate(
        self,
        key: Optional[K] = None,
        tag: str | None = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            key: Specific key to invalidate
            tag: Tag to invalidate

        Returns:
            Number of entries invalidated
        """
        if key is not None:
            # Invalidate specific key
            await self.cache.delete(key)

            # Remove from tag mappings
            async with self._tag_lock:
                tags = self._key_to_tags.pop(key, set())

                for t in tags:
                    keys = self._tag_to_keys.get(t, set())
                    keys.discard(key)

                    if not keys:
                        self._tag_to_keys.pop(t, None)

            return 1

        elif tag is not None:
            # Invalidate by tag
            count = 0

            async with self._tag_lock:
                keys = self._tag_to_keys.pop(tag, set())

                for k in keys:
                    await self.cache.delete(k)

                    # Update key_to_tags
                    tags = self._key_to_tags.get(k, set())
                    tags.discard(tag)

                    if not tags:
                        self._key_to_tags.pop(k, None)

                    count += 1

            return count

        else:
            # Invalidate all
            count = await self.cache.clear()

            # Clear tag mappings
            async with self._tag_lock:
                self._tag_to_keys.clear()
                self._key_to_tags.clear()

            return count

    async def _update_tags(self, key: K, tags: list[str]) -> None:
        """
        Update tag mappings for a key.

        Args:
            key: The query key
            tags: List of tags
        """
        async with self._tag_lock:
            # Remove old tags
            old_tags = self._key_to_tags.pop(key, set())

            for tag in old_tags:
                keys = self._tag_to_keys.get(tag, set())
                keys.discard(key)

                if not keys:
                    self._tag_to_keys.pop(tag, None)

            # Add new tags
            self._key_to_tags[key] = set(tags)

            for tag in tags:
                if tag not in self._tag_to_keys:
                    self._tag_to_keys[tag] = set()

                self._tag_to_keys[tag].add(key)

    async def _start_refresh(
        self,
        key: K,
        refresh_func: Any,
    ) -> None:
        """
        Start background refresh for a cache entry.

        Args:
            key: The query key
            refresh_func: Function to refresh the entry
        """
        async with self._refresh_lock:
            # Check if already refreshing
            if key in self._refresh_tasks and not self._refresh_tasks[key].done():
                return

            # Create and start refresh task
            self._refresh_tasks[key] = asyncio.create_task(
                self._refresh_entry(key, refresh_func)
            )

    async def _refresh_entry(
        self,
        key: K,
        refresh_func: Any,
    ) -> None:
        """
        Refresh a cache entry.

        Args:
            key: The query key
            refresh_func: Function to refresh the entry
        """
        try:
            # Call the refresh function
            result = await refresh_func()

            # Get existing entry
            entry = await self.cache.get(key)

            if entry is None:
                # Entry was removed during refresh
                return

            # Update entry with new result
            metadata = entry.get("metadata", {})
            tags = metadata.get("tags", [])

            await self.set(
                key=key,
                result=result,
                tags=tags,
                refresh_func=refresh_func,
            )

            self.logger.debug(f"Refreshed cache entry: {key}")

        except Exception as e:
            self.logger.warning(f"Error refreshing cache entry {key}: {str(e)}")

        finally:
            # Remove from refresh tasks
            async with self._refresh_lock:
                self._refresh_tasks.pop(key, None)

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        # Get base stats
        stats = await self.cache.get_stats()

        # Add query cache stats
        async with self._tag_lock, self._refresh_lock:
            stats.update(
                {
                    "tags": len(self._tag_to_keys),
                    "tagged_keys": sum(
                        len(keys) for keys in self._tag_to_keys.values()
                    ),
                    "active_refreshes": sum(
                        1 for task in self._refresh_tasks.values() if not task.done()
                    ),
                }
            )

        return stats


def normalize_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Normalize a SQL query for caching.

    This removes comments, extra whitespace, and normalizes parameters.

    Args:
        query: SQL query string
        params: Query parameters

    Returns:
        Normalized query and parameters
    """
    # Remove comments
    lines = []
    for line in query.split("\n"):
        # Remove inline comments
        if "--" in line:
            line = line.split("--")[0]

        # Keep non-empty lines
        if line.strip():
            lines.append(line)

    # Rejoin lines and normalize whitespace
    normalized = " ".join(line.strip() for line in lines)

    # Replace multiple spaces with a single space
    normalized = " ".join(normalized.split())

    # Lowercase keywords (optional)
    # normalized = re.sub(r'\b(SELECT|FROM|WHERE|JOIN|AND|OR|GROUP BY|ORDER BY|LIMIT|OFFSET)\b',
    #                     lambda m: m.group(0).lower(), normalized)

    # Normalize parameters if provided
    normalized_params = None
    if params:
        # For named parameters, sort by name
        if isinstance(params, dict):
            normalized_params = dict(sorted(params.items()))
        else:
            # For positional parameters, keep as is
            normalized_params = params

    return normalized, normalized_params


def generate_cache_key(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    prefix: str = "query",
) -> str:
    """
    Generate a cache key for a query.

    Args:
        query: SQL query string
        params: Query parameters
        prefix: Cache key prefix

    Returns:
        Cache key
    """
    # Normalize query and parameters
    normalized_query, normalized_params = normalize_query(query, params)

    # Create key components
    key_parts = [prefix, normalized_query]

    # Add parameters if present
    if normalized_params:
        # Serialize parameters to JSON
        try:
            params_str = json.dumps(normalized_params, sort_keys=True)
            key_parts.append(params_str)
        except (TypeError, ValueError):
            # Fall back to string representation for non-JSON serializable params
            params_str = str(normalized_params)
            key_parts.append(params_str)

    # Join and hash the key parts
    key_str = "|".join(key_parts)
    return f"{prefix}:{hashlib.md5(key_str.encode('utf-8')).hexdigest()}"


def get_cache_tags_for_model(model_class: Any) -> list[str]:
    """
    Get cache tags for a model class.

    Args:
        model_class: The model class

    Returns:
        List of cache tags
    """
    # Get class name
    class_name = model_class.__name__

    # Get table name if available
    table_name = getattr(model_class, "__tablename__", class_name.lower())

    # Create tags
    tags = [
        f"model:{class_name}",
        f"table:{table_name}",
    ]

    return tags


# Module-level singleton instance
_cache_manager_instance: Optional["CacheManager"] = None


def get_cache_manager(
    registry: Optional[ResourceRegistry] = None,
    logger: logging.Logger | None = None,
) -> "CacheManager":
    """
    Get the global cache manager.

    Args:
        registry: Optional resource registry
        logger: Optional logger instance

    Returns:
        The cache manager instance
    """
    global _cache_manager_instance

    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(registry, logger)

    return _cache_manager_instance


class CacheManager:
    """
    Manager for caches in the application.

    This class provides:
    - Centralized cache management
    - Cache creation and retrieval
    - Statistics and monitoring
    - Cleanup and maintenance
    """

    def __init__(
        self,
        registry: Optional[ResourceRegistry] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the cache manager.

        Args:
            registry: Optional resource registry
            logger: Optional logger instance
        """

        self.registry = registry or get_resource_registry()
        self.logger = logger or logging.getLogger(__name__)

        # Caches
        self._caches: Dict[str, Cache] = {}
        self._query_caches: Dict[str, QueryCache] = {}
        self._cache_lock = AsyncLock()

        # Maintenance
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 60.0  # seconds
        self._running = False

    async def start(self) -> None:
        """
        Start the cache manager.

        This starts the cleanup task and registers with the resource registry.
        """
        if self._running:
            return

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(), name="cache_manager_cleanup"
        )

        # Register with resource registry
        await self.registry.register("cache_manager", self)

        self._running = True
        self.logger.info("Cache manager started")

    async def stop(self) -> None:
        """
        Stop the cache manager.

        This stops the cleanup task and releases resources.
        """
        if not self._running:
            return

        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
            self._cleanup_task = None

        self._running = False
        self.logger.info("Cache manager stopped")

    async def close(self) -> None:
        """
        Close the cache manager.

        Alias for stop().
        """
        await self.stop()

    async def _cleanup_loop(self) -> None:
        """
        Periodic cleanup of caches.
        """
        try:
            while True:
                # Wait for next cleanup
                await asyncio.sleep(self._cleanup_interval)

                # Clean up caches
                await self._cleanup_caches()

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            self.logger.debug("Cache cleanup task cancelled")
            raise

        except Exception as e:
            self.logger.error(f"Error in cache cleanup: {str(e)}", exc_info=True)

    async def _cleanup_caches(self) -> None:
        """
        Clean up expired entries in all caches.
        """
        async with self._cache_lock:
            # Clean up regular caches
            for name, cache in self._caches.items():
                try:
                    count = await cache.cleanup()
                    if count > 0:
                        self.logger.debug(
                            f"Cleaned up {count} entries from cache '{name}'"
                        )
                except Exception as e:
                    self.logger.warning(f"Error cleaning up cache '{name}': {str(e)}")

            # Clean up query caches
            for name, cache in self._query_caches.items():
                try:
                    count = await cache.cache.cleanup()
                    if count > 0:
                        self.logger.debug(
                            f"Cleaned up {count} entries from query cache '{name}'"
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Error cleaning up query cache '{name}': {str(e)}"
                    )

    async def get_cache(
        self,
        name: str,
        create_if_missing: bool = True,
        **kwargs: Any,
    ) -> Cache:
        """
        Get a cache by name.

        Args:
            name: Name of the cache
            create_if_missing: Whether to create the cache if it doesn't exist
            **kwargs: Additional arguments for cache creation

        Returns:
            The cache

        Raises:
            ValueError: If cache doesn't exist and create_if_missing is False
        """
        async with self._cache_lock:
            if name in self._caches:
                return self._caches[name]

            if not create_if_missing:
                raise ValueError(f"Cache '{name}' not found")

            # Create new cache
            cache = Cache(name=name, **kwargs)
            self._caches[name] = cache

            return cache

    async def get_query_cache(
        self,
        name: str,
        create_if_missing: bool = True,
        **kwargs: Any,
    ) -> QueryCache:
        """
        Get a query cache by name.

        Args:
            name: Name of the cache
            create_if_missing: Whether to create the cache if it doesn't exist
            **kwargs: Additional arguments for cache creation

        Returns:
            The query cache

        Raises:
            ValueError: If cache doesn't exist and create_if_missing is False
        """
        async with self._cache_lock:
            if name in self._query_caches:
                return self._query_caches[name]

            if not create_if_missing:
                raise ValueError(f"Query cache '{name}' not found")

            # Create new cache
            cache = QueryCache(name=name, **kwargs)
            self._query_caches[name] = cache

            return cache

    async def invalidate_cache(
        self,
        name: str,
        key: Optional[Any] = None,
    ) -> int:
        """
        Invalidate a cache.

        Args:
            name: Name of the cache
            key: Optional key to invalidate

        Returns:
            Number of entries invalidated
        """
        async with self._cache_lock:
            # Check if it's a regular cache
            if name in self._caches:
                cache = self._caches[name]

                if key is not None:
                    await cache.delete(key)
                    return 1
                else:
                    return await cache.clear()

            # Check if it's a query cache
            elif name in self._query_caches:
                cache = self._query_caches[name]

                if key is not None:
                    return await cache.invalidate(key=key)
                else:
                    return await cache.invalidate()

            # Cache not found
            return 0

    async def invalidate_by_tags(
        self,
        tags: Union[str, list[str]],
    ) -> int:
        """
        Invalidate cache entries by tags.

        Args:
            tags: Tag or list of tags to invalidate

        Returns:
            Number of entries invalidated
        """
        # Convert single tag to list
        tag_list = [tags] if isinstance(tags, str) else tags

        count = 0

        # Invalidate in all query caches
        async with self._cache_lock:
            for cache in self._query_caches.values():
                for tag in tag_list:
                    count += await cache.invalidate(tag=tag)

        return count

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        stats = {
            "caches": {},
            "query_caches": {},
            "total_caches": 0,
            "total_entries": 0,
            "total_bytes": 0,
            "total_hits": 0,
            "total_misses": 0,
        }

        async with self._cache_lock:
            # Regular caches
            for name, cache in self._caches.items():
                cache_stats = await cache.get_stats()
                stats["caches"][name] = cache_stats

                # Update totals
                stats["total_caches"] += 1
                stats["total_entries"] += cache_stats["size"]
                stats["total_bytes"] += cache_stats["bytes"]
                stats["total_hits"] += cache_stats["hits"]
                stats["total_misses"] += cache_stats["misses"]

            # Query caches
            for name, cache in self._query_caches.items():
                cache_stats = await cache.get_stats()
                stats["query_caches"][name] = cache_stats

                # Update totals
                stats["total_caches"] += 1
                stats["total_entries"] += cache_stats["size"]
                stats["total_bytes"] += cache_stats["bytes"]
                stats["total_hits"] += cache_stats["hits"]
                stats["total_misses"] += cache_stats["misses"]

        return stats


# Function already defined above


def cached(
    ttl: Optional[float] = 300.0,
    cache_name: str | None = None,
    key_prefix: str | None = None,
    strategy: CacheStrategy = CacheStrategy.LRU,
) -> Callable:
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live for cache entries in seconds
        cache_name: Name of the cache to use
        key_prefix: Prefix for cache keys
        strategy: Cache eviction strategy

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        # Get function signature
        sig = inspect.signature(func)
        is_method = inspect.ismethod(func) or "self" in sig.parameters

        # Generate cache name if not provided
        nonlocal cache_name
        if cache_name is None:
            module = func.__module__
            name = func.__qualname__
            cache_name = f"{module}.{name}"

        # Generate key prefix if not provided
        nonlocal key_prefix
        if key_prefix is None:
            key_prefix = func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache manager
            manager = get_cache_manager()

            # Get cache
            cache = await manager.get_cache(
                name=cache_name,
                strategy=strategy,
                ttl=ttl,
            )

            # Generate cache key
            if is_method:
                # Skip 'self' or 'cls' for methods
                key_args = args[1:]
            else:
                key_args = args

            # Convert args and kwargs to a string for the key
            try:
                key_str = f"{key_prefix}:{key_args!r}:{kwargs!r}"
                key = hashlib.md5(key_str.encode("utf-8")).hexdigest()
            except Exception:
                # Fall back to simple key if args are not hashable
                key = f"{key_prefix}:{id(args)}:{id(kwargs)}"

            # Try to get from cache
            result = await cache.get(key)

            if result is not None:
                return result

            # Not in cache, call the function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(key, result)

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we can't use the cache directly
            # Just call the function
            return func(*args, **kwargs)

        # Use appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def query_cached(
    ttl: Optional[float] = 60.0,
    cache_name: str = "query_cache",
    tags: list[str] | None = None,
) -> Callable:
    """
    Decorator for caching database query results.

    Args:
        ttl: Time-to-live for cache entries in seconds
        cache_name: Name of the cache to use
        tags: Tags for cache invalidation

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache manager
            manager = get_cache_manager()

            # Get query cache
            cache = await manager.get_query_cache(
                name=cache_name,
                ttl=ttl,
            )

            # Generate cache key
            try:
                key_str = f"{func.__qualname__}:{args!r}:{kwargs!r}"
                key = hashlib.md5(key_str.encode("utf-8")).hexdigest()
            except Exception:
                # Fall back to simple key if args are not hashable
                key = f"{func.__qualname__}:{id(args)}:{id(kwargs)}"

            # Define refresh function
            async def refresh_func() -> Any:
                return await func(*args, **kwargs)

            # Try to get from cache or set
            return await cache.get_or_set(
                key=key,
                getter=refresh_func,
                tags=tags,
                ttl=ttl,
                refresh_func=refresh_func,
            )

        # Only works for async functions
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("query_cached can only be used with async functions")

        return wrapper

    return decorator
