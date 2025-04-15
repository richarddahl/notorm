# Dependency Injection in Uno Framework

## Overview

The Uno framework provides a robust dependency injection (DI) system that helps organize application components, manage their lifecycle, and improve testability. The DI system is designed to be flexible, type-safe, and efficient.

## Key Concepts

### Services

Services are the building blocks of your application. They encapsulate specific functionality and can depend on other services. The Uno framework's DI system manages the lifecycle of services and resolves their dependencies automatically.

### Service Scopes

Services can have different lifetimes:

- **Singleton**: One instance per container
- **Scoped**: One instance per scope (e.g., per request)
- **Transient**: New instance each time

### Service Collection

A service collection is used to register services with the DI container. It provides a fluent interface for configuring services and their dependencies.

### Service Provider

The service provider is the central registry for all services in the application. It manages service lifecycle and provides methods for resolving services.

## Registration Methods

### Using the Service Collection

```python
from uno.dependencies.scoped_container import ServiceCollection, ServiceScope

# Create a service collection
services = ServiceCollection()

# Register services
services.add_singleton(ConfigService)
services.add_scoped(DatabaseSessionService)
services.add_transient(LoggerService)

# Register a service with an interface
services.add_singleton(IConfigService, ConfigService)

# Register a service with constructor parameters
services.add_singleton(EmailService, smtp_server="smtp.example.com", port=587)

# Register an existing instance
config = ConfigService(config_path="/path/to/config.json")
services.add_instance(IConfigService, config)
```

### Using Decorators

```python
from uno.dependencies.decorators import singleton, scoped, transient

# Register a singleton service
@singleton
class ConfigService:```

def __init__(self):```

self.config = {}
```
```

# Register a singleton service with an interface
@singleton(IConfigService)
class ConfigServiceImpl:```

def __init__(self):```

self.config = {}
```
```

# Register a scoped service
@scoped(IDatabaseService)
class DatabaseService:```

def __init__(self):```

self.connection = None
```
```

# Register a transient service
@transient(ILoggerService)
class LoggerService:```

def __init__(self):```

self.logs = []
```
```
```

## Resolving Services

### Using the Service Provider

```python
from uno.dependencies.modern_provider import get_service_provider

# Get the service provider
provider = get_service_provider()

# Get a service
config_service = provider.get_service(IConfigService)

# Get a service in a scope
with provider.create_scope() as scope:```

db_service = scope.resolve(IDatabaseService)
```
```

### Using Decorators

```python
from uno.dependencies.decorators import inject, inject_params

# Inject dependencies by type
@inject(IConfigService, IDatabaseService)
def process_data(config_service, db_service):```

# Use the services
pass
```

# Inject dependencies by parameter type annotations
@inject_params()
def process_data(config_service: IConfigService, db_service: IDatabaseService):```

# Use the services
pass
```

# Make a class's constructor use dependency injection
@injectable_class()
class DataProcessor:```

def __init__(self, config_service: IConfigService, db_service: IDatabaseService):```

self.config_service = config_service
self.db_service = db_service
```
```
```

## Scopes and Lifecycle Management

### Creating Scopes

```python
from uno.dependencies.modern_provider import get_service_provider

provider = get_service_provider()

# Synchronous scope
with provider.create_scope("my_scope") as scope:```

# Resolve services within the scope
service = scope.resolve(MyScopedService)
```

# Asynchronous scope
async with provider.create_async_scope("my_async_scope") as scope:```

# Resolve services within the scope
service = scope.resolve(MyScopedService)
```
```

### Service Lifecycle

Services can implement a lifecycle interface to perform initialization and cleanup:

```python
from uno.dependencies.modern_provider import ServiceLifecycle

@singleton
class DatabaseService(ServiceLifecycle):```

async def initialize(self) -> None:```

# Connect to the database
self.connection = await create_connection()
```

async def dispose(self) -> None:```

# Close the connection
await self.connection.close()
```
```
```

## Integration with FastAPI

The Uno framework provides seamless integration with FastAPI:

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
@router.get("/items")
async def get_items(db_service: IDatabaseService):```

return await db_service.get_items()
```

# Or use the resolve_service dependency
@app.get("/config")
async def get_config(config_service = Depends(resolve_service(IConfigService))):```

return config_service.get_config()
```

# Include the router
app.include_router(router)
```

## Automatic Service Discovery

The Uno framework can automatically discover and register services in your codebase:

```python
from uno.dependencies.discovery import scan_directory_for_services

# Scan a directory for services
scan_directory_for_services(```

directory="./src",
base_package="myapp"
```
)
```

## Testing

The Uno framework provides utilities for testing services:

```python
from unittest.mock import MagicMock
from uno.dependencies.scoped_container import ServiceCollection

# Create a service collection for testing
services = ServiceCollection()

# Register a mock service
mock_config = MagicMock(spec=IConfigService)
mock_config.get_value.return_value = "test"
services.add_instance(IConfigService, mock_config)

# Initialize the container for testing
from uno.dependencies.scoped_container import initialize_container
initialize_container(services)

# Test your service
from myapp.services import MyService
service = MyService()
assert service.get_config_value() == "test"
```

## Best Practices

1. **Use Interfaces**: Define clear interfaces for your services to improve testability and maintain separation of concerns.

2. **Minimize Service Dependencies**: Keep the number of dependencies for a service to a minimum to reduce coupling.

3. **Prefer Constructor Injection**: Inject dependencies through the constructor to make them explicit.

4. **Use Appropriate Scopes**: Choose the appropriate scope for your services based on their lifecycle requirements.

5. **Register Services Early**: Register all services during application startup to catch any configuration issues early.

6. **Test with Mock Services**: Use mock services in your tests to isolate the component under test.

7. **Use the Decorator Pattern**: Use decorators to easily register services and inject dependencies.

8. **Document Service Interfaces**: Clearly document the purpose and contract of each service interface.

9. **Organize Services by Feature**: Group related services together in feature modules.

10. **Use Lifecycle Management**: Implement the ServiceLifecycle interface for services that need initialization or cleanup.

## Advanced Topics

### Conditional Registration

```python
from uno.dependencies.modern_provider import get_service_provider

provider = get_service_provider()

# Register different implementations based on conditions
if use_real_db:```

provider.register_service(IDatabaseService, RealDatabaseService)
```
else:```

provider.register_service(IDatabaseService, MockDatabaseService)
```
```

### Factory Methods

```python
from uno.dependencies.scoped_container import ServiceCollection

services = ServiceCollection()

# Register a factory method
def create_logger(name):```

return LoggerService(name=name)
```

services.add_singleton(ILoggerService, create_logger, name="app")
```

### Scoped Database Sessions

```python
from uno.dependencies.fastapi_integration import DIAPIRouter

router = DIAPIRouter()

@router.get("/items")
async def get_items(db_service: IDatabaseService):```

# This will use a database session scoped to the request```
```

return await db_service.get_items()
```
```