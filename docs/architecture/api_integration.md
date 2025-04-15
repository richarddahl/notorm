# API Integration Layer

The API Integration Layer in uno connects the Application Service Layer to HTTP endpoints, providing a clean boundary between the domain model and external clients. It translates HTTP requests into commands and queries, and transforms the results back into HTTP responses.

## Overview

The API Integration Layer is built on FastAPI and provides a set of components for creating RESTful APIs that interact with application services. It handles:

- Routing HTTP requests to appropriate application services
- Extracting context information (user, tenant, permissions) from HTTP requests
- Validating and converting HTTP request data to commands and queries
- Executing commands and queries via application services
- Converting command and query results to HTTP responses
- Handling errors and exceptions consistently
- Generating OpenAPI documentation for the API

## Key Components

### Service Context Provider

The `ContextProvider` class extracts context information from HTTP requests:

```python
class ContextProvider:```

async def __call__(self, request: Request) -> ServiceContext:```

# Extract user ID, tenant ID, permissions, etc. from request
user_id = self._get_user_id(request)
is_authenticated = user_id is not None
tenant_id = self._get_tenant_id(request)
permissions = self._get_permissions(request)
``````

```
```

# Create and return service context
return ServiceContext(
    user_id=user_id,
    tenant_id=tenant_id,
    is_authenticated=is_authenticated,
    permissions=permissions,
    request_metadata={
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "path": request.url.path,
        "method": request.method,
    }
)
```
```
```

### API Endpoint

The `ApiEndpoint` class provides the base functionality for API endpoints:

```python
class ApiEndpoint:```

def __init__(```

self,
service: ApplicationService,
router: APIRouter,
path: str,
response_model: Optional[Type[BaseModel]] = None,
logger: Optional[logging.Logger] = None
```
):```

# Initialize API endpoint
```
``````

```
```

def handle_result(```

self,
result: Union[CommandResult, QueryResult]
```
) -> Union[Response, Dict[str, Any]]:```

# Convert command/query result to HTTP response
```
``````

```
```

def handle_exception(self, exception: Exception) -> Response:```

# Convert exception to HTTP response
```
```
```

### Entity API

The `EntityApi` class provides standard CRUD endpoints for entities:

```python
class EntityApi(Generic[EntityT]):```

def __init__(```

self,
entity_type: Type[EntityT],
service: EntityService[EntityT],
router: APIRouter,
prefix: str,
tags: List[str],
create_dto: Optional[Type[BaseModel]] = None,
update_dto: Optional[Type[BaseModel]] = None,
response_model: Optional[Type[BaseModel]] = None,
logger: Optional[logging.Logger] = None
```
):```

# Initialize entity API and register routes
```
```
```

### Aggregate API

The `AggregateApi` class extends the entity API with aggregate-specific operations:

```python
class AggregateApi(EntityApi[AggregateT], Generic[AggregateT]):```

def __init__(```

self,
aggregate_type: Type[AggregateT],
service: AggregateService[AggregateT],
router: APIRouter,
prefix: str,
tags: List[str],
create_dto: Optional[Type[BaseModel]] = None,
update_dto: Optional[Type[BaseModel]] = None,
response_model: Optional[Type[BaseModel]] = None,
logger: Optional[logging.Logger] = None
```
):```

# Initialize aggregate API and register routes
```
```
```

### Service API Registry

The `ServiceApiRegistry` class provides a central place to register and retrieve API endpoints:

```python
class ServiceApiRegistry:```

def __init__(self, router: APIRouter, service_registry: Optional[ServiceRegistry] = None):```

# Initialize API registry
```
``````

```
```

def register_entity_api(```

self,
entity_type: Type[EntityT],
prefix: str,
tags: List[str],
service_name: Optional[str] = None,
create_dto: Optional[Type[BaseModel]] = None,
update_dto: Optional[Type[BaseModel]] = None,
response_model: Optional[Type[BaseModel]] = None
```
) -> EntityApi[EntityT]:```

# Register entity API
```
``````

```
```

def register_aggregate_api(```

self,
aggregate_type: Type[AggregateT],
prefix: str,
tags: List[str],
service_name: Optional[str] = None,
create_dto: Optional[Type[BaseModel]] = None,
update_dto: Optional[Type[BaseModel]] = None,
response_model: Optional[Type[BaseModel]] = None
```
) -> AggregateApi[AggregateT]:```

# Register aggregate API
```
```
```

## Implementing API Integration

### Basic Implementation

To create a RESTful API for your domain model:

