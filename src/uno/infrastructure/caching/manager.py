"""Cache manager module.

This module provides the main entry point for the Uno caching framework.
"""

from typing import Any, Dict, List, Optional, Type, Union, TypeVar, cast
import asyncio
import logging
import threading
from contextlib import contextmanager, asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from uno.caching.config import CacheConfig
from uno.caching.local.base import LocalCache
from uno.caching.local.memory import MemoryCache
from uno.caching.local.file import FileCache
from uno.caching.distributed.base import DistributedCache
from uno.caching.distributed.redis import RedisCache
from uno.caching.distributed.memcached import MemcachedCache
from uno.caching.key import get_cache_key
from uno.caching.invalidation.strategy import InvalidationStrategy
from uno.caching.invalidation.time_based import TimeBasedInvalidation
from uno.caching.invalidation.event_based import EventBasedInvalidation
from uno.caching.invalidation.pattern_based import PatternBasedInvalidation
from uno.caching.monitoring.monitor import CacheMonitor

T = TypeVar('T')

logger = logging.getLogger("uno.caching")


_cache_manager_lock = threading.RLock()
_cache_manager_instance: Optional["CacheManager"] = None


def get_cache_manager(config: Optional[CacheConfig] = None) -> "CacheManager":
    """Get or create the singleton instance of the cache manager.
    
    Args:
        config: Optional cache configuration. Used only if creating a new instance.
        
    Returns:
        The singleton cache manager instance.
    """
    global _cache_manager_instance
    
    if _cache_manager_instance is None:
        with _cache_manager_lock:
            if _cache_manager_instance is None:
                _cache_manager_instance = CacheManager(config)
                _cache_manager_instance.initialize()
    return _cache_manager_instance


