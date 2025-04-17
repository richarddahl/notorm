"""
Product domain models.
"""

from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from pydantic import Field, field_validator

from uno.domain.core import Entity
from uno.domain.value_objects import Money


class ProductCategory(str, Enum):
    """Product category enumeration."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    BEAUTY = "beauty"
    TOYS = "toys"
    FOOD = "food"
    OTHER = "other"


class Product(Entity):
    """
    Product entity in the domain model.
    
    This represents a product in the system, with inventory and pricing data.
    """
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    price: Money
    category: ProductCategory = Field(...)
    sku: str = Field(..., min_length=3, max_length=20)
    in_stock: bool = Field(default=True)
    stock_quantity: int = Field(default=0, ge=0)
    tags: List[str] = Field(default_factory=list)
    
    @field_validator('stock_quantity')
    @classmethod
    def validate_stock_quantity(cls, v: int, values: dict) -> int:
        """Validate stock quantity and update in_stock."""
        in_stock = v > 0
        if 'in_stock' in values and values['in_stock'] != in_stock:
            values['in_stock'] = in_stock
        return v
    
    def update_stock(self, quantity: int) -> None:
        """
        Update the stock quantity.
        
        Args:
            quantity: The new stock quantity
        """
        if quantity < 0:
            raise ValueError("Stock quantity cannot be negative")
            
        self.stock_quantity = quantity
        self.in_stock = quantity > 0
        self.updated_at = datetime.now(timezone.utc)
        self.add_event(ProductStockUpdatedEvent(
            product_id=str(self.id),
            old_quantity=self.stock_quantity,
            new_quantity=quantity
        ))
    
    def increase_stock(self, amount: int) -> None:
        """
        Increase the stock quantity.
        
        Args:
            amount: The amount to increase by
        """
        if amount < 0:
            raise ValueError("Amount must be positive")
        self.stock_quantity += amount
        self.in_stock = self.stock_quantity > 0
        self.updated_at = datetime.now(timezone.utc)
    
    def decrease_stock(self, amount: int) -> None:
        """
        Decrease the stock quantity.
        
        Args:
            amount: The amount to decrease by
        """
        if amount < 0:
            raise ValueError("Amount must be positive")
        if amount > self.stock_quantity:
            raise ValueError("Not enough stock")
        self.stock_quantity -= amount
        self.in_stock = self.stock_quantity > 0
        self.updated_at = datetime.now(timezone.utc)
    
    def update_price(self, price: Money) -> None:
        """
        Update the price.
        
        Args:
            price: The new price
        """
        old_price = self.price
        self.price = price
        self.updated_at = datetime.now(timezone.utc)
        self.add_event(ProductPriceUpdatedEvent(
            product_id=str(self.id),
            old_price=old_price.to_dict(),
            new_price=price.to_dict()
        ))
    
    def update_category(self, category: ProductCategory) -> None:
        """
        Update the category.
        
        Args:
            category: The new category
        """
        self.category = category
        self.updated_at = datetime.now(timezone.utc)
    
    def is_in_stock(self) -> bool:
        """
        Check if the product is in stock.
        
        Returns:
            True if the product is in stock, False otherwise
        """
        return self.in_stock and self.stock_quantity > 0
        
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the product.
        
        Args:
            tag: The tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the product.
        
        Args:
            tag: The tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now(timezone.utc)


# Domain Events
from uno.domain.core import DomainEvent

class ProductPriceUpdatedEvent(DomainEvent):
    """Event fired when a product's price is updated."""
    product_id: str
    old_price: dict
    new_price: dict
    
    
class ProductStockUpdatedEvent(DomainEvent):
    """Event fired when a product's stock is updated."""
    product_id: str
    old_quantity: int
    new_quantity: int