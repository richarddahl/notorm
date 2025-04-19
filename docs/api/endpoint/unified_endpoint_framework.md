# Unified Endpoint Framework

The UNO Framework provides a comprehensive, unified approach to creating API endpoints that integrate seamlessly with domain services. This guide explains the architecture, components, and usage patterns of the unified endpoint framework.

## Overview

The unified endpoint framework follows clean architectural principles, separating concerns into discrete layers:

1. **Domain Layer**: Contains business logic, entities, and domain services
2. **Application Layer**: Orchestrates domain operations through application services
3. **API Layer**: Exposes domain and application services through HTTP endpoints

The framework provides standardized endpoint classes for different API patterns:

- **BaseEndpoint**: Foundation for all endpoint types
- **CrudEndpoint**: Standard CRUD operations for entity types
- **QueryEndpoint**: Read operations with optional filtering
- **CommandEndpoint**: Write operations with side effects
- **CqrsEndpoint**: Combined Command-Query Responsibility Segregation

## Key Components

### Endpoint Base Classes

```python
from uno.api.endpoint import BaseEndpoint, CrudEndpoint, QueryEndpoint, CommandEndpoint

# Basic endpoint
endpoint = BaseEndpoint(
    router=router,
    tags=["Products"]
)

# CRUD endpoint for entity operations
crud_endpoint = CrudEndpoint(
    service=product_service,
    create_model=ProductCreateDTO,
    response_model=ProductResponseDTO,
    update_model=ProductUpdateDTO,
    path="/products",
    tags=["Products"]
)

# Query endpoint for read operations
query_endpoint = QueryEndpoint(
    service=get_products_service,
    query_model=ProductQueryDTO,
    response_model=List[ProductResponseDTO],
    path="/products/search",
    method="get",
    tags=["Products"]
)

# Command endpoint for write operations
command_endpoint = CommandEndpoint(
    service=create_product_service,
    command_model=ProductCommandDTO,
    response_model=ProductResponseDTO,
    path="/products/create",
    method="post",
    tags=["Products"]
)
```

### CQRS Pattern

The Command-Query Responsibility Segregation (CQRS) pattern separates operations that read data (queries) from operations that modify data (commands):

```python
from uno.api.endpoint import CqrsEndpoint, CommandHandler, QueryHandler

# Create handlers
get_products_handler = QueryHandler(
    service=get_products_service,
    query_model=ProductQueryDTO,
    response_model=List[ProductResponseDTO],
    path="/search",
    method="get"
)

create_product_handler = CommandHandler(
    service=create_product_service,
    command_model=ProductCommandDTO,
    response_model=ProductResponseDTO,
    path="/create",
    method="post"
)

# Combine in a CQRS endpoint
endpoint = CqrsEndpoint(
    queries=[get_products_handler],
    commands=[create_product_handler],
    base_path="/products",
    tags=["Products"]
)
```

### Response Formatting

The framework provides standardized response formatting:

```python
from uno.api.endpoint.response import DataResponse, ErrorResponse, PaginatedResponse

# Standard data response
@router.get("/items")
async def get_items() -> DataResponse[List[Item]]:
    items = await item_service.get_all()
    return DataResponse(data=items)

# Paginated response
@router.get("/items/paged")
async def get_paged_items(page: int = 1, page_size: int = 20) -> PaginatedResponse[Item]:
    result = await item_service.get_paged(page, page_size)
    return PaginatedResponse(
        data=result.items,
        metadata=PaginationMetadata(
            page=page,
            page_size=page_size,
            total=result.total
        )
    )
```

### Error Handling

Comprehensive error handling is built into the framework:

```python
from uno.api.endpoint.middleware import setup_error_handlers

# In your FastAPI app setup
app = FastAPI()
setup_error_handlers(app)
```

All endpoints automatically convert domain-level errors to appropriate HTTP responses:

```python
# In your domain service
if not user_has_permission:
    return Failure("Access denied", error_code="FORBIDDEN")

# The endpoint will convert this to a 403 Forbidden response
```

### Authentication

The framework includes comprehensive authentication support:

```python
from uno.api.endpoint.auth import SecureCrudEndpoint, JwtAuthBackend

# Create auth backend
auth_backend = JwtAuthBackend(
    secret_key=settings.jwt_secret,
    token_url="/api/auth/token"
)

# Create secure endpoint
endpoint = SecureCrudEndpoint(
    service=product_service,
    create_model=ProductCreateDTO,
    response_model=ProductResponseDTO,
    auth_backend=auth_backend,
    create_permissions=["products.create"],
    read_permissions=["products.read"],
    update_permissions=["products.update"],
    delete_permissions=["products.delete"],
    path="/products",
    tags=["Products"]
)
```

### Filtering

The framework supports powerful filtering capabilities:

```python
from uno.api.endpoint.filter import FilterableCrudEndpoint

# Create filterable endpoint
endpoint = FilterableCrudEndpoint(
    service=product_service,
    create_model=ProductCreateDTO,
    response_model=ProductResponseDTO,
    filter_fields=["name", "category", "price"],
    use_graph_backend=True,  # Optional Apache AGE support
    path="/products",
    tags=["Products"]
)
```

