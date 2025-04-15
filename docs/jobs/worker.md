# Workers

The Worker component processes jobs from the queue, executing tasks and reporting results.

## Overview

Workers are the processing engines of the background jobs system. They:

- Monitor queues for available jobs
- Execute tasks with the specified parameters
- Handle job completion and failure reporting
- Implement retry and error handling logic
- Provide health and performance metrics

## Worker Types

The system offers different worker types to meet various requirements:

### Synchronous Worker

Processes jobs one at a time in a single thread:

```python
from uno.jobs.worker import SyncWorker

worker = SyncWorker(```

queue_name="default",
worker_id="sync-worker-1"
```
)
await worker.start()
```

### Thread Pool Worker

Processes multiple jobs concurrently using a thread pool:

```python
from uno.jobs.worker import ThreadPoolWorker

worker = ThreadPoolWorker(```

queue_name="default",
worker_id="thread-worker-1",
max_threads=10
```
)
await worker.start()
```

### Process Pool Worker

Processes jobs in separate processes for CPU-bound tasks:

```python
from uno.jobs.worker import ProcessPoolWorker

worker = ProcessPoolWorker(```

queue_name="default",
worker_id="process-worker-1",
max_processes=4
```
)
await worker.start()
```

### Async Worker

Processes jobs concurrently using asyncio for IO-bound tasks:

```python
from uno.jobs.worker import AsyncWorker

worker = AsyncWorker(```

queue_name="default",
worker_id="async-worker-1",
max_concurrent=50
```
)
await worker.start()
```

### Distributed Worker

Works as part of a cluster of workers across multiple machines:

```python
from uno.jobs.worker import DistributedWorker

worker = DistributedWorker(```

queue_name="default",
worker_id="distributed-worker-1",
cluster_id="cluster-1",
coordinator_url="redis://localhost:6379/0"
```
)
await worker.start()
```

## Worker Configuration

Workers offer rich configuration options:

```python
from uno.jobs.worker import AsyncWorker

worker = AsyncWorker(```

# Basic configuration
queue_name="default",              # Queue to process
worker_id="worker-1",              # Unique worker identifier
``````

```
```

# Concurrency settings
max_concurrent=20,                 # Maximum concurrent jobs
batch_size=10,                     # Jobs to fetch at once
``````

```
```

# Processing settings
shutdown_timeout=30,               # Seconds to wait for graceful shutdown
poll_interval=1.0,                 # Seconds between polling when queue is empty
prefetch=True,                     # Whether to prefetch next jobs
``````

```
```

# Reliability settings
heartbeat_interval=30,             # Seconds between worker heartbeats
max_job_duration=3600,             # Maximum job runtime in seconds
``````

```
```

# Health check settings
healthcheck_interval=60,           # Seconds between health checks
``````

```
```

# Middleware
middleware=[logging_middleware],   # Processing middleware
``````

```
```

# Error handling
max_failures=100,                  # Max consecutive failures before shutdown
``````

```
```

# Monitoring
metrics_enabled=True,              # Whether to collect metrics
metrics_interval=10                # Seconds between metrics collection
```
)
```

## Worker Lifecycle

Workers follow a defined lifecycle:

1. **Initialization**: Worker is created with configuration
2. **Starting**: Worker connects to the queue and initializes
3. **Running**: Worker continuously processes jobs
4. **Pausing**: Worker temporarily stops processing new jobs
5. **Resuming**: Worker resumes processing jobs
6. **Shutting Down**: Worker gracefully stops, completing current jobs
7. **Stopped**: Worker is fully stopped and resources released

Control the worker lifecycle with:

```python
# Start the worker
await worker.start()

# Pause processing
await worker.pause()

# Resume processing
await worker.resume()

# Gracefully shutdown
await worker.shutdown()

# Force immediate shutdown (not recommended)
await worker.shutdown(wait=False)
```

## Job Processing Flow

The worker processes jobs through the following steps:

1. **Job Acquisition**: Worker fetches a job from the queue
2. **Task Loading**: Worker loads the task module and function
3. **Execution**: Worker runs the task with provided arguments
4. **Result Processing**: Worker captures the return value or exception
5. **Job Completion**: Worker updates the job status in the queue

## Task Discovery

Workers automatically discover tasks through:

### Module Path

Specifying the full module path:

```python
await queue.enqueue(```

task="my_app.tasks.reports.generate_report",
args=["monthly", "pdf"]
```
)
```

### Task Registry

Using the task registry:

```python
from uno.jobs.tasks import task, TaskRegistry

# Register a task
@task(name="generate_report")
async def generate_monthly_report(report_type, format):```

# Task implementation
pass
```

# Enqueue using registered name
await queue.enqueue(```

task="generate_report",
args=["monthly", "pdf"]
```
)
```

