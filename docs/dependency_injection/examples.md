# Dependency Injection Examples

This page provides practical examples of using uno's dependency injection system in various scenarios.

## Basic Service Registration and Resolution

### Defining Service Interfaces

```python
from typing import Protocol, Dict, Any, List

class ConfigServiceProtocol(Protocol):```

"""Configuration service interface."""
``````

```
```

def get_value(self, key: str, default: Any = None) -> Any:```

"""Get a configuration value by key."""
...
```
``````

```
```

def all(self) -> Dict[str, Any]:```

"""Get all configuration values."""
...
```
```

class LoggerServiceProtocol(Protocol):```

"""Logger service interface."""
``````

```
```

def debug(self, message: str) -> None:```

"""Log a debug message."""
...
```
``````

```
```

def info(self, message: str) -> None:```

"""Log an info message."""
...
```
``````

```
```

def warning(self, message: str) -> None:```

"""Log a warning message."""
...
```
``````

```
```

def error(self, message: str) -> None:```

"""Log an error message."""
...
```
```

class UserRepositoryProtocol(Protocol):```

"""User repository interface."""
``````

```
```

async def get_user(self, user_id: str) -> Dict[str, Any]:```

"""Get a user by ID."""
...
```
``````

```
```

async def get_users(self) -> List[Dict[str, Any]]:```

"""Get all users."""
...
```
``````

```
```

async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Create a new user."""
...
```
``````

```
```

async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Update a user."""
...
```
``````

```
```

async def delete_user(self, user_id: str) -> bool:```

"""Delete a user."""
...
```
```
```

### Implementing Services

```python
import logging
from typing import Dict, Any, List, Optional
import json
import os

from uno.dependencies.decorators import singleton, scoped, transient, injectable_class
from uno.dependencies.modern_provider import ServiceLifecycle

@singleton(ConfigServiceProtocol)
class ConfigService(ConfigServiceProtocol):```

"""Configuration service implementation."""
``````

```
```

def __init__(self, config_path: str = "config.json"):```

"""Initialize the configuration service."""
self.config_path = config_path
self.config = {}
self._load_config()
```
``````

```
```

def _load_config(self) -> None:```

"""Load the configuration from a JSON file."""
if os.path.exists(self.config_path):
    with open(self.config_path, "r") as f:
        self.config = json.load(f)
```
``````

```
```

def get_value(self, key: str, default: Any = None) -> Any:```

"""Get a configuration value by key."""
return self.config.get(key, default)
```
``````

```
```

def all(self) -> Dict[str, Any]:```

"""Get all configuration values."""
return self.config.copy()
```
```

@singleton(LoggerServiceProtocol)
class LoggerService(LoggerServiceProtocol, ServiceLifecycle):```

"""Logger service implementation."""
``````

```
```

def __init__(self, logger_name: str = "app"):```

"""Initialize the logger service."""
self.logger = logging.getLogger(logger_name)
self.handler = None
```
``````

```
```

async def initialize(self) -> None:```

"""Initialize the logger."""
# Set up logging handlers
self.handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
self.handler.setFormatter(formatter)
self.logger.addHandler(self.handler)
self.logger.setLevel(logging.INFO)
self.logger.info("Logger initialized")
```
``````

```
```

async def dispose(self) -> None:```

"""Clean up the logger."""
if self.handler:
    self.logger.removeHandler(self.handler)
    self.handler.close()
    self.logger.info("Logger disposed")
```
``````

```
```

def debug(self, message: str) -> None:```

"""Log a debug message."""
self.logger.debug(message)
```
``````

```
```

def info(self, message: str) -> None:```

"""Log an info message."""
self.logger.info(message)
```
``````

```
```

def warning(self, message: str) -> None:```

"""Log a warning message."""
self.logger.warning(message)
```
``````

```
```

def error(self, message: str) -> None:```

"""Log an error message."""
self.logger.error(message)
```
```

