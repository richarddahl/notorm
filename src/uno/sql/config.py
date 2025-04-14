# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Configuration for SQL generation and execution."""

import logging
from typing import List, Optional, Type, ClassVar

from pydantic import BaseModel
from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.engine.sync import SyncEngineFactory, sync_connection
from uno.sql.errors import (
    SQLConfigError,
    SQLConfigInvalidError,
    SQLExecutionError
)

from uno.sql.registry import SQLConfigRegistry
from uno.sql.emitter import SQLEmitter


class SQLConfig(BaseModel):
    """Configuration for SQL generation and execution for a table.

    This class manages SQL emitters for specific tables or database operations.
    It maintains a registry of all SQLConfig subclasses for dynamic registration
    and discovery.

    Attributes:
        default_emitters: Default emitters to use for this config
        table: Table for which SQL is being generated
        connection_config: Connection configuration
        engine_factory: Engine factory for creating connections
        emitters: Emitter instances
    """

    # Default emitters to use for this config
    default_emitters: ClassVar[List[Type[SQLEmitter]]] = []

    # The table for which SQL is being generated
    table: ClassVar[Optional[Table]] = None

    # Connection configuration
    connection_config: Optional[ConnectionConfig] = None

    # Engine factory for creating connections
    engine_factory: Optional[SyncEngineFactory] = None

    # Emitter instances
    emitters: List[SQLEmitter] = []

    model_config = {"arbitrary_types_allowed": True}

    def __init_subclass__(cls, **kwargs) -> None:
        """Register the SQLConfig subclass in the registry.

        Args:
            **kwargs: Additional keyword arguments

        Raises:
            UnoError: If a subclass with the same name already exists in the registry
        """
        super().__init_subclass__(**kwargs)
        if cls is not SQLConfig:  # Don't register the base class
            SQLConfigRegistry.register(cls)

    def __init__(self, **kwargs):
        """Initialize the SQLConfig with default emitters if none provided.

        Args:
            **kwargs: Initialization parameters
        """
        super().__init__(**kwargs)

        # If no emitters were provided, create them from default_emitters
        if not self.emitters and self.__class__.default_emitters:
            self.emitters = [
                emitter_cls(
                    table=self.__class__.table,
                    connection_config=self.connection_config,
                    engine_factory=self.engine_factory,
                )
                for emitter_cls in self.__class__.default_emitters
            ]

    def emit_sql(self, connection: Optional[Connection] = None) -> None:
        """Emit SQL for all registered emitters.

        Args:
            connection: Optional existing connection to use. If not provided,
                       a new connection will be created using the engine factory.

        Raises:
            UnoError: If SQL emission fails
        """
        should_create_connection = connection is None

        try:
            if should_create_connection:
                if self.engine_factory is None:
                    self.engine_factory = SyncEngineFactory()

                with sync_connection(
                    factory=self.engine_factory, config=self.connection_config
                ) as conn:
                    self._emit_sql_internal(conn)
            else:
                self._emit_sql_internal(connection)
        except SQLAlchemyError as e:
            logging.error(f"Error emitting SQL: {e}")
            raise UnoError(f"Failed to emit SQL: {e}", "SQL_EMISSION_ERROR")

    def _emit_sql_internal(self, connection: Connection) -> None:
        """Internal method to emit SQL statements.

        Args:
            connection: Database connection
        """
        for emitter in self.emitters:
            logging.info(f"Emitting SQL for {emitter.__class__.__name__}")
            emitter.emit_sql(connection)
