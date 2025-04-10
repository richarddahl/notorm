# uno Test Suite

This directory contains the test suite for the uno framework. The tests are organized into different categories to provide comprehensive coverage of the codebase.

## Test Structure

- `unit/`: Unit tests for individual components with mocked dependencies
  - `test_core/`: Tests for core modules like model, obj, registry
  - `database/`: Tests for database operations and connections
  - `queries/`: Tests for filter and query functionality
  - `sql/`: Tests for SQL generation and database schema components
  - `schema/`: Tests for schema management components
  - `api/`: Tests for API endpoint creation and routing
  
- `auth/`: Tests related to authentication and authorization functionality

- `meta/`: Tests related to metadata functionality

- `pgjwt/`: Tests for PostgreSQL JWT integration

## Running Tests

The test environment uses pytest. You can run tests using the following commands:

### Running all tests:

```bash
ENV=test pytest
```

### Running unit tests only:

```bash
ENV=test pytest tests/unit/
```

### Running a specific test file:

```bash
ENV=test pytest tests/path/to/test_file.py
```

### Running a specific test class or method:

```bash
ENV=test pytest tests/path/to/test_file.py::TestClassName::test_method_name
```

### Running with verbose output:

```bash
ENV=test pytest -vv --capture=tee-sys --show-capture=all
```

## Test Environment

Tests require:

1. A PostgreSQL database for integration tests (some tests are skipped without it)
2. Python 3.12+ with the required dependencies
3. Environment variables configured according to the project settings

Note: Some tests are skipped when running without specific dependencies. Check the test logs for details about skipped tests.

## Test Design Principles

1. **Isolation**: Tests should run in isolation, with minimal dependencies on external systems.
2. **Independence**: Tests should not depend on the order of execution.
3. **Coverage**: Tests should cover both success and failure scenarios.
4. **Clarity**: Tests should clearly document what they're testing and why.
5. **Maintainability**: Tests should be easy to understand and maintain.

## Test Coverage (as of April 2025)

| Component          | Unit Tests | Integration Tests | Notes                           |
|--------------------|------------|-------------------|----------------------------------|
| Core functionality | High       | Medium            | Strong unit test coverage        |
| Database           | Medium     | Medium            | Some async tests skipped         |
| Queries/Filters    | High       | Low               | Good unit coverage               |
| SQL Generation     | High       | None              | Added April 2025                 |
| Schema Management  | Medium     | Low               | Added April 2025                 |
| API Endpoints      | Medium     | Low               | Added April 2025                 |
| Authentication     | Medium     | Medium            | Partially covered                |

## Adding New Tests

When adding new tests:

1. Follow the existing structure and naming conventions
2. Add unit tests for new functionality
3. Mock external dependencies when appropriate
4. Include clear docstrings explaining the test's purpose
5. Ensure tests clean up after themselves

Test names should follow the convention:
- `test_[function_name]_[expected_behavior]` for positive cases
- `test_[function_name]_[condition]_[expected_behavior]` for conditional cases
- `test_[function_name]_with_[condition]` for tests with specific setups

Examples:
- `test_validate_input_valid_data`
- `test_process_data_empty_input_returns_error`
- `test_generate_sql_with_table`

Refer to the README files in each test subdirectory for more specific guidance on testing each component.