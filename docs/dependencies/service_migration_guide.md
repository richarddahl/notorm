# Service Refactoring Migration Guide

## Overview

The `BaseService` class in `src/uno/dependencies/service.py` has been refactored to align with the standardized service pattern defined in `src/uno/core/base/service.py`. This guide explains how to migrate your existing services to the new pattern.

## Key Changes

1. `BaseService` now extends `CoreBaseService` from `uno.core.base.service`
2. Services now use the `Result` pattern for error handling
3. `CrudService` has been updated to use the Result pattern
4. A `LegacyServiceAdapter` provides backward compatibility

## How to Migrate Your Services

### For Simple Services

1. Update your imports:

```python
# Before
from uno.dependencies.service import BaseService

# After
from uno.core.base.service import BaseService
```

2. Update your service implementation:

```python
# Before
class MyService(BaseService[ModelT, ResultT]):
    async def execute(self, *args, **kwargs) -> ResultT:
        # Implementation

# After
class MyService(BaseService[Dict[str, Any], ResultT]):
    async def _execute_internal(self, input_data: Dict[str, Any]) -> Result[ResultT]:
        # Implementation
        return Success(result)
```

### For CRUD Services

1. Update your imports:

```python
# Before
from uno.dependencies.service import CrudService

# After
from uno.dependencies.service import CrudService  # New Result-based implementation
from uno.core.errors.result import Result, Success, Failure
```

2. Update your service usage:

```python
# Before
result = await crud_service.get(id)

# After
result = await crud_service.get(id)
if result.is_success():
    data = result.value
    # Use the data
else:
    # Handle the error
    error_message = result.error
```

### For Code That Can't Be Updated Immediately

Use the `LegacyServiceAdapter` to wrap new-style services:

```python
from uno.dependencies.service import LegacyServiceAdapter

# Create a modern service
modern_service = MyModernService(repository, logger)

# Wrap it with the adapter for legacy code
legacy_compatible_service = LegacyServiceAdapter(modern_service)

# Legacy code can use it with the old interface
result = await legacy_compatible_service.execute(*args, **kwargs)
```

## Benefits of the New Pattern

1. **Consistent Error Handling**: The `Result` pattern provides a standardized way to handle both success and failure cases
2. **Separation of Concerns**: The pattern separates error handling from business logic
3. **Type Safety**: Better type hints through generics
4. **Validation Support**: Built-in mechanism for input validation

## Examples

### Example: Simple Service

```python
from typing import Dict, Any
from uno.core.base.service import BaseService
from uno.core.errors.result import Result, Success, Failure

class UserCreationService(BaseService[Dict[str, Any], User]):
    def __init__(self, user_repository, logger=None):
        super().__init__(logger)
        self.user_repository = user_repository
    
    async def validate(self, input_data: Dict[str, Any]) -> Optional[Result[User]]:
        # Validate input
        if "email" not in input_data:
            return Failure("Email is required")
        return None
    
    async def _execute_internal(self, input_data: Dict[str, Any]) -> Result[User]:
        try:
            user = await self.user_repository.create(input_data)
            return Success(user)
        except Exception as e:
            return Failure(str(e))
```

### Example: CRUD Service Usage

```python
# Create a CRUD service
user_service = CrudService(user_repository)

# Get a user
result = await user_service.get("user-123")
if result.is_success():
    user = result.value
    # Use user data
else:
    # Handle error
    error_message = result.error
```

## Questions?

If you have questions about migrating your services, please contact the development team.
