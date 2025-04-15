# Read Model Projection System

The Read Model Projection system is a key component of the CQRS (Command Query Responsibility Segregation) pattern in uno. It allows for efficient querying by creating and maintaining specialized read models that are optimized for specific query use cases.

## Overview

In a CQRS architecture, we separate the command side (which handles data modifications) from the query side (which handles data retrieval). The Read Model Projection system focuses on the query side, providing a structured way to maintain read models that are derived from domain events.

The system consists of several key components:

1. **Read Models** - Data structures optimized for specific query scenarios
2. **Projections** - Components that transform domain events into read models
3. **Projector** - Manages projections and ensures events are routed correctly
4. **Query Services** - Provide a clean API for querying read models
5. **Cache Services** - Improve performance through caching mechanisms

## Key Components

### Read Models

Read models are specialized data structures optimized for specific query scenarios. Unlike domain models that capture business rules and state transitions, read models are designed for fast and efficient data retrieval.

```python
class UserReadModel(ReadModel):
    """Read model for user queries."""
    
    user_id: str
    username: str
    email: str
    is_active: bool = True
    last_updated: datetime
```

### Projections

Projections transform domain events into read models. Each projection defines how a specific type of event affects a particular read model.

```python
class UserCreatedProjection(Projection[UserReadModel, UserCreatedEvent]):
    """Projection that creates a user read model when a user is created."""
    
    async def apply(self, event: UserCreatedEvent) -> Optional[UserReadModel]:
        """Apply a UserCreatedEvent to create a user read model."""
        return UserReadModel(
            id=event.user_id,
            user_id=event.user_id,
            username=event.username,
            email=event.email,
            is_active=True,
            last_updated=event.timestamp
        )
```

### Projector

The projector manages a set of projections and ensures that domain events are routed to the appropriate projections.

```python
# Create the projector
projector = Projector(event_bus, event_store)

# Register projections
projector.register_projection(user_created_projection)
projector.register_projection(user_updated_projection)
projector.register_projection(user_deleted_projection)
```

### Query Services

Query services provide a clean API for querying read models. They handle the details of data retrieval and can incorporate optimizations like caching.

```python
# Create the query service
query_service = ReadModelQueryService(repository, UserReadModel, cache)

# Query the read model
user = await query_service.get_by_id(user_id)
active_users = await query_service.find({"is_active": True})
```

### Cache Services

Cache services improve performance by caching frequently accessed read models. The framework provides both in-memory and Redis-based implementations.

```python
# Create a cache
cache = InMemoryReadModelCache(UserReadModel)

# Use it with a query service
query_service = ReadModelQueryService(repository, UserReadModel, cache)
```

## Architecture Diagrams

```
┌───────────────┐     ┌──────────────┐     ┌───────────────┐
│ Domain Events │────▶│  Projections │────▶│  Read Models  │
└───────────────┘     └──────────────┘     └───────────────┘
                                                   │
                                                   ▼
                                           ┌───────────────┐
                                           │ Query Services│
                                           └───────────────┘
                                                   │
                                                   ▼
                                           ┌───────────────┐
                                           │   API Layer   │
                                           └───────────────┘
```

## Integration with Existing Systems

The Read Model Projection system integrates seamlessly with the existing uno framework:

1. It subscribes to domain events from the event bus
2. It can use the event store for event sourcing and rebuilding read models
3. It complements the existing CQRS components by handling the query side
4. It can be used alongside or as a replacement for traditional ORM-based queries

## Best Practices

1. **Design read models for specific query scenarios**: Instead of creating generic read models, design them specifically for the queries they need to support.

2. **Keep projections simple**: Projections should focus on data transformation, not business logic.

3. **Consider performance implications**: For high-volume events, use the `AsyncProjector` to process events asynchronously.

4. **Use caching appropriately**: Caching can greatly improve performance, but be mindful of cache invalidation challenges.

5. **Implement rebuilding capabilities**: Ensure you can rebuild read models from scratch by replaying events.

6. **Test thoroughly**: Write comprehensive tests for your projections and query services.

## Example Usage

Here's a complete example showing how to set up and use the Read Model Projection system:

```python
# Define a read model
class UserReadModel(ReadModel):
    user_id: str
    username: str
    email: str
    is_active: bool = True

# Define a projection
class UserCreatedProjection(Projection[UserReadModel, UserCreatedEvent]):
    async def apply(self, event: UserCreatedEvent) -> Optional[UserReadModel]:
        return UserReadModel(
            id=event.user_id,
            user_id=event.user_id,
            username=event.username,
            email=event.email
        )

# Set up the infrastructure
repository = InMemoryReadModelRepository(UserReadModel)
cache = InMemoryReadModelCache(UserReadModel)
projector = Projector(event_bus, event_store)
query_service = ReadModelQueryService(repository, UserReadModel, cache)

# Register the projection
projector.register_projection(UserCreatedProjection(
    UserReadModel, UserCreatedEvent, repository
))

# Query data
user = await query_service.get_by_id(user_id)
active_users = await query_service.find({"is_active": True})
```

## Advanced Usage

### Asynchronous Processing

For high-volume event processing, use the `AsyncProjector`:

```python
async_projector = AsyncProjector(event_bus, event_store)
await async_projector.start()
```

### Custom Repositories

Implement custom repositories for specific storage needs:

```python
class PostgresReadModelRepository(ReadModelRepository[T]):
    # Implementation for PostgreSQL
```

### Batch Projections

For more efficient processing of related events:

```python
class BatchUserProjection(BatchProjection[UserReadModel, UserEvent]):
    async def apply_batch(self, events: List[UserEvent]) -> List[Optional[UserReadModel]]:
        # Process multiple events at once
```

## Conclusion

The Read Model Projection system provides a powerful way to implement the query side of CQRS in uno. By creating specialized read models that are optimized for specific query scenarios, you can achieve better performance and scalability while maintaining a clean separation of concerns.