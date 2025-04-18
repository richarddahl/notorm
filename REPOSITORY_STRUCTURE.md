# UNO Framework Repository Structure

This document defines the target folder structure for the UNO framework following the architectural consolidation. This structure follows clean architecture and Domain-Driven Design principles.

## Overview

The repository will be organized into these main layers:

```
src/uno/
├── core/           # Core abstractions and utilities
├── domain/         # Domain model and business logic
├── application/    # Application services and use cases
├── infrastructure/ # External system integrations 
├── interface/      # API endpoints and UI
└── crosscutting/   # Cross-cutting concerns
```

## Detailed Structure

### Core Layer (`src/uno/core/`)

Contains fundamental abstractions, interfaces, and utilities that are used throughout the system.

```
core/
├── protocols/        # Core protocol definitions
│   ├── __init__.py
│   ├── repository.py
│   ├── service.py
│   ├── event.py
│   ├── entity.py
│   └── specification.py
├── errors/           # Error handling framework
│   ├── __init__.py
│   ├── result.py     # Result pattern implementation
│   ├── catalog.py    # Error catalog
│   └── exceptions.py # Base exceptions
├── config/           # Configuration system
│   ├── __init__.py
│   └── provider.py
├── utils/            # Shared utilities
│   ├── __init__.py
│   └── validation.py
├── async/            # Async utilities
│   ├── __init__.py
│   └── task_manager.py
└── __init__.py
```

### Domain Layer (`src/uno/domain/`)

Contains the business models, domain services, and business rules. Organized by bounded contexts.

```
domain/
├── common/           # Shared domain components
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   └── base_entity.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   └── base_value_object.py
│   └── specifications/
│       ├── __init__.py
│       └── base_specification.py
├── attributes/       # Attributes bounded context
│   ├── __init__.py
│   ├── entities.py
│   ├── value_objects.py
│   ├── repositories.py
│   ├── services.py
│   └── specifications.py
├── values/           # Values bounded context
│   ├── __init__.py
│   ├── entities.py
│   ├── value_objects.py
│   ├── repositories.py
│   ├── services.py
│   └── specifications.py
├── meta/             # Meta bounded context
│   ├── __init__.py
│   ├── entities.py
│   ├── repositories.py
│   └── services.py
├── vector_search/    # Vector search bounded context
│   ├── __init__.py
│   ├── entities.py
│   ├── repositories.py
│   ├── services.py
│   └── events.py
└── __init__.py
```

### Application Layer (`src/uno/application/`)

Contains application services, command handlers, and orchestrates domain operations.

```
application/
├── common/          # Shared application components
│   ├── __init__.py
│   ├── dto.py
│   └── mapper.py
├── attributes/      # Attributes application services
│   ├── __init__.py
│   ├── services.py
│   ├── commands.py
│   ├── queries.py
│   └── dtos.py
├── values/          # Values application services
│   ├── __init__.py
│   ├── services.py
│   ├── commands.py
│   ├── queries.py
│   └── dtos.py
├── workflows/       # Workflow application services
│   ├── __init__.py
│   ├── engine.py
│   ├── services.py
│   └── dtos.py
├── jobs/            # Job scheduling and processing
│   ├── __init__.py
│   ├── scheduler.py
│   ├── worker.py
│   └── dtos.py
└── __init__.py
```

### Infrastructure Layer (`src/uno/infrastructure/`)

Contains implementations for external system integrations, data access, messaging, etc.

```
infrastructure/
├── persistence/      # Database access
│   ├── __init__.py
│   ├── database.py
│   ├── connection_pool.py
│   ├── unit_of_work.py
│   └── repositories/
│       ├── __init__.py
│       ├── sqlalchemy_repository.py
│       └── in_memory_repository.py
├── messaging/        # Messaging infrastructure
│   ├── __init__.py
│   ├── event_bus.py
│   └── adapters/
│       ├── __init__.py
│       ├── postgres_adapter.py
│       └── redis_adapter.py
├── events/           # Event storage and handling
│   ├── __init__.py
│   ├── event_store.py
│   └── dispatchers.py
├── di/               # Dependency injection
│   ├── __init__.py
│   ├── container.py
│   └── provider.py
├── serialization/    # Serialization
│   ├── __init__.py
│   └── json.py
└── __init__.py
```

### Interface Layer (`src/uno/interface/`)

Contains API endpoints, UI elements, and other user interfaces.

```
interface/
├── api/              # API endpoints
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   ├── endpoint.py
│   │   └── controller.py
│   ├── attributes/
│   │   ├── __init__.py
│   │   └── endpoints.py
│   ├── values/
│   │   ├── __init__.py
│   │   └── endpoints.py
│   └── auth/
│       ├── __init__.py
│       └── endpoints.py
├── cli/              # Command-line interfaces
│   ├── __init__.py
│   └── commands.py
├── fastapi/          # FastAPI integration
│   ├── __init__.py
│   ├── app.py
│   ├── middleware.py
│   └── dependencies.py
└── __init__.py
```

### Cross-Cutting Layer (`src/uno/crosscutting/`)

Contains concerns that span multiple layers, such as logging, security, etc.

```
crosscutting/
├── logging/         # Logging framework
│   ├── __init__.py
│   └── logger.py
├── monitoring/      # Monitoring and metrics
│   ├── __init__.py
│   ├── metrics.py
│   └── health.py
├── security/        # Security services
│   ├── __init__.py
│   ├── authentication.py
│   └── authorization.py
├── validation/      # Validation framework
│   ├── __init__.py
│   └── validator.py
└── __init__.py
```

## Migration Strategy

The migration to this structure will be performed incrementally:

1. Create the core protocol interfaces first
2. Establish the basic infrastructure layer
3. Migrate domain models one bounded context at a time
4. Refactor application services to use the new domain models
5. Update interface components to use the new application services
6. Integrate cross-cutting concerns

Each bounded context will be migrated as a unit to minimize disruption and maintain functionality throughout the migration process.

## Naming Conventions

- **Directories**: Plural form for collections of related components (e.g., `protocols/`, `entities/`)
- **Files**: Singular form for base classes and interfaces, plural for collections of utilities
- **Classes**: PascalCase, with appropriate suffix indicating role (e.g., `Repository`, `Service`)
- **Methods**: snake_case, with verb prefixes indicating action (e.g., `get_`, `create_`)
- **Module Names**: Descriptive lower_case_with_underscores

## Implementation Notes

When implementing this structure:

1. Start with establishing the core protocols
2. Create base implementations for each major pattern
3. Use progressive migration to move existing code
4. Validate protocol compliance at each step
5. Maintain test coverage throughout

This structure facilitates a clean separation of concerns while allowing for modular development and testing. It aligns with modern architectural practices including Domain-Driven Design, Clean Architecture, and SOLID principles.