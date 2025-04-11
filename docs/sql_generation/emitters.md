# SQL Emitters

SQL emitters in Uno are components that generate SQL statements for various database objects. They provide a clean and consistent way to create complex SQL without writing raw SQL strings.

## Using Emitters with Dependency Injection

Uno provides a dependency injection system for working with SQL emitters. This approach offers better testability, consistent configuration, and simplified usage patterns:

```python
from uno.dependencies import get_sql_emitter_factory, get_sql_execution_service
from uno.sql.emitters.function import FunctionEmitter

# Get services via dependency injection
factory = get_sql_emitter_factory()
executor = get_sql_execution_service()

# Create an emitter using the factory
function_emitter = factory.create_emitter_instance(
    FunctionEmitter,
    name="update_timestamp",
    params=[],
    return_type="TRIGGER",
    body="""
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    """,
    language="plpgsql"
)

# Execute it with the execution service
executor.execute_emitter(function_emitter)
```

### Using Registered Emitters

Standard emitters are registered with the factory:

```python
from uno.dependencies import get_sql_emitter_factory, get_db_manager

# Get the SQL emitter factory
emitter_factory = get_sql_emitter_factory()

# Create an emitter by name
emitter = emitter_factory.get_emitter(
    "create_pgulid"  # Pre-registered emitter
)

# Execute the emitter
db_manager = get_db_manager()
db_manager.execute_from_emitter(emitter)
```

### Direct SQL Execution

For simpler cases, you can execute SQL directly:

```python
from uno.dependencies import get_sql_execution_service

# Get the execution service
sql_execution = get_sql_execution_service()

# Execute DDL directly
sql_execution.execute_ddl("""
CREATE TABLE test (
    id SERIAL PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")
```

## Base Emitter

The SQLEmitter class is the foundation for all SQL emitters. It provides common functionality for SQL generation:

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType

class CustomEmitter(SQLEmitter):
    """Custom SQL emitter for a specific purpose."""
    
    def generate_sql(self):
        """Generate SQL statements."""
        return [
            SQLStatement(
                name="custom_statement",
                type=SQLStatementType.TABLE,
                sql="CREATE TABLE example (id SERIAL PRIMARY KEY, name TEXT)"
            )
        ]
```

## Table Emitter

The `TableEmitter` generates SQL for creating database tables:

```python
from uno.sql.emitters.table import TableEmitter
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

# Define a model
class CustomerModel(UnoModel):
    __tablename__ = "customer"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)

# Create a table emitter
emitter = TableEmitter(model=CustomerModel)

# Generate SQL for the table
statements = emitter.generate_sql()
for statement in statements:
    print(f"{statement.name}: {statement.sql}")
```

The generated SQL will include:

- Primary key definitions
- Column types and constraints
- Indices
- Foreign keys
- Comments

## Function Emitter

The `FunctionEmitter` generates SQL for creating database functions:

```python
from uno.sql.builders.function import FunctionEmitter

# Define function parameters
params = [
    {"name": "customer_id", "type": "TEXT"},
    {"name": "new_status", "type": "TEXT"}
]

# Define function body
body = """
UPDATE customer
SET status = new_status
WHERE id = customer_id;
RETURN 1;
"""

# Create a function emitter
emitter = FunctionEmitter(
    name="update_customer_status",
    params=params,
    return_type="INTEGER",
    body=body,
    language="plpgsql"
)

# Generate SQL for the function
statements = emitter.generate_sql()
for statement in statements:
    print(f"{statement.name}: {statement.sql}")
```

## Trigger Emitter

The `TriggerEmitter` generates SQL for creating database triggers:

```python
from uno.sql.builders.trigger import TriggerEmitter

# Create a trigger emitter
emitter = TriggerEmitter(
    name="customer_update_trigger",
    table="customer",
    events=["INSERT", "UPDATE"],
    timing="AFTER",
    function="log_customer_changes",
    for_each="ROW"
)

# Generate SQL for the trigger
statements = emitter.generate_sql()
for statement in statements:
    print(f"{statement.name}: {statement.sql}")
```

## Security Emitter

The `SecurityEmitter` generates SQL for security-related operations, such as row-level security policies:

```python
from uno.sql.emitters.security import SecurityEmitter

# Create a security emitter
emitter = SecurityEmitter(
    table="customer",
    policy_name="customer_access_policy",
    using_expr="(user_id = current_user_id())",
    check_expr="(user_id = current_user_id())"
)

# Generate SQL for the security policy
statements = emitter.generate_sql()
for statement in statements:
    print(f"{statement.name}: {statement.sql}")
```

## Grants Emitter

The `GrantsEmitter` generates SQL for granting permissions:

```python
from uno.sql.emitters.grants import GrantsEmitter

# Create a grants emitter
emitter = GrantsEmitter(
    table="customer",
    privileges=["SELECT", "INSERT", "UPDATE"],
    roles=["app_user", "app_admin"]
)

