"""
Unit of Work pattern implementation for the Uno framework.

This module implements the Unit of Work pattern to coordinate operations
across multiple repositories and provide transaction management.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import (
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Generic,
    cast,
    Any,
    Set,
    Callable,
)

from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.unified_events import UnoDomainEvent, EventBus, default_event_bus
from uno.domain.repositories import Repository, AggregateRepository
from uno.core.errors.base import UnoError


T = TypeVar("T")
RepoT = TypeVar("RepoT", bound=Repository)


class UnitOfWork(ABC):
    """
    Abstract base class for Unit of Work implementations.

    The Unit of Work pattern maintains a list of objects affected by a business transaction
    and coordinates the writing out of changes and resolution of concurrency problems.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the unit of work.

        Args:
            event_bus: Optional event bus for domain events
            logger: Optional logger instance
        """
        self.event_bus = event_bus or default_event_bus
        self.logger = logger or logging.getLogger(__name__)
        self._repositories: Dict[Type[Repository], Repository] = {}

    @abstractmethod
    async def begin(self) -> None:
        """Begin a transaction."""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass

    def register_repository(self, repo_type: Type[RepoT], repo: RepoT) -> None:
        """
        Register a repository with this unit of work.

        Args:
            repo_type: Repository type
            repo: Repository instance
        """
        self._repositories[repo_type] = repo

    def get_repository(self, repo_type: Type[RepoT]) -> RepoT:
        """
        Get a repository by type.

        Args:
            repo_type: Repository type

        Returns:
            Repository instance

        Raises:
            KeyError: If repository type is not registered
        """
        if repo_type not in self._repositories:
            raise KeyError(f"Repository not found: {repo_type.__name__}")

        return cast(RepoT, self._repositories[repo_type])

    async def collect_and_publish_events(self) -> None:
        """Collect events from repositories and publish them."""
        if not self.event_bus:
            return

        all_events: List[UnoDomainEvent] = []

        # Collect events from repositories
        for repo in self._repositories.values():
            if isinstance(repo, AggregateRepository):
                all_events.extend(repo.collect_events())

        # Publish events
        for event in all_events:
            await self.event_bus.publish(event)

    async def __aenter__(self) -> "UnitOfWork":
        """Enter the context manager."""
        await self.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        if exc_type:
            self.logger.error(
                f"Rolling back transaction due to {exc_type.__name__}: {exc_val}"
            )
            await self.rollback()
            return

        try:
            await self.commit()
            await self.collect_and_publish_events()
        except Exception as e:
            self.logger.error(f"Error in unit of work commit: {e}")
            await self.rollback()
            raise UnoError(
                message=f"Failed to commit transaction: {str(e)}",
                error_code="TRANSACTION_ERROR",
            )


class SqlAlchemyUnitOfWork(UnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.

    This implementation uses SQLAlchemy sessions for transaction management.
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the SQLAlchemy unit of work.

        Args:
            session_factory: Factory function that creates SQLAlchemy sessions
            event_bus: Optional event bus for domain events
            logger: Optional logger instance
        """
        super().__init__(event_bus, logger)
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None

    async def begin(self) -> None:
        """Begin a transaction."""
        self.session = self.session_factory()
        self.logger.debug("SQLAlchemy transaction started")

    async def commit(self) -> None:
        """Commit the transaction."""
        if self.session:
            await self.session.commit()
            self.logger.debug("SQLAlchemy transaction committed")

    async def rollback(self) -> None:
        """Rollback the transaction."""
        if self.session:
            await self.session.rollback()
            self.logger.debug("SQLAlchemy transaction rolled back")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager, ensuring resource cleanup."""
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            if self.session:
                await self.session.close()
                self.session = None


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory implementation of the Unit of Work pattern.

    This implementation is useful for testing and doesn't perform actual transactions.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the in-memory unit of work.

        Args:
            event_bus: Optional event bus for domain events
            logger: Optional logger instance
        """
        super().__init__(event_bus, logger)
        self._committed = False
        self._rolled_back = False

    async def begin(self) -> None:
        """Begin a transaction."""
        self._committed = False
        self._rolled_back = False
        self.logger.debug("In-memory transaction started")

    async def commit(self) -> None:
        """Commit the transaction."""
        self._committed = True
        self.logger.debug("In-memory transaction committed")

    async def rollback(self) -> None:
        """Rollback the transaction."""
        self._rolled_back = True
        self.logger.debug("In-memory transaction rolled back")

    @property
    def committed(self) -> bool:
        """Check if the transaction was committed."""
        return self._committed

    @property
    def rolled_back(self) -> bool:
        """Check if the transaction was rolled back."""
        return self._rolled_back


@asynccontextmanager
async def transaction(uow_factory: Callable[[], UnitOfWork]) -> UnitOfWork:
    """
    Context manager for transactions.

    This utility function provides a convenient way to use a unit of work
    in a transaction context.

    Args:
        uow_factory: Factory function that creates unit of work instances

    Yields:
        Unit of work instance
    """
    async with uow_factory() as uow:
        yield uow
