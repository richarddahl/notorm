"""
Adapter module for transitioning from DIContainer to UnoServiceProvider.

This module provides adapter functions and compatibility layers for
transitioning from the legacy DIContainer system to the modern
UnoServiceProvider system.

This module should only be used during the transition period and
should be removed once the transition is complete.
"""

import logging
import inspect
from contextlib import contextmanager, asynccontextmanager
from typing import Dict, Type, TypeVar, Any, Optional, Callable, cast

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
    get_service_provider,
)
from uno.dependencies.scoped_container import (
    ServiceScope,
    create_scope as modern_create_scope,
    create_async_scope as modern_create_async_scope,
)

# Legacy imports (for type compatibility)
# Define ServiceLifetime enum for compatibility
class ServiceLifetime:
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"

T = TypeVar('T')


def get_container():
    """
    Legacy compatibility function for getting the global container.
    
    This function is a drop-in replacement for the legacy get_container()
    function, returning a container-like object that uses UnoServiceProvider
    under the hood.
    
    Returns:
        A container-like object
    """
    return ContainerAdapter()


def get_service(service_type: Type[T]) -> T:
    """
    Legacy compatibility function for getting a service.
    
    This function is a drop-in replacement for the legacy get_service()
    function, resolving services from the UnoServiceProvider.
    
    Args:
        service_type: The type of service to resolve
        
    Returns:
        An instance of the requested service
    """
    provider = get_service_provider()
    return provider.get_service(service_type)


@contextmanager
def create_scope(scope_id: Optional[str] = None):
    """
    Legacy compatibility function for creating a scope.
    
    This function is a drop-in replacement for the legacy create_scope()
    function, creating a scope using the UnoServiceProvider.
    
    Args:
        scope_id: Optional scope identifier
        
    Yields:
        The created scope
    """
    with modern_create_scope(scope_id) as scope:
        yield ScopeAdapter(scope)


@asynccontextmanager
async def create_async_scope(scope_id: Optional[str] = None):
    """
    Legacy compatibility function for creating an async scope.
    
    This function is a drop-in replacement for the legacy create_async_scope()
    function, creating an async scope using the UnoServiceProvider.
    
    Args:
        scope_id: Optional scope identifier
        
    Yields:
        The created scope
    """
    async with modern_create_async_scope(scope_id) as scope:
        yield ScopeAdapter(scope)


def initialize_container(services: Any = None, logger: Optional[logging.Logger] = None) -> Any:
    """
    Legacy compatibility function for initializing the container.
    
    This function is a drop-in replacement for the legacy initialize_container()
    function, initializing the UnoServiceProvider.
    
    Args:
        services: Optional services (ignored, for compatibility only)
        logger: Optional logger for diagnostic information
        
    Note:
        This is a synchronous initialization for compatibility.
        It's less powerful than the async version but works for simple cases.
    """
    logger = logger or logging.getLogger("uno.di.adapter")
    logger.info("Using synchronous container initialization for compatibility")
    
    # Create a minimal service collection
    from uno.dependencies.scoped_container import ServiceCollection
    collection = ServiceCollection()
    
    # Initialize the collection
    from uno.dependencies.scoped_container import initialize_container as init_modern
    return init_modern(collection, logger)


def reset_container() -> None:
    """
    Legacy compatibility function for resetting the container.
    
    This function is a drop-in replacement for the legacy reset_container()
    function, but does not actually reset the UnoServiceProvider.
    
    Note:
        This function does not actually reset the UnoServiceProvider,
        as that requires async shutdown. Instead, it logs a warning
        and suggests using the async shutdown approach.
    """
    logger = logging.getLogger("uno.di.adapter")
    logger.warning(
        "reset_container() is deprecated. "
        "Use 'await shutdown_services()' instead."
    )


