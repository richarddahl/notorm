"""
Domain models package.

This package contains concrete domain models built upon the core DDD
components defined in uno.domain.core.
"""

from uno.domain.core import (
    UnoDomainEvent,
    ValueObject,
    PrimitiveValueObject,
    Entity,
    AggregateRoot,
)

from uno.domain.value_objects import (
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
    "UnoDomainEvent",
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
