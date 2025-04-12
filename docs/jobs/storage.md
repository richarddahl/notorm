# Storage Backends

The Storage Backends component provides persistent storage for jobs, queues, and schedules in the background processing system.

## Overview

Storage backends are responsible for:

- Storing and retrieving job data
- Managing queue state and operations
- Persisting scheduler information
- Ensuring reliability and durability of job processing
- Supporting concurrent access from multiple workers

The system provides several storage backends to meet different requirements.

## Available Backends

### In-Memory Storage

Stores data in memory, suitable for development and testing:

```python
from uno.jobs.storage import InMemoryStorage
from uno.jobs.queue import JobQueue

# Create an in-memory storage backend
storage = InMemoryStorage()

# Use it with a queue
queue = JobQueue(storage=storage)
```

Key characteristics:
- Fast performance
- No persistence across restarts
- Limited to a single process
- Suitable for development and testing

### Database Storage

Stores data in a SQL database, providing durability and shared access:

```python
from uno.jobs.storage import DatabaseStorage
from uno.jobs.queue import JobQueue

# Create a database storage backend
storage = DatabaseStorage(
    connection_string="postgresql://user:pass@localhost/dbname",
    table_prefix="jobs_"  # Optional prefix for all tables
)

# Use it with a queue
queue = JobQueue(storage=storage)
```

Supported databases:
- PostgreSQL
- MySQL
- SQLite

Key characteristics:
- Durable storage
- Transaction support
- Suitable for production use
- Shared access from multiple processes/machines
- Slower than in-memory storage

### Redis Storage

Uses Redis for high-performance storage with persistence:

```python
from uno.jobs.storage import RedisStorage
from uno.jobs.queue import JobQueue

# Create a Redis storage backend
storage = RedisStorage(
    redis_url="redis://localhost:6379/0",
    key_prefix="jobs:"  # Optional prefix for Redis keys
)

# Use it with a queue
queue = JobQueue(storage=storage)
```

Key characteristics:
- High performance
- Optional persistence
- Suitable for production use
- Distributed locking support
- Efficient for high-throughput scenarios

### MongoDB Storage

Stores data in MongoDB, suitable for document-oriented workloads:

```python
from uno.jobs.storage import MongoDBStorage
from uno.jobs.queue import JobQueue

# Create a MongoDB storage backend
storage = MongoDBStorage(
    connection_string="mongodb://localhost:27017",
    database="jobs_db",
    collection_prefix="jobs_"  # Optional prefix for all collections
)

# Use it with a queue
queue = JobQueue(storage=storage)
```

Key characteristics:
- Flexible schema
- Good performance
- Suitable for jobs with complex, nested data
- Built-in sharding support for scalability

## Storage Interface

All storage backends implement the common `Storage` interface:

```python
from uno.jobs.storage import Storage

class CustomStorage(Storage):
    """Custom storage implementation."""
    
    async def initialize(self):
        """Initialize the storage backend."""
        # Setup connection, create tables/collections, etc.
        pass
    
    async def shutdown(self):
        """Clean up resources used by the storage backend."""
        # Close connections, etc.
        pass
    
    # Job operations
    async def create_job(self, job_data):
        """Create a new job record."""
        pass
    
    async def get_job(self, job_id):
        """Get a job by ID."""
        pass
    
    async def update_job(self, job_id, updates):
        """Update a job's data."""
        pass
    
    async def delete_job(self, job_id):
        """Delete a job."""
        pass
    
    # Queue operations
    async def enqueue(self, queue_name, job_data):
        """Add a job to a queue."""
        pass
    
    async def dequeue(self, queue_name, worker_id):
        """Get the next job from a queue."""
        pass
    
    async def complete_job(self, job_id, result):
        """Mark a job as completed."""
        pass
    
    async def fail_job(self, job_id, error, retry=False):
        """Mark a job as failed."""
        pass
    
    # Other required methods...
```

## Storage Configuration

Each storage backend offers configuration options:

### Database Storage Configuration

```python
from uno.jobs.storage import DatabaseStorage

storage = DatabaseStorage(
    # Connection settings
    connection_string="postgresql://user:pass@localhost/dbname",
    table_prefix="jobs_",
    
    # Connection pool settings
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    
    # Schema settings
    create_tables=True,
    migrate_schema=True,
    
    # Performance settings
    use_batch_operations=True,
    result_compression=True,
    
    # Advanced settings
    json_serializer=custom_serializer,
    json_deserializer=custom_deserializer
)
```

### Redis Storage Configuration

