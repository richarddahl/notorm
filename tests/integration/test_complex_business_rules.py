"""
Integration tests for complex business rules and API endpoints.

This module provides comprehensive tests for complex business rules involving
multiple entities, cross-entity validation, and integration with API endpoints.
It focuses on testing advanced business logic and ensuring proper API behavior
under complex scenarios.
"""

import pytest
import json
import re
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator

from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from uno.core.errors import ValidationContext, UnoError, ErrorCode
from uno.core.errors.validation import ValidationError
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.database.db import FilterParam
from uno.core.di import inject, Inject
from uno.dependencies.interfaces import UnoRepositoryProtocol, UnoServiceProtocol


# ===== DOMAIN MODELS =====

class CustomerModel(UnoModel):
    """Database model for customers."""
    
    __tablename__ = "customers"
    
    first_name: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    last_name: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
    phone: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    address: Mapped[str] = mapped_column(nullable=True)
    city: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    state: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    postal_code: Mapped[PostgresTypes.String20] = mapped_column(nullable=True)
    country: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    loyalty_points: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class ProductModel(UnoModel):
    """Database model for products."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    sku: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, unique=True)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    minimum_order_quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    maximum_order_quantity: Mapped[int] = mapped_column(nullable=True)
    tax_rate: Mapped[PostgresTypes.Decimal5_2] = mapped_column(nullable=False, default=0)
    is_taxable: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class OrderItemModel(UnoModel):
    """Database model for order items."""
    
    __tablename__ = "order_items"
    
    order_id: Mapped[str] = mapped_column(nullable=False)
    product_id: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    discount: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False, default=0)
    tax_amount: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class OrderModel(UnoModel):
    """Database model for orders."""
    
    __tablename__ = "orders"
    
    customer_id: Mapped[str] = mapped_column(nullable=False)
    order_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    total_amount: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    status: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, default="pending")
    shipping_address: Mapped[str] = mapped_column(nullable=True)
    shipping_city: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    shipping_state: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    shipping_postal_code: Mapped[PostgresTypes.String20] = mapped_column(nullable=True)
    shipping_country: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    shipping_method: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    payment_method: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    payment_status: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, default="pending")
    notes: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


# ===== BUSINESS OBJECTS =====

class CustomerDTO(BaseModel):
    """Data transfer object for customer API responses."""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True
    loyalty_points: int = 0
    created_at: datetime
    updated_at: datetime

    @property
    def full_name(self) -> str:
        """Get the customer's full name."""
        return f"{self.first_name} {self.last_name}"


