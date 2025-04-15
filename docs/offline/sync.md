# Synchronization Engine

The Synchronization Engine is responsible for keeping local and remote data in sync, allowing applications to function seamlessly in both online and offline environments.

## Overview

The Synchronization Engine provides bidirectional data synchronization between the local Offline Store and a remote server. It handles:

1. **Detecting Changes**: Identifying changes made locally and remotely
2. **Efficient Transfer**: Minimizing data transferred between client and server
3. **Conflict Detection**: Identifying when the same data is modified in multiple places
4. **Conflict Resolution**: Resolving conflicts between local and remote changes
5. **Error Handling**: Robust error handling for network issues and conflicts
6. **Cancellation**: Support for cancelling ongoing synchronization

## Architecture

The Synchronization Engine is built as a layered system:

```
┌───────────────────────────────────────────────────────────┐
│                 SynchronizationEngine                      │
└───────────┬───────────────────────────────┬───────────────┘```
```

    │                               │
    │                               │
```
```
┌───────────▼───────────┐       ┌───────────▼───────────┐
│   Sync Strategies     │       │   Network Adapters    │
│                       │       │                       │
│ - Two-way             │       │ - RestAdapter        │
│ - Pull-only           │       │ - GraphQLAdapter     │
│ - Push-only           │       │                      │
└───────────┬───────────┘       └───────────┬──────────┘```
```

    │                               │
    │                               │
```
``````

        └───────────────┬───────────────┘
                        │
                        │
              ┌─────────▼─────────┐
              │   ChangeTracker   │
              └─────────┬─────────┘
                        │
                        │
           ┌────────────▼────────────┐
           │   Conflict Resolution   │
           │                         │
           │ - ServerWinsResolver    │
           │ - ClientWinsResolver    │
           │ - TimestampBasedResolver│
           │ - MergeFieldsResolver   │
           │ - Custom resolvers      │
           └─────────────────────────┘
```
```

### Components

1. **Synchronization Engine**: Core component that coordinates the synchronization process
2. **Sync Strategies**: Different approaches to synchronization (two-way, pull-only, push-only)
3. **Network Adapters**: Handles communication with different server types (REST, GraphQL)
4. **Change Tracker**: Tracks changes to local data for efficient synchronization
5. **Conflict Resolution**: Resolves conflicts between local and remote changes using configurable strategies

## Synchronization Process

The synchronization process follows these general steps:

1. **Preparation**: 
   - Identify changed data since last sync
   - Determine sync priority for different collections

2. **Upload Changes**:
   - Send local changes to the server
   - Handle server responses and validation

3. **Download Changes**:
   - Fetch remote changes from the server
   - Apply changes to local database

4. **Conflict Resolution**:
   - Detect conflicts between local and remote changes
   - Apply resolution strategies based on configuration
   - Record resolution decisions for future reference

5. **Finalization**:
   - Update sync metadata (timestamps, markers, etc.)
   - Trigger notifications for completed sync

## Implementation

The Synchronization Engine has been fully implemented with the following core components:

### Core Components

1. **SynchronizationEngine**: The main class responsible for coordinating the synchronization process
2. **NetworkAdapter**: Abstract base class defining the interface for server communication
3. **ChangeTracker**: Tracks changes to local data to efficiently synchronize with the server
4. **ConflictResolver**: Interface for different conflict resolution strategies

### Engine Implementation

The `SynchronizationEngine` class provides methods for:

- Synchronizing data between client and server
- Managing the synchronization process
- Handling errors and conflicts
- Cancelling ongoing synchronization

### Network Adapters

The following network adapters have been implemented:

- **RestAdapter**: Adapter for communicating with REST APIs
  - Supports authentication
  - Handles retries and error handling
  - Implements batch operations for efficiency

### Conflict Resolution

Several conflict resolution strategies have been implemented:

- **ServerWinsResolver**: Always chooses the server's version
- **ClientWinsResolver**: Always chooses the local version
- **TimestampBasedResolver**: Chooses the most recently updated version
- **MergeFieldsResolver**: Selectively merges fields from both versions
- **Custom resolvers**: Support for custom resolution logic

