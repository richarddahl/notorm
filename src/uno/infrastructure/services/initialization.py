"""
Initialization for the Uno framework service pattern.

This module provides functions for initializing the service pattern in the application,
registering it with the dependency injection system, and configuring it to work with
other components of the framework.
"""

import logging
from typing import Optional, Dict, Any

from uno.dependencies.scoped_container import ServiceCollection
from uno.infrastructure.repositories.di import init_repository_system
from uno.infrastructure.services.di import init_service_system
from uno.infrastructure.services.base import Service, CrudService, EventPublisher
from uno.infrastructure.services.factory import ServiceFactory
from uno.core.events import EventBus
from uno.core.errors.result import Result


async def initialize_unified_services(
    service_collection: Optional[ServiceCollection] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Initialize the unified service pattern.
    
    This function initializes the repository and service systems,
    configuring them to work together seamlessly. It should be called
    during application startup.
    
    Args:
        service_collection: Optional service collection to register with
        logger: Optional logger for initialization
    """
    # Get or create a logger
    logger = logger or logging.getLogger("uno.services")
    logger.info("Initializing unified service pattern")
    
    # Create a service collection if not provided
    if service_collection is None:
        service_collection = ServiceCollection()
    
    # Initialize the repository system
    init_repository_system(service_collection)
    
    # Initialize the service system
    init_service_system(service_collection)
    
    # Register the event bus
    event_bus = EventBus(logger=logging.getLogger("uno.events"))
    service_collection.add_instance(EventBus, event_bus)
    
    # Register the event publisher
    service_collection.add_instance(
        EventPublisher,
        EventPublisher(event_bus=event_bus, logger=logging.getLogger("uno.events"))
    )
    
    logger.info("Unified service pattern initialized successfully")


def get_service_diagram() -> str:
    """
    Get a text-based diagram of the service pattern.
    
    Returns:
        A text-based diagram of the service pattern
    """
    return """
    Unified Service Pattern Architecture
    ===================================
    
    ┌──────────────────────────────────────────────────────────────────┐
    │                         Service Protocols                         │
    │                                                                  │
    │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
    │  │ServiceProtocol│  │CrudService    │  │ApplicationService   │   │
    │  │              │  │Protocol       │  │Protocol             │   │
    │  └──────────────┘  └───────────────┘  └─────────────────────┘   │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
                                   ▲                                    
                                   │                                    
                                   │                                    
    ┌──────────────────────────────────────────────────────────────────┐
    │                       Service Implementations                     │
    │                                                                  │
    │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
    │  │Service       │  │CrudService    │  │ApplicationService   │   │
    │  │              │  │               │  │                     │   │
    │  └──────────────┘  └───────────────┘  └─────────────────────┘   │
    │         ▲                  ▲                   ▲                 │
    │         │                  │                   │                 │
    │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
    │  │Transactional │  │AggregateRoot  │  │EventCollecting      │   │
    │  │Service       │  │Service        │  │Service              │   │
    │  └──────────────┘  └───────────────┘  └─────────────────────┘   │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
                ▲                    ▲                    ▲              
                │                    │                    │              
                │                    │                    │              
    ┌───────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ Service Factory   │  │     DI System    │  │Repository System │
    │                   │  │                  │  │                  │
    │ ┌─────────────┐  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │
    │ │ServiceFactory│  │  │ │ServiceResolver│ │  │ │Repository    │ │
    │ │             │  │  │ │              │ │  │ │Protocol      │ │
    │ └─────────────┘  │  │ └──────────────┘ │  │ └──────────────┘ │
    │                   │  │                  │  │                  │
    │ ┌─────────────┐  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │
    │ │create_service│  │  │ │get_service   │ │  │ │AbstractUnitOf│ │
    │ │             │  │  │ │              │ │  │ │Work (core.uow)│ │
    │ └─────────────┘  │  │ └──────────────┘ │  │ └──────────────┘ │
    │                   │  │                  │  │                  │
    └───────────────────┘  └──────────────────┘  └──────────────────┘
    """




class ServiceDiagnostics(Service):
    """
    Service diagnostics utility.
    
    This service provides diagnostic information about the service pattern,
    including capabilities, performance metrics, and health checks.
    """
    
    async def get_capabilities(self) -> Result[Dict[str, Any]]:
        """
        Get the capabilities of the service pattern.
        
        Returns:
            Result containing the capabilities
        """
        capabilities = {
            "services": {
                "base": "Basic service functionality with error handling",
                "crud": "CRUD operations for entities",
                "aggregate": "Aggregate root operations with optimistic concurrency",
                "query": "Read-only operations optimized for querying",
                "application": "Complex operations that coordinate multiple services",
                "transactional": "Operations that require transaction management",
                "event_collecting": "Operations that publish domain events",
            },
            "features": {
                "result_pattern": "Error handling using Result objects",
                "dependency_injection": "Automatic dependency resolution",
                "event_integration": "Integration with the domain event system",
                "repository_integration": "Integration with the repository pattern",
                "async_support": "Support for asynchronous operations",
                "validation": "Input validation",
                "error_handling": "Consistent error handling",
                "logging": "Comprehensive logging",
            },
            "components": {
                "factory": "Factory for creating services",
                "di": "Dependency injection integration",
                "protocols": "Interface definitions",
                "base": "Base implementations",
                "examples": "Example implementations",
                "migration": "Migration guide from legacy services",
            }
        }
        
        return Result.success(capabilities)
    
    async def run_health_check(self) -> Result[Dict[str, Any]]:
        """
        Run a health check on the service pattern.
        
        Returns:
            Result containing the health check results
        """
        # Check if factory is available
        from uno.infrastructure.services.factory import get_service_factory
        try:
            factory = get_service_factory()
            factory_available = True
        except Exception:
            factory_available = False
        
        # Check if DI is available
        from uno.infrastructure.services.di import get_service_by_type
        try:
            get_service_by_type(ServiceDiagnostics)
            di_available = True
        except Exception:
            di_available = True
        
        # Check if repository system is available
        from uno.infrastructure.repositories.di import get_repository
        try:
            get_repository.__module__
            repository_available = True
        except Exception:
            repository_available = False
        
        # Check if event system is available
        from uno.core.events import get_event_bus
        try:
            get_event_bus.__module__
            event_system_available = True
        except Exception:
            event_system_available = False
        
        # Return results
        return Result.success({
            "factory_available": factory_available,
            "di_available": di_available,
            "repository_available": repository_available,
            "event_system_available": event_system_available,
            "status": "healthy" if all([
                factory_available,
                di_available,
                repository_available,
                event_system_available
            ]) else "degraded"
        })