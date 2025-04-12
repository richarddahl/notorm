# Error Handling Framework

The Uno framework provides a comprehensive error handling system that combines structured errors, contextual information, error codes, functional error handling, and structured logging.

## Key Features

- **Structured Errors**: All errors have standardized attributes including error codes, messages, and contextual information.
- **Error Catalog**: Centralized registry of error codes with metadata like severity, category, and HTTP status codes.
- **Contextual Information**: Errors capture and maintain context to aid in debugging and provide better error messages.
- **Result Pattern**: Functional error handling using the Result/Either pattern (Success/Failure).
- **Validation Framework**: Structured validation with support for nested fields and multiple errors.
- **Structured Logging**: Context-aware logging that seamlessly integrates with the error handling system.

## Core Components

### Error Classes

- `UnoError`: Base class for all framework errors with error codes and context.
- `ErrorCode`: Constants and utilities for working with error codes.
- `ErrorCategory`: Enum for categorizing errors (validation, authorization, etc.).
- `ErrorSeverity`: Enum for error severity levels (info, warning, error, critical, fatal).
- `ErrorInfo`: Metadata about an error code.
- `ValidationError`: Specialized error for validation failures with detailed error information.

### Error Context

- `add_error_context(**context)`: Add to the current error context.
- `get_error_context()`: Get the current error context.
- `with_error_context`: Decorator that adds function parameters to error context.

### Error Catalog

- `ErrorCatalog`: Interface to the error catalog.
- `register_error()`: Register an error code in the catalog.
- `get_error_code_info()`: Get information about an error code.
- `get_all_error_codes()`: Get all registered error codes.

### Result Pattern

- `Success[T]`: Represents a successful result with a value.
- `Failure[T]`: Represents a failed result with an error.
- `Result[T]`: Type alias for `Union[Success[T], Failure[T]]`.
- `of(value)`: Create a successful result.
- `failure(error)`: Create a failed result.
- `from_exception`: Decorator to convert exception-based functions to Result-based functions.
- `from_awaitable`: Convert an async operation to a Result.
- `combine(results)`: Combine multiple Results into a single Result.
- `combine_dict(results)`: Combine a dictionary of Results into a single Result.

### Validation

- `ValidationContext`: Context for collecting validation errors.
- `validate_fields()`: Utility for validating fields in a dictionary.
- `FieldValidationError`: Field-specific validation error.

### Logging

- `configure_logging()`: Configure logging for the application.
- `get_logger()`: Get a logger with context support.
- `LogConfig`: Configuration for logging.
- `add_logging_context()`: Add to the current logging context.
- `get_logging_context()`: Get the current logging context.
- `with_logging_context`: Decorator that adds function parameters to logging context.

## Usage Examples

### Basic Error Handling

```python
from uno.core.errors import UnoError, ErrorCode

try:
    # Some operation that might fail
    if not user_exists(user_id):
        raise UnoError(
            f"User with ID '{user_id}' not found",
            ErrorCode.RESOURCE_NOT_FOUND,
            user_id=user_id
        )
except UnoError as e:
    # Handle the error
    print(f"Error: {e.message} (Code: {e.error_code})")
    print(f"Context: {e.context}")
```

### Using Validation Context

```python
from uno.core.errors import ValidationContext

def validate_user(user):
    context = ValidationContext("User")
    
    if not user.username:
        context.add_error(
            field="username",
            message="Username is required",
            error_code="FIELD_REQUIRED"
        )
    
    # Support for nested validation
    email_context = context.nested("email")
    if not user.email:
        email_context.add_error(
            field="",
            message="Email is required",
            error_code="FIELD_REQUIRED"
        )
    
    # Raise ValidationError if there are any errors
    context.raise_if_errors()
```

### Using the Result Pattern

```python
from uno.core.errors import Result, Success, Failure, of, failure

def create_user(user_data):
    # Validate user data
    try:
        user = User(**user_data)
        validate_user(user)
    except ValidationError as e:
        return failure(e)
    
    # Create user
    try:
        user_id = db.insert_user(user)
        return of(user_id)
    except Exception as e:
        return failure(UnoError(
            f"Failed to create user: {str(e)}",
            ErrorCode.INTERNAL_ERROR
        ))

# Usage
result = create_user(user_data)

if result.is_success:
    user_id = result.value
    print(f"User created with ID: {user_id}")
else:
    error = result.error
    print(f"Failed to create user: {error}")
```

### Converting Exception-Based Functions

```python
from uno.core.errors import from_exception

@from_exception
def get_user(user_id):
    user = db.get_user(user_id)
    if not user:
        raise UnoError(
            f"User with ID '{user_id}' not found",
            ErrorCode.RESOURCE_NOT_FOUND,
            user_id=user_id
        )
    return user

# Now returns a Result
result = get_user(user_id)
```

### Structured Logging

```python
from uno.core.errors import configure_logging, get_logger, LogConfig, add_logging_context

# Configure logging
configure_logging(LogConfig(level="INFO", json_format=True))

# Get a logger
logger = get_logger(__name__)

# Add context to logs
add_logging_context(user_id="user123", operation="create_user")

# Log with context
logger.info("Creating new user")

# Log an error
try:
    # Some operation
    pass
except Exception as e:
    logger.error("Failed to create user", exc_info=e)
```

## Best Practices

1. **Always use error codes**: Make sure every error has a unique, descriptive error code.
2. **Include context in errors**: Add relevant context information to errors to aid in debugging.
3. **Use the Result pattern for operations that can fail**: This makes error handling more explicit and functional.
4. **Register error codes in the catalog**: This provides additional metadata and ensures consistency.
5. **Use validation context for complex validation**: This enables collecting multiple validation errors.
6. **Use structured logging**: This integrates with the error handling system and provides better logs.
7. **Map internal errors to appropriate external errors**: Don't expose internal errors to clients.