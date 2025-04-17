"""
Cache service for read models.

This module defines the cache service for read models, providing
an abstraction over different caching mechanisms.
"""

import logging
import json
import hashlib
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast
from datetime import datetime, UTC, timedelta

from pydantic import BaseModel, Field

from uno.read_model.read_model import ReadModel

T = TypeVar('T', bound=ReadModel)


class CacheConfig(BaseModel):
    """
    Configuration for read model caching.
    
    Attributes:
        enabled: Whether caching is enabled
        ttl_seconds: Default time-to-live for cached items
        namespace: Namespace prefix for cache keys
        invalidate_on_update: Whether to invalidate cache on model updates
        max_cache_size: Maximum number of items to cache (for in-memory cache)
    """
    
    enabled: bool = True
    ttl_seconds: int = 300  # 5 minutes
    namespace: str = "read_model"
    invalidate_on_update: bool = True
    max_cache_size: int = 1000


class CacheMetrics(BaseModel):
    """
    Metrics for cache operations.
    
    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        sets: Number of cache sets
        invalidations: Number of cache invalidations
        errors: Number of cache errors
    """
    
    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0
    errors: int = 0


class ReadModelCache(Generic[T]):
    """
    Cache service for read models.
    
    This service provides an abstraction over different caching mechanisms,
    with support for different cache backends.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        config: Optional[CacheConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the cache service.
        
        Args:
            model_type: The type of read model
            config: Cache configuration
            logger: Optional logger for diagnostics
        """
        self.model_type = model_type
        self.config = config or CacheConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.metrics = CacheMetrics()
    
    async def get(self, key: str) -> Optional[T]:
        """
        Get a read model from cache.
        
        Args:
            key: The cache key
            
        Returns:
            The read model if found, None otherwise
        """
        # To be implemented by subclasses
        raise NotImplementedError("ReadModelCache.get must be implemented by subclasses")
    
    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a read model in cache.
        
        Args:
            key: The cache key
            value: The read model to cache
            ttl_seconds: Optional TTL override
        """
        # To be implemented by subclasses
        raise NotImplementedError("ReadModelCache.set must be implemented by subclasses")
    
    async def invalidate(self, key: str) -> None:
        """
        Invalidate a cached read model.
        
        Args:
            key: The cache key
        """
        # To be implemented by subclasses
        raise NotImplementedError("ReadModelCache.invalidate must be implemented by subclasses")
    
    async def clear(self) -> None:
        """Clear all cached read models."""
        # To be implemented by subclasses
        raise NotImplementedError("ReadModelCache.clear must be implemented by subclasses")
    
    def get_namespace_key(self, key: str) -> str:
        """
        Get a namespaced cache key.
        
        Args:
            key: The original key
            
        Returns:
            Namespaced key
        """
        return f"{self.config.namespace}:{self.model_type.__name__}:{key}"
    
    def get_metrics(self) -> Dict[str, int]:
        """
        Get cache metrics.
        
        Returns:
            Dictionary of cache metrics
        """
        return self.metrics.model_dump()
    
    def reset_metrics(self) -> None:
        """Reset cache metrics."""
        self.metrics = CacheMetrics()


class InMemoryReadModelCache(ReadModelCache[T]):
    """
    In-memory implementation of read model cache.
    
    This implementation stores read models in memory, which is useful
    for testing and simple applications.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        config: Optional[CacheConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the in-memory cache.
        
        Args:
            model_type: The type of read model
            config: Cache configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(model_type, config, logger)
        self.cache: Dict[str, Dict[str, Any]] = {}  # key -> {value, expires_at}
    
    async def get(self, key: str) -> Optional[T]:
        """
        Get a read model from cache.
        
        Args:
            key: The cache key
            
        Returns:
            The read model if found, None otherwise
        """
        if not self.config.enabled:
            return None
        
        namespaced_key = self.get_namespace_key(key)
        
        try:
            # Check if key exists and is not expired
            if namespaced_key in self.cache:
                entry = self.cache[namespaced_key]
                
                # Check expiration
                if "expires_at" in entry:
                    expires_at = entry["expires_at"]
                    if expires_at and datetime.now(UTC) > expires_at:
                        # Expired
                        del self.cache[namespaced_key]
                        self.metrics.misses += 1
                        return None
                
                # Return the cached value
                if "value" in entry:
                    cached_data = entry["value"]
                    self.metrics.hits += 1
                    
                    # Convert the cached data to the model type
                    if isinstance(cached_data, dict):
                        return self.model_type(**cached_data)
                    elif isinstance(cached_data, self.model_type):
                        return cached_data
                
            # Not found or invalid
            self.metrics.misses += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting from cache: {e}")
            self.metrics.errors += 1
            return None
    
    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a read model in cache.
        
        Args:
            key: The cache key
            value: The read model to cache
            ttl_seconds: Optional TTL override
        """
        if not self.config.enabled:
            return
        
        namespaced_key = self.get_namespace_key(key)
        
        try:
            # Calculate expiration time
            ttl = ttl_seconds if ttl_seconds is not None else self.config.ttl_seconds
            expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
            
            # Store value with expiration
            self.cache[namespaced_key] = {
                "value": value.model_dump(),
                "expires_at": expires_at
            }
            
            self.metrics.sets += 1
            
            # Check if we need to evict old entries
            if len(self.cache) > self.config.max_cache_size:
                self._evict_oldest_entries()
                
        except Exception as e:
            self.logger.error(f"Error setting in cache: {e}")
            self.metrics.errors += 1
    
    async def invalidate(self, key: str) -> None:
        """
        Invalidate a cached read model.
        
        Args:
            key: The cache key
        """
        if not self.config.enabled:
            return
        
        namespaced_key = self.get_namespace_key(key)
        
        try:
            if namespaced_key in self.cache:
                del self.cache[namespaced_key]
                self.metrics.invalidations += 1
                
        except Exception as e:
            self.logger.error(f"Error invalidating cache: {e}")
            self.metrics.errors += 1
    
    async def clear(self) -> None:
        """Clear all cached read models."""
        try:
            # Clear only keys in our namespace
            namespace_prefix = f"{self.config.namespace}:{self.model_type.__name__}:"
            
            keys_to_delete = [
                key for key in self.cache.keys()
                if key.startswith(namespace_prefix)
            ]
            
            for key in keys_to_delete:
                del self.cache[key]
                
            self.metrics.invalidations += len(keys_to_delete)
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            self.metrics.errors += 1
    
    def _evict_oldest_entries(self) -> None:
        """Evict the oldest entries from the cache."""
        # Sort entries by expiration time
        sorted_entries = sorted(
            [(k, v.get("expires_at", datetime.max.replace(tzinfo=UTC))) 
             for k, v in self.cache.items()],
            key=lambda x: x[1]
        )
        
        # Calculate number of entries to evict (remove 25% of max size)
        num_to_evict = max(1, int(self.config.max_cache_size * 0.25))
        
        # Evict oldest entries
        for i in range(min(num_to_evict, len(sorted_entries))):
            key = sorted_entries[i][0]
            if key in self.cache:
                del self.cache[key]


class RedisReadModelCache(ReadModelCache[T]):
    """
    Redis implementation of read model cache.
    
    This implementation uses Redis for distributed caching.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        redis_client: Any,  # Redis client
        config: Optional[CacheConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Redis cache.
        
        Args:
            model_type: The type of read model
            redis_client: Redis client instance
            config: Cache configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(model_type, config, logger)
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[T]:
        """
        Get a read model from Redis cache.
        
        Args:
            key: The cache key
            
        Returns:
            The read model if found, None otherwise
        """
        if not self.config.enabled:
            return None
        
        namespaced_key = self.get_namespace_key(key)
        
        try:
            # Get from Redis
            cached_data = await self.redis.get(namespaced_key)
            
            if cached_data:
                # Parse the JSON data
                model_data = json.loads(cached_data)
                self.metrics.hits += 1
                
                # Convert to model instance
                return self.model_type(**model_data)
            
            self.metrics.misses += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting from Redis cache: {e}")
            self.metrics.errors += 1
            return None
    
    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a read model in Redis cache.
        
        Args:
            key: The cache key
            value: The read model to cache
            ttl_seconds: Optional TTL override
        """
        if not self.config.enabled:
            return
        
        namespaced_key = self.get_namespace_key(key)
        
        try:
            # Convert model to JSON
            model_json = json.dumps(value.model_dump())
            
            # Calculate TTL
            ttl = ttl_seconds if ttl_seconds is not None else self.config.ttl_seconds
            
            # Store in Redis with expiration
            await self.redis.set(namespaced_key, model_json, ex=ttl)
            
            self.metrics.sets += 1
                
        except Exception as e:
            self.logger.error(f"Error setting in Redis cache: {e}")
            self.metrics.errors += 1
    
    async def invalidate(self, key: str) -> None:
        """
        Invalidate a cached read model in Redis.
        
        Args:
            key: The cache key
        """
        if not self.config.enabled:
            return
        
        namespaced_key = self.get_namespace_key(key)
        
        try:
            # Delete from Redis
            await self.redis.delete(namespaced_key)
            self.metrics.invalidations += 1
                
        except Exception as e:
            self.logger.error(f"Error invalidating Redis cache: {e}")
            self.metrics.errors += 1
    
    async def clear(self) -> None:
        """Clear all cached read models in Redis."""
        try:
            # Find keys in our namespace
            namespace_prefix = f"{self.config.namespace}:{self.model_type.__name__}:*"
            
            # Get matching keys
            keys = await self.redis.keys(namespace_prefix)
            
            if keys:
                # Delete all matching keys
                await self.redis.delete(*keys)
                self.metrics.invalidations += len(keys)
            
        except Exception as e:
            self.logger.error(f"Error clearing Redis cache: {e}")
            self.metrics.errors += 1


class MultiLevelReadModelCache(ReadModelCache[T]):
    """
    Multi-level implementation of read model cache.
    
    This implementation combines multiple cache levels
    (e.g., in-memory and Redis) for better performance.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        caches: List[ReadModelCache[T]],
        config: Optional[CacheConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the multi-level cache.
        
        Args:
            model_type: The type of read model
            caches: List of cache implementations (ordered from fastest to slowest)
            config: Cache configuration
            logger: Optional logger for diagnostics
        """
        super().__init__(model_type, config, logger)
        self.caches = caches
    
    async def get(self, key: str) -> Optional[T]:
        """
        Get a read model from multi-level cache.
        
        Args:
            key: The cache key
            
        Returns:
            The read model if found, None otherwise
        """
        if not self.config.enabled:
            return None
        
        # Try each cache level
        for i, cache in enumerate(self.caches):
            try:
                value = await cache.get(key)
                
                if value:
                    # Found in this cache level
                    self.metrics.hits += 1
                    
                    # Populate lower-level caches
                    for j in range(i):
                        await self.caches[j].set(key, value)
                    
                    return value
                    
            except Exception as e:
                self.logger.warning(f"Error getting from cache level {i}: {e}")
        
        # Not found in any cache
        self.metrics.misses += 1
        return None
    
    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a read model in multi-level cache.
        
        Args:
            key: The cache key
            value: The read model to cache
            ttl_seconds: Optional TTL override
        """
        if not self.config.enabled:
            return
        
        # Set in all cache levels
        for i, cache in enumerate(self.caches):
            try:
                await cache.set(key, value, ttl_seconds)
            except Exception as e:
                self.logger.warning(f"Error setting in cache level {i}: {e}")
        
        self.metrics.sets += 1
    
    async def invalidate(self, key: str) -> None:
        """
        Invalidate a cached read model in all cache levels.
        
        Args:
            key: The cache key
        """
        if not self.config.enabled:
            return
        
        # Invalidate in all cache levels
        for i, cache in enumerate(self.caches):
            try:
                await cache.invalidate(key)
            except Exception as e:
                self.logger.warning(f"Error invalidating cache level {i}: {e}")
        
        self.metrics.invalidations += 1
    
    async def clear(self) -> None:
        """Clear all cached read models in all cache levels."""
        # Clear all cache levels
        for i, cache in enumerate(self.caches):
            try:
                await cache.clear()
            except Exception as e:
                self.logger.warning(f"Error clearing cache level {i}: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get combined cache metrics.
        
        Returns:
            Dictionary of combined cache metrics
        """
        # Start with our own metrics
        metrics = super().get_metrics()
        
        # Add per-level metrics
        level_metrics = {}
        for i, cache in enumerate(self.caches):
            level_metrics[f"level_{i}"] = cache.get_metrics()
        
        metrics["levels"] = level_metrics
        return metrics