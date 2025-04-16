# UnoEndpointFactory

The `UnoEndpointFactory` class automates the creation of FastAPI endpoints for domain entities and repositories. It handles the generation of RESTful API endpoints for common operations like create, read, update, and delete (CRUD).

## Overview

The endpoint factory creates standardized API endpoints based on domain entity configurations. This ensures consistency across your API and reduces the boilerplate code needed to expose your domain entities via a RESTful interface.

The factory supports two approaches:
1. **Domain-Driven Design**: Using repositories and domain entities (recommended)
2. **Legacy Pattern**: Using model objects directly (compatible with UnoObj pattern)

## Basic Usage

### Creating an Endpoint Factory

```python
from uno.api.endpoint_factory import UnoEndpointFactory

# Create an endpoint factory
endpoint_factory = UnoEndpointFactory()
```

### Domain-Driven Approach (Recommended)

```python
from fastapi import FastAPI
from dataclasses import dataclass
from typing import Optional
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.core.protocols import Repository

# Create a FastAPI application
app = FastAPI()

# Define your domain entity
@dataclass
class UserEntity:
    email: str
    username: str
    full_name: str
    is_active: bool = True
    id: Optional[str] = None
    
    # Optional display names for API documentation
    display_name: str = "User"
    display_name_plural: str = "Users"

# Create a repository for the entity
class UserRepository(Repository):
    # Implement the Repository interface...
    async def get_by_id(self, id): pass
    async def list(self, filters=None, options=None): pass
    async def add(self, entity): pass
    async def update(self, entity): pass
    async def delete(self, id): pass

# Create a schema manager
class UserSchemaManager:
    def __init__(self):
        self.schemas = {
            "view_schema": UserViewDto,  # Define your DTOs
            "edit_schema": UserCreateDto
        }
    
    def get_schema(self, schema_name):
        return self.schemas.get(schema_name)

# Initialize components
user_repository = UserRepository()
schema_manager = UserSchemaManager()

# Create endpoints for the entity
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=schema_manager,
    path_prefix="/api/v1",
    endpoint_tags=["Users"]
)
```

### Legacy Approach (Backward Compatible)

```python
from fastapi import FastAPI
from uno.model import UnoModel
from uno.api.endpoint_factory import UnoEndpointFactory

# Create a FastAPI application
app = FastAPI()

# Define your model class
class CustomerModel(UnoModel):
    # Model definition...
    pass

# Create endpoints for the model
endpoints = endpoint_factory.create_endpoints(
    app=app,
    model_obj=CustomerModel,
    path_prefix="/api/v1",
    endpoint_tags=["Customers"]
)
```

## Generated Endpoints

The endpoint factory generates the following standard endpoints:

| Endpoint Type | HTTP Method | Path Pattern | Description |
|---------------|-------------|--------------|-------------|
| Create | POST | `/api/v1/{resource}` | Create a new entity |
| View | GET | `/api/v1/{resource}/{id}` | Get a single entity by ID |
| List | GET | `/api/v1/{resource}` | List entities with filtering |
| Update | PATCH | `/api/v1/{resource}/{id}` | Update an entity by ID |
| Delete | DELETE | `/api/v1/{resource}/{id}` | Delete an entity by ID |
| Import | PUT | `/api/v1/{resource}` | Import/bulk create entities |

For example, with a `User` entity and path prefix `/api/v1`:

- `POST /api/v1/user` - Create a new user
- `GET /api/v1/user/{id}` - Get a user by ID
- `GET /api/v1/user` - List users with filtering
- `PATCH /api/v1/user/{id}` - Update a user
- `DELETE /api/v1/user/{id}` - Delete a user
- `PUT /api/v1/user` - Import/bulk create users

## Customizing Endpoints

### Selecting Specific Endpoints

You can specify which endpoints to create:

```python
# Create only read endpoints
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=schema_manager,
    endpoints=["View", "List"],  # Only these endpoints
    path_prefix="/api/v1"
)
```

