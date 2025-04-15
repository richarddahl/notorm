# SQL Emitters Reference

This guide provides detailed documentation on the various SQL emitters available in uno. SQL emitters are powerful components that generate SQL statements for different database objects and operations, abstracting away the complexity of raw SQL while providing a consistent API.

## Emitter Base Classes

### SQLEmitter

The foundation of the SQL generation system is the `SQLEmitter` base class. It provides:

- Automatic conversion of properties to SQL statements
- SQL execution with transaction handling
- Error handling and logging
- Observer pattern for monitoring SQL operations

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType

class CustomEmitter(SQLEmitter):
    """Custom SQL emitter example."""
    
    # Properties that will be converted to SQL statements
    create_function: str = """
    CREATE OR REPLACE FUNCTION public.example()
    RETURNS INTEGER
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN 1;
    END;
    $$;
    """

# Basic usage
emitter = CustomEmitter()
emitter.emit_with_connection()
```

### SQLConfigRegistry

The `SQLConfigRegistry` manages SQL configuration classes, allowing registration and batch execution:

```python
from uno.sql.registry import SQLConfigRegistry
from uno.sql.emitter import SQLEmitter

# Define a config class
class MyDatabaseConfig(SQLEmitter):
    create_schema: str = "CREATE SCHEMA IF NOT EXISTS example;"

# Register the config
SQLConfigRegistry.register(MyDatabaseConfig)

# Later, emit all registered configs
SQLConfigRegistry.emit_all(connection)
```

## Table Creation and Management Emitters

### TableEmitter

Generates SQL for creating database tables based on UnoModel definitions:

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
emitter.emit_with_connection()
```

### TableMergeFunction

Generates a PostgreSQL function for merging records using the MERGE command (PostgreSQL 16+):

```python
from uno.sql.emitters.table import TableMergeFunction
from sqlalchemy import Table, MetaData, Column, String
from sqlalchemy.engine import create_engine

# Define a table
metadata = MetaData()
users = Table(
    'users', metadata,
    Column('id', String, primary_key=True),
    Column('email', String, nullable=False, unique=True),
    Column('name', String, nullable=False)
)

# Create a merge function emitter
emitter = TableMergeFunction(table=users)
emitter.emit_with_connection()

# The generated function can be used like this in PostgreSQL:
# SELECT myschema.merge_users_record('{"id": "123", "email": "user@example.com", "name": "John Doe"}'::jsonb);
```

### RecordVersionAudit

Creates a trigger for automatically versioning records when they change:

```python
from uno.sql.emitters.table import RecordVersionAudit
from sqlalchemy import Table, MetaData, Column, String

# Define a table
metadata = MetaData()
documents = Table(
    'documents', metadata,
    Column('id', String, primary_key=True),
    Column('content', String),
    Column('version', Integer, nullable=False, default=1)
)

# Create a version audit emitter
emitter = RecordVersionAudit(table=documents)
emitter.emit_with_connection()
```

### EnableHistoricalAudit

Creates a history table and trigger for keeping a full audit history of changes:

```python
from uno.sql.emitters.table import EnableHistoricalAudit
from sqlalchemy import Table, MetaData, Column, String

# Define a table
metadata = MetaData()
users = Table(
    'users', metadata,
    Column('id', String, primary_key=True),
    Column('email', String),
    Column('name', String)
)

# Create a historical audit emitter
emitter = EnableHistoricalAudit(
    table=users,
    history_table_name="users_history",
    excluded_columns=["last_login"]
)
emitter.emit_with_connection()
```

## Function and Procedure Emitters

### FunctionEmitter

Creates custom PostgreSQL functions:

```python
from uno.sql.emitters.function import FunctionEmitter

# Create a function emitter
emitter = FunctionEmitter(
    schema="public",
    name="calculate_discount",
    args=[
        {"name": "price", "type": "NUMERIC"},
        {"name": "discount_percent", "type": "NUMERIC"}
    ],
    return_type="NUMERIC",
    body="""
    BEGIN
        RETURN price * (1 - discount_percent / 100);
    END;
    """,
    language="plpgsql",
    volatility="IMMUTABLE"
)
emitter.emit_with_connection()
```

### TableFunctionEmitter

Creates functions that return table results (like views but with parameters):

