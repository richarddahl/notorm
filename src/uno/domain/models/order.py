"""
Order domain models.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import Field, field_validator

from uno.domain.core import Entity, ValueObject


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderItem(ValueObject):
    """
    Order item value object.
    
    This represents an item in an order, with product, quantity, and price data.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    
    @field_validator('total_price')
    @classmethod
    def validate_total_price(cls, v: float, values: dict) -> float:
        """Validate total price is correct."""
        if 'quantity' in values and 'unit_price' in values:
            expected = round(values['quantity'] * values['unit_price'], 2)
            if abs(v - expected) > 0.01:  # Allow small rounding differences
                raise ValueError(f'Total price should be {expected}')
        return round(v, 2)  # Round to 2 decimal places


class Order(Entity):
    """
    Order entity in the domain model.
    
    This represents an order in the system, with items, status, and shipping data.
    """
    
    user_id: str
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    total_amount: float = Field(..., ge=0)
    shipping_address: Optional[Dict[str, str]] = None
    payment_method: Optional[str] = None
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items: List[OrderItem] = Field(default_factory=list)
    
    @field_validator('total_amount')
    @classmethod
    def validate_total_amount(cls, v: float, values: dict) -> float:
        """Validate total amount is positive."""
        if v < 0:
            raise ValueError('Total amount must be non-negative')
        return round(v, 2)  # Round to 2 decimal places
    
    def add_item(self, item: OrderItem) -> None:
        """
        Add an item to the order.
        
        Args:
            item: The item to add
        """
        self.items.append(item)
        self.total_amount = round(self.total_amount + item.total_price, 2)
        self.updated_at = datetime.now(timezone.utc)
    
    def remove_item(self, item_id: str) -> None:
        """
        Remove an item from the order.
        
        Args:
            item_id: The ID of the item to remove
        """
        item = next((item for item in self.items if item.id == item_id), None)
        if item:
            self.items = [i for i in self.items if i.id != item_id]
            self.total_amount = round(self.total_amount - item.total_price, 2)
            self.updated_at = datetime.now(timezone.utc)
    
    def update_status(self, status: OrderStatus) -> None:
        """
        Update the order status.
        
        Args:
            status: The new status
        """
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
    
    def cancel(self) -> None:
        """Cancel the order."""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError("Cannot cancel order that has been shipped or delivered")
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)
    
    def ship(self) -> None:
        """Mark the order as shipped."""
        if self.status != OrderStatus.PROCESSING:
            raise ValueError("Order must be processing before shipping")
        self.status = OrderStatus.SHIPPED
        self.updated_at = datetime.now(timezone.utc)
    
    def deliver(self) -> None:
        """Mark the order as delivered."""
        if self.status != OrderStatus.SHIPPED:
            raise ValueError("Order must be shipped before delivery")
        self.status = OrderStatus.DELIVERED
        self.updated_at = datetime.now(timezone.utc)
    
    def refund(self) -> None:
        """Mark the order as refunded."""
        self.status = OrderStatus.REFUNDED
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_total(self) -> float:
        """
        Calculate the total amount of the order.
        
        Returns:
            The total amount
        """
        return round(sum(item.total_price for item in self.items), 2)
    
    def validate_total(self) -> bool:
        """
        Validate that the total amount matches the sum of item prices.
        
        Returns:
            True if the total amount is correct, False otherwise
        """
        calculated = self.calculate_total()
        return abs(self.total_amount - calculated) < 0.01  # Allow small rounding differences