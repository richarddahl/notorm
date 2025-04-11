"""
Event-driven vector search components.

This module provides event-driven capabilities for the vector search system,
enabling real-time updates and synchronization of vector embeddings.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Type, Set, Union
from datetime import datetime
import uuid

from pydantic import Field

from uno.domain.core import DomainEvent, Entity
from uno.domain.event_dispatcher import EventDispatcher, domain_event_handler, EventSubscriber
from uno.sql.emitters.vector import VectorSQLEmitter, VectorConfig


class VectorContentEvent(DomainEvent):
    """
    Base event for vector content changes.
    
    This event is triggered when content that should be vectorized
    is created, updated, or deleted.
    """
    
    entity_id: str
    entity_type: str
    content_fields: Dict[str, str] = {}
    operation: str = "update"  # "create", "update", or "delete"
    
    @classmethod
    def from_entity(cls, entity: Entity, content_fields: List[str], operation: str = "update") -> "VectorContentEvent":
        """
        Create a vector content event from an entity.
        
        Args:
            entity: The entity that changed
            content_fields: List of field names containing content to vectorize
            operation: The operation that occurred (create, update, delete)
            
        Returns:
            A vector content event
        """
        # Extract content fields from entity
        content_data = {}
        entity_dict = entity.model_dump()
        
        for field in content_fields:
            if field in entity_dict and entity_dict[field]:
                content_data[field] = str(entity_dict[field])
        
        # Create the event
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=f"{entity.__class__.__name__}.vector_{operation}",
            entity_id=entity.id,
            entity_type=entity.__class__.__name__,
            content_fields=content_data,
            operation=operation,
            timestamp=datetime.utcnow()
        )


class EntityCreatedEvent(DomainEvent):
    """Event for entity creation."""
    
    entity_id: str
    entity_type: str
    entity_data: Dict[str, Any]
    

class EntityUpdatedEvent(DomainEvent):
    """Event for entity updates."""
    
    entity_id: str
    entity_type: str
    entity_data: Dict[str, Any]
    changed_fields: List[str] = Field(default_factory=list)


class EntityDeletedEvent(DomainEvent):
    """Event for entity deletion."""
    
    entity_id: str
    entity_type: str


class VectorEmbeddingUpdateRequested(DomainEvent):
    """
    Event requesting an embedding update.
    
    This event is published when an embedding needs to be 
    updated based on content changes.
    """
    
    entity_id: str
    entity_type: str
    content: str
    priority: int = 0  # Higher numbers = higher priority
    


class VectorEmbeddingUpdated(DomainEvent):
    """
    Event indicating an embedding was updated.
    
    This event is published after an embedding has been 
    successfully updated.
    """
    
    entity_id: str
    entity_type: str
    embedding_dimensions: int
    success: bool = True
    error_message: Optional[str] = None


class VectorEventHandler(EventSubscriber):
    """
    Handles events related to vector content changes.
    
    This subscriber listens for entity changes and triggers
    vector update events when necessary.
    """
    
    def __init__(
        self, 
        dispatcher: EventDispatcher,
        vectorizable_types: Dict[str, List[str]],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the vector event handler.
        
        Args:
            dispatcher: The event dispatcher
            vectorizable_types: Dict mapping entity types to content field lists
            logger: Optional logger for diagnostic output
        """
        super().__init__(dispatcher)
        self.vectorizable_types = vectorizable_types
        self.logger = logger or logging.getLogger(__name__)
    
    @domain_event_handler("*")
    async def handle_entity_events(self, event: DomainEvent) -> None:
        """
        Handle entity-related events.
        
        This handler detects entity changes and triggers vector
        updates when relevant fields change.
        
        Args:
            event: The domain event
        """
        # Handle creation events
        if isinstance(event, EntityCreatedEvent):
            await self._handle_entity_created(event)
            
        # Handle update events
        elif isinstance(event, EntityUpdatedEvent):
            await self._handle_entity_updated(event)
            
        # Handle deletion events
        elif isinstance(event, EntityDeletedEvent):
            await self._handle_entity_deleted(event)
    
    async def _handle_entity_created(self, event: EntityCreatedEvent) -> None:
        """Handle entity creation events."""
        # Check if this entity type should be vectorized
        if event.entity_type not in self.vectorizable_types:
            return
            
        # Get the fields to vectorize
        content_fields = self.vectorizable_types[event.entity_type]
        
        # Extract content from the entity data
        content_data = {}
        for field in content_fields:
            if field in event.entity_data and event.entity_data[field]:
                content_data[field] = str(event.entity_data[field])
        
        # If we have content, publish a vector content event
        if content_data:
            vector_event = VectorContentEvent(
                event_id=str(uuid.uuid4()),
                event_type=f"{event.entity_type}.vector_create",
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                content_fields=content_data,
                operation="create",
                timestamp=datetime.utcnow()
            )
            
            await self.dispatcher.publish(vector_event)
    
    async def _handle_entity_updated(self, event: EntityUpdatedEvent) -> None:
        """Handle entity update events."""
        # Check if this entity type should be vectorized
        if event.entity_type not in self.vectorizable_types:
            return
            
        # Get the fields to vectorize
        content_fields = self.vectorizable_types[event.entity_type]
        
        # Check if any vectorizable fields have changed
        changed_vectorizable_fields = [
            field for field in event.changed_fields 
            if field in content_fields
        ]
        
        # If no vectorizable fields changed, we can skip
        if not changed_vectorizable_fields:
            return
            
        # Extract content from the entity data
        content_data = {}
        for field in content_fields:
            if field in event.entity_data and event.entity_data[field]:
                content_data[field] = str(event.entity_data[field])
        
        # If we have content, publish a vector content event
        if content_data:
            vector_event = VectorContentEvent(
                event_id=str(uuid.uuid4()),
                event_type=f"{event.entity_type}.vector_update",
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                content_fields=content_data,
                operation="update",
                timestamp=datetime.utcnow()
            )
            
            await self.dispatcher.publish(vector_event)
    
    async def _handle_entity_deleted(self, event: EntityDeletedEvent) -> None:
        """Handle entity deletion events."""
        # Check if this entity type should be vectorized
        if event.entity_type not in self.vectorizable_types:
            return
            
        # Publish a vector content event for deletion
        vector_event = VectorContentEvent(
            event_id=str(uuid.uuid4()),
            event_type=f"{event.entity_type}.vector_delete",
            entity_id=event.entity_id,
            entity_type=event.entity_type,
            content_fields={},
            operation="delete",
            timestamp=datetime.utcnow()
        )
        
        await self.dispatcher.publish(vector_event)


