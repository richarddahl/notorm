"""
Integration tests for distributed cache functionality.

This module tests the distributed caching system in a real
environment with Redis, verifying that caching, invalidation,
and cross-process synchronization work correctly.
"""

import asyncio
import time
import pytest
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

from uno.caching.distributed import RedisCache
from uno.database.query_cache import (
    QueryCache,
    QueryCacheConfig,
    CacheBackend,
    CacheStrategy,
    cached_query,
    set_named_cache,
    get_named_cache,
    clear_all_caches,
)
from uno.database.session import async_session
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base


# Define test models
Base = declarative_base()


class TestCacheItem(Base):
    """Test model for cache integration tests."""

    __tablename__ = "test_cache_items"
    __test__ = False  # Prevent pytest from treating this as a test case

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    value = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))


@pytest.fixture(scope="module")
async def setup_test_db():
    """Set up test database tables and sample data."""
    from uno.database.session import get_engine

    engine = get_engine()

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Insert sample data
    async with async_session() as session:
        # Add items
        items = []
        for i in range(1, 21):
            item = TestCacheItem(
                name=f"Item {i}",
                description=f"Description for item {i}",
                value=float(i * 10),
                is_active=i % 2 == 0,
            )
            items.append(item)

        session.add_all(items)
        await session.commit()

    yield

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def redis_cache():
    """Create a Redis cache instance for testing."""
    from uno.settings import uno_settings

    # Use the test Redis URL from settings
    redis_url = uno_settings.REDIS_URL or "redis://localhost:6379/0"

    # Create the cache
    cache = RedisCache(
        url=redis_url,
        prefix="test_distributed_cache:",
        default_ttl=30.0,  # 30 seconds for testing
    )

    yield cache

    # Clean up
    await cache.clear()


