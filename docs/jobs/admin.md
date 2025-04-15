# Job System Administration

The Uno Background Processing System provides a comprehensive administration API that enables managing jobs, queues, workers, and schedules through a RESTful interface.

## Overview

The administration API allows you to:

- Monitor job execution and system status
- Manage jobs (create, cancel, retry)
- Control queues (pause, resume, clear)
- View worker status
- Manage schedules (create, enable, disable, delete)
- Access system metrics and health checks

## API Routes

The administration API is implemented as a FastAPI router that can be integrated into your application.

### Setup

```python
from fastapi import FastAPI
from uno.jobs.admin.api import router as jobs_router

app = FastAPI()
app.include_router(jobs_router)
```

## Endpoints

### System Information

#### GET /jobs/info
Returns overall system information including worker count, queue count, schedule count, and health status.

```json
{
  "worker_count": 4,
  "queue_count": 3,
  "schedule_count": 5,
  "total_jobs": 127,
  "health_status": "healthy"
}
```

#### GET /jobs/health
Returns detailed health check information for all components of the job system.

```json
{
  "status": "healthy",
  "message": "Job system is healthy",
  "checks": {```

"worker_worker1": {
  "status": "healthy",
  "message": "Worker is healthy",
  "details": {```

"jobs_processed": 45,
"uptime_seconds": 3600
```
  }
},
"scheduler": {
  "status": "healthy",
  "message": "Scheduler is healthy",
  "details": {```

"schedules_processed": 12
```
  }
}
```
  },
  "timestamp": "2025-04-12T10:15:30.123456"
}
```

#### GET /jobs/metrics
Returns collected metrics for the job system.

```json
{
  "metrics": {```

"uno_jobs.job_enqueued": {
  "type": "counter",
  "values": [```

{
  "labels": {"queue": "default", "task": "email", "priority": "HIGH"},
  "value": 56
}
```
  ]
},
"uno_jobs.queue_length": {
  "type": "gauge",
  "values": [```

{
  "labels": {"queue": "default", "status": "pending"},
  "value": 12
}
```
  ]
}
```
  },
  "timestamp": "2025-04-12T10:15:30.123456"
}
```

### Queue Management

#### GET /jobs/queues
Returns a list of all queues with their status and job counts.

```json
[
  {```

"name": "default",
"length": 5,
"jobs_by_status": [
  {"status": "PENDING", "count": 5},
  {"status": "RUNNING", "count": 2},
  {"status": "COMPLETED", "count": 45},
  {"status": "FAILED", "count": 3}
]
```
  }
]
```

#### GET /jobs/queues/{queue_name}
Returns detailed information about a specific queue.

#### POST /jobs/queues/{queue_name}/clear
Clears all pending jobs from a queue.

```json
{
  "success": true,
  "jobs_cleared": 5,
  "queue_name": "default"
}
```

#### POST /jobs/queues/{queue_name}/pause
Pauses a queue, preventing jobs from being processed.

```json
{
  "success": true,
  "queue_name": "default",
  "status": "paused"
}
```

#### POST /jobs/queues/{queue_name}/resume
Resumes a paused queue.

```json
{
  "success": true,
  "queue_name": "default",
  "status": "resumed"
}
```

### Job Management

#### GET /jobs
Returns a list of jobs with optional filtering by status and queue.

Query parameters:
- `status`: Filter by job status (e.g., PENDING, RUNNING, COMPLETED, FAILED)
- `queue_name`: Filter by queue name
- `limit`: Maximum number of jobs to return (default: 100)
- `offset`: Offset for pagination (default: 0)

```json
[
  {```

"id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
"queue_name": "default",
"status": "COMPLETED",
"task_name": "send_email",
"priority": "HIGH",
"created_at": "2025-04-12T10:00:00",
"updated_at": "2025-04-12T10:00:05",
"started_at": "2025-04-12T10:00:02",
"completed_at": "2025-04-12T10:00:05",
"retries": 0,
"max_retries": 3,
"is_scheduled": false,
"result": {"success": true, "message_id": "123456"},
"error": null,
"metadata": {"user_id": "123", "email_type": "welcome"},
"tags": ["user", "email", "onboarding"]
```
  }
]
```

#### GET /jobs/{job_id}
Returns detailed information about a specific job.

#### POST /jobs
Creates a new job.

Request body:
```json
{
  "task_name": "send_email",
  "args": ["user@example.com"],
  "kwargs": {"subject": "Welcome", "template": "welcome_email"},
  "queue_name": "emails",
  "priority": "HIGH",
  "scheduled_at": "2025-04-12T12:00:00",
  "max_retries": 3,
  "retry_delay_seconds": 60,
  "timeout_seconds": 30,
  "metadata": {"user_id": "123", "email_type": "welcome"},
  "tags": ["user", "email", "onboarding"]
}
```

