# DB Manager

> **New Name**: This component was previously called `SchemaManager` but has been renamed to `DBManager` to better reflect its purpose of managing database objects rather than Pydantic schemas.

The `DBManager` is a central component in uno's database architecture that executes DDL (Data Definition Language) statements and manages database objects like schemas, functions, and triggers. It provides a bridge between SQL generation through emitters and actual database execution.

## Key Features

- Execute DDL statements and SQL scripts with built-in validation
- Verify existence of database objects (tables, functions, triggers, etc.)
- Create and manage database schemas and extensions
- Integrate with SQLEmitters for SQL generation
- Support both direct SQL execution and emitter-based execution
- Manage database users, roles, and privileges
- Prevent potentially dangerous operations through SQL validation
- Integration with dependency injection

## Basic Usage

### Direct SQL Execution

```python
from uno.dependencies import get_db_manager

# Get the database manager
db_manager = get_db_manager()

# Execute a DDL statement
db_manager.execute_ddl("""
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN```

NEW.updated_at = NOW();
RETURN NEW;
```
END;
$$ LANGUAGE plpgsql;
""")
```

### Using with SQL Emitters

```python
from uno.dependencies import get_db_manager
from uno.sql.emitters.function import FunctionEmitter

# Get the database manager
db_manager = get_db_manager()

# Create a function emitter
function_emitter = FunctionEmitter(```

name="update_timestamp",
params=[],
return_type="TRIGGER",
body="""
BEGIN```

NEW.updated_at = NOW();
RETURN NEW;
```
END;
""",
language="plpgsql"
```
)

# Execute the emitter
db_manager.execute_from_emitter(function_emitter)
```

### Checking Object Existence

```python
from uno.dependencies import get_db_manager

# Get the database manager
db_manager = get_db_manager()

# Check if a function exists
if not db_manager.function_exists("update_timestamp", schema="public"):```

# Create the function if it doesn't exist
db_manager.execute_ddl("""
CREATE OR REPLACE FUNCTION public.update_timestamp() 
RETURNS TRIGGER AS $$
BEGIN```

NEW.updated_at = NOW();
RETURN NEW;
```
END;
$$ LANGUAGE plpgsql;
""")
```
```

### Managing Schemas and Extensions

```python
from uno.dependencies import get_db_manager

# Get the database manager
db_manager = get_db_manager()

# Create a schema
db_manager.create_schema("analytics")

# Create extensions
db_manager.create_extension("pgcrypto")
db_manager.create_extension("uuid-ossp", schema="analytics")
```

## Advanced Usage

### Using Multiple Emitters

```python
from uno.dependencies import get_db_manager
from uno.sql.emitters.function import FunctionEmitter
from uno.sql.emitters.trigger import TriggerEmitter

# Get the database manager
db_manager = get_db_manager()

# Create function emitter
function_emitter = FunctionEmitter(```

name="update_timestamp",
params=[],
return_type="TRIGGER",
body="""
BEGIN```

NEW.updated_at = NOW();
RETURN NEW;
```
END;
""",
language="plpgsql"
```
)

# Create trigger emitter
trigger_emitter = TriggerEmitter(```

name="user_timestamp_trigger",
table="users",
events=["INSERT", "UPDATE"],
timing="BEFORE",
function="update_timestamp",
for_each="ROW"
```
)

# Execute both emitters
db_manager.execute_from_emitters([function_emitter, trigger_emitter])
```

### Managing Users and Privileges

```python
from uno.dependencies import get_db_manager

# Get the database manager
db_manager = get_db_manager()

# Create users and roles
db_manager.create_user("app_user", "secure_password", is_superuser=False)
db_manager.create_role("readonly")
db_manager.create_role("readwrite", granted_roles=["readonly"])

# Grant privileges
db_manager.grant_privileges(```

privileges=["SELECT"],
on_object="users",
to_role="readonly",
object_type="TABLE",
schema="public"
```
)

db_manager.grant_privileges(```

