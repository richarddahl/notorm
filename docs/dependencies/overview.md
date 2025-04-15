# Modern Dependency Injection in Uno

The Uno framework includes a modern, hierarchical dependency injection system that improves code maintainability, testability, and decoupling of components.

## Overview

Dependency injection (DI) is a design pattern that allows you to decouple the creation of objects from their usage. In the Uno framework, this is implemented using a custom, protocol-based DI container that supports proper scoping and lifecycle management.

Uno supports both traditional UnoObj-based development and modern dependency injection patterns. This documentation explains the dependency injection system and how it can be used alongside or as an alternative to the UnoObj pattern.

## Key Benefits

- **Testability**: Easily replace real components with mocks during testing
- **Decoupling**: Components depend on abstractions, not concrete implementations 
- **Configurability**: Centralized configuration of application dependencies
- **Lifecycle Management**: Properly scoped instances with async support
- **Flexibility**: Choose between UnoObj and DI based on your needs
- **Scalability**: Better organization for complex domains and larger teams
- **AsyncIO Support**: Fully supports async lifecycle and async-aware service resolution

## Core Components

### Interfaces

The DI system is based on Protocol classes that define interfaces for various components:

- `UnoRepositoryProtocol`: Interface for data access repositories
- `UnoServiceProtocol`: Interface for service classes that implement business logic
- `UnoConfigProtocol`: Interface for configuration providers
- `UnoDatabaseProviderProtocol`: Interface for database connection providers
- `UnoDBManagerProtocol`: Interface for database management operations

### ServiceScope

The DI system supports three service scopes:

- `SINGLETON`: One instance per container (application-lifetime)
- `SCOPED`: One instance per scope (e.g., per request)
- `TRANSIENT`: New instance each time

### Service Provider

The modern DI system uses a centralized service provider that manages service registration and resolution:

```python
from uno.dependencies.modern_provider import get_service_provider, initialize_services

# Initialize the service provider (typically in application startup)
await initialize_services()

# Get the service provider
provider = get_service_provider()

# Get a service by its protocol
db_manager = provider.get_service(UnoDBManagerProtocol)
```

### Scoped Container

The underlying container supports hierarchical scoping for proper service lifecycle management:

```python
from uno.dependencies.scoped_container import get_service, create_scope, create_async_scope

# Get a singleton service
config = get_service(UnoConfigProtocol)

# Create a synchronous scope
with create_scope("request_123") as scope:```

# Get a scoped service
repo = scope.resolve(UserRepository)
```
    
# Create an async scope
async with create_async_scope("async_request_456") as scope:```

# Get a scoped service
repo = scope.resolve(UserRepository)
``````

await repo.get_by_id(123)
```
```

### FastAPI Integration

The DI system integrates with FastAPI's dependency injection system:

```python
from fastapi import APIRouter, Depends
from uno.dependencies.fastapi_integration import configure_fastapi
from uno.dependencies.database import get_db_session, get_repository

# Configure FastAPI with the DI system
configure_fastapi(app)

router = APIRouter()

@router.get("/items")
async def list_items(```

repo = Depends(get_repository(ItemRepository))
```
):```

# Use injected dependencies
return await repo.list()
```
```

## Architecture Patterns

Uno supports multiple architectural patterns:

1. **UnoObj Pattern**: The traditional approach using UnoObj for everything
2. **Dependency Injection Pattern**: Modern approach with protocols, repositories, and services
3. **Hybrid Pattern**: Combining both approaches strategically

## Usage Examples

### Service Configuration

```python
from uno.dependencies.scoped_container import ServiceCollection
from uno.dependencies.modern_provider import configure_base_services

# Create service collection
services = ServiceCollection()

# Register a singleton service
services.add_singleton(```

LoggerServiceProtocol,
LoggerService,
log_level="INFO"
```
)

# Register a scoped service
services.add_scoped(```

UserRepositoryProtocol, 
UserRepository
```
)

# Register a transient service
services.add_transient(```

NotificationServiceProtocol,
NotificationService
```
)

# Register an existing instance
logger = create_logger()
services.add_instance(Logger, logger)
```

### Creating a Repository

```python
from sqlalchemy.ext.asyncio import AsyncSession
from uno.database.repository import UnoBaseRepository
from app.models import Item

class ItemRepository(UnoBaseRepository[Item]):```

def __init__(self, session: AsyncSession):```

super().__init__(session, Item)
```
    
async def find_by_category(self, category: str):```

# Custom repository method
stmt = select(self.entity_class).where(self.entity_class.category == category)
result = await self.session.execute(stmt)
return list(result.scalars().all())
```
```
```

### Creating a Service

```python
from typing import List, Optional, Protocol
from app.repositories import ItemRepository
from app.models import Item

class ItemServiceProtocol(Protocol):```

async def get_items(self, category: Optional[str] = None) -> List[Item]: ...
```

class ItemService:```

def __init__(self, repository: ItemRepository):```

self.repository = repository
```
    
async def get_items(self, category: Optional[str] = None) -> List[Item]:```

if category:
    return await self.repository.find_by_category(category)
else:
    return await self.repository.list()
```
```
```

### Using Services in FastAPI Endpoints

```python
from fastapi import APIRouter, Depends
from uno.dependencies.database import get_repository
from app.repositories import ItemRepository
from app.services import ItemService

router = APIRouter()

@router.get("/items")
async def list_items(```

category: Optional[str] = None,```
```

repo = Depends(get_repository(ItemRepository))
```
):```

# Create and use the service
service = ItemService(repo)
return await service.get_items(category)
```
```

## Testing with Modern DI

The modern DI system makes testing much easier by allowing you to register mock services:

```python
import pytest
import logging
from unittest.mock import MagicMock
from uno.dependencies.scoped_container import ServiceCollection, initialize_container
from app.services import ItemService, ItemServiceProtocol
from app.repositories import ItemRepository

@pytest.fixture
def setup_test_di():```

"""Set up dependency injection for testing."""
# Create mock repository
mock_repo = MagicMock(spec=ItemRepository)
mock_repo.find_by_category.return_value = [{`id`: "1", `name`: "Test Item"}]
``````

```
```

# Create service collection
services = ServiceCollection()
services.add_instance(ItemRepository, mock_repo)
``````

```
```

# Initialize container with test services
initialize_container(services, logging.getLogger("test"))
``````

```
```

return mock_repo
```

@pytest.fixture
def service(setup_test_di):```

"""Create service with the mock repository."""
mock_repo = setup_test_di
return ItemService(mock_repo)
```

def test_service_get_items(service):```

"""Test the service with the mock repository."""
result = await service.get_items(category="test")
assert len(result) == 1
assert result[0][`id`] == "1"
assert result[0][`name`] == "Test Item"
```
```

## Lifecycle Management

The modern DI system supports proper lifecycle management for services:

```python
from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle

# Define a service with lifecycle hooks
class DatabaseService(ServiceLifecycle):```

async def initialize(self) -> None:```

"""Initialize database connections."""
await self.connect()
await self.create_schema()
```
    
async def dispose(self) -> None:```

"""Close database connections."""
await self.disconnect()
```
```

# Register the service for lifecycle management
provider = get_service_provider()
provider.register_lifecycle_service(DatabaseService)
```

The service provider will ensure that all registered lifecycle services are properly initialized during application startup and disposed during shutdown.