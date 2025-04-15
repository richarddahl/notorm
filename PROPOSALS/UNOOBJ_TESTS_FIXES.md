# UnoObj Tests Fixes

This document details the fixes applied to make the tests in `tests/unit/test_core/test_obj.py` pass with Python 3.13.

## Background

The UnoObj class has been refactored to use a deferred import pattern for its dependencies to avoid circular imports. Instead of importing dependencies directly:

```python
from uno.schema.schema_manager import UnoSchemaManager
from uno.queries.filter_manager import UnoFilterManager
from uno.database.db import UnoDBFactory
```

It now uses getter functions:

```python
def get_schema_manager() -> SchemaManagerProtocol:
    """Get the schema manager instance."""
    from uno.schema.schema_manager import UnoSchemaManager
    return UnoSchemaManager()

def get_filter_manager() -> FilterManagerProtocol:
    """Get the filter manager instance."""
    from uno.queries.filter_manager import UnoFilterManager
    return UnoFilterManager()

def get_db_factory(obj: Type[Any]) -> Any:
    """Get the database factory instance."""
    from uno.database.db import UnoDBFactory
    return UnoDBFactory(obj=obj)
```

This required updating the tests to patch these getter functions rather than the direct class imports.

## Issues and Fixes

### 1. TestUnoObjInstantiation

**Issue**: The test was patching direct class imports instead of the getter functions.

**Original Code**:
```python
with patch('uno.obj.UnoFilterManager', return_value=mock_filter_manager):
    with patch('uno.obj.UnoSchemaManager', return_value=mock_schema_manager):
        with patch('uno.obj.UnoDBFactory', return_value=mock_db_factory):
            # Test code...
```

**Fixed Code**:
```python
with patch('uno.obj.get_db_factory', return_value=mock_db_factory):
    with patch('uno.obj.get_schema_manager', return_value=mock_schema_manager):
        with patch('uno.obj.get_filter_manager', return_value=mock_filter_manager):
            # Test code...
```

### 2. TestUnoObjSchemaOperations

**Issue**: Similar to above, patching direct class imports instead of getter functions.

**Fix**: Updated all patch calls to use the getter functions instead of direct imports.

### 3. UnoError vs UnoObjSchemaError

**Issue**: The test was expecting the generic `UnoError` class, but the implementation now uses the specific `UnoObjSchemaError` class.

**Original Code**:
```python
with pytest.raises(UnoError) as excinfo:
    obj.to_model(schema_name="nonexistent")
assert "Schema nonexistent not found" in str(excinfo.value)
assert excinfo.value.error_code == "SCHEMA_NOT_FOUND"
```

**Fixed Code**:
```python
with pytest.raises(UnoObjSchemaError) as excinfo:
    obj.to_model(schema_name="nonexistent")
assert "Schema nonexistent not found" in str(excinfo.value)
assert excinfo.value.error_code == "OBJ-0201"
```

### 4. TestUnoObjConfiguration

**Issue**: The `configure` method of UnoObj directly creates an instance of `UnoEndpointFactory` rather than using a getter function:

```python
# From uno/obj.py - UnoObj.configure:
endpoint_factory = UnoEndpointFactory()
endpoint_factory.create_endpoints(...)
```

**Fix**: Updated the test to patch `UnoEndpointFactory` directly but with a special pattern to ensure the mock is used:

```python
with patch('uno.obj.UnoEndpointFactory', MagicMock(return_value=mock_endpoint_factory)):
    # Test code...
```

## Lessons Learned

1. **Deferred Import Pattern**: The code has moved to a deferred import pattern to avoid circular dependencies. This pattern imports dependencies at function call time rather than module import time.

2. **Getter Functions vs Direct Imports**: Tests need to adapt to this pattern by patching the getter functions, not the direct imports.

3. **Error Handling**: Error codes in UnoObjErrors are now more specific (e.g., "OBJ-0201" instead of "SCHEMA_NOT_FOUND").

4. **Dependency Injection**: The modern DI system in uno uses protocols and getter functions instead of direct class imports.

5. **Type Safety**: The new system uses Protocol classes for better type safety with dependency injection.

## Summary

All UnoObj tests now pass with Python 3.13. The changes were primarily focused on adapting the tests to use the modern dependency injection system with deferred imports via getter functions, rather than direct class imports. These changes reflect a architectural shift in uno toward more loosely coupled components and better handling of circular dependencies.