# Domain-Driven API Endpoints

## Overview

The Uno framework uses a Domain-Driven Design (DDD) approach for its API endpoints. This document explains the architecture and patterns used across all modules for creating standardized, maintainable API endpoints.

## Key Components

### 1. Domain Entities

Domain entities are the core of the DDD approach. They are defined in each module's `entities.py` file and represent the business objects of your domain:

```python
from dataclasses import dataclass, field
from typing import List, Optional
from uno.domain.core import AggregateRoot

@dataclass
class MetaType(AggregateRoot[str]):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
```

### 2. Domain Repositories

Repositories handle data access for domain entities. They are defined in each module's `domain_repositories.py` file:

```python
from uno.domain.repository import Repository
from .entities import MetaType

class MetaTypeRepository(Repository[MetaType, str]):
    """Repository for managing MetaType entities."""
    
    async def find_by_name(self, name: str) -> Optional[MetaType]:
        """Find a meta type by name."""
        # Implementation details
```

### 3. Domain Services

Services encapsulate business logic for domain entities. They are defined in each module's `domain_services.py` file:

```python
from uno.domain.service import DomainService
from uno.core.result import Result, Success, Failure
from .entities import MetaType
from .domain_repositories import MetaTypeRepository

class MetaTypeService(DomainService[MetaType, str]):
    """Service for managing MetaType entities."""
    
    def __init__(self, repository: MetaTypeRepository):
        super().__init__(repository)
        
    async def find_by_name(self, name: str) -> Result[MetaType]:
        """Find a meta type by name."""
        result = await self.repository.find_by_name(name)
        if not result:
            return Failure(f"MetaType with name '{name}' not found")
        return Success(result)
```

### 4. Domain Providers

Providers configure dependency injection for domain components. They are defined in each module's `domain_provider.py` file:

```python
from uno.dependencies.service import register_service
from .domain_repositories import MetaTypeRepository
from .domain_services import MetaTypeService

def register_meta_services():
    """Register meta services in the dependency container."""
    register_service(MetaTypeRepository)
    register_service(MetaTypeService, depends=[MetaTypeRepository])
```

### 5. Domain Endpoints

Endpoints expose domain functionality through the API. They are defined in each module's `domain_endpoints.py` file:

```python
from fastapi import APIRouter, Depends
from uno.domain.api_integration import create_domain_router, domain_endpoint
from .entities import MetaType
from .domain_services import MetaTypeService

def create_meta_router() -> APIRouter:
    """Create a router for meta endpoints."""
    router = create_domain_router(
        entity_type=MetaType,
        service_type=MetaTypeService,
        prefix="/meta-types",
        tags=["Meta"]
    )
    
    # Add custom endpoints
    @router.get("/by-name/{name}", response_model=MetaTypeResponse)
    @domain_endpoint(entity_type=MetaType, service_type=MetaTypeService)
    async def get_by_name(name: str, service: MetaTypeService):
        """Get a meta type by name."""
        return await service.find_by_name(name)
    
    return router
```

## Common Patterns

### Standard CRUD Endpoints

All domain-driven modules automatically provide these standard CRUD endpoints:

| Method | Endpoint        | Description                   |
|--------|-----------------|-------------------------------|
| POST   | /               | Create a new entity           |
| GET    | /{id}           | Get an entity by ID           |
| GET    | /               | List all entities (paginated) |
| PATCH  | /{id}           | Update an entity by ID        |
| DELETE | /{id}           | Delete an entity by ID        |

### Error Handling

All domain endpoints use the Result pattern for consistent error handling:

```python
async def create_entity(data: CreateDTO) -> Result[Entity]:
    try:
        # Create entity
        return Success(entity)
    except ValidationError as e:
        return Failure(f"Validation error: {str(e)}")
    except Exception as e:
        return Failure(f"Failed to create entity: {str(e)}")
```

The domain router automatically converts Result failures to appropriate HTTP error responses.

### DTOs and Schema Generation

Each domain router automatically generates DTOs (Data Transfer Objects) for API requests and responses:

1. **Response DTO**: Used for API responses, includes all entity fields plus ID and timestamps
2. **Create DTO**: Used for create requests, includes all entity fields except ID and timestamps
3. **Update DTO**: Used for update requests, same as Create DTO but all fields are optional

## Module-Specific Endpoints

Each module implements its own domain endpoints:

| Module        | Base Endpoint           | Key Functionality                                |
|---------------|-------------------------|--------------------------------------------------|
| Meta          | /meta-types             | Meta type management                             |
| Attributes    | /attributes             | Attribute definition and management              |
| Values        | /values                 | Value storage and retrieval                      |
| Authorization | /roles, /permissions    | Role-based access control                        |
| Reports       | /report-templates       | Report definition and execution                  |
| Vector Search | /vector-indexes         | Vector storage and semantic search               |
| Workflows     | /workflows              | Workflow definition and execution                |

## Creating Custom Endpoints

You can add custom endpoints to the domain router:

```python
@router.get("/custom-path", response_model=CustomResponseModel)
@domain_endpoint(entity_type=Entity, service_type=EntityService)
async def custom_endpoint(param: str, service: EntityService):
    """Custom endpoint description."""
    return await service.custom_operation(param)
```

The `domain_endpoint` decorator handles:
- Service injection
- Error handling with Result pattern
- Converting Result to appropriate HTTP responses

## Integration with FastAPI

Domain routers integrate seamlessly with FastAPI applications:

```python
from fastapi import FastAPI
from uno.attributes.domain_endpoints import create_attributes_router
from uno.meta.domain_endpoints import create_meta_router

app = FastAPI()
app.include_router(create_attributes_router())
app.include_router(create_meta_router())
```