"""
FastAPI integration for the unified endpoint framework.

This module provides utilities for integrating the unified endpoint framework
with FastAPI applications.
"""

from typing import Callable, Dict, List, Optional, Type, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from uno.core.di_fastapi import ScopedDeps
from uno.domain.entity.service import ServiceFactory
from uno.dependencies.fastapi_integration import RequestScopeMiddleware

from .middleware import ErrorHandlerMiddleware, setup_error_handlers

__all__ = [
    "setup_api",
    "create_api",
]


def setup_api(
    app: FastAPI,
    *,
    enable_cors: bool = True,
    cors_origins: Optional[List[str]] = None,
    enable_error_handling: bool = True,
    enable_scoped_dependencies: bool = True,
) -> None:
    """
    Set up a FastAPI application with the unified endpoint framework.
    
    This function adds middleware and configuration for integrating the
    unified endpoint framework with a FastAPI application.
    
    Args:
        app: The FastAPI application to set up.
        enable_cors: Whether to enable CORS middleware.
        cors_origins: List of allowed CORS origins.
        enable_error_handling: Whether to enable error handling middleware.
        enable_scoped_dependencies: Whether to enable scoped dependencies middleware.
    """
    # Add error handling
    if enable_error_handling:
        app.add_middleware(ErrorHandlerMiddleware)
        setup_error_handlers(app)
    
    # Add CORS
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add scoped dependencies
    if enable_scoped_dependencies:
        # Use the modern provider if available
        try:
            app.add_middleware(RequestScopeMiddleware)
        except ImportError:
            # Fall back to the traditional approach
            app.add_middleware(ScopedDeps)


def create_api(
    *,
    title: str = "UNO API",
    description: str = "API created with the UNO framework",
    version: str = "0.1.0",
    enable_cors: bool = True,
    cors_origins: Optional[List[str]] = None,
    enable_error_handling: bool = True,
    enable_scoped_dependencies: bool = True,
    openapi_url: str = "/openapi.json",
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
) -> FastAPI:
    """
    Create a new FastAPI application with the unified endpoint framework.
    
    This function creates a new FastAPI application and sets it up for use
    with the unified endpoint framework.
    
    Args:
        title: The title of the API.
        description: The description of the API.
        version: The version of the API.
        enable_cors: Whether to enable CORS middleware.
        cors_origins: List of allowed CORS origins.
        enable_error_handling: Whether to enable error handling middleware.
        enable_scoped_dependencies: Whether to enable scoped dependencies middleware.
        openapi_url: The URL for the OpenAPI JSON.
        docs_url: The URL for the Swagger UI.
        redoc_url: The URL for the ReDoc UI.
        
    Returns:
        A new FastAPI application ready to use with the unified endpoint framework.
    """
    # Create the FastAPI app
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        openapi_url=openapi_url,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )
    
    # Set up the app
    setup_api(
        app,
        enable_cors=enable_cors,
        cors_origins=cors_origins,
        enable_error_handling=enable_error_handling,
        enable_scoped_dependencies=enable_scoped_dependencies,
    )
    
    return app