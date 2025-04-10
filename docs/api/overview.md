# API Layer Overview

The API Layer in uno provides a clean interface for exposing business logic through REST endpoints, with support for automatic endpoint generation, advanced filtering, and authorization.

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

### EndpointFactory

The `EndpointFactory` class automatically generates endpoints for business objects based on their configuration.

```python
from uno.api.endpoint_factory import EndpointFactory
from fastapi import FastAPI

# Create a FastAPI app
app = FastAPI()

# Create an endpoint factory
factory = EndpointFactory(app)

# Register endpoints for all registered business objects
factory.register_endpoints()
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

## Default Endpoints

When you register endpoints for a business object, the following endpoints are created by default:

- `POST /api/v1/{model_name}` - Create a new object
- `GET /api/v1/{model_name}/{id}` - Get an object by ID
- `GET /api/v1/{model_name}` - List objects (with filtering and pagination)
- `PATCH /api/v1/{model_name}/{id}` - Update an object
- `DELETE /api/v1/{model_name}/{id}` - Delete an object
- `PUT /api/v1/{model_name}` - Import objects (batch create or update)

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

## Best Practices

1. **Use Consistent Endpoints**: Stick to RESTful endpoint patterns for consistency.

2. **Implement Filtering**: Use the FilterManager to handle query parameters.

3. **Document Endpoints**: Use FastAPI's documentation features to document your endpoints.

4. **Handle Errors**: Provide meaningful error messages and use appropriate HTTP status codes.

5. **Implement Pagination**: Always paginate large result sets.

6. **Secure Endpoints**: Use proper authentication and authorization.

## Next Steps

- [Endpoint](endpoint.md): Learn more about the UnoEndpoint class
- [Endpoint Factory](endpoint-factory.md): Understand the endpoint factory
- [Filter Manager](../queries/filter_manager.md): Learn about the filter manager
- [Authorization](../authorization/overview.md): Learn about authentication and authorization