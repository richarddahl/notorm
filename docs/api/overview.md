# API Layer

The API Layer in uno provides a clean interface for exposing domain models and business logic through REST endpoints, with support for automatic endpoint generation, advanced filtering, and authorization. It supports both the modern domain-driven design approach and the legacy UnoObj pattern.

## In This Section

- [Endpoint](endpoint.md) - Core UnoEndpoint class for API interfaces
- [Endpoint Factory](endpoint-factory.md) - Automatic endpoint generation
- [Domain Integration](domain-integration.md) - Using domain repositories with endpoints
- [Repository Adapter](repository-adapter.md) - Bridge between repositories and endpoints
- [Schemas](schemas.md) - Data validation and serialization
- [Schema Manager](schema-manager.md) - Schema creation and management

## Overview

The API Layer sits between client applications and the business logic layer, providing a standardized interface for accessing and manipulating data through HTTP/JSON. It's designed to automate common API patterns while allowing for customization and extension.

## Architecture

The API layer integrates with the other components of uno to provide a complete solution:

### Domain-Driven Design Approach (Recommended)

```
┌───────────────┐      ┌───────────────┐      ┌─────────────────┐      ┌───────────────┐
│  API Client   │      │  UnoEndpoint  │      │   Repository    │      │    Database   │
│  (HTTP/JSON)  │◄────►│  (FastAPI)    │◄────►│ with Entities   │◄────►│               │
└───────────────┘      └───────────────┘      └─────────────────┘      └───────────────┘
                              │
                              │
                      ┌───────▼──────┐
                      │ Repository   │
                      │ Adapter      │
                      └──────────────┘
```

### Legacy UnoObj Approach

```
┌───────────────┐      ┌───────────────┐      ┌─────────────────┐      ┌───────────────┐
│  API Client   │      │  UnoEndpoint  │      │     UnoObj      │      │    UnoDB      │
│  (HTTP/JSON)  │◄────►│  (FastAPI)    │◄────►│ (Business Logic)|◄────►│  (Database)   │
└───────────────┘      └───────────────┘      └─────────────────┘      └───────────────┘
```

### Request Flow (Inbound) - Domain-Driven Approach

1. **HTTP Request**: Client sends HTTP request to endpoint
2. **Validation**: Request data is validated using Pydantic schema
3. **Deserialization**: JSON data is converted to Pydantic DTO
4. **Repository Adapter**: DTO is mapped to domain entity operations
5. **Repository**: Domain repository performs the business operation
6. **Response**: Results are mapped to DTO and returned to client

### Request Flow (Inbound) - Legacy Approach

1. **HTTP Request**: Client sends HTTP request to endpoint
2. **Validation**: Request data is validated using Pydantic schema
3. **Deserialization**: JSON data is converted to Pydantic model
4. **Business Logic**: UnoObj processes the request
5. **Database Operation**: UnoDB performs the database operation
6. **Response**: Results are serialized and returned to client

## Key Components

### UnoEndpoint

The `UnoEndpoint` class is a FastAPI-based endpoint implementation that exposes CRUD operations for domain repositories or business objects.

```python
from uno.api.endpoint import UnoEndpoint
from fastapi import FastAPI

# Legacy approach with UnoObj
app = FastAPI()
endpoint = UnoEndpoint(app, Customer)
endpoint.register_endpoints()

# Domain-driven approach with repository
from uno.api.repository_adapter import RepositoryAdapter
from uno.dependencies.fastapi import get_repository

app = FastAPI()
# Create repository adapter for the customer repository
adapter = RepositoryAdapter(
    get_repository(CustomerRepository),
    CustomerEntity,
    CustomerSchema
)
endpoint = UnoEndpoint(app, adapter)
endpoint.register_endpoints()
```

### Repository Adapter

The `RepositoryAdapter` class bridges domain repositories with the endpoint system, allowing you to use domain-driven design with the API layer.

