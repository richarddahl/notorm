# Uno Repository File Documentation

This document provides a comprehensive overview of all source files in the Uno repository, organized by directory structure. Each file is classified into one of the following categories:

- **Unified Approach**: Files implementing the modern Domain-Driven Design principles with proper type hints and consistent structure
- **Legacy**: Files using older patterns, lacking type hints, or having inconsistent naming conventions
- **Supporting**: Files that provide utility/helper functionality
- **Documentation**: Documentation files and guides
- **Configuration**: Configuration files for the project, tests, or tools
- **Test**: Test files and testing infrastructure
- **Example**: Example code demonstrating usage

## Root Directory

- **README.md** - Main project documentation providing an overview of Uno framework features and usage. *Documentation*
- **CLAUDE.md** - Instructions for Claude Code AI when working with this codebase. *Documentation*
- **CODE.md** - Code standards and contribution guidelines. *Documentation*
- **LICENSE** - MIT license file for the project. *Documentation*
- **main.py** - Main entry point for the application. *Unified Approach*
- **pyproject.toml** - Python project configuration for dependency management and build settings. *Configuration*
- **pytest.ini** - Configuration for pytest test runner. *Configuration*
- **mypy.ini** - Configuration for mypy type checker. *Configuration*
- **mkdocs.yml** - Configuration for MkDocs documentation generator. *Configuration*
- **DDD_APPLICATION_DEVELOPMENT.md** - Guide for developing applications using Domain-Driven Design principles. *Documentation*
- **DDD_CODE_CLEANUP_PLAN.md** - Plan for cleaning up code to align with DDD principles. *Documentation*

## Docker Directory

### Docker Root

- **docker/Dockerfile** - Container definition for the PostgreSQL database with all required extensions. *Configuration*
- **docker/docker-compose.yaml** - Docker Compose configuration for the main development environment. *Configuration*
- **docker/docker-compose-pgadmin.yaml** - Docker Compose configuration for pgAdmin interface. *Configuration*
- **docker/download_pgvector.sh** - Script to download pgvector extension. *Supporting*
- **docker/init-db.sh** - Script to initialize the database with required roles and schemas. *Supporting*
- **docker/README.md** - Documentation for using Docker with the project. *Documentation*

### Docker Scripts

- **docker/scripts/download_pgvector.sh** - Script to download pgvector extension. *Supporting*
- **docker/scripts/init-db.sh** - Script to initialize the PostgreSQL database. *Supporting*
- **docker/scripts/init-extensions.sh** - Script to initialize PostgreSQL extensions. *Supporting*
- **docker/scripts/install_pgvector.sh** - Script to install pgvector extension. *Supporting*
- **docker/scripts/rebuild.sh** - Script to rebuild Docker containers. *Supporting*
- **docker/scripts/setup_test_docker.sh** - Script to set up Docker for testing. *Supporting*
- **docker/scripts/setup_with_docker.sh** - Script to set up development environment with Docker. *Supporting*

### Docker Test

- **docker/test/docker-compose.yaml** - Docker Compose configuration for test environment. *Configuration*

## Documentation (docs/)

The `docs/` directory contains extensive documentation organized by feature areas. All files in this directory are categorized as *Documentation*.

(Detailed listing of documentation files is omitted for brevity)

## Source Code (src/)

### Core Package (src/uno/core/)

