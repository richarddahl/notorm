# Async Error Handling

Proper error handling in asynchronous code requires special consideration. This guide outlines the best practices for handling errors in async code with the uno framework.

## Core Principles

1. **Result Pattern**: Use Result objects for representing operation outcomes
2. **Structured Error Propagation**: Properly propagate errors to the appropriate handler
3. **Cancellation Handling**: Properly handle task cancellation
4. **Resource Cleanup**: Ensure resources are cleaned up even in error cases
5. **Error Context**: Provide detailed context for errors

## Result Pattern

The uno framework uses a Result pattern to represent operation outcomes:

```python
from uno.core.result import Result, Success, Failure

async def get_user(user_id: str) -> Result[User, Exception]:
    try:
        # Try to get the user
        user = await db.users.get(id=user_id)
        if not user:
            return Failure(ValueError(f"User not found: {user_id}"))
        
        return Success(user)
    except Exception as e:
        return Failure(e)
```

Using Results in call sites:

```python
result = await get_user(user_id)
if result.is_success:
    # Access the success value
    user = result.value
    process_user(user)
else:
    # Access the error
    error = result.error
    logger.error(f"Failed to get user: {error}")
```

## Try/Except Patterns

Use try/except blocks to handle specific exceptions:

```python
async def perform_operation():
    try:
        # Attempt the operation
        await operation()
    except ConnectionError as e:
        # Handle connection errors
        logger.error(f"Connection error: {e}")
        await retry_with_backoff()
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {e}")
        return None
    except Exception as e:
        # Handle unexpected errors
        logger.exception(f"Unexpected error: {e}")
        raise
```

## Handling Cancellation

Always handle cancellation properly:

```python
async def cancellable_operation():
    try:
        await long_running_operation()
    except asyncio.CancelledError:
        # Perform any necessary cleanup
        logger.info("Operation was cancelled")
        raise  # Re-raise to propagate cancellation
```

## Error Context

Provide detailed context for errors:

```python
from uno.core.result import Success, Failure
from uno.core.errors import UnoError

async def process_data(data: Dict[str, Any]) -> Result[Dict[str, Any], UnoError]:
    try:
        # Process data
        processed = await transform_data(data)
        return Success(processed)
    except Exception as e:
        # Create an error with context
        error = UnoError(
            message="Failed to process data",
            error_code="DATA_PROCESSING_ERROR",
            source=process_data.__name__,
            context={
                "data_id": data.get("id"),
                "timestamp": datetime.now(),
                "error_type": type(e).__name__,
            },
            original_error=e,
        )
        return Failure(error)
```

## Retrying Operations

Use the retry decorator for operations that may fail temporarily:

```python
from uno.core.async_integration import retry, BackoffStrategy

@retry(
    max_attempts=3,
    retry_exceptions=[ConnectionError, TimeoutError],
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    max_delay=10.0
)
async def fetch_data(url: str) -> Dict[str, Any]:
    # This function will be retried if it raises one of the specified exceptions
    return await http_client.get(url)
```

## TaskGroup Error Handling

Handle errors from TaskGroup properly:

```python
from uno.core.async.helpers import TaskGroup

async def process_batch(items: List[Item]):
    try:
        async with TaskGroup() as group:
            for item in items:
                group.create_task(process_item(item))
            
            # If any task raises an exception, it will be propagated here
    except* Exception as eg:  # Python 3.11+ syntax for exception groups
        # Log the exception group
        logger.error(f"Error processing batch: {eg}")
        
        # Extract specific exceptions if needed
        for e in eg.exceptions:
            if isinstance(e, ResourceError):
                # Handle resource errors
                await cleanup_resources()
```

For Python < 3.11:

```python
try:
    async with TaskGroup() as group:
        for item in items:
            group.create_task(process_item(item))
except Exception as e:
    # Handle the first exception
    logger.error(f"Error processing batch: {e}")
    await cleanup_resources()
```

## Timeouts

Use timeouts for operations that may hang:

```python
import asyncio

async def fetch_with_timeout(url, timeout=5.0):
    try:
        async with asyncio.timeout(timeout):
            return await fetch_data(url)
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out for {url}")
        return None
```

## Resource Cleanup

Ensure resources are cleaned up in error cases:

```python
async def use_resource_safely():
    resource = await create_resource()
    try:
        # Use the resource
        await resource.operation()
    finally:
        # This block always executes, even if the operation fails
        await resource.close()
```

Better approach with context manager:

```python
async def use_resource_safely():
    async with await create_resource() as resource:
        # Use the resource
        await resource.operation()
        # Resource is automatically closed when exiting the context
```

## Error Mapping

Map low-level errors to domain-specific errors:

```python
from uno.core.result import Result, Success, Failure
from uno.domain.errors import UserNotFoundError, UserValidationError

async def get_user(user_id: str) -> Result[User, Exception]:
    try:
        user = await db.users.get(id=user_id)
        if not user:
            return Failure(UserNotFoundError(user_id))
        
        return Success(user)
    except ValueError as e:
        # Map ValueError to domain-specific error
        return Failure(UserValidationError(str(e)))
    except Exception as e:
        # Map other exceptions to generic error
        return Failure(e)
```

## Error Handling at API Boundaries

At API boundaries, convert Results to proper responses:

```python
from uno.core.result import Result
from uno.api.endpoint import UnoEndpoint

class UserEndpoint(UnoEndpoint):
    async def get(self, user_id: str):
        # Get user using Result pattern
        result = await self.user_service.get_user(user_id)
        
        # Convert Result to API response
        if result.is_success:
            # Return successful response
            return self.success_response(result.value)
        else:
            # Map error to appropriate response
            error = result.error
            if isinstance(error, UserNotFoundError):
                return self.error_response(error, status_code=404)
            elif isinstance(error, UserValidationError):
                return self.error_response(error, status_code=400)
            else:
                return self.error_response(error, status_code=500)
```

## Structured Logging

Use structured logging for error reporting:

```python
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

async def log_error(e: Exception, context: Dict[str, Any] = None):
    """Log an error with structured context."""
    log_context = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(e).__name__,
        "error_message": str(e),
        "traceback": traceback.format_exc(),
    }
    
    if context:
        log_context.update(context)
    
    logger.error("Error occurred", extra={"context": log_context})
```

## Best Practices

1. **Always** use Result objects for operation outcomes
2. **Always** handle cancellation in long-running operations
3. **Always** ensure resources are properly cleaned up in error cases
4. **Always** provide detailed context for errors
5. **Use** try/except blocks for specific error handling
6. **Consider** using retry for temporary failures
7. **Use** timeouts for operations that may hang
8. **Map** low-level errors to domain-specific errors at boundaries

## Anti-Patterns to Avoid

1. ❌ Ignoring exceptions
2. ❌ Catching all exceptions without proper handling
3. ❌ Not handling cancellation
4. ❌ Not cleaning up resources in error cases
5. ❌ Using bare except blocks without context
6. ❌ Not logging or reporting errors properly
7. ❌ Creating overly broad error handlers