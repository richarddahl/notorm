# Uno Testing Framework

The Uno Testing Framework provides comprehensive utilities for testing Uno applications, including property-based testing, integration testing with containerized dependencies, snapshot testing for complex objects, and performance regression testing.

## Installation

The testing framework is included in the core Uno package. For optional dependencies, install:

```bash
pip install -r requirements.txt
```

## Key Components

The testing framework consists of four main components:

1. **Property-Based Testing**: Generate test cases based on properties and invariants
2. **Integration Test Harness**: Manage containerized dependencies for integration tests
3. **Snapshot Testing**: Compare complex objects against stored snapshots
4. **Performance Testing**: Detect and monitor performance regressions

## Documentation

For detailed documentation and examples, see the [Testing Framework Documentation](../../../docs/testing/framework.md).

## Requirements

- Python 3.12+
- pytest 7.0+
- hypothesis 6.0+ (for property-based testing)
- pytest-asyncio 0.21.1+ (for async tests)

## Type Checking

To type check the testing framework:

```bash
mypy --install-types --non-interactive src/uno/testing
```