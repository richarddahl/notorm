# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
FastAPI exception handlers for Uno error system.

This module provides exception handlers for FastAPI applications that integrate
with the Uno error system. These handlers convert BaseError objects to
appropriate HTTP responses with correct status codes.
"""

from typing import Dict, Any, Union, List, Type, Callable
import traceback
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from uno.core.base.error import BaseError, ErrorCode, ErrorCategory, ErrorSeverity
from uno.core.errors.validation import ValidationError as UnoValidationError

# Setup logging
logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI, include_tracebacks: bool = False) -> None:
    """
    Set up exception handlers for a FastAPI application.

    This function registers exception handlers for various error types to ensure
    that errors are properly converted to HTTP responses with appropriate status codes.

    Args:
        app: The FastAPI application to set up handlers for
        include_tracebacks: Whether to include tracebacks in error responses (default: False)
    """

    @app.exception_handler(BaseError)
    async def uno_error_handler(request: Request, exc: BaseError) -> JSONResponse:
        """
        Handle BaseError exceptions.

        This handler converts BaseError objects to JSONResponse with appropriate status code
        from the error's error_info.

        Args:
            request: The FastAPI request object
            exc: The BaseError exception

        Returns:
            A JSONResponse with appropriate status code and content
        """
        logger.error(f"BaseError: {exc}", exc_info=True)

        response_content = _build_error_response(
            exc, include_traceback=include_tracebacks
        )

        return JSONResponse(status_code=exc.http_status_code, content=response_content)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle FastAPI RequestValidationError exceptions.

        This handler converts FastAPI validation errors to a consistent error format
        with status code 400.

        Args:
            request: The FastAPI request object
            exc: The RequestValidationError exception

        Returns:
            A JSONResponse with status code 400 and error content
        """
        logger.warning(f"Validation error: {exc}", exc_info=True)

        # Extract validation errors
        errors = []
        for error in exc.errors():
            error_loc = ".".join(str(loc) for loc in error.get("loc", []))
            error_msg = error.get("msg", "")
            error_type = error.get("type", "")

            errors.append(
                {"field": error_loc, "message": error_msg, "type": error_type}
            )

        response_content = {
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Validation error",
                "details": errors,
                "category": ErrorCategory.VALIDATION.name,
                "severity": ErrorSeverity.ERROR.name,
            }
        }

        if include_tracebacks:
            response_content["error"]["traceback"] = "".join(traceback.format_exc())

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=response_content
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic ValidationError exceptions.

        This handler converts Pydantic validation errors to a consistent error format
        with status code 400.

        Args:
            request: The FastAPI request object
            exc: The ValidationError exception

        Returns:
            A JSONResponse with status code 400 and error content
        """
        logger.warning(f"Pydantic validation error: {exc}", exc_info=True)

        # Extract validation errors
        errors = []
        for error in exc.errors():
            error_loc = ".".join(str(loc) for loc in error.get("loc", []))
            error_msg = error.get("msg", "")
            error_type = error.get("type", "")

            errors.append(
                {"field": error_loc, "message": error_msg, "type": error_type}
            )

        response_content = {
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Validation error",
                "details": errors,
                "category": ErrorCategory.VALIDATION.name,
                "severity": ErrorSeverity.ERROR.name,
            }
        }

        if include_tracebacks:
            response_content["error"]["traceback"] = "".join(traceback.format_exc())

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=response_content
        )

    @app.exception_handler(UnoValidationError)
    async def uno_validation_error_handler(
        request: Request, exc: UnoValidationError
    ) -> JSONResponse:
        """
        Handle UnoValidationError exceptions.

        This handler converts UnoValidationError objects to JSONResponse with status code 400.

        Args:
            request: The FastAPI request object
            exc: The UnoValidationError exception

        Returns:
            A JSONResponse with status code 400 and error content
        """
        logger.warning(f"Uno validation error: {exc}", exc_info=True)

        response_content = _build_error_response(
            exc, include_traceback=include_tracebacks
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=response_content
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle generic exceptions.

        This handler catches any uncaught exceptions and converts them to a JSONResponse
        with status code 500.

        Args:
            request: The FastAPI request object
            exc: The Exception object

        Returns:
            A JSONResponse with status code 500 and error content
        """
        # Log the error with traceback for server-side debugging
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        # Create a response with minimal information (for security reasons)
        response_content = {
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "An unexpected error occurred",
                "category": ErrorCategory.INTERNAL.name,
                "severity": ErrorSeverity.ERROR.name,
            }
        }

        # Include traceback only in development mode
        if include_tracebacks:
            response_content["error"]["traceback"] = "".join(traceback.format_exc())
            response_content["error"]["details"] = str(exc)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response_content
        )


def _build_error_response(
    exc: BaseError, include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Build a standardized error response from an BaseError.

    Args:
        exc: The BaseError exception
        include_traceback: Whether to include traceback in the response

    Returns:
        A dictionary with error details
    """
    # Start with the basic error information
    response = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "context": {k: str(v) for k, v in exc.context.items()},
        }
    }

    # Add category and severity if available
    if exc.category:
        response["error"]["category"] = exc.category.name

    if exc.severity:
        response["error"]["severity"] = exc.severity.name

    # Add traceback only if requested (typically in development mode)
    if include_traceback:
        response["error"]["traceback"] = exc.traceback

    return response


class ErrorHandlingMiddleware:
    """
    Middleware for handling errors in FastAPI applications.

    This middleware catches exceptions, logs them, and converts them to
    appropriate HTTP responses.
    """

    def __init__(
        self,
        app: FastAPI,
        include_tracebacks: bool = False,
        log_level: int = logging.ERROR,
    ):
        """
        Initialize the error handling middleware.

        Args:
            app: The FastAPI application
            include_tracebacks: Whether to include tracebacks in error responses
            log_level: The logging level for errors
        """
        self.app = app
        self.include_tracebacks = include_tracebacks
        self.log_level = log_level
        self.logger = logging.getLogger(__name__)

    async def __call__(self, scope, receive, send):
        """
        ASGI application entry point.

        Args:
            scope: The ASGI scope
            receive: The ASGI receive function
            send: The ASGI send function
        """
        if scope["type"] != "http":
            # Pass through non-HTTP requests
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Log the error
            self.logger.log(self.log_level, f"Error in request: {exc}", exc_info=True)

            # Convert to BaseError if it's not already
            if not isinstance(exc, BaseError):
                exc = BaseError(message=str(exc), error_code=ErrorCode.INTERNAL_ERROR)

            # Build the response
            response_content = _build_error_response(
                exc, include_traceback=self.include_tracebacks
            )

            # Send a JSON response
            response = JSONResponse(
                status_code=exc.http_status_code, content=response_content
            )

            await response(scope, receive, send)


def register_common_error_handlers(
    app: FastAPI, handlers: Dict[Type[Exception], Callable] = None
) -> None:
    """
    Register common error handlers for specific exception types.

    Args:
        app: The FastAPI application
        handlers: Custom exception handlers to register
    """
    # Set up the Uno error handlers
    setup_error_handlers(app)

    # Register custom handlers if provided
    if handlers:
        for exc_class, handler in handlers.items():
            app.add_exception_handler(exc_class, handler)
