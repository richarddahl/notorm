# Query Cache

The Query Cache module provides a high-performance, feature-rich caching system for database queries in the Uno framework.

## Features

- **Automatic query result caching**: Cache results of frequently executed queries
- **Multiple cache storage backends**: In-memory, Redis, or hybrid backends
- **Smart caching strategies**: Time-based, adaptive, and dependency-based strategies
- **Query dependency tracking**: Automatically track and invalidate related queries
- **Comprehensive metrics**: Track cache performance and utilization
- **Support for both raw SQL and ORM queries**: Works with all query types

## Architecture

The Query Cache system consists of the following main components:

1. **QueryCache**: The core cache implementation
2. **QueryCacheKey**: Generates consistent cache keys for queries
3. **CachedResult**: Wrapper for cached query results with metadata
4. **Decorators**: `@cached` and `@cached_query` decorators for easy integration

## Usage Examples

### Basic Caching

Using the query cache directly:

```python
from uno.database.query_cache import QueryCache, QueryCacheKey

# Create or get a cache instance
cache = QueryCache()

# Generate a cache key for the query
query = "SELECT * FROM users WHERE status = 'active'"
cache_key = QueryCacheKey.from_text(query, {"status": "active"}, ["users"])

# Try to get from cache first
cached_result = await cache.get(cache_key)

if cached_result.is_ok():```

# Use cached result
users = cached_result.unwrap()
print(f"Found {len(users)} users in cache")
```
else:```

# Cache miss, fetch from database
async with db_connection() as conn:```

result = await conn.execute(query)
users = await result.fetchall()
``````

```
```

# Cache the result
await cache.set(
    cache_key,
    users,
    ttl=60.0,  # Cache for 1 minute
    dependencies=["users"],  # Track dependency on users table
)
```
```
```

### Caching Function Results

Using the `@cached` decorator to automatically cache function results:

```python
from uno.database.query_cache import cached

# Cache the function result for 5 minutes
@cached(ttl=300.0, dependencies=["users"])
async def get_active_users():```

async with db_connection() as conn:```

result = await conn.execute("SELECT * FROM users WHERE status = 'active'")
return await result.fetchall()
```
```

# First call fetches from database
users = await get_active_users()

# Subsequent calls use the cached result
users = await get_active_users()  # Uses cached result
```

### Caching SQLAlchemy Query Results

Using the `@cached_query` decorator with SQLAlchemy:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uno.database.query_cache import cached_query

@cached_query(ttl=60.0, dependencies=["users", "orders"])
async def get_user_with_orders(session: AsyncSession, user_id: int):```

# This query will be cached based on user_id parameter
query = select(User).options(joinedload(User.orders)).where(User.id == user_id)
result = await session.execute(query)
return result.scalars().first()
```

# Usage with session
async with async_session() as session:```

# First call executes the query
user = await get_user_with_orders(session, 123)
``````

```
```

# Second call uses cached result
user_again = await get_user_with_orders(session, 123)
```
```

### Using Named Caches

Using named caches for different parts of your application:

```python
from uno.database.query_cache import get_named_cache, QueryCacheConfig, CacheStrategy

# Get a named cache with specific configuration
user_cache = get_named_cache("user_cache")
user_cache_config = QueryCacheConfig(```

strategy=CacheStrategy.DEPENDENCY,
default_ttl=300.0,  # 5 minutes default TTL
```
)

# Use the cache
async def get_user(user_id: int):```

cache_key = f"user:{user_id}"
``````

```
```

# Try cache first
cached_result = await user_cache.get(cache_key)
if cached_result.is_ok():```

return cached_result.unwrap()
```
``````

```
```

# Cache miss, fetch from database
user = await fetch_user_from_db(user_id)
``````

```
```

# Cache the result
await user_cache.set(```

cache_key,
user,
dependencies=["users"],
```
)
``````

```
```

return user
```
```

### Invalidating Cache Entries

Invalidating cache entries when data changes:

```python
from uno.database.query_cache import get_named_cache

# Get the cache
cache = get_named_cache("user_cache")

# Invalidate a specific key
await cache.invalidate("user:123")

# Invalidate all entries dependent on a table
await cache.invalidate_by_table("users")

# Invalidate by key pattern
await cache.invalidate_by_pattern("user:")

# Clear the entire cache
await cache.clear()
```

## Configuration

The Query Cache system offers extensive configuration options:

```python
from uno.database.query_cache import QueryCacheConfig, CacheBackend, CacheStrategy

