# Unified Endpoint Framework

The UNO Unified Endpoint Framework provides a standardized approach to creating API endpoints that integrate seamlessly with the domain entity framework. This framework simplifies the creation of REST APIs that follow best practices for API design, including CQRS pattern, standardized responses, proper error handling, and integration with OpenAPI documentation.

## Key Features

- **Standardized Endpoint Classes**: BaseEndpoint, CrudEndpoint, QueryEndpoint, CommandEndpoint
- **CQRS Support**: Separation of query and command operations with CqrsEndpoint
- **Automated CRUD Operations**: Automatic generation of CRUD endpoints for domain entities
- **Standardized Response Format**: Consistent response format for all API endpoints
- **Robust Error Handling**: Middleware and error handlers for standardized error responses
- **FastAPI Integration**: Seamless integration with FastAPI applications
- **OpenAPI Documentation**: Automatic generation of OpenAPI documentation

## Core Components

### BaseEndpoint

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
```

### CrudEndpoint

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

### CQRS Components

The framework provides support for the Command Query Responsibility Segregation (CQRS) pattern:

- **QueryHandler**: Handles read operations
- **CommandHandler**: Handles write operations
- **CqrsEndpoint**: Combines query and command handlers into a single endpoint

```python
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

### Factories

The framework includes factories for creating endpoints:

- **EndpointFactory**: Creates various endpoint types
- **CrudEndpointFactory**: Simplifies creation of CRUD endpoints for domain entities

```python
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

### Response Formatting

The framework provides standardized response formatting:

- **DataResponse**: Standard format for data responses
- **ErrorResponse**: Standard format for error responses
- **PaginatedResponse**: Standard format for paginated data responses

```python
class DataResponse(BaseModel, Generic[T]):
    """Standard response format for data."""
    
    data: T = Field(..., description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
```

## Usage Examples

### Basic CRUD Endpoint

```python
from uno.api.endpoint.base import CrudEndpoint
from uno.domain.entity.service import CrudService

# Create the service
service = ProductService()

# Create the endpoint
endpoint = CrudEndpoint(
    service=service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    tags=["Products"],
    path="/api/products",
)

# Register the endpoint
endpoint.register(app)
```

### CQRS Endpoint

```python
from uno.api.endpoint.cqrs import CommandHandler, CqrsEndpoint, QueryHandler

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
    response_model=ProductCreatedResult,
    path="",
    method="post",
)

# Create CQRS endpoint
endpoint = CqrsEndpoint(
    queries=[search_query],
    commands=[create_command],
    tags=["Products"],
    base_path="/api/products",
)

# Register the endpoint
endpoint.register(app)
```

### Using the Factory

```python
from uno.api.endpoint.factory import CrudEndpointFactory

# Create a factory from a schema
factory = CrudEndpointFactory.from_schema(
    service_factory=service_factory,
    entity_name="Product",
    schema=ProductSchema,
    tags=["Products"],
    path_prefix="/api",
)

# Create and register endpoints
factory.create_endpoints(app)
```

### Setting Up the API

```python
from uno.api.endpoint.integration import create_api

# Create the API
app = create_api(
    title="Product API",
    description="API for managing products",
    version="1.0.0",
)

# Register endpoints
# ...
```

## Integration with Domain Entity Framework

The Unified Endpoint Framework integrates seamlessly with the domain entity framework:

- **Service Layer**: Endpoints use domain services for business logic
- **Repository Layer**: Services use repositories for data access
- **Entity Layer**: Repositories work with domain entities
- **Result Pattern**: Consistent error handling across all layers

## Next Steps

- [CRUD Endpoints](crud_endpoints.md)
- [CQRS Pattern](cqrs_pattern.md)
- [Response Formatting](response_formatting.md)
- [Error Handling](error_handling.md)
- [OpenAPI Integration](openapi_integration.md)