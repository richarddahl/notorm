# Dependency Injection System Dependency Graph

This document maps the dependencies between components in the DI system to identify the most effective migration order.

## Core Components

```
DIContainer (uno.core.di)
  ├── ServiceLifetime
  ├── ServiceRegistration
  ├── ServiceScopeImpl (implements ServiceScope)
  ├── get_container()
  ├── get_service()
  ├── create_scope()
  └── initialize_container()

UnoServiceProvider (uno.dependencies.modern_provider)
  ├── ServiceLifecycle
  ├── register()
  ├── configure_services()
  ├── register_extension()
  ├── get_service()
  ├── create_scope()
  └── initialize()

ServiceScope Protocol (uno.core.protocols)
  └── [Interface for DI scopes]

ScoperContainer (uno.dependencies.scoped_container)
  ├── ServiceCollection
  ├── ServiceScope (enum)
  ├── ServiceResolver
  ├── get_container()
  ├── get_service()
  ├── create_scope()
  └── initialize_container()
```

## Decorator System

```
Decorators (uno.dependencies.decorators)
  ├── @service
  ├── @singleton
  ├── @scoped
  ├── @transient
  ├── @inject
  ├── @inject_params
  ├── @injectable_class
  └── @injectable_endpoint

DI Decorators (uno.core.di)
  └── [Similar decorators but using DIContainer]
```

## Integration Components

```
FastAPI Integration (uno.dependencies.fastapi_integration)
  ├── configure_fastapi()
  ├── DIAPIRouter
  ├── resolve_service()
  └── RequestScopeMiddleware

DI Testing (uno.core.di_testing)
  ├── TestContainer
  ├── reset_for_tests()
  └── configure_test_container()
```

## Domain Providers

```
Domain Providers (various modules)
  ├── authorization/domain_provider.py
  ├── workflows/domain_provider.py
  ├── meta/domain_provider.py
  ├── attributes/domain_provider.py
  ├── values/domain_provider.py
  ├── queries/domain_provider.py
  └── reports/domain_provider.py
```

## Dependency Graph

```
                    +-------------------+
                    | Core Protocols    |
                    | (ServiceScope)    |
                    +--------+----------+
                             |
                             v
       +-------------------+ | +-------------------+
       | ScoperContainer   |<+ | DIContainer       |
       | (scoped_container)|   | (di.py)           |
       +--------+----------+   +--------+----------+
                |                       |
                v                       v
       +--------+----------+   +--------+----------+
       | UnoServiceProvider|   | DI Testing        |
       | (modern_provider) |   | (di_testing.py)   |
       +--------+----------+   +--------+----------+
                |                       |
      +=========+==========+            |
      v         v          v            v
+-----+----+ +--+-------+ ++---------+ ++---------+
| Domain   | | Decorators| |FastAPI   | |Tests     |
| Providers| | (used by  | |Integration| |using DI  |
|          | | both)     | |          | |          |
+----------+ +----------+ +----------+ +----------+
```

## Usage Dependency Frequency

Based on code analysis, here's the approximate dependency frequency:

| Component | Usage Count | Critical Path |
|-----------|------------|--------------|
| get_container() | ~40 references | ✅ High |
| get_service() | ~30 references | ✅ High |
| create_scope() | ~20 references | ✅ High |
| ServiceLifetime | ~15 references | ✅ High |
| DIContainer direct | ~10 references | Medium |
| Testing utilities | ~8 references | Medium |
| FastAPI integration | ~5 references | Medium |
| Decorator system | ~30 references | ✅ High |

## Migration Order

Based on the dependency graph and usage patterns, here's the recommended migration order:

1. **Core Service Resolution**
   - Enhance UnoServiceProvider with missing features
   - Update ServiceScope compatibility
   - Create adapter functions for common operations

2. **Decorator System**
   - Update to work with both systems during transition
   - Ensure it uses UnoServiceProvider by default

3. **Domain Providers**
   - Standardize domain provider pattern
   - Update any direct DIContainer references

4. **Integration Components**
   - Update FastAPI integration
   - Create testing utilities for UnoServiceProvider

5. **Test Framework**
   - Update tests to use UnoServiceProvider
   - Create testing utilities for the new system

6. **Remove Legacy Code**
   - Remove DIContainer code
   - Update any remaining references

## Component Updates

### High Priority Components

1. `uno/dependencies/modern_provider.py`
   - Add missing features from DIContainer
   - Ensure compatibility with existing code

2. `uno/dependencies/decorators.py`
   - Update to use UnoServiceProvider
   - Maintain backward compatibility during transition

3. Core functions
   - Create adapter functions for get_container() → get_service_provider()
   - Ensure seamless transition for common patterns

### Medium Priority Components

1. `uno/dependencies/fastapi_integration.py`
   - Update to use UnoServiceProvider
   - Test with existing endpoints

2. Testing utilities
   - Create equivalent utilities for UnoServiceProvider
   - Ensure testing is straightforward

### Low Priority Components

1. Direct DIContainer usage
   - Update class references
   - Update any specialized uses

2. Advanced features
   - Implement any remaining advanced features
   - Optimize performance

## Conclusion

This dependency graph helps identify the most critical components to update first during the migration. By focusing on high-usage components like service resolution and decorators first, we can create a smoother transition path while ensuring backward compatibility during the migration process.