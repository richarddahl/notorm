# UNO Framework Integration Tests

This directory contains integration tests for the UNO framework. These tests verify that components work correctly together in a real environment with actual infrastructure dependencies like PostgreSQL and Redis.

## Overview

Integration tests verify that independently developed units of software work correctly when they are connected together. Unlike unit tests that isolate components, integration tests exercise multiple components in their expected runtime configuration.

The UNO integration test suite covers:

1. Core infrastructure functionality
2. Authentication and authorization systems 
3. Advanced data processing features

## Test Structure

Tests are organized by functional area:

```
tests/integration/
├── conftest.py                      # Shared fixtures and configuration
├── database/                        # Database-specific integration tests
├── test_auth_caching.py             # Token caching tests
├── test_auth_jwt.py                 # JWT authentication tests  
├── test_auth_rbac.py                # Role-based access control tests
├── test_batch_operations.py         # Batch operation tests
├── test_connection_pool.py          # Connection pool tests
├── test_db_permissions.py           # Database permission tests
├── test_distributed_cache.py        # Distributed cache tests
├── test_error_handling.py           # Error handling tests
├── test_migrations.py               # Database migration tests
├── test_query_optimizer.py          # Query optimizer tests
├── test_rls_session_variables.py    # RLS context tests
└── test_vector_search.py            # Vector search tests
```

## Running the Tests

These tests require external services (PostgreSQL, Redis) and are skipped by default unless explicitly enabled.

### Prerequisites

1. Docker installed and running
2. Docker Compose installed
3. PostgreSQL with pgvector extension for vector tests

### Setting Up the Test Environment

Run the test environment setup script:

```bash
./scripts/setup_test_env.sh
```

This script:
- Creates Docker containers for PostgreSQL and Redis
- Configures necessary extensions (pgvector, etc.)
- Sets up test database with proper permissions

### Running All Integration Tests

```bash
pytest tests/integration/ --run-integration
```

### Running Specific Test Categories

Run only pgvector-related tests:
```bash
pytest tests/integration/ --run-integration --run-pgvector
```

Run a specific test file:
```bash
pytest tests/integration/test_vector_search.py --run-integration
```

Run a specific test:
```bash
pytest tests/integration/test_query_optimizer.py::test_query_plan_analysis --run-integration
```

## Test Categories

### Core Infrastructure Tests

These tests verify the essential database and infrastructure components:

- **Database Migrations**: Tests the migration system that manages schema changes
- **Connection Pool**: Tests connection pooling, reuse, and resilience
- **Transaction Management**: Tests transaction isolation, rollback, and nesting
- **Error Handling**: Tests error propagation, context, and functional error handling

### Authentication and Authorization Tests

These tests verify security components:

- **JWT Authentication**: Tests token generation, validation, and refresh
- **RBAC**: Tests role assignment, inheritance, and permission enforcement
- **Token Caching**: Tests distributed caching for authentication tokens
- **RLS Session Variables**: Tests PostgreSQL session variable management for RLS
- **Database Permissions**: Tests database-level permission enforcement

### Data Processing Tests

These tests verify advanced data processing features:

- **Vector Search**: Tests vector similarity search, hybrid filtering, and performance
- **Batch Operations**: Tests multi-table batch operations and transaction management
- **Query Optimizer**: Tests query analysis, rewriting, and caching
- **Distributed Cache**: Tests cross-process cache synchronization and operations

## Adding New Tests

When adding new integration tests:

1. Create a new test file in the `tests/integration/` directory
2. Add appropriate markers (`@pytest.mark.integration`, etc.)
3. Use existing fixtures or add new ones to `conftest.py` if needed
4. Update `INTEGRATION_TEST_PROGRESS.md` with details of your implementation

## Best Practices

1. **Clean up after tests**: Ensure each test cleans up resources (drop tables, delete data)
2. **Control test isolation**: Use unique table names when needed to prevent conflicts
3. **Test realistic scenarios**: Integration tests should test real-world workflows
4. **Keep tests independent**: Tests should not depend on other tests running first
5. **Use appropriate markers**: Mark tests requiring specific infrastructure

## Troubleshooting

Common issues:

- **Skipped tests**: Ensure you're using `--run-integration` flag
- **Vector search failures**: Ensure you have `--run-pgvector` and pgvector extension
- **Connection errors**: Verify Docker containers are running with `docker ps`
- **Cached permissions**: Clear caches between tests with fixture cleanup methods

For additional help, see `tests/README.md` for general testing guidelines.