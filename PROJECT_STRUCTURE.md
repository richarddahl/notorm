# Notorm Project Structure

This document outlines the architecture and file structure of the Notorm framework, which implements a modern Python application development framework following Domain-Driven Design principles.

## Overview

Notorm is a comprehensive framework that provides:

- Domain-Driven Design architecture
- Result monad pattern for error handling
- Event-driven communication via an event bus
- SQLAlchemy 2.0 ORM for persistence
- Pydantic 2.0 for data validation and DTOs
- Dependency injection system
- Structured JSON logging
- PostgreSQL 16 for relational data
- Apache AGE for knowledge graph capabilities
- PGVector for vector embeddings storage

The framework follows a hexagonal architecture pattern (also known as ports and adapters), with clear separation between domain, application, and infrastructure layers.

## Directory Structure

notorm/
├── src/
│   └── uno/
│       ├── __init__.py
│       ├── core/                       # Core framework components
│       │   ├── __init__.py
│       │   ├── bootstrap.py            # App initialization
│       │   ├── protocols/              # Interface protocols
│       │   │   ├── __init__.py
│       │   │   ├── entity.py           # Entity protocol
│       │   │   └── repository.py       # Repository protocol
│       │   ├── errors/                 # Error handling system
│       │   │   ├── __init__.py
│       │   │   ├── result.py           # Result monad implementation
│       │   │   ├── framework.py        # Error framework (ErrorDetail, etc.)
│       │   │   ├── catalog.py          # Error code registry
│       │   │   ├── core_errors.py      # Framework-level error definitions
│       │   │   ├── result_utils.py     # Helper functions for Result objects
│       │   │   ├── logging_config.py   # Structured logging configuration
│       │   │   └── base.py             # Base error classes
│       │   └── di/                     # Dependency injection
│       │       ├── __init__.py
│       │       ├── container.py        # DI container
│       │       └── providers.py        # Service providers
│       ├── domain/                     # Domain model
│       │   ├── __init__.py
│       │   ├── core.py                 # Base domain abstractions (entities, VOs)
│       │   ├── events/                 # Domain events
│       │   │   ├── __init__.py
│       │   │   └── dispatcher.py       # Domain event dispatcher
│       │   └── vector/                 # Vector space domain objects
│       │       └── __init__.py
│       ├── infrastructure/             # Infrastructure components
│       │   ├── __init__.py
│       │   ├── db/                     # Database concerns
│       │   │   ├── __init__.py
│       │   │   ├── session.py          # SQLAlchemy session management 
│       │   │   ├── base_repository.py  # Base repository implementation
│       │   │   ├── unit_of_work.py     # Unit of work pattern
│       │   │   ├── vector/             # Vector store (pgvector)
│       │   │   │   └── repository.py
│       │   │   ├── graph/              # Knowledge graph (AGE)
│       │   │   │   └── repository.py
│       │   │   └── migrations/         # DB migrations
│       │   ├── events/                 # Event bus implementation
│       │   │   ├── __init__.py
│       │   │   └── bus.py              # Event bus
│       │   └── logging/                # Logging infrastructure
│       │       └── __init__.py
│       ├── application/                # Application layer
│       │   ├── __init__.py
│       │   ├── services/               # Application services
│       │   │   └── __init__.py
│       │   ├── commands/               # CQRS command handlers
│       │   │   └── __init__.py
│       │   ├── queries/                # CQRS query handlers
│       │   │   └── __init__.py
│       │   └── dtos/                   # Pydantic data transfer objects
│       │       └── __init__.py
│       ├── api/                        # API layer
│       │   ├── __init__.py
│       │   ├── endpoint/               # API endpoints
│       │   │   ├── __init__.py
│       │   │   ├── response.py         # Response formatting
│       │   │   └── router/             # FastAPI routers
│       │   │       ├── __init__.py
│       │   │       └── v1/             # API v1 endpoints
│       │   ├── middleware/             # API middleware
│       │   │   └── __init__.py
│       │   └── dependencies/           # FastAPI dependencies
│       │       └── __init__.py
│       ├── reports/                    # Reporting module 
│       │   ├── __init__.py
│       │   └── dtos.py                 # Report DTOs
│       └── ui/                         # UI layer
│           ├── static/                 # Static assets
│           ├── components/             # Web components
│           │   ├── base/               # Base components
│           │   └── views/              # Page view components
│           └── services/               # UI services
│               └── api.ts              # API client services
├── tests/                             
│   ├── __init__.py
│   ├── conftest.py                     # Test configurations and fixtures
│   ├── unit/                           # Unit tests
│   │   └── __init__.py
│   └── integration/                    # Integration tests
│       ├── __init__.py
│       ├── test_vector_search.py
│       └── test_api_endpoints.py
├── scripts/                           
│   ├── __init__.py
│   ├── createdb.py                     # Database creation script
│   ├── common/                         # Common script utilities
│   │   └── functions.sh
│   ├── docker/                         # Docker automation
│   │   └── test/
│   │       └── setup.sh                # Setup test containers
│   └── ci/                             # CI/CD scripts
│       └── test.sh                     # Test automation
├── pyproject.toml                      # Project configuration
└── README.md