- **src/uno/core/__init__.py** - Core package initialization. *Unified Approach*
- **src/uno/core/async_integration.py** - Integration utilities for asynchronous operations. *Unified Approach*
- **src/uno/core/async_manager.py** - Manager for asynchronous resources. *Unified Approach*
- **src/uno/core/async_utils.py** - Utilities for asynchronous programming. *Unified Approach*
- **src/uno/core/caching.py** - Caching implementation for improved performance. *Unified Approach*
- **src/uno/core/config.py** - Configuration management system. *Unified Approach*
- **src/uno/core/cqrs.py** - Command Query Responsibility Segregation pattern implementation. *Unified Approach*
- **src/uno/core/cqrs.py.bak** - Backup of previous CQRS implementation. *Legacy*
- **src/uno/core/cqrs_monitoring.py** - Monitoring extensions for CQRS. *Unified Approach*
- **src/uno/core/cqrs_optimizations.py** - Performance optimizations for CQRS. *Unified Approach*
- **src/uno/core/dataloader.py** - Data loading utilities. *Unified Approach*
- **src/uno/core/di.py** - Dependency injection system with lifecycle management. *Unified Approach*
- **src/uno/core/di.py.bak** - Backup of previous dependency injection implementation. *Legacy*
- **src/uno/core/di_adapter.py** - Adapter for the dependency injection system. *Unified Approach*
- **src/uno/core/di_fastapi.py** - FastAPI integration for dependency injection. *Unified Approach*
- **src/uno/core/di_testing.py** - Testing utilities for dependency injection. *Test*
- **src/uno/core/di_testing.py.bak** - Backup of previous testing utilities for dependency injection. *Legacy*
- **src/uno/core/domain.py** - Core domain model components. *Unified Approach*
- **src/uno/core/errors.py** - Error handling components. *Unified Approach*
- **src/uno/core/events.py** - Event system for domain events. *Legacy*
- **src/uno/core/fastapi_error_handlers.py** - Error handlers for FastAPI integration. *Unified Approach*
- **src/uno/core/fastapi_integration.py** - FastAPI integration utilities. *Unified Approach*
- **src/uno/core/feature_factory.py** - Factory for creating feature components. *Unified Approach*
- **src/uno/core/protocol_validator.py** - Validation system for protocol implementations. *Unified Approach*
- **src/uno/core/protocols.py** - Core protocol definitions. *Unified Approach*
- **src/uno/core/py.typed** - Marker file for type hints. *Unified Approach*
- **src/uno/core/resource_management.py** - Management of application resources. *Unified Approach*
- **src/uno/core/resource_monitor.py** - Monitoring of application resources. *Unified Approach*
- **src/uno/core/resources.py** - Resource definitions and abstractions. *Unified Approach*
- **src/uno/core/result.py** - Result pattern for functional error handling. *Unified Approach*
- **src/uno/core/types.py** - Core type definitions. *Unified Approach*
- **src/uno/core/unified_events.py** - Unified domain events system. *Unified Approach*
- **src/uno/core/uow.py** - Unit of Work pattern implementation. *Unified Approach*

#### Core Async Subpackage (src/uno/core/async/)

- **src/uno/core/async/__init__.py** - Async subpackage initialization. *Unified Approach*
- **src/uno/core/async/concurrency.py** - Enhanced concurrency primitives. *Unified Approach*
- **src/uno/core/async/context.py** - Context management for async operations. *Unified Approach*
- **src/uno/core/async/helpers.py** - Helper functions for async operations. *Unified Approach*
- **src/uno/core/async/task_manager.py** - Task management with proper cancellation. *Unified Approach*

#### Core Errors Subpackage (src/uno/core/errors/)

- **src/uno/core/errors/__init__.py** - Errors subpackage initialization. *Unified Approach*
- **src/uno/core/errors/base.py** - Base error classes. *Unified Approach*
- **src/uno/core/errors/catalog.py** - Error catalog with standardized error codes. *Unified Approach*
- **src/uno/core/errors/core_errors.py** - Core-specific error definitions. *Unified Approach*
- **src/uno/core/errors/examples.py** - Examples of error handling. *Example*
- **src/uno/core/errors/logging.py** - Error logging utilities. *Unified Approach*
- **src/uno/core/errors/py.typed** - Marker file for type hints. *Unified Approach*
- **src/uno/core/errors/result.py** - Result pattern implementation for error handling. *Unified Approach*
- **src/uno/core/errors/security.py** - Security-related error definitions. *Unified Approach*
- **src/uno/core/errors/validation.py** - Validation error handling. *Unified Approach*

