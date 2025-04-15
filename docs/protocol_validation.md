# Protocol Validation System

The Protocol Validation System provides tools to ensure that concrete implementations correctly fulfill Protocol interfaces, helping to catch implementation errors early in development.

## Features

- **Static Protocol Validation**: Validate that classes correctly implement protocols at development time
- **Runtime Protocol Validation**: Validate that instances correctly implement protocols at runtime
- **Implementation Discovery**: Find all classes in a module that implement a specific protocol
- **Declarative Implementation Marking**: Mark classes as implementations of protocols with a decorator
- **Comprehensive Error Messages**: Get detailed information about missing attributes and type mismatches
- **Command-Line Validation Tool**: Validate all protocol implementations across your codebase

## Usage Examples

### Validating Protocol Implementations

```python
from typing import Protocol, Optional, runtime_checkable
from uuid import UUID, uuid4
from uno.core import validate_protocol, validate_implementation, ProtocolValidationError

# Define a protocol
@runtime_checkable
class UserRepository(Protocol):```

async def get(self, id: UUID) -> Optional['User']:```

...
```
``````

```
```

async def save(self, user: 'User') -> None:```

...
```
```

# Validate a class against the protocol
class PostgresUserRepository:```

async def get(self, id: UUID) -> Optional['User']:```

# Implementation
return None
```
``````

```
```

async def save(self, user: 'User') -> None:```

# Implementation
pass
```
```

try:```

validate_protocol(PostgresUserRepository, UserRepository)
print("Class implements the protocol correctly!")
```
except ProtocolValidationError as e:```

print(f"Protocol validation failed: {e}")
```

# Validate an instance
repo = PostgresUserRepository()
validate_implementation(repo, UserRepository)
```

### Using the `@implements` Decorator

```python
from uno.core import implements

@implements(UserRepository)
class MongoUserRepository:```

async def get(self, id: UUID) -> Optional['User']:```

# Implementation
return None
```
``````

```
```

async def save(self, user: 'User') -> None:```

# Implementation
pass
```
```

# The decorator has already validated the implementation at class definition time
# If the class doesn't properly implement the protocol, a ProtocolValidationError 
# will be raised when the module is imported
```

### Finding Protocol Implementations

```python
from uno.core import find_protocol_implementations

# Find all classes that implement UserRepository in a module
implementations = find_protocol_implementations("app.repositories", UserRepository)

for impl in implementations:```

print(f"Found implementation: {impl.__name__}")
```
```

### Validating All Implementations

```python
from uno.core import verify_all_implementations

# Verify all classes marked with @implements in multiple modules
errors = verify_all_implementations(["app.repositories", "app.services"])

if errors:```

print(f"Found {len(errors)} classes with validation errors:")
for class_name, class_errors in errors.items():```

print(f"  {class_name}:")
for error in class_errors:
    print(f"    - {error}")
```
```
else:```

print("All implementations are valid!")
```
```

## Command-Line Validation Tool

The uno framework includes a command-line tool to validate protocol implementations across your entire codebase:

```bash
# Validate all protocol implementations in src.uno
python -m src.scripts.validate_protocols

# Validate specific modules with verbose output
python -m src.scripts.validate_protocols --verbose src.uno.api src.uno.repositories
```

## Best Practices

1. **Use the `@implements` decorator** to explicitly mark classes as protocol implementations and catch errors early
2. **Include protocol validation in CI/CD pipelines** using the command-line tool
3. **Create protocol interfaces before implementing them** to follow interface-first design
4. **Add type hints to all protocol methods and attributes** to enable comprehensive validation
5. **Use runtime_checkable for protocols** that need runtime checking in addition to static validation
6. **Separate domain protocols from infrastructure protocols** to maintain clean layering
7. **Validate at boundaries** - ensure that adapters and repositories correctly implement their protocols