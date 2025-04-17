"""Time-based cache invalidation module.

This module provides a time-based invalidation strategy.
"""

from typing import Any, Dict, Optional, Tuple, Union
import random
import time


class TimeBasedInvalidation:
    """Time-based cache invalidation strategy.
    
    This strategy invalidates cache entries based on their time-to-live (TTL).
    """
    
    def __init__(self, default_ttl: int = 300, ttl_jitter: float = 0.1):
        """Initialize the time-based invalidation strategy.
        
        Args:
            default_ttl: The default time-to-live in seconds.
            ttl_jitter: The factor to use for jitter (0.0 to 1.0).
        """
        self.default_ttl = default_ttl
        self.ttl_jitter = ttl_jitter
    
    def invalidate(self, key: str, value: Any) -> bool:
        """Determine if a value should be invalidated based on its TTL.
        
        Args:
            key: The cache key.
            value: The cached value.
            
        Returns:
            True if the value should be invalidated, False otherwise.
        """
        # Check if the value has a TTL attribute or metadata
        if hasattr(value, "ttl") and isinstance(value.ttl, (int, float)):
            # Check if the TTL has expired
            return value.ttl < time.time()
        
        if hasattr(value, "metadata") and isinstance(value.metadata, dict):
            if "ttl" in value.metadata and isinstance(value.metadata["ttl"], (int, float)):
                # Check if the TTL has expired
                return value.metadata["ttl"] < time.time()
            
            if "expiry" in value.metadata and isinstance(value.metadata["expiry"], (int, float)):
                # Check if the expiry time has passed
                return value.metadata["expiry"] < time.time()
        
        # For tuple values (value, expiry), common in many cache implementations
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], (int, float)):
            # Check if the expiry time has passed
            return value[1] < time.time()
        
        # No TTL information found
        return False
    
    def get_ttl(self, key: str, value: Any) -> int:
        """Get the TTL for a value.
        
        Args:
            key: The cache key.
            value: The cached value.
            
        Returns:
            The TTL in seconds.
        """
        # Check if the value has a TTL attribute or metadata
        if hasattr(value, "ttl") and isinstance(value.ttl, (int, float)):
            # Use the TTL from the value
            return max(0, int(value.ttl - time.time()))
        
        if hasattr(value, "metadata") and isinstance(value.metadata, dict):
            if "ttl" in value.metadata and isinstance(value.metadata["ttl"], (int, float)):
                # Use the TTL from the metadata
                return max(0, int(value.metadata["ttl"] - time.time()))
            
            if "expiry" in value.metadata and isinstance(value.metadata["expiry"], (int, float)):
                # Use the expiry time from the metadata
                return max(0, int(value.metadata["expiry"] - time.time()))
        
        # For tuple values (value, expiry), common in many cache implementations
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], (int, float)):
            # Use the expiry time from the tuple
            return max(0, int(value[1] - time.time()))
        
        # No TTL information found, use default
        return self.default_ttl
    
    def apply_jitter(self, ttl: int) -> int:
        """Apply jitter to a TTL to prevent cache stampede.
        
        Args:
            ttl: The time-to-live in seconds.
            
        Returns:
            The TTL with jitter applied.
        """
        if self.ttl_jitter <= 0.0:
            return ttl
        
        # Apply jitter (randomize TTL by +/- ttl_jitter)
        jitter_range = max(1, int(ttl * self.ttl_jitter))
        return ttl + random.randint(-jitter_range, jitter_range)
