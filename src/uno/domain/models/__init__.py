"""
Domain models package.

This package contains all domain model components including Entity, ValueObject,
AggregateRoot, DomainEvent, and related classes.
"""

from uno.domain.models.base import (
    DomainEvent,
    ValueObject,
    PrimitiveValueObject,
    Entity,
    AggregateRoot,
    CommandResult,
    # Common value objects
    Email,
    Money,
    Address,
)

from uno.domain.models.user import (
    User,
    UserRole,
)

from uno.domain.models.product import (
    Product,
    ProductCategory,
)

from uno.domain.models.order import (
    Order,
    OrderStatus,
    OrderItem,
)

__all__ = [
    # Base domain components
    "Entity",
    "AggregateRoot",
    "ValueObject",
    "PrimitiveValueObject",
    "DomainEvent",
    "CommandResult",
    
    # Common value objects
    "Email",
    "Money",
    "Address",
    
    # Domain models
    "User",
    "UserRole",
    "Product",
    "ProductCategory",
    "Order",
    "OrderStatus",
    "OrderItem",
]