## Architecture Components

### Core Layer

The foundation of the application framework, providing the essential building blocks.

#### Protocols

Defines structural interfaces using Python's Protocol typing system:

- `EntityProtocol`: Contract for domain entities with identity
- `RepositoryProtocol`: Contract for data access objects

#### Error Handling

A comprehensive error system using the Result monad pattern:

- `Result[T, E]`: Represents either success or failure outcomes
- `Success[T]`: Container for successful operations
- `Failure[E]`: Container for error conditions
- Error catalog with standardized error codes and detailed error information
- Context-specific error handling with detailed logging

#### Dependency Injection

A clean DI system for managing component dependencies:

- `Container`: Central service container
- Providers for different service types
- Support for scoped instances (request, singleton, transient)

### Domain Layer

Contains the core business logic and data models.

- Rich domain entities with encapsulated behavior
- Value objects for attribute management
- Domain events for state change propagation
- Aggregate roots to enforce consistency boundaries

### Infrastructure Layer

Implements technical capabilities and external integrations.

#### Database Access

- SQLAlchemy 2.0 ORM integration
- Repository implementations
- Unit of Work pattern for transaction management
- Support for PostgreSQL 16
- PGVector integration for vector embeddings
- Apache AGE for graph database capabilities

#### Event System

- Event bus for publish-subscribe communication
- Domain event handlers
- Integration event propagation

### Application Layer

Orchestrates domain objects to accomplish specific use cases.

- CQRS pattern (Command Query Responsibility Segregation)
- Command handlers for state mutations
- Query handlers for data retrieval
- Pydantic 2.0 data transfer objects

### API Layer

Exposes functionality to external consumers.

- Standardized response formatting
- Error translation to API-friendly formats
- Request validation

## Test Architecture

- Unit tests for core components
- Integration tests with database fixtures
- Vector search specific tests that can be conditionally enabled
- Coverage reporting with badge generation

## CI/CD and Scripts

- Containerization support with Docker
- Automated testing pipelines
- Database initialization and migration scripts
- Common utility functions

## Key Design Patterns

1. **Domain-Driven Design**: Focus on core domain and domain logic
2. **Repository Pattern**: Data access abstraction
3. **Unit of Work**: Transaction management
4. **Result Monad**: Functional error handling
5. **CQRS**: Separation of read and write operations
6. **Event Sourcing**: State changes as a sequence of events
7. **Dependency Injection**: Loose coupling between components
8. **Protocol-oriented Programming**: Type safety through structural typing

## Using the Framework

When building applications with this framework:

1. Model your domain entities and value objects in the domain layer
2. Define repositories in the infrastructure layer
3. Create application services to orchestrate domain objects
4. Use the Result pattern for error handling
5. Emit domain events for cross-aggregate communication
6. Define DTOs for clean data transfer between layers

## Testing Approach

The framework provides comprehensive testing utilities:

- Unit test your domain logic in isolation
- Integration tests with database fixtures
- CI integration via test.sh script with multiple options:
  - `-t, --type`: Specify test type (unit, integration, all)
  - `-c, --coverage`: Generate test coverage reports
  - `-x, --xml`: Generate JUnit XML reports for CI systems
  - `-v, --verbose`: Enable verbose test output

## Extending the Framework

When extending the framework:

1. Follow the established architectural boundaries
2. Add new domain models to the domain layer
3. Implement new repositories in the infrastructure layer
4. Register components with the DI system
5. Configure error codes in the error catalog
6. Add appropriate test coverage