class Customer(UnoObj[CustomerModel]):
    """Customer business object with domain-specific validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "first_name", "last_name", "email", "is_active"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for customers."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Email validation
        if hasattr(self, "email") and self.email:
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_pattern, self.email):
                context.add_error(
                    field="email",
                    message="Invalid email format",
                    error_code="INVALID_EMAIL_FORMAT"
                )
        
        # Phone validation (if provided)
        if hasattr(self, "phone") and self.phone:
            # Simple pattern for demonstration purposes
            phone_pattern = r"^\+?[\d\s\-\(\)]{10,20}$"
            if not re.match(phone_pattern, self.phone):
                context.add_error(
                    field="phone",
                    message="Invalid phone number format",
                    error_code="INVALID_PHONE_FORMAT"
                )
        
        # Postal code validation (if provided)
        if hasattr(self, "postal_code") and self.postal_code and hasattr(self, "country") and self.country:
            # Validate US postal codes (simple example)
            if self.country.lower() == "usa" or self.country.lower() == "united states":
                us_zip_pattern = r"^\d{5}(-\d{4})?$"
                if not re.match(us_zip_pattern, self.postal_code):
                    context.add_error(
                        field="postal_code",
                        message="Invalid US postal code format",
                        error_code="INVALID_POSTAL_CODE"
                    )
        
        return context
    
    # Business methods
    async def add_loyalty_points(self, points: int) -> int:
        """
        Add loyalty points to the customer's account.
        
        Args:
            points: The number of points to add (must be positive)
            
        Returns:
            The new loyalty points balance
            
        Raises:
            ValueError: If points is not positive
        """
        if points <= 0:
            raise UnoError(
                "Loyalty points must be a positive number",
                ErrorCode.VALIDATION_ERROR,
                field="points",
                provided_value=points
            )
        
        self.loyalty_points += points
        await self.save()
        return self.loyalty_points
    
    def to_dto(self) -> CustomerDTO:
        """Convert to DTO for API responses."""
        return CustomerDTO(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone=self.phone,
            address=self.address,
            city=self.city,
            state=self.state,
            postal_code=self.postal_code,
            country=self.country,
            is_active=self.is_active,
            loyalty_points=self.loyalty_points,
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class ProductDTO(BaseModel):
    """Data transfer object for product API responses."""
    id: str
    name: str
    description: Optional[str] = None
    price: Decimal
    sku: str
    category: str
    inventory_count: int
    is_active: bool
    minimum_order_quantity: int = 1
    maximum_order_quantity: Optional[int] = None
    tax_rate: Decimal = Decimal("0.00")
    is_taxable: bool = True
    created_at: datetime
    updated_at: datetime


class Product(UnoObj[ProductModel]):
    """Product business object with domain-specific validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "name", "price", "category", "inventory_count", "is_active"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for products."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Price validation
        if hasattr(self, "price") and self.price is not None:
            if self.price <= Decimal("0.00"):
                context.add_error(
                    field="price",
                    message="Price must be greater than zero",
                    error_code="INVALID_PRICE"
                )
        
        # SKU validation - must follow pattern ABC-12345
        if hasattr(self, "sku") and self.sku:
            sku_pattern = r"^[A-Z]{3}-\d{5}$"
            if not re.match(sku_pattern, self.sku):
                context.add_error(
                    field="sku",
                    message="SKU must follow pattern ABC-12345 (3 uppercase letters, dash, 5 digits)",
                    error_code="INVALID_SKU_FORMAT"
                )
        
        # Category validation
        if hasattr(self, "category") and self.category:
            valid_categories = ["Electronics", "Clothing", "Books", "Home", "Toys", "Food", "Sports"]
            if self.category not in valid_categories:
                context.add_error(
                    field="category",
                    message=f"Invalid category. Must be one of {', '.join(valid_categories)}",
                    error_code="INVALID_CATEGORY"
                )
        
        # Minimum order quantity validation
        if hasattr(self, "minimum_order_quantity") and self.minimum_order_quantity is not None:
            if self.minimum_order_quantity < 1:
                context.add_error(
                    field="minimum_order_quantity",
                    message="Minimum order quantity must be at least 1",
                    error_code="INVALID_MIN_ORDER_QUANTITY"
                )
        
        # Maximum order quantity validation
        if hasattr(self, "maximum_order_quantity") and self.maximum_order_quantity is not None:
            if hasattr(self, "minimum_order_quantity") and self.minimum_order_quantity is not None:
                if self.maximum_order_quantity < self.minimum_order_quantity:
                    context.add_error(
                        field="maximum_order_quantity",
                        message="Maximum order quantity must be greater than or equal to minimum order quantity",
                        error_code="INVALID_MAX_ORDER_QUANTITY"
                    )
        
        # Tax rate validation
        if hasattr(self, "tax_rate") and self.tax_rate is not None:
            if self.tax_rate < Decimal("0.00") or self.tax_rate > Decimal("100.00"):
                context.add_error(
                    field="tax_rate",
                    message="Tax rate must be between 0.00 and 100.00",
                    error_code="INVALID_TAX_RATE"
                )
        
        return context
    
    # Business methods
    async def reserve_inventory(self, quantity: int) -> bool:
        """
        Reserve inventory for an order.
        
        Args:
            quantity: The quantity to reserve
            
        Returns:
            True if the inventory was successfully reserved
            
        Raises:
            UnoError: If there's insufficient inventory or quantity is invalid
        """
        if quantity <= 0:
            raise UnoError(
                "Quantity must be a positive number",
                ErrorCode.BUSINESS_RULE,
                quantity=quantity
            )
        
        if quantity < self.minimum_order_quantity:
            raise UnoError(
                f"Order quantity less than minimum ({self.minimum_order_quantity})",
                ErrorCode.BUSINESS_RULE,
                quantity=quantity,
                minimum_quantity=self.minimum_order_quantity
            )
        
        if self.maximum_order_quantity is not None and quantity > self.maximum_order_quantity:
            raise UnoError(
                f"Order quantity exceeds maximum ({self.maximum_order_quantity})",
                ErrorCode.BUSINESS_RULE,
                quantity=quantity,
                maximum_quantity=self.maximum_order_quantity
            )
        
        if quantity > self.inventory_count:
            raise UnoError(
                f"Insufficient inventory: requested {quantity}, available {self.inventory_count}",
                ErrorCode.BUSINESS_RULE,
                requested_quantity=quantity,
                available_quantity=self.inventory_count
            )
        
        # Reserve inventory
        self.inventory_count -= quantity
        await self.save()
        return True
    
    def calculate_tax(self, quantity: int) -> Decimal:
        """
        Calculate tax for a given quantity of this product.
        
        Args:
            quantity: The quantity of products
            
        Returns:
            The calculated tax amount
        """
        if not self.is_taxable:
            return Decimal("0.00")
        
        base_amount = self.price * quantity
        tax_amount = (base_amount * self.tax_rate) / Decimal("100.00")
        return tax_amount.quantize(Decimal("0.01"))
    
    def to_dto(self) -> ProductDTO:
        """Convert to DTO for API responses."""
        return ProductDTO(
            id=self.id,
            name=self.name,
            description=self.description,
            price=self.price,
            sku=self.sku,
            category=self.category,
            inventory_count=self.inventory_count,
            is_active=self.is_active,
            minimum_order_quantity=self.minimum_order_quantity,
            maximum_order_quantity=self.maximum_order_quantity,
            tax_rate=self.tax_rate,
            is_taxable=self.is_taxable,
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class OrderItemDTO(BaseModel):
    """Data transfer object for order item API responses."""
    id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price: Decimal
    discount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    @property
    def subtotal(self) -> Decimal:
        """Calculate the subtotal (before tax)."""
        return (self.unit_price * self.quantity) - self.discount

    @property
    def total(self) -> Decimal:
        """Calculate the total (including tax)."""
        return self.subtotal + self.tax_amount


class OrderItem(UnoObj[OrderItemModel]):
    """Order item business object with domain-specific validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "order_id", "product_id", "quantity", "unit_price"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for order items."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Quantity validation
        if hasattr(self, "quantity") and self.quantity is not None:
            if self.quantity <= 0:
                context.add_error(
                    field="quantity",
                    message="Quantity must be greater than zero",
                    error_code="INVALID_QUANTITY"
                )
        
        # Unit price validation
        if hasattr(self, "unit_price") and self.unit_price is not None:
            if self.unit_price < Decimal("0.00"):
                context.add_error(
                    field="unit_price",
                    message="Unit price cannot be negative",
                    error_code="INVALID_UNIT_PRICE"
                )
        
        # Discount validation
        if hasattr(self, "discount") and self.discount is not None:
            if self.discount < Decimal("0.00"):
                context.add_error(
                    field="discount",
                    message="Discount cannot be negative",
                    error_code="INVALID_DISCOUNT"
                )
            
            # Check if discount exceeds item total
            if hasattr(self, "unit_price") and self.unit_price is not None and hasattr(self, "quantity") and self.quantity is not None:
                item_total = self.unit_price * self.quantity
                if self.discount > item_total:
                    context.add_error(
                        field="discount",
                        message="Discount cannot exceed item total price",
                        error_code="DISCOUNT_EXCEEDS_TOTAL"
                    )
        
        # Tax amount validation
        if hasattr(self, "tax_amount") and self.tax_amount is not None:
            if self.tax_amount < Decimal("0.00"):
                context.add_error(
                    field="tax_amount",
                    message="Tax amount cannot be negative",
                    error_code="INVALID_TAX_AMOUNT"
                )
        
        return context
    
    def calculate_subtotal(self) -> Decimal:
        """Calculate the subtotal (before tax)."""
        return (self.unit_price * self.quantity) - self.discount
    
    def calculate_total(self) -> Decimal:
        """Calculate the total (including tax)."""
        return self.calculate_subtotal() + self.tax_amount
    
    def to_dto(self) -> OrderItemDTO:
        """Convert to DTO for API responses."""
        return OrderItemDTO(
            id=self.id,
            order_id=self.order_id,
            product_id=self.product_id,
            quantity=self.quantity,
            unit_price=self.unit_price,
            discount=self.discount,
            tax_amount=self.tax_amount,
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class OrderDTO(BaseModel):
    """Data transfer object for order API responses."""
    id: str
    customer_id: str
    order_date: datetime
    total_amount: Decimal
    status: str
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_method: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemDTO] = []


class OrderStatus:
    """Enumeration of possible order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus:
    """Enumeration of possible payment statuses."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(UnoObj[OrderModel]):
    """Order business object with domain-specific validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "customer_id", "order_date", "total_amount", "status", "payment_status"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for orders."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Total amount validation
        if hasattr(self, "total_amount") and self.total_amount is not None:
            if self.total_amount < Decimal("0.00"):
                context.add_error(
                    field="total_amount",
                    message="Total amount cannot be negative",
                    error_code="INVALID_TOTAL_AMOUNT"
                )
        
        # Status validation
        if hasattr(self, "status") and self.status:
            valid_statuses = [
                OrderStatus.PENDING,
                OrderStatus.PROCESSING,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED
            ]
            if self.status not in valid_statuses:
                context.add_error(
                    field="status",
                    message=f"Invalid status. Must be one of {', '.join(valid_statuses)}",
                    error_code="INVALID_STATUS"
                )
        
        # Payment status validation
        if hasattr(self, "payment_status") and self.payment_status:
            valid_payment_statuses = [
                PaymentStatus.PENDING,
                PaymentStatus.PAID,
                PaymentStatus.FAILED,
                PaymentStatus.REFUNDED
            ]
            if self.payment_status not in valid_payment_statuses:
                context.add_error(
                    field="payment_status",
                    message=f"Invalid payment status. Must be one of {', '.join(valid_payment_statuses)}",
                    error_code="INVALID_PAYMENT_STATUS"
                )
        
        # Shipping validation
        if hasattr(self, "status") and self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            shipping_fields = [
                "shipping_address", "shipping_city", "shipping_state",
                "shipping_postal_code", "shipping_country", "shipping_method"
            ]
            
            for field in shipping_fields:
                if hasattr(self, field) and not getattr(self, field):
                    context.add_error(
                        field=field,
                        message=f"{field.replace('_', ' ').title()} is required for shipped orders",
                        error_code="MISSING_SHIPPING_INFO"
                    )
        
        return context
    
    # Business methods
    async def update_status(self, new_status: str) -> bool:
        """
        Update the order status.
        
        Args:
            new_status: The new status to set
            
        Returns:
            True if the status was successfully updated
            
        Raises:
            UnoError: If the status transition is invalid
        """
        # Validate new status
        valid_statuses = [
            OrderStatus.PENDING,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED
        ]
        if new_status not in valid_statuses:
            raise UnoError(
                f"Invalid status: {new_status}",
                ErrorCode.VALIDATION_ERROR,
                field="status",
                provided_value=new_status,
                valid_values=valid_statuses
            )
        
        # Validate status transition
        if self.status == OrderStatus.CANCELLED and new_status != OrderStatus.CANCELLED:
            raise UnoError(
                "Cannot change status of a cancelled order",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                requested_status=new_status
            )
        
        if self.status == OrderStatus.DELIVERED and new_status not in [OrderStatus.CANCELLED]:
            raise UnoError(
                "Delivered orders can only be cancelled",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                requested_status=new_status
            )
        
        # Check shipping information for shipped orders
        if new_status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            required_fields = [
                "shipping_address", "shipping_city", "shipping_state",
                "shipping_postal_code", "shipping_country", "shipping_method"
            ]
            
            missing_fields = []
            for field in required_fields:
                if not getattr(self, field, None):
                    missing_fields.append(field)
            
            if missing_fields:
                raise UnoError(
                    "Missing shipping information",
                    ErrorCode.BUSINESS_RULE,
                    missing_fields=missing_fields
                )
        
        # Update status
        self.status = new_status
        await self.save()
        return True
    
    async def update_payment_status(self, payment_status: str) -> bool:
        """
        Update the payment status.
        
        Args:
            payment_status: The new payment status
            
        Returns:
            True if the payment status was successfully updated
            
        Raises:
            UnoError: If the payment status is invalid
        """
        # Validate payment status
        valid_statuses = [
            PaymentStatus.PENDING,
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
            PaymentStatus.REFUNDED
        ]
        if payment_status not in valid_statuses:
            raise UnoError(
                f"Invalid payment status: {payment_status}",
                ErrorCode.VALIDATION_ERROR,
                field="payment_status",
                provided_value=payment_status,
                valid_values=valid_statuses
            )
        
        # Update payment status
        self.payment_status = payment_status
        await self.save()
        return True
    
    def to_dto(self, items: List[OrderItemDTO] = None) -> OrderDTO:
        """
        Convert to DTO for API responses.
        
        Args:
            items: Optional list of order items to include
        """
        return OrderDTO(
            id=self.id,
            customer_id=self.customer_id,
            order_date=self.order_date,
            total_amount=self.total_amount,
            status=self.status,
            shipping_address=self.shipping_address,
            shipping_city=self.shipping_city,
            shipping_state=self.shipping_state,
            shipping_postal_code=self.shipping_postal_code,
            shipping_country=self.shipping_country,
            shipping_method=self.shipping_method,
            payment_method=self.payment_method,
            payment_status=self.payment_status,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            items=items or []
        )


# ===== SERVICE CLASSES =====

class OrderService:
    """Service for handling order operations."""
    
    # For simplicity in testing, we'll skip constructor injection
    
    async def create_order(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        shipping_info: Dict[str, str],
        payment_method: str = None,
        notes: str = None
    ) -> Tuple[Order, List[OrderItem]]:
        """
        Create a new order with the provided items.
        
        Args:
            customer_id: The customer ID
            items: List of items to add to the order
            shipping_info: Shipping information
            payment_method: Optional payment method
            notes: Optional order notes
            
        Returns:
            A tuple containing the created order and its items
            
        Raises:
            UnoError: If there are validation or business rule errors
        """
        # Validate customer
        customer = await self.get_customer(customer_id)
        if not customer:
            raise UnoError(
                f"Customer not found: {customer_id}",
                ErrorCode.RESOURCE_NOT_FOUND,
                resource_type="Customer",
                resource_id=customer_id
            )
        
        if not customer.is_active:
            raise UnoError(
                f"Customer account is inactive: {customer_id}",
                ErrorCode.BUSINESS_RULE,
                customer_id=customer_id
            )
        
        # Validate and reserve products
        order_items = []
        total_amount = Decimal("0.00")
        
        for item_data in items:
            product_id = item_data.get("product_id")
            quantity = item_data.get("quantity", 0)
            
            # Validate product and quantity
            product = await self.get_product(product_id)
            if not product:
                raise UnoError(
                    f"Product not found: {product_id}",
                    ErrorCode.RESOURCE_NOT_FOUND,
                    resource_type="Product",
                    resource_id=product_id
                )
            
            if not product.is_active:
                raise UnoError(
                    f"Product is not available: {product_id}",
                    ErrorCode.BUSINESS_RULE,
                    product_id=product_id
                )
            
            # Check quantity limits
            if quantity < product.minimum_order_quantity:
                raise UnoError(
                    f"Minimum order quantity not met for product {product.name}",
                    ErrorCode.BUSINESS_RULE,
                    product_id=product_id,
                    product_name=product.name,
                    minimum_quantity=product.minimum_order_quantity,
                    requested_quantity=quantity
                )
            
            if product.maximum_order_quantity and quantity > product.maximum_order_quantity:
                raise UnoError(
                    f"Maximum order quantity exceeded for product {product.name}",
                    ErrorCode.BUSINESS_RULE,
                    product_id=product_id,
                    product_name=product.name,
                    maximum_quantity=product.maximum_order_quantity,
                    requested_quantity=quantity
                )
            
            # Reserve inventory
            try:
                await product.reserve_inventory(quantity)
            except UnoError as e:
                # Unreserve any previously reserved inventory
                for item in order_items:
                    product = await self.get_product(item.product_id)
                    if product:
                        product.inventory_count += item.quantity
                        await product.save()
                
                # Re-raise the error
                raise UnoError(
                    f"Could not reserve inventory: {e}",
                    ErrorCode.BUSINESS_RULE,
                    product_id=product_id,
                    product_name=product.name,
                    requested_quantity=quantity,
                    available_quantity=product.inventory_count
                )
            
            # Calculate item price and tax
            unit_price = product.price
            discount = Decimal(item_data.get("discount", "0.00"))
            tax_amount = product.calculate_tax(quantity)
            
            # Create order item
            order_item = OrderItem(
                id=str(uuid.uuid4()),
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                tax_amount=tax_amount
            )
            
            # Validate order item
            validation_context = order_item.validate("edit_schema")
            if validation_context.has_errors():
                # Unreserve inventory
                for item in order_items:
                    product = await self.get_product(item.product_id)
                    if product:
                        product.inventory_count += item.quantity
                        await product.save()
                
                # Also unreserve current product's inventory
                product.inventory_count += quantity
                await product.save()
                
                raise ValidationError(
                    "Invalid order item",
                    ErrorCode.VALIDATION_ERROR,
                    validation_errors=validation_context.errors
                )
            
            # Add item
            order_items.append(order_item)
            
            # Update total amount
            item_total = order_item.calculate_total()
            total_amount += item_total
        
        # Create order
        order = Order(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            order_date=datetime.now(),
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method=payment_method,
            notes=notes,
            **shipping_info
        )
        
        # Validate order
        validation_context = order.validate("edit_schema")
        if validation_context.has_errors():
            # Unreserve inventory
            for item in order_items:
                product = await self.get_product(item.product_id)
                if product:
                    product.inventory_count += item.quantity
                    await product.save()
            
            raise ValidationError(
                "Invalid order",
                ErrorCode.VALIDATION_ERROR,
                validation_errors=validation_context.errors
            )
        
        # Save order
        await order.save()
        
        # Save order items and link to order
        for item in order_items:
            item.order_id = order.id
            await item.save()
        
        # Award loyalty points (simple example: 1 point per $10 spent)
        loyalty_points = int(total_amount / Decimal("10.00"))
        if loyalty_points > 0:
            await customer.add_loyalty_points(loyalty_points)
        
        return order, order_items
    
    async def get_order(self, order_id: str) -> Order:
        """Get an order by ID."""
        return await Order.get(order_id)
    
    async def get_order_items(self, order_id: str) -> List[OrderItem]:
        """Get all items for an order."""
        return await OrderItem.filter({"order_id": order_id})
    
    async def get_customer(self, customer_id: str) -> Customer:
        """Get a customer by ID."""
        return await Customer.get(customer_id)
    
    async def get_product(self, product_id: str) -> Product:
        """Get a product by ID."""
        return await Product.get(product_id)


# ===== API SETUP =====

# Create FastAPI app
app = FastAPI()

# Mock database
customers_db = {}
products_db = {}
orders_db = {}
order_items_db = {}

# Mock customer functions
@patch.object(Customer, 'get')
async def mock_get_customer(id):
    if id in customers_db:
        return customers_db[id]
    return None

@patch.object(Customer, 'filter')
async def mock_filter_customers(filters=None):
    results = list(customers_db.values())
    return results

@patch.object(Customer, 'save')
async def mock_save_customer(self):
    customers_db[self.id] = self
    return self

# Mock product functions
@patch.object(Product, 'get')
async def mock_get_product(id):
    if id in products_db:
        return products_db[id]
    return None

@patch.object(Product, 'filter')
async def mock_filter_products(filters=None):
    results = list(products_db.values())
    if filters and hasattr(filters, 'get'):
        category = filters.get('category')
        if category:
            results = [p for p in results if p.category == category]
    return results

@patch.object(Product, 'save')
async def mock_save_product(self):
    products_db[self.id] = self
    return self

# Mock order functions
@patch.object(Order, 'get')
async def mock_get_order(id):
    if id in orders_db:
        return orders_db[id]
    return None

@patch.object(Order, 'filter')
async def mock_filter_orders(filters=None):
    results = list(orders_db.values())
    if filters and hasattr(filters, 'get'):
        customer_id = filters.get('customer_id')
        if customer_id:
            results = [o for o in results if o.customer_id == customer_id]
        
        status = filters.get('status')
        if status:
            results = [o for o in results if o.status == status]
    return results

@patch.object(Order, 'save')
async def mock_save_order(self):
    orders_db[self.id] = self
    return self

# Mock order item functions
@patch.object(OrderItem, 'get')
async def mock_get_order_item(id):
    if id in order_items_db:
        return order_items_db[id]
    return None

@patch.object(OrderItem, 'filter')
async def mock_filter_order_items(filters=None):
    results = list(order_items_db.values())
    if filters and hasattr(filters, 'get'):
        order_id = filters.get('order_id')
        if order_id:
            results = [i for i in results if i.order_id == order_id]
    return results

@patch.object(OrderItem, 'save')
async def mock_save_order_item(self):
    order_items_db[self.id] = self
    return self

# Dependencies
async def get_order_service():
    return OrderService()

# API endpoints

@app.post("/orders")
async def create_order(
    data: dict,
    order_service: OrderService = Depends(get_order_service)
):
    try:
        customer_id = data.get("customer_id")
        items = data.get("items", [])
        shipping_info = data.get("shipping_info", {})
        payment_method = data.get("payment_method")
        notes = data.get("notes")
        
        order, order_items = await order_service.create_order(
            customer_id=customer_id,
            items=items,
            shipping_info=shipping_info,
            payment_method=payment_method,
            notes=notes
        )
        
        # Convert to DTOs for response
        order_dto = order.to_dto()
        order_dto.items = [item.to_dto() for item in order_items]
        
        return {
            "status": "success",
            "data": json.loads(order_dto.model_dump_json())
        }
    except ValidationError as e:
        return {
            "status": "error",
            "message": str(e),
            "errors": e.validation_errors,
            "code": e.error_code
        }
    except UnoError as e:
        return {
            "status": "error",
            "message": str(e),
            "code": e.error_code
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    data: dict,
    order_service: OrderService = Depends(get_order_service)
):
    try:
        new_status = data.get("status")
        
        order = await order_service.get_order(order_id)
        if not order:
            return {
                "status": "error",
                "message": f"Order not found: {order_id}",
                "code": ErrorCode.RESOURCE_NOT_FOUND
            }
        
        await order.update_status(new_status)
        
        order_items = await order_service.get_order_items(order_id)
        order_dto = order.to_dto([item.to_dto() for item in order_items])
        
        return {
            "status": "success",
            "data": json.loads(order_dto.model_dump_json())
        }
    except UnoError as e:
        return {
            "status": "error",
            "message": str(e),
            "code": e.error_code
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.put("/orders/{order_id}/payment")
async def update_payment_status(
    order_id: str,
    data: dict,
    order_service: OrderService = Depends(get_order_service)
):
    try:
        payment_status = data.get("payment_status")
        
        order = await order_service.get_order(order_id)
        if not order:
            return {
                "status": "error",
                "message": f"Order not found: {order_id}",
                "code": ErrorCode.RESOURCE_NOT_FOUND
            }
        
        await order.update_payment_status(payment_status)
        
        order_items = await order_service.get_order_items(order_id)
        order_dto = order.to_dto([item.to_dto() for item in order_items])
        
        return {
            "status": "success",
            "data": json.loads(order_dto.model_dump_json())
        }
    except UnoError as e:
        return {
            "status": "error",
            "message": str(e),
            "code": e.error_code
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service)
):
    try:
        order = await order_service.get_order(order_id)
        if not order:
            return {
                "status": "error",
                "message": f"Order not found: {order_id}",
                "code": ErrorCode.RESOURCE_NOT_FOUND
            }
        
        order_items = await order_service.get_order_items(order_id)
        order_dto = order.to_dto([item.to_dto() for item in order_items])
        
        return {
            "status": "success",
            "data": json.loads(order_dto.model_dump_json())
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ===== TEST SETUP =====

@pytest.fixture
def test_client():
    # Create test client
    client = TestClient(app)
    
    # Reset databases before each test
    customers_db.clear()
    products_db.clear()
    orders_db.clear()
    order_items_db.clear()
    
    # Seed with test data
    seed_test_data()
    
    return client

def seed_test_data():
    """Seed the test databases with sample data."""
    # Create sample customers
    customers = [
        Customer(
            id="cust-1",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1-555-123-4567",
            address="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94105",
            country="USA",
            is_active=True,
            loyalty_points=100
        ),
        Customer(
            id="cust-2",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="+1-555-987-6543",
            address="456 Oak Ave",
            city="Los Angeles",
            state="CA",
            postal_code="90001",
            country="USA",
            is_active=True,
            loyalty_points=50
        ),
        Customer(
            id="cust-3",
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@example.com",
            phone="+1-555-555-5555",
            address="789 Elm St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA",
            is_active=False,
            loyalty_points=25
        )
    ]
    
    for customer in customers:
        customers_db[customer.id] = customer
    
    # Create sample products
    products = [
        Product(
            id="prod-1",
            name="Laptop",
            description="High-performance laptop",
            price=Decimal("999.99"),
            sku="ELE-12345",
            category="Electronics",
            inventory_count=50,
            is_active=True,
            minimum_order_quantity=1,
            maximum_order_quantity=5,
            tax_rate=Decimal("8.50"),
            is_taxable=True
        ),
        Product(
            id="prod-2",
            name="T-Shirt",
            description="Cotton T-shirt",
            price=Decimal("19.99"),
            sku="CLO-67890",
            category="Clothing",
            inventory_count=200,
            is_active=True,
            minimum_order_quantity=1,
            maximum_order_quantity=10,
            tax_rate=Decimal("5.00"),
            is_taxable=True
        ),
        Product(
            id="prod-3",
            name="Book",
            description="Bestselling novel",
            price=Decimal("14.99"),
            sku="BOO-24680",
            category="Books",
            inventory_count=100,
            is_active=True,
            minimum_order_quantity=1,
            tax_rate=Decimal("0.00"),
            is_taxable=False
        ),
        Product(
            id="prod-4",
            name="Coffee Maker",
            description="Automatic coffee maker",
            price=Decimal("89.99"),
            sku="HOM-13579",
            category="Home",
            inventory_count=30,
            is_active=True,
            minimum_order_quantity=1,
            maximum_order_quantity=3,
            tax_rate=Decimal("7.25"),
            is_taxable=True
        ),
        Product(
            id="prod-5",
            name="Gaming Console",
            description="Next-gen gaming console",
            price=Decimal("499.99"),
            sku="ELE-98765",
            category="Electronics",
            inventory_count=10,
            is_active=True,
            minimum_order_quantity=1,
            maximum_order_quantity=1,
            tax_rate=Decimal("8.50"),
            is_taxable=True
        ),
        Product(
            id="prod-6",
            name="Headphones",
            description="Noise-cancelling headphones",
            price=Decimal("149.99"),
            sku="ELE-54321",
            category="Electronics",
            inventory_count=0,  # Out of stock
            is_active=True,
            minimum_order_quantity=1,
            tax_rate=Decimal("8.50"),
            is_taxable=True
        ),
        Product(
            id="prod-7",
            name="Limited Edition Watch",
            description="Collector's watch",
            price=Decimal("1299.99"),
            sku="CLO-11111",
            category="Clothing",
            inventory_count=5,
            is_active=False,  # Not active
            minimum_order_quantity=1,
            tax_rate=Decimal("5.00"),
            is_taxable=True
        )
    ]
    
    for product in products:
        products_db[product.id] = product
    
    # Create a sample order with items
    order = Order(
        id="order-1",
        customer_id="cust-1",
        order_date=datetime.now() - timedelta(days=3),
        total_amount=Decimal("1159.98"),
        status=OrderStatus.PROCESSING,
        shipping_address="123 Main St",
        shipping_city="San Francisco",
        shipping_state="CA",
        shipping_postal_code="94105",
        shipping_country="USA",
        shipping_method="UPS",
        payment_method="Credit Card",
        payment_status=PaymentStatus.PAID
    )
    orders_db[order.id] = order
    
    order_items = [
        OrderItem(
            id="item-1",
            order_id="order-1",
            product_id="prod-1",
            quantity=1,
            unit_price=Decimal("999.99"),
            discount=Decimal("0.00"),
            tax_amount=Decimal("85.00")
        ),
        OrderItem(
            id="item-2",
            order_id="order-1",
            product_id="prod-3",
            quantity=5,
            unit_price=Decimal("14.99"),
            discount=Decimal("0.00"),
            tax_amount=Decimal("0.00")
        )
    ]
    
    for item in order_items:
        order_items_db[item.id] = item


# ===== TESTS =====

def test_create_order_success(test_client):
    """Test creating an order with valid data."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-2", "quantity": 3, "discount": "5.00"},
            {"product_id": "prod-3", "quantity": 2, "discount": "0.00"}
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        },
        "payment_method": "Credit Card"
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["customer_id"] == "cust-1"
    assert data["data"]["status"] == "pending"
    assert data["data"]["payment_status"] == "pending"
    assert len(data["data"]["items"]) == 2
    
    # Check inventory was reduced
    product = products_db["prod-2"]
    assert product.inventory_count == 197  # 200 - 3 = 197
    
    product = products_db["prod-3"]
    assert product.inventory_count == 98   # 100 - 2 = 98
    
    # Check loyalty points were awarded (simple calculation: $1 = 0.1 points)
    customer = customers_db["cust-1"]
    assert customer.loyalty_points > 100  # Started with 100, should have more now

def test_create_order_inactive_customer(test_client):
    """Test creating an order with an inactive customer."""
    order_data = {
        "customer_id": "cust-3",  # Inactive customer
        "items": [
            {"product_id": "prod-2", "quantity": 3}
        ],
        "shipping_info": {
            "shipping_address": "789 Elm St",
            "shipping_city": "New York",
            "shipping_state": "NY",
            "shipping_postal_code": "10001",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200  # API always returns 200 but with error status
    data = response.json()
    assert data["status"] == "error"
    assert "Customer account is inactive" in data["message"]
    
    # Verify inventory was not changed
    product = products_db["prod-2"]
    assert product.inventory_count == 200  # Should still have original inventory

def test_create_order_inactive_product(test_client):
    """Test creating an order with an inactive product."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-7", "quantity": 1}  # Inactive product
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "not available" in data["message"]

def test_create_order_insufficient_inventory(test_client):
    """Test creating an order with insufficient inventory."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-5", "quantity": 20}  # Only 10 in stock
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "inventory" in data["message"]

def test_create_order_out_of_stock(test_client):
    """Test creating an order with an out-of-stock product."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-6", "quantity": 1}  # 0 in stock
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "inventory" in data["message"]

