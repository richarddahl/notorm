# Dependency Injection System

This document describes the dependency injection (DI) system used in the UNO framework.

## Overview

The UNO framework uses a dependency injection system to manage component dependencies, making code more modular, testable, and maintainable. The DI system is built on the following principles:

1. **Interface-based design**: Dependencies are defined by interfaces (protocols)
2. **Constructor injection**: Dependencies are provided via constructors
3. **Lifetime management**: Services have defined lifetimes (singleton, scoped, transient)
4. **Scope hierarchies**: Scopes can be nested to create hierarchies of dependencies

## Core Components

### Container

The `Container` is the central registry for all services and handles creating service instances. It provides:

- Service registration with different lifetimes
- Service resolution with dependency injection
- Scope creation

```python
from uno.core.di import Container, ServiceLifetime
from uno.core.protocols import RepositoryProtocol

# Create a container
container = Container()

# Register services
container.register(RepositoryProtocol, UserRepository, ServiceLifetime.SCOPED)
container.register(ServiceProtocol, UserService)
container.register_instance(ConfigProtocol, config_instance)

# Resolve services
service = container.resolve(ServiceProtocol)
```

### Provider

The `Provider` acts as a facade to the container and manages its lifecycle. It allows for:

- Service configuration in a central location
- Root scope creation and management
- Service resolution through the root scope

```python
from uno.core.di import Provider

# Create a custom provider
class AppProvider(Provider):
    def configure_services(self, container=None):
        container = container or self._container
        
        # Register services
        container.register(LoggerProtocol, Logger, ServiceLifetime.SINGLETON)
        container.register(ConfigProtocol, Config)
        
        # Call base to mark as configured
        super().configure_services(container)

# Create and use the provider
provider = AppProvider()
service = provider.get_service(ServiceProtocol)
```

### Scope

The `Scope` manages service instances with scoped lifetime and provides access to services from the parent container. It's useful for:

- Request-scoped services in web applications
- Transaction-scoped services in data operations
- Unit of work patterns

```python
from uno.core.di import Container

# Create a container and scope
container = Container()
container.register(RepositoryProtocol, UserRepository, ServiceLifetime.SCOPED)

# Create a scope and get services
scope = container.create_scope()
repo1 = scope.get(RepositoryProtocol)  # Same instance returned for this scope
repo2 = scope.get(RepositoryProtocol)  # Same instance as repo1

# Create another scope
another_scope = container.create_scope()
repo3 = another_scope.get(RepositoryProtocol)  # Different instance than repo1
```

## Service Lifetimes

The DI system supports three service lifetimes:

1. **Singleton** (`ServiceLifetime.SINGLETON`): Services are created once and shared across all scopes
2. **Scoped** (`ServiceLifetime.SCOPED`): Services are created once per scope
3. **Transient** (`ServiceLifetime.TRANSIENT`): Services are created each time they are requested

## FastAPI Integration

The DI system integrates with FastAPI through the `Inject` dependency:

```python
from fastapi import APIRouter, Depends
from uno.core.di.fastapi import Inject
from uno.core.protocols import ServiceProtocol

router = APIRouter()

@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    service: ServiceProtocol = Inject(ServiceProtocol)
):
    return await service.get_by_id(item_id)
```

You can also use the `DependencyProvider` directly:

```python
from fastapi import FastAPI
from uno.core.di.fastapi import DependencyProvider, cleanup_request_scope

app = FastAPI()
provider = DependencyProvider()

@app.middleware("http")
async def di_middleware(request, call_next):
    response = await call_next(request)
    await cleanup_request_scope(request)
    return response

@app.get("/items/{item_id}")
async def get_item(
    item_id: str,
    service = Depends(provider.depends(ServiceProtocol))
):
    return await service.get_by_id(item_id)
```

## Best Practices

### 1. Define Dependencies as Protocols

Define your dependencies as protocols to ensure loose coupling:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LoggerProtocol(Protocol):
    def log(self, message: str) -> None: ...
```

### 2. Use Constructor Injection

Receive dependencies via constructors:

```python
class UserService:
    def __init__(self, repository: RepositoryProtocol, logger: LoggerProtocol):
        self._repository = repository
        self._logger = logger
```

### 3. Configure Services in a Central Location

Create a custom provider to configure all services:

```python
class AppProvider(Provider):
    def configure_services(self, container=None):
        container = container or self._container
        
        # Register core services
        container.register(LoggerProtocol, Logger, ServiceLifetime.SINGLETON)
        container.register(ConfigProtocol, AppConfig, ServiceLifetime.SINGLETON)
        
        # Register repositories
        container.register(UserRepositoryProtocol, UserRepository, ServiceLifetime.SCOPED)
        container.register(ProductRepositoryProtocol, ProductRepository, ServiceLifetime.SCOPED)
        
        # Register application services
        container.register(UserServiceProtocol, UserService)
        container.register(ProductServiceProtocol, ProductService)
        
        super().configure_services(container)
```

### 4. Use Scoped Services for Request-Scoped Resources

Use scoped lifetime for database connections and other request-scoped resources:

```python
# In provider configuration
container.register(DatabaseConnectionProtocol, DatabaseConnection, ServiceLifetime.SCOPED)

# In FastAPI middleware
@app.middleware("http")
async def di_middleware(request, call_next):
    response = await call_next(request)
    await cleanup_request_scope(request)  # This will dispose of scoped services
    return response
```

### 5. Test with TestProvider

Create a test provider for unit testing:

```python
class TestProvider(Provider):
    def configure_services(self, container=None):
        container = container or self._container
        
        # Register mocks for testing
        container.register(LoggerProtocol, MockLogger, ServiceLifetime.SINGLETON)
        container.register(ConfigProtocol, MockConfig, ServiceLifetime.SINGLETON)
        container.register(RepositoryProtocol, MockRepository, ServiceLifetime.SCOPED)
        
        super().configure_services(container)
```

## Advanced Features

### Factory Registration

Register a factory function to customize service creation:

```python
def config_factory(**kwargs):
    """Create configuration based on environment."""
    env = kwargs.get("environment", "development")
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

container.register_factory(ConfigProtocol, config_factory)
```

### Child Scopes

Create child scopes for nested operations:

```python
def process_batch(items):
    # Create a scope for the batch operation
    with container.create_scope() as batch_scope:
        for item in items:
            # Create a child scope for each item
            with batch_scope.create_child_scope() as item_scope:
                service = item_scope.get(ProcessingServiceProtocol)
                service.process(item)
```