## Usage

### Setting Up Synchronization

```python
from uno.offline import OfflineStore
from uno.offline.sync import (```

SynchronizationEngine,
SyncOptions,
RestAdapter,
ServerWinsResolver
```
)

# Create offline store
store = OfflineStore(name="my-app-data")

# Create network adapter for server communication
adapter = RestAdapter(```

base_url="https://api.example.com/v1",
headers={"Accept": "application/json"},
auth_token="my-auth-token"
```
)

# Configure synchronization
sync_options = SyncOptions(```

collections=["users", "orders", "products"],
strategy="two-way",  # or "pull-only", "push-only"
network_adapter=adapter,
conflict_strategy="server-wins"  # simple string option
```
)

# Alternatively, use a more advanced conflict resolution strategy
sync_options = SyncOptions(```

collections=["users", "orders", "products"],
strategy="two-way",
network_adapter=adapter,
conflict_strategy=ServerWinsResolver()  # explicit resolver instance
```
)

# Create sync engine
sync_engine = SynchronizationEngine(store, sync_options)
```

### Manual Synchronization

```python
# Synchronize all configured collections
try:```

result = await sync_engine.sync()
print(f"Uploaded: {result['uploaded']}, Downloaded: {result['downloaded']}")
``````

```
```

if result["conflicts"] > 0:```

print(f"Resolved {result['conflicts']} conflicts")
```
    
if result["errors"]:```

print(f"Encountered errors: {result['errors']}")
```
    
```
except Exception as e:```

print(f"Synchronization failed: {e}")
```

# Synchronize specific collections
result = await sync_engine.sync(collections=["users", "orders"])
```

### Handling Conflicts

```python
from uno.offline.sync import MergeFieldsResolver

# Create a custom conflict resolution strategy
resolver = MergeFieldsResolver(```

client_fields=["name", "description"],  # Fields to take from client
server_fields=["price", "inventory"]     # Fields to take from server
```
)

# Use the resolver in sync options
sync_options = SyncOptions(```

collections=["products"],
strategy="two-way",
network_adapter=adapter,
conflict_strategy=resolver
```
)
```

### Custom Conflict Resolution

```python
from uno.offline.sync import ConflictResolver

# Define a custom conflict resolution function
def my_resolver(collection, local_data, server_data):```

if collection == "users":```

# For users, merge data selectively
result = server_data.copy()
# Keep the user's local profile changes
if "profile" in local_data:
    result["profile"] = local_data["profile"]
return result
```
else:```

# For other collections, use server data
return server_data
```
```

# Create a resolver with the custom function
resolver = ConflictResolver(my_resolver)

# Use in sync options
sync_options = SyncOptions(```

collections=["users", "products"],
conflict_strategy=resolver
```
)
```

### Cancelling Synchronization

```python
import asyncio

# Start synchronization in a task
sync_task = asyncio.create_task(sync_engine.sync())

# Later, cancel it
sync_engine.cancel()

# Wait for the task to complete (will raise SyncCancelledError)
try:```

await sync_task
```
except SyncCancelledError:```

print("Synchronization was cancelled")
```
```

## Synchronization Strategies

The Synchronization Engine supports different synchronization strategies:

### Two-Way Synchronization

Synchronizes changes in both directions (default):

```python
from uno.offline.sync import SyncOptions

sync_options = SyncOptions(```

collections=["users", "products"],
strategy="two-way",
network_adapter=adapter,
conflict_strategy="server-wins"
```
)
```

Best for:
- Most applications where data changes on both client and server
- Full synchronization requirements
- Applications requiring data consistency

### Pull-Only Synchronization

Only pulls changes from the server:

```python
from uno.offline.sync import SyncOptions

sync_options = SyncOptions(```

collections=["users", "products"],
strategy="pull-only",
network_adapter=adapter,
conflict_strategy="server-wins"
```
)
```

Best for:
- Read-heavy applications
- Applications where server is the source of truth
- Updating reference data

### Push-Only Synchronization

Only pushes local changes to the server:

```python
from uno.offline.sync import SyncOptions

sync_options = SyncOptions(```

