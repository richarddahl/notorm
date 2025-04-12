"""Cache invalidation strategy module.

This module provides the base class for cache invalidation strategies.
"""

from typing import Any, Dict, List, Optional, Union, Protocol
import random
import time


class InvalidationProtocol(Protocol):
    """Protocol for invalidation strategies."""
    
    def invalidate(self, key: str, value: Any) -> bool:
        """Determine if a value should be invalidated.
        
        Args:
            key: The cache key.
            value: The cached value.
            
        Returns:
            True if the value should be invalidated, False otherwise.
        """
        ...


class InvalidationStrategy:
    """Base class for cache invalidation strategies.
    
    This class allows combining multiple invalidation strategies.
    """
    
    def __init__(self, strategies: Optional[List[InvalidationProtocol]] = None):
        """Initialize the invalidation strategy.
        
        Args:
            strategies: Optional list of invalidation strategies to combine.
        """
        self.strategies = strategies or []
    
    def invalidate(self, key: str, value: Any) -> bool:
        """Determine if a value should be invalidated.
        
        Args:
            key: The cache key.
            value: The cached value.
            
        Returns:
            True if the value should be invalidated, False otherwise.
        """
        # A value should be invalidated if any strategy says it should be invalidated
        return any(strategy.invalidate(key, value) for strategy in self.strategies)
    
    def add_strategy(self, strategy: InvalidationProtocol) -> None:
        """Add an invalidation strategy.
        
        Args:
            strategy: The invalidation strategy to add.
        """
        self.strategies.append(strategy)
    
    def apply_jitter(self, ttl: int, jitter_factor: float = 0.1) -> int:
        """Apply jitter to a TTL to prevent cache stampede.
        
        Args:
            ttl: The time-to-live in seconds.
            jitter_factor: The factor to use for jitter (0.0 to 1.0).
            
        Returns:
            The TTL with jitter applied.
        """
        if jitter_factor <= 0.0:
            return ttl
        
        # Apply jitter (randomize TTL by +/- jitter_factor)
        jitter_range = max(1, int(ttl * jitter_factor))
        return ttl + random.randint(-jitter_range, jitter_range)
