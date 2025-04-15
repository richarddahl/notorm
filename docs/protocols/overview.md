# Protocol-Based Design

The uno framework is built on a foundation of protocol-based design, leveraging Python's Protocol typing to create a modular, loosely coupled architecture. This approach allows for increased flexibility, testability, and maintainability.

## What are Protocols?

Protocols in Python (introduced in Python 3.8 via PEP 544) are a way to define interfaces or contracts that classes should fulfill. Unlike traditional abstract base classes (ABCs), protocols are based on structural typing rather than inheritance. This means a class can implicitly implement a protocol by simply providing the required methods and attributes, without explicitly inheriting from or registering with the protocol.

Key characteristics of protocols:

- **Structural typing**: Classes are considered compatible with a protocol if they have the required methods and attributes, regardless of inheritance
- **Loose coupling**: Dependencies can be expressed in terms of the behavior they need, not specific implementations
- **Type checking**: Static type checkers like mypy can verify protocol compliance at development time
- **Runtime checking**: The `@runtime_checkable` decorator enables isinstance/issubclass checks with protocols

## Core Protocol Categories

The uno framework defines protocols for various architectural patterns:

### Domain-Driven Design

- `Entity`: Base protocol for domain entities with identity
- `AggregateRoot`: Protocol for aggregate roots that can register and manage domain events
- `ValueObject`: Protocol for value objects with value equality semantics
- `Repository`: Protocol for persistence operations on specific entity types
- `DomainService`: Protocol for domain services that implement domain logic

### Event-Driven Architecture

- `DomainEvent`: Protocol for events that represent something significant that happened in the domain
- `EventHandler`: Protocol for components that respond to specific events
- `EventBus`: Protocol for event distribution system that connects events to handlers

### CQRS Pattern

- `Command`: Protocol for objects representing a request to change state
- `CommandHandler`: Protocol for components that handle specific commands
- `Query`: Protocol for objects representing a request for information
- `QueryHandler`: Protocol for components that handle specific queries

### Resource Management

- `UnitOfWork`: Protocol for transaction management
- `ResourceManager`: Protocol for acquiring and releasing resources
- `Cache`: Protocol for caching operations

### Configuration

- `ConfigProvider`: Protocol for accessing application configuration from various sources

### Messaging

- `MessagePublisher`: Protocol for publishing messages to topics or queues
- `MessageConsumer`: Protocol for subscribing to and processing messages

### Plugin Architecture

- `Plugin`: Protocol for modules that provide additional functionality
- `PluginManager`: Protocol for registering and managing plugins

## Benefits of Protocol-Based Design

1. **Dependency inversion**: Components depend on abstractions (protocols) rather than concrete implementations
2. **Easier testing**: Dependencies can be easily mocked or stubbed by implementing the required protocol
3. **Flexibility**: Implementations can be swapped without changing client code
4. **Clear contracts**: Protocols provide clear documentation of expected behavior
5. **Framework independence**: Business logic can be written independent of specific frameworks
6. **Gradual adoption**: Protocols can be introduced incrementally into existing codebases

## Pattern: Layered Design with Protocols

A key architectural pattern in uno is the use of protocols to define clear boundaries between layers:

```
┌───────────────────────┐   
│  API Layer            │   
│  (Controllers)        │   
└───────────┬───────────┘   ```
```

    │ Depends on   
```
```
┌───────────▼───────────┐   
│  Application Layer    │   
│  (Use Cases)          │   
└───────────┬───────────┘   ```
```

    │ Depends on   
```
```
┌───────────▼───────────┐ ◄─── Domain protocols define
│  Domain Layer         │      the core business model  
│  (Entities, Value     │      and operations
│   Objects, etc.)      │   
└───────────┬───────────┘   ```
```

    │ Uses via protocols   
```
```
┌───────────▼───────────┐   
│  Infrastructure Layer │   
│  (Repositories, etc.) │   
└───────────────────────┘   
```

In this layered architecture:

- Domain layer defines protocols for repositories and services it needs
- Infrastructure layer provides implementations of these protocols
- Domain layer doesn't depend on infrastructure details
- Application layer coordinates use cases through domain protocols
- API layer depends only on the application layer protocols

## Using Protocols in the uno Framework

### Defining Protocols

```python
from typing import Protocol, TypeVar, Optional

T = TypeVar('T')
KeyT = TypeVar('KeyT')

class Repository(Protocol[T, KeyT]):```

"""Protocol for repositories."""
``````

```
```

async def get(self, id: KeyT) -> Optional[T]:```

"""Get an entity by its ID."""
...
```
``````

```
```

async def save(self, entity: T) -> None:```

"""Save an entity."""
...
```
```
```

### Implementing Protocols

```python
from uuid import UUID
from domain.models import User

class PostgresUserRepository:```

"""Postgres implementation of the user repository."""
``````

```
```

async def get(self, id: UUID) -> Optional[User]:```

# Implementation using PostgreSQL
...
```
``````

```
```

async def save(self, user: User) -> None:```

# Implementation using PostgreSQL
...
```
```
```

### Depending on Protocols

```python
from domain.repositories import UserRepository

class UserService:```

"""Service for user operations."""
``````

```
```

def __init__(self, user_repository: UserRepository):```

self.user_repository = user_repository
```
``````

```
```

async def get_user(self, id: UUID) -> Optional[User]:```

return await self.user_repository.get(id)
```
```
```

## Protocol Validation

The uno framework includes a comprehensive protocol validation system to ensure that implementations correctly fulfill their protocol contracts. See the [Protocol Validation](../protocol_validation.md) page for details.