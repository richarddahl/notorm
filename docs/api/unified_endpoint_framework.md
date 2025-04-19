# Unified Endpoint Framework Developer Guide

The UNO Unified Endpoint Framework provides a comprehensive solution for creating FastAPI endpoints that integrate seamlessly with the domain entity framework. This guide will help you understand how to use the framework to build consistent, maintainable, and well-documented APIs.

## Introduction

The Unified Endpoint Framework is part of the UNO architecture modernization plan, specifically Phase 3: API Integration. It provides a standardized approach to creating API endpoints that follows best practices for API design, including CQRS pattern, standardized responses, proper error handling, and integration with OpenAPI documentation.

### Key Features

- **Standardized Endpoint Classes**: BaseEndpoint, CrudEndpoint, QueryEndpoint, CommandEndpoint
- **CQRS Support**: Separation of query and command operations with CqrsEndpoint
- **Factory Pattern**: Automated endpoint creation with EndpointFactory and CrudEndpointFactory
- **Standardized Response Format**: Consistent response format with DataResponse, ErrorResponse, PaginatedResponse
- **Error Handling**: Middleware and handlers for standardized error responses
- **FastAPI Integration**: Seamless integration with FastAPI applications

## Installation

The Unified Endpoint Framework is part of the UNO framework and is available in the `uno.api.endpoint` package.

## Quick Start

### Creating a Basic CRUD Endpoint

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

from uno.api.endpoint.base import CrudEndpoint
from uno.api.endpoint.integration import create_api
from uno.domain.entity.service import CrudService

# Define your models
class ProductResponse(BaseModel):
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")

class CreateProductRequest(BaseModel):
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")

class UpdateProductRequest(BaseModel):
    name: str = Field(None, description="Product name")
    price: float = Field(None, description="Product price")

# Create your service
product_service = ProductService()  # Your CrudService implementation

# Create the API
app = create_api(title="Product API", description="API for managing products")

# Create and register the endpoint
endpoint = CrudEndpoint(
    service=product_service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    tags=["Products"],
    path="/api/products",
)
endpoint.register(app)
```

### Creating a CQRS Endpoint

```python
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field

from uno.api.endpoint.cqrs import CommandHandler, CqrsEndpoint, QueryHandler
from uno.api.endpoint.integration import create_api

# Define your models
class ProductSearchQuery(BaseModel):
    name: Optional[str] = Field(None, description="Product name contains")
    min_price: Optional[float] = Field(None, description="Minimum price")

class ProductSearchResult(BaseModel):
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")

class CreateProductCommand(BaseModel):
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")

# Create your services
search_service = SearchProductsService()  # Your query service
create_service = CreateProductService()   # Your command service

# Create the API
app = create_api(title="Product CQRS API", description="API for managing products using CQRS")

# Create query and command handlers
search_query = QueryHandler(
    service=search_service,
    response_model=List[ProductSearchResult],
    query_model=ProductSearchQuery,
    path="/search",
    method="get",
)

create_command = CommandHandler(
    service=create_service,
    command_model=CreateProductCommand,
    response_model=ProductSearchResult,
    path="",
    method="post",
)

# Create and register the CQRS endpoint
endpoint = CqrsEndpoint(
    queries=[search_query],
    commands=[create_command],
    tags=["Products"],
    base_path="/api/products",
)
endpoint.register(app)
```

### Using the Factory Pattern

```python
from fastapi import FastAPI
from pydantic import BaseModel

from uno.api.endpoint.factory import CrudEndpointFactory
from uno.api.endpoint.integration import create_api
from uno.domain.entity.service import ServiceFactory

