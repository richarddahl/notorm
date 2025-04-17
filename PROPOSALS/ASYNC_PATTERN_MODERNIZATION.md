# Async Pattern Modernization

## Overview

This document outlines the plan to modernize async patterns throughout the uno framework, transitioning from legacy patterns to modern Python 3.12+ async best practices.

## Current Issues

The uno framework currently uses several async patterns that are either deprecated or don't follow modern best practices:

1. **Direct Event Loop Access**
   - `asyncio.get_event_loop()` is used directly in multiple places
   - This approach is discouraged in Python 3.10+ and may be removed in future versions

2. **Inconsistent Task Management**
   - Inconsistent approaches to creating and managing tasks
   - Not using modern task group patterns effectively

3. **Signal Handling**
   - Signal handling uses direct event loop access
   - Could be modernized with newer patterns

4. **Transaction Management**
   - Transaction management is done inconsistently across the codebase
   - Some places use explicit commit/rollback while others use context managers

## Modernization Plan

### 1. Replace Direct Event Loop Access

Replace all instances of `asyncio.get_event_loop()` with more modern alternatives:

- **For task creation**: Use `asyncio.create_task()` or the TaskManager 
- **For signal handling**: Create a centralized signal management system
- **For application entry points**: Use `asyncio.run()`

### 2. Implement TaskGroup for Task Management

Python 3.11+ introduced official support for `asyncio.TaskGroup`, which provides a structured way to manage groups of tasks:

```python
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(coro1())
    task2 = tg.create_task(coro2())
    # Tasks are automatically awaited when exiting the context
    # Exceptions are propagated properly
```

The framework should:
- Update the existing `TaskGroup` implementation to align with the standard library version
- Use TaskGroup wherever multiple tasks are created and need coordinated cancellation
- Provide helpers to make task creation and management easier

### 3. Standardize Transaction Management

Create consistent transaction management patterns:

```python
# Context manager pattern
async with transaction_context(session) as tx:
    # Operations within transaction
    # Auto-commits on success, rolls back on exception
```

Improvements:
- Create a standard `transaction` context manager
- Update all database operations to use consistent transaction patterns
- Add transaction decorator for service methods

### 4. Modern Signal Handling

Replace direct event loop signal handling with a more modular approach:

```python
def register_signal_handlers(handler_func):
    """Register signal handlers that call the given function."""
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(handler_func(s)))
```

### 5. AsyncManager Improvements

The AsyncManager class should be updated to:
- Remove direct event loop access
- Use TaskGroup for task management
- Provide better lifecycle management
- Support structured concurrency patterns

## Implementation Plan

### Phase 1: Core Utilities

1. Create modern async utilities:
   - `transaction` context manager
   - Updated `TaskGroup` implementation
   - Signal handling utilities

2. Update the AsyncManager class:
   - Remove direct event loop access
   - Use TaskGroup for task management
   - Implement modern signal handling

### Phase 2: Update Database Layer

1. Standardize transaction management throughout the database layer
2. Update session management to use modern patterns
3. Ensure all database operations use consistent async patterns

### Phase 3: Update Application Services

1. Update all application services to use the new async utilities
2. Ensure consistent task management across the codebase
3. Verify proper resource cleanup

## Benefits

The modernized async patterns will provide several benefits:

1. **Future-Proofing**: Ensures compatibility with newer Python versions
2. **Better Resource Management**: More structured approach to managing async resources
3. **Improved Error Handling**: Better propagation of exceptions in async code
4. **Easier Debugging**: More consistent patterns make async code easier to debug
5. **Performance Improvements**: Modern patterns can lead to better performance

## Compatibility

As uno is a new library without existing users, these changes can be made without backward compatibility concerns. All code will be updated to use the new patterns without maintaining legacy adapters.

## Testing

All changes will be thoroughly tested:
- Update unit tests to test the new async patterns
- Ensure integration tests use the new patterns
- Add specific tests for error handling in async contexts