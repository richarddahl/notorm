"""
Unified event system for the Uno framework.

This module provides a comprehensive event system for implementing event-driven
architecture, supporting both synchronous and asynchronous event processing with
strong typing, event persistence, and reliable delivery.
"""

import asyncio
import inspect
import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from enum import Enum, auto
from typing import (
    Any,
    Dict,
    List,
    Set,
    Type,
    TypeVar,
    Generic,
    Protocol,
    Callable,
    Awaitable,
    Optional,
    Union,
    cast,
    get_type_hints,
    Pattern,
    runtime_checkable,
)
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from uno.core.errors import UnoError, ErrorCategory, with_async_error_context


# =============================================================================
# Type Variables and Protocols
# =============================================================================

T = TypeVar("T")
E = TypeVar("E", bound="UnoDomainEvent")
TEvent = TypeVar("TEvent", bound="UnoDomainEvent")
HandlerFnT = TypeVar("HandlerFnT")


@runtime_checkable
class DomainEventProtocol(Protocol):
    """Protocol interface for domain events."""

    event_id: str
    event_type: str
    timestamp: datetime
    aggregate_id: Optional[str]
    aggregate_type: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEventProtocol":
        """Create event from dictionary."""
        ...


# =============================================================================
# Event Priorities
# =============================================================================


class EventPriority(Enum):
    """Priorities for event handlers to determine execution order."""

    HIGH = auto()  # Execute before normal handlers
    NORMAL = auto()  # Default priority
    LOW = auto()  # Execute after normal handlers


# =============================================================================
# Base Event Implementation
# =============================================================================


