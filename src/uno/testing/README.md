# uno Testing Framework

The uno Testing Framework provides comprehensive utilities for testing uno applications, including property-based testing, integration testing with containerized dependencies, mock data generation, snapshot testing for complex objects, and performance regression testing.

## Installation

The testing framework is included in the core uno package. For optional dependencies, install:

```bash
pip install -r requirements.txt
```

## Key Components

The testing framework consists of five main components:

1. **Property-Based Testing**: Generate test cases based on properties and invariants
2. **Integration Test Harness**: Manage containerized dependencies for integration tests
3. **Mock Data Generation**: Create realistic test data based on models or schemas
4. **Snapshot Testing**: Compare complex objects against stored snapshots
5. **Performance Testing**: Detect and monitor performance regressions

## Property-Based Testing

The `uno.testing.property_based` module provides utilities for property-based testing:

```python
from uno.testing.property_based import PropertyTest, forall, assume, stateful_test

class TestUserService(PropertyTest):
    @forall(username=st.text(min_size=3, max_size=50),
            email=st.emails(),
            bio=st.text(max_size=200).allow_none())
    async def test_create_user(self, username, email, bio):
        """Test that we can create users with valid data."""
        # Arrange
        user_data = {"username": username, "email": email, "bio": bio}
        
        # Act
        user = await self.user_service.create_user(user_data)
        
        # Assert
        assert user.username == username
        assert user.email == email
        assert user.bio == bio
```

Key features:
- Built on top of Hypothesis for powerful property-based testing
- Domain-specific features for uno applications
- Support for stateful testing with `stateful_test`
- Integrates with uno's dependency injection system

## Integration Testing

The `uno.testing.integration` module provides utilities for integration testing:

```python
from uno.testing.integration import IntegrationTestHarness

@pytest.fixture(scope="session")
def test_harness():
    """Create a test harness with containerized services."""
    harness = IntegrationTestHarness(
        services=[
            IntegrationTestHarness.get_postgres_config(),
            IntegrationTestHarness.get_redis_config()
        ]
    )
    
    with harness.start_services():
        yield harness

@pytest_asyncio.fixture
async def test_environment(test_harness):
    """Create a test environment."""
    async with test_harness.create_test_environment() as env:
        yield env

async def test_user_service(test_environment):
    """Test the user service with integration testing."""
    # Get repositories and services
    user_repo = test_environment.get_repository(UserRepository)
    user_service = test_environment.get_service(UserService)
    
    # Test with database operations
    user_id = await test_environment.db.insert_test_data(
        "users",
        {"username": "testuser", "email": "test@example.com"}
    )
    
    # Use the service
    user = await user_service.get_user(user_id)
    assert user is not None
```

Key features:
- Containerized service management
- Database testing utilities
- API testing utilities
- Repository and service testing
- Test environment management
- Test data setup and verification

## Mock Data Generation

The `uno.testing.mock_data` module provides utilities for generating test data:

```python
from uno.testing.mock_data.generators import ModelDataGenerator, SchemaBasedGenerator

# Generate data for a model
generator = ModelDataGenerator(seed=42)
user_data = generator.generate_for_model(UserModel)

# Generate data from a schema
schema_generator = SchemaBasedGenerator(seed=42)
data = schema_generator.generate_from_schema({
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 50},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 18, "maximum": 100}
    },
    "required": ["username", "email"]
})
```

Key features:
- Generate data for models based on type hints
- Generate data from JSON Schema
- Realistic data generation with Faker
- Customizable generation strategies
- Reproducible data generation with seed

## Snapshot Testing

The `uno.testing.snapshot` module provides utilities for snapshot testing:

```python
from uno.testing.snapshot import snapshot_test

@snapshot_test
def test_api_response(client):
    """Test that the API response matches the snapshot."""
    response = client.get("/users/1")
    # The response will be compared with the stored snapshot
    return response.json()
```

Key features:
- Snapshot storage and comparison
- Support for complex data structures
- Integration with pytest
- Automatic snapshot updates

## Performance Testing

The `uno.testing.performance` module provides utilities for performance benchmarking:

```python
from uno.testing.performance import benchmark

@benchmark(iterations=100)
def test_query_performance(db_session):
    """Benchmark the performance of a database query."""
    result = db_session.execute("SELECT * FROM users")
    return result.fetchall()
```

Key features:
- Measure execution time and memory usage
- Detect performance regressions
- Statistical analysis of performance metrics
- Integration with CI/CD pipelines

## Documentation

For detailed documentation and examples, see:

- [Property-Based Testing](../../../docs/testing/property_based_testing.md)
- [Integration Testing](../../../docs/testing/integration_testing.md)
- [Mock Data Generation](../../../docs/testing/mock_data_generation.md)
- [Snapshot Testing](../../../docs/testing/snapshot_testing.md)
- [Performance Testing](../../../docs/testing/performance_testing.md)

## Requirements

- Python 3.12+
- pytest 7.0+
- hypothesis 6.0+ (for property-based testing)
- pytest-asyncio 0.21.1+ (for async tests)
- docker (for integration testing with containers)
- faker (for realistic mock data generation)

## Type Checking

To type check the testing framework:

```bash
mypy --install-types --non-interactive src/uno/testing
```

## Examples

See the example files in each module:

- `uno.testing.property_based.examples`
- `uno.testing.integration.example`
- `uno.testing.mock_data.examples`
- `uno.testing.snapshot.examples`
- `uno.testing.performance.examples`