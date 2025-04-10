# Database Layer Overview

The Database Layer in uno provides a comprehensive approach to database operations, with specialized components for connection management, model definition, and SQL generation.

## Key Components

### DatabaseFactory

The `DatabaseFactory` is a unified factory for creating database connections. It supports both synchronous and asynchronous operations and provides consistent error handling, connection pooling, and resource management.

```python
from uno.database.engine import DatabaseFactory

# Create a database factory
db_factory = DatabaseFactory()

# Get specialized factories
sync_factory = db_factory.get_sync_engine_factory()
async_factory = db_factory.get_async_engine_factory()
session_factory = db_factory.get_async_session_factory()
```

### Connection Context Managers

Context managers for safely obtaining and disposing of database connections:

```python
# Synchronous operations
from uno.database.engine import sync_connection

with sync_connection(db_role="my_role", db_name="my_database") as conn:
    # Use the connection
    result = conn.execute(query)

# Asynchronous operations
from uno.database.engine import async_connection

async with async_connection(db_role="my_role", db_name="my_database") as conn:
    # Use the connection asynchronously
    result = await conn.execute(query)
```

### UnoModel

The `UnoModel` class is a SQLAlchemy `DeclarativeBase` subclass that provides standardized column types, type annotations, and configuration for database constraints.

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class CustomerModel(UnoModel):
    __tablename__ = "customer"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
```

### UnoDB

The `UnoDB` class provides database operations for models, including CRUD operations, filtering, and transaction management.

```python
from uno.database.db import UnoDBFactory

# Create a database interface for a model
db = UnoDBFactory(obj=CustomerModel)

# Create a new record
customer, created = await db.create(schema=customer_data)

# Get a record by ID
customer = await db.get(id="abc123")

# Update a record
updated = await db.update(to_db_model=customer)

# Delete a record
await db.delete(customer)
```

### SQL Emitters

SQL emitters generate SQL statements for database objects, including tables, functions, triggers, and grants.

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.emitters.table import TableEmitter

# Create a table emitter
emitter = TableEmitter(model=CustomerModel)

# Generate SQL for creating the table
sql = emitter.emit()
```

## Features

### Connection Management

- Centralized approach to database connection management
- Support for both synchronous and asynchronous operations
- Connection pooling and retry logic
- Resource management and cleanup

### Model Definition

- Type-annotated models with standardized column types
- Support for PostgreSQL-specific features
- Integration with SQLAlchemy ORM
- Support for model inheritance, relationships, and constraints

### SQL Generation

- Automatic generation of SQL for creating database objects
- Support for complex SQL features like functions and triggers
- Row-level security integration
- Migration support

## Best Practices

1. **Use Context Managers**: Always use the provided context managers for database connections
2. **Leverage Type Annotations**: Use proper type annotations for better IDE support and type checking
3. **Follow SQLAlchemy Patterns**: Adhere to SQLAlchemy's recommended patterns and practices
4. **Use PostgreSQL Features**: Leverage PostgreSQL-specific features when appropriate
5. **Manage Resources**: Properly dispose of connections and sessions

## Next Steps

- [Database Engine](engine.md): Learn about the database engine factory pattern
- [UnoModel](../models/overview.md): Understand how to define database models
- [UnoDB](unodb.md): Learn about database operations
- [SQL Emitters](../sql_generation/overview.md): Understand how to generate SQL statements