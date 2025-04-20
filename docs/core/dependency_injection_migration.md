# Migrating to the New Dependency Injection System

This guide helps you migrate from the legacy dependency injection system to the new unified DI system in `uno.core.di`.

## Overview of Changes

The UNO framework has consolidated multiple dependency injection implementations into a single, coherent system based on modern design patterns and Python features. The new system is located in `uno.core.di` and provides:

- Protocol-based interface definitions
- Container-based service registration
- Scoped dependency management
- FastAPI integration
- Comprehensive testing support

## Migration Steps

### Step 1: Update Imports

Change imports from the legacy modules to the new module:

**Before:**
```python
from uno.dependencies.interfaces import ServiceProviderProtocol
from uno.dependencies.modern_provider import ModernProvider
from uno.dependencies.scoped_container import ScopedContainer
```

**After:**
```python
from uno.core.di import ProviderProtocol, Provider, Container, Scope
```

### Step 2: Update Class References

Update class names to use the new unified naming scheme:

**Before:**
```python
class MyProvider(ModernProvider):
    def configure(self, container):
        # ...
```

**After:**
```python
class MyProvider(Provider):
    def configure_services(self, container=None):
        container = container or self._container
        # ...
```

### Step 3: Update Registration Methods

The registration methods have been standardized:

**Before:**
```python
container.register_service(Logger, ConsoleLogger, lifetime="singleton")
container.register_transient(Repository, SqlRepository)
```

**After:**
```python
from uno.core.di import ServiceLifetime

container.register(LoggerProtocol, ConsoleLogger, lifetime=ServiceLifetime.SINGLETON)
container.register(RepositoryProtocol, SqlRepository, lifetime=ServiceLifetime.TRANSIENT)
```

### Step 4: Update Service Resolution

Service resolution now uses consistent methods:

**Before:**
```python
logger = provider.get_service(Logger)
repository = scope.resolve(Repository)
```

**After:**
```python
logger = provider.get_service(LoggerProtocol)
repository = scope.get(RepositoryProtocol)
```

### Step 5: Update FastAPI Integration

FastAPI integration has been simplified:

**Before:**
```python
from uno.dependencies import inject_dependency

@app.get("/items/{item_id}")
async def get_item(
    item_id: str,
    service = inject_dependency(ItemService)
):
    # ...
```

**After:**
```python
from uno.core.di.fastapi import Inject

@app.get("/items/{item_id}")
async def get_item(
    item_id: str,
    service: ServiceProtocol = Inject(ServiceProtocol)
):
    # ...
```

### Step 6: Update Testing Code

Testing utilities have been enhanced:

**Before:**
```python
from uno.dependencies.testing import TestContainer, mock_service

def test_service():
    container = TestContainer()
    container.register_mock(Logger, MockLogger())
    
    with mock_service(Service, MockService()):
        # Test code
```

**After:**
```python
from uno.core.di import Container
import pytest

@pytest.fixture
def test_container():
    container = Container()
    container.register_instance(LoggerProtocol, MockLogger())
    return container

def test_service(test_container):
    service = test_container.resolve(ServiceProtocol)
    # Test code
```

## Common Migration Patterns

### From inject Decorators to Constructor Injection

**Before:**
```python
import inject

class UserService:
    @inject.param("repository", UserRepository)
    def __init__(self, repository=None):
        self.repository = repository
```

**After:**
```python
class UserService:
    def __init__(self, repository: UserRepositoryProtocol):
        self.repository = repository
```

### From Service Locator to DI

**Before:**
```python
from uno.dependencies import get_service

def process_order(order_id):
    service = get_service(OrderService)
    return service.process(order_id)
```

**After:**
```python
def process_order(order_id, service: OrderServiceProtocol):
    return service.process(order_id)
```

### From Domain Provider to Provider

> **Migration Note:**
> As of April 2025, all `domain_provider.py` modules in the uno codebase have been deprecated and replaced by a single `provider.py` per domain. All dependency registration and DI logic should now be centralized in these canonical `provider.py` files. Any usage of `domain_provider.py` will emit a deprecation warning and should be updated immediately.

**Before:**
```python
class AttributesDomainProvider:
    def configure(self, container):
        container.register(AttributesRepository, SqlAttributesRepository)
        container.register(AttributesService, AttributesService)
```

**After:**
```python
class AttributesProvider(Provider):
    def configure_services(self, container=None):
        container = container or self._container
        
        container.register(AttributesRepositoryProtocol, SqlAttributesRepository, 
                          ServiceLifetime.SCOPED)
        container.register(AttributesServiceProtocol, AttributesService)
```

## Complete Example

### Before

```python
from uno.dependencies.interfaces import ServiceProviderProtocol
from uno.dependencies.modern_provider import ModernProvider
from uno.dependencies.scoped_container import ScopedContainer
import inject

class LoggerService:
    def log(self, message):
        print(message)

class UserRepository:
    @inject.param("logger", LoggerService)
    def __init__(self, logger=None):
        self.logger = logger
    
    def get_user(self, user_id):
        self.logger.log(f"Getting user {user_id}")
        return {"id": user_id, "name": "Test User"}

class DomainProvider(ModernProvider):
    def configure(self, container):
        container.register_singleton(LoggerService, LoggerService)
        container.register_transient(UserRepository, UserRepository)

# FastAPI usage
from uno.dependencies import inject_dependency

@app.get("/users/{user_id}")
async def get_user(user_id: str, repo = inject_dependency(UserRepository)):
    return repo.get_user(user_id)
```

### After

```python
from uno.core.di import Provider, Container, ServiceLifetime
from typing import Protocol, runtime_checkable

@runtime_checkable
class LoggerProtocol(Protocol):
    def log(self, message: str) -> None: ...

@runtime_checkable
class UserRepositoryProtocol(Protocol):
    def get_user(self, user_id: str) -> dict: ...

class Logger:
    def log(self, message: str) -> None:
        print(message)

class UserRepository:
    def __init__(self, logger: LoggerProtocol):
        self.logger = logger
    
    def get_user(self, user_id: str) -> dict:
        self.logger.log(f"Getting user {user_id}")
        return {"id": user_id, "name": "Test User"}

class AppProvider(Provider):
    def configure_services(self, container=None):
        container = container or self._container
        
        container.register(LoggerProtocol, Logger, ServiceLifetime.SINGLETON)
        container.register(UserRepositoryProtocol, UserRepository)

# FastAPI usage
from uno.core.di.fastapi import Inject

@app.get("/users/{user_id}")
async def get_user(
    user_id: str, 
    repo: UserRepositoryProtocol = Inject(UserRepositoryProtocol)
):
    return repo.get_user(user_id)
```

## Troubleshooting

### Circular Dependencies

If you encounter circular dependency errors:

1. Use factory registration for one of the circular dependencies
2. Consider refactoring to remove the circular dependency
3. Use property injection instead of constructor injection

### Missing Services

If you get "service not registered" errors:

1. Check that your provider's `configure_services` method is being called
2. Verify the service is registered with the correct protocol
3. Ensure you're using the right container/scope

### Scope Disposal Issues

If resources aren't being disposed properly:

1. Make sure you're calling `scope.dispose()` when done with the scope
2. Verify disposable services implement a `dispose()` method
3. For FastAPI, ensure the `cleanup_request_scope` middleware is registered

## Timeline

- **Current**: Transition period with both systems available
- **Next release**: Legacy system deprecated with warnings
- **Future release**: Legacy system removed

During the transition period, you can use both systems side by side, but all new code should use the new system exclusively.