def test_create_order_below_minimum_quantity(test_client):
    """Test creating an order below minimum order quantity."""
    # Create a product with minimum order quantity of 5
    product = Product(
        id="prod-min-qty",
        name="Bulk Item",
        description="Must order at least 5",
        price=Decimal("9.99"),
        sku="BLK-12345",
        category="Home",
        inventory_count=100,
        is_active=True,
        minimum_order_quantity=5,
        tax_rate=Decimal("7.25"),
        is_taxable=True
    )
    products_db[product.id] = product
    
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-min-qty", "quantity": 3}  # Below minimum of 5
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Minimum order quantity" in data["message"]

def test_create_order_above_maximum_quantity(test_client):
    """Test creating an order above maximum order quantity."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-2", "quantity": 15}  # Above maximum of 10
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Maximum order quantity" in data["message"]

def test_update_order_status_success(test_client):
    """Test successfully updating an order status."""
    # Update from processing to shipped
    update_data = {
        "status": OrderStatus.SHIPPED
    }
    
    response = test_client.put("/orders/order-1/status", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["status"] == OrderStatus.SHIPPED

def test_update_cancelled_order_status(test_client):
    """Test attempting to update a cancelled order."""
    # First cancel the order
    update_data = {
        "status": OrderStatus.CANCELLED
    }
    
    response = test_client.put("/orders/order-1/status", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["status"] == OrderStatus.CANCELLED
    
    # Now try to update it to shipped
    update_data = {
        "status": OrderStatus.SHIPPED
    }
    
    response = test_client.put("/orders/order-1/status", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Cannot change status of a cancelled order" in data["message"]

def test_update_to_shipped_without_shipping_info(test_client):
    """Test updating to shipped status without shipping info."""
    # Create an order without shipping info
    order = Order(
        id="order-no-shipping",
        customer_id="cust-1",
        order_date=datetime.now(),
        total_amount=Decimal("100.00"),
        status=OrderStatus.PENDING,
        payment_method="Credit Card",
        payment_status=PaymentStatus.PAID
    )
    orders_db[order.id] = order
    
    # Try to update to shipped
    update_data = {
        "status": OrderStatus.SHIPPED
    }
    
    response = test_client.put("/orders/order-no-shipping/status", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Missing shipping information" in data["message"]

def test_update_payment_status_success(test_client):
    """Test successfully updating payment status."""
    update_data = {
        "payment_status": PaymentStatus.PAID
    }
    
    response = test_client.put("/orders/order-1/payment", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["payment_status"] == PaymentStatus.PAID

def test_update_payment_status_invalid(test_client):
    """Test updating payment status with invalid value."""
    update_data = {
        "payment_status": "invalid-status"
    }
    
    response = test_client.put("/orders/order-1/payment", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Invalid payment status" in data["message"]

def test_get_order_success(test_client):
    """Test getting an order with all its items."""
    response = test_client.get("/orders/order-1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["id"] == "order-1"
    assert len(data["data"]["items"]) == 2

def test_get_nonexistent_order(test_client):
    """Test getting a non-existent order."""
    response = test_client.get("/orders/non-existent-order")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "not found" in data["message"]

def test_complex_order_with_multiple_products(test_client):
    """Test creating a complex order with multiple products."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-1", "quantity": 1, "discount": "100.00"},  # Laptop with discount
            {"product_id": "prod-2", "quantity": 2, "discount": "0.00"},    # T-shirts
            {"product_id": "prod-3", "quantity": 3, "discount": "5.00"},    # Books with discount
            {"product_id": "prod-4", "quantity": 1, "discount": "0.00"}     # Coffee maker
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA",
            "shipping_method": "FedEx"
        },
        "payment_method": "PayPal",
        "notes": "Gift wrap items separately"
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Check order details
    assert data["data"]["customer_id"] == "cust-1"
    assert data["data"]["payment_method"] == "PayPal"
    assert data["data"]["notes"] == "Gift wrap items separately"
    assert data["data"]["shipping_method"] == "FedEx"
    
    # Check items
    assert len(data["data"]["items"]) == 4
    
    # Check inventory was reduced correctly
    assert products_db["prod-1"].inventory_count == 49  # 50 - 1 = 49
    assert products_db["prod-2"].inventory_count == 198  # 200 - 2 = 198
    assert products_db["prod-3"].inventory_count == 97  # 100 - 3 = 97
    assert products_db["prod-4"].inventory_count == 29  # 30 - 1 = 29

