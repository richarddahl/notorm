# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
import logging
from logging import Logger
from sqlalchemy.ext.asyncio import AsyncEngine

# Import engine-specific modules
from uno.database.engine.sync import SyncEngineFactory, sync_connection
from uno.database.engine.asynceng import AsyncEngineFactory

# Use string type annotations for session imports to break circular dependencies
__all__ = [
    "DatabaseFactory",
    "SyncEngineFactory",
    "sync_connection",
    "AsyncEngineFactory",
    "AsyncEngine",
]


class DatabaseFactory:
    """
    Unified factory for all database connection types.

    Provides central access to sync and async database functionality.
    """

    def __init__(self, logger: Optional[Logger] = None):
        """Initialize all component factories."""
        self.logger = logger or logging.getLogger(__name__)

        # Initialize specialized factories
        self.sync_engine_factory = SyncEngineFactory(logger=self.logger)
        self.async_engine_factory = AsyncEngineFactory(logger=self.logger)

        # Dynamically import AsyncSessionFactory to avoid circular imports
        from uno.database.session import AsyncSessionFactory

        self.async_session_factory = AsyncSessionFactory(
            engine_factory=self.async_engine_factory, logger=self.logger
        )

    # Factory accessors
    def get_sync_engine_factory(self) -> SyncEngineFactory:
        """Get the synchronous engine factory."""
        return self.sync_engine_factory

    def get_async_engine_factory(self) -> AsyncEngineFactory:
        """Get the asynchronous engine factory."""
        return self.async_engine_factory

    def get_async_session_factory(self):
        """Get the asynchronous session factory."""
        return self.async_session_factory
