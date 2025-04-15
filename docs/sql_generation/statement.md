# SQL Statement

The `SQLStatement` class in uno represents a SQL statement with metadata about its type, dependencies, and execution order. It provides a structured way to manage schema initialization, modifications, and database operations.

## Overview

In uno, SQL statements are represented as structured entities with metadata to handle:

- SQL DDL/DML code generation
- Statement dependencies and execution order
- Statement categorization by type (functions, triggers, indexes, etc.)
- Registration and discovery of SQL configurations

## Core Components

### SQLStatement

The `SQLStatement` class represents a single SQL statement with execution metadata:

```python
from uno.sql.statement import SQLStatement, SQLStatementType

# Create a SQL function statement
function_statement = SQLStatement(
    name="create_audit_log_function",
    type=SQLStatementType.FUNCTION,
    sql="""
    CREATE OR REPLACE FUNCTION audit_log()
    RETURNS TRIGGER AS $$
    BEGIN
        INSERT INTO audit_log (table_name, record_id, action)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP);
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
    depends_on=["create_audit_log_table"]
)
```

The `SQLStatement` class has the following attributes:

- `name`: Unique identifier for the statement
- `type`: Type of SQL statement (function, trigger, etc.)
- `sql`: The actual SQL statement to execute
- `depends_on`: List of statement names this statement depends on

### SQLStatementType

The `SQLStatementType` enum categorizes SQL statements by their purpose:

```python
class SQLStatementType(Enum):
    """Types of SQL statements that can be emitted."""
    FUNCTION = "function"
    TRIGGER = "trigger"
    INDEX = "index"
    CONSTRAINT = "constraint"
    GRANT = "grant"
    VIEW = "view"
    PROCEDURE = "procedure"
    TABLE = "table"
    ROLE = "role"
    SCHEMA = "schema"
    EXTENSION = "extension"
    DATABASE = "database"
    INSERT = "insert"
```

## SQL Configuration Registry

The `SQLConfigRegistry` manages the registration and execution of SQL configuration classes:

```python
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig

# Create a new SQL configuration class
class AuditLogConfig(SQLConfig):
    def get_statements(self):
        return [
            SQLStatement(
                name="create_audit_log_table",
                type=SQLStatementType.TABLE,
                sql="""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    record_id UUID NOT NULL,
                    action TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            ),
            SQLStatement(
                name="create_audit_log_function",
                type=SQLStatementType.FUNCTION,
                sql="""
                CREATE OR REPLACE FUNCTION audit_log()
                RETURNS TRIGGER AS $$
                BEGIN
                    INSERT INTO audit_log (table_name, record_id, action)
                    VALUES (TG_TABLE_NAME, NEW.id, TG_OP);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """,
                depends_on=["create_audit_log_table"]
            )
        ]

# Register the configuration class
SQLConfigRegistry.register(AuditLogConfig)

# Emit all SQL statements
SQLConfigRegistry.emit_all()
```

### Registry Operations

The `SQLConfigRegistry` provides the following operations:

- `register(config_class)`: Register a SQLConfig class
- `get(name)`: Get a SQLConfig class by name
- `all()`: Get all registered SQLConfig classes
- `emit_all()`: Emit SQL for all registered SQLConfig classes

## Common Statement Types

### Function Statements

