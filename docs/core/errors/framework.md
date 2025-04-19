# Error Framework

The UNO Error Framework provides a comprehensive approach to error handling across all layers of the application. It standardizes error definitions, adds rich context to errors, and simplifies error handling in a consistent way.

## Overview

The error framework has several key components:

1. **Error Catalog**: A centralized registry of error definitions
2. **Error Context**: Rich contextual information about errors
3. **Standard Error Classes**: Hierarchical set of error types
4. **Result Pattern**: Consistent result objects for operations that can fail
5. **Error Logging**: Structured logging for errors with context

## Error Catalog

The error catalog provides a central registry for all error definitions in the application. This enables consistent error codes, messages, and categorization.

```python
from uno.core.errors.framework import register_error, ErrorCategory, ErrorSeverity

# Register an application-specific error
register_error(
    code="PRODUCT_OUT_OF_STOCK",
    message_template="Product {product_id} is out of stock. Available: {available}, requested: {requested}",
    category=ErrorCategory.BUSINESS,
    severity=ErrorSeverity.WARNING,
    http_status_code=400,
    help_text="Check product availability before placing an order.",
)

# Create an error instance
from uno.core.errors.framework import create_error

error = create_error(
    code="PRODUCT_OUT_OF_STOCK",
    params={
        "product_id": "123",
        "available": 5,
        "requested": 10
    }
)
```

## Error Context

Error context provides rich information about the circumstances in which an error occurred:

```python
from uno.core.errors.framework import get_error_context

# Get the current error context
context = get_error_context()

# Add request information
context.request_id = request.headers.get("X-Request-ID")
context.path = request.url.path
context.method = request.method
context.user_id = request.headers.get("X-User-ID")

# Add application information
context.application = "my-app"
context.component = "order-service"
```

## Standard Error Classes

The framework provides a hierarchy of standard error classes:

- **FrameworkError**: Base class for all errors
  - **ValidationError**: Errors related to input validation
  - **DatabaseError**: Errors related to database operations
  - **AuthenticationError**: Errors related to authentication
  - **AuthorizationError**: Errors related to authorization
  - **NotFoundError**: Errors related to resources not found
  - **ConflictError**: Errors related to resource conflicts
  - **RateLimitError**: Errors related to rate limiting
  - **ServerError**: Errors related to server issues

```python
from uno.core.errors.framework import ValidationError, NotFoundError

# Create a validation error
validation_error = ValidationError(
    "Quantity must be positive",
    code="INVALID_QUANTITY",
    field="quantity"
)

# Create a not found error
not_found_error = NotFoundError(
    "Product not found",
    code="PRODUCT_NOT_FOUND"
)
```

## Result Pattern

The framework integrates with the Result pattern for operations that can fail:

```python
from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.framework import ValidationError, ErrorCatalog

def check_stock(product_id, requested_quantity):
    """Check if there's enough stock for the requested quantity."""
    if requested_quantity <= 0:
        return Failure(
            ValidationError(
                "Requested quantity must be positive",
                field="requested_quantity",
            )
        )
    
    product = get_product(product_id)
    if product is None:
        return ErrorCatalog.to_result(
            code="PRODUCT_NOT_FOUND",
            params={"product_id": product_id}
        )
    
    if requested_quantity <= product.stock:
        return Success(True)
    
    return ErrorCatalog.to_result(
        code="PRODUCT_OUT_OF_STOCK",
        params={
            "product_id": product_id,
            "available": product.stock,
            "requested": requested_quantity,
        }
    )
```

## Error Logging

The framework provides structured logging for errors with context:

```python
from uno.core.errors.framework import log_error

# Log an error with context
error_log = log_error(
    error,
    include_traceback=True,
    context=context
)

# Access error log information
print(error_log.error.code)
print(error_log.error.message)
print(error_log.context)
```

## HTTP Integration

The error framework integrates with HTTP endpoints through middleware:

```python
from fastapi import FastAPI, Request, Response
from uno.core.errors.framework import get_error_context, log_error

app = FastAPI()

@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Middleware for handling errors and adding context."""
    try:
        # Create error context with request information
        context = get_error_context()
        context.request_id = request.headers.get("X-Request-ID")
        context.path = request.url.path
        context.method = request.method
        
        # Process the request
        return await call_next(request)
    except Exception as e:
        # Log the error with context
        error_log = log_error(e, include_traceback=True, context=context)
        
        # Return error response
        if hasattr(e, "status_code"):
            status_code = e.status_code
        else:
            status_code = 500
        
        return Response(
            content=f'{{"error": "{str(e)}", "code": "{getattr(e, "code", "INTERNAL_ERROR")}"}}',
            status_code=status_code,
            media_type="application/json",
        )
```

## Working with the Result Pattern

The error framework works seamlessly with the Result pattern:

```python
from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.framework import NotFoundError, ValidationError

async def get_order(order_id: str) -> Result[Order]:
    """Get an order by ID."""
    if not order_id:
        return Failure(
            ValidationError(
                "Order ID cannot be empty",
                field="order_id"
            )
        )
    
    order = await db.get_order(order_id)
    if not order:
        return Failure(
            NotFoundError(
                f"Order with ID {order_id} not found",
                code="ORDER_NOT_FOUND"
            )
        )
    
    return Success(order)

# Using the result
result = await get_order("123")
if isinstance(result, Success):
    order = result.value
    # Do something with the order
else:
    error = result.error
    # Handle the error
```

## Best Practices

Here are some best practices for using the error framework:

1. **Use the Catalog**: Register all error codes in the catalog for consistency
2. **Be Specific**: Use the most specific error class for each situation
3. **Add Context**: Always include context with errors for better debugging
4. **Use Proper Categories**: Categorize errors correctly for better organization
5. **Include Help Text**: Provide helpful guidance for resolving errors
6. **Return Results**: Use the Result pattern for operations that can fail
7. **Log Appropriately**: Log errors with the appropriate severity
8. **Centralize HTTP Handling**: Use middleware for consistent error responses

## Complete Example

See the `uno.core.errors.examples.error_framework_example` module for a complete example of how to use the error framework in a real application.