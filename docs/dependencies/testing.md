# Testing with Dependencies

uno provides a comprehensive set of tools for testing code that uses dependency injection.

## Overview

Testing with dependency injection involves replacing real dependencies with mock or test versions. uno's testing utilities make this process straightforward and expressive.

## Key Testing Components

### TestingContainer

The `TestingContainer` class provides a way to configure test-specific dependencies:

```python
from uno.dependencies.testing import TestingContainer
from uno.dependencies.interfaces import UnoRepositoryProtocol

# Create a container
container = TestingContainer()

# Bind a mock repository
mock_repo = MagicMock(spec=UnoRepositoryProtocol)
container.bind(UnoRepositoryProtocol, mock_repo)

# Configure the container
container.configure()

# Run your tests...

# Restore original configuration
container.restore()
```

### Mock Factories

The testing module includes several factory classes for creating common mocks:

- `MockRepository`: Creates mock repositories with predefined behavior
- `MockConfig`: Creates mock configuration providers
- `MockService`: Creates mock services
- `TestSession`: Creates mock database sessions
- `TestSessionProvider`: Creates mock session providers

Example usage:

```python
from uno.dependencies.testing import MockRepository, MockConfig

# Create a repository with predefined items
items = [{'id': '1', 'name': 'Test Item'}]
repo = MockRepository.with_items(items)

# Create a config with predefined values
config = MockConfig.create({'DEFAULT_LIMIT': 10})
```

### Configure Test Container

For convenience, the `configure_test_container` function creates a container with common mocks already configured:

```python
from uno.dependencies.testing import configure_test_container

# Configure with default mocks
container = configure_test_container()

# Configure with custom mocks
container = configure_test_container({```

CustomInterface: custom_mock
```
})
```

## Testing Patterns

### Using Pytest Fixtures

```python
import pytest
from uno.dependencies.testing import configure_test_container, MockRepository

@pytest.fixture
def test_container():```

"""Fixture for a test container."""
container = configure_test_container()
yield container
container.restore()
```

@pytest.fixture
def mock_repository():```

"""Fixture for a mock repository with test data."""
items = [```

{'id': '1', 'name': 'Item 1'},
{'id': '2', 'name': 'Item 2'}
```
]
return MockRepository.with_items(items)
```

def test_service(test_container, mock_repository):```

"""Test a service with the mock repository."""
# Configure the container to use our specific repository
inject.instance(UnoRepositoryProtocol, mock_repository)
``````

```
```

# Create and test a service that uses the repository
service = MyService()
result = service.get_item('1')
assert result['name'] == 'Item 1'
```
```

### Testing Async Code

When testing async code that uses dependency injection, use pytest-asyncio:

```python
import pytest

@pytest.mark.asyncio
async def test_async_service(test_container):```

# Configure mock repository to return specific items
items = [{'id': '1', 'name': 'Test Item'}]
repo = MockRepository.with_items(items)
``````

```
```

# Override default mock
inject.instance(UnoRepositoryProtocol, repo)
``````

```
```

# Test the async service
service = AsyncItemService()
result = await service.get_items()
assert result == items
```
```

### Integration with FastAPI Tests

When testing FastAPI endpoints that use dependency injection:

```python
from fastapi.testclient import TestClient
from unittest.mock import patch

# Override FastAPI dependencies
def override_get_repository():```

return MockRepository.with_items([```

{'id': '1', 'name': 'Test Item'}
```
])
```

app.dependency_overrides[get_repository] = override_get_repository

# Test with the test client
client = TestClient(app)
response = client.get("/items")
assert response.status_code == 200
assert response.json() == [{'id': '1', 'name': 'Test Item'}]
```

## Best Practices

1. **Use fixtures** to set up and tear down test dependencies
2. **Configure once** at the test module or class level when possible
3. **Mock at the right level** - mock repositories for service tests, mock services for API tests
4. **Test with real components** occasionally to verify integration
5. **Clean up** after tests by restoring the original configuration