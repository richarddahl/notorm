# SQL API

The Uno SQL module provides a comprehensive framework for generating, executing, and managing SQL statements for database operations. It includes support for functions, triggers, and other SQL objects.

## Key Features

- **SQL Generation**: Generate SQL statements for various database objects
- **SQL Execution**: Execute SQL statements with proper error handling
- **Function and Trigger Support**: Create and manage PostgreSQL functions and triggers
- **Domain-Driven Design**: Rich domain model with clear separation of concerns
- **Configuration Management**: Manage SQL configurations with emitters and connection settings
- **Dependency Injection**: Full integration with Uno's dependency injection system

## Core Concepts

### SQL Statements

SQL statements represent database operations like creating functions, triggers, etc. They include metadata such as name, type, and dependencies on other statements.

### SQL Emitters

Emitters are responsible for generating SQL statements based on configuration. They support various types of statements like functions, triggers, indexes, etc.

### SQL Functions

Functions are PostgreSQL stored procedures that can be called from SQL statements. The SQL module provides support for creating, managing, and deploying functions to the database.

### SQL Triggers

Triggers are database objects that execute when specific events occur on a table. The SQL module provides support for creating, managing, and deploying triggers to the database.

### SQL Configurations

Configurations group together emitters and connection settings for executing SQL statements. They provide a way to organize and reuse SQL generation logic.

## API Usage

### Working with SQL Statements

```python
from uno.sql import (
    create_sql_statement, 
    execute_sql_statement,
    SQLStatementType
)

# Create a SQL statement
statement_result = await create_sql_statement(
    name="create_user_table",
    statement_type=SQLStatementType.TABLE,
    sql="""
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
)

# Execute the statement
if statement_result.is_success():
    statement = statement_result.value
    execution_result = await execute_sql_statement(statement, connection)
    
    if execution_result.is_success():
        print(f"Statement executed successfully in {execution_result.value.duration_ms}ms")
```

### Creating Functions

```python
from uno.sql import create_sql_function

# Create a function
function_result = await create_sql_function(
    schema="public",
    name="record_audit",
    body="""
    DECLARE
        record_id uuid;
    BEGIN
        INSERT INTO audit_logs (table_name, action, user_id)
        VALUES (TG_TABLE_NAME, TG_OP, current_setting('app.user_id', TRUE))
        RETURNING id INTO record_id;
        
        RETURN NEW;
    END;
    """,
    args="",
    return_type="TRIGGER",
    language="plpgsql",
    volatility="STABLE",
    security_definer=True
)

if function_result.is_success():
    function = function_result.value
    print(f"Function {function.schema}.{function.name} created")
```

### Creating Triggers

```python
from uno.sql import create_sql_trigger

# Create a trigger
trigger_result = await create_sql_trigger(
    schema="public",
    name="users_audit_trigger",
    table="users",
    function_name="record_audit",
    events=["INSERT", "UPDATE", "DELETE"],
    for_each="ROW"
)

if trigger_result.is_success():
    trigger = trigger_result.value
    print(f"Trigger {trigger.schema}.{trigger.name} created for table {trigger.table}")
```

### Working with Database Connections

```python
from uno.sql import create_database_connection, execute_sql

# Create connection info
connection_info_result = await create_database_connection(
    db_name="myapp",
    db_user="app_user",
    db_host="localhost",
    db_port=5432,
    db_schema="public"
)

if connection_info_result.is_success():
    connection_info = connection_info_result.value
    
    # Execute SQL using the connection info
    result = await execute_sql(
        connection_info=connection_info,
        sql="SELECT COUNT(*) FROM users",
        params={}
    )
    
    if result.is_success():
        print(f"User count: {result.value[0]['count']}")
```

### Advanced Service Usage

```python
from uno.sql import (
    get_sql_statement_service,
    get_sql_function_service,
    get_sql_trigger_service
)

# Get the statement service
statement_service = await get_sql_statement_service()

# List all statements of a specific type
statements_result = await statement_service.get_statements_by_type(SQLStatementType.FUNCTION)
if statements_result.is_success():
    for statement in statements_result.value:
        print(f"Function statement: {statement.name}")

# Get the function service
function_service = await get_sql_function_service()

# Get all functions in a schema
functions_result = await function_service.get_functions_by_schema("public")
if functions_result.is_success():
    for function in functions_result.value:
        print(f"Function: {function.name}")

# Get the trigger service
trigger_service = await get_sql_trigger_service()

# Get all triggers for a table
triggers_result = await trigger_service.get_triggers_by_table("public", "users")
if triggers_result.is_success():
    for trigger in triggers_result.value:
        print(f"Trigger: {trigger.name}")
```

