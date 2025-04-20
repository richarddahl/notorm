"""
Domain protocols package.

This package contains protocol interfaces for domain components like
EntityProtocol, ValueObjectProtocol, etc.
"""

from .entity_protocols import EntityProtocol, AggregateRootProtocol
from .value_object_protocols import ValueObjectProtocol, PrimitiveValueObjectProtocol
from .specification import SpecificationProtocol

__all__ = [
    "EntityProtocol",
    "AggregateRootProtocol",
    "ValueObjectProtocol",
    "PrimitiveValueObjectProtocol",
    "SpecificationProtocol",
]
