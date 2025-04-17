# Domain Service API Integration

This guide explains how to use the unified domain service pattern with API endpoints, allowing you to create consistent, maintainable API endpoints that integrate directly with your domain logic.

## Overview

The domain service API integration provides a bridge between your domain services and API endpoints, ensuring proper separation of concerns while allowing seamless integration. The key components include:

1. **Domain Services** - Encapsulate domain logic and business rules
2. **Service Endpoint Adapters** - Convert between API models and domain models
3. **Service Endpoint Factory** - Create standardized endpoints for domain services
4. **Entity Service Endpoints** - Create CRUD endpoints for domain entities

This approach ensures:

- **Separation of concerns** - Domain logic stays in domain services
- **Consistent error handling** - Domain errors are properly mapped to HTTP responses
- **Type safety** - Input and output models are properly validated
- **Reusability** - Domain services can be used in multiple contexts
- **Testability** - Domain logic can be tested independently of API endpoints

## Getting Started

### 1. Define Domain Services

Create domain services that handle business operations:

```python
class CreateUserService(DomainService[CreateUserInput, UserOutput, UnitOfWork]):
    """Service for creating new users."""
    
    async def _execute_internal(self, input_data: CreateUserInput) -> Result[UserOutput]:
        # Implement business logic
        # ...
        return Success(output)
```

### 2. Set Up API Integration

Configure domain service endpoint factory:

```python
from uno.api.service_endpoint_factory import get_domain_service_endpoint_factory

def setup_domain_endpoints(app: FastAPI) -> None:
    # Create router for domain endpoints
    router = APIRouter(prefix="/api/v1", tags=["Domain"])
    
    # Get endpoint factory
    endpoint_factory = get_domain_service_endpoint_factory()
    
    # Create endpoints for domain services
    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=CreateUserService,
        path="/users",
        method="POST",
        summary="Create User",
        description="Create a new user in the system",
        response_model=UserOutput,
        status_code=201
    )
```

## Key Components

### Domain Service Adapter

The `DomainServiceAdapter` acts as a bridge between domain services and API endpoints, handling:

- Converting between API and domain models
- Error handling and HTTP response mapping
- Logging and diagnostics

```python
from uno.api.service_endpoint_adapter import DomainServiceAdapter

adapter = DomainServiceAdapter(
    service=service,
    input_model=input_model,
    output_model=output_model
)

# Execute the domain service via the adapter
result = await adapter.execute(input_data)
```

### Domain Service Endpoint Factory

The `DomainServiceEndpointFactory` creates FastAPI endpoints for domain services:

```python
from uno.api.service_endpoint_factory import DomainServiceEndpointFactory

factory = DomainServiceEndpointFactory()

# Create an endpoint for a domain service
factory.create_domain_service_endpoint(
    app=app,  # or router
    service_class=MyDomainService,
    path="/my-endpoint",
    method="POST"
)
```

### Entity Service Endpoints

For CRUD operations on domain entities, use the entity service endpoints:

```python
# Create CRUD endpoints for an entity
factory.create_entity_service_endpoints(
    app=app,  # or router
    entity_type=User,
    path_prefix="/users",
    tags=["Users"]
)
```

This will create standardized endpoints for:
- `POST /users` - Create
- `GET /users/{id}` - View
- `GET /users` - List
- `PUT /users/{id}` - Update
- `DELETE /users/{id}` - Delete

## Error Handling

Domain errors are automatically mapped to appropriate HTTP responses:

- `NOT_FOUND` → 404 Not Found
- `UNAUTHORIZED` → 401 Unauthorized
- `FORBIDDEN` → 403 Forbidden
- `VALIDATION_ERROR` → 400 Bad Request
- `INTERNAL_ERROR` → 500 Internal Server Error
- `CONFLICT` → 409 Conflict

## Complete Example

A complete implementation example is available at:

```python
# Source file: /src/uno/api/service_endpoint_example.py
```

This example demonstrates:
1. Domain model implementation (entities and aggregates)
2. Domain services for business operations
3. API integration using service endpoint factory
4. CRUD endpoints for entities
5. Event handling integration

To run the example:

```bash
python -m src.uno.api.service_endpoint_example
```

Then visit [http://localhost:8000/docs](http://localhost:8000/docs) to see the OpenAPI documentation.

## Best Practices

1. **Keep domain logic in domain services** - Use services to encapsulate business logic
2. **Use input/output models** - Define clear interfaces for domain services
3. **Separate domain and API models** - Don't expose domain models directly
4. **Use Result pattern** - Return Success/Failure instead of raising exceptions
5. **Handle domain events** - Use event handlers for side effects
6. **Use proper HTTP methods** - GET for queries, POST for commands
7. **Document API endpoints** - Use FastAPI's built-in documentation features
8. **Test at both levels** - Test domain services separately from API endpoints

## Advanced Use Cases

### Custom Error Handling

If you need custom error handling:

```python
def custom_error_handler(result: Result) -> None:
    # Handle specific errors
    if not result.is_success:
        error = result.error
        if error_requires_custom_handling(error):
            # Custom error handling
            raise HTTPException(...)

# Use the custom error handler with the factory
factory = DomainServiceEndpointFactory(error_handler=custom_error_handler)
```

### Custom Dependencies

To add custom dependencies to endpoints:

```python
factory.create_domain_service_endpoint(
    service_class=MyService,
    path="/endpoint",
    dependencies=[Depends(my_dependency)]
)
```

### Custom Status Codes

Control HTTP status codes for success responses:

```python
factory.create_domain_service_endpoint(
    service_class=CreateUserService,
    path="/users",
    status_code=201  # Created status code
)
```