privileges=["INSERT", "UPDATE", "DELETE"],
on_object="users",
to_role="readwrite",
object_type="TABLE",
schema="public"
```
)
```

### Database Initialization

```python
from uno.dependencies import get_db_manager
from uno.database.config import ConnectionConfig

# Get the database manager
db_manager = get_db_manager()

# Create database configuration
config = ConnectionConfig(```

db_role="postgres",
db_user_pw="password",
db_host="localhost",
db_port=5432,
db_name="new_database",
db_driver="postgresql+asyncpg",
db_schema="public"
```
)

# Initialize a new database
db_manager.initialize_database(config)
```

## Integration with Emission Registry

The DBManager works seamlessly with the Emission Registry:

```python
from uno.dependencies import get_db_manager
from uno.sql.registry import EmissionRegistry

# Get the database manager
db_manager = get_db_manager()

# Create emission registry
registry = EmissionRegistry()
registry.register_emitter("function", FunctionEmitter)
registry.register_emitter("trigger", TriggerEmitter)

# Create emitters from registry
function_emitter = registry.create_emitter(```

"function",
name="update_timestamp",
params=[],
return_type="TRIGGER",
body="BEGIN NEW.updated_at = NOW(); RETURN NEW; END;",
language="plpgsql"
```
)

trigger_emitter = registry.create_emitter(```

"trigger",```
```

name="user_timestamp_trigger",
table="users",
events=["INSERT", "UPDATE"],
timing="BEFORE",
function="update_timestamp",
for_each="ROW"
```
)

# Execute the emitters
db_manager.execute_from_emitters([function_emitter, trigger_emitter])
```

## API Reference

### Core Methods

- `execute_ddl(ddl: str) -> None`: Execute a DDL statement
- `execute_script(script: str) -> None`: Execute a SQL script with multiple statements
- `execute_from_emitter(emitter: BaseEmitter) -> None`: Execute SQL from an emitter
- `execute_from_emitters(emitters: List[BaseEmitter]) -> None`: Execute SQL from multiple emitters

### Schema Management

- `create_schema(schema_name: str) -> None`: Create a database schema
- `drop_schema(schema_name: str, cascade: bool = False) -> None`: Drop a database schema
- `create_extension(extension_name: str, schema: Optional[str] = None) -> None`: Create a PostgreSQL extension

### Object Verification

- `table_exists(table_name: str, schema: Optional[str] = None) -> bool`: Check if a table exists
- `function_exists(function_name: str, schema: Optional[str] = None) -> bool`: Check if a function exists
- `type_exists(type_name: str, schema: Optional[str] = None) -> bool`: Check if a type exists
- `trigger_exists(trigger_name: str, table_name: str, schema: Optional[str] = None) -> bool`: Check if a trigger exists
- `policy_exists(policy_name: str, table_name: str, schema: Optional[str] = None) -> bool`: Check if a policy exists

### Database Administration

- `initialize_database(config: ConnectionConfig) -> None`: Initialize a new database
- `drop_database(config: ConnectionConfig) -> None`: Drop a database
- `create_user(username: str, password: str, is_superuser: bool = False) -> None`: Create a database user
- `create_role(rolename: str, granted_roles: Optional[List[str]] = None) -> None`: Create a database role
- `grant_privileges(privileges: List[str], on_object: str, to_role: str, object_type: str = "TABLE", schema: Optional[str] = None) -> None`: Grant privileges to a role

## Security Features

The `DBManager` includes several security features to protect against potentially dangerous operations:

### SQL Validation

Before executing any DDL statement, the `DBManager` validates the SQL to prevent certain risky operations:

```python
from uno.dependencies import get_db_manager

db_manager = get_db_manager()

# This will raise a ValueError
try:```

