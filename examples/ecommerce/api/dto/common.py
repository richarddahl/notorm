"""
Common data transfer objects for the API layer.

This module contains DTOs shared across multiple API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class AddressDTO(BaseModel):
    """Data transfer object for addresses."""

    street: str = Field(..., description="Street address including number")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="ZIP or postal code")
    country: str = Field(default="USA", description="Country name")

    class Config:
        json_schema_extra = {
            "example": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345",
                "country": "USA",
            }
        }


class MoneyDTO(BaseModel):
    """Data transfer object for monetary amounts."""

    amount: float = Field(..., description="Monetary amount")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")

    class Config:
        json_schema_extra = {"example": {"amount": 29.99, "currency": "USD"}}


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    def get_limit_offset(self) -> tuple[int, int]:
        """Calculate limit and offset for database queries."""
        limit = self.page_size
        offset = (self.page - 1) * self.page_size
        return limit, offset


class PaginatedResponse(BaseModel):
    """Generic wrapper for paginated responses."""

    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls, items: List[Any], total: int, pagination: PaginationParams
    ) -> "PaginatedResponse":
        """Create a paginated response."""
        pages = (
            (total + pagination.page_size - 1) // pagination.page_size
            if total > 0
            else 0
        )
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")

    class Config:
        json_schema_extra = {
            "example": {"detail": "Resource not found", "code": "NOT_FOUND"}
        }