```python
function_statement = SQLStatement(
    name="create_merge_function", 
    type=SQLStatementType.FUNCTION,
    sql="""
    CREATE OR REPLACE FUNCTION merge_record(
        target_table TEXT,
        primary_key TEXT,
        primary_value TEXT,
        data JSONB
    ) RETURNS JSONB AS $$
    DECLARE
        column_exists BOOLEAN;
        column_name TEXT;
        column_value TEXT;
        columns TEXT[];
        values TEXT[];
        update_parts TEXT[];
        sql_statement TEXT;
        result JSONB;
    BEGIN
        -- Check if record exists
        EXECUTE format('SELECT EXISTS(SELECT 1 FROM %I WHERE %I = %L)', 
                      target_table, primary_key, primary_value)
        INTO column_exists;
        
        -- Extract columns and values from JSONB
        FOR column_name, column_value IN SELECT * FROM jsonb_each_text(data)
        LOOP
            columns := array_append(columns, column_name);
            values := array_append(values, quote_literal(column_value));
            
            IF column_name != primary_key THEN
                update_parts := array_append(update_parts, 
                                          format('%I = %s', column_name, quote_literal(column_value)));
            END IF;
        END LOOP;
        
        -- Build and execute SQL statement
        IF column_exists THEN
            -- UPDATE
            sql_statement := format('UPDATE %I SET %s WHERE %I = %L RETURNING to_jsonb(%I.*)', 
                                 target_table, 
                                 array_to_string(update_parts, ', '), 
                                 primary_key, 
                                 primary_value,
                                 target_table);
        ELSE
            -- INSERT
            sql_statement := format('INSERT INTO %I (%s) VALUES (%s) RETURNING to_jsonb(%I.*)', 
                                 target_table, 
                                 array_to_string(columns, ', '), 
                                 array_to_string(values, ', '),
                                 target_table);
        END IF;
        
        EXECUTE sql_statement INTO result;
        RETURN result;
    END;
    $$ LANGUAGE plpgsql;
    """
)
```

### Trigger Statements

```python
trigger_statement = SQLStatement(
    name="create_audit_trigger",
    type=SQLStatementType.TRIGGER,
    sql="""
    CREATE TRIGGER audit_customer_changes
    AFTER INSERT OR UPDATE ON customer
    FOR EACH ROW
    EXECUTE FUNCTION audit_log();
    """,
    depends_on=["create_audit_log_function"]
)
```

### Index Statements

```python
index_statement = SQLStatement(
    name="create_customer_email_index",
    type=SQLStatementType.INDEX,
    sql="""
    CREATE INDEX IF NOT EXISTS idx_customer_email
    ON customer (email);
    """
)
```

### Grant Statements

```python
grant_statement = SQLStatement(
    name="grant_customer_access",
    type=SQLStatementType.GRANT,
    sql="""
    GRANT SELECT, INSERT, UPDATE ON customer TO app_user;
    """
)
```

## Statement Dependencies and Execution Order

The `SQLStatement` class uses the `depends_on` attribute to define dependencies:

```python
statements = [
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
        name="create_order_table",
        type=SQLStatementType.TABLE,
        sql="""
        CREATE TABLE IF NOT EXISTS order (
            id UUID PRIMARY KEY,
            customer_id UUID NOT NULL REFERENCES customer(id),
            total DECIMAL(10,2) NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        depends_on=["create_customer_table"]
    ),
    SQLStatement(
        name="create_order_item_table",
        type=SQLStatementType.TABLE,
        sql="""
        CREATE TABLE IF NOT EXISTS order_item (
            id UUID PRIMARY KEY,
            order_id UUID NOT NULL REFERENCES order(id),
            product_id UUID NOT NULL,
            quantity INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        depends_on=["create_order_table"]
    )
]
```

The framework uses the dependencies to determine the execution order:

1. `create_customer_table` (no dependencies)
2. `create_order_table` (depends on customer table)
3. `create_order_item_table` (depends on order table)

## Best Practices

1. **Statement Organization**: Group related statements in dedicated configuration classes.

2. **Naming Conventions**: Use clear, descriptive names for statements.

3. **Dependencies**: Properly define dependencies to ensure correct execution order.

4. **Error Handling**: Implement proper exception handling when executing statements.

5. **Idempotency**: Make statements idempotent (use IF NOT EXISTS, OR REPLACE, etc.).

6. **Versioning**: Use a versioning scheme for schema changes.

7. **Documentation**: Document the purpose and relationships between statements.

8. **Testing**: Test statements with sample data to verify correct behavior.

9. **Security**: Use parameterized statements to prevent SQL injection.

10. **Isolation**: Keep database implementation details isolated from business logic.

## SQL Configuration Patterns

### Schema Initialization

```python
class SchemaInitConfig(SQLConfig):
    def get_statements(self):
        return [
            SQLStatement(
                name="create_schemas",
                type=SQLStatementType.SCHEMA,
                sql="""
                CREATE SCHEMA IF NOT EXISTS app;
                CREATE SCHEMA IF NOT EXISTS audit;
                """
            ),
            SQLStatement(
                name="create_extensions",
                type=SQLStatementType.EXTENSION,
                sql="""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE EXTENSION IF NOT EXISTS "pgcrypto";
                """
            )
        ]
```

