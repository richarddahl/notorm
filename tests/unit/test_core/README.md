# Core Module Tests

This directory contains tests for the core modules of uno. These tests focus on the fundamental building blocks of the system.

## Test Files

### `test_model.py`

Tests for the `UnoModel` class and related functionality:
- PostgresTypes enum and type annotations
- MetadataFactory for generating SQLAlchemy metadata
- UnoModel class methods and properties
- Model field definitions and validation

### `test_obj.py`

Tests for the `UnoObj` business logic layer:
- Object initialization and validation
- Schema operations and property access
- CRUD operations (save, update, delete)
- Relationship handling
- Event triggering and handling

### `test_registry.py`

Tests for the `UnoRegistry` class which manages object registration:
- Singleton pattern implementation
- Registration and lookup functionality
- Validation of registered objects
- Error handling for duplicate registrations

### `test_errors.py`

Tests for the custom error classes:
- Error inheritance hierarchy
- Error message formatting
- Error code assignment
- Exception handling behavior

### `test_utilities.py`

Tests for utility functions:
- String conversion (snake_case, camel_case, etc.)
- Data structure utilities
- Type conversion helpers
- Common utility functions

## Running the Tests

To run just the core module tests:

```bash
ENV=test pytest tests/unit/test_core/
```

To run a specific test file:

```bash
ENV=test pytest tests/unit/test_core/test_model.py
```

## Test Design

These tests use pytest fixtures extensively to provide test data and mock dependencies. When working with these tests:

1. Pay attention to fixture dependencies
2. Use proper mocking for external dependencies
3. Ensure each test is isolated from others
4. Watch for global state in singleton objects (like Registry)

For detailed debugging tips, refer to the parent directory's README.