# SQL Classes Refactoring Migration Guide

## Overview

We've restructured the SQL-related code to follow better modularity principles, separating concerns into individual modules. This guide will help you migrate existing code to use the new structure.

## Directory Structure

The new structure is organized as follows:

```
uno/db/sql/
│
├── __init__.py             # Re-exports key classes
├── registry.py             # SQLConfigRegistry 
├── config.py               # SQLConfig base class
├── emitter.py              # SQLEmitter base class and protocols
├── statement.py            # SQLStatement and SQLStatementType
├── builders/
│   ├── __init__.py         # Re-exports builders
│   ├── function.py         # SQLFunctionBuilder
│   ├── trigger.py          # SQLTriggerBuilder
│   └── index.py            # SQLIndexBuilder
├── emitters/
│   ├── __init__.py         # Re-exports common emitters
│   ├── grants.py           # AlterGrants and other permission emitters
│   ├── triggers.py         # Various trigger emitters
│   └── functions.py        # Common function emitters
└── observers.py            # SQL observer implementations
```

## Backward Compatibility

For backward compatibility, we've maintained a `classes.py` file that re-exports all the key classes from their new locations. However, this module is deprecated and will display a warning when imported.

## Migration Steps

### Step 1: Update Imports

Replace imports from the old monolithic module with imports from the new specific modules.

**Old code:**
```python
from uno.sql.classes import (
    SQLEmitter, 
    SQLConfig, 
    SQLStatement,
    SQLStatementType
)
```

**New code:**
```python
from uno.sql.emitter import SQLEmitter
from uno.sql.config import SQLConfig
from uno.sql.statement import SQLStatement, SQLStatementType
```

Or, for simpler imports, use the re-exports from `__init__.py`:

```python
from uno.db.sql import SQLEmitter, SQLConfig, SQLStatement, SQLStatementType
```

### Step 2: Use Builder Classes

Replace manual string creation with the new builder classes.

**Old code:**
```python
def create_sql_function(self, function_name, function_body, return_type="TRIGGER"):
    return f"""
        CREATE OR REPLACE FUNCTION {self.schema}.{function_name}()
        RETURNS {return_type}
        LANGUAGE plpgsql
        VOLATILE
        AS $fnct$
        {function_body}
        $fnct$;
    """
```

**New code:**
```python
from uno.sql.builders import SQLFunctionBuilder

function_sql = (
    SQLFunctionBuilder()
    .with_schema(self.schema)
    .with_name(function_name)
    .with_return_type(return_type)
    .with_body(function_body)
    .build()
)
```

### Step 3: Use Statement Types

Replace string-based statement types with the enum-based SQLStatementType.

**Old code:**
```python
statements.append({
    "name": "some_function",
    "type": "function",
    "sql": sql_string
})
```

**New code:**
```python
from uno.sql.statement import SQLStatement, SQLStatementType

statements.append(SQLStatement(
    name="some_function",
    type=SQLStatementType.FUNCTION,
    sql=sql_string
))
```

### Step 4: Implement Observers

Use the observer pattern for logging and monitoring SQL operations.

```python
from uno.sql.observers import LoggingSQLObserver
from uno.sql.emitter import SQLEmitter

# Register the logging observer
SQLEmitter.register_observer(LoggingSQLObserver())
```

## Benefits of the New Structure

1. **Better Organization**: Each module has a clear, single responsibility
2. **Improved Code Reuse**: Common functions and utilities are centralized
3. **Enhanced Testability**: Simplified unit testing of individual components
4. **Type Safety**: Better type hints and protocols for all components
5. **Builder Pattern**: Fluent interfaces for creating complex SQL statements
6. **Documentation**: Comprehensive docstrings for all classes and methods

## Example: Creating a Custom Emitter

