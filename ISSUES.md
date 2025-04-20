# uno Library: Deficiencies & Remediation Plan

## 1. Dependency Injection (DI) Consistency
**Deficiency:**
- Multiple `provider.py` and `domain_provider.py` modules exist across layers. Some register dependencies directly, risking bypass of the central DI container and reducing testability/maintainability.
- Inconsistent usage of DI patterns across modules.

**Remediation:**
- Refactor all provider modules to use the central DI container (`uno.core.di.provider.Provider` or equivalent).
- Remove direct instantiation of dependencies outside DI system.
- Document and enforce a single, canonical way to register and resolve dependencies.
- Track progress in `DI_ISSUES.md`.

---

## 2. Event-Driven Architecture & Event Sourcing
**Deficiency:**
- Event system is robust, but integration patterns across modules are not always clear.
- Missing: uniform event versioning/upcasting, explicit aggregate/event version checks, event replay/audit tooling.

**Remediation:**
- Audit all domain/application services to ensure domain events are published for all state changes.
- Add documentation and code samples for event-driven patterns.
- Implement or document event versioning/upcasting and event replay support.
- Create a checklist for event sourcing compliance for all aggregates.

---

## 3. Result Monad & Error Handling
**Deficiency:**
- Some helper functions and edge cases may still raise exceptions or return raw types.
- Inconsistencies in `convert=True` flags and type annotations.

**Remediation:**
- Audit all APIs for consistent `Result` usage.
- Add linting/tests to enforce `Result` return types and prohibit bare exceptions.
- Document error-handling conventions for contributors.

---

## 4. DDD Patterns & Aggregate Boundaries
**Deficiency:**
- Some modules may have leaky abstractions or unclear aggregate boundaries.
- Dependencies sometimes registered by concrete class, not interface.
- Not all aggregates/entities are clearly documented.

**Remediation:**
- Audit all domain models for DDD compliance (aggregate roots, encapsulation, domain events).
- Register dependencies by interface, not concrete class.
- Add/expand documentation on aggregate boundaries and DDD patterns.

---

## 5. Modern Python & Tooling
**Deficiency:**
- Some files may use legacy type hints or patterns.
- Tool configuration may not be fully centralized in `pyproject.toml`.
- Potential legacy/deprecated code paths remain.

**Remediation:**
- Audit for legacy type hints, update to modern syntax.
- Centralize all tool configs in `pyproject.toml`.
- Remove deprecated/legacy code and references from docs/codebase.

---

## 6. Documentation & Onboarding
**Deficiency:**
- Documentation is fragmented and sometimes references legacy patterns.
- No clear onboarding or contributing guide.

**Remediation:**
- Consolidate and update documentation, removing legacy references.
- Add `README.md` and `CONTRIBUTING.md` at repo root.
- Document DDD, event-driven, and DI patterns with code samples.

---

## 7. Testing & Quality
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
