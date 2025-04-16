# Domain-Driven API Integration

This guide explains how to integrate domain-driven design with API endpoints in the Uno framework. The API module has been completely redesigned to support a clean domain-driven approach, while maintaining compatibility with legacy patterns.

## Overview

The Uno framework provides a seamless way to expose domain entities via RESTful API endpoints. The key components of this integration are:

1. **Domain Entities** - Core business objects (`ApiResource`, `EndpointConfig`)
2. **Domain Repositories** - Data access interfaces and implementations
3. **Domain Services** - Business logic for API operations
4. **Domain Provider** - Dependency injection configuration
5. **Repository Adapters** - Bridge between domain repositories and API endpoints

This approach follows domain-driven design principles by keeping your domain logic separate from your API presentation layer while still providing a convenient way to expose your domain entities to clients.

## Basic Usage

### 1. Define Your Domain Entity

```python
from dataclasses import dataclass
from typing import Optional

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
```

### 2. Create Data Transfer Objects (DTOs)

```python
from pydantic import BaseModel

class UserCreateDto(BaseModel):
    """DTO for creating users."""
    email: str
    username: str
    full_name: str
    is_active: bool = True

class UserViewDto(BaseModel):
    """DTO for viewing users."""
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool
```

### 3. Create a Schema Manager

```python
class UserSchemaManager:
    """Schema manager for user entities."""
    
    def __init__(self):
        self.schemas = {
            "view_schema": UserViewDto,
            "edit_schema": UserCreateDto,
            # Add other schemas as needed
        }
    
    def get_schema(self, schema_name: str) -> type[BaseModel]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)
```

### 4. Implement a Repository

```python
from uno.core.protocols import Repository
from typing import Dict, List, Optional, Any

class UserRepository(Repository):
    """Repository for user entities."""
    
    def __init__(self):
        self.users = {}  # In-memory store for example
    
    async def get_by_id(self, id: str) -> Optional[UserEntity]:
        """Get a user by ID."""
        return self.users.get(id)
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[UserEntity]:
        """List users with optional filtering and pagination."""
        # Implementation details...
        return list(self.users.values())
    
    async def add(self, entity: UserEntity) -> UserEntity:
        """Add a user to the repository."""
        self.users[entity.id] = entity
        return entity
    
    async def update(self, entity: UserEntity) -> UserEntity:
        """Update a user in the repository."""
        self.users[entity.id] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        """Delete a user from the repository."""
        if id in self.users:
            del self.users[id]
            return True
        return False
```

### 5. Create API Endpoints

```python
from fastapi import FastAPI
from uno.api.endpoint_factory import UnoEndpointFactory

app = FastAPI()

# Create repository and schema manager
user_repository = UserRepository()
user_schema_manager = UserSchemaManager()

# Create endpoint factory
endpoint_factory = UnoEndpointFactory()

# Create endpoints for the User entity
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
    endpoints=["Create", "View", "List", "Update", "Delete"],
    path_prefix="/api/v1",
    endpoint_tags=["Users"],
)
```

This will create the following RESTful endpoints:

- `POST /api/v1/user` - Create a new user
- `GET /api/v1/user/{id}` - Get a user by ID
- `GET /api/v1/user` - List users with filtering and pagination
- `PATCH /api/v1/user/{id}` - Update a user
- `DELETE /api/v1/user/{id}` - Delete a user

## Advanced Usage

### Customizing Endpoints

You can customize which endpoints are created by specifying the endpoint types:

```python
# Create only read endpoints
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
    endpoints=["View", "List"],  # Only these endpoints will be created
    path_prefix="/api/v1",
)
```

### Adding Dependencies

You can add dependencies to the endpoints for authorization, validation, etc.:

```python
from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create endpoints with authorization dependency
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
    dependencies=[Depends(oauth2_scheme)],  # Will be added to all endpoints
    path_prefix="/api/v1",
)
```

### Read-Only Repository

For read-only access, you can use a read-only repository adapter:

```python
from uno.api.repository_adapter import ReadOnlyRepositoryAdapter

# Create a read-only adapter
read_only_adapter = ReadOnlyRepositoryAdapter(
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
)

# Create only read endpoints
endpoints = endpoint_factory.create_endpoints(
    app=app,
    model_obj=read_only_adapter,  # Use adapter directly
    endpoints=["View", "List"],
    path_prefix="/api/v1",
)
```

### Batch Operations

For repositories that support batch operations, you can use the BatchRepositoryAdapter:

```python
from uno.api.repository_adapter import BatchRepositoryAdapter

# Create a batch adapter
batch_adapter = BatchRepositoryAdapter(
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
)

# The Import endpoint will now use batch operations
endpoints = endpoint_factory.create_endpoints(
    app=app,
    model_obj=batch_adapter,  # Use adapter directly
    endpoints=["Import", "List"],
    path_prefix="/api/v1",
)
```

