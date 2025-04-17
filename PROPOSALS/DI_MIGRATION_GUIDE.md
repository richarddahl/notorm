# Dependency Injection Migration Guide

This guide provides a detailed mapping between the DIContainer usage patterns and their equivalents in UnoServiceProvider to assist with the migration process.

## Import Changes

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `from uno.core.di import get_container` | `from uno.dependencies.modern_provider import get_service_provider` | Global container access |
| `from uno.core.di import get_service` | `from uno.dependencies.modern_provider import get_service_provider` | Use `get_service_provider().get_service(Type)` |
| `from uno.core.di import create_scope` | `from uno.dependencies.modern_provider import get_service_provider` | Use `get_service_provider().create_scope()` |
| `from uno.core.di import ServiceLifetime` | `from uno.dependencies.modern_provider import ServiceLifecycle` | Enum for service lifetimes |
| `from uno.core.di import DIContainer` | `from uno.dependencies.modern_provider import UnoServiceProvider` | Container class |

## Service Registration

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `container.register_singleton(Type, Implementation)` | `provider.register(Type, lambda c: Implementation(), ServiceLifecycle.SINGLETON)` | Register singleton |
| `container.register_scoped(Type, Implementation)` | `provider.register(Type, lambda c: Implementation(), ServiceLifecycle.SCOPED)` | Register scoped service |
| `container.register_transient(Type, Implementation)` | `provider.register(Type, lambda c: Implementation(), ServiceLifecycle.TRANSIENT)` | Register transient service |
| `container.register_instance(Type, instance)` | *To be implemented* | Register existing instance |
| `container.register_factory(Type, factory, lifetime)` | `provider.register(Type, factory, lifecycle)` | Register with factory |

## Service Resolution

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `container.get_service(Type)` | `provider.get_service(Type)` | Resolve service |
| `get_service(Type)` | `get_service_provider().get_service(Type)` | Global resolution |
| Constructor injection | *To be implemented* | Automatic constructor injection |

## Scope Management

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `with create_scope() as scope:` | `with get_service_provider().create_scope() as scope:` | Create scope |
| `async with create_async_scope() as scope:` | `async with get_service_provider().create_scope() as scope:` | Create async scope |
| `scope.get_service(Type)` | `scope.get_service(Type)` | Resolve from scope |

## Lifecycle Management

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `initialize_container()` | `get_service_provider().initialize()` | Initialize container |
| `reset_container()` | `get_service_provider().shutdown()` | Shutdown container |
| Service with `initialize()` method | *To be implemented* | Service initialization |
| Service with `dispose()` method | *To be implemented* | Service disposal |

## Decorator Usage

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `@service(ServiceLifetime.SINGLETON)` | `@service(ServiceLifecycle.SINGLETON)` | Service decorator |
| `@inject(Type1, Type2)` | `@inject(Type1, Type2)` | Injection decorator |
| `@inject_params()` | `@inject_params()` | Parameter injection |

## Framework Integration

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `configure_fastapi(app)` | *To be implemented* | FastAPI integration |
| `DIAPIRouter` | *To be implemented* | FastAPI router with DI |

## Domain-Specific Provider Pattern

```python
# DIContainer approach (typically global)
from uno.core.di import get_container, ServiceLifetime

def configure_my_services(container):
    container.register_singleton(MyService, MyServiceImpl)
    container.register_scoped(MyRepository, MyRepositoryImpl)

# UnoServiceProvider approach (domain-specific)
from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle
from functools import lru_cache

@lru_cache(maxsize=1)
def get_my_domain_provider() -> UnoServiceProvider:
    provider = UnoServiceProvider("my_domain")
    
    provider.register(
        MyService,
        lambda container: MyServiceImpl(
            repository=container.resolve(MyRepository),
            logger=logging.getLogger("uno.my_domain"),
        ),
        lifecycle=ServiceLifecycle.SINGLETON,
    )
    
    provider.register(
        MyRepository,
        lambda container: MyRepositoryImpl(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider

def configure_my_domain_services(container):
    provider = get_my_domain_provider()
    provider.configure_container(container)
```

## Handling Circular Dependencies

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| No direct support | `provider.add_container_configured_callback(callback)` | Configure after registration |

```python
# UnoServiceProvider approach
provider = UnoServiceProvider("my_domain")

# Register services with potential circular dependency
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

## Testing Approaches

| DIContainer | UnoServiceProvider | Note |
|-------------|-------------------|------|
| `from uno.core.di_testing import TestContainer` | *To be implemented* | Testing container |
| `reset_container()` | *To be implemented* | Reset for testing |

## Common Patterns

### Service with Dependencies (Constructor Injection)

```python
# DIContainer approach
class MyService:
    def __init__(self, repository: MyRepository, logger: Logger):
        self.repository = repository
        self.logger = logger

# After migration
class MyService:
    def __init__(self, repository: MyRepository, logger: Logger):
        self.repository = repository
        self.logger = logger

# Registration is different:
# Before:
container.register_singleton(MyService)

# After:
provider.register(
    MyService,
    lambda container: MyService(
        repository=container.resolve(MyRepository),
        logger=logging.getLogger("uno.my_domain"),
    ),
    lifecycle=ServiceLifecycle.SINGLETON,
)
```

## Migration Process

1. Identify all usages of DIContainer in the codebase
2. Convert imports to use UnoServiceProvider equivalents
3. Update service registration patterns 
4. Update service resolution patterns
5. Test thoroughly to ensure behavior is preserved

## Conclusion

This migration guide provides a mapping between DIContainer and UnoServiceProvider patterns to assist with the transition. By following these equivalents, you can systematically update the codebase to use the domain-oriented approach consistently.