class CacheManager:
    """Main entry point for the Uno caching framework.
    
    This class manages the cache hierarchy, including local and distributed caches,
    invalidation strategies, and monitoring.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize the cache manager.
        
        Args:
            config: Optional cache configuration. If not provided, default configuration is used.
        """
        self.config = config or CacheConfig()
        self.local_cache: Optional[LocalCache] = None
        self.distributed_cache: Optional[DistributedCache] = None
        self.invalidation_strategy: Optional[InvalidationStrategy] = None
        self.monitor: Optional[CacheMonitor] = None
        self.initialized = False
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def initialize(self) -> None:
        """Initialize the caching system.
        
        This method creates the necessary cache components based on the configuration.
        """
        if not self.config.enabled:
            logger.info("Caching is disabled by configuration")
            return
        
        if self.initialized:
            logger.debug("Cache manager already initialized")
            return
        
        # Initialize local cache
        local_config = self.config.local
        if local_config.type == "memory":
            self.local_cache = MemoryCache(
                max_size=local_config.max_size,
                ttl=local_config.ttl,
                lru_policy=local_config.lru_policy
            )
        elif local_config.type == "file":
            self.local_cache = FileCache(
                directory=local_config.directory,
                max_size=local_config.max_size,
                ttl=local_config.ttl,
                shards=local_config.shards
            )
        
        # Initialize distributed cache if enabled
        if self.config.distributed.enabled:
            dist_config = self.config.distributed
            if dist_config.type == "redis":
                self.distributed_cache = RedisCache(
                    connection_string=dist_config.connection_string,
                    hosts=dist_config.hosts,
                    username=dist_config.username,
                    password=dist_config.password,
                    database=dist_config.database,
                    use_connection_pool=dist_config.use_connection_pool,
                    max_connections=dist_config.max_connections,
                    ttl=dist_config.ttl,
                    prefix=dist_config.prefix
                )
            elif dist_config.type == "memcached":
                self.distributed_cache = MemcachedCache(
                    hosts=dist_config.hosts,
                    max_pool_size=dist_config.max_pool_size,
                    connect_timeout=dist_config.connect_timeout,
                    ttl=dist_config.ttl,
                    prefix=dist_config.prefix
                )
        
        # Initialize invalidation strategy
        invalidation_config = self.config.invalidation
        strategies = []
        
        if invalidation_config.time_based:
            strategies.append(TimeBasedInvalidation(
                default_ttl=invalidation_config.default_ttl,
                ttl_jitter=invalidation_config.ttl_jitter
            ))
        
        if invalidation_config.event_based:
            strategies.append(EventBasedInvalidation(
                event_handlers=invalidation_config.event_handlers
            ))
        
        if invalidation_config.pattern_based:
            strategies.append(PatternBasedInvalidation(
                patterns=invalidation_config.patterns,
                consistent_hashing=invalidation_config.consistent_hashing
            ))
        
        if strategies:
            self.invalidation_strategy = InvalidationStrategy(strategies)
        
        # Initialize monitoring if enabled
        if self.config.monitoring.enabled:
            self.monitor = CacheMonitor(
                config=self.config.monitoring,
                local_cache=self.local_cache,
                distributed_cache=self.distributed_cache
            )
        
        self.initialized = True
        logger.info("Cache manager initialized successfully")
    
    def shutdown(self) -> None:
        """Shutdown the caching system and release resources."""
        if not self.initialized:
            return
        
        if self.monitor:
            self.monitor.shutdown()
        
        if self.distributed_cache:
            self.distributed_cache.close()
        
        if self.local_cache:
            self.local_cache.close()
        
        self._executor.shutdown(wait=True)
        
        self.initialized = False
        logger.info("Cache manager shut down successfully")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache.
        
        This method checks the local cache first, then falls back to the distributed
        cache if the value is not found locally and multi-level caching is enabled.
        
        Args:
            key: The cache key.
            default: The default value to return if the key is not found.
            
        Returns:
            The cached value or the default value if not found.
        """
        if not self.initialized or not self.config.enabled:
            return default
        
        # Generate full cache key
        full_key = get_cache_key(key, self.config.key_prefix, self.config.use_hash_keys, 
                              self.config.hash_algorithm)
        
        # Try local cache first
        if self.local_cache:
            try:
                value = self.local_cache.get(full_key)
                if value is not None:
                    if self.monitor:
                        self.monitor.record_hit("local")
                    return value
                if self.monitor:
                    self.monitor.record_miss("local")
            except Exception as e:
                logger.warning(f"Error getting value from local cache: {e}")
                if self.monitor:
                    self.monitor.record_error("local", "get", str(e))
                if not self.config.fallback_on_error or not self.config.use_multi_level:
                    return default
        
        # Try distributed cache if multi-level is enabled
        if self.distributed_cache and self.config.use_multi_level:
            try:
                value = self.distributed_cache.get(full_key)
                if value is not None:
                    # Store in local cache for future access
                    if self.local_cache:
                        try:
                            self.local_cache.set(full_key, value)
                        except Exception as e:
                            logger.warning(f"Error setting value in local cache: {e}")
                            if self.monitor:
                                self.monitor.record_error("local", "set", str(e))
                    
                    if self.monitor:
                        self.monitor.record_hit("distributed")
                    return value
                if self.monitor:
                    self.monitor.record_miss("distributed")
            except Exception as e:
                logger.warning(f"Error getting value from distributed cache: {e}")
                if self.monitor:
                    self.monitor.record_error("distributed", "get", str(e))
        
        return default
    
    async def get_async(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache asynchronously.
        
        This is the async version of the get method.
        
        Args:
            key: The cache key.
            default: The default value to return if the key is not found.
            
        Returns:
            The cached value or the default value if not found.
        """
        if not self.initialized or not self.config.enabled:
            return default
        
        # Generate full cache key
        full_key = get_cache_key(key, self.config.key_prefix, self.config.use_hash_keys, 
                              self.config.hash_algorithm)
        
        # Try local cache first (we can do this synchronously as it's in-memory)
        if self.local_cache:
            try:
                value = self.local_cache.get(full_key)
                if value is not None:
                    if self.monitor:
                        await asyncio.to_thread(self.monitor.record_hit, "local")
                    return value
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_miss, "local")
            except Exception as e:
                logger.warning(f"Error getting value from local cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "local", "get", str(e))
                if not self.config.fallback_on_error or not self.config.use_multi_level:
                    return default
        
        # Try distributed cache if multi-level is enabled
        if self.distributed_cache and self.config.use_multi_level:
            try:
                # Use the async interface for the distributed cache
                value = await self.distributed_cache.get_async(full_key)
                if value is not None:
                    # Store in local cache for future access
                    if self.local_cache:
                        try:
                            self.local_cache.set(full_key, value)
                        except Exception as e:
                            logger.warning(f"Error setting value in local cache: {e}")
                            if self.monitor:
                                await asyncio.to_thread(self.monitor.record_error, "local", "set", str(e))
                    
                    if self.monitor:
                        await asyncio.to_thread(self.monitor.record_hit, "distributed")
                    return value
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_miss, "distributed")
            except Exception as e:
                logger.warning(f"Error getting value from distributed cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "distributed", "get", str(e))
        
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.
        
        This method sets the value in the local cache and, if multi-level caching
        is enabled, also in the distributed cache.
        
        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
            
        Returns:
            True if the value was successfully cached, False otherwise.
        """
        if not self.initialized or not self.config.enabled:
            return False
        
        # Generate full cache key
        full_key = get_cache_key(key, self.config.key_prefix, self.config.use_hash_keys, 
                              self.config.hash_algorithm)
        
        if ttl is None:
            ttl = self.config.invalidation.default_ttl
        
        # Add jitter to TTL to prevent cache stampede
        if self.invalidation_strategy and isinstance(self.invalidation_strategy, TimeBasedInvalidation):
            ttl = self.invalidation_strategy.apply_jitter(ttl)
        
        success = True
        
        # Set in local cache
        if self.local_cache:
            try:
                local_ttl = min(ttl, self.config.local.ttl) if ttl > 0 else self.config.local.ttl
                self.local_cache.set(full_key, value, local_ttl)
            except Exception as e:
                logger.warning(f"Error setting value in local cache: {e}")
                if self.monitor:
                    self.monitor.record_error("local", "set", str(e))
                success = False
        
        # Set in distributed cache if multi-level is enabled
        if self.distributed_cache and self.config.use_multi_level:
            try:
                dist_ttl = min(ttl, self.config.distributed.ttl) if ttl > 0 else self.config.distributed.ttl
                self.distributed_cache.set(full_key, value, dist_ttl)
            except Exception as e:
                logger.warning(f"Error setting value in distributed cache: {e}")
                if self.monitor:
                    self.monitor.record_error("distributed", "set", str(e))
                success = False
        
        return success
    
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache asynchronously.
        
        This is the async version of the set method.
        
        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
            
        Returns:
            True if the value was successfully cached, False otherwise.
        """
        if not self.initialized or not self.config.enabled:
            return False
        
        # Generate full cache key
        full_key = get_cache_key(key, self.config.key_prefix, self.config.use_hash_keys, 
                              self.config.hash_algorithm)
        
        if ttl is None:
            ttl = self.config.invalidation.default_ttl
        
        # Add jitter to TTL to prevent cache stampede
        if self.invalidation_strategy and isinstance(self.invalidation_strategy, TimeBasedInvalidation):
            ttl = await asyncio.to_thread(self.invalidation_strategy.apply_jitter, ttl)
        
        success = True
        
        # Set in local cache (we can do this synchronously as it's in-memory)
        if self.local_cache:
            try:
                local_ttl = min(ttl, self.config.local.ttl) if ttl > 0 else self.config.local.ttl
                self.local_cache.set(full_key, value, local_ttl)
            except Exception as e:
                logger.warning(f"Error setting value in local cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "local", "set", str(e))
                success = False
        
        # Set in distributed cache if multi-level is enabled
        if self.distributed_cache and self.config.use_multi_level:
            try:
                dist_ttl = min(ttl, self.config.distributed.ttl) if ttl > 0 else self.config.distributed.ttl
                # Use the async interface for the distributed cache
                await self.distributed_cache.set_async(full_key, value, dist_ttl)
            except Exception as e:
                logger.warning(f"Error setting value in distributed cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "distributed", "set", str(e))
                success = False
        
        return success
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.
        
        This method deletes the value from both local and distributed caches.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the value was successfully deleted, False otherwise.
        """
        if not self.initialized or not self.config.enabled:
            return False
        
        # Generate full cache key
        full_key = get_cache_key(key, self.config.key_prefix, self.config.use_hash_keys, 
                              self.config.hash_algorithm)
        
        success = True
        
        # Delete from local cache
        if self.local_cache:
            try:
                self.local_cache.delete(full_key)
            except Exception as e:
                logger.warning(f"Error deleting value from local cache: {e}")
                if self.monitor:
                    self.monitor.record_error("local", "delete", str(e))
                success = False
        
        # Delete from distributed cache
        if self.distributed_cache:
            try:
                self.distributed_cache.delete(full_key)
            except Exception as e:
                logger.warning(f"Error deleting value from distributed cache: {e}")
                if self.monitor:
                    self.monitor.record_error("distributed", "delete", str(e))
                success = False
        
        return success
    
    async def delete_async(self, key: str) -> bool:
        """Delete a value from the cache asynchronously.
        
        This is the async version of the delete method.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the value was successfully deleted, False otherwise.
        """
        if not self.initialized or not self.config.enabled:
            return False
        
        # Generate full cache key
        full_key = get_cache_key(key, self.config.key_prefix, self.config.use_hash_keys, 
                              self.config.hash_algorithm)
        
        success = True
        
        # Delete from local cache (we can do this synchronously as it's in-memory)
        if self.local_cache:
            try:
                self.local_cache.delete(full_key)
            except Exception as e:
                logger.warning(f"Error deleting value from local cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "local", "delete", str(e))
                success = False
        
        # Delete from distributed cache
        if self.distributed_cache:
            try:
                # Use the async interface for the distributed cache
                await self.distributed_cache.delete_async(full_key)
            except Exception as e:
                logger.warning(f"Error deleting value from distributed cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "distributed", "delete", str(e))
                success = False
        
        return success
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.
        
        This method deletes all keys matching the given pattern from both local
        and distributed caches.
        
        Args:
            pattern: The pattern to match against cache keys.
            
        Returns:
            The number of keys invalidated.
        """
        if not self.initialized or not self.config.enabled:
            return 0
        
        count = 0
        
        # Invalidate in local cache
        if self.local_cache:
            try:
                count += self.local_cache.invalidate_pattern(pattern)
            except Exception as e:
                logger.warning(f"Error invalidating pattern in local cache: {e}")
                if self.monitor:
                    self.monitor.record_error("local", "invalidate_pattern", str(e))
        
        # Invalidate in distributed cache
        if self.distributed_cache:
            try:
                count += self.distributed_cache.invalidate_pattern(pattern)
            except Exception as e:
                logger.warning(f"Error invalidating pattern in distributed cache: {e}")
                if self.monitor:
                    self.monitor.record_error("distributed", "invalidate_pattern", str(e))
        
        return count
    
    async def invalidate_pattern_async(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern asynchronously.
        
        This is the async version of the invalidate_pattern method.
        
        Args:
            pattern: The pattern to match against cache keys.
            
        Returns:
            The number of keys invalidated.
        """
        if not self.initialized or not self.config.enabled:
            return 0
        
        count = 0
        
        # Invalidate in local cache (we can do this synchronously as it's in-memory)
        if self.local_cache:
            try:
                count += self.local_cache.invalidate_pattern(pattern)
            except Exception as e:
                logger.warning(f"Error invalidating pattern in local cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "local", "invalidate_pattern", str(e))
        
        # Invalidate in distributed cache
        if self.distributed_cache:
            try:
                # Use the async interface for the distributed cache
                count += await self.distributed_cache.invalidate_pattern_async(pattern)
            except Exception as e:
                logger.warning(f"Error invalidating pattern in distributed cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "distributed", "invalidate_pattern", str(e))
        
        return count
    
    def clear(self) -> bool:
        """Clear all cached values.
        
        This method clears both local and distributed caches.
        
        Returns:
            True if the caches were successfully cleared, False otherwise.
        """
        if not self.initialized or not self.config.enabled:
            return False
        
        success = True
        
        # Clear local cache
        if self.local_cache:
            try:
                self.local_cache.clear()
            except Exception as e:
                logger.warning(f"Error clearing local cache: {e}")
                if self.monitor:
                    self.monitor.record_error("local", "clear", str(e))
                success = False
        
        # Clear distributed cache
        if self.distributed_cache:
            try:
                self.distributed_cache.clear()
            except Exception as e:
                logger.warning(f"Error clearing distributed cache: {e}")
                if self.monitor:
                    self.monitor.record_error("distributed", "clear", str(e))
                success = False
        
        return success
    
    async def clear_async(self) -> bool:
        """Clear all cached values asynchronously.
        
        This is the async version of the clear method.
        
        Returns:
            True if the caches were successfully cleared, False otherwise.
        """
        if not self.initialized or not self.config.enabled:
            return False
        
        success = True
        
        # Clear local cache (we can do this synchronously as it's in-memory)
        if self.local_cache:
            try:
                self.local_cache.clear()
            except Exception as e:
                logger.warning(f"Error clearing local cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "local", "clear", str(e))
                success = False
        
        # Clear distributed cache
        if self.distributed_cache:
            try:
                # Use the async interface for the distributed cache
                await self.distributed_cache.clear_async()
            except Exception as e:
                logger.warning(f"Error clearing distributed cache: {e}")
                if self.monitor:
                    await asyncio.to_thread(self.monitor.record_error, "distributed", "clear", str(e))
                success = False
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            A dictionary with cache statistics.
        """
        if not self.initialized or not self.config.enabled or not self.monitor:
            return {}
        
        return self.monitor.get_stats()
    
    def check_health(self) -> Dict[str, bool]:
        """Check the health of the caching system.
        
        Returns:
            A dictionary with health status for each cache component.
        """
        if not self.initialized or not self.config.enabled:
            return {"enabled": False}
        
        health = {"enabled": True}
        
        if self.local_cache:
            try:
                health["local"] = self.local_cache.check_health()
            except Exception:
                health["local"] = False
        
        if self.distributed_cache:
            try:
                health["distributed"] = self.distributed_cache.check_health()
            except Exception:
                health["distributed"] = False
        
        return health
    
    async def check_health_async(self) -> Dict[str, bool]:
        """Check the health of the caching system asynchronously.
        
        Returns:
            A dictionary with health status for each cache component.
        """
        if not self.initialized or not self.config.enabled:
            return {"enabled": False}
        
        health = {"enabled": True}
        
        if self.local_cache:
            try:
                health["local"] = await asyncio.to_thread(self.local_cache.check_health)
            except Exception:
                health["local"] = False
        
        if self.distributed_cache:
            try:
                health["distributed"] = await self.distributed_cache.check_health_async()
            except Exception:
                health["distributed"] = False
        
        return health
    
    @contextmanager
    def cache_context(self, region: Optional[str] = None):
        """Create a cache context for a specific region.
        
        This context manager allows using region-specific cache settings.
        
        Args:
            region: The cache region name.
            
        Yields:
            The cache manager instance with region-specific settings.
        """
        original_config = self.config
        
        try:
            if region and region in self.config.regions:
                # Apply region-specific settings
                region_config = self.config.regions[region]
                # Create a new config with region-specific overrides
                # (this is a simplified approach; in practice, we would need to do a deep merge)
                merged_config = CacheConfig(**{**original_config.__dict__, **region_config})
                self.config = merged_config
            
            yield self
        finally:
            # Restore original config
            self.config = original_config
    
    @asynccontextmanager
    async def cache_context_async(self, region: Optional[str] = None):
        """Create a cache context for a specific region asynchronously.
        
        This is the async version of the cache_context method.
        
        Args:
            region: The cache region name.
            
        Yields:
            The cache manager instance with region-specific settings.
        """
        original_config = self.config
        
        try:
            if region and region in self.config.regions:
                # Apply region-specific settings
                region_config = self.config.regions[region]
                # Create a new config with region-specific overrides
                # (this is a simplified approach; in practice, we would need to do a deep merge)
                merged_config = CacheConfig(**{**original_config.__dict__, **region_config})
                self.config = merged_config
            
            yield self
        finally:
            # Restore original config
            self.config = original_config
