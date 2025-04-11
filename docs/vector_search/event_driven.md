# Event-Driven Vector Updates

This guide explains how to use the event-driven architecture for vector search, enabling real-time embedding updates and efficient synchronization.

## Overview

The event-driven vector search system allows:

1. **Real-time updates** - Embeddings update automatically when content changes
2. **Efficient synchronization** - Only changed entities are re-embedded
3. **Batch processing** - Efficient handling of bulk updates
4. **Priority queuing** - Critical updates can be prioritized

This approach keeps your vector embeddings in sync with your data while minimizing database load.

## Architecture

The event-driven system consists of:

1. **Events** - Domain events for content changes and vector operations
2. **Event Handlers** - Process content changes and trigger embedding updates
3. **Update Services** - Manage the update process with queuing and batching

Events flow through the system as follows:

```
EntityCreated/Updated/Deleted → VectorContentEvent → VectorEmbeddingUpdateRequested → Database Update → VectorEmbeddingUpdated
```

## Setting Up Event-Driven Vector Search

### 1. Configure Entity Triggers

First, set up event triggers for your entity classes:

```python
from uno.domain.vector_events import VectorEntityTriggers
from uno.domain.event_dispatcher import EventDispatcher

# Create an event dispatcher
dispatcher = EventDispatcher()

# Configure entity triggers
VectorEntityTriggers.setup_entity_triggers(
    entity_class=Document,
    content_fields=["title", "content", "summary"],
    dispatcher=dispatcher
)
```

### 2. Set Up Event Handlers

Register the vector event handlers:

```python
from uno.domain.vector_events import VectorEventHandler, VectorUpdateHandler

# Define which entity types and fields should be vectorized
vectorizable_types = {
    "Document": ["title", "content", "summary"],
    "Product": ["name", "description"]
}

# Create handlers
vector_event_handler = VectorEventHandler(
    dispatcher=dispatcher,
    vectorizable_types=vectorizable_types
)

vector_update_handler = VectorUpdateHandler(
    dispatcher=dispatcher
)
```

### 3. Start the Update Service

Set up and start the vector update service:

```python
from uno.domain.vector_update_service import VectorUpdateService

# Create update service
update_service = VectorUpdateService(
    dispatcher=dispatcher,
    batch_size=10,
    update_interval=1.0
)

# Start the service
await update_service.start()
```

## Handling Content Updates

Once configured, the system will automatically:

1. Detect when entity content changes
2. Generate events for these changes
3. Queue embedding updates
4. Process updates efficiently in batches
5. Update the database with new embeddings

## Manual Updates

You can also manually trigger updates:

```python
# Queue a single update
await update_service.queue_update(
    entity_id="doc123",
    entity_type="Document",
    content="This is the document content to embed",
    priority=5  # Higher priority
)
```

## Batch Updates

For large data sets or initial loading, use batch updates:

```python
from uno.domain.vector_update_service import BatchVectorUpdateService

# Create batch service
batch_service = BatchVectorUpdateService(
    dispatcher=dispatcher,
    batch_size=100
)

# Update all documents
stats = await batch_service.update_all_entities(
    entity_type="Document",
    content_fields=["title", "content"]
)

print(f"Processed {stats['processed']} entities with {stats['succeeded']} successes")

# Or update specific entities
stats = await batch_service.update_entities_by_ids(
    entity_type="Document",
    entity_ids=["doc1", "doc2", "doc3"],
    content_fields=["title", "content"]
)
```

## Monitoring Update Performance

You can monitor the update service performance:

```python
# Get update service statistics
stats = update_service.get_stats()

print(f"Queue size: {stats['queue_size']}")
print(f"Processed: {stats['processed']}")
print(f"Success rate: {stats['processed'] - stats['failed']}/{stats['processed']}")
```

## Event Handlers

You can create custom event handlers to perform additional actions when embeddings change:

```python
from uno.domain.event_dispatcher import EventSubscriber, domain_event_handler
from uno.domain.vector_events import VectorEmbeddingUpdated

class MyVectorHandler(EventSubscriber):
    @domain_event_handler()
    async def handle_embedding_updated(self, event: VectorEmbeddingUpdated) -> None:
        if event.success:
            print(f"Successfully updated embedding for {event.entity_type} {event.entity_id}")
            # Perform additional actions like updating a search index
```

## Database Integration

The event-driven system works with the PostgreSQL triggers by:

1. Using the `generate_embedding` function in the database
2. Directly updating the embedding column with the result
3. Leveraging database triggers for data consistency

This ensures that embeddings remain consistent with entity data, even if updates come from multiple sources.