#### Core Examples Subpackage (src/uno/core/examples/)

- **src/uno/core/examples/README.md** - Overview of example code. *Documentation*
- **src/uno/core/examples/__init__.py** - Examples subpackage initialization. *Example*
- **src/uno/core/examples/async_example.py** - Example of async patterns. *Example*
- **src/uno/core/examples/batch_operations_example.py** - Example of batch operations. *Example*
- **src/uno/core/examples/connection_pool_example.py** - Example of connection pooling. *Example*
- **src/uno/core/examples/cqrs_example.py** - Example of CQRS pattern. *Example*
- **src/uno/core/examples/di_fastapi_example.py** - Example of FastAPI with DI. *Example*
- **src/uno/core/examples/docs_example.py** - Example of documentation generation. *Example*
- **src/uno/core/examples/error_handling_example.py** - Example of error handling. *Example*
- **src/uno/core/examples/events_example.py** - Example of event system. *Example*
- **src/uno/core/examples/migration_example.py** - Example of migration. *Example*
- **src/uno/core/examples/modern_architecture_example.py** - Example of modern architecture. *Example*
- **src/uno/core/examples/monitoring_dashboard_example.py** - Example of monitoring dashboard. *Example*
- **src/uno/core/examples/monitoring_example.py** - Example of monitoring. *Example*
- **src/uno/core/examples/optimizer_metrics_example.py** - Example of optimizer metrics. *Example*
- **src/uno/core/examples/pg_optimizer_example.py** - Example of PostgreSQL optimizer. *Example*
- **src/uno/core/examples/plugin_example.py** - Example of plugin system. *Example*
- **src/uno/core/examples/query_cache_example.py** - Example of query caching. *Example*
- **src/uno/core/examples/query_optimizer_example.py** - Example of query optimization. *Example*
- **src/uno/core/examples/resource_example.py** - Example of resource management. *Example*
- **src/uno/core/examples/unified_events_example.py** - Example of unified events system. *Example*

### Domain Package (src/uno/domain/)

