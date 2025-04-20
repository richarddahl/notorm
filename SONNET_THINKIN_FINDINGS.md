# Codebase Architecture & Component Analysis

This document presents the findings from analyzing the `uno` codebase, specifically focusing on its architectural patterns, core components, and their relevance for creating DDD-aligned, event-driven, loosely coupled, modern Python applications.

## Overview

The `uno` codebase (described as "uno is not an orm") implements a comprehensive framework for building domain-driven, event-driven applications with PostgreSQL 16, SQLAlchemy 2.0 ORM, FastAPI, and Pydantic 2. The architecture follows several modern design principles and patterns:

- **Domain-Driven Design (DDD)**: Clear separation of domain, application, and infrastructure layers
- **Command Query Responsibility Segregation (CQRS)**: Distinct query and command paths
- **Event-Driven Architecture**: Robust event system with publishers, subscribers, and an event bus
- **Dependency Injection**: Flexible DI container for managing dependencies
- **Unit of Work Pattern**: Consistent transaction and domain event handling

## Core Architecture Components

### 1. Domain Layer (`src/uno/domain`)

The domain layer contains the core business logic and domain entities, implementing DDD principles:

#### Key Components:

- **Entities**: Domain objects with identity and lifecycle (e.g., `BaseValue`, `BooleanValue`, etc.)
- **Value Objects**: Immutable objects representing concepts without identity
- **Aggregates**: Clusters of domain objects treated as a unit
- **Domain Events**: Immutable records of significant occurrences in the domain
- **Domain Services**: Operations that don't belong to a specific entity

```python
# Example domain entity from entities.py
@dataclass
class BaseValue(AggregateRoot[str]):
    """
    Base class for all value entities.
    This class contains common fields and validation for all value types.
    """
    name: str
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None
    __uno_model__: ClassVar[str] = ""

    def validate(self) -> None:
        """Validate the value."""
        if not self.name:
            raise ValidationError("Name cannot be empty")
```

The domain layer is carefully isolated from infrastructure concerns, ensuring business rules remain pure and free from technical implementation details.

### 2. Event System (`src/uno/core/events`)

The framework implements a robust event system that enables event-driven architecture:

#### Key Components:

- **Event Class**: Base class for domain events with standardized metadata
- **AsyncEventBus**: Asynchronous event bus implementation for publishing events
- **Event Handlers**: Subscribers to domain events
- **Event Store**: Persistence mechanism for domain events

```python
# Example from event.py
class Event(BaseModel):
    """
    Base class for all events in the UNO framework.
    Events are immutable value objects representing something that happened in the system.
    """
    model_config = ConfigDict(frozen=True)

    # Core event metadata
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(default_factory=lambda: _class_to_event_type(Event.__name__))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Tracing and correlation
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    # Domain context
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    aggregate_version: Optional[int] = None
```

This event system enables loose coupling between components, allowing different parts of the application to react to domain events without direct dependencies.

### 3. Repository Pattern (`src/uno/domain/repositories.py`)

The repository pattern provides an abstraction layer over data access:

#### Key Features:

- **Generic Repository**: Type-safe, reusable repository implementation
- **Domain-Specific Repositories**: Specialized repositories for different entity types
- **Async Operations**: Full support for asynchronous database operations
- **Result Type**: Error handling through a Result monad pattern

```python
class ValueRepository(UnoBaseRepository, Generic[T, M], ValueRepositoryProtocol[T]):
    """Generic repository for value operations."""

    async def get_by_id(
        self, value_id: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[T]]:
        """
        Get a value by ID.

        Args:
            value_id: The ID of the value to get
            session: Optional database session

        Returns:
            Result containing the value or None if not found
        """
        # Implementation...
```

The repository pattern effectively isolates domain code from the database implementation details, promoting looser coupling.

### 4. Unit of Work Pattern (`src/uno/core/uow`)

The Unit of Work pattern coordinates writing changes and maintaining consistency:

#### Key Features:

- **Transactional Boundary**: Clean separation of transaction boundaries
- **Event Collection**: Automatic collection of domain events
- **Event Publishing**: Events published only after successful commit
- **Rollback Handling**: Automatic rollback on exceptions

```python
class AbstractUnitOfWork(UnitOfWork, ABC):
    """
    Abstract base class for Unit of Work implementations.
    
    The Unit of Work pattern maintains a list of objects affected by a business
    transaction and coordinates writing out changes while ensuring consistency.
    """
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the Unit of Work context.
        
        If an exception occurred, the transaction will be rolled back.
        Otherwise, the transaction will be committed and events published.
        """
        try:
            if exc_type:
                self._logger.debug(
                    f"Rolling back transaction due to {exc_type.__name__}: {exc_val}"
                )
                await self.rollback()
            else:
                self._logger.debug("Committing transaction")
                await self.commit()
                await self.publish_events()
        except Exception as e:
            self._logger.error(f"Error in unit of work exit: {e}")
            await self.rollback()
            raise
```

