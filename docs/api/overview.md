# API Layer Overview

The API Layer in uno provides a clean interface for exposing business logic through REST endpoints, with support for automatic endpoint generation, advanced filtering, and authorization.

## Architecture

The API layer integrates with the other components of the Uno framework to provide a complete solution:

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  API Client   │      │  UnoEndpoint  │      │    UnoObj     │      │    UnoDB      │
│  (HTTP/JSON)  │◄────►│  (FastAPI)    │◄────►│ (Business Logic) ◄────►│  (Database)   │
└───────────────┘      └───────────────┘      └───────────────┘      └───────────────┘
```

## Data Flow

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
from uno.api.endpoint_factory import UnoEndpointFactory
from fastapi import FastAPI
from uno.authorization.objs import User

# Create FastAPI app
app = FastAPI()

# Create endpoint factory
factory = UnoEndpointFactory()

# Create endpoints for User model
factory.create_endpoints(
    app=app,
    model_obj=User,
    endpoints=["List", "View", "Create", "Update", "Delete"]
)
```

### FilterManager

The `FilterManager` class handles query parameters and filtering for API endpoints.

```python
from uno.queries.filter_manager import FilterManager
from uno.queries.filter import FilterParam

# Create a filter manager
filter_manager = FilterManager()

# Create filter parameters from query parameters
filter_params = FilterParam(
    limit=10,
    offset=0,
    name__contains="John",
    status__in=["active", "pending"]
)

# Apply filters to a query
filtered_query = filter_manager.apply_filters(query, filter_params)
```

## Integration with UnoObj and UnoDB

The API layer is tightly integrated with the UnoObj and UnoDB layers:

1. **UnoObj Integration**:
   - Endpoints use UnoObj methods for business logic
   - Uses schemas from UnoObj's SchemaManager
   - Converts between HTTP/JSON and UnoObj representations

2. **UnoDB Integration**:
   - Database operations are delegated to UnoObj methods
   - Uses UnoObj to convert between UnoModel and API schemas
   - Handles transaction management

## Default Endpoints

When you register endpoints for a business object, the following endpoints are created by default:

- `POST /api/v1/{model_name}` - Create a new object (CreateEndpoint)
- `GET /api/v1/{model_name}/{id}` - Get an object by ID (ViewEndpoint)
- `GET /api/v1/{model_name}` - List objects with filtering and pagination (ListEndpoint)
- `PATCH /api/v1/{model_name}/{id}` - Update an object (UpdateEndpoint)
- `DELETE /api/v1/{model_name}/{id}` - Delete an object (DeleteEndpoint)
- `PUT /api/v1/{model_name}` - Import objects (batch create or update) (ImportEndpoint)

You can customize which endpoints are created by setting the `endpoints` class variable in your `UnoObj` subclass:

```python
class Customer(UnoObj[CustomerModel]):
    model = CustomerModel
    endpoints = ["Create", "View", "List"]  # Only these endpoints will be created
```

## Filtering

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

## Pagination

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

## Sorting

Sorting is supported through the `order_by` query parameter:

```
GET /api/v1/customer?order_by=name
```

For descending order, use a minus sign:

```
GET /api/v1/customer?order_by=-name
```

For multiple sort fields, separate them with commas:

```
GET /api/v1/customer?order_by=name,-created_at
```

## Error Handling

The API layer provides standardized error responses:

```json
{
  "error": "NOT_FOUND",
  "message": "Customer with ID 'abc123' not found",
  "detail": {
    "id": "abc123"
  }
}
```

## Custom Endpoints

You can create custom endpoints by extending the UnoEndpoint class:

```python
from uno.api.endpoint import UnoEndpoint
from fastapi import FastAPI

class CustomUserEndpoint(UnoEndpoint):
    """Custom endpoint for user statistics."""
    
    def __init__(self, model, app, **kwargs):
        super().__init__(model, app, **kwargs)
        
        @app.get(f"/api/v1/{self.model.__name__.lower()}/stats")
        async def stats():
            """Get user statistics."""
            result = await self.model.get_statistics()
            return result
```

## Complete Integration Example

This example demonstrates the complete integration of UnoObj, UnoModel, UnoDB, and UnoEndpoint:

```python
from fastapi import FastAPI
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.authorization.objs import User

# Create a FastAPI app
app = FastAPI()

# Create a User object
user = User(
    email="john@example.com",
    handle="john_doe",
    full_name="John Doe",
    is_superuser=False
)

# 1. Convert UnoObj to UnoModel via schema
user._ensure_schemas_created()
user_model = user.to_model(schema_name="edit_schema")

# 2. Save to database using UnoDB
db = UnoDBFactory(user)
saved_model, success = await db.create(user_model)

# 3. Create API endpoints for User
factory = UnoEndpointFactory()
factory.create_endpoints(
    app=app,
    model_obj=User,
    endpoints=["List", "View"]
)

# 4. Client accesses the API
# GET /api/v1/user - Lists all users
# GET /api/v1/user/{id} - Gets a specific user

# 5. Endpoint returns data via schema
# Response data is converted to a Pydantic schema
# Schema can be used to recreate UnoObj instance
```

## Best Practices

1. **Use Consistent Endpoints**: Stick to RESTful endpoint patterns for consistency.

2. **Implement Filtering**: Use the FilterManager to handle query parameters.

3. **Document Endpoints**: Use FastAPI's documentation features to document your endpoints.

4. **Handle Errors**: Provide meaningful error messages and use appropriate HTTP status codes.

5. **Implement Pagination**: Always paginate large result sets.

6. **Secure Endpoints**: Use proper authentication and authorization.

7. **Test Integration**: Create integration tests that verify the complete flow from UnoObj to API endpoints and back.

## Next Steps

- [Endpoint](endpoint.md): Learn more about the UnoEndpoint class
- [Endpoint Factory](endpoint-factory.md): Understand the endpoint factory
- [Filter Manager](../queries/filter_manager.md): Learn about the filter manager
- [Authorization](../authorization/overview.md): Learn about authentication and authorization