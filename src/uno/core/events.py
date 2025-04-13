"""
Event system for the Uno framework.

This module provides a comprehensive event system for implementing event-driven
architecture, including event publishing, subscription, and handling. It supports
both synchronous and asynchronous event processing with strong typing.
"""

import logging
import inspect
import asyncio
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any, Dict, List, Set, Type, TypeVar, Generic, Protocol, 
    Callable, Awaitable, Optional, Union, cast, get_type_hints,
    runtime_checkable
)

from .errors import DomainError, ErrorCategory, with_error_context, with_async_error_context
from .protocols import DomainEvent, EventHandler, EventBus


# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")
TEvent = TypeVar("TEvent", bound=DomainEvent)


# =============================================================================
# Event Priorities
# =============================================================================

class EventPriority(Enum):
    """Priorities for event handlers to determine execution order."""
    
    HIGH = auto()     # Execute before normal handlers
    NORMAL = auto()   # Default priority
    LOW = auto()      # Execute after normal handlers


# =============================================================================
# Base Event Implementation
# =============================================================================

class Event(DomainEvent):
    """
    Base implementation of a domain event.
    
    Events represent something that happened in the domain that domain experts care about.
    They are immutable and named in the past tense.
    """
    
    def __init__(
        self,
        event_id: str = None,
        timestamp: datetime = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize a domain event.
        
        Args:
            event_id: Unique identifier for the event (generated if not provided)
            timestamp: When the event occurred (defaults to now)
            metadata: Additional contextual information about the event
        """
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = self.__class__.__name__
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary representation.
        
        Returns:
            Dictionary representation of the event
        """
        # Get all instance attributes
        attributes = {
            key: value for key, value in self.__dict__.items()
            if not key.startswith("_") and key not in {"event_id", "event_type", "timestamp", "metadata"}
        }
        
        # Create the base dictionary
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "data": attributes
        }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """
        Create event from dictionary representation.
        
        Args:
            data: Dictionary representation of the event
            
        Returns:
            Event instance
        """
        # Extract base fields
        event_id = data.get("event_id")
        timestamp_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
        metadata = data.get("metadata", {})
        
        # Create instance
        instance = cls(event_id=event_id, timestamp=timestamp, metadata=metadata)
        
        # Set data attributes
        for key, value in data.get("data", {}).items():
            setattr(instance, key, value)
        
        return instance
    
    def __eq__(self, other: object) -> bool:
        """Compare events by their ID."""
        if not isinstance(other, DomainEvent):
            return False
        return self.event_id == other.event_id
    
    def __hash__(self) -> int:
        """Hash event by its ID."""
        return hash(self.event_id)
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.event_type}(id={self.event_id}, timestamp={self.timestamp})"


# =============================================================================
# Event Handler Wrapper
# =============================================================================

