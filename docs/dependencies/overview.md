# Dependency Injection in Uno

The Uno framework includes a comprehensive dependency injection system to improve code maintainability, testability, and decoupling of components.

## Overview

Dependency injection (DI) is a design pattern that allows you to decouple the creation of objects from their usage. In the Uno framework, this is implemented using the `inject` library along with custom interfaces and components.

Uno supports both traditional UnoObj-based development and modern dependency injection patterns. This documentation explains the dependency injection system and how it can be used alongside or as an alternative to the UnoObj pattern.

## Key Benefits

- **Testability**: Easily replace real components with mocks during testing
- **Decoupling**: Components depend on abstractions, not concrete implementations 
- **Configurability**: Centralized configuration of application dependencies
- **Lifecycle Management**: Properly scoped instances for web request lifecycles
- **Flexibility**: Choose between UnoObj and DI based on your needs
- **Scalability**: Better organization for complex domains and larger teams

## Core Components

### Interfaces

The DI system is based on Protocol classes that define interfaces for various components:

- `UnoRepositoryProtocol`: Interface for data access repositories
- `UnoServiceProtocol`: Interface for service classes that implement business logic
- `UnoConfigProtocol`: Interface for configuration providers
- `UnoSessionProviderProtocol`: Interface for database session providers
- `UnoSessionManagerProtocol`: Interface for session management

### Container

The DI container is configured at application startup and provides access to registered dependencies:

```python
from uno.dependencies import configure_di, get_container, get_instance

# Configure the container
inject.configure(configure_di)

# Get an instance from the container
config = get_instance(UnoConfigProtocol)
```

### FastAPI Integration

The DI system integrates with FastAPI's dependency injection system:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_db_session, get_repository, inject_dependency
from uno.dependencies.interfaces import UnoConfigProtocol

router = APIRouter()

@router.get("/items")
async def list_items(
    config: UnoConfigProtocol = Depends(inject_dependency(UnoConfigProtocol)),
    repo = Depends(get_repository(ItemRepository))
):
    # Use injected dependencies
    limit = config.get_value("DEFAULT_LIMIT", 100)
    return await repo.list(limit=limit)
```

## Architecture Patterns

Uno supports multiple architectural patterns:

1. **UnoObj Pattern**: The traditional approach using UnoObj for everything
2. **Dependency Injection Pattern**: Modern approach with repositories and services
3. **Hybrid Pattern**: Combining both approaches strategically

For detailed guidance on choosing between these patterns, see:
- [Usage Guide](usage.md) - How to use dependency injection
- [Hybrid Approach](hybrid_approach.md) - How to combine UnoObj with DI
- [Decision Guide](decision_guide.md) - When to use each pattern

## Usage Examples

### Creating a Repository

```python
from sqlalchemy.ext.asyncio import AsyncSession
from uno.di import UnoRepository
from app.models import Item

class ItemRepository(UnoRepository[Item]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Item)
        
    async def find_by_category(self, category: str):
        # Custom repository method
        stmt = select(self.model_class).where(self.model_class.category == category)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

### Creating a Service

```python
from uno.di import UnoService
from uno.di.interfaces import UnoRepositoryProtocol
from app.models import Item

class ItemService(UnoService[Item, List[Item]]):
    def __init__(self, repository: UnoRepositoryProtocol[Item]):
        super().__init__(repository)
        
    async def execute(self, category: Optional[str] = None) -> List[Item]:
        if category:
            return await self.repository.find_by_category(category)
        else:
            return await self.repository.list()
```

### Using in FastAPI Endpoints

```python
from fastapi import APIRouter, Depends
from uno.di import get_db_session, get_repository
from app.repositories import ItemRepository
from app.services import ItemService

router = APIRouter()

@router.get("/items")
async def list_items(
    category: Optional[str] = None,
    session = Depends(get_db_session),
    repo = Depends(get_repository(ItemRepository))
):
    # Create and use the service
    service = ItemService(repo)
    return await service.execute(category)
```

## Testing with DI

The DI system makes testing much easier by allowing you to inject mock dependencies:

```python
import pytest
import inject
from unittest.mock import MagicMock
from app.services import ItemService

def configure_test_di(binder):
    # Create mock repository
    mock_repo = MagicMock()
    mock_repo.find_by_category.return_value = [{"id": "1", "name": "Test Item"}]
    
    # Bind the mock to the repository protocol
    binder.bind(UnoRepositoryProtocol, mock_repo)

@pytest.fixture
def service():
    # Configure test DI container
    inject.clear_and_configure(configure_test_di)
    
    # Get repository from container 
    repo = inject.instance(UnoRepositoryProtocol)
    
    # Create service with mock repository
    return ItemService(repo)

def test_service_execute(service):
    # Test the service with the mock repository
    result = await service.execute(category="test")
    assert len(result) == 1
    assert result[0]["name"] == "Test Item"
```