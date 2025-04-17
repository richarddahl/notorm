"""
Integration between the event store and the CQRS system.

This module provides the necessary glue code to connect the CQRS system
with the event store implementation, enabling event sourcing for aggregates.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Type, TypeVar, cast, Union, Generic
from datetime import datetime, UTC

from uno.core.di import inject_dependency
from uno.domain.events import (
    DomainEvent,
    EventBus,
    EventStore,
    EventPublisher,
    get_event_bus,
    get_event_store,
)
from uno.domain.event_store import PostgresEventStore, EventSourcedRepository
from uno.domain.event_store_manager import EventStoreManager
from uno.domain.models import AggregateRoot
from uno.core.result import Result


T = TypeVar("T", bound=DomainEvent)
A = TypeVar("A", bound=AggregateRoot)


class EventStoreIntegration:
    """
    Integration between the event store and the CQRS system.

    This class provides methods for setting up and managing the event store
    integration with the CQRS system.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        event_store: Optional[EventStore] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the event store integration.

        Args:
            event_bus: Optional event bus instance, defaults to the global instance
            event_store: Optional event store instance, defaults to the global instance
            logger: Optional logger for diagnostic information
        """
        self.event_bus = event_bus or get_event_bus()
        self.event_store = event_store or get_event_store()
        self.logger = logger or logging.getLogger(__name__)
        self.store_manager = EventStoreManager(logger=self.logger)
        self.publisher = EventPublisher(self.event_bus, self.event_store)

    async def initialize(self) -> None:
        """
        Initialize the event store integration.

        This method:
        1. Creates the necessary database schema for the event store
        2. Sets up event listeners for publishing events to the store
        3. Initializes the event publishers
        """
        try:
            # Create the database schema
            self.store_manager.create_event_store_schema()
            self.logger.info("Event store schema initialized successfully")

            # Set up listeners (if any specific initialization is needed)
            # This is a placeholder for future extensions

            self.logger.info("Event store integration initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing event store integration: {e}")
            raise

    async def publish_event(self, event: DomainEvent) -> Result[None]:
        """
        Publish an event to the event store and event bus.

        Args:
            event: The domain event to publish

        Returns:
            Result indicating success or failure
        """
        try:
            await self.publisher.publish(event)
            return Result.success(None)
        except Exception as e:
            self.logger.error(f"Error publishing event {event.event_type}: {e}")
            return Result.failure(str(e))

    async def publish_events(self, events: List[DomainEvent]) -> Result[None]:
        """
        Publish multiple events to the event store and event bus.

        Args:
            events: The domain events to publish

        Returns:
            Result indicating success or failure
        """
        try:
            await self.publisher.publish_many(events)
            return Result.success(None)
        except Exception as e:
            self.logger.error(f"Error publishing {len(events)} events: {e}")
            return Result.failure(str(e))

    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """
        Get all events of a specific type from the event store.

        Args:
            event_type: The type of events to retrieve
            since: Optional timestamp to retrieve events since

        Returns:
            List of events matching the criteria
        """
        try:
            events = await self.event_store.get_events_by_type(event_type, since)
            return events
        except Exception as e:
            self.logger.error(f"Error getting events by type {event_type}: {e}")
            return []

    async def get_events_by_aggregate(
        self, aggregate_id: str, event_types: Optional[List[str]] = None
    ) -> List[DomainEvent]:
        """
        Get all events for a specific aggregate from the event store.

        Args:
            aggregate_id: The ID of the aggregate to get events for
            event_types: Optional list of event types to filter by

        Returns:
            List of events for the aggregate
        """
        try:
            events = await self.event_store.get_events_by_aggregate_id(
                aggregate_id, event_types
            )
            return events
        except Exception as e:
            self.logger.error(f"Error getting events for aggregate {aggregate_id}: {e}")
            return []

    def get_repository(self, aggregate_type: Type[A]) -> EventSourcedRepository[A]:
        """
        Get an event-sourced repository for a specific aggregate type.

        Args:
            aggregate_type: The type of aggregate the repository will manage

        Returns:
            An event-sourced repository for the aggregate type
        """
        return EventSourcedRepository(aggregate_type, self.event_store)

    @classmethod
    def create_event_store(
        cls, event_type: Type[T], schema: str = "public"
    ) -> PostgresEventStore[T]:
        """
        Create a PostgreSQL event store for a specific event type.

        Args:
            event_type: The type of events the store will handle
            schema: Optional database schema to use

        Returns:
            A configured PostgreSQL event store
        """
        return PostgresEventStore(event_type, schema=schema)


# Create default instance
default_integration = EventStoreIntegration()


def get_event_store_integration() -> EventStoreIntegration:
    """Get the default event store integration instance."""
    return default_integration


@inject_dependency
def get_event_sourced_repository(
    aggregate_type: Type[A], integration: EventStoreIntegration = None
) -> EventSourcedRepository[A]:
    """
    Get an event-sourced repository for a specific aggregate type.

    This function is injectable with the dependency injection system.

    Args:
        aggregate_type: The type of aggregate the repository will manage
        integration: Optional event store integration instance

    Returns:
        An event-sourced repository for the aggregate type
    """
    if integration is None:
        integration = get_event_store_integration()

    return integration.get_repository(aggregate_type)
