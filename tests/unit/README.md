# Unit Tests for NotORM

This directory contains unit tests for the core components of the NotORM framework. The tests are organized by module to provide comprehensive coverage of the codebase.

## Test Structure

- `test_core/`: Tests for core modules (model, obj, registry, errors, utilities)
  - `test_model.py`: Tests for UnoModel, PostgresTypes, and metadata functionality
  - `test_obj.py`: Tests for UnoObj business logic layer
  - `test_registry.py`: Tests for the UnoRegistry singleton pattern
  - `test_errors.py`: Tests for custom error classes
  - `test_utilities.py`: Tests for utility functions

## Running Tests

To run all unit tests:

```bash
ENV=test pytest tests/unit/
```

To run a specific test module:

```bash
ENV=test pytest tests/unit/test_core/test_model.py
```

To run with verbose output:

```bash
ENV=test pytest tests/unit/test_core/test_model.py -v
```

## Test Design Philosophy

1. **Isolation**: Tests are designed to run in isolation, with minimal dependencies on external systems.
2. **Mocking**: External dependencies are mocked where appropriate to ensure tests are deterministic.
3. **Coverage**: Tests aim to cover both successful and error scenarios.
4. **Documentation**: Each test class and method includes docstrings explaining its purpose.
5. **Maintainability**: Tests are structured to be easy to understand and maintain.

## Adding New Tests

When adding new tests:

1. Place tests in the appropriate module/directory
2. Follow the existing naming and structure patterns
3. Mock external dependencies to ensure isolation
4. Include docstrings explaining the purpose of the tests
5. Run tests to ensure they pass before committing

## Future Test Areas

1. Database connections and transactions
2. Schema management
3. API endpoint functionality 
4. Authentication and authorization
5. Filter and query management