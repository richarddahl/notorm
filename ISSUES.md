# uno Library: Deficiencies & Remediation Plan

## 1. Event-Driven Architecture & Event Sourcing
**Deficiency:**
- Event system is robust, but integration patterns across modules are not always clear.
- Missing: uniform event versioning/upcasting, explicit aggregate/event version checks, event replay/audit tooling.

**Remediation:**
- Audit all domain/application services to ensure domain events are published for all state changes.
- Add documentation and code samples for event-driven patterns.
- Implement or document event versioning/upcasting and event replay support.
- Create a checklist for event sourcing compliance for all aggregates.

**Status (as of 2025-04-20):**

- **Domain Event Publication:**
  - All core domain/application services and aggregate roots are instrumented to publish domain events for state changes.
  - The Unit of Work pattern automatically collects and publishes events after successful commits.
  - Event publishing is handled via `EventPublisher` and `AsyncEventBus`, supporting both sync and async flows.

- **Documentation & Code Samples:**
  - Extensive documentation exists in `docs/core/events/index.md` and related files, covering event-driven patterns, handler best practices, integration with UoW, CQRS, and code samples.
  - Example event classes and handlers are present in `examples/ecommerce_app/catalog/domain/events.py` and other modules.

- **Event Versioning, Replay, Audit Tooling:**
  - The event store (notably `PostgresEventStore`) supports event versioning (`aggregate_version` field).
  - Event replay is supported via APIs like `get_events_by_aggregate` and aggregate reconstruction (`Aggregate.from_events(events)`).
  - Migration and audit tooling available via `eventstore_migration.py` and `eventstore.py` scripts.
  - Upcasting/versioning for long-lived events is documented, but explicit upcaster implementations may need further expansion.

- **Event Sourcing Compliance Checklist:**
  - Best practices for event naming, content, idempotency, and handler isolation are documented.
  - No formal, codified checklist file yet; compliance is described in docs.

**Next Steps:**
- Formalize a compliance checklist (as a Markdown file or doc section).
- Expand upcaster/versioning code samples if needed.
- Continue to audit new aggregates/services for event sourcing compliance.

---

## 2. Result Monad & Error Handling
**Deficiency:**
- Some helper functions and edge cases may still raise exceptions or return raw types.
- Inconsistencies in `convert=True` flags and type annotations.

**Remediation:**
- Audit all APIs for consistent `Result` usage.
- Add linting/tests to enforce `Result` return types and prohibit bare exceptions.
- Document error-handling conventions for contributors.

**Progress (2025-04-20):**
- Auditing infrastructure modules (e.g., aggregation.py, dtos.py) for exception-raising code and raw returns.
- Converting helper/infrastructure functions to use `Result` instead of raising exceptions where feasible.
- Verifying `convert=True` flags and modern type annotations in all Success/Failure calls.
- Drafting error-handling conventions for contributors (to be added in docs).

---

## 3. DDD Patterns & Aggregate Boundaries
**Deficiency:**
- Aggregate boundaries are not always explicit or well-documented.
- Some modules do not enforce aggregate invariants or encapsulation.
- Inconsistent use of DDD tactical patterns (entities, value objects, repositories, etc.).

**Remediation:**
- Review all domain modules for correct aggregate boundaries.
- Update documentation to clarify aggregate roles and invariants.
- Refactor code to consistently apply DDD tactical patterns.

**Catalog Domain DDD Review (2025-04-20):**
- **Aggregate Boundaries:**
  - `Product` is the aggregate root, encapsulating variants, images, and category memberships. Invariants (name, SKU, price, ownership of variants/images) are enforced in `check_invariants()`.
  - `Category` can serve as an aggregate root for product organization, but invariants (e.g., uniqueness of name/slug, parent-child validity) could be more explicit.
  - `ProductVariant` and `ProductImage` are entities owned by `Product` and do not reference other aggregates directly.
- **Tactical Patterns:**
  - Value objects are used for complex fields (e.g., `Money`, `Inventory`).
  - Domain events are registered for state changes (creation, update, price change, inventory update).
  - Business logic for product state changes is encapsulated in the aggregate root.
- **Documentation:**
  - Added a dedicated section to `docs/domain/aggregates.md` summarizing catalog aggregates, their roles, invariants, and DDD compliance.
- **Recommendations:**
  - Consider formalizing invariants for `Category` (e.g., enforce unique slugs, valid parent-child relationships).
  - Ensure repositories operate only on aggregate roots.
  - Continue to keep business logic within aggregates and use value objects for all complex value types.

---

## 4. Modern Python & Tooling
**Deficiency:**
- Some files may use legacy type hints or patterns.
- Tool configuration may not be fully centralized in `pyproject.toml`.
- Potential legacy/deprecated code paths remain.

**Remediation:**
- Audit for legacy type hints, update to modern syntax.
- Centralize all tool configs in `pyproject.toml`.
- Remove deprecated/legacy code and references from docs/codebase.

---

## 5. Documentation & Onboarding
**Deficiency:**
- Documentation is fragmented and sometimes references legacy patterns.
- No clear onboarding or contributing guide.

**Remediation:**
- Consolidate and update documentation, removing legacy references.
- Add `README.md` and `CONTRIBUTING.md` at repo root.
- Document DDD, event-driven, and DI patterns with code samples.

---

## 6. Testing & Quality
**Deficiency:**
- Unclear test coverage for core/event-driven/DI logic.
- Potential lack of integration and property-based tests.

**Remediation:**
- Ensure all core modules have unit and integration tests.
- Add property-based tests for critical logic.
- Add tests for event replay, event store consistency, and DI registration.

---

# Next Steps
- Review, prioritize, and assign these issues.
- Track DI refactor progress in `DI_ISSUES.md`.
- Schedule audits for DDD, event sourcing, and error handling consistency.
- Update documentation and tests as remediation progresses.