### Using a Custom Router

You can use a custom router instead of the app directly:

```python
from fastapi import APIRouter

# Create a router
custom_router = APIRouter(prefix="/api/v1/custom")

# Create endpoints with the router
endpoints = endpoint_factory.create_endpoints(
    router=custom_router,  # Use router instead of app
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=schema_manager
)

# Include the router in your app
app.include_router(custom_router)
```

### Adding Path Prefix

You can customize the path prefix:

```python
# Create endpoints with a custom path prefix
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=schema_manager,
    path_prefix="/api/v2",  # Custom prefix
)
```

### Setting Custom Status Codes

You can customize the status codes:

```python
# Create endpoints with custom status codes
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=schema_manager,
    status_codes={
        "Create": 201,  # Created
        "Delete": 204,  # No Content
    }
)
```

### Adding Dependencies

You can add dependencies to the endpoints:

```python
from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create endpoints with dependencies
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=schema_manager,
    dependencies=[Depends(oauth2_scheme)],  # Add to all endpoints
)
```

## Advanced Usage

### Custom Endpoint Types

You can register custom endpoint types:

```python
from uno.api.endpoint import UnoRouter, UnoEndpoint

# Create a custom router
class ReportRouter(UnoRouter):
    path_suffix: str = "/report"
    method: str = "GET"
    
    # Define endpoint behavior...
    def endpoint_factory(self):
        async def endpoint(self):
            # Generate report...
            return {"report": "data"}
        
        setattr(self.__class__, "endpoint", endpoint)

# Create a custom endpoint
class ReportEndpoint(UnoEndpoint):
    router = ReportRouter
    
# Register the custom endpoint
endpoint_factory.register_endpoint_type("Report", ReportEndpoint)

# Use the custom endpoint
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=schema_manager,
    endpoints=["List", "Report"],  # Include custom endpoint
)
```

### Direct Repository Adapter Usage

You can create a repository adapter directly:

```python
from uno.api.repository_adapter import RepositoryAdapter

# Create adapter
adapter = RepositoryAdapter(
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
)

# Create endpoints using the adapter
endpoints = endpoint_factory.create_endpoints(
    app=app,
    model_obj=adapter,  # Use adapter directly
    endpoints=["List", "View"],
)
```

### Specialized Adapters

You can use specialized repository adapters for specific use cases:

```python
from uno.api.repository_adapter import ReadOnlyRepositoryAdapter, BatchRepositoryAdapter

# Read-only adapter
read_adapter = ReadOnlyRepositoryAdapter(
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
)

# Batch operations adapter
batch_adapter = BatchRepositoryAdapter(
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
)
```

## Endpoint Features

All endpoints created by the factory include:

1. **Request Validation**: Input validation using Pydantic models
2. **Response Serialization**: Output serialization to JSON
3. **Error Handling**: Standardized error responses
4. **OpenAPI Documentation**: Automatic documentation generation
5. **Field Selection**: Support for selecting specific fields to return
6. **Pagination**: Support for paginating list results
7. **Filtering**: Support for filtering list results

### Example of Field Selection

All endpoints support field selection:

```
GET /api/v1/user/123?fields=id,email,username
```

This returns only the specified fields:

```json
{
  "id": "123",
  "email": "user@example.com",
  "username": "user123"
}
```

### Example of Pagination

List endpoints support pagination:

```
GET /api/v1/user?page=2&page_size=10
```

### Example of Filtering

List endpoints support filtering:

```
GET /api/v1/user?username=john&is_active=true
```

## Best Practices

