# Error Handling Framework

The Uno framework provides a comprehensive error handling system that emphasizes type safety, predictability, and contextual information.

## Overview

Effective error handling is critical for building robust applications. The Uno error handling framework uses a Result pattern to eliminate exceptions for expected error flows, combined with a structured approach to error reporting and handling.

## Key Components

### Result Pattern

The `Result` pattern separates success and failure paths:

```python
from uno.core.errors.result import Result, Success, Failure
from typing import Optional, List, TypeVar, Generic

T = TypeVar('T')
E = TypeVar('E')

# Function returning a Result
def find_user_by_email(email: str) -> Result[User, str]:
    user = user_repository.find_by_email(email)
    if user:
        return Success(user)
    else:
        return Failure(f"User with email {email} not found")

# Using a result
result = find_user_by_email("user@example.com")
if result.is_success:
    user = result.value
    # Process the user
else:
    error_message = result.error
    # Handle the error
```

The `Result` class provides:
- Type-safe success and failure paths
- Clear indication of outcome without exceptions
- Pattern matching support
- Monadic operations (map, bind, etc.)

### Error Classes

The framework defines a hierarchy of error classes:

```python
from uno.core.errors.base import BaseError, ErrorCode, ErrorCategory

# Define an error code
class UserErrors(ErrorCode):
    USER_NOT_FOUND = "USER_NOT_FOUND"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    INVALID_PASSWORD = "INVALID_PASSWORD"

# Use the error code in an error
class UserNotFoundError(BaseError):
    def __init__(self, email: str):
        super().__init__(
            f"User with email {email} not found",
            UserErrors.USER_NOT_FOUND,
            category=ErrorCategory.NOT_FOUND
        )
        self.email = email

# Raise the error
raise UserNotFoundError("user@example.com")
```

Key features of error classes:
- Structured error information
- Error codes for categorization
- Context data for debugging
- Standardized formatting

### Error Catalog

The error catalog provides a centralized registry of errors:

```python
from uno.core.errors.catalog import ErrorCatalog, register_error

# Register an error
@register_error(code="USER_NOT_FOUND", http_status=404)
class UserNotFoundError(BaseError):
    """Raised when a user is not found."""
    
    def __init__(self, email: str):
        super().__init__(
            f"User with email {email} not found",
            "USER_NOT_FOUND",
            category=ErrorCategory.NOT_FOUND
        )
        self.email = email

# Get error information from the catalog
error_info = ErrorCatalog.get_error_info("USER_NOT_FOUND")
print(f"HTTP status: {error_info.http_status}")
```

The error catalog enables:
- Centralized error management
- Consistent HTTP status code mapping
- Documentation generation
- Error traceability

### Result Pattern for Async Functions

For asynchronous code, use the async result helpers:

```python
from uno.core.errors.result import Result, Success, Failure, async_result

@async_result
async def find_user_by_email(email: str) -> Result[User, str]:
    user = await user_repository.find_by_email(email)
    if user:
        return Success(user)
    else:
        return Failure(f"User with email {email} not found")

# Using an async result
result = await find_user_by_email("user@example.com")
if result.is_success:
    user = result.value
    # Process the user
else:
    error_message = result.error
    # Handle the error
```

## Integration with FastAPI

The error framework integrates seamlessly with FastAPI:

```python
from uno.core.errors.fastapi_handlers import setup_error_handlers
from fastapi import FastAPI

app = FastAPI()
setup_error_handlers(app)

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    result = await user_service.get_user(user_id)
    if result.is_success:
        return result.value
    else:
        # The error handler will convert this to the appropriate HTTP response
        raise result.error
```

When using the error handlers, errors are automatically converted to appropriate HTTP responses:
- `NotFoundError` → 404 Not Found
- `ValidationError` → 422 Unprocessable Entity
- `AuthenticationError` → 401 Unauthorized
- `AuthorizationError` → 403 Forbidden
- etc.

## Error Logging

The error framework includes integrated logging:

```python
from uno.core.errors.logging import log_error, configure_error_logging
import logging

# Configure logging
logger = logging.getLogger(__name__)
configure_error_logging()

# Log an error
try:
    # Operation that might fail
    user = find_user(user_id)
except BaseError as e:
    # Log with context
    log_error(logger, e, extra={"user_id": user_id})
```

Key features of error logging:
- Structured logging with context
- Error code and category tracking
- Integration with monitoring systems
- Correlation ID support

## Result Pattern with Monads

The `Result` class supports monadic operations for cleaner code:

