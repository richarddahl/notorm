# Domain-Oriented Dependency Injection Guide

This guide explains the domain-oriented dependency injection approach used in the uno framework, which is based on the `UnoServiceProvider` class.

## Introduction

The uno framework uses a domain-oriented approach to dependency injection, where each domain module has its own service provider. This approach has several advantages:

- **Domain Boundary Enforcement**: Each domain manages its own dependencies, enforcing clear boundaries between domains
- **Explicit Dependencies**: Dependencies between domains are explicit, making the codebase easier to understand
- **Modular Testing**: Each domain can be tested independently
- **Reduced Global State**: Minimizes reliance on global state by encapsulating dependencies within domains

## Domain Provider Pattern

### Basic Structure

Each domain module should follow this pattern:

```python
from functools import lru_cache
import logging
from typing import Dict, Any, Optional, Type

from uno.database.db_manager import DBManager
from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
)
from your_domain.domain_repositories import YourRepository
from your_domain.domain_services import YourService

@lru_cache(maxsize=1)
def get_your_domain_provider() -> UnoServiceProvider:
    """
    Get the YourDomain module service provider.
    
    Returns:
        A configured service provider for the YourDomain module
    """
    provider = UnoServiceProvider("your_domain")
    logger = logging.getLogger("uno.your_domain")
    
    # Register repositories
    provider.register(
        YourRepository,
        lambda container: YourRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register services
    provider.register(
        YourService,
        lambda container: YourService(
            repository=container.resolve(YourRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider

def configure_your_domain_services(container):
    """
    Configure YourDomain services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_your_domain_provider()
    provider.configure_container(container)
```

### Key Components

- **Domain Provider Function**: A cached function that returns a configured `UnoServiceProvider` for the domain
- **Repository Registration**: Registers repositories with their dependencies
- **Service Registration**: Registers services with their dependencies
- **Configuration Function**: Configures a container with the domain's services

## Creating a New Domain Provider

1. **Create a domain_provider.py file** in your domain module
2. **Define a get_your_domain_provider() function** that returns a configured `UnoServiceProvider`
3. **Register repositories and services** with their dependencies
4. **Define a configure_your_domain_services() function** that configures a container with the domain's services

## Service Registration

### Registering Services

The `UnoServiceProvider` supports three types of service registration:

1. **Factory-based registration**:

```python
provider.register(
    YourService,
    lambda container: YourService(
        dependency=container.resolve(Dependency),
    ),
    lifecycle=ServiceLifecycle.SINGLETON,
)
```

2. **Type-based registration with constructor injection**:

```python
provider.register_type(
    YourService,
    YourServiceImplementation,
    lifecycle=ServiceLifecycle.SCOPED,
)
```

3. **Instance registration**:

```python
instance = YourService()
provider.register_instance(YourService, instance)
```

### Service Lifecycles

The `UnoServiceProvider` supports three lifecycle options:

- **SINGLETON**: One instance for the entire application
- **SCOPED**: One instance per scope (e.g., per request)
- **TRANSIENT**: New instance every time it's requested

```python
from uno.dependencies.modern_provider import ServiceLifecycle

# Singleton
provider.register(Type, factory, lifecycle=ServiceLifecycle.SINGLETON)

# Scoped
provider.register(Type, factory, lifecycle=ServiceLifecycle.SCOPED)

# Transient
provider.register(Type, factory, lifecycle=ServiceLifecycle.TRANSIENT)
```

## Handling Circular Dependencies

In some cases, services need to reference each other, creating a circular dependency. You can resolve this using container configuration callbacks:

```python
provider = UnoServiceProvider("my_domain")

# Register services
provider.register(
    ServiceA,
    lambda container: ServiceA(logger=logging.getLogger("uno.my_domain")),
    lifecycle=ServiceLifecycle.SCOPED,
)

provider.register(
    ServiceB,
    lambda container: ServiceB(
        service_a=container.resolve(ServiceA),
        logger=logging.getLogger("uno.my_domain"),
    ),
    lifecycle=ServiceLifecycle.SCOPED,
)

# Add a callback to resolve the circular dependency
def configure_circular_dependencies(container):
    service_a = container.resolve(ServiceA)
    service_b = container.resolve(ServiceB)
    service_a.service_b = service_b

provider.add_container_configured_callback(configure_circular_dependencies)
```

