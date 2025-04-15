# Multi-Level Caching

The uno Caching Framework's multi-level caching system combines the benefits of different cache types to provide optimal performance, reliability, and scalability.

## Overview

Multi-level caching creates a hierarchy of cache layers, each with different performance characteristics, durability, and scope:

1. **Local Memory Cache** (L1): Ultra-fast in-process cache with the lowest latency but limited to a single process
2. **Local File Cache** (optional L1 alternative): Persistent local cache that survives process restarts
3. **Distributed Cache** (L2): Shared cache across multiple processes/services for consistency and scalability

## How Multi-Level Caching Works

### Read Operations

When retrieving a value with multi-level caching enabled:

1. First, the system checks the local cache (memory or file)
   - If found, the value is returned immediately
   - If not found, or if an error occurs and `fallback_on_error` is enabled, continue to step 2
   
2. Next, the system checks the distributed cache
   - If found, the value is returned and also stored in the local cache for future access
   - If not found, the operation returns null or a default value

### Write Operations

When storing a value with multi-level caching enabled:

1. The value is stored in the local cache with its specified TTL
   - The local cache may have a maximum TTL limit that overrides larger values

2. The value is also stored in the distributed cache
   - The distributed cache may have a different TTL than the local cache

### Delete Operations

When deleting a value with multi-level caching enabled:

1. The value is deleted from the local cache
2. The value is also deleted from the distributed cache

## Configuration

Multi-level caching is configured through the `CacheConfig`:

```python
from uno.caching import CacheConfig, LocalCacheConfig, DistributedCacheConfig

config = CacheConfig(
    # Enable multi-level caching
    use_multi_level=True,
    
    # Enable fallback on errors
    fallback_on_error=True,
    
    # Configure local cache
    local=LocalCacheConfig(
        type="memory",  # or "file" for persistent storage
        max_size=10000,  # Maximum items for memory, MB for file
        ttl=600,        # Default TTL in seconds (10 minutes)
    ),
    
    # Configure distributed cache
    distributed=DistributedCacheConfig(
        enabled=True,
        type="redis",   # or "memcached"
        hosts=["redis:6379"],
        ttl=3600,       # Default TTL in seconds (1 hour)
    )
)
```

### TTL Handling

- Each cache layer can have a different default TTL
- When setting a value with an explicit TTL:
  - Local cache: `min(specified_ttl, local.ttl)` is used
  - Distributed cache: `min(specified_ttl, distributed.ttl)` is used

## Benefits

### Performance Optimization

Multi-level caching provides significant performance benefits:

1. **Reduced latency**: Most requests are served from the ultra-fast local cache
2. **Reduced network traffic**: Fewer calls to the distributed cache
3. **Improved hit rates**: Items missing from one cache may be found in another

### Reliability

Multi-level caching enhances system reliability:

1. **Fault tolerance**: The system can continue to function even if the distributed cache is temporarily unavailable
2. **Graceful degradation**: If the distributed cache fails, the local cache still provides some caching benefit

### Scalability

Multi-level caching improves scalability:

1. **Reduced load on distributed cache**: Local caches absorb most read operations
2. **Efficient resource usage**: Frequently accessed items stay in fast local memory

## Usage Examples

### Basic Operations

```python
# Get the cache manager
cache_manager = CacheManager.get_instance()

# Set a value (will be stored in both local and distributed caches)
cache_manager.set("user:123", user_data, ttl=3600)

# Get a value (checks local cache first, then distributed)
user_data = cache_manager.get("user:123")

# Delete a value (from both local and distributed caches)
cache_manager.delete("user:123")
```

### Async Operations

```python
# Set a value asynchronously
await cache_manager.set_async("user:123", user_data, ttl=3600)

# Get a value asynchronously
user_data = await cache_manager.get_async("user:123")

# Delete a value asynchronously
await cache_manager.delete_async("user:123")
```

### Batch Operations

```python
# Get multiple values at once
results = cache_manager.multi_get(["user:123", "user:456", "user:789"])

# Set multiple values at once
cache_manager.multi_set({
    "user:123": user1_data,
    "user:456": user2_data,
    "user:789": user3_data,
}, ttl=3600)
```

## Cache Consistency

Multi-level caching introduces potential cache consistency challenges. The uno Caching Framework mitigates these with:

1. **TTL-based consistency**: Data naturally expires after its TTL, limiting the window for inconsistency
2. **Write-through caching**: All writes update both cache levels
3. **Delete propagation**: Deletes are propagated to all cache levels
4. **Event-based invalidation**: Domain events can trigger targeted cache invalidation

For applications with strict consistency requirements, you can:

1. Use shorter TTLs for sensitive data
2. Implement explicit invalidation on data changes
3. Use event-based invalidation to propagate changes

## Monitoring Multi-Level Caches

The cache monitoring system provides detailed insights into multi-level cache performance:

```python
# Get cache statistics
stats = cache_manager.monitor.get_stats()

# Check hit rates for different cache levels
print(f"Local cache hit rate: {stats['hit_rate']['local']:.2f}")
print(f"Distributed cache hit rate: {stats['hit_rate']['distributed']:.2f}")
print(f"Overall hit rate: {stats['hit_rate']['overall']:.2f}")

# Check sizes
print(f"Local cache size: {stats['size']['local']} items")
print(f"Distributed cache size: {stats['size']['distributed']} items")
```

## Best Practices

1. **Balance local and distributed cache sizes**:
   - Local cache: large enough to hold frequently accessed items but small enough to avoid memory pressure
   - Distributed cache: large enough to hold all items that benefit from caching

2. **Consider TTL hierarchy**:
   - Local cache: shorter TTLs (minutes to hours)
   - Distributed cache: longer TTLs (hours to days)

3. **Monitor cache efficiency**:
   - Track hit rates for both cache levels
   - Adjust cache sizes and TTLs based on hit rates and memory usage

4. **Handle distributed cache failures gracefully**:
   - Enable `fallback_on_error`
   - Monitor distributed cache health
   - Add circuit breakers for persistent failures

5. **Optimize local cache for your workload**:
   - Memory cache: for high-throughput, low-latency applications
   - File cache: for applications that need persistence across restarts

6. **Ensure proper invalidation**:
   - Implement consistent invalidation policies across all cache levels
   - Use event-based invalidation for real-time updates
