# Migrating to the New Dependency Injection System

## Overview

This guide explains how to migrate from the old dependency injection system to the new system. The new system offers several advantages:

- **Proper Scoping**: Support for singleton, scoped, and transient services
- **Automatic Dependency Resolution**: Dependencies are automatically resolved based on type annotations
- **Decorator-Based Registration**: Easy service registration with decorators
- **Lifecycle Management**: Services can implement initialization and cleanup methods
- **FastAPI Integration**: Seamless integration with FastAPI

## Migration Steps

### 1. Update Imports

Replace imports from the old system with imports from the new system:

#### Old

```python
import inject
from uno.dependencies.container import get_container, get_instance
from uno.dependencies.provider import get_service_provider
```

#### New

```python
from uno.dependencies.modern_provider import (```

get_service_provider,
initialize_services,
shutdown_services
```
)
from uno.dependencies.scoped_container import (```

ServiceCollection,
ServiceScope,
get_service
```
)
from uno.dependencies.decorators import (```

singleton,
scoped,
transient,
inject,
inject_params,
injectable_class
```
)
```

### 2. Update Service Registration

Replace service registration using `inject.bind` with the new registration methods:

#### Old

```python
def configure_di(binder: inject.Binder) -> None:```

binder.bind(IConfigService, ConfigService())
binder.bind(IDatabaseService, DatabaseService())
```
    
inject.configure(configure_di)
```

#### New

**Option 1: Using decorators**

```python
@singleton(IConfigService)
class ConfigService:```

def __init__(self):```

self.config = {}
```
```

@scoped(IDatabaseService)
class DatabaseService:```

def __init__(self):```

self.connection = None
```
```
```

**Option 2: Using the service collection**

```python
from uno.dependencies.scoped_container import ServiceCollection

services = ServiceCollection()
services.add_singleton(IConfigService, ConfigService)
services.add_scoped(IDatabaseService, DatabaseService)

# Initialize the provider with the services
provider = get_service_provider()
provider.configure_services(services)
```

### 3. Update Service Resolution

Replace service resolution using `inject.instance` with the new resolution methods:

#### Old

```python
config_service = inject.instance(IConfigService)
```

#### New

```python
# Using the service provider
provider = get_service_provider()
config_service = provider.get_service(IConfigService)

# Using get_service shortcut
from uno.dependencies.scoped_container import get_service
config_service = get_service(IConfigService)

# Using decorators
@inject(IConfigService)
def use_config(config_service):```

# Use the config service
pass
```

# Using parameter type annotations
@inject_params()
def use_config(config_service: IConfigService):```

# Use the config service
pass
```
```

### 4. Update Service Implementation

Consider implementing the `ServiceLifecycle` interface for services that need initialization or cleanup:

```python
from uno.dependencies.modern_provider import ServiceLifecycle

@singleton(IDatabaseService)
class DatabaseService(ServiceLifecycle):```

def __init__(self):```

self.connection = None
```
``````

```
```

async def initialize(self) -> None:```

# Connect to the database
self.connection = await create_connection()
```
``````

```
```

async def dispose(self) -> None:```

# Close the connection
if self.connection:
    await self.connection.close()
```
```
```

### 5. Update FastAPI Integration

Replace FastAPI dependency injection with the new integration:

#### Old

```python
from fastapi import FastAPI, Depends
from uno.dependencies.fastapi import get_config_service

app = FastAPI()

@app.get("/config")
async def get_config(config_service = Depends(get_config_service)):```

return config_service.get_config()
```
```

#### New

```python
from fastapi import FastAPI
from uno.dependencies.fastapi_integration import (```

configure_fastapi,
DIAPIRouter,
resolve_service
```
)

# Create a FastAPI application
app = FastAPI()

# Configure FastAPI with Uno DI
configure_fastapi(app)

# Create a router with automatic dependency injection
router = DIAPIRouter()

# Define an endpoint with automatically injected dependencies
@router.get("/config")
async def get_config(config_service: IConfigService):```

return config_service.get_config()
```

# Include the router
app.include_router(router)
```

### 6. Update Application Startup and Shutdown

Add service initialization and shutdown to your application:

```python
from fastapi import FastAPI
from uno.dependencies.modern_provider import initialize_services, shutdown_services
from uno.dependencies.fastapi_integration import configure_fastapi

app = FastAPI()
configure_fastapi(app)

# The services will be initialized when the application starts
# and shut down when the application stops
```

If you need more control over the initialization process:

