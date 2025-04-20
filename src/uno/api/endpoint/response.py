"""
Response formatting for API endpoints.

This module provides utilities for standardizing API responses and handling
pagination, filtering, and error responses.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, create_model

from uno.core.errors.result import Result, Success
from uno.core.errors.framework import ErrorDetail as FrameworkErrorDetail

__all__ = [
    "PaginatedResponse",
    "DataResponse",
    "ApiErrorDetail",
    "ErrorResponse",
    "response_handler",
    "paginated_response",
    "framework_error_to_api_error",
]

T = TypeVar("T")


class PaginationMetadata(BaseModel):
    """Metadata for paginated responses."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class ApiErrorDetail(BaseModel):
    """API-friendly representation of error details."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: str | None = Field(None, description="Field associated with the error")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard response format for paginated data."""

    data: list[T] = Field(..., description="List of items")
    meta: PaginationMetadata = Field(..., description="Pagination metadata")


class DataResponse(BaseModel, Generic[T]):
    """Standard response format for data."""

    data: T = Field(..., description="Response data")
    meta: dict[str, Any] | None = Field(None, description="Response metadata")


class ErrorResponse(BaseModel):
    """Standard response format for errors."""

    error: ApiErrorDetail = Field(..., description="Error details")
    meta: dict[str, Any] | None = Field(None, description="Response metadata")


def response_handler(
    result: Result[T], status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    Handle a Result object and return a standardized API response.

    Args:
        result: The Result object to handle.
        status_code: The HTTP status code to use for successful responses.

    Returns:
        A standardized JSONResponse.
    """
    if isinstance(result, Success):
        response = DataResponse(data=result.value)
        return JSONResponse(content=response.dict(), status_code=status_code)

    # Handle specific error types
    error = result.error
    error_status_code = status.HTTP_400_BAD_REQUEST

    # Map domain errors to HTTP status codes
    if hasattr(error, "status_code"):
        error_status_code = error.status_code
    elif hasattr(error, "code"):
        error_code = error.code
        if error_code.startswith("NOT_FOUND"):
            error_status_code = status.HTTP_404_NOT_FOUND
        elif error_code.startswith("UNAUTHORIZED"):
            error_status_code = status.HTTP_401_UNAUTHORIZED
        elif error_code.startswith("FORBIDDEN"):
            error_status_code = status.HTTP_403_FORBIDDEN
        elif error_code.startswith("CONFLICT"):
            error_status_code = status.HTTP_409_CONFLICT

    # Create error detail
    error_detail = ApiErrorDetail(
        code=getattr(error, "code", "ERROR"),
        message=str(error),
        field=getattr(error, "field", None),
        details=getattr(error, "details", None),
    )

    # Create error response
    response = ErrorResponse(error=error_detail)
    return JSONResponse(content=response.dict(), status_code=error_status_code)


def paginated_response(
    items: list[T],
    page: int,
    page_size: int,
    total_items: int,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """
    Create a standardized paginated response.

    Args:
        items: The list of items for the current page.
        page: The current page number.
        page_size: The number of items per page.
        total_items: The total number of items.
        status_code: The HTTP status code to use for the response.

    Returns:
        A standardized JSONResponse with pagination metadata.
    """
    # Calculate pagination metadata
    total_pages = (total_items + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1

    # Create pagination metadata
    meta = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )

    # Create paginated response
    response = PaginatedResponse(data=items, meta=meta)
    return JSONResponse(content=response.dict(), status_code=status_code)
