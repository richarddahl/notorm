# Testing Framework

The Uno Testing Framework provides comprehensive utilities for testing Uno applications, 
including integration testing with containerized dependencies, property-based testing,
snapshot testing for complex objects, and performance regression testing.

All testing follows the standardized approach defined in the [Test Standardization Plan](../project/test_standardization_plan.md).

## Installation

The testing framework is included in the core Uno package and doesn't require any additional installation steps.

## Key Components

The testing framework consists of five main components:

1. **Integration Tests**: Verify component interactions in real environments
2. **Property-Based Testing**: Generate test cases based on properties and invariants
3. **Integration Test Harness**: Manage containerized dependencies for integration tests
4. **Snapshot Testing**: Compare complex objects against stored snapshots
5. **Performance Testing**: Detect and monitor performance regressions

## Integration Tests

The comprehensive integration test suite verifies that Uno components work correctly together in real-world environments. These tests cover core infrastructure, authentication/authorization, and data processing features.

### Running Integration Tests

```bash
# Run all integration tests
hatch run test:integration

# Run integration tests with vector search components
hatch run test:integration-vector

# Run specific integration test
pytest tests/integration/test_query_optimizer.py --run-integration
```

### Integration Test Categories

The integration test suite includes:

1. **Core Infrastructure Tests**
   - Database migrations
   - Connection pooling
   - Transaction management
   - Error handling

2. **Authentication and Authorization Tests**
   - JWT authentication
   - Role-based access control
   - Token caching
   - Session variables for RLS context
   - Database-level permissions

3. **Data Processing Tests**
   - Vector search
   - Batch operations
   - Query optimization
   - Distributed caching

### Benchmarking

Integration tests include benchmarking capabilities to measure performance:

```bash
# Run performance benchmarks
cd tests/integration
./run_benchmarks.py

# Compare with previous benchmark results
./run_benchmarks.py --compare previous_results.json

# Generate CSV report
./run_benchmarks.py --csv
```

## Property-Based Testing

Property-based testing allows you to define properties that should hold true for a wide range of inputs, and then automatically generate test cases to verify those properties.

### Examples

```python
from uno.testing.property_based import given_model, given_sql
from uno.model import UnoModel

class User(UnoModel):```

name: str
email: str
age: int
``````

```
```

def validate(self):```

return len(self.name) > 0 and '@' in self.email and self.age >= 0
```
```

@given_model(User)
def test_user_validation(model):```

# This test will automatically generate various User instances
assert model.validate()
```
    
@given_model(```

User, 
exclude_fields=["email"],
field_overrides={"name": "Fixed Name"}
```
)
def test_user_with_options(model):```

# This test will use a fixed name and default email
assert model.name == "Fixed Name"
```
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

class CustomType:```

def __init__(self, value):```

self.value = value
```
```

# Register a custom strategy
register_custom_strategy(```

CustomType, 
st.builds(CustomType, value=st.integers(1, 100))
```
)
```

## Integration Test Harness

The integration test harness helps you manage containerized dependencies for integration tests, such as PostgreSQL, Redis, and other services.

### Examples

```python
import pytest
from uno.testing.integration import IntegrationTestHarness

@pytest.fixture(scope="session")
def test_db():```

# Setup a PostgreSQL database for testing
harness = IntegrationTestHarness()
harness.services = [IntegrationTestHarness.get_postgres_config()]
``````

```
```

with harness.start_services():```

# Services are started
yield harness.get_connection_string("postgres")
```
# Services are automatically stopped
```

# Using a docker-compose file
@pytest.fixture(scope="session")
def test_environment():```

harness = IntegrationTestHarness(docker_compose_file="tests/docker-compose.test.yaml")
``````

```
```

with harness.start_services():```

yield harness
```
```
```

### Custom Service Configuration

```python
from uno.testing.integration.harness import ServiceConfig

# Custom service configuration
service_config = ServiceConfig(```

name="custom-service",
image="custom-image:latest",
ports={8080: 80},
environment={"ENV_VAR": "value"},
volumes={"/host/path": "/container/path"},
command="custom command",
health_check_url="http://localhost:8080/health",
ready_log_message="Service is ready"
```
)
```

## Snapshot Testing

Snapshot testing allows you to capture the state of complex objects and compare them against stored snapshots in future test runs.

### Examples

```python
from uno.testing.snapshot import snapshot_test, compare_snapshot

def test_complex_object():```

obj = create_complex_object()
# Compare against stored snapshot
assert snapshot_test(obj)
``````

```
```

# Get detailed comparison information
result = compare_snapshot(obj)
if not result["matches"]:```

print("Differences:", result["diff"])
```
```
```

### Updating Snapshots

To update snapshots when the expected output changes:

```python
def test_with_updated_expectations():```

obj = create_complex_object()
# Update the snapshot
snapshot_test(obj, update=True)
```
```

## Performance Testing

Performance testing helps you detect and monitor performance regressions in your code.

### Examples

```python
from uno.testing.performance import PerformanceTest, benchmark

def test_performance_manual():```

# Create a performance test
perf_test = PerformanceTest(name="database-query")
``````

```
```

# Measure performance
with perf_test.measure():```

result = db.execute_complex_query()
```
``````

```
```

# Check if performance is acceptable
acceptable, details = perf_test.check_performance()
assert acceptable, details["message"]
```

# Using the decorator
@benchmark(name="api-request", iterations=5)
def test_api_performance():```

client.get("/api/users")
# The function is automatically benchmarked
```

# Async support
@benchmark(name="async-operation")
async def test_async_performance():```

await async_operation()
# Async functions are also supported
```

# Integration benchmark example with output metrics
@pytest.mark.benchmark
def test_query_optimizer_benchmark(query_optimizer, setup_test_db):```

"""Benchmark the query optimizer performance."""
start_time = time.time()
``````

```
```

# Run the operation to benchmark
result = query_optimizer.execute_optimized_query(complex_query)
``````

```
```

duration = time.time() - start_time
``````

```
```

# Output benchmark metrics in standard format
print(f"BENCHMARK: query_execution_time={duration:.4f}")
print(f"BENCHMARK: rows_processed={len(result)}")
``````

```
```

assert duration < 0.5, "Query optimization should complete in under 0.5 seconds"
```
```

### Performance Tracking

The framework automatically saves performance data to benchmark files in the `tests/benchmarks` directory. These files track performance over time and can be used to detect regressions.

### Comprehensive Benchmarking System

The Uno framework includes a dedicated benchmarking system for integration tests:

1. **Benchmark Runner**: The `run_benchmarks.py` script discovers and runs all benchmark tests, collects metrics, and generates reports.

2. **Metrics Extraction**: Standardized format for reporting metrics using the `BENCHMARK: name=value` pattern in test output.

3. **Result Comparison**: Compare benchmark results across runs to detect performance regressions.

4. **Dashboard Integration**: Performance metrics can be visualized in the benchmarks dashboard.

### Benchmark Dashboard

The benchmark dashboard provides visualization and analysis of benchmark results:

```bash
# Run the benchmark dashboard
cd benchmarks/dashboard
./run_dashboard.sh
```

The dashboard offers:
- Historical performance tracking
- Regression detection
- Performance comparison across components
- Trend analysis and visualization