1. Set up a FastAPI application and router
2. Create DTOs for request and response models
3. Register entity and aggregate APIs in the service API registry

```python
# Create FastAPI app and router
app = FastAPI(title="My API")
router = APIRouter()

# Create API registry
api_registry = ServiceApiRegistry(router, service_registry)

# Register entity API
api_registry.register_entity_api(```

entity_type=Product,
prefix="/products",
tags=["Products"],
service_name="ProductService",
create_dto=ProductCreateDto,
update_dto=ProductUpdateDto,
response_model=ProductResponseDto
```
)

# Register aggregate API
api_registry.register_aggregate_api(```

aggregate_type=Order,
prefix="/orders",
tags=["Orders"],
service_name="OrderService",
create_dto=OrderCreateDto,
update_dto=OrderUpdateDto,
response_model=OrderResponseDto
```
)

# Include router in app
app.include_router(router, prefix="/api/v1")
```

### Custom Context Provider

You can customize how context information is extracted from HTTP requests:

```python
class CustomContextProvider(ContextProvider):```

def _get_user_id(self, request: Request) -> Optional[str]:```

# Extract user ID from JWT token
token = request.headers.get("Authorization", "").replace("Bearer ", "")
if token:
    return decode_jwt(token).get("sub")
return None
```
``````

```
```

def _get_tenant_id(self, request: Request) -> Optional[str]:```

# Extract tenant ID from subdomain
host = request.headers.get("host", "")
if "." in host:
    return host.split(".")[0]
return None
```
``````

```
```

def _get_permissions(self, request: Request) -> List[str]:```

# Extract permissions from JWT token
token = request.headers.get("Authorization", "").replace("Bearer ", "")
if token:
    return decode_jwt(token).get("permissions", [])
return []
```
```

# Register custom context provider
from uno.api.service_api import default_context_provider
default_context_provider = CustomContextProvider()
```

### Custom API Endpoints

You can extend the base API classes to add custom endpoints:

```python
class OrderApi(AggregateApi[Order]):```

def __init__(```

self,
aggregate_type: Type[Order],
service: OrderService,
router: APIRouter,
prefix: str,
tags: List[str],
create_dto = None,
update_dto = None,
response_model = None,
logger = None
```
):```

super().__init__(
    aggregate_type=aggregate_type,
    service=service,
    router=router,
    prefix=prefix,
    tags=tags,
    create_dto=create_dto,
    update_dto=update_dto,
    response_model=response_model,
    logger=logger
)
``````

```
```

# Register additional routes
self._register_checkout_route()
```
``````

```
```

def _register_checkout_route(self) -> None:```

@self.router.post(
    f"{self.prefix}/{{order_id}}/checkout",
    response_model=self.response_model,
    tags=self.tags,
)
async def checkout_order(
    order_id: str,
    context: ServiceContext = Depends(get_context),
):
    try:
        result = await self.service.checkout(order_id, context)
        return self._handle_result(result)
    except Exception as e:
        return self._handle_exception(e)
```
```
```

### DTOs and Response Models

You can create Data Transfer Objects (DTOs) and response models for your API:

```python
# Manually create DTOs
class ProductCreateDto(BaseModel):```

name: str
description: str
price: float
sku: str
in_stock: bool = True
```

class ProductUpdateDto(BaseModel):```

name: Optional[str] = None
description: Optional[str] = None
price: Optional[float] = None
sku: Optional[str] = None
in_stock: Optional[bool] = None
```

class ProductResponseDto(BaseModel):```

id: str
name: str
description: str
price: float
sku: str
in_stock: bool
created_at: str
updated_at: Optional[str] = None
```

# Or use the utility functions
ProductCreateDto = create_dto_for_entity(```

entity_type=Product,
name="ProductCreateDto",
exclude=["id", "created_at", "updated_at"],
optional=["in_stock"]
```
)

ProductUpdateDto = create_dto_for_entity(```

entity_type=Product,
name="ProductUpdateDto",
exclude=["id", "created_at", "updated_at"],
optional=["name", "description", "price", "sku", "in_stock"]
```
)

ProductResponseDto = create_response_model_for_entity(```

entity_type=Product,
name="ProductResponseDto"
```
)
```

## Error Handling

The API Integration Layer provides standardized error handling:

```python
class ApiError(BaseModel):```

code: ApiErrorCode
message: str
details: Optional[Dict[str, Any]] = None
```

class ApiErrorCode(str, Enum):```

