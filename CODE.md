# Notorm (UNO) Codebase Documentation

This document provides a comprehensive overview of the Notorm (UNO) codebase, explaining the purpose of each module and identifying core vs. auxiliary components.

## Overview

UNO ("uno is not an orm") is a Python library that integrates SQLAlchemy, Pydantic, and FastAPI with PostgreSQL 16. It follows a Domain-Driven Design (DDD) approach with a clear separation of concerns between domain logic, data access, and API presentation.

The codebase is undergoing significant modernization and refactoring to adopt a unified DDD approach, as evident from recent commits and structural changes.

## Core Modules

### uno/core

**Purpose**: Provides fundamental building blocks and patterns for the entire framework.  
**Status**: Core functionality, actively modernized.  
**Required**: Yes

Key components:
- `unified_events.py`: Canonical implementation of domain events system
- `di.py`: Dependency injection system
- `errors/`: Comprehensive error handling with Result pattern
- `result.py`: Functional error handling pattern implementation
- `domain.py`: Core domain model abstractions
- `async/`: Modern async utilities and patterns
- `protocols.py`: Type-safe interfaces using Python protocols
- `monitoring/`: Metrics collection and monitoring tools
- `uow.py`: Unit of Work pattern implementation

The presence of `.bak` files like `di.py.bak` and `cqrs.py.bak` indicates active refactoring.

### uno/domain

**Purpose**: Implements Domain-Driven Design patterns and abstractions.  
**Status**: Core functionality, central to the new architecture.  
**Required**: Yes

Key components:
- `core.py`: Entity, ValueObject, AggregateRoot implementations
- `repositories.py`: Data access abstraction with repository pattern
- `specifications.py`: Query specification pattern for domain objects
- `unified_services.py`: Standardized domain service patterns
- `unit_of_work.py`: Transaction boundary management
- `repository_adapter.py`: Adapter for repository migration
- `service_adapter.py`: Adapter for service migration

This module is actively being standardized to provide a unified DDD approach, with adapter classes to facilitate migration from older patterns.

### uno/api

**Purpose**: Framework integration with FastAPI and RESTful API creation.  
**Status**: Core functionality, being integrated with DDD approach.  
**Required**: Yes

Key components:
- `endpoint.py`: Base classes for API endpoints
- `endpoint_factory.py`: Factory for creating endpoints
- `domain_endpoints.py`: Domain-driven endpoint implementations
- `service_endpoint_adapter.py`: Bridges domain services with API endpoints
- `service_endpoint_factory.py`: Creates endpoints from domain services
- `error_handlers.py`: API-specific error handling

This module is being modernized to integrate with the unified domain services approach, with adapters to bridge domain and API layers.

### uno/dependencies

**Purpose**: Modern dependency injection system.  
**Status**: Core functionality, actively modernized.  
**Required**: Yes

Key components:
- `interfaces.py`: Protocol definitions for injectable components
- `modern_provider.py`: Modern DI container implementation
- `service.py`: Service registration and resolution
- `fastapi_integration.py`: Integration with FastAPI's dependency system
- `scoped_container.py`: Scoped service lifetime management

This module represents the modern DI approach, replacing older service provider patterns.

### uno/infrastructure

**Purpose**: Implementation of technical concerns separated from domain logic.  
**Status**: Core functionality, structured by technical domain.  
**Required**: Yes

Key subdirectories:
- `database/`: Database connectivity and ORM integration
- `sql/`: SQL generation and execution
- `security/`: Authentication, authorization, and encryption
- `caching/`: Caching strategies and implementations
- `reports/`: Reporting functionality
- `messaging/`: Messaging and event processing

These modules provide the technical implementation details, keeping the domain layer focused on business logic.

## Feature Modules

### uno/attributes

**Purpose**: Entity attribute management system.  
**Status**: Feature module, following DDD structure.  
**Required**: Optional feature

Key components:
- `entities.py`: Domain entities for attributes
- `repositories.py`: Data access for attributes
- `services.py`: Business logic for attributes
- `api_integration.py`: API integration for attributes

This module demonstrates the new DDD approach with clear separation of domain, repository, service, and API layers.

### uno/values

**Purpose**: Value management system.  
**Status**: Feature module, following DDD structure.  
**Required**: Optional feature

Similar structure to attributes, following the same DDD patterns.

### uno/meta

**Purpose**: Metadata management system.  
**Status**: Feature module, following DDD structure.  
**Required**: Optional feature

