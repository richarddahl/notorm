# Welcome to uno

uno is a comprehensive application framework for building data-driven applications with PostgreSQL and FastAPI. Despite its name, uno is NOT an ORM - it's a complete framework that goes well beyond traditional ORMs to provide a unified approach to database operations, API definition, and business logic.

The name "uno" (Spanish for "one") represents the unified nature of the framework, bringing together database, API, and business logic in a cohesive but loosely coupled system.

## Key Features

- **Unified Database Management**: Centralized approach to database connection management with support for both synchronous and asynchronous operations
- **SQL Generation**: Powerful SQL emitters for creating and managing database objects
- **API Integration**: FastAPI endpoint factory for quickly building REST APIs
- **Schema Management**: Advanced schema generation and validation
- **Business Logic Layer**: Clean separation of business logic from database operations with both UnoObj and Dependency Injection patterns
- **Authorization System**: Built-in user and permission management
- **Advanced Filtering**: Dynamic query building with support for complex filters
- **Workflow Management**: Support for complex business workflows and state transitions
- **Metadata Management**: Track relationships between entities
- **PostgreSQL Integration**: Leverages PostgreSQL-specific features like JSONB, ULID, and row-level security

## Getting Started

To get started with uno, check out the [Getting Started](getting_started.md) guide. For a deeper understanding of the framework's architecture, see the [Architecture Overview](architecture/overview.md).

For information about the new dependency injection system, see the [Dependencies Overview](dependencies/overview.md) and [Hybrid Architecture](dependencies/hybrid_approach.md) guides.

## Three-Tier Architecture

uno is built on a modular architecture with three primary components:

1. **Data Layer**: Manages database connections, schema definition, and data operations
   - `UnoModel`: SQLAlchemy-based model for defining database tables
   - `DatabaseFactory`: Centralized factory for creating database connections
   - `SQL Emitters`: Components that generate SQL for various database objects

2. **Business Logic Layer**: Handles validation, processing, and business rules
   - `UnoObj`: Pydantic-based models that encapsulate business logic
   - `Repositories/Services`: Modern dependency injection pattern for complex domains
   - `Registry`: Central registry for managing object relationships
   - `Schema Manager`: Manages schema definitions and transformations

3. **API Layer**: Exposes functionality through REST endpoints
   - `UnoEndpoint`: FastAPI-based endpoints for CRUD operations
   - `EndpointFactory`: Automatically generates endpoints from objects
   - `Filter Manager`: Handles query parameters and filtering