Response:
```json
{
  "success": true,
  "job_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

#### POST /jobs/{job_id}/cancel
Cancels a pending job.

```json
{
  "success": true,
  "job_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "cancelled"
}
```

#### POST /jobs/{job_id}/retry
Retries a failed job.

```json
{
  "success": true,
  "job_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "pending"
}
```

### Worker Management

#### GET /workers
Returns a list of all workers with their status.

```json
[
  {```

"name": "AsyncWorker-1",
"status": "running",
"queue_names": ["default", "emails"],
"current_job_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
"jobs_processed": 45,
"is_healthy": true,
"details": {
  "concurrency": 5,
  "uptime_seconds": 3600
}
```
  }
]
```

#### GET /workers/{worker_name}
Returns detailed information about a specific worker.

### Schedule Management

#### GET /schedules
Returns a list of all schedules.

```json
[
  {```

"id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
"name": "daily_report",
"task_name": "generate_report",
"queue_name": "reports",
"schedule_type": "cron",
"next_run_at": "2025-04-13T00:00:00",
"last_run_at": "2025-04-12T00:00:00",
"enabled": true,
"created_at": "2025-04-01T00:00:00",
"updated_at": "2025-04-12T00:00:05"
```
  }
]
```

#### GET /schedules/{schedule_id}
Returns detailed information about a specific schedule.

#### POST /schedules
Creates a new schedule.

Request body:
```json
{
  "name": "daily_report",
  "task_name": "generate_report",
  "schedule_type": "cron",
  "schedule_params": {"expression": "0 0 * * *"},
  "args": ["daily"],
  "kwargs": {"format": "pdf"},
  "queue_name": "reports",
  "priority": "NORMAL",
  "max_retries": 3,
  "retry_delay_seconds": 300,
  "timeout_seconds": 600,
  "metadata": {"report_type": "daily"},
  "enabled": true
}
```

Response:
```json
{
  "success": true,
  "schedule_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

#### POST /schedules/{schedule_id}/enable
Enables a schedule.

```json
{
  "success": true,
  "schedule_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "enabled"
}
```

#### POST /schedules/{schedule_id}/disable
Disables a schedule.

```json
{
  "success": true,
  "schedule_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "disabled"
}
```

#### DELETE /schedules/{schedule_id}
Deletes a schedule.

```json
{
  "success": true,
  "schedule_id": "e3b1c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

## Dependency Injection

The administration API integrates with Uno's dependency injection system:

```python
from uno.dependencies.fastapi import get_job_manager, get_job_metrics

# Register dependencies in your container
container.register(JobManager, instance=job_manager)
container.register(JobMetrics, instance=job_metrics)

# No additional setup needed - the API router will use the DI system
app.include_router(jobs_router)
```

## Security Considerations

The administration API should be secured in production environments:

```python
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

# Create security dependency
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key: str = Security(api_key_header)):```

if api_key != "your-secret-key":```

raise HTTPException(status_code=403, detail="Invalid API key")
```
return api_key
```

# Secure the router
app.include_router(```

jobs_router,
dependencies=[Depends(get_api_key)]
```
)
```

## UI Integration

The administration API can be integrated with admin UI frameworks like:

- Swagger UI (automatic with FastAPI)
- Custom dashboards using React, Vue, or other frontend frameworks
- Admin panels like FastAPI Admin

FastAPI automatically provides Swagger documentation:

```
http://your-server/docs
```

## Command Line Tools

You can also create command-line tools that interface with the administration API:

```python
import click
import httpx

@click.group()
def cli():```

"""Command-line interface for Uno Jobs."""
pass
```

@cli.command()
def list_jobs():```

"""List all jobs."""
response = httpx.get("http://localhost:8000/jobs/jobs")
jobs = response.json()
for job in jobs:```

click.echo(f"{job['id']} - {job['task_name']} - {job['status']}")
```
```

if __name__ == "__main__":```

cli()
```
```

## Best Practices

1. **Secure the API**: Always protect the administration API in production
2. **Monitor Job Health**: Regularly check the health endpoint
3. **Limit Access**: Control who can access job management features
4. **Audit Changes**: Log all administrative actions
5. **Use Pagination**: Always use limits and offsets when listing large numbers of jobs
6. **Clean Up**: Regularly clean up old jobs to maintain database performance
7. **Track Metrics**: Use the metrics endpoint to monitor system health