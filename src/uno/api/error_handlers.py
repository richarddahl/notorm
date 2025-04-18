# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
FastAPI error handlers for Uno API endpoints.

This module provides standardized error handling for FastAPI endpoints,
ensuring consistent error responses across the API.
"""

from typing import Any, Dict, Optional, Type, Union, Callable
import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from uno.core.base.error import (
    BaseError,
    ValidationError,
    NotFoundError,
    AuthorizationError,
)
from uno.core.errors.result import ErrorResult

# Configure logger
logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
        help_text: Optional[str] = None,
    ):
        """
        Initialize a standardized error response.

        Args:
            code: Error code (e.g. "VALIDATION_ERROR")
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details, if any
            help_text: Optional help text to guide users in resolving the error
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.help_text = help_text

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error response to a dictionary."""
        response = {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

        if self.help_text:
            response["help_text"] = self.help_text

        return response

    def to_json_response(self) -> JSONResponse:
        """Convert the error response to a FastAPI JSONResponse."""
        return JSONResponse(status_code=self.status_code, content=self.to_dict())


# Error mapping - maps error types to handler functions
ERROR_HANDLERS: Dict[Type[Exception], Callable[[Exception], ErrorResponse]] = {}


def register_error_handler(
    exception_type: Type[Exception],
) -> Callable[
    [Callable[[Exception], ErrorResponse]], Callable[[Exception], ErrorResponse]
]:
    """
    Decorator to register an error handler for an exception type.

    Args:
        exception_type: The exception type to handle

    Returns:
        Decorator function
    """

    def decorator(
        handler: Callable[[Exception], ErrorResponse],
    ) -> Callable[[Exception], ErrorResponse]:
        ERROR_HANDLERS[exception_type] = handler
        return handler

    return decorator


@register_error_handler(ValidationError)
def handle_validation_error(exc: ValidationError) -> ErrorResponse:
    """Handle ValidationError exceptions."""
    return ErrorResponse(
        code="VALIDATION_ERROR",
        message=str(exc),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=getattr(exc, "details", {}),
        help_text="Please check the request parameters and ensure they meet the validation requirements.",
    )


@register_error_handler(PydanticValidationError)
def handle_pydantic_validation_error(exc: PydanticValidationError) -> ErrorResponse:
    """Handle Pydantic ValidationError exceptions."""
    errors = []
    for error in exc.errors():
        error_info = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        errors.append(error_info)

    return ErrorResponse(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors},
        help_text="Please check the format of your request and make sure all required fields are provided.",
    )


@register_error_handler(RequestValidationError)
def handle_request_validation_error(exc: RequestValidationError) -> ErrorResponse:
    """Handle FastAPI RequestValidationError exceptions."""
    errors = []
    for error in exc.errors():
        error_info = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        errors.append(error_info)

    return ErrorResponse(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors},
        help_text="Please check the format of your request and make sure all required fields are provided.",
    )


@register_error_handler(NotFoundError)
def handle_not_found_error(exc: NotFoundError) -> ErrorResponse:
    """Handle NotFoundError exceptions."""
    return ErrorResponse(
        code="NOT_FOUND",
        message=str(exc),
        status_code=status.HTTP_404_NOT_FOUND,
        details=getattr(exc, "details", {}),
        help_text="The requested resource could not be found. Please check the identifier and try again.",
    )


@register_error_handler(AuthorizationError)
def handle_authorization_error(exc: AuthorizationError) -> ErrorResponse:
    """Handle AuthorizationError exceptions."""
    return ErrorResponse(
        code="FORBIDDEN",
        message=str(exc),
        status_code=status.HTTP_403_FORBIDDEN,
        details=getattr(exc, "details", {}),
        help_text="You do not have the necessary permissions to access this resource.",
    )


@register_error_handler(ErrorResult)
def handle_error_result(exc: ErrorResult) -> ErrorResponse:
    """Handle ErrorResult from Result type."""
    status_mapping = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "CONFLICT": status.HTTP_409_CONFLICT,
    }

    status_code = status_mapping.get(exc.error_code, status.HTTP_400_BAD_REQUEST)

    return ErrorResponse(
        code=exc.error_code,
        message=exc.error_message,
        status_code=status_code,
        details=exc.error_details or {},
    )


@register_error_handler(Exception)
def handle_generic_exception(exc: Exception) -> ErrorResponse:
    """Handle generic exceptions."""
    # Log the full exception for debugging
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())

    return ErrorResponse(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        help_text="Please try again later. If the problem persists, contact the system administrator.",
    )


def find_exception_handler(exc: Exception) -> Callable[[Exception], ErrorResponse]:
    """
    Find the appropriate error handler for an exception.

    Args:
        exc: The exception to handle

    Returns:
        Error handler function
    """
    # Try to find a direct match for the exception type
    for exc_type, handler in ERROR_HANDLERS.items():
        if isinstance(exc, exc_type):
            return handler

    # If no direct match, find a base class match
    for exc_type, handler in ERROR_HANDLERS.items():
        if issubclass(type(exc), exc_type):
            return handler

    # Default to generic exception handler
    return handle_generic_exception


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI.

    Args:
        request: The FastAPI request
        exc: The exception to handle

    Returns:
        JSONResponse with standardized error format
    """
    handler = find_exception_handler(exc)
    error_response = handler(exc)

    # Log the error
    if error_response.status_code >= 500:
        logger.error(
            f"Error processing request {request.url}: {error_response.message}"
        )
        logger.error(traceback.format_exc())
    elif error_response.status_code >= 400:
        logger.warning(
            f"Client error for request {request.url}: {error_response.message}"
        )

    return error_response.to_json_response()


def configure_error_handlers(app: FastAPI) -> None:
    """
    Configure error handlers for a FastAPI application.

    Args:
        app: FastAPI application
    """
    # Register the global exception handler
    app.exception_handler(Exception)(global_exception_handler)

    # Register specific exception handlers
    app.exception_handler(ValidationError)(
        lambda req, exc: handle_validation_error(exc).to_json_response()
    )
    app.exception_handler(PydanticValidationError)(
        lambda req, exc: handle_pydantic_validation_error(exc).to_json_response()
    )
    app.exception_handler(RequestValidationError)(
        lambda req, exc: handle_request_validation_error(exc).to_json_response()
    )
    app.exception_handler(NotFoundError)(
        lambda req, exc: handle_not_found_error(exc).to_json_response()
    )
    app.exception_handler(AuthorizationError)(
        lambda req, exc: handle_authorization_error(exc).to_json_response()
    )
    app.exception_handler(ErrorResult)(
        lambda req, exc: handle_error_result(exc).to_json_response()
    )
