# Test Standardization Plan

This document outlines the plan to standardize all tests to use pytest style, following the principle that DDL-emitting classes should be tested synchronously, and everything else should be tested asynchronously unless inherently synchronous.

## Current State

- 7 unittest-style test files in `tests/unit_unittest/database/`
- 95+ pytest-style test files throughout the codebase
- Multiple conftest.py files with fixtures in various directories

## Standardization Steps

### 1. Convert unittest-style Tests to pytest-style

Convert all unittest-style tests following these patterns:

1. **Replace Test Class Structure**:
   - Change `unittest.IsolatedAsyncioTestCase` classes to simple test functions with `@pytest.mark.asyncio` decorator
   - Move shared `setUp` code to pytest fixtures with appropriate scope

2. **Transform Assertion Methods**:
   - Replace `self.assertEqual(a, b)` with `assert a == b`
   - Replace `self.assertTrue(a)` with `assert a is True` or `assert a`
   - Replace `self.assertFalse(a)` with `assert a is False` or `assert not a`
   - Replace `self.assertIn(a, b)` with `assert a in b`
   - Replace `self.assertIsNone(a)` with `assert a is None`
   - Replace `self.assertIsNotNone(a)` with `assert a is not None`
   - Replace `self.assertRaises(Exc, func, args...)` with `with pytest.raises(Exc): func(args...)`

3. **Convert Test Methods to Functions**:
   - Rename from `test_something(self)` to `test_something(fixture1, fixture2, ...)`
   - Remove `self.` references and replace with explicit fixture usage

4. **Move Files to Correct Locations**:
   - Move from `tests/unit_unittest/database/` to `tests/unit/database/`

### 2. Create Common Fixtures

1. **Database-Specific Fixtures**:
   - Create a `test_db_factory` fixture 
   - Create a `mock_db_model` fixture
   - Create a `mock_db_object` fixture

2. **Fixture Organization**:
   - Add appropriate fixtures to `/tests/unit/database/conftest.py`
   - Use consistent fixture patterns across all test modules

### 3. Update Test Structure in database directory

1. **File Organization**:
   - Ensure tests follow repository structure
   - Keep test files organized by component they test  

2. **Testing Approach**:
   - Synchronous testing for DDL-emitting classes
   - Asynchronous testing for everything else (unless inherently synchronous)

### 4. Detailed Conversion Plan for `unit_unittest/database` Files:

1. `test_db_basic.py` → Convert to pytest style with fixtures
2. `test_db_create.py` → Convert to pytest style with fixtures
3. `test_db_filter.py` → Convert to pytest style with fixtures  
4. `test_db_get.py` → Convert to pytest style with fixtures
5. `test_db_merge.py` → Convert to pytest style with fixtures (example provided)
6. `test_session_async.py` → Convert to pytest style with fixtures
7. `test_session_mock.py` → Convert to pytest style with fixtures

### 5. Update Test Running Commands

1. Update the test commands in CLAUDE.md to reflect standardized testing approach
2. Ensure CI test commands are updated to match

## Implementation Approach

1. Create new pytest-style versions of each test file, keeping the old ones temporarily
2. Verify new test files pass with the appropriate command
3. Once verified, replace old test files with the new versions
4. Update any documentation references to the old structure

## Example Conversion

The file `test_db_merge.py` has been converted as an example of the transformation required:
- Original: `tests/unit_unittest/database/test_db_merge.py`
- Converted: `tests/unit_unittest/database/test_db_merge.py.new`

This file demonstrates:
- Converting from class-based to function-based tests
- Using fixtures instead of setUp methods
- Using pytest assertions instead of unittest assertions
- Maintaining the async pattern for async tests

## Completion Criteria

Standardization will be complete when:
1. All tests use pytest style
2. Tests are located in the correct directories
3. Common fixtures are used consistently
4. Test organization follows the repository structure
5. All tests pass with the standardized approach