# Uno Architecture Overview

The Uno framework follows a modern, clean architecture design that emphasizes separation of concerns, domain-driven design principles, and modern Python features. This document provides a high-level overview of the architectural patterns and design principles that form the foundation of Uno.

## Core Principles

Uno is built on several key architectural principles:

1. **Domain-Driven Design**: Business logic is encapsulated in a rich domain model with clear boundaries.
2. **Clean Architecture**: Dependencies point inward, with domain logic independent of infrastructure.
3. **SOLID Principles**: Particularly Interface Segregation and Dependency Inversion via Protocols.
4. **Protocol-Based Design**: Using Python's Protocol typing for flexible contracts.
5. **Async-First**: Modern async/await patterns throughout the codebase.
6. **Type Safety**: Comprehensive type hints with Python's typing system.
7. **Event-Driven Architecture**: Decoupled communication via domain events.

## Architectural Layers

Uno organizes code into distinct layers, each with specific responsibilities:

![Architecture Diagram](../assets/images/architecture_layers.png)

### Core Layer

The Core layer contains fundamental abstractions, interfaces (protocols), and utilities that are used across the framework:

- Protocol definitions for all major components
- Error handling with the Result pattern
- Common utilities and helpers
- Base class definitions

Key modules:
- `uno.core.protocols`: Protocol definitions
- `uno.core.errors`: Error handling framework
- `uno.core.events`: Event system
- `uno.core.uow`: Unit of Work pattern
- `uno.core.validation`: Validation framework

### Domain Layer

The Domain layer encapsulates business logic and domain models:

- Entities and value objects
- Domain services with core business rules
- Aggregates and domain events
- Repository interfaces
- Business rules and validation

Key modules:
- `uno.domain.entity`: Entity framework
- `uno.domain.entity.aggregate`: Aggregate root implementation
- `uno.domain.entity.specification`: Specification pattern
- `uno.domain.entity.service`: Domain service base classes

### Application Layer

The Application layer orchestrates domain operations and implements use cases:

- Application services
- Command and query handlers (CQRS)
- DTOs and mapping
- Business workflows
- Cross-cutting concerns

Key modules:
- `uno.application.dto`: Data Transfer Objects
- `uno.application.queries`: Query processing
- `uno.application.workflows`: Business workflows
- `uno.application.jobs`: Background job processing

### Infrastructure Layer

The Infrastructure layer provides concrete implementations of core interfaces:

- Database access (PostgreSQL/SQLAlchemy)
- Event bus implementations
- External service integrations
- Repository implementations
- Technical services

Key modules:
- `uno.infrastructure.database`: Database connectivity
- `uno.infrastructure.repositories`: Repository implementations
- `uno.infrastructure.services`: Technical service implementations
- `uno.infrastructure.security`: Authentication and authorization

### Interface Layer

The Interface layer exposes the application to external systems:

- API endpoints (FastAPI)
- CLI commands
- User interfaces
- Event handlers

Key modules:
- `uno.api.endpoint`: HTTP endpoints
- `uno.api.endpoint.cqrs`: CQRS pattern for endpoints
- `uno.api.endpoint.filter`: Filtering capabilities
- `uno.api.endpoint.factory`: Endpoint factory methods

## Key Patterns

### Repository Pattern

The Repository pattern provides a collection-like interface for domain entities:

```python
class Repository(Protocol[T, ID]):
    async def get_by_id(self, id: ID) -> Optional[T]: ...
    async def find_all(self) -> list[T]: ...
    async def save(self, entity: T) -> T: ...
    async def delete(self, entity: T) -> None: ...
```

### Unit of Work Pattern

The Unit of Work pattern manages transactions and coordinates changes:

```python
class UnitOfWork(Protocol):
    async def begin(self) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

### Result Pattern

The Result pattern provides a clear way to handle successes and failures:

```python
class Result(Generic[T, E]):
    @property
    def is_success(self) -> bool: ...
    
    @property
    def value(self) -> Optional[T]: ...
    
    @property
    def error(self) -> Optional[E]: ...
```

### CQRS Pattern

The Command Query Responsibility Segregation pattern separates reads from writes:

```python
class QueryHandler(Protocol[T, R]):
    async def handle(self, query: T) -> Result[R, E]: ...

class CommandHandler(Protocol[T, R]):
    async def handle(self, command: T) -> Result[R, E]: ...
```

### Event-Driven Pattern

The Event-Driven Pattern enables decoupled communication:

```python
class EventBus(Protocol):
    async def publish(self, event: Event) -> None: ...
    async def subscribe(self, event_type: str, handler: Callable) -> None: ...
```

## PostgreSQL Integration

Uno deeply integrates with PostgreSQL to leverage its advanced features:

1. **Custom Functions**: SQL functions for complex operations
2. **Triggers**: Automated reactions to data changes
3. **Row-Level Security**: Fine-grained access control
4. **Apache AGE**: Knowledge graph capabilities
5. **pgvector**: Vector storage for machine learning

## Dependency Injection

Uno uses a dependency injection system based on Python's Protocol typing:

```python
# Define a protocol
class ConfigProtocol(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def all(self) -> dict[str, Any]: ...

# Create an implementation
class EnvironmentConfig(ConfigProtocol):
    def get(self, key: str, default: Any = None) -> Any:
        return os.environ.get(key, default)
        
    def all(self) -> dict[str, Any]:
        return dict(os.environ)

# Register with container
container = Container()
container.register(ConfigProtocol, EnvironmentConfig())

# Use the dependency
def setup_app(config: ConfigProtocol = Injected(ConfigProtocol)):
    debug_mode = config.get("DEBUG", False)
```

## Event System

Uno's event system enables loosely coupled communication between components:

1. **Event Definition**: Events are immutable value objects with metadata
2. **Publishing**: Events are published to an event bus
3. **Subscription**: Handlers subscribe to specific event types
4. **Event Store**: Events can be persisted for event sourcing
5. **Event Bus**: Distributes events to subscribers

## API Framework

Uno provides a unified approach to API development:

1. **Endpoint Base Classes**: Standardized endpoint definitions
2. **CQRS Integration**: Command and query handling
3. **Response Formatting**: Consistent response structures
4. **Error Handling**: Automatic error translation
5. **Documentation**: Enhanced OpenAPI documentation

## Next Steps

To explore specific aspects of the architecture in more detail:

- [Domain-Driven Design](domain_driven_design.md)
- [Async-First Architecture](async_architecture.md)
- [Event-Driven Architecture](event_driven_architecture.md)
- [CQRS Pattern](cqrs.md)
- [Dependency Injection](dependency_injection.md)