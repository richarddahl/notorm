# Database Provider

The Uno framework includes a unified database provider system that centralizes database connections and provides a consistent API for both synchronous and asynchronous database access.

## Overview

The `DatabaseProvider` is the primary entry point for all database operations in Uno applications. It manages connection pools, session factories, and provides context managers for database access.

The `DatabaseProvider` is a core component of the new database architecture, designed to work with both the legacy UnoObj pattern and the new dependency injection approach. It offers a clean, testable interface for database operations with proper resource management and error handling.

## Key Features

- **Unified API**: Consistent interface for both sync and async operations
- **Connection Pooling**: Efficient connection management for both SQLAlchemy and raw connections
- **Context Managers**: Clean resource management with context managers
- **Dependency Injection**: Seamless integration with the DI system
- **Health Checks**: Built-in database health monitoring

## Usage

### Basic Usage with Dependency Injection

The most common way to access the database is through the dependency injection system:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_db_session

router = APIRouter()

@router.get("/items")
async def list_items(session = Depends(get_db_session)):
    result = await session.execute("SELECT * FROM items")
    return result.scalars().all()
```

### Accessing the Provider Directly

For more advanced cases, you can access the database provider directly:

```python
from uno.dependencies import get_instance, UnoDatabaseProviderProtocol

# Get the database provider
db_provider = get_instance(UnoDatabaseProviderProtocol)

# Use with async context manager
async with db_provider.async_session() as session:
    # Use SQLAlchemy ORM
    result = await session.execute("SELECT * FROM items")
    items = result.scalars().all()
    
# Use with sync context manager
with db_provider.sync_connection() as conn:
    # Use raw psycopg connection
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
```

### Raw Connections

For operations that require direct database access:

```python
from uno.dependencies import get_raw_connection

async def execute_complex_query():
    async with get_raw_connection() as conn:
        # Use asyncpg features
        records = await conn.fetch("SELECT * FROM items WHERE id = $1", some_id)
        return records
```

## Connection Types

The database provider offers four types of connections:

| Method | Return Type | Description |
|--------|-------------|-------------|
| `async_session()` | `AsyncSession` | SQLAlchemy ORM async session |
| `sync_session()` | `Session` | SQLAlchemy ORM sync session |
| `async_connection()` | `asyncpg.Connection` | Raw asyncpg connection |
| `sync_connection()` | `psycopg.Connection` | Raw psycopg connection |

## Configuration

The database provider is configured automatically based on your application settings. The connection parameters are read from your environment or settings file:

```python
# Example settings
DB_NAME = "myapp"
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER_PW = "password"
DB_ASYNC_DRIVER = "postgresql+asyncpg"
DB_SCHEMA = "public"
```

## Health Checks

The database provider includes a health check method that can be used to verify database connectivity:

```python
from uno.dependencies import get_instance, UnoDatabaseProviderProtocol

async def check_database_health():
    db_provider = get_instance(UnoDatabaseProviderProtocol)
    is_healthy = await db_provider.health_check()
    return {"database": "up" if is_healthy else "down"}
```

## Lifecycle Management

For proper resource management, the database provider should be closed when shutting down the application:

```python
from fastapi import FastAPI
from uno.dependencies import get_instance, UnoDatabaseProviderProtocol

app = FastAPI()

@app.on_event("shutdown")
async def shutdown_event():
    db_provider = get_instance(UnoDatabaseProviderProtocol)
    await db_provider.close()
```

## Advanced Usage

### Transaction Management

```python
async with get_db_session() as session:
    async with session.begin():
        # All operations in this block will be in a transaction
        await session.execute("INSERT INTO items (name) VALUES (:name)", {"name": "New Item"})
        await session.execute("UPDATE counters SET value = value + 1 WHERE name = 'items'")
        # Transaction automatically committed if no exceptions, rolled back otherwise
```

### Multiple Databases

If your application needs to connect to multiple databases, you can create and register additional database providers:

```python
from uno.database.provider import DatabaseProvider
from uno.database.config import ConnectionConfig
import inject

# Create a new database provider
analytics_config = ConnectionConfig(
    db_name="analytics",
    db_host="analytics.example.com",
    # other parameters...
)
analytics_db = DatabaseProvider(analytics_config)

# Register in the DI container
inject.instance(inject.Binder).bind("AnalyticsDB", analytics_db)

# Use it in your code
analytics_db = inject.instance("AnalyticsDB")
```