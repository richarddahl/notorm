# Asynchronous Programming in uno

The uno framework is built with asynchronous programming at its core, leveraging Python's asyncio library with modern patterns and best practices.

## Contents

- [Modern Async Patterns](modern_patterns.md) - An overview of the async patterns used in uno
- [TaskGroup](taskgroup.md) - How to use the TaskGroup for structured concurrency
- [Transaction Management](transactions.md) - How to use transaction context managers
- [Resource Management](resources.md) - How to properly manage async resources
- [Error Handling](error_handling.md) - How to handle errors in async code
- [Complete Example](../../examples/modern_async_patterns.py) - A comprehensive example demonstrating all the patterns together

## Quick Reference

### Creating Tasks

```python
# Create a task
task = asyncio.create_task(coroutine())

# Create a task within a task group
async with TaskGroup() as group:
    task = group.create_task(coroutine())
```

### Managing Resources

```python
# Using a resource with async context manager
async with resource as r:
    await r.operation()
```

### Database Transactions

```python
# Simple transaction
async with transaction(session):
    # Database operations

# Transaction manager
async with transaction_manager() as session:
    # Database operations
```

### Timeouts

```python
# Timeout for an operation
async with asyncio.timeout(5.0):
    await operation()
```

### Retry

```python
@retry(max_attempts=3)
async def operation():
    # May fail but will retry
```

## Async Manager

The `AsyncManager` provides centralized management of async resources, tasks, and lifecycle:

```python
from uno.core.async_manager import get_async_manager

# Get the manager
manager = get_async_manager()

# Create a managed task
task = manager.create_task(coroutine())

# Use task group
async with manager.task_group() as group:
    group.create_task(coroutine())

# Register a resource
await manager.register_resource(resource)

# Graceful shutdown
await manager.shutdown()
```

## Further Reading

For more information on Python's asyncio:

- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [PEP 3156 - Asynchronous I/O Support](https://peps.python.org/pep-3156/)
- [PEP 492 - Coroutines with async and await syntax](https://peps.python.org/pep-0492/)
- [PEP 567 - Context Variables](https://peps.python.org/pep-0567/)
- [PEP 654 - Exception Groups and except*](https://peps.python.org/pep-0654/)