```python
from uno.sql.emitters.function import TableFunctionEmitter

# Create a table function emitter
emitter = TableFunctionEmitter(
    schema="public",
    name="search_products",
    args=[
        {"name": "search_term", "type": "TEXT"},
        {"name": "category_id", "type": "TEXT", "default": "NULL"}
    ],
    return_columns=[
        {"name": "id", "type": "TEXT"},
        {"name": "name", "type": "TEXT"},
        {"name": "price", "type": "NUMERIC"},
        {"name": "relevance", "type": "FLOAT"}
    ],
    body="""
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.price,
        ts_rank_cd(p.search_vector, to_tsquery('english', search_term)) AS relevance
    FROM
        products p
    WHERE
        p.search_vector @@ to_tsquery('english', search_term)
        AND (category_id IS NULL OR p.category_id = category_id)
    ORDER BY
        relevance DESC;
    """,
    language="plpgsql"
)
emitter.emit_with_connection()
```

## Trigger Emitters

### TriggerEmitter

Creates database triggers that execute functions on table events:

```python
from uno.sql.emitters.trigger import TriggerEmitter

# Create a trigger emitter
emitter = TriggerEmitter(
    schema="public",
    table="users",
    name="update_timestamp_trigger",
    function="update_timestamp",
    timing="BEFORE",
    operation="UPDATE",
    for_each="ROW"
)
emitter.emit_with_connection()
```

### InsertMetaRecordTrigger

Creates a trigger for automatically inserting a meta record before inserting the main record:

```python
from uno.sql.emitters.table import InsertMetaRecordTrigger
from sqlalchemy import Table, MetaData, Column, String

# Define a table
metadata = MetaData()
users = Table(
    'users', metadata,
    Column('id', String, primary_key=True),
    Column('name', String)
)

# Create the trigger emitter
emitter = InsertMetaRecordTrigger(table=users)
emitter.emit_with_connection()
```

## Security and Permission Emitters

### SecurityPolicyEmitter

Creates row-level security policies for tables:

```python
from uno.sql.emitters.security import SecurityPolicyEmitter

# Create a security policy emitter
emitter = SecurityPolicyEmitter(
    schema="app",
    table="documents",
    policy_name="documents_access_policy",
    access_type="ALL",
    role="authenticated",
    using_expr="owner_id = current_user_id()",
    with_check_expr="owner_id = current_user_id()"
)
emitter.emit_with_connection()
```

### GrantsEmitter

Creates GRANT statements for tables, views, functions, etc.:

```python
from uno.sql.emitters.grants import GrantsEmitter

# Create a grants emitter for a table
emitter = GrantsEmitter(
    schema="app",
    object_name="users",
    object_type="TABLE",
    privileges=["SELECT", "INSERT", "UPDATE"],
    roles=["app_user", "app_admin"]
)
emitter.emit_with_connection()

# Create a grants emitter for a function
function_grants = GrantsEmitter(
    schema="app",
    object_name="calculate_total",
    object_type="FUNCTION",
    privileges=["EXECUTE"],
    roles=["app_user"]
)
function_grants.emit_with_connection()
```

### RoleEmitter

Creates database roles and users:

```python
from uno.sql.emitters.security import RoleEmitter

# Create roles emitter
emitter = RoleEmitter(
    roles=[
        {"name": "app_reader", "login": False, "inherit": True},
        {"name": "app_writer", "login": False, "inherit": True},
        {"name": "app_admin", "login": False, "inherit": True}
    ]
)
emitter.emit_with_connection()
```

## Vector Search Emitters

### VectorExtensionEmitter

Creates and configures the pgvector extension:

```python
from uno.sql.emitters.vector import VectorExtensionEmitter

# Create vector extension emitter
emitter = VectorExtensionEmitter()
emitter.emit_with_connection()
```

### VectorTableEmitter

Creates tables with vector columns:

```python
from uno.sql.emitters.vector import VectorTableEmitter

# Create vector table emitter
emitter = VectorTableEmitter(
    schema="app",
    table_name="documents",
    primary_key_column="id",
    content_column="text",
    embedding_column="embedding",
    embedding_dimension=1536,
    metadata_column="metadata",
    index_method="hnsw"  # or "ivfflat" or "ivfflat_hnsw"
)
emitter.emit_with_connection()
```

### VectorSearchEmitter

Creates functions for vector similarity search:

```python
from uno.sql.emitters.vector import VectorSearchEmitter

# Create vector search emitter
emitter = VectorSearchEmitter(
    schema="app",
    table_name="documents",
    embedding_column="embedding",
    primary_key_column="id",
    content_column="text",
    metadata_column="metadata"
)
emitter.emit_with_connection()
```

