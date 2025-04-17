# Modern Async Patterns in uno

This guide outlines the modern async patterns used throughout the uno framework and how to implement them in your code.

## Core Principles

The uno framework follows these principles for async code:

1. **Structured Concurrency**: Tasks are organized in groups with managed lifecycles
2. **Proper Resource Management**: Resources are always properly closed
3. **Consistent Transaction Handling**: Database transactions use standardized context managers
4. **Error Propagation**: Errors are properly propagated and handled
5. **Cancellation Handling**: All async operations properly handle cancellation

## TaskGroup for Structured Concurrency

The TaskGroup class provides a way to manage multiple related tasks:

```python
from uno.core.async.helpers import TaskGroup

async def process_items(items):
    async with TaskGroup() as group:
        # Create tasks that will be automatically awaited and cleaned up
        for item in items:
            group.create_task(process_item(item))
        
        # The TaskGroup automatically cleans up when exiting the context
```

### When to Use TaskGroup

- When creating multiple related tasks that should be managed together
- When you need to ensure all tasks complete or are cancelled before continuing
- When you want to properly handle errors from multiple tasks

## Transaction Management

Always use transaction context managers for database operations:

```python
from uno.database.transaction import transaction

async def update_user(user_id, data, session):
    async with transaction(session):
        # Perform database operations
        # Automatically commits on success, rolls back on error
```

For more complex scenarios, use the transaction factory:

```python
from uno.database.transaction_factory import create_write_transaction_manager

# Create a transaction manager for a specific session factory
transaction_manager = create_write_transaction_manager(session_factory)

async def update_user(user_id, data):
    # This creates a session, executes in a transaction, and properly closes
    async with transaction_manager() as session:
        # Perform database operations
        # Transaction is automatically committed or rolled back
```

## Async Resources

All resources should use async context managers for proper cleanup:

```python
from uno.core.async.helpers import AsyncResource

class DatabaseConnection(AsyncResource):
    async def _initialize(self) -> None:
        # Initialize the resource
        self.connection = await create_connection()
    
    async def _cleanup(self) -> None:
        # Clean up the resource
        await self.connection.close()
    
    async def execute(self, query):
        # Use the resource
        return await self.connection.execute(query)

# Using the resource
async with DatabaseConnection() as conn:
    result = await conn.execute("SELECT * FROM users")
```

## Handling Time

Always use `asyncio.get_running_loop().time()` instead of `asyncio.get_event_loop().time()`:

```python
import asyncio

async def measure_time():
    start = asyncio.get_running_loop().time()
    await some_operation()
    end = asyncio.get_running_loop().time()
    return end - start
```

## Signal Handling

Use the modern signal handling pattern:

```python
from uno.core.async.helpers import setup_signal_handler

async def handle_signal(sig):
    print(f"Received signal {sig.name}")
    # Clean up and shut down

async def main():
    # Set up signal handlers
    await setup_signal_handler(signal.SIGINT, handle_signal)
    await setup_signal_handler(signal.SIGTERM, handle_signal)
    
    # Run the application
    # ...
```

## Retry Pattern

Use the retry decorator for operations that may fail temporarily:

```python
from uno.core.async_integration import retry, BackoffStrategy

@retry(
    max_attempts=3,
    retry_exceptions=[ConnectionError, TimeoutError],
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    max_delay=10.0
)
async def fetch_data(url):
    # This function will retry up to 3 times with exponential backoff
    # if it raises ConnectionError or TimeoutError
    return await http_client.get(url)
```

## Timeout Handling

Always use timeouts for operations that may hang:

```python
import asyncio

async def fetch_with_timeout(url, timeout=5.0):
    async with asyncio.timeout(timeout):
        return await fetch_data(url)
```

## Batching Operations

Use AsyncBatcher for efficient batch processing:

```python
from uno.core.async_integration import AsyncBatcher

# Create a batcher that processes items in batches of 100
batcher = AsyncBatcher(
    batch_operation=process_batch,
    max_batch_size=100,
    max_wait_time=0.1
)

# Add items individually, they'll be processed in batches
for item in items:
    result = await batcher.add_item(item)
```

## Managing Concurrency

Control the number of concurrent operations:

```python
from uno.core.async_integration import concurrent_limited

@concurrent_limited(max_concurrent=5)
async def process_item(item):
    # This function will have at most 5 concurrent executions
    # Others will wait until a slot is available
    await expensive_operation(item)
```

## Best Practices

1. **Never** access the event loop directly, use `asyncio.create_task()` and `asyncio.get_running_loop()`
2. **Always** use context managers for resources and transactions
3. **Always** handle cancellation in long-running operations
4. **Always** use TaskGroup for managing multiple tasks
5. **Always** clean up resources properly

## Anti-Patterns to Avoid

1. ❌ Using `asyncio.get_event_loop()`
2. ❌ Manual transaction management with explicit commit/rollback
3. ❌ Creating "fire and forget" tasks without proper management
4. ❌ Not handling cancellation in long-running operations
5. ❌ Using `asyncio.gather()` without proper error handling