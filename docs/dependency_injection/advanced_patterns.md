# Advanced Dependency Injection Patterns

This guide covers advanced patterns and techniques for using uno's dependency injection system. These patterns help solve complex scenarios, manage service lifecycle, implement cross-cutting concerns, and optimize performance.

## Scoping and Lifecycle Management

### Managing Service Lifecycle

Services that need initialization or cleanup should implement the `ServiceLifecycle` interface:

```python
from uno.dependencies.modern_provider import ServiceLifecycle

class DatabaseService(ServiceLifecycle):
    """Database service with lifecycle management."""
    
    def __init__(self, config_service):
        self.config_service = config_service
        self.connection_pool = None
        self.metrics = {"queries": 0, "errors": 0}
    
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        # Get configuration values
        host = self.config_service.get_value("DB_HOST", "localhost")
        port = self.config_service.get_value("DB_PORT", 5432)
        user = self.config_service.get_value("DB_USER", "postgres")
        password = self.config_service.get_value("DB_PASSWORD", "")
        database = self.config_service.get_value("DB_NAME", "postgres")
        
        # Create connection pool
        import asyncpg
        self.connection_pool = await asyncpg.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            min_size=5,
            max_size=20
        )
    
    async def dispose(self) -> None:
        """Close the database connection pool."""
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None
```

The service provider automatically calls `initialize()` during application startup and `dispose()` during shutdown:

```python
from fastapi import FastAPI
from uno.dependencies.modern_provider import initialize_services, shutdown_services

app = FastAPI()

@app.on_event("startup")
async def startup():
    await initialize_services()

@app.on_event("shutdown")
async def shutdown():
    await shutdown_services()
```

### Request-Scoped Services

Request-scoped services are created once per request and share state within that request:

```python
from uno.dependencies.decorators import scoped, injectable_class
from uno.dependencies.fastapi_integration import DIAPIRouter
from typing import Dict, Any, Optional

@scoped
class RequestContext:
    """Request-scoped context for sharing state within a request."""
    
    def __init__(self):
        self.user_id = None
        self.tenant_id = None
        self.start_time = time.time()
        self.metadata = {}
    
    def set_user_id(self, user_id: str) -> None:
        self.user_id = user_id
    
    def set_tenant_id(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
    
    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

@scoped
@injectable_class()
class RequestAuditService:
    """Service that audits request activities."""
    
    def __init__(self, context: RequestContext, logger_service):
        self.context = context
        self.logger = logger_service
        self.actions = []
    
    def record_action(self, action: str, resource: str, details: Optional[Dict[str, Any]] = None):
        """Record an action for the current request."""
        self.actions.append({
            "user_id": self.context.user_id,
            "tenant_id": self.context.tenant_id,
            "timestamp": time.time(),
            "action": action,
            "resource": resource,
            "details": details or {}
        })
        
        self.logger.info(
            f"User {self.context.user_id} performed {action} on {resource}"
        )
    
    async def save_audit_trail(self):
        """Save the audit trail for this request."""
        # Logic to persist audit trail to database
        pass

# Create a router with automatic dependency injection
router = DIAPIRouter()

@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    context: RequestContext,
    audit_service: RequestAuditService,
    item_service = None  # Will be injected automatically
):
    """Get an item by ID."""
    # Set context information
    context.set_user_id("user123")
    context.set_tenant_id("tenant456")
    
    # Record the action
    audit_service.record_action("get", f"item/{item_id}")
    
    # Get the item
    item = await item_service.get_item(item_id)
    
    # At the end of the request, the RequestContext and RequestAuditService
    # will be automatically disposed when the request scope ends
    return item
```

## Factory Patterns

### Factory Functions

Factory functions allow dynamic creation of services with complex initialization logic:

```python
from uno.dependencies.scoped_container import ServiceCollection
from uno.dependencies.modern_provider import get_service_provider
import logging

def configure_services():
    """Configure services with factory functions."""
    services = ServiceCollection()
    
    # Register a factory function for creating loggers
    def create_logger(name):
        logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    # Register with factory function
    services.add_singleton_factory(
        logging.Logger,
        lambda: create_logger("app")
    )
    
    # Register a service that depends on the logger
    services.add_singleton_factory(
        NotificationService,
        lambda resolver: NotificationService(
            logger=resolver.resolve(logging.Logger),
            sms_enabled=True,
            email_enabled=True
        )
    )
    
    # Configure the service provider
    provider = get_service_provider()
    provider.configure_services(services)
```

