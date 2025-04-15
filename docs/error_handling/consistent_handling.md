# Consistent Error Handling Across Application Layers

This document provides guidance for implementing consistent error handling across all layers of applications built with uno.

## Core Principles

1. **Explicit Error Types**: Use specific error types that clearly convey the nature of the error
2. **Domain-Specific Error Codes**: Use well-defined error codes categorized by domain
3. **Contextual Information**: Include relevant context with every error
4. **Functional Error Handling**: Use the Result pattern for operations that can fail
5. **Clean API Boundaries**: Transform internal errors to appropriate external errors at API boundaries
6. **Consistent Recovery Strategies**: Apply consistent error recovery strategies by error type
7. **Proper Error Propagation**: Handle or propagate errors appropriately at each layer

## Application Layers

A typical application has these layers, each with specific error handling requirements:

1. **API Layer**: HTTP/REST endpoints, API controllers, middleware
2. **Application Layer**: Application services, commands, queries, use cases
3. **Domain Layer**: Domain model, business rules, entities, value objects
4. **Infrastructure Layer**: Repositories, external services, database access, messaging

## Error Handling Strategies by Layer

### API Layer

The API layer is the boundary between your application and external clients. It must:

1. **Transform Internal Errors**:
   - Map internal errors to appropriate HTTP status codes
   - Sanitize error messages to avoid exposing sensitive information
   - Provide consistent error response format

2. **Handle Validation Errors**:
   - Use automatic request validation with well-defined error responses
   - Include field-level validation details

3. **Use Middlewares**:
   - Implement error handling middleware to catch unhandled exceptions
   - Log all errors at the API boundary
   - Transform to appropriate HTTP responses

#### Example: FastAPI Error Handling

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from uno.core.errors import UnoError, ErrorCode, EntityNotFoundError, AuthorizationError

app = FastAPI()

@app.exception_handler(UnoError)
async def uno_error_handler(request: Request, exc: UnoError):
    """Handle UnoError exceptions."""
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "category": exc.category.name if exc.category else None,
                "details": exc.context
            }
        }
    )

