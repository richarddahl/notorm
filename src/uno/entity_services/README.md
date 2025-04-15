# Entity Service Layer

The Entity Service Layer provides a bridge between the UnoObj business logic layer and the dependency injection system.

## Overview

uno has two complementary approaches to implementing business logic:

1. **UnoObj Pattern**: The original approach where business logic is encapsulated within UnoObj classes, which combine data representation, validation, and business operations.

2. **Service Pattern**: A DI-friendly approach where business logic is encapsulated in service classes that operate on domain models.

This module provides a bridge between these two approaches, allowing you to:

- Gradually migrate from UnoObj to services
- Use UnoObj and services together
- Choose the right pattern for each use case

## Key Components

### UnoEntityService

The UnoEntityService is a base class for services that operate on UnoObj instances:

```python
class UnoEntityService(Generic[T]):
    """
    Service for working with UnoObj entities.
    
    This service provides a bridge between the UnoObj pattern and
    the dependency injection service pattern.
    """
    
    def __init__(self, entity_class: Type[T], logger: Optional[logging.Logger] = None):
        self.entity_class = entity_class
        self.logger = logger or logging.getLogger(__name__)
    
    async def get(self, id: str) -> Optional[T]:
        """Get an entity by ID."""
        return await self.entity_class.get(id=id)
    
    async def filter(self, **kwargs) -> List[T]:
        """Filter entities by criteria."""
        return await self.entity_class.filter(kwargs)
```

### UnoEntityServiceFactory

The UnoEntityServiceFactory creates services for UnoObj classes:

```python
class UnoEntityServiceFactory:
    """
    Factory for creating entity services.
    
    This factory creates services for UnoObj classes, providing
    a consistent way to access them through dependency injection.
    """
    
    def create_service(self, entity_class: Type[T]) -> UnoEntityService[T]:
        """Create a service for a UnoObj class."""
        return UnoEntityService(entity_class)
```

## Usage Examples

### Using with Dependency Injection

```python
from uno.dependencies import get_service_provider
from uno.entity_services import UnoEntityServiceFactory
from my_app.entities import UserObj

# Create a factory
factory = UnoEntityServiceFactory()

# Create a service for UserObj
user_service = factory.create_service(UserObj)

# Use the service
user = await user_service.get(id="123")
users = await user_service.filter(tenant_id="456")
```

### Custom Entity Services

You can create custom services that extend the base service:

```python
from uno.entity_services import UnoEntityService
from my_app.entities import UserObj

class UserEntityService(UnoEntityService[UserObj]):
    """Custom service for User entities."""
    
    def __init__(self, logger=None):
        super().__init__(UserObj, logger)
    
    async def find_by_email(self, email: str) -> Optional[UserObj]:
        """Find a user by email."""
        users = await self.filter(email=email)
        return users[0] if users else None
    
    async def activate_user(self, user_id: str) -> UserObj:
        """Activate a user."""
        user = await self.get(id=user_id)
        if user:
            user.is_active = True
            return await user.save()
        return None
```

## Integration with Service Provider

You can register entity services with the service provider:

```python
from uno.dependencies import get_service_provider
from uno.entity_services import UnoEntityServiceFactory
from my_app.entities import UserObj, GroupObj
from my_app.services import UserEntityService

# Get the service provider
provider = get_service_provider()

# Register factory
factory = UnoEntityServiceFactory()
provider.register_service(UnoEntityServiceFactory, factory)

# Register custom service
user_service = UserEntityService()
provider.register_service(UserEntityService, user_service)

# Use factory to create and register standard services
group_service = factory.create_service(GroupObj)
provider.register_service(UnoEntityService[GroupObj], group_service)
```

## Benefits

- **Gradual Migration**: You can migrate from UnoObj to services at your own pace
- **Consistency**: Provides a consistent interface for all entity operations
- **Testability**: Makes it easier to mock and test entity operations
- **Flexibility**: Choose the right pattern for each use case
- **DI Integration**: Full integration with the dependency injection system