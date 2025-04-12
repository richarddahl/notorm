# Caching Framework

The Uno Caching Framework provides a comprehensive solution for managing application data caching. It includes support for multi-level caching, distributed caching, advanced invalidation strategies, and detailed monitoring tools.

## Key Features

The caching framework offers the following key features:

1. **Multi-Level Caching**
   - Local in-memory cache for ultra-fast access
   - Local file-based cache for persistence across restarts
   - Distributed cache (Redis or Memcached) for sharing across services

2. **Flexible Invalidation Strategies**
   - Time-based invalidation with TTL support
   - Event-based invalidation triggered by domain events
   - Pattern-based invalidation for entities and related objects
   - Anti-stampede features with jitter and consistent hashing

3. **Comprehensive Monitoring**
   - Performance metrics collection
   - Health monitoring with alerts
   - Cache efficiency analysis
   - Prometheus integration

4. **Ease of Use**
   - Simple decorator-based API for caching functions
   - Async/sync dual API support
   - Pluggable architecture

## Getting Started

To use the Uno Caching Framework, you'll first need to create a cache manager instance:

```python
from uno.caching import CacheManager, CacheConfig

# Create a cache configuration
config = CacheConfig(
    # Enable multi-level caching
    use_multi_level=True,
    
    # Configure local cache
    local=LocalCacheConfig(
        type="memory",
        max_size=10000,  # Maximum number of items
        ttl=3600,  # Default TTL in seconds
    ),
    
    # Configure distributed cache (optional)
    distributed=DistributedCacheConfig(
        enabled=True,
        type="redis",
        connection_string="redis://localhost:6379/0",
    )
)

# Create the cache manager
cache_manager = CacheManager(config)
```

For simpler use cases, you can use the predefined configurations:

```python
# Development configuration (memory cache only)
config = CacheConfig.development_defaults()

# Production configuration (multi-level with Redis)
config = CacheConfig.production_defaults()
```

## Basic Usage

Once you have a cache manager, you can use it to cache and retrieve values:

### Simple Caching

```python
# Get the cache manager (singleton instance)
cache_manager = CacheManager.get_instance()

# Cache a value
cache_manager.set("user:123", user_data, ttl=3600)  # TTL in seconds

# Get a cached value
user_data = cache_manager.get("user:123")
```

### Function Caching with Decorators

```python
from uno.caching.decorators import cached, async_cached

# Cache a synchronous function
@cached(ttl=3600)
def get_user(user_id: str) -> dict:
    # Expensive operation to get user data
    return {"id": user_id, "name": "John Doe"}

# Cache an asynchronous function
@async_cached(ttl=3600)
async def get_user_async(user_id: str) -> dict:
    # Expensive async operation to get user data
    return {"id": user_id, "name": "John Doe"}
```

### Cache Invalidation

```python
# Invalidate a specific key
cache_manager.delete("user:123")

# Invalidate multiple keys matching a pattern
cache_manager.invalidate_pattern("user:*")

# Clear all cache
cache_manager.clear()
```

## Multi-Level Caching

Multi-level caching allows you to combine the benefits of different cache types:

1. **Local cache** (first level): Provides ultra-fast access with no network overhead
2. **Distributed cache** (second level): Enables sharing cache data between multiple services

When multi-level caching is enabled:

- On read: The system first checks the local cache, then falls back to the distributed cache
- On write: The system writes to both local and distributed caches
- When a value is retrieved from the distributed cache, it's also stored in the local cache for future access

Example configuration:

```python
config = CacheConfig(
    use_multi_level=True,
    local=LocalCacheConfig(
        type="memory",
        max_size=10000,
        ttl=600,  # Local cache has shorter TTL (10 minutes)
    ),
    distributed=DistributedCacheConfig(
        enabled=True,
        type="redis",
        connection_string="redis://localhost:6379/0",
        ttl=3600,  # Distributed cache has longer TTL (1 hour)
    )
)
```

## Cache Invalidation Strategies

The caching framework supports several invalidation strategies that can be used individually or in combination:

### Time-Based Invalidation

Time-based invalidation uses a time-to-live (TTL) to automatically expire cache entries:

```python
from uno.caching.invalidation import TimeBasedInvalidation

# Create a time-based invalidation strategy
strategy = TimeBasedInvalidation(
    default_ttl=300,  # Default TTL in seconds
    ttl_jitter=0.1,   # Add randomness to prevent cache stampede
)

# Use the strategy
cache_manager.set("user:123", user_data, ttl=600)  # Override default TTL
```

### Event-Based Invalidation

Event-based invalidation triggers cache invalidation based on domain events:

```python
from uno.caching.invalidation import EventBasedInvalidation

# Define event handlers
event_handlers = {
    "user.updated": ["user:{id}*", "profile:{id}*"],
    "user.deleted": ["user:{id}*", "profile:{id}*", "friends:{id}*"],
}

# Create an event-based invalidation strategy
strategy = EventBasedInvalidation(event_handlers)

# When a user is updated, trigger invalidation
user_id = "123"
patterns = strategy.handle_event("user.updated", {"id": user_id})
for pattern in patterns:
    cache_manager.invalidate_pattern(pattern)
```

### Pattern-Based Invalidation

Pattern-based invalidation associates entity types with cache key patterns:

```python
from uno.caching.invalidation import PatternBasedInvalidation

# Define patterns for entity types
patterns = {
    "user": ["user:{id}*", "profile:{id}*"],
    "post": ["post:{id}*", "timeline:*"],
}

# Create a pattern-based invalidation strategy
strategy = PatternBasedInvalidation(patterns)

# When a user is updated, invalidate related cache entries
user_id = "123"
patterns = strategy.invalidate_entity("user", user_id)
for pattern in patterns:
    cache_manager.invalidate_pattern(pattern)
```

