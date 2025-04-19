# Database Connections

This guide explains how to manage database connections in the Uno framework.

## Overview

The Uno framework provides a robust database connection management system that handles:

- Connection pooling
- Connection lifecycle
- Async and sync connections
- Transaction management
- Connection monitoring
- Error handling

The primary components for connection management are:

1. **Database Engine**: Creates and configures database engines
2. **Connection Providers**: Manage connection acquisition and release
3. **Session Management**: Provides database sessions for operations
4. **Transaction Management**: Coordinates transactions across operations

## Engine Configuration

### Creating Database Engines

```python
from uno.infrastructure.database.engine import (
    create_async_engine,
    create_sync_engine,
    AsyncEngine,
    SyncEngine
)

# Create an async engine
async_engine = create_async_engine(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False
)

# Create a sync engine
sync_engine = create_sync_engine(
    connection_string="postgresql+psycopg2://user:password@localhost:5432/dbname",
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False
)
```

Key engine configuration options:

- `pool_size`: Base number of connections to keep open
- `max_overflow`: Maximum number of connections above pool_size
- `pool_timeout`: How long to wait for a connection from the pool
- `pool_recycle`: Recycle connections after this many seconds
- `echo`: Log SQL statements (useful for debugging)

### Enhanced Async Engine

For applications requiring advanced pooling, use `PooledAsyncEngine`:

```python
from uno.infrastructure.database.engine import PooledAsyncEngine

# Create a pooled async engine with metrics
pooled_engine = PooledAsyncEngine(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    metrics_enabled=True,
    pool_name="main"
)

# Get pool stats
stats = await pooled_engine.get_pool_stats()
print(f"Pool size: {stats.size}, Used: {stats.used}, Idle: {stats.idle}")
```

The `PooledAsyncEngine` provides:
- Enhanced connection pooling metrics
- Customizable connection retry logic
- Soft and hard limits on connection count
- Integration with health checks
- Connection initialization hooks

## Session Management

### Using Sessions

```python
from uno.infrastructure.database.session import get_session, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Using a synchronous session
with get_session() as session:
    result = session.execute("SELECT 1")
    # Work with session...

# Using an async session
async with get_async_session() as session:
    result = await session.execute("SELECT 1")
    # Work with session...
```

### Session Factory

For custom session requirements:

```python
from uno.infrastructure.database.session import (
    create_session_factory,
    create_async_session_factory
)

# Create session factories
sync_session_factory = create_session_factory(sync_engine)
async_session_factory = create_async_session_factory(async_engine)

# Use session factory
session = sync_session_factory()
with session:
    # Use session...

# Use async session factory
async_session = async_session_factory()
async with async_session:
    # Use session...
```

### Custom Session Configuration

```python
from uno.infrastructure.database.session import (
    create_async_session_factory,
    AsyncSessionConfig
)

# Create custom session configuration
session_config = AsyncSessionConfig(
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Create custom session factory
custom_factory = create_async_session_factory(
    async_engine,
    config=session_config
)

# Use custom session
async with custom_factory() as session:
    # Use session...
```

## Using UnoDB

`UnoDB` is the main database interface that provides session management:

```python
from uno.infrastructure.database import UnoDB

# Create database interface
db = UnoDB(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    pool_size=10,
    max_overflow=20
)

# Use with async context manager
async with db.session() as session:
    result = await session.execute("SELECT * FROM users WHERE id = :id", {"id": 1})
    user = result.fetchone()
```

UnoDB features:
- Simplified session management
- Automatic engine configuration
- Transaction handling
- Connection pooling
- Error handling

## Dependency Injection Integration

```python
from uno.core.di import configure_container, get_dependency
from uno.infrastructure.database import UnoDB
from uno.infrastructure.database.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

# Configure the DI container
configure_container()

# Register database components
container.register(UnoDB, UnoDB(connection_string="postgresql+asyncpg://..."))

# Get a session from the container
async def use_session():
    session = await get_dependency(AsyncSession)
    # Use session...
    
# Or use the session provider
async def use_session_provider():
    async with get_async_session() as session:
        # Use session...
```

## Connection Pooling

### Connection Pool Management

```python
from uno.infrastructure.database.engine import PooledAsyncEngine, PoolStats

# Create pooled engine
engine = PooledAsyncEngine(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

# Get pool statistics
stats: PoolStats = await engine.get_pool_stats()
print(f"Size: {stats.size}")
print(f"Used: {stats.used}")
print(f"Idle: {stats.idle}")
print(f"Soft limit: {stats.soft_limit}")
print(f"Hard limit: {stats.hard_limit}")

# Clear idle connections
await engine.clear_idle_connections()

# Warm up the pool
await engine.warmup_pool(connections=5)
```

### Connection Pool Monitoring