@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    """Handle EntityNotFoundError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "entity_type": exc.context.get("entity_type"),
                "entity_id": exc.context.get("entity_id")
            }
        }
    )

# Endpoint that uses error handling
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        return await user_service.get_user(user_id)
    except EntityNotFoundError as e:
        # Will be handled by the exception handler
        raise
    except Exception as e:
        # Convert unexpected errors to a standardized internal error
        raise UnoError(
            f"Unexpected error retrieving user: {str(e)}",
            ErrorCode.INTERNAL_ERROR,
            user_id=user_id
        )
```

### Application Layer

The application layer coordinates domain operations and external services. It should:

1. **Use the Result Pattern**:
   - Return `Result[T]` for operations that can fail
   - Avoid throwing exceptions for expected failure cases
   - Convert domain-specific errors to application-level errors when appropriate

2. **Add Application Context**:
   - Enrich errors with application-level context
   - Use `with_error_context` to add operation details

3. **Handle Service Integration**:
   - Wrap external service calls to normalize error handling
   - Implement retry policies for transient errors

#### Example: Application Service with Result Pattern

```python
from uno.core.errors import Result, Success, Failure, UnoError, ErrorCode, with_error_context

class UserService:
    def __init__(self, user_repository, email_service):
        self.user_repository = user_repository
        self.email_service = email_service

    @with_error_context
    async def create_user(self, user_data: dict) -> Result[str]:
        """Create a new user and send welcome email."""
        # Validate input
        validation_result = self._validate_user_data(user_data)
        if validation_result.is_failure:
            return validation_result

        # Create user
        try:
            user_id = await self.user_repository.create(user_data)
        except UnoError as e:
            return Failure(e)
        except Exception as e:
            return Failure(UnoError(
                f"Failed to create user: {str(e)}",
                ErrorCode.INTERNAL_ERROR,
                user_data=user_data
            ))

        # Send welcome email
        email_result = await self._send_welcome_email(user_id, user_data["email"])
        if email_result.is_failure:
            # Log but don't fail the operation for non-critical errors
            logger.warning(f"Failed to send welcome email: {email_result.error}")

        return Success(user_id)

    def _validate_user_data(self, user_data: dict) -> Result[None]:
        # Validation logic
        if not user_data.get("email"):
            return Failure(UnoError(
                "Email is required",
                ErrorCode.VALIDATION_ERROR,
                field="email"
            ))
        return Success(None)

    async def _send_welcome_email(self, user_id: str, email: str) -> Result[None]:
        try:
            await self.email_service.send_welcome(email)
            return Success(None)
        except Exception as e:
            return Failure(UnoError(
                f"Failed to send welcome email: {str(e)}",
                ErrorCode.API_INTEGRATION_ERROR,
                user_id=user_id,
                email=email
            ))
```

### Domain Layer

The domain layer contains business rules and core entities. It should:

1. **Use Domain-Specific Errors**:
   - Define and use specialized error types for domain concepts
   - Include domain-specific context in errors

2. **Enforce Invariants**:
   - Raise errors when domain invariants are violated
   - Use clear, business-oriented error messages

3. **Validate at Boundaries**:
   - Validate all inputs to domain operations
   - Use explicit validation that returns all validation errors at once

#### Example: Domain Model with Specialized Errors

```python
from uno.core.errors import UnoError, ErrorCode, DomainValidationError, AggregateInvariantViolationError

class Order:
    def __init__(self, order_id: str, customer_id: str, items: list):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items
        self.status = "draft"
        self._validate()

    def _validate(self):
        """Validate the order."""
        if not self.items:
            raise DomainValidationError(
                "Order must have at least one item",
                entity_name="Order",
                order_id=self.order_id
            )

    def submit(self):
        """Submit the order for processing."""
        if self.status != "draft":
            raise AggregateInvariantViolationError(
                f"Cannot submit order in {self.status} status",
                aggregate_name="Order",
                aggregate_id=self.order_id,
                current_status=self.status,
                expected_status="draft"
            )

        # Check inventory availability
        unavailable_items = self._check_inventory()
        if unavailable_items:
            raise DomainValidationError(
                "Some items are unavailable",
                entity_name="Order",
                unavailable_items=unavailable_items
            )

        self.status = "submitted"
        return True

    def _check_inventory(self):
        # Inventory check logic here
        return []
```

### Infrastructure Layer

The infrastructure layer implements technical concerns. It should:

1. **Map External Errors**:
   - Convert external service errors to application-specific errors
   - Add context about the external service and operation

2. **Implement Resilience**:
   - Use retry mechanisms for transient errors
   - Implement circuit breakers for failing services

3. **Provide Detailed Errors**:
   - Include technical details needed for troubleshooting
   - Log detailed error information

#### Example: Repository with Error Mapping

```python
from uno.core.errors import UnoError, ErrorCode, EntityNotFoundError
import psycopg
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class UserRepository:
    def __init__(self, db_session):
        self.db_session = db_session

    async def get_by_id(self, user_id: str):
        """Get a user by ID."""
        try:
            result = await self.db_session.execute(
                "SELECT * FROM users WHERE id = %s", (user_id,)
            )
            user = result.fetchone()
            if not user:
                raise EntityNotFoundError("User", user_id)
            return user
        except psycopg.DatabaseError as e:
            # Map database errors to application errors
            if "deadlock detected" in str(e).lower():
                raise UnoError(
                    f"Database deadlock: {str(e)}",
                    ErrorCode.DB_DEADLOCK_ERROR,
                    user_id=user_id
                )
            raise UnoError(
                f"Database error: {str(e)}",
                ErrorCode.DB_QUERY_ERROR,
                user_id=user_id,
                query="get_user_by_id"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(UnoError),
        retry_error_callback=lambda retry_state: retry_state.outcome.result()
    )
    async def create(self, user_data: dict):
        """Create a new user with retry for transient errors."""
        try:
            result = await self.db_session.execute(
                """
                INSERT INTO users (name, email, status)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_data["name"], user_data["email"], "active")
            )
            await self.db_session.commit()
            return result.fetchone()[0]
        except psycopg.IntegrityError as e:
            await self.db_session.rollback()
            if "unique constraint" in str(e).lower() and "email" in str(e).lower():
                raise UnoError(
                    "User with this email already exists",
                    ErrorCode.DB_INTEGRITY_ERROR,
                    field="email",
                    value=user_data.get("email")
                )
            raise UnoError(
                f"Database integrity error: {str(e)}",
                ErrorCode.DB_INTEGRITY_ERROR,
                fields=user_data.keys()
            )
        except psycopg.DatabaseError as e:
            await self.db_session.rollback()
            # Only retry certain types of errors
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                error = UnoError(
                    f"Transient database error: {str(e)}",
                    ErrorCode.DB_CONNECTION_ERROR,
                    retry_allowed=True
                )
            else:
                error = UnoError(
                    f"Database error: {str(e)}",
                    ErrorCode.DB_QUERY_ERROR,
                    retry_allowed=False
                )
            raise error
