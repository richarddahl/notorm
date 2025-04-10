# SQLConfig Migration Guide

This guide explains how to migrate your existing SQLConfig classes to use the new modular structure.

## Key Changes

1. **Import Path Changes**: 
   - Changed `uno.sql.classes` to `uno.sql.config`
   - Changed `uno.sql.tablesql` to `uno.sql.emitters.table`
   - Changed `uno.sql.graphsql` to `uno.sql.emitters.graph`
   - Changed `uno.auth.rlssql` to `uno.sql.emitters.security`

2. **Attribute Naming**:
   - Changed `sql_emitters` to `default_emitters`

## Step-by-Step Migration

1. Update the imports at the top of your file:
   ```python
   # Before
   from uno.sql.classes import SQLConfig
   from uno.sql.tablesql import AlterGrants, InsertMetaType
   from uno.sql.graphsql import GraphSQLEmitter
   
   # After
   from uno.sql.config import SQLConfig
   from uno.sql.emitters.table import AlterGrants, InsertMetaType
   from uno.sql.emitters.graph import GraphSQLEmitter
   ```

2. Change the attribute name in your SQLConfig classes:
   ```python
   # Before
   class MySQLConfig(SQLConfig):
       table = MyModel.__table__
       sql_emitters = [
           AlterGrants,
           InsertMetaType,
           GraphSQLEmitter,
       ]
   
   # After
   class MySQLConfig(SQLConfig):
       table = MyModel.__table__
       default_emitters = [
           AlterGrants,
           InsertMetaType,
           GraphSQLEmitter,
       ]
   ```

3. For security-related emitters, update the import:
   ```python
   # Before
   from uno.auth.rlssql import UserRowLevelSecurity
   
   # After
   from uno.sql.emitters.security import UserRowLevelSecurity
   ```

## Examples

Here are some examples of migrated SQLConfig classes:

### Simple Table Configuration

```python
# Before
from uno.sql.classes import SQLConfig
from uno.sql.tablesql import AlterGrants, InsertMetaType
from uno.sql.graphsql import GraphSQLEmitter

class MetaSQLConfig(SQLConfig):
    table = MetaRecordModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]

# After
from uno.sql.config import SQLConfig
from uno.sql.emitters.table import AlterGrants, InsertMetaType
from uno.sql.emitters.graph import GraphSQLEmitter

class MetaSQLConfig(SQLConfig):
    table = MetaRecordModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
```

### Configuration with Security Emitters

```python
# Before
from uno.sql.classes import SQLConfig
from uno.sql.tablesql import AlterGrants, InsertMetaType
from uno.auth.rlssql import UserRowLevelSecurity
from uno.sql.graphsql import GraphSQLEmitter

class UserSQLConfig(SQLConfig):
    table = UserModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        UserRowLevelSecurity,
        GraphSQLEmitter,
    ]

# After
from uno.sql.config import SQLConfig
from uno.sql.emitters.table import AlterGrants, InsertMetaType
from uno.sql.emitters.security import UserRowLevelSecurity
from uno.sql.emitters.graph import GraphSQLEmitter

class UserSQLConfig(SQLConfig):
    table = UserModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        UserRowLevelSecurity,
        GraphSQLEmitter,
    ]
```

## Backward Compatibility

During the transition period, you might encounter code that still uses the old structure. The backward compatibility layer in `uno.sql.classes` will continue to work, but will generate deprecation warnings:

```
DeprecationWarning: Importing from uno.sql.classes is deprecated. 
Import from the appropriate modules instead.
```

It's recommended to update your code to use the new structure as soon as possible.
