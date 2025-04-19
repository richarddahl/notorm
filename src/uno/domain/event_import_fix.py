"""
Transitional module for backward compatibility with the new event system.

This module provides imports from the new event system to maintain compatibility
with code that was importing from the old uno.domain.event_dispatcher module.
"""

import warnings
from typing import Any, Type, Callable, Optional, Union

from uno.core.events import Event, AsyncEventBus
from uno.core.protocols.event import EventHandler


# Deprecated event dispatcher compatibility class
class EventDispatcher:
    """
    Deprecated event dispatcher implementation.
    
    This class provides backward compatibility with code that was using the
    old event_dispatcher.EventDispatcher class. It forwards operations to
    the new AsyncEventBus implementation.
    """
    
    def __init__(self, logger=None):
        """Initialize with deprecation warning."""
        warnings.warn(
            "EventDispatcher is deprecated and will be removed in a future version. "
            "Use uno.core.events.AsyncEventBus instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._event_bus = AsyncEventBus()
        self._logger = logger
    
    async def dispatch(self, event: Event) -> None:
        """Dispatch an event to handlers."""
        await self._event_bus.publish(event)
    
    def register_handler(self, event_type: Type[Event], handler: Callable) -> None:
        """Register an event handler."""
        async def adapter(event: Event) -> None:
            result = handler(event)
            if hasattr(result, "__await__"):
                await result
        
        async def run_subscription():
            """Run the subscription asynchronously."""
            await self._event_bus.subscribe(event_type.get_event_type(), adapter)
        
        import asyncio
        asyncio.create_task(run_subscription())
    
    def unregister_handler(self, event_type: Type[Event], handler: Callable) -> None:
        """Unregister an event handler."""
        # This is not fully compatible because we can't retrieve the adapter
        # Just log a warning
        if self._logger:
            self._logger.warning(
                "Unregistering handlers is not fully supported in the transition "
                "to the new event system. Please migrate to uno.core.events.AsyncEventBus."
            )


# Decorator for registering event handlers
def domain_event_handler():
    """
    Deprecated decorator for event handlers.
    
    This decorator provides backward compatibility with code that was using the
    old event_dispatcher.domain_event_handler decorator.
    """
    warnings.warn(
        "domain_event_handler decorator is deprecated and will be removed in a future version. "
        "Use uno.core.events.register_event_handler instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    def decorator(func):
        """The actual decorator."""
        return func
    
    return decorator


# Base class for event handlers
class EventHandler:
    """
    Deprecated base class for event handlers.
    
    This class provides backward compatibility with code that was using the
    old event_dispatcher.EventHandler class.
    """
    
    def __init__(self, **kwargs):
        """Initialize with deprecation warning."""
        warnings.warn(
            "EventHandler class is deprecated and will be removed in a future version. "
            "Use function-based handlers with uno.core.events instead.",
            DeprecationWarning,
            stacklevel=2
        )


# Base class for event subscribers
class EventSubscriber:
    """
    Deprecated base class for event subscribers.
    
    This class provides backward compatibility with code that was using the
    old event_dispatcher.EventSubscriber class.
    """
    
    def __init__(self, dispatcher=None):
        """Initialize with deprecation warning."""
        warnings.warn(
            "EventSubscriber class is deprecated and will be removed in a future version. "
            "Use function-based handlers with uno.core.events instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.dispatcher = dispatcher