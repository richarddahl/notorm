# Repository Adapter

The Repository Adapter provides a bridge between domain repositories and the uno API endpoint system, allowing you to use domain-driven design with the API layer without modifying either component.

## Overview

The Repository Adapter takes a domain repository and wraps it with methods that match the interface expected by the `UnoEndpoint` and `UnoRouter` classes. This allows you to use your domain entities and repositories with the existing endpoint system.

```
┌───────────────┐      ┌───────────────┐      ┌─────────────────┐
│  UnoEndpoint  │      │  Repository   │      │   Domain        │
│  (API Layer)  │◄────►│  Adapter      │◄────►│   Repository    │
└───────────────┘      └───────────────┘      └─────────────────┘
```

## Adapter Types

The repository adapter system provides three main adapter types for different use cases:

1. **RepositoryAdapter**: Provides full CRUD operations (get, list, create, update, delete)
2. **ReadOnlyRepositoryAdapter**: Provides read-only operations (get, list)
3. **BatchRepositoryAdapter**: Provides batch operations in addition to standard CRUD

## Installation

The repository adapter is included in the uno API module and doesn't require any additional installation:

```python
from uno.api.repository_adapter import RepositoryAdapter, ReadOnlyRepositoryAdapter, BatchRepositoryAdapter
```

## Basic Usage

### Creating a Repository Adapter

```python
from uno.api.repository_adapter import RepositoryAdapter
from uno.dependencies.fastapi import get_repository
from fastapi import Depends

# Create a repository adapter
adapter = RepositoryAdapter(
    repository_dependency=Depends(get_repository(CustomerRepository)),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO
)
```

### Using with UnoEndpoint

```python
from uno.api.endpoint import UnoEndpoint
from uno.api.repository_adapter import RepositoryAdapter
from fastapi import FastAPI, Depends
from uno.dependencies.fastapi import get_repository

# Create FastAPI app
app = FastAPI()

# Create repository adapter
adapter = RepositoryAdapter(
    repository_dependency=Depends(get_repository(CustomerRepository)),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO
)

# Create endpoint with adapter
endpoint = UnoEndpoint(app, adapter, prefix="/api/v1/customers")
endpoint.register_endpoints()
```

### Using with EndpointFactory

```python
from uno.api.endpoint_factory import EndpointFactory
from uno.dependencies.fastapi import get_repository
from fastapi import FastAPI

# Create FastAPI app
app = FastAPI()

# Create endpoints with repository
customer_router = EndpointFactory.create_endpoints(
    app=app,
    repository=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO,
    prefix="/api/v1/customers",
    tag="Customers"
)

# Register router with app
app.include_router(customer_router)
```

## Adapter Options

The `RepositoryAdapter` class accepts several parameters to customize its behavior:

```python
RepositoryAdapter(
    repository_dependency,      # Dependency that resolves to a repository instance
    entity_type,                # Type of the domain entity
    schema_type,                # Type of the API schema (DTO)
    include_fields=None,        # List of fields to include in responses
    exclude_fields=None,        # List of fields to exclude from responses
    paginated=True,             # Whether to paginate list responses
    filter_manager=None,        # Custom filter manager for filtering
    max_page_size=100,          # Maximum page size for paginated results
    default_page_size=10        # Default page size for paginated results
)
```

## Read-Only Repository Adapter

If your API should be read-only, you can use the `ReadOnlyRepositoryAdapter`:

```python
from uno.api.repository_adapter import ReadOnlyRepositoryAdapter
from uno.dependencies.fastapi import get_repository

# Create a read-only adapter
adapter = ReadOnlyRepositoryAdapter(
    repository_dependency=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO
)

# Create endpoint with read-only adapter
endpoint = UnoEndpoint(app, adapter, prefix="/api/v1/customers")
endpoint.register_endpoints()
```

The `ReadOnlyRepositoryAdapter` will only register `get` and `list` endpoints.

## Batch Operations Adapter

The `BatchRepositoryAdapter` adds support for batch operations:

```python
from uno.api.repository_adapter import BatchRepositoryAdapter
from uno.dependencies.fastapi import get_repository

# Create a batch adapter
adapter = BatchRepositoryAdapter(
    repository_dependency=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO
)

# Create endpoint with batch adapter
endpoint = UnoEndpoint(app, adapter, prefix="/api/v1/customers")
endpoint.register_endpoints()
```

The `BatchRepositoryAdapter` will register additional endpoints for batch operations:

- `POST /batch`: Batch create
- `PATCH /batch`: Batch update
- `DELETE /batch`: Batch delete

## Custom Adapters

You can create custom adapters by extending the `RepositoryAdapter` class:

```python
from uno.api.repository_adapter import RepositoryAdapter
from typing import List, Optional

class CustomerRepositoryAdapter(RepositoryAdapter[CustomerEntity, CustomerDTO]):
    """Custom adapter for customer repository."""
    
    async def get_active_customers(self) -> List[CustomerDTO]:
        """Get active customers."""
        # Get repository from dependency
        repository = await self.resolve_repository()
        
        # Get active customers from repository
        result = await repository.get_active_customers()
        
        # Convert entities to DTOs
        return [self.schema_type.from_entity(entity) for entity in result]
```

## Entity to Schema Conversion

The repository adapter automatically handles the conversion between domain entities and API schemas (DTOs). To customize this conversion, you can implement the `from_entity` method in your schema class:

```python
class CustomerDTO(BaseModel):
    id: str
    name: str
    email: str
    status: str
    created_at: datetime
    
    @classmethod
    def from_entity(cls, entity: CustomerEntity) -> "CustomerDTO":
        """Convert entity to DTO."""
        return cls(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            status=entity.status.value,  # Convert enum to string
            created_at=entity.created_at
        )
```

## Request to Entity Conversion

For create and update operations, the repository adapter needs to convert API schemas back to domain entities or entity creation data. To customize this conversion, you can implement a custom method in your adapter:

```python
class CustomerRepositoryAdapter(RepositoryAdapter[CustomerEntity, CustomerDTO]):
    """Custom adapter for customer repository."""
    
    async def _prepare_create_data(self, data: CustomerDTO) -> dict:
        """Convert DTO to entity creation data."""
        return {
            "name": data.name,
            "email": data.email,
            "status": CustomerStatus(data.status),  # Convert string to enum
            "created_at": datetime.now(UTC)
        }
```

## Error Handling

The repository adapter integrates with the uno Result type for error handling. If your repository methods return a Result type, the adapter will automatically handle errors:

```python
# In your repository
async def get_by_id(self, id: str) -> Result[CustomerEntity]:
    try:
        customer = await self._get_by_id(id)
        if not customer:
            return Failure(NotFoundError(f"Customer with ID {id} not found"))
        return Success(customer)
    except Exception as e:
        return Failure(DatabaseError(str(e)))

# In your endpoint
@router.get("/{id}")
async def get_customer(
    id: str,
    repo = Depends(get_repository(CustomerRepository))
):
    result = await repo.get_by_id(id)
    
    if result.is_failure():
        error = result.error
        if isinstance(error, NotFoundError):
            raise HTTPException(404, error.message)
        raise HTTPException(500, error.message)
    
    return CustomerDTO.from_entity(result.value)
```

## Complete Example

Here's a complete example of using the repository adapter with a domain repository:

```python
from fastapi import FastAPI, Depends, HTTPException
from uno.api.endpoint import UnoEndpoint
from uno.api.repository_adapter import RepositoryAdapter
from uno.dependencies.fastapi import get_repository
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Domain entity
class CustomerEntity:
    def __init__(self, id: str, name: str, email: str, created_at: datetime):
        self.id = id
        self.name = name
        self.email = email
        self.created_at = created_at

# API schema (DTO)
class CustomerDTO(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime
    
    @classmethod
    def from_entity(cls, entity: CustomerEntity) -> "CustomerDTO":
        return cls(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            created_at=entity.created_at
        )

# API schema for creation
class CustomerCreateDTO(BaseModel):
    name: str
    email: EmailStr

# Repository protocol
class CustomerRepositoryProtocol:
    async def get_by_id(self, id: str) -> CustomerEntity:
        ...
    
    async def get_all(self, limit: int = 10, offset: int = 0) -> List[CustomerEntity]:
        ...
    
    async def create(self, data: dict) -> CustomerEntity:
        ...
    
    async def update(self, id: str, data: dict) -> CustomerEntity:
        ...
    
    async def delete(self, id: str) -> bool:
        ...

# Repository implementation
class CustomerRepository(CustomerRepositoryProtocol):
    # Implementation details...
    pass

# Create FastAPI app
app = FastAPI()

# Create repository adapter
adapter = RepositoryAdapter(
    repository_dependency=Depends(get_repository(CustomerRepository)),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO
)

# Create endpoint with adapter
endpoint = UnoEndpoint(app, adapter, prefix="/api/v1/customers")
endpoint.register_endpoints()
```

