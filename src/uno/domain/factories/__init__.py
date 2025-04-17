"""
Domain factories package.

This package contains factory components for creating domain entities.
"""

from .entity_factory import EntityFactory, create_entity_factory

__all__ = [
    "EntityFactory",
    "create_entity_factory",
]