@scoped(UserRepositoryProtocol)
@injectable_class()
class UserRepository(UserRepositoryProtocol):```

"""User repository implementation."""
``````

```
```

def __init__(self, config: ConfigServiceProtocol, logger: LoggerServiceProtocol):```

"""Initialize the user repository."""
self.config = config
self.logger = logger
self.users = {}
self.logger.info("UserRepository initialized")
```
``````

```
```

async def get_user(self, user_id: str) -> Dict[str, Any]:```

"""Get a user by ID."""
self.logger.debug(f"Getting user {user_id}")
return self.users.get(user_id, {})
```
``````

```
```

async def get_users(self) -> List[Dict[str, Any]]:```

"""Get all users."""
self.logger.debug("Getting all users")
return list(self.users.values())
```
``````

```
```

async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Create a new user."""
user_id = user_data.get("id")
self.logger.info(f"Creating user {user_id}")
self.users[user_id] = user_data```
```

return user
```_data
``````

```
```

async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Update a user."""
self.logger.info(f"Updating user {user_id}")
if user_id in self.users:
    self.users[user_id].update(user_data)
    return self.users[user_id]
return {}
```
``````

```
```

async def delete_user(self, user_id: str) -> bool:```

"""Delete a user."""
self.logger.info(f"Deleting user {user_id}")
if user_id in self.users:
    del self.users[user_id]
    return True
return False
```
```
```

### Service Composition

```python
from typing import Dict, Any, List, Optional
from uno.dependencies.decorators import singleton, inject_params, injectable_class

@singleton
@injectable_class()
class UserService:```

"""User service implementation."""
``````

```
```

def __init__(self, user_repository: UserRepositoryProtocol, logger: LoggerServiceProtocol):```

"""Initialize the user service."""
self.user_repository = user_repository
self.logger = logger
self.logger.info("UserService initialized")
```
``````

```
```

async def get_user(self, user_id: str) -> Dict[str, Any]:```

"""Get a user by ID."""
self.logger.debug(f"UserService getting user {user_id}")
return await self.user_repository.get_user(user_id)
```
``````

```
```

async def get_users(self) -> List[Dict[str, Any]]:```

"""Get all users."""
self.logger.debug("UserService getting all users")
return await self.user_repository.get_users()
```
``````

```
```

async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Create a new user."""
self.logger.info(f"UserService creating user {user_data.get('id')}")
return await self.user_repository.create_user(user_data)
```
``````

```
```

async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Update a user."""
self.logger.info(f"UserService updating user {user_id}")
return await self.user_repository.update_user(user_id, user_data)
```
``````

```
```

async def delete_user(self, user_id: str) -> bool:```

"""Delete a user."""
self.logger.info(f"UserService deleting user {user_id}")
return await self.user_repository.delete_user(user_id)
```
```

# Using the service with dependency injection
@inject_params()
async def process_user(user_id: str, user_service: UserService) -> Dict[str, Any]:```

"""Process a user."""
return await user_service.get_user(user_id)
```
```

## FastAPI Integration

### Basic API Setup

```python
from fastapi import FastAPI
from uno.dependencies.fastapi_integration import configure_fastapi, DIAPIRouter
from uno.dependencies.modern_provider import initialize_services, shutdown_services

# Create a FastAPI application
app = FastAPI()

# Configure FastAPI with uno DI
configure_fastapi(app)

# Create API endpoints

@app.on_event("startup")
async def startup():```

# Initialize services
await initialize_services()
```

@app.on_event("shutdown")
async def shutdown():```

# Shut down services
await shutdown_services()
```
```

### API Endpoints with Dependency Injection

```python
from fastapi import FastAPI, Path, Query, Body, HTTPException
from typing import Dict, Any, List, Optional

from uno.dependencies.fastapi_integration import DIAPIRouter

# Create a router with automatic dependency injection
router = DIAPIRouter(prefix="/api/users", tags=["users"])

@router.get("/")
async def get_users(```