This will register the following endpoints:

- `GET /api/v1/customers/{id}`: Get a customer by ID
- `GET /api/v1/customers`: List customers with pagination and filtering
- `POST /api/v1/customers`: Create a new customer
- `PATCH /api/v1/customers/{id}`: Update a customer
- `DELETE /api/v1/customers/{id}`: Delete a customer

## Advanced Usage

### Custom Endpoint Methods

You can add custom methods to your repository adapter:

```python
class CustomerRepositoryAdapter(RepositoryAdapter[CustomerEntity, CustomerDTO]):
    """Custom adapter for customer repository."""
    
    async def get_by_email(self, email: str) -> Optional[CustomerDTO]:
        """Get customer by email."""
        repository = await self.resolve_repository()
        result = await repository.get_by_email(email)
        
        if not result:
            return None
        
        return self.schema_type.from_entity(result)
```

And then use these methods in custom endpoints:

```python
class CustomerEndpoint(UnoEndpoint):
    """Custom endpoint for customer operations."""
    
    def register_endpoints(self):
        """Register custom endpoints."""
        super().register_endpoints()  # Register standard endpoints
        
        @self.app.get(f"{self.prefix}/by-email")
        async def get_by_email(
            email: str,
            adapter = Depends(lambda: self.model)
        ):
            """Get customer by email."""
            result = await adapter.get_by_email(email)
            
            if not result:
                raise HTTPException(404, f"Customer with email {email} not found")
            
            return result
```

### Customizing Filtering

You can customize how filtering is handled in the repository adapter:

```python
from uno.queries.filter_manager import FilterManager
from uno.queries.filter import FilterParam

class CustomFilterManager(FilterManager):
    """Custom filter manager for customer repository."""
    
    def build_filters(self, params: FilterParam) -> dict:
        """Build filters for repository."""
        filters = {}
        
        if params.get("name__contains"):
            filters["name__icontains"] = params.get("name__contains")
        
        if params.get("status__in"):
            filters["status__in"] = params.get("status__in").split(",")
        
        return filters

# Create adapter with custom filter manager
adapter = RepositoryAdapter(
    repository_dependency=get_repository(CustomerRepository),
    entity_type=CustomerEntity,
    schema_type=CustomerDTO,
    filter_manager=CustomFilterManager()
)
```

### Integration with Domain Services

You can also integrate with domain services in your repository adapter:

```python
class CustomerRepositoryAdapter(RepositoryAdapter[CustomerEntity, CustomerDTO]):
    """Custom adapter for customer repository."""
    
    def __init__(
        self,
        repository_dependency,
        service_dependency,
        entity_type,
        schema_type,
        **kwargs
    ):
        super().__init__(repository_dependency, entity_type, schema_type, **kwargs)
        self.service_dependency = service_dependency
    
    async def resolve_service(self):
        """Resolve service dependency."""
        if callable(self.service_dependency):
            return await self.service_dependency()
        return self.service_dependency
    
    async def create(self, data: dict) -> CustomerDTO:
        """Create customer using service."""
        service = await self.resolve_service()
        result = await service.create_customer(data)
        
        return self.schema_type.from_entity(result)
```

## See Also

- [Domain Integration](domain-integration.md) - Guide on integrating domain-driven design with the API layer
- [Endpoint Factory](endpoint-factory.md) - Documentation for the endpoint factory
- [Endpoint](endpoint.md) - Documentation for the endpoint system