# Define your models
class ProductSchema(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int
    is_active: bool

# Create the API
app = create_api(title="Product API", description="API for managing products")

# Create a service factory
service_factory = ServiceFactory()

# Create a CRUD endpoint factory
factory = CrudEndpointFactory.from_schema(
    service_factory=service_factory,
    entity_name="Product",
    schema=ProductSchema,
    tags=["Products"],
    path_prefix="/api",
    exclude_fields=["created_at", "updated_at"],
    readonly_fields=["id"],
)

# Create and register endpoints
factory.create_endpoints(app)
```

## Core Components

### 1. BaseEndpoint

The foundation of all endpoints, providing common functionality for registering routes and handling responses.

```python
class BaseEndpoint(Generic[RequestModel, ResponseModel, IdType]):
    """Base class for all API endpoints."""
    
    def __init__(
        self,
        *,
        router: Optional[APIRouter] = None,
        tags: Optional[List[str]] = None,
    ):
        """Initialize a new endpoint instance."""
        self.router = router or APIRouter()
        self.tags = tags or []
    
    def register(self, app: FastAPI, prefix: str = "") -> None:
        """Register this endpoint with a FastAPI application."""
        app.include_router(self.router, prefix=prefix, tags=self.tags)
        
    def handle_result(self, result: Result[ResponseModel], **kwargs) -> ResponseModel:
        """Handle a Result object from a domain service."""
        # Implementation details...
```

### 2. CrudEndpoint

Provides standardized implementation of CRUD operations for domain entities.

```python
class CrudEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """Base class for CRUD endpoints that work with domain entities."""
    
    def __init__(
        self,
        *,
        service: CrudService,
        create_model: Type[RequestModel],
        response_model: Type[ResponseModel],
        update_model: Optional[Type[RequestModel]] = None,
        router: Optional[APIRouter] = None,
        tags: Optional[List[str]] = None,
        path: str = "",
        id_field: str = "id",
    ):
        """Initialize a new CRUD endpoint instance."""
        # Implementation details...
```

### 3. CQRS Components

The framework provides support for the Command Query Responsibility Segregation (CQRS) pattern:

```python
class QueryHandler(Generic[RequestModel, ResponseModel]):
    """Handler for a query operation in a CQRS endpoint."""
    
    def __init__(
        self,
        service: Union[ApplicationService, DomainService],
        response_model: Type[ResponseModel],
        query_model: Optional[Type[RequestModel]] = None,
        path: str = "",
        method: str = "get",
    ):
        """Initialize a new query handler."""
        # Implementation details...

class CommandHandler(Generic[RequestModel, ResponseModel]):
    """Handler for a command operation in a CQRS endpoint."""
    
    def __init__(
        self,
        service: Union[ApplicationService, DomainService],
        command_model: Type[RequestModel],
        response_model: Optional[Type[ResponseModel]] = None,
        path: str = "",
        method: str = "post",
    ):
        """Initialize a new command handler."""
        # Implementation details...

class CqrsEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """Endpoint that implements the CQRS pattern."""
    
    def __init__(
        self,
        *,
        queries: List[QueryHandler] = None,
        commands: List[CommandHandler] = None,
        router: Optional[APIRouter] = None,
        tags: Optional[List[str]] = None,
        base_path: str = "",
    ):
        """Initialize a new CQRS endpoint instance."""
        # Implementation details...
```

### 4. Factory Pattern

The framework includes factories for creating endpoints:

```python
class EndpointFactory:
    """Factory for creating API endpoints."""
    
    @staticmethod
    def create_crud_endpoint(
        service: CrudService,
        create_model: Type[RequestModel],
        response_model: Type[ResponseModel],
        update_model: Optional[Type[RequestModel]] = None,
        router: Optional[APIRouter] = None,
        tags: Optional[List[str]] = None,
        path: str = "",
        id_field: str = "id",
    ) -> CrudEndpoint[RequestModel, ResponseModel, IdType]:
        """Create a new CRUD endpoint."""
        # Implementation details...

class CrudEndpointFactory(Generic[RequestModel, ResponseModel, IdType]):
    """Factory for creating CRUD endpoints."""
    
    @classmethod
    def from_schema(
        cls,
        *,
        service_factory: ServiceFactory,
        entity_name: str,
        schema: Type[BaseModel],
        tags: Optional[List[str]] = None,
        path_prefix: str = "/api",
        exclude_fields: Optional[List[str]] = None,
        readonly_fields: Optional[List[str]] = None,
    ) -> "CrudEndpointFactory":
        """Create a CrudEndpointFactory from a Pydantic schema."""
        # Implementation details...
```

### 5. Response Formatting

The framework provides standardized response formatting:

```python
class DataResponse(BaseModel, Generic[T]):
    """Standard response format for data."""
    
    data: T = Field(..., description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")

class ErrorResponse(BaseModel):
    """Standard response format for errors."""
    
    error: ErrorDetail = Field(..., description="Error details")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard response format for paginated data."""
    
    data: List[T] = Field(..., description="List of items")
    meta: PaginationMetadata = Field(..., description="Pagination metadata")
```

### 6. Error Handling

The framework includes middleware for handling errors:

```python
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors in API requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and handle any errors."""
        # Implementation details...

def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for a FastAPI application."""
    # Implementation details...
```

### 7. FastAPI Integration

The framework provides utilities for integrating with FastAPI:

```python
def setup_api(
    app: FastAPI,
    *,
    enable_cors: bool = True,
    cors_origins: Optional[List[str]] = None,
    enable_error_handling: bool = True,
    enable_scoped_dependencies: bool = True,
) -> None:
    """Set up a FastAPI application with the unified endpoint framework."""
    # Implementation details...

def create_api(
    *,
    title: str = "UNO API",
    description: str = "API created with the UNO framework",
    version: str = "0.1.0",
    enable_cors: bool = True,
    cors_origins: Optional[List[str]] = None,
    enable_error_handling: bool = True,
    enable_scoped_dependencies: bool = True,
    openapi_url: str = "/openapi.json",
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
) -> FastAPI:
    """Create a new FastAPI application with the unified endpoint framework."""
    # Implementation details...
```

## Integration with Domain Entity Framework

The Unified Endpoint Framework integrates seamlessly with the domain entity framework from Phase 2 of the architecture modernization plan:

### Service Layer Integration

Endpoints can use domain services for business logic:

```python
from uno.domain.entity.service import CrudService, ApplicationService, DomainService

# CRUD operations
crud_endpoint = CrudEndpoint(service=crud_service, ...)

# Query operations
query_handler = QueryHandler(service=query_service, ...)

# Command operations
command_handler = CommandHandler(service=command_service, ...)
```

### Repository Layer Integration

Domain services use repositories for data access:

```python
from uno.domain.entity.repository import EntityRepository, SQLAlchemyRepository
from uno.domain.entity.service import CrudService

class ProductRepository(SQLAlchemyRepository[Product, str, ProductModel]):
    # Repository implementation...

class ProductService(CrudService[Product, str]):
    def __init__(self, repository: ProductRepository):
        super().__init__(repository)
```

### Result Pattern Integration

The framework uses the Result pattern for error handling:

```python
from uno.core.errors.result import Result, Success, Error

async def execute(self, command: CreateProductCommand) -> Result[ProductCreatedResult]:
    # Service implementation...
```

## Best Practices

### 1. Use the CQRS Pattern for Complex Operations

For complex operations, use the CQRS pattern to separate read and write operations:

```python
# Query endpoint for reading data
endpoint.add_query(QueryHandler(
    service=get_product_stats_service,
    response_model=ProductStatsResult,
    query_model=ProductStatsQuery,
    path="/stats",
    method="get",
))

# Command endpoint for writing data
endpoint.add_command(CommandHandler(
    service=update_product_availability_service,
    command_model=UpdateProductAvailabilityCommand,
    path="/availability",
    method="put",
))
```

### 2. Use the Factory Pattern for Consistency

Use the factory pattern to ensure consistency across endpoints:

```python
factory = CrudEndpointFactory.from_schema(
    service_factory=service_factory,
    entity_name="Product",
    schema=ProductSchema,
    tags=["Products"],
    path_prefix="/api",
)

factory.create_endpoints(app)
```

### 3. Standardize Response Formatting

Use the standardized response formatting for consistent API responses:

```python
from uno.api.endpoint.response import DataResponse, ErrorResponse, PaginatedResponse, paginated_response

# Return a data response
@router.get("/api/products/{id}", response_model=DataResponse[ProductResponse])
async def get_product(id: str):
    result = await product_service.get_by_id(id)
    return DataResponse(data=result.value)

# Return a paginated response
@router.get("/api/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(page: int = 1, page_size: int = 50):
    result = await product_service.find({})
    count_result = await product_service.count({})
    return paginated_response(
        items=result.value,
        page=page,
        page_size=page_size,
        total_items=count_result.value,
    )
```

### 4. Use Proper Error Handling

Use the error handling middleware for consistent error responses:

```python
from uno.api.endpoint.middleware import ErrorHandlerMiddleware, setup_error_handlers

# Set up error handling
app.add_middleware(ErrorHandlerMiddleware)
setup_error_handlers(app)
```

### 5. Document Your API

Use FastAPI's and Pydantic's documentation features:

```python
class CreateProductRequest(BaseModel):
    """Request to create a new product."""
    
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price", gt=0)
    description: str = Field("", description="Product description")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Example Product",
                "price": 19.99,
                "description": "This is an example product",
            }
        }
```

## Advanced Features

### 1. Custom Response Handlers

You can create custom response handlers for specific needs:

```python
class CustomEndpoint(BaseEndpoint):
    def handle_result(self, result: Result, **kwargs):
        if isinstance(result, Success):
            # Custom success handling
            return {
                "data": result.value,
                "custom_meta": {"processed_at": datetime.now().isoformat()}
            }
        else:
            # Custom error handling
            # ...
```

### 2. Custom Query Parameter Handling

You can create custom query parameter handlers for advanced filtering:

```python
@router.get("/api/products/search")
async def search_products(
    query: str = None,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    sort_by: str = None,
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 50,
):
    # Build filter criteria
    filters = {}
    if query:
        filters["name__contains"] = query
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["price__gte"] = min_price
    if max_price is not None:
        filters["price__lte"] = max_price
        
    # Add sorting
    order_by = sort_by if sort_by else "name"
    if sort_dir == "desc":
        order_by = f"-{order_by}"
        
    # Execute query
    result = await product_service.find(
        filters=filters,
        order_by=order_by,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    
    # Return paginated response
    # ...
```

### 3. Integration with Authentication and Authorization

You can integrate with authentication and authorization systems:

```python
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify token and get user
    # ...

# Secure an endpoint
@router.post("/api/products", dependencies=[Depends(get_current_user)])
async def create_product(product: CreateProductRequest):
    # Create product
    # ...
```

## Migration from Legacy Code

If you have legacy code using the old endpoint patterns, you can use the compatibility layer:

```python
from uno.api.endpoint.compatibility import create_legacy_endpoint

# Create a modern endpoint from a legacy service
endpoint = create_legacy_endpoint(
    service=legacy_service,
    app=app,
    path="/api/legacy",
    tags=["Legacy"],
)
```

## Conclusion

The Unified Endpoint Framework provides a powerful and flexible way to create FastAPI endpoints that integrate seamlessly with the domain entity framework. By following the patterns and best practices outlined in this guide, you can build consistent, maintainable, and well-documented APIs that leverage the power of domain-driven design.

## Next Steps

- Learn more about [CQRS Pattern](endpoint/cqrs_pattern.md)
- Learn more about [Response Formatting](endpoint/response_formatting.md)
- Learn more about [Error Handling](endpoint/error_handling.md)
- Learn more about [OpenAPI Integration](endpoint/openapi_integration.md)
- Learn more about [Authentication and Authorization](endpoint/authentication.md)