### Service Factory

A service factory pattern for creating specialized service instances:

```python
from typing import Dict, Type, TypeVar, Generic, Any
from uno.dependencies.decorators import singleton, injectable_class

T = TypeVar('T')

@singleton
@injectable_class()
class RepositoryFactory:
    """Factory for creating repository instances."""
    
    def __init__(self, db_manager, config_service):
        self.db_manager = db_manager
        self.config_service = config_service
        self._registry = {}
    
    def register(self, entity_type: str, repository_class: Type[T]) -> None:
        """Register a repository class for an entity type."""
        self._registry[entity_type] = repository_class
    
    def create(self, entity_type: str) -> T:
        """Create a repository for the specified entity type."""
        if entity_type not in self._registry:
            raise ValueError(f"No repository registered for entity type: {entity_type}")
        
        repository_class = self._registry[entity_type]
        
        # Create repository with dependencies
        return repository_class(
            db_manager=self.db_manager,
            schema=self.config_service.get_value("DB_SCHEMA", "public")
        )

# Usage
@injectable_class()
class UserService:
    def __init__(self, repository_factory: RepositoryFactory):
        self.repository = repository_factory.create("user")
```

## Complex Dependency Chains

### Managing Deep Dependency Hierarchies

For services with complex dependency hierarchies, use composition and layering:

```python
from typing import Protocol, Dict, List, Any
from uno.dependencies.decorators import singleton, scoped, injectable_class

# Define protocols for each layer
class ConfigProtocol(Protocol):
    def get_value(self, key: str, default: Any = None) -> Any: ...

class LoggerProtocol(Protocol):
    def info(self, message: str) -> None: ...
    def error(self, message: str, exc_info: bool = False) -> None: ...

class DatabaseProtocol(Protocol):
    async def query(self, sql: str, *params) -> List[Dict[str, Any]]: ...
    async def execute(self, sql: str, *params) -> None: ...

class CacheProtocol(Protocol):
    async def get(self, key: str) -> Any: ...
    async def set(self, key: str, value: Any, ttl: int = None) -> None: ...

class RepositoryProtocol(Protocol):
    async def get_by_id(self, id: str) -> Any: ...
    async def list_all(self) -> List[Any]: ...
    async def create(self, data: Any) -> Any: ...
    async def update(self, id: str, data: Any) -> Any: ...
    async def delete(self, id: str) -> bool: ...

# Implement each layer
@singleton
@injectable_class()
class Config:
    def __init__(self):
        self.settings = {
            "cache_ttl": 300,
            "db_schema": "public",
            "max_connections": 10
        }
    
    def get_value(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

@singleton
@injectable_class()
class Logger:
    def info(self, message: str) -> None:
        print(f"INFO: {message}")
    
    def error(self, message: str, exc_info: bool = False) -> None:
        print(f"ERROR: {message}")

@singleton
@injectable_class()
class Database:
    def __init__(self, config: ConfigProtocol, logger: LoggerProtocol):
        self.config = config
        self.logger = logger
        self.connected = False
    
    async def connect(self):
        self.logger.info("Connecting to database...")
        self.connected = True
    
    async def query(self, sql: str, *params) -> List[Dict[str, Any]]:
        if not self.connected:
            await self.connect()
        self.logger.info(f"Executing query: {sql}")
        # Simulate query execution
        return [{"id": "123", "name": "Test"}]
    
    async def execute(self, sql: str, *params) -> None:
        if not self.connected:
            await self.connect()
        self.logger.info(f"Executing statement: {sql}")

@singleton
@injectable_class()
class Cache:
    def __init__(self, config: ConfigProtocol, logger: LoggerProtocol):
        self.config = config
        self.logger = logger
        self.ttl = config.get_value("cache_ttl", 300)
        self.data = {}
    
    async def get(self, key: str) -> Any:
        self.logger.info(f"Getting from cache: {key}")
        return self.data.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        self.logger.info(f"Setting in cache: {key}")
        self.data[key] = value

@scoped
@injectable_class()
class UserRepository:
    def __init__(
        self, 
        database: DatabaseProtocol, 
        cache: CacheProtocol, 
        logger: LoggerProtocol,
        config: ConfigProtocol
    ):
        self.database = database
        self.cache = cache
        self.logger = logger
        self.schema = config.get_value("db_schema", "public")
    
    async def get_by_id(self, id: str) -> Any:
        # Try cache first
        cache_key = f"user:{id}"
        cached_user = await self.cache.get(cache_key)
        if cached_user:
            return cached_user
        
        # Query database
        users = await self.database.query(
            f"SELECT * FROM {self.schema}.users WHERE id = $1",
            id
        )
        user = users[0] if users else None
        
        # Cache result
        if user:
            await self.cache.set(cache_key, user)
        
        return user
    
    async def list_all(self) -> List[Any]:
        return await self.database.query(f"SELECT * FROM {self.schema}.users")
    
    async def create(self, data: Any) -> Any:
        # Implementation omitted for brevity
        pass
    
    async def update(self, id: str, data: Any) -> Any:
        # Implementation omitted for brevity
        pass
    
    async def delete(self, id: str) -> bool:
        # Implementation omitted for brevity
        pass

@scoped
@injectable_class()
class UserService:
    def __init__(self, repository: UserRepository, logger: LoggerProtocol):
        self.repository = repository
        self.logger = logger
    
    async def get_user(self, id: str) -> Any:
        self.logger.info(f"Getting user with ID: {id}")
        return await self.repository.get_by_id(id)
    
    async def list_users(self) -> List[Any]:
        self.logger.info("Listing all users")
        return await self.repository.list_all()
```

