# Domain-Driven Design Architecture

This document outlines the Domain-Driven Design (DDD) architecture for the Uno framework, explaining the key concepts, structure, and implementation patterns.

## Introduction to DDD

Domain-Driven Design is an approach to software development that focuses on:

1. Building a shared understanding of the domain between developers and domain experts
2. Focusing on the core domain and domain logic
3. Basing complex designs on a model of the domain
4. Collaborating with domain experts to improve the model and resolve domain-related issues

## Core DDD Concepts

### Bounded Contexts

Bounded Contexts are explicit boundaries within which a domain model applies. They help to:

- Clarify what belongs together and what doesn't
- Allow different models to evolve in different parts of the system
- Avoid conflicts between models in different contexts

### Ubiquitous Language

A common language shared between developers and domain experts within a bounded context, ensuring that:

- Terms have consistent meanings
- The code reflects the domain language
- Communication is clearer between all stakeholders

### Entities

Objects that have distinct identities that persist throughout the system's lifecycle, where:

- They are distinguished by their identity, not their attributes
- They may change over time but maintain the same identity
- Equality is determined by identity, not by attribute values

### Value Objects

Immutable objects that describe aspects of the domain with no conceptual identity, where:

- They are defined by their attributes
- They are immutable
- They can be shared freely
- Equality is determined by comparing all attributes

### Aggregates

Clusters of domain objects (entities and value objects) treated as a single unit, where:

- One entity serves as the aggregate root
- External references are only allowed to the aggregate root
- Changes to the aggregate must maintain internal consistency
- Aggregates are the basic unit of data storage and retrieval

### Domain Events

Notifications of significant occurrences in the domain, where:

- They represent something that has happened in the domain
- They are immutable and represent past actions
- They can trigger reactions from other parts of the system
- They are named in the past tense

### Repositories

Mechanisms for encapsulating storage, retrieval, and search of aggregates, where:

- They provide a collection-like interface for accessing domain objects
- They hide the details of the persistence infrastructure
- They work with entire aggregates, not parts of an aggregate

### Domain Services

Operations that don't conceptually belong to any entity or value object, where:

- They represent domain concepts that are processes or transformations
- They are stateless operations
- They often coordinate between multiple entities or aggregates

## Uno Framework DDD Architecture

The Uno framework implements DDD principles through a clear separation of layers and components.

### Layered Architecture

```
┌───────────────────────────────────────────────┐
│ User Interface / API Layer                    │
│ (Endpoints, Controllers, DTOs)                │
└─────────────────────┬─────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│ Application Layer                             │
│ (Application Services, Use Cases, Commands)   │
└─────────────────────┬─────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│ Domain Layer                                  │
│ (Entities, Value Objects, Domain Events,      │
│  Domain Services, Aggregates)                 │
└─────────────────────┬─────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│ Infrastructure Layer                          │
│ (Repositories, DB Access, External Services)  │
└───────────────────────────────────────────────┘
```

### Domain Layer

The domain layer contains:

- **Entities**: Objects with identity and lifecycle
- **Value Objects**: Immutable objects defined by their attributes
- **Aggregates**: Clusters of related objects with a root entity
- **Domain Events**: Notifications of important domain occurrences
- **Domain Services**: Stateless operations on multiple entities

### Application Layer

The application layer contains:

- **Application Services**: Orchestrators for use cases
- **Commands and Queries**: Request objects for operations
- **DTO Mapping**: Conversion between domain objects and DTOs

### Infrastructure Layer

The infrastructure layer contains:

- **Repositories**: Persistence mechanisms for aggregates
- **Database Access**: Low-level database operations
- **External Service Adapters**: Integration with external systems

### User Interface / API Layer

The API layer contains:

- **Endpoints**: API entry points
- **DTOs**: Data Transfer Objects for API communication
- **Validation**: Request validation logic

## Bounded Contexts in Uno Framework

