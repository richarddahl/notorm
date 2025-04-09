# Centralized Database Engine

This document describes the centralized database connection management in the uno package.

## Overview

A centralized approach to database connection management is defined that:

1. Provides a consistent way to create database connections across the application
2. Consolidates error handling, retry logic, and connection pooling
3. Enables dependency injection for better testability
4. Reduces code duplication

## Key Components

### 1. DatabaseFactory (`uno/db/engine.py`)

A factory class that centralizes the creation of database engines:

```python
from uno.db.engine import get_engine_factory

# Get the global factory instance
factory = get_engine_factory()

# Create an engine
engine = factory.create_engine(
    db_role="my_role",
    db_name="my_database"
)
```

### 2. engine_context Context Manager

A context manager for safely obtaining and disposing of database connections:

```python
from uno.db.engine import engine_context

with engine_context(
    db_role="my_role",
    db_name="my_database"
) as conn:
    # Use the connection
    result = conn.execute(query)
```

### 3. Updated DBManager

The `DBManager` class has been updated to use the centralized engine factory:

```python
from uno.db.engine import DatabaseFactory
from uno.db.manager import DBManager

# Create a DBManager with a custom engine factory
my_factory = DatabaseFactory(config=my_config)
manager = DBManager(
    config=my_config,
    engine_factory=my_factory
)

# Create the database
manager.create_db()
```

## Implementation Details

### DatabaseFactory Features

- **Connection Pooling**: Configure connection pools consistently
- **Retry Logic**: Built-in exponential backoff for transient failures
- **Connection Callbacks**: Register functions to run on each new connection
- **Validation**: Parameter validation before connection attempts
- **Consistent Logging**: Structured, detailed connection logging

### Integration with Existing Code

The DBManager class has been updated to use the centralized engine factory while maintaining the same public API. This ensures backward compatibility while improving the underlying implementation.

## Benefits

1. **Reduced Duplication**: Eliminated duplicate connection logic across the codebase
2. **Improved Error Handling**: Consistent, centralized error handling and retry logic
3. **Better Testability**: Easier to mock the database layer in tests
4. **Configuration Management**: Central point for database connection configuration
5. **Connection Lifecycle Management**: Consistent resource cleanup and connection pooling

## Usage Guidelines

1. **Prefer engine_context**: Always use the engine_context context manager instead of directly creating engines
2. **Inject Dependencies**: When creating custom services, inject the engine factory rather than creating connections directly
3. **Use Factory for Configuration**: Configure connection parameters through the factory
4. **Leverage Connection Callbacks**: Use connection callbacks for session initialization, query logging, etc.

## Testing

When testing code that uses the database:

1. Create a mock engine factory
2. Inject the mock factory into your services
3. Use the factory's API to control test behavior

```python
class MockEngineFactory(DatabaseFactory):
    def create_engine(self, **kwargs):
        # Return a mock engine
        return mock_engine

# Inject the mock factory
my_service = MyService(engine_factory=MockEngineFactory())
```
