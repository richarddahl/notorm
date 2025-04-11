"""
Dependencies module for Uno framework.

This module provides a centralized dependency injection system
to improve testability, maintainability, and decoupling of components.

The module offers two complementary approaches to dependency management:
1. The traditional access methods that directly use inject.instance()
2. The unified ServiceProvider pattern for centralized service access
3. The new modern DI system with proper scoping and decorator-based registration
"""

# Legacy DI system (for backward compatibility)
from uno.dependencies.container import configure_di, get_container, get_instance
from uno.dependencies.provider import ServiceProvider, get_service_provider, initialize_services

# Interfaces
from uno.dependencies.interfaces import (
    UnoRepositoryProtocol, 
    UnoServiceProtocol, 
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol,
    SchemaManagerProtocol,
    DomainRepositoryProtocol,
    DomainServiceProtocol,
    EventBusProtocol,
)

# Implementations
from uno.dependencies.repository import UnoRepository
from uno.dependencies.service import UnoService, CrudService

# FastAPI integration (legacy)
from uno.dependencies.fastapi import (
    inject_dependency,
    get_config
)

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
    
    from uno.dependencies.fastapi_integration import (
        configure_fastapi,
        DIAPIRouter,
        resolve_service,
        RequestScopeMiddleware,
        get_request_scope,
        lifespan
    )
    
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
    # Container (legacy)
    "configure_di",
    "get_container",
    "get_instance",
    
    # Interfaces
    "UnoRepositoryProtocol",
    "UnoServiceProtocol",
    "UnoConfigProtocol",
    "UnoDatabaseProviderProtocol",
    "UnoDBManagerProtocol",
    "SQLEmitterFactoryProtocol",
    "SQLExecutionProtocol",
    "SchemaManagerProtocol",
    "DomainRepositoryProtocol",
    "DomainServiceProtocol",
    "EventBusProtocol",
    
    # Vector Search Interfaces
    "VectorSearchServiceProtocol",
    "RAGServiceProtocol",
    "VectorUpdateServiceProtocol",
    "BatchVectorUpdateServiceProtocol",
    "VectorConfigServiceProtocol",
    
    # Implementations
    "UnoRepository",
    "UnoService",
    "CrudService",
    
    # FastAPI integration (legacy)
    "inject_dependency",
    "get_config",
    
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
    
    # Service Provider (legacy)
    "ServiceProvider",
    "get_service_provider",
    "initialize_services",
    
    # Vector search implementations
    "get_vector_search_service",
    "get_rag_service",
]

# Add testing utilities if in test environment
if os.environ.get('ENV') == 'test':
    __all__ += [
        "TestingContainer",
        "MockRepository",
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