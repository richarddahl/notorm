# Dependency Injection System

This document explains the Dependency Injection (DI) system in uno, which provides a modern, type-safe approach to managing dependencies.

## Overview

The uno DI system provides:

- **Type-Safe Injection**: All dependencies are registered with proper type information
- **Lifetime Management**: Support for singleton, scoped, and transient services
- **Automatic Resolution**: Dependencies of dependencies are automatically resolved
- **Scope Management**: Proper lifecycle management with scope disposal
- **FastAPI Integration**: Seamless integration with FastAPI dependency system
- **Testing Utilities**: Tools to make testing with DI easier

## Core Components

### DIContainer

The `DIContainer` is the central registry for all services:

```python
from uno.core.di import DIContainer

# Create a container
container = DIContainer()

# Register services
container.register_singleton(Logger, ConsoleLogger)
container.register_scoped(DbSession, AsyncDbSession)
container.register_transient(PasswordHasher, BCryptHasher)
```

### Service Lifetime

The DI system supports three service lifetimes:

1. **Singleton**: Created once and shared across all requests
2. **Scoped**: Created once per scope (e.g., per HTTP request)
3. **Transient**: Created each time requested

```python
# Singleton: One instance for the application lifetime
container.register_singleton(ConfigService)

# Scoped: One instance per scope (e.g., per HTTP request)
container.register_scoped(DbSession)

# Transient: New instance each time requested
container.register_transient(PasswordGenerator)
```

### ServiceScope

Scopes manage the lifecycle of scoped services:

```python
# Creating a scope
with container.create_scope() as scope:```

# Get a service from the scope
session = scope.resolve(DbSession)
# ...
```
# Session is disposed when scope ends
```

### Async Support

The DI system fully supports async initialization and disposal:

```python
# Creating an async scope
async with container.create_async_scope() as scope:```

# Get a service from the scope
session = scope.resolve(DbSession)
# ...
``` do async work ...
# Session is disposed asynchronously when scope ends
```

## Public API

The DI system provides a simple public API for most use cases:

```python
from uno.core.di import get_service, create_scope, create_async_scope

# Get a singleton service
logger = get_service(Logger)

# Create a scope
with create_scope() as scope:```

# Get a scoped service
session = scope.resolve(DbSession)
# Use the service
result = session.query(...)
```

# With async
async with create_async_scope() as scope:```

# Get a scoped service
session = scope.resolve(AsyncDbSession)
# Use the service
result = await session.query(...)
```
```

## Service Registration

Services can be registered in several ways:

### By Type

```python
# Register a concrete type
container.register_singleton(Logger, ConsoleLogger)

# Register a singleton instance
logger = ConsoleLogger()
container.register_instance(Logger, logger)

# Self-registration (implementation is the same as the service type)
container.register_singleton(ConsoleLogger)
```

### With Factory Functions

```python
# Register with a factory function
container.register_singleton(```

DbConnection,
lambda c: DbConnection(```

get_service(ConnectionConfig).connection_string
```
)
```
)
```

### With Parameters

```python
# Register with explicit parameters
container.register_singleton(```

UserService,
parameters={```

"strict_mode": True,
"max_retries": 3
```
}
```
)
```

## FastAPI Integration

The DI system integrates seamlessly with FastAPI:

```python
from fastapi import FastAPI, Depends
from uno.core.di_fastapi import FromDI

app = FastAPI()

# Use the DI system with FastAPI
@app.get("/users/{user_id}")
async def get_user(```

user_id: int,
user_service: UserService = Depends(FromDI(UserService))
```
):```

return await user_service.get_user(user_id)
```
```

### Request Scopes

The DI system automatically creates a scope for each FastAPI request:

```python
from uno.core.di_fastapi import configure_di_middleware

app = FastAPI()

# Configure the DI middleware
configure_di_middleware(app)

# Now each request gets its own DI scope
@app.get("/data")
async def get_data(```

session: DbSession = Depends(FromDI(DbSession))
```
):```

# This session is scoped to this request
return await session.query(...)
```
```

## Testing with DI

The DI system provides special utilities for testing:

```python
from uno.core.di_testing import test_container, inject_mock

# Create a test-specific container
with test_container() as container:```

# Register test versions of services
container.register_singleton(Logger, TestLogger)
# Run tests...
```

# Temporarily inject a mock
user_repo_mock = Mock(spec=UserRepository)
user_repo_mock.get_user.return_value = User(id=1, name="Test")

with inject_mock(UserRepository, user_repo_mock):```

# Code using get_service(UserRepository) will get the mock
service = UserService(get_service(UserRepository))
user = service.get_user(1)
assert user.name == "Test"
```
```

## Best Practices

### 1. Constructor Injection

Always prefer constructor injection over service location:

```python
# Good: Dependencies are explicit
class UserService:```

def __init__(self, user_repo: UserRepository, logger: Logger):```

self.user_repo = user_repo
self.logger = logger
```
```

# Usage
service = UserService(get_service(UserRepository), get_service(Logger))
```

### 2. Use Protocols for Interfaces

Define service interfaces using protocols:

```python
from typing import Protocol

class UserRepository(Protocol):```

async def get_user(self, user_id: int) -> User: ...
async def save_user(self, user: User) -> None: ...
```

# Implementation
class PostgresUserRepository:```

async def get_user(self, user_id: int) -> User:```

# Implementation...
```
``````

```
```

async def save_user(self, user: User) -> None:```

# Implementation...
```
```

# Registration
container.register_singleton(UserRepository, PostgresUserRepository)
```

### 3. Manage Lifetimes Carefully

Choose appropriate lifetimes for services:

- **Singleton**: For stateless services or services with global state
- **Scoped**: For services that need to be consistent within a request
- **Transient**: For services that should be created each time

### 4. Use Scope Properly

Always dispose scopes when done:

```python
# Good: Scope is properly disposed
with create_scope() as scope:```

service = scope.resolve(SomeService)
# Use service...
```

# Good: Async scope is properly disposed
async with create_async_scope() as scope:```

service = scope.resolve(AsyncService)
# Use service...
```
```

## Example: Complete Service Setup

Here's a complete example of setting up and using the DI system:

```python
from uno.core.di import (```

DIContainer, ServiceCollection, 
get_container, initialize_container,
get_service, create_scope, create_async_scope
```
)

# Define services
class Logger:```

def log(self, message: str): ...
```

class ConsoleLogger(Logger):```

def log(self, message: str):```

print(f"[LOG] {message}")
```
```

class DbConnection:```

def __init__(self, connection_string: str):```

self.connection_string = connection_string
```
``````

```
```

async def connect(self): ...
async def disconnect(self): ...
```

class UserRepository:```

def __init__(self, db_connection: DbConnection):```

self.db_connection = db_connection
```
``````

```
```

async def get_user(self, user_id: int): ...
```

class UserService:```

def __init__(```

self, 
user_repository: UserRepository,
logger: Logger
```
):```

self.user_repository = user_repository
self.logger = logger
```
``````

```
```

async def get_user(self, user_id: int):```

self.logger.log(f"Getting user {user_id}")
return await self.user_repository.get_user(user_id)
```
```

# Set up services
services = ServiceCollection()

# Register services
services.add_singleton(Logger, ConsoleLogger)
services.add_singleton(DbConnection, lambda c: DbConnection("postgres://localhost/app"))
services.add_scoped(UserRepository)
services.add_scoped(UserService)

# Initialize container
initialize_container(services)

# Application code
async def main():```

# Create a scope for the operation
async with create_async_scope() as scope:```

# Get the service from the scope
user_service = scope.resolve(UserService)
```
    ```

# Use the service
user = await user_service.get_user(123)
```
    ```

# Work with the user
print(f"Found user: {user.name}")
```
    ```

# Scope automatically disposes when exiting
```
```
```

## Additional Resources

- [Example: DI with FastAPI](/src/uno/core/examples/di_fastapi_example.py)
<!-- TODO: Create testing with DI documentation -->
<!-- - [Testing with DI](../testing/dependency_injection.md) -->
<!-- TODO: Create advanced DI patterns documentation -->
<!-- - [Advanced DI Patterns](../advanced/di_patterns.md) -->