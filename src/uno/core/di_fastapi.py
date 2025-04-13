"""
FastAPI integration for Uno's dependency injection system.

This module provides utilities for integrating the Uno DI container with FastAPI's
dependency injection system, allowing seamless use of Uno services in FastAPI applications.
"""

from typing import TypeVar, Type, Any, Callable, Optional, Generic, cast, Union, Awaitable
from fastapi import Depends, Request
import inspect
import contextvars

from . import di
from .protocols import ServiceScope

T = TypeVar("T")

# Current scope context variable
current_scope = contextvars.ContextVar[Optional[ServiceScope]]("di_current_scope", default=None)


class FromDI(Generic[T]):
    """
    Dependency provider for FastAPI that resolves dependencies from the Uno DI container.
    
    This class creates a callable that resolves a service from the DI container
    and can be used with FastAPI's Depends.
    
    Example:
        ```python
        @app.get("/users")
        async def get_users(
            service: UserService = Depends(FromDI(UserService))
        ):
            return await service.get_all_users()
        ```
    """
    
    def __init__(self, service_type: Type[T]):
        """
        Initialize a DI dependency.
        
        Args:
            service_type: The type of service to resolve
        """
        self.service_type = service_type
    
    def __call__(self) -> T:
        """
        Resolve the service from the DI container.
        
        Returns:
            The resolved service
        """
        # Get the active scope if one exists
        scope = current_scope.get()
        
        if scope is not None:
            # Use the active scope
            return scope.get_service(self.service_type)
        else:
            # Use the global container
            return di.get_service(self.service_type)


class ScopedDeps:
    """
    Context manager for creating a DI scope for FastAPI request handlers.
    
    This class creates a scope that lasts for the duration of a request handler
    and makes it available to FromDI dependencies.
    
    Example:
        ```python
        @app.get("/users")
        async def get_users(
            scoped_deps: ScopedDeps = Depends(ScopedDeps),
            service: UserService = Depends(FromDI(UserService))
        ):
            with scoped_deps:
                return await service.get_all_users()
        ```
    """
    
    def __init__(self, request: Request):
        """
        Initialize a scoped dependencies manager.
        
        Args:
            request: The FastAPI request
        """
        self.request = request
        self._scope: Optional[ServiceScope] = None
        self._token: Optional[contextvars.Token] = None
    
    def __enter__(self) -> "ScopedDeps":
        """
        Enter the scope context.
        
        Returns:
            Self for method chaining
        """
        # Create a scope with a unique ID from the request
        scope_id = f"request_{id(self.request)}"
        self._scope = di.get_container().create_scope()
        self._token = current_scope.set(self._scope)
        return self
    
    def __exit__(self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Exit the scope context."""
        if self._token is not None:
            # Restore previous scope
            current_scope.reset(self._token)
        
        if self._scope is not None:
            # Dispose the scope
            self._scope.dispose()
            self._scope = None


async def create_request_scope(request: Request):
    """
    FastAPI dependency that creates a request-scoped DI scope.
    
    This function can be used as a FastAPI dependency to create a scope that
    lasts for the duration of a request.
    
    Example:
        ```python
        @app.get("/users")
        async def get_users(
            scope: ServiceScope = Depends(create_request_scope),
            user_service: UserService = Depends(get_service(UserService))
        ):
            return await user_service.get_all_users()
        ```
    
    Args:
        request: The FastAPI request
        
    Returns:
        A service scope for the request
    """
    # Create a scope with a unique ID from the request
    scope_id = f"request_{id(request)}"
    
    # Create the scope
    scope = di.get_container().create_scope()
    
    # Store in request state for disposal
    request.state.di_scope = scope
    
    # Set as current scope
    token = current_scope.set(scope)
    
    # Store token in request state
    request.state.di_scope_token = token
    
    return scope


def get_service(service_type: Type[T]) -> Callable[[], T]:
    """
    Create a FastAPI dependency that resolves a service from the DI container.
    
    This function creates a dependency that resolves a service from the current
    scope if one exists, or directly from the container otherwise.
    
    Example:
        ```python
        @app.get("/users")
        async def get_users(
            user_service: UserService = Depends(get_service(UserService))
        ):
            return await user_service.get_all_users()
        ```
    
    Args:
        service_type: The type of service to resolve
        
    Returns:
        A dependency function that resolves the service
    """
    def dependency() -> T:
        # Get the active scope if one exists
        scope = current_scope.get()
        
        if scope is not None:
            # Use the active scope
            return scope.get_service(service_type)
        else:
            # Use the global container
            return di.get_service(service_type)
    
    return dependency


# =============================================================================
# FastAPI Application Extensions
# =============================================================================

def configure_di_middleware(app):
    """
    Configure FastAPI middleware for DI scope management.
    
    This function adds middleware to automatically create and dispose
    DI scopes for each request.
    
    Args:
        app: The FastAPI application
    """
    @app.middleware("http")
    async def di_scope_middleware(request: Request, call_next):
        """
        Middleware that creates a DI scope for each request.
        
        Args:
            request: The FastAPI request
            call_next: Function to call the next middleware or endpoint
            
        Returns:
            The response from the next middleware or endpoint
        """
        # Create a scope with a unique ID from the request
        scope_id = f"request_{id(request)}"
        
        async with di.create_async_scope(scope_id) as scope:
            # Set as current scope
            token = current_scope.set(scope)
            try:
                # Call the next middleware or endpoint
                response = await call_next(request)
                return response
            finally:
                # Restore previous scope
                current_scope.reset(token)


def register_app_shutdown(app):
    """
    Register FastAPI shutdown event handler for DI container shutdown.
    
    This function registers a shutdown event handler that shuts down
    the DI container when the FastAPI application stops.
    
    Args:
        app: The FastAPI application
    """
    @app.on_event("shutdown")
    async def shutdown_di_container():
        """Shut down the DI container when the application stops."""
        container = di.get_container()
        
        # Dispose all disposable services
        for service_type, instance in container._registry._singleton_instances.items():
            if isinstance(instance, di.AsyncDisposable):
                try:
                    await instance.dispose_async()
                except Exception as e:
                    container._logger.error(f"Error disposing service {service_type.__name__}: {str(e)}")
            elif isinstance(instance, di.Disposable):
                try:
                    instance.dispose()
                except Exception as e:
                    container._logger.error(f"Error disposing service {service_type.__name__}: {str(e)}")