# Domain Layer: Next Steps for DI Compliance

## Audit of Ad Hoc Provider Usage and Manual Instantiation

### Summary
A review of the codebase reveals that most modern domain modules are now DI container compliant. However, legacy or ad hoc provider modules and some manual instantiations may still exist, especially in application, meta, and workflow layers. Full compliance with the central DI system is critical for maintainability, testability, and architectural consistency.

### Findings

#### 1. Provider Modules
- **application/queries/domain_provider.py**: Contains a `configure_queries_services(container)` function that registers repositories/services with the DI container. No ad hoc instantiation found here.
- **application/workflows/domain_provider.py**: Uses a DI-compliant `configure_workflows_services(container)` function. No ad hoc instantiation found.
- **application/workflows/provider.py**: This module is DI compliant and registers all dependencies with the container. No ad hoc instantiation found.
- **meta/domain_provider.py**: Uses a DI-compliant `configure_meta_services(container)` function. No ad hoc instantiation found.
- **core/di/provider.py**: This is the DI system implementation, not an ad hoc provider.

**No provider.py or domain_provider.py modules found directly in the domain layer.**

#### 2. Endpoint Dependency Resolution
- All FastAPI endpoints in the domain layer use `Depends(lambda: get_service(ServiceType))`, which resolves services via the central DI system (imported from `uno.dependencies.scoped_container`).

#### 3. Manual Instantiation
- No evidence of repositories or services being instantiated directly in the domain layer. All constructors expect dependencies to be injected.
- All domain services and repositories are registered and resolved via the DI container in their respective modules.

### Remaining Tasks

#### 1. Double-check for Overlooked Ad Hoc Providers or Manual Instantiations
- [x] Searched all domain submodules for `provider.py`, `domain_provider.py`, and manual instantiation patterns.
- [x] Confirmed that all repositories and services are registered and resolved via the DI container, not instantiated directly.
- [x] No overlooked ad hoc provider modules or manual instantiations found in domain code.

#### 2. Remove References to Legacy Provider Patterns in Documentation/Comments
- [x] Searched `docs/`, `src/uno/domain/`, and related documentation for mentions of legacy/ad hoc provider patterns.
- [x] Updated or removed outdated references in migration guides and service pattern docs.
- [x] Confirmed all new documentation refers to the central DI system only.

#### 3. Ensure All Tests and Fixtures Use the DI Container
- [x] Audited test directory for manual instantiation of services/repositories.
- [x] No direct instantiation found; tests use container-based resolution or appropriate fixtures.
- [x] Added test fixture examples to documentation for future reference.

#### 4. Expand DI Compliance Documentation in Domain README
- [x] Added a section to the domain README explaining DI best practices, container registration, and dependency resolution.
- [x] Provided usage and testing examples for new developers.

---

**Status:**
All actionable steps to ensure full DI compliance in the domain layer are complete. The domain layer is now fully aligned with the central DI system. All new code and tests must continue to follow these patterns for ongoing compliance.

### Conclusion
The domain layer is nearly fully DI compliant. The remaining work is primarily verification, documentation cleanup, and ensuring that all new code continues to follow DI best practices.

---

_Last audited: 2025-04-20_
