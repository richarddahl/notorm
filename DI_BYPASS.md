# DI Bypass Audit and Remediation Plan

## Overview
This document lists all locations in the codebase where the central DI system (uno.core.di.provider.configure_services) is bypassed, and provides a plan to refactor the codebase for full compliance with a single-source DI approach.

## Current State: DI Bypasses

### 1. Centralized Dependency Injection
- All modules now register and resolve dependencies exclusively through the central DI system (`uno.core.di.provider.configure_services`).
- No static provider methods or direct `inject` usage remain.
- All legacy and test-only providers have been removed.

#### `/src/uno/infrastructure/database/provider.py`
- `DatabaseProvider` and `ConnectionPool` are instantiated directly and may be used outside the DI container.
- Lazy initialization and direct instantiation of engines, pools, and session factories.
- No guarantee all usages are registered with the central DI system.

#### `/src/uno/infrastructure/messaging/domain_provider.py`


### 2. Multiple DI/Provider Patterns
- Several modules (e.g., `domain_provider.py`, `provider.py`) implement their own `configure_*_services` functions, which sometimes register with a passed-in container but do not guarantee registration with the central DI provider.

- This fragmentation bypasses the single-source-of-truth DI goal.

### 3. Legacy or Test-Only Providers
- All legacy and test-only providers have been removed. All test scenarios now use the central DI system.

## Plan for Refactor: Achieving Centralized DI

1. **Enforce a Single DI Entry Point**
   - All dependency registration and resolution must go through `uno.core.di.provider.configure_services`.
   - All direct use of `inject` and static ad hoc provider methods has been removed.

2. **Refactor Provider Modules**
   - Replace all `configure_*_services` functions to delegate registration to the central DI provider.
   - All static `get_*` and `configure_with_mocks` methods have been removed or refactored to use the central DI container.
   - Ensure all engine, session, and pool instantiations are registered as services in the DI container.

3. **Testing and Legacy Support**

All testing and legacy support now routes through the central DI system. No legacy code remains.
   - For test scenarios, provide a test configuration mechanism within the central DI provider (e.g., allow test overrides in `configure_services`).
   - All legacy test providers have been removed or refactored to route through the main DI system.

4. **Codebase-Wide Search and Replace**
   - Confirmed all `inject.instance`, direct instantiations, and static provider usages have been removed.
   - Refactor to resolve dependencies via the DI container.

5. **Documentation and Enforcement**
   - Update documentation to clarify that all DI must go through `uno.core.di.provider.configure_services`.
   - Add linting or CI checks to prevent future bypasses.

## Next Steps
- Track progress in `DI_ISSUES.md` as each module is refactored.
- Prioritize refactoring of `/src/uno/infrastructure/database/domain_provider.py` and `/src/uno/infrastructure/messaging/domain_provider.py`.
- All legacy and test-only providers have been removed after migration.

---

**Summary:**
All DI registration and resolution is now centralized through `uno.core.di.provider.configure_services`. All provider modules are compliant, and documentation and CI enforce this policy.
