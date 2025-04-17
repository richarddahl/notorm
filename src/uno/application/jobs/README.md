# uno Background Processing System

The uno Background Processing system provides robust support for executing tasks asynchronously and on a schedule, enabling applications to handle time-consuming or resource-intensive operations without blocking the main application thread.

## Overview

The system follows a distributed job processing architecture with the following components:

- **Job Queue**: Stores pending jobs with priorities and manages job lifecycle
- **Workers**: Process jobs from the queue with configurable concurrency
- **Scheduler**: Creates jobs on a scheduled basis
- **Job Manager**: Coordinates job execution and worker management
- **Storage Backends**: Various storage options for different needs
- **Monitoring**: Metrics collection and health checks
- **Administration**: API endpoints for managing the job system

## Key Features

- **Prioritization**: Jobs can have CRITICAL, HIGH, NORMAL, or LOW priority
- **Flexible Scheduling**: Cron-style, interval-based, and one-time scheduling
- **Retry Policies**: Configurable retry counts and delays
- **Monitoring**: Metrics and health checks for system oversight
- **Storage Options**: In-memory, database, and Redis backends
- **Admin Interface**: Complete management of jobs, queues, and schedules

## Installation

The background processing system is included as part of uno.

## Basic Usage

### Creating a Job Manager

```python
from uno.jobs.storage.memory import InMemoryJobStorage
from uno.jobs.worker.async_worker import AsyncWorker
from uno.jobs.scheduler.scheduler import Scheduler
from uno.jobs.manager import JobManager

# Create storage backend
storage = InMemoryJobStorage()

# Create job manager with workers and scheduler
job_manager = JobManager(
    storage=storage,
    worker_classes=[AsyncWorker],
    scheduler=Scheduler(storage=storage),
)

# Start the job manager
await job_manager.start()
```

### Defining Tasks

```python
# Using decorator
@job_manager.task(
    name="send_email",
    description="Send an email to a user",
    max_retries=3,
    retry_delay=timedelta(minutes=5),
    queue="emails",
)
async def send_email(to: str, subject: str, body: str):
    # Implementation
    return {"success": True}

# Or register directly
def process_report(report_id: str, options: dict):
    # Implementation
    return {"report_id": report_id, "status": "completed"}

job_manager.register_task(
    name="process_report",
    handler=process_report,
    description="Process a report",
    max_retries=2,
    queue="reports",
)
```

### Enqueueing Jobs

```python
# Enqueue a job to run as soon as possible
result = await job_manager.enqueue(
    task_name="send_email",
    args=["user@example.com"],
    kwargs={"subject": "Hello", "body": "Test message"},
    priority=Priority.HIGH,
)

# Enqueue a job to run at a specific time
result = await job_manager.enqueue(
    task_name="process_report",
    args=["report-123"],
    kwargs={"options": {"format": "pdf"}},
    scheduled_at=datetime.utcnow() + timedelta(hours=2),
)

# Get the job ID
job_id = result.value
```

### Creating Schedules

```python
from uno.jobs.scheduler.schedules import CronSchedule, IntervalSchedule

# Create a cron schedule (run at 2am every day)
cron_schedule = CronSchedule(expression="0 2 * * *")

# Create an interval schedule (run every 30 minutes)
interval_schedule = IntervalSchedule(minutes=30)

# Add a schedule
result = await job_manager.scheduler.add_schedule(
    name="daily_report",
    task_name="process_report",
    schedule=cron_schedule,
    args=["daily-summary"],
    kwargs={"options": {"format": "pdf"}},
)
```

### Managing Jobs

```python
# Get a job by ID
job_result = await job_manager.get_job(job_id)
job = job_result.value

# Cancel a job
await job_manager.cancel_job(job_id)

# Retry a failed job
await job_manager.retry_job(job_id)

# Get jobs by status
failed_jobs = await job_manager.get_failed_jobs(limit=10)
```

### Managing Queues

```python
# Get all queue names
queue_names = await job_manager.get_queue_names()

# Get queue length
queue_length = await job_manager.get_queue_length("emails")

# Pause a queue
await job_manager.pause_queue("emails")

# Resume a queue
await job_manager.resume_queue("emails")

# Clear a queue
await job_manager.clear_queue("emails")
```

## Advanced Usage

### Storage Backends

The system supports multiple storage backends:

```python
# In-memory storage (for development)
from uno.jobs.storage.memory import InMemoryJobStorage
storage = InMemoryJobStorage()

# Database storage (for persistence)
from uno.jobs.storage.database import DatabaseJobStorage
storage = DatabaseJobStorage()

# Redis storage (for high throughput)
from uno.jobs.storage.redis import RedisJobStorage
storage = RedisJobStorage(redis_url="redis://localhost:6379/0")
```

### Monitoring

The system includes metrics collection and health checks:

```python
from uno.jobs.monitoring.metrics import JobMetrics, JobMetricsCollector
from uno.jobs.monitoring.health import JobSystemHealthChecker

# Create metrics
metrics = JobMetrics()
metrics_collector = JobMetricsCollector(job_manager, metrics)
await metrics_collector.start()

# Create health checker
health_checker = JobSystemHealthChecker(job_manager)
await health_checker.start()

# Get metrics
all_metrics = metrics.get_metrics()

# Get health status
health_status = await health_checker.get_system_health()
```

### Administration API

The system includes a FastAPI router for administration:

```python
from fastapi import FastAPI
from uno.jobs.admin.api import router as jobs_router

app = FastAPI()
app.include_router(jobs_router)
```

## Dependency Injection

The system integrates with uno's dependency injection system:

```python
from uno.dependencies.fastapi import get_job_manager, get_job_metrics

# In a FastAPI endpoint
@app.post("/jobs")
async def create_job(job: CreateJobRequest, job_manager: JobManager = Depends(get_job_manager)):
    result = await job_manager.enqueue(
        task_name=job.task_name,
        args=job.args,
        kwargs=job.kwargs,
    )
    return {"job_id": result.value}
```

## Documentation

For more detailed information, see the component-specific documentation:
- [Job Queue](queue.md)
- [Workers](worker.md)
- [Scheduler](scheduler.md)
- [Tasks](tasks.md)
- [Storage Backends](storage.md)
- [Monitoring](monitoring.md)
- [Administration](admin.md)