## Conditional Registration

### Environment-Based Configuration

Register different implementations based on environment:

```python
from uno.dependencies.scoped_container import ServiceCollection
from uno.dependencies.modern_provider import get_service_provider
import os

def configure_services():
    """Configure services based on environment."""
    services = ServiceCollection()
    
    # Register common services
    services.add_singleton(LoggerService)
    
    # Get environment
    env = os.environ.get("APP_ENV", "development")
    
    if env == "development":
        # Development services
        services.add_singleton(ConfigProtocol, DevConfig)
        services.add_singleton(DatabaseProtocol, DevDatabase)
        services.add_singleton(EmailProtocol, DevEmailService)  # Sends to console
    elif env == "testing":
        # Testing services
        services.add_singleton(ConfigProtocol, TestConfig)
        services.add_singleton(DatabaseProtocol, InMemoryDatabase)
        services.add_singleton(EmailProtocol, MockEmailService)  # No-op
    else:
        # Production services
        services.add_singleton(ConfigProtocol, ProdConfig)
        services.add_singleton(DatabaseProtocol, ProdDatabase)
        services.add_singleton(EmailProtocol, SmtpEmailService)  # Real SMTP
    
    # Configure service provider
    provider = get_service_provider()
    provider.configure_services(services)
```

### Feature Flags

Implement conditional services based on feature flags:

```python
from uno.dependencies.scoped_container import ServiceCollection
from uno.dependencies.modern_provider import get_service_provider

def configure_services(config):
    """Configure services based on feature flags."""
    services = ServiceCollection()
    
    # Register base services
    services.add_singleton(LoggerService)
    services.add_singleton(ConfigService)
    services.add_singleton(DatabaseService)
    
    # Add services based on feature flags
    if config.get_feature("use_redis_cache"):
        services.add_singleton(CacheProtocol, RedisCache)
    else:
        services.add_singleton(CacheProtocol, InMemoryCache)
    
    if config.get_feature("vector_search"):
        services.add_singleton(SearchProtocol, VectorSearch)
    else:
        services.add_singleton(SearchProtocol, SimpleSearch)
    
    if config.get_feature("audit_trail"):
        services.add_scoped(AuditService)
        # Register an event handler for audit events
        services.add_singleton_factory(
            AuditEventHandler,
            lambda resolver: AuditEventHandler(
                resolver.resolve(EventBusProtocol),
                resolver.resolve(AuditService)
            )
        )
    
    # Configure service provider
    provider = get_service_provider()
    provider.configure_services(services)
```

## Event-Driven Architecture

### Event Bus with Dependency Injection

Implement an event-driven architecture with DI:

```python
from typing import Dict, List, Any, Callable, TypeVar, Type
from uno.dependencies.decorators import singleton, injectable_class
import asyncio

# Define event types
class Event:
    """Base class for all events."""
    pass

class UserCreatedEvent(Event):
    def __init__(self, user_id: str, data: Dict[str, Any]):
        self.user_id = user_id
        self.data = data

class UserUpdatedEvent(Event):
    def __init__(self, user_id: str, data: Dict[str, Any]):
        self.user_id = user_id
        self.data = data

class UserDeletedEvent(Event):
    def __init__(self, user_id: str):
        self.user_id = user_id

# Event handler type
T = TypeVar('T', bound=Event)
EventHandler = Callable[[T], None]

@singleton
@injectable_class()
class EventBus:
    """Event bus for publishing and subscribing to events."""
    
    def __init__(self, logger_service):
        self.logger = logger_service
        self._handlers: Dict[Type[Event], List[EventHandler]] = {}
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None
    
    def subscribe(self, event_type: Type[T], handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self.logger.info(f"Handler subscribed to {event_type.__name__}")
    
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        self.logger.info(f"Event published: {type(event).__name__}")
        await self._queue.put(event)
    
    async def start(self) -> None:
        """Start processing events."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_events())
        self.logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop processing events."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            await self._task
            self._task = None
        self.logger.info("Event bus stopped")
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await self._queue.get()
                event_type = type(event)
                
                if event_type in self._handlers:
                    handlers = self._handlers[event_type]
                    self.logger.info(f"Processing {event_type.__name__} with {len(handlers)} handlers")
                    
                    for handler in handlers:
                        try:
                            await handler(event)
                        except Exception as e:
                            self.logger.error(f"Error in event handler: {str(e)}")
                
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing events: {str(e)}")

# Event handlers with dependency injection
@singleton
@injectable_class()
class UserEventHandler:
    """Handler for user events."""
    
    def __init__(self, logger_service, event_bus: EventBus):
        self.logger = logger_service
        self.event_bus = event_bus
        
        # Subscribe to events
        event_bus.subscribe(UserCreatedEvent, self.handle_user_created)
        event_bus.subscribe(UserUpdatedEvent, self.handle_user_updated)
        event_bus.subscribe(UserDeletedEvent, self.handle_user_deleted)
    
    async def handle_user_created(self, event: UserCreatedEvent) -> None:
        """Handle user created event."""
        self.logger.info(f"User created: {event.user_id}")
        # Implementation omitted for brevity
    
    async def handle_user_updated(self, event: UserUpdatedEvent) -> None:
        """Handle user updated event."""
        self.logger.info(f"User updated: {event.user_id}")
        # Implementation omitted for brevity
    
    async def handle_user_deleted(self, event: UserDeletedEvent) -> None:
        """Handle user deleted event."""
        self.logger.info(f"User deleted: {event.user_id}")
        # Implementation omitted for brevity

# Event-driven service with dependency injection
@scoped
@injectable_class()
class EventDrivenUserService:
    """User service that publishes events."""
    
    def __init__(self, repository, event_bus: EventBus, logger_service):
        self.repository = repository
        self.event_bus = event_bus
        self.logger = logger_service
    
    async def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user and publish an event."""
        # Create the user
        user = await self.repository.create(data)
        
        # Publish the event
        await self.event_bus.publish(UserCreatedEvent(user["id"], user))
        
        return user
    
    async def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user and publish an event."""
        # Update the user
        user = await self.repository.update(user_id, data)
        
        # Publish the event
        if user:
            await self.event_bus.publish(UserUpdatedEvent(user_id, user))
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and publish an event."""
        # Delete the user
        result = await self.repository.delete(user_id)
        
        # Publish the event
        if result:
            await self.event_bus.publish(UserDeletedEvent(user_id))
        
        return result
```

## Testing Strategies

### Unit Testing with Mock Services

Test services in isolation with mock dependencies:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from uno.dependencies.scoped_container import ServiceCollection, initialize_container

# Test a service with mock dependencies
def test_user_service():
    """Test UserService with mock dependencies."""
    # Create a service collection for testing
    services = ServiceCollection()
    
    # Create mock repository
    mock_repository = MagicMock()
    mock_repository.get_by_id = AsyncMock(return_value={"id": "123", "name": "Test User"})
    mock_repository.list_all = AsyncMock(return_value=[{"id": "123", "name": "Test User"}])
    
    # Create mock logger
    mock_logger = MagicMock()
    
    # Register mocks
    services.add_instance(UserRepository, mock_repository)
    services.add_instance(LoggerProtocol, mock_logger)
    
    # Register the service under test
    services.add_singleton(UserService)
    
    # Initialize the container
    initialize_container(services)
    
    # Get the service
    from uno.dependencies.scoped_container import get_service
    user_service = get_service(UserService)
    
    # Test the service
    result = asyncio.run(user_service.get_user("123"))
    
    # Verify the result
    assert result == {"id": "123", "name": "Test User"}
    
    # Verify the mock was called
    mock_repository.get_by_id.assert_called_once_with("123")
    mock_logger.info.assert_called_once_with("Getting user with ID: 123")