# Attempting to drop a production database is blocked
db_manager.execute_ddl("DROP DATABASE PRODUCTION;")
```
except ValueError as e:```

print(f"Error: {e}")  # Error: Disallowed operation in DDL statement...
```

# This will also raise a ValueError
try:```

# Attempting to grant all privileges to PUBLIC is blocked
db_manager.execute_ddl("GRANT ALL ON ALL TABLES IN SCHEMA public TO PUBLIC;")
```
except ValueError as e:```

print(f"Error: {e}")
```
```

### Protected Operations

The following operations are protected by the validation system:

1. **Production Database Protection**:
   - Dropping production, live, or critical databases 
   - Example: `DROP DATABASE PRODUCTION;`

2. **Critical Extension Protection**:
   - Dropping core extensions like pgcrypto, uuid-ossp, and pg_trgm
   - Example: `DROP EXTENSION PG_CRYPTO;`

3. **Privilege Escalation Protection**:
   - Granting excessive privileges that could be a security risk
   - Example: `GRANT ALL ON ALL TABLES IN SCHEMA public TO PUBLIC;`

4. **Dangerous Statement Protection**:
   - Truncating all tables or creating superusers
   - Example: `CREATE USER admin SUPERUSER;`

### Logging and Auditing

All DDL operations are logged with the following information:
- Statement type (CREATE, ALTER, DROP, etc.)
- Object name and schema
- Success or failure status
- Error messages when applicable

This provides an audit trail for database structure changes.

## Best Practices

1. **Use Emitters**: Prefer using emitters for SQL generation instead of writing raw SQL

2. **Verify Before Creating**: Always check if an object exists before creating it

3. **Use Transactions**: Group related operations to ensure atomic execution

4. **Separate Schemas**: Use separate schemas for different application components

5. **Manage Privileges**: Carefully manage database privileges for security

6. **Handle Errors**: Implement proper error handling for database operations

7. **Log Operations**: Enable logging for audit and debugging purposes

8. **Use Dependency Injection**: Access the DBManager through the dependency injection system

9. **Keep Idempotent**: Design operations to be idempotent when possible

10. **Use with Alembic**: Use DBManager for schema operations not handled by Alembic

## Relationship with Other Components

- **DatabaseProvider**: Provides database connections to the DBManager
- **SQLEmitters**: Generate SQL for the DBManager to execute
- **EmissionRegistry**: Manages and creates emitters for use with the DBManager
- **Alembic**: Handles table creation and migrations, while DBManager handles other database objects

## Migration Guide: SchemaManager to DBManager

If you are migrating from the old `SchemaManager` to the new `DBManager`, follow these steps:

### Code Changes

1. **Update Imports**

```python
# Old
from uno.database.schema_manager import SchemaManager
from uno.dependencies import UnoSchemaManagerProtocol

# New
from uno.database.db_manager import DBManager
from uno.dependencies import UnoDBManagerProtocol
```

2. **Update DI References**

```python
# Old
schema_manager = get_instance(UnoSchemaManagerProtocol)

# New
db_manager = get_instance(UnoDBManagerProtocol)
```

3. **Update Direct Instantiation**

```python
# Old
schema_manager = SchemaManager(connection_provider=connection_provider)

# New
db_manager = DBManager(connection_provider=connection_provider)
```

### Compatibility

The `DBManager` provides the same methods as `SchemaManager` with identical signatures, so your existing code should work with minimal changes. The main differences are:

- Better validation of SQL statements before execution
- Improved logging and error handling
- Better integration with SQL Emitters
- Clearer naming that doesn't conflict with Pydantic schema concepts

## Conclusion

The DBManager is a powerful tool for managing PostgreSQL database objects and executing DDL statements. By integrating with SQLEmitters, it provides a clean, type-safe way to generate and execute complex SQL. With built-in security validation, it helps prevent potentially dangerous operations. Use it for creating functions, triggers, policies, and other database objects that are not handled by Alembic migrations.