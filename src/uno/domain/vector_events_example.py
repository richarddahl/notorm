"""
Example usage of event-driven vector search in Uno.

This module demonstrates how to set up and use the event-driven vector search
system for automatic embedding updates and synchronization.
"""

import asyncio
import logging
from typing import List, Dict, Any

from pydantic import Field

from uno.domain.core import Entity, DomainEvent
from uno.domain.event_dispatcher import EventDispatcher, domain_event_handler, EventSubscriber
from uno.domain.vector_events import (
    VectorEntityTriggers,
    VectorEventHandler,
    VectorUpdateHandler,
    VectorEmbeddingUpdated
)
from uno.domain.vector_update_service import VectorUpdateService, BatchVectorUpdateService


# Example entity class
class Document(Entity):
    """Example document entity class."""
    
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    author: str = ""


# Example custom event handler
class DocumentVectorHandler(EventSubscriber):
    """
    Example of a custom event handler for document vector events.
    
    This class demonstrates how to respond to vector embedding updates
    with custom logic.
    """
    
    @domain_event_handler()
    async def handle_embedding_updated(self, event: VectorEmbeddingUpdated) -> None:
        """Handle embedding update events."""
        if event.entity_type == "Document" and event.success:
            print(f"✅ Document {event.entity_id} embedding updated successfully")
            
            # In a real application, you might want to:
            # - Update a search index
            # - Generate notifications
            # - Trigger content recommendations
            # - Log analytics data
            # - etc.
        elif not event.success:
            print(f"❌ Error updating embedding for {event.entity_type} {event.entity_id}: {event.error_message}")


async def setup_event_driven_system():
    """
    Set up the event-driven vector search system.
    
    This function demonstrates how to configure and start
    all components of the event-driven vector system.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("vector_events_example")
    
    # Create event dispatcher
    dispatcher = EventDispatcher(logger=logger)
    
    # Configure entity triggers
    VectorEntityTriggers.setup_entity_triggers(
        entity_class=Document,
        content_fields=["title", "content"],
        dispatcher=dispatcher
    )
    
    # Define which entity types and fields should be vectorized
    vectorizable_types = {
        "Document": ["title", "content"],
    }
    
    # Create event handlers
    vector_event_handler = VectorEventHandler(
        dispatcher=dispatcher,
        vectorizable_types=vectorizable_types,
        logger=logger
    )
    
    vector_update_handler = VectorUpdateHandler(
        dispatcher=dispatcher,
        logger=logger
    )
    
    # Create custom handler
    document_handler = DocumentVectorHandler(dispatcher=dispatcher)
    
    # Create update service
    update_service = VectorUpdateService(
        dispatcher=dispatcher,
        batch_size=10,
        update_interval=1.0,
        logger=logger
    )
    
    # Start the update service
    await update_service.start()
    
    # Create batch service for bulk operations
    batch_service = BatchVectorUpdateService(
        dispatcher=dispatcher,
        batch_size=100,
        logger=logger
    )
    
    return {
        "dispatcher": dispatcher,
        "update_service": update_service,
        "batch_service": batch_service
    }


async def demonstrate_event_driven_updates():
    """
    Demonstrate event-driven vector updates.
    
    This function shows the system in action with example operations.
    """
    print("Setting up event-driven vector search system...")
    services = await setup_event_driven_system()
    
    update_service = services["update_service"]
    batch_service = services["batch_service"]
    
    try:
        # Create a new document - this will trigger automatic embedding
        print("\nCreating a new document...")
        doc = Document(
            id="doc1",
            title="Introduction to Vector Search",
            content="""
            Vector search uses embeddings to find semantically similar content.
            This is more powerful than traditional keyword search because it can
            understand meaning, not just exact word matches.
            """
        )
        
        # Wait a moment for events to process
        await asyncio.sleep(2)
        
        # Update the document - this will trigger an embedding update
        print("\nUpdating the document...")
        doc.content += """
        Vector search is particularly useful for RAG (Retrieval-Augmented Generation)
        where it can find relevant context for LLM prompts.
        """
        
        # Wait a moment for events to process
        await asyncio.sleep(2)
        
        # Manually queue an update with high priority
        print("\nManually queuing a high-priority update...")
        await update_service.queue_update(
            entity_id="doc1",
            entity_type="Document",
            content="This is a high priority update to the document content.",
            priority=10  # Higher priority
        )
        
        # Wait a moment for events to process
        await asyncio.sleep(2)
        
        # Show update service statistics
        print("\nUpdate service statistics:")
        stats = update_service.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Demonstrate batch update
        print("\nPerforming batch update...")
        batch_stats = await batch_service.update_entities_by_ids(
            entity_type="Document",
            entity_ids=["doc1", "doc2", "doc3"],
            content_fields=["title", "content"]
        )
        
        print("\nBatch update statistics:")
        for key, value in batch_stats.items():
            print(f"  {key}: {value}")
        
    finally:
        # Clean up
        print("\nStopping services...")
        await update_service.stop()
        print("Event-driven vector search demonstration completed")


# Run the demonstration
if __name__ == "__main__":
    # Run the async demonstration
    asyncio.run(demonstrate_event_driven_updates())