user_service: UserService,
limit: int = Query(10, description="Maximum number of users to return")
```
) -> List[Dict[str, Any]]:```

"""Get all users."""
users = await user_service.get_users()
return users[:limit]
```

@router.get("/{user_id}")
async def get_user(```

user_id: str = Path(..., description="The ID of the user to get"),
user_service: UserService = None  # This will be injected automatically
```
) -> Dict[str, Any]:```

"""Get a user by ID."""
user = await user_service.get_user(user_id)
if not user:```

raise HTTPException(status_code=404, detail="User not found")
```
return user
```

@router.post("/")
async def create_user(```

user_data: Dict[str, Any] = Body(..., description="The user data"),
user_service: UserService = None  # This will be injected automatically
```
) -> Dict[str, Any]:```

"""Create a new user."""
return await user_service.create_user(user_data)
```

@router.put("/{user_id}")
async def update_user(```

user_id: str = Path(..., description="The ID of the user to update"),
user_data: Dict[str, Any] = Body(..., description="The updated user data"),
user_service: UserService = None  # This will be injected automatically
```
) -> Dict[str, Any]:```

"""Update a user."""
user = await user_service.update_user(user_id, user_data)
if not user:```

raise HTTPException(status_code=404, detail="User not found")
```
return user
```

@router.delete("/{user_id}")
async def delete_user(```

user_id: str = Path(..., description="The ID of the user to delete"),
user_service: UserService = None  # This will be injected automatically
```
) -> Dict[str, Any]:```

"""Delete a user."""
success = await user_service.delete_user(user_id)
if not success:```

raise HTTPException(status_code=404, detail="User not found")
```
return {"success": True, "message": f"User {user_id} deleted"}
```

# Include the router in the application
app.include_router(router)
```

## Request Scoping

### Request Context

```python
from typing import Dict, Any, Optional
from fastapi import Request, Depends

from uno.dependencies.decorators import scoped, injectable_class
from uno.dependencies.fastapi_integration import DIAPIRouter

@scoped
class RequestContext:```

"""Request context for tracking request-specific data."""
``````

```
```

def __init__(self):```

"""Initialize the request context."""
self.user_id = None
self.request_id = None
self.metadata = {}
```
``````

```
```

def set_user_id(self, user_id: str) -> None:```

"""Set the user ID."""
self.user_id = user_id
```
``````

```
```

def set_request_id(self, request_id: str) -> None:```

"""Set the request ID."""
self.request_id = request_id
```
``````

```
```

def add_metadata(self, key: str, value: Any) -> None:```

"""Add metadata to the request context."""
self.metadata[key] = value
```
``````

```
```

def get_metadata(self, key: str, default: Any = None) -> Any:```

"""Get metadata from the request context."""
return self.metadata.get(key, default)
```
```

# Create a router with automatic dependency injection
router = DIAPIRouter(prefix="/api", tags=["api"])

@router.get("/me")
async def get_current_user(```

context: RequestContext,
user_service: UserService
```
) -> Dict[str, Any]:```

"""Get the current user."""
if not context.user_id:```

raise HTTPException(status_code=401, detail="Not authenticated")
```
``````

```
```

user = await user_service.get_user(context.user_id)
if not user:```

raise HTTPException(status_code=404, detail="User not found")
```
``````

```
```

return user
```
```

### Authentication Middleware

```python
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Dict, Any, Optional

from uno.dependencies.decorators import singleton, scoped, injectable_class
from uno.dependencies.fastapi_integration import DIAPIRouter, resolve_service

# Create a token service
@singleton
@injectable_class()
class TokenService:```

"""Token service for generating and validating JWT tokens."""
``````

```
```

def __init__(self, config: ConfigServiceProtocol, logger: LoggerServiceProtocol):```

"""Initialize the token service."""
self.config = config
self.logger = logger
self.secret_key = config.get_value("TOKEN_SECRET", "secret")
self.algorithm = config.get_value("TOKEN_ALGORITHM", "HS256")
```
``````