class EventHandlerWrapper[T_Event](Generic[T_Event]):
    """
    Wrapper for event handlers that provides metadata and execution control.
    
    This wrapper stores information about the handler, such as its priority,
    and provides methods for executing the handler with proper error handling.
    """
    
    def __init__(
        self,
        handler: EventHandler[T_Event],
        priority: EventPriority = EventPriority.NORMAL,
        is_async: bool = None
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
            if hasattr(handler, "handle"):
                is_async = asyncio.iscoroutinefunction(handler.handle)
            else:
                is_async = asyncio.iscoroutinefunction(handler)
                
        self.is_async = is_async
    
    async def execute(self, event: T_Event) -> None:
        """
        Execute the handler with the given event.
        
        Args:
            event: The event to handle
            
        Raises:
            DomainError: If the handler fails
        """
        try:
            # Add context to any errors
            with with_error_context(event_type=event.event_type, event_id=event.event_id):
                # Handle based on whether the handler is a class or function
                if hasattr(self.handler, "handle"):
                    # Class-based handler
                    result = self.handler.handle(event)
                else:
                    # Function-based handler
                    result = self.handler(event)
                
                # Await if the handler is async
                if self.is_async:
                    await result
                
        except Exception as e:
            # Wrap in DomainError if not already
            if not isinstance(e, DomainError):
                raise DomainError(
                    message=f"Error handling event {event.event_type}: {str(e)}",
                    code="EVENT_HANDLER_ERROR",
                    category=ErrorCategory.UNEXPECTED,
                    cause=e
                )
            raise


# =============================================================================
# Event Bus Implementation
# =============================================================================

class DefaultEventBus(EventBus):
    """
    Default implementation of the event bus.
    
    The event bus manages event subscriptions and dispatches events to
    registered handlers based on event type.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        max_concurrency: int = 10
    ):
        """
        Initialize the event bus.
        
        Args:
            logger: Optional logger for diagnostic information
            max_concurrency: Maximum number of concurrent event handlers when dispatching async
        """
        self._logger = logger or logging.getLogger("uno.events")
        self._max_concurrency = max_concurrency
        self._handlers: Dict[Type, List[EventHandlerWrapper]] = {}
    
    def subscribe(self, event_type: Type[TEvent], handler: EventHandler[TEvent]) -> None:
        """
        Subscribe a handler to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The handler to call when events occur
        """
        # Create handler entry for this event type if it doesn't exist
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        # Create wrapper for the handler
        wrapper = EventHandlerWrapper(handler)
        
        # Add to handlers
        self._handlers[event_type].append(wrapper)
        
        self._logger.debug(f"Subscribed {handler} to {event_type.__name__}")
    
    def subscribe_with_priority(
        self,
        event_type: Type[TEvent],
        handler: EventHandler[TEvent],
        priority: EventPriority
    ) -> None:
        """
        Subscribe a handler with a specific priority.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The handler to call when events occur
            priority: The handler's execution priority
        """
        # Create handler entry for this event type if it doesn't exist
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        # Create wrapper for the handler
        wrapper = EventHandlerWrapper(handler, priority)
        
        # Add to handlers
        self._handlers[event_type].append(wrapper)
        
        self._logger.debug(f"Subscribed {handler} to {event_type.__name__} with priority {priority.name}")
    
    def unsubscribe(self, event_type: Type[TEvent], handler: EventHandler[TEvent]) -> None:
        """
        Unsubscribe a handler from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        if event_type not in self._handlers:
            return
        
        # Find and remove the handler
        self._handlers[event_type] = [
            wrapper for wrapper in self._handlers[event_type]
            if wrapper.handler != handler
        ]
        
        self._logger.debug(f"Unsubscribed {handler} from {event_type.__name__}")
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed handlers.
        
        This method delivers the event to all handlers subscribed to its type,
        respecting their priority order.
        
        Args:
            event: The event to publish
        """
        event_type = type(event)
        self._logger.debug(f"Publishing event {event_type.__name__} ({event.event_id})")
        
        # Get handlers for this event type
        handlers = self._get_handlers_for_event(event)
        
        if not handlers:
            self._logger.debug(f"No handlers found for {event_type.__name__}")
            return
        
        # Sort handlers by priority
        handlers.sort(key=lambda wrapper: wrapper.priority.value)
        
        # Execute each handler
        for wrapper in handlers:
            await wrapper.execute(event)
    
    async def publish_async(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed handlers asynchronously.
        
        This method delivers the event to all handlers concurrently, with
        a maximum level of concurrency defined by max_concurrency.
        
        Args:
            event: The event to publish
        """
        event_type = type(event)
        self._logger.debug(f"Publishing event {event_type.__name__} ({event.event_id}) asynchronously")
        
        # Get handlers for this event type
        handlers = self._get_handlers_for_event(event)
        
        if not handlers:
            self._logger.debug(f"No handlers found for {event_type.__name__}")
            return
        
        # Sort handlers by priority
        handlers.sort(key=lambda wrapper: wrapper.priority.value)
        
        # Create tasks for each handler
        tasks = [wrapper.execute(event) for wrapper in handlers]
        
        # Execute tasks with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self._max_concurrency)
        
        async def execute_with_semaphore(task):
            async with semaphore:
                return await task
        
        # Wait for all tasks to complete
        await asyncio.gather(
            *(execute_with_semaphore(task) for task in tasks)
        )
    
    def _get_handlers_for_event(self, event: DomainEvent) -> List[EventHandlerWrapper]:
        """
        Get all handlers that should receive this event.
        
        Args:
            event: The event to get handlers for
            
        Returns:
            List of handlers for this event
        """
        event_type = type(event)
        handlers = []
        
        # Add direct handlers for this event type
        if event_type in self._handlers:
            handlers.extend(self._handlers[event_type])
        
        # Add handlers for parent classes
        for base in event_type.__mro__[1:]:  # Skip the event type itself
            if base in self._handlers and base != object:
                handlers.extend(self._handlers[base])
        
        return handlers


# =============================================================================
# Event Publisher
# =============================================================================

class EventPublisher:
    """
    Facade for publishing events to the event bus.
    
    The event publisher provides a simplified interface for publishing events
    and can collect events for batch publishing.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the event publisher.
        
        Args:
            event_bus: The event bus to publish events to
            logger: Optional logger for diagnostic information
        """
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger("uno.events")
        self._collected_events: List[DomainEvent] = []
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event immediately.
        
        Args:
            event: The event to publish
        """
        asyncio.create_task(self._event_bus.publish(event))
    
    def publish_sync(self, event: DomainEvent) -> None:
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
            loop.run_until_complete(self._event_bus.publish(event))
        else:
            # Use running event loop
            if loop.is_running():
                # Create a future and run it until complete
                future = asyncio.run_coroutine_threadsafe(
                    self._event_bus.publish(event), loop
                )
                future.result()  # Wait for completion
            else:
                # Run the coroutine until complete
                loop.run_until_complete(self._event_bus.publish(event))
    
    async def publish_async(self, event: DomainEvent) -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: The event to publish
        """
        await self._event_bus.publish(event)
    
    def collect(self, event: DomainEvent) -> None:
        """
        Collect an event for later batch publishing.
        
        Args:
            event: The event to collect
        """
        self._collected_events.append(event)
    
    def publish_collected(self) -> None:
        """Publish all collected events."""
        events = self._collected_events.copy()
        self._collected_events.clear()
        
        for event in events:
            self.publish(event)
    
    async def publish_collected_async(self) -> None:
        """Publish all collected events asynchronously."""
        events = self._collected_events.copy()
        self._collected_events.clear()
        
        # Publish all events concurrently
        await asyncio.gather(
            *(self._event_bus.publish(event) for event in events)
        )
    
    def clear_collected(self) -> None:
        """Clear all collected events without publishing them."""
        self._collected_events.clear()


# =============================================================================
# Event Handler Decorator
# =============================================================================

def event_handler(
    event_type: Optional[Type[DomainEvent]] = None,
    priority: EventPriority = EventPriority.NORMAL
):
    """
    Decorator for marking a function as an event handler.
    
    This decorator can be used to mark functions as event handlers and
    optionally specify the event type they handle and their priority.
    
    Args:
        event_type: The type of event to handle (inferred from type hints if None)
        priority: The handler's execution priority
        
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
                    if isinstance(param_type, type) and issubclass(param_type, DomainEvent):
                        event_type = param_type
        
        # Store metadata on the function
        func.__event_handler__ = True
        func.__event_type__ = event_type
        func.__event_priority__ = priority
        
        return func
    
    # Allow using as @event_handler without calling
    if callable(event_type):
        func = event_type
        event_type = None
        return decorator(func)
    
    return decorator


# =============================================================================
# Event Handler Scanner
# =============================================================================

class EventHandlerScanner:
    """
    Scanner for finding and registering event handlers.
    
    This class helps automate the process of finding event handlers in modules
    and registering them with the event bus.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the scanner.
        
        Args:
            event_bus: The event bus to register handlers with
            logger: Optional logger for diagnostic information
        """
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger("uno.events")
    
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
                
                if event_type is not None:
                    self._event_bus.subscribe_with_priority(event_type, obj, priority)
                    count += 1
                    self._logger.debug(f"Registered function handler {obj.__name__} for {event_type.__name__}")
            
            # Handle class-based handlers
            elif (
                inspect.isclass(obj) and 
                hasattr(obj, "handle") and 
                inspect.isfunction(getattr(obj, "handle"))
            ):
                # Try to find event type from handle method
                handle_method = getattr(obj, "handle")
                hints = get_type_hints(handle_method)
                
                params = inspect.signature(handle_method).parameters
                if params:
                    # Skip self
                    params_iter = iter(params.values())
                    next(params_iter)  # Skip self
                    
                    if params_iter:
                        first_param = next(params_iter)
                        if first_param.name in hints:
                            param_type = hints[first_param.name]
                            if isinstance(param_type, type) and issubclass(param_type, DomainEvent):
                                # Create instance
                                instance = obj()
                                
                                # Get priority if specified
                                priority = getattr(
                                    handle_method, "__event_priority__", 
                                    getattr(obj, "__event_priority__", EventPriority.NORMAL)
                                )
                                
                                self._event_bus.subscribe_with_priority(param_type, instance, priority)
                                count += 1
                                self._logger.debug(f"Registered class handler {obj.__name__} for {param_type.__name__}")
        
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
                
                if event_type is not None:
                    self._event_bus.subscribe_with_priority(event_type, method, priority)
                    count += 1
                    self._logger.debug(f"Registered method handler {instance.__class__.__name__}.{name} for {event_type.__name__}")
        
        return count


# =============================================================================
# Public API Functions
# =============================================================================

# Global event bus instance
_event_bus: Optional[EventBus] = None
_event_publisher: Optional[EventPublisher] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        The global event bus instance
        
    Raises:
        DomainError: If the event bus is not initialized
    """
    global _event_bus
    if _event_bus is None:
        raise DomainError(
            message="Event bus is not initialized",
            code="EVENT_BUS_NOT_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )
    return _event_bus


def get_event_publisher() -> EventPublisher:
    """
    Get the global event publisher instance.
    
    Returns:
        The global event publisher instance
        
    Raises:
        DomainError: If the event publisher is not initialized
    """
    global _event_publisher
    if _event_publisher is None:
        raise DomainError(
            message="Event publisher is not initialized",
            code="EVENT_PUBLISHER_NOT_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )
    return _event_publisher


def initialize_events(
    logger: Optional[logging.Logger] = None,
    max_concurrency: int = 10
) -> None:
    """
    Initialize the global event system.
    
    Args:
        logger: Optional logger for diagnostic information
        max_concurrency: Maximum number of concurrent event handlers
        
    Raises:
        DomainError: If the event system is already initialized
    """
    global _event_bus, _event_publisher
    if _event_bus is not None:
        raise DomainError(
            message="Event system is already initialized",
            code="EVENT_SYSTEM_ALREADY_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )
    
    _event_bus = DefaultEventBus(logger, max_concurrency)
    _event_publisher = EventPublisher(_event_bus, logger)


def reset_events() -> None:
    """Reset the global event system (primarily for testing)."""
    global _event_bus, _event_publisher
    _event_bus = None
    _event_publisher = None


def publish_event(event: DomainEvent) -> None:
    """
    Publish an event using the global event publisher.
    
    Args:
        event: The event to publish
    """
    get_event_publisher().publish(event)


def publish_event_sync(event: DomainEvent) -> None:
    """
    Publish an event synchronously using the global event publisher.
    
    Args:
        event: The event to publish
    """
    get_event_publisher().publish_sync(event)


async def publish_event_async(event: DomainEvent) -> None:
    """
    Publish an event asynchronously using the global event publisher.
    
    Args:
        event: The event to publish
    """
    await get_event_publisher().publish_async(event)


def collect_event(event: DomainEvent) -> None:
    """
    Collect an event for later batch publishing.
    
    Args:
        event: The event to collect
    """
    get_event_publisher().collect(event)


def publish_collected_events() -> None:
    """Publish all collected events using the global event publisher."""
    get_event_publisher().publish_collected()


async def publish_collected_events_async() -> None:
    """Publish all collected events asynchronously using the global event publisher."""
    await get_event_publisher().publish_collected_async()


def clear_collected_events() -> None:
    """Clear all collected events without publishing them."""
    get_event_publisher().clear_collected()


def subscribe_handler(
    event_type: Type[DomainEvent],
    handler: EventHandler,
    priority: EventPriority = EventPriority.NORMAL
) -> None:
    """
    Subscribe a handler to events of a specific type.
    
    Args:
        event_type: The type of event to subscribe to
        handler: The handler to call when events occur
        priority: The handler's execution priority
    """
    get_event_bus().subscribe_with_priority(event_type, handler, priority)


def unsubscribe_handler(
    event_type: Type[DomainEvent],
    handler: EventHandler
) -> None:
    """
    Unsubscribe a handler from events of a specific type.
    
    Args:
        event_type: The type of event to unsubscribe from
        handler: The handler to remove
    """
    get_event_bus().unsubscribe(event_type, handler)


def scan_for_handlers(module) -> int:
    """
    Scan a module for event handlers and register them.
    
    Args:
        module: The module to scan
        
    Returns:
        Number of handlers registered
    """
    scanner = EventHandlerScanner(get_event_bus())
    return scanner.scan_module(module)