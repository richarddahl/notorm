# Async Resource Management

Proper management of asynchronous resources is crucial for creating robust applications. This guide explains how to correctly manage async resources in the uno framework.

## Core Principles

1. **Context Managers**: All resources should be managed with async context managers
2. **Proper Initialization**: Resources should be properly initialized before use
3. **Proper Cleanup**: Resources should be properly cleaned up when no longer needed
4. **Cancellation Handling**: Resource operations should handle cancellation gracefully
5. **Error Handling**: Errors during resource operations should be properly captured and handled

## AsyncResource Base Class

The uno framework provides an `AsyncResource` base class that implements these principles:

```python
from uno.core.async.helpers import AsyncResource

class DatabaseConnection(AsyncResource):
    async def _initialize(self) -> None:
        """Initialize the resource."""
        self.connection = await create_connection()
    
    async def _cleanup(self) -> None:
        """Clean up the resource."""
        await self.connection.close()
    
    async def execute(self, query: str) -> Any:
        """Execute a query using the resource."""
        return await self.connection.execute(query)

# Using the resource
async with DatabaseConnection() as conn:
    result = await conn.execute("SELECT * FROM users")
```

## Resources with AsyncManager

Register important resources with the AsyncManager for centralized lifecycle management:

```python
from uno.core.async_manager import get_async_manager

async def setup_resources():
    # Get the manager
    manager = get_async_manager()
    
    # Create and register resources
    db_pool = await create_db_pool()
    await manager.register_resource(db_pool, name="database_pool")
    
    cache = await create_cache()
    await manager.register_resource(cache, name="redis_cache")
    
    # Resources will be properly shut down when the manager shuts down
```

## Connection Pools

Database connection pools should be properly managed:

```python
from uno.database.enhanced_connection_pool import EnhancedConnectionPool

# Create a connection pool
pool = EnhancedConnectionPool(
    dsn="postgresql://user:password@localhost/dbname",
    min_size=5,
    max_size=20
)

# Use the pool as a context manager
async with pool.acquire() as connection:
    # Use the connection
    result = await connection.fetch("SELECT * FROM users")

# When your application shuts down
await pool.close()
```

## AsyncResourcePool

For custom resources that need pooling, use the AsyncResourcePool:

```python
from uno.core.async_integration import AsyncResourcePool

# Create a factory function
async def create_api_client():
    client = ApiClient()
    await client.initialize()
    return client

# Create a pool
pool = AsyncResourcePool(
    factory=create_api_client,
    max_size=10,
    min_size=2,
    max_idle=5
)

# Use a resource from the pool
async with pool.get() as client:
    # Use the client
    result = await client.fetch_data()

# When done with the pool
await pool.close()
```

## AsyncCache

For caching, use the AsyncCache with proper resource management:

```python
from uno.core.async_integration import AsyncCache

# Create a cache
cache = AsyncCache(ttl=60.0, refresh_before_expiry=50.0)

# Use the cache
async def get_data(key):
    # Gets from cache or fetches
    return await cache.get(key, fetch_func=fetch_data)

# When done with the cache
await cache.clear()
```

## Resource Tracking

For tracking resource usage, use the resource monitoring utilities:

```python
from uno.core.resource_monitor import track_resource

# Track resource usage
@track_resource("api_client")
async def use_api_client():
    client = ApiClient()
    try:
        await client.initialize()
        return await client.fetch_data()
    finally:
        await client.close()
```

## Error Handling with Resources

Always use try/finally or context managers to ensure cleanup:

```python
async def use_resource_safely():
    # Method 1: Using a context manager (preferred)
    async with Resource() as resource:
        await resource.operation()
    
    # Method 2: Using try/finally
    resource = Resource()
    try:
        await resource.initialize()
        await resource.operation()
    finally:
        await resource.cleanup()
```

## Cancellation Handling

Resources should handle cancellation gracefully:

```python
async def cleanup_on_cancel():
    resource = Resource()
    try:
        await resource.initialize()
        await resource.long_operation()
    except asyncio.CancelledError:
        # Perform any necessary cleanup before re-raising
        await resource.cleanup()
        raise
    finally:
        # This still runs even if cancelled
        await resource.final_cleanup()
```

## AsyncExitStack for Multiple Resources

When managing multiple resources, use AsyncExitStack:

```python
from contextlib import AsyncExitStack

async def use_multiple_resources():
    async with AsyncExitStack() as stack:
        # Enter contexts and register cleanup
        db = await stack.enter_async_context(Database())
        cache = await stack.enter_async_context(Cache())
        api = await stack.enter_async_context(ApiClient())
        
        # Use resources
        data = await db.query()
        cached = await cache.get("key")
        result = await api.fetch()
        
        # All resources are automatically cleaned up
```

## Resource Classes Hierarchy

In uno, resources follow this general hierarchy:

```
AsyncResource (base)
├── DatabaseResource
│   ├── ConnectionPool
│   ├── TransactionManager
│   └── QueryExecutor
├── CacheResource
│   ├── LocalCache
│   └── DistributedCache
├── NetworkResource
│   ├── HttpClient
│   └── WebSocketClient
└── FileResource
    ├── FileReader
    └── FileWriter
```

Each resource type implements its own initialization and cleanup logic.

## Best Practices

1. **Always** use async context managers for resource management
2. **Always** ensure resources are properly closed, even in error cases
3. **Always** handle cancellation in long-lived resources
4. **Consider** using resource pools for expensive resources
5. **Consider** registering important resources with AsyncManager
6. **Use** AsyncExitStack for managing multiple resources together
7. **Implement** proper error handling for all resource operations

## Anti-Patterns to Avoid

1. ❌ Manual resource management without context managers
2. ❌ Not handling cancellation in resource cleanup
3. ❌ Creating resource-intensive operations without proper bounds
4. ❌ Leaking connections or other resources
5. ❌ Not handling errors that occur during cleanup