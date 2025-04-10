# Unit Tests for uno

This directory contains unit tests for the core components of the uno framework. The tests are organized by module to provide comprehensive coverage of the codebase.

## Test Structure

- `test_core/`: Tests for core modules (model, obj, registry, errors, utilities)
  - `test_model.py`: Tests for UnoModel, PostgresTypes, and metadata functionality
  - `test_obj.py`: Tests for UnoObj business logic layer
  - `test_registry.py`: Tests for the UnoRegistry singleton pattern
  - `test_errors.py`: Tests for custom error classes
  - `test_utilities.py`: Tests for utility functions
- `database/`: Tests for database-related modules
  - `test_db.py`: Tests for UnoDBFactory and database operations
- `queries/`: Tests for query and filter-related modules
  - `test_filter.py`: Tests for UnoFilter and lookup definitions
  - `test_filter_manager.py`: Tests for UnoFilterManager and filter validation
- `schema/`: Tests for schema management
  - `test_schema.py`: Tests for UnoSchema and schema configuration
  - `test_schema_manager.py`: Tests for UnoSchemaManager and schema creation
- `sql/`: Tests for SQL generation and database schema components
  - `test_emitters.py`: Tests for SQL emitters that generate database objects
  - `test_builders.py`: Tests for SQL function and trigger builders
  - `test_statement.py`: Tests for SQL statement representations
  - `test_database_emitters.py`: Tests for database-level SQL emitters
- `api/`: Tests for API components
  - `test_endpoint_factory.py`: Tests for the UnoEndpointFactory and endpoint creation

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

## Coverage Summary

| Module          | Coverage | Description                                        |
|-----------------|----------|----------------------------------------------------|
| Core            | High     | Model, object, registry, error handling, utilities |
| Queries         | High     | Filters, lookups, filter management                |
| SQL Generation  | High     | Emitters, builders, statements, database emitters  |
| Database        | Low      | Connection management, transaction handling        |
| Schema          | Medium   | Schema management, schema configuration            |
| API             | Medium   | API endpoint creation and routing                  |
| Authorization   | Low      | Permission models (auth tests exist outside unit/) |

## Future Test Areas

1. Expanding schema and migration testing
2. Additional API endpoint functionality (endpoint implementation)
3. Authentication and authorization flows
4. Message queue integration
5. Performance and load testing

## Debugging Tests

When debugging tests, especially for Pydantic models:

1. Watch for attribute access issues with patching Pydantic models
   - Avoid direct attribute assignment on model instances
   - Use `@patch()` decorator instead of `patch.object()` when possible
   - For model properties, prefer patching at the class level

2. Be aware of naming conflicts in mock objects
   - Avoid using attribute names that match model field names
   - Use protected attributes (with underscore prefix) for internal mock state
   - Use properties to control attribute access when needed

3. Test isolation issues
   - Each test should clean up after itself, especially when using singletons
   - Use fixtures with proper teardown to reset global state
   
4. Working with SQL generation tests
   - SQL generation tests verify structure rather than exact formatting
   - Check for key elements in generated SQL rather than exact string matching
   - Mock configuration values appropriately for consistent testing
   - Remember that SQL builders can inject values (like role names) based on context