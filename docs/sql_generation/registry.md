# SQL Configuration Registry

The `SQLConfigRegistry` class in uno manages the registration and execution of SQL configuration classes. It provides a centralized system for managing and applying SQL statements across the application.

## Overview

The `SQLConfigRegistry` provides:

- Central registration of SQL configuration classes
- Discovery of configuration classes
- Ordered execution of SQL statements based on dependencies
- Dependency resolution for SQL statements
- Execution of SQL statements against the database

## SQL Configuration Classes

The registry works with `SQLConfig` classes, which provide SQL statements for various database objects:

```python
from uno.sql.config import SQLConfig
from uno.sql.statement import SQLStatement, SQLStatementType

class CustomerConfig(SQLConfig):
    """SQL configuration for customer-related database objects."""
    
    def get_statements(self):
        """Get all SQL statements for customer functionality."""
        return [
            SQLStatement(
                name="create_customer_table",
                type=SQLStatementType.TABLE,
                sql="""
                CREATE TABLE IF NOT EXISTS customer (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            ),
            SQLStatement(
                name="create_customer_index",
                type=SQLStatementType.INDEX,
                sql="""
                CREATE INDEX IF NOT EXISTS idx_customer_email
                ON customer (email);
                """,
                depends_on=["create_customer_table"]
            ),
            SQLStatement(
                name="create_customer_audit_trigger",
                type=SQLStatementType.TRIGGER,
                sql="""
                CREATE TRIGGER audit_customer_changes
                AFTER INSERT OR UPDATE ON customer
                FOR EACH ROW
                EXECUTE FUNCTION audit_log();
                """,
                depends_on=["create_customer_table", "create_audit_log_function"]
            )
        ]
```

## Basic Usage

### Registering Configuration Classes

```python
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig

# Create SQL configuration classes
class CustomerConfig(SQLConfig):
    # Configuration for customer tables, functions, etc.
    # ...

class OrderConfig(SQLConfig):
    # Configuration for order tables, functions, etc.
    # ...

class AuditConfig(SQLConfig):
    # Configuration for audit tables, functions, etc.
    # ...

# Register configuration classes
SQLConfigRegistry.register(CustomerConfig)
SQLConfigRegistry.register(OrderConfig)
SQLConfigRegistry.register(AuditConfig)
```

### Retrieving Configuration Classes

```python
from uno.sql.registry import SQLConfigRegistry

# Get a specific configuration class
customer_config_class = SQLConfigRegistry.get("CustomerConfig")

# Get all registered configuration classes
all_configs = SQLConfigRegistry.all()
```

### Emitting SQL Statements

```python
from uno.sql.registry import SQLConfigRegistry
from uno.database.engine.sync import SyncEngineFactory
from uno.database.config import ConnectionConfig

# Emit SQL for all registered configuration classes
SQLConfigRegistry.emit_all()

# Emit SQL with custom connection
connection_config = ConnectionConfig(
    host="localhost",
    port=5432,
    database="app_db",
    user="app_user",
    password="app_password"
)

engine_factory = SyncEngineFactory()

# Emit SQL with specific configuration
SQLConfigRegistry.emit_all(
    config=connection_config,
    engine_factory=engine_factory,
    exclude=["AuditConfig"]  # Skip certain configurations
)
```

## Advanced Usage

### Custom SQL Configuration

```python
from uno.sql.config import SQLConfig
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.database.config import ConnectionConfig

class CustomConfig(SQLConfig):
    """Custom SQL configuration with special handling."""
    
    def __init__(self, connection_config=None, engine_factory=None):
        super().__init__(connection_config, engine_factory)
        self.schema_name = connection_config.schema if connection_config else "public"
    
    def get_statements(self):
        """Get statements with custom schema."""
        return [
            SQLStatement(
                name="create_custom_table",
                type=SQLStatementType.TABLE,
                sql=f"""
                CREATE TABLE IF NOT EXISTS {self.schema_name}.custom (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    data JSONB
                );
                """
            )
        ]
    
    def before_emit(self, connection):
        """Perform pre-emission actions."""
        # Create schema if needed
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name};")
    
    def after_emit(self, connection):
        """Perform post-emission actions."""
        # Grant permissions
        connection.execute(f"GRANT SELECT ON {self.schema_name}.custom TO app_user;")

# Register the custom configuration
SQLConfigRegistry.register(CustomConfig)
```

### Multi-Environment Configuration

```python
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig
from uno.database.config import ConnectionConfig

# Create environment-specific configurations
dev_config = ConnectionConfig(
    host="localhost",
    port=5432,
    database="app_dev",
    user="app_dev_user",
    password="dev_password",
    schema="dev"
)

prod_config = ConnectionConfig(
    host="db.example.com",
    port=5432,
    database="app_prod",
    user="app_prod_user",
    password="prod_password",
    schema="prod"
)

# Emit SQL for development environment
SQLConfigRegistry.emit_all(config=dev_config)

# Emit SQL for production environment
SQLConfigRegistry.emit_all(config=prod_config)
```

### Dependency Resolution

