"""
FastAPI Integration

This module provides integration of the dependency injection system with FastAPI.
"""

import inspect
from typing import Type, Any, Callable, TypeVar, get_type_hints, Optional, Dict

from fastapi import Depends, Request, params
from starlette.concurrency import run_in_threadpool

from uno.core.di.protocols import ProviderProtocol, ScopeProtocol
from uno.core.di.provider import Provider

T = TypeVar("T")


class DependencyProvider:
    """
    Provides dependencies for FastAPI endpoints.
    
    This class manages the lifecycle of dependencies within FastAPI requests,
    ensuring proper scoping and disposal of resources.
    """
    
    def __init__(self, provider: Optional[ProviderProtocol] = None):
        """
        Initialize a new dependency provider.
        
        Args:
            provider: The service provider to use, or None to create a new one
        """
        self._provider = provider or Provider()
        self._configure_provider()
    
    def _configure_provider(self) -> None:
        """Configure the service provider."""
        self._provider.configure_services()
    
    def get_request_scope(self, request: Request) -> ScopeProtocol:
        """
        Get the dependency scope for a request.
        
        Args:
            request: The FastAPI request
            
        Returns:
            The dependency scope for the request
        """
        if not hasattr(request.state, "di_scope"):
            # Create a new scope for the request
            request.state.di_scope = self._provider.create_scope()
        
        return request.state.di_scope
    
    def depends(self, service_type: Type[T], **kwargs: Any) -> Callable[..., T]:
        """
        Create a FastAPI dependency for a service.
        
        Args:
            service_type: The type of service to inject
            **kwargs: Additional parameters for service creation
            
        Returns:
            A FastAPI dependency function
        """
        
        async def _get_dependency(request: Request = Depends()) -> T:
            scope = self.get_request_scope(request)
            return scope.get(service_type, **kwargs)
        
        return _get_dependency
    
    def inject(self, func: Callable) -> Callable:
        """
        Decorator to inject dependencies into a function.
        
        Args:
            func: The function to inject dependencies into
            
        Returns:
            A wrapper function that injects dependencies
        """
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Create a dependency for each parameter with a type hint
        dependencies = {}
        for name, param in signature.parameters.items():
            if name in type_hints:
                param_type = type_hints[name]
                dependencies[name] = self.depends(param_type)
        
        async def _wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a dictionary of dependencies
            for name, dependency in dependencies.items():
                if name not in kwargs:
                    kwargs[name] = await dependency()
            
            # Call the original function
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return await run_in_threadpool(func, *args, **kwargs)
        
        return _wrapper


# Global dependency provider instance
_dependency_provider: Optional[DependencyProvider] = None


def get_dependency_provider() -> DependencyProvider:
    """
    Get the global dependency provider instance.
    
    Returns:
        The global dependency provider
    """
    global _dependency_provider
    if _dependency_provider is None:
        _dependency_provider = DependencyProvider()
    
    return _dependency_provider


def set_dependency_provider(provider: DependencyProvider) -> None:
    """
    Set the global dependency provider instance.
    
    Args:
        provider: The dependency provider to use
    """
    global _dependency_provider
    _dependency_provider = provider


def Inject(service_type: Type[T], **kwargs: Any) -> Depends:
    """
    Create a FastAPI dependency for a service.
    
    Args:
        service_type: The type of service to inject
        **kwargs: Additional parameters for service creation
        
    Returns:
        A FastAPI Depends object
    """
    provider = get_dependency_provider()
    return Depends(provider.depends(service_type, **kwargs))


async def cleanup_request_scope(request: Request) -> None:
    """
    Clean up the request dependency scope.
    
    This function should be called when a request is complete to dispose of
    any scoped dependencies.
    
    Args:
        request: The FastAPI request
    """
    if hasattr(request.state, "di_scope"):
        scope = request.state.di_scope
        scope.dispose()
        delattr(request.state, "di_scope")