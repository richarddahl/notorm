# Async-First Architecture

The Uno framework implements a comprehensive async-first architecture that extends beyond simply using Python's asyncio. This architecture ensures robust handling of asynchronous operations with proper cancellation, error handling, and resource management.

## Core Components

### Task Management

The `TaskManager` and `TaskGroup` classes provide structured concurrency patterns for managing related tasks:

```python
from uno.core.async import TaskGroup, TaskManager

# Create a task group for related operations
async with TaskGroup(name="data_processing") as group:
    # Create tasks that will be properly managed
    task1 = group.create_task(fetch_data(id1), name="fetch_1")
    task2 = group.create_task(fetch_data(id2), name="fetch_2")
    
    # Tasks are automatically cleaned up when the group exits
    results = []
    for task in [task1, task2]:
        try:
            result = await task
            results.append(result)
        except Exception as e:
            logger.error(f"Task failed: {e}")
```

### Enhanced Concurrency Primitives

The framework provides enhanced versions of standard asyncio primitives:

```python
from uno.core.async import AsyncLock, AsyncSemaphore, AsyncEvent, timeout

# Use an enhanced lock with timeout and cancellation handling
async with AsyncLock(name="resource_lock") as lock:
    # Lock is automatically released even on cancellation
    
    # Use timeout context for operations
    async with timeout(5.0, "Operation timed out"):
        # This will raise a TimeoutError after 5 seconds
        await long_running_operation()
```

### Async Integration Utilities

Utilities like decorators for common async patterns:

```python
from uno.core.async_integration import cancellable, retry, timeout_handler

# Apply multiple async patterns at once
@cancellable
@retry(max_attempts=3)
@timeout_handler(timeout_seconds=5.0)
async def fetch_external_data(id):
    # This function now has:
    # - Proper cancellation handling
    # - Automatic retry on failure
    # - Timeout after 5 seconds
    
    # Implement the core functionality
    return await api_client.get(f"/data/{id}")
```

### Resource Management

Centralized management of async resources:

```python
from uno.core.async_manager import get_async_manager, as_task

# Get the global async manager
manager = get_async_manager()

# Create managed background tasks
@as_task("background_monitor")
async def monitor_system():
    # This task is managed by the AsyncManager
    while True:
        await asyncio.sleep(10)
        # Do monitoring work
        
        # Check if shutting down
        if manager.is_shutting_down():
            break

# Register resources for lifecycle management
await manager.register_resource(db_client, name="database")
```

### Enhanced Database Operations

Database operations with improved async handling:

```python
from uno.database.enhanced_session import enhanced_async_session, SessionOperationGroup

# Use enhanced async session with proper cleanup
async with enhanced_async_session() as session:
    # Session is automatically closed even on cancellation
    
    # Execute query with timeout
    result = await session.execute("SELECT * FROM data WHERE id = :id", {"id": data_id})
    row = result.fetchone()

# Use session operation group for coordinated transactions
async with SessionOperationGroup() as op_group:
    # Create multiple sessions if needed
    session1 = await op_group.create_session()
    session2 = await op_group.create_session()
    
    # Run operations with proper coordination
    results = await op_group.run_in_transaction(
        session1,
        [
            lambda s: s.execute("UPDATE data SET value = :value WHERE id = :id", 
                               {"id": id1, "value": value1}),
            lambda s: s.execute("INSERT INTO audit (action, entity_id) VALUES (:action, :id)",
                               {"action": "update", "id": id1})
        ]
    )
```

### Batching and Caching

Utilities for efficient async operations:

```python
from uno.core.async_integration import AsyncBatcher, AsyncCache

# Create a batcher for database operations
insert_batcher = AsyncBatcher(
    batch_operation=batch_insert_function,
    max_batch_size=100,
    max_wait_time=0.05
)

# Add items to the batch and get results
result = await insert_batcher.add_item(data)

# Create a cache for frequent queries
query_cache = AsyncCache(
    ttl=60.0,  # 1 minute TTL
    refresh_before_expiry=10.0  # Refresh 10s before expiry
)

# Get from cache or fetch
result = await query_cache.get(
    key=cache_key,
    fetch_func=lambda k: fetch_from_database(k)
)
```

## Key Features

### Proper Cancellation Handling

All async utilities properly handle task cancellation, ensuring:

- Resources are properly cleaned up
- No resource leaks occur
- Proper propagation of cancellation

### Structured Concurrency

The framework implements structured concurrency principles:

- Tasks are organized into logical groups
- Parent tasks wait for all child tasks
- Errors propagate properly
- Resources are cleaned up deterministically

### Timeout Management

Comprehensive timeout handling:

- All operations can have timeouts
- Timeouts are reported with meaningful messages
- Automatic resource cleanup on timeout

### Resource Lifecycle Management

Complete lifecycle management:

- Resources are registered with the AsyncManager
- Graceful shutdown with proper cleanup
- Signal handling for clean application termination

### Error Recovery

Robust error handling:

- Automatic retry for transient errors
- Circuit breakers for external services
- Rate limiting to prevent overload
- Proper backoff strategies

## Integration with Other Components

The Async-First Architecture integrates with other Uno framework components:

- **DDD**: Async repository implementations
- **CQRS**: Async command and query handling
- **Event-Driven Architecture**: Async event publication and handling
- **API Layer**: Async endpoints with proper cancellation

## Best Practices

### Decorated Functions

Use the provided decorators for the most common patterns:

```python
@cancellable  # Always handle cancellation properly
@retry(max_attempts=3)  # Retry on transient errors
@timeout_handler(timeout_seconds=5.0)  # Set timeouts
@rate_limited(operations_per_second=10)  # Control request rates
@concurrent_limited(max_concurrent=5)  # Limit concurrency
async def your_function():
    # Implementation
```

### Structured Task Management

Always use structured concurrency to manage tasks:

```python
async with TaskGroup() as group:
    # Create tasks within the group
    tasks = [
        group.create_task(process_item(item)) 
        for item in items
    ]
    
    # Process results as they complete
    for task in tasks:
        try:
            result = await task
            # Handle result
        except Exception as e:
            # Handle error
```

### Resource Cleanup

Always use context managers for resources:

```python
async with AsyncContextGroup() as ctx_group:
    # Add multiple resources to the group
    session = await ctx_group.enter_async_context(enhanced_async_session())
    client = await ctx_group.enter_async_context(api_client.connect())
    
    # Use resources safely
    # All resources are cleaned up when exiting the context
```

### Application Lifecycle

Integrate with the application lifecycle:

```python
from uno.core.async_manager import run_application

async def startup():
    # Initialize resources
    pass

async def cleanup():
    # Clean up resources
    pass

# Run the application with proper lifecycle management
await run_application(
    startup_func=startup,
    cleanup_func=cleanup
)
```