# Repository Restructuring and Naming Standardization

This document outlines the plan for standardizing naming conventions and directory structure in the uno (not orm) codebase. The goal is to improve maintainability, readability, and consistency throughout the project.

## Core Principles

1. **Clarity**: Names should clearly indicate purpose and role
2. **Consistency**: Similar concepts should follow the same naming patterns
3. **Conventionality**: Follow standard Python/industry conventions where appropriate
4. **Simplicity**: Avoid unnecessary complexity in naming and structure

## Directory Structure Standardization

### Top-Level Organization

```
/src/uno/
├── api/              # API endpoints and FastAPI integration
├── application/      # Application services, DTOs, and cross-cutting concerns
├── core/             # Core utilities, base classes, and frameworks
├── domain/           # Domain models, repositories interfaces, services interfaces
├── infrastructure/   # Implementations of repositories, external services, etc.
├── scripts/          # CLI tools and maintenance scripts
└── __init__.py
```

### Module-Specific Structure

Each module should follow this pattern:

```
/module_name/
├── models/           # Data models specific to this module
├── interfaces/       # Protocols and interfaces
├── repositories/     # Repository implementations
├── services/         # Service implementations
├── exceptions.py     # Module-specific exceptions
├── constants.py      # Module-specific constants
└── __init__.py       # Exports public API
```

## Naming Convention Rules

### Directory Naming

1. **Rule**: Use plural form for directories containing multiple implementations
2. **Examples**:
   - `/models/` (not `/model/`)
   - `/repositories/` (not `/repository/`)
   - `/services/` (not `/service/`)

### File Naming

1. **Rule**: Use snake_case for all Python files
2. **Rule**: Use singular form for base/interface files
3. **Rule**: Use plural form for collections of utilities
4. **Rule**: Use descriptive, action-oriented names for implementation files
5. **Examples**:
   - `base_repository.py` - Base class or interface
   - `user_repository.py` - Specific implementation
   - `validators.py` - Collection of validation utilities
   - `query_executor.py` - Implementation of a specific action

### Class Naming

1. **Rule**: Use PascalCase for all classes
2. **Rule**: Use standard suffixes to indicate role:
   - `Repository` - Data access objects
   - `Service` - Business logic services
   - `Factory` - Object creation
   - `Manager` - Resource management
   - `Controller` - Endpoint handling
3. **Rule**: Use `Base` prefix for abstract/base classes:
   - `BaseRepository`
   - `BaseService`
4. **Rule**: Domain entities should use clean domain names without suffixes:
   - `User` (not `UserEntity` or `UserModel`)
   - `Product` (not `ProductEntity`)
5. **Examples**:
   - `UserRepository` - Repository for user data
   - `OrderService` - Service for order business logic
   - `EndpointFactory` - Factory for creating endpoints
   - `CacheManager` - Manager for cache resources

### Function/Method Naming

1. **Rule**: Use snake_case for all functions and methods
2. **Rule**: Use verb prefix for actions:
   - `get_` for retrieval operations
   - `create_` for creation operations
   - `update_` for update operations
   - `delete_` for deletion operations
   - `validate_` for validation operations
3. **Examples**:
   - `get_user_by_id()`
   - `create_order()`
   - `update_product_price()`
   - `delete_inactive_accounts()`

## Specific Changes Required

### Directory Restructuring

1. **Consolidate DTOs**:
   - Move `/uno/dto/` to `/uno/application/dto/`
   - Ensure all module-specific DTOs use consistent naming

2. **Consolidate Async Utilities**:
   - Merge `/uno/core/async/` and `/uno/core/asynchronous/` into `/uno/core/async/`

3. **Standardize Domain Integration**:
   - Move all domain-related classes to `/uno/domain/`
   - Move domain implementations to appropriate infrastructure directories

4. **Organize Repositories**:
   - Move repository interfaces to `/uno/domain/repositories/`
   - Move repository implementations to `/uno/infrastructure/repositories/`

### File Renaming

1. **Base/Interface Files**:
   - Rename `model.py` to `base_model.py`
   - Rename `repository.py` to `base_repository.py`
   - Rename `service.py` to `base_service.py`

