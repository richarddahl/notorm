"""Projector implementation for the Uno framework.

This module defines the projection system for transforming domain events into read models
as part of the CQRS pattern's query side.
"""

import asyncio
import logging
import time
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from enum import Enum, auto
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union,
    Protocol, cast, Awaitable, NamedTuple, Counter
)

from uno.core.result import Result, Success, Failure
from uno.domain.events import DomainEvent, EventBus, EventStore, EventHandler
from uno.read_model.read_model import ReadModel, ReadModelRepository

# Type variables
T = TypeVar('T', bound=ReadModel)
EventT = TypeVar('EventT', bound=DomainEvent)


class ProjectionErrorHandlingStrategy(Enum):
    """Strategy for handling errors in projections."""
    FAIL_FAST = auto()          # Stop processing on first error
    CONTINUE = auto()           # Log errors and continue
    RETRY = auto()              # Retry failed events
    DEAD_LETTER = auto()        # Move failed events to dead-letter queue


@dataclass
class ProjectionError:
    """Information about a projection error."""
    event_id: str
    event_type: str
    aggregate_id: Optional[str]
    error_message: str
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0
    last_retry: Optional[datetime] = None


@dataclass
class ProjectionStats:
    """Statistics for projections."""
    total_events_processed: int = 0
    successful_events: int = 0
    failed_events: int = 0
    retry_attempts: int = 0
    retry_successes: int = 0
    processing_time_ms: float = 0.0
    last_processed_event_id: Optional[str] = None
    last_processed_timestamp: Optional[datetime] = None
    event_type_counts: Dict[str, int] = field(default_factory=dict)
    
    def record_success(self, event: DomainEvent, processing_time_ms: float) -> None:
        """Record a successful event processing."""
        self.total_events_processed += 1
        self.successful_events += 1
        self.processing_time_ms += processing_time_ms
        self.last_processed_event_id = event.event_id
        self.last_processed_timestamp = datetime.now(UTC)
        
        # Update event type counts
        event_type = event.event_type
        if event_type in self.event_type_counts:
            self.event_type_counts[event_type] += 1
        else:
            self.event_type_counts[event_type] = 1
    
    def record_failure(self, event: DomainEvent) -> None:
        """Record a failed event processing."""
        self.total_events_processed += 1
        self.failed_events += 1
        self.last_processed_event_id = event.event_id
        self.last_processed_timestamp = datetime.now(UTC)
    
    def record_retry(self, success: bool) -> None:
        """Record a retry attempt."""
        self.retry_attempts += 1
        if success:
            self.retry_successes += 1


class ProgressTracker:
    """Track progress of event processing for projections."""
    
    def __init__(self, projection_id: str, repository: Optional[Any] = None):
        """
        Initialize the progress tracker.
        
        Args:
            projection_id: Unique identifier for the projection
            repository: Optional repository for persisting progress
        """
        self.projection_id = projection_id
        self.repository = repository
        self.last_processed_position: Optional[int] = None
        self.last_processed_timestamp: Optional[datetime] = None
        self.checkpoint_frequency: int = 100  # Save progress every 100 events
        self.events_since_checkpoint: int = 0
    
    async def record_progress(self, position: int, timestamp: Optional[datetime] = None) -> None:
        """
        Record processing progress.
        
        Args:
            position: The position/sequence number of the processed event
            timestamp: Optional timestamp of the processed event
        """
        self.last_processed_position = position
        self.last_processed_timestamp = timestamp or datetime.now(UTC)
        self.events_since_checkpoint += 1
        
        # Save checkpoint if needed
        if self.events_since_checkpoint >= self.checkpoint_frequency:
            await self.save_checkpoint()
    
    async def save_checkpoint(self) -> None:
        """Save the current progress checkpoint."""
        if self.repository and self.last_processed_position is not None:
            try:
                await self.repository.save_progress(
                    self.projection_id,
                    self.last_processed_position,
                    self.last_processed_timestamp
                )
                self.events_since_checkpoint = 0
            except Exception as e:
                logging.error(f"Error saving progress checkpoint: {e}")
    
    async def load_checkpoint(self) -> bool:
        """
        Load the last saved checkpoint.
        
        Returns:
            True if checkpoint was loaded successfully, False otherwise
        """
        if self.repository:
            try:
                checkpoint = await self.repository.load_progress(self.projection_id)
                if checkpoint:
                    self.last_processed_position, self.last_processed_timestamp = checkpoint
                    return True
            except Exception as e:
                logging.error(f"Error loading progress checkpoint: {e}")
        return False


