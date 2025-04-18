"""
Provider Implementation

This module provides the service provider implementation for dependency injection.
The provider acts as a facade to the container and manages the lifecycle of the container.
"""

from typing import Dict, Type, Any, Optional, List, TypeVar

from uno.core.di.protocols import ProviderProtocol, ContainerProtocol, ScopeProtocol
from uno.core.di.container import Container

T = TypeVar("T")


class Provider(ProviderProtocol):
    """
    Service provider implementation.
    
    The provider manages the container and provides access to services.
    """
    
    def __init__(self, container: Optional[ContainerProtocol] = None):
        """
        Initialize a new provider.
        
        Args:
            container: The container to use, or None to create a new one
        """
        self._container = container or Container()
        self._configured = False
        self._root_scope: Optional[ScopeProtocol] = None
    
    def configure_services(self, container: Optional[ContainerProtocol] = None) -> None:
        """
        Configure services in the container.
        
        This method is designed to be overridden by subclasses to register
        services with the container.
        
        Args:
            container: The container to configure, or None to use the provider's container
        """
        # Default implementation does nothing
        self._configured = True
    
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
        if not self._configured:
            self.configure_services(self._container)
        
        if self._root_scope is None:
            self._root_scope = self._container.create_scope()
        
        return self._root_scope.get(service_type, **kwargs)
    
    def create_scope(self) -> ScopeProtocol:
        """
        Create a new dependency scope.
        
        Returns:
            A new scope instance
        """
        if not self._configured:
            self.configure_services(self._container)
        
        return self._container.create_scope()
    
    def dispose(self) -> None:
        """
        Dispose of the provider and all managed resources.
        """
        if self._root_scope is not None:
            self._root_scope.dispose()
            self._root_scope = None