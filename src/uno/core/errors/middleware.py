from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import Any, Dict, Optional
from uno.core.errors.framework import FrameworkError, ErrorCatalog


class ErrorHandlingMiddleware:
    """Middleware for handling and formatting errors consistently."""

    async def __call__(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except FrameworkError as e:
            return JSONResponse(
                status_code=e.http_status_code,
                content={
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details,
                        "category": e.category.value,
                        "severity": e.severity.value,
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None
                    }
                }
            )
        except RequestValidationError as e:
            error_details = {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": e.errors(),
                    "body": e.body
                }
            }
            return JSONResponse(
                status_code=400,
                content={
                    "error": error_details
                }
            )
        except ValidationError as e:
            error_details = {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {
                    "errors": e.errors(),
                    "message": str(e)
                }
            }
            return JSONResponse(
                status_code=400,
                content={
                    "error": error_details
                }
            )
        except Exception as e:
            error_details = {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {
                    "message": str(e)
                }
            }
            return JSONResponse(
                status_code=500,
                content={
                    "error": error_details
                }
            )
