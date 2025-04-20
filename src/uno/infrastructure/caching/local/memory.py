"""Memory cache module.

This module provides an in-memory cache implementation.
"""

from typing import Any, Dict, List, Optional, Tuple, Set, Union
import re
import threading
import time
import fnmatch
from collections import OrderedDict

from uno.caching.local.base import LocalCache


class MemoryCache(LocalCache):
    """In-memory cache implementation.

    This implementation uses a dictionary to store values in memory. It supports
    LRU eviction policy to keep memory usage under control.
    """

    def __init__(self, max_size: int = 1000, ttl: int = 300, lru_policy: bool = True):
        """Initialize the memory cache.

        Args:
            max_size: The maximum number of items to store in the cache.
            ttl: The default time-to-live in seconds.
            lru_policy: Whether to use the LRU eviction policy.
        """
        self.max_size = max_size
        self.default_ttl = ttl
        self.lru_policy = lru_policy

        # Use OrderedDict if LRU policy is enabled
        if lru_policy:
            self._cache: dict[str, Tuple[Any, float]] = OrderedDict()
        else:
            self._cache: dict[str, Tuple[Any, float]] = {}

        self._lock = threading.RLock()

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "size": 0,
            "max_size": max_size,
            "insertions": 0,
            "deletions": 0,
            "created_at": time.time(),
        }

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found or expired.
        """
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            value, expiry = self._cache[key]

            # Check if the value has expired
            if expiry < time.time():
                # Remove expired value
                del self._cache[key]
                self._stats["size"] -= 1
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None

            # Update access order if using LRU policy
            if self.lru_policy:
                self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.

        Returns:
            True if the value was successfully cached, False otherwise.
        """
        with self._lock:
            # Check if we need to evict an item due to size limit
            if key not in self._cache and len(self._cache) >= self.max_size:
                self._evict()

            # Calculate expiry time
            if ttl is None:
                ttl = self.default_ttl
            expiry = time.time() + ttl

            # Update stats for new insertion
            if key not in self._cache:
                self._stats["size"] += 1
                self._stats["insertions"] += 1

            # Store the value with its expiry time
            self._cache[key] = (value, expiry)

            # Update access order if using LRU policy
            if self.lru_policy:
                self._cache.move_to_end(key)

            return True

    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key.

        Returns:
            True if the value was successfully deleted, False otherwise.
        """
        with self._lock:
            if key not in self._cache:
                return False

            del self._cache[key]
            self._stats["size"] -= 1
            self._stats["deletions"] += 1
            return True

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        This method uses Unix shell-style wildcards (e.g., * matches any characters).

        Args:
            pattern: The pattern to match against cache keys.

        Returns:
            The number of keys invalidated.
        """
        with self._lock:
            # Convert wildcard pattern to regex
            keys_to_delete = [
                k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)
            ]

            for key in keys_to_delete:
                del self._cache[key]
                self._stats["size"] -= 1
                self._stats["deletions"] += 1

            return len(keys_to_delete)

    def clear(self) -> bool:
        """Clear all cached values.

        Returns:
            True if the cache was successfully cleared, False otherwise.
        """
        with self._lock:
            size = len(self._cache)
            self._cache.clear()

            # Update stats
            self._stats["deletions"] += size
            self._stats["size"] = 0

            return True

    def check_health(self) -> bool:
        """Check the health of the cache.

        For the memory cache, this always returns True as the cache is healthy
        as long as the process is running.

        Returns:
            True if the cache is healthy, False otherwise.
        """
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            A dictionary with cache statistics.
        """
        with self._lock:
            # Copy stats and add current size
            stats = self._stats.copy()
            stats["size"] = len(self._cache)

            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            stats["hit_rate"] = (
                stats["hits"] / total_requests if total_requests > 0 else 0
            )

            # Add uptime
            stats["uptime"] = time.time() - stats["created_at"]

            return stats

    def close(self) -> None:
        """Close the cache and release resources.

        For memory cache, this simply clears the cache.
        """
        with self._lock:
            self._cache.clear()
            self._stats["size"] = 0

    def multi_get(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from the cache.

        Args:
            keys: The cache keys.

        Returns:
            A dictionary mapping keys to values. Keys not found in the cache are omitted.
        """
        with self._lock:
            result = {}
            now = time.time()

            for key in keys:
                if key in self._cache:
                    value, expiry = self._cache[key]

                    # Check if the value has expired
                    if expiry >= now:
                        result[key] = value
                        self._stats["hits"] += 1

                        # Update access order if using LRU policy
                        if self.lru_policy:
                            self._cache.move_to_end(key)
                    else:
                        # Remove expired value
                        del self._cache[key]
                        self._stats["size"] -= 1
                        self._stats["expirations"] += 1
                        self._stats["misses"] += 1
                else:
                    self._stats["misses"] += 1

            return result

    def multi_set(self, mapping: dict[str, Any], ttl: int | None = None) -> bool:
        """Set multiple values in the cache.

        Args:
            mapping: A dictionary mapping keys to values.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.

        Returns:
            True if all values were successfully cached, False otherwise.
        """
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl

            expiry = time.time() + ttl

            for key, value in mapping.items():
                # Check if we need to evict an item due to size limit
                if key not in self._cache and len(self._cache) >= self.max_size:
                    self._evict()

                # Update stats for new insertion
                if key not in self._cache:
                    self._stats["size"] += 1
                    self._stats["insertions"] += 1

                # Store the value with its expiry time
                self._cache[key] = (value, expiry)

                # Update access order if using LRU policy
                if self.lru_policy:
                    self._cache.move_to_end(key)

            return True

    def multi_delete(self, keys: list[str]) -> bool:
        """Delete multiple values from the cache.

        Args:
            keys: The cache keys.

        Returns:
            True if all values were successfully deleted, False otherwise.
        """
        with self._lock:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
                    self._stats["size"] -= 1
                    self._stats["deletions"] += 1

            return True

    def touch(self, key: str, ttl: int) -> bool:
        """Update the TTL of a cached value.

        Args:
            key: The cache key.
            ttl: The new TTL in seconds.

        Returns:
            True if the TTL was successfully updated, False otherwise.
        """
        with self._lock:
            if key not in self._cache:
                return False

            value, _ = self._cache[key]
            expiry = time.time() + ttl
            self._cache[key] = (value, expiry)

            # Update access order if using LRU policy
            if self.lru_policy:
                self._cache.move_to_end(key)

            return True

    def _evict(self) -> None:
        """Evict an item from the cache based on the eviction policy."""
        if not self._cache:
            return

        if self.lru_policy:
            # With LRU policy, evict the least recently used item
            key, _ = self._cache.popitem(last=False)
        else:
            # Without LRU policy, evict a random item
            key = next(iter(self._cache.keys()))
            del self._cache[key]

        self._stats["size"] -= 1
        self._stats["evictions"] += 1
