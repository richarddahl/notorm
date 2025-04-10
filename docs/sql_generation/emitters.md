# SQL Emitters

SQL emitters in uno are components that generate SQL statements for various database objects. They provide a clean and consistent way to create complex SQL without writing raw SQL strings.

## Base Emitter

The `BaseEmitter` class is the foundation for all SQL emitters. It provides common functionality for SQL generation:

```python
from uno.sql.emitter import BaseEmitter

class CustomEmitter(BaseEmitter):
    def __init__(self, model):
        super().__init__()
        self.model = model
    
    def emit(self):
        """Generate SQL for the model."""
        return f"-- SQL for {self.model.__tablename__}"
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
sql = emitter.emit()
print(sql)
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
sql = emitter.emit()
print(sql)
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
sql = emitter.emit()
print(sql)
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
sql = emitter.emit()
print(sql)
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
sql = emitter.emit()
print(sql)
```

## Using Emitters Together

You can combine multiple emitters to generate complex SQL:

```python
from uno.sql.emitters.table import TableEmitter
from uno.sql.builders.function import FunctionEmitter
from uno.sql.builders.trigger import TriggerEmitter
from uno.sql.emitters.security import SecurityEmitter
from uno.sql.emitters.grants import GrantsEmitter

# Generate table SQL
table_sql = TableEmitter(model=CustomerModel).emit()

# Generate function SQL
function_sql = FunctionEmitter(
    name="update_customer_status",
    params=[
        {"name": "customer_id", "type": "TEXT"},
        {"name": "new_status", "type": "TEXT"}
    ],
    return_type="INTEGER",
    body="UPDATE customer SET status = new_status WHERE id = customer_id; RETURN 1;",
    language="plpgsql"
).emit()

# Generate trigger SQL
trigger_sql = TriggerEmitter(
    name="customer_update_trigger",
    table="customer",
    events=["INSERT", "UPDATE"],
    timing="AFTER",
    function="log_customer_changes",
    for_each="ROW"
).emit()

# Generate security SQL
security_sql = SecurityEmitter(
    table="customer",
    policy_name="customer_access_policy",
    using_expr="(user_id = current_user_id())",
    check_expr="(user_id = current_user_id())"
).emit()

# Generate grants SQL
grants_sql = GrantsEmitter(
    table="customer",
    privileges=["SELECT", "INSERT", "UPDATE"],
    roles=["app_user", "app_admin"]
).emit()

# Combine all SQL
complete_sql = f"""
-- Create table
{table_sql}

-- Create function
{function_sql}

-- Create trigger
{trigger_sql}

-- Create security policy
{security_sql}

-- Grant permissions
{grants_sql}
"""

print(complete_sql)
```

## Best Practices

1. **Use Emitters Instead of Raw SQL**: Prefer using emitters over writing raw SQL to ensure consistency and maintainability.

2. **Separate Concerns**: Use different emitters for different types of database objects.

3. **Validate SQL**: Test the generated SQL to ensure it's correct and follows your database's requirements.

4. **Use Migrations**: Combine emitters with a migration system to manage database schema changes.

5. **Document Generated SQL**: Add comments to explain the purpose and behavior of generated SQL.

6. **Leverage PostgreSQL Features**: Use PostgreSQL-specific features when appropriate.

7. **Test Edge Cases**: Test SQL generation with special characters, long names, and other edge cases.

8. **Reuse Common Patterns**: Create helper functions for common SQL generation patterns.

9. **Handle Errors**: Implement error handling for SQL execution errors.

10. **Version Control**: Store generated SQL in version control to track changes.