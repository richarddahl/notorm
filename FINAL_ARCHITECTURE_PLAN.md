# Unified Architecture Plan for UNO Framework

This document outlines the comprehensive plan to unify all interfaces and remove duplicative code in the UNO framework, creating a modern, loosely coupled, domain-driven, reactive platform for web API-based applications.

## Table of Contents

- [1. Core Architecture Components](#1-core-architecture-components)
  - [Repository Pattern](#repository-pattern)
  - [Service Pattern](#service-pattern)
  - [Event System](#event-system)
- [2. Infrastructure Integration](#2-infrastructure-integration)
  - [Database Access](#database-access)
  - [Dependency Injection](#dependency-injection)
  - [API Integration](#api-integration)
- [3. Domain Modeling](#3-domain-modeling)
  - [Entity Framework](#entity-framework)
  - [Validation Framework](#validation-framework)
- [4. Cross-Cutting Concerns](#4-cross-cutting-concerns)
  - [Error Handling](#error-handling)
  - [Configuration](#configuration)
  - [Logging and Monitoring](#logging-and-monitoring)
- [5. Implementation Plan](#5-implementation-plan)
  - [Phase 1: Core Infrastructure (2 weeks)](#phase-1-core-infrastructure-2-weeks)
  - [Phase 2: Domain Framework (2 weeks)](#phase-2-domain-framework-2-weeks)
  - [Phase 3: API Integration (2 weeks)](#phase-3-api-integration-2-weeks)
  - [Phase 4: Cross-Cutting Concerns (1 week)](#phase-4-cross-cutting-concerns-1-week)
  - [Phase 5: Legacy Removal (1 week)](#phase-5-legacy-removal-1-week)
- [6. Testing Strategy](#6-testing-strategy)
- [7. Documentation Plan](#7-documentation-plan)
- [8. Validation](#8-validation)
- [9. Specific Code Areas Needing Consolidation](#9-specific-code-areas-needing-consolidation)

## 1. Core Architecture Components

### Repository Pattern

**Current State:**
- Multiple repository base classes: `UnoRepository`, `BaseRepository`, `DomainRepository`
- Mix of SQLAlchemy and custom implementations
- Duplicated functionality across `sqlalchemy_repositories` and domain repositories

**Consolidation Plan:**
- Create unified `Repository` protocol in `domain/protocols`
- Implement a single `SqlRepository` that uses modern SQLAlchemy 2.0 async patterns
- Remove all legacy repository implementations
- Standardize on a single unit-of-work pattern for transactions

### Service Pattern

**Current State:**
- Multiple service base classes: `BaseService`, `UnoService`, `DomainService`
- Inconsistent patterns between service implementations
- Mix of result handling approaches

**Consolidation Plan:**
- Create unified `Service` protocol with standardized methods
- Implement `ApplicationService` for business logic with proper domain isolation
- Standardize on Result pattern for all service returns
- Remove all legacy service implementations

### Event System

**Current State:**
- Multiple event handlers: `EventHandler`, `DomainEventHandler`, `VectorEventHandler`
- Inconsistent event publication mechanisms
- Mix of sync and async approaches

**Consolidation Plan:**
- Create unified `EventBus` interface with standardized publish/subscribe methods
- Implement reactive event processing using modern async patterns
- Standardize on domain events as immutable value objects
- Create event store integration for event sourcing

## 2. Infrastructure Integration

### Database Access

**Current State:**
- Multiple database session patterns
- Mix of sync and async approaches
- Inconsistent connection pool management

**Consolidation Plan:**
- Create unified `DatabaseProvider` interface
- Standardize on asyncpg for async access, psycopg3 for sync when needed
- Implement connection pooling with proper health monitoring
- Remove legacy database access patterns

### Dependency Injection

**Current State:**
- Mixture of `inject` library and custom DI
- Multiple container implementations
- Inconsistent registration patterns

**Consolidation Plan:**
- Standardize on a single DI container pattern
- Create unified lifetime management (singleton, scoped, transient)
- Implement proper scope resolution for HTTP requests
- Remove all legacy DI components

### API Integration

**Current State:**
- Multiple endpoint patterns (`UnoEndpoint`, `ApiEndpoint`, `DomainEndpoint`)
- Inconsistent FastAPI integration
- Mix of route registration approaches

**Consolidation Plan:**
- Create unified `Endpoint` base class with consistent registration
- Implement proper dependency injection for endpoints
- Standardize on OpenAPI documentation generation
- Remove all legacy endpoint patterns

## 3. Domain Modeling

### Entity Framework

**Current State:**
- Mix of models: `UnoModel`, `Domain.Entity`, `BaseModel`
- Inconsistent identity and equality implementations
- Scattered value object implementations

**Consolidation Plan:**
- Create unified domain modeling framework
- Implement proper Entity, AggregateRoot, and ValueObject base classes
- Standardize on immutable value objects with proper equality
- Formalize identity management for entities

### Validation Framework

**Current State:**
- Mix of validation approaches: Pydantic, manual validation, domain validation
- Inconsistent error handling in validation
- Duplicated validation logic

**Consolidation Plan:**
- Create unified validation framework
- Leverage Pydantic v2 for schema validation
- Implement domain validation for business rules
- Standardize on Result pattern for validation results

## 4. Cross-Cutting Concerns

### Error Handling

**Current State:**
- Multiple error classes: `UnoError`, `BaseError`, domain-specific errors
- Inconsistent error propagation
- Mix of exception and Result pattern use

**Consolidation Plan:**
- Create unified error catalog with proper categorization
- Standardize on Result pattern for all operations that can fail
- Implement consistent error logging and monitoring
- Remove all legacy error handling

### Configuration

**Current State:**
- Already unified with ConfigProtocol (completed)
- Some remaining legacy access patterns

**Consolidation Plan:**
- Complete migration to unified ConfigProtocol
- Remove all deprecated access patterns
- Enhance configuration with environment-specific loading

### Logging and Monitoring

**Current State:**
- Inconsistent logging approaches
- Mix of monitoring integrations
- Duplicate telemetry code

**Consolidation Plan:**
- Create unified logging framework with structured logging
- Implement standardized metrics collection
- Create tracing infrastructure for request flow
- Consolidate health check mechanisms

## 5. Implementation Plan

### Phase 1: Core Infrastructure (2 weeks)

1. **Week 1**
   - Create unified protocols for all major components
   - Implement core DI container and lifetime management
   - Draft initial interface designs and protocol definitions

2. **Week 2**
   - Develop database access layer with proper connection pooling
   - Create event bus implementation with proper async support
   - Implement initial protocol validation scripts

### Phase 2: Domain Framework (2 weeks)

1. **Week 3**
   - Implement unified domain model base classes
   - Create repository pattern implementation
   - Develop initial unit tests for domain components

2. **Week 4**
   - Develop service pattern implementation
   - Implement validation framework
   - Create integration tests for domain components

### Phase 3: API Integration (2 weeks)

1. **Week 5**
   - Create unified endpoint framework
   - Implement CQRS pattern for HTTP endpoints
   - Develop initial API integration tests

2. **Week 6**
   - Develop OpenAPI documentation generation
   - Create standardized response formatting
   - Implement authentication and authorization integration

### Phase 4: Cross-Cutting Concerns (1 week)

1. **Week 7**
   - Implement error handling framework
   - Develop logging and monitoring infrastructure
   - Create consistent health check system
   - Implement configuration management

### Phase 5: Legacy Removal (1 week)

1. **Week 8**
   - Remove all deprecated code paths
   - Delete legacy modules and folders
   - Update all documentation and examples
   - Create migration scripts for existing code

## 6. Testing Strategy

1. **Unit Testing**
   - Create comprehensive unit test suite for all new components
   - Implement property-based testing for domain logic
   - Ensure >90% code coverage for core components

2. **Integration Testing**
   - Implement integration tests for component interactions
   - Create database integration tests with test containers
   - Test event propagation across system boundaries

3. **System Testing**
   - Develop system tests for end-to-end scenarios
   - Create API contract tests for external interfaces
   - Implement performance benchmarks for key components

4. **Performance Testing**
   - Create latency benchmarks for critical paths
   - Implement throughput tests for high-volume scenarios
   - Develop resource utilization metrics

## 7. Documentation Plan

1. **Architecture Documentation**
   - Create architectural overview document
   - Develop component reference documentation
   - Document architectural decisions and rationales

2. **Developer Guides**
   - Create migration guides for existing code
   - Develop quickstart guides for new projects
   - Document best practices and patterns

3. **API Documentation**
   - Implement automatic OpenAPI documentation
   - Create usage examples for all API endpoints
   - Document authentication and authorization requirements

4. **Example Applications**
   - Develop reference implementation with all major patterns
   - Create domain-specific example applications
   - Document common use cases and solutions

## 8. Validation

1. **Static Analysis**
   - Create protocol validation scripts for all major interfaces
   - Implement static analysis checks for pattern compliance
   - Develop custom linting rules for architectural compliance

2. **Runtime Validation**
   - Develop runtime validation for protocol implementations
   - Create telemetry for measuring adoption of unified patterns
   - Implement health checks for system integrity

3. **Performance Validation**
   - Create benchmark suite for key components
   - Implement load testing scenarios
   - Develop performance regression testing

4. **Security Validation**
   - Implement security testing for API endpoints
   - Create vulnerability scanning for dependencies
   - Develop security best practices documentation

## 9. Specific Code Areas Needing Consolidation

1. **Repository Pattern**
   - `uno/domain/repositories` vs `uno/dependencies/repository`
   - `uno/domain/repositories` vs `uno/domain/sqlalchemy_repositories`
   - Multiple unit-of-work implementations

2. **Service Pattern**
   - `uno/domain/service` vs `uno/dependencies/service`
   - Inconsistent service lifetime management
   - Duplicate service registration patterns

3. **Event System**
   - `uno/core/events` vs `uno/domain/event_dispatcher`
   - Multiple event bus implementations
   - Inconsistent event handling patterns

4. **API Layer**
   - `uno/api/endpoint` vs `uno/api/domain_endpoints`
   - Multiple route registration patterns
   - Duplicate response formatting code

5. **Data Transfer**
   - `uno/schema` vs `uno/dto`
   - Inconsistent validation approaches
   - Duplicate serialization code

6. **Error Handling**
   - `uno/core/errors` vs domain-specific error classes
   - Inconsistent error propagation
   - Mix of Result pattern and exceptions

7. **Async Patterns**
   - Multiple async patterns across the codebase
   - Inconsistent use of async/await
   - Mix of callback and coroutine approaches

8. **Domain Model**
   - Inconsistent entity identity management
   - Scattered value object implementations
   - Multiple aggregate root patterns


By implementing this comprehensive plan, UNO will emerge as a cohesive, modern framework built on solid architectural principles, with no legacy code or backward compatibility layers to maintain. The result will be a clean, performant, and developer-friendly platform for building robust web API applications using domain-driven design and reactive principles.

## Comments

Here’s a high‑level take based on your FINAL_ARCHITECTURE_PLAN.md and a quick tour of the current repo.  I’ve organized my comments into

   1. What I see today
   2. Key gaps against the plan
   3. A recommended roadmap of discrete tasks

—

   1. Current state
      • You’ve already invested heavily in Protocols (in src/uno/protocols.py, domain/protocols.py) and you’ve got dozens of “repository” and “service” implementations scattered under domain/, api/, infrastructure/, dependencies/,
etc.
      • There’s a mix of sync vs async, multiple DI approaches, multiple event‑bus/handler implementations, multiple DTO/Schema layers, and a half‑dozen endpoint factories/adapters under src/uno/api.
      • You have Pydantic in places, some custom validation code in domain/validation.py, a legacy migrations folder, and both SQLAlchemy and hand‑rolled database code.
      • Test coverage exists but is siloed (unit/api/core/domain directories).
   2. Gaps vs. “modern, loosely coupled, DDD, reactive”
      • Repository & Service: no single canonical base class or unit‑of‑work; implementations still live in three or four parallel hierarchies.
      • Event System: no unified async/reactive EventBus, event sourcing store, or immutable domain‑event model in one place.
      • DI: you’re mixing the inject library, your own “container” modules, and ad‑hoc factories—no single composition root.
      • API Layer: multiple endpoint registration patterns, no one BaseEndpoint class or coercion of responses into a standard envelope.
      • Domain Layer: Entities/Aggregates/ValueObjects are only protocols; there isn’t yet a core module that provides a concrete EntityBase, AggregateRootBase, ValueObjectBase, SpecificationBase, etc.
      • Reactive: everything is “async,” but there’s no “pull‑push” reactive model (streams, back‑pressure, Rx abstractions, etc.).
      • Cross‑cutting: error‑handling, logging, monitoring, health checks live in multiple places and aren’t wired into a single “middleware” pipeline.
   3. Recommended next steps (by slice)

Phase 0 – Organize & Codify
• Establish your folder‑level layering:
– src/uno/domain  (pure­‑DDD: Entities/Aggregates/ValueObjects/Specs/DomainServices)
– src/uno/application  (application services, DTOs/mappers, input validation)
– src/uno/infrastructure  (DB, messaging, event store, third‑party APIs)
– src/uno/interface  (HTTP endpoints, CLI, UIs)
• Move existing code into one of those four layers; remove or archive dead‐end modules.
• Verify your Protocol definitions cover every abstraction you need (Repository, Service, EventBus, Config, DBClient, etc.).

Phase 1 – Core Foundations (2 weeks)
• Dependency Injection
– Pick one container (e.g. di‑framework of your choice or FastAPI’s) and build a single CompositionRoot where everything gets registered.
– Define and register lifetime scopes (singleton, request, transient).
• Database & Repository
– Build a single SqlAlchemy 2.0 async engine/provider class.
– Implement RepositoryBase<U,T> + UnitOfWork that implements your RepositoryProtocol.
• Event Bus
– Create a single AsyncEventBus (e.g. backed by an asyncio.Queue or RxPY) that implements your EventBus protocol.
– Wire it into the UnitOfWork so that domain events on aggregates are published automatically at commit time.

Phase 2 – Domain Framework (2 weeks)
• Concrete Domain Base Classes
– EntityBase (with id, created_at, updated_at, event registry)
– AggregateRootBase (invariants, versioning)
– ValueObjectBase + PrimitiveValueObjectBase
– SpecificationBase (and, or, not)
– DomainService base that returns a CommandResult (success/failure + events)
• Migrate one small bounded context (e.g. your vector_search examples) onto those bases, prove green tests.

Phase 3 – Application & API (2 weeks)
• Application Services
– Define ApplicationService base that orchestrates domain calls, maps to/from DTO
– Centralize validation (Pydantic v2 for I/O, domain validation for business rules)
• HTTP Interface
– Create an EndpointBase (FastAPI router wrapper), standard response envelope, error‐handler middleware.
– Auto‑generate OpenAPI via Pydantic models.
– Migrate a handful of existing endpoints into the new pattern, delete legacy adapters.

Phase 4 – Cross‑Cutting & Reactive (1 week)
• Logging/Monitoring/Health
– Structured JSON logging, a metrics registry abstraction, a health endpoint.
• Reactive Enhancements
– For long‑running processes (e.g. event streams, background workers), layer on an Rx‑style API (async iterables or RxPY) so consumers can subscribe/pipeline/transform.
• Security, Config, Caching
– One ConfigProvider (env/file), one Auth middleware, one Cache abstraction.

Phase 5 – Cleanup & Docs (1 week)
• Remove all archived/legacy code paths.
• Update mkdocs YAML, regenerate docs, add quickstarts and examples.
• Flesh out migration guides (from old repositories/services to new ones).
• Lock in static analysis (mypy, flake8, custom lint rules for protocol compliance).

—
By slicing the work into small phases—first carving out your layers and DI anchor, then steadily migrating repos, domain, API, and finally cross‑cutting concerns—you’ll converge on a lean, testable, reactive, DDD‑style framework
with zero duplicated patterns and a single conformant implementation of every protocol.