2. **Integration Files**:
   - Standardize all domain integration files to use `domain_*.py` pattern:
     - `domain_repositories.py`
     - `domain_services.py`
     - `domain_endpoints.py`
   - Rename adapter files to follow the same pattern:
     - `repository_adapter.py` → `domain_repository_adapter.py`

3. **Duplicate Files**:
   - Identify and eliminate duplicate files across the codebase

### Class Renaming

1. **Base Classes**:
   - Rename `UnoDTO` to `BaseDTO`
   - Rename `UnoModel` to `BaseModel`
   - Rename `UnoRepository` to `BaseRepository`
   - Rename `UnoService` to `BaseService`

2. **Repositories and Services**:
   - Ensure consistent use of suffixes:
     - All repositories should end with `Repository`
     - All services should end with `Service`
     - All factories should end with `Factory`
     - All managers should end with `Manager`

3. **Domain Models**:
   - Use clean domain names without unnecessary suffixes

## Implementation Plan

### Phase 1: Directory Structure Alignment (COMPLETED)

1. Create new directory structure where needed ✅
2. Move files to appropriate locations ✅
   - Created `/core/base/` for base classes ✅
   - Created `/domain/base/` for domain base models ✅
3. Update imports to reflect new structure ✅
   - Updated imports in affected modules ✅
   - Removed all backward compatibility aliases ✅
4. Delete empty legacy directories ✅
   - Removed old files with `.bak` extension ✅

Progress:
- Created `/src/uno/core/base/` directory ✅
- Implemented `/src/uno/core/base/dto.py` ✅
- Implemented `/src/uno/core/base/repository.py` ✅
- Implemented `/src/uno/core/base/service.py` ✅
- Implemented `/src/uno/core/base/error.py` ✅
- Created `/src/uno/domain/base/` directory ✅
- Implemented `/src/uno/domain/base/model.py` ✅
- Created `/src/uno/domain/entities/` directory ✅
- Implemented `/src/uno/domain/entities/base_entity.py` ✅
- Created `/src/uno/domain/repositories/` directory ✅
- Implemented `/src/uno/domain/repositories/repository_adapter.py` ✅
- Created `/src/uno/domain/services/` directory ✅
- Implemented `/src/uno/domain/services/base_domain_service.py` ✅
- Created `/src/uno/domain/attributes/` directory ✅
- Implemented `/src/uno/domain/attributes/service_interface.py` ✅
- Created `/src/uno/domain/method_naming_standard.py` ✅
- Standardized `/src/uno/domain/specifications/` directory ✅
- Renamed specification files to follow conventions ✅
- Implemented `/src/uno/infrastructure/services/base_service.py` ✅
- Consolidated duplicate async code ✅
- Created Architecture documentation in `/src/uno/ARCHITECTURE.md` ✅

### Phase 2: File Naming Standardization (COMPLETED)

1. Rename files to follow standardized naming conventions ✅
   - Renamed specification files ✅
   - Created properly named base service files ✅
   - Created properly named repository files ✅
   - Created properly named DTO files ✅
2. Update imports across the codebase ✅
   - Updated import references in affected modules ✅
   - Updated all DTO imports to use BaseDTO ✅
3. Update documentation references ✅
   - Updated ARCHITECTURE.md with new structure ✅

### Phase 3: Class Renaming (COMPLETED)

1. Rename classes to follow standardized naming conventions ✅
   - Renamed `UnoDTO` to `BaseDTO` ✅
   - Renamed `UnoModel` to `BaseModel` ✅
   - Renamed `Repository` to `BaseRepository` ✅
   - Renamed `Service` to `BaseService` ✅
   - Renamed `QueryService` to `BaseQueryService` ✅
   - Renamed `UnoError` to `BaseError` ✅
2. Update all references to renamed classes ✅
   - Updated references to `Repository` ✅
   - Updated references to `Service` ✅
   - Removed all backward compatibility aliases ✅
3. Update documentation to reflect new class names ✅
   - Created Architecture documentation ✅

### Phase 4: Function/Method Standardization (COMPLETED)

1. Standardize function and method names ✅
   - Created method naming standard documentation ✅
   - Defined consistent patterns for repository operations ✅
   - Defined consistent patterns for service operations ✅
   - Defined verb prefixes for different operation types ✅
