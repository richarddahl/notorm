# Modern Service Provider

The `UnoServiceProvider` is a modern dependency injection container for the Uno framework. It provides a centralized way to register, configure, and manage services throughout the application.

## Basic Usage

```python
from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle
from uno.database.db_manager import DBManager

# Create a provider for a specific domain
provider = UnoServiceProvider("my_domain")

# Register repositories and services
provider.register(
    MyRepository,
    lambda container: MyRepository(
        db_factory=container.resolve(DBManager),
    ),
    lifecycle=ServiceLifecycle.SCOPED,
)

provider.register(
    MyService,
    lambda container: MyService(
        repository=container.resolve(MyRepository),
        logger=logging.getLogger("uno.my_domain"),
    ),
    lifecycle=ServiceLifecycle.SCOPED,
)

# Configure a container with all registered services
provider.configure_container(container)
```

## Service Lifecycles

The `ServiceLifecycle` class provides constants for different service lifetimes:

- `ServiceLifecycle.SINGLETON`: The service is created once and reused for all requests
- `ServiceLifecycle.SCOPED`: The service is created once per scope (e.g., per request)
- `ServiceLifecycle.TRANSIENT`: The service is created every time it's requested

## Handling Circular Dependencies

Sometimes services need to reference each other, creating a circular dependency. This can be resolved using the `add_container_configured_callback` method:

```python
provider = UnoServiceProvider("my_domain")

# Register services with potential circular dependency
provider.register(
    ServiceA,
    lambda container: ServiceA(
        # ServiceB not available yet
        logger=logging.getLogger("uno.my_domain"),
    ),
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

## Domain Provider Pattern

The recommended pattern for domain modules is to create a provider function that configures and returns a `UnoServiceProvider`:

```python
import logging
from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.database.db_manager import DBManager
from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
)
from my_domain.domain_repositories import MyRepository
from my_domain.domain_services import MyService

@lru_cache(maxsize=1)
def get_my_domain_provider() -> UnoServiceProvider:
    """
    Get the MyDomain module service provider.
    
    Returns:
        A configured service provider for the MyDomain module
    """
    provider = UnoServiceProvider("my_domain")
    logger = logging.getLogger("uno.my_domain")
    
    # Register repositories
    provider.register(
        MyRepository,
        lambda container: MyRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register services
    provider.register(
        MyService,
        lambda container: MyService(
            repository=container.resolve(MyRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider

def configure_my_domain_services(container):
    """
    Configure MyDomain services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_my_domain_provider()
    provider.configure_container(container)
```