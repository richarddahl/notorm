"""
Event handler definitions for the Uno event system.

This module defines the event handler interface and utilities for creating
and managing event handlers.
"""

import inspect
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Awaitable, Callable, Generic, Optional, Type, TypeVar, Union, get_type_hints

from uno.events.core.event import Event

# Type variables
E = TypeVar("E", bound=Event)
EventHandlerFunc = Callable[[E], Any]
AsyncEventHandlerFunc = Callable[[E], Awaitable[Any]]
EventHandlerCallable = Union[EventHandlerFunc[E], AsyncEventHandlerFunc[E]]


class EventPriority(Enum):
    """Priority levels for event handlers."""
    
    HIGH = auto()      # Execute before normal handlers
    NORMAL = auto()    # Default priority
    LOW = auto()       # Execute after normal handlers


class EventHandler(Generic[E], ABC):
    """
    Abstract base class for event handlers.
    
    Event handlers process events by executing domain logic in response
    to the events. Handlers can be synchronous or asynchronous.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the event handler.
        
        Args:
            name: Optional name for this handler (defaults to class name)
        """
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    async def handle(self, event: E) -> None:
        """
        Handle an event.
        
        This method must be implemented by subclasses to define how
        the handler processes events.
        
        Args:
            event: The event to handle
        """
        pass


def event_handler(
    event_type: Optional[Type[Event]] = None,
    priority: EventPriority = EventPriority.NORMAL,
    topic: Optional[str] = None,
):
    """
    Decorator for marking a function as an event handler.
    
    This decorator can be used to annotate functions that handle specific
    event types. It stores metadata about the handler that can be used
    by the event system for registration and execution.
    
    Args:
        event_type: The type of event this handler can process
        priority: Priority level for this handler
        topic: Optional topic filter for topic-based routing
        
    Returns:
        The decorated function with event handler metadata
    """
    def decorator(func: Callable):
        # Try to infer event type from type hints if not provided
        nonlocal event_type
        if event_type is None:
            hints = get_type_hints(func)
            # Find first parameter's type
            params = inspect.signature(func).parameters
            if params:
                first_param_name = next(iter(params))
                if first_param_name in hints:
                    param_type = hints[first_param_name]
                    # Check if this is a valid event type
                    if isinstance(param_type, type) and issubclass(param_type, Event):
                        event_type = param_type
        
        # Store metadata on the function
        func.__event_handler__ = True
        func.__event_type__ = event_type
        func.__event_priority__ = priority
        func.__event_topic__ = topic
        
        return func
    
    # Handle case where decorator is used without calling (e.g., @event_handler)
    if callable(event_type) and not isinstance(event_type, type):
        func = event_type
        event_type = None
        return decorator(func)
    
    return decorator