2. Update all references to renamed functions ✅
   - Updated repository method references ✅
   - Updated service method references ✅
   - Ensured consistent naming patterns ✅
3. Update documentation to reflect new function names ✅
   - Added method naming documentation in `/src/uno/domain/method_naming_standard.py` ✅

## Example Changes

| Current Path/Name | Standardized Path/Name | Status |
|-------------------|------------------------|--------|
| `/uno/dto/dto.py` | `/uno/core/base/dto.py` | ✅ Completed |
| `UnoDTO` | `BaseDTO` | ✅ Completed |
| `/uno/domain/model.py` | `/uno/domain/base/model.py` | ✅ Completed |
| `UnoModel` | `BaseModel` | ✅ Completed |
| `/uno/core/async/` + `/uno/core/asynchronous/` | `/uno/core/async/` | ✅ Completed |
| `/uno/infrastructure/repositories/base.py (Repository)` | `/uno/core/base/repository.py (BaseRepository)` | ✅ Completed |
| `/uno/infrastructure/services/base.py (Service)` | `/uno/core/base/service.py (BaseService)` | ✅ Completed |
| `/uno/infrastructure/services/base.py` | `/uno/infrastructure/services/base_service.py` | ✅ Completed |
| `/uno/domain/repository_adapter.py` | `/uno/domain/repositories/repository_adapter.py` | ✅ Completed |
| `/uno/domain/core.py (Entity, etc.)` | `/uno/domain/entities/base_entity.py` | ✅ Completed |
| `/uno/domain/service_example.py` | `/uno/domain/services/base_domain_service.py` | ✅ Completed |
| `/uno/domain/specifications/specifications.py` | `/uno/domain/specifications/base_specification.py` | ✅ Completed |
| `/uno/domain/specifications/composite_specifications.py` | `/uno/domain/specifications/composite_specification.py` | ✅ Completed |
| `/uno/domain/specifications/enhanced.py` | `/uno/domain/specifications/enhanced_specification.py` | ✅ Completed |
| `/uno/attributes/domain_services.py` | `/uno/domain/attributes/service_interface.py` | ✅ Completed |
| Not Defined | `/uno/domain/method_naming_standard.py` | ✅ Completed |
| `UnoError` in various files | `/uno/core/base/error.py (BaseError)` | ✅ Completed |

## Guiding Principles for Implementation

1. **No backward compatibility**: Make changes directly without preserving legacy patterns ✅
2. **Complete over partial**: Complete each phase fully before moving to the next ✅
3. **Test-driven verification**: Run tests after each phase to ensure functionality ✅
4. **Documentation updates**: Update documentation alongside code changes ✅
5. **Commit logical units**: Make commits for logical groups of changes ✅

## Completion Status

All phases of the repository restructuring have been completed:
- Phase 1: Directory Structure Alignment ✅
- Phase 2: File Naming Standardization ✅
- Phase 3: Class Renaming ✅
- Phase 4: Function/Method Standardization ✅

The codebase now has a consistent structure with:
- Standardized directory organization
- Consistent file naming conventions
- Clear and consistent class naming
- Standardized method naming patterns
- No backward compatibility layers
- Updated documentation

## Validation and Automation Tools

To support ongoing maintenance of these standards, we've implemented validation and automation tools:

### Import Standards Validator

The `validate_import_standards.py` script analyzes the codebase for:

- Usage of legacy class names (`UnoModel`, `UnoRepository`, `UnoError`, etc.)
- Imports from deprecated modules
- Backward compatibility layers

It generates detailed reports to guide cleanup efforts.

### Automatic Import Modernizer

The `modernize_imports.py` script automatically updates:

- Legacy class names to their `Base`-prefixed versions
- Deprecated import paths to the standardized ones
- Adds missing imports as needed

### Error Classes Modernizer

The `modernize_error_classes.py` script specifically modernizes error handling code.

For more details on these tools, see:
- `src/scripts/README_MODERNIZATION.md`: Full documentation of the modernization tools
- `MODERNIZATION_UPDATE.md`: Overview of the validation results and modernization process

By implementing these changes and maintaining them with our validation tools, we've achieved a more organized, consistent, and maintainable codebase that adheres to standard naming conventions and follows a clear structural pattern.