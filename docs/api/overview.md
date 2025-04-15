# API Layer

The API Layer in uno provides a clean interface for exposing business logic through REST endpoints, with support for automatic endpoint generation, advanced filtering, and authorization.

## In This Section

- [Endpoint](endpoint.md) - Core UnoEndpoint class for API interfaces
- [Endpoint Factory](endpoint-factory.md) - Automatic endpoint generation
- [Schemas](schemas.md) - Data validation and serialization
- [Schema Manager](schema-manager.md) - Schema creation and management

## Overview

The API Layer sits between client applications and the business logic layer, providing a standardized interface for accessing and manipulating data through HTTP/JSON. It's designed to automate common API patterns while allowing for customization and extension.

## Architecture

The API layer integrates with the other components of uno to provide a complete solution:

```
┌───────────────┐      ┌───────────────┐      ┌─────────────────┐      ┌───────────────┐
│  API Client   │      │  UnoEndpoint  │      │     UnoObj      │      │    UnoDB      │
│  (HTTP/JSON)  │◄────►│  (FastAPI)    │◄────►│ (Business Logic)|◄────►│  (Database)   │
└───────────────┘      └───────────────┘      └─────────────────┘      └───────────────┘
```

### Request Flow (Inbound)

1. **HTTP Request**: Client sends HTTP request to endpoint
2. **Validation**: Request data is validated using Pydantic schema
3. **Deserialization**: JSON data is converted to Pydantic model
4. **Business Logic**: UnoObj processes the request
5. **Database Operation**: UnoDB performs the database operation
6. **Response**: Results are serialized and returned to client

### Response Flow (Outbound)

1. **Database Query**: Data is retrieved from database
2. **Model Mapping**: Data is mapped to UnoModel
3. **Schema Conversion**: Model is converted to schema using SchemaManager
4. **Serialization**: Schema is serialized to JSON
5. **HTTP Response**: JSON is returned to client

## Key Components

### UnoEndpoint

The `UnoEndpoint` class is a FastAPI-based endpoint implementation that exposes CRUD operations for business objects.

```python
from uno.api.endpoint import UnoEndpoint
from fastapi import FastAPI

# Create a FastAPI app
app = FastAPI()

# Create an endpoint for the Customer class
endpoint = UnoEndpoint(app, Customer)

# Register endpoints
endpoint.register_endpoints()
```

### UnoEndpointFactory

The `UnoEndpointFactory` class automatically generates endpoints for business objects based on their configuration.

```python
from uno.api.endpoint_factory import EndpointFactory
from fastapi import FastAPI
from uno.dependencies.fastapi import get_db_session

# Create FastAPI app
app = FastAPI()

# Create endpoints for Customer model
customer_router = EndpointFactory.create_endpoints(```

obj_class=Customer,
prefix="/customers",
tag="Customers",
session_dependency=get_db_session
```
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

You can create custom endpoints by extending the UnoEndpoint class:

```python
from uno.api.endpoint import UnoEndpoint
from fastapi import FastAPI, Depends
from uno.dependencies.fastapi import get_db_session

class CustomUserEndpoint(UnoEndpoint):```

"""Custom endpoint for user statistics."""
``````

```
```

def register_endpoints(self):```

"""Register custom endpoints."""
super().register_endpoints()  # Register standard endpoints
``````

```
```

@self.app.get(f"/api/v1/{self.model.__name__.lower()}/stats")
async def stats(session = Depends(get_db_session)):
    """Get user statistics."""
    result = await self.db.get_statistics(session)
    return result
```
```
```

Alternatively, you can use FastAPI's router directly:

```python
from fastapi import APIRouter, Depends
from uno.dependencies.fastapi import get_db_session
from uno.database.repository import UnoBaseRepository

# Create a router
router = APIRouter(prefix="/customers", tags=["Customers"])

# Define a custom endpoint
@router.get("/stats")
async def customer_stats(session = Depends(get_db_session)):```

# Create a repository
repo = UnoBaseRepository(session, CustomerModel)
``````

```
```

# Get statistics
total = await repo.count()
active = await repo.count(CustomerModel.is_active == True)
``````

```
```

return {```

"total": total,
"active": active,
"inactive": total - active
```
}
```

# Add the router to your app
app.include_router(router)
```

## Integration with Dependency Injection

The modern uno architecture integrates the API layer with dependency injection:

```python
from fastapi import APIRouter, Depends
from uno.dependencies.fastapi import get_db_session, get_repository

# Create a router
router = APIRouter(prefix="/customers", tags=["Customers"])

# Create endpoints with dependency injection
@router.get("/{customer_id}")
async def get_customer(```

customer_id: str,
customer_repo = Depends(get_repository(CustomerRepository))
```
):```

customer = await customer_repo.get_by_id(customer_id)
if not customer:```

raise HTTPException(status_code=404, detail="Customer not found")
```
return customer
```

@router.post("/")
async def create_customer(```

customer_data: CustomerCreateSchema,
customer_service = Depends(get_service(CustomerService))
```
):```

try:```

customer = await customer_service.create_customer(customer_data)
return customer
```
except ValidationError as e:```

raise HTTPException(status_code=400, detail=str(e))
```
```
```

## Best Practices

1. **Use Consistent Endpoints**: Stick to RESTful endpoint patterns for consistency.
   ```python
   # Good
   @router.get("/{id}")       # Get by ID
   @router.get("/")           # List with filters
   @router.post("/")          # Create
   
   # Avoid
   @router.get("/fetch/{id}") # Non-standard naming
   @router.get("/list")       # Redundant action in URL
   ```

2. **Implement Filtering**: Use the FilterManager to handle query parameters.
   ```python
   @router.get("/")
   async def list_customers(```

   filter_params: FilterParams = Depends(),
   repo = Depends(get_repository(CustomerRepository))
```
   ):```

   filter_manager = FilterManager()
   return await repo.filter(filter_manager.build_filters(filter_params))
```
   ```

3. **Document Endpoints**: Use FastAPI's documentation features to document your endpoints.
   ```python
   @router.get(```

   "/{id}", 
   response_model=CustomerSchema,
   summary="Get customer by ID",
   description="Retrieves a customer by their unique identifier"
```
   )
   async def get_customer(id: str):
       """
       Get a customer by ID.
       
       - **id**: The customer ID
       
       Returns the customer details if found, or 404 if not found.
       """```

   # Implementation
```
   ```

4. **Use Appropriate Status Codes**: Return appropriate HTTP status codes for different scenarios.
   ```python
   @router.post("/", status_code=201)  # Created
   async def create_customer(customer: CustomerCreateSchema):```

   # Implementation
   
```
   @router.delete("/{id}", status_code=204)  # No Content
   async def delete_customer(id: str):```

   # Implementation
```
   ```

5. **Implement Pagination**: Always paginate large result sets.
   ```python
   @router.get("/")
   async def list_customers(```

   limit: int = 10,
   offset: int = 0,
   repo = Depends(get_repository(CustomerRepository))
```
   ):```

   results = await repo.get_all(limit=limit, offset=offset)
   count = await repo.count()
   return {```

   "data": results,
   "total_count": count,
   "limit": limit,
   "offset": offset
```
   }
```
   ```

## Related Sections

- [Business Logic](/docs/business_logic/overview.md) - UnoObj implementation for business logic
- [Filter Manager](/docs/queries/filter_manager.md) - Advanced filtering and query building
- [Authorization](/docs/authorization/overview.md) - Authentication and authorization
- [Dependency Injection](/docs/dependency_injection/overview.md) - Modern DI architecture