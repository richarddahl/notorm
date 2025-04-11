"""
Event dispatcher for domain events.

This module provides event dispatching functionality for domain events,
enabling subscribers to react to domain events in a decoupled manner.
"""

import asyncio
import logging
from typing import Dict, List, Set, Type, Callable, Awaitable, TypeVar, Optional, Any, Generic

from uno.domain.core import DomainEvent
from uno.domain.event_store import EventStore


E = TypeVar('E', bound=DomainEvent)
EventHandler = Callable[[E], Awaitable[None]]


class EventDispatcher(Generic[E]):
    """
    Event dispatcher for domain events.
    
    The event dispatcher manages event subscriptions and dispatches events
    to registered handlers when events are published.
    """
    
    def __init__(self, event_store: Optional[EventStore[E]] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the event dispatcher.
        
        Args:
            event_store: Optional event store for persisting events
            logger: Optional logger for diagnostic information
        """
        self.event_store = event_store
        self.logger = logger or logging.getLogger(__name__)
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe a handler to a specific event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The handler function to call when events occur
        """
        if event_type == '*':
            self._wildcard_handlers.append(handler)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            
        self.logger.debug(f"Handler {handler.__name__} subscribed to event type {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            handler: The handler function to unsubscribe
        """
        if event_type == '*':
            if handler in self._wildcard_handlers:
                self._wildcard_handlers.remove(handler)
        elif event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                
        self.logger.debug(f"Handler {handler.__name__} unsubscribed from event type {event_type}")
    
    async def publish(self, event: E) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: The event to publish
        """
        self.logger.debug(f"Publishing event {event.event_type} with ID {event.event_id}")
        
        # Store the event if we have an event store
        if self.event_store:
            try:
                await self.event_store.save_event(event)
            except Exception as e:
                self.logger.error(f"Error saving event to event store: {e}")
        
        # Get handlers for this event type
        handlers = self._handlers.get(event.event_type, []) + self._wildcard_handlers
        
        # Execute all handlers concurrently
        tasks = []
        for handler in handlers:
            # Wrap handler in a try-except to prevent one handler failure from affecting others
            async def safe_execute(h: EventHandler, e: E) -> None:
                try:
                    await h(e)
                except Exception as ex:
                    self.logger.error(f"Error in event handler {h.__name__} for event {e.event_type}: {ex}")
            
            tasks.append(asyncio.create_task(safe_execute(handler, event)))
            
        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks)
            
        self.logger.debug(f"Event {event.event_type} with ID {event.event_id} published to {len(handlers)} handlers")


class PostgresEventListener:
    """
    Listen for events from PostgreSQL's NOTIFY/LISTEN mechanism.
    
    This class sets up a listener for PostgreSQL notifications and dispatches
    them as domain events using the event dispatcher.
    """
    
    def __init__(
        self,
        dispatcher: EventDispatcher,
        event_type: Type[E],
        channel: str = 'domain_events',
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the PostgreSQL event listener.
        
        Args:
            dispatcher: The event dispatcher to publish events to
            event_type: The type of events to create from notifications
            channel: The PostgreSQL notification channel to listen on
            logger: Optional logger for diagnostic information
        """
        self.dispatcher = dispatcher
        self.event_type = event_type
        self.channel = channel
        self.logger = logger or logging.getLogger(__name__)
        self._running = False
        self._task = None
    
    async def start(self) -> None:
        """Start listening for events."""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._listen_for_events())
        self.logger.info(f"Started PostgreSQL event listener on channel {self.channel}")
    
    async def stop(self) -> None:
        """Stop listening for events."""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            
        self.logger.info(f"Stopped PostgreSQL event listener on channel {self.channel}")
    
    async def _listen_for_events(self) -> None:
        """Listen for events from PostgreSQL and dispatch them."""
        import json
        from asyncpg import create_pool, Connection
        from uno.settings import uno_settings
        
        # Create a connection pool
        pool = await create_pool(
            user=uno_settings.DB_USER,
            password=uno_settings.DB_USER_PW,
            database=uno_settings.DB_NAME,
            host=uno_settings.DB_HOST,
            port=uno_settings.DB_PORT
        )
        
        try:
            # Get a connection from the pool
            async with pool.acquire() as conn:
                # Listen for notifications
                await conn.add_listener(self.channel, self._on_notification)
                await conn.execute(f"LISTEN {self.channel}")
                
                # Stay alive until stopped
                self.logger.info(f"Listening for events on channel {self.channel}")
                while self._running:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Error in PostgreSQL event listener: {e}")
        finally:
            # Clean up
            await pool.close()
    
    async def _on_notification(self, conn: Any, pid: int, channel: str, payload: str) -> None:
        """Handle a notification from PostgreSQL."""
        try:
            # Parse the payload
            import json
            data = json.loads(payload)
            
            # Create a domain event from the notification
            event = self.event_type(
                event_id=data.get('event_id'),
                event_type=data.get('event_type'),
                timestamp=data.get('timestamp'),
                aggregate_id=data.get('aggregate_id'),
                aggregate_type=data.get('aggregate_type')
            )
            
            # Dispatch the event
            await self.dispatcher.publish(event)
            
        except Exception as e:
            self.logger.error(f"Error processing PostgreSQL notification: {e}")


def domain_event_handler(event_type: str = '*'):
    """
    Decorator for domain event handlers.
    
    This decorator marks a method as a domain event handler and registers
    it with the event dispatcher when the class is instantiated.
    
    Args:
        event_type: The type of event to handle, or '*' for all events
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable[[Any, E], Awaitable[None]]):
        # Mark the function as an event handler
        func.__is_event_handler__ = True
        func.__event_type__ = event_type
        return func
    return decorator


class EventSubscriber:
    """
    Base class for event subscribers.
    
    Event subscribers contain one or more event handlers and register
    them with the event dispatcher when instantiated.
    """
    
    def __init__(self, dispatcher: EventDispatcher):
        """
        Initialize the event subscriber.
        
        Args:
            dispatcher: The event dispatcher to register handlers with
        """
        self.dispatcher = dispatcher
        
        # Register all methods decorated with @domain_event_handler
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '__is_event_handler__'):
                event_type = getattr(attr, '__event_type__')
                dispatcher.subscribe(event_type, attr)