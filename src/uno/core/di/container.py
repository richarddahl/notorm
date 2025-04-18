"""
Container Implementation

This module provides the core container implementation for the dependency injection system.
"""

import inspect
from typing import Dict, Type, Any, Optional, Callable, List, Union, TypeVar, get_type_hints, get_origin, get_args

from uno.core.di.protocols import ContainerProtocol, ScopeProtocol, ServiceLifetime, FactoryProtocol
from uno.core.di.scope import Scope

T = TypeVar("T")
TImpl = TypeVar("TImpl")


class ServiceRegistration:
    """
    Information about a registered service.
    """
    
    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Union[Type, Callable]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        instance: Any = None,
        factory_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a service registration.
        
        Args:
            service_type: The service type
            implementation: The implementation type or factory function
            lifetime: The service lifetime
            instance: An existing instance (for singleton services)
            factory_kwargs: Additional parameters for the factory function
        """
        self.service_type = service_type
        self.implementation = implementation if implementation is not None else service_type
        self.lifetime = lifetime
        self.instance = instance
        self.factory_kwargs = factory_kwargs or {}


class Container(ContainerProtocol):
    """
    Main container implementation for dependency injection.
    
    The container manages service registrations and creates instances based on
    registered service definitions.
    """
    
    def __init__(self):
        """Initialize a new container."""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Union[Type[TImpl], FactoryProtocol[T]]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        **factory_kwargs: Any
    ) -> None:
        """
        Register a service with the container.
        
        Args:
            service_type: The type of service to register (usually a Protocol)
            implementation_type: The implementation type or factory function
            lifetime: The service lifetime
            **factory_kwargs: Additional parameters for the factory function
        """
        self._registrations[service_type] = ServiceRegistration(
            service_type=service_type,
            implementation=implementation_type,
            lifetime=lifetime,
            factory_kwargs=factory_kwargs,
        )
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance with the container.
        
        Args:
            service_type: The type of service to register
            instance: The instance to register
        """
        self._registrations[service_type] = ServiceRegistration(
            service_type=service_type,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
        )
        self._singletons[service_type] = instance
    
    def register_factory(
        self, 
        service_type: Type[T], 
        factory: FactoryProtocol[T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> None:
        """
        Register a factory function with the container.
        
        Args:
            service_type: The type of service to register
            factory: The factory function
            lifetime: The service lifetime
        """
        self._registrations[service_type] = ServiceRegistration(
            service_type=service_type,
            implementation=factory,
            lifetime=lifetime,
        )
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_type: The type of service to check
            
        Returns:
            True if the service is registered, False otherwise
        """
        return service_type in self._registrations
    
    def resolve(self, service_type: Type[T], **kwargs: Any) -> T:
        """
        Resolve a service from the container.
        
        Args:
            service_type: The type of service to resolve
            **kwargs: Additional parameters for service creation
            
        Returns:
            An instance of the requested service
            
        Raises:
            KeyError: If the service is not registered
        """
        if not self.is_registered(service_type):
            raise KeyError(f"Service {service_type.__name__} is not registered")
        
        registration = self._registrations[service_type]
        
        # Handle already-created singletons
        if registration.lifetime == ServiceLifetime.SINGLETON and service_type in self._singletons:
            return self._singletons[service_type]
        
        # Create the instance
        instance = self._create_instance(registration, **kwargs)
        
        # Store singleton instances
        if registration.lifetime == ServiceLifetime.SINGLETON:
            self._singletons[service_type] = instance
        
        return instance
    
    def create_scope(self) -> ScopeProtocol:
        """
        Create a new dependency scope.
        
        Returns:
            A new scope instance
        """
        return Scope(self)
    
    def _create_instance(self, registration: ServiceRegistration, **kwargs: Any) -> Any:
        """
        Create an instance of a service.
        
        Args:
            registration: The service registration
            **kwargs: Additional parameters for service creation
            
        Returns:
            The created instance
        """
        if registration.instance is not None:
            return registration.instance
        
        # Combine factory kwargs from registration with passed kwargs
        all_kwargs = {**registration.factory_kwargs, **kwargs}
        
        # Handle factory functions
        if callable(registration.implementation) and not isinstance(registration.implementation, type):
            return registration.implementation(**all_kwargs)
        
        # Handle constructor injection
        constructor_params = self._get_constructor_params(registration.implementation, all_kwargs)
        
        return registration.implementation(**constructor_params)
    
    def _get_constructor_params(self, implementation: Type, explicit_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get parameters for a constructor, resolving dependencies.
        
        Args:
            implementation: The implementation type
            explicit_params: Explicitly provided parameters
            
        Returns:
            A dictionary of parameter values
        """
        params = {}
        
        # Get constructor parameter types
        try:
            signature = inspect.signature(implementation.__init__)
            type_hints = get_type_hints(implementation.__init__)
        except (ValueError, TypeError, AttributeError):
            # No constructor, use empty params
            return explicit_params
        
        # Skip self parameter
        parameters = list(signature.parameters.items())
        if parameters and parameters[0][0] == 'self':
            parameters = parameters[1:]
        
        # Resolve each parameter
        for name, param in parameters:
            # Use explicitly provided parameter if available
            if name in explicit_params:
                params[name] = explicit_params[name]
                continue
            
            # Get parameter type
            param_type = type_hints.get(name, None)
            if param_type is None:
                # No type hint, use default if available
                if param.default is not inspect.Parameter.empty:
                    params[name] = param.default
                continue
            
            # Handle Optional[Type]
            if get_origin(param_type) is Union:
                args = get_args(param_type)
                if type(None) in args:  # This is Optional[T]
                    non_none_args = [arg for arg in args if arg is not type(None)]
                    if len(non_none_args) == 1:
                        param_type = non_none_args[0]
            
            # Try to resolve the type from the container
            try:
                params[name] = self.resolve(param_type)
            except KeyError:
                # If the parameter has a default value, use it
                if param.default is not inspect.Parameter.empty:
                    params[name] = param.default
        
        return params