```python
from uno.api.repository_adapter import RepositoryAdapter
from fastapi import Depends
from uno.dependencies.fastapi import get_repository

# Create a repository adapter
adapter = RepositoryAdapter(
    repository_dependency=Depends(get_repository(CustomerRepository)),
    entity_type=CustomerEntity,
    schema_type=CustomerSchema
)

# Use with UnoEndpoint or UnoEndpointFactory
endpoint = UnoEndpoint(app, adapter)
```

There are specialized adapters for different use cases:
- `RepositoryAdapter`: Full CRUD operations
- `ReadOnlyRepositoryAdapter`: Read-only operations (get, list)
- `BatchRepositoryAdapter`: Supports batch operations

### UnoEndpointFactory

The `UnoEndpointFactory` class automatically generates endpoints for domain repositories or business objects.

```python
from uno.api.endpoint_factory import EndpointFactory
from fastapi import FastAPI
from uno.dependencies.fastapi import get_db_session, get_repository

# Create FastAPI app
app = FastAPI()

# Legacy approach with UnoObj
customer_router = EndpointFactory.create_endpoints(
    app=app,
    model_obj=Customer,
    prefix="/customers",
    tag="Customers",
    session_dependency=get_db_session
)

# Domain-driven approach with repository
customer_router = EndpointFactory.create_endpoints(
    app=app,
    repository=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    prefix="/customers",
    tag="Customers"
)

# Register the router with the app
app.include_router(customer_router)
```

### FilterManager

The `FilterManager` class handles query parameters and filtering for API endpoints.

```python
from uno.queries.filter_manager import FilterManager
from uno.queries.filter import FilterParam

# Create a filter manager
filter_manager = FilterManager()

# Create filter parameters from query parameters
filter_params = FilterParam(```

limit=10,
offset=0,
name__contains="John",
status__in=["active", "pending"]
```
)

# Apply filters to a query
filtered_query = filter_manager.apply_filters(query, filter_params)
```

## Standard Endpoints

When you register endpoints for a business object, the following endpoints are created by default:

| Method | Path                         | Description                                   | Endpoint Type   |
|--------|------------------------------|-----------------------------------------------|----------------|
| POST   | /api/v1/{model_name}         | Create a new object                           | CreateEndpoint |
| GET    | /api/v1/{model_name}/{id}    | Get an object by ID                           | ViewEndpoint   |
| GET    | /api/v1/{model_name}         | List objects with filtering and pagination    | ListEndpoint   |
| PATCH  | /api/v1/{model_name}/{id}    | Update an object                              | UpdateEndpoint |
| DELETE | /api/v1/{model_name}/{id}    | Delete an object                              | DeleteEndpoint |
| PUT    | /api/v1/{model_name}         | Import objects (batch create or update)       | ImportEndpoint |

You can customize which endpoints are created by setting the `endpoints` class variable in your `UnoObj` subclass:

```python
class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
endpoints = ["Create", "View", "List"]  # Only these endpoints will be created
```
```

## Advanced Features

### Filtering

The API layer supports advanced filtering through query parameters:

```
GET /api/v1/customer?name__contains=John&status__in=active,pending&limit=10&offset=0&order_by=name
```

Filter operators include:

- `__eq`: Equal to (default if no operator is specified)
- `__ne`: Not equal to
- `__gt`: Greater than
- `__lt`: Less than
- `__ge`: Greater than or equal to
- `__le`: Less than or equal to
- `__contains`: Contains (case-sensitive)
- `__icontains`: Contains (case-insensitive)
- `__startswith`: Starts with
- `__endswith`: Ends with
- `__in`: In a list of values
- `__range`: Between two values

### Pagination

Pagination is supported through `limit` and `offset` query parameters:

```
GET /api/v1/customer?limit=10&offset=20
```

The response includes pagination metadata:

```json
{
  "data": [...],
  "total_count": 100,
  "limit": 10,
  "offset": 20,
  "next_offset": 30,
  "previous_offset": 10
}
```

### Sorting

Sorting is supported through the `order_by` query parameter:

```
GET /api/v1/customer?order_by=name      # Ascending order
GET /api/v1/customer?order_by=-name     # Descending order
GET /api/v1/customer?order_by=name,-created_at  # Multiple fields
```

### Error Handling

The API layer provides standardized error responses:

```json
{
  "error": "NOT_FOUND",
  "message": "Customer with ID 'abc123' not found",
  "detail": {```

"id": "abc123"
```
  }
}
```

## Creating Custom Endpoints

### With Domain Repositories (Recommended)

You can create custom endpoints using domain repositories and adapters:

```python
from uno.api.endpoint import UnoEndpoint
from uno.api.repository_adapter import RepositoryAdapter
from fastapi import FastAPI, Depends
from uno.dependencies.fastapi import get_repository

