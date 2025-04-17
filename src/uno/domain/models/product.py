"""
Product domain models.
"""

from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from pydantic import Field, field_validator

from uno.domain.models.base import Entity


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
    price: float = Field(..., gt=0)
    category: ProductCategory = Field(...)
    sku: str = Field(..., min_length=3, max_length=20)
    in_stock: bool = Field(default=True)
    stock_quantity: int = Field(default=0, ge=0)
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2)  # Round to 2 decimal places
    
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
        self.stock_quantity = quantity
        self.in_stock = quantity > 0
        self.updated_at = datetime.now(timezone.utc)
    
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
    
    def update_price(self, price: float) -> None:
        """
        Update the price.
        
        Args:
            price: The new price
        """
        if price <= 0:
            raise ValueError("Price must be positive")
        self.price = round(price, 2)
        self.updated_at = datetime.now(timezone.utc)
    
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