## Understanding the Repository Adapter

The repository adapter is a bridge between your domain repositories and the API endpoint system. It:

1. Converts between domain entities and DTOs
2. Handles common operations like filtering and pagination
3. Provides error handling and logging
4. Implements methods compatible with the endpoint system

You can create a repository adapter manually:

```python
from uno.api.repository_adapter import RepositoryAdapter

adapter = RepositoryAdapter(
    repository=user_repository,
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
)
```

Or let the endpoint factory create it automatically:

```python
endpoints = endpoint_factory.create_endpoints(
    app=app,
    repository=user_repository,  # Adapter created automatically
    entity_type=UserEntity,
    schema_manager=user_schema_manager,
)
```

## Complete Example

Here's a complete example including an app with demo data:

```python
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from uno.api.endpoint_factory import UnoEndpointFactory
from uno.core.protocols import Repository


# Domain entity
@dataclass
class UserEntity:
    email: str
    username: str
    full_name: str
    is_active: bool = True
    id: Optional[str] = None
    
    display_name: str = "User"
    display_name_plural: str = "Users"
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid4())


# API Schemas (DTOs)
class UserCreateDto(BaseModel):
    email: str
    username: str
    full_name: str
    is_active: bool = True

class UserViewDto(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool


# Schema Manager
class UserSchemaManager:
    def __init__(self):
        self.schemas = {
            "view_schema": UserViewDto,
            "edit_schema": UserCreateDto,
        }
    
    def get_schema(self, schema_name: str) -> type[BaseModel]:
        return self.schemas.get(schema_name)


# Repository
class UserRepository(Repository):
    def __init__(self):
        self.users = {}
    
    async def get_by_id(self, id: str) -> Optional[UserEntity]:
        return self.users.get(id)
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[UserEntity]:
        return list(self.users.values())
    
    async def add(self, entity: UserEntity) -> UserEntity:
        if not entity.id:
            entity.id = str(uuid4())
        self.users[entity.id] = entity
        return entity
    
    async def update(self, entity: UserEntity) -> UserEntity:
        if entity.id not in self.users:
            return None
        self.users[entity.id] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        if id in self.users:
            del self.users[id]
            return True
        return False


# API Endpoint Setup
def create_app() -> FastAPI:
    app = FastAPI(title="Domain-Driven API Example")
    
    # Create repository and schema manager
    user_repository = UserRepository()
    user_schema_manager = UserSchemaManager()
    
    # Create endpoint factory
    endpoint_factory = UnoEndpointFactory()
    
    # Create endpoints for the User entity
    endpoints = endpoint_factory.create_endpoints(
        app=app,
        repository=user_repository,
        entity_type=UserEntity,
        schema_manager=user_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix="/api/v1",
        endpoint_tags=["Users"],
    )
    
    # Add demo data
    @app.on_event("startup")
    async def add_demo_data():
        # Create some demo users
        demo_users = [
            UserEntity(
                email="john@example.com",
                username="john",
                full_name="John Doe",
            ),
            UserEntity(
                email="jane@example.com",
                username="jane",
                full_name="Jane Smith",
            ),
        ]
        
        # Add demo users to repository
        for user in demo_users:
            await user_repository.add(user)
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## New Domain-Driven Design Implementation

The API module now includes a full domain-driven design implementation with clear separation of concerns. This section covers the new approach for integrating APIs with domain-driven design.

### Setting Up the Provider

Before using the API module, you need to configure the dependency injection provider:

```python
from uno.api import ApiProvider

# Configure with in-memory repositories (default)
ApiProvider.configure()

# Or configure with file-based persistence
ApiProvider.configure(persistence_directory="/path/to/data")

# Or configure with custom repositories
ApiProvider.configure(
    resource_repository=CustomApiResourceRepository(),
    endpoint_repository=CustomEndpointConfigRepository()
)
```

### Creating API Resources and Endpoints

Once configured, you can use the provider to access services:

```python
import asyncio
from uno.api import ApiProvider

async def create_api_resources():
    # Get the API resource service
    api_service = ApiProvider.get_api_resource_service()
    
    # Create a resource
    customer_resource = await api_service.create_resource(
        name="Customers",
        path_prefix="/api/v1/customers",
        entity_type_name="Customer",
        tags=["Customers"],
        description="Customer management API"
    )
    
    # Add an endpoint
    await api_service.add_endpoint_to_resource(
        resource_id=customer_resource.value.id,
        path="/api/v1/customers/{id}",
        method="GET",
        summary="Get customer by ID",
        description="Retrieves a customer by their unique identifier"
    )

# Run the async function
asyncio.run(create_api_resources())
```

### Generating CRUD Endpoints Automatically

You can automatically generate CRUD endpoints for an entity type:

```python
import asyncio
from uno.api import ApiProvider