```

### Integration Testing with Test Container

Test multiple services working together:

```python
import pytest
from uno.dependencies.testing import configure_test_container, TestingContainer

@pytest.fixture
def test_container():
    """Create a test container with real services."""
    container = TestingContainer()
    
    # Register real services with test configuration
    container.register_singleton(ConfigProtocol, TestConfig())
    container.register_singleton(LoggerProtocol, Logger())
    container.register_singleton(DatabaseProtocol, InMemoryDatabase())
    container.register_singleton(CacheProtocol, InMemoryCache())
    container.register_scoped(UserRepository)
    container.register_scoped(UserService)
    
    # Configure the test container
    configure_test_container(container)
    
    return container

@pytest.mark.asyncio
async def test_user_creation_flow(test_container):
    """Test the entire user creation flow."""
    # Get the services
    from uno.dependencies.scoped_container import get_service
    user_service = get_service(UserService)
    
    # Create a user
    user_data = {"name": "Test User", "email": "test@example.com"}
    user = await user_service.create_user(user_data)
    
    # Verify the user was created
    assert user["id"] is not None
    assert user["name"] == "Test User"
    
    # Get the user
    retrieved_user = await user_service.get_user(user["id"])
    
    # Verify the user was retrieved
    assert retrieved_user == user
```

## Performance Optimization

### Lazy Initialization

Implement lazy initialization for expensive resources:

```python
from uno.dependencies.decorators import singleton, injectable_class
import asyncio
import time

@singleton
@injectable_class()
class LazyDatabaseConnection:
    """Database connection that initializes lazily."""
    
    def __init__(self, config_service, logger_service):
        self.config = config_service
        self.logger = logger_service
        self._connection = None
        self._lock = asyncio.Lock()
    
    async def get_connection(self):
        """Get the database connection, initializing if necessary."""
        if self._connection is None:
            async with self._lock:
                if self._connection is None:
                    self.logger.info("Initializing database connection...")
                    
                    # Simulate connection initialization
                    await asyncio.sleep(0.1)
                    
                    self._connection = {
                        "host": self.config.get_value("DB_HOST"),
                        "port": self.config.get_value("DB_PORT"),
                        "connected_at": time.time()
                    }
                    
                    self.logger.info("Database connection initialized")
        
        return self._connection
    
    async def execute(self, query, *params):
        """Execute a query on the database."""
        conn = await self.get_connection()
        
        # Simulate query execution
        self.logger.info(f"Executing query: {query}")
        await asyncio.sleep(0.01)
        
        return {"result": "success", "rows": 1}
```

### Connection Pooling

Implement connection pooling with DI:

```python
from uno.dependencies.decorators import singleton, scoped, injectable_class
import asyncio
import random
import time
from typing import Dict, List, Any, Optional

@singleton
@injectable_class()
class ConnectionPool:
    """Pool of database connections."""
    
    def __init__(self, config_service, logger_service):
        self.config = config_service
        self.logger = logger_service
        self.min_size = self.config.get_value("DB_MIN_POOL_SIZE", 5)
        self.max_size = self.config.get_value("DB_MAX_POOL_SIZE", 20)
        self.connections = []
        self.in_use = set()
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            self.logger.info(f"Initializing connection pool with {self.min_size} connections")
            
            # Create initial connections
            for _ in range(self.min_size):
                connection = await self._create_connection()
                self.connections.append(connection)
            
            self._initialized = True
    
    async def get_connection(self):
        """Get a connection from the pool."""
        await self.initialize()
        
        async with self._lock:
            # Try to find an available connection
            for conn in self.connections:
                if conn not in self.in_use:
                    self.in_use.add(conn)
                    return conn
            
            # If no connection is available, create a new one if we're under max_size
            if len(self.connections) < self.max_size:
                self.logger.info("Creating additional connection")
                connection = await self._create_connection()
                self.connections.append(connection)
                self.in_use.add(connection)
                return connection
            
            # Wait for a connection to become available
            self.logger.info("Connection pool exhausted, waiting for connection")
            while all(conn in self.in_use for conn in self.connections):
                await asyncio.sleep(0.01)
            
            # Find the first available connection
            for conn in self.connections:
                if conn not in self.in_use:
                    self.in_use.add(conn)
                    return conn
    
    async def release_connection(self, connection):
        """Release a connection back to the pool."""
        async with self._lock:
            if connection in self.in_use:
                self.in_use.remove(connection)
    
    async def _create_connection(self):
        """Create a new database connection."""
        # Simulate connection creation
        await asyncio.sleep(0.05)
        
        connection = {
            "id": random.randint(1000, 9999),
            "host": self.config.get_value("DB_HOST"),
            "port": self.config.get_value("DB_PORT"),
            "created_at": time.time()
        }
        
        self.logger.info(f"Created new connection {connection['id']}")
        return connection