1. **Use Domain Repositories**: Prefer the domain-driven approach with repositories.
2. **Define Clear Entity Boundaries**: Each entity should have its own repository.
3. **Create Specific DTOs**: Define specific DTOs for different operations.
4. **Use Dependency Injection**: Add dependencies for authorization and validation.
5. **Apply Consistent Path Prefixes**: Use consistent path prefixes for API versioning.
6. **Document Your API**: Add descriptions and examples to your schemas.
7. **Test Your Endpoints**: Create tests for your API endpoints.
8. **Secure Your API**: Add authentication and authorization.
9. **Use Transaction Handling**: Implement proper transaction handling in repositories.
10. **Handle Errors Gracefully**: Provide clear error messages.

## Related Documentation

- [Domain Integration](domain-integration.md): Detailed guide on domain-driven integration
- [API Overview](overview.md): Overview of the API system
- [Repository Adapter](repository-adapter.md): Guide to repository adapters
- [Workflows API](workflows.md): Comprehensive reference for the Workflow System API

```python
# Create only specific endpoint types
endpoint_factory.create_endpoints(
    app,
    Customer,
    endpoints=["Create", "View", "List"]  # Only these endpoints will be created
)
```

Available endpoint types:

- `Create` - POST endpoint for creating new objects
- `View` - GET endpoint for retrieving a single object
- `List` - GET endpoint for listing objects with filtering
- `Update` - PATCH endpoint for updating an object
- `Delete` - DELETE endpoint for deleting an object
- `Import` - PUT endpoint for importing/bulk creating objects

### Adding Custom Tags

You can add custom tags to the endpoints for better API documentation:

```python
# Add custom tags
endpoint_factory.create_endpoints(
    app,
    Customer,
    endpoint_tags=["customers", "core-api"]
)
```

## Advanced Usage

### Custom Endpoint Creation

You can create endpoints manually using the endpoint classes:

```python
from uno.endpoint import CreateEndpoint, ViewEndpoint
from fastapi import FastAPI

app = FastAPI()

# Create a specific endpoint
CreateEndpoint(
    model=Customer,
    app=app,
)

# Create a custom view endpoint
ViewEndpoint(
    model=Customer,
    app=app,
)
```

### Custom Routes

You can create custom routes that leverage the standard endpoints:

```python
from fastapi import FastAPI, Depends, HTTPException
from typing import List

app = FastAPI()

# Create standard endpoints
endpoint_factory.create_endpoints(app, Customer)

# Add a custom route
@app.get("/api/v1/customers/search")
async def search_customers(q: str):
    """Search customers by name or email."""
    if len(q) < 3:
        raise HTTPException(status_code=400, detail="Search term must be at least 3 characters")
    
    # Create filter parameters
    filter_params = Customer.create_filter_params()(
        name__i_contains=q,
        limit=10
    )
    
    # Validate and filter
    validated_filters = Customer.validate_filter_params(filter_params)
    return await Customer.filter(filters=validated_filters)
```

### Adding Middleware

You can add middleware to customize request/response handling:

```python
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Callable

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Process request
        print(f"Request: {request.method} {request.url.path}")
        
        # Call next middleware or endpoint
        response = await call_next(request)
        
        # Process response
        print(f"Response: {response.status_code}")
        return response
```

# Create FastAPI app with middleware
app = FastAPI()
app.add_middleware(LoggingMiddleware)

# Create endpoints
endpoint_factory.create_endpoints(app, Customer)
```

### Authentication and Authorization

You can integrate authentication and authorization:

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Implement token validation and user lookup
    # This is just a placeholder - implement your own auth logic
    if token != "valid_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": "testuser"}
```

# Create the app
app = FastAPI()