- **src/uno/domain/README.md** - Overview of domain module. *Documentation*
- **src/uno/domain/__init__.py** - Domain package initialization. *Unified Approach*
- **src/uno/domain/api_example.py** - Example of domain API. *Example*
- **src/uno/domain/api_integration.py** - Domain API integration. *Unified Approach*
- **src/uno/domain/application_example.py** - Example of application services. *Example*
- **src/uno/domain/application_services.py** - Application services. *Unified Approach*
- **src/uno/domain/authorization.py** - Domain authorization. *Unified Approach*
- **src/uno/domain/authorization_example.py** - Example of domain authorization. *Example*
- **src/uno/domain/bounded_context.py** - Bounded context implementation. *Unified Approach*
- **src/uno/domain/command_handlers.py** - Command handlers. *Unified Approach*
- **src/uno/domain/context_definitions.py** - Context definitions. *Unified Approach*
- **src/uno/domain/core.py** - Core domain components. *Unified Approach*
- **src/uno/domain/cqrs.py** - CQRS implementation. *Unified Approach*
- **src/uno/domain/cqrs_example.py** - Example of CQRS. *Example*
- **src/uno/domain/cqrs_read_model.py** - Read model for CQRS. *Unified Approach*
- **src/uno/domain/enhanced_query.py** - Enhanced query capabilities. *Unified Approach*
- **src/uno/domain/event_dispatcher.py** - Event dispatcher. *Unified Approach*
- **src/uno/domain/event_store.py** - Event store. *Unified Approach*
- **src/uno/domain/event_store_integration.py** - Event store integration. *Unified Approach*
- **src/uno/domain/event_store_manager.py** - Event store management. *Unified Approach*
- **src/uno/domain/events.py** - Domain events. *Legacy*
- **src/uno/domain/exceptions.py** - Domain exceptions. *Unified Approach*
- **src/uno/domain/factories.py** - Domain factories. *Unified Approach*
- **src/uno/domain/factory.py** - Factory pattern implementation. *Legacy*
- **src/uno/domain/graph_path_query.py** - Graph-based path queries. *Unified Approach*
- **src/uno/domain/index.py** - Domain indexing. *Unified Approach*
- **src/uno/domain/models.py** - Domain model definitions. *Legacy*
- **src/uno/domain/multi_tenant.py** - Multi-tenant support. *Unified Approach*
- **src/uno/domain/protocols.py** - Domain protocols. *Unified Approach*
- **src/uno/domain/query.py** - Query definition. *Legacy*
- **src/uno/domain/query_example.py** - Example of domain queries. *Example*
- **src/uno/domain/query_handlers.py** - Query handlers. *Unified Approach*
- **src/uno/domain/query_optimizer.py** - Query optimization. *Unified Approach*
- **src/uno/domain/rbac.py** - Role-based access control. *Unified Approach*
- **src/uno/domain/repositories.py** - Legacy repository pattern implementation. *Legacy*
- **src/uno/domain/repository.py** - Modern repository definition. *Unified Approach*
- **src/uno/domain/repository_adapter.py** - Adapter between old and new repository implementations. *Unified Approach*
- **src/uno/domain/repository_factory.py** - Factory for creating repositories. *Unified Approach*
- **src/uno/domain/repository_protocols.py** - Legacy repository protocols. *Legacy*
- **src/uno/domain/repository_results.py** - Legacy repository result types. *Legacy*
- **src/uno/domain/selective_updater.py** - Selective entity updating. *Unified Approach*
- **src/uno/domain/service.py** - Legacy domain service definition. *Legacy*
- **src/uno/domain/service_adapter.py** - Adapter between old and new service implementations. *Unified Approach*
- **src/uno/domain/service_example.py** - Example of domain service. *Example*
- **src/uno/domain/services.py** - Legacy domain services. *Legacy*
- **src/uno/domain/specification_translators.py** - Legacy specification translators. *Legacy*
- **src/uno/domain/specifications.py** - Legacy specification pattern implementation. *Legacy*
- **src/uno/domain/sqlalchemy_repositories.py** - Legacy SQLAlchemy repository implementations. *Legacy*
- **src/uno/domain/unified_services.py** - Modern domain service patterns. *Unified Approach*
- **src/uno/domain/unit_of_work.py** - Legacy unit of work pattern. *Legacy*
- **src/uno/domain/unit_of_work_standardized.py** - Modern unit of work pattern. *Unified Approach*
- **src/uno/domain/validation.py** - Domain validation. *Unified Approach*
- **src/uno/domain/value_objects.py** - Value objects implementation. *Unified Approach*
- **src/uno/domain/vector_events.py** - Vector search event handling. *Unified Approach*
- **src/uno/domain/vector_events_example.py** - Example of vector events. *Example*
- **src/uno/domain/vector_example.py** - Example of vector search. *Example*
- **src/uno/domain/vector_search.py** - Vector search implementation. *Unified Approach*
- **src/uno/domain/vector_update_service.py** - Vector update service. *Unified Approach*

#### Domain Factories Subpackage (src/uno/domain/factories/)

- **src/uno/domain/factories/__init__.py** - Factories subpackage initialization. *Unified Approach*
- **src/uno/domain/factories/entity_factory.py** - Entity factory implementation. *Unified Approach*

#### Domain Repositories Subpackage (src/uno/domain/repositories/)

- **src/uno/domain/repositories/__init__.py** - Repositories subpackage initialization. *Unified Approach*
- **src/uno/domain/repositories/base.py** - Base repository. *Unified Approach*
- **src/uno/domain/repositories/unit_of_work.py** - Unit of Work implementation. *Unified Approach*

#### Domain Repository Protocols Subpackage (src/uno/domain/repository_protocols/)

