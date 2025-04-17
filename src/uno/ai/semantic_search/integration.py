"""
Integration utilities for semantic search.

This module provides integration helpers to connect semantic search
with other components of the Uno framework, such as domain entities
and repositories.
"""

import logging
from typing import (
    List,
    Dict,
    Any,
    Optional,
    Type,
    Callable,
    TypeVar,
    Generic,
    Protocol,
    Union,
)
from uuid import UUID

from uno.ai.semantic_search.engine import SemanticSearchEngine
from uno.core.unified_events import EventBus, subscribe, UnoDomainEvent

# Set up logger
logger = logging.getLogger(__name__)

# Define type variables for entity types
T = TypeVar("T")


class EntityProtocol(Protocol):
    """Protocol for entities that can be indexed."""

    id: Union[str, UUID]

    def dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        ...


class EntityIndexer(Generic[T]):
    """
    Indexer for domain entities.

    Indexes domain entities in the semantic search engine,
    connecting domain events to search indexing.
    """

    def __init__(
        self,
        engine: SemanticSearchEngine,
        entity_type: str,
        text_extractor: Callable[[T], str],
        metadata_extractor: Optional[Callable[[T], Dict[str, Any]]] = None,
        id_formatter: Optional[Callable[[T], str]] = None,
        entity_class: Optional[Type[T]] = None,
    ):
        """
        Initialize the entity indexer.

        Args:
            engine: Semantic search engine
            entity_type: Type name for indexed entities
            text_extractor: Function to extract text from entities
            metadata_extractor: Function to extract metadata from entities
            id_formatter: Function to format entity IDs (defaults to str)
            entity_class: Optional entity class for type checking
        """
        self.engine = engine
        self.entity_type = entity_type
        self.text_extractor = text_extractor
        self.metadata_extractor = metadata_extractor
        self.id_formatter = id_formatter or (lambda x: str(x.id))
        self.entity_class = entity_class

    async def index_entity(self, entity: T) -> Any:
        """
        Index a single entity.

        Args:
            entity: Entity to index

        Returns:
            ID of the indexed document
        """
        # Type check if entity class is provided
        if self.entity_class and not isinstance(entity, self.entity_class):
            logger.warning(
                f"Expected entity type {self.entity_class.__name__}, "
                f"got {type(entity).__name__}"
            )

        # Extract text
        text = self.text_extractor(entity)

        # Extract metadata
        metadata = None
        if self.metadata_extractor:
            metadata = self.metadata_extractor(entity)

        # Format entity ID
        entity_id = self.id_formatter(entity)

        # Index document
        doc_id = await self.engine.index_document(
            document=text,
            entity_id=entity_id,
            entity_type=self.entity_type,
            metadata=metadata,
        )

        logger.debug(f"Indexed entity {entity_id} of type {self.entity_type}")
        return doc_id

    async def index_entities(self, entities: List[T]) -> List[Any]:
        """
        Index multiple entities.

        Args:
            entities: List of entities to index

        Returns:
            List of indexed document IDs
        """
        documents = []

        for entity in entities:
            # Extract text
            text = self.text_extractor(entity)

            # Extract metadata
            metadata = None
            if self.metadata_extractor:
                metadata = self.metadata_extractor(entity)

            # Format entity ID
            entity_id = self.id_formatter(entity)

            documents.append(
                {
                    "text": text,
                    "entity_id": entity_id,
                    "entity_type": self.entity_type,
                    "metadata": metadata,
                }
            )

        # Index documents in batch
        doc_ids = await self.engine.index_batch(documents)

        logger.debug(f"Indexed {len(doc_ids)} entities of type {self.entity_type}")
        return doc_ids

    async def delete_entity(self, entity_id: Union[str, UUID]) -> int:
        """
        Delete an entity from the index.

        Args:
            entity_id: ID of the entity to delete

        Returns:
            Number of documents deleted
        """
        count = await self.engine.delete_document(
            entity_id=str(entity_id), entity_type=self.entity_type
        )

        logger.debug(f"Deleted entity {entity_id} of type {self.entity_type}")
        return count


# Event integration
class EntityEvent(UnoDomainEvent):
    """Base class for entity events."""

    entity: Any


class EntityCreatedEvent(EntityEvent):
    """Event fired when an entity is created."""

    pass


class EntityUpdatedEvent(EntityEvent):
    """Event fired when an entity is updated."""

    pass


class EntityDeletedEvent(UnoDomainEvent):
    """Event fired when an entity is deleted."""

    entity_id: Union[str, UUID]
    entity_type: str


def connect_entity_events(
    indexer: EntityIndexer,
    event_bus: Optional[EventBus] = None,
    entity_created_event: Type[EntityEvent] = EntityCreatedEvent,
    entity_updated_event: Type[EntityEvent] = EntityUpdatedEvent,
    entity_deleted_event: Type[EntityDeletedEvent] = EntityDeletedEvent,
) -> None:
    """
    Connect entity events to indexer actions.

    Args:
        indexer: Entity indexer
        event_bus: Event bus (default: get from event_bus module)
        entity_created_event: Event type for entity creation
        entity_updated_event: Event type for entity updates
        entity_deleted_event: Event type for entity deletion
    """
    # Get event bus if not provided
    if event_bus is None:
        from uno.core.unified_events import get_event_bus

        event_bus = get_event_bus()

    # Define event handlers
    @subscribe(entity_created_event)
    async def handle_entity_created(event: EntityEvent) -> None:
        try:
            await indexer.index_entity(event.entity)
        except Exception as e:
            logger.error(f"Error indexing created entity: {str(e)}")

    @subscribe(entity_updated_event)
    async def handle_entity_updated(event: EntityEvent) -> None:
        try:
            await indexer.index_entity(event.entity)
        except Exception as e:
            logger.error(f"Error indexing updated entity: {str(e)}")

    @subscribe(entity_deleted_event)
    async def handle_entity_deleted(event: EntityDeletedEvent) -> None:
        try:
            if event.entity_type == indexer.entity_type:
                await indexer.delete_entity(event.entity_id)
        except Exception as e:
            logger.error(f"Error deleting entity from index: {str(e)}")

    # Register handlers with event bus
    event_bus.register(handle_entity_created)
    event_bus.register(handle_entity_updated)
    event_bus.register(handle_entity_deleted)

    logger.info(
        f"Connected entity events for {indexer.entity_type} to semantic search indexing"
    )