# Create a configuration
config = QueryCacheConfig(```

# Cache behavior
enabled=True,
strategy=CacheStrategy.SMART,
backend=CacheBackend.HYBRID,
``````

```
```

# Cache sizing and expiration
default_ttl=300.0,  # 5 minutes
max_entries=10000,
``````

```
```

# Advanced settings
track_dependencies=True,
auto_invalidate=True,
log_hits=True,
log_misses=True,
``````

```
```

# Smart caching settings
adaptive_ttl=True,
min_ttl=10.0,
max_ttl=3600.0,  # 1 hour
``````

```
```

# Redis settings (when using REDIS or HYBRID backend)
redis_url="redis://localhost:6379/0",
redis_prefix="my_app_cache:",
```
)

# Create a cache with this configuration
from uno.database.query_cache import QueryCache
cache = QueryCache(config=config)
```

## Performance Metrics

The Query Cache provides comprehensive metrics for monitoring and optimization:

```python
from uno.database.query_cache import get_named_cache

# Get the cache
cache = get_named_cache("user_cache")

# Get cache statistics
stats = cache.get_stats()

# Print performance metrics
print(f"Cache performance:")
print(f"  Hits: {stats['performance']['hits']}")
print(f"  Misses: {stats['performance']['misses']}")
print(f"  Hit rate: {stats['performance']['hit_rate'] * 100:.2f}%")
print(f"  Average hit time: {stats['performance']['avg_hit_time'] * 1000:.2f} ms")

# Print size metrics
print(f"Cache size:")
print(f"  Current entries: {stats['size']['current_entries']}")
print(f"  Total entries: {stats['size']['total_entries']}")

# Print invalidation metrics
print(f"Cache invalidation:")
print(f"  Invalidations: {stats['invalidation']['invalidations']}")
print(f"  Evictions: {stats['invalidation']['evictions']}")
print(f"  Dependencies tracked: {stats['invalidation']['dependencies_tracked']}")
```

## Cache Backends

The Query Cache supports multiple storage backends:

- **MEMORY**: Local in-memory cache (fastest, not shared between processes)
- **REDIS**: Distributed cache using Redis (shared between processes)
- **HYBRID**: Two-level cache using both memory and Redis

Each backend has different performance characteristics and use cases:

```python
from uno.database.query_cache import QueryCacheConfig, CacheBackend

# In-memory cache (fastest, not distributed)
memory_config = QueryCacheConfig(backend=CacheBackend.MEMORY)

# Redis cache (distributed, shared between processes)
redis_config = QueryCacheConfig(```

backend=CacheBackend.REDIS,
redis_url="redis://localhost:6379/0",
redis_prefix="app_cache:",
```
)

# Hybrid cache (best of both worlds)
hybrid_config = QueryCacheConfig(```

backend=CacheBackend.HYBRID,
redis_url="redis://localhost:6379/0",
redis_prefix="app_cache:",
```
)
```

## Caching Strategies

The Query Cache offers multiple caching strategies:

- **SIMPLE**: Basic time-based caching
- **SMART**: Adaptive caching based on query frequency and complexity
- **DEPENDENCY**: Track dependencies between queries for advanced invalidation

Each strategy optimizes for different access patterns:

```python
from uno.database.query_cache import QueryCacheConfig, CacheStrategy

# Simple time-based caching
simple_config = QueryCacheConfig(```

strategy=CacheStrategy.SIMPLE,
default_ttl=300.0,  # 5 minutes
```
)

# Smart adaptive caching
smart_config = QueryCacheConfig(```

strategy=CacheStrategy.SMART,
adaptive_ttl=True,
min_ttl=10.0,
max_ttl=3600.0,  # 1 hour
analyze_complexity=True,
```
)

# Dependency-based caching
dependency_config = QueryCacheConfig(```

strategy=CacheStrategy.DEPENDENCY,
track_dependencies=True,
auto_invalidate=True,
```
)
```

## Best Practices

1. **Identify cacheable queries**: Best candidates are queries that are frequently executed but rarely modified
2. **Set appropriate TTLs**: Longer for relatively static data, shorter for frequently changing data
3. **Track dependencies**: Always specify table dependencies for proper invalidation
4. **Use named caches**: Separate caches for different parts of your application
5. **Monitor cache performance**: Regularly check the hit rate and adjust TTLs accordingly
6. **Invalidate appropriately**: Call `invalidate_by_table()` when data changes
7. **Use decorators**: The `@cached_query` decorator makes integration seamless
8. **Test with real infrastructure**: Use integration tests to verify cache behavior in real environments

## Testing the Query Cache

The framework includes comprehensive integration tests for the query cache system, ensuring it works correctly with both memory and Redis backends:

### Running Tests

```bash
# Run query cache integration tests with the distributed cache tests
pytest tests/integration/test_distributed_cache.py --run-integration

