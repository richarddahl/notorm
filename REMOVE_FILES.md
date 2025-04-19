# Files and Modules to Remove

This document identifies files and modules that are no longer needed due to the comprehensive modernization efforts in the UNO framework. All files listed below have been verified to exist in the repository and have been superseded by modern implementations.

## Core Module Deprecated Files

- `/src/uno/model.py` - Legacy model definitions replaced by the unified domain entity framework
- `/src/uno/mixins.py` - Legacy mixins that have been integrated into the new domain models
- `/src/uno/core/protocols/database.py` - Contains backward compatibility aliases (UnoDatabaseProviderProtocol)
- `/src/uno/core/config.py` - Contains backward compatibility for UnoConfigProtocol

## Interface and Dependency Injection Files

- `/src/uno/dependencies/interfaces.py` - Contains references to deprecated interfaces
- `/src/uno/dependencies/service.py` - Legacy service dependency injection
- `/src/uno/dependencies/database.py` - Contains deprecated database interfaces
- `/src/uno/dependencies/vector_interfaces.py` - Legacy vector interfaces
- `/src/uno/dependencies/vector_provider.py` - Legacy vector provider

## API and Endpoint Files

- `/src/uno/api/service_endpoint_factory.py` - Explicitly marked as deprecated, only imports from new implementation
- `/src/uno/api/service_api.py` - Contains UnoEndpoint references that have been replaced
- `/src/uno/api/repository_adapter.py` - Legacy adapter replaced by the unified repository pattern
- `/src/uno/values/api_integration.py` - Legacy API integration
- `/src/uno/values/domain_endpoints_factory.py` - Legacy endpoints factory
- `/src/uno/values/domain_endpoints.py` - Legacy endpoints implementation
- `/src/uno/attributes/api_integration.py` - Legacy API integration
- `/src/uno/application/queries/api_integration.py` - Legacy API integration

## Database and Infrastructure Files

- `/src/uno/infrastructure/database/db.py` - Deprecated database implementation
- `/src/uno/infrastructure/database/enhanced_connection_pool.py` - Legacy connection pool
- `/src/uno/infrastructure/database/enhanced_db.py` - Legacy enhanced DB implementation
- `/src/uno/infrastructure/repositories/base.py` - Legacy repository implementations
- `/src/uno/infrastructure/repositories/__init__.py` - Contains deprecated implementations
- `/src/uno/infrastructure/repositories/sqlalchemy.py` - Legacy SQLAlchemy integration
- `/src/uno/infrastructure/services/__init__.py` - Legacy service implementations
- `/src/uno/infrastructure/sql/emitters/vector_temp.py` - Temporary implementation marked for replacement
- `/src/uno/infrastructure/database/pg_error_handler.py` - Legacy error handling for PostgreSQL

## Domain Module Files

- `/src/uno/domain/specification_translators.py` - Legacy implementation replaced by new specification system
- `/src/uno/domain/__init__.py` - Contains deprecated implementations and imports
- `/src/uno/dto/__init__.py` - Legacy DTO implementation replaced by the unified approach

## Modernization Scripts (Completed One-Time Scripts)

- `/src/scripts/modernize_imports.py` - One-time import modernization script
- `/src/scripts/modernize_async.py` - One-time async modernization script
- `/src/scripts/modernize_domain.py` - One-time domain modernization script
- `/src/scripts/modernize_result.py` - One-time result pattern modernization script

## Debug Tools

- `/src/uno/devtools/debugging/middleware.py` - Contains deprecated implementations

## Implementation Plan

The removal process should be carefully managed to ensure system stability:

1. **Phase 1: Verification**
   - For each file, verify that it's truly deprecated by searching for all imports
   - Ensure that all functionality has a modern replacement
   - Run tests to confirm the modern implementations work correctly

2. **Phase 2: Explicit Deprecation**
   - Add explicit deprecation warnings to any files that don't already have them
   - Update documentation to reflect that these components are deprecated

3. **Phase 3: Staged Removal**
   - First remove files marked as "compatibility" or explicit transitional modules
   - Next remove one-time modernization scripts
   - Then remove core deprecated implementations
   - Finally remove legacy implementations in domain, infrastructure, and API layers

4. **Phase 4: Validation**
   - After each removal, run the test suite to ensure functionality is preserved
   - Check for any broken imports or references
   - Update documentation to reflect the changes

## Post-Removal Cleanup

After removing the deprecated files:

1. Update any remaining import statements that point to new locations
2. Remove any references to deprecated components from documentation
3. Update the architecture documentation to reflect the simplified structure
4. Run a full test suite to ensure all functionality works correctly

By removing these deprecated files, we'll complete the modernization of the UNO framework, resulting in a cleaner, more maintainable codebase with a unified architecture.