class CustomerEndpoint(UnoEndpoint):
    """Custom endpoint for customer operations."""
    
    def register_endpoints(self):
        """Register custom endpoints."""
        super().register_endpoints()  # Register standard endpoints
        
        @self.app.get(f"{self.prefix}/stats")
        async def stats(
            repository = Depends(get_repository(CustomerRepository))
        ):
            """Get customer statistics."""
            total = await repository.count()
            active = await repository.count_active()
            return {
                "total": total,
                "active": active,
                "inactive": total - active
            }

# Create adapter and endpoint
adapter = RepositoryAdapter(
    get_repository(CustomerRepository),
    CustomerEntity,
    CustomerSchema
)
endpoint = CustomerEndpoint(app, adapter, prefix="/api/v1/customers")
endpoint.register_endpoints()
```

### With Legacy UnoObj Pattern

You can create custom endpoints by extending the UnoEndpoint class:

```python
from uno.api.endpoint import UnoEndpoint
from fastapi import FastAPI, Depends
from uno.dependencies.fastapi import get_db_session

class CustomUserEndpoint(UnoEndpoint):
    """Custom endpoint for user statistics."""
    
    def register_endpoints(self):
        """Register custom endpoints."""
        super().register_endpoints()  # Register standard endpoints
        
        @self.app.get(f"/api/v1/{self.model.__name__.lower()}/stats")
        async def stats(session = Depends(get_db_session)):
            """Get user statistics."""
            result = await self.db.get_statistics(session)
            return result
```

### Using FastAPI Router Directly

Alternatively, you can use FastAPI's router directly with domain repositories:

```python
from fastapi import APIRouter, Depends
from uno.dependencies.fastapi import get_repository

# Create a router
router = APIRouter(prefix="/customers", tags=["Customers"])

# Define a custom endpoint with domain repository
@router.get("/stats")
async def customer_stats(
    repository = Depends(get_repository(CustomerRepository))
):
    # Get statistics
    total = await repository.count()
    active = await repository.count_active()
    
    return {
        "total": total,
        "active": active,
        "inactive": total - active
    }

# Add the router to your app
app.include_router(router)
```

## Integration with Dependency Injection

The modern domain-driven architecture fully integrates the API layer with dependency injection, which is the recommended approach:

```python
from fastapi import APIRouter, Depends, HTTPException
from uno.dependencies.fastapi import get_repository, get_service
from uno.core.result import Result

# Create a router
router = APIRouter(prefix="/customers", tags=["Customers"])

# Create endpoints with domain repositories
@router.get("/{customer_id}", response_model=CustomerDTO)
async def get_customer(
    customer_id: str,
    customer_repo = Depends(get_repository(CustomerRepository))
):
    result: Result[CustomerEntity] = await customer_repo.get_by_id(customer_id)
    
    if result.is_failure():
        raise HTTPException(status_code=404, detail=result.error.message)
    
    return CustomerDTO.from_entity(result.value)

