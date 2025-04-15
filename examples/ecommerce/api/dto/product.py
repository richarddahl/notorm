"""
Product-related data transfer objects for the API layer.

This module contains DTOs for product management and catalog browsing.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator

from examples.ecommerce.api.dto.common import MoneyDTO


class ProductAttributeDTO(BaseModel):
    """Data transfer object for product attributes."""

    name: str = Field(..., description="Attribute name")
    value: str = Field(..., description="Attribute value")


class RatingDTO(BaseModel):
    """Data transfer object for product ratings."""

    score: int = Field(..., ge=1, le=5, description="Rating score (1-5)")
    comment: Optional[str] = Field(None, description="Rating comment")

    class Config:
        json_schema_extra = {
            "example": {"score": 5, "comment": "Excellent product, highly recommended!"}
        }


class CreateProductRequest(BaseModel):
    """Request model for creating a new product."""

    name: str = Field(..., min_length=1, max_length=100, description="Product name")
    description: str = Field(..., min_length=1, description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    currency: str = Field(default="USD", description="Price currency")
    category_id: Optional[str] = Field(None, description="Category ID")
    inventory_count: int = Field(default=0, ge=0, description="Initial inventory count")
    attributes: Optional[Dict[str, str]] = Field(None, description="Product attributes")

    @field_validator("price")
    def price_must_be_positive(cls, v):
        """Validate that price is positive."""
        if v <= 0:
            raise ValueError("Price must be positive")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Premium Laptop",
        json_schema_extracription": "High-end laptop with 16GB RAM and 1TB SSD",
                "price": 1299.99,
                "currency": "USD",
                "category_id": "electronics",
                "inventory_count": 10,
                "attributes": {
                    "brand": "TechPro",
                    "model": "X5000",
                    "color": "Silver",
                    "weight": "3.5 lbs",
                    "screen_size": "15.6 inches",
                },
            }
        }


class UpdateProductRequest(BaseModel):
    """Request model for updating a product."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Product name"
    )
    description: Optional[str] = Field(
        None, min_length=1, description="Product description"
    )
    price: Optional[float] = Field(None, gt=0, description="Product price")
    currency: Optional[str] = Field(None, description="Price currency")
    category_id: Optional[str] = Field(None, description="Category ID")
    inventory_count: Optional[int] = Field(None, ge=0, description="Inventory count")
    attributes: Optional[Dict[str, str]] = Field(None, description="Product attributes")
    is_active: Optional[bool] = Field(None, description="Whether the product is active")

    clasjson_schema_extra
        json_schema_extra = {
            "example": {
                "name": "Premium Laptop X6",
                "price": 1399.99,
                "inventory_count": 15,
                "is_active": True,
            }
        }


class ProductResponse(BaseModel):
    """Response model for product data."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: MoneyDTO = Field(..., description="Product price")
    category_id: Optional[str] = Field(None, description="Category ID")
    inventory_count: int = Field(..., description="Inventory count")
    is_active: bool = Field(..., description="Whether the product is active")
    is_in_stock: bool = Field(..., description="Whether the product is in stock")
    attributes: Dict[str, str] = Field(..., description="Product attributes")
    average_rating: Optional[float] = Field(None, description="Average rating")
    ratings_count: int = Field(..., description="Number of ratings")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    clasjson_schema_extra
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Premium Laptop",
                "description": "High-end laptop with 16GB RAM and 1TB SSD",
                "price": {"amount": 1299.99, "currency": "USD"},
                "category_id": "electronics",
                "inventory_count": 10,
                "is_active": True,
                "is_in_stock": True,
                "attributes": {
                    "brand": "TechPro",
                    "model": "X5000",
                    "color": "Silver",
                    "weight": "3.5 lbs",
                    "screen_size": "15.6 inches",
                },
                "average_rating": 4.5,
                "ratings_count": 12,
                "created_at": "2023-01-01T12:00:00Z",
            }
        }


class ProductSearchParams(BaseModel):
    """Query parameters for product search."""

    query: Optional[str] = Field(None, description="Search query")
    category_id: Optional[str] = Field(None, description="Category ID")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    in_stock_only: bool = Field(False, description="Only include products in stock")
    sort_by: str = Field(default="name", description="Sort field")
    sort_order: str = Field(default="asc", description="Sort order (asc or desc)")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
        json_schema_extrary": "laptop",
                "category_id": "electronics",
                "min_price": 1000,
                "max_price": 2000,
                "in_stock_only": True,
                "sort_by": "price",
                "sort_order": "asc",
                "page": 1,
                "page_size": 20,
            }
        }


class InventoryUpdateRequest(BaseModel):
    """Request model for updating product inventory."""

    change: int = Field(
        ..., description="Inventory change amount (positive to add, negative to remove)"
    )
    reason: str = Field(
        ..., min_length=1, description="Reason for the inventory change"
    )
json_schema_extra
    class Config:
        json_schema_extra = {"example": {"change": 5, "reason": "Received new shipment"}}


class AddRatingRequest(BaseModel):
    """Request model for adding a product rating."""

    score: int = Field(..., ge=1, le=5, description="Rating score (1-5)")
    comment: Optional[str] = Field(None, description="Rating comment")

    class Config:
        json_schema_extra = {
            "example": {"score": 5, "comment": "Excellent product, highly recommended!"}
        }
json_schema_extra