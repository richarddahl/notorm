"""
FastAPI integration for Uno framework.

This module provides utilities for integrating the Uno dependency injection
system with FastAPI, including middleware for request scopes, dependency
providers, and lifecycle management.
"""

import inspect
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Type, TypeVar, Optional, Union, List, Callable, cast, get_type_hints

from fastapi import FastAPI, Request, Response, Depends, APIRouter
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from uno.dependencies.modern_provider import (
    UnoServiceProvider, 
    get_service_provider,
    initialize_services,
    shutdown_services
)
from uno.dependencies.scoped_container import ServiceResolver, create_async_scope


T = TypeVar('T')


class RequestScopeMiddleware(BaseHTTPMiddleware):
    """
    Middleware for creating request scopes.
    
    This middleware creates a new scope for each request, allowing scoped
    services to be resolved with request lifetime.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self._logger = logging.getLogger("uno.fastapi")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch the request.
        
        This method creates a new scope for the request, makes it available
        in the request state, and cleans it up when the request is done.
        
        Args:
            request: The request
            call_next: The next middleware or endpoint
            
        Returns:
            The response
        """
        provider = get_service_provider()
        
        # Create a unique scope ID for this request
        scope_id = f"request_{id(request)}"
        
        # Create a scope for this request
        async with provider.create_scope(scope_id) as scope:
            # Store the scope in the request state
            request.state.di_scope = scope
            
            # Process the request
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                self._logger.error(f"Error processing request: {e}")
                raise
            finally:
                # Cleanup the scope reference
                if hasattr(request.state, "di_scope"):
                    delattr(request.state, "di_scope")
        
        # The scope is automatically disposed when we exit the context manager


def get_request_scope(request: Request) -> ServiceResolver:
    """
    Get the request scope.
    
    This function is a FastAPI dependency that provides access to the
    request's DI scope.
    
    Args:
        request: The request
        
    Returns:
        The request's DI scope
    """
    if not hasattr(request.state, "di_scope"):
        raise RuntimeError("No DI scope found in request state")
    return request.state.di_scope


def resolve_service(service_type: Type[T]) -> Callable[[Request], T]:
    """
    Create a FastAPI dependency for resolving a service.
    
    This function creates a FastAPI dependency that resolves a service
    from the request's DI scope.
    
    Args:
        service_type: The type of service to resolve
        
    Returns:
        A FastAPI dependency that resolves the service
    """
    def dependency(request: Request) -> T:
        scope = get_request_scope(request)
        return scope.resolve(service_type)
    
    # Set a meaningful name for the dependency
    dependency.__name__ = f"resolve_{service_type.__name__}"
    
    return dependency


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler for service initialization and shutdown.
    
    This context manager initializes the Uno services when the application
    starts and shuts them down when the application stops.
    
    Args:
        app: The FastAPI application
        
    Yields:
        The FastAPI application
    """
    # Initialize services
    await initialize_services()
    
    yield
    
    # Shut down services
    await shutdown_services()


def configure_fastapi(app: FastAPI) -> None:
    """
    Configure FastAPI with Uno dependency injection.
    
    This function adds the request scope middleware and integrates the
    Uno dependency injection system with FastAPI.
    
    Args:
        app: The FastAPI application
    """
    # Add the request scope middleware
    app.add_middleware(RequestScopeMiddleware)
    
    # Set up lifespan management
    app.router.lifespan_context = lifespan


class DIAPIRouter(APIRouter):
    """
    API router with automatic dependency injection.
    
    This router extends FastAPI's APIRouter to automatically inject
    dependencies into endpoint handlers based on their parameter types.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the router."""
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger("uno.fastapi")
    
    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *args,
        **kwargs
    ) -> None:
        """
        Add an API route with automatic dependency injection.
        
        This method automatically injects dependencies into the endpoint
        based on its parameter types.
        
        Args:
            path: The URL path
            endpoint: The endpoint handler
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        # Get parameter type hints
        sig = inspect.signature(endpoint)
        type_hints = get_type_hints(endpoint)
        
        # Skip if no type hints or all parameters already have dependencies
        if not type_hints or all(
            param.default is not param.empty for param in sig.parameters.values()
        ):
            return super().add_api_route(path, endpoint, *args, **kwargs)
        
        # Get existing dependencies
        dependencies = kwargs.get("dependencies", [])
        
        # Add dependencies for typed parameters
        for name, param in sig.parameters.items():
            # Skip parameters with default values or without type hints
            if param.default is not param.empty or name not in type_hints:
                continue
            
            # Skip parameters that are handled by FastAPI
            if name in {"request", "response", "background_tasks"}:
                continue
            
            # Get the parameter type
            param_type = type_hints[name]
            
            # Create a dependency for this parameter
            try:
                # Add dependency to inject the parameter
                dependencies.append(Depends(resolve_service(param_type)))
                self._logger.debug(f"Added dependency for {name}: {param_type.__name__}")
            except Exception as e:
                self._logger.warning(f"Error adding dependency for {name}: {e}")
        
        # Update dependencies
        kwargs["dependencies"] = dependencies
        
        # Add the route with dependencies
        super().add_api_route(path, endpoint, *args, **kwargs)


def create_router(*args, **kwargs) -> DIAPIRouter:
    """
    Create a DIAPIRouter.
    
    This function is a convenience function for creating a DIAPIRouter.
    
    Args:
        *args: Arguments to pass to DIAPIRouter constructor
        **kwargs: Keyword arguments to pass to DIAPIRouter constructor
        
    Returns:
        A DIAPIRouter instance
    """
    return DIAPIRouter(*args, **kwargs)