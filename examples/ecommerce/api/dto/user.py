"""
User-related data transfer objects for the API layer.

This module contains DTOs for user profile management, etc.
Note: Authentication is handled externally via JWT.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr

from examples.ecommerce.api.dto.common import AddressDTO


class UserResponse(BaseModel):
    """Response model for user data."""
    
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    billing_address: Optional[AddressDTO] = Field(None, description="Billing address")
    shipping_address: Optional[AddressDTO] = Field(None, description="Shipping address")
    is_active: bool = Field(..., description="Whether the user is active")
    is_admin: bool = Field(..., description="Whether the user is an administrator")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "555-123-4567",
                "billing_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345"
                },
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345"
                },
                "is_active": True,
                "is_admin": False,
                "created_at": "2023-01-01T12:00:00Z"
            }
        }


class CreateUserRequest(BaseModel):
    """Request model for creating a new user profile."""
    
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    billing_address: Optional[AddressDTO] = Field(None, description="Billing address")
    shipping_address: Optional[AddressDTO] = Field(None, description="Shipping address")
    use_billing_for_shipping: bool = Field(False, description="Use billing address for shipping")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "555-123-4567",
                "billing_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345"
                },
                "use_billing_for_shipping": True
            }
        }


class UpdateUserRequest(BaseModel):
    """Request model for updating user profile."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    billing_address: Optional[AddressDTO] = Field(None, description="Billing address")
    shipping_address: Optional[AddressDTO] = Field(None, description="Shipping address")
    use_billing_for_shipping: Optional[bool] = Field(None, description="Use billing address for shipping")
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "Johnny",
                "phone": "555-987-6543",
                "billing_address": {
                    "street": "456 Oak Ave",
                    "city": "Othertown",
                    "state": "NY",
                    "postal_code": "67890"
                },
                "use_billing_for_shipping": True
            }
        }