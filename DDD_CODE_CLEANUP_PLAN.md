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

✅ Standardize on the DDD-based implementation in `src/uno/domain/entity/repository.py`:

1. ✅ Create core `EntityRepository` class with unified interface
2. ✅ Implement `InMemoryRepository` and `SQLAlchemyRepository` with specification support
3. ✅ Add deprecation warnings to legacy implementations
4. ✅ Create examples demonstrating the new repository pattern

### Implementation Steps

1. **Core Repository Components** (COMPLETED):
   - ✅ Created `EntityRepository` base class with specifications support
   - ✅ Implemented `InMemoryRepository` for testing and prototyping
   - ✅ Created `SQLAlchemyRepository` with comprehensive feature support
   - ✅ Added `EntityMapper` for mapping between domain and persistence models

2. **Specification Integration** (COMPLETED):
   - ✅ Implemented specification translators for different data sources
   - ✅ Added support for advanced querying features
   - ✅ Created examples demonstrating specification-based queries

3. **Legacy Code Deprecation** (COMPLETED):
   - ✅ Added deprecation warnings to `uno.core.base.repository`
   - ✅ Added deprecation warnings to `uno.infrastructure.repositories`
   - ✅ Added deprecation warnings to `uno.domain.specifications`
   - ✅ Added deprecation warnings to `uno.domain.specification_translators`

4. **Documentation and Examples** (COMPLETED):
   - ✅ Created comprehensive examples in `uno.domain.entity.examples`
   - ✅ Updated implementation progress documentation
   - ✅ Added code comments explaining migration paths

## 3. Service Pattern Standardization

### Problem

Multiple service implementations with different patterns:
- Unified domain services (`src/uno/domain/unified_services.py`)
- Legacy domain services (`src/uno/domain/services.py` and `src/uno/domain/service.py`)
- Module-specific services (attributes, values, etc.)

### Solution

✅ Standardize on the DDD-based implementation in `src/uno/domain/entity/service.py`:

1. ✅ Create core service classes with standardized interfaces
2. ✅ Implement service hierarchy with proper domain isolation 
3. ✅ Standardize on Result pattern for all service operations
4. ✅ Create examples demonstrating the new service pattern

### Implementation Steps

1. **Core Service Components** (COMPLETED):
   - ✅ Created `DomainService` base class for domain-specific business logic
   - ✅ Implemented `DomainServiceWithUnitOfWork` for transaction management
   - ✅ Created `ApplicationService` for cross-domain orchestration
   - ✅ Implemented `CrudService` for standardized entity operations

2. **Service Factory** (COMPLETED):
   - ✅ Created `ServiceFactory` for simplified service creation
   - ✅ Added support for repository and unit of work factory injection
   - ✅ Implemented flexible configuration options

3. **Integration with Repository and UoW** (COMPLETED):
   - ✅ Integrated with `EntityRepository` for data access
   - ✅ Added support for specification-based querying
   - ✅ Integrated with Unit of Work for transaction management

4. **Documentation and Examples** (COMPLETED):
   - ✅ Created comprehensive examples in `uno.domain.entity.examples.service_example.py`
   - ✅ Updated implementation progress documentation
   - ✅ Added code comments explaining usage patterns and best practices

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

1. ✅ Created comprehensive domain entity framework documentation:
   - `/docs/domain/entity_framework.md`: Overview of the domain entity framework
   - `/docs/domain/repository_pattern.md`: Detailed guide to the repository pattern
   - `/docs/domain/specification_pattern.md`: Guide to the specification pattern
   - `/docs/domain/service_pattern.md`: Explanation of the service layer

2. ✅ Added extensive code examples:
   - `src/uno/domain/entity/examples/repository_example.py`: Repository usage
   - `src/uno/domain/entity/examples/specification_querying.py`: Specification pattern
   - `src/uno/domain/entity/examples/service_example.py`: Service pattern

3. ✅ Added deprecation notices to legacy implementations:
   - Added warnings to legacy repository implementations
   - Added warnings to legacy service implementations
   - Added warnings to legacy specification implementations

4. Update `DDD_APPLICATION_DEVELOPMENT.md` with migration guides