```
```

def create_token(self, user_id: str, data: Dict[str, Any] = None) -> str:```

"""Create a JWT token."""
payload = data or {}
payload["sub"] = user_id
return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
```
``````

```
```

def validate_token(self, token: str) -> Dict[str, Any]:```

"""Validate a JWT token."""
try:
    payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
    return payload
except jwt.PyJWTError as e:
    self.logger.error(f"Token validation error: {e}")
    raise ValueError("Invalid token")
```
```

# Create an authentication middleware
security = HTTPBearer()

async def get_current_user(```

credentials: HTTPAuthorizationCredentials = Depends(security),
token_service: TokenService = Depends(resolve_service(TokenService)),
context: RequestContext = Depends(resolve_service(RequestContext))
```
) -> Dict[str, Any]:```

"""Get the current user from the token."""
try:```

payload = token_service.validate_token(credentials.credentials)
user_id = payload.get("sub")
if not user_id:```

raise HTTPException(status_code=401, detail="Invalid token")
```
``````

```
```

# Set the user ID in the request context
context.set_user_id(user_id)
return payload
```
except ValueError:```

raise HTTPException(status_code=401, detail="Invalid token")
```
```

# Create a protected router
protected_router = DIAPIRouter(prefix="/api/protected", tags=["protected"])

@protected_router.get("/data")
async def get_protected_data(```

user: Dict[str, Any] = Depends(get_current_user),
user_service: UserService = None  # This will be injected automatically
```
) -> Dict[str, Any]:```

"""Get protected data."""
return {```

"user_id": user.get("sub"),
"message": "This is protected data",
"user_data": await user_service.get_user(user.get("sub"))
```
}
```

# Include the router in the application
app.include_router(protected_router)
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

from uno.dependencies.scoped_container import ServiceCollection, initialize_container, get_service

# Test a service with mocked dependencies
@pytest.fixture
def setup_test_container():```

"""Set up a test container with mocked dependencies."""
# Create a service collection for testing
services = ServiceCollection()
``````

```
```

# Create mock dependencies
mock_config = MagicMock(spec=ConfigServiceProtocol)
mock_config.get_value.return_value = "test_value"
mock_config.all.return_value = {"key": "test_value"}
``````

```
```

mock_logger = MagicMock(spec=LoggerServiceProtocol)
``````

```
```

mock_user_repository = MagicMock(spec=UserRepositoryProtocol)
mock_user_repository.get_user = AsyncMock(return_value={"id": "test_user", "name": "Test User"})
mock_user_repository.get_users = AsyncMock(return_value=[{"id": "test_user", "name": "Test User"}])
``````

```
```

# Register mocks
services.add_instance(ConfigServiceProtocol, mock_config)
services.add_instance(LoggerServiceProtocol, mock_logger)
services.add_instance(UserRepositoryProtocol, mock_user_repository)
``````

```
```

# Register the service under test
services.add_singleton(UserService)
``````

```
```

# Initialize the container
initialize_container(services)
``````

```
```

# Return mock dependencies for assertions
return {```

"config": mock_config,
"logger": mock_logger,
"user_repository": mock_user_repository
```
}
```

@pytest.mark.asyncio
async def test_user_service_get_user(setup_test_container):```

"""Test the user service get_user method."""
# Get mocked dependencies
mocks = setup_test_container
``````

```
```

# Get the service under test
user_service = get_service(UserService)
``````

```
```

# Call the method
result = await user_service.get_user("test_user")
``````

```
```

# Verify the method was called with the correct parameters
mocks["user_repository"].get_user.assert_called_once_with("test_user")
``````

```
```

# Verify the result
assert result == {"id": "test_user", "name": "Test User"}
```
```

### Integration Testing

