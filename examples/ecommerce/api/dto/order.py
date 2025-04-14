"""
Order-related data transfer objects for the API layer.

This module contains DTOs for order management and processing.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from examples.ecommerce.api.dto.common import AddressDTO, MoneyDTO


class OrderItemDTO(BaseModel):
    """Data transfer object for order items."""

    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity")

    @validator("quantity")
    def quantity_must_be_positive(cls, v):
        """Validate that quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "quantity": 2,
            }
        }


class OrderItemResponse(BaseModel):
    """Response model for order items."""

    id: str = Field(..., description="Order item ID")
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    price: MoneyDTO = Field(..., description="Product price")
    quantity: int = Field(..., description="Quantity")
    total_price: MoneyDTO = Field(..., description="Total price for this item")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "product_id": "456e7890-e12d-34d5-a678-426614174000",
                "product_name": "Premium Laptop",
                "price": {"amount": 1299.99, "currency": "USD"},
                "quantity": 1,
                "total_price": {"amount": 1299.99, "currency": "USD"},
            }
        }


class PaymentDetailsDTO(BaseModel):
    """Data transfer object for payment details."""

    method: str = Field(..., description="Payment method")
    details: Dict[str, Any] = Field(..., description="Payment details")

    class Config:
        json_schema_extra = {
            "example": {
                "method": "credit_card",
                "details": {
                    "card_number": "4111111111111111",
                    "expiry_month": 12,
                    "expiry_year": 2025,
                    "holder_name": "John Doe",
                },
            }
        }


class PaymentResponse(BaseModel):
    """Response model for payment data."""

    id: str = Field(..., description="Payment ID")
    amount: MoneyDTO = Field(..., description="Payment amount")
    method: str = Field(..., description="Payment method")
    status: str = Field(..., description="Payment status")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": {"amount": 1299.99, "currency": "USD"},
                "method": "credit_card",
                "status": "completed",
                "transaction_id": "txn_123456789",
                "created_at": "2023-01-01T12:00:00Z",
            }
        }


class CreateOrderRequest(BaseModel):
    """Request model for creating a new order."""

    items: List[OrderItemDTO] = Field(..., min_items=1, description="Order items")
    shipping_address: AddressDTO = Field(..., description="Shipping address")
    billing_address: AddressDTO = Field(..., description="Billing address")
    notes: Optional[str] = Field(None, description="Order notes")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "product_id": "123e4567-e89b-12d3-a456-426614174000",
                        "quantity": 1,
                    },
                    {
                        "product_id": "789e0123-e45d-67d8-a901-426614174000",
                        "quantity": 2,
                    },
                ],
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                },
                "billing_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                },
                "notes": "Please leave package at the door",
            }
        }


class OrderResponse(BaseModel):
    """Response model for order data."""

    id: str = Field(..., description="Order ID")
    user_id: str = Field(..., description="User ID")
    items: List[OrderItemResponse] = Field(..., description="Order items")
    shipping_address: AddressDTO = Field(..., description="Shipping address")
    billing_address: AddressDTO = Field(..., description="Billing address")
    status: str = Field(..., description="Order status")
    subtotal: MoneyDTO = Field(..., description="Order subtotal")
    payment: Optional[PaymentResponse] = Field(None, description="Payment information")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    shipped_at: Optional[str] = Field(None, description="Shipping timestamp (ISO 8601)")
    delivered_at: Optional[str] = Field(
        None, description="Delivery timestamp (ISO 8601)"
    )
    cancelled_at: Optional[str] = Field(
        None, description="Cancellation timestamp (ISO 8601)"
    )
    notes: Optional[str] = Field(None, description="Order notes")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e7890-e12d-34d5-a678-426614174000",
                "items": [
                    {
                        "id": "789e0123-e45d-67d8-a901-426614174000",
                        "product_id": "abc1234-e56d-78d9-a012-426614174000",
                        "product_name": "Premium Laptop",
                        "price": {"amount": 1299.99, "currency": "USD"},
                        "quantity": 1,
                        "total_price": {"amount": 1299.99, "currency": "USD"},
                    }
                ],
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                },
                "billing_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                },
                "status": "paid",
                "subtotal": {"amount": 1299.99, "currency": "USD"},
                "payment": {
                    "id": "def5678-e90e-12e3-a456-426614174000",
                    "amount": {"amount": 1299.99, "currency": "USD"},
                    "method": "credit_card",
                    "status": "completed",
                    "transaction_id": "txn_123456789",
                    "created_at": "2023-01-01T12:05:00Z",
                },
                "created_at": "2023-01-01T12:00:00Z",
                "shipped_at": null,
                "delivered_at": null,
                "cancelled_at": null,
                "notes": "Please leave package at the door",
            }
        }


class ProcessPaymentRequest(BaseModel):
    """Request model for processing an order payment."""

    payment_method: str = Field(..., description="Payment method")
    payment_details: Dict[str, Any] = Field(..., description="Payment details")

    class Config:
        json_schema_extra = {
            "example": {
                "payment_method": "credit_card",
                "payment_details": {
                    "card_number": "4111111111111111",
                    "expiry_month": 12,
                    "expiry_year": 2025,
                    "holder_name": "John Doe",
                },
            }
        }


class UpdateOrderStatusRequest(BaseModel):
    """Request model for updating an order's status."""

    status: str = Field(..., description="New order status")
    notes: Optional[str] = Field(None, description="Status change notes")

    @validator("status")
    def validate_status(cls, v):
        """Validate that the status is valid."""
        valid_statuses = [
            "pending",
            "paid",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "shipped",
                "notes": "Shipped via FedEx, tracking number: 123456789",
            }
        }


class CancelOrderRequest(BaseModel):
    """Request model for cancelling an order."""

    reason: Optional[str] = Field(None, description="Cancellation reason")

    class Config:
        json_schema_extra = {"example": {"reason": "Customer requested cancellation"}}