```python
from uno.jobs.storage import RedisStorage

storage = RedisStorage(
    # Connection settings
    redis_url="redis://localhost:6379/0",
    key_prefix="jobs:",
    
    # Connection pool settings
    max_connections=20,
    
    # Performance settings
    use_pipeline=True,
    result_compression=True,
    
    # Persistence settings
    use_persistence=True,
    
    # Advanced settings
    serializer=custom_serializer,
    deserializer=custom_deserializer
)
```

## Storage Operations

Storage backends provide operations for managing jobs and queues:

### Job Management

```python
# Create a job
job_id = await storage.create_job({
    "task": "process_file",
    "args": ["file123"],
    "status": "pending"
})

# Get a job
job = await storage.get_job(job_id)

# Update a job
await storage.update_job(job_id, {
    "status": "running",
    "started_at": datetime.now().isoformat()
})

# Delete a job
await storage.delete_job(job_id)
```

### Queue Management

```python
# Add a job to a queue
await storage.enqueue("default", job_data)

# Get the next job from a queue
job = await storage.dequeue("default", "worker-1")

# Mark a job as complete
await storage.complete_job(job_id, {"result": "success"})

# Mark a job as failed
await storage.fail_job(job_id, {"error": "Connection failed"}, retry=True)
```

### Batch Operations

Some storage backends support batch operations for improved performance:

```python
# Batch create jobs
job_ids = await storage.batch_create_jobs([job_data1, job_data2, job_data3])

# Batch update jobs
await storage.batch_update_jobs([
    (job_id1, updates1),
    (job_id2, updates2)
])
```

## Transactions

Storage backends can provide transaction support:

```python
async with storage.transaction() as tx:
    # Operations within a transaction
    job_id = await tx.create_job(job_data)
    await tx.enqueue("default", job_id)
    
    # If an exception is raised, the transaction will be rolled back
    # Otherwise, it will be committed
```

## Storage Migrations

Some storage backends support schema migrations:

```python
from uno.jobs.storage import migrate_storage

# Migrate the storage schema
await migrate_storage(storage, target_version="1.2.0")
```

## Storage Diagnostics

Storage backends provide diagnostic utilities:

```python
# Check storage health
health = await storage.check_health()
if health["status"] == "healthy":
    print("Storage is healthy")
else:
    print(f"Storage has issues: {health['issues']}")

# Get storage statistics
stats = await storage.get_statistics()
print(f"Total jobs: {stats['total_jobs']}")
print(f"Jobs by status: {stats['jobs_by_status']}")
```

## Distributed Locking

Some storage backends provide distributed locking capabilities:

```python
# Create a distributed lock
async with storage.create_lock("scheduler", timeout=60) as lock:
    # This block will only be executed by one process at a time
    # If the lock cannot be acquired, LockError will be raised
    # The lock will be automatically released when the block exits
    # The lock will automatically expire after the timeout
    pass
```

## Storage Maintenance

Storage backends may need occasional maintenance:

```python
# Prune old jobs
deleted_count = await storage.prune_jobs(
    status=["completed", "failed"],
    older_than=datetime.now() - timedelta(days=7)
)
print(f"Deleted {deleted_count} old jobs")

# Compact the storage (for backends that support it)
if hasattr(storage, "compact"):
    await storage.compact()
```

## Custom Storage Implementations

You can create custom storage backends by implementing the `Storage` interface:

```python
from uno.jobs.storage import Storage

class CustomStorage(Storage):
    """Custom storage implementation."""
    
    def __init__(self, custom_config):
        self.config = custom_config
    
    async def initialize(self):
        # Initialize your storage
        pass
    
    async def shutdown(self):
        # Clean up resources
        pass
    
    # Implement all required methods from the Storage interface
    # ...
```

## Storage Events

Some storage backends emit events that can be listened to:

```python
# Register event handlers
@storage.on("job_created")
async def on_job_created(job_id, job_data):
    print(f"Job created: {job_id}")

@storage.on("job_completed")
async def on_job_completed(job_id, result):
    print(f"Job completed: {job_id}")
```

## Storage Replication

Some storage backends support replication for high availability:

```python
from uno.jobs.storage import RedisStorage

# Primary-replica Redis setup
storage = RedisStorage(
    redis_url="redis://primary:6379/0",
    replicas=[
        "redis://replica1:6379/0",
        "redis://replica2:6379/0"
    ],
    read_from_replicas=True
)
```

## Storage Security

Storage backends support security features:

```python
from uno.jobs.storage import DatabaseStorage

# Secure database connection
storage = DatabaseStorage(
    connection_string="postgresql://user:pass@localhost/dbname",
    ssl_mode="require",
    ssl_cert_file="/path/to/cert.pem",
    ssl_key_file="/path/to/key.pem",
    ssl_ca_file="/path/to/ca.pem"
)
```