# Generate SQL for granting permissions
statements = emitter.generate_sql()
for statement in statements:
    print(f"{statement.name}: {statement.sql}")
```

## Using Emitters Together

You can combine multiple emitters to generate complex SQL:

```python
from uno.sql.emitters.table import TableEmitter
from uno.sql.builders.function import FunctionEmitter
from uno.sql.builders.trigger import TriggerEmitter
from uno.sql.emitters.security import SecurityEmitter
from uno.sql.emitters.grants import GrantsEmitter

# Using dependency injection to work with multiple emitters
from uno.dependencies import get_sql_emitter_factory, get_sql_execution_service

# Get services
factory = get_sql_emitter_factory()
executor = get_sql_execution_service()

# Create emitters using the factory
table_emitter = factory.create_emitter_instance(TableEmitter, model=CustomerModel)

function_emitter = factory.create_emitter_instance(
    FunctionEmitter,
    name="update_customer_status",
    params=[
        {"name": "customer_id", "type": "TEXT"},
        {"name": "new_status", "type": "TEXT"}
    ],
    return_type="INTEGER",
    body="UPDATE customer SET status = new_status WHERE id = customer_id; RETURN 1;",
    language="plpgsql"
)

trigger_emitter = factory.create_emitter_instance(
    TriggerEmitter,
    name="customer_update_trigger",
    table="customer",
    events=["INSERT", "UPDATE"],
    timing="AFTER",
    function="log_customer_changes",
    for_each="ROW"
)

# Execute them in sequence
executor.execute_emitter(table_emitter)
executor.execute_emitter(function_emitter)
executor.execute_emitter(trigger_emitter)

# Or for more complex orchestration, you can register them with standard names
factory.register_emitter("customer_table", lambda: TableEmitter(model=CustomerModel))
factory.register_emitter("customer_function", lambda: FunctionEmitter(...))
factory.register_emitter("customer_trigger", lambda: TriggerEmitter(...))

# And then create and execute them by name
emitters = [
    factory.get_emitter("customer_table"),
    factory.get_emitter("customer_function"),
    factory.get_emitter("customer_trigger")
]

# Execute all emitters in a batch
for emitter in emitters:
    executor.execute_emitter(emitter)
```

## Table Merge Function Emitter

The `TableMergeFunction` emitter generates a PostgreSQL function for merging records using the MERGE command introduced in PostgreSQL 16. It's designed for upsert operations that intelligently handle both inserts and updates based on primary keys or unique constraints.

```python
from uno.dependencies import get_sql_emitter_factory, get_sql_execution_service
from uno.sql.emitters import TableMergeFunction
from sqlalchemy import Table, MetaData

# Get services
factory = get_sql_emitter_factory()
executor = get_sql_execution_service()

# Get a SQLAlchemy table object
metadata = MetaData()
table = Table('my_table', metadata, autoload_with=engine)

# Create the merge function emitter using the factory
emitter = factory.create_emitter_instance(TableMergeFunction, table=table)

# Execute it with the execution service
executor.execute_emitter(emitter)
```

The generated merge function accepts a JSONB object and performs the following operations:

1. Examines the JSONB data to identify which keys to use for record matching (primary keys or unique constraints)
2. Looks up the record in the database if matching key fields are present
3. If found, updates non-key columns that have changed (ignoring null values for required columns)
4. If not found, inserts a new record
5. Returns the final record with an `_action` field indicating 'inserted', 'updated', or 'selected'

Usage example:

```sql
-- Call the generated merge function
SELECT my_schema.merge_my_table_record('{"id": "123", "name": "John Doe", "email": "john@example.com"}'::jsonb);

-- Result includes the action performed
-- {"id": "123", "name": "John Doe", "email": "john@example.com", "_action": "inserted"}
```

The function is particularly useful for integrating with UnoObj's model_dump() data and provides a complete record lifecycle management solution.

## Best Practices

1. **Use Dependency Injection**: Prefer using the SQL emitter factory and execution service through dependency injection for better testability and consistency.

2. **Leverage Factory Services**: Use the `get_sql_emitter_factory()` to create emitters with consistent configuration.

3. **Centralize Execution**: Use the `get_sql_execution_service()` for standardized SQL execution.

4. **Separate Concerns**: Use different emitters for different types of database objects.

5. **Validate SQL**: Test the generated SQL to ensure it's correct and follows your database's requirements.

6. **Use Migrations**: Combine emitters with a migration system to manage database schema changes.

7. **Document Generated SQL**: Add comments to explain the purpose and behavior of generated SQL.

8. **Leverage PostgreSQL Features**: Use PostgreSQL-specific features when appropriate, such as the MERGE command in PostgreSQL 16+.

9. **Test Edge Cases**: Test SQL generation with special characters, long names, and other edge cases.

10. **Register Common Emitters**: Register frequently used emitters with the factory for easy reuse.

11. **Handle Errors**: Properly handle SQL execution errors by checking validation results.

12. **Maintain Abstraction Layers**: Keep the SQL generation and execution concerns separate from business logic.