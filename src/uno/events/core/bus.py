"""
Event bus implementation for the Uno event system.

The event bus is responsible for routing events to the appropriate handlers
based on event type and topic. It supports both synchronous and asynchronous
event handling.
"""

import asyncio
import inspect
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Type, TypeVar, Union, cast

import structlog
from structlog.stdlib import LoggerFactory

from uno.events.core.event import Event
from uno.events.core.handler import EventHandler, EventHandlerCallable, EventPriority

# Type variables
E = TypeVar("E", bound=Event)


class Subscription:
    """
    Event subscription tracking a handler and its filter criteria.
    
    Subscriptions define how events are routed to handlers based on event type
    and optional topic filters.
    """
    
    def __init__(
        self,
        handler: Union[EventHandler[E], EventHandlerCallable[E]],
        event_type: Optional[Type[E]] = None,
        topic_pattern: Optional[Union[str, Pattern]] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        """
        Initialize an event subscription.
        
        Args:
            handler: The event handler function or object
            event_type: The type of event this subscription matches
            topic_pattern: Optional regex pattern for topic matching
            priority: The execution priority for this handler
        """
        self.handler = handler
        self.event_type = event_type
        self.priority = priority
        
        # Compile topic pattern if provided as string
        if isinstance(topic_pattern, str):
            self.topic_pattern = re.compile(topic_pattern)
        else:
            self.topic_pattern = topic_pattern
        
        # Determine if handler is async
        if isinstance(handler, EventHandler):
            self.is_async = asyncio.iscoroutinefunction(handler.handle)
            self.handler_name = handler.__class__.__name__
        else:
            self.is_async = asyncio.iscoroutinefunction(handler)
            self.handler_name = getattr(handler, "__name__", str(handler))
    
    def matches_event(self, event: Event) -> bool:
        """
        Check if this subscription matches the given event.
        
        Args:
            event: The event to check
            
        Returns:
            True if the subscription matches the event, False otherwise
        """
        # Check event type if specified
        if self.event_type and not isinstance(event, self.event_type):
            return False
        
        # Check topic pattern if specified
        if self.topic_pattern and event.topic:
            return bool(self.topic_pattern.match(event.topic))
        elif self.topic_pattern and not event.topic:
            return False
        
        return True
    
    async def invoke(self, event: Event) -> None:
        """
        Invoke the handler with the given event.
        
        Args:
            event: The event to handle
        """
        # Cast event to the handler's expected type
        typed_event = cast(E, event)
        
        try:
            if isinstance(self.handler, EventHandler):
                # Class-based handler
                result = self.handler.handle(typed_event)
            else:
                # Function-based handler
                result = self.handler(typed_event)
            
            # If the handler returns a coroutine, await it
            if asyncio.iscoroutine(result):
                await result
                
        except Exception as e:
            # Log the error but don't propagate it to prevent one handler
            # failure from affecting other handlers
            logger = structlog.get_logger("uno.events")
            logger.error(
                "Error in event handler",
                handler=self.handler_name,
                event_type=event.type,
                event_id=event.id,
                error=str(e),
                exc_info=True,
            )


class EventBus:
    """
    Event bus for publishing and subscribing to events.
    
    The event bus is the central component of the event system, responsible for
    routing events to the appropriate handlers and managing subscriptions.
    """
    
    def __init__(self, max_concurrency: int = 10):
        """
        Initialize the event bus.
        
        Args:
            max_concurrency: Maximum number of handlers to execute concurrently
        """
        structlog.configure(logger_factory=LoggerFactory())
        self.logger = structlog.get_logger("uno.events")
        self.max_concurrency = max_concurrency
        self._subscriptions: List[Subscription] = []
    
    def subscribe(
        self,
        event_type: Type[E],
        handler: Union[EventHandler[E], EventHandlerCallable[E]],
        priority: EventPriority = EventPriority.NORMAL,
        topic: Optional[str] = None,
    ) -> None:
        """
        Subscribe a handler to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The event handler (function or class)
            priority: The execution priority for this handler
            topic: Optional topic filter for topic-based routing
        """
        subscription = Subscription(
            handler=handler,
            event_type=event_type,
            topic_pattern=topic,
            priority=priority,
        )
        
        self._subscriptions.append(subscription)
        
        # Sort subscriptions by priority
        self._subscriptions.sort(
            key=lambda s: s.priority.value
        )
        
        handler_name = (
            handler.__class__.__name__ 
            if isinstance(handler, EventHandler) 
            else getattr(handler, "__name__", str(handler))
        )
        
        self.logger.info(
            "Handler subscribed",
            handler=handler_name,
            event_type=event_type.__name__,
            topic=topic,
            priority=priority.name,
        )
    
    def unsubscribe(
        self,
        event_type: Type[E],
        handler: Union[EventHandler[E], EventHandlerCallable[E]],
        topic: Optional[str] = None,
    ) -> None:
        """
        Unsubscribe a handler from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The event handler to unsubscribe
            topic: Optional topic filter for topic-based routing
        """
        initial_count = len(self._subscriptions)
        
        # Find all subscriptions that match the criteria
        self._subscriptions = [
            s for s in self._subscriptions 
            if not (
                s.event_type == event_type and
                s.handler == handler and
                (topic is None or s.topic_pattern == re.compile(topic))
            )
        ]
        
        # Log only if we actually removed subscriptions
        if len(self._subscriptions) < initial_count:
            handler_name = (
                handler.__class__.__name__ 
                if isinstance(handler, EventHandler) 
                else getattr(handler, "__name__", str(handler))
            )
            
            self.logger.info(
                "Handler unsubscribed",
                handler=handler_name,
                event_type=event_type.__name__,
                topic=topic,
            )
    
    def get_handlers_for_event(self, event: Event) -> List[Subscription]:
        """
        Get all handlers that match the given event.
        
        Args:
            event: The event to match
            
        Returns:
            List of matching subscriptions
        """
        return [s for s in self._subscriptions if s.matches_event(event)]
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all matching handlers in sequence.
        
        This method processes handlers in priority order, waiting for each
        handler to complete before moving to the next one.
        
        Args:
            event: The event to publish
        """
        self.logger.debug(
            "Publishing event",
            event_type=event.type,
            event_id=event.id,
            topic=event.topic,
        )
        
        # Get handlers for this event
        handlers = self.get_handlers_for_event(event)
        
        if not handlers:
            self.logger.debug(
                "No handlers for event",
                event_type=event.type,
                event_id=event.id,
            )
            return
        
        # Execute handlers in priority order
        for subscription in handlers:
            await subscription.invoke(event)
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event to all matching handlers concurrently.
        
        This method processes handlers in priority groups, executing handlers
        within each priority group concurrently but maintaining the order
        between priority groups.
        
        Args:
            event: The event to publish
        """
        self.logger.debug(
            "Publishing event asynchronously",
            event_type=event.type,
            event_id=event.id,
            topic=event.topic,
        )
        
        # Get handlers for this event
        handlers = self.get_handlers_for_event(event)
        
        if not handlers:
            self.logger.debug(
                "No handlers for event",
                event_type=event.type,
                event_id=event.id,
            )
            return
        
        # Group handlers by priority
        priority_groups: Dict[EventPriority, List[Subscription]] = {}
        for sub in handlers:
            if sub.priority not in priority_groups:
                priority_groups[sub.priority] = []
            priority_groups[sub.priority].append(sub)
        
        # Process each priority group in order
        for priority in sorted(priority_groups.keys(), key=lambda p: p.value):
            group = priority_groups[priority]
            
            # Create tasks for all handlers in this priority group
            tasks = [subscription.invoke(event) for subscription in group]
            
            # Use semaphore to limit concurrency
            semaphore = asyncio.Semaphore(self.max_concurrency)
            
            async def with_semaphore(task):
                async with semaphore:
                    return await task
            
            # Execute all handlers in this priority group concurrently
            await asyncio.gather(
                *(with_semaphore(task) for task in tasks),
                return_exceptions=True,  # Don't let failures block other handlers
            )
    
    async def publish_many(self, events: List[Event]) -> None:
        """
        Publish multiple events sequentially.
        
        Args:
            events: The events to publish
        """
        for event in events:
            await self.publish(event)
    
    async def publish_many_async(self, events: List[Event]) -> None:
        """
        Publish multiple events concurrently.
        
        Args:
            events: The events to publish
        """
        await asyncio.gather(*(self.publish_async(event) for event in events))