class UnoDomainEvent(BaseModel):
    """
    Base class for domain events.

    Domain events represent significant occurrences within the domain model.
    They are immutable records of something that happened and are named in the past tense.
    """

    model_config = ConfigDict(frozen=True)

    # Standard event metadata
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(
        default_factory=lambda: _cls_name_to_event_type(UnoDomainEvent.__name__)
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    version: int = 1

    # Optional correlation and causation IDs for event tracing
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    # Optional topic for routing
    topic: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary.

        Returns:
            Dictionary representation of the event
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnoDomainEvent":
        """
        Create event from dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            Event instance
        """
        return cls(**data)

    def to_json(self) -> str:
        """
        Convert event to JSON string.

        Returns:
            JSON string representation of the event
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "UnoDomainEvent":
        """
        Create event from JSON string.

        Args:
            json_str: JSON string representation of the event

        Returns:
            Event instance
        """
        return cls.from_dict(json.loads(json_str))

    def with_metadata(
        self,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        topic: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
    ) -> "UnoDomainEvent":
        """
        Create a copy of the event with additional metadata.

        Args:
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional causation ID for event causality chains
            topic: Optional topic for routing
            aggregate_id: Optional aggregate ID
            aggregate_type: Optional aggregate type

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

        if aggregate_id:
            data["aggregate_id"] = aggregate_id

        if aggregate_type:
            data["aggregate_type"] = aggregate_type

        return self.__class__(**data)


# =============================================================================
# Event Handler Base Class
# =============================================================================


class EventHandler(Generic[E], ABC):
    """
    Abstract base class for event handlers.

    Event handlers process domain events by executing business logic
    in response to the events.
    """

    def __init__(self, event_type: Type[E], name: Optional[str] = None):
        """
        Initialize the event handler.

        Args:
            event_type: The type of event this handler can process
            name: Optional name for the handler, defaults to the class name
        """
        self.event_type = event_type
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def handle(self, event: E) -> None:
        """
        Handle an event.

        Args:
            event: The event to handle
        """
        pass

    def can_handle(self, event: UnoDomainEvent) -> bool:
        """
        Check if this handler can handle the given event.

        Args:
            event: The event to check

        Returns:
            True if this handler can handle the event, False otherwise
        """
        return isinstance(event, self.event_type)


# =============================================================================
# Type aliases for event handler functions
# =============================================================================

SyncEventHandler = Callable[[E], None]
AsyncEventHandler = Callable[[E], Awaitable[None]]
EventHandlerFn = Union[SyncEventHandler[E], AsyncEventHandler[E]]


# =============================================================================
# Event Handler Wrapper
# =============================================================================


class EventHandlerWrapper(Generic[TEvent]):
    """
    Wrapper for event handlers that provides metadata and execution control.

    This wrapper stores information about the handler, such as its priority,
    and provides methods for executing the handler with proper error handling.
    """

    def __init__(
        self,
        handler: Union[EventHandler[TEvent], EventHandlerFn[TEvent]],
        priority: EventPriority = EventPriority.NORMAL,
        is_async: Optional[bool] = None,
    ):
        """
        Initialize an event handler wrapper.

        Args:
            handler: The event handler function or instance
            priority: The handler's execution priority
            is_async: Whether the handler is async (auto-detected if None)
        """
        self.handler = handler
        self.priority = priority

        # Auto-detect if the handler is async
        if is_async is None:
            if isinstance(handler, EventHandler):
                is_async = asyncio.iscoroutinefunction(handler.handle)
            else:
                is_async = asyncio.iscoroutinefunction(handler)

        self.is_async = is_async

        # Get handler name for better logging
        if isinstance(handler, EventHandler):
            self.handler_name = f"{handler.__class__.__name__}.handle"
        elif hasattr(handler, "__name__"):
            self.handler_name = handler.__name__
        else:
            self.handler_name = str(handler)

    async def execute(self, event: TEvent) -> None:
        """
        Execute the handler with the given event.

        Args:
            event: The event to handle

        Raises:
            UnoError: If the handler fails
        """
        try:
            # Add context to any errors
            async with with_async_error_context(
                event_type=event.event_type,
                event_id=event.event_id,
                handler=self.handler_name,
            ):
                if isinstance(self.handler, EventHandler):
                    # Class-based handler
                    result = self.handler.handle(event)
                else:
                    # Function-based handler
                    result = self.handler(event)

                # Await if the handler is async
                if self.is_async:
                    await result
                elif asyncio.iscoroutine(result):
                    # Handler function that returns a coroutine but was not marked as async
                    await result

        except Exception as e:
            # Wrap in UnoError if not already
            if not isinstance(e, UnoError):
                raise UnoError(
                    message=f"Error handling event {event.event_type}: {str(e)}",
                    error_code="EVENT_HANDLER_ERROR",
                    category=ErrorCategory.UNEXPECTED,
                    context={
                        "handler": self.handler_name,
                        "cause": str(e),
                        "event_id": event.event_id,
                    },
                )
            raise


# =============================================================================
# Event Subscription
# =============================================================================


class EventSubscription(Generic[TEvent]):
    """
    Event subscription holding a handler function or object.

    This class tracks a subscription for a specific event type or topic,
    along with its handler function or object.
    """

    def __init__(
        self,
        handler: Union[EventHandler[TEvent], EventHandlerFn[TEvent]],
        event_type: Optional[Type[TEvent]] = None,
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
        self.handler_wrapper = EventHandlerWrapper(
            handler=handler, priority=priority, is_async=is_async
        )
        self.event_type = event_type

        # Compile topic pattern if provided as string
        if isinstance(topic_pattern, str):
            self.topic_pattern = re.compile(topic_pattern)
        else:
            self.topic_pattern = topic_pattern

    def matches_event(self, event: UnoDomainEvent) -> bool:
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

    async def invoke(self, event: UnoDomainEvent) -> None:
        """
        Invoke the handler for the given event.

        Args:
            event: The event to handle
        """
        await self.handler_wrapper.execute(cast(TEvent, event))


# =============================================================================
# Event Bus Implementation
# =============================================================================


class EventBus:
    """
    Event bus for publishing and subscribing to domain events.

    The event bus enables loosely coupled communication between different
    parts of the application using an event-driven architecture.
    """

    def __init__(
        self, logger: Optional[logging.Logger] = None, max_concurrency: int = 10
    ):
        """
        Initialize the event bus.

        Args:
            logger: Optional logger for diagnostic information
            max_concurrency: Maximum number of concurrent event handlers when dispatching async
        """
        self.logger = logger or logging.getLogger("uno.events")
        self.max_concurrency = max_concurrency
        self._subscriptions: List[EventSubscription] = []
        self._publish_time: Dict[str, float] = {}  # Event type -> last publish time

    def subscribe(
        self,
        event_type: Type[E],
        handler: Union[EventHandler[E], EventHandlerFn[E]],
        priority: EventPriority = EventPriority.NORMAL,
        topic_pattern: Optional[str] = None,
    ) -> None:
        """
        Subscribe a handler to events of a specific type or topic.

        Args:
            event_type: The type of event to subscribe to
            handler: Event handler function or object
            priority: Handler priority
            topic_pattern: Optional topic pattern for topic-based routing
        """
        # Create subscription
        subscription = EventSubscription(
            handler=handler,
            event_type=event_type,
            topic_pattern=topic_pattern,
            priority=priority,
        )

        # Add subscription to list
        self._subscriptions.append(subscription)

        # Sort subscriptions by priority
        self._subscriptions.sort(key=lambda s: s.handler_wrapper.priority.value)

        handler_name = (
            handler.__class__.__name__
            if isinstance(handler, EventHandler)
            else getattr(handler, "__name__", str(handler))
        )
        self.logger.debug(
            f"Subscribed handler {handler_name} to events: "
            f"event_type={event_type.__name__ if event_type else 'Any'}, "
            f"topic_pattern={topic_pattern or 'Any'}, "
            f"priority={priority.name}"
        )

    def unsubscribe(
        self,
        event_type: Type[E],
        handler: Union[EventHandler[E], EventHandlerFn[E]],
        topic_pattern: Optional[str] = None,
    ) -> None:
        """
        Unsubscribe a handler from events of a specific type or topic.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function or object to unsubscribe
            topic_pattern: Optional topic pattern for topic-based routing
        """
        # Compile topic pattern if provided
        compiled_pattern = re.compile(topic_pattern) if topic_pattern else None

        # Find and remove matching subscriptions
        initial_count = len(self._subscriptions)

        # Function to check if a subscription matches the criteria
        def matches_criteria(subscription: EventSubscription) -> bool:
            handler_wrapper = subscription.handler_wrapper
            sub_handler = handler_wrapper.handler

            # Check handler identity
            if isinstance(handler, EventHandler) and isinstance(
                sub_handler, EventHandler
            ):
                # For class-based handlers, check identity
                if id(sub_handler) != id(handler):
                    return False
            elif sub_handler != handler:
                # For function-based handlers, check equality
                return False

            # Check event type
            if event_type is not None and subscription.event_type != event_type:
                return False

            # Check topic pattern
            if (
                topic_pattern is not None
                and subscription.topic_pattern != compiled_pattern
            ):
                return False

            return True

        # Remove matching subscriptions
        self._subscriptions = [
            s for s in self._subscriptions if not matches_criteria(s)
        ]

        if len(self._subscriptions) < initial_count:
            handler_name = (
                handler.__class__.__name__
                if isinstance(handler, EventHandler)
                else getattr(handler, "__name__", str(handler))
            )
            self.logger.debug(
                f"Unsubscribed handler {handler_name} from events: "
                f"event_type={event_type.__name__ if event_type else 'Any'}, "
                f"topic_pattern={topic_pattern or 'Any'}"
            )

    async def publish(self, event: UnoDomainEvent) -> None:
        """
        Publish an event to all matching subscribers.

        This method delivers the event to all handlers subscribed to its type,
        respecting their priority order.

        Args:
            event: The event to publish
        """
        event_type_name = event.__class__.__name__
        topic = event.topic or ""

        self.logger.debug(
            f"Publishing event: {event_type_name} (topic={topic}, id={event.event_id})"
        )

        # Get matching subscriptions
        matching_subscriptions = [
            s for s in self._subscriptions if s.matches_event(event)
        ]

        if not matching_subscriptions:
            self.logger.debug(f"No handlers registered for event: {event_type_name}")
            return

        # Sort subscriptions by priority (although they should already be sorted)
        matching_subscriptions.sort(key=lambda s: s.handler_wrapper.priority.value)

        # Invoke handlers sequentially in priority order
        for subscription in matching_subscriptions:
            try:
                await subscription.invoke(event)
            except Exception as e:
                self.logger.error(f"Error in event handler: {str(e)}")
                # Don't re-raise to ensure all handlers get a chance to execute

    async def publish_async(self, event: UnoDomainEvent) -> None:
        """
        Publish an event to all subscribed handlers asynchronously.

        This method delivers the event to all handlers concurrently, with
        a maximum level of concurrency defined by max_concurrency.

        Args:
            event: The event to publish
        """
        event_type_name = event.__class__.__name__
        topic = event.topic or ""

        self.logger.debug(
            f"Publishing event {event_type_name} (id={event.event_id}, topic={topic}) asynchronously"
        )

        # Get matching subscriptions
        matching_subscriptions = [
            s for s in self._subscriptions if s.matches_event(event)
        ]

        if not matching_subscriptions:
            self.logger.debug(f"No handlers registered for event: {event_type_name}")
            return

        # Sort subscriptions by priority
        matching_subscriptions.sort(key=lambda s: s.handler_wrapper.priority.value)

        # Group subscriptions by priority to maintain priority ordering
        # while allowing concurrency within each priority level
        priority_groups: Dict[EventPriority, List[EventSubscription]] = {}
        for sub in matching_subscriptions:
            priority = sub.handler_wrapper.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(sub)

        # Process each priority group in order
        for priority in sorted(priority_groups.keys(), key=lambda p: p.value):
            group = priority_groups[priority]

            # Create tasks for each handler in this priority group
            tasks = [subscription.invoke(event) for subscription in group]

            # Execute tasks with semaphore to limit concurrency
            semaphore = asyncio.Semaphore(self.max_concurrency)

            async def execute_with_semaphore(task):
                async with semaphore:
                    return await task

            # Wait for all tasks in this priority group to complete before moving to the next
            await asyncio.gather(
                *(execute_with_semaphore(task) for task in tasks),
                return_exceptions=True,  # Don't let one failure prevent others from running
            )

    async def publish_many(self, events: List[UnoDomainEvent]) -> None:
        """
        Publish multiple events sequentially.

        Args:
            events: The events to publish
        """
        for event in events:
            await self.publish(event)

    async def publish_many_async(self, events: List[UnoDomainEvent]) -> None:
        """
        Publish multiple events concurrently.

        Args:
            events: The events to publish
        """
        await asyncio.gather(*(self.publish_async(event) for event in events))


# =============================================================================
# Event Publisher
# =============================================================================


class EventPublisher:
    """
    Helper class for publishing events.

    This class provides a convenient interface for collecting and publishing
    events to an event bus.
    """

    def __init__(
        self,
        event_bus: EventBus,
        event_store: Optional["EventStore"] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the event publisher.

        Args:
            event_bus: The event bus to publish events to
            event_store: Optional event store for event persistence
            logger: Optional logger for diagnostic information
        """
        self.event_bus = event_bus
        self.event_store = event_store
        self.logger = logger or logging.getLogger("uno.events")
        self._collected_events: List[UnoDomainEvent] = []

    def collect(self, event: UnoDomainEvent) -> None:
        """
        Collect an event for later batch publishing.

        Args:
            event: The event to collect
        """
        self._collected_events.append(event)

    def collect_many(self, events: List[UnoDomainEvent]) -> None:
        """
        Collect multiple events for later batch publishing.

        Args:
            events: The events to collect
        """
        self._collected_events.extend(events)

    async def publish_collected(self) -> None:
        """
        Publish all collected events sequentially.

        This method publishes all events that have been collected and
        clears the list of collected events.
        """
        events = self._collected_events.copy()
        self._collected_events.clear()

        if not events:
            return

        # Persist events if event store is available
        if self.event_store:
            for event in events:
                await self.event_store.save_event(event)

        # Publish events to the event bus
        await self.event_bus.publish_many(events)

    async def publish_collected_async(self) -> None:
        """
        Publish all collected events asynchronously.

        This method publishes all events that have been collected concurrently
        and clears the list of collected events.
        """
        events = self._collected_events.copy()
        self._collected_events.clear()

        if not events:
            return

        # Persist events if event store is available
        if self.event_store:
            # We still persist serially to maintain ordering in the event store
            for event in events:
                await self.event_store.save_event(event)

        # Publish events to the event bus concurrently
        await self.event_bus.publish_many_async(events)

    def clear_collected(self) -> None:
        """Clear all collected events without publishing them."""
        self._collected_events.clear()

    async def publish(self, event: UnoDomainEvent) -> None:
        """
        Publish an event immediately.

        Args:
            event: The event to publish
        """
        # Persist event if event store is available
        if self.event_store:
            await self.event_store.save_event(event)

        # Publish event to the event bus
        await self.event_bus.publish(event)

    async def publish_async(self, event: UnoDomainEvent) -> None:
        """
        Publish an event asynchronously.

        Args:
            event: The event to publish
        """
        # Persist event if event store is available
        if self.event_store:
            await self.event_store.save_event(event)

        # Publish event to the event bus asynchronously
        await self.event_bus.publish_async(event)

    def publish_sync(self, event: UnoDomainEvent) -> None:
        """
        Publish an event synchronously, blocking until all handlers complete.

        Args:
            event: The event to publish
        """
        # Create a new event loop if needed
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.publish(event))
        else:
            # Use running event loop
            if loop.is_running():
                # Create a future and run it until complete
                future = asyncio.run_coroutine_threadsafe(self.publish(event), loop)
                future.result()  # Wait for completion
            else:
                # Run the coroutine until complete
                loop.run_until_complete(self.publish(event))

    async def publish_many(self, events: List[UnoDomainEvent]) -> None:
        """
        Publish multiple events immediately.

        Args:
            events: The events to publish
        """
        # Persist events if event store is available
        if self.event_store:
            for event in events:
                await self.event_store.save_event(event)

        # Publish events to the event bus
        await self.event_bus.publish_many(events)

    async def publish_many_async(self, events: List[UnoDomainEvent]) -> None:
        """
        Publish multiple events asynchronously.

        Args:
            events: The events to publish
        """
        # Persist events if event store is available
        if self.event_store:
            for event in events:
                await self.event_store.save_event(event)

        # Publish events to the event bus asynchronously
        await self.event_bus.publish_many_async(events)


# =============================================================================
# Event Store Base Class
# =============================================================================


class EventStore(Generic[E]):
    """
    Abstract base class for event stores.

    Event stores persist domain events for event sourcing, auditing,
    and reliable processing.
    """

    async def save_event(self, event: E) -> None:
        """
        Save a domain event to the store.

        Args:
            event: The domain event to save
        """
        raise NotImplementedError

    async def get_events_by_aggregate_id(
        self, aggregate_id: str, event_types: Optional[List[str]] = None
    ) -> List[E]:
        """
        Get all events for a specific aggregate ID.

        Args:
            aggregate_id: The ID of the aggregate to get events for
            event_types: Optional list of event types to filter by

        Returns:
            List of events for the aggregate
        """
        raise NotImplementedError

    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[E]:
        """
        Get all events of a specific type.

        Args:
            event_type: The type of events to retrieve
            since: Optional timestamp to retrieve events since

        Returns:
            List of events matching the criteria
        """
        raise NotImplementedError


# =============================================================================
# In-memory Event Store Implementation
# =============================================================================


class InMemoryEventStore(EventStore[E]):
    """
    In-memory implementation of the event store.

    This implementation stores events in memory, which is useful for
    testing and simple applications.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the in-memory event store.

        Args:
            logger: Optional logger for diagnostic information
        """
        self.logger = logger or logging.getLogger("uno.events")
        self.events: List[E] = []

    async def save_event(self, event: E) -> None:
        """
        Save a domain event to the in-memory store.

        Args:
            event: The domain event to save
        """
        self.events.append(event)
        self.logger.debug(f"Event saved to in-memory store: {event.__class__.__name__}")

    async def get_events_by_aggregate_id(
        self, aggregate_id: str, event_types: Optional[List[str]] = None
    ) -> List[E]:
        """
        Get all events for a specific aggregate ID.

        Args:
            aggregate_id: The ID of the aggregate to get events for
            event_types: Optional list of event types to filter by

        Returns:
            List of events for the aggregate
        """
        filtered_events = [
            e for e in self.events if getattr(e, "aggregate_id", None) == aggregate_id
        ]

        if event_types:
            filtered_events = [
                e for e in filtered_events if e.event_type in event_types
            ]

        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.timestamp)

        return filtered_events

    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[E]:
        """
        Get all events of a specific type.

        Args:
            event_type: The type of events to retrieve
            since: Optional timestamp to retrieve events since

        Returns:
            List of events matching the criteria
        """
        filtered_events = [e for e in self.events if e.event_type == event_type]

        if since:
            filtered_events = [e for e in filtered_events if e.timestamp >= since]

        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.timestamp)

        return filtered_events


# =============================================================================
# Event Handler Decorator
# =============================================================================


def event_handler(
    event_type: Optional[Type[UnoDomainEvent]] = None,
    priority: EventPriority = EventPriority.NORMAL,
    topic_pattern: Optional[str] = None,
):
    """
    Decorator for marking a function as an event handler.

    This decorator can be used to mark functions as event handlers and
    optionally specify the event type they handle and their priority.

    Args:
        event_type: The type of event to handle (inferred from type hints if None)
        priority: The handler's execution priority
        topic_pattern: Optional topic pattern for topic-based routing

    Returns:
        Decorated function with event handler metadata
    """

    def decorator(func):
        # If event_type is None, try to infer from type hints
        nonlocal event_type
        if event_type is None:
            hints = get_type_hints(func)
            # Find first parameter's type
            params = inspect.signature(func).parameters
            if params:
                first_param = next(iter(params.values()))
                if first_param.name in hints:
                    param_type = hints[first_param.name]
                    # For Protocols, we can't use issubclass directly
                    try:
                        if isinstance(param_type, type) and hasattr(
                            param_type, "__init__"
                        ):
                            # Only check for concrete types, not Protocol
                            event_type = param_type
                    except TypeError:
                        # This is likely a Protocol, which is fine - we'll skip direct type checking
                        pass

        # Store metadata on the function
        func.__event_handler__ = True
        func.__event_type__ = event_type
        func.__event_priority__ = priority
        func.__event_topic_pattern__ = topic_pattern

        return func

    # Allow using as @event_handler without calling
    if callable(event_type):
        func = event_type
        event_type = None
        return decorator(func)

    return decorator


# =============================================================================
# Event Subscriber Base Class
# =============================================================================


class EventSubscriber:
    """
    Base class for event subscribers.

    Event subscribers contain one or more event handlers and register
    them with the event bus when instantiated.
    """

    def __init__(self, event_bus: EventBus):
        """
        Initialize the event subscriber and register handlers.

        Args:
            event_bus: The event bus to register handlers with
        """
        self.event_bus = event_bus

        # Register all methods decorated with @event_handler
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "__event_handler__"):
                event_type = getattr(attr, "__event_type__")
                priority = getattr(attr, "__event_priority__", EventPriority.NORMAL)
                topic_pattern = getattr(attr, "__event_topic_pattern__", None)

                if event_type is not None:
                    event_bus.subscribe(
                        event_type=event_type,
                        handler=attr,
                        priority=priority,
                        topic_pattern=topic_pattern,
                    )


# =============================================================================
# Event Handler Scanner
# =============================================================================


class EventHandlerScanner:
    """
    Scanner for finding and registering event handlers.

    This class helps automate the process of finding event handlers in modules
    and registering them with the event bus.
    """

    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        """
        Initialize the scanner.

        Args:
            event_bus: The event bus to register handlers with
            logger: Optional logger for diagnostic information
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger("uno.events")

    def scan_module(self, module) -> int:
        """
        Scan a module for event handlers and register them.

        Args:
            module: The module to scan

        Returns:
            Number of handlers registered
        """
        count = 0

        # Find all members in the module
        for name, obj in inspect.getmembers(module):
            # Handle function-based handlers
            if inspect.isfunction(obj) and hasattr(obj, "__event_handler__"):
                event_type = getattr(obj, "__event_type__", None)
                priority = getattr(obj, "__event_priority__", EventPriority.NORMAL)
                topic_pattern = getattr(obj, "__event_topic_pattern__", None)

                if event_type is not None:
                    self.event_bus.subscribe(
                        event_type=event_type,
                        handler=obj,
                        priority=priority,
                        topic_pattern=topic_pattern,
                    )
                    count += 1
                    self.logger.debug(
                        f"Registered function handler {obj.__name__} for {event_type.__name__}"
                    )

            # Handle class-based handlers
            elif (
                inspect.isclass(obj)
                and hasattr(obj, "handle")
                and inspect.isfunction(getattr(obj, "handle"))
            ):
                # Try to find event type from handle method
                handle_method = getattr(obj, "handle")
                hints = get_type_hints(handle_method)

                params = inspect.signature(handle_method).parameters
                if len(params) >= 2:  # At least self + event
                    # Skip self
                    params_iter = iter(params.values())
                    next(params_iter)  # Skip self

                    if params_iter:
                        first_param = next(params_iter)
                        if first_param.name in hints:
                            param_type = hints[first_param.name]
                            # For Protocols with non-method members, we can't use issubclass
                            try:
                                if isinstance(param_type, type) and hasattr(
                                    param_type, "__init__"
                                ):
                                    # Create instance
                                    instance = obj()

                                    # Get priority if specified
                                    priority = getattr(
                                        handle_method,
                                        "__event_priority__",
                                        getattr(
                                            obj,
                                            "__event_priority__",
                                            EventPriority.NORMAL,
                                        ),
                                    )

                                    # Get topic pattern if specified
                                    topic_pattern = getattr(
                                        handle_method,
                                        "__event_topic_pattern__",
                                        getattr(obj, "__event_topic_pattern__", None),
                                    )

                                    self.event_bus.subscribe(
                                        event_type=param_type,
                                        handler=instance,
                                        priority=priority,
                                        topic_pattern=topic_pattern,
                                    )
                                    count += 1
                                    self.logger.debug(
                                        f"Registered class handler {obj.__name__} for {param_type.__name__}"
                                    )
                            except TypeError:
                                # This is likely a Protocol with non-method members, which is fine
                                # Currently we skip these, but we could register them without type checking if needed
                                pass

        return count

    def scan_instance(self, instance) -> int:
        """
        Scan an instance for event handlers and register them.

        Args:
            instance: The instance to scan

        Returns:
            Number of handlers registered
        """
        count = 0

        # Find all methods in the instance
        for name, method in inspect.getmembers(instance, inspect.ismethod):
            if hasattr(method, "__event_handler__"):
                event_type = getattr(method, "__event_type__", None)
                priority = getattr(method, "__event_priority__", EventPriority.NORMAL)
                topic_pattern = getattr(method, "__event_topic_pattern__", None)

                if event_type is not None:
                    self.event_bus.subscribe(
                        event_type=event_type,
                        handler=method,
                        priority=priority,
                        topic_pattern=topic_pattern,
                    )
                    count += 1
                    self.logger.debug(
                        f"Registered method handler {instance.__class__.__name__}.{name} for {event_type.__name__}"
                    )

        return count


# =============================================================================
# Public API and Global Instances
# =============================================================================

# Global instances
_event_bus: Optional[EventBus] = None
_event_store: Optional[EventStore] = None
_event_publisher: Optional[EventPublisher] = None


def initialize_events(
    logger: Optional[logging.Logger] = None,
    max_concurrency: int = 10,
    in_memory_event_store: bool = True,
) -> None:
    """
    Initialize the global event system.

    Args:
        logger: Optional logger for diagnostic information
        max_concurrency: Maximum number of concurrent event handlers
        in_memory_event_store: Whether to create an in-memory event store

    Raises:
        UnoError: If the event system is already initialized
    """
    global _event_bus, _event_store, _event_publisher

    if _event_bus is not None:
        raise UnoError(
            message="Event system is already initialized",
            error_code="EVENT_SYSTEM_ALREADY_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )

    _event_bus = EventBus(logger, max_concurrency)

    if in_memory_event_store:
        _event_store = InMemoryEventStore(logger)

    _event_publisher = EventPublisher(_event_bus, _event_store, logger)


def reset_events() -> None:
    """
    Reset the global event system.

    This function is primarily intended for testing scenarios where
    you need to reset the event system between tests.
    """
    global _event_bus, _event_store, _event_publisher
    _event_bus = None
    _event_store = None
    _event_publisher = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Returns:
        The global event bus instance

    Raises:
        UnoError: If the event bus is not initialized
    """
    if _event_bus is None:
        initialize_events()
    return _event_bus


def get_event_store() -> Optional[EventStore]:
    """
    Get the global event store instance.

    Returns:
        The global event store instance, or None if no event store is configured
    """
    return _event_store


def get_event_publisher() -> EventPublisher:
    """
    Get the global event publisher instance.

    Returns:
        The global event publisher instance

    Raises:
        UnoError: If the event publisher is not initialized
    """
    if _event_publisher is None:
        initialize_events()
    return _event_publisher


def publish_event(event: UnoDomainEvent) -> None:
    """
    Publish an event using the global event publisher.

    This function publishes the event asynchronously, returning immediately
    while the event is processed in the background.

    Args:
        event: The event to publish
    """
    asyncio.create_task(get_event_publisher().publish(event))


def publish_event_sync(event: UnoDomainEvent) -> None:
    """
    Publish an event synchronously using the global event publisher.

    This function blocks until all event handlers have completed processing.

    Args:
        event: The event to publish
    """
    get_event_publisher().publish_sync(event)


async def publish_event_async(event: UnoDomainEvent) -> None:
    """
    Publish an event asynchronously using the global event publisher.

    Args:
        event: The event to publish
    """
    await get_event_publisher().publish_async(event)


def collect_event(event: UnoDomainEvent) -> None:
    """
    Collect an event for later batch publishing.

    Args:
        event: The event to collect
    """
    get_event_publisher().collect(event)


def collect_events(events: List[UnoDomainEvent]) -> None:
    """
    Collect multiple events for later batch publishing.

    Args:
        events: The events to collect
    """
    get_event_publisher().collect_many(events)


def publish_collected_events() -> None:
    """
    Publish all collected events using the global event publisher.

    This function publishes the events asynchronously, returning immediately
    while the events are processed in the background.
    """
    asyncio.create_task(get_event_publisher().publish_collected())


async def publish_collected_events_async() -> None:
    """
    Publish all collected events asynchronously using the global event publisher.

    Args:
        events: The events to publish
    """
    await get_event_publisher().publish_collected_async()


def clear_collected_events() -> None:
    """Clear all collected events without publishing them."""
    get_event_publisher().clear_collected()


def subscribe_handler(
    event_type: Type[E],
    handler: Union[EventHandler[E], EventHandlerFn[E]],
    priority: EventPriority = EventPriority.NORMAL,
    topic_pattern: Optional[str] = None,
) -> None:
    """
    Subscribe a handler to events of a specific type or topic.

    Args:
        event_type: The type of event to subscribe to
        handler: The handler to call when events occur
        priority: The handler's execution priority
        topic_pattern: Optional topic pattern for topic-based routing
    """
    get_event_bus().subscribe(
        event_type=event_type,
        handler=handler,
        priority=priority,
        topic_pattern=topic_pattern,
    )


def unsubscribe_handler(
    event_type: Type[E],
    handler: Union[EventHandler[E], EventHandlerFn[E]],
    topic_pattern: Optional[str] = None,
) -> None:
    """
    Unsubscribe a handler from events of a specific type or topic.

    Args:
        event_type: The type of event to unsubscribe from
        handler: The handler to remove
        topic_pattern: Optional topic pattern for topic-based routing
    """
    get_event_bus().unsubscribe(
        event_type=event_type, handler=handler, topic_pattern=topic_pattern
    )


def scan_for_handlers(module) -> int:
    """
    Scan a module for event handlers and register them.

    This function scans a module for functions and classes decorated with
    @event_handler and registers them with the event bus.

    Args:
        module: The module to scan

    Returns:
        Number of handlers registered
    """
    scanner = EventHandlerScanner(get_event_bus())
    return scanner.scan_module(module)


def scan_instance_for_handlers(instance) -> int:
    """
    Scan an instance for event handlers and register them.

    This function scans an instance for methods decorated with
    @event_handler and registers them with the event bus.

    Args:
        instance: The instance to scan

    Returns:
        Number of handlers registered
    """
    scanner = EventHandlerScanner(get_event_bus())
    return scanner.scan_instance(instance)


# =============================================================================
# Helper Functions
# =============================================================================


def _cls_name_to_event_type(cls_name: str) -> str:
    """
    Convert a class name to an event type identifier.

    Args:
        cls_name: The class name to convert

    Returns:
        The event type identifier (in snake_case)
    """
    # Convert CamelCase to snake_case
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls_name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