# Create endpoints with domain services
@router.post("/", response_model=CustomerDTO, status_code=201)
async def create_customer(
    customer_data: CustomerCreateDTO,
    customer_service = Depends(get_service(CustomerService))
):
    result = await customer_service.create_customer(customer_data)
    
    if result.is_failure():
        raise HTTPException(status_code=400, detail=result.error.message)
    
    return CustomerDTO.from_entity(result.value)
```

### Using Repository Adapter with Endpoint Factory

The domain-driven approach can also use the repository adapter with the endpoint factory:

```python
from uno.api.endpoint_factory import EndpointFactory
from uno.dependencies.fastapi import get_repository

# Create customer endpoints with repository adapter
customer_router = EndpointFactory.create_endpoints(
    repository=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO,
    prefix="/customers",
    tag="Customers"
)

app.include_router(customer_router)
```

## Best Practices

1. **Use Domain-Driven Design**: Prefer domain repositories and entities over UnoObj.
   ```python
   # Recommended: Domain-driven approach
   @router.get("/{id}")
   async def get_customer(
       id: str,
       repo = Depends(get_repository(CustomerRepository))
   ):
       result = await repo.get_by_id(id)
       # Handle result and convert to DTO
       
   # Legacy: UnoObj approach
   @router.get("/{id}")
   async def get_customer(
       id: str,
       session = Depends(get_db_session)
   ):
       customer = Customer.get(id, session)
       return customer.to_dict()
   ```

2. **Use Result Type for Error Handling**: Return Result type from repository/service methods.
   ```python
   @router.post("/")
   async def create_customer(
       data: CustomerCreateDTO,
       service = Depends(get_service(CustomerService))
   ):
       result = await service.create_customer(data)
       
       if result.is_failure():
           raise HTTPException(
               status_code=result.error.status_code or 400,
               detail=result.error.message
           )
       
       return CustomerDTO.from_entity(result.value)
   ```

3. **Use DTOs for API Contracts**: Create explicit DTOs for request/response models.
   ```python
   # DTO for customer creation requests
   class CustomerCreateDTO(BaseModel):
       name: str
       email: EmailStr
       phone: Optional[str] = None
       
   # DTO for customer responses
   class CustomerDTO(BaseModel):
       id: str
       name: str
       email: str
       phone: Optional[str] = None
       created_at: datetime
       
       @classmethod
       def from_entity(cls, entity: CustomerEntity) -> "CustomerDTO":
           return cls(
               id=entity.id,
               name=entity.name,
               email=entity.email,
               phone=entity.phone,
               created_at=entity.created_at
           )
   ```

4. **Implement Validation**: Use Pydantic validation for request data.
   ```python
   # Domain validation rules
   class CustomerCreateDTO(BaseModel):
       name: str = Field(..., min_length=2, max_length=100)
       email: EmailStr
       phone: Optional[str] = Field(None, pattern=r'^\+?[0-9]{10,15}$')
       
       @validator('name')
       def name_cannot_contain_special_chars(cls, v):
           if re.search(r'[^a-zA-Z0-9 ]', v):
               raise ValueError('Name cannot contain special characters')
           return v
   ```

5. **Use Repository Adapter for Consistent Patterns**: Use repository adapters when working with UnoEndpoint.
   ```python
   # Create repository adapter
   adapter = RepositoryAdapter(
       repository_dependency=get_repository(CustomerRepository),
       entity_type=CustomerEntity,
       schema_type=CustomerDTO
   )
   
   # Create endpoint with adapter
   endpoint = UnoEndpoint(app, adapter, prefix="/customers")
   endpoint.register_endpoints()
   ```

## Related Sections

- [Domain Integration](domain-integration.md) - Detailed guide on domain-driven API integration
- [Domain Driven Design](/docs/architecture/domain_driven_design.md) - DDD architecture overview
- [Repositories](/docs/domain/repository.md) - Working with domain repositories
- [Filter Manager](/docs/queries/filter_manager.md) - Advanced filtering and query building
- [Authorization](/docs/authorization/overview.md) - Authentication and authorization
- [Dependency Injection](/docs/dependency_injection/overview.md) - Modern DI architecture