Similar structure to attributes, following the same DDD patterns.

### uno/ai

**Purpose**: AI and vector search capabilities.  
**Status**: Advanced feature module, somewhat experimental.  
**Required**: Optional feature

Key components:
- `semantic_search/`: Vector-based semantic search
- `recommendations/`: AI-powered recommendations
- `content_generation/`: AI content generation
- `graph_integration/`: Knowledge graph integration
- `vector_storage.py`: Vector storage abstraction

This is a more recent addition to the framework, providing advanced AI capabilities.

### uno/application

**Purpose**: Application services and use cases.  
**Status**: Supporting module, standard in DDD architecture.  
**Required**: Yes

Key subdirectories:
- `dto/`: Data Transfer Object management
- `queries/`: Query execution and management
- `workflows/`: Business process workflows
- `jobs/`: Background job processing

These modules provide higher-level application services that coordinate domain operations.

## Developer Tools and Utilities

### uno/devtools

**Purpose**: Development tools and utilities.  
**Status**: Supporting module, development-time only.  
**Required**: No, development only

Key components:
- `cli/`: Command-line interface for development tasks
- `codegen/`: Scaffolding and code generation
- `modeler/`: Visual data modeling tool
- `profiling/`: Performance profiling
- `debugging/`: Enhanced debugging tools

This module is purely for development convenience and not required for runtime operation.

### scripts/

**Purpose**: Command-line scripts for project management and operations.  
**Status**: Supporting utilities, some of which may be outdated.  
**Required**: No, development only

Key scripts categories:
- Database setup and management
- Code modernization and migration utilities
- Validation scripts
- Docker setup and management
- Developer environment setup

Some scripts may be remnants of previous approaches, but many are still useful for development and operations.

## Examples and Tests

### uno/examples

**Purpose**: Example applications and code demos.  
**Status**: Educational, recently updated to showcase DDD patterns.  
**Required**: No, educational only

Key examples:
- `ecommerce_app/`: Comprehensive e-commerce application example
  - Catalog context: Products, categories, variants, images
  - Order context: Orders, order items, statuses (placeholder)
  - Customer context: Customer profiles and accounts (placeholder)
  - Cart context: Shopping cart functionality (placeholder)
  - Shipping context: Shipping options and tracking (placeholder)
  - Payment context: Payment processing (placeholder)

This is a well-structured example application that demonstrates the full stack from domain model to API endpoints using domain-driven design principles.

### tests/

**Purpose**: Unit and integration tests.  
**Status**: Actively maintained, evolving with the codebase.  
**Required**: No, testing only

Key test categories:
- Unit tests for core and domain modules
- Integration tests for database and API functionality
- Performance benchmarks

Tests are categorized by module and type, with a clear distinction between unit and integration tests.

## Front-end and Static Resources

### src/static

**Purpose**: Front-end resources and web components.  
**Status**: Supporting module, used for admin UI.  
**Required**: Optional feature

Key components:
- `components/`: Web components using lit-html
- `assets/`: Images, scripts, and other static assets

This provides UI components for administrative interfaces and dashboards.

## Documentation

### docs/

**Purpose**: Framework documentation for developers.  
**Status**: Extensive documentation, actively maintained.  
**Required**: No, documentation only

Documentation is organized by module and feature, with architecture overviews, API documentation, and usage guides.

## Configuration and Environment

### docker/

**Purpose**: Docker configuration for development and testing.  
**Status**: Supporting infrastructure, Docker-first approach.  
**Required**: Yes for development

Key components:
- `Dockerfile`: Main Docker image definition
- `docker-compose.yaml`: Service composition
- `scripts/`: Docker setup and management scripts

The framework takes a Docker-first approach for development and testing, particularly for PostgreSQL.

### Project Configuration Files

- `pyproject.toml`: Python project configuration
- `pytest.ini`: Test configuration
- `mypy.ini`: Type checking configuration
- `mkdocs.yml`: Documentation site configuration

These files provide the standard configuration for the project's build, test, and documentation tools.

## Remnants of Previous Work

The following components appear to be remnants of previous approaches, in the process of being refactored or deprecated:

1. `.bak` files in the core module (e.g., `di.py.bak`, `cqrs.py.bak`) - Original versions of files that have been refactored
2. Legacy import paths with deprecation warnings
3. Many files in the `src/scripts/` directory related to modernization (e.g., `modernize_async.py`, `modernize_domain.py`)
4. Deployment-related code that's been moved or replaced (`src/uno/deployment/` has been deleted)
5. Schema management that's being unified (`src/uno/schema/` has been deleted)
6. Many proposals and documentation files in the PROPOSALS directory that have been deleted in the current branch
7. Parallel module implementations (original and modernized versions) to maintain compatibility during migration

