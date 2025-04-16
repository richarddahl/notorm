# Domain-Driven API Integration

This guide explains how to integrate domain-driven design with API endpoints in the Uno framework. It demonstrates the use of repository adapters and domain entities to create RESTful API endpoints.

## Overview

The Uno framework provides a seamless way to expose domain entities via RESTful API endpoints. The key components of this integration are:

1. **Domain Entities**: Your core business objects
2. **Repositories**: Classes that manage data access for entities
3. **Repository Adapters**: Bridge between repositories and API endpoints
4. **Endpoint Factory**: Creates standardized endpoints for entities
5. **Schema Management**: Handles conversion between entities and DTOs

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

## Best Practices

1. **Separation of Concerns**: Keep your domain logic separate from your API layer.
2. **DTOs vs. Entities**: Use DTOs for API communication and entities for domain logic.
3. **Repository Pattern**: Implement the Repository protocol for data access.
4. **Error Handling**: Provide meaningful error responses.
5. **Pagination**: Always paginate list endpoints for large datasets.
6. **Documentation**: Use OpenAPI features for clear documentation.
7. **Validation**: Validate input at the DTO level.
8. **Authorization**: Add authorization checks to your endpoints.
9. **Testing**: Test your repositories and API endpoints separately.
10. **Versioning**: Use versioning in your API URLs.

## Migration from UnoObj Pattern

If you're migrating from the UnoObj pattern to domain-driven design, here's a step-by-step approach:

1. **Create Domain Entities**: Convert your UnoObj classes to domain entities.
2. **Implement Repositories**: Create repositories for your entities.
3. **Create DTOs**: Define your API schemas as Pydantic models.
4. **Set Up Schema Manager**: Create a schema manager to handle conversion.
5. **Update Endpoints**: Use the endpoint factory with your repositories.

For more details, see the [Migration Guide](migration-guide.md).

## Related Documentation

- [API Overview](overview.md)
- [Repository Adapter](repository-adapter.md)
- [Repository Pattern](../domain/repositories.md)
- [Domain-Driven Design](../architecture/domain_driven_design.md)
- [Schema Management](schema-manager.md)