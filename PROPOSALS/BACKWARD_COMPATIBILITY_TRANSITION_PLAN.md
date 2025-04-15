# Clean Slate Implementation Plan: Removing Legacy Code

This document outlines a direct approach to remove all backward compatibility code from uno, resulting in a clean, modern, testable, and well-designed library.

## Identified Legacy Code Patterns

After analyzing the codebase, we've identified several patterns of legacy code that need to be removed:

1. **Legacy Class Structures**: Duplicate class hierarchies from earlier prototyping (e.g., workflow legacy classes)
2. **Legacy Dependency Injection System**: Old DI methods that should be replaced by modern approaches
3. **Module Re-exports**: Re-exporting symbols from new locations for backward compatibility
4. **Transitional API Patterns**: Older API patterns that should be replaced with modern ones
5. **Result Pattern Inconsistencies**: Mixed usage of Ok/Err and Success/Failure patterns

## Implementation Strategy

We will implement a direct removal approach since this is a new system and backward compatibility is not needed:

1. **Step 1 (Week 1-2)**: Complete Inventory and Removal Plan
2. **Step 2 (Week 2-3)**: Direct Removal of Legacy Code
3. **Step 3 (Week 3-4)**: Testing and Validation

## Step 1: Complete Inventory and Removal Plan

Create a comprehensive inventory of all legacy code with the following information:
- Location of the code
- Modern pattern to standardize on
- Any dependent code that needs updates

## Step 2: Direct Removal of Legacy Code

### 2.1 Dependency Injection System

The dependency injection system contains legacy code that should be eliminated:

```python
# Remove completely:
from uno.dependencies.container import configure_di, get_container, get_instance
from uno.dependencies.provider import ServiceProvider, get_service_provider, initialize_services

# Standardize on:
from uno.dependencies.scoped_container import ServiceCollection, ServiceResolver, get_service
from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle
from uno.dependencies.decorators import singleton, scoped, transient, inject_params
```

#### Removal Plan:

1. Remove files: `uno/dependencies/container.py`
2. Clean `__init__.py` to remove legacy imports and re-exports
3. Update any code using the legacy DI system to use the modern equivalent
4. Remove the old ServiceProvider implementation

### 2.2 Database Access Layer

Eliminate legacy database access patterns:

#### Removal Plan:

1. Remove any direct low-level database API code
2. Standardize on the repository pattern using UnoRepository
3. Eliminate any direct session access code paths in favor of dependency-injected repositories

### 2.3 Result Pattern Standardization

Standardize on Success/Failure throughout the codebase:

```python
# Remove completely:
from uno.core.errors.result import Result, Ok, Err

# Standardize on:
from uno.core.errors.result import Result, Success, Failure
```

#### Removal Plan:

1. Remove Ok and Err classes from the result.py file
2. Convert all occurrences to Success and Failure
3. Update all return type annotations to use single-type parameter Result

### 2.4 Legacy Class Structure Removal

The workflows module and potentially other modules may contain legacy class structures:

#### Removal Plan:

1. Remove all legacy classes (e.g., the workflow legacy UnoObj classes we already removed)
2. Identify and remove similar patterns in other modules
3. Keep only the modern implementations

## Step 3: Testing and Validation

### 3.1 Comprehensive Testing

1. Create targeted tests for each modernized component
2. Ensure all core functionality works as expected
3. Verify that all code paths use the modern patterns

## Detailed Inventory of Legacy Code to Remove

### 1. Legacy Workflow Classes

**Location**: `/src/uno/workflows/objs.py` (Already removed)

**Modern Standard**: `WorkflowDef` class and associated modern workflow components.

**Removal Actions**:
- ✓ Remove legacy WorkflowStep, WorkflowTransition, WorkflowTask, and WorkflowInstance classes
- ✓ Remove mock model classes created for compatibility
- ✓ Update schemas.py to reflect modern-only structure

### 2. Legacy Dependency Injection System

**Location**: `/src/uno/dependencies/__init__.py`, `/src/uno/dependencies/container.py`

**Modern Standard**: 
```python
from uno.dependencies import get_service
user_service = get_service(UserService)
```

**Removal Actions**:
- Delete `container.py` file entirely
- Remove from `__init__.py`:
  - `configure_di`
  - `get_container`
  - `get_instance`
  - Legacy `ServiceProvider`
  - Legacy `get_service_provider`
  - Legacy `initialize_services`
- Update any depending code to use modern alternatives

### 3. Legacy FastAPI Integration

**Location**: `/src/uno/dependencies/fastapi.py`

**Modern Standard**:
```python
@router.get("/{user_id}")
@inject_params()
async def get_user(user_id: str, config: ConfigService):
    # Implementation
```

**Removal Actions**:
- Remove `inject_dependency` function
- Remove `get_config` and any other direct Depends wrappers
- Standardize on `@inject_params()` and proper typing
- Replace with direct imports from fastapi_integration.py

### 4. Result Pattern Standardization

**Location**: Throughout the codebase, especially in service and repository layers

**Modern Standard**:
```python
return Success({"data": result})
if result.is_success:
    value = result.value
```

**Removal Actions**:
- Remove `Ok` and `Err` classes from result.py
- Update all imports to standardize on Success/Failure
- Find and replace all `is_ok()` with `is_success`
- Find and replace all `is_err()` with `is_failure`
- Find and replace all `unwrap()` with `value`
- Find and replace all `unwrap_err()` with `error`

### 5. SQL Module Re-exports

**Location**: `/src/uno/sql/__init__.py`

**Modern Standard**: Direct imports from specific modules.

**Removal Actions**:
- Remove the comment about "backward compatibility"
- Reorganize imports to import directly from specific modules
- Update module docstring to reflect modern usage

### 6. UnoObj vs. Modern Domain Entities

**Location**: Various files

**Modern Standard**: Domain-driven design with proper entity classes and repositories.

**Removal Actions**:
- Identify modules still using UnoObj for complex domains
- Convert to proper domain entities and repositories
- Retain UnoObj only for simple CRUD operations

## Testing Strategy

### 1. Unit Testing

Create targeted tests for each modernized component:

```python
def test_modern_di_system():
    # Test modern DI system without legacy components
    
def test_result_pattern():
    # Test Success/Failure pattern without Ok/Err
```

### 2. Integration Testing

```python
def test_complete_workflow():
    # Test entire workflow with modern components only
```

### 3. Validation Scripts

Create scripts to scan the codebase to ensure:
- No imports of removed modules
- No uses of removed classes or functions
- Consistent use of modern patterns

## Conclusion

By removing all legacy code and standardizing on modern patterns, we will create a clean, consistent, and maintainable codebase. This direct approach is appropriate since we're building a new system and don't need backward compatibility with prototypes.

The result will be:
- A cleaner, more focused codebase
- Better performance without compatibility layers
- A consistent developer experience
- Improved testability through proper dependency injection
- A solid foundation for future development

This clean slate approach will set us up for success with a modern, testable, well-designed library.