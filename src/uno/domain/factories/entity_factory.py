"""
Entity factory implementation.

This module provides factory classes and functions for creating domain entities.
"""

from typing import TypeVar, Type, Dict, Any, Generic, Callable

from ..protocols.entity_protocols import EntityProtocol

T = TypeVar("T", bound=EntityProtocol)


class EntityFactory(Generic[T]):
    """Factory for creating domain entities."""

    def __init__(self, entity_class: Type[T]):
        """
        Initialize the entity factory.

        Args:
            entity_class: The entity class to create
        """
        self.entity_class = entity_class

    def create(self, **kwargs: Any) -> T:
        """
        Create a new entity.

        Args:
            **kwargs: Keyword arguments to pass to the entity constructor

        Returns:
            A new entity instance
        """
        return self.entity_class(**kwargs)

    def create_from_dict(self, data: dict[str, Any]) -> T:
        """
        Create a new entity from a dictionary.

        Args:
            data: Dictionary containing entity data

        Returns:
            A new entity instance
        """
        return self.entity_class(**data)


def create_entity_factory(entity_class: Type[T]) -> EntityFactory[T]:
    """
    Create an entity factory for the given entity class.

    Args:
        entity_class: The entity class to create a factory for

    Returns:
        An entity factory
    """
    return EntityFactory(entity_class)
