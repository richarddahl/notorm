"""Base distributed cache module.

This module provides the base class for distributed cache implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import time


class DistributedCache(ABC):
    """Base class for distributed cache implementations."""
    
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
    async def get_async(self, key: str) -> Any:
        """Get a value from the cache asynchronously.
        
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
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache asynchronously.
        
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
    async def delete_async(self, key: str) -> bool:
        """Delete a value from the cache asynchronously.
        
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
    async def invalidate_pattern_async(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern asynchronously.
        
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
    async def clear_async(self) -> bool:
        """Clear all cached values asynchronously.
        
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
    async def check_health_async(self) -> bool:
        """Check the health of the cache asynchronously.
        
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
    async def get_stats_async(self) -> Dict[str, Any]:
        """Get cache statistics asynchronously.
        
        Returns:
            A dictionary with cache statistics.
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the cache and release resources."""
        pass
    
    @abstractmethod
    def multi_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from the cache.
        
        Args:
            keys: The cache keys.
            
        Returns:
            A dictionary mapping keys to values. Keys not found in the cache are omitted.
        """
        pass
    
    @abstractmethod
    async def multi_get_async(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from the cache asynchronously.
        
        Args:
            keys: The cache keys.
            
        Returns:
            A dictionary mapping keys to values. Keys not found in the cache are omitted.
        """
        pass
    
    @abstractmethod
    def multi_set(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache.
        
        Args:
            mapping: A dictionary mapping keys to values.
            ttl: Optional time-to-live in seconds.
            
        Returns:
            True if all values were successfully cached, False otherwise.
        """
        pass
    
    @abstractmethod
    async def multi_set_async(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache asynchronously.
        
        Args:
            mapping: A dictionary mapping keys to values.
            ttl: Optional time-to-live in seconds.
            
        Returns:
            True if all values were successfully cached, False otherwise.
        """
        pass
    
    @abstractmethod
    def multi_delete(self, keys: List[str]) -> bool:
        """Delete multiple values from the cache.
        
        Args:
            keys: The cache keys.
            
        Returns:
            True if all values were successfully deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    async def multi_delete_async(self, keys: List[str]) -> bool:
        """Delete multiple values from the cache asynchronously.
        
        Args:
            keys: The cache keys.
            
        Returns:
            True if all values were successfully deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the key exists, False otherwise.
        """
        pass
    
    @abstractmethod
    async def exists_async(self, key: str) -> bool:
        """Check if a key exists in the cache asynchronously.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the key exists, False otherwise.
        """
        pass
    
    @abstractmethod
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value.
        
        Args:
            key: The cache key.
            amount: The amount to increment by.
            
        Returns:
            The new value or None if the operation failed.
        """
        pass
    
    @abstractmethod
    async def increment_async(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value asynchronously.
        
        Args:
            key: The cache key.
            amount: The amount to increment by.
            
        Returns:
            The new value or None if the operation failed.
        """
        pass
    
    @abstractmethod
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a numeric value.
        
        Args:
            key: The cache key.
            amount: The amount to decrement by.
            
        Returns:
            The new value or None if the operation failed.
        """
        pass
    
    @abstractmethod
    async def decrement_async(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a numeric value asynchronously.
        
        Args:
            key: The cache key.
            amount: The amount to decrement by.
            
        Returns:
            The new value or None if the operation failed.
        """
        pass
    
    @abstractmethod
    def touch(self, key: str, ttl: int) -> bool:
        """Update the TTL of a cached value.
        
        Args:
            key: The cache key.
            ttl: The new TTL in seconds.
            
        Returns:
            True if the TTL was successfully updated, False otherwise.
        """
        pass
    
    @abstractmethod
    async def touch_async(self, key: str, ttl: int) -> bool:
        """Update the TTL of a cached value asynchronously.
        
        Args:
            key: The cache key.
            ttl: The new TTL in seconds.
            
        Returns:
            True if the TTL was successfully updated, False otherwise.
        """
        pass
