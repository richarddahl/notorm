# Offline Store

The Offline Store is a robust client-side data storage solution that enables applications to function effectively without network connectivity. It provides a consistent API for data access regardless of online status.

## Overview

The Offline Store provides:

1. **Consistent Data Access**: A unified API for data operations regardless of connectivity
2. **Persistence**: Reliable storage of application data on the client
3. **Querying**: Rich query capabilities similar to server-side operations
4. **Relational Data**: Support for relationships between data entities
5. **Security**: Encryption and access control for sensitive data
6. **Storage Management**: Size limits, eviction strategies, and storage optimization

## Architecture

The Offline Store is built as a layered system:

```
┌───────────────────────────────────────────────────────────┐
│                   Offline Store API                        │
└───────────┬───────────────────────────────┬───────────────┘
            │                               │
┌───────────▼───────────┐       ┌───────────▼───────────┐
│   Data Access Layer    │       │  Storage Engine Layer │
└───────────┬───────────┘       └───────────┬───────────┘
            │                               │
┌───────────▼───────────┐       ┌───────────▼───────────┐
│   Change Tracking      │       │   Storage Adapters    │
└───────────┬───────────┘       └───────────┬───────────┘
            │                               │
            └───────────────┬───────────────┘
                            │
                  ┌─────────▼─────────┐
                  │ Encryption Layer  │
                  └─────────┬─────────┘
                            │
               ┌────────────▼────────────┐
               │     Storage Backends    │
               └─────────────────────────┘
```

### Components

1. **Offline Store API**: Provides a unified interface for all data operations
2. **Data Access Layer**: Implements CRUD operations and query processing
3. **Change Tracking**: Records changes for later synchronization
4. **Storage Engine**: Manages the low-level storage operations
5. **Storage Adapters**: Adapts storage for different types of data
6. **Encryption Layer**: Provides optional encryption for sensitive data
7. **Storage Backends**: Pluggable storage mechanisms (IndexedDB, WebSQL, LocalStorage, etc.)

## Usage

### Setup and Configuration

```python
from uno.offline import OfflineStore, StorageOptions, EncryptionOptions

# Configure the offline store
options = StorageOptions(
    storage_backend="indexeddb",  # Or "websql", "localstorage", etc.
    database_name="my_app_db",
    version=1,
    size_limit=100_000_000,  # 100MB
    eviction_strategy="lru",  # Least Recently Used
    encryption=EncryptionOptions(
        enabled=True,
        sensitive_fields=["password", "credit_card", "ssn"],
        encryption_key_provider="user_passphrase"
    ),
    storage_schema=[
        {
            "name": "users",
            "key_path": "id",
            "indexes": [
                {"name": "email", "key_path": "email", "unique": True},
                {"name": "name", "key_path": "name"}
            ]
        },
        {
            "name": "orders",
            "key_path": "id",
            "indexes": [
                {"name": "user_id", "key_path": "user_id"},
                {"name": "date", "key_path": "date"}
            ]
        }
    ]
)

# Create the offline store
store = OfflineStore(options)

# Initialize the store (creates database, tables, and indexes)
await store.initialize()
```

### Basic CRUD Operations

```python
# Create a record
user = {
    "id": "user123",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "customer"
}
await store.create("users", user)

# Read a record
user = await store.get("users", "user123")

# Update a record
user["role"] = "admin"
await store.update("users", user)

# Delete a record
await store.delete("users", "user123")
```

### Querying

```python
# Simple query with filtering
users = await store.query("users", {
    "filters": {
        "role": "admin"
    }
})

# More complex query with operators
users = await store.query("users", {
    "filters": {
        "role": "admin",
        "created_at": {"$gt": "2023-01-01"}
    },
    "sort": [{"field": "name", "direction": "asc"}],
    "limit": 10,
    "offset": 0
})

# Query with relationships
orders = await store.query("orders", {
    "filters": {
        "user_id": "user123",
        "status": "pending"
    },
    "include": ["user", "items"],
    "sort": [{"field": "date", "direction": "desc"}]
})
```

### Batch Operations

```python
# Batch create
users = [
    {"id": "user1", "name": "Alice", "email": "alice@example.com"},
    {"id": "user2", "name": "Bob", "email": "bob@example.com"},
    {"id": "user3", "name": "Charlie", "email": "charlie@example.com"}
]
await store.create_batch("users", users)

# Batch update
updates = [
    {"id": "user1", "role": "admin"},
    {"id": "user2", "role": "editor"},
    {"id": "user3", "role": "viewer"}
]
await store.update_batch("users", updates)

# Batch delete
await store.delete_batch("users", ["user1", "user2", "user3"])
```

### Transactions

```python
# Start a transaction
transaction = await store.begin_transaction(["users", "orders"])

try:
    # Perform operations within the transaction
    user = {"id": "user123", "name": "John Doe", "email": "john@example.com"}
    await transaction.create("users", user)
    
    order = {"id": "order456", "user_id": "user123", "total": 99.99}
    await transaction.create("orders", order)
    
    # Commit the transaction
    await transaction.commit()
except Exception as e:
    # Rollback on error
    await transaction.rollback()
    print(f"Transaction failed: {e}")
```

### Change Tracking

```python
# Get changes made since last sync
changes = await store.get_changes()

# Get changes for a specific collection
user_changes = await store.get_changes("users")

# Mark changes as synchronized
await store.mark_synchronized(changes)
```

## Storage Backends

The Offline Store supports multiple storage backends to accommodate different platforms and browser capabilities:

### IndexedDB

