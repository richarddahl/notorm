"""
Vector update service for managing embedding updates.

This module provides a service for managing vector embedding updates,
including batch processing, prioritization, and monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime
import uuid
from queue import PriorityQueue
from dataclasses import dataclass, field

from uno.domain.core import UnoEvent
from uno.domain.event_dispatcher import EventDispatcher
from uno.domain.vector_events import (
    VectorContentEvent,
    VectorEmbeddingUpdateRequested,
    VectorEmbeddingUpdated,
)
from uno.sql.emitters.vector import VectorBatchEmitter


@dataclass(order=True)
class UpdateTask:
    """
    Task for updating vector embeddings with priority support.

    This class represents a task in the embedding update queue
    with support for prioritization.
    """

    # The priority field determines the order in the priority queue
    priority: int

    # The actual task data (not used for comparison)
    entity_id: str = field(compare=False)
    entity_type: str = field(compare=False)
    content: str = field(compare=False)
    timestamp: datetime = field(compare=False)
    retries: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)


class VectorUpdateService:
    """
    Service for managing vector embedding updates.

    This service provides a centralized way to manage embedding updates,
    including queuing, prioritization, and batch processing.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        batch_size: int = 10,
        update_interval: float = 1.0,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the vector update service.

        Args:
            dispatcher: Event dispatcher for publishing events
            batch_size: Number of updates to process in a batch
            update_interval: Seconds between update batches
            logger: Optional logger for diagnostic output
        """
        self.dispatcher = dispatcher
        self.batch_size = batch_size
        self.update_interval = update_interval
        self.logger = logger or logging.getLogger(__name__)

        # Task queue for updates
        self.task_queue: PriorityQueue = PriorityQueue()

        # Set of entity IDs currently being processed to avoid duplicates
        self.processing: Set[str] = set()

        # Statistics
        self.stats: Dict[str, Any] = {
            "queued": 0,
            "processed": 0,
            "failed": 0,
            "retried": 0,
            "started_at": datetime.utcnow(),
        }

        # Processing state
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the update service."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        self.logger.info("Vector update service started")

    async def stop(self) -> None:
        """Stop the update service."""
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

        self.logger.info("Vector update service stopped")

    async def queue_update(
        self, entity_id: str, entity_type: str, content: str, priority: int = 0
    ) -> None:
        """
        Queue an embedding update.

        Args:
            entity_id: ID of the entity to update
            entity_type: Type of the entity
            content: Text content to embed
            priority: Priority level (higher values = higher priority)
        """
        # Create task
        task = UpdateTask(
            priority=priority,
            entity_id=entity_id,
            entity_type=entity_type,
            content=content,
            timestamp=datetime.utcnow(),
        )

        # Add to queue
        self.task_queue.put(task)
        self.stats["queued"] += 1

        self.logger.debug(
            f"Queued update for {entity_type} {entity_id} (priority: {priority})"
        )

    async def process_event(self, event: UnoEvent) -> None:
        """
        Process vector-related events.

        Args:
            event: The domain event to process
        """
        # Handle vector content events
        if isinstance(event, VectorContentEvent) and event.operation != "delete":
            # Extract content
            content = " ".join(event.content_fields.values())

            # Queue the update
            await self.queue_update(
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                content=content,
            )

        # Handle explicit update requests
        elif isinstance(event, VectorEmbeddingUpdateRequested):
            await self.queue_update(
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                content=event.content,
                priority=event.priority,
            )

    async def _process_queue(self) -> None:
        """Process tasks from the queue."""
        while self._running:
            try:
                # Process up to batch_size tasks
                processed = 0
                start_time = time.time()

                while not self.task_queue.empty() and processed < self.batch_size:
                    # Get a task
                    task = self.task_queue.get()

                    # Skip if already processing (avoid duplicates)
                    if task.entity_id in self.processing:
                        self.task_queue.task_done()
                        continue

                    # Mark as processing
                    self.processing.add(task.entity_id)

                    try:
                        # Process the task
                        await self._process_task(task)
                        processed += 1
                    finally:
                        # Mark as done and remove from processing
                        self.task_queue.task_done()
                        self.processing.remove(task.entity_id)

                # Log batch statistics
                if processed > 0:
                    duration = time.time() - start_time
                    self.logger.info(
                        f"Processed {processed} vector updates in {duration:.2f}s"
                    )

                # Sleep before next batch
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                self.logger.error(f"Error in update queue processing: {e}")
                await asyncio.sleep(self.update_interval)

    async def _process_task(self, task: UpdateTask) -> None:
        """
        Process a single update task.

        Args:
            task: The update task to process
        """
        try:
            # Publish an embedding update request
            event = VectorEmbeddingUpdateRequested(
                event_id=str(uuid.uuid4()),
                event_type="vector.embedding_update_requested",
                entity_id=task.entity_id,
                entity_type=task.entity_type,
                content=task.content,
                priority=task.priority,
                timestamp=datetime.utcnow(),
            )

            await self.dispatcher.publish(event)
            self.stats["processed"] += 1

        except Exception as e:
            self.logger.error(
                f"Error processing update for {task.entity_type} {task.entity_id}: {e}"
            )
            self.stats["failed"] += 1

            # Retry if not exceeded max retries
            if task.retries < task.max_retries:
                # Decrease priority and increment retry count
                task.priority -= 1
                task.retries += 1

                # Add back to queue
                self.task_queue.put(task)
                self.stats["retried"] += 1

                self.logger.info(
                    f"Retrying update for {task.entity_type} {task.entity_id} "
                    f"(retry {task.retries}/{task.max_retries})"
                )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service statistics
        """
        stats = dict(self.stats)
        stats["queue_size"] = self.task_queue.qsize()
        stats["processing"] = len(self.processing)
        stats["uptime"] = (datetime.utcnow() - stats["started_at"]).total_seconds()

        return stats


