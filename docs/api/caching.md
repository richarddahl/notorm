# Caching API

The Uno Caching module provides a comprehensive framework for implementing multi-level caching in your application. It supports both local and distributed caching with various strategies for cache invalidation and monitoring.

## Key Features

- **Multi-level caching**: Combine in-memory caching with distributed caching for optimal performance
- **Flexible invalidation strategies**: Time-based, event-based, and pattern-based cache invalidation
- **Monitoring and statistics**: Track cache hits, misses, and errors
- **Configurable regions**: Define different caching policies for different parts of your application
- **Domain-driven design**: Rich domain model with clear separation of concerns

## Core Concepts

### Cache Providers

Cache providers are the underlying storage mechanisms for cached items. The caching module supports the following provider types:

- **Memory**: In-memory caching for fast local access
- **File**: File-based caching for persistent local storage
- **Redis**: Distributed caching using Redis
- **Memcached**: Distributed caching using Memcached

### Cache Regions

Cache regions allow you to define different caching policies for different parts of your application. Each region can have its own TTL (time-to-live), invalidation strategy, and provider.

### Invalidation Rules

Invalidation rules define when and how cached items should be invalidated. The module supports three types of invalidation strategies:

- **Time-based**: Invalidate items after a specified TTL
- **Event-based**: Invalidate items when specific events occur
- **Pattern-based**: Invalidate items based on key patterns

## API Usage

### Basic Caching Operations

```python
from uno.caching import get_cache_item, set_cache_item, delete_cache_item

# Get an item from the cache
result = await get_cache_item("user:123")
if result.is_success() and result.value:
    user = result.value.value
else:
    # Cache miss - fetch from database
    user = await db.get_user(123)
    # Store in cache with a TTL of 300 seconds
    await set_cache_item("user:123", user, ttl_seconds=300)

# Delete an item from the cache
await delete_cache_item("user:123")
```

### Working with Cache Regions

```python
from uno.caching import (
    get_cache_region_service, 
    get_cache_provider_service,
    CacheProviderId,
    set_cache_item,
    get_cache_item
)

# Create a cache provider
provider_service = await get_cache_provider_service()
provider_result = await provider_service.register_provider(
    name="redis-provider",
    provider_type="redis",
    connection_details={"host": "localhost", "port": 6379}
)

# Create a cache region
region_service = await get_cache_region_service()
region_result = await region_service.create_region(
    name="user-profiles",
    provider_id=provider_result.value.id,
    ttl=600,  # 10 minutes
    max_size=10000
)

# Use the region for caching
await set_cache_item("user:123", user_data, region_name="user-profiles")
result = await get_cache_item("user:123", region_name="user-profiles")
```

### Invalidation Rules

```python
from uno.caching import get_invalidation_rule_service

rule_service = await get_invalidation_rule_service()

# Create a pattern-based invalidation rule
await rule_service.create_rule(
    name="user-data-rule",
    strategy_type="pattern_based",
    pattern="user:*"
)

# Create an event-based invalidation rule
await rule_service.create_rule(
    name="user-update-rule",
    strategy_type="event_based",
    events=["user_updated", "user_profile_changed"]
)

# Find rules that match a key
result = await rule_service.find_matching_rules("user:123")
matching_rules = result.value if result.is_success() else []
```

### Cache Configuration

```python
from uno.caching import get_cache_configuration_service

config_service = await get_cache_configuration_service()

# Enable multi-level caching
await config_service.enable_multi_level()

# Configure a region
await config_service.add_region_config("api-responses", {
    "ttl": 120,  # 2 minutes
    "max_size": 5000,
    "invalidation_strategy": "time_based"
})

# Get the current configuration
config_result = await config_service.get_active_configuration()
if config_result.is_success():
    config = config_result.value
    print(f"Caching enabled: {config.enabled}")
    print(f"Multi-level caching: {config.use_multi_level}")
```

## HTTP API

The caching module provides a RESTful API for managing the cache. The API is available at `/api/cache`.

### Providers

