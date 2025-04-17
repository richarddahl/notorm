# Domain-Oriented Dependency Injection

## Overview

The uno framework uses a domain-oriented dependency injection approach with `UnoServiceProvider`. This document explains the system and how to use it effectively.

## Key Features

1. **Domain-Oriented Approach**: Each domain module has its own service provider that manages its dependencies
2. **Comprehensive Lifecycle Management**: Full support for initialization and disposal of services
3. **Testing Utilities**: Specialized tools for testing with dependency injection
4. **FastAPI Integration**: Seamless integration with FastAPI's dependency system

## Using the System

### Domain Provider Pattern

Each domain module should follow this pattern:

```python
from functools import lru_cache
from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle

@lru_cache(maxsize=1)
def get_your_domain_provider() -> UnoServiceProvider:
    provider = UnoServiceProvider("your_domain")
    
    # Register repositories and services
    provider.register(
        YourRepository,
        lambda container: YourRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider

def configure_your_domain_services(container):
    provider = get_your_domain_provider()
    provider.configure_container(container)
```

### Service Registration

```python
# Using register method
provider.register(
    Type, 
    lambda container: Implementation(dependency=container.resolve(Dependency)), 
    lifecycle=ServiceLifecycle.SINGLETON
)

# Using register_type method (with constructor injection)
provider.register_type(
    Type, 
    Implementation, 
    lifecycle=ServiceLifecycle.SCOPED
)

# Using register_instance method
provider.register_instance(Type, instance)
```

### Lifecycle Management

```python
from uno.dependencies.modern_provider import Initializable, Disposable

class YourService(Initializable, Disposable):
    def initialize(self) -> None:
        # Initialize resources
        pass
    
    def dispose(self) -> None:
        # Clean up resources
        pass
```

### Testing Utilities

```python
from uno.dependencies.testing_provider import test_service_provider, MockService

with test_service_provider() as provider:
    # Register mocks
    mock_service = MockService()
    provider.register_mock(ServiceType, mock_service)
    
    # Use provider for testing
    service = provider.get_service(ServiceType)
```

## Documentation

For more detailed information, see:

- [Domain Provider Guide](domain_provider_guide.md) - Comprehensive guide to the domain-oriented approach
- [Domain Provider Example](domain_provider_example.py) - Example implementation of a domain provider