```python
from fastapi import FastAPI
from uno.dependencies.modern_provider import get_service_provider
from uno.dependencies.fastapi_integration import configure_fastapi

app = FastAPI()
configure_fastapi(app)

@app.on_event("startup")
async def startup():```

# Initialize services
provider = get_service_provider()
await provider.initialize()
```

@app.on_event("shutdown")
async def shutdown():```

# Shut down services
provider = get_service_provider()
await provider.shutdown()
```
```

### 7. Update Tests

Replace test utilities with the new testing support:

#### Old

```python
from uno.dependencies.testing import TestingContainer, MockConfig

def test_service():```

# Create test container
container = TestingContainer()
``````

```
```

# Register mock services
mock_config = MockConfig.create({"key": "value"})
container.bind(IConfigService, mock_config)
``````

```
```

# Configure and test
container.configure()
try:```

# Test your service
service = MyService()
assert service.get_config_value() == "value"
```
finally:```

container.restore()
```
```
```

#### New

```python
from unittest.mock import MagicMock
from uno.dependencies.scoped_container import ServiceCollection, initialize_container

def test_service():```

# Create a service collection for testing
services = ServiceCollection()
``````

```
```

# Register a mock service
mock_config = MagicMock(spec=IConfigService)
mock_config.get_value.return_value = "value"
services.add_instance(IConfigService, mock_config)
``````

```
```

# Initialize the container for testing
initialize_container(services)
``````

```
```

# Test your service
service = MyService()
assert service.get_config_value() == "value"
```
```

## Examples

### Basic Service Example

```python
from uno.dependencies.decorators import singleton, inject_params

# Define a service
@singleton
class LoggerService:```

def log(self, message: str) -> None:```

print(f"[LOG] {message}")
```
```

# Define a service that depends on another service
@singleton
@injectable_class()
class UserService:```

def __init__(self, logger: LoggerService):```

self.logger = logger
```
``````

```
```

def get_user(self, user_id: str) -> dict:```

self.logger.log(f"Getting user {user_id}")
return {"id": user_id, "name": "Test User"}
```
```

# Use the service
@inject_params()
def process_user(user_id: str, user_service: UserService) -> dict:```

return user_service.get_user(user_id)
```
```

### FastAPI Example

```python
from fastapi import FastAPI
from uno.dependencies.fastapi_integration import (```

configure_fastapi,
DIAPIRouter
```
)
from uno.dependencies.decorators import singleton, scoped

# Define a service
@singleton
class ConfigService:```

def get_config(self) -> dict:```

return {"app_name": "My App", "version": "1.0.0"}
```
```

# Define a scoped service
@scoped
class RequestContext:```

def __init__(self):```

self.user_id = None
```
``````

```
```

def set_user_id(self, user_id: str) -> None:```

self.user_id = user_id
```
```

# Create a FastAPI application
app = FastAPI()
configure_fastapi(app)

# Create a router with automatic dependency injection
router = DIAPIRouter()

# Define an endpoint with automatically injected dependencies
@router.get("/config")
async def get_config(config: ConfigService):```

return config.get_config()
```

# Define an endpoint with scoped services
@router.get("/users/{user_id}")
async def get_user(user_id: str, context: RequestContext, config: ConfigService):```

context.set_user_id(user_id)
return {```

"user_id": context.user_id,
"app_name": config.get_config()["app_name"]
```
}
```

# Include the router
app.include_router(router)
```

## Common Issues

### Circular Dependencies

If you encounter circular dependencies, consider refactoring your services to break the cycle:

1. **Extract Interface**: Move the common functionality to an interface
2. **Use Event Bus**: Use an event bus to decouple components
3. **Lazy Resolution**: Resolve dependencies lazily when needed

### Missing Dependencies

If a dependency is not found, check that:

1. The service is registered with the correct interface
2. The service is registered before it's used
3. The dependency is annotated correctly

### Scope Issues

If you encounter scope issues:

1. **Singleton Depending on Scoped**: Singletons should not depend on scoped services
2. **Scoped Outside Scope**: Scoped services can only be resolved within a scope

## Migration Checklist

- [ ] Update imports to use the new DI system
- [ ] Update service registration to use decorators or the service collection
- [ ] Update service resolution to use the new methods
- [ ] Implement lifecycle management for services that need it
- [ ] Update FastAPI integration
- [ ] Update application startup and shutdown
- [ ] Update tests
- [ ] Verify all services are properly initialized and disposed