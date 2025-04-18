"""
Dependency Injection Protocols

This module defines the core protocols for the dependency injection system.
"""

import enum
from typing import Protocol, TypeVar, Generic, Any, Optional, Type, Dict, Callable, List, runtime_checkable, Union

T = TypeVar("T")
TImpl = TypeVar("TImpl")


class ServiceLifetime(enum.Enum):
    """Service lifetime options for dependency injection."""
    
    SINGLETON = "singleton"
    """Service is created once and shared across all scopes."""
    
    SCOPED = "scoped"
    """Service is created once per scope (e.g., per request)."""
    
    TRANSIENT = "transient"
    """Service is created each time it is requested."""


@runtime_checkable
class FactoryProtocol(Protocol[T]):
    """Protocol for factory functions that create service instances."""
    
    def __call__(self, **kwargs: Any) -> T:
        """
        Create a service instance.
        
        Args:
            **kwargs: Additional parameters for service creation
            
        Returns:
            An instance of the service
        """
        ...


@runtime_checkable
class ScopeProtocol(Protocol):
    """Protocol for dependency injection scopes."""
    
    def get(self, service_type: Type[T], **kwargs: Any) -> T:
        """
        Get a service instance from the scope.
        
        Args:
            service_type: The type of service to get
            **kwargs: Additional parameters for service creation
            
        Returns:
            An instance of the requested service
            
        Raises:
            KeyError: If the service is not registered
        """
        ...
    
    def create_child_scope(self) -> "ScopeProtocol":
        """
        Create a new child scope that inherits from this scope.
        
        Returns:
            A new scope instance
        """
        ...
    
    def dispose(self) -> None:
        """
        Dispose of this scope and all managed resources.
        """
        ...


@runtime_checkable
class ContainerProtocol(Protocol):
    """Protocol for dependency injection containers."""
    
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
        ...
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance with the container.
        
        Args:
            service_type: The type of service to register
            instance: The instance to register
        """
        ...
    
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
        ...
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_type: The type of service to check
            
        Returns:
            True if the service is registered, False otherwise
        """
        ...
    
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
        ...
    
    def create_scope(self) -> ScopeProtocol:
        """
        Create a new dependency scope.
        
        Returns:
            A new scope instance
        """
        ...


@runtime_checkable
class ProviderProtocol(Protocol):
    """Protocol for service providers that manage DI configuration."""
    
    def configure_services(self, container: ContainerProtocol) -> None:
        """
        Configure services in the container.
        
        Args:
            container: The container to configure
        """
        ...
    
    def get_service(self, service_type: Type[T], **kwargs: Any) -> T:
        """
        Get a service instance.
        
        Args:
            service_type: The type of service to get
            **kwargs: Additional parameters for service creation
            
        Returns:
            An instance of the requested service
            
        Raises:
            KeyError: If the service is not registered
        """
        ...
    
    def create_scope(self) -> ScopeProtocol:
        """
        Create a new dependency scope.
        
        Returns:
            A new scope instance
        """
        ...
    
    def dispose(self) -> None:
        """
        Dispose of the provider and all managed resources.
        """
        ...