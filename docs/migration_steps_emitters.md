# SQLEmitter Refactoring Migration Steps

## Overview

We've restructured the SQL-related code to follow a more modular architecture with better separation of concerns. This document outlines the steps required to migrate from the monolithic `classes.py` approach to the new modular structure.

## New Directory Structure

```
uno/db/sql/
│
├── __init__.py             # Re-exports key classes
├── registry.py             # SQLConfigRegistry 
├── config.py               # SQLConfig base class
├── emitter.py              # SQLEmitter base class
├── statement.py            # SQLStatement and SQLStatementType
├── observers.py            # SQL observer implementations
├── builders/
│   ├── __init__.py         # Re-exports builders
│   ├── function.py         # SQLFunctionBuilder
│   ├── trigger.py          # SQLTriggerBuilder
│   └── index.py            # SQLIndexBuilder
└── emitters/
    ├── __init__.py         # Re-exports common emitters
    ├── database.py         # Database-level emitters (formerly dbsql.py)
    ├── table.py            # Table-level emitters (formerly tablesql.py)
    ├── security.py         # Security-related emitters (formerly rlssql.py)
    └── graph.py            # Graph database emitters (formerly graphsql.py)
```

## Migration Steps

### Step 1: Create New Module Files

Create all the new module files according to the directory structure above:

1. Create the folder structure with appropriate `__init__.py` files
2. Create the core modules: `registry.py`, `config.py`, `emitter.py`, `statement.py`, `observers.py`
3. Create the builder modules in the `builders/` directory
4. Create the emitter modules in the `emitters/` directory

### Step 2: Migrate Base Classes

First, move the core classes from `classes.py` to their respective modules:

- Move `SQLEmitter` to `emitter.py`
- Move `SQLConfig` to `config.py`
- Move `SQLConfigRegistry` to `registry.py`
- Create `SQLStatement` and `SQLStatementType` in `statement.py`
- Create builder classes in the appropriate builder modules

### Step 3: Migrate Emitter Classes

Move each emitter class to its appropriate module:

1. **Database-level emitters** to `emitters/database.py`:
   - `CreateRolesAndDatabase`
   - `CreateSchemasAndExtensions`
   - `RevokeAndGrantPrivilegesAndSetSearchPaths`
   - `CreatePGULID`
   - `CreateTokenSecret`
   - `GrantPrivileges`
   - `SetRole`
   - `DropDatabaseAndRoles`

2. **Table-level emitters** to `emitters/table.py`:
   - `InsertMetaRecordFunction`
   - `InsertMetaRecordTrigger`
   - `RecordStatusFunction`
   - `RecordUserAuditFunction`
   - `InsertPermission`
   - `ValidateGroupInsert`
   - `InsertGroupForTenant`
   - `DefaultGroupTenant`
   - `UserRecordUserAuditFunction`
   - `AlterGrants`
   - `InsertMetaType`
   - `RecordVersionAudit`
   - `EnableHistoricalAudit`

3. **Security-related emitters** to `emitters/security.py`:
   - `RowLevelSecurity`
   - `UserRowLevelSecurity`
   - `CreateRLSFunctions`
   - `GetPermissibleGroupsFunction`

4. **Graph-related emitters** to `emitters/graph.py`:
   - `GraphSQLEmitter`
   - `Node`
   - `Edge`

### Step 4: Update Imports in Existing Code

Update imports in all dependent code to use the new module paths:

**Old imports:**
```python
from uno.sql.classes import SQLEmitter, SQLConfig
```

**New imports:**
```python
from uno.sql.emitter import SQLEmitter
from uno.sql.config import SQLConfig
```

Or, use the re-exports from `__init__.py`:
```python
from uno.db.sql import SQLEmitter, SQLConfig
```

### Step 5: Implement Backwards Compatibility

To ease the transition, implement backward compatibility by having `classes.py` re-export the classes from their new locations with a deprecation warning:

```python
# classes.py
import warnings

# Re-export from new modular structure
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig
from uno.sql.emitter import SQLEmitter
# ...other imports...

# Show deprecation warning
warnings.warn(
    "Importing from uno.sql.classes is deprecated. "
    "Import from the appropriate modules instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### Step 6: Convert SQL String Generation to Use Builders

Replace direct SQL string creation with builder usage:

**Old approach:**
```python
def create_sql_function(self, function_name: str, function_body: str) -> str:
    return f"""
    CREATE OR REPLACE FUNCTION {schema}.{function_name}()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    VOLATILE
    AS $fnct$
    {function_body}
    $fnct$;
    """
```

**New approach:**
```python
from uno.sql.builders import SQLFunctionBuilder

function_sql = (
    SQLFunctionBuilder()
    .with_schema(schema)
    .with_name(function_name)
    .with_return_type("TRIGGER")
    .with_body(function_body)
    .build()
)
```

### Step 7: Update SQL Generation to Use SQLStatement

Replace direct SQL string returns with `SQLStatement` objects:

**Old approach:**
```python
@computed_field
def create_trigger(self) -> str:
    return trigger_sql
```

**New approach:**
```python
def generate_sql(self) -> List[SQLStatement]:
    statements = []
    # ...
    statements.append(SQLStatement(
        name="create_trigger", 
        type=SQLStatementType.TRIGGER,
        sql=trigger_sql
    ))
    return statements
```

### Step 8: Update Tests

Update test cases to work with the new structure:

1. Create tests for individual builder components
2. Update tests for emitters to use the new `generate_sql()` method
3. Use the `SQLEmitterTester` or similar utilities to test SQL generation

### Step 9: Update Documentation

Update documentation to reflect the new structure and recommended usage patterns:

1. Update docstrings for all classes and methods
2. Create examples of how to use the new builder pattern
3. Document the new module structure and explain where to find each component

### Step 10: Gradual Rollout

Implement the changes in phases:

1. Start with core classes and builders
2. Migrate simple emitters first
3. Gradually migrate more complex emitters
4. Once all emitters are migrated, add deprecation warnings to `classes.py`
5. After a grace period, consider removing the compatibility layer

## Benefits of the New Structure

1. **Improved Maintainability**: Smaller, focused files make code easier to understand and modify
2. **Better Testability**: Components can be tested in isolation
3. **Reduced Duplication**: Shared logic is centralized in utility functions and base classes
4. **Enhanced Type Safety**: Better type annotations throughout the codebase
5. **Builder Pattern**: Fluent interfaces for creating complex SQL statements
6. **Statement Metadata**: More information about generated SQL for debugging and optimization

## Example Usage

Here's an example of how to use the new structure to create a custom SQLEmitter:

```python
from typing import List
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder

class CustomValidationEmitter(SQLEmitter):
    """Custom emitter for data validation."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate validation SQL statements."""
        statements = []
        
        if not self.table:
            return statements
            
        # Build validation function using the builder
        function_body = """
        DECLARE
            record_exists BOOLEAN;
        BEGIN
            SELECT EXISTS (
                SELECT 1 FROM {schema}.{table} 
                WHERE name = NEW.name AND tenant_id = NEW.tenant_id
            ) INTO record_exists;
            
            IF record_exists THEN
                RAISE EXCEPTION 'Record with name % already exists', NEW.name;
            END IF;
            
            RETURN NEW;
        END;
        """.format(schema=self.config.DB_SCHEMA, table=self.table.name)
        
        function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_validate_uniqueness")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )
        
        statements.append(SQLStatement(
            name=f"{self.table.name}_validate_uniqueness_function",
            type=SQLStatementType.FUNCTION,
            sql=function_sql
        ))
        
        # Build the trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_validate_uniqueness_trigger")
            .with_function(f"{self.table.name}_validate_uniqueness")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE")
            .build()
        )
        
        statements.append(SQLStatement(
            name=f"{self.table.name}_validate_uniqueness_trigger",
            type=SQLStatementType.TRIGGER,
            sql=trigger_sql,
            depends_on=[f"{self.table.name}_validate_uniqueness_function"]
        ))
        
        return statements
```