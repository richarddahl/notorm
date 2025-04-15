# Database Protocol Interfaces

This document describes the protocol-based interfaces for database connectivity in the Uno framework.

## Introduction

Database access in Uno has been refactored to use protocol interfaces, providing several benefits:

1. **Decoupling**: Database components are now decoupled from specific implementations
2. **Testability**: Components can be easily tested with mock implementations
3. **Flexibility**: Different database backends can be supported with minimal code changes
4. **Contract enforcement**: Protocols clearly define expected behavior

## Core Database Protocols

### DatabaseSessionProtocol

This protocol defines the interface for database sessions, abstracting the underlying database API:

```python
@runtime_checkable
class DatabaseSessionProtocol(Protocol):```

"""Protocol for database sessions."""
``````

```
```

async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:```

"""Execute a statement."""
...
```
``````

```
```

async def commit(self) -> None:```

"""Commit the current transaction."""
...
```
``````

```
```

async def rollback(self) -> None:```

"""Rollback the current transaction."""
...
```
``````

```
```

async def close(self) -> None:```

"""Close the session."""
...
```
``````

```
```

def add(self, instance: Any) -> None:```

"""Add an instance to the session."""
...
```
```
```

### DatabaseSessionFactoryProtocol

This protocol defines the interface for session factories, which create database sessions:

```python
@runtime_checkable
class DatabaseSessionFactoryProtocol(Protocol):```

"""Protocol for session factories."""
``````

```
```

def create_session(self, config: Any) -> DatabaseSessionProtocol:```

"""Create a database session."""
...
```
``````

```
```

def get_scoped_session(self, config: Any) -> Any:```

"""Get a scoped session."""
...
```
``````

```
```

async def remove_all_scoped_sessions(self) -> None:```

"""Remove all scoped sessions."""
...
```
```
```

### DatabaseSessionContextProtocol

This protocol defines the interface for session context managers:

```python
@runtime_checkable
class DatabaseSessionContextProtocol(Protocol):```

"""Protocol for database session context managers."""
``````

```
```

async def __aenter__(self) -> DatabaseSessionProtocol:```

"""Enter the context manager."""
...
```
``````

```
```

async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:```

"""Exit the context manager."""
...
```
```
```

### DatabaseRepository

This protocol defines the interface for database repositories:

```python
@runtime_checkable
class DatabaseRepository(Protocol[EntityT, KeyT]):```

"""Protocol for database repositories."""
``````

```
```

@classmethod
async def get(cls, **kwargs: Any) -> Optional[EntityT]:```

"""Get an entity by keyword arguments."""
...
```
``````

```
```

@classmethod
async def create(cls, entity: EntityT) -> tuple[EntityT, bool]:```

"""Create a new entity."""
...
```
``````

```
```

@classmethod
async def update(cls, entity: EntityT, **kwargs: Any) -> EntityT:```

"""Update an existing entity."""
...
```
``````

```
```

@classmethod
async def delete(cls, **kwargs: Any) -> bool:```

"""Delete an entity by keyword arguments."""
...
```
``````

```
```

@classmethod
async def filter(cls, filters: Any = None) -> list[EntityT]:```

"""Filter entities by criteria."""
...
```
``````

```
```

@classmethod
async def merge(cls, data: dict) -> Any:```

"""Merge data into an entity."""
...
```
```
```

## Implementation Examples

### Session Context Implementation

```python
class AsyncSessionContext(DatabaseSessionContextProtocol):```

"""Context manager for async database sessions, implementing DatabaseSessionContextProtocol."""
``````

```
```

def __init__(```

self,
db_driver: str = uno_settings.DB_ASYNC_DRIVER,
db_name: str = uno_settings.DB_NAME,
db_user_pw: str = uno_settings.DB_USER_PW, 
db_role: str = f"{uno_settings.DB_NAME}_login",
db_host: Optional[str] = uno_settings.DB_HOST,
db_port: Optional[int] = uno_settings.DB_PORT,
factory: Optional[DatabaseSessionFactoryProtocol] = None,
logger: Optional[logging.Logger] = None,
scoped: bool = False,
**kwargs: Any
```
):```

"""Initialize the async session context."""
# Implementation details...
```
    
async def __aenter__(self) -> DatabaseSessionProtocol:```

"""Enter the async context, returning a database session."""
# Implementation details...
return self.session
```
``````

```
```

async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:```

"""Exit the async context, closing the session if needed."""
# Implementation details...
```
```
```

### Repository Implementation

```python
def UnoDBFactory(```

obj: BaseModel,
session_context_factory: Optional[Type[DatabaseSessionContextProtocol]] = None
```
) -> Type[DatabaseRepository[T, K]]:```

"""
Factory function that creates a UnoDB class implementing the DatabaseRepository protocol.
"""
# Use provided session factory or default
SessionContextClass = session_context_factory or AsyncSessionContext
``````

```
```

class UnoDB(DatabaseRepository[T, K]):```

"""Repository implementation that uses the provided session context."""
``````

```
```

@classmethod
async def get(cls, **kwargs: Any) -> Optional[T]:
    """Get an entity by keyword arguments."""
    # Implementation using the session context
    session_context = SessionContextClass()
    async with session_context as session:
        # Query implementation...
        return result
```
```
```

## Usage in Application Code

Instead of directly depending on specific database implementations, application code can now depend on these protocols:

```python
async def fetch_users(```

repository: Type[DatabaseRepository[UserModel, UUID]], 
filter_criteria: Optional[FilterParam] = None
```
) -> List[UserModel]:```

"""
Fetch users from the database using a repository that implements DatabaseRepository.
``````

```
```

The repository implementation can be swapped without changing this function.
"""
return await repository.filter(filter_criteria)
```
```

## Testing with Mock Implementations

Protocol interfaces make it easy to create mock implementations for testing:

```python
class MockDatabaseSessionContext(DatabaseSessionContextProtocol):```

"""Mock session context for testing."""
``````

```
```

async def __aenter__(self) -> DatabaseSessionProtocol:```

"""Return a mock session."""
return MockDatabaseSession()
```
``````

```
```

async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:```

"""Clean up resources."""
pass
```
```


class MockUserRepository(DatabaseRepository[UserModel, UUID]):```

"""Mock user repository for testing."""
``````

```
```

_users: Dict[UUID, UserModel] = {}
``````

```
```

@classmethod
async def get(cls, **kwargs: Any) -> Optional[UserModel]:```

"""Get a user by ID."""
user_id = kwargs.get('id')
return cls._users.get(user_id)
```
``````

```
```

# Implement other methods...
```
```

## Future Improvements

Future improvements to the database protocol interfaces include:

1. Strengthen type annotations for better static type checking
2. Add more specialized protocols for specific database operations
3. Create protocol validation tests to ensure implementations correctly adhere to contracts
4. Implement adapters for different database backends (e.g., MongoDB, DynamoDB)