collections=["users", "products"],
strategy="push-only",
network_adapter=adapter,
conflict_strategy="server-wins"
```
)
```

Best for:
- Write-heavy applications
- Data collection applications
- Uploading local changes without overwriting local data

## Network Adapters

Network adapters handle communication with the server based on different protocols:

### REST Adapter

```python
from uno.offline.sync import RestAdapter

adapter = RestAdapter(```

base_url="https://api.example.com/v1",
headers={"Accept": "application/json"},
auth_token="my-auth-token"
```,```

timeout=30.0,
retry_count=3,
retry_delay=1.0
```
)
```

The REST adapter provides:
- Authentication with tokens
- Automatic retries with exponential backoff
- Error handling for network issues
- Conflict detection and reporting
- Batch operations for efficiency

### Custom Adapter

You can create custom adapters by implementing the `NetworkAdapter` interface:

```python
from uno.offline.sync import NetworkAdapter

class MyCustomAdapter(NetworkAdapter):```

async def fetch_changes(self, collection, query_params=None):```

"""Fetch changes from the server."""
# Custom implementation
pass
```
    
async def send_change(self, collection, data):```

"""Send a change to the server."""
# Custom implementation
pass
```
    
async def is_online(self):```

"""Check if the server is reachable."""
# Custom implementation
pass
```
    
def get_server_timestamp(self):```

"""Get the server's timestamp."""
# Custom implementation
pass
```
```

# Create and use the adapter
adapter = MyCustomAdapter()
```

### Batch Support

For additional efficiency, you can implement the `BatchSupportMixin` to add batch operations support:

```python
from uno.offline.sync import NetworkAdapter, BatchSupportMixin

class MyBatchAdapter(NetworkAdapter, BatchSupportMixin):```

# Implement required NetworkAdapter methods
``````

```
```

async def send_batch(self, collection, batch):```

"""Send a batch of changes to the server."""
# Custom implementation for efficient batch sending
pass
```
    
async def fetch_batch(self, collection, ids, query_params=None):```

"""Fetch a batch of records from the server."""
# Custom implementation for efficient batch fetching
pass
```
```
```

## Conflict Resolution

The Synchronization Engine supports various conflict resolution strategies:

### Server Wins

Always chooses the server's version of the data:

```python
from uno.offline.sync import ServerWinsResolver

# Simple string shorthand
sync_options = SyncOptions(```

collections=["users", "products"],
conflict_strategy="server-wins"  # String shorthand
```
)

# Or explicitly
sync_options = SyncOptions(```

collections=["users", "products"],
conflict_strategy=ServerWinsResolver()
```
)
```

### Client Wins

Always chooses the client's version of the data:

```python
from uno.offline.sync import ClientWinsResolver

sync_options = SyncOptions(```

collections=["users", "products"],
conflict_strategy=ClientWinsResolver()
```
)
```

### Timestamp Based

Chooses the most recently updated version:

```python
from uno.offline.sync import TimestampBasedResolver

sync_options = SyncOptions(```

collections=["users", "products"],
conflict_strategy=TimestampBasedResolver(timestamp_field="updated_at")
```
)
```

### Merge Fields

Selectively merges fields from both versions:

```python
from uno.offline.sync import MergeFieldsResolver

sync_options = SyncOptions(```

collections=["users", "products"],
conflict_strategy=MergeFieldsResolver(```

client_fields=["name", "description"],
server_fields=["price", "inventory"]
```
)
```
)
```

### Custom Resolution

You can also provide a custom conflict resolution function:

```python
from uno.offline.sync import ConflictResolver

def my_resolver(collection, local_data, server_data):```

# Custom logic to resolve conflicts
if collection == "users":```

# For users, prefer local profile changes but server permission changes
result = server_data.copy()
result["profile"] = local_data.get("profile", {})
return result
```
else:```

# For other collections, use server data
return server_data
```
```

sync_options = SyncOptions(```

collections=["users", "products"],
conflict_strategy=ConflictResolver(my_resolver)
```
)
```

## Advanced Features

### Prioritized Synchronization

Configure which collections and records sync first:

```python
sync_options = SyncOptions(```