##se  Parallel Module Implementations

This section outlines pairs or groups of modules that implement similar functionality through different approaches, likely to support a transition from legacy implementations to modernized versions.

### Dependency Injection

1. **DI Container Implementation**
   - Legacy: `/src/uno/core/di.py` - Original DI container using a custom implementation
   - Modern: `/src/uno/dependencies/modern_provider.py` - Modern DI system with additional features
   - Adapter: `/src/uno/core/di_adapter.py` - Adapter that bridges the old and new systems, with clear deprecation warnings

### Domain Events System

1. **Event Handling**
   - Legacy: Not present (likely removed, but referenced in imports)
   - Modern: `/src/uno/core/unified_events.py` - Comprehensive event system with both synchronous and asynchronous capabilities

### Unit of Work Pattern

1. **Unit of Work Implementation**
   - Legacy: `/src/uno/domain/unit_of_work.py` - Basic unit of work pattern implementation
   - Modern: `/src/uno/domain/unit_of_work_standardized.py` - Enhanced implementation with improved error handling and result types

### Repository Pattern

1. **Repository Implementation**
   - Legacy: `/src/uno/domain/repositories.py` - Basic repository pattern implementation
   - Modern: `/src/uno/domain/repository.py` - Enhanced repository with specification pattern support and improved error handling

### Specification Pattern

1. **Specifications Implementation**
   - Legacy: `/src/uno/domain/specifications.py` - Basic specification pattern implementation
   - Modern: `/src/uno/domain/specifications/base_specifications.py` - Modular implementation with enhanced features

2. **Specification Translators**
   - Legacy: `/src/uno/domain/specification_translators.py` - Monolithic translator implementation
   - Modern: `/src/uno/domain/specification_translators/postgresql_translator.py` - Specific database implementation in a modular structure

### Domain Services

1. **Domain Service Pattern**
   - Legacy: Legacy domain service classes (not directly visible in the files examined)
   - Modern: `/src/uno/domain/unified_services.py` - Enhanced domain services with standardized error handling and result types

### API Endpoints

1. **Endpoint Creation**
   - Legacy: `/src/uno/api/endpoint.py` and `/src/uno/api/endpoint_factory.py` - Base endpoint functionality
   - Modern: `/src/uno/api/service_endpoint_factory.py` - Integration with domain services for endpoint creation

2. **Service Endpoints**
   - Legacy: Likely through direct model access
   - Modern: `/src/uno/api/repository_adapter.py` - Adapters that connect repositories to endpoints
   - Modern: `/src/uno/api/service_endpoint_adapter.py` - Adapters for domain services

### Example Implementations

Several files in the codebase follow this naming pattern to demonstrate the transition:
- `/src/uno/core/examples/unified_events_example.py` vs `/src/uno/core/examples/events_example.py`
- `/src/uno/domain/vector_events_example.py` vs `/src/uno/domain/vector_example.py`

### Migration Notes

The parallel implementations generally exhibit these characteristics:

1. **Clear Module Organization**: Modern versions tend to be organized into subdirectories with specific concerns separated
2. **Improved Error Handling**: Modern implementations use Result types and standardized error patterns
3. **Better Type Safety**: Enhanced type annotations and protocol validations
4. **Adapter Pattern Usage**: Adapter classes allow for gradual migration
5. **Consistent Docstrings**: Modern versions have more comprehensive documentation
6. **Async-First Design**: Newer modules prioritize asynchronous operations with proper context management
7. **Event-Driven Architecture**: Modern implementations integrate with the unified event system

## Conclusion

The Notorm/UNO codebase is undergoing significant modernization to adopt a unified Domain-Driven Design approach. The core modules (`core`, `domain`, `api`, `dependencies`, `infrastructure`) form the foundation of the framework, while various feature modules provide optional functionality.

The recent refactoring focuses on standardizing the domain layer, unifying the event system, and providing clear adapters for integration between layers. The ecommerce_app example demonstrates the intended architecture and patterns for applications built with this framework.

The codebase shows a commitment to modern Python practices, with extensive use of type hints, protocols, and async features, while maintaining a clean separation of concerns according to DDD principles.