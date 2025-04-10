# Testing in NotORM

This document provides an overview of the testing approach in the NotORM framework, including philosophy, test organization, and guidelines for writing effective tests.

## Test Philosophy

NotORM follows these testing principles:

1. **Test-Driven Development**: Whenever possible, write tests before implementing features to ensure clear requirements and verifiable functionality.

2. **Comprehensive Coverage**: Aim for thorough test coverage across all critical components, with special focus on:
   - Core data model functionality
   - Data validation and error handling
   - SQL generation for database schemas
   - API behavior and endpoints
   - Authentication and authorization

3. **Isolation and Independence**: Tests should be self-contained and not rely on specific execution order or external state.

4. **Maintainability**: Tests should be easy to understand, maintain, and extend as the codebase evolves.

## Test Organization

Tests are organized into several categories:

### Unit Tests

Located in the `tests/unit/` directory, these tests verify individual components in isolation from their dependencies using mocking.

- **Core Tests** (`tests/unit/test_core/`): Testing fundamental model, object, registry, and utility classes
- **Database Tests** (`tests/unit/database/`): Testing database connection and transaction handling
- **Query Tests** (`tests/unit/queries/`): Testing filter creation and query building
- **SQL Tests** (`tests/unit/sql/`): Testing SQL generation for database schema components
  - **SQL Emitters**: Testing emitters that generate database objects
  - **SQL Builders**: Testing function and trigger builders
  - **SQL Statements**: Testing statement representations
  - **Database Emitters**: Testing database-level SQL operations
- **Schema Tests** (`tests/unit/schema/`): Testing schema management
  - **Schema Configuration**: Testing schema configuration and validation
  - **Schema Manager**: Testing schema creation and retrieval
- **API Tests** (`tests/unit/api/`): Testing API components
  - **Endpoint Factory**: Testing the creation of API endpoints

### Integration Tests

Located in various subdirectories of `tests/`, these tests verify the interaction between components:

- **Auth Tests** (`tests/auth/`): Testing authentication and authorization functionality
- **Meta Tests** (`tests/meta/`): Testing metadata handling and registration
- **PGJWT Tests** (`tests/pgjwt/`): Testing PostgreSQL JWT integration

## Running Tests

The test suite uses pytest. Use the following commands to run tests:

```bash
# Run all tests
ENV=test pytest

# Run only unit tests
ENV=test pytest tests/unit/

# Run tests with detailed output
ENV=test pytest -vv --capture=tee-sys --show-capture=all

# Run a specific test file
ENV=test pytest tests/path/to/test_file.py

# Run a specific test class or method
ENV=test pytest tests/path/to/test_file.py::TestClass::test_method
```

## Writing Effective Tests

When writing tests, follow these guidelines:

### Test Structure

1. **Test Naming**: Use descriptive names that explain what's being tested and under what conditions.
   - `test_[function_name]_[expected_behavior]` for positive cases
   - `test_[function_name]_[condition]_[expected_behavior]` for conditional cases
   - `test_[function_name]_with_[condition]` for tests with specific setups

2. **Test Method Structure**:
   - **Arrange**: Set up the test environment and data
   - **Act**: Execute the function being tested
   - **Assert**: Verify the results match expectations

3. **Documentation**: Include clear docstrings explaining test purpose and the specific scenario being tested.

### Mocking and Fixtures

1. **Fixtures**: Use pytest fixtures for common setup and teardown operations.
2. **Mocking**: Use the `unittest.mock` module to replace dependencies.
3. **Patching**: For Pydantic models, use `@patch()` rather than `patch.object()` when possible.

### Common Patterns

1. **Testing SQL Generation**:
   ```python
   # Test SQL function generation
   function_sql = some_function_builder.build()
   assert "CREATE OR REPLACE FUNCTION" in function_sql
   assert "RETURNS trigger" in function_sql
   assert "expected_function_body" in function_sql
   ```

2. **Testing Database Operations**:
   ```python
   # Mock the database connection
   with patch("uno.database.db.async_connection") as mock_conn:
       mock_cursor = AsyncMock()
       mock_conn.__aenter__.return_value = mock_conn
       mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
       
       # Set up the expected result
       mock_cursor.fetchone.return_value = {"id": "test_id"}
       
       # Call the method being tested
       result = await obj.get_by_id("test_id")
       
       # Verify the result
       assert result.id == "test_id"
   ```

3. **Testing Database Configuration**:
   ```python
   # Test ConnectionConfig and URI generation
   from uno.database.config import ConnectionConfig
   
   # Create config with test values
   config = ConnectionConfig(
       db_role="test_role",
       db_name="test_db",
       db_host="localhost",
       db_port=5432,
       db_user_pw="test@password",
       db_driver="postgresql+psycopg2"
   )
   
   # Test immutability
   with pytest.raises(Exception) as exc_info:
       config.db_name = "new_name"
   assert "frozen" in str(exc_info.value).lower()
   
   # Test URI generation with password encoding
   with patch('urllib.parse.quote_plus') as mock_quote_plus:
       mock_quote_plus.return_value = "encoded_password"
       uri = config.get_uri()
       mock_quote_plus.assert_called_once_with("test@password")
       assert uri == "postgresql+psycopg2://test_role:encoded_password@localhost:5432/test_db"
   ```

