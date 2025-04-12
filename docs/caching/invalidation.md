# Cache Invalidation Strategies

The Uno Caching Framework provides several powerful strategies for invalidating cached data to ensure consistency between your cache and the source of truth.

## Overview

Cache invalidation is one of the "two hard things" in computer science, and the Uno Caching Framework addresses this challenge with several complementary strategies:

1. **Time-Based Invalidation**: Automatically expire cache entries after a specified time-to-live (TTL)
2. **Event-Based Invalidation**: Trigger cache invalidation in response to specific domain events
3. **Pattern-Based Invalidation**: Invalidate related cache entries when an entity changes

These strategies can be used individually or combined for comprehensive cache management.

## Time-Based Invalidation

Time-based invalidation is the simplest form of cache invalidation. Each cache entry has a time-to-live (TTL), after which it is automatically removed from the cache.

### Basic Configuration

```python
from uno.caching.invalidation import TimeBasedInvalidation

# Create time-based invalidation strategy
strategy = TimeBasedInvalidation(
    default_ttl=300,  # Default TTL in seconds
    ttl_jitter=0.1,   # Add 10% randomness to prevent cache stampede
)
```

### Setting TTL on Cache Entries

```python
# Set a value with a specific TTL
cache_manager.set("user:123", user_data, ttl=3600)  # 1 hour TTL

# Set a value with the default TTL
cache_manager.set("user:456", user_data)  # Uses default TTL
```

### Anti-Cache-Stampede Features

Cache stampede occurs when many processes simultaneously attempt to regenerate an expired cache entry. The framework prevents this with:

1. **TTL Jitter**: Adds randomness to TTL times to distribute expiration
2. **Background Refresh**: With the `@async_cached` decorator, entries can be refreshed asynchronously before expiration

```python
# Apply jitter to a TTL
ttl = strategy.apply_jitter(300)  # Will be between 270-330 seconds with 10% jitter

# Background refresh with cached decorator
@async_cached(ttl=300, refresh_before=30)  # Refresh 30 seconds before expiration
async def get_user(user_id: str):
    # Expensive operation to get user data
    return {"id": user_id, "name": "John Doe"}
```

## Event-Based Invalidation

Event-based invalidation removes or updates cache entries in response to specific domain events in your application.

### Basic Configuration

```python
from uno.caching.invalidation import EventBasedInvalidation

# Define event handlers mapping events to cache patterns
event_handlers = {
    "user.updated": ["user:{id}*", "profile:{id}*"],
    "user.deleted": ["user:{id}*", "profile:{id}*", "friends:{id}*"],
    "post.created": ["timeline:*", "feed:*"],
    "post.*": ["stats:posts"],  # Wildcard event pattern
}

# Create event-based invalidation strategy
strategy = EventBasedInvalidation(event_handlers)
```

### Triggering Invalidation

```python
# When a user is updated, trigger invalidation
user_id = "123"
patterns = strategy.handle_event("user.updated", {"id": user_id})

# Invalidate cache entries matching the patterns
for pattern in patterns:
    cache_manager.invalidate_pattern(pattern)
```

### Integration with Domain Events

For seamless integration with your domain events:

```python
from uno.caching import CacheManager
from uno.caching.invalidation import EventBasedInvalidation

# Event handler function
def handle_domain_event(event_type, payload):
    cache_manager = CacheManager.get_instance()
    invalidation = cache_manager.invalidation_strategy
    
    if isinstance(invalidation, EventBasedInvalidation):
        patterns = invalidation.handle_event(event_type, payload)
        for pattern in patterns:
            cache_manager.invalidate_pattern(pattern)

# Register with your event system
event_bus.subscribe(handle_domain_event)
```

### Dynamic Pattern Substitution

Event handlers support dynamic pattern substitution using event payload data:

```python
# Event handler with dynamic patterns
event_handlers = {
    "user.updated": ["user:{id}", "profile:{id}"],
}

# Event with payload
payload = {"id": "123", "name": "John Doe"}
patterns = strategy.handle_event("user.updated", payload)
# patterns = ["user:123", "profile:123"]
```

