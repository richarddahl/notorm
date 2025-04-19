# Files and Modules to Remove

This document identifies files and modules that are no longer needed due to the comprehensive modernization efforts in the UNO framework. This list has been compiled based on an analysis of files that actually exist in the repository.

## Legacy Security Components

- `/src/uno/infrastructure/security/legacy/auth/manager.py`
- `/src/uno/infrastructure/security/legacy/auth/totp.py`
- `/src/uno/infrastructure/security/legacy/auth/password.py`
- `/src/uno/infrastructure/security/legacy/auth/sso.py`
- `/src/uno/infrastructure/security/legacy/auth/__init__.py`
- `/src/uno/infrastructure/security/legacy/auth/examples.py`
- `/src/uno/infrastructure/security/legacy/auth/fastapi_integration.py`
- `/src/uno/infrastructure/security/legacy/auth/token_cache.py`
- `/src/uno/infrastructure/security/auth/__init__.py`
- `/src/uno/infrastructure/security/auth/jwt.py`
- `/src/uno/infrastructure/authorization/legacy/api_integration.py`

## Deprecated Core Components

- `/src/uno/core/base/repository.py` - Legacy base repository implementation
- `/src/uno/core/base/service.py` - Legacy base service implementation
- `/src/uno/core/uow.py` - Legacy unit of work implementation
- `/src/uno/core/di_testing.py` - Legacy testing DI components
- `/src/uno/core/errors/validation.py` - Legacy validation error handling
- `/src/uno/core/events/event_basic.py` - Legacy event implementation replaced by unified events

## Legacy Dependency Injection Components

- `/src/uno/dependencies/database.py` - Contains deprecated database interfaces
- `/src/uno/dependencies/testing.py` - Legacy testing utilities
- `/src/uno/dependencies/testing_provider.py` - Legacy testing provider
- `/src/uno/dependencies/vector_interfaces.py` - Legacy vector interfaces
- `/src/uno/dependencies/vector_provider.py` - Legacy vector provider implementation

## Legacy Domain Components

- `/src/uno/domain/event_import_fix.py` - Temporary fix that's been properly integrated
- `/src/uno/domain/entity/compatibility.py` - Compatibility layer for legacy implementations
- `/src/uno/domain/repositories/repository_adapter.py` - Legacy repository adapter
- `/src/uno/domain/repositories/__init__.py` - Legacy repository module
- `/src/uno/domain/services/__init__.py` - Legacy services module
- `/src/uno/domain/services/base_domain_service.py` - Legacy service implementation
- `/src/uno/domain/specifications/__init__.py` - Legacy specifications module
- `/src/uno/domain/specification_translators/__init__.py` - Legacy specification translator module
- `/src/uno/domain/entities/__init__.py` - Legacy entities module
- `/src/uno/domain/core.py` - Legacy domain core implementation
- `/src/uno/domain/exceptions.py` - Legacy exception handling
- `/src/uno/domain/validation.py` - Legacy validation implementation
- `/src/uno/domain/api_example.py` - Legacy example code
- `/src/uno/domain/api_integration.py` - Legacy API integration
- `/src/uno/domain/protocols.py` - Duplicate protocol definitions

## Legacy API Components

- `/src/uno/api/domain_endpoints.py` - Legacy domain endpoints implementation
- `/src/uno/api/domain_repositories.py` - Legacy domain repositories for API
- `/src/uno/api/domain_services.py` - Legacy domain services for API
- `/src/uno/api/service_endpoint_adapter.py` - Legacy service endpoint adapter
- `/src/uno/api/service_endpoint_factory.py` - Legacy service endpoint factory
- `/src/uno/api/examples/migration_example.py` - Legacy migration example
- `/src/uno/api/entities.py` - Legacy entity implementations

## Legacy Infrastructure Components

- `/src/uno/infrastructure/repositories/__init__.py` - Legacy repository implementations
- `/src/uno/infrastructure/repositories/factory.py` - Legacy repository factory
- `/src/uno/infrastructure/repositories/di.py` - Legacy dependency injection for repositories
- `/src/uno/infrastructure/repositories/unit_of_work.py` - Legacy unit of work implementation
- `/src/uno/infrastructure/services/__init__.py` - Legacy service implementations
- `/src/uno/infrastructure/services/factory.py` - Legacy service factory
- `/src/uno/infrastructure/services/base_service.py` - Legacy base service
- `/src/uno/infrastructure/services/initialization.py` - Legacy service initialization
- `/src/uno/infrastructure/authorization/domain_endpoints.py` - Legacy domain endpoints for auth
- `/src/uno/infrastructure/authorization/api_integration.py` - Legacy API integration for auth
- `/src/uno/infrastructure/sql/classes.py` - Legacy SQL classes
- `/src/uno/infrastructure/database/db.py` - Legacy database implementation
- `/src/uno/infrastructure/database/enhanced_db.py` - Legacy enhanced DB implementation
- `/src/uno/infrastructure/database/enhanced_connection_pool.py` - Legacy connection pool
- `/src/uno/infrastructure/database/enhanced_pool_session.py` - Legacy pool session
- `/src/uno/infrastructure/database/enhanced_session.py` - Legacy session implementation
- `/src/uno/infrastructure/database/pooled_session.py` - Legacy pooled session
- `/src/uno/infrastructure/database/query_cache.py` - Legacy query cache

## Notes on Removal Process

When removing these files:

1. Verify each file is truly deprecated by checking for imports in the codebase
2. Remove any references or imports to these files from other parts of the codebase
3. Update any configuration files that might reference these modules
4. Run the test suite to ensure no functionality is broken
5. Update documentation to reflect the removal

## Removal Verification Process

To efficiently verify that a file can be safely removed:

1. Use the `grep` command to search for imports of the file or references to classes defined in the file
2. Check if the file is still in use and properly deprecated with warnings
3. Identify any dependencies that might break if the file is removed
4. Ensure that modern replacements for all functionality exist
5. Create unit tests for the modern implementations before removing legacy code

## Implementation Plan

The removal should happen in phases:

1. First mark all files with explicit deprecation warnings (if not already done)
2. Next remove files that are purely legacy and have no active dependencies
3. Then remove files that have dependencies but those dependencies have alternatives
4. Finally remove any compatibility modules

By following this structured approach to removing deprecated files, we can ensure a clean, modern codebase while maintaining stability and functionality.