- **src/uno/domain/repository_protocols/__init__.py** - Repository protocols package initialization. *Unified Approach*
- **src/uno/domain/repository_protocols/repository_protocol.py** - Modern repository protocol definition. *Unified Approach*

#### Domain Repository Results Subpackage (src/uno/domain/repository_results/)

- **src/uno/domain/repository_results/__init__.py** - Repository results package initialization. *Unified Approach*
- **src/uno/domain/repository_results/repository_result.py** - Modern repository result definition. *Unified Approach*

#### Domain Specifications Subpackage (src/uno/domain/specifications/)

- **src/uno/domain/specifications/__init__.py** - Specifications package initialization. *Unified Approach*
- **src/uno/domain/specifications/base.py** - Base specification. *Unified Approach*
- **src/uno/domain/specifications/base_specifications.py** - Base specification implementations. *Unified Approach*
- **src/uno/domain/specifications/composite_specifications.py** - Composite specification implementations. *Unified Approach*
- **src/uno/domain/specifications/enhanced.py** - Enhanced specification implementations. *Unified Approach*

#### Domain Specification Translators Subpackage (src/uno/domain/specification_translators/)

- **src/uno/domain/specification_translators/__init__.py** - Specification translators package initialization. *Unified Approach*
- **src/uno/domain/specification_translators/postgresql.py** - PostgreSQL specification translator. *Unified Approach*
- **src/uno/domain/specification_translators/postgresql_translator.py** - Enhanced PostgreSQL specification translator. *Unified Approach*

### API Package (src/uno/api/)

- **src/uno/api/__init__.py** - API package initialization. *Unified Approach*
- **src/uno/api/admin_ui.py** - Admin UI integration. *Unified Approach*
- **src/uno/api/api_example.py** - Example of API usage. *Example*
- **src/uno/api/apidef.py** - API definitions. *Legacy*
- **src/uno/api/cqrs_integration.py** - CQRS integration with API. *Unified Approach*
- **src/uno/api/domain_endpoints.py** - Domain-driven endpoints. *Unified Approach*
- **src/uno/api/domain_provider.py** - Domain provider for API. *Unified Approach*
- **src/uno/api/domain_repositories.py** - Domain repositories for API. *Unified Approach*
- **src/uno/api/domain_services.py** - Domain services for API. *Unified Approach*
- **src/uno/api/endpoint.py** - Legacy endpoint definition. *Legacy*
- **src/uno/api/endpoint_factory.py** - Legacy factory for creating endpoints. *Legacy*
- **src/uno/api/entities.py** - API entity models. *Unified Approach*
- **src/uno/api/error_handlers.py** - API error handling. *Unified Approach*
- **src/uno/api/examples/domain_endpoint_example.py** - Example of domain endpoints. *Example*
- **src/uno/api/repository_adapter.py** - Repository adapter for API. *Unified Approach*
- **src/uno/api/service_api.py** - Service API. *Unified Approach*
- **src/uno/api/service_endpoint_adapter.py** - Service endpoint adapter. *Unified Approach*
- **src/uno/api/service_endpoint_example.py** - Example of service endpoint. *Example*
- **src/uno/api/service_endpoint_factory.py** - Modern factory for creating service endpoints. *Unified Approach*

### Dependencies Package (src/uno/dependencies/)

