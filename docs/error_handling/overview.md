# Error Handling Framework

The Uno framework provides a comprehensive error handling system that combines structured errors, contextual information, error codes, functional error handling, and structured logging.

## Key Features

- **Structured Errors**: All errors have standardized attributes including error codes, messages, and contextual information.
- **Error Catalog**: Centralized registry of error codes with metadata like severity, category, and HTTP status codes.
- **Contextual Information**: Errors capture and maintain context to aid in debugging and provide better error messages.
- **Result Pattern**: Functional error handling using the Result/Either pattern (Success/Failure).
- **Validation Framework**: Structured validation with support for nested fields and multiple errors.
- **Structured Logging**: Context-aware logging that seamlessly integrates with the error handling system.
- **FastAPI Integration**: Automatic conversion of errors to HTTP responses with appropriate status codes.

## Core Components

### Error Classes

- `UnoError`: Base class for all framework errors with error codes and context.
- `ErrorCode`: Constants and utilities for working with error codes.
- `ErrorCategory`: Enum for categorizing errors (validation, authorization, etc.).
- `ErrorSeverity`: Enum for error severity levels (info, warning, error, critical, fatal).
- `ErrorInfo`: Metadata about an error code.
- `ValidationError`: Specialized error for validation failures with detailed error information.
- Additional specialized errors:
  - `EntityNotFoundError`: For when entities are not found.
  - `AuthorizationError`: For permission/authorization issues.
  - `ConcurrencyError`: For handling optimistic concurrency conflicts.
  - `DomainValidationError`: For domain-specific validation failures.

### Error Context

- `add_error_context(**context)`: Add to the current error context.
- `get_error_context()`: Get the current error context.
- `with_error_context`: Decorator that adds function parameters to error context.
- `with_async_error_context`: Async decorator/context manager for adding error context.

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

### FastAPI Integration

- `setup_error_handlers(app)`: Set up exception handlers for a FastAPI application.
- `ErrorHandlingMiddleware`: ASGI middleware for handling errors in FastAPI applications.
- `register_common_error_handlers(app)`: Register a set of common error handlers.

## Usage Examples

### Basic Error Handling

```python
from uno.core.errors import UnoError, ErrorCode

try:```

# Some operation that might fail
if not user_exists(user_id):```

raise UnoError(
    f"User with ID '{user_id}' not found",
    ErrorCode.RESOURCE_NOT_FOUND,
    user_id=user_id
)
```
```
except UnoError as e:```

# Handle the error
print(f"Error: {e.message} (Code: {e.error_code})")
print(f"Context: {e.context}")
```
```

### Using Specialized Error Types

```python
from uno.core.errors.base import EntityNotFoundError, ValidationError

# Using specialized error for entity not found
def get_user(user_id):```

user = db.find_user(user_id)
if not user:```

raise EntityNotFoundError(
    entity_type="User",
    entity_id=user_id
)
```
return user
```

# Using specialized error for validation
def validate_email(email):```

if "@" not in email:```

raise ValidationError(
    message="Invalid email format",
    field="email",
    value=email
)
```
```
```

### Using Error Context

```python
from uno.core.errors.base import with_error_context, with_async_error_context

# Add context with a decorator
@with_error_context
def process_order(order_id, user_id):```

# All arguments are added to error context automatically
# Any UnoError raised here will have order_id and user_id in context
return do_processing(order_id)
```

# Add context with a context manager
def update_user(user_id, data):```

with with_error_context(user_id=user_id, operation="update"):```

# Any UnoError raised here will have the context
return perform_update(user_id, data)
```
```

# With async functions
@with_async_error_context
async def process_payment(payment_id, amount):```

# Async context with all args added automatically
return await payment_provider.process(payment_id, amount)
```

async def verify_payment(payment_id):```

async with with_async_error_context(payment_id=payment_id, operation="verify"):```

# Context for this async block
return await payment_provider.verify(payment_id)
```
```
```

### Using Validation Context

```python
from uno.core.errors import ValidationContext

def validate_user(user):```

context = ValidationContext("User")
``````

```
```

if not user.username:```

context.add_error(
    field="username",
    message="Username is required",
    error_code="FIELD_REQUIRED"
)
```
``````

```
```

# Support for nested validation
email_context = context.nested("email")
if not user.email:```

email_context.add_error(
    field="",
    message="Email is required",
    error_code="FIELD_REQUIRED"
)
```
``````

```
```

# Raise ValidationError if there are any errors
context.raise_if_errors()
```
```

### Using the Result Pattern

```python
from uno.core.errors import Result, Success, Failure, of, failure

def create_user(user_data):```

# Validate user data
try:```

user = User(**user_data)
validate_user(user)
```
except ValidationError as e:```

return failure(e)
```
``````

```
```

# Create user
try:```

user_id = db.insert_user(user)
return of(user_id)
```
except Exception as e:```

return failure(UnoError(
    f"Failed to create user: {str(e)}",
    ErrorCode.INTERNAL_ERROR
))
```
```

# Usage
result = create_user(user_data)

if result.is_success:```

