# Integration Testing with Uno

This document provides guidelines and examples for integration testing with Uno applications using the `uno.testing.integration` package.

## Overview

Integration testing verifies that different components of your application work together correctly. The Uno testing framework provides utilities for efficient integration testing with:

- Containerized testing environments (PostgreSQL, Redis, etc.)
- Database integration tests
- API integration tests
- Service and repository testing
- Test data generation
- Common test fixtures

## Getting Started

### Setting Up the Test Environment

To run integration tests, you'll need to set up the test environment. The `IntegrationTestHarness` class provides utilities for managing containerized dependencies:

```python
import pytest
from uno.testing.integration import IntegrationTestHarness

@pytest.fixture(scope="session")
def test_harness():```

"""Set up the test environment."""
harness = IntegrationTestHarness(```

services=[
    IntegrationTestHarness.get_postgres_config(),
    IntegrationTestHarness.get_redis_config()
]
```
)
``````

```
```

# Start services and yield the harness
with harness.start_services():```

yield harness
```
```
```

### Using Docker Compose

For more complex environments, you can use Docker Compose:

```python
@pytest.fixture(scope="session")
def test_harness():```

"""Set up the test environment with Docker Compose."""
harness = IntegrationTestHarness(```

docker_compose_file="path/to/docker-compose.yaml"
```
)
``````

```
```

with harness.start_services():```

yield harness
```
```
```

### Command-Line Options

The integration testing framework provides command-line options for configuring tests:

```bash
pytest --database-url=postgresql://user:pass@host:port/dbname
pytest --use-docker --docker-compose-file=docker-compose.test.yaml
pytest --skip-cleanup
```

## Test Environment

The `TestEnvironment` class provides a unified interface for accessing test components:

```python
@pytest_asyncio.fixture
async def test_environment(test_harness):```

"""Create a test environment."""
async with test_harness.create_test_environment() as env:```

yield env
```
```
```

This provides access to:

- `env.db`: Database testing utilities
- `env.api`: API testing utilities
- `env.get_repository()`: Get repository instances
- `env.get_service()`: Get service instances

## Database Testing

### Working with Test Data

Insert test data:

```python
async def test_database_operations(test_environment):```

"""Test database operations."""
# Insert test data
user_id = await test_environment.db.insert_test_data(```

"users",
{"username": "testuser", "email": "test@example.com"}
```
)
``````

```
```

# Verify the data
user = await test_environment.db.get_by_id("users", user_id)
assert user["username"] == "testuser"
```
```

### Bulk Data Operations

Load multiple rows of test data:

```python
async def test_with_bulk_data(test_environment):```

"""Test with bulk data."""
# Define test data
test_data = {```

"users": [
    {"username": "user1", "email": "user1@example.com"},
    {"username": "user2", "email": "user2@example.com"}
]
```
}
``````

```
```

# Set up test data with the environment
await test_environment.setup_test_data(test_data_file)
``````

```
```

# Verify data loaded correctly
count = await test_environment.db.count_rows("users")
assert count == 2
```
```

### Raw SQL Execution

Execute raw SQL for test setup and verification:

```python
async def test_with_sql(test_environment):```

"""Test with raw SQL."""
# Execute SQL query
result = await test_environment.db.execute_sql(```

"SELECT * FROM users WHERE username = :username",
username="testuser"
```
)
``````

```
```

# Process results
user = result.mappings().first()
assert user is not None
```
```

## Working with Repositories and Services

### Testing Repositories

Get repository instances from the test environment:

```python
async def test_user_repository(test_environment):```

"""Test the user repository."""
# Get repository from the environment
repo = test_environment.get_repository(UserRepository)
``````

```
```

# Use the repository
user = await repo.get_by_id(1)
assert user is not None
```
```

### Testing Services

Get service instances with dependencies automatically resolved:

```python
async def test_user_service(test_environment):```

"""Test the user service."""
# Get service with dependencies automatically resolved
service = test_environment.get_service(UserService)
``````

```
```

# Use the service
user = await service.get_user(1)
assert user is not None
```
```

## API Testing

The `ApiTestService` provides utilities for testing API endpoints:

```python
async def test_api_endpoints(test_environment):```

"""Test API endpoints."""
# Get data from an endpoint
users = test_environment.api.get("/users/")
assert len(users) > 0
``````

```
```

# Create a new resource
new_user = test_environment.api.post("/users/", {```

"username": "apiuser",
"email": "api@example.com"
```
})
assert new_user["id"] is not None
``````

```
```

# Update a resource
updated = test_environment.api.put(f"/users/{new_user['id']}", {```

"username": "updateduser"
```
})
assert updated["username"] == "updateduser"
``````

```
```

# Delete a resource
test_environment.api.delete(f"/users/{new_user['id']}")
```
```

## Advanced Techniques

### Isolated Test Environments

Create an isolated environment for each test:

```python
@pytest_asyncio.fixture
async def isolated_test(test_harness):```

"""Create an isolated test environment."""
# Create a unique schema name
import uuid
schema = f"test_{uuid.uuid4().hex[:8]}"
``````

```
```

