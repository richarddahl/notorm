# Job Queue

The Job Queue component is responsible for storing, prioritizing, and managing jobs that need to be processed by workers.

## Overview

The Job Queue is a central component in the background processing system, acting as a buffer between job producers (applications, schedulers) and job consumers (workers). It ensures that:

- Jobs are processed in order of priority
- Jobs remain persistent even if the application restarts
- Multiple workers can process jobs concurrently
- Job status is tracked throughout the lifecycle

## Queue Structure

Each queue has the following characteristics:

- **Name**: Unique identifier for the queue
- **Priority Levels**: Multiple priority levels (critical, high, normal, low)
- **FIFO Processing**: First-in, first-out for jobs with the same priority
- **Status Tracking**: Jobs are tracked as they move through the lifecycle
- **Persistence**: Jobs are stored in a persistent backend

## Job Lifecycle

Jobs move through the following states:

1. **Pending**: Job is waiting in the queue
2. **Reserved**: Job has been claimed by a worker but not yet started
3. **Running**: Job is currently being processed
4. **Completed**: Job has finished successfully
5. **Failed**: Job has encountered an error
6. **Retrying**: Job failed but will be retried
7. **Cancelled**: Job was manually cancelled before completion

## Job Structure

Each job contains:

```python
{```

"id": "uuid-string",                      # Unique job identifier
"task": "module.function",                # Task to execute
"args": [1, 2, 3],                        # Positional arguments
"kwargs": {"param1": "value1"},           # Keyword arguments
"queue": "default",                       # Queue name
"priority": "normal",                     # Priority level
"status": "pending",                      # Current job status
"created_at": "2023-04-12T10:00:00Z",     # Creation timestamp
"scheduled_for": "2023-04-12T10:05:00Z",  # When to process the job
"started_at": null,                       # When processing started
"completed_at": null,                     # When processing completed
"result": null,                           # Result data (if successful)
"error": null,                            # Error information (if failed)
"retry_count": 0,                         # Number of retries attempted
"max_retries": 3,                         # Maximum retry attempts
"retry_delay": 60,                        # Seconds between retries
"tags": ["report", "monthly"],            # Optional tags for filtering
"metadata": {"user_id": 123}              # Custom metadata
```
}
```

## Priority Levels

The queue supports four priority levels:

1. **Critical (0)**: Highest priority, processed immediately
2. **High (10)**: Higher than normal, but below critical
3. **Normal (20)**: Default priority level
4. **Low (30)**: Lowest priority, processed when resources allow

Jobs with higher priority are always processed before jobs with lower priority, regardless of when they were added to the queue.

## Queue Operations

The queue supports the following operations:

### Enqueue

Add a new job to the queue:

```python
await queue.enqueue(```

task="reports.generate_monthly_report",
args=[123, "monthly"],
kwargs={"format": "pdf"},
priority="high",
scheduled_for=datetime.now() + timedelta(minutes=5),
max_retries=3,
retry_delay=60,
tags=["report", "monthly"],
metadata={"requester": "user_123"}
```
)
```

### Dequeue

Get the next job from the queue:

```python
job = await queue.dequeue(worker_id="worker1")
```

### Complete

Mark a job as completed:

```python
await queue.complete(job_id="job123", result={"file_url": "/reports/123.pdf"})
```

### Fail

Mark a job as failed:

```python
await queue.fail(```

job_id="job123",
error={"type": "ValueError", "message": "Invalid parameters"},
retry=True
```
)
```

### Cancel

Cancel a pending job:

```python
await queue.cancel(job_id="job123")
```

### Get Job

Retrieve a job by ID:

```python
job = await queue.get_job(job_id="job123")
```

### List Jobs

List jobs with filtering:

```python
jobs = await queue.list_jobs(```

status=["pending", "running"],
queue="default",
priority="high",
tags=["report"],
limit=20,
offset=0
```
)
```

## Queue Statistics

The queue provides statistics for monitoring:

```python
stats = await queue.get_statistics()
"""
{```

"total_jobs": 1250,
"pending_jobs": 45,
"running_jobs": 10,
"completed_jobs": 1150,
"failed_jobs": 45,
"retry_jobs": 5,
"by_priority": {```

"critical": 0,
"high": 5,
"normal": 35,
"low": 5
```
},
"by_queue": {```

"default": 30,
"reports": 15
```
}
```
}
"""
```

## Storage Backends

The Job Queue can use different storage backends:

### In-Memory

For development and testing, stores jobs in memory:

```python
from uno.jobs.storage import InMemoryStorage
from uno.jobs.queue import JobQueue

storage = InMemoryStorage()
queue = JobQueue(storage=storage)
```

### Database

For production, stores jobs in a database:

```python
from uno.jobs.storage import DatabaseStorage
from uno.jobs.queue import JobQueue

storage = DatabaseStorage(connection_string="postgresql://user:pass@localhost/dbname")
queue = JobQueue(storage=storage)
```

### Redis

For high-throughput scenarios:

```python
from uno.jobs.storage import RedisStorage
from uno.jobs.queue import JobQueue

storage = RedisStorage(redis_url="redis://localhost:6379/0")
queue = JobQueue(storage=storage)
```

## Queue Management

The queue provides tools for management:

### Pruning

Remove old completed jobs:

```python
await queue.prune(```

status=["completed", "failed"],
older_than=datetime.now() - timedelta(days=30)
```
)
```

### Requeuing

Requeue stuck jobs:

```python
count = await queue.requeue_stuck(```

older_than=datetime.now() - timedelta(hours=1)
```
)
```

### Pausing

Pause a queue to stop processing new jobs:

```python
await queue.pause()
```

### Resuming

Resume a paused queue:

```python
await queue.resume()
```

## Error Handling

The queue implements sophisticated error handling:

### Automatic Retries

Jobs that fail can be automatically retried:

```python
await queue.enqueue(```

task="external_api.make_request",
max_retries=3,
retry_delay=60
```
)
```

### Dead Letter Queue

Jobs that exceed retry limits are moved to a dead letter queue:

```python
# Configure a dead letter queue
await queue.configure(dead_letter_queue="failed-jobs")

# Get jobs from the dead letter queue
failed_jobs = await queue.list_jobs(queue="failed-jobs")
```

### Error Details

Detailed error information is captured for debugging:

```python
job = await queue.get_job(job_id="job123")
if job["status"] == "failed":```

error = job["error"]
print(f"Error type: {error['type']}")
print(f"Error message: {error['message']}")
print(f"Error traceback: {error['traceback']}")
```
```