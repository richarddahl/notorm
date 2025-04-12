# Testing Framework

The Uno Testing Framework provides comprehensive utilities for testing Uno applications, 
including property-based testing, integration testing with containerized dependencies, 
snapshot testing for complex objects, and performance regression testing.

## Installation

The testing framework is included in the core Uno package and doesn't require any additional installation steps.

## Key Components

The testing framework consists of four main components:

1. **Property-Based Testing**: Generate test cases based on properties and invariants
2. **Integration Test Harness**: Manage containerized dependencies for integration tests
3. **Snapshot Testing**: Compare complex objects against stored snapshots
4. **Performance Testing**: Detect and monitor performance regressions

## Property-Based Testing

Property-based testing allows you to define properties that should hold true for a wide range of inputs, and then automatically generate test cases to verify those properties.

### Examples

```python
from uno.testing.property_based import given_model, given_sql
from uno.model import UnoModel

class User(UnoModel):
    name: str
    email: str
    age: int
    
    def validate(self):
        return len(self.name) > 0 and '@' in self.email and self.age >= 0

@given_model(User)
def test_user_validation(model):
    # This test will automatically generate various User instances
    assert model.validate()
    
@given_model(
    User, 
    exclude_fields=["email"],
    field_overrides={"name": "Fixed Name"}
)
def test_user_with_options(model):
    # This test will use a fixed name and default email
    assert model.name == "Fixed Name"
```

### Available Strategies

- `UnoStrategy`: Base strategy class for Uno testing
- `ModelStrategy`: Strategy for generating instances of Uno models
- `SQLStrategy`: Strategy for generating SQL statements

### Custom Strategies

You can register custom strategies for specific types:

```python
from hypothesis import strategies as st
from uno.testing.property_based import register_custom_strategy

class CustomType:
    def __init__(self, value):
        self.value = value

# Register a custom strategy
register_custom_strategy(
    CustomType, 
    st.builds(CustomType, value=st.integers(1, 100))
)
```

## Integration Test Harness

The integration test harness helps you manage containerized dependencies for integration tests, such as PostgreSQL, Redis, and other services.

### Examples

```python
import pytest
from uno.testing.integration import IntegrationTestHarness

@pytest.fixture(scope="session")
def test_db():
    # Setup a PostgreSQL database for testing
    harness = IntegrationTestHarness()
    harness.services = [IntegrationTestHarness.get_postgres_config()]
    
    with harness.start_services():
        # Services are started
        yield harness.get_connection_string("postgres")
    # Services are automatically stopped

# Using a docker-compose file
@pytest.fixture(scope="session")
def test_environment():
    harness = IntegrationTestHarness(docker_compose_file="tests/docker-compose.test.yaml")
    
    with harness.start_services():
        yield harness
```

### Custom Service Configuration

```python
from uno.testing.integration.harness import ServiceConfig

# Custom service configuration
service_config = ServiceConfig(
    name="custom-service",
    image="custom-image:latest",
    ports={8080: 80},
    environment={"ENV_VAR": "value"},
    volumes={"/host/path": "/container/path"},
    command="custom command",
    health_check_url="http://localhost:8080/health",
    ready_log_message="Service is ready"
)
```

## Snapshot Testing

Snapshot testing allows you to capture the state of complex objects and compare them against stored snapshots in future test runs.

### Examples

```python
from uno.testing.snapshot import snapshot_test, compare_snapshot

def test_complex_object():
    obj = create_complex_object()
    # Compare against stored snapshot
    assert snapshot_test(obj)
    
    # Get detailed comparison information
    result = compare_snapshot(obj)
    if not result["matches"]:
        print("Differences:", result["diff"])
```

### Updating Snapshots

To update snapshots when the expected output changes:

```python
def test_with_updated_expectations():
    obj = create_complex_object()
    # Update the snapshot
    snapshot_test(obj, update=True)
```

## Performance Testing

Performance testing helps you detect and monitor performance regressions in your code.

### Examples

```python
from uno.testing.performance import PerformanceTest, benchmark

def test_performance_manual():
    # Create a performance test
    perf_test = PerformanceTest(name="database-query")
    
    # Measure performance
    with perf_test.measure():
        result = db.execute_complex_query()
    
    # Check if performance is acceptable
    acceptable, details = perf_test.check_performance()
    assert acceptable, details["message"]

# Using the decorator
@benchmark(name="api-request", iterations=5)
def test_api_performance():
    client.get("/api/users")
    # The function is automatically benchmarked

# Async support
@benchmark(name="async-operation")
async def test_async_performance():
    await async_operation()
    # Async functions are also supported
```

### Performance Tracking

The framework automatically saves performance data to benchmark files in the `tests/benchmarks` directory. These files track performance over time and can be used to detect regressions.