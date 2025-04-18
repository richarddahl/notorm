# Uno Framework Error Handling

The Uno framework provides a comprehensive, unified approach to error handling. This system combines structured exceptions with a functional Result pattern, rich diagnostic information, and consistent error reporting across the application.

## Core Concepts

### Single Import Point

All error handling components are available from a single import point:

```python
from uno.core.errors import (
    UnoError, ValidationError, DatabaseError, AuthorizationError, 
    Result, Success, Failure, success, failure,
    ErrorCode, with_error_context
)
```

### Structured Exceptions with Context

`UnoError` is the foundation of the error system, providing structured error handling with error codes and contextual information:

```python
from uno.core.errors import UnoError, ErrorCode

# Raising errors with context
raise UnoError(
    message="Failed to process user data", 
    error_code=ErrorCode.INTERNAL_ERROR, 
    user_id=123,
    operation="account_update"
)
```

### Specialized Error Types

Common error scenarios have specialized error classes:

```python
from uno.core.errors import ValidationError, EntityNotFoundError, DatabaseError

# Validation errors
raise ValidationError(
    message="Invalid input data",
    field="email",
    value="not-an-email"
)

# Entity not found
raise EntityNotFoundError(
    entity_type="User",
    entity_id=123
)

# Database errors
raise DatabaseError(
    message="Database query failed",
    error_code=ErrorCode.DB_QUERY_ERROR,
    query="SELECT * FROM users WHERE id = :id",
    params={"id": 123}
)
```

### Functional Error Handling with Result Pattern

For functions where errors are expected and should be handled functionally:

```python
from uno.core.errors import Result, success, failure

def divide(a: int, b: int) -> Result[float]:
    if b == 0:
        return failure(ValueError("Division by zero"))
    return success(a / b)

# Using the result
result = divide(10, 2)
if result.is_success:
    print(f"Result: {result.value}")
else:
    print(f"Error: {result.error}")

# Chaining operations with the Result pattern
def get_user(user_id: int) -> Result[dict]:
    # Implementation...
    
def update_user(user: dict, data: dict) -> Result[dict]:
    # Implementation...

# Chain operations with flat_map
result = get_user(123).flat_map(
    lambda user: update_user(user, {"status": "active"})
)
```

### Error Context for Diagnostics

Rich contextual information for errors using decorators and context managers:

```python
from uno.core.errors import with_error_context, with_async_error_context, add_error_context

# Using as a decorator (automatically captures function parameters)
@with_error_context
def process_user(user_id: int, action: str):
    # user_id and action are automatically added to error context
    add_error_context(processing_time=datetime.now())
    # If an error occurs, it will include all context information
    
# Using as a context manager
with with_error_context(operation="user_update", user_id=123):
    # Code that might raise errors
    pass

# Async version for coroutines
@with_async_error_context
async def process_user_async(user_id: int):
    # Context works the same as in synchronous code
    pass
```

### Validation System

Structured validation with a focus on clear error messages:

```python
from uno.core.errors import ValidationContext, validate_fields
from typing import Dict, Any, Optional

def validate_email(value: str) -> Optional[str]:
    if "@" not in value:
        return "Invalid email format"
    return None

def validate_user(data: Dict[str, Any]):
    validate_fields(
        data=data,
        required_fields={"username", "email", "password"},
        validators={
            "email": [validate_email],
            "password": [lambda v: "Password too short" if len(v) < 8 else None]
        },
        entity_name="User"
    )
    
# Using ValidationContext for complex validation
def validate_complex_object(data: Dict[str, Any]):
    context = ValidationContext("ComplexObject")
    
    # Validate top-level fields
    if "name" not in data:
        context.add_error("name", "Field is required")
    
    # Validate nested objects
    if "address" in data:
        address_ctx = context.nested("address")
        if "city" not in data["address"]:
            address_ctx.add_error("city", "Field is required")
    
    # Raise if any errors were found
    context.raise_if_errors()
```

### Integration with FastAPI

Built-in integration with FastAPI for consistent error responses:

```python
from fastapi import FastAPI
from uno.core.errors.fastapi_error_handlers import setup_error_handlers

app = FastAPI()
setup_error_handlers(app, include_tracebacks=False)  # Set to True in development
```

This will automatically convert `UnoError` exceptions to appropriate HTTP responses with the right status codes and structured error information.

## Error Categories and Severity

Errors are categorized for consistent handling across the application:

```python
from uno.core.errors import ErrorCategory, ErrorSeverity

# Error categories for classification
print(ErrorCategory.VALIDATION)  # For input validation errors
print(ErrorCategory.DATABASE)    # For database-related errors
print(ErrorCategory.AUTHORIZATION)  # For permission issues

# Error severity for prioritization
print(ErrorSeverity.WARNING)  # Minor issues
print(ErrorSeverity.ERROR)    # Standard errors
print(ErrorSeverity.CRITICAL)  # Critical failures
```

## Best Practices

1. **Single Exception Base Class**: Use `UnoError` or its subclasses for all application-specific exceptions.

2. **Appropriate Error Types**: Use the most specific error type for each situation:
   - `ValidationError` for input validation failures
   - `EntityNotFoundError` for missing resources
   - `AuthorizationError` for permission issues
   - `DatabaseError` for database-related issues
   - `ConfigurationError` for configuration problems
   - `DependencyError` for dependency resolution failures

3. **Result Pattern for Expected Errors**: Use the Result pattern for functions where errors are expected and should be handled functionally.

4. **Rich Context**: Always include relevant context with errors to aid in debugging and troubleshooting.

5. **Consistent Error Codes**: Register new error codes in the catalog with meaningful message templates and descriptions.

6. **FastAPI Integration**: Use the FastAPI error handlers to ensure consistent error responses across API endpoints.

7. **Structured Validation**: Use the validation utilities for complex input validation with clear, user-friendly error messages.