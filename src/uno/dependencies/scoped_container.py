"""
Scoped dependency injection container for Uno framework.

This module implements a hierarchical dependency injection container that supports
different scopes for services, such as singleton (application), request, and transient.
"""

import inspect
import logging
from enum import Enum, auto
from typing import Dict, Type, TypeVar, Any, Optional, Union, Callable, Generic, cast, List, Set
from contextlib import contextmanager, asynccontextmanager

T = TypeVar('T')
ProviderT = TypeVar('ProviderT')


class ServiceScope(Enum):
    """Service lifetime scopes for dependency injection."""
    SINGLETON = auto()  # One instance per container
    SCOPED = auto()     # One instance per scope (e.g., request)
    TRANSIENT = auto()  # New instance each time


class ServiceRegistration(Generic[T]):
    """
    Service registration information.
    
    Holds the configuration for how a service should be resolved, including
    its implementation type or factory, scope, and initialization parameters.
    """
    
    def __init__(
        self,
        implementation: Union[Type[T], Callable[..., T]],
        scope: ServiceScope = ServiceScope.SINGLETON,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize service registration.
        
        Args:
            implementation: Type or factory function for the service
            scope: Service lifetime scope
            params: Optional parameters to pass to the constructor/factory
        """
        self.implementation = implementation
        self.scope = scope
        self.params = params or {}


class ServiceResolver:
    """
    Service resolver for dependency injection.
    
    This class is responsible for resolving services based on their registrations,
    including handling dependencies and maintaining instance caches for different scopes.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the service resolver.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self._logger = logger or logging.getLogger("uno.di")
        
    def register(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T]],
        scope: ServiceScope = ServiceScope.SINGLETON,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a service with the container.
        
        Args:
            service_type: The type or protocol to register
            implementation: The implementation type or factory function
            scope: The service lifetime scope
            params: Optional parameters to pass to the constructor/factory
        """
        registration = ServiceRegistration(implementation, scope, params)
        self._registrations[service_type] = registration
        self._logger.debug(f"Registered {service_type.__name__} with scope {scope.name}")
        
        # Clear singleton cache for this type if it exists
        if service_type in self._singletons:
            del self._singletons[service_type]
            self._logger.debug(f"Cleared singleton cache for {service_type.__name__}")
        
        # Clear scoped caches for this type
        for scope_id, instances in self._scoped_instances.items():
            if service_type in instances:
                del instances[service_type]
                self._logger.debug(f"Cleared scoped cache for {service_type.__name__} in scope {scope_id}")
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance as a singleton.
        
        Args:
            service_type: The type or protocol to register
            instance: The instance to register
        """
        self._singletons[service_type] = instance
        self._logger.debug(f"Registered instance of {service_type.__name__}")
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.
        
        This method returns an instance of the requested service type, creating it
        if necessary according to its registered scope.
        
        Args:
            service_type: The type of service to resolve
            
        Returns:
            An instance of the requested service
            
        Raises:
            KeyError: If the service type is not registered
            ValueError: If a scoped service is requested outside a scope
        """
        # Check if there's a registration for this type
        if service_type not in self._registrations:
            self._logger.error(f"No registration found for {service_type.__name__}")
            raise KeyError(f"No registration found for {service_type.__name__}")
        
        registration = self._registrations[service_type]
        
        # Handle singletons
        if registration.scope == ServiceScope.SINGLETON:
            if service_type not in self._singletons:
                self._singletons[service_type] = self._create_instance(registration)
            return cast(T, self._singletons[service_type])
        
        # Handle scoped services
        if registration.scope == ServiceScope.SCOPED:
            if not self._current_scope:
                self._logger.error(f"Attempted to resolve scoped service {service_type.__name__} outside a scope")
                raise ValueError(f"Scoped service {service_type.__name__} cannot be resolved outside a scope")
            
            if self._current_scope not in self._scoped_instances:
                self._scoped_instances[self._current_scope] = {}
                
            scope_cache = self._scoped_instances[self._current_scope]
            if service_type not in scope_cache:
                scope_cache[service_type] = self._create_instance(registration)
            
            return cast(T, scope_cache[service_type])
        
        # Handle transient services
        return cast(T, self._create_instance(registration))
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """
        Create a service instance from a registration.
        
        Args:
            registration: The service registration
            
        Returns:
            The created service instance
        """
        impl = registration.implementation
        params = registration.params.copy()
        
        # If it's a callable but not a class, just call it with params
        if callable(impl) and not inspect.isclass(impl):
            return impl(**params)
        
        # Otherwise it's a class, so we need to inspect its constructor
        sig = inspect.signature(impl.__init__)  # type: ignore
        
        # Get constructor params, excluding self
        for param_name, param in list(sig.parameters.items())[1:]:
            # Skip if we already have this param
            if param_name in params:
                continue
                
            # Skip if it has a default value
            if param.default is not param.empty:
                continue
                
            # Skip *args and **kwargs
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
                
            # Try to resolve this parameter as a dependency
            param_type = param.annotation
            if param_type is not param.empty and param_type is not Any:
                try:
                    params[param_name] = self.resolve(param_type)
                except (KeyError, ValueError):
                    # If we can't resolve it, let the constructor fail
                    pass
        
        # Create the instance
        return impl(**params)  # type: ignore
    
    @contextmanager
    def create_scope(self, scope_id: Optional[str] = None) -> 'ServiceResolver':
        """
        Create a service scope.
        
        This context manager creates a new scope for resolving scoped services,
        ensuring they are properly disposed when the scope ends.
        
        Args:
            scope_id: Optional scope identifier, defaults to a generated ID
            
        Yields:
            The service resolver with the active scope
        """
        prev_scope = self._current_scope
        scope_id = scope_id or f"scope_{id(object())}"
        
        try:
            self._current_scope = scope_id
            self._logger.debug(f"Created scope {scope_id}")
            yield self
        finally:
            # Clean up disposable services in this scope
            if scope_id in self._scoped_instances:
                instances = self._scoped_instances[scope_id]
                # Dispose any resources that need disposing
                for instance in instances.values():
                    if hasattr(instance, 'dispose') and callable(instance.dispose):
                        try:
                            instance.dispose()
                        except Exception as e:
                            self._logger.warning(f"Error disposing service: {e}")
                
                # Remove the scope
                del self._scoped_instances[scope_id]
                self._logger.debug(f"Removed scope {scope_id}")
            
            # Restore previous scope
            self._current_scope = prev_scope
    
    @asynccontextmanager
    async def create_async_scope(self, scope_id: Optional[str] = None) -> 'ServiceResolver':
        """
        Create an async service scope.
        
        This async context manager creates a new scope for resolving scoped services,
        ensuring they are properly disposed when the scope ends.
        
        Args:
            scope_id: Optional scope identifier, defaults to a generated ID
            
        Yields:
            The service resolver with the active scope
        """
        prev_scope = self._current_scope
        scope_id = scope_id or f"async_scope_{id(object())}"
        
        try:
            self._current_scope = scope_id
            self._logger.debug(f"Created async scope {scope_id}")
            yield self
        finally:
            # Clean up disposable services in this scope
            if scope_id in self._scoped_instances:
                instances = self._scoped_instances[scope_id]
                # Dispose any resources that need disposing
                for instance in instances.values():
                    if hasattr(instance, 'dispose_async') and callable(instance.dispose_async):
                        try:
                            await instance.dispose_async()
                        except Exception as e:
                            self._logger.warning(f"Error disposing async service: {e}")
                    elif hasattr(instance, 'dispose') and callable(instance.dispose):
                        try:
                            instance.dispose()
                        except Exception as e:
                            self._logger.warning(f"Error disposing service: {e}")
                
                # Remove the scope
                del self._scoped_instances[scope_id]
                self._logger.debug(f"Removed async scope {scope_id}")
            
            # Restore previous scope
            self._current_scope = prev_scope


class ServiceCollection:
    """
    Collection for configuring service registrations.
    
    This class provides a fluent interface for registering services,
    making it easier to configure the dependency injection container.
    """
    
    def __init__(self):
        """Initialize the service collection."""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
    
    def add_singleton(
        self, 
        service_type: Type[T], 
        implementation: Optional[Union[Type[T], Callable[..., T]]] = None,
        **params: Any
    ) -> 'ServiceCollection':
        """
        Register a singleton service.
        
        Args:
            service_type: The type or protocol to register
            implementation: The implementation type or factory function, defaults to service_type
            **params: Parameters to pass to the constructor/factory
            
        Returns:
            The service collection for method chaining
        """
        impl = implementation or service_type
        self._registrations[service_type] = ServiceRegistration(
            impl, ServiceScope.SINGLETON, params
        )
        return self
    
    def add_instance(self, service_type: Type[T], instance: T) -> 'ServiceCollection':
        """
        Register an existing instance as a singleton.
        
        Args:
            service_type: The type or protocol to register
            instance: The instance to register
            
        Returns:
            The service collection for method chaining
        """
        self._instances[service_type] = instance
        return self
    
    def add_scoped(
        self, 
        service_type: Type[T], 
        implementation: Optional[Union[Type[T], Callable[..., T]]] = None,
        **params: Any
    ) -> 'ServiceCollection':
        """
        Register a scoped service.
        
        Args:
            service_type: The type or protocol to register
            implementation: The implementation type or factory function, defaults to service_type
            **params: Parameters to pass to the constructor/factory
            
        Returns:
            The service collection for method chaining
        """
        impl = implementation or service_type
        self._registrations[service_type] = ServiceRegistration(
            impl, ServiceScope.SCOPED, params
        )
        return self
    
    def add_transient(
        self, 
        service_type: Type[T], 
        implementation: Optional[Union[Type[T], Callable[..., T]]] = None,
        **params: Any
    ) -> 'ServiceCollection':
        """
        Register a transient service.
        
        Args:
            service_type: The type or protocol to register
            implementation: The implementation type or factory function, defaults to service_type
            **params: Parameters to pass to the constructor/factory
            
        Returns:
            The service collection for method chaining
        """
        impl = implementation or service_type
        self._registrations[service_type] = ServiceRegistration(
            impl, ServiceScope.TRANSIENT, params
        )
        return self
    
    def build(self, logger: Optional[logging.Logger] = None) -> ServiceResolver:
        """
        Build a service resolver from the collection.
        
        Args:
            logger: Optional logger for diagnostic information
            
        Returns:
            A configured service resolver
        """
        resolver = ServiceResolver(logger)
        
        # Register all services
        for service_type, registration in self._registrations.items():
            resolver.register(
                service_type,
                registration.implementation,
                registration.scope,
                registration.params
            )
        
        # Register all instances
        for service_type, instance in self._instances.items():
            resolver.register_instance(service_type, instance)
        
        return resolver


# Global container for dependency injection
_container: Optional[ServiceResolver] = None


def get_container() -> ServiceResolver:
    """
    Get the global container instance.
    
    Returns:
        The service resolver
        
    Raises:
        RuntimeError: If the container has not been initialized
    """
    global _container
    if _container is None:
        raise RuntimeError("Container has not been initialized. Call initialize_container first")
    return _container


def initialize_container(services: Optional[ServiceCollection] = None, logger: Optional[logging.Logger] = None) -> ServiceResolver:
    """
    Initialize the global container.
    
    Args:
        services: Optional service collection to build the container from
        logger: Optional logger for diagnostic information
        
    Returns:
        The initialized service resolver
    """
    global _container
    
    if services:
        _container = services.build(logger)
    else:
        _container = ServiceResolver(logger)
    
    return _container


def get_service(service_type: Type[T]) -> T:
    """
    Get a service from the global container.
    
    Args:
        service_type: The type of service to resolve
        
    Returns:
        An instance of the requested service
    """
    return get_container().resolve(service_type)


@contextmanager
def create_scope(scope_id: Optional[str] = None) -> ServiceResolver:
    """
    Create a service scope.
    
    This context manager creates a new scope for resolving scoped services,
    ensuring they are properly disposed when the scope ends.
    
    Args:
        scope_id: Optional scope identifier, defaults to a generated ID
        
    Yields:
        The service resolver with the active scope
    """
    with get_container().create_scope(scope_id) as scope:
        yield scope


@asynccontextmanager
async def create_async_scope(scope_id: Optional[str] = None) -> ServiceResolver:
    """
    Create an async service scope.
    
    This async context manager creates a new scope for resolving scoped services,
    ensuring they are properly disposed when the scope ends.
    
    Args:
        scope_id: Optional scope identifier, defaults to a generated ID
        
    Yields:
        The service resolver with the active scope
    """
    async with get_container().create_async_scope(scope_id) as scope:
        yield scope


async def get_scoped_service(service_type: Type[T]) -> T:
    """
    Get a scoped service from the container.
    
    This function creates a temporary scope and resolves the service within it.
    The scope is then closed, so any scoped dependencies will be disposed.
    
    Args:
        service_type: The type of service to resolve
        
    Returns:
        An instance of the requested service
    """
    async with create_async_scope(f"temp_scope_{id(object())}") as scope:
        return scope.resolve(service_type)