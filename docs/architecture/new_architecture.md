# Unified Architecture Overview

This document provides an overview of the new unified architecture for the UNO framework.

## Core Principles

The architecture is designed around these core principles:

1. **Domain-Driven Design**: Clear separation of domain logic from infrastructure
2. **Clean Architecture**: Layered design with dependencies pointing inward
3. **SOLID Principles**: Especially Interface Segregation and Dependency Inversion
4. **Protocol-Based Interfaces**: Using Python's Protocol typing for flexible contracts
5. **Async-First**: Modern async/await patterns throughout

## Architectural Layers

The architecture is organized into these distinct layers:

![Architecture Diagram](../assets/images/architecture_layers.png)

### Core Layer

Contains fundamental interfaces (protocols) and utilities:

- Protocol definitions for all major components
- Error handling framework with Result pattern
- Common utilities and helpers

### Domain Layer

Contains business logic and domain models:

- Entities and value objects
- Domain services
- Business rules and validation
- Domain events

### Application Layer

Orchestrates domain operations and defines use cases:

- Application services
- Commands and queries (CQRS)
- DTOs and mapping
- Business workflows

### Infrastructure Layer

Provides implementations of core interfaces:

- Database access
- Event bus
- External integrations
- Persistence repositories

### Interface Layer

Exposes the application to external systems:

- API endpoints
- CLI commands
- User interfaces

### Cross-Cutting Layer

Handles concerns that span multiple layers:

- Logging
- Monitoring
- Security
- Validation

## Key Patterns

### Repository Pattern

```python
class Repository(Protocol[T, ID]):
    async def get_by_id(self, id: ID) -> Optional[T]: ...
    async def find_all(self) -> List[T]: ...
    async def save(self, entity: T) -> T: ...
    async def delete(self, entity: T) -> None: ...
```

### Result Pattern

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

```python
class QueryHandler(Protocol[T, R]):
    async def handle(self, query: T) -> Result[R]: ...

class CommandHandler(Protocol[T, R]):
    async def handle(self, command: T) -> Result[R]: ...
```

### Event-Driven Pattern

```python
class EventBus(Protocol):
    async def publish(self, event: Event) -> None: ...
    async def subscribe(self, event_type: str, handler: Callable) -> None: ...
```

## Implementation Guide

For implementation details, refer to:

- [Repository Structure](repository_structure.md)
- [Implementation Plan](implementation_plan.md)
- [Migration Guide](migration_guide.md)