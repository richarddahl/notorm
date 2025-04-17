"""
FastAPI integration for the modern dependency injection system.

This module provides utilities for integrating the UnoServiceProvider
with FastAPI applications.
"""

import logging
import inspect
from contextlib import asynccontextmanager
from typing import Dict, Type, Any, Callable, Optional, List, get_type_hints, cast, TypeVar, Generic

from fastapi import FastAPI, Depends, Request
from fastapi.routing import APIRouter
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
    get_service_provider,
)
from uno.dependencies.scoped_container import create_async_scope

T = TypeVar("T")


class RequestScopeMiddleware(BaseHTTPMiddleware):
    """
    Middleware that creates a request scope for each incoming request.
    
    This middleware creates a dependency injection scope for each incoming request,
    allowing scoped services to be created and disposed properly.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process an incoming request and create a DI scope.
        
        Args:
            request: The incoming request
            call_next: The next middleware or application handler
            
        Returns:
            The response from the application
        """
        provider = get_service_provider()
        
        # Create a scope for this request
        async with provider.create_scope(f"request_{id(request)}") as scope:
            # Store the scope in the request state
            request.state.di_scope = scope
            
            # Process the request
            response = await call_next(request)
            
            # Return the response
            return response


async def get_request_scope(request: Request):
    """
    Get the dependency injection scope for the current request.
    
    This function retrieves the scope created by the RequestScopeMiddleware
    for the current request.
    
    Args:
        request: The current request
        
    Returns:
        The dependency injection scope for the request
    """
    return request.state.di_scope


def resolve_service(service_type: Type[T]) -> Callable[[Request], T]:
    """
    Create a FastAPI dependency that resolves a service from the request scope.
    
    This function creates a FastAPI dependency that resolves a service from the
    request's dependency injection scope.
    
    Args:
        service_type: The type of service to resolve
        
    Returns:
        A dependency function that resolves the service
    """
    async def _resolve(request: Request) -> T:
        # Get the scope from the request
        if not hasattr(request.state, "di_scope"):
            raise RuntimeError(
                "RequestScopeMiddleware is not configured. "
                "Please add RequestScopeMiddleware to your application."
            )
        
        # Resolve the service from the scope
        scope = request.state.di_scope
        return scope.resolve(service_type)
    
    return _resolve


class DIAPIRouter(APIRouter):
    """
    API router with dependency injection support.
    
    This router extends FastAPI's APIRouter with automatic dependency injection
    for service types in endpoint function parameters.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the router."""
        super().__init__(*args, **kwargs)
    
    def add_api_route(
        self, path: str, endpoint: Callable, **kwargs
    ) -> None:
        """
        Add an API route with automatic dependency injection.
        
        Args:
            path: The URL path for the route
            endpoint: The endpoint function
            **kwargs: Additional arguments to pass to the router
        """
        # Get parameter type hints
        type_hints = get_type_hints(endpoint)
        
        # Create dependencies for service type parameters
        for name, param in inspect.signature(endpoint).parameters.items():
            # Skip parameters processed by FastAPI
            if name in {"request", "response", "background_tasks"}:
                continue
            
            # Get parameter type hint
            if name in type_hints:
                param_type = type_hints[name]
                
                # Check if the parameter type is registered with the service provider
                try:
                    # Only add dependency if this is a known service type
                    provider = get_service_provider()
                    if provider.has_service(param_type):
                        # Add a dependency for this parameter
                        kwargs.setdefault("dependencies", []).append(
                            Depends(resolve_service(param_type))
                        )
                except:
                    # If has_service raises an exception, skip this parameter
                    pass
        
        # Add the route to the router
        super().add_api_route(path, endpoint, **kwargs)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI applications.
    
    This context manager initializes the service provider when the application
    starts and shuts it down when the application stops.
    
    Args:
        app: The FastAPI application
    """
    # Initialize the service provider
    provider = get_service_provider()
    await provider.initialize()
    
    try:
        # Yield control to the application
        yield
    finally:
        # Shut down the service provider
        await provider.shutdown()


def configure_fastapi(app: FastAPI) -> None:
    """
    Configure a FastAPI application with dependency injection.
    
    This function configures a FastAPI application with the necessary middleware
    and lifespan events for using dependency injection.
    
    Args:
        app: The FastAPI application to configure
    """
    # Add the request scope middleware
    app.add_middleware(RequestScopeMiddleware)
    
    # Configure the lifespan
    app.router.lifespan_context = lifespan