user_id = result.value
print(f"User created with ID: {user_id}")
```
else:```

error = result.error
print(f"Failed to create user: {error}")
```
```

### Converting Exception-Based Functions

```python
from uno.core.errors import from_exception

@from_exception
def get_user(user_id):```

user = db.get_user(user_id)
if not user:```

raise UnoError(
    f"User with ID '{user_id}' not found",
    ErrorCode.RESOURCE_NOT_FOUND,
    user_id=user_id
)
```
return user
```

# Now returns a Result
result = get_user(user_id)
```

### Using Result Pattern with Chaining

```python
from uno.core.result import Success, Failure, from_exception

# Using the Result pattern with chaining
result = (```

get_user(user_id)                      # Returns Result[User]
.map(lambda user: user.preferences)    # Transform to preferences if successful
.flat_map(load_preferences)            # Returns Result[Preferences]
.on_success(cache_preferences)         # Side effect on success
.on_failure(lambda e: log_error(e))    # Side effect on failure
```
)

# Handling the result
if result.is_success:```

preferences = result.value
return preferences
```
else:```

# Get a default or computed value on failure
return result.unwrap_or(default_preferences)
# Or compute a default from the error
# return result.unwrap_or_else(lambda e: get_default_for_error(e))
```
```

### Integrating with FastAPI

```python
from fastapi import FastAPI
from uno.core.fastapi_error_handlers import (```

setup_error_handlers, 
ErrorHandlingMiddleware,
register_common_error_handlers
```
)

app = FastAPI()

# Option 1: Set up exception handlers (recommended)
setup_error_handlers(app, include_tracebacks=(app.debug))

# Option 2: Use middleware approach
app.add_middleware(```

ErrorHandlingMiddleware,
include_tracebacks=(app.debug)
```
)

# Option 3: Register custom error handlers
register_common_error_handlers(```

app,
handlers={```

CustomError: custom_error_handler
```
}
```
)

# Your FastAPI endpoints can now raise UnoError
# and they will be converted to appropriate HTTP responses
@app.get("/users/{user_id}")
def get_user(user_id: str):```

user = db.get_user(user_id)
if not user:```

raise EntityNotFoundError(
    entity_type="User",
    entity_id=user_id
)
```
return user
```
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
try:```

# Some operation
pass
```
except Exception as e:```

logger.error("Failed to create user", exc_info=e)
```
```

## Example Error Response

When using the FastAPI integration, UnoError objects are automatically converted to HTTP responses with the appropriate status code:

```json
{
  "error": {```

"code": "DB-0001",
"message": "Database connection error: Failed to connect to database at 127.0.0.1:5432",
"category": "DATABASE",
"severity": "CRITICAL",
"context": {
  "host": "127.0.0.1",
  "port": "5432",
  "retry_count": "3"
}
```
  }
}
```

## Best Practices

1. **Always use error codes**: Make sure every error has a unique, descriptive error code.
2. **Use specialized error types**: Choose the most specific error type for your situation.
3. **Include context in errors**: Add relevant context information to errors to aid in debugging.
4. **Use the Result pattern for operations that can fail**: This makes error handling more explicit and functional.
5. **Register error codes in the catalog**: This provides additional metadata and ensures consistency.
6. **Use validation context for complex validation**: This enables collecting multiple validation errors.
7. **Use structured logging**: This integrates with the error handling system and provides better logs.
8. **Map internal errors to appropriate external errors**: Don't expose internal errors to clients.
9. **Use FastAPI integration**: Let the framework convert errors to appropriate HTTP responses.
10. **Be consistent with error handling**: Use the same patterns throughout your application.

## Error Categories

Uno provides several error categories to help classify errors:

| Category | Description | Example |
|----------|-------------|---------|
| VALIDATION | Input validation errors | Invalid email format |
| BUSINESS_RULE | Business rule violations | Insufficient inventory |
| AUTHORIZATION | Permission errors | User not authorized |
| AUTHENTICATION | Identity errors | Invalid credentials |
| DATABASE | Database-related errors | Connection failed |
| NETWORK | Network/connectivity errors | Timeout |
| RESOURCE | Resource availability errors | File not found |
| CONFIGURATION | System configuration errors | Missing config |
| INTEGRATION | External system integration errors | API unavailable |
| INTERNAL | Unexpected internal errors | Unhandled exception |
| INITIALIZATION | Initialization errors | Failed to start service |
| SERIALIZATION | Serialization/deserialization errors | Invalid JSON |
| DEPENDENCY | Dependency resolution errors | Missing dependency |
| EXECUTION | Execution/processing errors | Command failed |
| SECURITY | Security-related errors | Invalid token |
| CONFLICT | Resource conflicts | Duplicate record |
| NOT_FOUND | Resource not found | Entity doesn't exist |
| UNEXPECTED | Unexpected errors | Unknown error |

## See Also

- [Error Catalog](catalog.md) - Details of the error catalog system.
- [Result Pattern](result.md) - In-depth guide to the Result pattern.
- [Validation](validation.md) - Validation system details.
- [Logging](logging.md) - Structured logging integration.