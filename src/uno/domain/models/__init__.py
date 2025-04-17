"""
Domain models for the domain layer.

This module contains the domain model entities, value objects, and domain events
that make up the core domain model for the uno framework.
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