@scoped
@injectable_class()
class DatabaseSession:
    """Database session with connection management."""
    
    def __init__(self, pool: ConnectionPool, logger_service):
        self.pool = pool
        self.logger = logger_service
        self.connection = None
    
    async def __aenter__(self):
        """Enter the context manager."""
        self.connection = await self.pool.get_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if self.connection:
            await self.pool.release_connection(self.connection)
            self.connection = None
    
    async def execute(self, query: str, *params) -> Dict[str, Any]:
        """Execute a query."""
        if not self.connection:
            raise RuntimeError("No active connection. Use 'async with' to acquire a connection.")
        
        self.logger.info(f"Executing query on connection {self.connection['id']}")
        
        # Simulate query execution
        await asyncio.sleep(0.01)
        
        return {"result": "success", "rows": 1}
    
    async def query(self, query: str, *params) -> List[Dict[str, Any]]:
        """Execute a query that returns rows."""
        if not self.connection:
            raise RuntimeError("No active connection. Use 'async with' to acquire a connection.")
        
        self.logger.info(f"Querying on connection {self.connection['id']}")
        
        # Simulate query execution
        await asyncio.sleep(0.01)
        
        return [{"id": "123", "name": "Test"}]

# Usage with dependency injection
@scoped
@injectable_class()
class UserRepository:
    def __init__(self, session_factory: DatabaseSession, logger_service):
        self.session_factory = session_factory
        self.logger = logger_service
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user from the database."""
        self.logger.info(f"Getting user {user_id}")
        
        async with self.session_factory as session:
            results = await session.query(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            return results[0] if results else None
    
    async def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user in the database."""
        self.logger.info(f"Creating user {data.get('name')}")
        
        async with self.session_factory as session:
            await session.execute(
                "INSERT INTO users (id, name, email) VALUES ($1, $2, $3)",
                data.get("id", "123"),
                data.get("name"),
                data.get("email")
            )
            
            return {"id": data.get("id", "123"), **data}
```

## Dynamic Service Resolution

### Service Locator Pattern

While dependency injection is preferred, a service locator can be useful in specific scenarios:

```python
from typing import Dict, Type, TypeVar, Any
from uno.dependencies.modern_provider import get_service_provider

T = TypeVar('T')

