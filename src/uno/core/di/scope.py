"""
Scope Implementation

This module provides the scope implementation for the dependency injection system.
Scopes manage the lifetime of services within a specific context, such as a request.
"""

from typing import Dict, Type, Any, Optional, TypeVar

from uno.core.di.protocols import ScopeProtocol, ContainerProtocol

T = TypeVar("T")


class Scope(ScopeProtocol):
    """
    Dependency injection scope.
    
    A scope maintains a set of services with scoped lifetime and provides
    access to services from the parent container.
    """
    
    def __init__(self, container: ContainerProtocol, parent_scope: Optional["Scope"] = None):
        """
        Initialize a new scope.
        
        Args:
            container: The parent container
            parent_scope: The parent scope, if any
        """
        self._container = container
        self._parent_scope = parent_scope
        self._scoped_services: Dict[Type, Any] = {}
        self._disposed = False
    
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
            RuntimeError: If the scope has been disposed
        """
        self._check_not_disposed()
        
        # Try to get scoped instance
        if service_type in self._scoped_services:
            return self._scoped_services[service_type]
        
        # Resolve from container
        instance = self._container.resolve(service_type, **kwargs)
        
        # Store scoped instances
        from uno.core.di.container import ServiceRegistration, ServiceLifetime
        if (
            hasattr(self._container, "_registrations") and 
            service_type in self._container._registrations and
            self._container._registrations[service_type].lifetime == ServiceLifetime.SCOPED
        ):
            self._scoped_services[service_type] = instance
        
        return instance
    
    def create_child_scope(self) -> ScopeProtocol:
        """
        Create a new child scope that inherits from this scope.
        
        Returns:
            A new scope instance
            
        Raises:
            RuntimeError: If the scope has been disposed
        """
        self._check_not_disposed()
        return Scope(self._container, self)
    
    def dispose(self) -> None:
        """
        Dispose of this scope and all managed resources.
        """
        if self._disposed:
            return
        
        # Dispose of any disposable services
        for service in self._scoped_services.values():
            if hasattr(service, "dispose") and callable(service.dispose):
                service.dispose()
        
        self._scoped_services.clear()
        self._disposed = True
    
    def _check_not_disposed(self) -> None:
        """
        Check that the scope has not been disposed.
        
        Raises:
            RuntimeError: If the scope has been disposed
        """
        if self._disposed:
            raise RuntimeError("Scope has been disposed")
    
    def __enter__(self) -> "Scope":
        """Enter the scope context."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the scope context and dispose of the scope."""
        self.dispose()