```python
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig
from uno.sql.statement import SQLStatement, SQLStatementType

class SchemaConfig(SQLConfig):
    """Configuration for database schema."""
    
    def get_statements(self):
        return [
            SQLStatement(
                name="create_app_schema",
                type=SQLStatementType.SCHEMA,
                sql="CREATE SCHEMA IF NOT EXISTS app;"
            )
        ]

class TableConfig(SQLConfig):
    """Configuration for database tables."""
    
    def get_statements(self):
        return [
            SQLStatement(
                name="create_customer_table",
                type=SQLStatementType.TABLE,
                sql="""
                CREATE TABLE IF NOT EXISTS app.customer (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL
                );
                """,
                depends_on=["create_app_schema"]  # Depends on schema creation
            ),
            SQLStatement(
                name="create_order_table",
                type=SQLStatementType.TABLE,
                sql="""
                CREATE TABLE IF NOT EXISTS app.order (
                    id UUID PRIMARY KEY,
                    customer_id UUID REFERENCES app.customer(id)
                );
                """,
                depends_on=["create_customer_table"]  # Depends on customer table
            )
        ]

# Register configurations
SQLConfigRegistry.register(SchemaConfig)
SQLConfigRegistry.register(TableConfig)

# Emit SQL in the correct order based on dependencies
SQLConfigRegistry.emit_all()
```

## Integration Patterns

### Application Initialization

```python
from uno.sql.registry import SQLConfigRegistry
from uno.database.engine.sync import SyncEngineFactory
from uno.database.config import ConnectionConfig

def initialize_database():
    """Initialize the database schema and objects."""
    # Load connection configuration
    connection_config = ConnectionConfig.from_env()
    
    # Create engine factory
    engine_factory = SyncEngineFactory()
    
    # Register SQL configurations
    register_sql_configurations()
    
    # Emit SQL to initialize database
    SQLConfigRegistry.emit_all(
        config=connection_config,
        engine_factory=engine_factory
    )

def register_sql_configurations():
    """Register all SQL configurations."""
    from app.sql.schema import SchemaConfig
    from app.sql.users import UserConfig
    from app.sql.audit import AuditConfig
    from app.sql.security import SecurityConfig
    
    SQLConfigRegistry.register(SchemaConfig)
    SQLConfigRegistry.register(UserConfig)
    SQLConfigRegistry.register(AuditConfig)
    SQLConfigRegistry.register(SecurityConfig)

# Initialize database during application startup
initialize_database()
```

### Migration Support

```python
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig
from uno.sql.statement import SQLStatement, SQLStatementType

class MigrationConfig(SQLConfig):
    """Configuration for database migrations."""
    
    def __init__(self, connection_config=None, engine_factory=None, version=None):
        super().__init__(connection_config, engine_factory)
        self.version = version or "latest"
    
    def get_statements(self):
        """Get migration statements based on version."""
        if self.version == "v1":
            return self.get_v1_statements()
        elif self.version == "v2":
            return self.get_v2_statements()
        else:
            return self.get_latest_statements()
    
    def get_v1_statements(self):
        """Get V1 migration statements."""
        return [
            SQLStatement(
                name="create_v1_tables",
                type=SQLStatementType.TABLE,
                sql="-- V1 schema creation statements..."
            )
        ]
    
    def get_v2_statements(self):
        """Get V2 migration statements."""
        return [
            SQLStatement(
                name="alter_v1_to_v2",
                type=SQLStatementType.TABLE,
                sql="-- V1 to V2 migration statements...",
                depends_on=["create_v1_tables"]
            )
        ]
    
    def get_latest_statements(self):
        """Get latest migration statements."""
        return [
            SQLStatement(
                name="create_latest_tables",
                type=SQLStatementType.TABLE,
                sql="-- Latest schema creation statements..."
            )
        ]

# Migrate to specific version
migration_config = MigrationConfig(version="v2")
SQLConfigRegistry.register(migration_config)
SQLConfigRegistry.emit_all()
```

## Best Practices

1. **Organize by Domain**: Group related SQL statements in domain-specific configuration classes.

2. **Define Dependencies**: Properly specify dependencies between SQL statements to ensure correct execution order.

3. **Use Idempotent Statements**: Make SQL statements idempotent (IF NOT EXISTS, OR REPLACE, etc.) for safe re-execution.

4. **Validate Before Execution**: Validate SQL statements before execution to catch errors early.

5. **Handle Errors**: Implement proper error handling for SQL execution failures.

6. **Separate Environment Concerns**: Use configuration to adapt SQL for different environments.

7. **Version Control**: Keep SQL configurations under version control alongside application code.

8. **Document Purpose**: Add clear documentation for each SQL configuration class.

9. **Test SQL Execution**: Write tests to verify SQL execution and results.

10. **Use Transactions**: Execute related SQL statements within transactions for atomicity.

## Common SQL Configuration Patterns

### Feature-Based Configurations

Organize SQL configurations around application features:

```python
class UserManagementConfig(SQLConfig):
    """SQL configuration for user management feature."""
    # ...

class ReportingConfig(SQLConfig):
    """SQL configuration for reporting feature."""
    # ...

class NotificationConfig(SQLConfig):
    """SQL configuration for notification feature."""
    # ...
```

### Layer-Based Configurations

Organize SQL configurations around application layers:

```python
class SchemaConfig(SQLConfig):
    """SQL configuration for database schemas."""
    # ...

class TableConfig(SQLConfig):
    """SQL configuration for database tables."""
    # ...

class FunctionConfig(SQLConfig):
    """SQL configuration for database functions."""
    # ...

class SecurityConfig(SQLConfig):
    """SQL configuration for database security."""
    # ...
```

### Module-Based Configurations

Organize SQL configurations around application modules:

```python
class CoreConfig(SQLConfig):
    """SQL configuration for core module."""
    # ...

class CustomerConfig(SQLConfig):
    """SQL configuration for customer module."""
    # ...

class OrderConfig(SQLConfig):
    """SQL configuration for order module."""
    # ...

class InventoryConfig(SQLConfig):
    """SQL configuration for inventory module."""
    # ...
```