- **src/uno/dependencies/__init__.py** - Dependencies package initialization. *Unified Approach*
- **src/uno/dependencies/database.py** - Database dependencies. *Unified Approach*
- **src/uno/dependencies/decorators.py** - Dependency injection decorators. *Unified Approach*
- **src/uno/dependencies/discovery.py** - Dependency discovery. *Unified Approach*
- **src/uno/dependencies/fastapi_integration.py** - FastAPI dependency integration. *Unified Approach*
- **src/uno/dependencies/fastapi_provider.py** - FastAPI dependency provider. *Legacy*
- **src/uno/dependencies/interfaces.py** - Dependency interfaces. *Unified Approach*
- **src/uno/dependencies/modern_provider.py** - Modern dependency provider. *Unified Approach*
- **src/uno/dependencies/repository.py** - Repository dependencies. *Unified Approach*
- **src/uno/dependencies/resolution_errors.py** - Dependency resolution errors. *Unified Approach*
- **src/uno/dependencies/scoped_container.py** - Scoped dependency container. *Unified Approach*
- **src/uno/dependencies/service.py** - Service dependencies. *Unified Approach*
- **src/uno/dependencies/testing.py** - Testing utilities for dependencies. *Test*
- **src/uno/dependencies/testing_provider.py** - Testing provider for dependencies. *Test*
- **src/uno/dependencies/vector_interfaces.py** - Vector search dependency interfaces. *Unified Approach*
- **src/uno/dependencies/vector_provider.py** - Vector search dependency provider. *Unified Approach*

### Infrastructure Package (src/uno/infrastructure/)

#### Infrastructure Database Subpackage (src/uno/infrastructure/database/)

- **src/uno/infrastructure/database/__init__.py** - Database subpackage initialization. *Unified Approach*
- **src/uno/infrastructure/database/config.py** - Database configuration. *Unified Approach*
- **src/uno/infrastructure/database/connection_health.py** - Database connection health. *Unified Approach*
- **src/uno/infrastructure/database/connection_health_integration.py** - Database connection health integration. *Unified Approach*
- **src/uno/infrastructure/database/db.py** - Database access. *Legacy*
- **src/uno/infrastructure/database/db_manager.py** - Database manager. *Legacy*
- **src/uno/infrastructure/database/enhanced_connection_pool.py** - Enhanced database connection pool. *Unified Approach*
- **src/uno/infrastructure/database/enhanced_db.py** - Enhanced database access. *Unified Approach*
- **src/uno/infrastructure/database/enhanced_pool_session.py** - Enhanced pooled database session. *Unified Approach*
- **src/uno/infrastructure/database/enhanced_session.py** - Enhanced database session. *Unified Approach*
- **src/uno/infrastructure/database/query_cache.py** - Database query cache. *Unified Approach*
- **src/uno/infrastructure/database/query_optimizer.py** - Database query optimizer. *Unified Approach*

#### Infrastructure SQL Subpackage (src/uno/infrastructure/sql/)

- **src/uno/infrastructure/sql/__init__.py** - SQL subpackage initialization. *Unified Approach*
- **src/uno/infrastructure/sql/emitter.py** - Base SQL emitter. *Unified Approach*
- **src/uno/infrastructure/sql/registry.py** - SQL registry. *Unified Approach*
- **src/uno/infrastructure/sql/statement.py** - SQL statement construction. *Unified Approach*

### Examples Package (src/uno/examples/)

#### E-Commerce App Example (src/uno/examples/ecommerce_app/)

- **src/uno/examples/ecommerce_app/README.md** - Overview of e-commerce example. *Documentation*
- **src/uno/examples/ecommerce_app/__init__.py** - E-commerce package initialization. *Example*
- **src/uno/examples/ecommerce_app/main.py** - E-commerce application entry point. *Example*
- **src/uno/examples/ecommerce_app/shared/value_objects.py** - Shared value objects for e-commerce. *Example*

##### Catalog Context (src/uno/examples/ecommerce_app/catalog/)

- **src/uno/examples/ecommerce_app/catalog/__init__.py** - Catalog context initialization. *Example*
- **src/uno/examples/ecommerce_app/catalog/domain/entities.py** - Catalog domain entities. *Example*
- **src/uno/examples/ecommerce_app/catalog/domain/events.py** - Catalog domain events. *Example*
- **src/uno/examples/ecommerce_app/catalog/domain/value_objects.py** - Catalog domain value objects. *Example*
- **src/uno/examples/ecommerce_app/catalog/repository/models.py** - Catalog repository models. *Example*
- **src/uno/examples/ecommerce_app/catalog/repository/specifications.py** - Catalog repository specifications. *Example*
- **src/uno/examples/ecommerce_app/catalog/api/product_endpoints.py** - Catalog product endpoints. *Example*
- **src/uno/examples/ecommerce_app/catalog/api/category_endpoints.py** - Catalog category endpoints. *Example*
- **src/uno/examples/ecommerce_app/catalog/services/product_service.py** - Catalog product services. *Example*

