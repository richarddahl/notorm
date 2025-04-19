"""
Base Unit of Work implementation.

This module defines the base implementation of the Unit of Work pattern,
providing common functionality for all concrete implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    Dict, Any, Type, TypeVar, Optional, Generic, Set, List,
    Protocol, Callable, Awaitable, cast, runtime_checkable,
)

from uno.core.protocols import UnitOfWork, Repository
from uno.core.events import Event, AsyncEventBus

# Type variables
T = TypeVar("T")
RepoT = TypeVar("RepoT", bound=Repository)


class AbstractUnitOfWork(UnitOfWork, ABC):
    """
    Abstract base class for Unit of Work implementations.
    
    The Unit of Work pattern maintains a list of objects affected by a business
    transaction and coordinates writing out changes while ensuring consistency.
    """
    
    def __init__(
        self,
        event_bus: Optional[AsyncEventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the Unit of Work.
        
        Args:
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostics
        """
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        self._repositories: Dict[Type[Repository], Repository] = {}
        self._events: List[Event] = []
    
    def register_repository(self, repo_type: Type[RepoT], repo: RepoT) -> None:
        """
        Register a repository with this Unit of Work.
        
        Args:
            repo_type: The repository type/interface
            repo: The repository implementation
        """
        self._repositories[repo_type] = repo
    
    def get_repository(self, repo_type: Type[RepoT]) -> RepoT:
        """
        Get a repository by its type.
        
        Args:
            repo_type: The repository type/interface
            
        Returns:
            The repository implementation
            
        Raises:
            KeyError: If the repository is not registered
        """
        if repo_type not in self._repositories:
            raise KeyError(f"Repository not found: {repo_type.__name__}")
        return cast(RepoT, self._repositories[repo_type])
    
    def add_event(self, event: Event) -> None:
        """
        Add a domain event to be published after commit.
        
        Args:
            event: The domain event to add
        """
        self._events.append(event)
    
    def add_events(self, events: List[Event]) -> None:
        """
        Add multiple domain events to be published after commit.
        
        Args:
            events: The domain events to add
        """
        self._events.extend(events)
    
    def collect_new_events(self) -> List[Event]:
        """
        Collect new domain events from all registered repositories.
        
        Returns:
            A list of new domain events
        """
        # Collect events from all repositories that support event collection
        for repo in self._repositories.values():
            if hasattr(repo, "collect_events") and callable(getattr(repo, "collect_events")):
                events = repo.collect_events()
                if events:
                    self._events.extend(events)
        
        return self._events
    
    async def publish_events(self) -> None:
        """
        Publish all collected domain events.
        
        This is called automatically after a successful commit.
        """
        if not self._event_bus:
            self._logger.warning("No event bus configured, events will not be published")
            self._events.clear()
            return
        
        # Get all events to publish
        events = self.collect_new_events()
        
        # Publish each event
        self._logger.debug(f"Publishing {len(events)} events")
        for event in events:
            await self._event_bus.publish(event)
        
        # Clear the events after publishing
        self._events.clear()
    
    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    async def __aenter__(self) -> "AbstractUnitOfWork":
        """
        Enter the Unit of Work context.
        
        Returns:
            The Unit of Work instance
        """
        await self.begin()
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