# Create protected endpoints for Customer
@app.get("/api/v1/customers")
async def list_customers(
    current_user = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """List customers with authorization."""
    # Implement authorization check
    # e.g., check if user has permission to list customers
    
    # Create filter parameters
    filter_params = Customer.create_filter_params()(
        limit=limit,
        offset=offset
    )
    
    # Validate and filter
    validated_filters = Customer.validate_filter_params(filter_params)
    return await Customer.filter(filters=validated_filters)
```

## Common Patterns

### Versioned API Endpoints

Create different versions of your API:

```python
from fastapi import FastAPI, APIRouter

# Create the main app
app = FastAPI()

# Create versioned routers
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

# Create a factory for each version
v1_factory = UnoEndpointFactory()
v2_factory = UnoEndpointFactory()

# Create v1 endpoints
class CustomerV1(UnoObj[CustomerModel]):```

model = CustomerModel
# v1 configuration
```

# Create v2 endpoints with different behavior
class CustomerV2(UnoObj[CustomerModel]):```

model = CustomerModel
# v2 configuration with additional fields or different validation
```

# Create endpoints for each version
v1_factory.create_endpoints(v1_router, CustomerV1)
v2_factory.create_endpoints(v2_router, CustomerV2)

# Include routers in the main app
app.include_router(v1_router)
app.include_router(v2_router)
```

### Custom Response Models

Customize the response models for endpoints:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from uno.endpoint import ViewEndpoint, ListEndpoint

# Define a custom response model
class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    # Add computed fields
    full_name: Optional[str] = None
    status: str = "active"
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "name": "John Doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "status": "active"
            }
        }
```

# Create endpoints with custom response models
ViewEndpoint(
    model=Customer,
    app=app,
    response_model=CustomerResponse
)

# For list endpoint
ListEndpoint(
    model=Customer,
    app=app,
    response_model=CustomerResponse
)
```

### Customizing Endpoint Behavior

Override the endpoint factory method to customize behavior:

```python
from uno.endpoint_factory import UnoEndpointFactory

class CustomEndpointFactory(UnoEndpointFactory):
    def create_endpoints(self, app, model_obj, endpoints=None, endpoint_tags=None):
        """Custom endpoint creation with additional behavior."""
        # Call parent method
        super().create_endpoints(app, model_obj, endpoints, endpoint_tags)
        
        # Add custom behavior
        model_name = model_obj.__name__.lower()
        
        # Add a custom export endpoint
        @app.get(f"/api/v1/{model_name}/export")
        async def export_data():
            """Export all data as CSV."""
            # Implement export logic
            return {"message": f"Exporting {model_name} data"}
```

# Use the custom factory
custom_factory = CustomEndpointFactory()
custom_factory.create_endpoints(app, Customer)
```

## Testing

When testing endpoints created by the factory, focus on API behavior:

```python
from fastapi.testclient import TestClient
import pytest

# Create a test client
@pytest.fixture
def client():
    # Create app and endpoints
    app = FastAPI()
    endpoint_factory = UnoEndpointFactory()
    endpoint_factory.create_endpoints(app, Customer)
    
    return TestClient(app)
```

def test_list_endpoint(client):
    """Test the list endpoint."""
    # Make a request
    response = client.get("/api/v1/customer")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

def test_create_endpoint(client):
    """Test the create endpoint."""
    # Create test data
    test_data = {
        "name": "Test Customer",
        "email": "test@example.com"
    }
    
    # Make a request
    response = client.post("/api/v1/customer", json=test_data)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_data["name"]
    assert data["email"] == test_data["email"]
    assert "id" in data  # Should have an ID
```

## Best Practices

1. **Consistent API Design**: Use the endpoint factory to ensure consistent API design across your application.

2. **Document Endpoints**: Use FastAPI's automatic documentation features to describe your endpoints.

3. **Validate Input Data**: Ensure your schemas properly validate input data before processing.

4. **Handle Errors Consistently**: Implement consistent error handling across endpoints.

5. **Use Dependency Injection**: Leverage FastAPI's dependency injection for common functionality.

6. **Add Rate Limiting**: Consider adding rate limiting for public-facing APIs.

7. **Monitor Performance**: Track endpoint performance to identify bottlenecks.

8. **Version Your API**: Use versioning to make non-backward-compatible changes.

9. **Test Thoroughly**: Test all endpoints with various inputs, including edge cases.

10. **Secure Endpoints**: Implement proper authentication and authorization.
