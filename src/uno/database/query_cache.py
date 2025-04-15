"""
Query cache system for database operations.

This module provides a high-performance query caching system that integrates
with SQLAlchemy to cache frequently executed queries and reduce database load.

Features:
- Automatic query result caching
- Multiple cache storage backends
- Configurable cache invalidation strategies
- Query dependency tracking
- Support for both raw SQL and ORM queries
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union, Type, TypeVar, Generic, cast, Callable
import asyncio
import hashlib
import inspect
import json
import logging
import time
import functools
from dataclasses import dataclass, field
from enum import Enum
import pickle

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.result import Result
from sqlalchemy.sql import Select, Executable
from sqlalchemy.orm import DeclarativeMeta

from uno.core.async_integration import AsyncCache
from uno.core.errors.result import Result as OpResult, Success, Failure
from uno.settings import uno_settings


T = TypeVar('T')
ModelT = TypeVar('ModelT', bound=DeclarativeMeta)


class CacheBackend(Enum):
    """
    Cache storage backends for query results.
    
    Different backends optimize for different access patterns:
    - MEMORY: Local in-memory cache (fastest, not shared between processes)
    - REDIS: Distributed cache using Redis (shared between processes)
    - HYBRID: Two-level cache using both memory and Redis
    """
    
    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"


class CacheStrategy(Enum):
    """
    Caching strategies for query results.
    
    Different strategies optimize for different workloads:
    - SIMPLE: Basic time-based caching
    - SMART: Adaptive caching based on query frequency and complexity
    - DEPENDENCY: Track dependencies between queries for invalidation
    """
    
    SIMPLE = "simple"
    SMART = "smart"
    DEPENDENCY = "dependency"


@dataclass
class QueryCacheConfig:
    """
    Configuration for the query cache system.
    
    Controls behavior of caching, invalidation, and storage.
    """
    
    # Cache behavior
    enabled: bool = True
    strategy: CacheStrategy = CacheStrategy.SIMPLE
    backend: CacheBackend = CacheBackend.MEMORY
    
    # Cache sizing and expiration
    default_ttl: float = 300.0  # 5 minutes
    max_entries: int = 10000
    
    # Advanced settings
    track_dependencies: bool = True
    auto_invalidate: bool = True
    log_hits: bool = False
    log_misses: bool = False
    
    # Smart caching settings
    adaptive_ttl: bool = True
    min_ttl: float = 10.0
    max_ttl: float = 3600.0  # 1 hour
    
    # Query analysis
    analyze_complexity: bool = True
    complexity_factor: float = 1.0
    
    # Redis settings (when using REDIS or HYBRID backend)
    redis_url: str = "redis://localhost:6379/0"
    redis_prefix: str = "query_cache:"


@dataclass
class QueryCacheStats:
    """
    Statistics for the query cache system.
    
    Tracks performance and utilization metrics.
    """
    
    # Cache performance
    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    evictions: int = 0
    
    # Timing stats
    total_hit_time: float = 0.0
    total_miss_time: float = 0.0
    
    # Size stats
    current_entries: int = 0
    total_entries: int = 0
    
    # Dependency stats
    dependencies_tracked: int = 0
    cascading_invalidations: int = 0
    
    def record_hit(self, duration: float) -> None:
        """Record a cache hit."""
        self.hits += 1
        self.total_hit_time += duration
    
    def record_miss(self, duration: float) -> None:
        """Record a cache miss."""
        self.misses += 1
        self.total_miss_time += duration
    
    def record_invalidation(self) -> None:
        """Record a cache invalidation."""
        self.invalidations += 1
    
    def record_eviction(self) -> None:
        """Record a cache eviction."""
        self.evictions += 1
    
    def record_entry_added(self) -> None:
        """Record a new cache entry."""
        self.current_entries += 1
        self.total_entries += 1
    
    def record_entry_removed(self) -> None:
        """Record a removed cache entry."""
        self.current_entries = max(0, self.current_entries - 1)
    
    def record_dependency(self) -> None:
        """Record a tracked dependency."""
        self.dependencies_tracked += 1
    
    def record_cascading_invalidation(self) -> None:
        """Record a cascading invalidation."""
        self.cascading_invalidations += 1
    
    @property
    def hit_rate(self) -> float:
        """Get the cache hit rate (0.0-1.0)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    @property
    def avg_hit_time(self) -> float:
        """Get the average hit access time in seconds."""
        if self.hits == 0:
            return 0.0
        return self.total_hit_time / self.hits
    
    @property
    def avg_miss_time(self) -> float:
        """Get the average miss access time in seconds."""
        if self.misses == 0:
            return 0.0
        return self.total_miss_time / self.misses
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the cache statistics.
        
        Returns:
            Dictionary of summarized statistics
        """
        return {
            "performance": {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": self.hit_rate,
                "avg_hit_time": self.avg_hit_time,
                "avg_miss_time": self.avg_miss_time,
            },
            "size": {
                "current_entries": self.current_entries,
                "total_entries": self.total_entries,
            },
            "invalidation": {
                "invalidations": self.invalidations,
                "evictions": self.evictions,
                "dependencies_tracked": self.dependencies_tracked,
                "cascading_invalidations": self.cascading_invalidations,
            },
        }


class QueryCacheKey:
    """
    Key generator for uniquely identifying cacheable queries.
    
    Handles both raw SQL and ORM queries with consistent hashing.
    """
    
    @staticmethod
    def hash_query(
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
        table_names: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a hash for a query.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Query parameters
            table_names: List of affected table names
            
        Returns:
            Hash string for the query
        """
        # Normalize the query to a string
        if isinstance(query, str):
            query_str = query
        elif hasattr(query, "compile"):
            # SQLAlchemy query object
            compiled = query.compile(compile_kwargs={"literal_binds": True})
            query_str = str(compiled)
        else:
            # Fallback for other executable types
            query_str = str(query)
        
        # Create a combined string for hashing
        parts = [query_str]
        
        # Add parameters if provided
        if params:
            # Sort parameters for consistent hashing
            param_str = json.dumps(params, sort_keys=True)
            parts.append(param_str)
        
        # Add table names if provided
        if table_names:
            # Sort table names for consistent hashing
            table_str = ",".join(sorted(table_names))
            parts.append(table_str)
        
        # Create a hash of the combined string
        combined = "|".join(parts)
        return hashlib.md5(combined.encode("utf-8")).hexdigest()
    
    @staticmethod
    def from_select(
        select_query: Select,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a cache key from a SQLAlchemy select query.
        
        Args:
            select_query: SQLAlchemy select query
            params: Optional query parameters
            
        Returns:
            Cache key for the query
        """
        # Extract table names from select query
        table_names = []
        
        # Handle different SQLAlchemy versions
        if hasattr(select_query, "froms") and select_query.froms:
            # Extract from column or table
            for from_clause in select_query.froms:
                if hasattr(from_clause, "__tablename__"):
                    table_names.append(from_clause.__tablename__)
                elif hasattr(from_clause, "name"):
                    table_names.append(from_clause.name)
        
        # Handle selectable with different interface
        elif hasattr(select_query, "selectable"):
            selectable = select_query.selectable
            if hasattr(selectable, "__tablename__"):
                table_names.append(selectable.__tablename__)
            elif hasattr(selectable, "name"):
                table_names.append(selectable.name)
        
        # Generate the hash
        return QueryCacheKey.hash_query(select_query, params, table_names)
    
    @staticmethod
    def from_text(
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        table_names: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a cache key from a SQL text query.
        
        Args:
            sql: SQL query string
            params: Optional query parameters
            table_names: Optional list of affected table names
            
        Returns:
            Cache key for the query
        """
        return QueryCacheKey.hash_query(sql, params, table_names)
    
    @staticmethod
    def from_function(
        func_obj: Any,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Generate a cache key from a function call.
        
        Args:
            func_obj: Function object
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key for the function call
        """
        # Get function name and module
        func_name = func_obj.__name__
        module_name = func_obj.__module__
        
        # Serialize arguments to a stable format
        serialized_args = []
        for arg in args:
            try:
                # Try to use JSON for stability
                json_str = json.dumps(arg, sort_keys=True)
                serialized_args.append(json_str)
            except (TypeError, OverflowError):
                # Fall back to the string representation
                serialized_args.append(str(arg))
        
        # Serialize keyword arguments
        serialized_kwargs = {}
        for key, value in sorted(kwargs.items()):
            try:
                # Try to use JSON for stability
                json_str = json.dumps(value, sort_keys=True)
                serialized_kwargs[key] = json_str
            except (TypeError, OverflowError):
                # Fall back to the string representation
                serialized_kwargs[key] = str(value)
        
        # Combine all parts
        parts = [
            module_name,
            func_name,
            ",".join(serialized_args),
            json.dumps(serialized_kwargs, sort_keys=True),
        ]
        
        # Create a hash of the combined string
        combined = "|".join(parts)
        return hashlib.md5(combined.encode("utf-8")).hexdigest()


@dataclass
class CachedResult(Generic[T]):
    """
    Wrapper for a cached query result.
    
    Stores the result along with metadata for cache management.
    """
    
    # Result data
    data: T
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    query_time: float = 0.0
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    # Dependencies
    dependencies: Set[str] = field(default_factory=set)
    
    def update_access(self) -> None:
        """Update access metrics when result is accessed."""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if the result has expired."""
        return time.time() > self.expires_at
    
    @property
    def age(self) -> float:
        """Get the age of the cached result in seconds."""
        return time.time() - self.created_at
    
    @property
    def idle_time(self) -> float:
        """Get the idle time since last access in seconds."""
        return time.time() - self.last_accessed
    
    def get_value(self) -> T:
        """Get the cached data value."""
        self.update_access()
        return self.data
    
    def add_dependency(self, table_name: str) -> None:
        """Add a dependency to the cached result."""
        self.dependencies.add(table_name)


class QueryCache:
    """
    Cache system for database query results.
    
    Provides caching for both raw SQL and ORM queries with
    automatic invalidation and dependency tracking.
    """
    
    def __init__(
        self,
        config: Optional[QueryCacheConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the query cache.
        
        Args:
            config: Optional configuration for the cache
            logger: Optional logger instance
        """
        self.config = config or QueryCacheConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # Memory cache storage
        self._cache: Dict[str, CachedResult[Any]] = {}
        
        # Statistics
        self.stats = QueryCacheStats()
        
        # Dependency tracking
        self._dependencies: Dict[str, Set[str]] = {}  # table_name -> set of cache keys
        
        # Redis client (initialized lazily)
        self._redis_client = None
        
        # Async cache for intelligent object handling
        self._object_cache = AsyncCache[str, Any](
            ttl=self.config.default_ttl,
            logger=self.logger,
        )
    
    async def get_redis_client(self):
        """Get or create the Redis client."""
        if self._redis_client is None:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(self.config.redis_url)
        return self._redis_client
    
    async def get(self, key: str) -> OpResult[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Result containing the cached value or an error
        """
        start_time = time.time()
        
        # Check if caching is disabled
        if not self.config.enabled:
            self.stats.record_miss(time.time() - start_time)
            return Failure(Exception("Caching is disabled"))
        
        # Try to get from in-memory cache first
        cached_result = self._cache.get(key)
        
        if cached_result is not None:
            # Check if the result has expired
            if cached_result.is_expired():
                self._cache.pop(key, None)
                self.stats.record_entry_removed()
                self.stats.record_miss(time.time() - start_time)
                
                if self.config.log_misses:
                    self.logger.debug(f"Cache miss (expired): {key}")
                
                return Failure(Exception("Cache entry expired"))
            
            # Record cache hit
            duration = time.time() - start_time
            self.stats.record_hit(duration)
            
            if self.config.log_hits:
                self.logger.debug(
                    f"Cache hit: {key} (age: {cached_result.age:.2f}s, "
                    f"accesses: {cached_result.access_count})"
                )
            
            # Update access metrics
            cached_result.update_access()
            
            return Success(cached_result.get_value())
        
        # If using Redis or Hybrid backend, try Redis
        if self.config.backend in (CacheBackend.REDIS, CacheBackend.HYBRID):
            try:
                redis_client = await self.get_redis_client()
                redis_key = f"{self.config.redis_prefix}{key}"
                
                # Get from Redis
                value = await redis_client.get(redis_key)
                
                if value is not None:
                    # Deserialize the value
                    cached_result = pickle.loads(value)
                    
                    # Check if expired
                    if cached_result.is_expired():
                        await redis_client.delete(redis_key)
                        self.stats.record_miss(time.time() - start_time)
                        
                        if self.config.log_misses:
                            self.logger.debug(f"Cache miss (Redis expired): {key}")
                        
                        return Failure(Exception("Redis cache entry expired"))
                    
                    # Store in memory for Hybrid backend
                    if self.config.backend == CacheBackend.HYBRID:
                        self._cache[key] = cached_result
                    
                    # Record cache hit
                    duration = time.time() - start_time
                    self.stats.record_hit(duration)
                    
                    if self.config.log_hits:
                        self.logger.debug(
                            f"Cache hit (Redis): {key} (age: {cached_result.age:.2f}s, "
                            f"accesses: {cached_result.access_count})"
                        )
                    
                    # Update access metrics
                    cached_result.update_access()
                    
                    return Success(cached_result.get_value())
            
            except Exception as e:
                self.logger.warning(f"Error accessing Redis cache: {str(e)}")
        
        # Record cache miss
        duration = time.time() - start_time
        self.stats.record_miss(duration)
        
        if self.config.log_misses:
            self.logger.debug(f"Cache miss: {key}")
        
        return Failure(Exception("Cache miss"))
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        dependencies: Optional[List[str]] = None,
        query_time: float = 0.0,
    ) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds
            dependencies: Optional list of table dependencies
            query_time: Optional execution time of the original query
        """
        # Check if caching is disabled
        if not self.config.enabled:
            return
        
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.config.default_ttl
        
        # Apply TTL limits if adaptive TTL is enabled
        if self.config.adaptive_ttl:
            ttl = max(self.config.min_ttl, min(ttl, self.config.max_ttl))
        
        # Create expiration timestamp
        expires_at = time.time() + ttl
        
        # Create cached result
        cached_result = CachedResult(
            data=value,
            expires_at=expires_at,
            query_time=query_time,
        )
        
        # Track dependencies if provided
        if dependencies and self.config.track_dependencies:
            for table_name in dependencies:
                cached_result.add_dependency(table_name)
                
                # Add to dependency tracking
                if table_name not in self._dependencies:
                    self._dependencies[table_name] = set()
                self._dependencies[table_name].add(key)
                
                # Update stats
                self.stats.record_dependency()
        
        # Store in memory cache
        self._cache[key] = cached_result
        self.stats.record_entry_added()
        
        # Store in Redis if using Redis or Hybrid backend
        if self.config.backend in (CacheBackend.REDIS, CacheBackend.HYBRID):
            try:
                redis_client = await self.get_redis_client()
                redis_key = f"{self.config.redis_prefix}{key}"
                
                # Serialize the cached result
                serialized = pickle.dumps(cached_result)
                
                # Store in Redis with TTL
                await redis_client.setex(
                    redis_key,
                    int(ttl),
                    serialized,
                )
            
            except Exception as e:
                self.logger.warning(f"Error storing in Redis cache: {str(e)}")
        
        # Check if we need to evict entries
        if len(self._cache) > self.config.max_entries:
            await self._evict_entries()
    
    async def invalidate(self, key: str) -> None:
        """
        Invalidate a specific cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        # Check if the key exists in memory
        removed = self._cache.pop(key, None)
        
        if removed:
            self.stats.record_invalidation()
            self.stats.record_entry_removed()
        
        # Remove from Redis if using Redis or Hybrid backend
        if self.config.backend in (CacheBackend.REDIS, CacheBackend.HYBRID):
            try:
                redis_client = await self.get_redis_client()
                redis_key = f"{self.config.redis_prefix}{key}"
                
                # Remove from Redis
                await redis_client.delete(redis_key)
            
            except Exception as e:
                self.logger.warning(f"Error invalidating Redis cache: {str(e)}")
    
    async def invalidate_by_table(self, table_name: str) -> None:
        """
        Invalidate all cache entries dependent on a table.
        
        Args:
            table_name: Table name to invalidate
        """
        # Get all cache keys dependent on the table
        dependent_keys = self._dependencies.get(table_name, set())
        
        if dependent_keys:
            # Create a copy since we'll be modifying during iteration
            keys_to_invalidate = list(dependent_keys)
            
            # Invalidate each key
            for key in keys_to_invalidate:
                await self.invalidate(key)
            
            # Update stats for cascading invalidation
            self.stats.record_cascading_invalidation()
            
            # Clear dependencies for this table
            self._dependencies[table_name] = set()
    
    async def invalidate_by_pattern(self, pattern: str) -> None:
        """
        Invalidate all cache entries matching a key pattern.
        
        Args:
            pattern: Key pattern to match (simple string contains matching)
        """
        # Find matching keys in memory
        matching_keys = [key for key in self._cache.keys() if pattern in key]
        
        # Invalidate each key
        for key in matching_keys:
            await self.invalidate(key)
        
        # Invalidate in Redis if using Redis or Hybrid backend
        if self.config.backend in (CacheBackend.REDIS, CacheBackend.HYBRID):
            try:
                redis_client = await self.get_redis_client()
                redis_pattern = f"{self.config.redis_prefix}*{pattern}*"
                
                # Find matching keys in Redis
                matching_redis_keys = await redis_client.keys(redis_pattern)
                
                # Delete the keys
                if matching_redis_keys:
                    await redis_client.delete(*matching_redis_keys)
            
            except Exception as e:
                self.logger.warning(f"Error invalidating Redis cache by pattern: {str(e)}")
    
    async def clear(self) -> None:
        """Clear the entire cache."""
        # Clear memory cache
        self._cache.clear()
        self._dependencies.clear()
        
        # Clear Redis if using Redis or Hybrid backend
        if self.config.backend in (CacheBackend.REDIS, CacheBackend.HYBRID):
            try:
                redis_client = await self.get_redis_client()
                redis_pattern = f"{self.config.redis_prefix}*"
                
                # Find all keys in Redis
                all_redis_keys = await redis_client.keys(redis_pattern)
                
                # Delete the keys
                if all_redis_keys:
                    await redis_client.delete(*all_redis_keys)
            
            except Exception as e:
                self.logger.warning(f"Error clearing Redis cache: {str(e)}")
        
        # Reset statistics
        self.stats = QueryCacheStats()
    
    async def _evict_entries(self) -> None:
        """Evict cache entries to make room for new ones."""
        # Calculate number of entries to evict
        entries_to_evict = len(self._cache) - self.config.max_entries + 10  # Evict a few extra to avoid frequent evictions
        
        if entries_to_evict <= 0:
            return
        
        # Find least recently used entries
        entries = list(self._cache.items())
        entries.sort(key=lambda x: x[1].last_accessed)
        
        # Evict the entries
        for i in range(min(entries_to_evict, len(entries))):
            key, _ = entries[i]
            self._cache.pop(key, None)
            
            # Remove from dependencies tracking
            for deps in self._dependencies.values():
                deps.discard(key)
            
            # Update stats
            self.stats.record_eviction()
            self.stats.record_entry_removed()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary of cache statistics
        """
        stats = self.stats.get_summary()
        
        # Add additional stats
        stats["config"] = {
            "backend": self.config.backend.value,
            "strategy": self.config.strategy.value,
            "default_ttl": self.config.default_ttl,
            "max_entries": self.config.max_entries,
        }
        
        return stats


# Cache decorators

def cached(
    ttl: Optional[float] = None,
    dependencies: Optional[List[str]] = None,
    key_builder: Optional[Callable[..., str]] = None,
    cache_instance: Optional[QueryCache] = None,
):
    """
    Decorator to cache the results of a function.
    
    Args:
        ttl: Optional time-to-live in seconds
        dependencies: Optional list of table dependencies
        key_builder: Optional function to build the cache key
        cache_instance: Optional QueryCache instance
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get or create cache instance
            cache = cache_instance or _get_default_cache()
            
            # Check if caching is disabled
            if not cache.config.enabled:
                return await func(*args, **kwargs)
            
            # Build the cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = QueryCacheKey.from_function(func, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            
            if cached_result.is_success:
                return cached_result.value
            
            # Execute the function
            start_time = time.time()
            result = await func(*args, **kwargs)
            query_time = time.time() - start_time
            
            # Cache the result
            await cache.set(
                cache_key,
                result,
                ttl=ttl,
                dependencies=dependencies,
                query_time=query_time,
            )
            
            return result
            
        return wrapper
    
    return decorator


def cached_query(
    ttl: Optional[float] = None,
    dependencies: Optional[List[str]] = None,
    cache_instance: Optional[QueryCache] = None,
):
    """
    Decorator to cache the results of a query function.
    
    Args:
        ttl: Optional time-to-live in seconds
        dependencies: Optional list of table dependencies
        cache_instance: Optional QueryCache instance
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract session from args or kwargs
            session = None
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break
            
            if session is None and "session" in kwargs:
                session = kwargs["session"]
            
            if session is None:
                # No session found, can't cache
                return await func(*args, **kwargs)
            
            # Get or create cache instance
            cache = cache_instance or _get_default_cache()
            
            # Check if caching is disabled
            if not cache.config.enabled:
                return await func(*args, **kwargs)
            
            # Build the cache key
            cache_key = QueryCacheKey.from_function(func, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            
            if cached_result.is_success:
                return cached_result.value
            
            # Execute the query function
            start_time = time.time()
            result = await func(*args, **kwargs)
            query_time = time.time() - start_time
            
            # Parse dependencies if not provided
            actual_dependencies = dependencies
            if actual_dependencies is None and cache.config.track_dependencies:
                # Inspect the function source to try to find table names
                actual_dependencies = []
                try:
                    source = inspect.getsource(func)
                    # Very simple heuristic to extract table names from function source
                    # This should be enhanced with proper parsing
                    table_candidates = []
                    if "from " in source.lower():
                        parts = source.lower().split("from ")
                        for part in parts[1:]:
                            table_part = part.split(" where ")[0].split(" join ")[0].strip()
                            if table_part and not table_part.startswith(("(", "select")):
                                table_candidates.append(table_part)
                    
                    for candidate in table_candidates:
                        # Clean up the candidate
                        clean_candidate = candidate.strip("'\"`()[]{} \t\n").split(".")[0]
                        if clean_candidate:
                            actual_dependencies.append(clean_candidate)
                except Exception:
                    # Failed to extract dependencies, continue without them
                    pass
            
            # Cache the result
            await cache.set(
                cache_key,
                result,
                ttl=ttl,
                dependencies=actual_dependencies,
                query_time=query_time,
            )
            
            return result
            
        return wrapper
    
    return decorator


# Helper functions

class QueryCacheManager:
    """
    Global manager for query cache instances.
    
    Provides centralized management of query caches.
    """
    
    _default_cache: Optional[QueryCache] = None
    _named_caches: Dict[str, QueryCache] = {}
    
    # Singleton instance (will be replaced with DI in the future)
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance.
        
        DEPRECATED: This method is maintained for backward compatibility only and will be removed.
        Use dependency injection via uno.dependencies.modern_provider.get_service() instead.
        
        Returns:
            QueryCacheManager instance
        """
        # Import at function level to avoid circular imports
        from uno.dependencies.modern_provider import register_singleton
        
        if cls._instance is None:
            cls._instance = QueryCacheManager()
            # Register with DI system for future use
            try:
                register_singleton(QueryCacheManager, cls._instance)
            except Exception:
                # Ignore errors if DI system is not initialized
                pass
                
        return cls._instance
    
    def get_default_cache(self) -> QueryCache:
        """
        Get the default query cache.
        
        Returns:
            Default QueryCache instance
        """
        if self._default_cache is None:
            self._default_cache = QueryCache()
        return self._default_cache
    
    def set_default_cache(self, cache: QueryCache) -> None:
        """
        Set the default query cache.
        
        Args:
            cache: QueryCache instance to use as default
        """
        self._default_cache = cache
    
    def get_named_cache(self, name: str) -> QueryCache:
        """
        Get a named query cache.
        
        Args:
            name: Name of the cache
            
        Returns:
            QueryCache instance
        """
        if name not in self._named_caches:
            self._named_caches[name] = QueryCache()
        return self._named_caches[name]
    
    def set_named_cache(self, name: str, cache: QueryCache) -> None:
        """
        Set a named query cache.
        
        Args:
            name: Name of the cache
            cache: QueryCache instance
        """
        self._named_caches[name] = cache
    
    def get_all_caches(self) -> Dict[str, QueryCache]:
        """
        Get all named caches.
        
        Returns:
            Dictionary of named caches
        """
        return dict(self._named_caches)
    
    async def clear_all_caches(self) -> None:
        """Clear all caches."""
        if self._default_cache:
            await self._default_cache.clear()
        
        for cache in self._named_caches.values():
            await cache.clear()


# Get the global cache manager (this will be replaced with DI in the future)
def _get_cache_manager() -> QueryCacheManager:
    """
    Get the global cache manager.
    
    This function provides a bridge between the legacy singleton pattern
    and the modern dependency injection system.
    
    Returns:
        QueryCacheManager instance
    """
    from uno.dependencies.modern_provider import get_service, register_singleton
    
    try:
        # Try to get from DI system first
        return get_service(QueryCacheManager)
    except Exception:
        # Fall back to singleton pattern temporarily
        manager = QueryCacheManager.get_instance()
        
        # Register with DI system for future use
        try:
            register_singleton(QueryCacheManager, manager)
        except Exception:
            # Ignore errors if DI system is not initialized
            pass
            
        return manager


def _get_default_cache() -> QueryCache:
    """
    Get the default query cache.
    
    Returns:
        Default QueryCache instance
    """
    return _get_cache_manager().get_default_cache()


def set_default_cache(cache: QueryCache) -> None:
    """
    Set the default query cache.
    
    Args:
        cache: QueryCache instance to use as default
    """
    _get_cache_manager().set_default_cache(cache)


def get_named_cache(name: str) -> QueryCache:
    """
    Get a named query cache.
    
    Args:
        name: Name of the cache
        
    Returns:
        QueryCache instance
    """
    return _get_cache_manager().get_named_cache(name)


def set_named_cache(name: str, cache: QueryCache) -> None:
    """
    Set a named query cache.
    
    Args:
        name: Name of the cache
        cache: QueryCache instance
    """
    _get_cache_manager().set_named_cache(name, cache)


async def clear_all_caches() -> None:
    """Clear all query caches."""
    await _get_cache_manager().clear_all_caches()