# UNO Framework Implementation Plan

This document details the concrete steps required to implement the unified architecture described in FINAL_ARCHITECTURE_PLAN.md. The implementation is organized into phases with specific tasks, dependencies, estimated effort, and validation criteria.

## Table of Contents

- [Overview](#overview)
  - [Goals](#goals)
  - [Success Criteria](#success-criteria)
  - [Team Structure](#team-structure)
- [Phase 0: Preparation (1 week)](#phase-0-preparation-1-week)
- [Phase 1: Core Infrastructure (2 weeks)](#phase-1-core-infrastructure-2-weeks)
- [Phase 2: Domain Framework (2 weeks)](#phase-2-domain-framework-2-weeks)
- [Phase 3: API Integration (2 weeks)](#phase-3-api-integration-2-weeks)
- [Phase 4: Cross-Cutting Concerns (1 week)](#phase-4-cross-cutting-concerns-1-week)
- [Phase 5: Legacy Removal (1 week)](#phase-5-legacy-removal-1-week)
- [Testing and Validation Strategy](#testing-and-validation-strategy)
- [Migration Strategy](#migration-strategy)
- [Risk Assessment and Mitigation](#risk-assessment-and-mitigation)

## Overview

### Goals

1. Consolidate duplicate implementations across the codebase
2. Establish a clean, consistent architectural foundation
3. Implement modern async patterns throughout
4. Remove all legacy code with no backward compatibility layers
5. Ensure comprehensive test coverage and documentation

### Success Criteria

1. All protocol interfaces have a single canonical implementation
2. Zero deprecated or duplicated code paths
3. >90% test coverage for all core components
4. All components follow consistent patterns for async, error handling, and DI
5. Complete, generated documentation with examples

### Team Structure

- Core Infrastructure Team: 2 developers
- Domain Model Team: 2 developers
- API/Interface Team: 1 developer
- QA/Documentation Team: 1 developer

## Phase 0: Preparation (1 week)

### Week 0: Analysis and Setup

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **Codebase Audit** | Complete inventory of all duplicate implementations | 2 days | None | Inventory document with all duplication highlighted |
| **Protocol Validation** | Create script to validate protocol compliance | 2 days | None | Working script that identifies non-compliant implementations |
| **Repository Structure** | Establish final folder structure | 1 day | Codebase audit | Directory structure document with migration paths |
| **Test Harness** | Set up test infrastructure for new components | 1 day | Repository structure | Working CI pipeline with test reporting |
| **Documentation Framework** | Configure documentation generation | 1 day | Repository structure | Working doc generation pipeline |

**Deliverables:**
- Complete codebase inventory document
- Protocol validation script
- CI/CD pipeline updates
- Documentation generation setup
- Final folder structure blueprint

## Phase 1: Core Infrastructure (2 weeks)

### Week 1: Protocol Definitions

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **Define Core Protocols** | Create/refine protocol interfaces for Repository, Service, EventBus | 2 days | None | Static type checking passes |
| **DI Container** | Implement unified DI container with lifetime management | 3 days | Core protocols | Unit tests for container resolution |
| **Validation Framework** | Create core validation mechanisms with Result pattern | 2 days | None | Unit tests for validation cases |
| **Protocol Testing** | Create test fixtures and mocks for protocols | 1 day | Core protocols | Mock implementations pass protocol validation |

**Deliverables:**
- Complete protocol definitions in `uno/core/protocols/`
- Unified DI container implementation
- Validation framework with Result pattern
- Protocol test fixtures

### Week 2: Infrastructure Components

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **Database Provider** | Implement unified asyncpg-based DatabaseProvider | 2 days | Core protocols | Integration tests with test database |
| **Connection Pooling** | Create connection pool with health monitoring | 2 days | Database provider | Stress tests for pool behavior |
| **Event Bus** | Implement AsyncEventBus with pub/sub | 2 days | Core protocols | Unit tests for event propagation |
| **Unit of Work** | Create transaction management with event dispatching | 2 days | Database provider, Event bus | Integration tests for transaction patterns |

**Deliverables:**
- DatabaseProvider implementation
- Connection pool with health checks
- AsyncEventBus implementation
- UnitOfWork pattern with event integration

## Phase 2: Domain Framework (2 weeks)

### Week 3: Domain Foundations

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **Entity Base Classes** | Create Entity, AggregateRoot base implementations | 2 days | Core protocols | Unit tests for entity behavior |
| **Value Objects** | Implement ValueObject pattern with equality | 1 day | Core protocols | Unit tests for value semantics |
| **Specifications** | Create specification pattern implementation | 2 days | Core protocols | Unit tests for composite specifications |
| **Identity Management** | Implement ID generation and equality | 1 day | Entity base classes | Unit tests for identity behavior |
| **Domain Events** | Create domain event base classes | 1 day | Event bus | Unit tests for event registration |

**Deliverables:**
- Complete domain modeling framework in `uno/domain/`
- Entity and Aggregate base classes
- Value object implementation
- Specification framework
- Domain event system

### Week 4: Repository and Services

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **SqlRepository** | Implement SqlAlchemy 2.0 repository base | 3 days | Entity base, Unit of work | Integration tests with test database |
| **Repository Querying** | Create query builder for repositories | 2 days | SqlRepository | Unit tests for query building |
| **Service Base** | Implement application service pattern | 2 days | Repository base | Unit tests for service orchestration |
| **Domain Services** | Create domain service pattern | 1 day | Entity base | Unit tests for domain logic |

**Deliverables:**
- SqlRepository implementation
- Query builder for repositories
- Application service base class
- Domain service pattern

## Phase 3: API Integration (2 weeks)

### Week 5: API Foundations

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **Endpoint Base** | Create unified Endpoint base class | 2 days | Service base | Integration tests with test client |
| **Response Formatting** | Implement standardized response envelope | 1 day | Endpoint base | Unit tests for response formats |
| **Error Middleware** | Create error handling middleware | 2 days | Error framework | Integration tests for error paths |
| **Authentication** | Implement auth middleware | 1 day | Endpoint base | Integration tests with auth scenarios |
| **OpenAPI Generation** | Configure automatic API docs | 1 day | Endpoint base | Generated OpenAPI spec validation |

**Deliverables:**
- Endpoint base class
- Standardized response formatting
- Error handling middleware
- Authentication integration
- OpenAPI documentation generation

### Week 6: API Patterns

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **CQRS Implementation** | Create command/query handlers | 2 days | Service base | Unit tests for handler behavior |
| **Input Validation** | Integrate Pydantic validation | 1 day | Endpoint base | Integration tests for validation |
| **DTO Mapping** | Implement automatic DTO/entity mapping | 2 days | Entity base, Service base | Unit tests for mapping scenarios |
| **Pagination** | Create standardized pagination | 1 day | Response formatting | Integration tests for paged results |
| **Filtering** | Implement query parameter filtering | 1 day | Query builder | Integration tests for filtered results |

**Deliverables:**
- CQRS implementation
- Input validation integration
- DTO/entity mapping
- Pagination support
- Query parameter filtering

## Phase 4: Cross-Cutting Concerns (1 week)

### Week 7: Cross-Cutting Implementation

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **Error Framework** | Finalize error catalog and handling | 1 day | Result pattern | Unit tests for error scenarios |
| **Logging** | Implement structured logging | 1 day | None | Integration tests for log output |
| **Metrics** | Create metrics collection | 1 day | None | Dashboard verification |
| **Tracing** | Implement distributed tracing | 1 day | None | Trace visualization |
| **Health Checks** | Create health monitoring | 1 day | Connection pooling | Health endpoint tests |

**Deliverables:**
- Complete error framework
- Structured logging implementation
- Metrics collection
- Distributed tracing
- Health check system

## Phase 5: Legacy Removal (1 week)

### Week 8: Cleanup and Finalization

| Task | Description | Effort | Dependencies | Validation |
|------|-------------|--------|--------------|------------|
| **Migration Scripts** | Create code migration scripts | 2 days | All new components | Script execution success |
| **Legacy Code Removal** | Remove deprecated code paths | 2 days | Migration scripts | Build passes with no deprecated imports |
| **Documentation Update** | Update all documentation | 2 days | All new components | Doc generation success |
| **Example Applications** | Create reference implementations | 2 days | All new components | Working example apps |

**Deliverables:**
- Migration scripts for existing code
- Clean codebase with no legacy components
- Updated documentation
- Example application implementations

## Testing and Validation Strategy

### Unit Testing

- Implement tests for all new components (min. 90% coverage)
- Create property-based tests for domain logic
- Implement contract tests for all protocol implementations

### Integration Testing

- Database integration with test containers
- API contract testing with test client
- Event propagation testing
- Async behavior testing

### Performance Testing

- Create benchmarks for critical paths
- Implement load tests for high-throughput scenarios
- Measure resource utilization

### Validation Tools

- Create static analysis checks for architectural compliance
- Implement runtime monitoring for performance and errors
- Establish CI/CD pipeline for continuous validation

## Migration Strategy

### For Existing Code

1. **Parallel Implementation**: Create new components alongside existing ones
2. **Targeted Migration**: Migrate one module completely before moving to the next
3. **Progressive Replacement**: Replace leaf nodes first, then work up the dependency chain
4. **Feature Flags**: Use feature flags to control cutover to new implementations
5. **Documentation**: Create detailed migration guides for each component

### For New Development

1. Use the new architecture exclusively for all new features
2. Provide examples and templates for common patterns
3. Implement linting rules to enforce architectural guidelines

## Risk Assessment and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Schedule Overrun** | Medium | High | Break work into smaller chunks, prioritize core functionality |
| **Regression Bugs** | Medium | High | Maintain high test coverage, perform incremental replacements |
| **Performance Issues** | Low | Medium | Benchmark before/after, optimize critical paths |
| **Developer Adoption** | Medium | Medium | Create comprehensive docs, examples, and migration guides |
| **Integration Complexity** | High | Medium | Test integration points continuously, create clear boundaries |

## Progress Tracking

Use the protocol validation script to track adoption of the new architecture:

```
$ python src/scripts/validate_protocols.py --report

Protocol Compliance Report:
Repository: 24/45 implementations (53%)
Service: 18/32 implementations (56%)
EventBus: 2/4 implementations (50%)
...
```

Track coverage over time to ensure continuous progress toward 100% compliance.

## Conclusion

This implementation plan provides a roadmap to transform the UNO framework into a cohesive, modern architecture built on solid domain-driven design principles. By following this structured approach, with clear deliverables and validation criteria for each phase, we can systematically eliminate duplication and inconsistency while building a foundation that will support future growth and maintainability.

The plan balances the need for thoroughness with pragmatic timelines, allowing for progressive improvement while maintaining a functioning system throughout the transition. By focusing on core abstractions first and establishing clean interfaces between components, we create the flexibility to evolve implementation details as requirements change.



## Project Structure
Below is a suggested “four‑layer” structure to replace/augment the existing layout under src/uno. You can include this in your docs (for example in src/uno/ARCHITECTURE.md under a new “Layers” section, or as its own markdown file).

    src/uno/
    │
    ├── domain/               # ——— Domain Layer ———
    │   • Pure business logic, entities, value‑objects, specs, domain‑services
    │   ├── entities/         # Entity, AggregateRoot, ValueObject base classes + folder for sub‑domains
    │   ├── services/         # Stateless domain services (implement DomainServiceProtocol)
    │   ├── specifications/   # Specification<T> classes (and/or/not)
    │   ├── events/           # DomainEventProtocol + event definitions
    │   ├── factories/        # EntityFactoryProtocol implementations
    │   └── protocols.py      # Domain‑only Protocol interfaces (EntityProtocol, ValueObjectProtocol, etc.)
    │
    ├── application/          # ——— Application Layer ———
    │   • Application‑services, use‑case orchestration, DTO‐mappers, transactions
    │   ├── services/         # ApplicationService classes (use cases)
    │   ├── workflows/        # Orchestration or saga‑style workflows if needed
    │   ├── dto/              # Pydantic/Payload schemas, Command/Query DTOs
    │   ├── mappers/          # Map domain models ↔ DTOs
    │   └── composition.py    # Composition root: DI container, registrations for all protocols
    │
    ├── infrastructure/       # ——— Infrastructure Layer ———
    │   • Adapters for all external systems: DB, messaging, 3rd‑party APIs, file I/O
    │   ├── db/               # Database providers: SqlAlchemyEngine, connection pools
    │   ├── repositories/     # Concrete Repository<T> implementations (SqlRepository, InMemory, etc.)
    │   ├── eventbus/         # AsyncEventBus, EventStore integrations
    │   ├── messaging/        # Kafka/RabbitMQ/SQS clients and handlers
    │   ├── cache/            # Cache adapters (Redis, local cache, etc.)
    │   └── config/           # ConfigProvider implementations (env, files, vaults)
    │
    └── interface/            # ——— Interface Layer ———
        • Exposed entry‑points: HTTP, CLI, UIs, GraphQL, etc.
        ├── http/             # FastAPI/Starlette routers, controllers, error handlers
        │   ├── endpoints/    # Endpoint definitions inheriting EndpointBase
        │   ├── middleware/   # Logging, auth, error‑handling middleware
        │   └── schemas/      # Request/Response models (OpenAPI/Pydantic)
        ├── cli/              # Click/typer commands
        ├── ws/               # WebSocket gateways if any
        └── docs/             # Static assets or UI (SwaggerUI customizations, admin UI)

Key points:

• “domain” contains only pure‑DDD code—no imports from FastAPI, SQL, or DI.
• “application” orchestrates domain calls, handles transactions (via UoW), maps to/from DTOs, and boots your DI container in composition.py.
• “infrastructure” implements every Protocol (DBClientProtocol, RepositoryProtocol, EventBusProtocol, ConfigProtocol, etc.) against real systems.
• “interface” wires request/response, CLI commands, or other I/O into your application layer via adapters/endpoints.