```python
from uno.infrastructure.database.connection_health import (
    ConnectionHealthMonitor,
    HealthStatus
)

# Create a monitor
monitor = ConnectionHealthMonitor(engine)

# Check pool health
health: HealthStatus = await monitor.check_health()
print(f"Status: {health.status}")  # OK, WARNING, or CRITICAL
print(f"Details: {health.details}")
print(f"Pool utilization: {health.metrics['pool_utilization']}")

# Register with health checks
health_checks.register("database_connection", monitor.check_health)
```

## Connection Lifecycle Hooks

```python
from uno.infrastructure.database.engine import (
    ConnectionHook,
    PooledAsyncEngine
)

class CustomConnectionHook(ConnectionHook):
    """Custom connection hook for initialization."""
    
    async def on_connect(self, connection):
        """Run when a connection is created."""
        # Set session variables
        await connection.execute("SET application_name = 'MyApp'")
        await connection.execute("SET search_path = public, analytics")
        
    async def on_checkout(self, connection):
        """Run when a connection is checked out from the pool."""
        # Reset transaction isolation level
        await connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
    
    async def on_checkin(self, connection):
        """Run when a connection is returned to the pool."""
        # Clear transaction state
        await connection.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED")

# Create engine with hook
engine = PooledAsyncEngine(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    connection_hooks=[CustomConnectionHook()]
)
```

## Using Multiple Databases

### Configure Multiple Database Engines

```python
from uno.infrastructure.database.manager import DatabaseManager
from uno.infrastructure.database.engine import create_async_engine

# Create database manager
db_manager = DatabaseManager()

# Register multiple databases
db_manager.register_engine(
    "default",
    create_async_engine("postgresql+asyncpg://user:pass@localhost:5432/main_db")
)

db_manager.register_engine(
    "analytics",
    create_async_engine("postgresql+asyncpg://user:pass@localhost:5432/analytics_db")
)

db_manager.register_engine(
    "reporting",
    create_async_engine("postgresql+asyncpg://user:pass@localhost:5432/reporting_db")
)

# Use specific database
async with db_manager.get_session("analytics") as session:
    # Use analytics database
    result = await session.execute("SELECT * FROM metrics")
```

### Database Routing

```python
from uno.infrastructure.database.manager import DatabaseRouter

class CustomDatabaseRouter(DatabaseRouter):
    """Custom database router for entity operations."""
    
    def get_database_for_read(self, entity_type: Type) -> str:
        """Get database for read operations."""
        if entity_type.__module__.startswith("myapp.analytics"):
            return "analytics"
        elif entity_type.__module__.startswith("myapp.reporting"):
            return "reporting"
        return "default"
    
    def get_database_for_write(self, entity_type: Type) -> str:
        """Get database for write operations."""
        if entity_type.__module__.startswith("myapp.analytics"):
            return "analytics"
        elif entity_type.__module__.startswith("myapp.reporting"):
            return "reporting"
        return "default"

# Register router with manager
db_manager.set_router(CustomDatabaseRouter())

# Use with repository
user_repo = UserRepository(db_manager.get_session_for_entity(User))
```

## Connection Error Handling

### Retry Logic

```python
from uno.infrastructure.database.engine import (
    RetryConfig,
    RetryableError,
    PooledAsyncEngine
)

# Define retry configuration
retry_config = RetryConfig(
    max_retries=3,
    retry_delay=0.1,
    backoff_factor=2.0,
    retryable_errors=[
        "OperationalError",
        "ConnectionError",
        "InterfaceError"
    ]
)

# Create engine with retry
engine = PooledAsyncEngine(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    retry_config=retry_config
)

# The engine will automatically retry operations
async with engine.connect() as conn:
    try:
        # This will retry up to 3 times if it fails with a retryable error
        await conn.execute("SELECT 1")
    except RetryableError as e:
        print(f"Operation failed after retries: {e}")
```

### Circuit Breaker

```python
from uno.infrastructure.database.engine import (
    CircuitBreakerConfig,
    PooledAsyncEngine
)

# Define circuit breaker configuration
cb_config = CircuitBreakerConfig(
    failure_threshold=5,
    reset_timeout=30.0,
    trip_timeout=60.0
)

# Create engine with circuit breaker
engine = PooledAsyncEngine(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    circuit_breaker_config=cb_config
)
```

## Connection Events

```python
from uno.infrastructure.database.engine import EngineEventHandler, PooledAsyncEngine

class ConnectionEventLogger(EngineEventHandler):
    """Log database connection events."""
    
    async def on_pool_created(self, engine):
        """Called when the connection pool is created."""
        print(f"Pool created: {engine}")
    
    async def on_pool_recycled(self, engine):
        """Called when the connection pool is recycled."""
        print(f"Pool recycled: {engine}")
    
    async def on_pool_disposed(self, engine):
        """Called when the connection pool is disposed."""
        print(f"Pool disposed: {engine}")
    
    async def on_checkout(self, engine, connection):
        """Called when a connection is checked out."""
        print(f"Connection checked out: {connection}")
    
    async def on_checkin(self, engine, connection):
        """Called when a connection is checked in."""
        print(f"Connection checked in: {connection}")
    
    async def on_connection_error(self, engine, error):
        """Called when a connection error occurs."""
        print(f"Connection error: {error}")

# Register event handler
engine = PooledAsyncEngine(
    connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname",
    event_handlers=[ConnectionEventLogger()]
)
```