## Graph Database Emitters

### GraphEmitter

Creates functions and triggers for managing a graph representation of relational data:

```python
from uno.sql.emitters.graph import GraphEmitter

# Create graph emitter
emitter = GraphEmitter(
    schema="app",
    table_name="users",
    node_label="User",
    properties=["id", "name", "email"],
    relationship_columns=[
        {"column": "manager_id", "target_table": "users", "rel_type": "REPORTS_TO"}
    ]
)
emitter.emit_with_connection()
```

### GraphPathEmitter

Creates functions for finding paths in a graph:

```python
from uno.sql.emitters.graph import GraphPathEmitter

# Create graph path emitter
emitter = GraphPathEmitter(
    schema="app"
)
emitter.emit_with_connection()
```

## Event Store Emitters

### EventStoreEmitter

Creates tables and functions for event sourcing:

```python
from uno.sql.emitters.event_store import EventStoreEmitter

# Create event store emitter
emitter = EventStoreEmitter(
    schema="app",
    table_name="events"
)
emitter.emit_with_connection()
```

### AggregateSnapshotEmitter

Creates tables and functions for storing snapshots of aggregate state:

```python
from uno.sql.emitters.event_store import AggregateSnapshotEmitter

# Create snapshot emitter
emitter = AggregateSnapshotEmitter(
    schema="app",
    table_name="aggregate_snapshots"
)
emitter.emit_with_connection()
```

## Database Administration Emitters

### DatabaseEmitter

Creates databases and essential roles:

```python
from uno.sql.emitters.database import DatabaseEmitter

# Create database emitter
emitter = DatabaseEmitter(
    db_name="my_application",
    admin_role="my_application_admin",
    writer_role="my_application_writer",
    reader_role="my_application_reader"
)
emitter.emit_with_connection()
```

### SchemaEmitter

Creates database schemas with proper permissions:

```python
from uno.sql.emitters.database import SchemaEmitter

# Create schema emitter
emitter = SchemaEmitter(
    schemas=["public", "app", "audit"]
)
emitter.emit_with_connection()
```

### ExtensionEmitter

Creates database extensions:

```python
from uno.sql.emitters.database import ExtensionEmitter

# Create extensions emitter
emitter = ExtensionEmitter(
    extensions=["pgcrypto", "uuid-ossp", "ltree"]
)
emitter.emit_with_connection()
```

## Using Emitters with Dependency Injection

uno provides a dependency injection system for working with SQL emitters, offering better testability and consistency:

```python
from fastapi import Depends
from uno.dependencies import get_sql_emitter_factory, get_sql_execution_service
from uno.sql.emitters.table import TableEmitter

class DatabaseService:
    def __init__(
        self,
        emitter_factory=Depends(get_sql_emitter_factory),
        sql_executor=Depends(get_sql_execution_service)
    ):
        self.emitter_factory = emitter_factory
        self.sql_executor = sql_executor
        
    async def initialize_tables(self, models):
        """Initialize database tables for the given models."""
        for model in models:
            # Create an emitter instance
            emitter = self.emitter_factory.create_emitter(
                TableEmitter,
                model=model
            )
            
            # Execute the emitter
            await self.sql_executor.execute_emitter_async(emitter)
```

## SQL Emitter Factory

The `SQLEmitterFactory` creates and manages emitter instances:

```python
from uno.dependencies import get_sql_emitter_factory
from uno.sql.emitters.security import SecurityPolicyEmitter

# Get the factory
factory = get_sql_emitter_factory()

# Create an emitter
policy_emitter = factory.create_emitter(
    SecurityPolicyEmitter,
    schema="app",
    table="documents",
    policy_name="documents_access_policy",
    using_expr="owner_id = current_user_id()"
)

# Register a named emitter for reuse
factory.register_emitter(
    "documents_security_policy",
    lambda: SecurityPolicyEmitter(
        schema="app",
        table="documents",
        policy_name="documents_access_policy",
        using_expr="owner_id = current_user_id()"
    )
)

# Later, get the registered emitter
registered_emitter = factory.get_emitter("documents_security_policy")
```

## SQL Execution Service

The `SQLExecutionService` provides a standardized way to execute emitters:

```python
from uno.dependencies import get_sql_execution_service

# Get the service
executor = get_sql_execution_service()

# Execute an emitter
executor.execute_emitter(emitter)

# Execute SQL directly
executor.execute_sql("CREATE SCHEMA IF NOT EXISTS app;")

# Execute SQL with parameters
executor.execute_sql(
    "INSERT INTO app.users (id, name) VALUES (:id, :name)",
    {"id": "123", "name": "John Doe"}
)

# Execute a batch of emitters
executor.execute_batch([
    schema_emitter,
    table_emitter,
    function_emitter
])
```

## Combining Multiple Emitters

For complex database setups, you can create a composite emitter that combines multiple emitters:

```python
from uno.sql.emitter import SQLEmitter

class ApplicationDatabaseSetup(SQLEmitter):
    """Complete database setup for the application."""
    
    def __init__(self, connection_config=None):
        super().__init__(connection_config=connection_config)
        
        # Create child emitters
        self.database_emitter = DatabaseEmitter(
            db_name="my_application"
        )
        
        self.schema_emitter = SchemaEmitter(
            schemas=["app", "audit"]
        )
        
        self.extensions_emitter = ExtensionEmitter(
            extensions=["pgcrypto", "uuid-ossp"]
        )
        
        self.table_emitters = [
            TableEmitter(model=UserModel),
            TableEmitter(model=ProductModel),
            TableEmitter(model=OrderModel)
        ]
        
        self.security_emitters = [
            SecurityPolicyEmitter(
                schema="app",
                table="users",
                policy_name="users_access_policy",
                using_expr="id = current_user_id() OR is_admin()"
            ),
            SecurityPolicyEmitter(
                schema="app",
                table="orders",
                policy_name="orders_access_policy",
                using_expr="user_id = current_user_id() OR is_admin()"
            )
        ]
    
    def emit_with_connection(self, dry_run=False, **kwargs):
        """Execute all emitters in sequence."""
        # Execute database and schema setup first
        self.database_emitter.emit_with_connection(dry_run=dry_run, **kwargs)
        self.schema_emitter.emit_with_connection(dry_run=dry_run, **kwargs)
        self.extensions_emitter.emit_with_connection(dry_run=dry_run, **kwargs)
        
        # Execute table creation
        for emitter in self.table_emitters:
            emitter.emit_with_connection(dry_run=dry_run, **kwargs)
        
        # Execute security policies
        for emitter in self.security_emitters:
            emitter.emit_with_connection(dry_run=dry_run, **kwargs)
```

## Custom SQL Emitters

Creating your own custom SQL emitters is straightforward:

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType

class CustomEmitter(SQLEmitter):
    """Custom SQL emitter for a specific purpose."""
    
    def __init__(self, schema: str, table_name: str, **kwargs):
        super().__init__(**kwargs)
        self.schema = schema
        self.table_name = table_name
    
    def generate_sql(self):
        """Generate custom SQL statements."""
        statements = []
        
        # Generate a custom function
        function_sql = self.format_sql_template(
            """
            CREATE OR REPLACE FUNCTION {schema}.custom_function()
            RETURNS TRIGGER
            LANGUAGE plpgsql
            AS $$
            BEGIN
                -- Custom implementation
                RETURN NEW;
            END;
            $$;
            """,
            schema=self.schema
        )
        
        statements.append(SQLStatement(
            name="custom_function",
            type=SQLStatementType.FUNCTION,
            sql=function_sql
        ))
        
        # Generate a custom trigger
        trigger_sql = self.format_sql_template(
            """
            CREATE OR REPLACE TRIGGER custom_trigger
            BEFORE INSERT OR UPDATE ON {schema}.{table_name}
            FOR EACH ROW
            EXECUTE FUNCTION {schema}.custom_function();
            """,
            schema=self.schema,
            table_name=self.table_name
        )
        
        statements.append(SQLStatement(
            name="custom_trigger",
            type=SQLStatementType.TRIGGER,
            sql=trigger_sql
        ))
        
        return statements
```

## Advanced SQL Emitter Features

### Property-Based SQL Generation

The simplest way to define SQL statements is using class properties:

```python
class SimpleEmitter(SQLEmitter):
    create_function: str = """
    CREATE OR REPLACE FUNCTION app.example()
    RETURNS INTEGER
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN 1;
    END;
    $$;
    """
    
    create_trigger: str = """
    CREATE TRIGGER example_trigger
    AFTER INSERT ON app.example_table
    FOR EACH ROW
    EXECUTE FUNCTION app.example();
    """
