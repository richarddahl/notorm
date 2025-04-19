# Protocol Testing Framework

This document details the Protocol Testing Framework implementation for the UNO framework as part of the architectural modernization plan.

## Overview

The Protocol Testing Framework provides comprehensive tools for validating and testing protocol implementations. It ensures that implementations properly fulfill their protocol contracts, both statically and at runtime, and provides utilities for mocking protocols for testing purposes.

## Key Components

### 1. Protocol Validation

The `protocol_validator` module provides core functionality for validating protocol implementations:

- `validate_protocol(cls, protocol)`: Verifies that a class correctly implements a protocol
- `validate_implementation(instance, protocol)`: Validates that an instance properly implements a protocol
- `find_protocol_implementations(module, protocol)`: Finds all classes that implement a specific protocol
- `implements(*protocols)`: Decorator for marking and validating protocol implementations

This validation is thorough, checking both attribute presence and type compatibility:

```python
from uno.core.protocol_validator import implements
from uno.domain.protocols import Repository, Entity

@implements(Repository[User, UUID])
class UserRepository:
    async def get(self, id: UUID) -> Optional[User]:
        # Implementation
        ...
```

### 2. Protocol Testing

The `protocol_testing` module extends the validation capabilities with testing utilities:

#### ProtocolMock

`ProtocolMock[P]` creates mock implementations of protocols for testing:

```python
from uno.core.protocol_testing import ProtocolMock
from uno.domain.protocols import Repository

# Create a mock repository
repo_mock = ProtocolMock[Repository[User, UUID]]()

# Configure the mock
user = User(id=uuid4(), name="Test User")
repo_mock.configure_method("get", return_value=user)

# Get the mock implementation
repo = repo_mock.create()

# Use the mock
assert await repo.get(user.id) == user
```

#### ProtocolTestCase

`ProtocolTestCase[P]` is a base test case for testing protocol implementations:

```python
from uno.core.protocol_testing import ProtocolTestCase
from uno.domain.protocols import Repository

class TestUserRepository(ProtocolTestCase[Repository[User, UUID]]):
    protocol_type = Repository[User, UUID]
    implementation_type = PostgresUserRepository
    
    def test_implementation(self):
        # Validates statically
        self.validate_implementation_static()
        
        # Create and validate an instance
        repo = self.create_implementation()
        
        # Test implementation specifics
        # ...
```

### 3. Automated Test Generation

The framework also provides utilities for automatically generating tests for protocol implementations:

- `all_protocol_implementations(module_name)`: Finds all implementations of all protocols in a module
- `create_protocol_test_suite(module_name)`: Creates a test suite that tests all protocol implementations in a module

This enables automatic validation of all protocol implementations in a codebase:

```python
from uno.core.protocol_testing import create_protocol_test_suite

# Create a test suite for all protocol implementations in a module
suite = create_protocol_test_suite("uno.infrastructure.database")

# Run the tests
unittest.TextTestRunner().run(suite)
```

## Use Cases

### 1. Development Validation

During development, the `@implements` decorator provides immediate validation:

```python
@implements(Repository[User, UUID])
class UserRepository:
    # If this class doesn't properly implement the Repository protocol,
    # a ProtocolValidationError will be raised at definition time
    ...
```

### 2. Unit Testing

For testing, `ProtocolTestCase` provides a structured way to test implementations:

```python
class TestUserRepository(ProtocolTestCase[Repository[User, UUID]]):
    protocol_type = Repository[User, UUID]
    implementation_type = UserRepository
    
    def test_save_and_retrieve(self):
        repo = self.create_implementation()
        user = User(id=uuid4(), name="Test")
        
        # Test specific behaviors
        await repo.save(user)
        retrieved = await repo.get(user.id)
        self.assertEqual(retrieved, user)
```

### 3. CI/CD Validation

For continuous integration, the validation script provides system-wide checking:

```bash
# Run protocol validation across the codebase
python -m src.scripts.validate_protocols --verbose
```

### 4. Mocking Dependencies

For testing services that depend on protocols, `ProtocolMock` simplifies mocking:

```python
def test_user_service():
    # Create a mock repository
    repo_mock = ProtocolMock[Repository[User, UUID]]()
    
    # Configure the mock
    user = User(id=uuid4(), name="Test")
    repo_mock.configure_method("get", return_value=user)
    
    # Create the service with the mock
    service = UserService(repo_mock.create())
    
    # Test the service
    result = await service.get_user_by_id(user.id)
    assert result == user
```

## Implementation Details

### Validation Approach

The framework validates protocol implementation in several ways:

1. **Static Attribute Checking**: Ensures all required attributes exist
2. **Type Compatibility**: Verifies that types match between protocol and implementation
3. **Runtime Validation**: Confirms that instances properly implement protocols
4. **Mock Configuration**: Provides runtime behavior for testing

### Error Reporting

Validation errors provide detailed information about what's missing or incorrect:

```
ProtocolValidationError: Class 'InvalidUserRepository' does not properly implement protocol 'Repository'.
Missing attributes: list, delete. Type mismatches: get (expected: User, found: Dict[str, Any])
```

## Next Steps

1. Finish implementing the Unit of Work pattern to complete Phase 1
2. Add more comprehensive examples in the documentation
3. Create protocol compliance reports for the codebase
4. Enhance IDE integration for protocol validation

## Conclusion

The Protocol Testing Framework completes a critical piece of the Phase 1 implementation, providing robust tools for ensuring that implementations correctly fulfill their protocol contracts. This framework is essential for maintaining the integrity of the architecture as the codebase evolves, enabling loose coupling while ensuring proper interfaces are maintained.