class BatchVectorUpdateService:
    """
    Service for batch updating vectors.

    This service provides methods for updating vectors in batch,
    useful for initial data loads and bulk operations.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        batch_size: int = 100,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the batch vector update service.

        Args:
            dispatcher: Event dispatcher for publishing events
            batch_size: Number of entities to process in a batch
            logger: Optional logger for diagnostic output
        """
        self.dispatcher = dispatcher
        self.batch_size = batch_size
        self.logger = logger or logging.getLogger(__name__)

    async def update_all_entities(
        self, entity_type: str, content_fields: List[str]
    ) -> Dict[str, int]:
        """
        Update embeddings for all entities of a given type.

        Args:
            entity_type: The type of entity to update
            content_fields: Fields containing content to vectorize

        Returns:
            Dictionary with operation statistics
        """
        # Create a VectorBatchEmitter for this operation
        emitter = VectorBatchEmitter(
            entity_type=entity_type, content_fields=content_fields
        )

        # Import needed modules
        from uno.database.session import async_session

        # Statistics
        stats = {"total": 0, "processed": 0, "succeeded": 0, "failed": 0}

        try:
            # Get total count
            async with async_session() as session:
                stats["total"] = await emitter.execute_get_count(session)

            # Process in batches
            offset = 0
            while True:
                # Get a batch of entities
                async with async_session() as session:
                    entities = await emitter.execute_get_batch(
                        connection=session, limit=self.batch_size, offset=offset
                    )

                    if not entities:
                        break

                    # Process this batch
                    self.logger.info(
                        f"Processing batch of {len(entities)} {entity_type} entities "
                        f"(offset: {offset})"
                    )

                    batch_start = time.time()
                    for entity in entities:
                        try:
                            # Extract content
                            content_data = {}
                            for field in content_fields:
                                if field in entity and entity[field]:
                                    content_data[field] = str(entity[field])

                            # Skip if no content
                            if not content_data:
                                continue

                            # Create and publish a vector content event
                            event = VectorContentEvent(
                                event_id=str(uuid.uuid4()),
                                event_type=f"{entity_type}.vector_update",
                                entity_id=entity["id"],
                                entity_type=entity_type,
                                content_fields=content_data,
                                operation="update",
                                timestamp=datetime.utcnow(),
                            )

                            await self.dispatcher.publish(event)

                            stats["processed"] += 1
                            stats["succeeded"] += 1

                        except Exception as e:
                            self.logger.error(
                                f"Error processing {entity_type} {entity.get('id')}: {e}"
                            )
                            stats["processed"] += 1
                            stats["failed"] += 1

                    batch_duration = time.time() - batch_start
                    if batch_duration > 0:
                        self.logger.info(
                            f"Processed batch in {batch_duration:.2f}s "
                            f"({len(entities) / batch_duration:.2f} entities/s)"
                        )

                    # Move to next batch
                    offset += len(entities)

            return stats

        except Exception as e:
            self.logger.error(f"Error in batch update: {e}")
            return stats

    async def update_entities_by_ids(
        self, entity_type: str, entity_ids: List[str], content_fields: List[str]
    ) -> Dict[str, int]:
        """
        Update embeddings for specific entities by ID.

        Args:
            entity_type: The type of entity to update
            entity_ids: List of entity IDs to update
            content_fields: Fields containing content to vectorize

        Returns:
            Dictionary with operation statistics
        """
        # Create a VectorBatchEmitter for this operation
        emitter = VectorBatchEmitter(
            entity_type=entity_type, content_fields=content_fields
        )

        # Import needed modules
        from uno.database.session import async_session

        # Statistics
        stats = {"total": len(entity_ids), "processed": 0, "succeeded": 0, "failed": 0}

        try:
            # Process in batches
            for i in range(0, len(entity_ids), self.batch_size):
                batch_ids = entity_ids[i : i + self.batch_size]

                # Get this batch of entities
                async with async_session() as session:
                    entities = await emitter.execute_get_entities_by_ids(
                        connection=session, entity_ids=batch_ids
                    )

                    # Process this batch
                    self.logger.info(
                        f"Processing batch of {len(entities)} {entity_type} entities "
                        f"(batch {i//self.batch_size + 1}/{(len(entity_ids) + self.batch_size - 1) // self.batch_size})"
                    )

                    batch_start = time.time()
                    for entity in entities:
                        try:
                            # Extract content
                            content_data = {}
                            for field in content_fields:
                                if field in entity and entity[field]:
                                    content_data[field] = str(entity[field])

                            # Skip if no content
                            if not content_data:
                                continue

                            # Create and publish a vector content event
                            event = VectorContentEvent(
                                event_id=str(uuid.uuid4()),
                                event_type=f"{entity_type}.vector_update",
                                entity_id=entity["id"],
                                entity_type=entity_type,
                                content_fields=content_data,
                                operation="update",
                                timestamp=datetime.utcnow(),
                            )

                            await self.dispatcher.publish(event)

                            stats["processed"] += 1
                            stats["succeeded"] += 1

                        except Exception as e:
                            self.logger.error(
                                f"Error processing {entity_type} {entity.get('id')}: {e}"
                            )
                            stats["processed"] += 1
                            stats["failed"] += 1

                    batch_duration = time.time() - batch_start
                    if batch_duration > 0:
                        self.logger.info(
                            f"Processed batch in {batch_duration:.2f}s "
                            f"({len(entities) / batch_duration:.2f} entities/s)"
                        )

            return stats

        except Exception as e:
            self.logger.error(f"Error in batch update: {e}")
            return stats