## HTTP API

The SQL module provides a RESTful API for managing SQL statements, emitters, functions, triggers, and configurations. The API is available at `/api/sql`.

### SQL Statements

- `GET /api/sql/statements`: List all SQL statements
- `GET /api/sql/statements/{id}`: Get a SQL statement by ID
- `GET /api/sql/statements/by-name/{name}`: Get a SQL statement by name
- `POST /api/sql/statements`: Create a new SQL statement
- `PUT /api/sql/statements/{id}`: Update a SQL statement
- `DELETE /api/sql/statements/{id}`: Delete a SQL statement

### SQL Emitters

- `GET /api/sql/emitters`: List all SQL emitters
- `GET /api/sql/emitters/{id}`: Get a SQL emitter by ID
- `GET /api/sql/emitters/by-name/{name}`: Get a SQL emitter by name
- `POST /api/sql/emitters`: Create a new SQL emitter
- `PUT /api/sql/emitters/{id}`: Update a SQL emitter
- `DELETE /api/sql/emitters/{id}`: Delete a SQL emitter
- `POST /api/sql/emitters/{id}/generate`: Generate statements using an emitter

### SQL Configurations

- `GET /api/sql/configurations`: List all SQL configurations
- `GET /api/sql/configurations/{id}`: Get a SQL configuration by ID
- `GET /api/sql/configurations/by-name/{name}`: Get a SQL configuration by name
- `POST /api/sql/configurations`: Create a new SQL configuration
- `PUT /api/sql/configurations/{id}`: Update a SQL configuration
- `DELETE /api/sql/configurations/{id}`: Delete a SQL configuration
- `POST /api/sql/configurations/{id}/emitters/{emitter_id}`: Add an emitter to a configuration
- `DELETE /api/sql/configurations/{id}/emitters/{emitter_id}`: Remove an emitter from a configuration

### SQL Functions

- `GET /api/sql/functions`: List all SQL functions
- `GET /api/sql/functions/{id}`: Get a SQL function by ID
- `GET /api/sql/functions/{schema}/{name}`: Get a SQL function by schema and name
- `POST /api/sql/functions`: Create a new SQL function
- `PUT /api/sql/functions/{id}`: Update a SQL function
- `DELETE /api/sql/functions/{id}`: Delete a SQL function

### SQL Triggers

- `GET /api/sql/triggers`: List all SQL triggers
- `GET /api/sql/triggers/{id}`: Get a SQL trigger by ID
- `GET /api/sql/triggers/{schema}/{name}`: Get a SQL trigger by schema and name
- `POST /api/sql/triggers`: Create a new SQL trigger
- `PUT /api/sql/triggers/{id}`: Update a SQL trigger
- `DELETE /api/sql/triggers/{id}`: Delete a SQL trigger

## Function Builder API

The SQL module includes a builder API for constructing SQL functions with a fluent interface.

```python
from uno.sql import SQLFunctionBuilder

# Create a function with the builder
function_sql = (
    SQLFunctionBuilder()
    .with_schema("public")
    .with_name("calculate_total")
    .with_args("order_id integer")
    .with_return_type("numeric")
    .with_body("""
    DECLARE
        total numeric := 0;
    BEGIN
        SELECT SUM(price * quantity) INTO total
        FROM order_items
        WHERE order_id = $1;
        
        RETURN total;
    END;
    """)
    .with_language("plpgsql")
    .with_volatility("STABLE")
    .build()
)

print(function_sql)
```

## Trigger Builder API

The SQL module also includes a builder API for constructing SQL triggers.

```python
from uno.sql import SQLTriggerBuilder

# Create a trigger with the builder
trigger_sql = (
    SQLTriggerBuilder()
    .with_schema("public")
    .with_name("order_items_update_trigger")
    .on_table("order_items")
    .for_events(["INSERT", "UPDATE", "DELETE"])
    .execute_function("update_order_total")
    .with_when("NEW.quantity <> OLD.quantity OR NEW.price <> OLD.price")
    .for_each_row()
    .build()
)

print(trigger_sql)
```

## Integration with FastAPI

The SQL module integrates with FastAPI for dependency injection:

```python
from fastapi import FastAPI, Depends
from uno.sql import get_sql_dependencies

app = FastAPI()

# Register SQL dependencies
sql_deps = get_sql_dependencies()

@app.get("/functions/{schema}/{name}")
async def get_function(
    schema: str,
    name: str,
    function_service = Depends(sql_deps["get_sql_function_service"])
):
    result = await function_service.get_function_by_name(schema, name)
    if result.is_success():
        return result.value
    else:
        return {"error": result.error}
```