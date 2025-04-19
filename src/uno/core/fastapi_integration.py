"""
FastAPI integration for the Uno framework resource management.

This module provides utilities for integrating Uno's resource management
with FastAPI's lifecycle events.
"""

from typing import Callable, Optional, List, Dict, Any, TypeVar, AsyncIterator
import asyncio
import logging
import contextlib
from fastapi import FastAPI, APIRouter, Depends, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.asynchronous.task_manager import get_async_manager
from uno.core.resource_management import (
    get_resource_manager,
    initialize_resources,
)
from uno.core.resource_monitor import get_resource_monitor
from uno.database.pooled_session import pooled_async_session
from uno.core.protocols import DatabaseSessionProtocol


T = TypeVar("T")


class ResourceManagementMiddleware(BaseHTTPMiddleware):
    """
    Middleware for resource management.

    This middleware:
    - Cleans up resources after each request
    - Tracks request metrics
    - Adds resource health headers
    """

    def __init__(
        self,
        app: FastAPI,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the middleware.

        Args:
            app: FastAPI application
            logger: Optional logger instance
        """
        super().__init__(app)
        self.logger = logger or logging.getLogger(__name__)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """
        Process a request.

        Args:
            request: The HTTP request
            call_next: Function to call the next middleware/route handler

        Returns:
            HTTP response
        """
        # Process the request
        start_time = asyncio.get_event_loop().time()

        response = await call_next(request)

        # Calculate request duration
        duration = asyncio.get_event_loop().time() - start_time

        # Add resource health header if monitoring is enabled
        try:
            monitor = get_resource_monitor()
            health = await monitor.get_health_summary()

            # Add health headers
            response.headers["X-Resource-Health"] = health["overall_health"]
            response.headers["X-Resource-Count"] = str(health["resource_count"])
            response.headers["X-Request-Duration"] = f"{duration:.6f}s"

        except Exception as e:
            self.logger.warning(f"Error adding resource health headers: {str(e)}")

        return response


def setup_resource_management(app: FastAPI) -> None:
    """
    Set up resource management for a FastAPI application.

    This function:
    - Registers startup and shutdown event handlers
    - Adds the resource management middleware

    Args:
        app: FastAPI application
    """

    # Register startup event handler
    @app.on_event("startup")
    async def startup_resource_management() -> None:
        """Initialize resource management on application startup."""
        # Initialize resources
        await initialize_resources()

        # Start the async manager
        await get_async_manager().start()

    # Register shutdown event handler
    @app.on_event("shutdown")
    async def shutdown_resource_management() -> None:
        """Shut down resource management on application shutdown."""
        # Shut down the async manager
        await get_async_manager().shutdown()

    # Add resource management middleware
    app.add_middleware(ResourceManagementMiddleware)


def create_health_endpoint(app: FastAPI) -> None:
    """
    Create a health check endpoint for a FastAPI application.

    This function adds a /health endpoint that returns resource health information.

    Args:
        app: FastAPI application
    """

    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Check the health of the application.

        Returns:
            Health status of all resources
        """
        monitor = get_resource_monitor()
        return await monitor.get_health_summary()


@contextlib.asynccontextmanager
async def db_session_dependency() -> AsyncIterator[DatabaseSessionProtocol]:
    """
    FastAPI dependency for a database session.

    This function provides a database session as a FastAPI dependency,
    ensuring proper cleanup after the request.

    Yields:
        Database session
    """
    async with pooled_async_session() as session:
        yield session


def create_resource_monitoring_endpoints(
    app: FastAPI,
    prefix: str = "/management",
    tags: List[str] = ["Management"],
    dependencies: List[Any] = None,
) -> None:
    """
    Create resource monitoring endpoints.

    This function adds endpoints for monitoring application resources.

    Args:
        app: FastAPI application
        prefix: URL prefix for the endpoints
        tags: Tags for the endpoints
        dependencies: Additional dependencies for the endpoints
    """
    router = APIRouter(prefix=prefix, tags=tags, dependencies=dependencies or [])

    @router.get("/resources", summary="List all resources")
    async def list_resources(include_history: bool = False):
        """
        List all managed resources.

        Args:
            include_history: Whether to include historical metrics

        Returns:
            Resource metrics
        """
        monitor = get_resource_monitor()
        return await monitor.get_metrics(include_history=include_history)

    @router.get("/resources/{name}", summary="Get resource details")
    async def get_resource(name: str, include_history: bool = False):
        """
        Get details for a specific resource.

        Args:
            name: Name of the resource
            include_history: Whether to include historical metrics

        Returns:
            Resource metrics

        Raises:
            404: If resource not found
        """
        monitor = get_resource_monitor()
        metrics = await monitor.get_metrics(
            resource_name=name,
            include_history=include_history,
        )

        if name not in metrics["resources"]:
            return {"error": f"Resource '{name}' not found"}, 404

        return metrics["resources"][name]

    @router.get("/health", summary="Get health summary")
    async def get_health():
        """
        Get a summary of resource health.

        Returns:
            Health summary
        """
        monitor = get_resource_monitor()
        return await monitor.get_health_summary()

    # Register the router with the app
    app.include_router(router)
