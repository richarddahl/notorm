# Event System Review and Refactoring Plan

## 1. Overview of the Current Event System

The codebase implements a comprehensive event-driven architecture centered around the UNO framework. The event system comprises several core components:

- **Event Protocols**: Abstract interfaces (protocols) for events, event buses, event stores, and publishers (`src/uno/core/protocols/event.py`).
- **Event Base Class**: An immutable, serializable event value object (`src/uno/core/events/event.py`).
- **Async Event Bus**: Asynchronous, concurrency-controlled event bus for publishing/subscribing (`src/uno/core/events/bus.py`).
- **Event Publisher**: High-level API for publishing (and optionally persisting) events (`src/uno/core/events/publisher.py`).
- **Event Store**: Abstract and in-memory implementations for event sourcing (`src/uno/core/events/store.py`).
- **Subscription Management**: Persistent, configurable, and monitored event subscriptions (`src/uno/core/events/subscription.py`).
- **Monitoring and Logging**: Structured event logging and metrics (`src/uno/core/monitoring/events.py`).
- **Infrastructure Extensions**: SQL event store emitters, security/audit events, and event-based cache invalidation strategies.

## 2. Key Strengths

- **Strong Protocol Orientation**: Clear interfaces for all event system components.
- **Async-First Design**: Event bus and publisher support async operations and concurrency.
- **Immutability and Serialization**: Events are immutable value objects with robust (de)serialization.
- **Subscription Management**: Dynamic, persistent, and observable subscriptions with runtime metrics.
- **Event Sourcing Ready**: Event store abstractions (in-memory, SQL emitters) support event sourcing.
- **Monitoring/Audit Integration**: Structured logging and audit events are first-class citizens.

---

## 3. Refactoring Progress (as of 2025-04-19)

### Completed Steps
- **Canonical Event Base:** Designated `Event` in `src/uno/core/events/event.py` as the single canonical base class for all events.
- **Monitoring Events:** Refactored `MonitoringEvent` to inherit from the canonical base, removed redundant fields, and updated serialization methods.
- **Security/Audit Events:** Refactored `SecurityEvent` to inherit from the canonical base, removed legacy fields, and updated type annotations and serialization.
- **Type Annotations & Imports:** Updated to modern Python (3.10+) type annotations and removed deprecated/unused imports.
- **Lint Fixes:** Addressed major lint and formatting issues in refactored files.
- **Domain Events:** Refactored User and Product domain events to inherit from the canonical Event class.

### In Progress / Next Steps
- **Domain Events:** Refactoring remaining domain-specific events to inherit from the canonical base and conform to `EventProtocol`.
- **Event Usage:** Update all event creation, handlers, and tests to use unified event types.
- **Protocol Conformance:** Ensure all event-related components (bus, store, publisher) are fully type-safe and protocol-compliant.
- **Documentation:** Update documentation and examples to reflect the unified event system.
- **Legacy Cleanup:** Remove any remaining legacy event code and ensure no duplicate event base classes remain.

---

## 4. Outstanding Issues & Considerations

- Some domain events may still use legacy base classes or have redundant metadata fields. These need systematic migration.
- Event handler and test code must be reviewed for compatibility with new event type signatures.
- Ensure all event serialization/deserialization paths are consistent and robust.
- Continue to monitor for lint and type issues as the migration proceeds.

---

*This document will be updated as the refactoring progresses. See `EVENT_CHECKLIST.md` for a granular, step-by-step migration log.*

## 3. Issues and Areas for Refactoring

### 3.1. Protocol/Interface Consistency
- Some event-related infrastructure (e.g., `SecurityEvent`, monitoring `Event`) does not implement or inherit from the core `EventProtocol`.
- There are multiple event base types (e.g., `src/uno/core/events/event.py:Event`, `src/uno/core/monitoring/events.py:Event`, `src/uno/infrastructure/security/audit/event.py:SecurityEvent`), which can cause confusion and hinder polymorphic event handling.

**Refactor Plan:**
- Consolidate all event types to inherit from or conform to `EventProtocol`.
- Consider a single canonical `Event` base class for all domain, audit, and monitoring events, or use explicit adapters.

### 3.2. Event Handler Registration and Discovery
- Subscription management is robust, but handler discovery and dynamic registration may be brittle (e.g., via module/function names as strings in configs).
- Lack of type-checking or validation for handler signatures at registration time.

**Refactor Plan:**
- Use explicit handler registration APIs with type-checking.
- Provide utilities to auto-discover handlers via decorators or entry points.
- Validate handler signatures at subscription time.

### 3.3. Error Handling and Result Monad Usage
- Some event system methods (especially in subscriptions, publishers, and stores) return raw values or raise exceptions, while the rest of the codebase is migrating to a Result monad pattern.

**Refactor Plan:**
- Refactor all event system methods (publish, subscribe, append_events, etc.) to return `Result` types consistently.
- Ensure all async error handling uses `Result`, not bare exceptions.

### 3.4. Metadata and Context Propagation
- Not all event types support full metadata (correlation/causation IDs, aggregate info, trace context).
- Context propagation (e.g., for distributed tracing) is not enforced across all event types and handlers.

**Refactor Plan:**
- Standardize event metadata fields across all event types.
- Provide context propagation utilities and enforce their use in event emission and handling.

### 3.5. Infrastructure/Domain Boundary Clarity
- Some infrastructure event types (e.g., cache invalidation, audit) are tightly coupled to their consumers and do not use the event bus or store.

**Refactor Plan:**
- Route all infrastructure events through the unified event bus (optionally with domain/infrastructure segregation).
- Decouple cache/audit event emission from direct consumers.

### 3.6. Documentation and Examples
- There are multiple documentation files, but some are outdated or incomplete.
- Examples use different event base types and patterns.

**Refactor Plan:**
- Unify and update event system documentation.
- Provide canonical, end-to-end examples for domain, infrastructure, and monitoring events.

## 4. Concrete Refactoring Steps

1. **Unify Event Base Classes**
   - Refactor `SecurityEvent` and monitoring `Event` to inherit from or conform to `EventProtocol`.
   - Consider merging into a single `BaseEvent` if feasible.
2. **Enforce Protocol Compliance**
   - Add runtime/type-checking for event handler registration.
   - Validate all event types and handlers at startup.
3. **Result Monad Everywhere**
   - Refactor all event system methods to use `Result[T, E]` for error handling.
   - Update tests and documentation accordingly.
4. **Standardize Metadata**
   - Ensure all events (domain, audit, monitoring, infra) support and propagate full metadata/context.
5. **Handler Discovery/Registration**
   - Implement decorator or entry-point based handler discovery.
   - Remove string-based handler references from configs where possible.
6. **Bus-Centric Architecture**
   - Route all event types (including infrastructure/audit/cache) through the event bus.
   - Decouple direct calls in infrastructure code.
7. **Documentation/Examples**
   - Consolidate and update all event system docs.
   - Add canonical usage examples for all event types and layers.

## 5. Summary Table of Issues and Actions

| Area                        | Issue/Observation                                             | Refactoring Action                     |
|-----------------------------|--------------------------------------------------------------|----------------------------------------|
| Event Base Types            | Multiple, inconsistent event classes                         | Unify/standardize to EventProtocol     |
| Handler Registration        | String-based, brittle, lacks type-checking                   | Use decorators/APIs, validate types    |
| Error Handling              | Inconsistent Result monad usage                              | Refactor for Result everywhere         |
| Metadata/Context            | Not all events support full metadata                         | Standardize and propagate metadata     |
| Infra/Domain Boundaries     | Infra events bypass bus/store                                | Route all events through event bus     |
| Documentation/Examples      | Outdated, fragmented docs/examples                           | Consolidate and update                 |

---

This document should be kept up to date as event system refactoring progresses. Track all major changes and use this as the single source of truth for event architecture decisions.