```

### Dynamic SQL Generation

For more complex cases, you can override the `generate_sql()` method:

```python
class DynamicEmitter(SQLEmitter):
    def __init__(self, table_names: list[str], **kwargs):
        super().__init__(**kwargs)
        self.table_names = table_names
    
    def generate_sql(self):
        statements = []
        
        for table_name in self.table_names:
            audit_function_sql = self.format_sql_template(
                """
                CREATE OR REPLACE FUNCTION app.audit_{table_name}()
                RETURNS TRIGGER
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    INSERT INTO app.audit_log (
                        table_name, record_id, action, old_data, new_data
                    ) VALUES (
                        '{table_name}',
                        CASE 
                            WHEN TG_OP = 'DELETE' THEN OLD.id 
                            ELSE NEW.id 
                        END,
                        TG_OP,
                        CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END,
                        CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END
                    );
                    
                    RETURN CASE 
                        WHEN TG_OP = 'DELETE' THEN OLD 
                        ELSE NEW 
                    END;
                END;
                $$;
                """,
                table_name=table_name
            )
            
            statements.append(SQLStatement(
                name=f"audit_{table_name}_function",
                type=SQLStatementType.FUNCTION,
                sql=audit_function_sql
            ))
            
            audit_trigger_sql = self.format_sql_template(
                """
                CREATE OR REPLACE TRIGGER audit_{table_name}_trigger
                AFTER INSERT OR UPDATE OR DELETE ON app.{table_name}
                FOR EACH ROW
                EXECUTE FUNCTION app.audit_{table_name}();
                """,
                table_name=table_name
            )
            
            statements.append(SQLStatement(
                name=f"audit_{table_name}_trigger",
                type=SQLStatementType.TRIGGER,
                sql=audit_trigger_sql
            ))
        
        return statements
```

### Builder Integration

You can use SQL builders in your emitters for more complex SQL:

```python
from uno.sql.emitter import SQLEmitter
from uno.sql.builders.function import SQLFunctionBuilder
from uno.sql.builders.trigger import SQLTriggerBuilder
from uno.sql.statement import SQLStatement, SQLStatementType

class BuilderBasedEmitter(SQLEmitter):
    def __init__(self, schema: str, table_name: str, **kwargs):
        super().__init__(**kwargs)
        self.schema = schema
        self.table_name = table_name
    
    def generate_sql(self):
        statements = []
        
        # Use function builder
        function_builder = self.get_function_builder()
        function_sql = (
            function_builder
            .with_schema(self.schema)
            .with_name(f"update_{self.table_name}_timestamp")
            .with_return_type("TRIGGER")
            .with_body("""
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            """)
            .build()
        )
        
        statements.append(SQLStatement(
            name=f"update_{self.table_name}_timestamp_function",
            type=SQLStatementType.FUNCTION,
            sql=function_sql
        ))
        
        # Use trigger builder
        from uno.sql.builders.trigger import SQLTriggerBuilder
        
        trigger_builder = SQLTriggerBuilder()
        trigger_sql = (
            trigger_builder
            .with_schema(self.schema)
            .with_table(self.table_name)
            .with_name(f"update_{self.table_name}_timestamp_trigger")
            .with_function(f"update_{self.table_name}_timestamp")
            .with_timing("BEFORE")
            .with_operation("UPDATE")
            .with_for_each("ROW")
            .build()
        )
        
        statements.append(SQLStatement(
            name=f"update_{self.table_name}_timestamp_trigger",
            type=SQLStatementType.TRIGGER,
            sql=trigger_sql
        ))
        
        return statements
```

## Best Practices

### 1. Use the Right Emitter Type

Choose the appropriate emitter type for each database operation:

- **TableEmitter**: For creating tables from UnoModel definitions
- **FunctionEmitter**: For creating database functions and procedures
- **TriggerEmitter**: For creating database triggers
- **SecurityPolicyEmitter**: For creating row-level security policies
- **GrantsEmitter**: For creating GRANT statements
- **Custom emitters**: For specific domain requirements

### 2. Use Builders for Complex Statements

Use builders for complex SQL statements to ensure correctness and readability:

```python
from uno.sql.builders.function import SQLFunctionBuilder

