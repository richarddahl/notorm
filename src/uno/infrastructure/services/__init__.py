"""
Service pattern implementation for the Uno framework.

This package provides a comprehensive implementation of the service pattern,
with support for various service capabilities, including:

- Basic service functionality with error handling
- CRUD services for entity operations
- Aggregate services for domain roots
- Query services for read operations
- Application services for coordinating complex operations
- Event collection for domain events
- Transactional services with Unit of Work

The implementation is designed to integrate with the repository pattern,
dependency injection system, and event system of the Uno framework.
"""

# Protocols
from uno.infrastructure.services.protocols import (
    ServiceProtocol,
    TransactionalServiceProtocol,
    CrudServiceProtocol,
    AggregateCrudServiceProtocol,
    QueryServiceProtocol,
    RepositoryQueryServiceProtocol,
    ApplicationServiceProtocol,
    EventCollectingServiceProtocol,
    ReadModelServiceProtocol,
    DomainEventPublisherProtocol
)

# Base implementations
from uno.infrastructure.services.base import (
    Service,
    TransactionalService,
    CrudService,
    AggregateCrudService,
    QueryService,
    RepositoryQueryService,
    ApplicationService,
    EventPublisher
)

# Factory functions
from uno.infrastructure.services.factory import (
    ServiceFactory,
    get_service_factory,
    create_service,
    create_crud_service,
    create_aggregate_service,
    create_query_service,
    create_application_service,
    create_event_publisher,
    get_cached_service,
    clear_service_cache
)

# DI integration
from uno.infrastructure.services.di import (
    init_service_system,
    get_service_by_type,
    get_crud_service,
    get_aggregate_service,
    get_query_service,
    get_application_service,
    get_event_publisher,
    register_service,
    register_service_instance,
    register_crud_service,
    register_aggregate_service,
    register_query_service,
    register_application_service
)

# Initialization
from uno.infrastructure.services.initialization import (
    initialize_unified_services,
    get_service_diagram,
    ServiceDiagnostics
)

# Export everything for convenient imports
__all__ = [
    # Protocols
    "ServiceProtocol",
    "TransactionalServiceProtocol",
    "CrudServiceProtocol",
    "AggregateCrudServiceProtocol",
    "QueryServiceProtocol",
    "RepositoryQueryServiceProtocol",
    "ApplicationServiceProtocol",
    "EventCollectingServiceProtocol",
    "ReadModelServiceProtocol",
    "DomainEventPublisherProtocol",
    
    # Base implementations
    "Service",
    "TransactionalService",
    "CrudService",
    "AggregateCrudService",
    "QueryService",
    "RepositoryQueryService",
    "ApplicationService",
    "EventPublisher",
    
    # Factory functions
    "ServiceFactory",
    "get_service_factory",
    "create_service",
    "create_crud_service",
    "create_aggregate_service",
    "create_query_service",
    "create_application_service",
    "create_event_publisher",
    "get_cached_service",
    "clear_service_cache",
    
    # DI integration
    "init_service_system",
    "get_service_by_type",
    "get_crud_service",
    "get_aggregate_service",
    "get_query_service",
    "get_application_service",
    "get_event_publisher",
    "register_service",
    "register_service_instance",
    "register_crud_service",
    "register_aggregate_service",
    "register_query_service",
    "register_application_service",
    
    # Initialization
    "initialize_unified_services",
    "get_service_diagram",
    "ServiceDiagnostics"
]