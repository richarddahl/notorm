"""
Event-driven architecture implementation for the Uno framework.

This module provides a comprehensive event system for the domain model,
supporting both synchronous and asynchronous event handling, as well as
event persistence and reliable processing.
"""

import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any, Dict, Generic, List, Optional, Set, Type, TypeVar, 
    Callable, Awaitable, Union, Pattern, cast
)
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# Type variables
T = TypeVar('T', bound='DomainEvent')
HandlerFnT = TypeVar('HandlerFnT')


class EventPriority(Enum):
    """Priority levels for event handling."""
    
    HIGH = auto()
    NORMAL = auto()
    LOW = auto()


class DomainEvent(BaseModel):
    """
    Base class for domain events.
    
    Domain events represent significant occurrences within the domain model.
    They are immutable records of something that happened.
    """
    
    model_config = ConfigDict(frozen=True)
    
    # Standard event metadata
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(default="domain_event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    version: int = 1
    
    # Optional correlation and causation IDs for event tracing
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    # Optional topic for routing
    topic: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create event from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "DomainEvent":
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def with_metadata(
        self,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> "DomainEvent":
        """
        Create a copy of the event with additional metadata.
        
        Args:
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional causation ID for event causality chains
            topic: Optional topic for routing
            
        Returns:
            A new event instance with the additional metadata
        """
        data = self.to_dict()
        
        if correlation_id:
            data["correlation_id"] = correlation_id
        
        if causation_id:
            data["causation_id"] = causation_id
        
        if topic:
            data["topic"] = topic
        
        return self.__class__(**data)


class EventHandler(Generic[T], ABC):
    """
    Abstract base class for event handlers.
    
    Event handlers process domain events by executing business logic
    in response to the events.
    """
    
    def __init__(self, event_type: Type[T], name: Optional[str] = None):
        """
        Initialize the event handler.
        
        Args:
            event_type: The type of event this handler can process
            name: Optional name for the handler, defaults to the class name
        """
        self.event_type = event_type
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    async def handle(self, event: T) -> None:
        """
        Handle an event.
        
        Args:
            event: The event to handle
        """
        pass
    
    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can handle the given event.
        
        Args:
            event: The event to check
            
        Returns:
            True if this handler can handle the event, False otherwise
        """
        return isinstance(event, self.event_type)


# Type aliases for event handler functions
SyncEventHandler = Callable[[T], None]
AsyncEventHandler = Callable[[T], Awaitable[None]]
EventHandlerFn = Union[SyncEventHandler[T], AsyncEventHandler[T]]


class EventSubscription(Generic[T]):
    """
    Event subscription holding a handler function or object.
    
    This class tracks a subscription for a specific event type or topic,
    along with its handler function or object.
    """
    
    def __init__(
        self,
        handler: Union[EventHandler[T], EventHandlerFn[T]],
        event_type: Optional[Type[T]] = None,
        topic_pattern: Optional[Union[str, Pattern]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        is_async: Optional[bool] = None,
    ):
        """
        Initialize the event subscription.
        
        Args:
            handler: The event handler function or object
            event_type: The type of event this subscription is for
            topic_pattern: Optional topic pattern for topic-based routing
            priority: The priority of this subscription
            is_async: Whether the handler is asynchronous (auto-detected if None)
        """
        self.handler = handler
        self.event_type = event_type
        self.priority = priority
        
        # Compile topic pattern if provided as string
        if isinstance(topic_pattern, str):
            self.topic_pattern = re.compile(topic_pattern)
        else:
            self.topic_pattern = topic_pattern
        
        # Auto-detect if handler is async
        if is_async is None:
            self.is_async = asyncio.iscoroutinefunction(
                handler.handle if isinstance(handler, EventHandler) else handler
            )
        else:
            self.is_async = is_async
    
    def matches_event(self, event: DomainEvent) -> bool:
        """
        Check if this subscription matches the given event.
        
        Args:
            event: The event to check
            
        Returns:
            True if this subscription matches the event, False otherwise
        """
        # Check event type
        if self.event_type and not isinstance(event, self.event_type):
            return False
        
        # Check topic pattern
        if self.topic_pattern and event.topic:
            if isinstance(self.topic_pattern, Pattern):
                return bool(self.topic_pattern.match(event.topic))
        
        return True
    
    async def invoke(self, event: DomainEvent) -> None:
        """
        Invoke the handler for the given event.
        
        Args:
            event: The event to handle
        """
        # Cast event to the expected type
        typed_event = cast(T, event)
        
        if isinstance(self.handler, EventHandler):
            # Handler object
            await self.handler.handle(typed_event)
        elif self.is_async:
            # Async handler function
            await self.handler(typed_event)
        else:
            # Sync handler function - run in executor
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.handler, typed_event)


class EventBus:
    """
    Event bus for publishing and subscribing to domain events.
    
    The event bus enables loosely coupled communication between different
    parts of the application using an event-driven architecture.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the event bus.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._subscriptions: List[EventSubscription] = []
        self._publish_time: Dict[str, float] = {}  # Event type -> last publish time
    
    def subscribe(
        self,
        handler: Union[EventHandler[T], EventHandlerFn[T]],
        event_type: Optional[Type[T]] = None,
        topic_pattern: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """
        Subscribe to events of a specific type or topic.
        
        Args:
            handler: Event handler function or object
            event_type: The type of event to subscribe to
            topic_pattern: Optional topic pattern for topic-based routing
            priority: Handler priority
        """
        # If handler is an EventHandler, use its event_type if not provided
        if isinstance(handler, EventHandler) and event_type is None:
            event_type = handler.event_type
        
        # Create subscription
        subscription = EventSubscription(
            handler=handler,
            event_type=event_type,
            topic_pattern=topic_pattern,
            priority=priority,
        )
        
        # Add subscription to list, sorted by priority
        self._subscriptions.append(subscription)
        self._subscriptions.sort(key=lambda s: s.priority.value)
        
        self.logger.debug(
            f"Subscribed handler to events: "
            f"event_type={event_type.__name__ if event_type else 'Any'}, "
            f"topic_pattern={topic_pattern or 'Any'}, "
            f"priority={priority.name}"
        )
    
    def unsubscribe(
        self,
        handler: Union[EventHandler[T], EventHandlerFn[T]],
        event_type: Optional[Type[T]] = None,
        topic_pattern: Optional[str] = None,
    ) -> None:
        """
        Unsubscribe from events of a specific type or topic.
        
        Args:
            handler: Event handler function or object
            event_type: The type of event to unsubscribe from
            topic_pattern: Optional topic pattern for topic-based routing
        """
        # Compile topic pattern if provided
        compiled_pattern = re.compile(topic_pattern) if topic_pattern else None
        
        # Remove matching subscriptions
        removed = False
        self._subscriptions = [
            s for s in self._subscriptions
            if not (
                s.handler == handler and
                (event_type is None or s.event_type == event_type) and
                (topic_pattern is None or s.topic_pattern == compiled_pattern)
            ) or not removed and (removed := True)
        ]
        
        if removed:
            self.logger.debug(
                f"Unsubscribed handler from events: "
                f"event_type={event_type.__name__ if event_type else 'Any'}, "
                f"topic_pattern={topic_pattern or 'Any'}"
            )
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all matching subscribers.
        
        Args:
            event: The event to publish
        """
        event_type_name = event.__class__.__name__
        topic = event.topic or ""
        
        self.logger.debug(f"Publishing event: {event_type_name} (topic={topic})")
        self._publish_time[event_type_name] = time.time()
        
        # Get matching subscriptions
        matching_subscriptions = [
            s for s in self._subscriptions
            if s.matches_event(event)
        ]
        
        if not matching_subscriptions:
            self.logger.debug(f"No handlers registered for event: {event_type_name}")
            return
        
        # Invoke handlers
        for subscription in matching_subscriptions:
            try:
                await subscription.invoke(event)
            except Exception as e:
                self.logger.error(f"Error in event handler: {str(e)}")
    
    async def publish_many(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple events.
        
        Args:
            events: The events to publish
        """
        for event in events:
            await self.publish(event)


class EventStore(ABC):
    """
    Abstract base class for event stores.
    
    Event stores persist domain events for reliable processing and
    event sourcing.
    """
    
    @abstractmethod
    async def append(self, event: DomainEvent) -> None:
        """
        Append an event to the event store.
        
        Args:
            event: The event to append
        """
        pass
    
    @abstractmethod
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        since_version: Optional[int] = None,
        since_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[DomainEvent]:
        """
        Get events from the event store.
        
        Args:
            aggregate_id: Optional aggregate ID to filter by
            aggregate_type: Optional aggregate type to filter by
            since_version: Optional minimum version to filter by
            since_timestamp: Optional minimum timestamp to filter by
            limit: Optional maximum number of events to return
            
        Returns:
            List of events matching the criteria
        """
        pass


class InMemoryEventStore(EventStore):
    """
    In-memory implementation of the event store.
    
    This implementation stores events in memory, which is useful for
    testing and simple applications.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the in-memory event store.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._events: List[DomainEvent] = []
    
    async def append(self, event: DomainEvent) -> None:
        """
        Append an event to the event store.
        
        Args:
            event: The event to append
        """
        self._events.append(event)
        self.logger.debug(f"Event appended to store: {event.__class__.__name__}")
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        since_version: Optional[int] = None,
        since_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[DomainEvent]:
        """
        Get events from the event store.
        
        Args:
            aggregate_id: Optional aggregate ID to filter by
            aggregate_type: Optional aggregate type to filter by
            since_version: Optional minimum version to filter by
            since_timestamp: Optional minimum timestamp to filter by
            limit: Optional maximum number of events to return
            
        Returns:
            List of events matching the criteria
        """
        filtered_events = self._events.copy()
        
        # Apply filters
        if aggregate_id:
            filtered_events = [e for e in filtered_events if e.aggregate_id == aggregate_id]
        
        if aggregate_type:
            filtered_events = [e for e in filtered_events if e.aggregate_type == aggregate_type]
        
        if since_version:
            filtered_events = [e for e in filtered_events if e.version >= since_version]
        
        if since_timestamp:
            filtered_events = [e for e in filtered_events if e.timestamp >= since_timestamp]
        
        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.timestamp)
        
        # Apply limit
        if limit:
            filtered_events = filtered_events[:limit]
        
        return filtered_events


class EventPublisher:
    """
    Helper class for publishing events.
    
    This class provides a convenient interface for collecting and publishing
    events to an event bus.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        event_store: Optional[EventStore] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the event publisher.
        
        Args:
            event_bus: The event bus to publish events to
            event_store: Optional event store for event persistence
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.event_store = event_store
        self.logger = logger or logging.getLogger(__name__)
        self._pending_events: List[DomainEvent] = []
    
    def add(self, event: DomainEvent) -> None:
        """
        Add an event to be published later.
        
        Args:
            event: The event to add
        """
        self._pending_events.append(event)
    
    def add_many(self, events: List[DomainEvent]) -> None:
        """
        Add multiple events to be published later.
        
        Args:
            events: The events to add
        """
        self._pending_events.extend(events)
    
    async def publish_pending(self) -> None:
        """
        Publish all pending events.
        
        This method publishes all events that have been added with add()
        or add_many() and clears the list of pending events.
        """
        events = self._pending_events.copy()
        self._pending_events.clear()
        
        if not events:
            return
        
        # Persist events if event store is available
        if self.event_store:
            for event in events:
                await self.event_store.append(event)
        
        # Publish events to the event bus
        await self.event_bus.publish_many(events)
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event immediately.
        
        Args:
            event: The event to publish
        """
        # Persist event if event store is available
        if self.event_store:
            await self.event_store.append(event)
        
        # Publish event to the event bus
        await self.event_bus.publish(event)
    
    async def publish_many(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple events immediately.
        
        Args:
            events: The events to publish
        """
        # Persist events if event store is available
        if self.event_store:
            for event in events:
                await self.event_store.append(event)
        
        # Publish events to the event bus
        await self.event_bus.publish_many(events)


# Create default instances
default_event_bus = EventBus()
default_event_store = InMemoryEventStore()
default_publisher = EventPublisher(default_event_bus, default_event_store)


def get_event_bus() -> EventBus:
    """Get the default event bus."""
    return default_event_bus


def get_event_store() -> EventStore:
    """Get the default event store."""
    return default_event_store


def get_event_publisher() -> EventPublisher:
    """Get the default event publisher."""
    return default_publisher


def subscribe(
    event_type: Optional[Type[DomainEvent]] = None,
    topic_pattern: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
) -> Callable[[HandlerFnT], HandlerFnT]:
    """
    Decorator for subscribing functions or methods to events.
    
    This decorator registers a function or method as an event handler
    for a specific event type or topic.
    
    Args:
        event_type: The type of event to subscribe to
        topic_pattern: Optional topic pattern for topic-based routing
        priority: Handler priority
        
    Returns:
        The decorated function or method
    """
    def decorator(handler: HandlerFnT) -> HandlerFnT:
        # Subscribe the handler to the event bus
        default_event_bus.subscribe(
            handler=cast(Any, handler),
            event_type=event_type,
            topic_pattern=topic_pattern,
            priority=priority,
        )
        return handler
    return decorator