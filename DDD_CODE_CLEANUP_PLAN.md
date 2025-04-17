# Domain-Driven Design Code Cleanup Plan

This document outlines the plan for cleaning up code redundancies and consolidating on the unified domain-driven design approach we've implemented.

## 1. Domain Event Consolidation

### Problem

Multiple implementations of `DomainEvent`/`UnoDomainEvent` exist across the codebase:
- `src/uno/core/domain.py`
- `src/uno/core/protocols.py`
- `src/uno/core/protocols/__init__.py`
- `src/uno/domain/core.py`
- `src/uno/domain/models.py`
- `src/uno/domain/protocols.py`
- `src/uno/domain/protocols/event_protocols.py`

### Solution

Consolidate on the canonical implementation in `src/uno/core/unified_events.py`:

1. Replace concrete implementations with imports from the canonical version
2. Update protocol definitions to import from the canonical protocol
3. Add deprecation warnings where appropriate
4. Update all code that imports these classes to use the canonical implementation

### Implementation Steps

For each file:

1. **src/uno/core/domain.py**:
   - Replace with import from `uno.core.unified_events.UnoDomainEvent`
   - Add deprecation warning

2. **src/uno/core/protocols.py**:
   - Replace with import from `uno.core.unified_events.DomainEventProtocol`
   - Add deprecation warning

3. **src/uno/core/protocols/__init__.py**:
   - Replace with import from `uno.core.unified_events.DomainEventProtocol`
   - Add deprecation warning

4. **src/uno/domain/core.py**:
   - Replace with import from `uno.core.unified_events.UnoDomainEvent`
   - Add deprecation warning

5. **src/uno/domain/models.py**:
   - Replace with import from `uno.core.unified_events.UnoDomainEvent`
   - Add deprecation warning

6. **src/uno/domain/protocols.py**:
   - Replace with import from `uno.core.unified_events.DomainEventProtocol`
   - Add deprecation warning

7. **src/uno/domain/protocols/event_protocols.py**:
   - Replace with import from `uno.core.unified_events.DomainEventProtocol`
   - Add deprecation warning

## 2. Repository Pattern Standardization

### Problem

Multiple repository implementations with different patterns:
- Standard domain repository (`src/uno/domain/repository.py`)
- UnoRepository (`src/uno/dependencies/repository.py`)
- UnoBaseRepository (`src/uno/infrastructure/database/repository.py`)
- Module-specific repositories (attributes, values, etc.)

### Solution

Standardize on the DDD-based implementation in `src/uno/domain/repository.py`:

1. Create adapter classes for legacy repositories to implement the standard interface
2. Update module-specific repositories to extend the standard classes
3. Add deprecation warnings to legacy implementations
4. Create migration examples for application code

### Implementation Steps

1. **Create Adapter Classes**:
   - Create `LegacyRepositoryAdapter` that implements the standard repository interface and delegates to legacy repositories
   - Create `StandardRepositoryAdapter` that wraps standard repositories for legacy code

2. **Update Module Repositories**:
   - Refactor `AttributeRepository` to extend `SQLAlchemyRepository`
   - Refactor `ValueRepository` to extend `SQLAlchemyRepository`
   - Update specialized repositories like multitenancy to use the standard pattern

3. **Add Deprecation Warnings**:
   - Add warnings to `UnoRepository` and `UnoBaseRepository`
   - Document migration paths in code comments

4. **Create Migration Examples**:
   - Create example code showing how to migrate from legacy repositories to standard ones

## 3. Service Pattern Standardization

### Problem

Multiple service implementations with different patterns:
- Unified domain services (`src/uno/domain/unified_services.py`)
- Legacy domain services (`src/uno/domain/services.py` and `src/uno/domain/service.py`)
- Module-specific services (attributes, values, etc.)

### Solution

Standardize on the unified implementation in `src/uno/domain/unified_services.py`:

1. Create adapter classes for legacy services to implement the standard interface
2. Update module-specific services to extend the standard classes
3. Add deprecation warnings to legacy implementations
4. Create migration examples for application code

### Implementation Steps

1. **Create Adapter Classes**:
   - Create service adapters that implement standard interfaces but delegate to legacy implementations
   - Create backward-compatibility layers where needed

2. **Update Module Services**:
   - Refactor module-specific services to extend standard service classes
   - Update service factories to use the standardized approach

3. **Add Deprecation Warnings**:
   - Add warnings to legacy service implementations
   - Document migration paths in code comments

4. **Create Migration Examples**:
   - Create example code showing how to migrate from legacy services to unified ones

## 4. API Integration Standardization

### Problem

Multiple approaches to API endpoints that don't integrate properly with the domain services:
- Legacy endpoint implementations
- Direct repository usage in endpoints
- Inconsistent error handling

### Solution

Standardize on the service endpoint factory approach:

1. Update module-specific endpoints to use the service endpoint factory
2. Create adapter classes for legacy endpoints
3. Add deprecation warnings to legacy implementations
4. Create migration examples for application code

### Implementation Steps

1. **Standardize Module Endpoints**:
   - Update attribute, values, and other domain endpoints to use the service endpoint factory
   - Ensure consistent error handling across all endpoints

2. **Create Adapter Classes**:
   - Create endpoint adapters for legacy endpoints to use the new pattern
   - Create service endpoint adapters for specialized cases

3. **Add Deprecation Warnings**:
   - Add warnings to legacy endpoint implementations
   - Document migration paths in code comments

4. **Create Migration Examples**:
   - Create example code showing how to migrate from legacy endpoints to unified ones

## Implementation Timeline

1. **Phase 1: Domain Event Consolidation** (High Priority)
   - Replace implementations with imports
   - Add deprecation warnings
   - Update import statements across the codebase

2. **Phase 2: Repository Standardization** (Medium Priority)
   - Create adapter classes
   - Update module repositories
   - Add deprecation warnings

3. **Phase 3: Service Standardization** (Medium Priority)
   - Create service adapters
   - Update module services
   - Add deprecation warnings

4. **Phase 4: API Integration** (Low Priority)
   - Update module endpoints
   - Create endpoint adapters
   - Add deprecation warnings

## Impact Analysis

1. **Backward Compatibility**:
   - Adapter classes will maintain backward compatibility for existing code
   - Deprecation warnings will signal future removal
   - Migration examples will guide the transition

2. **Performance**:
   - Adapter layers may introduce minimal overhead
   - Consolidated implementations will reduce code size and complexity

3. **Maintainability**:
   - Single canonical implementations will be easier to maintain
   - Consistent patterns will reduce developer learning curve
   - Improved type safety through standardized interfaces

## Documentation Updates

1. Update `DDD_APPLICATION_DEVELOPMENT.md` with migration guides
2. Create code examples showing before/after for each pattern
3. Update API documentation to reflect the standardized approach
4. Add deprecation notices for legacy interfaces