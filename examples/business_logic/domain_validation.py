"""
Example implementation of domain-specific validation rules.

This module demonstrates advanced validation techniques for business objects
using the UnoObj framework.
"""

from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from datetime import datetime, date, timedelta
import re

from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from uno.core.errors import ValidationContext, UnoError, ErrorCode
from uno.core.errors.validation import ValidationError


# ===== PRODUCT DOMAIN =====

class ProductModel(UnoModel):
    """Database model for products."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    sku: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, unique=True)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    tags: Mapped[PostgresTypes.StringArray] = mapped_column(nullable=True)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)
    min_order_quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    max_order_quantity: Mapped[int] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    release_date: Mapped[date] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


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
        
        # Tags validation
        if hasattr(self, "tags") and self.tags:
            for i, tag in enumerate(self.tags):
                if not tag or len(tag) > 50:
                    context.add_error(
                        field=f"tags.{i}",
                        message="Tags must be non-empty and less than 50 characters",
                        error_code="INVALID_TAG"
                    )
        
        # Order quantity validation
        if (hasattr(self, "min_order_quantity") and hasattr(self, "max_order_quantity") and 
            self.min_order_quantity is not None and self.max_order_quantity is not None):
            if self.min_order_quantity < 1:
                context.add_error(
                    field="min_order_quantity",
                    message="Minimum order quantity must be at least 1",
                    error_code="INVALID_MIN_ORDER"
                )
            
            if self.max_order_quantity < self.min_order_quantity:
                context.add_error(
                    field="max_order_quantity",
                    message="Maximum order quantity must be greater than or equal to minimum order quantity",
                    error_code="INVALID_MAX_ORDER"
                )
        
        # Release date validation - cannot be in the past unless product exists
        if hasattr(self, "release_date") and self.release_date:
            today = date.today()
            if self.release_date < today and not self.id:
                context.add_error(
                    field="release_date",
                    message="Release date cannot be in the past for new products",
                    error_code="INVALID_RELEASE_DATE"
                )
        
        return context
    
    # Business methods
    async def reserve_inventory(self, quantity: int) -> bool:
        """Reserve inventory for an order."""
        # Validate quantity
        if quantity < self.min_order_quantity:
            raise UnoError(
                f"Quantity {quantity} is below minimum order quantity {self.min_order_quantity}",
                ErrorCode.VALIDATION_ERROR,
                field="quantity",
                min_order_quantity=self.min_order_quantity
            )
        
        if self.max_order_quantity and quantity > self.max_order_quantity:
            raise UnoError(
                f"Quantity {quantity} exceeds maximum order quantity {self.max_order_quantity}",
                ErrorCode.VALIDATION_ERROR,
                field="quantity",
                max_order_quantity=self.max_order_quantity
            )
        
        # Check inventory
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
    
    async def release_inventory(self, quantity: int) -> bool:
        """Release previously reserved inventory."""
        self.inventory_count += quantity
        await self.save()
        return True


# ===== CUSTOMER DOMAIN =====

class CustomerModel(UnoModel):
    """Database model for customers."""
    
    __tablename__ = "customers"
    
    first_name: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    last_name: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
    phone: Mapped[PostgresTypes.String20] = mapped_column(nullable=True)
    date_of_birth: Mapped[date] = mapped_column(nullable=True)
    address_line1: Mapped[PostgresTypes.String255] = mapped_column(nullable=True)
    address_line2: Mapped[PostgresTypes.String255] = mapped_column(nullable=True)
    city: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    state: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    postal_code: Mapped[PostgresTypes.String20] = mapped_column(nullable=True)
    country: Mapped[PostgresTypes.String2] = mapped_column(nullable=True)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    verification_date: Mapped[datetime] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class Customer(UnoObj[CustomerModel]):
    """Customer business object with domain-specific validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at", "verification_date"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "first_name", "last_name", "email", "is_verified"
        }),
        "address_schema": UnoSchemaConfig(include_fields={
            "id", "first_name", "last_name", "address_line1", "address_line2", "city", 
            "state", "postal_code", "country"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for customers."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Email validation
        if hasattr(self, "email") and self.email:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, self.email):
                context.add_error(
                    field="email",
                    message="Invalid email format",
                    error_code="INVALID_EMAIL"
                )
        
        # Phone validation
        if hasattr(self, "phone") and self.phone:
            # Strip all non-numeric characters for validation
            digits_only = re.sub(r"\D", "", self.phone)
            if len(digits_only) < 10 or len(digits_only) > 15:
                context.add_error(
                    field="phone",
                    message="Phone number must contain between 10 and 15 digits",
                    error_code="INVALID_PHONE"
                )
        
        # Date of birth validation - must be at least 18 years old
        if hasattr(self, "date_of_birth") and self.date_of_birth:
            today = date.today()
            age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            if age < 18:
                context.add_error(
                    field="date_of_birth",
                    message="Customer must be at least 18 years old",
                    error_code="UNDERAGE_CUSTOMER"
                )
            elif self.date_of_birth > today:
                context.add_error(
                    field="date_of_birth",
                    message="Date of birth cannot be in the future",
                    error_code="INVALID_DATE_OF_BIRTH"
                )
        
        # Country validation
        if hasattr(self, "country") and self.country:
            # ISO 3166-1 alpha-2 country code validation (simplified)
            valid_countries = ["US", "CA", "GB", "AU", "DE", "FR", "JP", "CN", "IN", "BR"]
            if self.country not in valid_countries:
                context.add_error(
                    field="country",
                    message=f"Invalid country code. Must be one of {', '.join(valid_countries)}",
                    error_code="INVALID_COUNTRY"
                )
        
        # Postal code validation based on country
        if hasattr(self, "postal_code") and hasattr(self, "country") and self.postal_code and self.country:
            if self.country == "US" and not re.match(r"^\d{5}(-\d{4})?$", self.postal_code):
                context.add_error(
                    field="postal_code",
                    message="US ZIP code must be in format 12345 or 12345-1234",
                    error_code="INVALID_POSTAL_CODE"
                )
            elif self.country == "CA" and not re.match(r"^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$", self.postal_code):
                context.add_error(
                    field="postal_code",
                    message="Canadian postal code must be in format A1A 1A1",
                    error_code="INVALID_POSTAL_CODE"
                )
            elif self.country == "GB" and not re.match(r"^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$", self.postal_code, re.IGNORECASE):
                context.add_error(
                    field="postal_code",
                    message="UK postal code must be in valid format (e.g., SW1A 1AA)",
                    error_code="INVALID_POSTAL_CODE"
                )
        
        # State validation for US addresses
        if (hasattr(self, "state") and hasattr(self, "country") and 
            self.state and self.country and self.country == "US"):
            us_states = [
                "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
                "DC", "PR", "VI"
            ]
            if self.state not in us_states:
                context.add_error(
                    field="state",
                    message=f"Invalid US state code. Must be one of {', '.join(us_states)}",
                    error_code="INVALID_STATE"
                )
        
        # Verification date must be set if is_verified is True
        if hasattr(self, "is_verified") and hasattr(self, "verification_date"):
            if self.is_verified and not self.verification_date:
                context.add_error(
                    field="verification_date",
                    message="Verification date is required when customer is verified",
                    error_code="MISSING_VERIFICATION_DATE"
                )
        
        return context
    
    # Business methods
    async def verify(self) -> bool:
        """Mark customer as verified."""
        self.is_verified = True
        self.verification_date = datetime.now()
        await self.save()
        return True
    
    async def update_address(self, 
                            address_line1: str, 
                            city: str, 
                            state: str, 
                            postal_code: str, 
                            country: str,
                            address_line2: Optional[str] = None) -> bool:
        """Update customer's address."""
        # Create temp object for validation
        temp_customer = Customer(
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country
        )
        
        # Validate using the address schema
        validation_context = temp_customer.validate("address_schema")
        validation_context.raise_if_errors()
        
        # Update address fields
        self.address_line1 = address_line1
        self.address_line2 = address_line2
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
        
        # Save changes
        await self.save()
        return True


# ===== ORDER DOMAIN =====

class OrderModel(UnoModel):
    """Database model for orders."""
    
    __tablename__ = "orders"
    
    customer_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=False)
    order_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    status: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, default="pending")
    shipping_address_line1: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    shipping_address_line2: Mapped[PostgresTypes.String255] = mapped_column(nullable=True)
    shipping_city: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    shipping_state: Mapped[PostgresTypes.String50] = mapped_column(nullable=False)
    shipping_postal_code: Mapped[PostgresTypes.String20] = mapped_column(nullable=False)
    shipping_country: Mapped[PostgresTypes.String2] = mapped_column(nullable=False)
    billing_address_line1: Mapped[PostgresTypes.String255] = mapped_column(nullable=True)
    billing_address_line2: Mapped[PostgresTypes.String255] = mapped_column(nullable=True)
    billing_city: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    billing_state: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    billing_postal_code: Mapped[PostgresTypes.String20] = mapped_column(nullable=True)
    billing_country: Mapped[PostgresTypes.String2] = mapped_column(nullable=True)
    subtotal: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    tax: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False, default=0)
    shipping_cost: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False, default=0)
    total: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    payment_method: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    payment_status: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    tracking_number: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    notes: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class OrderItemModel(UnoModel):
    """Database model for order items."""
    
    __tablename__ = "order_items"
    
    order_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=False)
    product_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    subtotal: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class OrderItem(UnoObj[OrderItemModel]):
    """Order item business object."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "order_id", "product_id", "quantity", "unit_price", "subtotal"
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
            if self.unit_price <= Decimal("0.00"):
                context.add_error(
                    field="unit_price",
                    message="Unit price must be greater than zero",
                    error_code="INVALID_UNIT_PRICE"
                )
        
        # Subtotal validation
        if (hasattr(self, "quantity") and hasattr(self, "unit_price") and 
            hasattr(self, "subtotal") and self.quantity is not None and 
            self.unit_price is not None and self.subtotal is not None):
            expected_subtotal = self.quantity * self.unit_price
            if abs(self.subtotal - expected_subtotal) > Decimal("0.01"):
                context.add_error(
                    field="subtotal",
                    message=f"Subtotal {self.subtotal} does not match quantity * unit_price = {expected_subtotal}",
                    error_code="INVALID_SUBTOTAL"
                )
        
        return context


class Order(UnoObj[OrderModel]):
    """Order business object with domain-specific validation."""
    
    # Order status constants
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_RETURNED = "returned"
    
    # Payment status constants
    PAYMENT_PENDING = "pending"
    PAYMENT_AUTHORIZED = "authorized"
    PAYMENT_PAID = "paid"
    PAYMENT_REFUNDED = "refunded"
    PAYMENT_FAILED = "failed"
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={
            "created_at", "updated_at", "order_date"
        }),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "customer_id", "order_date", "status", "total", "payment_status"
        }),
        "shipping_schema": UnoSchemaConfig(include_fields={
            "id", "shipping_address_line1", "shipping_address_line2", 
            "shipping_city", "shipping_state", "shipping_postal_code", 
            "shipping_country", "shipping_cost", "tracking_number"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for orders."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Status validation
        if hasattr(self, "status") and self.status:
            valid_statuses = [
                self.STATUS_PENDING, self.STATUS_CONFIRMED, self.STATUS_PROCESSING,
                self.STATUS_SHIPPED, self.STATUS_DELIVERED, self.STATUS_CANCELLED,
                self.STATUS_RETURNED
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
                self.PAYMENT_PENDING, self.PAYMENT_AUTHORIZED, self.PAYMENT_PAID,
                self.PAYMENT_REFUNDED, self.PAYMENT_FAILED
            ]
            if self.payment_status not in valid_payment_statuses:
                context.add_error(
                    field="payment_status",
                    message=f"Invalid payment status. Must be one of {', '.join(valid_payment_statuses)}",
                    error_code="INVALID_PAYMENT_STATUS"
                )
        
        # Total calculation validation
        if (hasattr(self, "subtotal") and hasattr(self, "tax") and 
            hasattr(self, "shipping_cost") and hasattr(self, "total") and
            self.subtotal is not None and self.tax is not None and 
            self.shipping_cost is not None and self.total is not None):
            expected_total = self.subtotal + self.tax + self.shipping_cost
            if abs(self.total - expected_total) > Decimal("0.01"):
                context.add_error(
                    field="total",
                    message=f"Total {self.total} does not match subtotal + tax + shipping = {expected_total}",
                    error_code="INVALID_TOTAL"
                )
        
        # Shipping address validation
        shipping_context = context.nested("shipping")
        
        # Country validation
        if hasattr(self, "shipping_country") and self.shipping_country:
            valid_shipping_countries = ["US", "CA", "GB"]  # Example limited shipping countries
            if self.shipping_country not in valid_shipping_countries:
                shipping_context.add_error(
                    field="country",
                    message=f"We don't ship to {self.shipping_country}. Available countries: {', '.join(valid_shipping_countries)}",
                    error_code="SHIPPING_COUNTRY_NOT_SUPPORTED"
                )
        
        # Payment method required for confirmed status
        if (hasattr(self, "status") and hasattr(self, "payment_method") and 
            self.status == self.STATUS_CONFIRMED and not self.payment_method):
            context.add_error(
                field="payment_method",
                message="Payment method is required for confirmed orders",
                error_code="MISSING_PAYMENT_METHOD"
            )
        
        # Tracking number required for shipped status
        if (hasattr(self, "status") and hasattr(self, "tracking_number") and 
            self.status == self.STATUS_SHIPPED and not self.tracking_number):
            context.add_error(
                field="tracking_number",
                message="Tracking number is required for shipped orders",
                error_code="MISSING_TRACKING_NUMBER"
            )
        
        return context
    
    # Business methods
    async def calculate_totals(self, items: List[OrderItem]) -> None:
        """Calculate order totals based on items."""
        self.subtotal = sum(item.subtotal for item in items)
        
        # Tax calculation (simplified - 10% for US, 20% for GB, 5% for others)
        tax_rates = {"US": Decimal("0.10"), "GB": Decimal("0.20")}
        tax_rate = tax_rates.get(self.shipping_country, Decimal("0.05"))
        self.tax = self.subtotal * tax_rate
        
        # Shipping cost calculation (simplified)
        base_shipping = Decimal("10.00")
        if self.shipping_country != "US":
            base_shipping = Decimal("25.00")
        self.shipping_cost = base_shipping
        
        # Calculate total
        self.total = self.subtotal + self.tax + self.shipping_cost
    
    async def confirm(self) -> bool:
        """Confirm the order."""
        if self.status != self.STATUS_PENDING:
            raise UnoError(
                f"Cannot confirm order that is not pending (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_PENDING
            )
        
        if not self.payment_method:
            raise UnoError(
                "Payment method is required to confirm order",
                ErrorCode.VALIDATION_ERROR,
                field="payment_method"
            )
        
        # Update status
        self.status = self.STATUS_CONFIRMED
        await self.save()
        return True
    
    async def ship(self, tracking_number: str) -> bool:
        """Mark order as shipped."""
        if self.status != self.STATUS_CONFIRMED and self.status != self.STATUS_PROCESSING:
            raise UnoError(
                f"Cannot ship order that is not confirmed or processing (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=[self.STATUS_CONFIRMED, self.STATUS_PROCESSING]
            )
        
        # Update status
        self.status = self.STATUS_SHIPPED
        self.tracking_number = tracking_number
        await self.save()
        return True
    
    async def cancel(self, reason: str = "") -> bool:
        """Cancel the order."""
        if self.status in [self.STATUS_SHIPPED, self.STATUS_DELIVERED]:
            raise UnoError(
                f"Cannot cancel order that has been {self.status}",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status
            )
        
        # Update status
        self.status = self.STATUS_CANCELLED
        self.notes = f"Cancellation reason: {reason}" + (f"\n{self.notes}" if self.notes else "")
        await self.save()
        return True


# ===== INTEGRATION TESTING =====

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_product_validation():
    """Test product domain validation."""
    # Test case 1: Valid product
    product = Product(
        name="Test Product",
        description="Test description",
        price=Decimal("29.99"),
        sku="ABC-12345",
        category="Electronics",
        tags=["test", "product", "electronics"],
        inventory_count=100,
        min_order_quantity=1,
        max_order_quantity=10,
        is_active=True,
        release_date=date.today() + timedelta(days=30)
    )
    
    # Validate product
    validation_context = product.validate("edit_schema")
    assert not validation_context.has_errors()
    
    # Test case 2: Invalid product
    invalid_product = Product(
        name="Invalid Product",
        price=Decimal("-10.00"),  # Invalid price
        sku="invalid-sku",  # Invalid SKU format
        category="Electronics",
        tags=["", "very-long-tag-that-exceeds-the-fifty-character-limit-for-tags"],  # Invalid tags
        inventory_count=100,
        min_order_quantity=0,  # Invalid min order
        max_order_quantity=5,  # Max < Min
        is_active=True,
        release_date=date.today() - timedelta(days=30)  # Past release date
    )
    
    # Validate product
    validation_context = invalid_product.validate("edit_schema")
    assert validation_context.has_errors()
    
    # Check specific errors
    errors = validation_context.errors
    error_fields = [error["field"] for error in errors]
    
    assert "price" in error_fields
    assert "sku" in error_fields
    assert "tags.0" in error_fields
    assert "tags.1" in error_fields
    assert "min_order_quantity" in error_fields
    assert "max_order_quantity" in error_fields
    assert "release_date" in error_fields

@pytest.mark.asyncio
async def test_customer_validation():
    """Test customer domain validation."""
    # Test case 1: Valid customer
    customer = Customer(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-123-4567",
        date_of_birth=date(1980, 1, 1),
        address_line1="123 Main St",
        city="Anytown",
        state="CA",
        postal_code="12345",
        country="US",
        is_verified=False
    )
    
    # Validate customer
    validation_context = customer.validate("edit_schema")
    assert not validation_context.has_errors()
    
    # Test case 2: Invalid customer
    invalid_customer = Customer(
        first_name="Jane",
        last_name="Doe",
        email="invalid-email",  # Invalid email
        phone="123",  # Invalid phone
        date_of_birth=date.today() - timedelta(days=365*17),  # Underage
        address_line1="123 Main St",
        city="Anytown",
        state="XX",  # Invalid state
        postal_code="INVALID",  # Invalid postal code
        country="XX",  # Invalid country
        is_verified=True  # Verified without verification date
    )
    
    # Validate customer
    validation_context = invalid_customer.validate("edit_schema")
    assert validation_context.has_errors()
    
    # Check specific errors
    errors = validation_context.errors
    error_fields = [error["field"] for error in errors]
    
    assert "email" in error_fields
    assert "phone" in error_fields
    assert "date_of_birth" in error_fields
    assert "state" in error_fields
    assert "postal_code" in error_fields
    assert "country" in error_fields
    assert "verification_date" in error_fields

@pytest.mark.asyncio
async def test_order_validation():
    """Test order domain validation."""
    # Test case 1: Valid order
    order = Order(
        customer_id="customer123",
        status=Order.STATUS_PENDING,
        shipping_address_line1="123 Main St",
        shipping_city="Anytown",
        shipping_state="CA",
        shipping_postal_code="12345",
        shipping_country="US",
        subtotal=Decimal("100.00"),
        tax=Decimal("10.00"),
        shipping_cost=Decimal("5.00"),
        total=Decimal("115.00")
    )
    
    # Validate order
    validation_context = order.validate("edit_schema")
    assert not validation_context.has_errors()
    
    # Test case 2: Invalid order
    invalid_order = Order(
        customer_id="customer123",
        status="invalid_status",  # Invalid status
        shipping_address_line1="123 Main St",
        shipping_city="Anytown",
        shipping_state="CA",
        shipping_postal_code="12345",
        shipping_country="RU",  # Unsupported country
        subtotal=Decimal("100.00"),
        tax=Decimal("10.00"),
        shipping_cost=Decimal("5.00"),
        total=Decimal("200.00")  # Incorrect total
    )
    
    # Validate order
    validation_context = invalid_order.validate("edit_schema")
    assert validation_context.has_errors()
    
    # Check specific errors
    errors = validation_context.errors
    error_fields = [error["field"] for error in errors]
    
    assert "status" in error_fields
    assert "shipping.country" in error_fields
    assert "total" in error_fields

@pytest.mark.asyncio
async def test_order_business_logic():
    """Test order business logic methods."""
    # Mock the save method
    with patch.object(Order, 'save', new_callable=AsyncMock) as mock_save:
        # Create an order
        order = Order(
            id="order123",
            customer_id="customer123",
            status=Order.STATUS_PENDING,
            shipping_address_line1="123 Main St",
            shipping_city="Anytown",
            shipping_state="CA",
            shipping_postal_code="12345",
            shipping_country="US",
            subtotal=Decimal("100.00"),
            tax=Decimal("10.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("115.00")
        )
        
        # Test confirm method - should fail without payment method
        with pytest.raises(UnoError) as excinfo:
            await order.confirm()
        assert "Payment method is required" in str(excinfo.value)
        
        # Set payment method and confirm
        order.payment_method = "credit_card"
        await order.confirm()
        assert order.status == Order.STATUS_CONFIRMED
        mock_save.assert_called_once()
        mock_save.reset_mock()
        
        # Test ship method
        await order.ship("TRACK-123456")
        assert order.status == Order.STATUS_SHIPPED
        assert order.tracking_number == "TRACK-123456"
        mock_save.assert_called_once()
        mock_save.reset_mock()
        
        # Test cancel method - should fail for shipped orders
        with pytest.raises(UnoError) as excinfo:
            await order.cancel("Customer requested cancellation")
        assert "Cannot cancel order that has been shipped" in str(excinfo.value)
        mock_save.assert_not_called()

@pytest.mark.asyncio
async def test_product_business_logic():
    """Test product business logic methods."""
    # Mock the save method
    with patch.object(Product, 'save', new_callable=AsyncMock) as mock_save:
        # Create a product
        product = Product(
            id="product123",
            name="Test Product",
            price=Decimal("29.99"),
            sku="ABC-12345",
            category="Electronics",
            inventory_count=10,
            min_order_quantity=2,
            max_order_quantity=5
        )
        
        # Test reserve_inventory method - invalid quantity
        with pytest.raises(UnoError) as excinfo:
            await product.reserve_inventory(1)  # Below min order quantity
        assert "below minimum order quantity" in str(excinfo.value)
        mock_save.assert_not_called()
        
        with pytest.raises(UnoError) as excinfo:
            await product.reserve_inventory(6)  # Above max order quantity
        assert "exceeds maximum order quantity" in str(excinfo.value)
        mock_save.assert_not_called()
        
        # Test reserve_inventory method - valid quantity
        await product.reserve_inventory(3)
        assert product.inventory_count == 7
        mock_save.assert_called_once()
        mock_save.reset_mock()
        
        # Test reserve_inventory method - insufficient inventory
        with pytest.raises(UnoError) as excinfo:
            await product.reserve_inventory(5)  # More than available
        assert "Insufficient inventory" in str(excinfo.value)
        mock_save.assert_not_called()
        
        # Test release_inventory method
        await product.release_inventory(2)
        assert product.inventory_count == 9
        mock_save.assert_called_once()

# Integration test with API endpoints
async def test_api_integration():
    """Test integration with API endpoints."""
    # This would typically be a real integration test with FastAPI
    # For demonstration, we'll use a simplified approach
    
    # Mock the Product.get method
    with patch('uno.obj.UnoObj.get', new_callable=AsyncMock) as mock_get:
        # Set up the mock to return a product
        product = Product(
            id="product123",
            name="Test Product",
            price=Decimal("29.99"),
            sku="ABC-12345",
            category="Electronics",
            inventory_count=10,
            min_order_quantity=2,
            max_order_quantity=5
        )
        mock_get.return_value = product
        
        # Mock API endpoint handler
        async def get_product_endpoint(product_id: str):
            try:
                # Get product from database
                product = await Product.get(id=product_id)
                
                # Return product as dictionary (simulating JSON response)
                return {"status": "success", "data": product.dict()}
            except UnoError as e:
                return {"status": "error", "message": str(e), "code": e.error_code}
        
        # Call the endpoint
        response = await get_product_endpoint("product123")
        assert response["status"] == "success"
        assert response["data"]["name"] == "Test Product"
        assert response["data"]["price"] == "29.99"  # String representation of Decimal
        
        # Mock API endpoint for updating product
        async def update_product_endpoint(product_id: str, data: Dict[str, Any]):
            try:
                # Get product from database
                product = await Product.get(id=product_id)
                
                # Update product attributes
                for key, value in data.items():
                    setattr(product, key, value)
                
                # Validate and save
                validation_context = product.validate("edit_schema")
                validation_context.raise_if_errors()
                
                await product.save()
                
                return {"status": "success", "data": product.dict()}
            except ValidationError as e:
                return {
                    "status": "error", 
                    "message": "Validation failed", 
                    "errors": e.validation_errors
                }
            except UnoError as e:
                return {"status": "error", "message": str(e), "code": e.error_code}
        
        # Patch the save method
        with patch.object(Product, 'save', new_callable=AsyncMock) as mock_save:
            # Call the endpoint with valid data
            response = await update_product_endpoint("product123", {"price": Decimal("39.99")})
            assert response["status"] == "success"
            assert response["data"]["price"] == "39.99"
            mock_save.assert_called_once()
            mock_save.reset_mock()
            
            # Call the endpoint with invalid data
            response = await update_product_endpoint("product123", {"price": Decimal("-10.00")})
            assert response["status"] == "error"
            assert "errors" in response
            assert any("price" in error["field"] for error in response["errors"])
            mock_save.assert_not_called()


if __name__ == "__main__":
    # This allows running the tests directly from this file
    import asyncio
    asyncio.run(pytest.main(["-xvs", __file__]))