## Connection Health Integration

```python
from uno.infrastructure.database.connection_health_integration import (
    setup_connection_health_checks
)
from uno.core.health.framework import HealthCheckRegistry

# Setup health checks
health_registry = HealthCheckRegistry()
setup_connection_health_checks(health_registry, engines=[engine])

# Now the health checks will include database connection status
health_status = await health_registry.check_all()
```

## Best Practices

### Connection Management

1. **Use UnoDB**: Let UnoDB handle connection management when possible
2. **Async by Default**: Prefer async connections for better scalability
3. **Connection Pooling**: Configure appropriate pool sizes based on workload
4. **Session Management**: Use the session as a context manager
5. **Connection Lifecycle**: Implement connection hooks for initialization
6. **Health Monitoring**: Set up health checks for database connections
7. **Error Handling**: Implement retry logic for transient failures
8. **Transaction Scope**: Keep transaction scope as narrow as possible
9. **Connection Events**: Monitor connection events for debugging
10. **Pool Sizing**: Start with small pools and scale based on metrics

### Pool Sizing Guidelines

| Workload Type | Recommended Pool Size | max_overflow | pool_recycle |
|---------------|----------------------|--------------|--------------|
| Light         | 5                    | 10           | 3600         |
| Medium        | 10                   | 20           | 1800         |
| Heavy         | 20                   | 30           | 900          |
| Batch Jobs    | 30+                  | 50           | 600          |

Adjust these values based on:
- Number of concurrent users
- Query complexity and duration
- Server resources
- Database server capacity

### Connection String Configuration

```python
# Configuration pattern for connection strings
from pydantic_settings import BaseSettings
from uno.core.di import ConfigProtocol
from functools import lru_cache
from typing import Dict, Any

class DatabaseSettings(BaseSettings, ConfigProtocol):
    """Database connection settings."""
    
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str
    db_pool_size: int = 10
    db_pool_overflow: int = 20
    db_pool_recycle: int = 3600
    
    @property
    def connection_string(self) -> str:
        """Get the database connection string."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self, key, default)
    
    def all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.dict()

@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get database settings (cached)."""
    return DatabaseSettings()

# Use settings to create a database
db = UnoDB(
    connection_string=get_db_settings().connection_string,
    pool_size=get_db_settings().db_pool_size,
    max_overflow=get_db_settings().db_pool_overflow,
    pool_recycle=get_db_settings().db_pool_recycle
)
```

## Examples

### Basic Database Operations

```python
from uno.infrastructure.database import UnoDB

# Create database
db = UnoDB("postgresql+asyncpg://user:password@localhost:5432/dbname")

# Query example
async def get_user(user_id: int):
    async with db.session() as session:
        result = await session.execute(
            "SELECT * FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        user = result.fetchone()
        return dict(user) if user else None

# Transaction example
async def transfer_funds(from_account_id: int, to_account_id: int, amount: float):
    async with db.session() as session:
        async with session.begin():
            # Debit from account
            await session.execute(
                "UPDATE accounts SET balance = balance - :amount WHERE id = :account_id",
                {"amount": amount, "account_id": from_account_id}
            )
            
            # Credit to account
            await session.execute(
                "UPDATE accounts SET balance = balance + :amount WHERE id = :account_id",
                {"amount": amount, "account_id": to_account_id}
            )
```

### Using SQLAlchemy ORM

```python
from uno.infrastructure.database import UnoDB
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.domain.models import UserModel

# Create database
db = UnoDB("postgresql+asyncpg://user:password@localhost:5432/dbname")

# Query with ORM
async def get_users_by_email_domain(domain: str):
    async with db.session() as session:
        query = select(UserModel).where(UserModel.email.endswith(f"@{domain}"))
        result = await session.execute(query)
        users = result.scalars().all()
        return users

# Create with ORM
async def create_user(name: str, email: str):
    async with db.session() as session:
        async with session.begin():
            user = UserModel(name=name, email=email)
            session.add(user)
            await session.flush()
            return user
```

## Further Reading

- [Transaction Management](transaction_management.md): Detailed guide to transactions
- [Unit of Work](../core/uow/index.md): Transaction management with Unit of Work
- [Connection Pooling](enhanced_connection_pool.md): Advanced connection pooling
- [Query Optimization](query_optimizer.md): Optimizing database queries