# Run all integration tests including cache tests
hatch run test:integration
```

### Test Coverage

The integration tests for query caching cover:

1. **Basic Cache Operations**: Verify cache get/set/delete operations
2. **Cache Expiration**: Test TTL and automatic expiration
3. **Dependency Tracking**: Verify dependency-based invalidation
4. **Cross-Process Synchronization**: Test that multiple processes share cache state correctly
5. **High-Concurrency Access**: Test behavior under concurrent load
6. **Integration with Query Optimizer**: Verify that the cache works correctly with query optimization

### Example Test

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_cache_dependencies(query_cache):```

"""Test cache dependency tracking."""
# Set values with dependencies
await query_cache.set(```

"query1", 
"result1", 
dependencies=["products", "customers"]
```
)
await query_cache.set(```

"query2", 
"result2", 
dependencies=["products"]
```
)
await query_cache.set(```

"query3", 
"result3", 
dependencies=["orders"]
```
)
``````

```
```

# Verify values are cached
assert (await query_cache.get("query1")).is_success
assert (await query_cache.get("query2")).is_success
assert (await query_cache.get("query3")).is_success
``````

```
```

# Invalidate by table dependency
await query_cache.invalidate_by_table("products")
``````

```
```

# Check invalidation
assert (await query_cache.get("query1")).is_error
assert (await query_cache.get("query2")).is_error
assert (await query_cache.get("query3")).is_success
```
```

## Advanced Features

### Custom Key Builders

Create custom cache key builders for complex scenarios:

```python
from uno.database.query_cache import cached

def my_key_builder(user_id, filter_params):```

"""Build a custom cache key."""
return f"users:{user_id}:{hash(frozenset(filter_params.items()))}"
```

@cached(key_builder=my_key_builder)
async def get_filtered_user_data(user_id, filter_params):```

# Function implementation
pass
```
```

### Query Dependency Analysis

Automatic dependency tracking for SQL queries:

```python
from uno.database.query_cache import cached_query

# Dependencies will be automatically extracted from the query
@cached_query(ttl=60.0)
async def get_user_orders(session, user_id):```

result = await session.execute(```

"""
SELECT o.* FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.id = :user_id
""",
{"user_id": user_id}
```
)
return await result.fetchall()
```
```

### Redis Connection Customization

Fine-tune Redis connection settings:

```python
from uno.database.query_cache import QueryCacheConfig, CacheBackend

# Customize Redis connection
redis_config = QueryCacheConfig(```

backend=CacheBackend.REDIS,
redis_url="redis://:password@redis.example.com:6379/1",
redis_prefix="app:cache:",
```
)
```

## FAQ

### How does the cache handle query parameters?

The query parameters are included in the cache key generation, so different parameter values will result in different cache entries. This ensures that queries with different parameters don't interfere with each other.

### How does dependency tracking work?

When you cache a query result, you can specify the database tables it depends on. When data in those tables changes, you can invalidate all cache entries that depend on those tables with a single call to `invalidate_by_table()`.

### How does the cache handle complex ORM queries?

The QueryCacheKey system can generate consistent keys for both raw SQL and ORM queries. For SQLAlchemy queries, it extracts the compiled SQL and parameters to create a stable hash.

### How do I ensure cache consistency when data changes?

Always call `invalidate_by_table()` when data changes. For example, after an insert, update, or delete operation, invalidate the associated tables to ensure cache consistency.

### Can I use multiple caches for different types of queries?

Yes, you can use named caches with different configurations using the `get_named_cache()` function. This allows you to have separate caches for different parts of your application.

### How do I monitor cache performance?

Use the `get_stats()` method to get comprehensive metrics about the cache, including hit rate, average access times, and invalidation statistics.

### How does the hybrid backend work?

The hybrid backend stores data in both memory and Redis. Reads check the local memory cache first (for speed) and then Redis if not found. Writes go to both stores. This gives you the speed of local caching with the distribution benefits of Redis.