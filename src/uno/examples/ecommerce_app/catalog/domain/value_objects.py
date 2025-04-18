"""
Value objects for the catalog context.

This module defines value objects specific to the catalog domain,
encapsulating validation logic and business rules.
"""

from enum import Enum
from decimal import Decimal
from typing import Optional

from uno.domain.core import ValueObject, PrimitiveValueObject


class ProductStatus(str, Enum):
    """Enumeration of possible product statuses."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class Dimensions(ValueObject):
    """Value object representing physical dimensions (length, width, height)."""
    
    length: Decimal
    width: Decimal
    height: Decimal
    unit: str = "cm"  # cm, in, etc.
    
    def validate(self) -> None:
        """Validate dimensions."""
        if self.length <= 0:
            raise ValueError("Length must be positive")
        if self.width <= 0:
            raise ValueError("Width must be positive")
        if self.height <= 0:
            raise ValueError("Height must be positive")
        if self.unit not in {"cm", "in", "mm", "m"}:
            raise ValueError(f"Unsupported unit: {self.unit}")
    
    def volume(self) -> Decimal:
        """Calculate volume based on dimensions."""
        return self.length * self.width * self.height


class Weight(ValueObject):
    """Value object representing weight."""
    
    value: Decimal
    unit: str = "kg"  # kg, g, lb, oz
    
    def validate(self) -> None:
        """Validate weight."""
        if self.value < 0:
            raise ValueError("Weight cannot be negative")
        if self.unit not in {"kg", "g", "lb", "oz"}:
            raise ValueError(f"Unsupported unit: {self.unit}")
    
    def convert_to(self, target_unit: str) -> "Weight":
        """Convert weight to a different unit."""
        if self.unit == target_unit:
            return self
            
        # Conversion factors to grams
        to_grams = {
            "kg": Decimal("1000"),
            "g": Decimal("1"),
            "lb": Decimal("453.59237"),
            "oz": Decimal("28.3495231")
        }
        
        # Conversion factors from grams
        from_grams = {
            "kg": Decimal("0.001"),
            "g": Decimal("1"),
            "lb": Decimal("0.00220462"),
            "oz": Decimal("0.0352739619")
        }
        
        # Convert to grams first, then to target unit
        grams = self.value * to_grams[self.unit]
        target_value = grams * from_grams[target_unit]
        
        return Weight(value=target_value, unit=target_unit)


class Inventory(ValueObject):
    """Value object representing inventory status and quantity."""
    
    quantity: int
    reserved: int = 0
    backorderable: bool = False
    restock_threshold: Optional[int] = None
    
    def validate(self) -> None:
        """Validate inventory."""
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if self.reserved < 0:
            raise ValueError("Reserved cannot be negative")
        if self.reserved > self.quantity:
            raise ValueError("Reserved cannot exceed quantity")
        if self.restock_threshold is not None and self.restock_threshold < 0:
            raise ValueError("Restock threshold cannot be negative")
    
    @property
    def available(self) -> int:
        """Calculate available quantity (total minus reserved)."""
        return self.quantity - self.reserved
    
    def is_low_stock(self) -> bool:
        """Check if inventory is below restock threshold."""
        if self.restock_threshold is None:
            return False
        return self.available <= self.restock_threshold
    
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock."""
        return self.available <= 0
    
    def can_fulfill(self, requested_quantity: int) -> bool:
        """Check if inventory can fulfill requested quantity."""
        if self.available >= requested_quantity:
            return True
        return self.backorderable