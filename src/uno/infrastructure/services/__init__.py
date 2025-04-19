"""
Service pattern implementation for the Uno framework.

CRITICAL DEPRECATION NOTICE: This package has been deprecated and replaced by the new domain entity framework
in uno.domain.entity.service. Please use the new implementation instead.

All service functionality has been moved to uno.domain.entity.service and this package
will be removed in a future release.
"""

import warnings

warnings.warn(
    "CRITICAL: The uno.infrastructure.services package is deprecated and will be removed in a future release. "
    "Use uno.domain.entity.service instead for all service implementations.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new implementation to re-export
from uno.domain.entity.service import (
    DomainService,
    DomainServiceWithUnitOfWork,
    ApplicationService,
    CrudService,
    ServiceFactory
)

# Re-export protocols for backward compatibility
from uno.core.base.service import (
    ServiceProtocol,
    CrudServiceProtocol,
    QueryServiceProtocol,
    BaseService,
    BaseQueryService
)

# Re-export factory functionality
def create_service(*args, **kwargs):
    warnings.warn("create_service is deprecated", DeprecationWarning, stacklevel=2)
    return None

def create_crud_service(*args, **kwargs):
    warnings.warn("create_crud_service is deprecated", DeprecationWarning, stacklevel=2)
    return None

get_service_factory = lambda: None  # Stub for backward compatibility
initialize_services = lambda: None  # Stub for backward compatibility

# Legacy exports
TransactionalService = DomainServiceWithUnitOfWork
CrudService = CrudService
RepositoryQueryService = ApplicationService
EventPublisher = ApplicationService
DomainEventPublisherProtocol = object  # Stub protocol

# Legacy factory exports - all deprecated stubs
def create_aggregate_service(*args, **kwargs):
    warnings.warn("create_aggregate_service is deprecated", DeprecationWarning, stacklevel=2)
    return None

def create_query_service(*args, **kwargs):
    warnings.warn("create_query_service is deprecated", DeprecationWarning, stacklevel=2)
    return None

def create_application_service(*args, **kwargs):
    warnings.warn("create_application_service is deprecated", DeprecationWarning, stacklevel=2)
    return None

def create_event_publisher(*args, **kwargs):
    warnings.warn("create_event_publisher is deprecated", DeprecationWarning, stacklevel=2)
    return None

get_cached_service = lambda: None  # Stub for backward compatibility
clear_service_cache = lambda: None  # Stub for backward compatibility

# DI integration stubs
init_service_system = lambda: None  # Stub for backward compatibility
get_service_by_type = lambda: None  # Stub for backward compatibility
get_crud_service = lambda: None  # Stub for backward compatibility
get_aggregate_service = lambda: None  # Stub for backward compatibility
get_query_service = lambda: None  # Stub for backward compatibility
get_application_service = lambda: None  # Stub for backward compatibility
get_event_publisher = lambda: None  # Stub for backward compatibility
register_service = lambda: None  # Stub for backward compatibility
register_service_instance = lambda: None  # Stub for backward compatibility
register_crud_service = lambda: None  # Stub for backward compatibility
register_aggregate_service = lambda: None  # Stub for backward compatibility
register_query_service = lambda: None  # Stub for backward compatibility
register_application_service = lambda: None  # Stub for backward compatibility

# Initialization stubs
initialize_unified_services = lambda: None  # Stub for backward compatibility
get_service_diagram = lambda: None  # Stub for backward compatibility
ServiceDiagnostics = object  # Stub class

# Infrastructure-specific protocols
TransactionalServiceProtocol = ServiceProtocol
AggregateCrudServiceProtocol = CrudServiceProtocol
RepositoryQueryServiceProtocol = QueryServiceProtocol
ApplicationServiceProtocol = ServiceProtocol
EventCollectingServiceProtocol = ServiceProtocol
ReadModelServiceProtocol = QueryServiceProtocol

# Export everything for convenient imports
__all__ = [
    # Core services from new implementation
    "DomainService",
    "DomainServiceWithUnitOfWork",
    "ApplicationService",
    "CrudService",
    "ServiceFactory",
    
    # Legacy protocols
    "ServiceProtocol",
    "CrudServiceProtocol",
    "QueryServiceProtocol",
    "TransactionalServiceProtocol",
    "AggregateCrudServiceProtocol",
    "RepositoryQueryServiceProtocol",
    "ApplicationServiceProtocol",
    "EventCollectingServiceProtocol",
    "ReadModelServiceProtocol",
    "DomainEventPublisherProtocol",
    
    # Legacy base classes
    "BaseService",
    "BaseQueryService",
    "TransactionalService", 
    "RepositoryQueryService",
    "EventPublisher",
    
    # Legacy factory functions
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
    
    # Legacy DI integration
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
    
    # Legacy initialization
    "initialize_unified_services",
    "get_service_diagram",
    "ServiceDiagnostics"
]