### OpenAPI Documentation

Built-in support for enhanced OpenAPI documentation:

```python
from uno.api.endpoint.openapi import OpenApiEnhancer, ResponseExample
from uno.api.endpoint.openapi_extensions import DocumentedCrudEndpoint

# Enhance app documentation
enhancer = OpenApiEnhancer(app)
enhancer.setup_jwt_auth(description="JWT authentication")
enhancer.apply()

# Create documented endpoint
endpoint = DocumentedCrudEndpoint(
    service=product_service,
    create_model=ProductCreateDTO,
    response_model=ProductResponseDTO,
    path="/products",
    tags=["Products"],
    summary="Product management endpoints",
    description="Endpoints for creating, retrieving, updating, and deleting products",
    operation_examples={
        "create": {
            "201": {
                "content": {"id": "123", "name": "Example Product"},
                "description": "Product created successfully"
            }
        }
    }
)
```

## Factory Pattern

The framework provides factory classes to simplify endpoint creation:

```python
from uno.api.endpoint.factory import CrudEndpointFactory, EndpointFactory

# Create a CRUD endpoint factory
factory = CrudEndpointFactory(
    service_factory=service_factory,
    path_prefix="/api",
    tags=["Products"]
)

# Create endpoints from a schema
endpoints = factory.from_schema(
    entity_name="Product",
    schema=ProductSchema,
    exclude_fields=["created_at", "updated_at"],
    readonly_fields=["id"]
)

# Register with FastAPI app
for endpoint in endpoints:
    endpoint.register(app)
```

## Integration with FastAPI

The framework seamlessly integrates with FastAPI:

```python
from fastapi import FastAPI
from uno.api.endpoint.integration import create_api, setup_api

# Create a FastAPI app with API configuration
app = create_api(
    title="My API",
    description="My API description",
    version="1.0.0"
)

# Set up API with endpoints
setup_api(
    app,
    endpoints=[product_endpoint, order_endpoint],
    include_auth=True,
    error_handling=True
)
```

## Best Practices

1. **Prefer CQRS for Complex Operations**: Use the CQRS pattern for operations with complex business logic or side effects
2. **Use Factories for Repetitive Endpoints**: Use factories to create multiple endpoints with similar patterns
3. **Standardize Response Formats**: Use the provided response classes for consistent API responses
4. **Leverage Domain Services**: Build endpoint functionality on top of domain and application services
5. **Document with Examples**: Use the OpenAPI utilities to provide comprehensive documentation
6. **Follow RESTful Conventions**: Use appropriate HTTP methods and status codes
7. **Implement Proper Error Handling**: Return appropriate error responses with meaningful messages and codes
8. **Use Authentication for Secure Resources**: Implement authentication for sensitive operations
9. **Consider Performance**: Use filtering, pagination, and projection to optimize API performance
10. **Test Thoroughly**: Write comprehensive tests for all endpoints and edge cases

## Examples

See the example modules in `uno.api.endpoint.examples` for complete implementations:

- `crud_example.py`: Basic CRUD operations
- `cqrs_example.py`: Command-Query Responsibility Segregation
- `auth_example.py`: Authentication and authorization
- `filter_example.py`: Advanced filtering
- `openapi_example.py`: Enhanced OpenAPI documentation

## Architecture

The unified endpoint framework follows a layered architecture:

```
┌───────────────────────────────────────────────────────────┐
│                     FastAPI Application                    │
└───────────────────────────┬───────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────┐
│                   Unified Endpoint Framework               │
│                                                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │BaseEndpoint │   │CrudEndpoint │   │CqrsEndpoint │      │
│  └─────────────┘   └─────────────┘   └─────────────┘      │
│                                                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │Filtering    │   │Authentication│   │OpenAPI      │      │
│  └─────────────┘   └─────────────┘   └─────────────┘      │
│                                                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │Responses    │   │ErrorHandling│   │Factory      │      │
│  └─────────────┘   └─────────────┘   └─────────────┘      │
└───────────────────────────┬───────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────┐
│                   Domain Services Layer                    │
└───────────────────────────┬───────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────┐
│                     Domain Model Layer                     │
└───────────────────────────────────────────────────────────┘
```

## Conclusion

The unified endpoint framework provides a powerful, flexible approach to building API endpoints that integrate seamlessly with domain-driven design principles. By leveraging the components provided by this framework, you can rapidly build consistent, maintainable, and well-documented APIs that expose your domain model to clients in a clean, structured way.

For additional details, see the specific documentation for each component:

- [Endpoint Base Classes](base.md)
- [CQRS Implementation](cqrs.md)
- [Response Formatting](response.md)
- [Error Handling](error_handling.md)
- [Authentication](authentication.md)
- [Filtering](filtering.md)
- [OpenAPI Documentation](openapi.md)
- [Factory Pattern](factory.md)
- [Integration with FastAPI](integration.md)