class ServiceLocator:
    """Service locator for resolving services by name or type."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceLocator, cls).__new__(cls)
            cls._instance._services = {}
            cls._instance._initialized = False
        return cls._instance
    
    def register(self, name: str, service_type: Type[T]) -> None:
        """Register a service type by name."""
        self._services[name] = service_type
    
    def get_service_by_name(self, name: str) -> Any:
        """Get a service by name."""
        if name not in self._services:
            raise ValueError(f"Service not registered: {name}")
        
        service_type = self._services[name]
        return get_service_provider().get_service(service_type)
    
    def get_service_by_type(self, service_type: Type[T]) -> T:
        """Get a service by type."""
        return get_service_provider().get_service(service_type)

# Usage example
def setup_service_locator():
    """Set up the service locator."""
    locator = ServiceLocator()
    
    # Register services
    locator.register("config", ConfigService)
    locator.register("logger", LoggerService)
    locator.register("database", DatabaseService)
    locator.register("cache", CacheService)
    locator.register("repository", UserRepository)
    locator.register("service", UserService)
    
    return locator

# Dynamic service resolution
def get_dynamic_service(service_name: str) -> Any:
    """Get a service dynamically."""
    locator = ServiceLocator()
    return locator.get_service_by_name(service_name)
```

> **Note**: The service locator pattern should be used judiciously as it can make dependencies less explicit and harder to trace.

### Plugins with Dynamic Registration

Implement a plugin system with dynamic service registration:

```python
from typing import Dict, Type, List, Any
from uno.dependencies.decorators import singleton, injectable_class
from uno.dependencies.modern_provider import get_service_provider

@singleton
@injectable_class()
class PluginManager:
    """Manager for dynamically loaded plugins."""
    
    def __init__(self, logger_service):
        self.logger = logger_service
        self.plugins = {}
    
    def register_plugin(self, name: str, plugin_class: Type, **params) -> None:
        """Register a plugin."""
        if name in self.plugins:
            self.logger.warning(f"Plugin {name} already registered, overwriting")
        
        self.plugins[name] = {
            "class": plugin_class,
            "params": params,
            "instance": None
        }
        
        self.logger.info(f"Registered plugin: {name}")
    
    def get_plugin(self, name: str) -> Any:
        """Get a plugin instance."""
        if name not in self.plugins:
            raise ValueError(f"Plugin not registered: {name}")
        
        plugin_info = self.plugins[name]
        
        # Create the instance if not already created
        if plugin_info["instance"] is None:
            # Resolve dependencies from the service provider
            provider = get_service_provider()
            
            # Get constructor parameters
            import inspect
            signature = inspect.signature(plugin_info["class"].__init__)
            params = {}
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                # If parameter is provided in registration, use it
                if param_name in plugin_info["params"]:
                    params[param_name] = plugin_info["params"][param_name]
                else:
                    # Otherwise, try to resolve from service provider
                    param_type = param.annotation
                    if param_type is not inspect.Parameter.empty:
                        try:
                            params[param_name] = provider.get_service(param_type)
                        except Exception as e:
                            self.logger.error(f"Failed to resolve dependency {param_name}: {str(e)}")
                            
                            # Use default if available
                            if param.default is not inspect.Parameter.empty:
                                params[param_name] = param.default
            
            # Create the instance
            plugin_info["instance"] = plugin_info["class"](**params)
            self.logger.info(f"Created plugin instance: {name}")
        
        return plugin_info["instance"]
    
    def get_plugins_by_base(self, base_class: Type) -> List[Any]:
        """Get all plugin instances that are subclasses of the base class."""
        instances = []
        
        for name, plugin_info in self.plugins.items():
            if issubclass(plugin_info["class"], base_class):
                instances.append(self.get_plugin(name))
        
        return instances

# Plugin base class
class Plugin:
    """Base class for all plugins."""
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass
    
    def name(self) -> str:
        """Get the plugin name."""
        return self.__class__.__name__

# Example plugin implementations
class EmailPlugin(Plugin):
    def __init__(self, logger_service, config_service):
        self.logger = logger_service
        self.config = config_service
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        self.logger.info(f"Sending email to {to}: {subject}")
        return True

class SmsPlugin(Plugin):
    def __init__(self, logger_service, config_service):
        self.logger = logger_service
        self.config = config_service
    
    def send_sms(self, to: str, message: str) -> bool:
        self.logger.info(f"Sending SMS to {to}: {message}")
        return True

# Setup plugins
def register_plugins(plugin_manager: PluginManager):
    """Register all plugins."""
    plugin_manager.register_plugin("email", EmailPlugin)
    plugin_manager.register_plugin("sms", SmsPlugin)

# Usage with dependency injection
@injectable_class()
class NotificationService:
    def __init__(self, plugin_manager: PluginManager, logger_service):
        self.plugin_manager = plugin_manager
        self.logger = logger_service
    
    def send_notification(self, to: str, subject: str, message: str, methods: List[str]) -> Dict[str, bool]:
        """Send a notification using multiple methods."""
        results = {}
        
        if "email" in methods:
            email_plugin = self.plugin_manager.get_plugin("email")
            results["email"] = email_plugin.send_email(to, subject, message)
        
        if "sms" in methods:
            sms_plugin = self.plugin_manager.get_plugin("sms")
            results["sms"] = sms_plugin.send_sms(to, message)
        
        return results
```

## Conclusion

These advanced patterns demonstrate how to effectively use uno's dependency injection system to solve complex problems, manage service lifecycle, optimize performance, and create flexible, maintainable applications. By using these patterns, you can create applications that are modular, testable, and scalable.

Remember to always consider the trade-offs when choosing a pattern, and to follow the principle of using the simplest solution that meets your requirements. The uno framework's dependency injection system is designed to be flexible enough to support a wide range of application architectures, from simple services to complex event-driven systems.