```python
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from uno.dependencies.fastapi_integration import configure_fastapi
from uno.dependencies.modern_provider import get_service_provider
from uno.dependencies.scoped_container import ServiceCollection

# Create a test client
@pytest.fixture
def app():```

"""Create a FastAPI application for testing."""
app = FastAPI()
configure_fastapi(app)
return app
```

@pytest.fixture
def client(app):```

"""Create a test client."""
return TestClient(app)
```

@pytest.fixture
def setup_test_services():```

"""Set up test services."""
# Create a service collection for testing
services = ServiceCollection()
``````

```
```

# Register real services
services.add_singleton(ConfigServiceProtocol, ConfigService, config_path="test_config.json")
services.add_singleton(LoggerServiceProtocol, LoggerService, logger_name="test")
services.add_scoped(UserRepositoryProtocol, UserRepository)
services.add_singleton(UserService)
services.add_singleton(TokenService)
services.add_scoped(RequestContext)
``````

```
```

# Configure the service provider
provider = get_service_provider()
provider.configure_services(services)
``````

```
```

# Initialize services
import asyncio
asyncio.run(provider.initialize())
``````

```
```

# Return the provider for cleanup
return provider
```

@pytest.fixture
def auth_token(setup_test_services):```

"""Create an authentication token."""
token_service = get_service_provider().get_service(TokenService)
return token_service.create_token("test_user")
```

@pytest.mark.asyncio
async def test_get_user_endpoint(client, auth_token):```

"""Test the get_user endpoint."""
# Set up some test data
user_service = get_service_provider().get_service(UserService)
await user_service.create_user({"id": "test_user", "name": "Test User"})
``````

```
```

# Make a request
response = client.get(```

"/api/users/test_user",
headers={"Authorization": f"Bearer {auth_token}"}
```
)
``````

```
```

# Verify the response
assert response.status_code == 200
assert response.json() == {"id": "test_user", "name": "Test User"}
```
```

## Advanced Features

### Factory Services

```python
from typing import Dict, Any, Type, TypeVar

from uno.dependencies.decorators import singleton, scoped, transient, injectable_class
from uno.dependencies.modern_provider import ServiceLifecycle

T = TypeVar('T')

@singleton
@injectable_class()
class ServiceFactory:```

"""Factory for creating services."""
``````

```
```

def __init__(self, config: ConfigServiceProtocol, logger: LoggerServiceProtocol):```

"""Initialize the service factory."""
self.config = config
self.logger = logger
self._registry = {}
```
``````

```
```

def register(self, name: str, service_class: Type[T]) -> None:```

"""Register a service class."""
self._registry[name] = service_class
self.logger.info(f"Registered service {name}")
```
``````

```
```

def create(self, name: str, **params) -> T:```

"""Create a service instance."""
if name not in self._registry:
    self.logger.error(f"Service {name} not found")
    raise ValueError(f"Service {name} not found")
``````

```
```

service_class = self._registry[name]
self.logger.info(f"Creating service {name}")
return service_class(**params)
```
```
```

### Event-Driven Architecture

```python
from typing import Dict, Any, Callable, List, Optional
import asyncio

from uno.dependencies.decorators import singleton, injectable_class
from uno.dependencies.modern_provider import ServiceLifecycle

# Event types
class UserCreatedEvent:```

"""Event raised when a user is created."""
``````

```
```

def __init__(self, user_id: str, user_data: Dict[str, Any]):```

"""Initialize the event."""
self.user_id = user_id
self.user_data = user_data
```
```

class UserUpdatedEvent:```

"""Event raised when a user is updated."""
``````

```
```

def __init__(self, user_id: str, user_data: Dict[str, Any]):```

"""Initialize the event."""
self.user_id = user_id
self.user_data = user_data
```
```

class UserDeletedEvent:```

"""Event raised when a user is deleted."""
``````

```
```

def __init__(self, user_id: str):```

"""Initialize the event."""
self.user_id = user_id
```
```

# Event bus
@singleton
class EventBus(ServiceLifecycle):```