def test_order_item_validation_negative_quantity(test_client):
    """Test validation fails for negative quantity."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-2", "quantity": -1}  # Negative quantity
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Quantity must be a positive number" in data["message"]

def test_order_item_validation_excessive_discount(test_client):
    """Test validation fails when discount exceeds item total."""
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-2", "quantity": 1, "discount": "50.00"}  # Price is 19.99, discount is 50.00
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    # This would fail in the OrderService.create_order method when validating order items
    assert "error" in data["status"]

def test_cross_entity_validation(test_client):
    """Test validation involving multiple entities."""
    # Create a new product with specific constraints
    product = Product(
        id="prod-cross-entity",
        name="Special Item",
        description="Only for premium customers with 200+ loyalty points",
        price=Decimal("1000.00"),
        sku="SPL-12345",
        category="Electronics",
        inventory_count=10,
        is_active=True,
        minimum_order_quantity=1,
        tax_rate=Decimal("8.50"),
        is_taxable=True
    )
    products_db[product.id] = product
    
    # Modify order service create_order method to check loyalty points
    original_create_order = OrderService.create_order
    
    async def patched_create_order(self, customer_id, items, shipping_info, payment_method=None, notes=None):
        # Check if ordering the special product
        for item_data in items:
            if item_data.get("product_id") == "prod-cross-entity":
                # Get customer
                customer = await self.get_customer(customer_id)
                if customer and customer.loyalty_points < 200:
                    raise UnoError(
                        "Special items require 200+ loyalty points",
                        ErrorCode.BUSINESS_RULE,
                        customer_id=customer_id,
                        product_id="prod-cross-entity",
                        required_points=200,
                        current_points=customer.loyalty_points
                    )
        
        # Call original method
        return await original_create_order(self, customer_id, items, shipping_info, payment_method, notes)
    
    # Patch the method
    OrderService.create_order = patched_create_order
    
    # Try to order with insufficient loyalty points
    order_data = {
        "customer_id": "cust-1",  # Has 100 points
        "items": [
            {"product_id": "prod-cross-entity", "quantity": 1}
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Special items require 200+ loyalty points" in data["message"]
    
    # Restore original method
    OrderService.create_order = original_create_order

def test_order_with_transaction_rollback(test_client):
    """Test order creation rolls back inventory changes on failure."""
    # Create a product that will pass initial validation but fail later
    product1 = Product(
        id="prod-rollback-1",
        name="Valid Product",
        description="This product will pass validation",
        price=Decimal("50.00"),
        sku="RBK-12345",
        category="Electronics",
        inventory_count=20,
        is_active=True,
        minimum_order_quantity=1,
        tax_rate=Decimal("8.50"),
        is_taxable=True
    )
    products_db[product1.id] = product1
    
    # Product with invalid tax rate that will fail validation
    product2 = Product(
        id="prod-rollback-2",
        name="Invalid Product",
        description="This product will cause the order to fail",
        price=Decimal("25.00"),
        sku="RBK-67890",
        category="Electronics",
        inventory_count=10,
        is_active=True,
        minimum_order_quantity=1,
        tax_rate=Decimal("150.00"),  # Invalid tax rate over 100%
        is_taxable=True
    )
    products_db[product2.id] = product2
    
    # Create order with both products
    order_data = {
        "customer_id": "cust-1",
        "items": [
            {"product_id": "prod-rollback-1", "quantity": 5},  # This will pass initially
            {"product_id": "prod-rollback-2", "quantity": 3}   # This will fail
        ],
        "shipping_info": {
            "shipping_address": "123 Main St",
            "shipping_city": "San Francisco",
            "shipping_state": "CA",
            "shipping_postal_code": "94105",
            "shipping_country": "USA"
        }
    }
    
    # Store original inventory
    original_inventory1 = product1.inventory_count
    original_inventory2 = product2.inventory_count
    
    response = test_client.post("/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    
    # Verify inventory was restored
    assert products_db["prod-rollback-1"].inventory_count == original_inventory1
    assert products_db["prod-rollback-2"].inventory_count == original_inventory2

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])