"""Projector implementation for the Uno framework.

This module defines the projection system for transforming domain events into read models
as part of the CQRS pattern's query side.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union,
    Protocol, cast, Awaitable
)

from uno.domain.events import DomainEvent, EventBus, EventStore, EventHandler
from uno.read_model.read_model import ReadModel, ReadModelRepository

# Type variables
T = TypeVar('T', bound=ReadModel)
EventT = TypeVar('EventT', bound=DomainEvent)


class Projection(Generic[T, EventT], ABC):
    """
    Abstract base class for projections.
    
    Projections are responsible for transforming domain events into read models.
    They define how domain events are applied to read models to keep the query
    side of the application in sync with the command side.
    """
    
    def __init__(
        self,
        read_model_type: Type[T],
        event_type: Type[EventT],
        repository: ReadModelRepository[T],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the projection.
        
        Args:
            read_model_type: The type of read model this projection creates/updates
            event_type: The type of event this projection handles
            repository: The repository for storing read models
            logger: Optional logger instance
        """
        self.read_model_type = read_model_type
        self.event_type = event_type
        self.repository = repository
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def apply(self, event: EventT) -> Optional[T]:
        """
        Apply an event to create or update a read model.
        
        Args:
            event: The event to apply
            
        Returns:
            The created or updated read model, or None if no action was taken
        """
        pass
    
    async def handle_event(self, event: EventT) -> None:
        """
        Handle an event by applying it and saving the result.
        
        Args:
            event: The event to handle
        """
        try:
            self.logger.debug(f"Handling event {event.event_type} ({event.event_id})")
            
            # Apply the event to create or update a read model
            read_model = await self.apply(event)
            
            # Save the read model if one was returned
            if read_model:
                await self.repository.save(read_model)
                self.logger.debug(f"Saved read model {read_model.id} (version {read_model.version})")
        except Exception as e:
            self.logger.error(f"Error handling event {event.event_type}: {str(e)}")


class ProjectionHandler(EventHandler[EventT]):
    """
    Event handler that delegates to a projection.
    
    This class bridges the gap between the event system and projections.
    """
    
    def __init__(
        self,
        projection: Projection[Any, EventT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the projection handler.
        
        Args:
            projection: The projection to delegate to
            logger: Optional logger instance
        """
        super().__init__(projection.event_type)
        self.projection = projection
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def handle(self, event: EventT) -> None:
        """
        Handle an event by delegating to the projection.
        
        Args:
            event: The event to handle
        """
        await self.projection.handle_event(event)


class Projector:
    """
    Projector for managing projections.
    
    The projector manages a set of projections and ensures that
    domain events are routed to the appropriate projections.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        event_store: Optional[EventStore] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the projector.
        
        Args:
            event_bus: The event bus to subscribe to
            event_store: Optional event store for replaying events
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.event_store = event_store
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._projections: Dict[Type[DomainEvent], List[Projection]] = {}
        self._handlers: Dict[Type[DomainEvent], ProjectionHandler] = {}
    
    def register_projection(self, projection: Projection) -> None:
        """
        Register a projection with the projector.
        
        Args:
            projection: The projection to register
        """
        # Add the projection to the list for its event type
        event_type = projection.event_type
        if event_type not in self._projections:
            self._projections[event_type] = []
        self._projections[event_type].append(projection)
        
        # Create a handler for the event type if one doesn't exist
        if event_type not in self._handlers:
            handler = ProjectionHandler(projection, self.logger)
            self._handlers[event_type] = handler
            
            # Subscribe the handler to the event bus
            self.event_bus.subscribe(
                handler=handler,
                event_type=event_type,
            )
            
            self.logger.debug(f"Registered projection for event type {event_type.__name__}")
    
    def unregister_projection(self, projection: Projection) -> None:
        """
        Unregister a projection from the projector.
        
        Args:
            projection: The projection to unregister
        """
        event_type = projection.event_type
        
        # Remove the projection from the list for its event type
        if event_type in self._projections:
            self._projections[event_type] = [p for p in self._projections[event_type] if p != projection]
            
            # If no more projections for this event type, unsubscribe the handler
            if not self._projections[event_type]:
                handler = self._handlers.pop(event_type, None)
                if handler:
                    self.event_bus.unsubscribe(
                        handler=handler,
                        event_type=event_type,
                    )
                
                self.logger.debug(f"Unregistered projection for event type {event_type.__name__}")
    
    async def rebuild_all(self) -> None:
        """
        Rebuild all read models by replaying events from the event store.
        
        This method is useful for rebuilding read models from scratch,
        for example after changing a projection or adding a new one.
        """
        if not self.event_store:
            self.logger.error("Cannot rebuild read models: no event store provided")
            return
        
        self.logger.info("Rebuilding all read models...")
        
        # Get all events from the event store
        events = await self.event_store.get_events()
        
        # Process events in order
        for event in events:
            event_type = type(event)
            
            # Skip events that don't have projections
            if event_type not in self._projections:
                continue
            
            # Apply each projection for this event type
            for projection in self._projections[event_type]:
                try:
                    read_model = await projection.apply(event)
                    if read_model:
                        await projection.repository.save(read_model)
                except Exception as e:
                    self.logger.error(f"Error rebuilding projection for event {event.event_type}: {str(e)}")
        
        self.logger.info("Rebuild complete")


class AsyncProjector(Projector):
    """
    Asynchronous projector for managing projections.
    
    This projector processes events asynchronously using a queue,
    which can improve performance and scalability.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        event_store: Optional[EventStore] = None,
        batch_size: int = 100,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the async projector.
        
        Args:
            event_bus: The event bus to subscribe to
            event_store: Optional event store for replaying events
            batch_size: Maximum number of events to process in a batch
            logger: Optional logger instance
        """
        super().__init__(event_bus, event_store, logger)
        self.batch_size = batch_size
        self._queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the async projector."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        self.logger.info("Async projector started")
    
    async def stop(self) -> None:
        """Stop the async projector."""
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
        
        self.logger.info("Async projector stopped")
    
    async def _worker(self) -> None:
        """Worker that processes events from the queue."""
        while self._running:
            try:
                # Get events up to batch size
                events = []
                for _ in range(self.batch_size):
                    try:
                        event = self._queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break
                
                if not events:
                    # If no events, wait for one
                    event = await self._queue.get()
                    events = [event]
                
                # Process events
                await self._process_events(events)
                
                # Mark tasks as done
                for _ in events:
                    self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in projector worker: {str(e)}")
    
    async def _process_events(self, events: List[DomainEvent]) -> None:
        """
        Process a batch of events.
        
        Args:
            events: The events to process
        """
        for event in events:
            event_type = type(event)
            
            # Skip events that don't have projections
            if event_type not in self._projections:
                continue
            
            # Apply each projection for this event type
            for projection in self._projections[event_type]:
                try:
                    read_model = await projection.apply(event)
                    if read_model:
                        await projection.repository.save(read_model)
                except Exception as e:
                    self.logger.error(f"Error applying projection for event {event.event_type}: {str(e)}")


class BatchProjection(Generic[T, EventT], Projection[T, EventT]):
    """
    Base class for batch projections.
    
    Batch projections process multiple events at once, which can be more
    efficient for certain types of projections.
    """
    
    async def apply_batch(self, events: List[EventT]) -> List[Optional[T]]:
        """
        Apply a batch of events to create or update read models.
        
        Args:
            events: The events to apply
            
        Returns:
            List of created or updated read models, or None for events that didn't result in changes
        """
        # Default implementation applies events one by one
        results = []
        for event in events:
            results.append(await self.apply(event))
        return results