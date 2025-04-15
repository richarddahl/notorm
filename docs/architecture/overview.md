# Architecture Overview

uno is built on a modular architecture with three primary components that work together to provide a comprehensive framework for building data-driven applications. Additionally, the framework incorporates several modern architectural patterns to support complex application development.

## Three-Tier Architecture

### 1. Data Layer

The Data Layer manages database connections, schema definition, and data operations:

- **UnoModel**: SQLAlchemy-based model for defining database tables
- **DatabaseFactory**: Centralized factory for creating database connections
- **SQL Emitters**: Components that generate SQL for various database objects

### 2. Business Logic Layer

The Business Logic Layer handles validation, processing, and business rules:

- **UnoObj**: Pydantic-based models that encapsulate business logic
- **Registry**: Central registry for managing object relationships
- **Schema Manager**: Manages schema definitions and transformations

### 3. API Layer

The API Layer exposes functionality through REST endpoints:

- **UnoEndpoint**: FastAPI-based endpoints for CRUD operations
- **EndpointFactory**: Automatically generates endpoints from objects
- **Filter Manager**: Handles query parameters and filtering
- **EntityApi/AggregateApi**: Base classes for modern API endpoints
- **ServiceApiRegistry**: Registry for managing API endpoints
- **ContextProvider**: Extracts security context from HTTP requests

## Architectural Patterns

The Uno framework implements several modern architectural patterns to support complex application development:

### Domain-Driven Design (DDD)

The domain layer provides tools for implementing DDD concepts:

- **Entities and Value Objects**: Base classes for creating domain objects
- **Aggregates**: Support for aggregate roots and consistency boundaries
- **Repositories**: Abstract data access behind repository interfaces
- **Domain Events**: Domain events for capturing changes and intentions
- **Bounded Contexts**: Tools for defining and managing bounded contexts

### Event-Driven Architecture

The event system provides infrastructure for event-driven applications:

- **Domain Events**: Events that represent significant occurrences in the domain
- **Event Bus**: Publish-subscribe mechanism for event routing
- **Event Handlers**: Both synchronous and asynchronous event processing
- **Event Sourcing**: Optional rebuilding of aggregates from event streams
- **Topic-Based Routing**: Hierarchical event routing for complex systems

### Command Query Responsibility Segregation (CQRS)

The CQRS pattern separates read and write operations:

- **Commands**: Represent intentions to change state
- **Command Handlers**: Process commands and execute business logic
- **Queries**: Represent requests for information
- **Query Handlers**: Retrieve data without changing state
- **Read Models**: Optimized data structures for querying
- **SQL-Based Query Handlers**: Performance-optimized direct SQL queries

## Component Relationships

These architectural elements are designed to work together but are loosely coupled, allowing for flexibility in how they're used:

- **UnoModel** defines the database structure and provides data access methods
- **UnoObj** wraps a model with business logic and validation
- **UnoEndpoint** exposes UnoObj functionality through a REST API
- **Domain Entities** encapsulate business rules and invariants
- **Repositories** provide data access abstraction for domain entities
- **Command/Query Handlers** process user intentions and requests

## Framework Features

### Database Features

- **Centralized Connection Management**: Unified approach to database connections with support for both synchronous and asynchronous operations
- **Advanced SQL Generation**: SQL emitters for creating tables, functions, triggers, and more
- **Transaction Management**: Support for atomic operations with proper error handling
- **Migration Support**: Tools for managing database schema migrations
- **Unit of Work**: Transaction management across multiple repositories

### Business Logic Features

- **Data Validation**: Pydantic-based validation of data inputs and outputs
- **Business Rules**: Encapsulation of business rules within domain entities
- **Domain Events**: Event-based communication between domain components
- **Invariant Checking**: Enforcement of business rules and constraints
- **Object Relationships**: Management of object relationships through the Registry

### API Features

- **Automatic Endpoint Generation**: Creation of CRUD endpoints from UnoObj classes
- **Advanced Filtering**: Support for complex query parameters and filtering
- **Authentication and Authorization**: Built-in user and permission management
- **Documentation**: Automatic OpenAPI documentation generation
- **Command/Query Dispatching**: Routing of commands and queries to their handlers

## Design Principles

uno is built on several key design principles:

1. **Separation of Concerns**: Clear separation between data access, business logic, and API layers
2. **Loose Coupling**: Components can be used independently or together
3. **Composition over Inheritance**: Favor composition patterns over deep inheritance hierarchies
4. **Convention over Configuration**: Sensible defaults with the ability to override
5. **Type Safety**: Comprehensive type annotations for better IDE support and runtime validation
6. **PostgreSQL Integration**: First-class support for PostgreSQL-specific features
7. **Domain-First Design**: Emphasis on modeling the domain accurately
8. **Event-Driven Communication**: Preference for event-based communication between components

## Architecture Documentation

- [Database Layer](/docs/database/overview.md): Understand the database connection management
- [Models](/docs/models/overview.md): Learn how to define data models
- [Business Logic](/docs/business_logic/overview.md): Understand how to implement business logic with UnoObj
- [API Integration](/docs/api/overview.md): Learn how to expose your business logic through API endpoints
- [Domain-Driven Design](domain_driven_design.md): Implementing DDD with Uno
- [Event-Driven Architecture](event_driven_architecture.md): Using the event system
- [CQRS Pattern](cqrs.md): Implementing Command Query Responsibility Segregation
- [Application Services](application_services.md): Building the application service layer
