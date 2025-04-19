"""
Domain Entity Framework for UNO

This package provides the Domain Entity framework, the foundation of the
Domain-Driven Design (DDD) implementation in UNO. It contains base classes 
and utilities for creating rich domain models with proper encapsulation,
identity management, and business rule enforcement.

Key components:
- EntityBase: Base class for all domain entities
- AggregateRoot: Base class for aggregate roots
- ValueObject: Base class for value objects
- Identity: Utilities for entity identity management
- DomainEvent: Base class for domain events
"""

from uno.domain.entity.base import EntityBase
from uno.domain.entity.identity import Identity, IdentityGenerator
from uno.domain.entity.value_object import ValueObject
from uno.domain.entity.aggregate import AggregateRoot

__all__ = [
    'EntityBase',
    'Identity',
    'IdentityGenerator',
    'ValueObject',
    'AggregateRoot',
]