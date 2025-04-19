# PostgreSQL Event Store

The PostgreSQL Event Store is a robust, production-ready implementation of the `EventStore` interface for persisting and retrieving domain events using PostgreSQL. This implementation is suitable for event sourcing and event-driven architectures in production environments.

## Features

- Persistent storage of domain events in PostgreSQL
- Support for optimistic concurrency control
- Auto-creation of database schema and tables
- Event notifications via PostgreSQL LISTEN/NOTIFY
- Efficient batch operations
- Transaction support
- Comprehensive querying capabilities
- Proper error handling and logging

## Configuration

The PostgreSQL Event Store is configured using the `PostgresEventStoreConfig` class:

```python
from uno.core.events import PostgresEventStoreConfig, PostgresEventStore

config = PostgresEventStoreConfig(
    # Connection settings
    connection_string="postgresql+asyncpg://username:password@localhost:5432/mydatabase",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # 30 minutes
    
    # Schema settings
    schema="public",
    table_name="domain_events",
    
    # Feature flags
    use_notifications=True,
    create_schema_if_missing=True,
    
    # Performance settings
    batch_size=100,
    use_connection_pool=True
)

event_store = PostgresEventStore(config=config)
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `connection_string` | SQLAlchemy connection string for PostgreSQL | Required |
| `pool_size` | Number of connections to keep in the pool | 10 |
| `max_overflow` | Maximum number of connections to allow in the pool | 20 |
| `pool_timeout` | Timeout in seconds for getting a connection from the pool | 30 |
| `pool_recycle` | Number of seconds after which a connection is recycled | 1800 |
| `schema` | Database schema to use | "public" |
| `table_name` | Name of the events table | "events" |
| `use_notifications` | Whether to set up PostgreSQL NOTIFY/LISTEN | True |
| `create_schema_if_missing` | Whether to create the schema and tables if missing | True |
| `batch_size` | Number of events to process in a batch | 100 |
| `use_connection_pool` | Whether to use SQLAlchemy connection pooling | True |

## Usage

### Basic Usage

```python
from uno.core.events import PostgresEventStoreConfig, PostgresEventStore, Event

# Configure the event store
config = PostgresEventStoreConfig(
    connection_string="postgresql+asyncpg://username:password@localhost:5432/mydatabase"
)

# Create the event store
event_store = PostgresEventStore(config=config)

# Initialize the store (creates schema and tables if needed)
await event_store.initialize()

# Store events
events = [
    UserCreated(user_id="123", name="John Doe", email="john@example.com"),
    EmailVerified(user_id="123", verified_at=datetime.now())
]
await event_store.append_events(events)

# Retrieve events for an aggregate
user_events = await event_store.get_events_by_aggregate("123")

# Retrieve events by type
created_events = await event_store.get_events_by_type("user_created")
```

### Event Sourcing

The PostgreSQL Event Store is ideal for event sourcing patterns where aggregates are reconstructed from their event history:

```python
# Store an event with aggregate information
event = UserCreated(
    user_id="123",
    name="John Doe",
    email="john@example.com",
    aggregate_id="123",
    aggregate_type="User"
)
await event_store.append_events([event])

# Add another event with optimistic concurrency
update_event = UserEmailChanged(
    user_id="123",
    old_email="john@example.com",
    new_email="john.doe@example.com",
    aggregate_id="123",
    aggregate_type="User"
)
await event_store.append_events([update_event], expected_version=1)

# Retrieve events and reconstruct the aggregate
events = await event_store.get_events_by_aggregate("123")
user = User.from_events(events)
```

## Database Schema

The PostgreSQL Event Store creates a table with the following schema:

```sql
CREATE TABLE {schema}.{table_name} (
    event_id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    correlation_id VARCHAR(36),
    causation_id VARCHAR(36),
    aggregate_id VARCHAR(36),
    aggregate_type VARCHAR(255),
    aggregate_version INTEGER,
    data JSONB NOT NULL,
    metadata JSONB
);

-- Indices for efficient querying
CREATE INDEX idx_{table_name}_event_type ON {schema}.{table_name}(event_type);
CREATE INDEX idx_{table_name}_occurred_at ON {schema}.{table_name}(occurred_at);
CREATE INDEX idx_{table_name}_aggregate_id ON {schema}.{table_name}(aggregate_id);
CREATE INDEX idx_{table_name}_aggregate_type ON {schema}.{table_name}(aggregate_type);
CREATE INDEX idx_{table_name}_correlation_id ON {schema}.{table_name}(correlation_id);
```

## Migration from InMemoryEventStore

To migrate events from the `InMemoryEventStore` to the `PostgresEventStore`, you can use the provided migration script:

```bash
python src/scripts/eventstore_migration.py --source memory --target postgres --connection "postgresql+asyncpg://username:password@localhost:5432/mydatabase"
```

Or programmatically:

```python
from uno.core.events import InMemoryEventStore, PostgresEventStore, PostgresEventStoreConfig

# Source in-memory store
source_store = InMemoryEventStore()

# Target PostgreSQL store
config = PostgresEventStoreConfig(
    connection_string="postgresql+asyncpg://username:password@localhost:5432/mydatabase"
)
target_store = PostgresEventStore(config=config)
await target_store.initialize()

# Get all events from source
events = source_store._events

# Group events by aggregate
events_by_aggregate = {}
for event in events:
    if event.aggregate_id:
        if event.aggregate_id not in events_by_aggregate:
            events_by_aggregate[event.aggregate_id] = []
        events_by_aggregate[event.aggregate_id].append(event)

# Migrate events aggregate by aggregate
for aggregate_id, aggregate_events in events_by_aggregate.items():
    # Sort events by version
    aggregate_events.sort(key=lambda e: e.aggregate_version or 0)
    
    # Store events in target
    await target_store.append_events(aggregate_events)
```

## Performance Considerations

- The PostgreSQL Event Store is designed to be efficient for both reading and writing events
- For write-heavy applications, consider using a connection pool with appropriate settings
- For read-heavy applications, ensure proper indices are in place
- Consider using batch operations for storing large numbers of events
- For very large event stores, consider implementing archiving strategies

## Error Handling

The PostgreSQL Event Store includes proper error handling for:

- Connection failures
- Transaction conflicts
- Concurrency violations
- Schema creation failures
- Event serialization/deserialization issues

All errors are properly logged with context information for debugging.