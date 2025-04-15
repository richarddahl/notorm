"""
Tests for the query cache module.

These tests verify the functionality of the query cache system.
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
import hashlib

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.query_cache import (
    CacheBackend,
    CacheStrategy,
    QueryCacheConfig,
    QueryCacheStats,
    QueryCacheKey,
    CachedResult,
    QueryCache,
    cached,
    cached_query,
    _get_default_cache,
    get_named_cache,
    set_default_cache,
    clear_all_caches,
)
from uno.core.errors.result import Result, Success, Failure


# Test QueryCacheKey
def test_query_cache_key():
    """Test QueryCacheKey class."""
    # Test hash_query for string
    key1 = QueryCacheKey.hash_query("SELECT * FROM users")
    assert isinstance(key1, str)
    assert len(key1) == 32  # MD5 hash length
    
    # Test hash_query with params
    key2 = QueryCacheKey.hash_query(
        "SELECT * FROM users WHERE id = :id",
        {"id": 1}
    )
    assert key2 != key1
    
    # Test hash_query with table names
    key3 = QueryCacheKey.hash_query(
        "SELECT * FROM users",
        None,
        ["users"]
    )
    assert key3 != key1
    
    # Test from_text
    key4 = QueryCacheKey.from_text("SELECT * FROM users")
    assert key4 == key1
    
    # Test from_function
    def test_func(a, b, c=None):
        pass
    
    key5 = QueryCacheKey.from_function(test_func, 1, 2, c=3)
    key6 = QueryCacheKey.from_function(test_func, 1, 2, c=3)
    key7 = QueryCacheKey.from_function(test_func, 1, 2, c=4)
    
    assert key5 == key6
    assert key5 != key7


# Test CachedResult
def test_cached_result():
    """Test CachedResult class."""
    # Create a cached result
    result = CachedResult(
        data="test_data",
        expires_at=time.time() + 60.0,
        query_time=0.1,
    )
    
    # Test initial state
    assert result.data == "test_data"
    assert result.access_count == 0
    assert result.query_time == 0.1
    assert not result.is_expired()
    
    # Test update_access
    result.update_access()
    assert result.access_count == 1
    assert result.last_accessed > result.created_at
    
    # Test get_value
    value = result.get_value()
    assert value == "test_data"
    assert result.access_count == 2
    
    # Test add_dependency
    result.add_dependency("users")
    assert "users" in result.dependencies
    
    # Test expiration
    result.expires_at = time.time() - 1.0
    assert result.is_expired()
    
    # Test properties
    assert result.age > 0
    assert result.idle_time >= 0


# Test QueryCacheStats
def test_query_cache_stats():
    """Test QueryCacheStats class."""
    stats = QueryCacheStats()
    
    # Test initial state
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.hit_rate == 0.0
    
    # Test record_hit
    stats.record_hit(0.1)
    assert stats.hits == 1
    assert stats.total_hit_time == 0.1
    
    # Test record_miss
    stats.record_miss(0.2)
    assert stats.misses == 1
    assert stats.total_miss_time == 0.2
    
    # Test hit_rate
    assert stats.hit_rate == 0.5  # 1 hit, 1 miss
    
    # Test avg_hit_time
    assert stats.avg_hit_time == 0.1
    
    # Test avg_miss_time
    assert stats.avg_miss_time == 0.2
    
    # Test record_entry_added and record_entry_removed
    stats.record_entry_added()
    assert stats.current_entries == 1
    assert stats.total_entries == 1
    
    stats.record_entry_added()
    assert stats.current_entries == 2
    assert stats.total_entries == 2
    
    stats.record_entry_removed()
    assert stats.current_entries == 1
    assert stats.total_entries == 2
    
    # Test record_invalidation
    stats.record_invalidation()
    assert stats.invalidations == 1
    
    # Test record_eviction
    stats.record_eviction()
    assert stats.evictions == 1
    
    # Test dependency tracking
    stats.record_dependency()
    assert stats.dependencies_tracked == 1
    
    stats.record_cascading_invalidation()
    assert stats.cascading_invalidations == 1
    
    # Test get_summary
    summary = stats.get_summary()
    assert "performance" in summary
    assert "size" in summary
    assert "invalidation" in summary
    assert summary["performance"]["hits"] == 1
    assert summary["performance"]["misses"] == 1
    assert summary["performance"]["hit_rate"] == 0.5


# Test QueryCache
@pytest.mark.asyncio
async def test_query_cache():
    """Test QueryCache class."""
    # Create a cache with memory backend
    config = QueryCacheConfig(
        enabled=True,
        backend=CacheBackend.MEMORY,
        strategy=CacheStrategy.SIMPLE,
        default_ttl=60.0,
    )
    cache = QueryCache(config=config)
    
    # Test setting and getting values
    key = "test_key"
    value = "test_value"
    
    # Initially, the key should not exist
    result = await cache.get(key)
    assert result.is_failure
    assert cache.stats.misses == 1
    
    # Set the value
    await cache.set(key, value)
    assert len(cache._cache) == 1
    assert cache.stats.current_entries == 1
    
    # Get the value
    result = await cache.get(key)
    assert result.is_success
    assert result.value == value
    assert cache.stats.hits == 1
    
    # Test invalidation
    await cache.invalidate(key)
    assert len(cache._cache) == 0
    assert cache.stats.invalidations == 1
    
    # Key should no longer exist
    result = await cache.get(key)
    assert result.is_failure
    assert cache.stats.misses == 2
    
    # Test dependencies
    key1 = "users_list"
    key2 = "user_count"
    value1 = ["user1", "user2"]
    value2 = 2
    
    # Set values with dependencies
    await cache.set(key1, value1, dependencies=["users"])
    await cache.set(key2, value2, dependencies=["users"])
    
    assert len(cache._cache) == 2
    assert "users" in cache._dependencies
    assert len(cache._dependencies["users"]) == 2
    
    # Invalidate by table
    await cache.invalidate_by_table("users")
    
    assert len(cache._cache) == 0
    assert cache.stats.invalidations == 3  # 1 + 2 (from dependencies)
    assert cache.stats.cascading_invalidations == 1
    
    # Test clear
    await cache.set(key, value)
    assert len(cache._cache) == 1
    
    await cache.clear()
    assert len(cache._cache) == 0
    assert len(cache._dependencies) == 0
    assert cache.stats.hits == 0  # Stats reset
    
    # Test stats
    stats = cache.get_stats()
    assert "config" in stats
    assert stats["config"]["backend"] == "memory"


# Test cached decorator
@pytest.mark.asyncio
async def test_cached_decorator():
    """Test cached decorator."""
    # Create a cache
    cache = QueryCache(
        config=QueryCacheConfig(
            enabled=True,
            backend=CacheBackend.MEMORY,
            strategy=CacheStrategy.SIMPLE,
            default_ttl=60.0,
        )
    )
    
    # Create a function to cache
    func_call_count = 0
    
    @cached(ttl=30.0, cache_instance=cache)
    async def test_func(a, b):
        nonlocal func_call_count
        func_call_count += 1
        return a + b
    
    # Call the function
    result1 = await test_func(1, 2)
    assert result1 == 3
    assert func_call_count == 1
    
    # Call again with same args, should use cache
    result2 = await test_func(1, 2)
    assert result2 == 3
    assert func_call_count == 1  # Still 1, cached
    
    # Call with different args
    result3 = await test_func(2, 3)
    assert result3 == 5
    assert func_call_count == 2  # Increased, not cached
    
    # Check cache stats
    assert cache.stats.hits == 1
    assert cache.stats.misses == 2
    assert len(cache._cache) == 2


# Test cached_query decorator
@pytest.mark.asyncio
async def test_cached_query_decorator():
    """Test cached_query decorator."""
    # Create a cache
    cache = QueryCache(
        config=QueryCacheConfig(
            enabled=True,
            backend=CacheBackend.MEMORY,
            strategy=CacheStrategy.SIMPLE,
            default_ttl=60.0,
        )
    )
    
    # Create a mock session
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(return_value=AsyncMock(
        fetchall=AsyncMock(return_value=["result1", "result2"])
    ))
    
    # Create a function to cache
    func_call_count = 0
    
    @cached_query(ttl=30.0, dependencies=["users"], cache_instance=cache)
    async def test_query(session, user_id):
        nonlocal func_call_count
        func_call_count += 1
        result = await session.execute(f"SELECT * FROM users WHERE id = {user_id}")
        return await result.fetchall()
    
    # Call the function
    result1 = await test_query(session, 1)
    assert result1 == ["result1", "result2"]
    assert func_call_count == 1
    
    # Call again with same args, should use cache
    result2 = await test_query(session, 1)
    assert result2 == ["result1", "result2"]
    assert func_call_count == 1  # Still 1, cached
    
    # Call with different args
    result3 = await test_query(session, 2)
    assert result3 == ["result1", "result2"]
    assert func_call_count == 2  # Increased, not cached
    
    # Check cache stats
    assert cache.stats.hits == 1
    assert cache.stats.misses == 2
    assert len(cache._cache) == 2
    
    # Test invalidation by table
    await cache.invalidate_by_table("users")
    
    # All cache entries should be gone
    assert len(cache._cache) == 0
    
    # Call again, should miss cache
    result4 = await test_query(session, 1)
    assert result4 == ["result1", "result2"]
    assert func_call_count == 3  # Increased, cache invalidated


# Test Redis backend
@pytest.mark.asyncio
async def test_redis_backend():
    """Test QueryCache with Redis backend."""
    # Only run if aioredis is available
    try:
        import redis.asyncio as redis
    except ImportError:
        pytest.skip("redis.asyncio not available")
    
    # Create a mock Redis client
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)  # Simulate cache miss initially
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.keys = AsyncMock(return_value=[])
    
    # Create a cache with Redis backend
    config = QueryCacheConfig(
        enabled=True,
        backend=CacheBackend.REDIS,
        strategy=CacheStrategy.SIMPLE,
        default_ttl=60.0,
    )
    cache = QueryCache(config=config)
    
    # Replace the Redis client with our mock
    with patch.object(cache, "get_redis_client", return_value=mock_redis):
        # Test set operation
        key = "test_key"
        value = "test_value"
        await cache.set(key, value)
        
        # Verify Redis setex was called
        mock_redis.setex.assert_awaited_once()
        
        # We need to ensure the memory cache is empty
        cache._cache = {}
        
        # Test get operation - make sure we only check Redis
        result = await cache.get(key)
        
        # Verify Redis get was called
        mock_redis.get.assert_awaited_once()
        assert result.is_failure  # Should be a miss since we're returning None
        
        # Simulate a hit by setting up a pickled value
        import pickle
        cached_result = CachedResult(
            data=value,
            expires_at=time.time() + 60.0,
        )
        mock_redis.get = AsyncMock(return_value=pickle.dumps(cached_result))
        
        # Get should now hit
        result = await cache.get(key)
        assert result.is_success
        assert result.value == value
        
        # Test invalidate
        await cache.invalidate(key)
        mock_redis.delete.assert_awaited_once()
        
        # Test clear
        await cache.clear()
        mock_redis.keys.assert_awaited_once()


# Test cache manager functions
@pytest.mark.asyncio
async def test_cache_manager():
    """Test cache manager functions."""
    # Get default cache
    default_cache = _get_default_cache()
    assert isinstance(default_cache, QueryCache)
    
    # Set default cache
    new_cache = QueryCache()
    set_default_cache(new_cache)
    assert _get_default_cache() is new_cache
    
    # Get named cache
    named_cache = get_named_cache("test_cache")
    assert isinstance(named_cache, QueryCache)
    assert named_cache is not new_cache
    
    # Clear all caches
    await clear_all_caches()
    
    # Restore default cache for other tests
    set_default_cache(default_cache)