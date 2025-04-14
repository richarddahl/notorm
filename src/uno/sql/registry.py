# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Registry for SQL configuration classes."""

import logging
from typing import Dict, Type, List, Optional

from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.engine.sync import SyncEngineFactory, sync_connection
from uno.sql.errors import (
    SQLErrorCode,
    SQLRegistryClassNotFoundError,
    SQLRegistryClassAlreadyExistsError,
    SQLExecutionError,
    SQLConfigError
)


class SQLConfigRegistry:
    """Registry of all SQLConfig classes.

    This class maintains a registry of all SQLConfig subclasses for
    dynamic registration and discovery.

    Attributes:
        _registry: Dictionary of registered SQLConfig classes by name
    """

    _registry: Dict[str, Type["SQLConfig"]] = {}

    @classmethod
    def register(cls, config_class: Type["SQLConfig"]) -> None:
        """Register a SQLConfig class in the registry.

        Args:
            config_class: SQLConfig class to register

        Raises:
            UnoError: If a class with the same name already exists in the registry
                     and it's not the same class
        """
        if config_class.__name__ in cls._registry:
            # Skip if trying to register the same class again
            existing_class = cls._registry[config_class.__name__]
            if config_class.__module__ == existing_class.__module__:
                return
            raise UnoError(
                f"SQLConfig class: {config_class.__name__} already exists in the registry.",
                "DUPLICATE_SQLCONFIG",
            )
        cls._registry[config_class.__name__] = config_class

    @classmethod
    def get(cls, name: str) -> Optional[Type["SQLConfig"]]:
        """Get a SQLConfig class by name.

        Args:
            name: Name of the SQLConfig class

        Returns:
            SQLConfig class if found, None otherwise
        """
        return cls._registry.get(name)

    @classmethod
    def all(cls) -> Dict[str, Type["SQLConfig"]]:
        """Get all registered SQLConfig classes.

        Returns:
            Dictionary of all registered SQLConfig classes
        """
        return dict(cls._registry)

    @classmethod
    def emit_all(
        cls,
        connection: Optional[Connection] = None,
        engine_factory: Optional[SyncEngineFactory] = None,
        config: Optional[ConnectionConfig] = None,
        exclude: List[str] = None,
    ) -> None:
        """Emit SQL for all registered SQLConfig classes.

        Args:
            connection: Optional existing connection to use
            engine_factory: Optional engine factory to create new connections
            config: Optional connection configuration
            exclude: List of config class names to exclude

        Raises:
            UnoError: If SQL emission fails
        """
        exclude = exclude or []

        # Use provided connection or create a new one
        should_create_connection = connection is None

        if should_create_connection:
            if engine_factory is None:
                engine_factory = SyncEngineFactory()

            with sync_connection(
                factory=engine_factory,
                config=config,
            ) as conn:
                for name, config_cls in cls._registry.items():
                    if name in exclude:
                        continue
                    config_instance = config_cls(
                        connection_config=config, engine_factory=engine_factory
                    )
                    config_instance.emit_sql(conn)
        else:
            # Use the provided connection
            for name, config_cls in cls._registry.items():
                if name in exclude:
                    continue
                config_instance = config_cls(
                    connection_config=config, engine_factory=engine_factory
                )
                config_instance.emit_sql(connection)


# Import SQLConfig here to avoid circular import
from uno.sql.config import SQLConfig  # noqa
