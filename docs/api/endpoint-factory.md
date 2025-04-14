# UnoEndpointFactory

The `UnoEndpointFactory` class automates the creation of FastAPI endpoints for `UnoObj` models. It handles the generation of RESTful API endpoints for common operations like create, read, update, and delete (CRUD).

## Overview

The endpoint factory creates standardized API endpoints based on model configurations. This ensures consistency across your API and reduces the boilerplate code needed to expose your models via a RESTful interface.

## Basic Usage

### Creating an Endpoint Factory

```python
from uno.endpoint_factory import UnoEndpointFactory

# Create an endpoint factory
endpoint_factory = UnoEndpointFactory()
```

### Creating Endpoints for a Model

```python
from fastapi import FastAPI
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes

# Create a FastAPI application
app = FastAPI()

# Define your model and business object
class CustomerModel(UnoModel):
    __tablename__ = "customer"
    # ... fields ...

class Customer(UnoObj[CustomerModel]):
    model = CustomerModel
    # ... configuration ...

# Create endpoints for the model
endpoint_factory.create_endpoints(app, Customer)
```

This will create the following endpoints:

- `POST /api/v1/customer` - Create a new customer
- `GET /api/v1/customer/{id}` - Get a customer by ID
- `GET /api/v1/customer` - List customers with filtering
- `PATCH /api/v1/customer/{id}` - Update a customer
- `DELETE /api/v1/customer/{id}` - Delete a customer
- `PUT /api/v1/customer` - Import a customer (bulk create/update)

### Customizing Endpoint Types

You can specify which types of endpoints to create:

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
class CustomerV1(UnoObj[CustomerModel]):
    model = CustomerModel
    # v1 configuration

# Create v2 endpoints with different behavior
class CustomerV2(UnoObj[CustomerModel]):
    model = CustomerModel
    # v2 configuration with additional fields or different validation

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

def test_list_endpoint(client):
    """Test the list endpoint."""
    # Make a request
    response = client.get("/api/v1/customer")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

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