## Lifecycle Management

Services can implement initialization and disposal methods:

```python
from uno.dependencies.modern_provider import Initializable, Disposable

class YourService(Initializable, Disposable):
    def initialize(self) -> None:
        """Initialize resources."""
        self._resources = {}
    
    def dispose(self) -> None:
        """Clean up resources."""
        self._resources.clear()
```

For asynchronous initialization and disposal:

```python
from uno.dependencies.modern_provider import AsyncInitializable, AsyncDisposable

class YourAsyncService(AsyncInitializable, AsyncDisposable):
    async def initialize_async(self) -> None:
        """Initialize resources asynchronously."""
        self._client = await create_async_client()
    
    async def dispose_async(self) -> None:
        """Clean up resources asynchronously."""
        await self._client.close()
```

## Using Services

### Direct Resolution

You can resolve services directly from the container:

```python
provider = get_your_domain_provider()
service = provider.get_service(YourService)
```

### With Scope

For scoped services, create a scope:

```python
provider = get_your_domain_provider()
with provider.create_scope() as scope:
    service = scope.resolve(YourService)
    # Use service...
```

### Async Scope

For async code:

```python
provider = get_your_domain_provider()
async with provider.create_scope() as scope:
    service = scope.resolve(YourService)
    # Use service...
```

## FastAPI Integration

### Configuring FastAPI

```python
from fastapi import FastAPI
from uno.dependencies.fastapi_provider import configure_fastapi

app = FastAPI()
configure_fastapi(app)
```

### Using Services in Endpoints

```python
from fastapi import Depends
from uno.dependencies.fastapi_provider import resolve_service

@app.get("/items/{item_id}")
async def get_item(
    item_id: int, 
    service: YourService = Depends(resolve_service(YourService))
):
    return service.get_item(item_id)
```

### DIAPIRouter

```python
from uno.dependencies.fastapi_provider import DIAPIRouter

router = DIAPIRouter()

@router.get("/items/{item_id}")
async def get_item(item_id: int, service: YourService):
    # YourService will be injected automatically
    return service.get_item(item_id)

app.include_router(router)
```

## Testing with Dependency Injection

### TestServiceProvider

```python
from uno.dependencies.testing_provider import TestServiceProvider, MockService

# Create a test service provider
provider = TestServiceProvider()

# Create and register a mock
mock_service = MockService()
provider.register_mock(YourService, mock_service)

# Use the provider
service = provider.get_service(YourService)
```

### With Context Manager

```python
from uno.dependencies.testing_provider import test_service_provider

with test_service_provider() as provider:
    # Register mocks
    provider.register_mock(YourService, mock_service)
    
    # Test your code
    service = provider.get_service(YourService)
    # ...
```

## Best Practices

1. **Domain Isolation**: Keep domain dependencies isolated to enforce boundaries
2. **Explicit Configuration**: Make dependencies explicit in your domain provider
3. **Consistent Lifecycle**: Use consistent service lifecycles
4. **Circular Dependency Handling**: Use configuration callbacks for circular dependencies
5. **Testing**: Use TestServiceProvider for testing
6. **Documentation**: Document your domain provider and its dependencies

## Adapter Layer

For compatibility with existing code, the framework includes an adapter layer:

```python
from uno.core import get_container, get_service, create_scope

# Using the container
container = get_container()
service = get_service(YourService)

# Using scopes
with create_scope() as scope:
    scoped_service = scope.get_service(YourService)
```

This adapter layer forwards calls to the underlying `UnoServiceProvider` system.

## Conclusion

The domain-oriented dependency injection approach provides a powerful and flexible way to manage dependencies in your application. By following the domain provider pattern, you can create a maintainable, testable, and modular codebase.