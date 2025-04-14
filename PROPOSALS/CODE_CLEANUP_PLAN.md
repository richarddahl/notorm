# Action Plan for Code Cleanup

## 1. Legacy Dependency Injection System

**Files to Update:**
1. `/Users/richarddahl/Code/notorm/src/uno/workflows/provider.py`
2. `/Users/richarddahl/Code/notorm/src/uno/workflows/recipients.py`
3. `/Users/richarddahl/Code/notorm/src/uno/workflows/integration.py`
4. `/Users/richarddahl/Code/notorm/src/uno/workflows/executor.py`
5. `/Users/richarddahl/Code/notorm/src/uno/workflows/conditions.py`
6. `/Users/richarddahl/Code/notorm/src/uno/workflows/app_integration.py`
7. `/Users/richarddahl/Code/notorm/src/uno/workflows/__init__.py`
8. `/Users/richarddahl/Code/notorm/src/uno/values/providers.py`
9. `/Users/richarddahl/Code/notorm/src/uno/attributes/providers.py`

**Actions:**
1. Remove all `import inject` statements
2. Replace any `@inject.params()` with modern `@inject_params()` decorator
3. Replace any `inject.instance()` calls with `get_service()`
4. Refactor constructor injection to follow the modern pattern

## 2. Legacy `get_instance()` Singleton Pattern

**Files to Update:**
1. `/Users/richarddahl/Code/notorm/src/uno/database/query_cache.py`
2. `/Users/richarddahl/Code/notorm/src/uno/deployment/strategies.py`

**Actions:**
1. Refactor `QueryCacheManager.get_instance()` to use dependency injection:
   - Remove the `_instance` class variable
   - Remove the `get_instance()` method
   - Create a proper dependency injection registration for the class
   - Convert any calls to `QueryCacheManager.get_instance()` to use DI

2. Apply similar refactoring to other classes using the singleton pattern

## 3. Legacy Result Pattern (`unwrap()`, `is_ok()`, `is_err()`)

**Files to Update:**
1. `/Users/richarddahl/Code/notorm/src/uno/database/query_cache.py`
2. `/Users/richarddahl/Code/notorm/src/uno/database/pg_optimizer_strategies.py`
3. `/Users/richarddahl/Code/notorm/src/uno/database/query_optimizer.py`
4. `/Users/richarddahl/Code/notorm/src/uno/database/distributed_query.py`
5. `/Users/richarddahl/Code/notorm/src/uno/core/examples/query_optimizer_example.py`
6. `/Users/richarddahl/Code/notorm/src/uno/core/examples/query_cache_example.py`
7. `/Users/richarddahl/Code/notorm/src/uno/core/errors/result.py`

**Actions:**
1. Replace `result.unwrap()` with `result.value`
2. Replace `result.is_ok()` with `result.is_success`
3. Replace `result.is_err()` with `result.is_failure`
4. Remove any remaining imports of `Ok, Err` from result module
5. Update any code that returns `Ok()` or `Err()` to use `Success()` or `Failure()`

## 4. Legacy Classes (references to removed classes)

**Actions:**
1. Scan for references to the legacy classes listed in `validate_clean_slate.py`
2. Remove any remaining references or code paths that still rely on these classes
3. Update any tests that might still be referencing these classes

## 5. Circular Imports

**Files to Update:**
1. `/Users/richarddahl/Code/notorm/src/uno/queries/filter.py` 
2. `/Users/richarddahl/Code/notorm/src/uno/queries/filter_manager.py`
3. `/Users/richarddahl/Code/notorm/src/uno/obj.py`

**Actions:**
1. Continue the protocol-based approach for breaking circular dependencies
2. Move shared types to core modules
3. Use TYPE_CHECKING imports consistently
4. Remove any direct circular imports
5. Consider reorganizing the code structure to naturally avoid circular dependencies

## 6. Unnecessary Example Files

**Files to Update:**
1. `/Users/richarddahl/Code/notorm/src/uno/core/examples/query_cache_example.py`
2. `/Users/richarddahl/Code/notorm/src/uno/core/examples/query_optimizer_example.py`
3. Other example files that may be outdated

**Actions:**
1. Review each example for relevance
2. Update examples to use current API patterns
3. Remove examples that are outdated and no longer match the current implementation
4. Ensure all examples follow current best practices

## 7. SQL Registry Improvements

**Files to Update:**
1. `/Users/richarddahl/Code/notorm/src/uno/sql/registry.py`
2. `/Users/richarddahl/Code/notorm/src/uno/sql/registry_patch.py`

**Actions:**
1. Implement proper idempotent registration in the main registry
2. Remove the need for monkey patching in validation scripts
3. Make the registry more robust against duplicate registrations

## 8. Unused Imports

**Actions:**
1. Run a tool to detect unused imports across the codebase
2. Remove all unused imports
3. Consolidate import statements where appropriate
4. Replace broad imports (`from typing import *`) with specific imports

## 9. Standardize Documentation

**Actions:**
1. Update all docstrings to follow consistent format
2. Ensure all functions have proper type annotations
3. Add missing documentation where needed
4. Remove outdated comments

## 10. Test Cleanup

**Actions:**
1. Complete conversion of unittest-style tests to pytest style
2. Remove duplicate tests
3. Ensure tests are using modern practices (fixtures, etc.)
4. Remove any tests for legacy functionality that has been removed

## Implementation Strategy

### Phase 1: Dependency Injection Cleanup
- Remove all `import inject` statements
- Replace `inject.instance()` with `get_service()`
- Update constructor injection patterns

### Phase 2: Result Pattern Standardization
- Replace all `unwrap()`, `is_ok()`, and `is_err()` methods
- Update return types and patterns to modern standard

### Phase 3: Class Structure Cleanup
- Remove references to legacy classes
- Update code paths to use modern implementations

### Phase 4: Import and Documentation Cleanup
- Clean up unused imports
- Fix circular imports
- Standardize documentation
- Update example files

### Phase 5: Validation and Testing
- Run validation scripts
- Ensure all tests pass
- Create new tests as needed

## Implementation Tools

1. **Automated Import Cleanup**
   - Use tools like `autoflake` or `isort` to clean up unused imports
   - Run these tools on the codebase to automatically fix common issues

2. **Enhanced Validation Scripts**
   - Update `validate_clean_slate.py` to detect more patterns
   - Add validation for import statements

3. **Testing Framework**
   - Ensure comprehensive test coverage
   - Refactor tests to follow current best practices

## Prioritization

1. **High Priority**
   - Legacy DI system (most files)
   - Legacy Result pattern
   - Circular imports

2. **Medium Priority**
   - Singleton pattern removal
   - SQL registry improvements
   - Example file updates

3. **Low Priority**
   - Documentation standardization
   - Test cleanup
   - Unused imports

## Expected Benefits

1. **Improved Code Quality**
   - Consistent patterns throughout the codebase
   - Removal of legacy code and patterns
   - Cleaner code structure

2. **Better Maintainability**
   - Easier to understand and modify code
   - Fewer dependencies and circular references
   - Consistent API patterns

3. **Performance Improvements**
   - Removal of unnecessary layers
   - More efficient dependency management
   - Better database access patterns

4. **Reduced Technical Debt**
   - Elimination of deprecated patterns
   - Removal of workarounds and patches
   - Consistent modern approach