# Migrating to the Modern Dependency Injection System

This guide provides instructions for migrating from the legacy dependency injection approach to the modern DI system in uno.

## Overview of Changes

The uno framework has transitioned from a legacy DI system using the `inject` library to a modern, custom-built DI container with the following improvements:

- Hierarchical scoping (singleton, scoped, transient)
- Proper async lifecycle support
- Automatic dependency resolution
- Protocol-based interface definitions
- Centralized service provider
- Improved FastAPI integration
- Better testability

## Key Migration Steps

Follow these steps to migrate your code to the modern DI system:

### 1. Replace Legacy Imports

**Before:**
```python
from uno.dependencies import get_instance, configure_di
from uno.dependencies.container import UnoContainer
import inject
```

**After:**
```python
from uno.dependencies.scoped_container import get_service, ServiceCollection, initialize_container
from uno.dependencies.modern_provider import get_service_provider, initialize_services
```

### 2. Replace Service Resolution

**Before:**
```python
# Using inject.instance()
service = inject.instance(ServiceType)

# Using get_instance()
service = get_instance(ServiceType)

# Using container
container = UnoContainer.get_instance()
service = container.get(ServiceType)
```

**After:**
```python
# For singleton services
service = get_service(ServiceType)

# Using service provider
provider = get_service_provider()
service = provider.get_service(ServiceType)

# In scoped context
with create_scope() as scope:```

service = scope.resolve(ServiceType)
```

# In async scoped context
async with create_async_scope() as scope:```

service = scope.resolve(ServiceType)
```
```

### 3. Replace Dependency Registration

**Before:**
```python
def configure_di(binder):```

# Bind services
binder.bind(ServiceType, ServiceImplementation())
binder.bind_to_provider(ServiceType, lambda: ServiceImplementation())
```

# Configure the container
inject.configure(configure_di)
```

**After:**
```python
# Create service collection
services = ServiceCollection()

# Register services
services.add_singleton(ServiceType, ServiceImplementation)
services.add_scoped(ServiceType, ServiceImplementation)
services.add_transient(ServiceType, ServiceImplementation)
services.add_instance(ServiceType, existing_instance)

# Initialize container
initialize_container(services)

# For application startup
await initialize_services()  # Calls configure_base_services() internally
```

### 4. Update FastAPI Dependencies

**Before:**
```python
from uno.dependencies import inject_dependency, get_repository

@router.get("/items")
async def list_items(```

config = Depends(inject_dependency(ConfigType)),
repo = Depends(get_repository(RepoType))
```
):```

# Use dependencies
pass
```
```

**After:**
```python
from uno.dependencies.database import get_repository
from uno.dependencies.decorators import inject_params

# Configure FastAPI with DI
from uno.dependencies.fastapi_integration import configure_fastapi
configure_fastapi(app)

@router.get("/items")
@inject_params()  # Optional decorator for constructor injection
async def list_items(```

repo = Depends(get_repository(RepoType))
```
):```

# Use dependencies
pass
```
```

### 5. Update Testing Code

**Before:**
```python
def configure_test_di(binder):```

# Create mocks
mock_service = MagicMock()
``````

```
```

# Bind mocks
binder.bind(ServiceType, mock_service)
```

@pytest.fixture
def setup_di():```

# Configure test container
inject.clear_and_configure(configure_test_di)
``````

```
```

# Get service from container
service = inject.instance(ServiceType)
return service
```
```

**After:**
```python
@pytest.fixture
def setup_test_di():```

# Create mocks
mock_service = MagicMock(spec=ServiceImplementation)
``````

```
```

# Create service collection
services = ServiceCollection()
services.add_instance(ServiceType, mock_service)
``````

```
```

# Initialize container with test services
initialize_container(services, logging.getLogger("test"))
``````

```
```

return mock_service
```

@pytest.fixture
def service():```

# Get service from container
return get_service(ServiceType)
```
```

## Lifecycle Management Migration

For services that need initialization and cleanup:

**Before:**
```python
class MyService:```

def __init__(self):```

self.initialized = False
```
    
def initialize(self):```

# Initialize resources
self.initialized = True
```
    
def cleanup(self):```

# Clean up resources
pass
```
```

# Manual initialization
service = get_instance(MyService)
service.initialize()
```

**After:**
```python
from uno.dependencies.modern_provider import ServiceLifecycle

class MyService(ServiceLifecycle):```

def __init__(self):```

self.initialized = False
```
    
async def initialize(self) -> None:```

# Initialize resources asynchronously
self.initialized = True
```
    
async def dispose(self) -> None:```

# Clean up resources asynchronously
pass
```
```

# Register for automatic lifecycle management
provider = get_service_provider()
provider.register_lifecycle_service(MyService)

# Service will be automatically initialized during startup
```

## Integration with FastAPI Application Lifecycle

Update your FastAPI application to properly initialize the DI system:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):```

# Initialize services on startup
from uno.dependencies.modern_provider import initialize_services
await initialize_services()
``````

```
```

# Yield control to FastAPI
yield
``````

```
```

# Shut down services on shutdown
from uno.dependencies.modern_provider import shutdown_services
await shutdown_services()
```

# Create app with lifespan
app = FastAPI(lifespan=lifespan)
```

## Validation

Use the validation script to verify that all legacy patterns have been removed:

```bash
python src/scripts/validate_clean_slate.py
```

This script checks for:
1. Banned imports from removed modules
2. Legacy class references
3. Legacy methods
4. Usage of `inject.instance()` or `get_instance()` methods

When all checks pass, your codebase is successfully migrated to the modern DI system.

## Benefits of Migration

By completing this migration, you'll gain:

1. **Improved Performance**: The modern DI system is more efficient
2. **Better Testability**: Easier to mock dependencies and test components in isolation
3. **Async Support**: Proper handling of async initialization and cleanup
4. **Better Scoping**: Hierarchical scopes for better resource management
5. **Simplified Code**: Cleaner, more consistent codebase

## Common Migration Issues

### Circular Dependencies

If you encounter circular dependencies during migration:

1. Use lazy loading by importing inside functions or methods
2. Restructure your code to eliminate circular dependencies
3. Use factory functions to break dependency cycles

### Missing Services

If services are not being resolved:

1. Verify that services are registered in the correct scope
2. Check for typos in service type annotations
3. Ensure services are registered before they are used
4. Verify that the service provider is properly initialized

### Async Event Loop Issues

If you encounter async event loop errors:

1. Ensure service initialization happens within the FastAPI lifespan
2. Avoid running `asyncio.run()` from inside an existing event loop
3. Use proper async context managers for scoped resources