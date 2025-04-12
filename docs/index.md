# Welcome to uno

uno is a comprehensive application framework for building data-driven applications with PostgreSQL and FastAPI. Despite its name, uno is NOT an ORM - it's a complete framework that goes well beyond traditional ORMs to provide a unified approach to database operations, API definition, and business logic.

The name "uno" (Spanish for "one") represents the unified nature of the framework, bringing together database, API, and business logic in a cohesive but loosely coupled system.

## Key Features

- **Unified Database Management**: Centralized approach to database connection management with support for both synchronous and asynchronous operations
- **Domain-Driven Design**: Comprehensive DDD implementation with entities, aggregates, value objects, repositories, and domain services
- **Event-Driven Architecture**: Robust event system with topic-based routing, event persistence, and both sync and async handlers
- **SQL Generation**: Powerful SQL emitters for creating and managing database objects
- **API Integration**: FastAPI endpoint factory for quickly building REST APIs
- **Schema Management**: Advanced schema generation and validation
- **Business Logic Layer**: Clean separation of business logic from database operations with both UnoObj and Dependency Injection patterns
- **Bounded Contexts**: Strategic design with explicit bounded contexts and context mapping
- **Authorization System**: Built-in user and permission management
- **Advanced Filtering**: Dynamic query building with support for complex filters
- **Workflow Management**: Support for complex business workflows and state transitions
- **Metadata Management**: Track relationships between entities
- **PostgreSQL Integration**: Leverages PostgreSQL-specific features like JSONB, ULID, and row-level security
- **Comprehensive Error Handling**: Structured error handling with error codes, contextual information, and Result pattern
- **Resource Management**: Connection pooling, circuit breakers, and resource lifecycle management
- **Performance Optimization**: Query caching, dataloader pattern, and streaming for large results

## Getting Started

To get started with uno, check out the [Getting Started](getting_started.md) guide. For a deeper understanding of the framework's architecture, see the [Architecture Overview](architecture/overview.md).

For information about the new dependency injection system, see the [Dependencies Overview](dependencies/overview.md) and [Hybrid Architecture](dependencies/hybrid_approach.md) guides. For details about the Domain-Driven Design implementation, see the [Domain-Driven Design](architecture/domain_driven_design.md) and [Bounded Contexts](architecture/bounded_contexts.md) documentation. To learn about the Event-Driven Architecture, see the [Event-Driven Architecture](architecture/event_driven_architecture.md) guide.

For information about the error handling framework, see the [Error Handling Overview](error_handling/overview.md).

## Layered Architecture

uno is built on a layered architecture aligned with Domain-Driven Design principles:

1. **Domain Layer**: Contains the business logic and domain model
   - `Entity`, `AggregateRoot`, `ValueObject`: Core domain model components
   - `DomainService`: Business logic that doesn't fit in entities
   - `Repository`: Interfaces for data access (domain-specific)
   - `DomainEvent`, `EventBus`, `EventStore`: Event-driven architecture components

2. **Application Layer**: Coordinates the domain objects to perform tasks
   - `UnoObj`: Pydantic-based models with business logic
   - `AggregateService`: Manages complex domain operations with transaction support
   - `UnitOfWork`: Transaction management across multiple repositories
   - `EventBus`: Facilitates communication between bounded contexts
   - `ErrorCatalog`: Centralized registry of error codes
   - `Result`: Functional error handling with Success/Failure pattern

3. **Infrastructure Layer**: Provides technical capabilities
   - `UnoModel`: SQLAlchemy-based model for database mapping
   - `DatabaseFactory`: Centralized factory for database connections
   - `UnoDBRepository`: Implementation of repositories with database access
   - `SQL Emitters`: Components that generate SQL for database objects
   - `ResourceManager`: Manages resource lifecycle and circuit breakers
   - `ConnectionPool`: Manages database connection pooling

4. **Presentation Layer**: Handles user interaction
   - `UnoEndpoint`: FastAPI-based endpoints for operations
   - `EndpointFactory`: Automatically generates endpoints
   - `FilterManager`: Handles query parameters and filtering
   - `ErrorHandler`: Maps domain errors to HTTP responses