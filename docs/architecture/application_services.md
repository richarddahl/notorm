# Application Service Layer

The Application Service Layer in uno serves as a facade between the presentation layer (such as API controllers or UI) and the domain model. It orchestrates the execution of use cases by coordinating domain objects, repositories, and infrastructure services.

## Overview

Application services provide a higher-level API that abstracts the details of the domain model and the CQRS pattern, making it easier for clients to interact with the system. They handle cross-cutting concerns such as:

- Authentication and authorization
- Input validation
- Transaction management
- Error handling
- Logging
- Event publishing

## Key Components

### Service Context

The `ServiceContext` class encapsulates information about the current request context:

```python
context = ServiceContext(```

user_id="user123",
tenant_id="tenant456",
is_authenticated=True,
permissions=["products:read", "orders:write"],
request_metadata={"ip_address": "192.168.1.1"}
```
)
```

This context is passed to service methods and is used for authorization and contextual information.

### Application Service

The `ApplicationService` abstract base class provides common functionality for all application services:

```python
class ApplicationService(ABC):```

async def execute_command(self, command: Command, context: ServiceContext) -> CommandResult:```

# Handle authorization, validation, and execution
```
    
async def execute_query(self, query: Query, context: ServiceContext) -> QueryResult:```

# Handle authorization, validation, and execution
```
```
```

### Entity and Aggregate Services

Specialized services for working with entities and aggregates provide convenience methods for common operations:

```python
# Entity service for Product entities
product_service = EntityService(```

entity_type=Product,
read_permission="products:read",
write_permission="products:write"
```
)

# Using the service
result = await product_service.create(```

{"name": "Laptop", "price": 999.99},
context
```
)
```

### Service Registry

The `ServiceRegistry` provides a central place to register and retrieve services:

```python
# Get the service registry
registry = get_service_registry()

# Register a service
registry.register_entity_service(```

entity_type=Product,
read_permission="products:read",
write_permission="products:write"
```
)

# Get a service
product_service = registry.get("ProductService")
```

## Implementing Application Services

### Basic Implementation

To create a custom application service:

1. Inherit from `ApplicationService` or one of its specialized subclasses
2. Override methods as needed to provide custom behavior

```python
class OrderService(AggregateService[Order]):```

def __init__(```

self,
aggregate_type: Type[Order],
product_service: ProductService,
dispatcher: Optional[Dispatcher] = None,
logger: Optional[logging.Logger] = None,
read_permission: Optional[str] = None,
write_permission: Optional[str] = None
```
):```

super().__init__(
    aggregate_type=aggregate_type,
    dispatcher=dispatcher,
    logger=logger,
    read_permission=read_permission,
    write_permission=write_permission
)
self.product_service = product_service
```
``````

```
```

# Custom method for a specific use case
async def checkout(self, order_id: str, context: ServiceContext) -> CommandResult:```

command = CheckoutOrderCommand(order_id=order_id)
return await self.execute_command(command, context)
```
```
```

### Authorization

Application services handle authorization using the service context:

```python
def authorize_command(self, command: Command, context: ServiceContext) -> None:```

# Require authentication
context.require_authentication()
``````

```
```

# Require specific permission
if self.write_permission:```

context.require_permission(self.write_permission)
```
``````

```
```

# Custom authorization logic
if isinstance(command, UpdateOrderCommand):```

# Only allow updating orders in pending status
order = await self.get_by_id(command.order_id, context)
if order.status != "pending":
    raise AuthorizationError("Cannot update non-pending orders")
```
```
```

### Input Validation

Application services validate commands and queries before execution:

```python
def validate_command(self, command: Command, context: ServiceContext) -> None:```

if isinstance(command, CreateProductCommand):```

data = command.product_data
``````

```
```

# Validate required fields
if 'name' not in data or not data['name']:
    raise ValidationError("Product name is required")
``````

```
```

# Validate business rules
if data.get('price', 0) < 0:
    raise ValidationError("Product price cannot be negative")
```
```
```

### Composition

Application services can compose other services to implement complex use cases:

```python
async def place_order(```

self,
customer_id: str,
items: List[OrderItemDto],
context: ServiceContext
```
) -> CommandResult:```

