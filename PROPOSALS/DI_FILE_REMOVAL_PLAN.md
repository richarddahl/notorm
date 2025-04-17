# Dependency Injection File Removal Plan

This document outlines the plan for removing legacy DIContainer files and updating references to use the new UnoServiceProvider system.

## Files to Remove

1. `/src/uno/core/di.py` - Main DIContainer implementation
2. `/src/uno/core/di_testing.py` - Testing utilities for DIContainer

## Files to Update

1. `/src/uno/core/__init__.py` - Update imports to use the adapter instead

### Current Import in `/src/uno/core/__init__.py`

```python
# Dependency Injection
from uno.core.di import (
    # Container management
    DIContainer, ServiceLifetime, ServiceRegistration,
    initialize_container, get_container, reset_container,
    
    # Service resolution
    get_service, create_scope, create_async_scope
)

# Testing utilities
from uno.core.di_testing import (
    # Test container
    TestContainer, test_container,
    
    # Mock injection
    inject_mock, create_test_scope
)
```

### Updated Import (Using Adapter)

```python
# Dependency Injection (Adapter for backward compatibility)
from uno.core.di_adapter import (
    # Container management
    ContainerAdapter as DIContainer, ServiceLifetime, ServiceRegistration,
    initialize_container, get_container, reset_container,
    
    # Service resolution
    get_service, create_scope, create_async_scope
)

# Testing utilities (Using modern implementation)
from uno.dependencies.testing_provider import (
    # Test container
    TestServiceProvider as TestContainer, test_service_provider as test_container,
    
    # Mock injection
    MockService, configure_test_provider as create_test_scope
)

# Add this alias for backward compatibility
inject_mock = lambda *args, **kwargs: None  # This will need to be implemented properly
```

## Tests to Update

1. `/tests/unit/dependencies/test_di_container.py` - Test the adapter instead
2. `/tests/unit/core/test_di.py` - Test the adapter instead

### Update Options for Tests

**Option 1: Update Tests to Use the Adapter**

```python
# Before
from uno.core.di import get_container, ServiceLifetime

# After
from uno.core.di_adapter import get_container, ServiceLifetime
```

**Option 2: Update Tests to Use UnoServiceProvider Directly**

```python
# Before
from uno.core.di import get_container, ServiceLifetime

# After
from uno.dependencies.modern_provider import get_service_provider, ServiceLifecycle
```

## Execution Plan

1. Create and test di_adapter.py (COMPLETED)
2. Update core/__init__.py to use the adapter
3. Verify with existing tests
4. Update test files to use the adapter
5. Remove the legacy files (di.py and di_testing.py)
6. Test the entire application to ensure everything works correctly

## Verification

After completing the file removals and updates, run:

```bash
python -m pytest -xvs tests/
```

to ensure all tests pass with the updated code.

## Risks and Mitigations

1. **Risk**: Code that directly imports from uno.core.di or uno.core.di_testing will break
   - **Mitigation**: Encourage using imports from uno.core instead of direct imports
   - **Fallback**: Keep stub files that re-export from di_adapter if necessary

2. **Risk**: Some tests may rely on internal implementation details of DIContainer
   - **Mitigation**: Update tests to use public API only
   - **Fallback**: Add missing functionality to di_adapter.py

3. **Risk**: Performance differences may cause subtle issues
   - **Mitigation**: Add comprehensive tests for edge cases
   - **Fallback**: Fine-tune the adapter implementation

## Timeline

This file removal should be carried out after all other transition steps are complete and verified working correctly.