@pytest.fixture
async def distributed_query_cache():
    """Create a distributed query cache instance for testing."""
    # Create cache configuration
    config = QueryCacheConfig(
        enabled=True,
        strategy=CacheStrategy.DEPENDENCY,
        backend=CacheBackend.REDIS,
        default_ttl=30.0,  # 30 seconds for testing
        track_dependencies=True,
        redis_url="redis://localhost:6379/0",  # Use default Redis or override
        redis_prefix="test_query_cache:",
    )

    # Create the cache
    cache = QueryCache(config=config)

    # Register as a named cache
    cache_name = "test_distributed_cache"
    set_named_cache(cache_name, cache)

    yield cache

    # Clean up
    await cache.clear()

    # Try to remove from named caches
    try:
        set_named_cache(cache_name, None)
    except:
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_basic(redis_cache):
    """Test basic Redis cache functionality."""
    # Define test key and value
    test_key = "test_basic_key"
    test_value = {"data": "test_value", "number": 42}

    # Check initial state (should be empty)
    value = await redis_cache.get(test_key)
    assert value is None

    # Set a value
    await redis_cache.set(test_key, test_value, ttl=10.0)

    # Get the value back
    retrieved_value = await redis_cache.get(test_key)
    assert retrieved_value == test_value

    # Delete the value
    await redis_cache.delete(test_key)

    # Verify it's gone
    value = await redis_cache.get(test_key)
    assert value is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_expiration(redis_cache):
    """Test Redis cache expiration."""
    # Set a value with short TTL
    await redis_cache.set("expiring_key", "short_lived_value", ttl=1.0)

    # Verify it exists
    value = await redis_cache.get("expiring_key")
    assert value == "short_lived_value"

    # Wait for expiration
    await asyncio.sleep(1.1)

    # Verify it's gone
    value = await redis_cache.get("expiring_key")
    assert value is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_bulk_operations(redis_cache):
    """Test bulk operations with Redis cache."""
    # Define multiple key-value pairs
    test_data = {
        "bulk_key1": "value1",
        "bulk_key2": "value2",
        "bulk_key3": "value3",
    }

    # Set multiple values
    for key, value in test_data.items():
        await redis_cache.set(key, value)

    # Get multiple values
    keys = list(test_data.keys())
    values = await redis_cache.mget(keys)

    # Verify all values were retrieved
    assert len(values) == len(keys)
    for i, key in enumerate(keys):
        assert values[i] == test_data[key]

    # Delete multiple values
    await redis_cache.delete(*keys)

    # Verify all are gone
    values = await redis_cache.mget(keys)
    assert all(v is None for v in values)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_pattern_operations(redis_cache):
    """Test pattern-based operations with Redis cache."""
    # Set values with pattern
    prefix = "pattern_test:"
    await redis_cache.set(f"{prefix}1", "value1")
    await redis_cache.set(f"{prefix}2", "value2")
    await redis_cache.set(f"{prefix}3", "value3")
    await redis_cache.set("different_key", "different_value")

    # Get keys by pattern
    pattern_keys = await redis_cache.keys(f"{prefix}*")
    assert len(pattern_keys) == 3
    assert all(k.startswith(prefix) for k in pattern_keys)

    # Delete by pattern
    await redis_cache.delete_pattern(f"{prefix}*")

    # Verify pattern keys are gone
    pattern_keys = await redis_cache.keys(f"{prefix}*")
    assert len(pattern_keys) == 0

    # Verify other key still exists
    value = await redis_cache.get("different_key")
    assert value == "different_value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_distributed_query_cache_basic(distributed_query_cache, setup_test_db):
    """Test basic distributed query cache functionality."""
    async with async_session() as session:
        # Define a query
        query = select(TestCacheItem).where(TestCacheItem.is_active == True)

        # Execute the query and create a cache key
        from uno.database.query_cache import QueryCacheKey

        cache_key = QueryCacheKey.from_select(query)

        # Execute query directly
        result = await session.execute(query)
        query_result = list(result.scalars().all())

        # Store in cache
        await distributed_query_cache.set(
            cache_key, query_result, dependencies=["test_cache_items"]
        )

        # Retrieve from cache
        cached_result = await distributed_query_cache.get(cache_key)
        assert cached_result.is_success
        assert len(cached_result.value) == len(query_result)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_distributed_cache_invalidation(distributed_query_cache, setup_test_db):
    """Test invalidation in distributed cache environment."""
    async with async_session() as session:
        # Set up multiple cached queries with dependencies
        queries = [
            (
                select(TestCacheItem).where(TestCacheItem.is_active == True),
                "active_items",
                ["test_cache_items"],
            ),
            (
                select(TestCacheItem).where(TestCacheItem.value > 100),
                "high_value_items",
                ["test_cache_items"],
            ),
            (
                select(TestCacheItem).where(TestCacheItem.name.like("Item%")),
                "named_items",
                ["test_cache_items"],
            ),
        ]

        # Execute and cache each query
        for query, key_suffix, dependencies in queries:
            result = await session.execute(query)
            query_result = list(result.scalars().all())

            cache_key = f"test_invalidation_{key_suffix}"
            await distributed_query_cache.set(
                cache_key, query_result, dependencies=dependencies
            )

            # Verify it's cached
            cached = await distributed_query_cache.get(cache_key)
            assert cached.is_success

        # Invalidate by table dependency
        await distributed_query_cache.invalidate_by_table("test_cache_items")

        # Verify all are invalidated
        for _, key_suffix, _ in queries:
            cache_key = f"test_invalidation_{key_suffix}"
            cached = await distributed_query_cache.get(cache_key)
            assert cached.is_error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cached_query_with_distributed_cache(
    distributed_query_cache, setup_test_db
):
    """Test the cached_query decorator with distributed cache."""

    # Define a function with cached_query decorator
    @cached_query(
        ttl=10.0,
        dependencies=["test_cache_items"],
        cache_instance=distributed_query_cache,
    )
    async def get_items_by_status(session: AsyncSession, is_active: bool):
        query = select(TestCacheItem).where(TestCacheItem.is_active == is_active)
        result = await session.execute(query)
        return list(result.scalars().all())

    # Execute the function
    async with async_session() as session:
        # First call - should miss cache
        start_time = time.time()
        items1 = await get_items_by_status(session, True)
        first_duration = time.time() - start_time

        # Second call - should hit cache
        start_time = time.time()
        items2 = await get_items_by_status(session, True)
        second_duration = time.time() - start_time

        # Check results
        assert len(items1) > 0
        assert items1 == items2

        # Check cache statistics
        stats = distributed_query_cache.get_stats()
        assert stats["performance"]["hits"] >= 1
        assert stats["performance"]["misses"] >= 1

        # Modify an item to test invalidation
        item = items1[0]
        item.is_active = not item.is_active
        session.add(item)
        await session.commit()

        # Invalidate cache
        await distributed_query_cache.invalidate_by_table("test_cache_items")

        # Third call - should miss cache due to invalidation
        items3 = await get_items_by_status(session, True)
        assert len(items3) != len(items1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_process_cache_synchronization(
    distributed_query_cache, setup_test_db
):
    """Test cache synchronization across multiple processes (simulated)."""
    # This test simulates multiple processes by using multiple cache instances
    # that connect to the same Redis instance

    # Create a second cache instance
    config2 = QueryCacheConfig(
        enabled=True,
        strategy=CacheStrategy.DEPENDENCY,
        backend=CacheBackend.REDIS,
        default_ttl=30.0,
        track_dependencies=True,
        redis_url="redis://localhost:6379/0",
        redis_prefix="test_query_cache:",  # Same prefix to share cache
    )
    second_cache = QueryCache(config=config2)

    try:
        # Set a value in the first cache
        test_key = "cross_process_test"
        test_value = {"process": "first", "timestamp": time.time()}

        await distributed_query_cache.set(test_key, test_value)

        # Verify it can be read from the second cache
        result = await second_cache.get(test_key)
        assert result.is_success
        assert result.value == test_value

        # Update from the second cache
        updated_value = {"process": "second", "timestamp": time.time()}
        await second_cache.set(test_key, updated_value)

        # Verify update is visible from the first cache
        result = await distributed_query_cache.get(test_key)
        assert result.is_success
        assert result.value == updated_value

        # Invalidate from the second cache
        await second_cache.invalidate(test_key)

        # Verify invalidation is visible from the first cache
        result = await distributed_query_cache.get(test_key)
        assert result.is_error

    finally:
        # Clean up
        await second_cache.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_named_cache_management():
    """Test management of named cache instances."""
    # Create a test cache configuration
    config = QueryCacheConfig(
        enabled=True,
        strategy=CacheStrategy.SIMPLE,
        backend=CacheBackend.MEMORY,
        default_ttl=10.0,
    )

    # Create a test cache
    test_cache = QueryCache(config=config)

    # Set as a named cache
    cache_name = "test_named_cache"
    set_named_cache(cache_name, test_cache)

    # Retrieve the named cache
    retrieved_cache = get_named_cache(cache_name)
    assert retrieved_cache is test_cache

    # Set and get a value
    test_key = "named_cache_test"
    test_value = {"named": True}

    await retrieved_cache.set(test_key, test_value)

    # Get from the original cache
    result = await test_cache.get(test_key)
    assert result.is_success
    assert result.value == test_value

    # Clear all caches
    await clear_all_caches()

    # Verify the cache is cleared
    result = await test_cache.get(test_key)
    assert result.is_error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_high_concurrency_cache_access(distributed_query_cache):
    """Test high concurrency access to distributed cache."""
    # Number of concurrent operations
    concurrency = 50

    # Set operation
    async def set_operation(i):
        key = f"concurrent_key_{i}"
        value = {"index": i, "value": f"concurrent_value_{i}"}
        await distributed_query_cache.set(key, value, ttl=10.0)
        return key

    # Get operation
    async def get_operation(key):
        result = await distributed_query_cache.get(key)
        return result.value if result.is_success else None

    # Run concurrent set operations
    set_tasks = [set_operation(i) for i in range(concurrency)]
    keys = await asyncio.gather(*set_tasks)

    # Run concurrent get operations
    get_tasks = [get_operation(key) for key in keys]
    results = await asyncio.gather(*get_tasks)

    # Verify all operations succeeded
    assert len(results) == concurrency
    assert all(result is not None for result in results)
    assert all(result["index"] == i for i, result in enumerate(results))

    # Run concurrent invalidation
    invalidate_tasks = [distributed_query_cache.invalidate(key) for key in keys]
    await asyncio.gather(*invalidate_tasks)

    # Verify all are invalidated
    verify_tasks = [get_operation(key) for key in keys]
    results = await asyncio.gather(*verify_tasks)
    assert all(result is None for result in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_with_serialization_edge_cases(distributed_query_cache):
    """Test cache with various data types requiring serialization."""
    test_cases = [
        ("simple_int", 42),
        ("simple_float", 3.14159),
        ("simple_string", "Hello, Cache!"),
        ("complex_dict", {"nested": {"data": ["array", "of", "values"], "number": 42}}),
        ("datetime_value", datetime.now(datetime.UTC)),
        ("mixed_list", [1, "two", 3.0, {"four": 4}, [5, 6]]),
        ("empty_values", {"null": None, "empty_list": [], "empty_dict": {}}),
        ("bool_values", {"true": True, "false": False}),
    ]

    # Set all values
    for key, value in test_cases:
        await distributed_query_cache.set(key, value)

    # Get all values
    for key, expected_value in test_cases:
        result = await distributed_query_cache.get(key)
        assert result.is_success

        # For datetime, just check type since exact equality might not preserve microseconds
        if isinstance(expected_value, datetime):
            assert isinstance(result.value, datetime)
        else:
            assert result.value == expected_value