BAD_REQUEST = "BAD_REQUEST"
UNAUTHORIZED = "UNAUTHORIZED"
FORBIDDEN = "FORBIDDEN"
NOT_FOUND = "NOT_FOUND"
CONFLICT = "CONFLICT"
INTERNAL_ERROR = "INTERNAL_ERROR"
VALIDATION_ERROR = "VALIDATION_ERROR"
```
```

Command and query errors are mapped to appropriate HTTP status codes:

- Authorization errors -> 401 Unauthorized
- Permission errors -> 403 Forbidden
- Entity not found -> 404 Not Found
- Concurrency errors -> 409 Conflict
- Validation errors -> 422 Unprocessable Entity
- Other errors -> 500 Internal Server Error

## Pagination

The API Integration Layer supports pagination for list endpoints:

```python
class PaginationParams(BaseModel):```

page: int = Field(1, description="Page number (1-indexed)", ge=1)
page_size: int = Field(50, description="Number of items per page", ge=1, le=100)
```

class PaginatedResponse(BaseModel, Generic[T]):```

items: List[T]
total: int
page: int
page_size: int
total_pages: int
has_next: bool
has_previous: bool
```
```

## Benefits

The API Integration Layer provides several benefits:

1. **Clean separation**: Isolates HTTP concerns from application logic
2. **Standardized endpoints**: Provides consistent API patterns for all entities and aggregates
3. **Type safety**: Uses Pydantic models for request and response validation
4. **Automatic documentation**: Generates OpenAPI documentation with FastAPI
5. **Error handling**: Provides consistent error responses
6. **Security**: Extracts and validates security context from HTTP requests
7. **Extensibility**: Can be extended with custom endpoints and behavior
8. **DRY principle**: Eliminates boilerplate code for standard CRUD operations

## Best Practices

1. **Use DTOs for input validation**: Always define DTOs for request data validation
2. **Separate read and write models**: Use different DTOs for create, update, and response
3. **Keep controllers thin**: Put business logic in application services, not in API endpoints
4. **Use dependency injection**: Inject services and other dependencies via FastAPI's dependency system
5. **Handle errors gracefully**: Return meaningful error messages and appropriate status codes
6. **Document your API**: Use FastAPI's built-in documentation features
7. **Use consistent naming**: Follow REST conventions for resource naming
8. **Version your API**: Use URL or header versioning for API compatibility

## Example

```python
# Define domain model
@dataclass
class Product(Entity):```

name: str
description: str
price: float
sku: str
in_stock: bool = True
``````

created_at: datetime = field(default_factory=datetime.utcnow)
updated_at: Optional[datetime] = None
```

# Define DTOs
class ProductCreateDto(BaseModel):```

name: str
description: str
price: float
sku: str
in_stock: bool = True
```

class ProductUpdateDto(BaseModel):```

name: Optional[str] = None
description: Optional[str] = None
price: Optional[float] = None
sku: Optional[str] = None
in_stock: Optional[bool] = None
```

class ProductResponseDto(BaseModel):```

id: str
name: str
description: str
price: float
sku: str
in_stock: bool
created_at: str
updated_at: Optional[str] = None
```

# Register API endpoints
api_registry.register_entity_api(```

entity_type=Product,
prefix="/products",
tags=["Products"],
create_dto=ProductCreateDto,
update_dto=ProductUpdateDto,
response_model=ProductResponseDto
```
)
```

The above code generates the following endpoints:

- `POST /products` - Create a new product
- `GET /products/{entity_id}` - Get a product by ID
- `PUT /products/{entity_id}` - Update a product
- `DELETE /products/{entity_id}` - Delete a product
- `GET /products` - List all products
- `GET /products/paginated` - Get a paginated list of products

## Integration with FastAPI

The API Integration Layer is built on FastAPI and leverages its features:

- **Path parameters**: `{entity_id}` for entity or aggregate IDs
- **Query parameters**: For filtering, sorting, and pagination
- **Request body**: For create and update operations
- **Dependencies**: For injecting the service context
- **Response models**: For validating and documenting responses
- **Tags**: For organizing endpoints in the documentation
- **Status codes**: For indicating the result of operations

## Conclusion

The API Integration Layer provides a clean, consistent way to expose your domain model as a RESTful API. By integrating with the Application Service Layer and leveraging FastAPI's features, it eliminates boilerplate code and ensures a consistent API design across your application.

The layer handles the translation between HTTP requests and application services, allowing each layer to focus on its primary responsibility: HTTP concerns in the API layer, use case orchestration in the application service layer, and business logic in the domain layer. This separation of concerns makes your application more maintainable, testable, and scalable.