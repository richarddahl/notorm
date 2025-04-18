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

---

By implementing this comprehensive plan, UNO will emerge as a cohesive, modern framework built on solid architectural principles, with no legacy code or backward compatibility layers to maintain. The result will be a clean, performant, and developer-friendly platform for building robust web API applications using domain-driven design and reactive principles.