sync_order=["users", "products", "orders"],
priority_records={```

"orders": lambda record: record.get("status") == "pending"
```
}
```
)
```

### Selective Synchronization

Sync only specific records matching certain criteria:

```python
sync_options = SyncOptions(```

sync_filters={```

"orders": {"status": {"$in": ["pending", "processing"]}},
"products": {"active": True}
```
}
```
)
```

### Background Synchronization

Configure background sync behavior:

```python
sync_options = SyncOptions(```

auto_sync_interval=300,  # 5 minutes
sync_on_connect=True,
sync_on_background=True,
background_sync_mode="low-priority"  # or "normal" or "high-priority"
```
)
```

### Network Status Handling

```python
# Register network status handlers
sync_engine.on_network_status_changed(lambda status: print(f"Network status changed: {status}"))

# Manually check network status
if sync_engine.is_online():```

print("Network is available")
```
else:```

print("Offline mode")
```

# Manually set network status (e.g., from app's network monitor)
sync_engine.set_network_status(True)  # Online
sync_engine.set_network_status(False) # Offline
```

### Partial Sync

Sync only certain fields to reduce data transfer:

```python
sync_options = SyncOptions(```

field_inclusion={```

"users": ["id", "name", "email", "updated_at"],
"products": ["id", "name", "price", "updated_at"]
```
}
```
)
```

## Error Handling

The Synchronization Engine provides comprehensive error handling with a hierarchy of error types:

```python
from uno.offline.sync import (```

SyncError,          # Base class for all sync errors
NetworkError,       # Network connectivity issues
ConflictError,      # Conflict between local and remote data
SyncCancelledError, # Synchronization was cancelled
ConfigurationError, # Invalid configuration
AdapterError,       # Network adapter issues
ChangeTrackingError # Issues with change tracking
```
)

# Handle different error types
try:```

result = await sync_engine.sync()
# Process result
```
except NetworkError as e:```

print(f"Network error: {e}")
# Handle network issues (retry later, etc.)
```
except ConflictError as e:```

print(f"Conflict: {e}")
print(f"Local data: {e.local_data}")
print(f"Server data: {e.server_data}")
# Handle conflict (maybe manual resolution)
```
except SyncCancelledError:```

print("Synchronization was cancelled")
``````

# Handle cancellation (cleanup, etc.)
```
except SyncError as e:```

print(f"Synchronization error: {e}")
# Handle other sync errors
```
```

Error details are included in the sync results:

```python
result = await sync_engine.sync()
if result["errors"]:```

print("Errors occurred during synchronization:")
for error in result["errors"]:```

print(f"- {error}")
```
```

# Check for collection-specific errors
for collection, details in result["details"].items():```

if details.get("errors"):```

print(f"Errors in collection {collection}:")
for error in details["errors"]:
    print(f"- {error}")
```
```
```

## Debugging and Monitoring

Tools for monitoring and debugging synchronization:

```python
# Enable detailed logging
sync_engine.set_log_level("debug")

# Get sync statistics
stats = sync_engine.get_statistics()
print(f"Total sync operations: {stats.total_syncs}")
print(f"Average sync duration: {stats.average_duration_ms}ms")
print(f"Data transferred: {stats.total_bytes_transferred} bytes")

# Export sync logs
logs = sync_engine.export_sync_logs()
with open("sync_logs.json", "w") as f:```

json.dump(logs, f, indent=2)
```
```

## Best Practices

1. **Start Simple**: Begin with server-wins strategy and move to more complex resolution as needed

2. **Sync Incrementally**: Use incremental sync for better performance and reduced bandwidth

3. **Field Selection**: Only sync the fields you need to reduce data transfer

4. **Error Recovery**: Implement proper retry mechanisms for failed syncs

5. **Conflict Visibility**: Make conflicts visible to users when appropriate

6. **Background Sync**: Use background sync to keep data fresh without disrupting the user

7. **Connection Awareness**: Be smart about when to sync based on network conditions

8. **Sync Tracking**: Keep track of sync status and errors for debugging

9. **User Control**: Give users control over when and how synchronization happens

10. **Testing**: Thoroughly test synchronization with various network conditions and edge cases