class Projection(Generic[T, EventT], ABC):
    """
    Abstract base class for projections.
    
    Projections are responsible for transforming domain events into read models.
    They define how domain events are applied to read models to keep the query
    side of the application in sync with the command side.
    
    Type Parameters:
        T: The type of read model this projection produces
        EventT: The type of event this projection handles
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
            # Remove from the list
            self._projections[event_type] = [p for p in self._projections[event_type] if id(p) != id(projection)]
            
            # If no more projections for this event type, unsubscribe the handler
            if not self._projections[event_type]:
                handler = self._handlers.pop(event_type, None)
                if handler:
                    self.event_bus.unsubscribe(
                        handler=handler,
                        event_type=event_type,
                    )
                # Remove the empty list
                del self._projections[event_type]
                
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


@dataclass
class SnapshotConfig:
    """Configuration for snapshot creation."""
    enabled: bool = True
    frequency: int = 100  # Create snapshot every 100 events
    retain_count: int = 5  # Number of snapshots to retain per aggregate
    min_time_between_snapshots: timedelta = timedelta(minutes=5)
    max_events_before_snapshot: int = 1000  # Force snapshot after this many events
    include_metadata: bool = True


class SnapshotProjector(Projector):
    """
    Projector with snapshot support.
    
    This projector creates and uses snapshots to improve performance
    when rebuilding read models from event history.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        event_store: EventStore,
        snapshot_repository: Any,
        snapshot_config: Optional[SnapshotConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the snapshot projector.
        
        Args:
            event_bus: The event bus to subscribe to
            event_store: Event store for retrieving events
            snapshot_repository: Repository for storing and retrieving snapshots
            snapshot_config: Optional snapshot configuration
            logger: Optional logger instance
        """
        super().__init__(event_bus, event_store, logger)
        self.snapshot_repository = snapshot_repository
        self.snapshot_config = snapshot_config or SnapshotConfig()
        self._event_counters: Dict[str, int] = {}  # Map aggregateId -> event count
        self._last_snapshot: Dict[str, datetime] = {}  # Map aggregateId -> timestamp
        
    async def rebuild_for_aggregate(self, aggregate_id: str, aggregate_type: str = None) -> None:
        """
        Rebuild read models for a specific aggregate, using snapshots if available.
        
        Args:
            aggregate_id: The ID of the aggregate to rebuild read models for
            aggregate_type: Optional aggregate type to filter events
        """
        if not self.event_store:
            self.logger.error("Cannot rebuild read model: no event store provided")
            return
        
        # Check if we have a snapshot
        snapshot = None
        snapshot_version = 0
        
        if self.snapshot_config.enabled:
            try:
                snapshot_result = await self.snapshot_repository.get_latest_snapshot(
                    aggregate_id, aggregate_type
                )
                if snapshot_result.is_success() and snapshot_result.value:
                    snapshot, snapshot_version = snapshot_result.value
                    self.logger.info(f"Using snapshot for {aggregate_id} at version {snapshot_version}")
            except Exception as e:
                self.logger.error(f"Error retrieving snapshot for {aggregate_id}: {e}")
        
        # Get events after the snapshot version
        event_filter = {"aggregate_id": aggregate_id}
        if aggregate_type:
            event_filter["aggregate_type"] = aggregate_type
            
        events = await self.event_store.get_events_by_aggregate_id(
            aggregate_id=aggregate_id, 
            after_version=snapshot_version if snapshot else None
        )
        
        if not events and not snapshot:
            self.logger.info(f"No events or snapshot found for aggregate {aggregate_id}")
            return
            
        # Apply snapshot if available
        if snapshot:
            for event_type, projections in self._projections.items():
                for projection in projections:
                    if hasattr(projection, "apply_snapshot"):
                        try:
                            read_model = await projection.apply_snapshot(snapshot, aggregate_id)
                            if read_model:
                                await projection.repository.save(read_model)
                                self.logger.debug(f"Applied snapshot for {aggregate_id} to read model {read_model.id}")
                        except Exception as e:
                            self.logger.error(f"Error applying snapshot for {aggregate_id}: {e}")
        
        # Apply events
        event_count = 0
        for event in events:
            event_type = type(event)
            event_count += 1
            
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
                    self.logger.error(f"Error applying event {event.event_type} to aggregate {aggregate_id}: {e}")
        
        # Create a new snapshot if needed
        if (self.snapshot_config.enabled and event_count > 0 and
                (event_count >= self.snapshot_config.frequency or 
                 (snapshot_version + event_count) >= self.snapshot_config.max_events_before_snapshot)):
            try:
                await self._create_snapshot(aggregate_id, aggregate_type, snapshot_version + event_count)
            except Exception as e:
                self.logger.error(f"Error creating snapshot for {aggregate_id}: {e}")
    
    async def _create_snapshot(self, aggregate_id: str, aggregate_type: str, version: int) -> None:
        """
        Create a new snapshot for an aggregate.
        
        Args:
            aggregate_id: The aggregate ID
            aggregate_type: The aggregate type
            version: The version of the aggregate
        """
        # Collect all read models for this aggregate
        read_models = {}
        metadata = {}
        
        for event_type, projections in self._projections.items():
            for projection in projections:
                if hasattr(projection, "get_for_snapshot"):
                    try:
                        read_model = await projection.get_for_snapshot(aggregate_id)
                        if read_model:
                            model_type = projection.read_model_type.__name__
                            read_models[model_type] = read_model
                    except Exception as e:
                        self.logger.error(f"Error getting read model for snapshot of {aggregate_id}: {e}")
        
        if not read_models:
            self.logger.warning(f"No read models to snapshot for {aggregate_id}")
            return
            
        # Add metadata if configured
        if self.snapshot_config.include_metadata:
            metadata = {
                "created_at": datetime.now(UTC).isoformat(),
                "projection_versions": {
                    proj.__class__.__name__: getattr(proj, "version", 1)
                    for event_type, projections in self._projections.items()
                    for proj in projections
                }
            }
        
        # Create the snapshot
        try:
            result = await self.snapshot_repository.save_snapshot(
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                version=version,
                read_models=read_models,
                metadata=metadata
            )
            
            if result.is_success():
                self.logger.info(f"Created snapshot for {aggregate_id} at version {version}")
                self._last_snapshot[aggregate_id] = datetime.now(UTC)
            else:
                self.logger.error(f"Failed to create snapshot for {aggregate_id}: {result.error}")
                
        except Exception as e:
            self.logger.error(f"Error saving snapshot for {aggregate_id}: {e}")
            
        # Prune old snapshots if configured
        if self.snapshot_config.retain_count > 0:
            try:
                await self.snapshot_repository.prune_snapshots(
                    aggregate_id=aggregate_id,
                    retain_count=self.snapshot_config.retain_count
                )
            except Exception as e:
                self.logger.error(f"Error pruning snapshots for {aggregate_id}: {e}")
    
    async def rebuild_all(self) -> None:
        """
        Rebuild all read models from the event store.
        
        This optimized implementation uses snapshots and processes
        events by aggregate for better performance.
        """
        if not self.event_store:
            self.logger.error("Cannot rebuild read models: no event store provided")
            return
        
        self.logger.info("Rebuilding all read models with snapshots...")
        
        # Get all unique aggregate IDs from the event store
        # This is a placeholder - in a real implementation, you'd have an optimized query
        all_events = await self.event_store.get_all_events()
        
        # Group by aggregate ID
        aggregate_ids = set()
        aggregate_types = {}
        
        for event in all_events:
            if hasattr(event, "aggregate_id") and event.aggregate_id:
                aggregate_ids.add(event.aggregate_id)
                if hasattr(event, "aggregate_type") and event.aggregate_type:
                    aggregate_types[event.aggregate_id] = event.aggregate_type
        
        # Process each aggregate
        self.logger.info(f"Rebuilding {len(aggregate_ids)} aggregates")
        for aggregate_id in aggregate_ids:
            aggregate_type = aggregate_types.get(aggregate_id)
            await self.rebuild_for_aggregate(aggregate_id, aggregate_type)
            
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


class VersionedProjection(Generic[T, EventT], Projection[T, EventT]):
    """
    Projection that supports versioning.
    
    This class enables projections to handle different versions of events or
    read models, supporting schema evolution and backwards compatibility.
    """
    
    @property
    def version(self) -> int:
        """Get the current projection version."""
        return 1  # Override in subclasses
    
    async def apply(self, event: EventT) -> Optional[T]:
        """
        Apply an event based on its version.
        
        Args:
            event: The event to apply
            
        Returns:
            The created or updated read model, or None if no action was taken
        """
        # Extract event version if available
        event_version = getattr(event, "version", 1)
        
        # Apply appropriate version handler based on event version
        method_name = f"apply_v{event_version}"
        if hasattr(self, method_name):
            handler = getattr(self, method_name)
            return await handler(event)
        
        # Fall back to latest version handler if no specific handler found
        return await self._apply_latest(event)
    
    @abstractmethod
    async def _apply_latest(self, event: EventT) -> Optional[T]:
        """
        Apply the latest version of the projection.
        
        Subclasses must implement this method to handle the latest version
        of events when no specific version handler is found.
        
        Args:
            event: The event to apply
            
        Returns:
            The created or updated read model, or None if no action was taken
        """
        pass


class ResilientProjection(Generic[T, EventT], Projection[T, EventT]):
    """
    Projection with error handling and retry capabilities.
    
    This class extends the basic projection with robust error handling,
    retry mechanisms, and progress tracking.
    """
    
    def __init__(
        self,
        read_model_type: Type[T],
        event_type: Type[EventT],
        repository: ReadModelRepository[T],
        error_strategy: ProjectionErrorHandlingStrategy = ProjectionErrorHandlingStrategy.CONTINUE,
        max_retries: int = 3,
        retry_delay_seconds: int = 5,
        progress_repository: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the resilient projection.
        
        Args:
            read_model_type: The type of read model this projection creates/updates
            event_type: The type of event this projection handles
            repository: The repository for storing read models
            error_strategy: Strategy for handling errors
            max_retries: Maximum number of retry attempts for failed events
            retry_delay_seconds: Delay between retry attempts in seconds
            progress_repository: Optional repository for tracking progress
            logger: Optional logger instance
        """
        super().__init__(read_model_type, event_type, repository, logger)
        self.error_strategy = error_strategy
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.stats = ProjectionStats()
        self.failed_events: Dict[str, ProjectionError] = {}
        self.progress_tracker = ProgressTracker(
            f"{read_model_type.__name__}_{event_type.__name__}",
            progress_repository
        )
    
    async def handle_event(self, event: EventT) -> Result[Optional[T]]:
        """
        Handle an event with error handling and retry mechanism.
        
        Args:
            event: The event to handle
            
        Returns:
            Result containing the created/updated read model or None
        """
        start_time = time.time()
        event_id = str(event.event_id)
        
        try:
            self.logger.debug(f"Handling event {event.event_type} ({event_id})")
            
            # Apply the event to create or update a read model
            read_model = await self.apply(event)
            
            # Save the read model if one was returned
            if read_model:
                await self.repository.save(read_model)
                self.logger.debug(f"Saved read model {read_model.id} (version {read_model.version})")
            
            # Record success
            processing_time = (time.time() - start_time) * 1000
            self.stats.record_success(event, processing_time)
            
            # Record progress
            position = getattr(event, "position", 0) or getattr(event, "sequence", 0)
            await self.progress_tracker.record_progress(position, getattr(event, "timestamp", None))
            
            # Remove from failed events if it was previously failed
            if event_id in self.failed_events:
                del self.failed_events[event_id]
            
            return Success(read_model)
            
        except Exception as e:
            self.logger.error(f"Error handling event {event.event_type} ({event_id}): {str(e)}")
            
            # Record failure
            self.stats.record_failure(event)
            
            # Create or update error record
            aggregate_id = getattr(event, "aggregate_id", None)
            
            if event_id in self.failed_events:
                error = self.failed_events[event_id]
                error.retry_count += 1
                error.last_retry = datetime.now(UTC)
                error.error_message = str(e)
            else:
                import traceback
                self.failed_events[event_id] = ProjectionError(
                    event_id=event_id,
                    event_type=event.event_type,
                    aggregate_id=aggregate_id,
                    error_message=str(e),
                    stack_trace=traceback.format_exc()
                )
            
            # Handle based on strategy
            if self.error_strategy == ProjectionErrorHandlingStrategy.FAIL_FAST:
                # Re-raise the exception
                raise
                
            elif self.error_strategy == ProjectionErrorHandlingStrategy.RETRY:
                # Retry if under max retries
                error = self.failed_events[event_id]
                if error.retry_count < self.max_retries:
                    self.logger.info(f"Scheduling retry {error.retry_count + 1}/{self.max_retries} for event {event_id}")
                    # The retry would be handled by the caller or a retry queue in a real impl
                    
            elif self.error_strategy == ProjectionErrorHandlingStrategy.DEAD_LETTER:
                # Move to dead letter queue (would be implemented in a real system)
                self.logger.info(f"Moving event {event_id} to dead-letter queue")
            
            return Failure(str(e))
    
    async def retry_failed_events(self) -> Dict[str, bool]:
        """
        Retry processing failed events.
        
        Returns:
            Dictionary mapping event IDs to success status
        """
        if not self.failed_events:
            return {}
        
        results = {}
        retry_list = list(self.failed_events.items())
        
        for event_id, error in retry_list:
            if error.retry_count >= self.max_retries:
                self.logger.warning(f"Skipping retry for event {event_id}: max retries exceeded")
                results[event_id] = False
                continue
            
            self.logger.info(f"Retrying event {event_id} (attempt {error.retry_count + 1}/{self.max_retries})")
            
            # In a real implementation, we would retrieve the event from the event store
            # For now, we'll assume a method to fetch the event
            try:
                event = await self._fetch_event_by_id(event_id)
                if not event:
                    self.logger.error(f"Could not fetch event {event_id} for retry")
                    results[event_id] = False
                    continue
                
                # Process the event
                result = await self.handle_event(event)
                success = result.is_success()
                
                # Record retry result
                self.stats.record_retry(success)
                results[event_id] = success
                
                # Remove from failed events if successful
                if success and event_id in self.failed_events:
                    del self.failed_events[event_id]
                
                # Wait before next retry
                if len(retry_list) > 1:
                    await asyncio.sleep(self.retry_delay_seconds)
                    
            except Exception as e:
                self.logger.error(f"Error during retry for event {event_id}: {str(e)}")
                results[event_id] = False
        
        return results
    
    async def _fetch_event_by_id(self, event_id: str) -> Optional[EventT]:
        """
        Fetch an event by its ID.
        
        This is a placeholder method. In a real implementation, this would
        retrieve the event from the event store.
        
        Args:
            event_id: The ID of the event to fetch
            
        Returns:
            The event if found, None otherwise
        """
        # This would be implemented in a real system to fetch from event store
        # For now, just return None
        return None
    
    def get_stats(self) -> ProjectionStats:
        """Get the current projection statistics."""
        return self.stats
    
    def get_failed_events(self) -> Dict[str, ProjectionError]:
        """Get all failed events."""
        return self.failed_events
    
    async def reset_stats(self) -> None:
        """Reset the projection statistics."""
        self.stats = ProjectionStats()
    
    async def clear_failed_events(self) -> None:
        """Clear all failed events."""
        self.failed_events.clear()


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