```python
from typing import List
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder

class CustomValidationEmitter(SQLEmitter):
    """Custom emitter for validation functions and triggers."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for validation."""
        statements = []
        
        if not self.table:
            return statements
            
        # Get schema and table information
        schema = self.connection_config.db_schema
        table_name = self.table.name
        
        # Build validation function
        function_body = """
        DECLARE
            record_exists BOOLEAN;
        BEGIN
            -- Check if record with same name already exists
            SELECT EXISTS (
                SELECT 1 FROM {schema}.{table_name} 
                WHERE name = NEW.name AND tenant_id = NEW.tenant_id
            ) INTO record_exists;
            
            IF record_exists THEN
                RAISE EXCEPTION 'Record with name % already exists for this tenant', NEW.name;
            END IF;
            
            RETURN NEW;
        END;
        """.format(schema=schema, table_name=table_name)
        
        function_sql = (
            SQLFunctionBuilder()
            .with_schema(schema)
            .with_name(f"{table_name}_validate_uniqueness")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )
        
        statements.append(SQLStatement(
            name=f"{table_name}_validate_uniqueness_function",
            type=SQLStatementType.FUNCTION,
            sql=function_sql
        ))
        
        # Build the trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(schema)
            .with_table(table_name)
            .with_name(f"{table_name}_validate_uniqueness_trigger")
            .with_function(f"{table_name}_validate_uniqueness")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE")
            .with_for_each("ROW")
            .build()
        )
        
        statements.append(SQLStatement(
            name=f"{table_name}_validate_uniqueness_trigger",
            type=SQLStatementType.TRIGGER,
            sql=trigger_sql,
            depends_on=[f"{table_name}_validate_uniqueness_function"]
        ))
        
        return statements
```

## Example: Registering with SQLConfig

```python
from uno.sql.config import SQLConfig
from sqlalchemy import Table, MetaData, Column, String, Integer

# Define a table
metadata = MetaData()
users_table = Table(
    'users', 
    metadata,
    Column('id', String, primary_key=True),
    Column('name', String),
    Column('tenant_id', String),
    Column('modified_by', String),
    Column('meta_id', String),
)

# Create a SQLConfig class for the table
class UserSQLConfig(SQLConfig):
    table = users_table
    default_emitters = [
        CustomValidationEmitter,
        RecordUserAuditFunction,
        AlterGrants,
    ]
```

## Example: Using SQLConfigRegistry

```python
from uno.sql.registry import SQLConfigRegistry
from uno.db.engine.sync import SyncEngineFactory, sync_connection
from uno.db.config import ConnectionConfig

# Create connection configuration
connection_config = ConnectionConfig(
    db_name="mydb",
    db_user_pw="password",
    db_role="mydb_login",
    db_schema="public",
)

# Create engine factory
engine_factory = SyncEngineFactory()

# Emit SQL for all registered configs
with sync_connection(factory=engine_factory, config=connection_config) as conn:
    SQLConfigRegistry.emit_all(
        connection=conn,
        exclude=["MetaTypeSQLConfig"]  # Optionally exclude specific configs
    )
```

## Gradual Migration Strategy

1. Start using the new imports in new code immediately
2. For existing code, use the backward compatibility imports from `classes.py`
3. Gradually migrate each module to use the new structure 
4. Use the builders for new SQL statements
5. Convert existing direct SQL strings to use builders when making changes
6. After all code has been migrated, remove uses of `classes.py`

## Performance Considerations

The new structure adds some overhead due to additional class instantiations and method calls, but the benefits in maintainability and correctness outweigh the small performance cost. The builder pattern in particular helps generate more robust SQL statements with less likelihood of errors.

## Testing

We've also enhanced testability with this structure. You can now:

1. Test SQL generators without executing SQL
2. Mock SQL executors for unit testing
3. Create observer implementations for validation and verification
4. Test SQL building in isolation

Example test:

```python
def test_custom_validation_emitter():
    # Create test table
    metadata = MetaData()
    test_table = Table('test_table', metadata, Column('id', String), Column('name', String))
    
    # Create test connection config
    config = ConnectionConfig(db_schema="test_schema", db_name="test_db")
    
    # Create emitter
    emitter = CustomValidationEmitter(table=test_table, connection_config=config)
    
    # Get SQL in dry run mode (no connection needed)
    statements = emitter.generate_sql()
    
    # Assertions
    assert len(statements) == 2
    assert statements[0].name == "test_table_validate_uniqueness_function"
    assert statements[0].type == SQLStatementType.FUNCTION
    assert "test_schema.test_table" in statements[0].sql
    
    assert statements[1].name == "test_table_validate_uniqueness_trigger" 
    assert statements[1].type == SQLStatementType.TRIGGER
    assert statements[1].depends_on == ["test_table_validate_uniqueness_function"]
```
