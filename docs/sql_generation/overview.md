# SQL Generation System Overview

The SQL Generation system in uno provides a robust and flexible approach for generating and executing SQL statements for various PostgreSQL database objects. This system allows you to create complex SQL without writing raw SQL strings, ensuring consistency, maintainability, and type safety.

## Key Components

The SQL Generation system consists of several key components:

### 1. SQLEmitter

The foundation of the SQL generation system is the `SQLEmitter` base class, which provides:

- SQL statement generation from model properties
- SQL execution with proper transaction handling
- Error handling and logging
- Observer pattern for SQL operation monitoring
- Support for dependency injection

### 2. SQLStatement

`SQLStatement` represents a single SQL statement with metadata:

- SQL text to be executed
- Statement type (function, trigger, index, etc.)
- Name for identification and tracking
- Dependencies on other statements

### 3. SQL Builders

Builders provide a fluent interface for creating SQL statements:

- `SQLFunctionBuilder`: For PostgreSQL functions
- `SQLTriggerBuilder`: For database triggers
- `SQLIndexBuilder`: For table indexes
- And more specialized builders

### 4. Statement Registry

The `SQLConfigRegistry` provides a registration system for SQL configuration classes:

- Registration of SQL configuration classes
- Retrieval of registered configurations
- Batch execution of all registered configurations

## When to Use

The SQL Generation system is ideal for:

1. **Database Schema Initialization**: Creating tables, functions, and triggers during application startup
2. **Dynamic SQL Generation**: Creating SQL based on runtime configuration
3. **Complex PostgreSQL Features**: Working with advanced PostgreSQL features like row-level security, functions, and triggers
4. **Database Migrations**: Generating SQL for schema migrations
5. **Custom Database Logic**: Implementing business logic directly in the database

## Basic Usage

### Using SQLEmitter

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType

# Create a custom emitter
class MyCustomEmitter(SQLEmitter):
    # Properties will be converted to SQL statements
    create_function_example: str = """
    CREATE OR REPLACE FUNCTION public.example_function()
    RETURNS INTEGER
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN 1;
    END;
    $$;
    """
    
    create_trigger_example: str = """
    CREATE OR REPLACE TRIGGER example_trigger
    AFTER INSERT ON example_table
    FOR EACH ROW
    EXECUTE FUNCTION public.example_function();
    """

# Create an instance and emit SQL
emitter = MyCustomEmitter()
with get_db_connection() as connection:
    emitter.emit_sql(connection)
```

### Using SQL Builders

```python
from uno.sql.builders.function import SQLFunctionBuilder

# Create a function using the builder
function_sql = (
    SQLFunctionBuilder()
    .with_schema("public")
    .with_name("calculate_total")
    .with_args("order_id text, include_tax boolean DEFAULT true")
    .with_return_type("numeric")
    .with_body("""
    DECLARE
        total numeric;
    BEGIN
        SELECT SUM(price * quantity) INTO total
        FROM order_items
        WHERE order_id = order_id;
        
        IF include_tax THEN
            total := total * 1.1;  -- 10% tax
        END IF;
        
        RETURN total;
    END;
    """)
    .build()
)

print(function_sql)
```

### Registering and Using SQL Configs

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.registry import SQLConfigRegistry

# Create a config class
class MyDatabaseSetup(SQLEmitter):
    create_example_function: str = """
    CREATE OR REPLACE FUNCTION public.example_function()
    RETURNS INTEGER
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN 1;
    END;
    $$;
    """

# Register the config
SQLConfigRegistry.register(MyDatabaseSetup)

# Later, emit all registered configs
SQLConfigRegistry.emit_all(connection)
```

## Advanced Features

### 1. Statement Dependencies

You can define dependencies between SQL statements to ensure proper execution order:

```python
from uno.sql.statement import SQLStatement, SQLStatementType

# Create statements with dependencies
create_table = SQLStatement(
    name="create_example_table",
    type=SQLStatementType.TABLE,
    sql="CREATE TABLE example_table (id SERIAL PRIMARY KEY, name TEXT);"
)

create_function = SQLStatement(
    name="create_audit_function",
    type=SQLStatementType.FUNCTION,
    sql="CREATE FUNCTION log_changes() RETURNS TRIGGER AS $$ BEGIN ... END; $$ LANGUAGE plpgsql;",
    depends_on=["create_example_table"]  # This will execute after create_table
)
```

### 2. Observer Pattern

You can register observers to monitor SQL operations:

```python
from uno.sql.observers import BaseObserver

# Create a custom observer
class SQLLogger(BaseObserver):
    def on_sql_generated(self, emitter_name, statements):
        print(f"Generated SQL from {emitter_name}: {len(statements)} statements")
        
    def on_sql_executed(self, emitter_name, statements, duration):
        print(f"Executed SQL from {emitter_name} in {duration:.2f}s")
        
    def on_sql_error(self, emitter_name, statements, error):
        print(f"Error executing SQL from {emitter_name}: {error}")

# Register the observer with an emitter class
SQLEmitter.register_observer(SQLLogger())
```

### 3. Dry Run Mode

You can generate SQL without executing it:

```python
# Generate SQL without executing
statements = emitter.emit_sql(connection, dry_run=True)

# Print statements for review
for statement in statements:
    print(f"{statement.name} ({statement.type.value}):")
    print(statement.sql)
    print()
```

### 4. Template Formatting

You can use templates with variable substitution:

```python
from uno.sql.emitter import SQLEmitter

class TemplateEmitter(SQLEmitter):
    def generate_sql(self):
        # Format a template with variables
        create_schema_sql = self.format_sql_template(
            "CREATE SCHEMA IF NOT EXISTS {schema_name};"
        )
        
        create_table_sql = self.format_sql_template(
            """
            CREATE TABLE {schema_name}.{table_name} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_by TEXT NOT NULL REFERENCES {schema_name}.users(id)
            );
            """,
            table_name="customers"
        )
        
        # Return statements
        return [
            SQLStatement(name="create_schema", type=SQLStatementType.SCHEMA, sql=create_schema_sql),
            SQLStatement(name="create_table", type=SQLStatementType.TABLE, sql=create_table_sql)
        ]
```

## Common SQL Generation Patterns

### 1. Database Initialization

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType

class DatabaseInitializer(SQLEmitter):
    # Create schema
    create_schema: str = "CREATE SCHEMA IF NOT EXISTS app;"
    
    # Create extension
    create_extension: str = "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
    
    # Create tables
    create_users_table: str = """
    CREATE TABLE IF NOT EXISTS app.users (
        id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    create_items_table: str = """
    CREATE TABLE IF NOT EXISTS app.items (
        id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
        name TEXT NOT NULL,
        user_id TEXT NOT NULL REFERENCES app.users(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Initialize with connection configuration
    def __init__(self, connection_config=None):
        super().__init__(connection_config=connection_config)

# Use the initializer
initializer = DatabaseInitializer()
initializer.emit_with_connection()
```

### 2. Creating Functions with Builders

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.builders.function import SQLFunctionBuilder
from uno.sql.statement import SQLStatement, SQLStatementType

class FunctionEmitter(SQLEmitter):
    def generate_sql(self):
        # Use builder to create a function
        update_timestamp_func = (
            SQLFunctionBuilder()
            .with_schema("public")
            .with_name("update_timestamp")
            .with_return_type("TRIGGER")
            .with_body("""
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            """)
            .with_language("plpgsql")
            .with_volatility("STABLE")
            .build()
        )
        
        # Return as a statement
        return [
            SQLStatement(
                name="update_timestamp_function",
                type=SQLStatementType.FUNCTION,
                sql=update_timestamp_func
            )
        ]
```

### 3. Creating Triggers with Builders

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.builders.trigger import SQLTriggerBuilder
from uno.sql.statement import SQLStatement, SQLStatementType

class TriggerEmitter(SQLEmitter):
    def generate_sql(self):
        # Use builder to create a trigger
        timestamp_trigger = (
            SQLTriggerBuilder()
            .with_schema("public")
            .with_table("users")
            .with_name("update_timestamp_trigger")
            .with_function("update_timestamp")
            .with_timing("BEFORE")
            .with_operation("UPDATE")
            .with_for_each("ROW")
            .build()
        )
        
        # Return as a statement
        return [
            SQLStatement(
                name="users_timestamp_trigger",
                type=SQLStatementType.TRIGGER,
                sql=timestamp_trigger
            )
        ]
```

### 4. Row-Level Security (RLS) Policies

```python
from uno.sql.emitter import SQLEmitter

class SecurityPolicyEmitter(SQLEmitter):
    enable_rls: str = """
    ALTER TABLE app.documents ENABLE ROW LEVEL SECURITY;
    """
    
    create_policy: str = """
    CREATE POLICY documents_user_policy ON app.documents
    FOR ALL
    TO authenticated
    USING (owner_id = current_user_id());
    """
    
    create_admin_policy: str = """
    CREATE POLICY documents_admin_policy ON app.documents
    FOR ALL
    TO admin
    USING (true);
    """
```

### 5. Batch SQL Execution with Connection Management

```python
from uno.sql.emitter import SQLEmitter
from uno.database.config import ConnectionConfig

# Create emitters
schema_emitter = SchemaEmitter()
table_emitter = TableEmitter()
function_emitter = FunctionEmitter()
policy_emitter = SecurityPolicyEmitter()

# Create connection config
config = ConnectionConfig(
    db_name="myapp",
    db_user_pw="password",
    db_driver="postgresql+psycopg2"
)

# Execute in sequence with the same connection
for emitter in [schema_emitter, table_emitter, function_emitter, policy_emitter]:
    emitter.emit_with_connection(config=config)
```

## Core SQL Emitter Types

### Table Creation Emitters

These emitters generate SQL for creating and managing database tables.

```python
from uno.sql.emitter import SQLEmitter

class TableEmitter(SQLEmitter):
    create_example_table: str = """
    CREATE TABLE IF NOT EXISTS app.example (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    create_timestamp_trigger: str = """
    CREATE TRIGGER update_timestamp
    BEFORE UPDATE ON app.example
    FOR EACH ROW
    EXECUTE FUNCTION app.update_timestamp();
    """
```

### Function Emitters

These emitters generate SQL for PostgreSQL functions.

```python
from uno.sql.emitter import SQLEmitter

class FunctionEmitter(SQLEmitter):
    create_update_timestamp: str = """
    CREATE OR REPLACE FUNCTION app.update_timestamp()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$;
    """
    
    create_generate_id: str = """
    CREATE OR REPLACE FUNCTION app.generate_id(prefix TEXT)
    RETURNS TEXT
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN prefix || '_' || gen_random_uuid()::text;
    END;
    $$;
    """
```

### Security and Permission Emitters

These emitters handle security-related SQL, including roles, permissions, and row-level security.

```python
from uno.sql.emitter import SQLEmitter

class SecurityEmitter(SQLEmitter):
    create_roles: str = """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_reader') THEN
            CREATE ROLE app_reader;
        END IF;
        
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_writer') THEN
            CREATE ROLE app_writer;
        END IF;
    END
    $$;
    """
    
    grant_permissions: str = """
    GRANT USAGE ON SCHEMA app TO app_reader, app_writer;
    GRANT SELECT ON ALL TABLES IN SCHEMA app TO app_reader;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO app_writer;
    """
    
    enable_rls: str = """
    ALTER TABLE app.documents ENABLE ROW LEVEL SECURITY;
    """
```

### Event Store Emitters

These emitters create tables and functions for implementing event sourcing.

```python
from uno.sql.emitter import SQLEmitter

class EventStoreEmitter(SQLEmitter):
    create_events_table: str = """
    CREATE TABLE IF NOT EXISTS app.events (
        id SERIAL PRIMARY KEY,
        aggregate_id TEXT NOT NULL,
        aggregate_type TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_data JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        
        -- Indices for efficient querying
        INDEX idx_events_aggregate_id (aggregate_id),
        INDEX idx_events_aggregate_type (aggregate_type),
        INDEX idx_events_event_type (event_type)
    );
    """
    
    create_append_event: str = """
    CREATE OR REPLACE FUNCTION app.append_event(
        p_aggregate_id TEXT,
        p_aggregate_type TEXT,
        p_event_type TEXT,
        p_event_data JSONB
    )
    RETURNS INTEGER
    LANGUAGE plpgsql
    AS $$
    DECLARE
        event_id INTEGER;
    BEGIN
        INSERT INTO app.events (
            aggregate_id, aggregate_type, event_type, event_data
        ) VALUES (
            p_aggregate_id, p_aggregate_type, p_event_type, p_event_data
        )
        RETURNING id INTO event_id;
        
        RETURN event_id;
    END;
    $$;
    """
```

### Database Merge Function Emitters

These emitters create merge functions for advanced upsert operations using PostgreSQL 16's MERGE command.

```python
from uno.sql.emitter import SQLEmitter

class MergeFunctionEmitter(SQLEmitter):
    create_merge_record: str = """
    CREATE OR REPLACE FUNCTION app.merge_user_record(p_data JSONB)
    RETURNS JSONB
    LANGUAGE plpgsql
    AS $$
    DECLARE
        v_id TEXT;
        v_email TEXT;
        v_result JSONB;
        v_action TEXT;
    BEGIN
        -- Extract key fields
        v_id := p_data->>'id';
        v_email := p_data->>'email';
        
        -- Perform the merge operation
        MERGE INTO app.users AS target
        USING (SELECT v_id AS id, v_email AS email) AS source
        ON target.id = source.id
        WHEN MATCHED THEN
            UPDATE SET
                name = COALESCE(p_data->>'name', target.name),
                updated_at = NOW()
        WHEN NOT MATCHED THEN
            INSERT (id, email, name)
            VALUES (
                v_id,
                v_email,
                p_data->>'name'
            )
        RETURNING *, 
            CASE
                WHEN xmax::text = '0' THEN 'inserted'
                ELSE 'updated'
            END AS merge_action
        INTO v_result, v_action;
        
        -- Add the action to the result
        v_result := v_result || jsonb_build_object('_action', v_action);
        
        RETURN v_result;
    END;
    $$;
    """
```

### Vector Search Emitters

These emitters create tables and functions for vector search operations using pgvector.

```python
from uno.sql.emitter import SQLEmitter

class VectorEmitter(SQLEmitter):
    create_extension: str = """
    CREATE EXTENSION IF NOT EXISTS vector;
    """
    
    create_documents_table: str = """
    CREATE TABLE IF NOT EXISTS app.documents (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        embedding vector(1536),
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    create_search_function: str = """
    CREATE OR REPLACE FUNCTION app.search_documents(
        query_embedding vector,
        match_threshold FLOAT DEFAULT 0.7,
        match_count INT DEFAULT 10
    )
    RETURNS TABLE (
        id TEXT,
        content TEXT,
        metadata JSONB,
        similarity FLOAT
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            d.id,
            d.content,
            d.metadata,
            1 - (d.embedding <=> query_embedding) AS similarity
        FROM
            app.documents d
        WHERE
            1 - (d.embedding <=> query_embedding) > match_threshold
        ORDER BY
            d.embedding <=> query_embedding
        LIMIT
            match_count;
    END;
    $$;
    """
```

## Best Practices

### 1. Organize SQL by Function

Group SQL statements by their purpose or functionality:

```python
class UserManagementSQL(SQLEmitter):
    """SQL for user management operations."""
    create_users_table: str = "..."
    create_user_audit_function: str = "..."
    create_user_audit_trigger: str = "..."

class ProductManagementSQL(SQLEmitter):
    """SQL for product management operations."""
    create_products_table: str = "..."
    create_product_categories_table: str = "..."
    create_product_search_function: str = "..."
```

### 2. Use Builders for Complex SQL

Use builders for complex SQL statements to ensure correctness:

```python
# Create a complex function with the builder
function_sql = (
    SQLFunctionBuilder()
    .with_schema("app")
    .with_name("process_order")
    .with_args("order_id TEXT, user_id TEXT")
    .with_return_type("JSONB")
    .with_body("""
    DECLARE
        v_result JSONB;
    BEGIN
        -- Check user permissions
        PERFORM app.verify_user_can_process_orders(user_id);
        
        -- Process the order
        UPDATE app.orders
        SET status = 'processing',
            processed_at = NOW(),
            processed_by = user_id
        WHERE id = order_id
        RETURNING to_jsonb(orders.*) INTO v_result;
        
        -- Log the operation
        INSERT INTO app.audit_log (
            user_id, action, resource_type, resource_id, details
        ) VALUES (
            user_id, 'process', 'order', order_id, v_result
        );
        
        RETURN v_result;
    END;
    """)
    .with_language("plpgsql")
    .as_security_definer()
    .build()
)
```

### 3. Use Dependency Injection

Utilize dependency injection for better testability:

```python
from uno.dependencies import get_sql_emitter_factory, get_sql_execution_service
from uno.sql.emitter import SQLEmitter

class MyService:
    def __init__(
        self,
        sql_factory=Depends(get_sql_emitter_factory),
        sql_executor=Depends(get_sql_execution_service)
    ):
        self.sql_factory = sql_factory
        self.sql_executor = sql_executor
    
    def initialize_database(self):
        # Create emitters through the factory
        schema_emitter = self.sql_factory.create_emitter(SchemaEmitter)
        table_emitter = self.sql_factory.create_emitter(TableEmitter)
        
        # Execute them
        self.sql_executor.execute_emitter(schema_emitter)
        self.sql_executor.execute_emitter(table_emitter)
```

### 4. Use Template Formatting

Use template formatting for reusable SQL patterns:

```python
class TableEmitter(SQLEmitter):
    def generate_audit_table_sql(self, source_table: str) -> str:
        return self.format_sql_template(
            """
            CREATE TABLE {schema_name}.{audit_table} (
                id SERIAL PRIMARY KEY,
                operation CHAR(1) NOT NULL,
                record_id TEXT NOT NULL,
                old_data JSONB,
                new_data JSONB,
                changed_by TEXT,
                changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            audit_table=f"{source_table}_audit"
        )
```

### 5. Test Generated SQL

Write tests for your SQL emitters:

```python
def test_function_emitter():
    # Create the emitter
    emitter = FunctionEmitter()
    
    # Generate SQL without executing
    statements = emitter.emit_sql(connection, dry_run=True)
    
    # Check that expected statements are generated
    assert len(statements) > 0
    assert any(s.name == "create_update_timestamp" for s in statements)
    
    # Validate SQL syntax (if possible in your test environment)
    for statement in statements:
        # Use a linter or parser to validate SQL syntax
        assert is_valid_sql(statement.sql)
```

### 6. Document SQL Behavior

Add comments to explain SQL behavior:

```python
class UserManagementSQL(SQLEmitter):
    create_user_audit_trigger: str = """
    -- Trigger: audit_user_changes
    --
    -- Purpose: Tracks all changes to user records for compliance and security auditing.
    -- Stores previous and new values as JSONB for flexible querying.
    -- Captures user ID making the change from session variable.
    --
    -- Note: Requires the 'current_user_id()' function to be defined.
    
    CREATE OR REPLACE TRIGGER audit_user_changes
    AFTER INSERT OR UPDATE OR DELETE ON app.users
    FOR EACH ROW
    EXECUTE FUNCTION app.log_user_changes();
    """
```

### 7. Use Transactions Appropriately

Ensure proper transaction handling:

```python
# For a set of statements that need to be atomic
with get_db_connection() as connection:
    with connection.begin():  # Start a transaction
        schema_emitter.emit_sql(connection)
        table_emitter.emit_sql(connection)
        function_emitter.emit_sql(connection)
        # If any emitter fails, the entire transaction will be rolled back
```

## SQLEmitter Class Reference

### Core Methods

| Method | Description |
|--------|-------------|
| `generate_sql()` | Generates SQL statements based on emitter properties |
| `execute_sql(connection, statements)` | Executes SQL statements on a connection |
| `emit_sql(connection, dry_run=False)` | Generates and optionally executes SQL statements |
| `emit_with_connection(dry_run=False, ...)` | Executes SQL with a new connection |
| `format_sql_template(template, **kwargs)` | Formats an SQL template with variables |
| `register_observer(observer)` | Registers an observer for SQL operations |

### Properties

| Property | Description |
|----------|-------------|
| `table` | The table for which SQL is being generated |
| `connection_config` | Database connection configuration |
| `config` | Configuration settings |
| `observers` | List of SQL operation observers |

## SQLStatement Class Reference

### Properties

| Property | Description |
|----------|-------------|
| `name` | Unique identifier for the statement |
| `type` | Type of SQL statement (function, trigger, etc.) |
| `sql` | The actual SQL statement text |
| `depends_on` | List of statement names this statement depends on |

### Statement Types

| Type | Description |
|------|-------------|
| `FUNCTION` | SQL function |
| `TRIGGER` | Database trigger |
| `INDEX` | Table index |
| `CONSTRAINT` | Table constraint |
| `GRANT` | Permission grant |
| `VIEW` | Database view |
| `PROCEDURE` | SQL procedure |
| `TABLE` | Database table |
| `ROLE` | Database role |
| `SCHEMA` | Database schema |
| `EXTENSION` | PostgreSQL extension |
| `DATABASE` | Database |
| `INSERT` | Data insertion |

## SQL Builder Classes Reference

### SQLFunctionBuilder

| Method | Description |
|--------|-------------|
| `with_schema(schema)` | Sets the schema for the function |
| `with_name(name)` | Sets the name of the function |
| `with_args(args)` | Sets the function arguments |
| `with_return_type(return_type)` | Sets the return type |
| `with_body(body)` | Sets the function body |
| `with_language(language)` | Sets the function language |
| `with_volatility(volatility)` | Sets the function volatility |
| `as_security_definer()` | Sets the function to use SECURITY DEFINER |
| `build()` | Builds the SQL function statement |

### SQLTriggerBuilder

| Method | Description |
|--------|-------------|
| `with_schema(schema)` | Sets the schema for the trigger |
| `with_table(table_name)` | Sets the table for the trigger |
| `with_name(trigger_name)` | Sets the name of the trigger |
| `with_function(function_name)` | Sets the function to be called |
| `with_timing(timing)` | Sets the timing (BEFORE, AFTER, INSTEAD OF) |
| `with_operation(operation)` | Sets the operations (INSERT, UPDATE, DELETE) |
| `with_for_each(for_each)` | Sets for_each (ROW, STATEMENT) |
| `build()` | Builds the SQL trigger statement |

### SQLIndexBuilder

| Method | Description |
|--------|-------------|
| `with_schema(schema)` | Sets the schema for the index |
| `with_table(table_name)` | Sets the table for the index |
| `with_name(index_name)` | Sets the name of the index |
| `with_columns(columns)` | Sets the columns to index |
| `with_method(method)` | Sets the index method (btree, hash, gist, gin) |
| `with_unique(is_unique)` | Sets whether the index is unique |
| `build()` | Builds the SQL index statement |

## Next Steps

- [SQL Emitters](emitters.md): Detailed documentation of specific SQL emitters
- [SQL Statements](statement.md): Learn more about SQL statements and their properties
- [SQL Registry](registry.md): Understanding the SQL registry system
- [SQL Examples](../examples/sql_examples.py): Complete examples of SQL generation