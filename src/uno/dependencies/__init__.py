"""
Dependencies module for Uno framework.

This module provides a modern dependency injection system
to improve testability, maintainability, and decoupling of components.

The module offers a decorator-based approach to dependency management
with proper scope handling and automatic discovery of injectable services.
"""

# Interfaces
from uno.dependencies.interfaces import (
    UnoServiceProtocol, 
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol,
    SchemaManagerProtocol,
    DomainServiceProtocol,
    EventBusProtocol,
)

# Implementations
from uno.dependencies.service import UnoService, CrudService

# Modern FastAPI integration is imported separately
# Modern FastAPI integration was removed as part of backward compatibility removal

# Database integration
from uno.dependencies.database import (
    get_db_session,
    get_raw_connection,
    get_repository,
    get_db_manager,
    get_sql_emitter_factory,
    get_sql_execution_service,
    get_schema_manager,
    get_event_bus,
    get_event_publisher,
    get_domain_registry,
    get_domain_repository,
    get_domain_service
)

# Vector search interfaces
from uno.dependencies.vector_interfaces import (
    VectorSearchServiceProtocol,
    RAGServiceProtocol,
    VectorUpdateServiceProtocol,
    BatchVectorUpdateServiceProtocol,
    VectorConfigServiceProtocol
)

# Vector search implementations
try:
    from uno.dependencies.vector_provider import (
        get_vector_search_service,
        get_rag_service
    )
except ImportError:
    # Vector search components not available
    get_vector_search_service = None
    get_rag_service = None

# New modern DI system
try:
    from uno.dependencies.scoped_container import (
        ServiceScope,
        ServiceCollection,
        ServiceResolver,
        get_service,
        create_scope,
        create_async_scope
    )
    
    from uno.dependencies.modern_provider import (
        UnoServiceProvider,
        ServiceLifecycle,
        get_service_provider as get_modern_provider,
        initialize_services as initialize_modern_services,
        shutdown_services
    )
    
    from uno.dependencies.decorators import (
        service,
        singleton,
        scoped,
        transient,
        inject,
        inject_params,
        injectable_class,
        injectable_endpoint
    )
    
    try:
        # Using internal fastapi_integration module directly
        from uno.dependencies.modern_fastapi import (
            configure_fastapi,
            DIAPIRouter,
            resolve_service,
            RequestScopeMiddleware,
            get_request_scope,
            lifespan
        )
    except ImportError:
        # Modern FastAPI integration not available
        configure_fastapi = None
        DIAPIRouter = None
        resolve_service = None
        RequestScopeMiddleware = None
        get_request_scope = None
        lifespan = None
    
    from uno.dependencies.discovery import (
        discover_services,
        register_services_in_package,
        scan_directory_for_services
    )
    
    MODERN_DI_AVAILABLE = True
except ImportError:
    # Modern DI system not available
    MODERN_DI_AVAILABLE = False


# Testing utilities
import os
if os.environ.get('ENV') == 'test':
    from uno.dependencies.testing import (
        TestingContainer,
        MockRepository,
        MockConfig,
        MockService,
        TestSession,
        TestSessionProvider,
        configure_test_container
    )


__all__ = [
    # Modern DI functionality uses decorator-based approach
    
    # Interfaces
    "UnoServiceProtocol",
    "UnoConfigProtocol",
    "UnoDatabaseProviderProtocol",
    "UnoDBManagerProtocol",
    "SQLEmitterFactoryProtocol",
    "SQLExecutionProtocol",
    "SchemaManagerProtocol",
    "DomainServiceProtocol",
    "EventBusProtocol",
    
    # Vector Search Interfaces
    "VectorSearchServiceProtocol",
    "RAGServiceProtocol",
    "VectorUpdateServiceProtocol",
    "BatchVectorUpdateServiceProtocol",
    "VectorConfigServiceProtocol",
    
    # Implementations
    "UnoService",
    "CrudService",
    
    # Modern FastAPI integration is in fastapi_integration module
    
    # Database integration
    "get_db_session",
    "get_raw_connection",
    "get_repository",
    "get_db_manager",
    "get_sql_emitter_factory",
    "get_sql_execution_service",
    "get_schema_manager",
    
    # Domain integration
    "get_event_bus",
    "get_event_publisher",
    "get_domain_registry",
    "get_domain_repository",
    "get_domain_service",
    
    # Modern service provider functionality is in UnoServiceProvider
    
    # Vector search implementations
    "get_vector_search_service",
    "get_rag_service",
]

# Add testing utilities if in test environment
if os.environ.get('ENV') == 'test':
    __all__ += [
        "TestingContainer",
        "MockConfig",
        "MockService",
        "TestSession",
        "TestSessionProvider",
        "configure_test_container",
    ]

# Add modern DI system if available
if MODERN_DI_AVAILABLE:
    __all__ += [
        # New DI core
        "ServiceScope",
        "ServiceCollection",
        "ServiceResolver",
        "get_service",
        "create_scope",
        "create_async_scope",
        
        # Modern provider
        "UnoServiceProvider",
        "ServiceLifecycle",
        "get_modern_provider",
        "initialize_modern_services",
        "shutdown_services",
        
        # Decorators
        "service",
        "singleton",
        "scoped",
        "transient",
        "inject",
        "inject_params",
        "injectable_class",
        "injectable_endpoint",
        
        # FastAPI integration
        "configure_fastapi",
        "DIAPIRouter",
        "resolve_service",
        "RequestScopeMiddleware",
        "get_request_scope",
        "lifespan",
        
        # Service discovery
        "discover_services",
        "register_services_in_package",
        "scan_directory_for_services"
    ]