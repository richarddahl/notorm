"""
Event system for the Uno framework.

This module implements the event-driven architecture for the Uno framework,
providing a mechanism for decoupling components through events.
"""

import asyncio
import inspect
import json
import logging
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Callable, Awaitable, Optional, Set, Type, TypeVar, Generic, cast

from uno.core.protocols import DomainEvent, EventHandler, EventBus

T = TypeVar('T')
EventT = TypeVar('EventT', bound=DomainEvent)


@dataclass
class BaseDomainEvent:
    """Base class for domain events."""
    
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def event_type(self) -> str:
        """Get the type of this event."""
        return self.__class__.__name__
    
    @property
    def aggregate_id(self) -> Any:
        """Get the identifier of the aggregate that raised this event."""
        raise NotImplementedError("Subclasses must implement aggregate_id")
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the event data."""
        # Convert to dict excluding methods and excluding private attributes
        return {
            k: v for k, v in asdict(self).items()
            if not k.startswith('_') and not callable(v)
        }
    
    def to_json(self) -> str:
        """Convert the event to JSON."""
        data = self.data.copy()
        data['event_id'] = str(data['event_id'])
        data['timestamp'] = data['timestamp'].isoformat()
        data['event_type'] = self.event_type
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BaseDomainEvent':
        """Create an event from JSON."""
        data = json.loads(json_str)
        data['event_id'] = uuid.UUID(data['event_id'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class BaseEventHandler(Generic[EventT]):
    """Base class for event handlers."""
    
    async def handle(self, event: EventT) -> None:
        """Handle an event."""
        raise NotImplementedError("Subclasses must implement handle")


class SimpleEventBus:
    """Simple in-memory event bus implementation."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the event bus.
        
        Args:
            logger: Optional logger
        """
        self._handlers: Dict[str, Set[EventHandler[Any]]] = {}
        self._logger = logger or logging.getLogger(__name__)
        self._task_group = None
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to the event bus.
        
        Args:
            event: The event to publish
        """
        event_type = event.event_type
        self._logger.debug(f"Publishing event: {event_type} ({event.event_id})")
        
        if event_type not in self._handlers:
            self._logger.debug(f"No handlers registered for event: {event_type}")
            return
        
        tasks = []
        for handler in self._handlers[event_type]:
            task = asyncio.create_task(self._safe_handle(handler, event))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _safe_handle(self, handler: EventHandler[Any], event: DomainEvent) -> None:
        """
        Safely handle an event, catching any exceptions.
        
        Args:
            handler: The handler
            event: The event
        """
        try:
            await handler.handle(event)
        except Exception as e:
            self._logger.error(f"Error handling event {event.event_type}: {e}")
            # In a production system, you would want to log more details, report metrics, etc.
    
    def subscribe(self, event_type: str, handler: EventHandler[Any]) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The event type
            handler: The handler
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(handler)
        self._logger.debug(f"Subscribed {handler.__class__.__name__} to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler[Any]) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The event type
            handler: The handler
        """
        if event_type in self._handlers:
            self._handlers[event_type].discard(handler)
            self._logger.debug(f"Unsubscribed {handler.__class__.__name__} from {event_type}")


class TypedEventBus(SimpleEventBus):
    """Event bus that uses event types instead of event type strings."""
    
    def subscribe_to_type(self, event_class: Type[DomainEvent], handler: EventHandler[Any]) -> None:
        """
        Subscribe a handler to an event class.
        
        Args:
            event_class: The event class
            handler: The handler
        """
        event_type = event_class.__name__
        self.subscribe(event_type, handler)
    
    def unsubscribe_from_type(self, event_class: Type[DomainEvent], handler: EventHandler[Any]) -> None:
        """
        Unsubscribe a handler from an event class.
        
        Args:
            event_class: The event class
            handler: The handler
        """
        event_type = event_class.__name__
        self.unsubscribe(event_type, handler)


class AsyncEventBus(TypedEventBus):
    """Event bus with async task management."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the event bus.
        
        Args:
            logger: Optional logger
        """
        super().__init__(logger)
        self._queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to the event bus.
        
        Args:
            event: The event to publish
        """
        await self._queue.put(event)
    
    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        self._logger.debug("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus."""
        if not self._running:
            return
        
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        self._logger.debug("Event bus stopped")
    
    async def _worker(self) -> None:
        """Worker that processes events from the queue."""
        while self._running:
            try:
                event = await self._queue.get()
                try:
                    await super().publish(event)
                finally:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in event worker: {e}")


class DomainEventPublisher:
    """Publisher for domain events."""
    
    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        """
        Initialize the publisher.
        
        Args:
            event_bus: The event bus
            logger: Optional logger
        """
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
    
    async def publish_events(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple events.
        
        Args:
            events: The events to publish
        """
        for event in events:
            await self._event_bus.publish(event)
            self._logger.debug(f"Published event: {event.event_type} ({event.event_id})")


def event_handler(event_class: Type[DomainEvent]):
    """
    Decorator for event handler methods.
    
    This decorator marks a method as an event handler for a specific event type.
    
    Args:
        event_class: The event class
    """
    def decorator(func: Callable[[Any, DomainEvent], Awaitable[None]]):
        setattr(func, '_event_class', event_class)
        return func
    return decorator


class DomainEventProcessor:
    """
    Base class for processing domain events.
    
    This class registers event handlers for domain events based on methods
    decorated with @event_handler.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize the processor.
        
        Args:
            event_bus: The event bus
        """
        self._event_bus = event_bus
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register event handlers."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_event_class'):
                event_class = getattr(method, '_event_class')
                
                # Create a handler class dynamically
                class_name = f"{self.__class__.__name__}_{name}_Handler"
                handler_class = type(class_name, (BaseEventHandler,), {
                    'handle': method
                })
                
                # Create an instance of the handler class
                handler = handler_class()
                
                # Subscribe the handler
                if isinstance(self._event_bus, TypedEventBus):
                    self._event_bus.subscribe_to_type(event_class, handler)
                else:
                    self._event_bus.subscribe(event_class.__name__, handler)