```

## Error Handling Patterns

### Pattern 1: Result Pattern for Expected Failures

Use the Result pattern for operations where failure is an expected outcome:

```python
from uno.core.errors import Result, Success, Failure, UnoError, ErrorCode

def find_user(user_id: str) -> Result[User]:
    user = db.get_user(user_id)
    if not user:
        return Failure(UnoError(
            f"User not found: {user_id}",
            ErrorCode.RESOURCE_NOT_FOUND,
            user_id=user_id
        ))
    return Success(user)

# Using the Result
result = find_user("user123")
if result.is_success:
    user = result.value
    # Use the user
else:
    # Handle error
    error = result.error
    print(f"Error: {error.message}")
```

### Pattern 2: Exceptions for Unexpected Failures

Use exceptions for truly exceptional conditions that shouldn't be part of the normal flow:

```python
def process_payment(payment_id: str) -> None:
    try:
        # Process payment logic
        pass
    except ConnectionError as e:
        # Wrap external exceptions in application-specific exceptions
        raise UnoError(
            f"Payment gateway connection error: {str(e)}",
            ErrorCode.NETWORK,
            payment_id=payment_id
        )
```

### Pattern 3: Validation Context for Multiple Errors

Use validation context to collect multiple validation errors:

```python
from uno.core.errors import ValidationContext

def validate_order(order_data: dict) -> None:
    context = ValidationContext("Order")
    
    # Check required fields
    for field in ["customer_id", "items", "shipping_address"]:
        if field not in order_data:
            context.add_error(field, f"{field} is required", "FIELD_REQUIRED")
    
    # Validate items
    if "items" in order_data and isinstance(order_data["items"], list):
        items_context = context.nested("items")
        for i, item in enumerate(order_data["items"]):
            item_context = items_context.nested(str(i))
            if "product_id" not in item:
                item_context.add_error("product_id", "Product ID is required", "FIELD_REQUIRED")
            if "quantity" not in item:
                item_context.add_error("quantity", "Quantity is required", "FIELD_REQUIRED")
            elif not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                item_context.add_error("quantity", "Quantity must be a positive integer", "INVALID_VALUE")
    
    # Raise ValidationError with all validation errors
    context.raise_if_errors()
```

### Pattern 4: Error Context Propagation

Use error context to maintain contextual information across the call stack:

```python
from uno.core.errors import with_error_context, add_error_context

@with_error_context
def process_order(order_id: str, user_id: str) -> None:
    # Context automatically includes order_id and user_id
    order = get_order(order_id)
    
    # Add more context information
    add_error_context(order_status=order.status)
    
    # Any UnoError raised here or in called functions will include the context
    process_payment(order.payment_id)
```

### Pattern 5: Retry for Transient Errors

Implement retry mechanisms for operations that might experience transient failures:

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from uno.core.errors import UnoError, ErrorCode

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry_error_callback=lambda retry_state: retry_state.outcome.result()
)
def fetch_external_api(resource_id: str) -> dict:
    try:
        response = requests.get(f"https://api.example.com/resources/{resource_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise UnoError(
            "API request timeout",
            ErrorCode.TIMEOUT_ERROR,
            resource_id=resource_id,
            retry_allowed=True
        )
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 429:
            raise UnoError(
                "API rate limit exceeded",
                ErrorCode.API_RATE_LIMIT_ERROR,
                resource_id=resource_id,
                retry_allowed=True
            )
        elif status_code == 404:
            raise UnoError(
                f"Resource not found: {resource_id}",
                ErrorCode.RESOURCE_NOT_FOUND,
                resource_id=resource_id,
                retry_allowed=False
            )
        else:
            raise UnoError(
                f"API error: {str(e)}",
                ErrorCode.API_INTEGRATION_ERROR,
                resource_id=resource_id,
                status_code=status_code,
                retry_allowed=status_code >= 500  # Only retry server errors
            )
```

## Error Handling Best Practices

### 1. Be Specific About Error Types

Use the most specific error type for the situation:

```python
# Good: Specific error with context
raise EntityNotFoundError("User", user_id)

# Bad: Generic error with vague message
raise Exception(f"Couldn't find user {user_id}")
```

### 2. Include Relevant Context Information

Always include context that will help diagnose the issue:

```python
# Good: Includes detailed context
raise UnoError(
    "Payment processing failed",
    ErrorCode.API_INTEGRATION_ERROR,
    payment_id=payment.id,
    amount=payment.amount,
    provider="stripe",
    error_code=stripe_error.code
)

# Bad: Missing important context
raise UnoError("Payment failed", ErrorCode.API_INTEGRATION_ERROR)
```

### 3. Use Consistent Error Codes

Use predefined error codes from the error catalog:

```python
# Good: Uses predefined error code
raise UnoError("User not authorized", ErrorCode.AUTHORIZATION_ERROR)

# Bad: Inconsistent or custom string codes
raise UnoError("User not authorized", "AUTH_FAIL_001")
```

### 4. Handle Errors at the Appropriate Level

Handle errors at the level where you have enough context to handle them properly:

```python
# Good: Handle database errors in the repository layer
try:
    result = await session.execute(query)
except psycopg.DatabaseError as e:
    raise UnoError(f"Database error: {str(e)}", ErrorCode.DB_QUERY_ERROR)

# Bad: Allow low-level exceptions to propagate to high-level code
# This loses context and makes proper handling difficult
```

### 5. Transform Errors at API Boundaries

Transform internal errors to appropriate external errors at API boundaries:

```python
# Good: Map internal errors to appropriate HTTP responses
@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={"error": {"code": exc.error_code, "message": exc.message}}
    )

# Bad: Exposing internal exception details
# @app.exception_handler(Exception)
# async def exception_handler(request, exc):
#     return JSONResponse(
#         status_code=500,
#         content={"error": str(exc), "traceback": traceback.format_exc()}
#     )
```

### 6. Use Functional Error Handling Where Appropriate

Use the Result pattern for operations that can fail in expected ways:

```python
# Good: Uses Result pattern for operation that can fail
def authenticate_user(email: str, password: str) -> Result[User]:
    user = find_user_by_email(email)
    if not user:
        return Failure(UnoError("Invalid credentials", ErrorCode.AUTHENTICATION_ERROR))
    
    if not verify_password(user, password):
        return Failure(UnoError("Invalid credentials", ErrorCode.AUTHENTICATION_ERROR))
    
    return Success(user)

# Using the Result
result = authenticate_user(email, password)
if result.is_success:
    user = result.value
    # Create session, etc.
else:
    # Handle authentication failure
```

### 7. Log Errors Appropriately

Log errors with appropriate severity and context:

```python
try:
    process_order(order_id)
except UnoError as e:
    # Determine log level based on error severity
    if e.severity == ErrorSeverity.CRITICAL:
        logger.critical(f"Critical error: {e.message}", extra=e.context)
    elif e.severity == ErrorSeverity.ERROR:
        logger.error(f"Error: {e.message}", extra=e.context)
    else:
        logger.warning(f"Warning: {e.message}", extra=e.context)
```

### 8. Document Error Handling Behavior

Document how errors are handled for each component:

```python
class PaymentService:
    """
    Handles payment processing.
    
    Raises:
        PaymentProcessingError: When payment processing fails due to gateway issues
        PaymentValidationError: When payment data is invalid
        PaymentDeclinedError: When payment is declined by the processor
    
    Returns Result[Transaction] for operations that can fail in expected ways.
    """
```

### 9. Implement Consistent Recovery Strategies

Implement appropriate recovery strategies based on error type:

```python
async def process_payment(payment_id: str) -> Result[Transaction]:
    try:
        return await payment_gateway.process(payment_id)
    except UnoError as e:
        if e.retry_allowed:
            # Retry logic for transient errors
            return await retry_with_backoff(process_payment, payment_id)
        else:
            # For non-retryable errors, fail immediately
            return Failure(e)
```

### 10. Test Error Scenarios

Write tests that verify error handling behaves as expected:

```python
@pytest.mark.asyncio
async def test_user_not_found():
    # Arrange
    user_id = "nonexistent_user"
    
    # Act
    result = await user_service.get_user(user_id)
    
    # Assert
    assert result.is_failure
    assert result.error.error_code == ErrorCode.RESOURCE_NOT_FOUND
    assert result.error.context["entity_type"] == "User"
    assert result.error.context["entity_id"] == user_id
```

## See Also

- [Error Handling Overview](overview.md) - Core error handling concepts
- [Expanded Error Catalog](expanded_catalog.md) - Comprehensive error code catalog
- [Result Pattern](result.md) - Functional error handling details
- [Error Monitoring](monitoring.md) - Monitoring and analyzing errors