## Error Handling

Workers implement robust error handling:

### Exception Handling

All exceptions during task execution are caught and reported:

```python
@task
async def task_that_might_fail():```

raise ValueError("Something went wrong")
```

# The worker will catch the exception, record it, and handle retries
```

### Retry Logic

Failed jobs can be automatically retried:

```python
@task(max_retries=3, retry_delay=60)
async def task_with_retries():```

# This task will be retried up to 3 times with 60 second delays
pass
```
```

### Timeout Handling

Tasks can be time-limited:

```python
@task(timeout=300)  # 5 minute timeout
async def long_running_task():```

# If this task exceeds 5 minutes, it will be terminated
pass
```
```

## Middleware

Workers support middleware for cross-cutting concerns:

```python
from uno.jobs.middleware import Middleware

class LoggingMiddleware(Middleware):```

async def before_execution(self, job, task_func):```

print(f"Starting job {job['id']}")
return await super().before_execution(job, task_func)
```
``````

```
```

async def after_execution(self, job, task_func, result):```

print(f"Completed job {job['id']}")
return await super().after_execution(job, task_func, result)
```
``````

```
```

async def on_error(self, job, task_func, exception):```

print(f"Error in job {job['id']}: {exception}")
return await super().on_error(job, task_func, exception)
```
```

# Use middleware with a worker
worker = AsyncWorker(```

queue_name="default",
worker_id="worker-1",
middleware=[LoggingMiddleware()]
```
)
```

## Monitoring and Health Checks

Workers provide monitoring capabilities:

### Health Checks

Periodic health checks ensure workers are functioning:

```python
# Health status
health = await worker.get_health()
"""
{```

"status": "healthy",
"uptime": 3600,
"jobs_processed": 150,
"failure_rate": 0.02,
"current_jobs": 5,
"last_job_completed": "2023-04-12T10:00:00Z"
```
}
"""
```

### Metrics

Workers collect performance metrics:

```python
# Performance metrics
metrics = await worker.get_metrics()
"""
{```

"jobs_processed_total": 1500,
"jobs_succeeded": 1450,
"jobs_failed": 50,
"processing_time_avg_ms": 120,
"processing_time_p95_ms": 350,
"processing_time_p99_ms": 850,
"queue_wait_time_avg_ms": 200,
"throughput_jobs_per_minute": 25,
"error_rate": 0.033,
"active_jobs": 10
```
}
"""
```

## Scaling and Distribution

Workers can be scaled horizontally for increased throughput:

### Multi-Worker Setup

Run multiple workers for a single queue:

```python
# Worker 1
worker1 = AsyncWorker(queue_name="default", worker_id="worker-1")
await worker1.start()

# Worker 2
worker2 = AsyncWorker(queue_name="default", worker_id="worker-2")
await worker2.start()

# Worker 3
worker3 = AsyncWorker(queue_name="default", worker_id="worker-3")
await worker3.start()
```

### Worker Pool

Create a managed pool of workers:

```python
from uno.jobs.worker import WorkerPool

pool = WorkerPool(```

queue_name="default",
worker_type=AsyncWorker,
min_workers=5,
max_workers=20,
worker_options={```

"max_concurrent": 10,
"heartbeat_interval": 30
```
}
```
)

# Start the pool with auto-scaling
await pool.start(auto_scale=True)
```

### Specialized Workers

Create workers that focus on specific job types:

```python
# High-priority worker for critical jobs
critical_worker = AsyncWorker(```

queue_name="default",
worker_id="critical-worker",
priority_levels=["critical"]
```
)

# Standard worker for normal jobs
standard_worker = AsyncWorker(```

queue_name="default",
worker_id="standard-worker",
priority_levels=["high", "normal"]
```
)

# Background worker for low-priority jobs
background_worker = AsyncWorker(```

queue_name="default",
worker_id="background-worker",
priority_levels=["low"]
```
)
```

## Advanced Features

### Graceful Shutdown

Workers can shut down gracefully:

```python
import signal

# Handle termination signals
for sig in (signal.SIGINT, signal.SIGTERM):```

signal.signal(sig, lambda s, f: asyncio.create_task(worker.shutdown()))
```

# Start the worker
await worker.start()

# In shutdown handler
async def shutdown_handler():```

print("Shutting down worker...")
await worker.shutdown()
print("Worker shutdown complete")
```
```

### Worker Coordination

Coordinate multiple workers in a cluster:

```python
from uno.jobs.worker import WorkerCoordinator

coordinator = WorkerCoordinator(```

storage_url="redis://localhost:6379/0",
cluster_id="production-cluster"
```
)

# Register a worker with the coordinator
await coordinator.register_worker(worker)

# Start coordinated processing
await coordinator.start()
```