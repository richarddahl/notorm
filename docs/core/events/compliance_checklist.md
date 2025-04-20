# Event Sourcing & Event-Driven Architecture Compliance Checklist

This checklist is intended to help developers and reviewers ensure that all aggregates, services, and modules in the codebase adhere to best practices for event sourcing and event-driven architecture.

---

## 1. Domain Event Publication
- [ ] All state-changing operations on aggregates publish domain events.
- [ ] Events are registered in aggregate roots, not services.
- [ ] Event publishing is integrated with the Unit of Work pattern.

## 2. Event Structure & Versioning
- [ ] Events include a version field for upcasting support.
- [ ] Event schemas are documented and versioned.
- [ ] Upcasters are implemented for breaking changes to event schemas.

## 3. Event Replay & Audit
- [ ] Aggregates can be reconstructed from event history.
- [ ] Event replay APIs are available for rebuilding state.
- [ ] Audit/migration tooling exists for event stores.

## 4. Event Handling & Idempotency
- [ ] Event handlers are idempotent (safe to process more than once).
- [ ] Handlers are isolated (no side effects outside their scope).
- [ ] Handlers are registered via the subscription manager or event bus.

## 5. Compliance for Aggregates
- [ ] All aggregates have documented invariants and event flows.
- [ ] Aggregates do not reference each other directly (use IDs).
- [ ] Aggregate boundaries are explicit and documented.

## 6. Documentation & Code Samples
- [ ] Event-driven patterns are documented in the codebase.
- [ ] Code samples for event creation, publishing, and handling are available.
- [ ] Migration and upcasting strategies are documented.

---

## How to Use
- Review this checklist when adding or refactoring aggregates, event handlers, or event store implementations.
- Ensure all boxes are checked before merging changes related to event sourcing or event-driven architecture.
- Update the checklist as new best practices or requirements emerge.

---

_Last updated: 2025-04-20_