The Uno framework is organized into the following bounded contexts:

### 1. Core Domain Context

Central domain concepts shared across the application:

- Base entity and value object classes
- Domain event infrastructure
- Repository interfaces
- Domain exceptions

### 2. Identity and Access Context

User identity and authorization concerns:

- Users, roles, and permissions
- Authentication mechanisms
- Access control policies

### 3. Metadata Context

Metadata and type system management:

- Type definitions and relationships
- Metadata attributes
- Tagging and categorization

### 4. Workflow Context

Business process and workflow management:

- Process definitions
- State machines
- Workflow execution

### 5. Messaging Context

Communication and notification systems:

- Message definitions
- Notification channels
- Subscription management

### 6. Reporting Context

Data analysis and reporting capabilities:

- Report definitions
- Data aggregation
- Export formats

## DDD Implementation Details

### Entity Implementation

```python
@dataclass
class Entity(Generic[KeyT]):
    """Base class for all domain entities."""
    
    id: KeyT
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def register_event(self, event: DomainEvent) -> None:
        """Register a domain event to be published after the entity is saved."""
        self._events.append(event)
    
    def clear_events(self) -> List[DomainEvent]:
        """Clear and return all registered events."""
        events = self._events.copy()
        self._events.clear()
        return events
```

### Aggregate Implementation

```python
@dataclass
class AggregateRoot(Entity[KeyT], Generic[KeyT]):
    """Base class for aggregate roots."""
    
    # Aggregate-specific behavior
    def check_invariants(self) -> None:
        """Check that all aggregate invariants are satisfied."""
        # Implement in derived classes
        pass
    
    def apply_changes(self) -> None:
        """Apply any pending changes and ensure consistency."""
        self.check_invariants()
```

### Value Object Implementation

```python
@dataclass(frozen=True)
class ValueObject:
    """Base class for value objects."""
    
    def equals(self, other: Any) -> bool:
        """Check if this value object equals another."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
```

### Repository Implementation

```python
class Repository(Generic[EntityT, KeyT]):
    """Base repository interface."""
    
    async def get(self, id: KeyT) -> Optional[EntityT]:
        """Get an entity by its ID."""
        ...
    
    async def save(self, entity: EntityT) -> None:
        """Save an entity."""
        # Publish any domain events
        events = entity.clear_events()
        for event in events:
            await self.publish_event(event)
        ...
    
    async def delete(self, id: KeyT) -> bool:
        """Delete an entity by its ID."""
        ...
    
    async def publish_event(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        ...
```

### Domain Service Implementation

```python
class DomainService:
    """Base class for domain services."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the domain service operation."""
        async with self.uow:
            result = await self._execute_internal(*args, **kwargs)
            await self.uow.commit()
            return result
    
    async def _execute_internal(self, *args, **kwargs) -> Any:
        """Internal implementation of the operation."""
        raise NotImplementedError()
```

## Migration Strategy

### Phase 1: Domain Model Extraction

1. Create core domain entity and value object base classes
2. Extract domain models from existing UnoObj classes
3. Organize models into appropriate bounded contexts
4. Introduce domain events for important state changes

### Phase 2: Repository Refactoring

1. Define repository interfaces for each aggregate type
2. Implement repositories with domain event publishing
3. Integrate with Unit of Work pattern
4. Update existing code to use repositories

### Phase 3: Service Extraction

1. Identify domain service operations
2. Extract service implementations from existing code
3. Apply proper dependency injection
4. Update client code to use the services

### Phase 4: Infrastructure Separation

1. Further separate domain logic from infrastructure
2. Refactor database access to work with aggregates
3. Implement proper transaction boundaries
4. Ensure domain invariants are enforced

## Conclusion

This Domain-Driven Design architecture provides a clear structure for organizing the Uno framework, focusing on the domain model and business logic while separating infrastructure concerns. By implementing these patterns, the framework will become more maintainable, expressive, and aligned with the problem domain.