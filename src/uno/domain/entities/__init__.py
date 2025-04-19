"""
Legacy domain entities module.

This module has been deprecated and replaced by the new domain entity framework
in uno.domain.entity. Please use the new implementation instead.
"""

import warnings

warnings.warn(
    "The uno.domain.entities module is deprecated. "
    "Use uno.domain.entity instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export the new implementations for backward compatibility
from uno.domain.entity import (
    EntityBase as Entity,
    AggregateRoot,
    ValueObject,
)

__all__ = [
    "Entity",
    "AggregateRoot",
    "ValueObject",
]