class ScopeAdapter:
    """
    Adapter class for scopes.
    
    This class adapts the modern scope interface to the legacy scope interface,
    allowing code that expects the legacy interface to work with modern scopes.
    """
    
    def __init__(self, scope):
        """
        Initialize the scope adapter.
        
        Args:
            scope: The modern scope to adapt
        """
        self._scope = scope
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service from the scope.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            An instance of the requested service
        """
        return self._scope.resolve(service_type)
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service from the scope.
        
        Args:
            service_type: The type of service to resolve
            
        Returns:
            An instance of the requested service
        """
        return self._scope.resolve(service_type)


class ContainerAdapter:
    """
    Adapter class for the container.
    
    This class adapts the UnoServiceProvider interface to the legacy DIContainer
    interface, allowing code that expects the legacy interface to work with
    the modern UnoServiceProvider.
    """
    
    def __init__(self):
        """Initialize the container adapter."""
        self._provider = get_service_provider()
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service from the container.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            An instance of the requested service
        """
        return self._provider.get_service(service_type)
    
    def create_scope(self):
        """
        Create a new scope.
        
        Returns:
            The new scope
        """
        return ScopeAdapter(self._provider.create_scope())
    
    def register_singleton(self, service_type: Type[T], implementation: Type[T] | T | None = None) -> None:
        """
        Register a singleton service.
        
        Args:
            service_type: The type of service to register
            implementation: The implementation or instance to use
        """
        if implementation is None:
            # Self-registration (type)
            self._provider.register_type(service_type, service_type, ServiceLifecycle.SINGLETON)
        elif isinstance(implementation, type):
            # Type registration
            self._provider.register_type(service_type, implementation, ServiceLifecycle.SINGLETON)
        else:
            # Instance registration
            self._provider.register_instance(service_type, implementation)
    
    def register_scoped(self, service_type: Type[T], implementation: Type[T] | None = None) -> None:
        """
        Register a scoped service.
        
        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        if implementation is None:
            # Self-registration
            self._provider.register_type(service_type, service_type, ServiceLifecycle.SCOPED)
        else:
            # Implementation registration
            self._provider.register_type(service_type, implementation, ServiceLifecycle.SCOPED)
    
    def register_transient(self, service_type: Type[T], implementation: Type[T] | None = None) -> None:
        """
        Register a transient service.
        
        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        if implementation is None:
            # Self-registration
            self._provider.register_type(service_type, service_type, ServiceLifecycle.TRANSIENT)
        else:
            # Implementation registration
            self._provider.register_type(service_type, implementation, ServiceLifecycle.TRANSIENT)
    
    def register_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[..., T], 
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """
        Register a service with a factory function.
        
        Args:
            service_type: The type of service to register
            factory: Factory function to create instances
            lifetime: Service lifetime
        """
        # Map legacy lifetime to modern lifecycle
        lifecycle = None
        if lifetime == ServiceLifetime.SINGLETON:
            lifecycle = ServiceLifecycle.SINGLETON
        elif lifetime == ServiceLifetime.SCOPED:
            lifecycle = ServiceLifecycle.SCOPED
        elif lifetime == ServiceLifetime.TRANSIENT:
            lifecycle = ServiceLifecycle.TRANSIENT
        
        # Register with factory
        self._provider.register(service_type, lambda container: factory(), lifecycle)
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance.
        
        Args:
            service_type: The type of service to register
            instance: The instance to use
        """
        self._provider.register_instance(service_type, instance)


# Define ServiceRegistration class for compatibility
class ServiceRegistration:
    """Legacy compatibility for ServiceRegistration."""
    
    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
    ):
        """Legacy compatibility initialization."""
        self.service_type = service_type
        self.implementation_type = implementation_type or service_type
        self.lifetime = lifetime
        self.factory = factory
        self.instance = instance

# Map legacy lifetime enum to modern lifecycle constants
LIFETIME_MAP = {
    ServiceLifetime.SINGLETON: ServiceLifecycle.SINGLETON,
    ServiceLifetime.SCOPED: ServiceLifecycle.SCOPED,
    ServiceLifetime.TRANSIENT: ServiceLifecycle.TRANSIENT,
}