##### Other Contexts (Placeholder)

- **src/uno/examples/ecommerce_app/order/__init__.py** - Order context initialization. *Example*
- **src/uno/examples/ecommerce_app/customer/__init__.py** - Customer context initialization. *Example*
- **src/uno/examples/ecommerce_app/cart/__init__.py** - Cart context initialization. *Example*
- **src/uno/examples/ecommerce_app/shipping/__init__.py** - Shipping context initialization. *Example*
- **src/uno/examples/ecommerce_app/payment/__init__.py** - Payment context initialization. *Example*

## Test Code (tests/)

### Unit Tests (tests/unit/)

- **tests/unit/core/test_unified_events.py** - Tests for unified events system. *Test*
- **tests/unit/domain/test_unified_services.py** - Tests for unified domain services. *Test*
- **tests/unit/domain/test_repository.py** - Tests for domain repository. *Test*
- **tests/unit/domain/test_specification_translators.py** - Tests for specification translators. *Test*
- **tests/unit/api/test_service_endpoint_integration.py** - Tests for service endpoint integration. *Test*

(Many more test files exist but are not listed for brevity)

### Legacy Tests (tests/unit_unittest/)

- **tests/unit_unittest/database/test_db_basic.py** - Legacy tests for database basics. *Legacy*
- **tests/unit_unittest/database/test_db_create.py** - Legacy tests for database creation. *Legacy*
- **tests/unit_unittest/database/test_db_filter.py** - Legacy tests for database filtering. *Legacy*
- **tests/unit_unittest/database/test_db_get.py** - Legacy tests for database retrieval. *Legacy*
- **tests/unit_unittest/database/test_db_merge.py** - Legacy tests for database merging. *Legacy*
- **tests/unit_unittest/database/test_session_async.py** - Legacy tests for async session. *Legacy*
- **tests/unit_unittest/database/test_session_mock.py** - Legacy tests for mocked sessions. *Legacy*

## Scripts (scripts/ and src/scripts/)

### Migration and Modernization Scripts

- **src/scripts/modernize_async.py** - Script to modernize async code. *Supporting*
- **src/scripts/modernize_datetime.py** - Script to modernize datetime usage. *Supporting*
- **src/scripts/modernize_domain.py** - Script to modernize domain code. *Supporting*
- **src/scripts/modernize_result.py** - Script to modernize result pattern usage. *Supporting*
- **src/scripts/check_all_modules_ddd.py** - Script to check all modules for DDD compliance. *Supporting*

### Docker and Database Scripts

- **scripts/docker/start.sh** - Script to start Docker containers. *Supporting*
- **scripts/docker/stop.sh** - Script to stop Docker containers. *Supporting*
- **src/scripts/createdb.py** - Script to create database. *Supporting*
- **src/scripts/dropdb.py** - Script to drop database. *Supporting*
- **src/scripts/db_init.py** - Script to initialize database. *Supporting*

### Development Tools

- **src/scripts/ddd_generator.py** - Script to generate DDD code. *Supporting*
- **scripts/launch_modeler.sh** - Script to launch the visual modeler. *Supporting*
- **src/scripts/generate_docs.py** - Script to generate documentation. *Supporting*
- **src/scripts/attributes_cli.py** - CLI for managing attributes. *Supporting*
- **src/scripts/values_cli.py** - CLI for managing values. *Supporting*
- **src/scripts/reports_cli.py** - CLI for managing reports. *Supporting*