## Monitoring Tools

The caching framework includes comprehensive monitoring tools:

```python
from uno.caching.monitoring import CacheMonitor

# Get the cache monitor from the manager
monitor = cache_manager.monitor

# Get cache statistics
stats = monitor.get_stats()
print(f"Hit rate: {stats['hit_rate']['overall']:.2f}")
print(f"Memory usage: {stats['size']['local']} items")

# Analyze performance
analysis = monitor.analyze_performance(time_window=3600)  # Last hour
print(f"Hit rate (last hour): {analysis['hit_rates']['overall']:.2f}")
print(f"P95 latency: {analysis['latency_stats']['local']['p95']:.2f} ms")

# Check health
health = monitor.check_health()
if not health["overall"]:
    print("Cache health check failed!")
    for component, status in health.items():
        if not status:
            print(f"Unhealthy component: {component}")
```

## Async API

The caching framework provides a fully asynchronous API for use with async/await code:

```python
# Get a value asynchronously
user_data = await cache_manager.get_async("user:123")

# Set a value asynchronously
await cache_manager.set_async("user:123", user_data, ttl=3600)

# Delete a value asynchronously
await cache_manager.delete_async("user:123")

# Invalidate pattern asynchronously
await cache_manager.invalidate_pattern_async("user:*")

# Get stats asynchronously
stats = await cache_manager.monitor.get_stats_async()
```

## Advanced Features

### Cache Regions

Cache regions allow you to define different caching configurations for different types of data:

```python
config = CacheConfig(
    # Default configuration
    local=LocalCacheConfig(
        type="memory",
        max_size=10000,
        ttl=3600,
    ),
    
    # Region-specific configurations
    regions={
        "short_lived": {
            "local": LocalCacheConfig(
                type="memory",
                max_size=1000,
                ttl=60,  # Short TTL for frequently changing data
            ),
        },
        "persistent": {
            "local": LocalCacheConfig(
                type="file",
                directory="/tmp/cache",
                max_size=100,  # MB
                ttl=86400,  # 1 day
            ),
        },
    }
)

# Use a specific region
with cache_manager.cache_context("short_lived"):
    cache_manager.set("frequent:123", data)

# Async version
async with cache_manager.cache_context_async("persistent"):
    await cache_manager.set_async("persistent:123", data)
```

### Custom Serialization

You can customize how values are serialized for storage in the cache:

```python
from uno.caching.serialization import JsonSerializer, PickleSerializer, ProtobufSerializer

config = CacheConfig(
    local=LocalCacheConfig(
        type="memory",
        serializer="pickle",  # Default serializer
    ),
    distributed=DistributedCacheConfig(
        type="redis",
        serializer="json",  # Use JSON for distributed cache
    )
)
```

### Performance Optimization

The caching framework includes several features for performance optimization:

1. **Cache-aside pattern**: Automatically fetches data from the source if not found in the cache

```python
from uno.caching.decorators import cache_aside

def get_from_database(user_id):
    # Expensive database query
    return {"id": user_id, "name": "John Doe"}

@cache_aside(
    get_from_cache=lambda user_id: cache_manager.get(f"user:{user_id}"),
    save_to_cache=lambda user_id, data: cache_manager.set(f"user:{user_id}", data)
)
def get_user(user_id):
    return get_from_database(user_id)
```

2. **Batch operations**: Efficiently get or set multiple values at once

```python
# Get multiple values
users = cache_manager.multi_get(["user:123", "user:456", "user:789"])

# Set multiple values
cache_manager.multi_set({
    "user:123": user1_data,
    "user:456": user2_data,
    "user:789": user3_data,
}, ttl=3600)
```

3. **TTL jitter**: Prevent cache stampede by adding randomness to TTLs

```python
from uno.caching.invalidation import TimeBasedInvalidation

strategy = TimeBasedInvalidation(
    default_ttl=300,
    ttl_jitter=0.1,  # 10% randomness
)

# TTL will be between 270 and 330 seconds
ttl = strategy.apply_jitter(300)
```

## Prometheus Integration

The caching framework can export metrics to Prometheus for monitoring:

```python
config = CacheConfig(
    monitoring=MonitoringConfig(
        enabled=True,
        prometheus_export=True,
        export_port=9090,
    )
)
```

This will export the following metrics:

- `cache_hits_total`: Counter of cache hits
- `cache_misses_total`: Counter of cache misses
- `cache_errors_total`: Counter of cache errors
- `cache_hit_rate`: Gauge of cache hit rate
- `cache_size`: Gauge of cache size
- `cache_operation_latency_milliseconds`: Histogram of operation latencies

You can then use Grafana or another tool to visualize these metrics.

## Best Practices

Here are some best practices for using the Uno Caching Framework:

1. **Choose appropriate TTLs**: Use shorter TTLs for frequently changing data and longer TTLs for static data
2. **Use multi-level caching**: Combine local and distributed caches for optimal performance
3. **Implement proper invalidation**: Use event-based or pattern-based invalidation to keep cache data fresh
4. **Monitor cache performance**: Regularly check hit rates and memory usage
5. **Avoid caching large objects**: Break down large objects into smaller, more cacheable pieces
6. **Use cache regions**: Group similar data with similar caching requirements
7. **Consider serialization costs**: Choose serialization formats based on your performance needs
8. **Handle cache failures gracefully**: Use fallback strategies when cache operations fail
9. **Avoid cache stampede**: Use jitter and distributed locks for high-traffic cache entries
10. **Test cache behavior**: Verify cache invalidation works correctly