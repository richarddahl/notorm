# TaskGroup for Structured Concurrency

The TaskGroup pattern provides a mechanism for managing multiple related tasks with proper lifecycle management, error handling, and cancellation.

## Overview

Structured concurrency is an approach to concurrent programming where child tasks are linked to their parent scope, ensuring that:

1. The parent cannot finish before its children complete
2. Errors in children are properly propagated to the parent
3. If the parent is cancelled, all children are cancelled
4. Resources are properly cleaned up when tasks finish

The TaskGroup class in uno implements these principles, providing a clean and safe way to manage concurrent tasks.

## Basic Usage

```python
from uno.core.async.helpers import TaskGroup

async def process_items(items):
    # Create a TaskGroup
    async with TaskGroup() as group:
        # Create tasks for each item
        for item in items:
            # Task is automatically tracked and managed
            group.create_task(process_item(item))
        
        # When we exit the context, all tasks are awaited
        # Any errors are propagated
        # If an error occurs in any task, other tasks are cancelled
```

## Creating Tasks

You create tasks using the `create_task` method:

```python
async with TaskGroup() as group:
    # Create a task
    task = group.create_task(some_coroutine())
    
    # Create a named task
    named_task = group.create_task(other_coroutine(), name="important_operation")
    
    # Tasks are automatically managed
    # No need to explicitly await them
```

## Handling Results

To get results from tasks, you can await them individually within the context:

```python
async with TaskGroup() as group:
    # Create tasks
    tasks = [
        group.create_task(fetch_data(1)),
        group.create_task(fetch_data(2)),
        group.create_task(fetch_data(3))
    ]
    
    # Process results as they complete
    results = []
    for task in tasks:
        try:
            result = await task
            results.append(result)
        except Exception as e:
            # Handle individual task errors
            logger.error(f"Task error: {e}")
```

## Error Handling

The TaskGroup propagates exceptions from child tasks to the parent:

```python
try:
    async with TaskGroup() as group:
        group.create_task(might_fail())
        group.create_task(also_might_fail())
        
        # If any task raises an exception, it's propagated here
except Exception as e:
    # Handle errors
    logger.error(f"Task group error: {e}")
```

If multiple tasks raise exceptions, an `ExceptionGroup` will be raised (Python 3.11+) or the first exception will be raised (earlier Python versions).

## Cancellation

The TaskGroup automatically cancels all tasks when the context is exited due to an exception or cancellation:

```python
async def with_timeout():
    try:
        # Set a timeout
        async with asyncio.timeout(5.0):
            async with TaskGroup() as group:
                # Create long-running tasks
                group.create_task(long_operation_1())
                group.create_task(long_operation_2())
                
                # If the timeout expires, all tasks are cancelled
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
```

You can also manually cancel tasks:

```python
async with TaskGroup() as group:
    task1 = group.create_task(operation1())
    task2 = group.create_task(operation2())
    
    # Cancel a specific task
    task1.cancel()
    
    # Or cancel all tasks at once
    await group.cancel_all()
```

## Integration with AsyncManager

The TaskGroup is deeply integrated with the AsyncManager:

```python
from uno.core.async_manager import get_async_manager

async def managed_operations():
    # Get the manager
    manager = get_async_manager()
    
    # Use the manager's task group
    async with manager.task_group() as group:
        # Tasks created here are managed by the AsyncManager
        # If the application shuts down, these tasks are properly cancelled
        group.create_task(background_operation())
```

## TaskGroup Properties

The TaskGroup provides properties to inspect its state:

```python
async with TaskGroup() as group:
    # Create tasks
    group.create_task(operation1())
    group.create_task(operation2())
    
    # Get active (running) tasks
    active_tasks = group.active_tasks
    
    # Get completed tasks
    completed_tasks = group.completed_tasks
    
    # Get cancelled tasks
    cancelled_tasks = group.cancelled_tasks
```

## Best Practices

1. **Always** use a TaskGroup for managing related concurrent tasks
2. **Always** handle exceptions from individual tasks or from the entire group
3. **Always** properly clean up resources used by tasks
4. **Consider** using timeouts for task groups that might take too long
5. **Avoid** creating "fire and forget" tasks outside of a TaskGroup

## Anti-Patterns to Avoid

1. ❌ Creating tasks with `asyncio.create_task()` without tracking them
2. ❌ Manually using `asyncio.gather()` for task coordination
3. ❌ Using callbacks for handling task completion
4. ❌ Ignoring cancellation in long-running tasks
5. ❌ Creating tasks that outlive their parent scope

## Example: Processing Data in Batches

```python
async def process_data_in_batches(data, batch_size=10):
    # Process data in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        
        # Process each batch with a task group
        async with TaskGroup() as group:
            for item in batch:
                group.create_task(process_item(item))
                
        # Wait for one batch to complete before starting the next
        logger.info(f"Batch {i//batch_size + 1} completed")
```

## Example: Complex Task Dependencies

```python
async def process_with_dependencies():
    # Step 1: Fetch data concurrently
    source_data = []
    async with TaskGroup() as group:
        sources = ["source1", "source2", "source3"]
        tasks = [group.create_task(fetch_data(source)) for source in sources]
        
        # Collect results
        for task in tasks:
            try:
                result = await task
                source_data.append(result)
            except Exception as e:
                logger.error(f"Failed to fetch data: {e}")
    
    # Step 2: Process the aggregated data
    if source_data:
        async with TaskGroup() as group:
            # Process with transformed data
            processed_data = transform_data(source_data)
            group.create_task(store_results(processed_data))
            group.create_task(notify_completion(processed_data))
```

## Further Reading

- [PEP 654 - Exception Groups and except*](https://peps.python.org/pep-0654/)
- [Structured Concurrency in Python](https://peps.python.org/pep-3156/)
- [TaskGroup in Python 3.11+](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup)