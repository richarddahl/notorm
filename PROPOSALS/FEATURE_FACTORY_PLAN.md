# Feature Factory Consolidation Plan

## 1. Existing DDD Boilerplate
The codebase contains ten feature sub-packages under `src/uno/` that follow the same Domain-Driven Design (DDD) layering:
  - **domain_provider.py**: per-feature DI configuration via `inject`
  - **domain_repositories.py**: factory or protocols for repositories
  - **domain_services.py**: business logic orchestration
  - **domain_endpoints.py**: HTTP/transport layer that wires services into routers
  - **entities.py** & **models.py**: entity and value-object definitions
  - **schemas.py** & **dtos.py**: input/output validation models

Each feature (attributes, authorization, database, messaging, meta, queries, read_model, reports, values, workflows) repeats this wiring almost identically.

## 2. Canonical Implementation Reference
The **api** sub-package demonstrates the most comprehensive, idiomatic DDD wiring:
  - Uses core `inject` container in `domain_provider.py`
  - Clear separation of protocols, implementations, logging, and helper methods
  - Exemplifies service registration, adapter creation, and endpoint assembly

## 3. Goals
1. Consolidate boilerplate into a generic factory to eliminate 10× repetition
2. Expose a simple, uniform API for loading repositories, services, and routers by feature name
3. Preserve existing `inject`-based configuration for backward compatibility within an initial transition period

## 4. Proposed `uno.core.feature_factory` Module
- **Location**: `src/uno/core/feature_factory.py`
- **Responsibilities**:
  1. Dynamically import feature modules (`domain_repositories`, `domain_services`, `domain_endpoints`)
  2. Provide accessor methods for repositories, services, and API routers
  3. Facilitate future migration away from per-feature `domain_provider.py`

### 4.1. Minimal Prototype API
```python
from uno.core.feature_factory import FeatureFactory

factory = FeatureFactory("api")
repos = factory.get_repositories()
services = factory.get_services()
router = factory.get_router()
```

## 5. Migration Steps
1. **Spike**: Implement `FeatureFactory` prototype and unit tests for core features (api, values).
2. **Refactor `api/`**: Replace `domain_provider.py` and similar modules in `api/` with calls to `FeatureFactory`.
3. **Bulk Update**: For remaining 9 features, delete `domain_provider.py`, `domain_repositories.py`, `domain_services.py`, `domain_endpoints.py`; import via `FeatureFactory` instead.
4. **Finalize**: Deprecate `uno.core.di_fastapi`/`uno.core.di` per-feature wiring; update docs and examples.

_Document version: 1.0_