"""Event bus for publishing and subscribing to events."""
``````

```
```

def __init__(self):```

"""Initialize the event bus."""
self._handlers = {}
self._running = False
self._event_queue = asyncio.Queue()
```
``````

```
```

async def initialize(self) -> None:```

"""Initialize the event bus."""
self._running = True
asyncio.create_task(self._process_events())
```
``````

```
```

async def dispose(self) -> None:```

"""Dispose the event bus."""
self._running = False
# Wait for all events to be processed
await self._event_queue.join()
```
``````

```
```

def subscribe(self, event_type: type, handler: Callable) -> None:```

"""Subscribe to an event type."""
if event_type not in self._handlers:
    self._handlers[event_type] = []
self._handlers[event_type].append(handler)
```
``````

```
```

async def publish(self, event: Any) -> None:```

"""Publish an event."""
await self._event_queue.put(event)
```
``````

```
```

async def _process_events(self) -> None:```

"""Process events from the queue."""
while self._running:
    try:
        event = await self._event_queue.get()
        event_type = type(event)
        
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    print(f"Error handling event {event_type.__name__}: {e}")
        
        self._event_queue.task_done()
    except asyncio.CancelledError:
        break
    except Exception as e:
        print(f"Error processing events: {e}")
```
```

# Event-driven user service
@singleton
@injectable_class()
class EventDrivenUserService:```

"""User service that publishes events."""
``````

```
```

def __init__(```

self,
user_repository: UserRepositoryProtocol,
event_bus: EventBus,
logger: LoggerServiceProtocol
```
):```

"""Initialize the user service."""
self.user_repository = user_repository
self.event_bus = event_bus
self.logger = logger
```
``````

```
```

async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Create a new user and publish an event."""
user = await self.user_repository.create_user(user_data)
``````

```
```

# Publish an event
await self.event_bus.publish(UserCreatedEvent(user["id"], user))
``````

```
```

return user
```
``````

```
```

async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:```

"""Update a user and publish an event."""
user = await self.user_repository.update_user(user_id, user_data)
``````

```
```

# Publish an event if the user was updated
if user:
    await self.event_bus.publish(UserUpdatedEvent(user_id, user))
``````

```
```

return user
```
``````

```
```

async def delete_user(self, user_id: str) -> bool:```

"""Delete a user and publish an event."""
success = await self.user_repository.delete_user(user_id)
``````

```
```

# Publish an event if the user was deleted
if success:
    await self.event_bus.publish(UserDeletedEvent(user_id))
``````

```
```

return success
```
```

# Event handler
@singleton
@injectable_class()
class UserEventHandler:```

"""Handler for user events."""
``````

```
```

def __init__(self, logger: LoggerServiceProtocol, event_bus: EventBus):```

"""Initialize the event handler."""
self.logger = logger
self.event_bus = event_bus
``````

```
```

# Subscribe to events
event_bus.subscribe(UserCreatedEvent, self.handle_user_created)
event_bus.subscribe(UserUpdatedEvent, self.handle_user_updated)
event_bus.subscribe(UserDeletedEvent, self.handle_user_deleted)
```
``````

```
```

async def handle_user_created(self, event: UserCreatedEvent) -> None:```

"""Handle a user created event."""
self.logger.info(f"User {event.user_id} created")
# Do something with the event
```
``````

```
```

async def handle_user_updated(self, event: UserUpdatedEvent) -> None:```

"""Handle a user updated event."""
self.logger.info(f"User {event.user_id} updated")
# Do something with the event
```
``````

```
```

async def handle_user_deleted(self, event: UserDeletedEvent) -> None:```

"""Handle a user deleted event."""
self.logger.info(f"User {event.user_id} deleted")
# Do something with the event
```
```
```

These examples demonstrate how to use uno's dependency injection system in various scenarios, from basic service registration and resolution to advanced features like event-driven architecture and factory services.