```python
from uno.core.errors.result import Result, Success, Failure

# Chain operations with bind
result = (
    find_user_by_email(email)
    .bind(lambda user: validate_password(user, password))
    .bind(lambda user: generate_token(user))
)

# Transform successful results with map
token_result = (
    find_user_by_email(email)
    .map(lambda user: user.generate_token())
)

# Recover from errors
result = (
    find_user_by_email(email)
    .recover(lambda error: create_guest_user())
)

# Combine multiple results
from uno.core.errors.result import combine_results

users_result = combine_results([
    find_user_by_email("user1@example.com"),
    find_user_by_email("user2@example.com"),
    find_user_by_email("user3@example.com")
])
```

## Domain-Specific Errors

Create domain-specific errors for clearer error handling:

```python
# Domain-specific error base class
class DomainError(BaseError):
    """Base class for domain errors."""
    pass

# User domain errors
class UserError(DomainError):
    """Base class for user-related errors."""
    pass

class UserNotFoundError(UserError):
    """Raised when a user is not found."""
    def __init__(self, user_id: str):
        super().__init__(
            f"User with ID {user_id} not found",
            "USER_NOT_FOUND",
            category=ErrorCategory.NOT_FOUND
        )
        self.user_id = user_id

# Order domain errors
class OrderError(DomainError):
    """Base class for order-related errors."""
    pass

class OrderNotFoundError(OrderError):
    """Raised when an order is not found."""
    def __init__(self, order_id: str):
        super().__init__(
            f"Order with ID {order_id} not found",
            "ORDER_NOT_FOUND",
            category=ErrorCategory.NOT_FOUND
        )
        self.order_id = order_id
```

## Best Practices

1. **Use the Result Pattern**: For expected errors, use the Result pattern instead of exceptions
2. **Define Error Codes**: Create enum-like classes for error codes to ensure consistency
3. **Include Context**: Always include relevant context in errors for debugging
4. **Domain-Specific Errors**: Create domain-specific error hierarchies
5. **Centralized Error Catalog**: Register errors in the central catalog
6. **Structured Logging**: Use the error logging utilities for consistent logging
7. **Proper Error Categories**: Use the appropriate error category (validation, not_found, etc.)
8. **Functional Style**: Use monadic operations for cleaner error handling

## Example Usage

### Service Layer

```python
from uno.core.errors.result import Result, Success, Failure
from uno.domain.entity import DomainService
from typing import Optional

class UserService(DomainService[User, UUID]):
    async def create_user(self, username: str, email: str, password: str) -> Result[User, UserError]:
        # Validate inputs
        if not self._is_valid_username(username):
            return Failure(InvalidUsernameError(username))
            
        # Check for existing user
        existing_user = await self._repository.find_by_email(email)
        if existing_user:
            return Failure(EmailAlreadyExistsError(email))
            
        # Create user
        user = User.create(username, email, self._hash_password(password))
        user = await self._repository.add(user)
        
        return Success(user)
```

### API Layer

```python
from fastapi import APIRouter, Depends, HTTPException
from uno.api.endpoint import BaseEndpoint
from uno.api.endpoint.response import DataResponse
from uno.core.di import get_dependency
from myapp.domain.services.user_service import UserService
from myapp.domain.errors import UserError
from pydantic import BaseModel

router = APIRouter()

class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    user_service: UserService = Depends(get_dependency(UserService))
) -> DataResponse[UserResponse]:
    result = await user_service.create_user(
        request.username,
        request.email,
        request.password
    )
    
    if result.is_success:
        return DataResponse(data=UserResponse(
            id=str(result.value.id),
            username=result.value.username,
            email=result.value.email
        ))
    else:
        # Let the error handler convert this to an appropriate HTTP response
        raise result.error
```

## Error Categories

The framework defines standard error categories:

| Category | Description | HTTP Status |
|----------|-------------|-------------|
| `VALIDATION` | Input validation errors | 422 |
| `NOT_FOUND` | Resource not found | 404 |
| `CONFLICT` | Resource conflict | 409 |
| `AUTHENTICATION` | Authentication failures | 401 |
| `AUTHORIZATION` | Authorization failures | 403 |
| `BUSINESS_RULE` | Business rule violations | 422 |
| `SYSTEM` | System/internal errors | 500 |
| `EXTERNAL` | External service errors | 502 |
| `TIMEOUT` | Operation timeout | 504 |
| `INPUT` | Invalid input data | 400 |

## Related Components

- [Result Pattern](result.md): Detailed explanation of the Result pattern
- [Error Catalog](catalog.md): Working with the error catalog
- [Validation Framework](../validation.md): Input validation
- [API Error Handling](../../api/endpoint/error_handling.md): API-specific error handling