# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Registry component for UnoObj model classes.

This module provides a registry mechanism for UnoObj classes, ensuring unique
registration and providing lookup capabilities.
"""

from typing import Dict, Type, Optional, ClassVar, TypeVar

from pydantic import BaseModel

from uno.errors import UnoRegistryError

T = TypeVar("T", bound="BaseModel")


class UnoRegistry:
    """
    Registry for UnoObj model classes.

    This class implements a singleton pattern to provide a global registry
    for UnoObj model classes.
    """

    _instance: Optional["UnoRegistry"] = None
    _models: Dict[str, Type[BaseModel]] = {}

    @classmethod
    def get_instance(cls) -> "UnoRegistry":
        """
        Get the singleton instance of the registry.

        Returns:
            UnoRegistry: The singleton registry instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, model_class: Type[T], table_name: str) -> None:
        """
        Register a model class with the registry.

        Args:
            model_class: The model class to register
            table_name: The table name to use as the registration key

        Raises:
            UnoRegistryError: If a model with the same table name is already registered
        """
        if table_name in self._models:
            raise UnoRegistryError(
                f"A Model class with the table name {table_name} already exists in the registry.",
                "DUPLICATE_MODEL",
            )
        self._models[table_name] = model_class

    def get(self, table_name: str) -> Optional[Type[T]]:
        """
        Get a model class by its table name.

        Args:
            table_name: The table name to look up

        Returns:
            The model class if found, None otherwise
        """
        return self._models.get(table_name)

    def get_all(self) -> Dict[str, Type[T]]:
        """
        Get all registered model classes.

        Returns:
            A dictionary of table names to model classes
        """
        return self._models.copy()

    def clear(self) -> None:
        """
        Clear all registered models.

        This is primarily useful for testing.
        """
        self._models.clear()