# Create a test environment
async with test_harness.create_test_environment() as env:```

# Create the schema and set it as the search path
await env.db.execute_sql(f"CREATE SCHEMA {schema}")
await env.db.execute_sql(f"SET search_path TO {schema}")
``````

```
```

yield env
``````

```
```

# Clean up
await env.db.execute_sql(f"DROP SCHEMA {schema} CASCADE")
```
```
```

### Transactions and Savepoints

Use transactions to isolate test changes:

```python
async def test_with_transaction(test_environment):```

"""Test with transaction isolation."""
with test_environment.db.transaction():```

# Make changes that will be rolled back
await test_environment.db.insert_test_data(
    "users", 
    {"username": "tempuser", "email": "temp@example.com"}
)
``````

```
```

# Verify the data exists within the transaction
user = await test_environment.db.execute_sql(```

"SELECT * FROM users WHERE username = 'tempuser'"
```
)
assert user.mappings().first() is not None
```
    
# After the transaction, the data should be rolled back
user = await test_environment.db.execute_sql(```

"SELECT * FROM users WHERE username = 'tempuser'"
```
)
assert user.mappings().first() is None
```
```

## Integration with Mock Data Generation

Use the mock data generators with integration tests:

```python
from uno.testing.mock_data.generators import ModelDataGenerator

async def test_with_mock_data(test_environment):```

"""Test with generated mock data."""
# Create a mock data generator
generator = ModelDataGenerator(seed=42)
``````

```
```

# Generate data for a model
user_data = generator.generate_for_model(UserModel)
``````

```
```

# Use the generated data
repo = test_environment.get_repository(UserRepository)
user_id = await repo.create(user_data)
``````

```
```

# Verify the data
user = await repo.get_by_id(user_id)
assert user is not None
```
```

## Best Practices

1. **Use a unique database for testing**: Never run tests against production databases.

2. **Isolate tests**: Use isolated schemas or transactions for test isolation.

3. **Clean up resources**: Always clean up resources after tests to avoid resource leaks.

4. **Use fixtures efficiently**: Reuse fixtures for common setup and teardown operations.

5. **Keep tests independent**: Tests should not depend on the state from other tests.

6. **Test with realistic data**: Use mock data generators for realistic test data.

7. **Use transactions for isolation**: Use transactions to isolate test changes from each other.

8. **Verify database state**: Always verify the database state after operations.

9. **Test error cases**: Test both happy paths and error cases.

10. **Configure Docker for CI**: Use Docker for consistent testing environments in CI/CD.

## Example Test Case

Here's a complete example of an integration test:

```python
import pytest
import pytest_asyncio
from uno.testing.integration import IntegrationTestHarness

# Fixtures
@pytest.fixture(scope="session")
def test_harness():```

"""Create a test harness."""
harness = IntegrationTestHarness(
    services=[IntegrationTestHarness.get_postgres_config()]
)```
```

with harness.start_services():```

yield harness
```
```

@pytest_asyncio.fixture
async def test_environment(test_harness):```

"""Create a test environment."""
async with test_harness.create_test_environment() as env:```

yield env
```
```

# Test cases
async def test_user_service(test_environment):```

"""Test the user service."""
# Get services and repositories
user_repo = test_environment.get_repository(UserRepository)
user_service = test_environment.get_service(UserService)
``````

```
```

# Create test data
user_data = {```

"username": "testuser",
"email": "test@example.com",
"bio": "This is a test user"
```
}
``````

```
```

# Use the service
user = await user_service.create_user(user_data)
assert user["id"] is not None
``````

```
```

# Verify with the repository
saved_user = await user_repo.get_by_id(user["id"])
assert saved_user["username"] == "testuser"
assert saved_user["email"] == "test@example.com"
```
```

## Running Integration Tests

Run integration tests with pytest:

```bash
# Run all integration tests
pytest tests/integration/

# Run tests with Docker services
pytest tests/integration/ --use-docker

# Run with a specific Docker Compose file
pytest tests/integration/ --use-docker --docker-compose-file=docker-compose.test.yaml

# Run with an existing database
pytest tests/integration/ --database-url=postgresql://user:pass@localhost:5432/testdb
```

## Troubleshooting

### Common Issues

1. **Docker containers not starting**: Ensure Docker is running and you have permissions to create containers.

2. **Connection errors**: Check that the database URL is correct and the database is running.

3. **Permission issues**: Ensure the test user has the required permissions on the database.

4. **Cleanup failures**: Use the `--skip-cleanup` flag to debug cleanup issues.

### Debugging Tips

1. **Increase logging**: Set the log level to DEBUG to see more details.

2. **Inspect Docker logs**: Use `docker logs <container_id>` to see container logs.

3. **Check test isolation**: Ensure tests are not interfering with each other.

4. **Verify Docker Compose file**: Ensure the Docker Compose file is correct and all services are properly configured.

5. **Check port conflicts**: Ensure the ports used by Docker services are not already in use.

## Conclusion

The Uno integration testing utilities provide a powerful framework for testing Uno applications. By following these guidelines and using the provided utilities, you can write comprehensive integration tests that verify your application's behavior across component boundaries.

For more examples, see the `example.py` file in the `uno.testing.integration` package.