# Uno Framework Documentation

Welcome to the Uno Framework documentation. uno is a platform for building data-driven applications with PostgreSQL and FastAPI.


For more information, see:

- [Documentation Index](./index.md) - Central index of all documentation resources  
- [Documentation Status Visualization](./project/documentation_status.md) - Visual overview of documentation coverage  
- [Documentation Development Plan](./project/documentation_plan.md) - Plan for ongoing documentation improvement  


## What is Uno?

Despite its name ("uno is not an ORM"), it's an application platform that goes well beyond traditional web frameworks to provide a unified approach to database operations, API definition, and business logic.

The name "uno" (Spanish for "one") represents the unified nature of the framework, bringing together database, API, and business logic in a cohesive but loosely coupled system.

## Key Features

- **Unified Database Management**: Centralized approach to database connection management with support for both synchronous and asynchronous operations
- **Domain-Driven Design**: Comprehensive DDD implementation with entities, aggregates, value objects, repositories, and domain services
- **Event-Driven Architecture**: Robust event system with topic-based routing, event persistence, and both sync and async handlers
- **Vector Search**: Integrated pgvector support for semantic search and embedding storage
- **SQL Generation**: Powerful SQL emitters for creating and managing database objects
- **API Integration**: FastAPI endpoint factory for quickly building REST APIs
- **Schema Management**: Advanced schema generation and validation
- **Business Logic Layer**: Clean separation of business logic from database operations with both UnoObj and Dependency Injection patterns
- **Authorization System**: Built-in user and permission management
- **Advanced Filtering**: Dynamic query building with support for complex filters
- **Type Safety**: Comprehensive type hinting and protocol validation
- **PostgreSQL Integration**: Leverages PostgreSQL-specific features like JSONB, ULID, and row-level security
- **Comprehensive Error Handling**: Structured error handling with error codes, contextual information, and Result pattern
- **Resource Management**: Connection pooling, circuit breakers, and resource lifecycle management

## Documentation Sections

- [**Getting Started**](getting_started.md): Installation and first steps
- [**Architecture**](architecture/overview.md): High-level architecture and design principles
- [**Data Layer**](database/overview.md): Database integration and management
- [**Business Logic**](business_logic/overview.md): Business logic implementation
- [**API Layer**](api/overview.md): API definition and integration
- [**Security**](security/overview.md): Authentication, authorization, and security features
- [**Vector Search**](vector_search/overview.md): Semantic search capabilities
- [**Error Handling**](error_handling/overview.md): Error management and reporting
- [**Type Safety**](type_safety/overview.md): Type hinting and protocol validation
- [**Dependency Injection**](dependency_injection/overview.md): Service location and dependency management
- [**Async Utilities**](async/overview.md): Asynchronous programming utilities
- [**Developer Tools**](developer_tools.md): Tools for development and debugging
- [**Documentation**](documentation_generation/overview.md): Documentation generation and standards

## Layered Architecture

Uno is built on a layered architecture aligned with Domain-Driven Design principles:

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

## Quick Start

To get started with Uno, follow these steps:

```bash
# Install with Docker (recommended)
./scripts/docker/start.sh

# Create a new database
python src/scripts/createdb.py

# Run the example application
python examples/ecommerce/app.py
```

For more detailed instructions, see the [Getting Started](getting_started.md) guide.