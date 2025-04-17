
# Progress Summary

- Confirmed project uses a `src/` directory layout for proper package management.
- Defined core Protocols for key abstractions:
  - `Repository[T]` for data persistence.
  - `EventBus` for asynchronous event pub/sub.
  - `UnitOfWork` for transaction management.
  - `CacheAdapter` for caching mechanisms.
  - `AuthProvider` for authentication/authorization.
- Incorporated existing Protocols from `uno/protocols.py` and verified alignment.
- Implemented a minimal RabbitMQ `EventBus` using `aio_pika`, serving as a starting point for RabbitMQ messaging.
- Prepared the foundational structure for dependency injection, module reorganization, and Pydantic DTOs, as per the plan.

    This document defines a modern, layered Domain-Driven Design (DDD) architecture for the uno library, aimed at building type-safe, scalable Python web APIs.

    ## Goals

        * Establish a coherent, extensible framework organized around DDD layers: Domain, Application, Infrastructure, API.
        * Reorganize existing modules into these layers, removing unused code.
        * Use Protocols in interfaces instead of ABCs or concrete classes.
        * Leverage Pydantic models for DTOs and configuration.
        * Provide CLI scaffolding for bounded contexts.
        * Enforce clear dependency directions and testability.

    ## Module Mapping

    Align existing modules into DDD layers:

    ┌──────────────────┬───────────────────────────────────────────────────────────────────────────────┐
    │ Layer            │ Modules / Files                                                               │
    ├──────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ Domain           │ uno/domain/, uno/values.py, uno/enums.py, domain Events                       │
    ├──────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ Application      │ uno/queries/, uno/jobs/, uno/workflows/, uno/dto/                             │
    ├──────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ Infrastructure   │ uno/database/, uno/sql/, uno/messaging/, uno/caching/, uno/security/          │
    ├──────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ API              │ uno/api/, uno/realtime/, FastAPI controllers & schemas                        │
    ├──────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ Core & Protocols │ uno/core/, uno/protocols.py, uno/errors.py, uno/settings.py, uno/dependencies │
    └──────────────────┴───────────────────────────────────────────────────────────────────────────────┘

    ## Core DDD Layers

    We adopt Onion/Hexagonal architecture:

        * **Domain**: Entities, Value Objects, Domain Events, business rules.
        * **Application**: Use cases, services, commands, queries, based only on domain interfaces.
        * **Infrastructure**: Repositories, messaging, storage, external APIs.
        * **API**: REST controllers, DTOs, route setup.

    Internal layers depend only on inner layers; use Protocols to define abstractions.

    ## Protocols and Utilities

    Centralize shared interfaces in uno/protocols.py, e.g., Repository[T], UnitOfWork, EventBus, CacheAdapter, AuthProvider.
    Define error hierarchies in uno/errors.py, configs in uno/settings.py (Pydantic).
    Set up Dependency Injection and logging utilities.

    ## CLI and Scaffolding

    Use CLI tools to generate new contexts:

        uno-cli create-context Order --output contexts/Order

    Creates folder structure with domain, application, infrastructure, api.
    Each folder includes a stub and README with guidelines.

    ## Messaging & Events

        * Domain events, async integration events via EventBus with adapters (in-memory, Kafka).
        * Handlers registered via Dependency Injection.

    ## Persistence

        * Repository interfaces in Domain, implementations using SQLAlchemy, Alembic migrations.
        * Optional CQRS with separate read models.

    ## Testing

        * Unit tests for domain and application layers.
        * Integration tests for infrastructure.
        * Use `pytest`, static analysis with `mypy`, `black`, `isort`, pre-commit hooks for code quality.

    ## Milestones

        1. Module reorganization
        2. Protocol extraction
        3. Pydantic DTOs
        4. Dependency registration
        5. Code cleanup
        6. Event & CQRS consolidation
        7. Testing & CI
        8. Documentation updates
        9. Release v1.0

    ### 1. Module Reorganization

        * Create directories:
            * `uno/domain/` for domain entities, value objects, domain events

            * `uno/application/` for use cases, commands, queries, services

            * `uno/infrastructure/` for repositories, database, messaging, caching, external integrations

            * `uno/api/` for FastAPI controllers, schemas, route setup

            * `uno/core/` for core utilities, Protocols, errors, settings, DI
        * Move code files from existing locations into these directories based on their responsibility.
        * Remove unused modules and code (like static assets, old vector search, other unrelated modules).

    ### 2. Define Protocols

        * In `uno/protocols.py`, define interfaces for core abstractions:
            * `Repository[T]` with methods: add, get, list, remove, etc.

            * `UnitOfWork` with commit, rollback.

            * `EventBus` with publish, subscribe.

            * `CacheAdapter` with get, set, delete.

            * `AuthProvider` with authenticate, authorize.
        * Update existing service and repository code to depend on these Protocols instead of concrete classes or ABCs.

    ### 3. Refactor Interfaces and Implementations

        * Replace existing abstract base classes with Protocols where appropriate.
        * In Infrastructure, implement repositories and adapters conforming to Protocols.
        * Ensure all dependencies are injected via the interfaces, enabling easy testing and swapping implementations.

    ### 4. Convert DTOs and Configurations to Pydantic

        * Migrate existing DTOs, request/response schemas to Pydantic models.
        * Convert configuration settings to Pydantic-based `Settings` class with environment variable support.
        * Update validation logic to use Pydantic validation rather than custom or legacy methods.

    ### 5. Setup Dependency Injection

        * In `uno/dependencies.py`, register all service implementations and Protocols.
        * Use a DI container or manual registration pattern.
        * Provide factory functions for repositories, event buses, cache, security, and other integrations.

    ### 6. Add CLI scaffolding

        * Create commands such as `create-context` that generate a new context folder with a predefined structure:      contexts/
              └── Order/
                  ├── domain/
                  ├── application/
                  ├── infrastructure/
                  └── api/
        * Include stub files and README guidance in each folder.

    ### 7. Set up Messaging & Events

        * Implement domain events in the domain layer.
        * Implement async event handlers and an event bus in infrastructure.
        * Integrate with external message brokers (Kafka, RabbitMQ) via adapters.

    ### 8. Configure Persistence and Migrations

        * Define repository interfaces in Domain.
        * Implement SQLAlchemy repositories in Infrastructure.
        * Set up Alembic for database migrations, and establish naming conventions.

    ### 9. Testing Strategy

        * Write unit tests for inner layers, mocking dependencies via Protocols.
        * Write integration tests for infrastructure components and CLI commands.
        * Enforce static typing with `mypy` and code quality with pre-commit hooks.

    ### 10. Document and update

        * Update the architecture.md to reflect the new structure, protocols, and best practices.
        * Create example usage, REST endpoints, and documentation/tutorials.

    ### 11. Final review & release

        * Conduct thorough testing and code review.
        * Tag the initial `v1.0` release once stability is achieved.
        * Continue to iterate and improve based on feedback.


    Living document, update as features evolve.