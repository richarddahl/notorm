# Domain Layer TODO List

This file tracks actionable tasks for improving the Domain layer, based on the issues and recommendations identified in DOMAIN_ISSUES.md. Check off items as they are completed to maintain a robust, DDD-aligned, event-driven architecture.

## 1. Domain Event Handling
- [x] Review all aggregate roots to ensure they collect and expose uncommitted domain events.  
  _AggregateRoot now implements a protocol-compliant get_uncommitted_events() method for consistent event exposure._
- [x] Refactor application services to publish all uncommitted domain events after successful operations.
  _UserService now demonstrates this pattern by collecting, publishing, and clearing domain events from the aggregate root after successful operations._
- [x] Centralize event publishing and clearing logic (e.g., via a helper or base class) to ensure consistency across services.
  _A reusable async helper (publish_and_clear_events) was implemented and adopted in UserService for consistent event handling._
- [x] Centralize event dispatching through a dedicated event bus.
  _AsyncEventBus now implements the new EventBusProtocol with support for metadata, timestamp, and correlation IDs. All event dispatching is routed through this unified interface. All imports updated to use uno.domain.event_bus._
- [x] Standardize event payloads and metadata (timestamps, correlation IDs, etc.).
  _Event publishing now supports robust metadata and correlation context for all events._
- [ ] Evaluate feasibility of event sourcing support for aggregates.

## 2. Richer Domain Models
- [x] Audit domain entities and value objects for business logic; move business rules from services into models where appropriate.
  _All value entity validation now uses the Result monad pattern. No exception-throwing remains in value object/entity validation._
- [x] Replace any anemic domain models with richer, behavior-driven models. 
  _Identified and refactored anemic models, especially in `entities.py`, `models/user.py`, `models/order.py`, and `models/product.py`.
- [x] Implement/enforce aggregate invariants via methods or factory functions. 
  _Reviewed aggregates for invariants and moved enforcement into methods or factories as needed._

**All domain model business logic now uses the Result monad pattern for error handling.**
- Refactored methods in `User`, `Order`, and `Product` models to return `Result[None, str]` instead of raising exceptions for business rule violations.
- Aggregate invariants are now enforced via methods returning `Result` types.

**Next steps:**
- Review the codebase for any remaining exception-throwing logic in domain or service layers.
- Run the test suite to ensure correctness after refactoring.
- Continue addressing linting and modernization (e.g., type annotations, import sorting, deprecated types).

## 3. Value Objects and Immutability
- [x] Verify all value objects are truly immutable (`@dataclass(frozen=True)` or Pydantic `frozen=True`).
  _All value objects are now implemented using either `@dataclass(frozen=True)` or Pydantic models with `ConfigDict(frozen=True)`. Immutability is enforced across the domain._
- [x] Implement or review equality and hashing methods for all value objects.
  _All value objects implement `__eq__` and `__hash__` either via dataclass defaults or Pydantic model config._

## 4. Aggregate Boundaries
- [x] Document aggregate roots and their transactional boundaries.
  _Aggregate roots are defined by the `AggregateRoot` class (see `entity/aggregate.py`). The docstring and class comments describe their role as consistency boundaries and entry points for transactional operations. Transactional boundaries are enforced at the aggregate root level, consistent with DDD best practices._
- [x] Refactor aggregate creation to use factory methods for validation and construction.
  _Aggregate creation is now standardized via factory methods such as `EntityBase.create` and the entity/factory pattern in `factories.py`. This ensures validation and construction logic is consistently applied._

## 5. Repository Abstractions
- [x] Ensure all repositories use a consistent async interface.
  _All repository classes (see `EntityRepository`, `SQLAlchemyRepository`, `InMemoryRepository`, `ValueRepository`, and `ValueRepositoryProtocol`) now consistently use async methods for all CRUD and query operations. This ensures compatibility with async workflows across the domain and value layers._
- [x] Confirm all repository methods return `Result` types for error handling.
  _SQLAlchemyRepository and InMemoryRepository now return Result types throughout, with most Success/Failure calls using convert=True. Type annotations updated to Python 3.10+ syntax. Remaining work: audit helpers/utilities and fix any missing conversion flags._
- [ ] Promote and implement the specification pattern for flexible querying.

## 6. Domain Services

## Workflow Validation Refactor
- [ ] Update all usages of workflow entity `validate` methods to check for `Result` types (`is_success()`/`is_failure()`) instead of catching exceptions, after all refactoring is complete.

- [ ] Audit all domain services for statelessness; refactor as needed.
- [x] Ensure all service methods return `Result` types (Success/Failure).
  _DomainService and DomainServiceWithUnitOfWork now consistently return Result types. Type annotations updated and linting improved. Remaining work: audit for lingering exceptions and ensure all helpers/utilities follow the pattern._
- [ ] Remove any lingering exception-throwing logic in favor of Result monad usage.
  _Partial: Most exceptions replaced with Result monad, but a final audit is needed for full compliance._

## 7. Error Handling
- [ ] Define and document custom domain-specific error types.
- [ ] Replace generic exceptions with domain-specific errors where possible.
- [ ] Complete transition to `Result` types in all helpers and utilities.
  _Partial: Main repositories and services migrated. Helpers/utilities still need review._

## 8. Dependency Injection
- [ ] Identify and remove all ad hoc provider modules in the domain layer.
- [ ] Refactor to resolve all dependencies (repositories, services, event buses) via the central DI container.
- [ ] Ensure all components are easily mockable for testing.

## 9. Documentation & Ubiquitous Language
- [ ] Review code, comments, and docs for use of domain expert language.
- [ ] Add or update module-level docstrings to explain aggregate boundaries, invariants, and business rules.

## 10. CQRS & Event-Driven Patterns
- [ ] Audit services and repositories for strict command/query separation.
- [ ] Ensure all state-changing operations publish domain events asynchronously.

---

Reference: See DOMAIN_ISSUES.md for context and rationale behind each task.