# Validate customer
customer = await self.customer_service.get_by_id(customer_id, context)
if not customer:```

return CommandResult.failure(
    command_id=str(uuid4()),
    command_type="PlaceOrder",
    error="Customer not found",
    error_code="CUSTOMER_NOT_FOUND"
)
```
``````

```
```

# Validate products and inventory
for item in items:```

product = await self.product_service.get_by_id(item.product_id, context)
if not product:
    return CommandResult.failure(
        command_id=str(uuid4()),
        command_type="PlaceOrder",
        error=f"Product {item.product_id} not found",
        error_code="PRODUCT_NOT_FOUND"
    )
``````

```
```

# Check inventory
inventory = await self.inventory_service.get_inventory(
    product.id, context
)
if inventory.quantity < item.quantity:
    return CommandResult.rejection(
        command_id=str(uuid4()),
        command_type="PlaceOrder",
        error=f"Insufficient inventory for product {product.id}",
        error_code="INSUFFICIENT_INVENTORY"
    )
```
``````

```
```

# Create the order
order_data = {```

"customer_id": customer_id,
"items": [item.to_dict() for item in items],
"status": "pending"
```
}
``````

```
```

# Execute create order command
return await self.create(order_data, context)
```
```

## Benefits

The Application Service Layer provides several benefits:

1. **Simplified API**: Provides a higher-level API that is easier to use than direct CQRS commands and queries
2. **Cross-cutting concerns**: Centralizes handling of authentication, authorization, validation, etc.
3. **Use case orchestration**: Coordinates multiple domain objects and services to implement complex use cases
4. **Separation of concerns**: Keeps business logic in the domain model while handling application concerns at the service level
5. **Testing**: Makes unit testing easier by providing a clear entry point for use cases

## Best Practices

1. **Keep services focused**: Each service should have a clearly defined responsibility
2. **Don't put domain logic in services**: Domain logic belongs in the domain model
3. **Validate inputs early**: Validate inputs at the application service level before passing to domain objects
4. **Use service composition**: Compose services to implement complex use cases
5. **Return rich results**: Use command and query results to provide detailed information about successes and failures
6. **Handle errors gracefully**: Catch and handle exceptions at the service level, returning appropriate results
7. **Leverage the service context**: Use the service context for authorization and contextual information
8. **Log appropriately**: Log service activities and errors for monitoring and debugging

## Example

```python
# Create a service context with permissions
context = ServiceContext(```

user_id="user-1",
is_authenticated=True,
permissions=["products:read", "orders:write"]
```
)

# Use the product service to get a product
product_result = await product_service.get_by_id("product-123", context)
if not product_result.is_success:```

print(f"Error: {product_result.error}")
return
```

product = product_result.output

# Use the order service to create an order
order_result = await order_service.create(```

{```

"customer_id": "customer-456",
"items": [
    {
        "product_id": product.id,
        "quantity": 2,
        "price": product.price
    }
]
```
},
context
```
)

if order_result.is_success:```

order = order_result.output
print(f"Order created: {order.id}")
```
else:```

print(f"Failed to create order: {order_result.error}")
```
```

## Integration with API Layer

Application services integrate naturally with the API layer:

```python
@router.post("/orders")
async def create_order(```

order_data: OrderCreateDto,
request: Request
```
):```

# Create service context from request
context = ServiceContext(```

user_id=request.user.id,
is_authenticated=True,
permissions=request.user.permissions
```
)
``````

```
```

# Execute the use case
result = await order_service.create(order_data.to_dict(), context)
``````

```
```

# Convert result to API response
if result.is_success:```

return JSONResponse(
    status_code=201,
    content={"id": result.output.id}
)
```
else:```

return JSONResponse(
    status_code=400,
    content={"error": result.error, "code": result.error_code}
)
```
```
```

## Conclusion

The Application Service Layer provides a powerful abstraction layer that simplifies interaction with the domain model while addressing cross-cutting concerns like authentication, authorization, and validation. By coordinating domain objects and providing a higher-level API, it makes it easier to implement complex use cases while keeping the domain model focused on core business logic.