## Pattern-Based Invalidation

Pattern-based invalidation makes it easy to invalidate related cache entries when an entity changes, based on predefined patterns.

### Basic Configuration

```python
from uno.caching.invalidation import PatternBasedInvalidation

# Define patterns for entity types
patterns = {
    "user": ["user:{id}", "profile:{id}", "friends:{id}*"],
    "post": ["post:{id}", "user:{user_id}:posts", "timeline:*"],
}

# Create pattern-based invalidation strategy
strategy = PatternBasedInvalidation(patterns)
```

### Triggering Invalidation

```python
# When a user entity changes
user_id = "123"
patterns = strategy.invalidate_entity("user", user_id)

# Invalidate cache entries matching the patterns
for pattern in patterns:
    cache_manager.invalidate_pattern(pattern)
```

### Consistent Hashing Support

For distributed environments, consistent hashing ensures that the same entity is always mapped to the same cache shard:

```python
from uno.caching.invalidation import PatternBasedInvalidation

# Enable consistent hashing
strategy = PatternBasedInvalidation(
    patterns=patterns,
    consistent_hashing=True
)

# Get the shard key for an entity
shard_key = strategy.get_shard_key("user", "123")
```

## Combining Strategies

The Uno Caching Framework allows combining multiple invalidation strategies:

```python
from uno.caching.invalidation import (
    InvalidationStrategy,
    TimeBasedInvalidation,
    EventBasedInvalidation,
    PatternBasedInvalidation
)

# Create individual strategies
time_based = TimeBasedInvalidation(default_ttl=300)
event_based = EventBasedInvalidation(event_handlers)
pattern_based = PatternBasedInvalidation(patterns)

# Combine strategies
combined_strategy = InvalidationStrategy([
    time_based,
    event_based,
    pattern_based
])

# Use combined strategy
cache_manager = CacheManager(CacheConfig(
    invalidation=InvalidationConfig(
        time_based=True,
        event_based=True,
        pattern_based=True,
    )
))
```

## Pattern Matching

The framework supports several pattern matching formats:

1. **Exact matching**: `"user:123"` matches only the exact key
2. **Wildcard matching**: `"user:*"` matches any key starting with "user:"
3. **Multiple wildcards**: `"user:*:posts"` matches keys like "user:123:posts"
4. **Character classes**: `"user:[0-9]*"` matches keys where the ID is numeric

Pattern matching is used in the following operations:

```python
# Invalidate by pattern
cache_manager.invalidate_pattern("user:*")

# Check if a key matches a pattern
is_match = strategy.match_pattern("user:123", "user:*")
```

## Programmatic Invalidation

In addition to automatic invalidation strategies, you can manually invalidate cache entries:

```python
# Invalidate a specific key
cache_manager.delete("user:123")

# Invalidate by pattern
cache_manager.invalidate_pattern("user:*")

# Clear all cache
cache_manager.clear()
```

## Best Practices

1. **Layer your invalidation strategies**:
   - Time-based: as a safety net to ensure eventual consistency
   - Event-based: for real-time updates on specific events
   - Pattern-based: for related entity invalidation

2. **Choose appropriate TTLs**:
   - Shorter TTLs for frequently changing data
   - Longer TTLs for static or rarely changing data
   - Consider business requirements for data freshness

3. **Be specific with patterns**:
   - Use specific patterns to avoid over-invalidation
   - Group related data under consistent key prefixes
   - Document your cache key structure

4. **Consider invalidation costs**:
   - Pattern invalidation can be expensive in distributed caches
   - Use targeted invalidation instead of broad patterns when possible
   - Monitor invalidation operations for performance impact

5. **Handle race conditions**:
   - Be aware of potential race conditions between cache writes and invalidations
   - Consider using versioned cache entries for critical data
   - Use optimistic concurrency control for sensitive operations

6. **Test invalidation behavior**:
   - Verify that invalidation works correctly in all scenarios
   - Test cache consistency under load
   - Monitor cache hit rates after invalidation events