The Unit of Work pattern ensures data consistency and atomic operations, providing a clear boundary for transactions.

### 5. CQRS Implementation (`src/uno/application/queries`)

The framework implements CQRS by separating query and command paths:

#### Key Components:

- **Query Executor**: Executes queries against the database
- **Query Caching**: Performance optimization for frequently used queries
- **Specialized Query Types**: Optimized queries for different use cases

```python
class QueryExecutor:
    """
    Executor for QueryModel instances.

    This class provides methods to execute saved QueryModel instances
    against the database to determine if records match the query criteria.
    It supports performance optimizations including caching and query planning.
    """
    
    async def execute_query(
        self,
        query: Query,
        session: AsyncSession | None = None,
        force_refresh: bool = False,
    ) -> Result[list[str]]:
        """
        Execute a query and return matching record IDs.
        """
        # Implementation...
```

The CQRS pattern enables independent scaling and optimization of read and write operations, enhancing performance.

### 6. Dependency Injection (`src/uno/core/di`)

The DI container manages dependencies and provides loose coupling:

#### Key Components:

- **DI Container**: Central registry for dependencies
- **Provider Interface**: Abstraction for dependency providers
- **Scoping Support**: Different scopes for dependencies (singleton, request, etc.)
- **FastAPI Integration**: Seamless integration with FastAPI's dependency injection

This DI implementation allows for better testability, maintainability, and loose coupling between components.

### 7. SQLAlchemy 2.0 & PostgreSQL Integration

The framework leverages SQLAlchemy 2.0's async features and PostgreSQL 16 capabilities:

#### Key Features:

- **Async Database Operations**: Full async support using SQLAlchemy 2.0
- **PostgreSQL-Specific Features**: Optimizations for PostgreSQL 16
- **Connection Pooling**: Efficient connection management
- **Migration Support**: Database migrations using Alembic

### 8. FastAPI & Pydantic 2 Integration

The framework integrates with FastAPI and Pydantic 2 for modern API development:

#### Key Features:

- **FastAPI Error Handlers**: Custom error handling for domain exceptions
- **Pydantic 2 Models**: Data validation using Pydantic 2
- **FastAPI Middleware**: Custom middleware for request/response processing
- **OpenAPI Documentation**: Automatic API documentation

## Practical Applications

This framework provides several benefits for building modern Python applications:

1. **Maintainability**: Clear separation of concerns and loose coupling
2. **Scalability**: CQRS and event-driven architecture enable independent scaling
3. **Performance**: Caching, query optimization, and async operations
4. **Testability**: Dependency injection and protocols facilitate testing
5. **Flexibility**: Modular design allows for easy extension

## Recommendations for Usage

1. **Start with Domain Modeling**: Define entities, value objects, and aggregates
2. **Use Event-Driven Communication**: Leverage events for loose coupling
3. **Implement CQRS**: Separate read and write operations
4. **Apply Repository Pattern**: Abstract data access through repositories
5. **Employ Unit of Work**: Manage transactions and data consistency

## Conclusion

The `uno` codebase represents a comprehensive framework for building DDD-aligned, event-driven, loosely coupled Python applications with PostgreSQL 16, SQLAlchemy 2.0, FastAPI, and Pydantic 2. Its architecture embodies modern design principles and provides a solid foundation for building complex applications.

The clean separation of domain logic from infrastructure concerns, combined with event-driven communication and CQRS, enables the development of maintainable, scalable, and performant applications.

## Areas for Improvement

Despite the overall strength of the architecture, several potential areas for improvement were identified:

1. **Documentation Cleanup**: The documentation still contains legacy references that need to be removed to avoid confusion for new developers.


3. **Testing Infrastructure**: The codebase would benefit from more extensive testing patterns and robust test fixtures to support comprehensive unit and integration testing of DDD components.


5. **Bounded Contexts Definition**: While bounded contexts are implemented, their separation could be more explicitly defined to better align with DDD principles.

6. **Performance Optimization Documentation**: Better documentation is needed on when and how to effectively use the implemented caching strategies and query optimizations.

7. **Developer Onboarding**: More clear examples or starter templates would help new developers quickly adopt the framework's patterns and practices.

8. **Coupling in Some Areas**: Despite the overall loose coupling design, there are instances where components have more dependencies than ideal, particularly in repository-entity interactions.

9. **Configuration Management**: A more standardized configuration approach would facilitate easier environment-specific deployments.

10. **Observability Infrastructure**: While logging is implemented, a more comprehensive observability solution (metrics, tracing, structured logging) would benefit applications built with this framework.