### Audit Trail Configuration

```python
class AuditTrailConfig(SQLConfig):
    def get_statements(self):
        return [
            SQLStatement(
                name="create_audit_schema",
                type=SQLStatementType.SCHEMA,
                sql="CREATE SCHEMA IF NOT EXISTS audit;"
            ),
            SQLStatement(
                name="create_audit_tables",
                type=SQLStatementType.TABLE,
                sql="""
                CREATE TABLE IF NOT EXISTS audit.log (
                    id SERIAL PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    data JSONB,
                    user_id UUID,
                    timestamp TIMESTAMP DEFAULT NOW()
                );
                """,
                depends_on=["create_audit_schema"]
            ),
            SQLStatement(
                name="create_audit_function",
                type=SQLStatementType.FUNCTION,
                sql="""
                CREATE OR REPLACE FUNCTION audit.log_changes()
                RETURNS TRIGGER AS $$
                DECLARE
                    data JSONB;
                BEGIN
                    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                        data = to_jsonb(NEW);
                    ELSE
                        data = to_jsonb(OLD);
                    END IF;
                    
                    INSERT INTO audit.log(
                        table_name, 
                        record_id, 
                        action, 
                        data, 
                        user_id
                    )
                    VALUES (
                        TG_TABLE_NAME,
                        data->>'id',
                        TG_OP,
                        data,
                        current_setting('app.user_id', true)::UUID
                    );
                    
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;
                """,
                depends_on=["create_audit_tables"]
            )
        ]
```

### Security Configuration

```python
class SecurityConfig(SQLConfig):
    def get_statements(self):
        return [
            SQLStatement(
                name="create_roles",
                type=SQLStatementType.ROLE,
                sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
                        CREATE ROLE app_user;
                    END IF;
                    
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_admin') THEN
                        CREATE ROLE app_admin;
                    END IF;
                END
                $$;
                """
            ),
            SQLStatement(
                name="create_row_level_security",
                type=SQLStatementType.FUNCTION,
                sql="""
                -- Enable RLS on tables
                ALTER TABLE customer ENABLE ROW LEVEL SECURITY;
                ALTER TABLE order ENABLE ROW LEVEL SECURITY;
                
                -- Create policies
                CREATE POLICY customer_access ON customer
                    USING (tenant_id = current_setting('app.tenant_id', true)::UUID);
                    
                CREATE POLICY order_access ON order
                    USING (tenant_id = current_setting('app.tenant_id', true)::UUID);
                """
            ),
            SQLStatement(
                name="grant_permissions",
                type=SQLStatementType.GRANT,
                sql="""
                -- Grant permissions to app_user
                GRANT USAGE ON SCHEMA public TO app_user;
                GRANT SELECT, INSERT, UPDATE ON customer TO app_user;
                GRANT SELECT, INSERT, UPDATE ON order TO app_user;
                
                -- Grant permissions to app_admin
                GRANT USAGE ON SCHEMA public TO app_admin;
                GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;
                """
            )
        ]
```

### Graph Integration

```python
class GraphConfig(SQLConfig):
    def get_statements(self):
        return [
            SQLStatement(
                name="create_age_extension",
                type=SQLStatementType.EXTENSION,
                sql="CREATE EXTENSION IF NOT EXISTS age;"
            ),
            SQLStatement(
                name="create_graph",
                type=SQLStatementType.FUNCTION,
                sql="""
                SELECT create_graph('app_graph');
                """,
                depends_on=["create_age_extension"]
            ),
            SQLStatement(
                name="create_vertex_labels",
                type=SQLStatementType.FUNCTION,
                sql="""
                SELECT create_vlabel('app_graph', 'Customer');
                SELECT create_vlabel('app_graph', 'Order');
                SELECT create_vlabel('app_graph', 'Product');
                """,
                depends_on=["create_graph"]
            ),
            SQLStatement(
                name="create_edge_labels",
                type=SQLStatementType.FUNCTION,
                sql="""
                SELECT create_elabel('app_graph', 'PLACED');
                SELECT create_elabel('app_graph', 'CONTAINS');
                """,
                depends_on=["create_vertex_labels"]
            )
        ]
```