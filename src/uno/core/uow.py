"""
Unit of Work pattern implementation for the Uno framework.

This module implements the Unit of Work pattern, which provides a way to
maintain a consistent state across a business transaction.

DEPRECATED: This module is deprecated in favor of the new unified implementation
in the uno.core.uow package. Use AbstractUnitOfWork, DatabaseUnitOfWork, and
related classes from uno.core.uow package instead.
"""

import inspect
import logging
import warnings
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import (
    Dict,
    Any,
    Type,
    TypeVar,
    Optional,
    Generic,
    Set,
    cast,
    AsyncContextManager,
)

warnings.warn(
    "The UnitOfWork implementation in uno.core.uow module is deprecated. "
    "Use AbstractUnitOfWork, DatabaseUnitOfWork, and related classes from uno.core.uow package instead.",
    DeprecationWarning,
    stacklevel=2
)

from uno.core.protocols import Repository, UnitOfWork, UnoEvent
from uno.core.events import EventBus

T = TypeVar("T")
RepoT = TypeVar("RepoT", bound=Repository)


class AbstractUnitOfWork(UnitOfWork, ABC):
    """
    Abstract base class for unit of work implementations.
    
    DEPRECATED: Use AbstractUnitOfWork from uno.core.uow package instead.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the unit of work.

        Args:
            event_bus: Optional event bus for publishing events
            logger: Optional logger
        """
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        self._repositories: Dict[Type[Repository], Repository] = {}
        self.events: Set[UnoEvent] = set()

    def register_repository(self, repo_type: Type[RepoT], repo: RepoT) -> None:
        """
        Register a repository with the unit of work.

        Args:
            repo_type: The repository type
            repo: The repository instance
        """
        self._repositories[repo_type] = repo

    def get_repository(self, repo_type: Type[RepoT]) -> RepoT:
        """
        Get a repository by its type.

        Args:
            repo_type: The repository type

        Returns:
            The repository instance

        Raises:
            KeyError: If the repository is not registered
        """
        if repo_type not in self._repositories:
            raise KeyError(f"Repository not found: {repo_type.__name__}")
        return cast(RepoT, self._repositories[repo_type])

    def collect_events(self) -> Set[UnoEvent]:
        """
        Collect all events from registered repositories.

        Returns:
            The collected events
        """
        # For each repository, collect events from aggregates
        for repo in self._repositories.values():
            if hasattr(repo, "collect_events"):
                self.events.update(repo.collect_events())

        return self.events

    async def publish_events(self) -> None:
        """Publish all collected events."""
        if not self._event_bus:
            return

        events = self.collect_events()
        for event in events:
            await self._event_bus.publish(event)

        self.events.clear()

    async def __aenter__(self) -> "AbstractUnitOfWork":
        """
        Enter the unit of work context.

        Returns:
            The unit of work
        """
        await self.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the unit of work context.

        If an exception occurred, rollback the transaction.
        Otherwise, commit the transaction and publish events.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        try:
            if exc_type:
                self._logger.debug(
                    f"Rolling back transaction due to {exc_type.__name__}: {exc_val}"
                )
                await self.rollback()
            else:
                self._logger.debug("Committing transaction")
                await self.commit()
                await self.publish_events()
        except Exception as e:
            self._logger.error(f"Error in unit of work exit: {e}")
            await self.rollback()
            raise


class DatabaseUnitOfWork(AbstractUnitOfWork):
    """
    Unit of work implementation for database operations.
    
    DEPRECATED: Use DatabaseUnitOfWork from uno.core.uow package instead.
    """

    def __init__(
        self,
        connection_factory: Any,  # Callable that returns a database connection
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the unit of work.

        Args:
            connection_factory: A factory that creates database connections
            event_bus: Optional event bus for publishing events
            logger: Optional logger
        """
        super().__init__(event_bus, logger)
        self._connection_factory = connection_factory
        self._connection = None
        self._transaction = None

    async def begin(self) -> None:
        """Begin a new transaction."""
        if self._connection is None:
            self._connection = await self._connection_factory()

        self._transaction = await self._connection.transaction()
        self._logger.debug("Transaction started")

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._transaction:
            await self._transaction.commit()
            self._transaction = None
            self._logger.debug("Transaction committed")

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._transaction:
            await self._transaction.rollback()
            self._transaction = None
            self._logger.debug("Transaction rolled back")


class ContextUnitOfWork:
    """
    A decorator that provides a unit of work context.

    This decorator is used to wrap coroutine methods to provide a unit of work context.
    
    DEPRECATED: Use unit_of_work decorator from uno.core.uow package instead.
    """

    def __init__(self, uow_factory: Any):  # Callable that returns a UnitOfWork
        """
        Initialize the decorator.

        Args:
            uow_factory: A factory that creates a unit of work
        """
        self._uow_factory = uow_factory

    def __call__(self, func):
        """
        Decorate a coroutine method.

        Args:
            func: The method to decorate

        Returns:
            The decorated method
        """

        async def wrapper(*args, **kwargs):
            async with self._uow_factory() as uow:
                # Inject the unit of work as a keyword argument
                if "uow" in inspect.signature(func).parameters:
                    kwargs["uow"] = uow
                return await func(*args, **kwargs)

        return wrapper


@asynccontextmanager
async def transaction(uow_factory: Any) -> AsyncContextManager[UnitOfWork]:
    """
    Context manager for a unit of work transaction.
    
    DEPRECATED: Use transaction context manager from uno.core.uow package instead.

    Args:
        uow_factory: A factory that creates a unit of work

    Yields:
        The unit of work
    """
    async with uow_factory() as uow:
        yield uow