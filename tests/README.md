# uno Test Suite

This directory contains the test suite for uno. The tests are organized into different categories to provide comprehensive coverage of the codebase.

## Test Structure

- `unit/`: Unit tests for individual components with mocked dependencies
  - `test_core/`: Tests for core modules like model, obj, registry
  - `database/`: Tests for database operations and connections
  - `queries/`: Tests for filter and query functionality
  - `sql/`: Tests for SQL generation and database schema components
  - `schema/`: Tests for schema management components
  - `api/`: Tests for API endpoint creation and routing

- `integration/`: Integration tests that verify components work correctly together
  - Core infrastructure (migrations, connections, transactions, error handling)
  - Authentication and authorization (JWT, RBAC, RLS, permissions)
  - Data processing (vector search, batch operations, query optimization)
  - Distributed features (caching, clustering)

- `benchmarks/`: Performance benchmark tests
  - Dashboard for visualizing performance metrics
  - Test data generators for benchmarking

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

### Running integration tests:

```bash
ENV=test pytest tests/integration/ --run-integration
```

### Running vector-specific tests:

```bash
ENV=test pytest tests/integration/ --run-integration --run-pgvector
```

### Running performance benchmarks:

```bash
ENV=test ./tests/integration/run_benchmarks.py
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

1. A PostgreSQL database for integration tests (tests are skipped without it)
2. Redis server for distributed cache tests
3. PostgreSQL with pgvector extension for vector search tests
4. Python 3.12+ with the required dependencies
5. Environment variables configured according to the project settings

You can set up a complete test environment using:

```bash
./scripts/setup_test_env.sh
```

This script creates Docker containers with all necessary services and extensions.

Note: Integration and vector tests are skipped by default and must be explicitly enabled using the `--run-integration` and `--run-pgvector` flags.

## Test Design Principles

1. **Isolation**: Tests should run in isolation, with minimal dependencies on external systems.
2. **Independence**: Tests should not depend on the order of execution.
3. **Coverage**: Tests should cover both success and failure scenarios.
4. **Clarity**: Tests should clearly document what they're testing and why.
5. **Maintainability**: Tests should be easy to understand and maintain.

## Test Coverage (as of April 2025)

| Component          | Unit Tests | Integration Tests | Notes                              |
|--------------------|------------|-------------------|----------------------------------- |
| Core functionality | High       | High              | Strong test coverage               |
| Database           | High       | High              | Connection pooling, transactions   |
| Queries/Filters    | High       | High              | Batch operations, optimization     |
| SQL Generation     | High       | Medium            | Added April 2025                   |
| Schema Management  | Medium     | High              | Migration tests added              |
| API Endpoints      | Medium     | Medium            | Authentication integration added   |
| Authentication     | High       | High              | JWT, RBAC, RLS all covered         |
| Vector Search      | Medium     | High              | pgvector integration fully tested  |
| Query Optimization | Medium     | High              | Added April 2025                   |
| Distributed Cache  | Medium     | High              | Added April 2025                   |

## Adding New Tests

When adding new tests:

1. Follow the existing structure and naming conventions
2. Add unit tests for new functionality
3. Add integration tests for component interactions
4. Add performance benchmarks for critical paths
5. Mock external dependencies when appropriate
6. Include clear docstrings explaining the test's purpose
7. Ensure tests clean up after themselves

### Test Naming Conventions

Unit test names should follow the convention:
- `test_[function_name]_[expected_behavior]` for positive cases
- `test_[function_name]_[condition]_[expected_behavior]` for conditional cases
- `test_[function_name]_with_[condition]` for tests with specific setups

Integration test names should focus on the interaction being tested:
- `test_[component1]_with_[component2]`
- `test_[workflow]_end_to_end`
- `test_[feature]_integration`

Performance test names should indicate what's being measured:
- `test_[component]_performance`
- `test_[operation]_benchmark`
- `test_performance_[scenario]`

Examples:
- `test_validate_input_valid_data`
- `test_query_optimizer_with_cache`
- `test_vector_search_performance`

### Adding Benchmarks

To add a new performance benchmark:
1. Create a test function in the appropriate file
2. Use the `@pytest.mark.benchmark` decorator if available
3. Output metrics using the `BENCHMARK: name=value` format in test output
4. Add the test to the `BENCHMARK_FUNCTIONS` list in `run_benchmarks.py`

Refer to the README files in each test subdirectory for more specific guidance on testing each component.