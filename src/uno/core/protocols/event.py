"""
Event Protocol Definitions

This module defines the event system protocols used throughout the system.
Events are used for decoupled communication between components and for
implementing event-driven architecture patterns.
"""

from typing import (
    Protocol,
    Optional,
    Dict,
    List,
    Any,
    Callable,
    Awaitable,
    runtime_checkable,
)
from datetime import datetime
from uuid import UUID


@runtime_checkable
class EventProtocol(Protocol):
    """
    Protocol defining the interface for domain events.

    Events represent something that happened in the domain that other
    components might be interested in. They are immutable and contain
    all the information about what happened.
    """

    @property
    def event_id(self) -> str:
        """
        Get the unique identifier for this event.

        Returns:
            The event ID as a string
        """
        ...

    @property
    def event_type(self) -> str:
        """
        Get the type of this event.

        Returns:
            The event type as a string
        """
        ...

    @property
    def occurred_at(self) -> datetime:
        """
        Get the timestamp when this event occurred.

        Returns:
            The timestamp as a datetime object
        """
        ...

    @property
    def data(self) -> dict[str, Any]:
        """
        Get the event data.

        Returns:
            A dictionary containing the event data
        """
        ...

    @property
    def aggregate_id(self) -> str | None:
        """
        Get the ID of the aggregate this event belongs to, if any.

        Returns:
            The aggregate ID as a string, or None if not applicable
        """
        ...


# Type alias for event handlers
# An event handler is a callable that takes an event and returns nothing
EventHandler = Callable[[EventProtocol], Awaitable[None]]


# DEPRECATED: EventBusProtocol is now defined in uno.domain.event_bus.
# Please use uno.domain.event_bus.EventBusProtocol as the canonical event bus protocol.
# This legacy protocol is retained for backward compatibility only and will be removed in a future release.


@runtime_checkable
class EventStoreProtocol(Protocol):
    """
    Protocol defining the interface for the event store.

    The event store is responsible for persisting events and providing
    functionality to retrieve them later. It is a key component for
    implementing event sourcing.
    """

    async def append_events(
        self, events: list[EventProtocol], expected_version: int | None = None
    ) -> int:
        """
        Append events to the event store.

        Args:
            events: The events to append
            expected_version: The expected version of the aggregate (for optimistic concurrency)

        Returns:
            The new version after appending these events
        """
        ...

    async def get_events_by_aggregate(
        self, aggregate_id: str, from_version: int = 0
    ) -> list[EventProtocol]:
        """
        Get all events for a specific aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            from_version: The starting version to retrieve from

        Returns:
            A list of events for the specified aggregate
        """
        ...

    async def get_events_by_type(
        self, event_type: str, start_date: Optional[datetime] = None
    ) -> list[EventProtocol]:
        """
        Get all events of a specific type.

        Args:
            event_type: The type of events to retrieve
            start_date: Optional starting date for filtering events

        Returns:
            A list of events of the specified type
        """
        ...


@runtime_checkable
class EventPublisherProtocol(Protocol):
    """
    Protocol defining the interface for event publishers.

    Event publishers are responsible for sending events to external systems
    or message brokers. They handle the integration with the messaging
    infrastructure.
    """

    async def publish_event(self, event: EventProtocol) -> None:
        """
        Publish an event to external systems.

        Args:
            event: The event to publish
        """
        ...

    async def publish_events(self, events: list[EventProtocol]) -> None:
        """
        Publish multiple events to external systems.

        Args:
            events: The events to publish
        """
        ...
