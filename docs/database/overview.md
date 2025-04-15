# Database Layer

The Database Layer in uno provides a comprehensive approach to database operations with specialized components for connection management, model definition, and SQL generation.

!!! note "Architectural Evolution"```

uno now offers both the original database architecture and a new unified architecture through the `DatabaseProvider`, `UnoBaseRepository`, and `SchemaManager` classes. The new architecture provides better separation of concerns, improved testability, and support for dependency injection.
```

## In This Section

- [Database Engine](engine.md) - Connection management and factory patterns
- [Database Manager](db_manager.md) - DDL execution and database management
- [Transaction Management](transaction_management.md) - Robust transaction handling patterns
- [Enhanced Connection Pool](enhanced_connection_pool.md) - Advanced connection pooling
- [Database Repository](repository.md) - Repository pattern implementation
- [Database Provider](provider.md) - Modern database connection provider
- [UnoDB](unodb.md) - Database operations interface for models
- [Schema Manager](schema_manager.md) - Schema creation and validation

## Overview

The Database Layer forms the foundation of uno, providing robust database connectivity, object-relational mapping, and type-safe database operations. It's designed to leverage PostgreSQL-specific features while maintaining a clean, consistent API that works well in both synchronous and asynchronous contexts.

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

### UnoModel

The `UnoModel` class is a SQLAlchemy `DeclarativeBase` subclass that provides standardized column types, type annotations, and configuration for database constraints.

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class CustomerModel(UnoModel):```

__tablename__ = "customer"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
```
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

## Modern Database Architecture

The new database architecture introduces a more modern approach to database operations, with improved separation of concerns, better testability, and support for dependency injection.

### DatabaseProvider

The `DatabaseProvider` is a centralized service that manages database connections, session factories, and connection pools.

```python
from uno.database.provider import DatabaseProvider
from uno.database.config import ConnectionConfig

# Create a database provider
config = ConnectionConfig(```

host="localhost", 
port=5432, 
user="postgres", 
password="password", 
database="mydb"
```
)
db_provider = DatabaseProvider(config)

# Get an async session
async with db_provider.async_session() as session:```

# Use the session
result = await session.execute(query)
```
```

### UnoBaseRepository

The `UnoBaseRepository` implements the repository pattern for data access. It provides a clean, testable interface for CRUD operations and complex queries.

```python
from uno.database.repository import UnoBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

class CustomerRepository(UnoBaseRepository[CustomerModel]):```

def __init__(self, session: AsyncSession):```

super().__init__(session, CustomerModel)
```
``````

```
```

async def get_by_email(self, email: str) -> Optional[CustomerModel]:```

stmt = select(self.model_class).where(self.model_class.email == email)
result = await self.session.execute(stmt)
return result.scalars().first()
```
```
```

### DBManager

The `DBManager` provides utilities for database operations, including executing DDL statements and managing database objects.

```python
from uno.database.db_manager import DBManager
from uno.sql.emitters.function import FunctionEmitter

# Create a database manager
db_manager = DBManager(get_connection)

# Execute DDL directly
db_manager.execute_ddl("CREATE TABLE customers (id SERIAL PRIMARY KEY, name TEXT)")

# Execute DDL through an emitter
function_emitter = FunctionEmitter(```

name="update_customer",
params=[{"name": "id", "type": "INTEGER"}, {"name": "name", "type": "TEXT"}],
return_type="VOID",
body="UPDATE customers SET name = $2 WHERE id = $1;"
```
)
db_manager.execute_from_emitter(function_emitter)
```

## Best Practices

1. **Use Context Managers**: Always use the provided context managers for database connections to ensure proper resource cleanup.
   ```python
   async with async_session() as session:```

   # Use session here
```
   ```

2. **Leverage Type Annotations**: Use proper type annotations for better IDE support and type checking.
   ```python
   async def get_user(user_id: str) -> Optional[UserModel]:```

   # Implementation
```
   ```

3. **Follow SQLAlchemy Patterns**: Adhere to SQLAlchemy's recommended patterns and practices for query building and execution.

4. **Use PostgreSQL Features**: Leverage PostgreSQL-specific features when appropriate, such as JSONB, GIN indexes, and row-level security.

5. **Manage Resources**: Properly dispose of connections and sessions to prevent resource leaks.

6. **Prefer Repositories**: For complex domain logic, use the repository pattern to encapsulate database access.

7. **Test Integration Points**: Use integration tests to verify database components work correctly together.

## Testing Database Components

The database layer includes comprehensive integration tests to ensure all components work correctly together:

### Connection Pool Tests

Tests verify that connection pooling works correctly with proper connection reuse, overflow handling, and circuit breaking for error conditions.

```bash
pytest tests/integration/test_connection_pool.py --run-integration
```

### Transaction Management Tests

Tests for transaction isolation, nested transactions, multi-table operations, and proper cleanup.

```bash
pytest tests/integration/test_transaction.py --run-integration
```

For more details on transaction management, see the [Transaction Management](transaction_management.md) documentation.

### Query Optimizer Tests

Tests for query plan analysis, automatic query optimization, and query caching.

```bash
pytest tests/integration/test_query_optimizer.py --run-integration
```

### Database Migration Tests

Tests for schema migration and version management.

```bash
pytest tests/integration/test_migrations.py --run-integration
```

### Batch Operations Tests

Tests for efficient batch processing with different execution strategies.

```bash
pytest tests/integration/test_batch_operations.py --run-integration
```

## Choosing an Approach

### When to Use the Original Architecture

- For simpler applications with straightforward database needs
- When working with existing uno code that uses the original patterns
- For quick prototyping

### When to Use the Modern Architecture

- For new features and modules
- When testability is a primary concern
- When dependency injection is preferred over the factory pattern
- For services that require fine-grained control over database operations

## Related Sections

- [Models Layer](/docs/models/overview.md) - Model definition and mapping
- [SQL Generation](/docs/sql_generation/overview.md) - SQL emitters and statement building
- [Dependency Injection](/docs/dependency_injection/overview.md) - Integration with the dependency injection system