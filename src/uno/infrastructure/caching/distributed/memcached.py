"""Memcached cache module.

This module provides a Memcached-based distributed cache implementation.
"""

from typing import Any, Dict, List, Optional, Tuple, Set, Union
import json
import pickle
import time
import asyncio
import logging
import random
from concurrent.futures import ThreadPoolExecutor

from uno.caching.distributed.base import DistributedCache

# Import Memcached client conditionally to avoid hard dependency
try:
    import pymemcache
    import aiomcache
    MEMCACHED_AVAILABLE = True
except ImportError:
    MEMCACHED_AVAILABLE = False

logger = logging.getLogger("uno.caching.memcached")


class MemcachedCache(DistributedCache):
    """Memcached-based distributed cache implementation.
    
    This implementation uses Memcached as a distributed cache. It supports both
    synchronous and asynchronous operations.
    """
    
    def __init__(self, hosts: Optional[List[str]] = None, max_pool_size: int = 10,
                 connect_timeout: float = 1.0, ttl: int = 300, prefix: str = "uno:"):
        """Initialize the Memcached cache.
        
        Args:
            hosts: List of Memcached hosts in format host:port.
            max_pool_size: Maximum number of connections in the pool.
            connect_timeout: Connection timeout in seconds.
            ttl: Default time-to-live in seconds.
            prefix: Key prefix for cache entries.
        """
        if not MEMCACHED_AVAILABLE:
            raise ImportError("Memcached client is not available. Please install it with `pip install pymemcache aiomcache`.")
        
        self.default_ttl = ttl
        self.prefix = prefix
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Parse host information
        if not hosts or len(hosts) == 0:
            hosts = ["localhost:11211"]
        
        # Create Memcached client for the synchronous API
        sync_servers = [self._parse_host(host) for host in hosts]
        
        if len(sync_servers) == 1:
            # Single server mode
            server = sync_servers[0]
            self._client = pymemcache.client.base.Client(
                server=server,
                connect_timeout=connect_timeout,
                timeout=connect_timeout,
                serializer=self._serialize_for_memcached,
                deserializer=self._deserialize_from_memcached
            )
        else:
            # Multiple servers mode (consistent hashing)
            self._client = pymemcache.client.hash.HashClient(
                servers=sync_servers,
                connect_timeout=connect_timeout,
                timeout=connect_timeout,
                serializer=self._serialize_for_memcached,
                deserializer=self._deserialize_from_memcached
            )
        
        # Create Memcached client for the asynchronous API
        # Note: aiomcache only supports a single server, so we'll pick the first one
        # or a random one if multiple servers are provided
        async_server = self._parse_host(hosts[0]) if len(hosts) == 1 else self._parse_host(random.choice(hosts))
        self._async_client = aiomcache.Client(
            host=async_server[0],
            port=async_server[1],
            pool_size=max_pool_size,
            pool_minsize=2
        )
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "insertions": 0,
            "deletions": 0,
            "created_at": time.time(),
        }
    
    def get(self, key: str) -> Any:
        """Get a value from the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            The cached value or None if not found.
        """
        try:
            full_key = self._get_full_key(key)
            value = self._client.get(full_key)
            
            if value is None:
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return value
        except Exception as e:
            logger.warning(f"Error getting value from Memcached: {e}")
            return None
    
    async def get_async(self, key: str) -> Any:
        """Get a value from the cache asynchronously.
        
        Args:
            key: The cache key.
            
        Returns:
            The cached value or None if not found.
        """
        try:
            full_key = self._get_full_key(key)
            value = await self._async_client.get(full_key.encode())
            
            if value is None:
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return self._deserialize(value)
        except Exception as e:
            logger.warning(f"Error getting value from Memcached: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.
        
        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
            
        Returns:
            True if the value was successfully cached, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            
            if ttl is None:
                ttl = self.default_ttl
            
            result = self._client.set(full_key, value, expire=ttl)
            
            if result:
                self._stats["insertions"] += 1
            
            return result
        except Exception as e:
            logger.warning(f"Error setting value in Memcached: {e}")
            return False
    
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache asynchronously.
        
        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
            
        Returns:
            True if the value was successfully cached, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            serialized_value = self._serialize(value)
            
            if ttl is None:
                ttl = self.default_ttl
            
            result = await self._async_client.set(full_key.encode(), serialized_value, exptime=ttl)
            
            if result:
                self._stats["insertions"] += 1
            
            return result
        except Exception as e:
            logger.warning(f"Error setting value in Memcached: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the value was successfully deleted, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            result = self._client.delete(full_key)
            
            if result:
                self._stats["deletions"] += 1
            
            return result
        except Exception as e:
            logger.warning(f"Error deleting value from Memcached: {e}")
            return False
    
    async def delete_async(self, key: str) -> bool:
        """Delete a value from the cache asynchronously.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the value was successfully deleted, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            result = await self._async_client.delete(full_key.encode())
            
            if result:
                self._stats["deletions"] += 1
            
            return result
        except Exception as e:
            logger.warning(f"Error deleting value from Memcached: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.
        
        Unfortunately, Memcached does not support pattern-based operations natively.
        This method always returns 0 as it can't be implemented efficiently.
        
        Args:
            pattern: The pattern to match against cache keys.
            
        Returns:
            The number of keys invalidated (always 0).
        """
        # Memcached doesn't support pattern-based operations
        logger.warning("Pattern-based invalidation is not supported by Memcached")
        return 0
    
    async def invalidate_pattern_async(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern asynchronously.
        
        Unfortunately, Memcached does not support pattern-based operations natively.
        This method always returns 0 as it can't be implemented efficiently.
        
        Args:
            pattern: The pattern to match against cache keys.
            
        Returns:
            The number of keys invalidated (always 0).
        """
        # Memcached doesn't support pattern-based operations
        logger.warning("Pattern-based invalidation is not supported by Memcached")
        return 0
    
    def clear(self) -> bool:
        """Clear all cached values.
        
        Note that Memcached's flush_all operation clears ALL keys in the entire cache,
        not just those with a specific prefix.
        
        Returns:
            True if the cache was successfully cleared, False otherwise.
        """
        try:
            # Note: This clears ALL keys in Memcached, not just those with our prefix
            self._client.flush_all()
            return True
        except Exception as e:
            logger.warning(f"Error clearing Memcached cache: {e}")
            return False
    
    async def clear_async(self) -> bool:
        """Clear all cached values asynchronously.
        
        Note that Memcached's flush_all operation clears ALL keys in the entire cache,
        not just those with a specific prefix.
        
        Returns:
            True if the cache was successfully cleared, False otherwise.
        """
        try:
            # Note: This clears ALL keys in Memcached, not just those with our prefix
            # aiomcache doesn't have flush_all, so we use a thread to call the sync version
            await asyncio.to_thread(self._client.flush_all)
            return True
        except Exception as e:
            logger.warning(f"Error clearing Memcached cache: {e}")
            return False
    
    def check_health(self) -> bool:
        """Check the health of the cache.
        
        Returns:
            True if the cache is healthy, False otherwise.
        """
        try:
            # Try to get a non-existent key to check if Memcached is responding
            self._client.get("__health_check__")
            return True
        except Exception:
            return False
    
    async def check_health_async(self) -> bool:
        """Check the health of the cache asynchronously.
        
        Returns:
            True if the cache is healthy, False otherwise.
        """
        try:
            # Try to get a non-existent key to check if Memcached is responding
            await self._async_client.get("__health_check__".encode())
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            A dictionary with cache statistics.
        """
        try:
            # Copy stats and add current info
            stats = self._stats.copy()
            
            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0
            
            # Add uptime
            stats["uptime"] = time.time() - stats["created_at"]
            
            # Add Memcached stats
            memcached_stats = self._client.stats()
            if isinstance(memcached_stats, dict):
                # Single server
                for key, value in memcached_stats.items():
                    stats[f"memcached_{key.decode() if isinstance(key, bytes) else key}"] = (
                        value.decode() if isinstance(value, bytes) else value
                    )
            elif isinstance(memcached_stats, list):
                # Multiple servers
                for i, server_stats in enumerate(memcached_stats):
                    if server_stats and isinstance(server_stats[1], dict):
                        for key, value in server_stats[1].items():
                            stats[f"memcached_{i}_{key.decode() if isinstance(key, bytes) else key}"] = (
                                value.decode() if isinstance(value, bytes) else value
                            )
            
            return stats
        except Exception as e:
            logger.warning(f"Error getting Memcached statistics: {e}")
            return self._stats.copy()
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """Get cache statistics asynchronously.
        
        Returns:
            A dictionary with cache statistics.
        """
        # aiomcache doesn't have a stats method, so we'll use a thread to call the sync version
        return await asyncio.to_thread(self.get_stats)
    
    def close(self) -> None:
        """Close the cache and release resources."""
        # Close the Memcached clients
        try:
            if hasattr(self, "_client") and self._client:
                self._client.close()
            
            if hasattr(self, "_async_client") and self._async_client:
                asyncio.get_event_loop().run_until_complete(self._async_client.close())
        except Exception as e:
            logger.warning(f"Error closing Memcached connections: {e}")
    
    def multi_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from the cache.
        
        Args:
            keys: The cache keys.
            
        Returns:
            A dictionary mapping keys to values. Keys not found in the cache are omitted.
        """
        if not keys:
            return {}
        
        try:
            # Get full keys
            full_keys = [self._get_full_key(key) for key in keys]
            
            # Get values from Memcached
            values = self._client.get_multi(full_keys)
            
            # Create result dictionary
            result = {}
            for i, key in enumerate(keys):
                full_key = full_keys[i]
                if full_key in values:
                    result[key] = values[full_key]
                    self._stats["hits"] += 1
                else:
                    self._stats["misses"] += 1
            
            return result
        except Exception as e:
            logger.warning(f"Error getting multiple values from Memcached: {e}")
            return {}
    
    async def multi_get_async(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from the cache asynchronously.
        
        Args:
            keys: The cache keys.
            
        Returns:
            A dictionary mapping keys to values. Keys not found in the cache are omitted.
        """
        if not keys:
            return {}
        
        # aiomcache doesn't have a get_multi method, so we'll implement it ourselves
        result = {}
        tasks = []
        
        for key in keys:
            tasks.append(self.get_async(key))
        
        values = await asyncio.gather(*tasks)
        
        for i, value in enumerate(values):
            if value is not None:
                result[keys[i]] = value
        
        return result
    
    def multi_set(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache.
        
        Args:
            mapping: A dictionary mapping keys to values.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
            
        Returns:
            True if all values were successfully cached, False otherwise.
        """
        if not mapping:
            return True
        
        try:
            # Get full keys
            full_mapping = {self._get_full_key(key): value for key, value in mapping.items()}
            
            if ttl is None:
                ttl = self.default_ttl
            
            # Set values in Memcached
            result = self._client.set_multi(full_mapping, expire=ttl)
            
            if not result:
                self._stats["insertions"] += len(mapping)
                return True
            else:
                # set_multi returns a list of keys that failed to be set
                self._stats["insertions"] += len(mapping) - len(result)
                return False
        except Exception as e:
            logger.warning(f"Error setting multiple values in Memcached: {e}")
            return False
    
    async def multi_set_async(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache asynchronously.
        
        Args:
            mapping: A dictionary mapping keys to values.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
            
        Returns:
            True if all values were successfully cached, False otherwise.
        """
        if not mapping:
            return True
        
        # aiomcache doesn't have a set_multi method, so we'll implement it ourselves
        tasks = []
        
        for key, value in mapping.items():
            tasks.append(self.set_async(key, value, ttl))
        
        results = await asyncio.gather(*tasks)
        
        return all(results)
    
    def multi_delete(self, keys: List[str]) -> bool:
        """Delete multiple values from the cache.
        
        Args:
            keys: The cache keys.
            
        Returns:
            True if all values were successfully deleted, False otherwise.
        """
        if not keys:
            return True
        
        try:
            # Get full keys
            full_keys = [self._get_full_key(key) for key in keys]
            
            # Delete keys from Memcached
            success = True
            for key in full_keys:
                if not self._client.delete(key):
                    success = False
                else:
                    self._stats["deletions"] += 1
            
            return success
        except Exception as e:
            logger.warning(f"Error deleting multiple values from Memcached: {e}")
            return False
    
    async def multi_delete_async(self, keys: List[str]) -> bool:
        """Delete multiple values from the cache asynchronously.
        
        Args:
            keys: The cache keys.
            
        Returns:
            True if all values were successfully deleted, False otherwise.
        """
        if not keys:
            return True
        
        # aiomcache doesn't have a delete_multi method, so we'll implement it ourselves
        tasks = []
        
        for key in keys:
            tasks.append(self.delete_async(key))
        
        results = await asyncio.gather(*tasks)
        
        return all(results)
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the key exists, False otherwise.
        """
        # Memcached doesn't have a direct exists method, so we'll use get
        return self.get(key) is not None
    
    async def exists_async(self, key: str) -> bool:
        """Check if a key exists in the cache asynchronously.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the key exists, False otherwise.
        """
        # Memcached doesn't have a direct exists method, so we'll use get_async
        return await self.get_async(key) is not None
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value.
        
        Args:
            key: The cache key.
            amount: The amount to increment by.
            
        Returns:
            The new value or None if the operation failed.
        """
        try:
            full_key = self._get_full_key(key)
            return self._client.incr(full_key, amount)
        except Exception as e:
            logger.warning(f"Error incrementing value in Memcached: {e}")
            return None
    
    async def increment_async(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value asynchronously.
        
        Args:
            key: The cache key.
            amount: The amount to increment by.
            
        Returns:
            The new value or None if the operation failed.
        """
        try:
            full_key = self._get_full_key(key)
            return await self._async_client.incr(full_key.encode(), amount)
        except Exception as e:
            logger.warning(f"Error incrementing value in Memcached: {e}")
            return None
    
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a numeric value.
        
        Args:
            key: The cache key.
            amount: The amount to decrement by.
            
        Returns:
            The new value or None if the operation failed.
        """
        try:
            full_key = self._get_full_key(key)
            return self._client.decr(full_key, amount)
        except Exception as e:
            logger.warning(f"Error decrementing value in Memcached: {e}")
            return None
    
    async def decrement_async(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a numeric value asynchronously.
        
        Args:
            key: The cache key.
            amount: The amount to decrement by.
            
        Returns:
            The new value or None if the operation failed.
        """
        try:
            full_key = self._get_full_key(key)
            return await self._async_client.decr(full_key.encode(), amount)
        except Exception as e:
            logger.warning(f"Error decrementing value in Memcached: {e}")
            return None
    
    def touch(self, key: str, ttl: int) -> bool:
        """Update the TTL of a cached value.
        
        Args:
            key: The cache key.
            ttl: The new TTL in seconds.
            
        Returns:
            True if the TTL was successfully updated, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            return self._client.touch(full_key, ttl)
        except Exception as e:
            logger.warning(f"Error updating TTL in Memcached: {e}")
            return False
    
    async def touch_async(self, key: str, ttl: int) -> bool:
        """Update the TTL of a cached value asynchronously.
        
        Args:
            key: The cache key.
            ttl: The new TTL in seconds.
            
        Returns:
            True if the TTL was successfully updated, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            return await self._async_client.touch(full_key.encode(), ttl)
        except Exception as e:
            logger.warning(f"Error updating TTL in Memcached: {e}")
            return False
    
    def _get_full_key(self, key: str) -> str:
        """Get the full key with prefix.
        
        Args:
            key: The cache key.
            
        Returns:
            The full key with prefix.
        """
        return f"{self.prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize a value for storage in Memcached.
        
        Args:
            value: The value to serialize.
            
        Returns:
            The serialized value as bytes.
        """
        # Use pickle for serialization
        return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize a value from Memcached.
        
        Args:
            data: The serialized value.
            
        Returns:
            The deserialized value.
        """
        # Use pickle for deserialization
        return pickle.loads(data)
    
    def _serialize_for_memcached(self, key: str, value: Any) -> Tuple[bytes, int, int]:
        """Serialize a value for the pymemcache client.
        
        Args:
            key: The cache key.
            value: The value to serialize.
            
        Returns:
            A tuple of (serialized_value, flags, length).
        """
        serialized_value = pickle.dumps(value)
        return serialized_value, 1, len(serialized_value)
    
    def _deserialize_from_memcached(self, key: str, value: bytes, flags: int) -> Any:
        """Deserialize a value for the pymemcache client.
        
        Args:
            key: The cache key.
            value: The serialized value.
            flags: The flags from Memcached.
            
        Returns:
            The deserialized value.
        """
        if flags == 1:
            return pickle.loads(value)
        return value
    
    def _parse_host(self, host_str: str) -> Tuple[str, int]:
        """Parse a host string into host and port.
        
        Args:
            host_str: The host string in format host:port.
            
        Returns:
            A tuple of (host, port).
        """
        parts = host_str.split(":")
        host = parts[0] or "localhost"
        port = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 11211
        return (host, port)
