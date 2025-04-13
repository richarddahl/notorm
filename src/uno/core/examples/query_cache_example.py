"""
Example usage of the query cache system.

This example demonstrates how to use the query cache for
improving database performance and reducing load.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.query_cache import (
    CacheBackend,
    CacheStrategy,
    QueryCacheConfig,
    QueryCache,
    QueryCacheKey,
    cached,
    cached_query,
    get_named_cache,
)
from uno.database.enhanced_pool_session import enhanced_pool_session


# Create a users table in SQLAlchemy models
class User:
    id: int
    name: str
    email: str


async def basic_caching_example():
    """Basic example of using the query cache."""
    print("Basic caching example:")
    
    # Create a cache with memory backend
    cache = QueryCache(
        config=QueryCacheConfig(
            backend=CacheBackend.MEMORY,
            default_ttl=60.0,  # 1 minute
            log_hits=True,
            log_misses=True,
        )
    )
    
    # Use the cache directly
    user_list_key = "users:all"
    
    # Try to get from cache first
    cached_result = await cache.get(user_list_key)
    
    if cached_result.is_success:
        # Use cached result
        users = cached_result.value
        print(f"Cache hit! Found {len(users)} users in cache")
    else:
        # Cache miss, fetch from database
        print("Cache miss! Fetching from database...")
        
        # Simulate database query with 500ms latency
        await asyncio.sleep(0.5)
        users = [
            {"id": 1, "name": "John", "email": "john@example.com"},
            {"id": 2, "name": "Jane", "email": "jane@example.com"},
        ]
        
        # Cache the result
        await cache.set(
            user_list_key,
            users,
            ttl=60.0,
            dependencies=["users"],
        )
        
        print(f"Fetched {len(users)} users from database and cached")
    
    # Try getting it again (should be cached now)
    cached_result = await cache.get(user_list_key)
    if cached_result.is_success:
        users = cached_result.value
        print(f"Second try: Cache hit! Found {len(users)} users in cache")
    
    # Show cache stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats['performance']['hits']} hits, {stats['performance']['misses']} misses")
    
    # Test invalidation
    print("\nInvalidating cache...")
    await cache.invalidate_by_table("users")
    
    # Try getting again (should miss now)
    cached_result = await cache.get(user_list_key)
    if cached_result.is_failure:
        print("Cache miss after invalidation")


async def cached_functions_example():
    """Example of using cache decorators."""
    print("\nCached functions example:")
    
    # Create a cache
    cache = QueryCache(
        config=QueryCacheConfig(
            backend=CacheBackend.MEMORY,
            default_ttl=60.0,
        )
    )
    
    # Define a function with the cached decorator
    @cached(ttl=30.0, dependencies=["users"], cache_instance=cache)
    async def get_user_count(filter_active: bool = False) -> int:
        print("  Executing get_user_count...")
        
        # Simulate database query
        await asyncio.sleep(0.3)
        
        if filter_active:
            return 8  # 8 active users
        else:
            return 10  # 10 total users
    
    # Call the function multiple times
    print("First call with filter_active=False:")
    count1 = await get_user_count(filter_active=False)
    print(f"  User count: {count1}")
    
    print("Second call with same parameters (should be cached):")
    count2 = await get_user_count(filter_active=False)
    print(f"  User count: {count2}")
    
    print("Call with different parameters:")
    count3 = await get_user_count(filter_active=True)
    print(f"  User count: {count3}")
    
    # Show cache stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats['performance']['hits']} hits, {stats['performance']['misses']} misses")


async def cached_queries_example():
    """Example of using cached_query decorator with SQLAlchemy."""
    print("\nCached queries example:")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Execute a simple query to set up database
        await session.execute(text("SELECT 1"))
        
        # Create a cache
        cache = get_named_cache("sqlalchemy_cache")
        
        # Define a query function with the cached_query decorator
        @cached_query(ttl=60.0, dependencies=["users"], cache_instance=cache)
        async def get_users_by_role(session: AsyncSession, role: str) -> List[Dict[str, Any]]:
            print(f"  Executing database query for role '{role}'...")
            
            # Simulate a complex query
            await asyncio.sleep(0.5)
            
            if role == "admin":
                return [
                    {"id": 1, "name": "Admin User", "email": "admin@example.com"},
                ]
            elif role == "user":
                return [
                    {"id": 2, "name": "Regular User 1", "email": "user1@example.com"},
                    {"id": 3, "name": "Regular User 2", "email": "user2@example.com"},
                ]
            else:
                return []
        
        # Call the query function
        print("First query for role 'admin':")
        admin_users = await get_users_by_role(session, "admin")
        print(f"  Found {len(admin_users)} admin users")
        
        print("Second query for role 'admin' (should be cached):")
        admin_users2 = await get_users_by_role(session, "admin")
        print(f"  Found {len(admin_users2)} admin users")
        
        print("Query for role 'user':")
        regular_users = await get_users_by_role(session, "user")
        print(f"  Found {len(regular_users)} regular users")
        
        # Show cache stats
        stats = cache.get_stats()
        print(f"Cache stats: {stats['performance']['hits']} hits, {stats['performance']['misses']} misses")
        
        # Invalidate by table
        print("\nInvalidating cache for 'users' table...")
        await cache.invalidate_by_table("users")
        
        # Query again (should miss cache)
        print("Query after invalidation:")
        admin_users3 = await get_users_by_role(session, "admin")
        print(f"  Found {len(admin_users3)} admin users")
        
        # Show updated stats
        stats = cache.get_stats()
        print(f"Updated cache stats: {stats['performance']['hits']} hits, {stats['performance']['misses']} misses")


async def performance_benchmark():
    """Benchmark comparing cached vs. uncached queries."""
    print("\nPerformance benchmark:")
    
    # Create a cache
    cache = QueryCache(
        config=QueryCacheConfig(
            backend=CacheBackend.MEMORY,
            default_ttl=60.0,
        )
    )
    
    # Define an uncached query function
    async def uncached_query():
        # Simulate database query with 100ms latency
        await asyncio.sleep(0.1)
        return {"data": "result"}
    
    # Define a cached query function
    @cached(cache_instance=cache)
    async def cached_query():
        # Same query
        await asyncio.sleep(0.1)
        return {"data": "result"}
    
    # Benchmark parameters
    iterations = 100
    
    # Benchmark uncached
    start_time = time.time()
    for _ in range(iterations):
        await uncached_query()
    uncached_time = time.time() - start_time
    
    print(f"Uncached: {iterations} queries in {uncached_time:.2f} seconds")
    print(f"Uncached average time per query: {(uncached_time/iterations)*1000:.2f} ms")
    
    # Benchmark cached (first iteration will be a miss, rest should be hits)
    start_time = time.time()
    for _ in range(iterations):
        await cached_query()
    cached_time = time.time() - start_time
    
    print(f"Cached: {iterations} queries in {cached_time:.2f} seconds")
    print(f"Cached average time per query: {(cached_time/iterations)*1000:.2f} ms")
    
    # Calculate improvement
    improvement = (uncached_time - cached_time) / uncached_time * 100
    print(f"Performance improvement: {improvement:.2f}%")
    
    # Show cache stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats['performance']['hits']} hits, {stats['performance']['misses']} misses")
    print(f"Hit rate: {stats['performance']['hit_rate']*100:.2f}%")


async def advanced_features_example():
    """Example of advanced query cache features."""
    print("\nAdvanced features example:")
    
    # Create a cache with smart strategy
    smart_cache = QueryCache(
        config=QueryCacheConfig(
            backend=CacheBackend.MEMORY,
            strategy=CacheStrategy.SMART,
            adaptive_ttl=True,
            min_ttl=10.0,
            max_ttl=300.0,
            analyze_complexity=True,
        )
    )
    
    # Create complex query key with query complexity info
    complex_query = """
    SELECT u.id, u.name, u.email, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.active = true
    GROUP BY u.id, u.name, u.email
    ORDER BY order_count DESC
    LIMIT 10
    """
    
    tables = ["users", "orders"]
    complex_key = QueryCacheKey.from_text(complex_query, None, tables)
    
    # Cache the result
    start_time = time.time()
    await asyncio.sleep(0.5)  # Simulate the complex query
    result = {"users": [{"id": 1, "name": "John", "orders": 5}]}
    query_time = time.time() - start_time
    
    await smart_cache.set(
        complex_key,
        result,
        dependencies=tables,
        query_time=query_time,
    )
    
    print("Cached a complex query result")
    print(f"Query execution time: {query_time:.2f} seconds")
    
    # Get the result
    cached = await smart_cache.get(complex_key)
    if cached.is_success:
        print("Successfully retrieved complex query from cache")
    
    # Demonstrate dependency tracking
    print("\nDependency tracking example:")
    
    # Cache multiple results with different dependencies
    await smart_cache.clear()
    
    # Cache user list with dependency on users table
    await smart_cache.set(
        "user:list",
        [{"id": 1, "name": "John"}],
        dependencies=["users"],
    )
    
    # Cache user count with dependency on users table
    await smart_cache.set(
        "user:count",
        1,
        dependencies=["users"],
    )
    
    # Cache order count with dependency on orders table
    await smart_cache.set(
        "order:count",
        10,
        dependencies=["orders"],
    )
    
    print("Cached 3 different values with dependencies:")
    print("  - user:list (depends on 'users')")
    print("  - user:count (depends on 'users')")
    print("  - order:count (depends on 'orders')")
    
    # Invalidate users table
    print("\nInvalidating 'users' table...")
    await smart_cache.invalidate_by_table("users")
    
    # Check which entries are still in cache
    user_list = await smart_cache.get("user:list")
    user_count = await smart_cache.get("user:count")
    order_count = await smart_cache.get("order:count")
    
    print(f"user:list in cache: {user_list.is_success}")
    print(f"user:count in cache: {user_count.is_success}")
    print(f"order:count in cache: {order_count.is_success}")
    
    # Show cache stats
    stats = smart_cache.get_stats()
    print(f"\nCache invalidation stats:")
    print(f"  Invalidations: {stats['invalidation']['invalidations']}")
    print(f"  Cascading invalidations: {stats['invalidation']['cascading_invalidations']}")
    print(f"  Dependencies tracked: {stats['invalidation']['dependencies_tracked']}")


async def main():
    """Run all examples."""
    await basic_caching_example()
    await cached_functions_example()
    await cached_queries_example()
    await performance_benchmark()
    await advanced_features_example()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())