class VectorUpdateHandler(EventSubscriber):
    """
    Handles vector content events and updates embeddings.
    
    This subscriber listens for vector content events and
    triggers the appropriate database operations to update
    embeddings.
    """
    
    def __init__(
        self,
        dispatcher: EventDispatcher,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the vector update handler.
        
        Args:
            dispatcher: The event dispatcher
            logger: Optional logger for diagnostic output
        """
        super().__init__(dispatcher)
        self.logger = logger or logging.getLogger(__name__)
    
    @domain_event_handler()
    async def handle_vector_content_event(self, event: VectorContentEvent) -> None:
        """
        Handle vector content events.
        
        This method processes content changes and updates
        the corresponding vector embeddings.
        
        Args:
            event: The vector content event
        """
        try:
            # Log the event
            self.logger.info(
                f"Processing {event.operation} vector event for {event.entity_type} {event.entity_id}"
            )
            
            # Handle based on operation type
            if event.operation == "delete":
                # For deletes, we'll set the embedding to NULL
                await self._update_embedding(
                    event.entity_type,
                    event.entity_id,
                    None
                )
                return
            
            # For creates and updates, we need to process the content
            if not event.content_fields:
                self.logger.warning(
                    f"No content fields in vector event for {event.entity_type} {event.entity_id}"
                )
                return
            
            # Combine content fields into a single text
            combined_content = " ".join(event.content_fields.values())
            
            # Request an embedding update
            embedding_event = VectorEmbeddingUpdateRequested(
                event_id=str(uuid.uuid4()),
                event_type="vector.embedding_update_requested",
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                content=combined_content,
                timestamp=datetime.utcnow()
            )
            
            await self.dispatcher.publish(embedding_event)
            
        except Exception as e:
            self.logger.error(f"Error processing vector content event: {e}")
    
    @domain_event_handler()
    async def handle_embedding_update_requested(self, event: VectorEmbeddingUpdateRequested) -> None:
        """
        Handle embedding update requests.
        
        This method processes embedding update requests by calling the
        database's embedding generation function.
        
        Args:
            event: The embedding update request event
        """
        try:
            # Log the request
            self.logger.info(
                f"Updating embedding for {event.entity_type} {event.entity_id}"
            )
            
            # Call the database function to update the embedding
            # This leverages the database triggers we've set up
            success = await self._update_embedding(
                event.entity_type,
                event.entity_id,
                event.content
            )
            
            # Publish a completion event
            completion_event = VectorEmbeddingUpdated(
                event_id=str(uuid.uuid4()),
                event_type="vector.embedding_updated",
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                embedding_dimensions=1536,  # This should be configurable
                success=success,
                timestamp=datetime.utcnow()
            )
            
            await self.dispatcher.publish(completion_event)
            
        except Exception as e:
            self.logger.error(f"Error updating embedding: {e}")
            
            # Publish a failure event
            failure_event = VectorEmbeddingUpdated(
                event_id=str(uuid.uuid4()),
                event_type="vector.embedding_updated",
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                embedding_dimensions=0,
                success=False,
                error_message=str(e),
                timestamp=datetime.utcnow()
            )
            
            await self.dispatcher.publish(failure_event)
    
    async def _update_embedding(
        self,
        entity_type: str,
        entity_id: str,
        content: Optional[str]
    ) -> bool:
        """
        Update an entity's embedding.
        
        Args:
            entity_type: The type of entity
            entity_id: The entity ID
            content: The content to embed, or None to clear the embedding
            
        Returns:
            Success flag
        """
        from sqlalchemy import text
        from uno.database.session import async_session
        from uno.settings import uno_settings
        
        table_name = entity_type.lower()
        
        try:
            async with async_session() as session:
                if content is None:
                    # Clear the embedding
                    await session.execute(
                        text(f"""
                        UPDATE {uno_settings.DB_SCHEMA}.{table_name} 
                        SET embedding = NULL
                        WHERE id = :id
                        """),
                        {"id": entity_id}
                    )
                else:
                    # Call the database function to directly generate embedding
                    # This is more efficient than updating the text fields and relying on triggers
                    # since we already have the combined content
                    await session.execute(
                        text(f"""
                        UPDATE {uno_settings.DB_SCHEMA}.{table_name} 
                        SET embedding = {uno_settings.DB_SCHEMA}.generate_embedding(:content)
                        WHERE id = :id
                        """),
                        {"id": entity_id, "content": content}
                    )
                
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Database error updating embedding: {e}")
            return False


class VectorEntityTriggers:
    """
    Helper for configuring entity change events for vectorization.
    
    This class helps with setting up entity change events to trigger
    vector updates automatically.
    """
    
    @staticmethod
    def setup_entity_triggers(
        entity_class: Type[Entity], 
        content_fields: List[str],
        dispatcher: EventDispatcher
    ) -> None:
        """
        Set up event triggers for an entity class.
        
        This method monkey-patches the entity class to publish
        events when instances are created, updated, or deleted.
        
        Args:
            entity_class: The entity class to set up triggers for
            content_fields: The fields containing content to vectorize
            dispatcher: The event dispatcher to publish events to
        """
        # Store the original model_post_init method
        original_post_init = entity_class.model_post_init
        
        # Override model_post_init to detect creation
        def patched_post_init(self, __context):
            # Call the original method
            original_post_init(self, __context)
            
            # Check if this is a new entity (created_at == updated_at)
            if self.created_at and (self.updated_at is None or self.created_at == self.updated_at):
                # Publish a creation event
                event = EntityCreatedEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=f"{self.__class__.__name__}.created",
                    entity_id=self.id,
                    entity_type=self.__class__.__name__,
                    entity_data=self.model_dump(),
                    timestamp=datetime.utcnow()
                )
                
                # Use asyncio to dispatch the event
                import asyncio
                
                async def dispatch():
                    await dispatcher.publish(event)
                
                asyncio.create_task(dispatch())
        
        # Replace the method
        entity_class.model_post_init = patched_post_init
        
        # Store the original model_post_update method if it exists
        original_post_update = getattr(entity_class, "model_post_update", None)
        
        # Create a new model_post_update method
        def patched_post_update(self, __context):
            # Call the original method if it exists
            if original_post_update:
                original_post_update(self, __context)
            
            # Determine which fields have changed
            changed_fields = getattr(__context, "changed_fields", [])
            
            # Publish an update event
            event = EntityUpdatedEvent(
                event_id=str(uuid.uuid4()),
                event_type=f"{self.__class__.__name__}.updated",
                entity_id=self.id,
                entity_type=self.__class__.__name__,
                entity_data=self.model_dump(),
                changed_fields=changed_fields,
                timestamp=datetime.utcnow()
            )
            
            # Use asyncio to dispatch the event
            import asyncio
            
            async def dispatch():
                await dispatcher.publish(event)
            
            asyncio.create_task(dispatch())
        
        # Add the method
        entity_class.model_post_update = patched_post_update