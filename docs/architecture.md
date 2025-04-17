<!-- docs/architecture.md -->
# Unified DDD Architecture for 'uno' Library

This document defines a unified, modern Domain‑Driven Design (DDD) architecture for the 'uno' library, a framework to build type‑safe Python web APIs.
It aligns and organizes existing modules into clear DDD layers, leverages Protocols over concrete base classes for interfaces, adopts Pydantic for
DTOs and settings, and removes unused code. The goal is to deliver a lean, extensible library for building production‑ready DDD applications.

## 1. Goals
- Offer a cohesive, type-safe DDD framework: Domain, Application, Infrastructure, API layers
- Consolidate and reuse existing modules under clear layer boundaries
- Use typing.Protocol for interface definitions (repositories, unit of work, event bus)
- Adopt Pydantic models for DTOs, schema validation, and settings management
- Provide CLI scaffolding to generate new bounded contexts and modules
- Remove unused code and modules without backward‑compatibility constraints
- Enforce dependency direction (inner layers independent of outer layers), strict typing, and testability

## 2. Layered Module Mapping

Align existing `src/uno` modules into the following DDD layers:

  Layer              | Modules / Files
  ------------------ | --------------------------------------------------------------
  Domain             | `uno/domain/`, `uno/values.py`, `uno/enums.py`, domain Events
  Application        | `uno/queries/`, `uno/jobs/`, `uno/workflows/`, DTOs in `uno/dto/`
  Infrastructure     | `uno/database/`, `uno/sql/`, `uno/messaging/`, `uno/caching/`, `uno/security/`
  API                | `uno/api/`, `uno/realtime/`, generate FastAPI controllers & schemas
  Core & Protocols   | `uno/core/`, `uno/protocols.py`, `uno/errors.py`, `uno/settings.py`, DI in `uno/dependencies/`

The root `uno/` package will be reorganized to match this structure: move or alias modules into new subpackages and remove unused folders
(e.g., `offline/`, `vector_search/`, `static/`, `templates/`).

## 3. Core DDD Layers
We follow Onion/Hexagonal architecture:

  - **Domain layer**
    - Entities, Value Objects, Aggregates, Domain Events
    - Pure business logic, no external dependencies
  - **Application layer**
    - Application Services (use‑cases), Commands, Queries, Unit of Work
    - Depends only on Domain interfaces (Protocols)
  - **Infrastructure layer**
    - Concrete implementations: Repositories (SQLAlchemy), EventBus adapters (Kafka, in‑process), Caching, Security
    - Depends on Application and Domain interfaces
  - **API layer**
    - Controllers (FastAPI), DTOs (Pydantic), routing, dependency injection
    - Depends on Application layer only

**Rule**: Deny imports from outer layers into inner layers. Use Protocols in inner layers to define abstractions.

## 4. Protocols and Core Utilities
Centralize shared interfaces and utilities:

- **uno/protocols.py**: Define Protocols for:
  - `Repository[T]`, `UnitOfWork`, `EventBus`, `CacheAdapter`, `AuthProvider`
  - CommandHandler, QueryHandler, EventHandler
- **uno/errors.py**: Standard exception hierarchy (DomainError, ApplicationError, InfrastructureError)
- **uno/settings.py**: Pydantic-based configuration management
- **uno/dependencies/**: DI container registrations, factory functions
- **uno/logging/**: Structured logging utilities


## 5. CLI Scaffolding
Use `devtools` or `scripts/` to scaffold new bounded contexts:
```bash
uno-cli create-context Order --output contexts/Order
```
The generated structure:
```
contexts/Order/
├── domain/
├── application/
├── infrastructure/
└── api/
```
Each folder includes a stub and README with guidelines.

## 6. Communication & Events
- **Domain Events**: Synchronous, in‑process, defined in Domain layer
- **Integration Events**: Asynchronous, versioned schemas (Protobuf/JSON-Schema), published via `EventBus` adapters
- Out-of-the-box adapters: in‑memory bus, Kafka, RabbitMQ
- Handlers registered via dependency injection in Infrastructure

## 7. Persistence & Data Access
- Define repository interfaces (Protocols) in Domain layer
- Implement repositories using SQLAlchemy in Infrastructure
- Use Alembic for migrations per context
- Optional CQRS: define read models in Application or dedicated `read_model/` package

## 8. Testing & Quality Gates
- Unit tests for Domain and Application layers (pytest + fixtures)
- Integration tests for Infrastructure adapters and CLI
- Static analysis: `black`, `isort`, `flake8`, `mypy --strict`
- Pre-commit hooks for formatting, linting, type checks

## 9. Refactor Plan & Milestones
1. **Module Reorganization**: Create `domain/`, `application/`, `infrastructure/`, `api/`, `core/` subpackages under `uno/` and move existing code accordingly.
2. **Protocol Definitions**: Extract interfaces into `uno/protocols.py`, replace ABCs with Protocols.
3. **Pydantic Adoption**: Convert DTOs, settings, and schema validations to Pydantic models.
4. **Dependency Injection**: Centralize in `uno/dependencies/`, register all adapters and services.
5. **Cleanup**: Remove unused modules (`offline/`, `vector_search/`, `static/`, `templates/`).
6. **CQRS & Events**: Consolidate read/write patterns, event bus adapters.
7. **Testing & CI**: Add strict mypy, pre-commit, and expand test coverage.
8. **Documentation & Examples**: Update docs and examples reflecting new structure.
9. **v1.0.0 Release**: Final review, tag, and publish.

---
_This document is the living architecture and roadmap for the DDD Python library. It will evolve as features are added and feedback is collected._