4. **Testing Database Engine Factory**:
   ```python
   # Test creating an engine with the factory
   from uno.database.engine.async import AsyncEngineFactory
   
   # Create factory and config
   factory = AsyncEngineFactory(logger=mock_logger)
   config = ConnectionConfig(db_driver="postgresql+asyncpg", ...)
   
   # Test with patch
   with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_create_engine:
       mock_engine = AsyncMock(spec=AsyncEngine)
       mock_create_engine.return_value = mock_engine
       
       # Call factory method
       engine = factory.create_engine(config)
       
       # Verify engine creation
       assert engine == mock_engine
       mock_create_engine.assert_called_once()
       
       # Verify URL was correctly formed
       url_arg = mock_create_engine.call_args[0][0]
       assert url_arg.drivername == config.db_driver
       assert url_arg.username == config.db_role
       assert url_arg.database == config.db_name
   ```

5. **Testing Filters and Queries**:
   ```python
   # Create a filter
   filter_instance = UnoFilter(source_node_label="User", ...)
   
   # Test query generation
   query = filter_instance.cypher_query("admin", "contains")
   assert "MATCH" in query
   assert "WHERE" in query
   assert "t.val CONTAINS 'admin'" in query
   ```

6. **Testing API Endpoints**:
   ```python
   # Test endpoint factory
   with patch("uno.api.endpoint.UnoEndpoint.__init__", return_value=None):
       factory = UnoEndpointFactory()
       factory.create_endpoints(app=mock_app, model_obj=mock_model, endpoints=["Create"])
       
       # Verify endpoint was created
       mock_endpoint_init.assert_called_once_with(
           model=mock_model,
           app=mock_app,
       )
   ```

## Test Coverage

As of April 2025, test coverage varies by component:

| Component                  | Unit Tests | Integration Tests | Notes                                       |
|----------------------------|------------|-------------------|---------------------------------------------|
| Core functionality         | High       | Medium            | Strong unit test coverage                    |
| Database Engine (Sync)     | High       | Medium            | Connection and engine factories well tested  |
| Database Engine (Async)    | Medium     | Low               | Challenging async context manager tests      |
| Database Configuration     | High       | None              | Connection config and URI generation tested  |
| Session Management         | Medium     | Low               | Session factories and context managers       |
| Queries/Filters            | High       | Low               | Good unit coverage                           |
| SQL Generation             | High       | None              | Added April 2025                             |
| Schema Management          | Medium     | Low               | Added April 2025                             |
| API Endpoints              | Medium     | Low               | Added April 2025                             |
| Authentication             | Medium     | Medium            | Partially covered                            |

## Recent Improvements

The following test modules were added in April 2025:

1. **SQL Emitters Tests**: Testing comprehensive SQL generation for database objects
   - Table emitters for creating tables, triggers, and constraints
   - Function emitters for database functions and procedures
   - SQL statement representation and dependencies

2. **Database Emitters Tests**: Testing database-level operations
   - Creation of roles and database
   - Schema and extension management
   - Privilege management
   - Database cleanup operations

3. **Database Engine and Configuration Tests**: Testing database connection management
   - Connection configuration validation and URI generation
   - Synchronous and asynchronous engine factories
   - Connection retry mechanisms and error handling
   - Connection pool configuration
   - Session management and transactions
   - DatabaseFactory integration and coordination

   See the detailed guide: [Testing Database Components](db/testing_database.md)

4. **Schema Management Tests**: Testing schema configuration and creation
   - Schema validation and field inclusion/exclusion
   - Schema manager for coordinating multiple schemas
   - Schema inheritance and composition

5. **API Endpoint Factory Tests**: Testing API endpoint creation
   - Endpoint factory for creating FastAPI routes
   - Endpoint type validation and routing
   - Error handling for endpoint creation

## Future Testing Areas

Priority areas for expanding test coverage:

1. **Async Context Managers**: Improve testing of async database context managers
   - Develop better techniques for testing `async_connection` and `async_session`
   - Create specialized AsyncMock utilities for testing coroutines in finally blocks
   - Add integration tests for async database operations

2. **API Integration Tests**: End-to-end testing of API endpoints
   - Test full request-response cycles with mocked database
   - Verify endpoint behaviors with different authentication states
   - Test error handling and response formatting

3. **Schema Migration Testing**: Tests for schema evolution over time
   - Test schema migration scripts and version tracking
   - Verify data integrity during schema changes
   - Test backward compatibility with older schema versions

4. **Performance Testing**: Add benchmarks for critical operations
   - Database connection pooling performance
   - Query execution time with different filter configurations
   - Schema generation and validation performance
   - API request handling latency

5. **Error Recovery Testing**: Test system resilience and error recovery
   - Database connection retry mechanisms
   - Handling of transient network errors
   - Transaction rollback behavior
   - Cleanup of partially created resources