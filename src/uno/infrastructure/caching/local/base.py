"""Base local cache module.

This module provides the base class for local cache implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import time


class LocalCache(ABC):
    """Base class for local cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds.

        Returns:
            True if the value was successfully cached, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key.

        Returns:
            True if the value was successfully deleted, False otherwise.
        """
        pass

    @abstractmethod
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        Args:
            pattern: The pattern to match against cache keys.

        Returns:
            The number of keys invalidated.
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cached values.

        Returns:
            True if the cache was successfully cleared, False otherwise.
        """
        pass

    @abstractmethod
    def check_health(self) -> bool:
        """Check the health of the cache.

        Returns:
            True if the cache is healthy, False otherwise.
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            A dictionary with cache statistics.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the cache and release resources."""
        pass

    def multi_get(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values from the cache.

        Args:
            keys: The cache keys.

        Returns:
            A dictionary mapping keys to values. Keys not found in the cache are omitted.
        """
        # Default implementation, can be overridden for more efficient batch operations
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def multi_set(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache.

        Args:
            mapping: A dictionary mapping keys to values.
            ttl: Optional time-to-live in seconds.

        Returns:
            True if all values were successfully cached, False otherwise.
        """
        # Default implementation, can be overridden for more efficient batch operations
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, ttl):
                success = False
        return success

    def multi_delete(self, keys: list[str]) -> bool:
        """Delete multiple values from the cache.

        Args:
            keys: The cache keys.

        Returns:
            True if all values were successfully deleted, False otherwise.
        """
        # Default implementation, can be overridden for more efficient batch operations
        success = True
        for key in keys:
            if not self.delete(key):
                success = False
        return success

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key.

        Returns:
            True if the key exists, False otherwise.
        """
        # Default implementation, can be overridden for more efficient implementation
        return self.get(key) is not None

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value.

        Args:
            key: The cache key.
            amount: The amount to increment by.

        Returns:
            The new value or None if the operation failed.
        """
        # Default implementation, can be overridden for atomic operations
        value = self.get(key)
        if value is None or not isinstance(value, (int, float)):
            return None
        new_value = value + amount
        if self.set(key, new_value):
            return new_value
        return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a numeric value.

        Args:
            key: The cache key.
            amount: The amount to decrement by.

        Returns:
            The new value or None if the operation failed.
        """
        # Default implementation, can be overridden for atomic operations
        return self.increment(key, -amount)

    def touch(self, key: str, ttl: int) -> bool:
        """Update the TTL of a cached value.

        Args:
            key: The cache key.
            ttl: The new TTL in seconds.

        Returns:
            True if the TTL was successfully updated, False otherwise.
        """
        # Default implementation, can be overridden for more efficient implementation
        value = self.get(key)
        if value is None:
            return False
        return self.set(key, value, ttl)
