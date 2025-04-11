# Schema Manager (Deprecated)

> **IMPORTANT**: The `SchemaManager` has been renamed to `DBManager` to better reflect its purpose of managing database objects rather than Pydantic schemas. This document is kept for reference, but new code should use `DBManager` instead. See [DB Manager](db_manager.md) for current documentation.

## Overview

The `SchemaManager` (now renamed to `DBManager`) provides a centralized way to execute DDL (Data Definition Language) statements, manage database schemas, verify database objects, and initialize databases. It's particularly useful for operations that require raw SQL execution or database administration tasks.

## Migration Guide

### How to Migrate from SchemaManager to DBManager

If you're using the old `SchemaManager`, here's how to migrate to the new `DBManager`:

1. **Update Imports**:
   ```python
   # Old
   from uno.database.schema_manager import SchemaManager
   from uno.dependencies import UnoSchemaManagerProtocol
   
   # New
   from uno.database.db_manager import DBManager
   from uno.dependencies import UnoDBManagerProtocol
   ```

2. **Update DI References**:
   ```python
   # Old
   schema_manager = get_instance(UnoSchemaManagerProtocol)
   
   # New
   db_manager = get_instance(UnoDBManagerProtocol)
   ```

3. **Method Parity**:
   The `DBManager` provides the same methods as `SchemaManager`, so your code should continue to work with only the import and reference changes.

### Key Differences

- Better naming that doesn't conflict with the concept of Pydantic schemas
- Enhanced validation of SQL statements before execution
- Improved logging and error handling
- Better integration with SQL Emitters

For complete documentation, see [DB Manager](db_manager.md).