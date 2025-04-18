"""
Event subscriber for the Uno event system.

This module provides the base class for event subscribers, which are
classes containing one or more event handlers that are automatically
registered with the event bus.
"""

import inspect
from typing import Any, Callable, Optional, Type

import structlog

from uno.events.core.bus import EventBus
from uno.events.core.event import Event
from uno.events.core.handler import EventPriority


class EventSubscriber:
    """
    Base class for event subscribers.
    
    Event subscribers are classes that contain one or more event handlers
    that are automatically registered with the event bus when the subscriber
    is instantiated.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize the event subscriber and register its handlers.
        
        Args:
            event_bus: The event bus to register handlers with
        """
        self.event_bus = event_bus
        self.logger = structlog.get_logger("uno.events")
        
        # Register all methods decorated with @event_handler
        self.register_handlers()
    
    def register_handlers(self) -> None:
        """Register all event handlers in this subscriber with the event bus."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "__event_handler__"):
                event_type = getattr(method, "__event_type__", None)
                priority = getattr(method, "__event_priority__", EventPriority.NORMAL)
                topic = getattr(method, "__event_topic__", None)
                
                if event_type is not None:
                    self.event_bus.subscribe(
                        event_type=event_type,
                        handler=method,
                        priority=priority,
                        topic=topic,
                    )
                    
                    self.logger.debug(
                        "Registered subscriber method",
                        subscriber=self.__class__.__name__,
                        method=name,
                        event_type=event_type.__name__,
                        priority=priority.name,
                        topic=topic,
                    )
    
    def unregister_handlers(self) -> None:
        """Unregister all event handlers in this subscriber from the event bus."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "__event_handler__"):
                event_type = getattr(method, "__event_type__", None)
                topic = getattr(method, "__event_topic__", None)
                
                if event_type is not None:
                    self.event_bus.unsubscribe(
                        event_type=event_type,
                        handler=method,
                        topic=topic,
                    )
                    
                    self.logger.debug(
                        "Unregistered subscriber method",
                        subscriber=self.__class__.__name__,
                        method=name,
                        event_type=event_type.__name__,
                        topic=topic,
                    )