async def create_crud_endpoints():
    # Get the endpoint factory service
    factory_service = ApiProvider.get_endpoint_factory_service()
    
    # Create CRUD endpoints
    result = await factory_service.create_crud_endpoints(
        resource_name="Products",
        entity_type_name="Product",
        path_prefix="/api/v1/products",
        tags=["Products"],
        description="Product management API"
    )
    
    # Print the created resource
    if result.is_success():
        print(f"Created resource: {result.value.name}")
        print(f"Created endpoints: {len(result.value.endpoints)}")
    else:
        print(f"Error: {result.error.message}")

# Run the async function
asyncio.run(create_crud_endpoints())
```

### Integrating with FastAPI

The API module includes a preconfigured FastAPI router for API resource management:

```python
from fastapi import FastAPI
from uno.api import ApiProvider, api_resource_router

# Configure the provider
ApiProvider.configure()

# Create FastAPI app
app = FastAPI()

# Include the API resource router
app.include_router(api_resource_router)
```

This router provides endpoints for managing API resources and their endpoints, which can be accessed at `/api/v1/api-resources`.

### Creating Adapters for Domain Repositories

To bridge your domain repositories with the API layer, use the repository adapter service:

```python
from uno.api import ApiProvider
from uno.dependencies.fastapi import get_repository

# Get the adapter service
adapter_service = ApiProvider.get_repository_adapter_service()

# Create an adapter for the repository
customer_adapter = adapter_service.create_adapter(
    repository=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    schema_type=CustomerSchema
)

# Use the adapter with FastAPI
@app.get("/api/v1/customers/{id}")
async def get_customer(id: str):
    customer = await customer_adapter.get(id)
    if customer:
        return customer
    raise HTTPException(status_code=404, detail="Customer not found")
```

### Testing

For testing, use the `TestingApiProvider`:

```python
from uno.api import TestingApiProvider
from unittest.mock import Mock

# Mock repositories
mock_resource_repo = Mock()
mock_endpoint_repo = Mock()

# Configure test container
dependencies = TestingApiProvider.configure(
    resource_repository=mock_resource_repo,
    endpoint_repository=mock_endpoint_repo
)

# Access configured services for testing
api_service = dependencies["api_service"]
factory_service = dependencies["endpoint_factory_service"]
```

## Best Practices

1. **Use the Provider**: Always configure the `ApiProvider` before using API services.
2. **Prefer Domain Repositories**: Use domain repositories instead of direct database access.
3. **Use Repository Adapters**: Bridge your domain repositories with the API layer using adapters.
4. **Implement Error Handling**: Use the `Result` pattern for consistent error handling.
5. **Create API Resources**: Define API resources for related endpoints to maintain organization.
6. **Validate Inputs**: Use Pydantic models for request validation.
7. **Document with OpenAPI**: Add descriptions, summaries, and tags to endpoints.
8. **Test with TestingApiProvider**: Use the testing provider for unit tests.
9. **Pagination**: Always paginate list endpoints for large datasets.
10. **Versioning**: Use versioning in your API URLs.

## Migration from UnoObj Pattern

If you're migrating from the UnoObj pattern to domain-driven design, here's a step-by-step approach:

1. **Configure the ApiProvider**: Set up the dependency injection provider.
2. **Create Domain Entities**: Convert your UnoObj classes to domain entities.
3. **Implement Domain Repositories**: Create repositories for your entities.
4. **Create DTOs**: Define your API schemas as Pydantic models.
5. **Create Repository Adapters**: Use the adapter service to bridge repositories and endpoints.
6. **Register with Service**: Use the endpoint factory service to create standard endpoints.
7. **Update FastAPI Application**: Include the generated routers in your app.

### Legacy Approach

```python
from uno.api import UnoEndpointFactory
from fastapi import FastAPI

app = FastAPI()

# Legacy approach with UnoObj
UnoEndpointFactory.create_endpoints(
    app=app,
    model_obj=Customer,
    prefix="/customers",
    tag="Customers"
)
```

### Domain-Driven Approach

```python
from uno.api import ApiProvider
from fastapi import FastAPI
from uno.dependencies.fastapi import get_repository

# Configure the provider
ApiProvider.configure()

# Create FastAPI app
app = FastAPI()

# Get the factory service
factory_service = ApiProvider.get_endpoint_factory_service()

# Register repository for endpoints
result = await factory_service.register_repository(
    repository=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    schema_type=CustomerSchema,
    path_prefix="/customers",
    tags=["Customers"]
)

# Add router to app
if result.is_success():
    # The endpoints are already registered with FastAPI
    # through the adapter integration
    pass
```

## Related Documentation

- [API Overview](overview.md)
- [Repository Adapter](repository-adapter.md)
- [Repository Pattern](../domain/repositories.md)
- [Domain-Driven Design](../architecture/domain_driven_design.md)
- [Schema Management](schema-manager.md)