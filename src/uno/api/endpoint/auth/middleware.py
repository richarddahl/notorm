"""
Authentication middleware for the unified endpoint framework.

This module provides middleware for authenticating requests in the unified endpoint framework.
"""

import logging
from typing import Callable, List, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import AuthenticationError
from .models import UserContext
from .protocols import AuthenticationBackend

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authenticating requests."""

    def __init__(
        self,
        app: FastAPI,
        auth_backend: AuthenticationBackend,
        exclude_paths: list[str] | None = None,
    ):
        """
        Initialize the authentication middleware.

        Args:
            app: The FastAPI application
            auth_backend: The authentication backend to use
            exclude_paths: Optional list of paths to exclude from authentication
        """
        super().__init__(app)
        self.auth_backend = auth_backend
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and authenticate the user.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            The response, either from the next handler or an error response
        """
        # Check if the path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        try:
            # Authenticate the request
            user = await self.auth_backend.authenticate(request)

            # Create a user context
            user_context = UserContext(user)

            # Set the user context in the request state
            request.state.user_context = user_context

            # Continue to the next middleware or endpoint handler
            return await call_next(request)

        except AuthenticationError as e:
            # Let the auth backend handle the error
            return await self.auth_backend.on_error(request, e)

        except Exception as e:
            # Log unexpected errors
            logger.exception(f"Unexpected error during authentication: {str(e)}")

            # Return a generic error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred during authentication",
                    }
                },
            )


def setup_auth(
    app: FastAPI,
    auth_backend: AuthenticationBackend,
    exclude_paths: list[str] | None = None,
) -> None:
    """
    Set up authentication for a FastAPI application.

    Args:
        app: The FastAPI application to set up
        auth_backend: The authentication backend to use
        exclude_paths: Optional list of paths to exclude from authentication
    """
    # Add authentication middleware
    app.add_middleware(
        AuthenticationMiddleware,
        auth_backend=auth_backend,
        exclude_paths=exclude_paths,
    )

    # Register authentication error handlers
    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        """
        Handle authentication errors.

        Args:
            request: The request that caused the error
            exc: The authentication error

        Returns:
            A JSON response with the error details
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {"code": exc.code, "message": str(exc), "details": exc.details}
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
