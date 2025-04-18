"""
Aggregate root for event sourcing.

This module provides the base AggregateRoot class for implementing
event-sourced domain entities.
"""

import functools
import inspect
from abc import ABC
from typing import Any, ClassVar, Dict, List, Optional, Set, Type, TypeVar, cast
from uuid import uuid4

from uno.events.core.event import Event

# Type variable for aggregate roots
T = TypeVar("T", bound="AggregateRoot")


def apply_event(event_class: Optional[Type[Event]] = None):
    """
    Decorator for marking a method as an event handler.
    
    Methods decorated with this will be automatically called when
    the specified event type is applied to the aggregate.
    
    Args:
        event_class: Optional event class this method handles
            (inferred from method signature if not provided)
            
    Returns:
        Decorated method
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, event, *args, **kwargs):
            return method(self, event, *args, **kwargs)
        
        # Store the event class on the method
        if event_class:
            wrapper.__applies_event__ = event_class
        else:
            # Try to infer the event class from the method signature
            sig = inspect.signature(method)
            params = list(sig.parameters.values())
            if len(params) >= 2:  # self + event
                param_annotation = params[1].annotation
                if param_annotation != inspect.Parameter.empty:
                    if isinstance(param_annotation, type) and issubclass(param_annotation, Event):
                        wrapper.__applies_event__ = param_annotation
        
        return wrapper
    
    # Handle case where decorator is used without calling
    if callable(event_class) and not isinstance(event_class, type):
        method = event_class
        event_class = None
        return decorator(method)
    
    return decorator


class AggregateRoot(ABC):
    """
    Base class for event-sourced aggregate roots.
    
    An aggregate root is a domain entity that forms the root of an aggregate,
    which is a cluster of associated objects treated as a unit for data changes.
    In event sourcing, the state of an aggregate is determined by replaying
    the events that have affected it.
    """
    
    # Map of event types to handler methods
    _event_handlers: ClassVar[Dict[Type[Event], str]] = {}
    
    def __init__(self, id: Optional[str] = None):
        """
        Initialize the aggregate root.
        
        Args:
            id: Optional unique identifier for this aggregate 
                (generated if not provided)
        """
        self._id = id or str(uuid4())
        self._version = 0
        self._pending_events: List[Event] = []
        
        # Initialize event handlers if not already done for this class
        if not hasattr(self.__class__, "_event_handlers_initialized"):
            self._initialize_event_handlers()
    
    @property
    def id(self) -> str:
        """Get the aggregate's unique identifier."""
        return self._id
    
    @property
    def version(self) -> int:
        """Get the aggregate's current version."""
        return self._version
    
    @classmethod
    def _initialize_event_handlers(cls) -> None:
        """
        Initialize the event handlers map for this class.
        
        This method scans the class for methods decorated with @apply_event
        and builds a map of event types to handler methods.
        """
        # Start with parent class handlers
        handlers = {}
        for base in cls.__bases__:
            if hasattr(base, "_event_handlers"):
                handlers.update(base._event_handlers)
        
        # Add handlers from this class
        for attr_name, attr_value in cls.__dict__.items():
            if hasattr(attr_value, "__applies_event__"):
                event_class = getattr(attr_value, "__applies_event__")
                if event_class:
                    handlers[event_class] = attr_name
        
        # Store handlers on the class
        cls._event_handlers = handlers
        cls._event_handlers_initialized = True
    
    def apply(self, event: Event, is_new: bool = True) -> None:
        """
        Apply an event to this aggregate.
        
        This method updates the aggregate's state based on the event
        and optionally adds the event to the list of pending events.
        
        Args:
            event: The event to apply
            is_new: Whether this is a new event (True) or a historic event (False)
        """
        # Always provide the aggregate ID and version in the event
        if not event.aggregate_id:
            event = event.with_metadata(
                aggregate_id=self.id,
                aggregate_type=self.__class__.__name__,
                aggregate_version=self._version + 1
            )
        
        # Apply the event to update the aggregate's state
        self._apply_event(event)
        
        # Increment version
        self._version += 1
        
        # Add to pending events if it's a new event
        if is_new:
            self._pending_events.append(event)
    
    def _apply_event(self, event: Event) -> None:
        """
        Apply an event to update the aggregate's state.
        
        Args:
            event: The event to apply
        """
        # Get handler for this event type
        event_class = event.__class__
        handler_name = None
        
        # Find the most specific handler for this event type
        for cls in event_class.__mro__:
            if cls in self._event_handlers:
                handler_name = self._event_handlers[cls]
                break
        
        if not handler_name:
            # Try by the event type string
            method_name = f"apply_{event.type}"
            if hasattr(self, method_name):
                handler_name = method_name
        
        # Call the handler if found
        if handler_name:
            handler = getattr(self, handler_name)
            handler(event)
    
    def get_pending_events(self) -> List[Event]:
        """
        Get all pending events.
        
        Returns:
            List of pending events
        """
        return self._pending_events.copy()
    
    def clear_pending_events(self) -> List[Event]:
        """
        Clear all pending events and return them.
        
        Returns:
            List of events that were pending
        """
        events = self._pending_events.copy()
        self._pending_events.clear()
        return events