Primary storage backend for modern browsers, offering:
- Larger storage capacity
- Structured data storage
- Index support for efficient queries
- Asynchronous API

```python
options = StorageOptions(storage_backend="indexeddb", ...)
```

### WebSQL

Alternative storage for browsers that support it:
- SQL-based storage
- Transaction support
- Good performance for complex queries

```python
options = StorageOptions(storage_backend="websql", ...)
```

### LocalStorage

Fallback storage for older browsers:
- Simple key-value storage
- Limited capacity (usually 5-10MB)
- Synchronous API

```python
options = StorageOptions(storage_backend="localstorage", ...)
```

### Custom Storage

Support for custom storage implementations:

```python
from uno.offline import StorageBackend

class MyCustomStorage(StorageBackend):
    async def initialize(self, options):
        # Initialize storage
        pass
    
    async def create(self, collection, data):
        # Create implementation
        pass
    
    # Implement other required methods

# Use custom storage
options = StorageOptions(storage_backend=MyCustomStorage(), ...)
```

## Advanced Features

### Encryption

The Offline Store provides optional encryption for sensitive data:

```python
encryption_options = EncryptionOptions(
    enabled=True,
    sensitive_fields=["password", "ssn", "credit_card"],
    encryption_key_provider="user_passphrase",
    encryption_algorithm="AES-GCM"
)
```

### Relationships

Define and query relationships between collections:

```python
# Define relationships in schema
schema = [
    {
        "name": "users",
        "key_path": "id",
        "relationships": [
            {
                "name": "orders",
                "collection": "orders",
                "type": "one-to-many",
                "foreign_key": "user_id"
            }
        ]
    },
    {
        "name": "orders",
        "key_path": "id",
        "relationships": [
            {
                "name": "user",
                "collection": "users",
                "type": "many-to-one",
                "foreign_key": "user_id"
            },
            {
                "name": "items",
                "collection": "order_items",
                "type": "one-to-many",
                "foreign_key": "order_id"
            }
        ]
    }
]

# Query with relationships
user_with_orders = await store.get("users", "user123", include=["orders"])
order_with_user_and_items = await store.get("orders", "order456", include=["user", "items"])
```

### Storage Management

Control and monitor storage usage:

```python
# Get storage usage information
usage = await store.get_storage_info()
print(f"Total usage: {usage.used_bytes / 1024 / 1024:.2f} MB")
print(f"Available: {usage.available_bytes / 1024 / 1024:.2f} MB")
print(f"Usage by collection: {usage.collection_usage}")

# Clear specific collections
await store.clear(["temp_data", "cache"])

# Set collection-specific eviction policies
await store.set_eviction_policy("logs", {
    "strategy": "max-age",
    "max_age_days": 7
})

await store.set_eviction_policy("cache", {
    "strategy": "max-size",
    "max_size_bytes": 10_000_000  # 10MB
})

# Compact storage
await store.compact()
```

## Storage Schema Migration

The Offline Store supports schema migrations for evolving data structures:

```python
from uno.offline import Migration, MigrationManager

# Define a migration
class AddUserPreferencesMigration(Migration):
    version = 2
    
    async def up(self, store):
        # Update schema with new preferences field
        users = await store.query("users")
        for user in users:
            if "preferences" not in user:
                user["preferences"] = {"theme": "light", "notifications": True}
                await store.update("users", user)
    
    async def down(self, store):
        # Remove preferences field
        users = await store.query("users")
        for user in users:
            if "preferences" in user:
                del user["preferences"]
                await store.update("users", user)

# Register migrations
migration_manager = MigrationManager([
    AddUserPreferencesMigration()
])

# Configure store with migration manager
options = StorageOptions(
    storage_backend="indexeddb",
    database_name="my_app_db",
    version=2,  # Increment version for migration
    migration_manager=migration_manager
)

# Migrations will run automatically during initialization
store = OfflineStore(options)
await store.initialize()
```

## Integration with Synchronization Engine

The Offline Store is designed to work seamlessly with the Synchronization Engine:

```python
from uno.offline import OfflineStore, SynchronizationEngine, SyncOptions

# Create offline store
store = OfflineStore(store_options)

# Create sync engine with the store
sync_options = SyncOptions(
    server_url="https://api.example.com",
    sync_collections=["users", "orders", "products"],
    sync_interval=300,  # 5 minutes
    conflict_strategy="server-wins"
)
sync_engine = SynchronizationEngine(store, sync_options)

# Start automatic synchronization
await sync_engine.start()

# Or trigger manual sync
await sync_engine.synchronize()
```

## Best Practices

1. **Define a Clear Schema**: Always define a clear schema with indexes for frequently queried fields.

2. **Use Transactions for Related Changes**: When updating related data, use transactions to ensure consistency.

3. **Monitor Storage Usage**: Implement storage monitoring and cleanup to avoid hitting storage limits.

4. **Encrypt Sensitive Data**: Always encrypt sensitive user data stored offline.

5. **Implement Migrations**: Plan for schema evolution with proper migration strategies.

6. **Consider Storage Limitations**: Be aware of storage limitations on different platforms and browsers.

7. **Optimize Data Size**: Minimize the amount of data stored offline by:
   - Storing only necessary fields
   - Using compression for large data
   - Implementing data expiration policies

8. **Use Optimistic UI Updates**: Update UI immediately while storing data to provide better user experience.

9. **Handle Storage Errors**: Implement proper error handling for storage operations:
   - Full storage
   - Quota exceeded
   - Permission denied
   - Storage not available