- `GET /api/cache/providers`: List all cache providers
- `GET /api/cache/providers/{id}`: Get a cache provider by ID
- `POST /api/cache/providers`: Create a new cache provider
- `PUT /api/cache/providers/{id}`: Update a cache provider
- `DELETE /api/cache/providers/{id}`: Delete a cache provider

### Regions

- `GET /api/cache/regions`: List all cache regions
- `GET /api/cache/regions/{id}`: Get a cache region by ID
- `POST /api/cache/regions`: Create a new cache region
- `PUT /api/cache/regions/{id}`: Update a cache region
- `DELETE /api/cache/regions/{id}`: Delete a cache region

### Invalidation Rules

- `GET /api/cache/rules`: List all invalidation rules
- `GET /api/cache/rules/{id}`: Get an invalidation rule by ID
- `POST /api/cache/rules`: Create a new invalidation rule
- `PUT /api/cache/rules/{id}`: Update an invalidation rule
- `DELETE /api/cache/rules/{id}`: Delete an invalidation rule

### Items

- `GET /api/cache/items/{key}`: Get a cached item by key
- `PUT /api/cache/items/{key}`: Set a cached item
- `DELETE /api/cache/items/{key}`: Delete a cached item
- `DELETE /api/cache/items`: Clear all cached items or items in a specific region
- `DELETE /api/cache/items/pattern/{pattern}`: Invalidate items matching a pattern

### Configuration

- `GET /api/cache/configuration`: Get the active cache configuration
- `PUT /api/cache/configuration`: Update the cache configuration
- `POST /api/cache/configuration/enable`: Enable caching
- `POST /api/cache/configuration/disable`: Disable caching

## Decorators

The caching module provides decorators for easy integration with your application code.

```python
from uno.caching import cached, async_cached, invalidate_cache

@cached(ttl=300, key_prefix="user")
def get_user(user_id):
    # This function's return value will be cached for 300 seconds
    return db.get_user(user_id)

@async_cached(ttl=300, key_prefix="user")
async def get_user_async(user_id):
    # This async function's return value will be cached for 300 seconds
    return await db.get_user_async(user_id)

@invalidate_cache(patterns=["user:*"])
def update_user(user_id, data):
    # This function will invalidate all cache keys matching the pattern "user:*"
    return db.update_user(user_id, data)
```

## Integration with FastAPI

The caching module integrates with FastAPI for dependency injection:

```python
from fastapi import FastAPI, Depends
from uno.caching import get_caching_dependencies

app = FastAPI()

# Register caching dependencies
caching_deps = get_caching_dependencies()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    cache_service = Depends(caching_deps["get_cache_item_service"])
):
    # First check cache
    result = await cache_service.get_item(f"user:{user_id}")
    if result.is_success() and result.value:
        return result.value.value
    
    # Cache miss - fetch from database
    user = await db.get_user(user_id)
    
    # Store in cache
    await cache_service.set_item(f"user:{user_id}", user, ttl_seconds=300)
    
    return user
```

## Advanced Usage

### Cache-Aside Pattern

```python
from uno.caching import cache_aside

# Define a function to load data if not in cache
async def load_user(user_id):
    return await db.get_user(user_id)

# Use the cache-aside pattern
user = await cache_aside(
    key=f"user:{user_id}",
    loader=lambda: load_user(user_id),
    ttl=300,
    region="users"
)
```

### Monitoring

```python
from uno.caching import get_cache_monitoring_service, CacheStatsType, CacheProviderId

monitoring_service = await get_cache_monitoring_service()

# Record a cache hit
await monitoring_service.record_statistic(
    provider_id=CacheProviderId("memory"),
    stat_type=CacheStatsType.HIT,
    value=1
)

# Get provider statistics
stats_result = await monitoring_service.get_provider_statistics(
    provider_id=CacheProviderId("memory"),
    start_time=datetime.now() - timedelta(hours=1)
)

# Get a summary of provider statistics
summary_result = await monitoring_service.get_provider_summary(
    provider_id=CacheProviderId("memory")
)
```