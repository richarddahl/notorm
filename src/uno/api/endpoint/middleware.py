"""
Middleware for API endpoints.

This module provides middleware for handling errors, logging, and other
cross-cutting concerns for API endpoints.
"""

from typing import Any, Callable, Dict, Optional, Type

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from uno.core.errors.base import UnoError

from .response import ErrorDetail, ErrorResponse

__all__ = [
    "ErrorHandlerMiddleware",
    "setup_error_handlers",
]


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling errors in API requests.
    
    This middleware catches exceptions and converts them to standardized error responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and handle any errors.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint handler.
            
        Returns:
            The response, either from the next handler or an error response.
        """
        try:
            return await call_next(request)
        except UnoError as e:
            # Handle domain errors
            status_code = getattr(e, "status_code", 400)
            error_detail = ErrorDetail(
                code=getattr(e, "code", "DOMAIN_ERROR"),
                message=str(e),
                field=getattr(e, "field", None),
                details=getattr(e, "details", None),
            )
            response = ErrorResponse(error=error_detail)
            return JSONResponse(content=response.dict(), status_code=status_code)
        except Exception as e:
            # Handle unexpected errors
            error_detail = ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details={"exception": str(e)},
            )
            response = ErrorResponse(error=error_detail)
            return JSONResponse(content=response.dict(), status_code=HTTP_500_INTERNAL_SERVER_ERROR)


def setup_error_handlers(app: FastAPI) -> None:
    """
    Set up error handlers for a FastAPI application.
    
    This function adds handlers for common error types, converting them to
    standardized error responses.
    
    Args:
        app: The FastAPI application to add handlers to.
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_detail = ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            details=exc.detail if not isinstance(exc.detail, str) else None,
        )
        response = ErrorResponse(error=error_detail)
        return JSONResponse(content=response.dict(), status_code=exc.status_code)
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = exc.errors()
        field = errors[0]["loc"][-1] if errors and "loc" in errors[0] and errors[0]["loc"] else None
        
        error_detail = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation error",
            field=field,
            details={"errors": errors},
        )
        response = ErrorResponse(error=error_detail)
        return JSONResponse(content=response.dict(), status_code=HTTP_422_UNPROCESSABLE_ENTITY)
    
    @app.exception_handler(UnoError)
    async def uno_error_handler(request: Request, exc: UnoError) -> JSONResponse:
        """Handle UnoError exceptions."""
        status_code = getattr(exc, "status_code", 400)
        error_detail = ErrorDetail(
            code=getattr(exc, "code", "DOMAIN_ERROR"),
            message=str(exc),
            field=getattr(exc, "field", None),
            details=getattr(exc, "details", None),
        )
        response = ErrorResponse(error=error_detail)
        return JSONResponse(content=response.dict(), status_code=status_code)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        error_detail = ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"exception": str(exc)},
        )
        response = ErrorResponse(error=error_detail)
        return JSONResponse(content=response.dict(), status_code=HTTP_500_INTERNAL_SERVER_ERROR)