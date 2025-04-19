# API Endpoint Framework Overview

The Uno API Endpoint Framework provides a comprehensive, unified approach to creating API endpoints that integrate seamlessly with domain services.

## Introduction

Building a modern API requires balancing several concerns:

- **Consistent interface**: Standardized response formats and error handling
- **Domain integration**: Clean connection to business logic
- **Security**: Authentication and authorization controls
- **Documentation**: Clear API documentation
- **Validation**: Input data validation

The Uno API Endpoint Framework addresses these concerns with a layered architecture that separates the interface from the application and domain logic.

## Key Features

- **Clean architecture integration**: Seamless connection to domain and application services
- **Declarative endpoints**: Define endpoints with minimal boilerplate
- **CQRS pattern support**: Separate command (write) and query (read) endpoints
- **Standardized responses**: Consistent response formatting
- **Comprehensive error handling**: Automatic error translation
- **Authentication & authorization**: Built-in security controls
- **Enhanced OpenAPI documentation**: Rich API documentation
- **Filtering & pagination**: Powerful data querying capabilities
- **Factory pattern**: Generate endpoints from schemas
- **Customization**: Extend and override default behaviors

## Base Endpoint Types

The framework provides several endpoint types to match different use cases:

### BaseEndpoint

The foundation for all endpoint types:

```python
from uno.api.endpoint import BaseEndpoint
from fastapi import APIRouter

router = APIRouter()

# Create a basic endpoint
endpoint = BaseEndpoint(
    router=router,
    prefix="/api",
    tags=["General"]
)

# Add custom routes
@endpoint.router.get("/health")
async def health_check():
    return {"status": "ok"}
```

### CrudEndpoint

Standard CRUD operations for entity types:

```python
from uno.api.endpoint import CrudEndpoint
from uno.core.di import get_dependency
from myapp.domain.services import ProductService
from myapp.api.dtos import ProductCreateDTO, ProductResponseDTO, ProductUpdateDTO

# Create a CRUD endpoint
product_endpoint = CrudEndpoint(
    service=get_dependency(ProductService),
    create_model=ProductCreateDTO,
    response_model=ProductResponseDTO,
    update_model=ProductUpdateDTO,
    path="/products",
    tags=["Products"]
)
```

This will create:
- GET `/products` - List all products
- GET `/products/{id}` - Get a single product
- POST `/products` - Create a new product
- PUT `/products/{id}` - Update a product
- DELETE `/products/{id}` - Delete a product

### QueryEndpoint

Read-only operations with filtering:

```python
from uno.api.endpoint import QueryEndpoint
from pydantic import BaseModel
from typing import List, Optional

class ProductQueryDTO(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None

# Create a query endpoint
product_query_endpoint = QueryEndpoint(
    service=get_dependency(ProductQueryService),
    query_model=ProductQueryDTO,
    response_model=List[ProductResponseDTO],
    path="/products/search",
    method="get",
    tags=["Products"]
)
```

### CommandEndpoint

Write operations with side effects:

```python
from uno.api.endpoint import CommandEndpoint
from pydantic import BaseModel

class OrderPlacementDTO(BaseModel):
    customer_id: str
    product_ids: List[str]
    shipping_address: str

class OrderResultDTO(BaseModel):
    order_id: str
    status: str
    total: float

# Create a command endpoint
place_order_endpoint = CommandEndpoint(
    service=get_dependency(OrderService),
    command_model=OrderPlacementDTO,
    response_model=OrderResultDTO,
    path="/orders/place",
    method="post",
    tags=["Orders"]
)
```

## CQRS Pattern

The Command-Query Responsibility Segregation (CQRS) pattern separates operations that read data (queries) from operations that modify data (commands):

```python
from uno.api.endpoint import CqrsEndpoint, CommandHandler, QueryHandler
from uno.core.di import get_dependency
from myapp.domain.services import OrderQueryService, OrderCommandService

# Create command and query handlers
get_orders_handler = QueryHandler(
    service=get_dependency(OrderQueryService),
    query_model=OrderQueryDTO,
    response_model=List[OrderResponseDTO],
    path="/search",
    method="get"
)

place_order_handler = CommandHandler(
    service=get_dependency(OrderCommandService),
    command_model=OrderPlacementDTO,
    response_model=OrderResultDTO,
    path="/place",
    method="post"
)

cancel_order_handler = CommandHandler(
    service=get_dependency(OrderCommandService),
    command_model=OrderCancellationDTO,
    response_model=OrderResultDTO,
    path="/cancel",
    method="post"
)

# Combine in a CQRS endpoint
order_endpoint = CqrsEndpoint(
    queries=[get_orders_handler],
    commands=[place_order_handler, cancel_order_handler],
    base_path="/orders",
    tags=["Orders"]
)
```

## Response Formatting

The framework provides standardized response formatting:

```python
from uno.api.endpoint.response import DataResponse, ErrorResponse, PaginatedResponse, PaginationMetadata
from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/items")
async def get_items() -> DataResponse[List[Item]]:
    items = await item_service.get_all()
    return DataResponse(data=items)

@router.get("/items/paged")
async def get_paged_items(page: int = 1, page_size: int = 20) -> PaginatedResponse[Item]:
    result = await item_service.get_paged(page, page_size)
    return PaginatedResponse(
        data=result.items,
        metadata=PaginationMetadata(
            page=page,
            page_size=page_size,
            total=result.total,
            pages=result.pages
        )
    )
```

Response format examples:

```json
// DataResponse
{
  "data": [...],
  "success": true
}

// PaginatedResponse
{
  "data": [...],
  "metadata": {
    "page": 1,
    "page_size": 20,
    "total": 157,
    "pages": 8
  },
  "success": true
}

// ErrorResponse
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {
      "resource_id": "123",
      "resource_type": "product"
    }
  },
  "success": false
}
```

## Error Handling

Comprehensive error handling is built into the framework:

```python
from uno.api.endpoint.middleware import setup_error_handlers
from fastapi import FastAPI, HTTPException
from uno.core.errors import NotFoundError, ValidationError

# In your FastAPI app setup
app = FastAPI()
setup_error_handlers(app)

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        # This will be converted to a proper error response
        raise NotFoundError(f"User with ID {user_id} not found")
    return user
```

Error handlers automatically convert various error types to appropriate HTTP responses:

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `NotFoundError` | 404 | Resource not found |
| `ValidationError` | 422 | Input validation failed |
| `AuthenticationError` | 401 | Authentication required |
| `AuthorizationError` | 403 | Permission denied |
| `ConflictError` | 409 | Resource conflict |
| `BusinessRuleError` | 422 | Business rule violation |
| `ExternalServiceError` | 502 | External service failure |
| `TimeoutError` | 504 | Operation timeout |

## Authentication

The framework includes comprehensive authentication support:

```python
from uno.api.endpoint.auth import SecureCrudEndpoint, JwtAuthBackend
from uno.core.di import get_dependency
from myapp.domain.services import ProductService
from myapp.api.dtos import ProductCreateDTO, ProductResponseDTO

# Create auth backend
auth_backend = JwtAuthBackend(
    secret_key=settings.jwt_secret,
    token_url="/api/auth/token"
)

# Create secure endpoint
secure_product_endpoint = SecureCrudEndpoint(
    service=get_dependency(ProductService),
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

Authentication features:
- JWT token support
- Role-based access control
- Permission-based authorization
- Multiple auth backend support
- Integration with FastAPI security

## Filtering

The framework supports powerful filtering capabilities:

```python
from uno.api.endpoint.filter import FilterableCrudEndpoint
from uno.core.di import get_dependency
from myapp.domain.services import ProductService
from myapp.api.dtos import ProductCreateDTO, ProductResponseDTO

# Create filterable endpoint
product_endpoint = FilterableCrudEndpoint(
    service=get_dependency(ProductService),
    create_model=ProductCreateDTO,
    response_model=ProductResponseDTO,
    filter_fields=["name", "category", "price"],
    sort_fields=["name", "price", "created_at"],
    use_graph_backend=True,  # Optional Apache AGE support
    path="/products",
    tags=["Products"]
)
```

This enables query parameters like:
- `?name=Product+Name` - Exact field match
- `?name__contains=product` - Field contains text
- `?price__gt=100&price__lt=200` - Range queries
- `?category__in=A,B,C` - Multiple options
- `?sort=price` - Sort by field (ascending)
- `?sort=-price` - Sort by field (descending)

## OpenAPI Documentation

Built-in support for enhanced OpenAPI documentation:

```python
from uno.api.endpoint.openapi import OpenApiEnhancer, ResponseExample
from uno.api.endpoint.openapi_extensions import DocumentedCrudEndpoint
from fastapi import FastAPI

# Create app
app = FastAPI()

# Enhance app documentation
enhancer = OpenApiEnhancer(app)
enhancer.setup_jwt_auth(description="JWT authentication")
enhancer.apply()

# Create documented endpoint
endpoint = DocumentedCrudEndpoint(
    service=get_dependency(ProductService),
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
from uno.core.di import get_dependency
from myapp.domain.services import ServiceFactory

# Create a service factory
service_factory = ServiceFactory()

# Create a CRUD endpoint factory
factory = CrudEndpointFactory(
    service_factory=service_factory.get_service,
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

## Integration with Domain Entity Framework

The Unified Endpoint Framework integrates seamlessly with the domain entity framework:

- **Service Layer**: Endpoints use domain services for business logic
- **Repository Layer**: Services use repositories for data access
- **Entity Layer**: Repositories work with domain entities
- **Result Pattern**: Consistent error handling across all layers

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

## Example Implementation

```python
from fastapi import FastAPI
from uno.api.endpoint import CrudEndpoint
from uno.api.endpoint.middleware import setup_error_handlers
from uno.api.endpoint.openapi import OpenApiEnhancer
from uno.core.di import configure_container, get_dependency
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

# DTOs
class ProductCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str

class ProductResponseDTO(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    price: float
    category: str

class ProductUpdateDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None

# App setup
app = FastAPI(title="Product API")
setup_error_handlers(app)
configure_container()

# OpenAPI enhancements
enhancer = OpenApiEnhancer(app)
enhancer.apply()

# Create endpoints
product_endpoint = CrudEndpoint(
    service=get_dependency(ProductService),
    create_model=ProductCreateDTO,
    response_model=ProductResponseDTO,
    update_model=ProductUpdateDTO,
    path="/products",
    tags=["Products"]
)

# Register endpoints
product_endpoint.register(app)

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Further Reading

- [Unified Endpoint Framework](unified_endpoint_framework.md): Detailed framework architecture
- [CQRS Pattern](cqrs_pattern.md): Command-Query Responsibility Segregation
- [Authentication](authentication.md): Authentication and authorization
- [Filtering](filtering.md): Advanced filtering capabilities
- [OpenAPI Extensions](openapi.md): Enhanced OpenAPI documentation