function_sql = (
    SQLFunctionBuilder()
    .with_schema("app")
    .with_name("complex_function")
    .with_args("param1 TEXT, param2 INTEGER")
    .with_return_type("JSONB")
    .with_body("""
    DECLARE
        v_result JSONB;
    BEGIN
        -- Complex implementation
        SELECT to_jsonb(subquery) INTO v_result
        FROM (
            SELECT * FROM some_table
            WHERE some_condition = param1
            AND other_condition > param2
        ) AS subquery;
        
        RETURN v_result;
    END;
    """)
    .with_language("plpgsql")
    .with_volatility("STABLE")
    .build()
)
```

### 3. Organize Emitters by Domain

Group related emitters together based on domain concerns:

```python
# User domain emitters
class UserSchemaEmitter(SQLEmitter):
    # User-related database schema setup
    pass

class UserFunctionsEmitter(SQLEmitter):
    # User-related functions
    pass

# Product domain emitters
class ProductSchemaEmitter(SQLEmitter):
    # Product-related database schema setup
    pass

class ProductFunctionsEmitter(SQLEmitter):
    # Product-related functions
    pass
```

### 4. Use Dependency Injection

Use dependency injection for better testability and flexibility:

```python
class DatabaseService:
    def __init__(
        self,
        emitter_factory=Depends(get_sql_emitter_factory),
        sql_executor=Depends(get_sql_execution_service),
        db_manager=Depends(get_db_manager)
    ):
        self.emitter_factory = emitter_factory
        self.sql_executor = sql_executor
        self.db_manager = db_manager
    
    async def setup_database(self):
        # Create emitters
        schema_emitter = self.emitter_factory.create_emitter(SchemaEmitter)
        extensions_emitter = self.emitter_factory.create_emitter(ExtensionEmitter)
        
        # Execute emitters
        async with self.db_manager.transaction():
            await self.sql_executor.execute_emitter_async(schema_emitter)
            await self.sql_executor.execute_emitter_async(extensions_emitter)
```

### 5. Use Template Formatting

Use template formatting for dynamic SQL:

```python
def generate_audit_trigger(self, table_name: str) -> str:
    return self.format_sql_template(
        """
        CREATE OR REPLACE TRIGGER audit_{table_name}_trigger
        AFTER INSERT OR UPDATE OR DELETE ON {schema_name}.{table_name}
        FOR EACH ROW
        EXECUTE FUNCTION {schema_name}.log_changes();
        """,
        table_name=table_name
    )
```

### 6. Transaction Management

Ensure proper transaction management for atomic operations:

```python
from uno.database.db_manager import get_db_manager

# Get the database manager
db_manager = get_db_manager()

# Execute multiple emitters in a transaction
async with db_manager.transaction():
    await sql_executor.execute_emitter_async(schema_emitter)
    await sql_executor.execute_emitter_async(table_emitter)
    await sql_executor.execute_emitter_async(function_emitter)
    # If any emitter fails, the transaction is rolled back
```

### 7. Error Handling

Implement proper error handling for SQL operations:

```python
try:
    result = emitter.emit_with_connection()
except SQLEmitterError as e:
    # Handle SQL emitter errors
    logger.error(f"SQL emitter error: {e}")
    # Log detailed information
    logger.debug(f"Error context: {e.context}")
    # Retry or fallback strategy
    if "already exists" in str(e):
        # Ignore already exists errors
        pass
    else:
        # Re-raise for other errors
        raise
```

### 8. Testing SQL Emitters

Write tests for your SQL emitters:

```python
def test_custom_emitter():
    # Create a test database connection
    with test_db_connection() as conn:
        # Create the emitter with dry run mode
        emitter = CustomEmitter(schema="test", table_name="example")
        statements = emitter.emit_sql(conn, dry_run=True)
        
        # Verify statements were generated correctly
        assert len(statements) == 2
        assert statements[0].name == "custom_function"
        assert statements[1].name == "custom_trigger"
        
        # Check SQL content
        assert "CREATE OR REPLACE FUNCTION test.custom_function()" in statements[0].sql
        assert "CREATE OR REPLACE TRIGGER custom_trigger" in statements[1].sql
```

## Next Steps

- [SQL Generation Overview](overview.md): Go back to the overview
- [SQL Statements](statement.md): Learn more about SQL statements
- [SQL Registry](registry.md): Understanding the SQL registry system
- [Advanced SQL Patterns](../database/pg_optimizer.md): Using PostgreSQL-specific features