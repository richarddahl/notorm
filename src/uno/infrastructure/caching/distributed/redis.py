"""Redis cache module.

This module provides a Redis-based distributed cache implementation.
"""

from typing import Any, Dict, List, Optional, Tuple, Set, Union
import json
import pickle
import time
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from uno.caching.distributed.base import DistributedCache

# Import Redis client conditionally to avoid hard dependency
try:
    import redis
    import redis.asyncio

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger("uno.caching.redis")


class RedisCache(DistributedCache):
    """Redis-based distributed cache implementation.

    This implementation uses Redis as a distributed cache. It supports both
    synchronous and asynchronous operations.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        hosts: list[str] | None = None,
        username: str | None = None,
        password: str | None = None,
        database: int = 0,
        use_connection_pool: bool = True,
        max_connections: int = 10,
        socket_timeout: float = 2.0,
        socket_connect_timeout: float = 1.0,
        retry_on_timeout: bool = True,
        ttl: int = 300,
        prefix: str = "uno:",
    ):
        """Initialize the Redis cache.

        Args:
            connection_string: Connection string for Redis. Format: redis://[[username]:[password]@][host][:port][/database]
            hosts: List of Redis hosts in format host:port. Ignored if connection_string is provided.
            username: Redis username. Ignored if connection_string is provided.
            password: Redis password. Ignored if connection_string is provided.
            database: Redis database number. Ignored if connection_string is provided.
            use_connection_pool: Whether to use a connection pool.
            max_connections: Maximum number of connections in the pool.
            socket_timeout: Socket timeout in seconds.
            socket_connect_timeout: Socket connection timeout in seconds.
            retry_on_timeout: Whether to retry on timeout.
            ttl: Default time-to-live in seconds.
            prefix: Key prefix for cache entries.
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis client is not available. Please install it with `pip install redis`."
            )

        self.default_ttl = ttl
        self.prefix = prefix
        self._executor = ThreadPoolExecutor(max_workers=4)

        # Parse connection information
        if connection_string:
            parsed = urlparse(connection_string)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            username = parsed.username
            password = parsed.password
            path = parsed.path
            database = int(path[1:]) if path and path[1:].isdigit() else 0
        else:
            # Use the first host by default if hosts are provided
            if hosts and len(hosts) > 0:
                host_parts = hosts[0].split(":")
                host = host_parts[0]
                port = int(host_parts[1]) if len(host_parts) > 1 else 6379
            else:
                host = "localhost"
                port = 6379

        # Create Redis client
        if use_connection_pool:
            self._pool = redis.ConnectionPool(
                host=host,
                port=port,
                username=username,
                password=password,
                db=database,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                max_connections=max_connections,
            )
            self._client = redis.Redis(
                connection_pool=self._pool, retry_on_timeout=retry_on_timeout
            )
        else:
            self._pool = None
            self._client = redis.Redis(
                host=host,
                port=port,
                username=username,
                password=password,
                db=database,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                retry_on_timeout=retry_on_timeout,
            )

        # Create async Redis client
        if use_connection_pool:
            self._async_pool = redis.asyncio.ConnectionPool(
                host=host,
                port=port,
                username=username,
                password=password,
                db=database,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                max_connections=max_connections,
            )
            self._async_client = redis.asyncio.Redis(
                connection_pool=self._async_pool, retry_on_timeout=retry_on_timeout
            )
        else:
            self._async_pool = None
            self._async_client = redis.asyncio.Redis(
                host=host,
                port=port,
                username=username,
                password=password,
                db=database,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                retry_on_timeout=retry_on_timeout,
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
            return self._deserialize(value)
        except redis.RedisError as e:
            logger.warning(f"Error getting value from Redis: {e}")
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
            value = await self._async_client.get(full_key)

            if value is None:
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return self._deserialize(value)
        except redis.RedisError as e:
            logger.warning(f"Error getting value from Redis: {e}")
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
            serialized_value = self._serialize(value)

            if ttl is None:
                ttl = self.default_ttl

            result = self._client.set(full_key, serialized_value, ex=ttl)

            if result:
                self._stats["insertions"] += 1

            return bool(result)
        except redis.RedisError as e:
            logger.warning(f"Error setting value in Redis: {e}")
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

            result = await self._async_client.set(full_key, serialized_value, ex=ttl)

            if result:
                self._stats["insertions"] += 1

            return bool(result)
        except redis.RedisError as e:
            logger.warning(f"Error setting value in Redis: {e}")
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

            return bool(result)
        except redis.RedisError as e:
            logger.warning(f"Error deleting value from Redis: {e}")
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
            result = await self._async_client.delete(full_key)

            if result:
                self._stats["deletions"] += 1

            return bool(result)
        except redis.RedisError as e:
            logger.warning(f"Error deleting value from Redis: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        Args:
            pattern: The pattern to match against cache keys.

        Returns:
            The number of keys invalidated.
        """
        try:
            full_pattern = self._get_full_key(pattern)
            keys = list(self._client.scan_iter(match=full_pattern))

            if not keys:
                return 0

            count = self._client.delete(*keys)
            self._stats["deletions"] += count

            return count
        except redis.RedisError as e:
            logger.warning(f"Error invalidating pattern in Redis: {e}")
            return 0

    async def invalidate_pattern_async(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern asynchronously.

        Args:
            pattern: The pattern to match against cache keys.

        Returns:
            The number of keys invalidated.
        """
        try:
            full_pattern = self._get_full_key(pattern)

            # Scan for matching keys
            keys = []
            cursor = b"0"

            while cursor != b"0":
                cursor, partial_keys = await self._async_client.scan(
                    cursor=cursor, match=full_pattern
                )
                keys.extend(partial_keys)

            if not keys:
                return 0

            count = await self._async_client.delete(*keys)
            self._stats["deletions"] += count

            return count
        except redis.RedisError as e:
            logger.warning(f"Error invalidating pattern in Redis: {e}")
            return 0

    def clear(self) -> bool:
        """Clear all cached values with this prefix.

        Returns:
            True if the cache was successfully cleared, False otherwise.
        """
        try:
            # Delete all keys with the specified prefix
            pattern = self._get_full_key("*")
            keys = list(self._client.scan_iter(match=pattern))

            if not keys:
                return True

            self._client.delete(*keys)
            return True
        except redis.RedisError as e:
            logger.warning(f"Error clearing Redis cache: {e}")
            return False

    async def clear_async(self) -> bool:
        """Clear all cached values with this prefix asynchronously.

        Returns:
            True if the cache was successfully cleared, False otherwise.
        """
        try:
            # Delete all keys with the specified prefix
            pattern = self._get_full_key("*")

            # Scan for matching keys
            keys = []
            cursor = b"0"

            while cursor != b"0":
                cursor, partial_keys = await self._async_client.scan(
                    cursor=cursor, match=pattern
                )
                keys.extend(partial_keys)

            if not keys:
                return True

            await self._async_client.delete(*keys)
            return True
        except redis.RedisError as e:
            logger.warning(f"Error clearing Redis cache: {e}")
            return False

    def check_health(self) -> bool:
        """Check the health of the cache.

        Returns:
            True if the cache is healthy, False otherwise.
        """
        try:
            # Ping the Redis server
            return self._client.ping()
        except redis.RedisError:
            return False

    async def check_health_async(self) -> bool:
        """Check the health of the cache asynchronously.

        Returns:
            True if the cache is healthy, False otherwise.
        """
        try:
            # Ping the Redis server
            return await self._async_client.ping()
        except redis.RedisError:
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
            stats["hit_rate"] = (
                stats["hits"] / total_requests if total_requests > 0 else 0
            )

            # Add uptime
            stats["uptime"] = time.time() - stats["created_at"]

            # Add Redis info
            info = self._client.info()
            stats["redis_version"] = info.get("redis_version")
            stats["used_memory"] = info.get("used_memory")
            stats["used_memory_human"] = info.get("used_memory_human")
            stats["connected_clients"] = info.get("connected_clients")
            stats["total_connections_received"] = info.get("total_connections_received")
            stats["total_commands_processed"] = info.get("total_commands_processed")

            # Count keys with the specified prefix
            pattern = self._get_full_key("*")
            stats["key_count"] = sum(1 for _ in self._client.scan_iter(match=pattern))

            return stats
        except redis.RedisError as e:
            logger.warning(f"Error getting Redis statistics: {e}")
            return self._stats.copy()

    async def get_stats_async(self) -> Dict[str, Any]:
        """Get cache statistics asynchronously.

        Returns:
            A dictionary with cache statistics.
        """
        try:
            # Copy stats and add current info
            stats = self._stats.copy()

            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            stats["hit_rate"] = (
                stats["hits"] / total_requests if total_requests > 0 else 0
            )

            # Add uptime
            stats["uptime"] = time.time() - stats["created_at"]

            # Add Redis info
            info = await self._async_client.info()
            stats["redis_version"] = info.get("redis_version")
            stats["used_memory"] = info.get("used_memory")
            stats["used_memory_human"] = info.get("used_memory_human")
            stats["connected_clients"] = info.get("connected_clients")
            stats["total_connections_received"] = info.get("total_connections_received")
            stats["total_commands_processed"] = info.get("total_commands_processed")

            # Count keys with the specified prefix
            pattern = self._get_full_key("*")
            key_count = 0
            cursor = b"0"

            while cursor != b"0":
                cursor, partial_keys = await self._async_client.scan(
                    cursor=cursor, match=pattern
                )
                key_count += len(partial_keys)

            stats["key_count"] = key_count

            return stats
        except redis.RedisError as e:
            logger.warning(f"Error getting Redis statistics: {e}")
            return self._stats.copy()

    def close(self) -> None:
        """Close the cache and release resources."""
        # Close the Redis clients
        try:
            if hasattr(self, "_client") and self._client:
                self._client.close()

            if hasattr(self, "_async_client") and self._async_client:
                asyncio.get_event_loop().run_until_complete(self._async_client.close())

            # Close the connection pools
            if hasattr(self, "_pool") and self._pool:
                self._pool.disconnect()

            if hasattr(self, "_async_pool") and self._async_pool:
                asyncio.get_event_loop().run_until_complete(
                    self._async_pool.disconnect()
                )
        except Exception as e:
            logger.warning(f"Error closing Redis connections: {e}")

    def multi_get(self, keys: list[str]) -> Dict[str, Any]:
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

            # Get values from Redis
            values = self._client.mget(full_keys)

            # Create result dictionary
            result = {}
            for i, value in enumerate(values):
                if value is not None:
                    result[keys[i]] = self._deserialize(value)
                    self._stats["hits"] += 1
                else:
                    self._stats["misses"] += 1

            return result
        except redis.RedisError as e:
            logger.warning(f"Error getting multiple values from Redis: {e}")
            return {}

    async def multi_get_async(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values from the cache asynchronously.

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

            # Get values from Redis
            values = await self._async_client.mget(full_keys)

            # Create result dictionary
            result = {}
            for i, value in enumerate(values):
                if value is not None:
                    result[keys[i]] = self._deserialize(value)
                    self._stats["hits"] += 1
                else:
                    self._stats["misses"] += 1

            return result
        except redis.RedisError as e:
            logger.warning(f"Error getting multiple values from Redis: {e}")
            return {}

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
            # Get full keys and serialize values
            pipeline = self._client.pipeline()

            for key, value in mapping.items():
                full_key = self._get_full_key(key)
                serialized_value = self._serialize(value)

                if ttl is None:
                    ttl = self.default_ttl

                pipeline.set(full_key, serialized_value, ex=ttl)

            # Execute the pipeline
            results = pipeline.execute()
            success = all(results)

            if success:
                self._stats["insertions"] += len(mapping)

            return success
        except redis.RedisError as e:
            logger.warning(f"Error setting multiple values in Redis: {e}")
            return False

    async def multi_set_async(
        self, mapping: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in the cache asynchronously.

        Args:
            mapping: A dictionary mapping keys to values.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.

        Returns:
            True if all values were successfully cached, False otherwise.
        """
        if not mapping:
            return True

        try:
            # Get full keys and serialize values
            pipeline = self._async_client.pipeline()

            for key, value in mapping.items():
                full_key = self._get_full_key(key)
                serialized_value = self._serialize(value)

                if ttl is None:
                    ttl = self.default_ttl

                pipeline.set(full_key, serialized_value, ex=ttl)

            # Execute the pipeline
            results = await pipeline.execute()
            success = all(results)

            if success:
                self._stats["insertions"] += len(mapping)

            return success
        except redis.RedisError as e:
            logger.warning(f"Error setting multiple values in Redis: {e}")
            return False

    def multi_delete(self, keys: list[str]) -> bool:
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

            # Delete keys from Redis
            deleted = self._client.delete(*full_keys)

            if deleted:
                self._stats["deletions"] += deleted

            # Consider the operation successful if at least one key was deleted
            return deleted > 0
        except redis.RedisError as e:
            logger.warning(f"Error deleting multiple values from Redis: {e}")
            return False

    async def multi_delete_async(self, keys: list[str]) -> bool:
        """Delete multiple values from the cache asynchronously.

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

            # Delete keys from Redis
            deleted = await self._async_client.delete(*full_keys)

            if deleted:
                self._stats["deletions"] += deleted

            # Consider the operation successful if at least one key was deleted
            return deleted > 0
        except redis.RedisError as e:
            logger.warning(f"Error deleting multiple values from Redis: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key.

        Returns:
            True if the key exists, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            return bool(self._client.exists(full_key))
        except redis.RedisError as e:
            logger.warning(f"Error checking if key exists in Redis: {e}")
            return False

    async def exists_async(self, key: str) -> bool:
        """Check if a key exists in the cache asynchronously.

        Args:
            key: The cache key.

        Returns:
            True if the key exists, False otherwise.
        """
        try:
            full_key = self._get_full_key(key)
            return bool(await self._async_client.exists(full_key))
        except redis.RedisError as e:
            logger.warning(f"Error checking if key exists in Redis: {e}")
            return False

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
            return self._client.incrby(full_key, amount)
        except redis.RedisError as e:
            logger.warning(f"Error incrementing value in Redis: {e}")
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
            return await self._async_client.incrby(full_key, amount)
        except redis.RedisError as e:
            logger.warning(f"Error incrementing value in Redis: {e}")
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
            return self._client.decrby(full_key, amount)
        except redis.RedisError as e:
            logger.warning(f"Error decrementing value in Redis: {e}")
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
            return await self._async_client.decrby(full_key, amount)
        except redis.RedisError as e:
            logger.warning(f"Error decrementing value in Redis: {e}")
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
            return bool(self._client.expire(full_key, ttl))
        except redis.RedisError as e:
            logger.warning(f"Error updating TTL in Redis: {e}")
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
            return bool(await self._async_client.expire(full_key, ttl))
        except redis.RedisError as e:
            logger.warning(f"Error updating TTL in Redis: {e}")
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
        """Serialize a value for storage in Redis.

        Args:
            value: The value to serialize.

        Returns:
            The serialized value as bytes.
        """
        # Use pickle for serialization
        return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize a value from Redis.

        Args:
            data: The serialized value.

        Returns:
            The deserialized value.
        """
        # Use pickle for deserialization
        return pickle.loads(data)
