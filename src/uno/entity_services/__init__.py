"""
Entity Services module for Uno framework.

This module provides a bridge between the UnoObj business logic layer
and the dependency injection service pattern.
"""

from uno.entity_services.base import UnoEntityService, UnoEntityServiceFactory

__all__ = [
    "UnoEntityService",
    "UnoEntityServiceFactory",
]