"""
Base Unit of Work implementation.

This module defines the base implementation of the Unit of Work pattern,
providing common functionality for all concrete implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, cast, TYPE_CHECKING

from uno.core.errors.result import Result
from uno.core.events import Event
from uno.domain.event_bus import EventBusProtocol
from uno.core.protocols.repository import RepositoryProtocol
if TYPE_CHECKING:
    from uno.core.protocols import UnitOfWork

# Type variables
T = TypeVar("T")
RepoT = TypeVar("RepoT", bound=RepositoryProtocol)


class AbstractUnitOfWork(ABC):
    """
    Abstract base class for Unit of Work implementations.

    The Unit of Work pattern maintains a list of objects affected by a business
    transaction and coordinates writing out changes while ensuring consistency.
    """

    def __init__(
        self,
        event_bus: EventBusProtocol | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the Unit of Work.

        Args:
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostics
        """
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        self._repositories: dict[type[RepositoryProtocol], RepositoryProtocol] = {}
        self._events: list[Event] = []

    def register_repository(self, repo_type: type[RepoT], repo: RepoT) -> None:
        """
        Register a repository with this Unit of Work.

        Args:
            repo_type: The repository type/interface
            repo: The repository implementation
        """
        self._repositories[repo_type] = repo

    def get_repository(self, repo_type: type[RepoT]) -> Result[RepoT, str]:
        """
        Get a repository by its type.

        Args:
            repo_type: The repository type/interface

        Returns:
            Result containing the repository implementation or an error
        """
        if repo_type not in self._repositories:
            return Result.failure(f"Repository not found: {repo_type.__name__}")
        return Result.success(cast(RepoT, self._repositories[repo_type]))

    def add_event(self, event: Event) -> None:
        """
        Add a domain event to be published after commit.

        Args:
            event: The domain event to add
        """
        self._events.append(event)

    def add_events(self, events: list[Event]) -> None:
        """
        Add multiple domain events to be published after commit.

        Args:
            events: The domain events to add
        """
        self._events.extend(events)

    def collect_new_events(self) -> list[Event]:
        """
        Collect new domain events from all registered repositories.

        Returns:
            A list of new domain events
        """
        # Collect events from all repositories that support event collection
        for repo in self._repositories.values():
            if hasattr(repo, "collect_events") and callable(repo.collect_events):
                events = repo.collect_events()
                if events:
                    self._events.extend(events)

        return self._events

    async def publish_events(self) -> Result[None, str]:
        """
        Publish all collected domain events.

        This is called automatically after a successful commit.

        Returns:
            Result indicating success or an error message
        """
        if not self._event_bus:
            self._logger.warning(
                "No event bus configured, events will not be published"
            )
            self._events.clear()
            return Result.success(None)

        try:
            # Get all events to publish
            events = self.collect_new_events()

            # Publish each event
            self._logger.debug(f"Publishing {len(events)} events")
            for event in events:
                await self._event_bus.publish(event)

            # Clear the events after publishing
            self._events.clear()
            return Result.success(None)
        except Exception as e:
            self._logger.error(f"Error publishing events: {e}")
            return Result.failure(f"Failed to publish events: {str(e)}")

    @abstractmethod
    async def begin(self) -> Result[None, str]:
        """Begin a new transaction.

        Returns:
            Result indicating success or an error message
        """
        pass

    @abstractmethod
    async def commit(self) -> Result[None, str]:
        """Commit the current transaction.

        Returns:
            Result indicating success or an error message
        """
        pass

    @abstractmethod
    async def rollback(self) -> Result[None, str]:
        """Rollback the current transaction.

        Returns:
            Result indicating success or an error message
        """
        pass

    async def __aenter__(self) -> "AbstractUnitOfWork":
        """
        Enter the Unit of Work context.

        Returns:
            The Unit of Work instance

        Raises:
            RuntimeError: If the transaction could not be started
        """
        result = await self.begin()
        if result.is_failure():
            raise RuntimeError(f"Failed to begin transaction: {result.error()}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the Unit of Work context.

        If an exception occurred, the transaction will be rolled back.
        Otherwise, the transaction will be committed and events published.

        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised

        Raises:
            RuntimeError: If both commit and rollback fail
        """
        if exc_type:
            self._logger.debug(
                f"Rolling back transaction due to {exc_type.__name__}: {exc_val}"
            )
            rollback_result = await self.rollback()
            if rollback_result.is_failure():
                self._logger.error(
                    "Failed to rollback transaction: %s", rollback_result.error()
                )
                # We don't re-raise here as we're already handling an exception
        else:
            self._logger.debug("Committing transaction")
            commit_result = await self.commit()

            if commit_result.is_failure():
                self._logger.error(
                    "Failed to commit transaction: %s", commit_result.error()
                )
                rollback_result = await self.rollback()
                if rollback_result.is_failure():
                    self._logger.error(
                        "Failed to rollback after commit failure: %s",
                        rollback_result.error(),
                    )
                    raise RuntimeError(
                        f"Failed to commit and rollback: {commit_result.error()}, {rollback_result.error()}"
                    )
                raise RuntimeError(
                    f"Failed to commit transaction: {commit_result.error()}"
                )

            # Only publish events if commit succeeded
            publish_result = await self.publish_events()
            if publish_result.is_failure():
                self._logger.error(
                    "Failed to publish events: %s", publish_result.error()
                )
                # We don't rollback here as the transaction was already committed
