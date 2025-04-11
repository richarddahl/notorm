# Database Layer Overview

> **New Architecture Available**: Uno now offers a unified database architecture through the `DatabaseProvider`, `UnoBaseRepository`, and `SchemaManager` classes. This modern architecture provides better separation of concerns, improved testability, and support for dependency injection. See the [New Database Architecture](#new-database-architecture) section for details.

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

## New Database Architecture

The new database architecture introduces a more modern approach to database operations, with improved separation of concerns, better testability, and support for dependency injection.

### DatabaseProvider

The `DatabaseProvider` is a centralized service that manages database connections, session factories, and connection pools. It provides a unified interface for both synchronous and asynchronous database operations.

```python
from uno.database.provider import DatabaseProvider
from uno.database.config import ConnectionConfig

# Create a database provider
config = ConnectionConfig(
    host="localhost", 
    port=5432, 
    user="postgres", 
    password="password", 
    database="mydb"
)
db_provider = DatabaseProvider(config)

# Get an async session
async with db_provider.async_session() as session:
    # Use the session
    result = await session.execute(query)

# Get a sync connection
with db_provider.sync_connection() as conn:
    # Use the connection
    result = conn.execute(query)
```

### UnoBaseRepository

The `UnoBaseRepository` implements the repository pattern for data access. It provides a clean, testable interface for CRUD operations and complex queries.

```python
from uno.database.repository import UnoBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

class CustomerRepository(UnoBaseRepository[CustomerModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CustomerModel)
    
    async def get_by_email(self, email: str) -> Optional[CustomerModel]:
        stmt = select(self.model_class).where(self.model_class.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_active_customers(self) -> List[CustomerModel]:
        stmt = select(self.model_class).where(self.model_class.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

### DBManager

The `DBManager` provides utilities for database operations, including executing DDL statements, managing schemas, functions, triggers, and other database objects.

```python
from uno.database.db_manager import DBManager
from uno.sql.emitters.function import FunctionEmitter
from contextlib import contextmanager
import psycopg

# Create a connection provider
def get_connection():
    @contextmanager
    def _get_connection():
        with psycopg.connect("postgresql://postgres:password@localhost/mydb") as conn:
            yield conn
    return _get_connection()

# Create a database manager
db_manager = DBManager(get_connection)

# Execute DDL directly
db_manager.execute_ddl("CREATE TABLE customers (id SERIAL PRIMARY KEY, name TEXT)")

# Execute DDL through an emitter
function_emitter = FunctionEmitter(
    name="update_customer",
    params=[{"name": "id", "type": "INTEGER"}, {"name": "name", "type": "TEXT"}],
    return_type="VOID",
    body="UPDATE customers SET name = $2 WHERE id = $1;"
)
db_manager.execute_from_emitter(function_emitter)
```

### Integration with Dependency Injection

The new architecture seamlessly integrates with dependency injection frameworks:

```python
from uno.dependencies.database import get_db_session, get_db_manager
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# In FastAPI endpoints
@app.get("/customers")
async def get_customers(session: AsyncSession = Depends(get_db_session)):
    repository = CustomerRepository(session)
    customers = await repository.get_all()
    return customers

# Using DBManager for DDL operations
@app.post("/initialize")
async def initialize_app(db_manager = Depends(get_db_manager)):
    # Create function using emitter
    from uno.sql.emitters.function import FunctionEmitter
    
    function_emitter = FunctionEmitter(
        name="audit_log",
        params=[
            {"name": "table_name", "type": "TEXT"},
            {"name": "action", "type": "TEXT"},
            {"name": "record_id", "type": "TEXT"}
        ],
        return_type="VOID",
        body="""
        INSERT INTO audit_log (table_name, action, record_id, created_at)
        VALUES ($1, $2, $3, NOW());
        """,
        language="plpgsql"
    )
    
    # Execute the emitter
    db_manager.execute_from_emitter(function_emitter)
    
    return {"status": "ok", "message": "Database initialized"}
```

### Benefits of the New Architecture

1. **Separation of Concerns**: Each component has a single responsibility
2. **Improved Testability**: Easy to mock and test components in isolation
3. **Dependency Injection**: Support for modern dependency injection patterns
4. **Type Safety**: Full type annotation and protocol-based interfaces
5. **Resource Management**: Consistent handling of database resources
6. **Compatibility**: Works alongside the existing database layer

### When to Use the New Architecture

- For new features and modules
- When testability is a primary concern
- When dependency injection is preferred over the factory pattern
- For services that require fine-grained control over database operations

## Next Steps

- [Database Engine](engine.md): Learn about the database engine factory pattern
- [UnoModel](../models/overview.md): Understand how to define database models
- [UnoDB](unodb.md): Learn about database operations
- [SQL Emitters](../sql_generation/overview.md): Understand how to generate SQL statements
- [Database Provider](provider.md): Learn about the new database provider
- [Repository Pattern](repository.md): Understand the repository pattern
- [DB Manager](db_manager.md): Learn about database operations and SQL execution