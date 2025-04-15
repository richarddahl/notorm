# Service Provider Pattern

The Service Provider pattern is a powerful approach for centralizing access to your application's services, providing a unified interface for service discovery and retrieval.

## Overview

The Uno framework implements the Unified Service Provider pattern to provide:

- Centralized service access
- Type-safe service retrieval
- Consistent service configuration
- Simplified testing and mocking

## Using the Service Provider

### Initializing Services

Initialize all services at your application's entry point:

```python
from uno.dependencies import initialize_services

def main():```

# Initialize all services
initialize_services()
``````

```
```

# Rest of your application code...
```
```

### Accessing Services

The service provider offers multiple ways to access services:

```python
from uno.dependencies import get_service_provider
from uno.dependencies.interfaces import UnoConfigProtocol, SchemaManagerProtocol

# Get the service provider
provider = get_service_provider()

# Option 1: Get a service by its protocol type (most flexible)
config = provider.get_service(UnoConfigProtocol)

# Option 2: Use specialized getter methods (most convenient)
config = provider.get_config()
db_manager = provider.get_db_manager()
schema_manager = provider.get_schema_manager()
```

### Available Services

The service provider gives you access to all core services:

| Service | Protocol | Accessor Method |
|---------|----------|----------------|
| Configuration | `UnoConfigProtocol` | `get_config()` |
| Database Provider | `UnoDatabaseProviderProtocol` | `get_db_provider()` |
| Database Manager | `UnoDBManagerProtocol` | `get_db_manager()` |
| SQL Emitter Factory | `SQLEmitterFactoryProtocol` | `get_sql_emitter_factory()` |
| SQL Execution | `SQLExecutionProtocol` | `get_sql_execution_service()` |
| Schema Manager | `SchemaManagerProtocol` | `get_schema_manager()` |

## Example: Schema Management

Here's an example of using the service provider for schema management:

```python
from uno.dependencies import get_service_provider
from my_app.models import UserModel

# Get the service provider
provider = get_service_provider()

# Get the schema manager
schema_manager = provider.get_schema_manager()

# Create standard schemas for the UserModel
schemas = schema_manager.create_standard_schemas(UserModel)

# Use the schemas for different purposes
api_schema = schemas['api']
view_schema = schemas['view']
edit_schema = schemas['edit']

# Validate user input
user_data = request.json
user = api_schema(**user_data)

# Return API response
return view_schema.model_validate(user).model_dump()
```

## Testing with the Service Provider

The Service Provider pattern makes testing easier by providing a consistent way to mock services:

```python
from unittest.mock import MagicMock, patch
from uno.dependencies import get_service_provider

def test_user_service():```

# Create a mock schema manager
mock_schema_manager = MagicMock()
``````

```
```

# Create a mock service provider
with patch('my_app.get_service_provider') as mock_get_provider:```

mock_provider = MagicMock()
mock_provider.get_schema_manager.return_value = mock_schema_manager
mock_get_provider.return_value = mock_provider
``````

```
```

# Test your code that uses the service provider
result = my_function_that_uses_services()
``````

```
```

# Assert that the mock was used correctly
mock_provider.get_schema_manager.assert_called_once()
```
```
```

## Extending the Service Provider

You can extend the service provider to include your own application-specific services:

```python
from uno.dependencies.provider import ServiceProvider
from my_app.interfaces import UserServiceProtocol

class MyServiceProvider(ServiceProvider):```

"""Custom service provider with application-specific services."""
``````

```
```

def get_user_service(self) -> UserServiceProtocol:```

"""
Get the user service.
```
    ```

Returns:
    The user service
"""
return self.get_service(UserServiceProtocol)
```
```

# Override the global provider
from uno.dependencies.provider import _service_provider
_service_provider = MyServiceProvider()
```

## Benefits Over Direct Injection

While the Uno framework supports both direct injection methods and the Service Provider pattern, using the Service Provider offers several advantages:

1. **Centralized Service Management**: All service access goes through a single point, making it easier to manage dependencies.

2. **Type Safety**: The specialized getters return properly typed services.

3. **Lazy Initialization**: Services are only created when needed.

4. **Simplified Testing**: It's easier to mock the service provider than individual inject calls.

5. **Explicit Dependencies**: Your code clearly shows which services it depends on.

6. **Reduced Boilerplate**: No need to repeat the same inject calls throughout your code.

The Service Provider pattern is especially useful for larger applications where you need to manage many interdependent services.