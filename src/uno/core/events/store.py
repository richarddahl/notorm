"""
Event store implementation for the UNO framework.

This module defines the EventStore interface and provides implementations
for event persistence, which is essential for event sourcing patterns.
"""

import abc
from datetime import datetime
from typing import List, Optional, Dict, Any, Generic, TypeVar

from uno.core.protocols.event import EventStoreProtocol, EventProtocol
from uno.core.events.event import Event

# Type variable for event store
E = TypeVar("E", bound=EventProtocol)


class EventStore(Generic[E], abc.ABC):
    """
    Abstract base class for event stores.

    The EventStore is responsible for persisting events and providing
    methods to retrieve them for various purposes such as:
    - Event sourcing
    - Replay and recovery
    - Audit trails
    - Analytics

    All EventStore implementations should inherit from this class.
    """

    @abc.abstractmethod
    async def append_events(
        self, events: list[E], expected_version: Optional[int] = None
    ) -> int:
        """
        Append events to the store, optionally with optimistic concurrency.

        Args:
            events: The events to append
            expected_version: The expected current version (for optimistic concurrency)

        Returns:
            The new version after appending these events

        Raises:
            ConcurrencyError: If expected_version is provided and doesn't match
        """
        pass

    @abc.abstractmethod
    async def get_events_by_aggregate(
        self, aggregate_id: str, from_version: int = 0
    ) -> list[E]:
        """
        Get all events for a specific aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            from_version: The starting version to retrieve from

        Returns:
            A list of events for the specified aggregate
        """
        pass

    @abc.abstractmethod
    async def get_events_by_type(
        self, event_type: str, start_date: Optional[datetime] = None
    ) -> list[E]:
        """
        Get all events of a specific type.

        Args:
            event_type: The type of events to retrieve
            start_date: Optional starting date for filtering events

        Returns:
            A list of events of the specified type
        """
        pass


class InMemoryEventStore(EventStore[EventProtocol]):
    """
    In-memory implementation of the event store.

    This implementation is primarily for testing and development.
    It stores all events in memory, which means they are lost when
    the application restarts.
    """

    def __init__(self):
        """Initialize an empty in-memory event store."""
        self._events: list[EventProtocol] = []
        self._aggregate_versions: Dict[str, int] = {}  # aggregate_id -> version

    async def append_events(
        self, events: list[EventProtocol], expected_version: Optional[int] = None
    ) -> int:
        """
        Append events to the store, with optional optimistic concurrency.

        Args:
            events: The events to append
            expected_version: The expected current version (for optimistic concurrency)

        Returns:
            The new version after appending these events

        Raises:
            ConcurrencyError: If expected_version is provided and doesn't match
        """
        if not events:
            return 0

        # Get the aggregate ID (assuming all events are for the same aggregate)
        aggregate_id = events[0].aggregate_id
        if not aggregate_id:
            raise ValueError("Events must have an aggregate_id for version tracking")

        # Check optimistic concurrency
        current_version = self._aggregate_versions.get(aggregate_id, 0)
        if expected_version is not None and expected_version != current_version:
            from uno.core.errors.base import ConcurrencyError

            raise ConcurrencyError(
                f"Concurrency conflict for aggregate {aggregate_id}: "
                f"expected version {expected_version}, but current version is {current_version}"
            )

        # Append events with incrementing versions
        for i, event in enumerate(events):
            version = current_version + i + 1
            # Create a new event with the version set
            event_dict = (
                event.to_dict() if hasattr(event, "to_dict") else event.__dict__.copy()
            )
            event_dict["aggregate_version"] = version

            # Store the event
            self._events.append(event)

        # Update the aggregate version
        new_version = current_version + len(events)
        self._aggregate_versions[aggregate_id] = new_version

        return new_version

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
        return [
            event
            for event in self._events
            if (
                event.aggregate_id == aggregate_id
                and getattr(event, "aggregate_version", 0) >= from_version
            )
        ]

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
        filtered_events = [
            event for event in self._events if event.event_type == event_type
        ]

        if start_date:
            filtered_events = [
                event for event in filtered_events if event.occurred_at >= start_date
            ]

        return filtered_events
