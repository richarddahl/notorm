# Async Utilities Overview

The uno framework provides a comprehensive suite of async utilities that extend Python's built-in asyncio library to address common challenges in asynchronous programming. These utilities are designed to make asynchronous code more robust, maintainable, and easier to reason about.

## Key Components

The async utilities are organized into several logical components:

### 1. Task Management

The task management module provides utilities for managing asyncio tasks with proper cancellation handling, error propagation, and cleanup:

- `TaskManager`: Global task manager for the application
- `TaskGroup`: Group of related tasks that can be managed together
- `task_context`: Context manager for task-specific context
- `run_task`: Function to run a task with proper error handling
- `run_tasks`: Function to run multiple tasks concurrently
- `cancel_on_exit`: Context manager that cancels tasks on exit

[Learn more about Task Management](task_management.md)

### 2. Concurrency Primitives

Enhanced concurrency primitives that extend the standard asyncio primitives with better error handling, timeout support, and debugging:

- `AsyncLock`: Enhanced lock with timeout and ownership tracking
- `AsyncSemaphore`: Enhanced semaphore with timeout support
- `AsyncEvent`: Enhanced event with timeout support
- `Limiter`: Utility for limiting concurrent operations
- `RateLimiter`: Utility for limiting the rate of operations
- `timeout`: Context manager for timeouts with meaningful messages

[Learn more about Concurrency Primitives](concurrency.md)

### 3. Context Management

Utilities for managing async context managers:

- `AsyncContextGroup`: Group of async context managers that can be entered and exited together
- `AsyncExitStack`: Enhanced version of asyncio's ExitStack
- `async_contextmanager`: Enhanced decorator for creating async context managers

[Learn more about Context Management](context.md)

### 4. Integration Utilities

Utilities for integrating async patterns into your application:

- `cancellable`: Decorator for making functions properly handle cancellation
- `timeout_handler`: Decorator for adding timeout handling to async functions
- `retry`: Decorator for adding retry logic to async functions
- `rate_limited`: Decorator for rate-limiting async functions
- `concurrent_limited`: Decorator for limiting concurrent executions
- `AsyncBatcher`: Utility for batching async operations
- `AsyncCache`: Async-aware cache with timeout and background refresh
- `AsyncResource`: Base class for async resources with lifecycle management
- `AsyncResourcePool`: Pool of async resources

[Learn more about Integration Utilities](integration.md)

### 5. Application Lifecycle Management

Utilities for managing the lifecycle of an async application:

- `AsyncManager`: Central manager for async resources and tasks
- `get_async_manager`: Function to get the singleton instance of AsyncManager
- `as_task`: Decorator to run a function as a managed task
- `run_application`: Function to run an application with proper lifecycle management

[Learn more about Application Lifecycle](lifecycle.md)

## Key Features

### Proper Cancellation Handling

All async utilities are designed to properly handle task cancellation, ensuring that resources are cleaned up properly and cancellation is propagated correctly.

### Structured Concurrency

The utilities implement structured concurrency patterns, making it easier to reason about async code and ensuring that resources are properly cleaned up.

### Enhanced Error Handling

The utilities provide better error handling than standard asyncio, with more meaningful error messages and proper error propagation.

### Resource Management

The utilities provide a comprehensive approach to resource management, ensuring that resources are properly acquired and released, even in the face of cancellation or errors.

### Performance Optimization

Many utilities are designed to optimize performance through batching, caching, and connection pooling.

## Usage Examples

### Basic Task Management

```python
from uno.core.async import TaskGroup

async def process_items(items):```

results = []
``````

```
```

async with TaskGroup(name="process_items") as group:```

# Create a task for each item
tasks = [
    group.create_task(process_item(item), name=f"process_{i}")
    for i, item in enumerate(items)
]
``````

```
```

# Process results as they complete
for task in tasks:
    try:
        result = await task
        results.append(result)
    except Exception as e:
        logger.error(f"Error processing item: {e}")
```
``````

```
```

return results
```
```

### Enhanced Concurrency Primitives

```python
from uno.core.async import AsyncLock, timeout

async def update_resource(resource_id, data):```

# Use an enhanced lock with timeout
async with AsyncLock(name=f"resource_{resource_id}"):```

# Use timeout for the operation
async with timeout(5.0, f"Timeout updating resource {resource_id}"):
    # Perform the update
    return await perform_update(resource_id, data)
```
```
```

### Integration with Decorators

```python
from uno.core.async_integration import cancellable, retry, timeout_handler

@cancellable
@retry(max_attempts=3)
@timeout_handler(timeout_seconds=5.0)
async def fetch_data(data_id):```

# This function now has:
# - Proper cancellation handling
# - Automatic retry on failure
# - Timeout after 5 seconds
return await api_client.get(f"/data/{data_id}")
```
```

### Application Lifecycle

```python
from uno.core.async_manager import run_application, get_async_manager

async def startup():```

# Initialize application resources
manager = get_async_manager()
``````

```
```

# Start background tasks
manager.create_task(background_task(), name="background")
```
    
async def cleanup():```

# Clean up resources
pass
```

# Run the application
if __name__ == "__main__":```

import asyncio
asyncio.run(run_application(```

startup_func=startup,
cleanup_func=cleanup
```
))
```
```

## Integration with Other Components

The async utilities are designed to integrate seamlessly with other uno framework components:

- **Database**: Enhanced async sessions and connection management
- **API**: Async endpoint handlers with proper cancellation
- **CQRS**: Async command and query handling
- **Events**: Async event publishing and handling

## Best Practices

For detailed best practices, see the individual component documentation pages.

- Always handle cancellation properly
- Use structured concurrency patterns
- Set appropriate timeouts for operations
- Use context managers for resource management
- Follow the resource acquisition is initialization (RAII) pattern
- Register resources with the AsyncManager for proper lifecycle management