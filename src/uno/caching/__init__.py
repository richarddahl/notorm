"""Uno Caching Framework.

This module provides a comprehensive caching framework for Uno applications,
including multi-level caching, distributed caching, cache invalidation strategies,
and monitoring tools.
"""

from uno.caching.config import CacheConfig
from uno.caching.manager import CacheManager
from uno.caching.local import LocalCache, MemoryCache, FileCache
from uno.caching.distributed import (
    DistributedCache, 
    RedisCache, 
    MemcachedCache
)
from uno.caching.decorators import (
    cached, 
    async_cached, 
    invalidate_cache,
    cache_aside
)
from uno.caching.key import get_cache_key
from uno.caching.invalidation import (
    InvalidationStrategy,
    TimeBasedInvalidation,
    EventBasedInvalidation,
    PatternBasedInvalidation
)
from uno.caching.monitoring import CacheMonitor

__version__ = "0.1.0"

__all__ = [
    "CacheConfig",
    "CacheManager",
    "LocalCache",
    "MemoryCache",
    "FileCache",
    "DistributedCache",
    "RedisCache",
    "MemcachedCache",
    "cached",
    "async_cached",
    "invalidate_cache",
    "cache_aside",
    "get_cache_key",
    "InvalidationStrategy",
    "TimeBasedInvalidation",
    "EventBasedInvalidation",
    "PatternBasedInvalidation",
    "CacheMonitor"
]
