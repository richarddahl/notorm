# Centralized Database Engine

This document describes the centralized database connection management in the uno package, supporting both synchronous and asynchronous operations.

## Overview

A centralized approach to database connection management is defined that:

1. Provides a consistent way to create database connections across the application
2. Consolidates error handling, retry logic, and connection pooling
3. Enables dependency injection for better testability
4. Reduces code duplication
5. Supports both synchronous and asynchronous operations

## Key Components

### 1. Database Factory Pattern

The framework provides specialized factories for different database access patterns:

- **DatabaseFactory**: Top-level facade that provides access to specialized factories
- **SyncEngineFactory**: Creates synchronous SQLAlchemy engines and connections
- **AsyncEngineFactory**: Creates asynchronous SQLAlchemy engines and connections 
- **AsyncSessionFactory**: Creates SQLAlchemy ORM sessions with async support

```python
from uno.database.engine import DatabaseFactory

# Create the unified factory
factory = DatabaseFactory()

# Access specialized factories
sync_factory = factory.get_sync_engine_factory()
async_factory = factory.get_async_engine_factory()
session_factory = factory.get_async_session_factory()
```

### 2. Connection Context Managers

Context managers for safely obtaining and disposing of database connections:

#### Synchronous Operations

```python
from uno.database.engine import sync_connection

with sync_connection(```

db_role="my_role",
db_name="my_database", 
db_driver="postgresql+psycopg2"
```
) as conn:```

# Use the connection
result = conn.execute(query)
```
```

#### Asynchronous Operations

```python
from uno.database.engine import async_connection

async with async_connection(```

db_role="my_role",
db_name="my_database",
db_driver="postgresql+asyncpg"
```
) as conn:```

# Use the connection asynchronously
result = await conn.execute(query)
```
```

### 3. Session Management

For ORM operations, the framework provides session context managers:

```python
from uno.database.session import async_session

async with async_session(```

db_role="my_role",
db_name="my_database"
```
) as session:```

# Use the ORM session
result = await session.execute(query)
await session.commit()
```
```

### 4. Configuration Management

Database connections are configured using the `ConnectionConfig` model:

```python
from uno.database.config import ConnectionConfig

# Create a connection configuration
config = ConnectionConfig(```

db_role="my_role",
db_name="my_database"
```,```

db_host="localhost",
db_port=5432,
db_driver="postgresql+asyncpg",
pool_size=10,
max_overflow=20
```
)

# Use with connection context managers
async with async_connection(config=config) as conn:```

# Use the connection
pass
```
```

## Implementation Details

### Engine Factory Features

The engine factories provide several advanced features:

- **Connection Pooling**: Configurable connection pools with sensible defaults
- **Retry Logic**: Built-in exponential backoff for handling transient failures
- **Connection Callbacks**: Register functions to execute on every new connection
- **Validation**: Comprehensive parameter validation before connection attempts
- **Consistent Logging**: Structured connection logging with consistent format
- **Error Handling**: Centralized error handling with appropriate recovery strategies
- **Resource Management**: Automatic disposal of connections and engines

### ConnectionConfig Model

The `ConnectionConfig` model offers:

- **Immutability**: Thread-safe, immutable configuration objects
- **Validation**: Type checking and validation of connection parameters
- **Smart Defaults**: Sensible defaults from application settings
- **URI Generation**: Automatic generation of database URIs based on config
- **Connection Pooling Options**: Fine-grained connection pool configuration

### Asynchronous Support

The async support includes:

- **Full AsyncIO Integration**: Native support for Python's asyncio
- **SQLAlchemy 2.0 Compatibility**: Support for the latest SQLAlchemy async APIs
- **Async Context Managers**: Proper resource management with async context managers
- **Async Session Support**: ORM session management with async/await syntax
- **Transaction Management**: Async-compatible transaction management

## Benefits

1. **Reduced Duplication**: Centralized connection logic eliminates duplication
2. **Improved Error Handling**: Consistent error handling across sync and async code
3. **Better Testability**: Clear interfaces make database code easier to mock
4. **Configuration Management**: Single source of truth for database configuration
5. **Connection Lifecycle Management**: Automatic cleanup of database resources
6. **Async and Sync Support**: Unified API for both synchronous and asynchronous operations
7. **Type Safety**: Comprehensive type hints improve IDE support and catch errors

## Usage Guidelines

1. **Prefer Context Managers**: Always use the provided context managers (sync_connection, async_connection) instead of directly creating engines
2. **Dependency Injection**: Inject factories into services rather than using global instances
3. **Centralized Configuration**: Store connection details in ConnectionConfig objects
4. **Connection Callbacks**: Use callbacks for session setup, rather than repeating code
5. **Error Handling**: Let the connection managers handle retries and error recovery
6. **Async Aware**: Use async_connection for async code paths and sync_connection for synchronous code
7. **Resource Management**: Rely on context managers to properly clean up resources

## Testing

The database layer is designed for testability. When testing code that uses the database:

### 1. Mock the Database Layer

```python
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection

# For synchronous tests
mock_sync_factory = MagicMock()
mock_engine = MagicMock()
mock_conn = MagicMock()
mock_sync_factory.create_engine.return_value = mock_engine
mock_engine.connect.return_value = mock_conn

# For asynchronous tests
mock_async_factory = AsyncMock()
mock_async_engine = AsyncMock(spec=AsyncEngine)
mock_async_conn = AsyncMock(spec=AsyncConnection)
mock_async_factory.create_engine.return_value = mock_async_engine
mock_async_engine.connect.return_value = mock_async_conn
mock_async_conn.__aenter__.return_value = mock_async_conn
```

### 2. Use Dependency Injection

```python
# Inject the mock factory when testing
service = MyDatabaseService(engine_factory=mock_sync_factory)
async_service = MyAsyncDatabaseService(engine_factory=mock_async_factory)
```

### 3. Testing Asynchronous Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_database_operation():```

# Setup async mocks
mock_factory = AsyncMock()
mock_engine = AsyncMock(spec=AsyncEngine)
mock_conn = AsyncMock(spec=AsyncConnection)
``````

```
```

# Configure mock chain
mock_factory.create_engine.return_value = mock_engine
mock_engine.connect.return_value = mock_conn
mock_conn.__aenter__.return_value = mock_conn
``````

```
```

# Setup your test service with the mock
service = MyService(engine_factory=mock_factory)
``````

```
```

# Run the test
result = await service.fetch_data()
``````

```
```

# Assert expectations
assert result is not None
mock_conn.execute.assert_called_once()
```
```