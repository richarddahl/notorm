# Jobs API Reference

This document provides a comprehensive reference for the Jobs API endpoints, following the domain-driven design approach. It includes detailed information about request and response formats, authentication requirements, and integration examples.

## Overview

The Jobs API provides functionality for managing background processing tasks, including:

- Creating and managing jobs
- Creating and managing schedules for recurring jobs
- Managing job queues
- Viewing registered tasks

## Authentication

All endpoints require authentication. Include a valid JWT token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Base URL

All endpoints are prefixed with `/api/v1`.

## Job Endpoints

### List Jobs

Retrieves a list of jobs with filtering and pagination.

```
GET /api/v1/jobs
```

**Query Parameters:**

- `queue_name` (optional): Filter by queue name
- `status` (optional): Filter by job status (can be multiple values)
- `priority` (optional): Filter by priority level
- `tags` (optional): Filter by tags
- `worker_id` (optional): Filter by worker ID
- `limit` (optional): Maximum number of jobs to return (default: 100)
- `offset` (optional): Number of jobs to skip (default: 0)
- `order_by` (optional): Field to order by (default: "created_at")
- `order_dir` (optional): Order direction (default: "desc")

**Response:**

```json
{
  "items": [
    {
      "id": "job-123",
      "task_name": "process_data",
      "args": [42, "test"],
      "kwargs": {"format": "json"},
      "queue_name": "default",
      "priority": "normal",
      "status": "completed",
      "scheduled_at": "2023-06-15T10:00:00Z",
      "created_at": "2023-06-15T09:55:00Z",
      "started_at": "2023-06-15T10:00:05Z",
      "completed_at": "2023-06-15T10:00:10Z",
      "result": {"processed": 42},
      "error": null,
      "retry_count": 0,
      "max_retries": 3,
      "retry_delay": 60,
      "tags": ["data", "processing"],
      "metadata": {"source": "api"},
      "worker_id": "worker-1",
      "timeout": 300,
      "version": "1.0",
      "duration": 5.0
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10,
  "pages": 5
}
```

### Get Job

Retrieves a specific job by ID.

```
GET /api/v1/jobs/{job_id}
```

**Path Parameters:**

- `job_id` (required): The ID of the job to retrieve

**Response:** `JobViewDto` (See above for structure)

### Create Job

Creates a new job.

```
POST /api/v1/jobs
```

**Request Body:**

```json
{
  "task_name": "process_data",
  "args": [42, "test"],
  "kwargs": {"format": "json"},
  "queue_name": "default",
  "priority": "normal",
  "scheduled_at": "2023-06-15T10:00:00Z",
  "max_retries": 3,
  "retry_delay": 60,
  "timeout": 300,
  "tags": ["data", "processing"],
  "metadata": {"source": "api"},
  "version": "1.0",
  "job_id": "custom-job-id"  // Optional
}
```

**Response:** `JobViewDto`

### Cancel Job

Cancels a job if it hasn't started yet.

```
POST /api/v1/jobs/{job_id}/cancel
```

**Path Parameters:**

- `job_id` (required): The ID of the job to cancel

**Request Body:**

```json
{
  "reason": "User-initiated cancellation"  // Optional
}
```

**Response:** `JobViewDto`

### Retry Job

Retries a failed job.

```
POST /api/v1/jobs/{job_id}/retry
```

**Path Parameters:**

- `job_id` (required): The ID of the job to retry

**Response:** `JobViewDto`

### Run Job Synchronously

Runs a job synchronously and waits for the result.

```
POST /api/v1/jobs/run-sync
```

**Request Body:**

```json
{
  "task_name": "process_data",
  "args": [42, "test"],
  "kwargs": {"format": "json"},
  "queue_name": "default",
  "priority": "normal",
  "timeout": 300,
  "metadata": {"source": "api"},
  "version": "1.0"
}
```

**Response:** Any (The result of the task execution)

### Get Job Statistics

Retrieves statistics about jobs.

```
GET /api/v1/jobs/stats
```

**Response:**

```json
{
  "total_jobs": 100,
  "pending_jobs": 10,
  "running_jobs": 5,
  "completed_jobs": 75,
  "failed_jobs": 8,
  "cancelled_jobs": 2,
  "avg_wait_time": 2.5,
  "avg_run_time": 10.2,
  "by_queue": {
    "default": {
      "total_jobs": 80,
      "pending_jobs": 8
    },
    "reports": {
      "total_jobs": 20,
      "pending_jobs": 2
    }
  },
  "by_priority": {
    "critical": 5,
    "high": 15,
    "normal": 70,
    "low": 10
  }
}
```

## Schedule Endpoints

### List Schedules

Retrieves a list of schedules with filtering and pagination.

```
GET /api/v1/schedules
```

**Query Parameters:**

- `status` (optional): Filter by status (active/paused)
- `tags` (optional): Filter by tags
- `limit` (optional): Maximum number of schedules to return (default: 100)
- `offset` (optional): Number of schedules to skip (default: 0)

**Response:**

```json
{
  "items": [
    {
      "id": "schedule-123",
      "name": "Daily Report",
      "task_name": "generate_report",
      "status": "active",
      "cron_expression": "0 0 * * *",
      "interval": null,
      "args": ["daily"],
      "kwargs": {"format": "pdf"},
      "queue_name": "reports",
      "priority": "normal",
      "tags": ["report", "daily"],
      "metadata": {"department": "accounting"},
      "max_retries": 3,
      "retry_delay": 60,
      "timeout": 600,
      "last_run_at": "2023-06-14T00:00:00Z",
      "next_run_at": "2023-06-15T00:00:00Z",
      "created_at": "2023-06-01T10:00:00Z",
      "updated_at": "2023-06-01T10:00:00Z",
      "version": "1.0"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10,
  "pages": 1
}
```

### Get Schedule

Retrieves a specific schedule by ID.

```
GET /api/v1/schedules/{schedule_id}
```

**Path Parameters:**

- `schedule_id` (required): The ID of the schedule to retrieve

**Response:** `ScheduleViewDto` (See above for structure)

### Create Schedule

Creates a new schedule.

```
POST /api/v1/schedules
```

**Request Body:**

```json
{
  "name": "Daily Report",
  "task_name": "generate_report",
  "cron_expression": "0 0 * * *",
  "args": ["daily"],
  "kwargs": {"format": "pdf"},
  "queue_name": "reports",
  "priority": "normal",
  "tags": ["report", "daily"],
  "metadata": {"department": "accounting"},
  "max_retries": 3,
  "retry_delay": 60,
  "timeout": 600,
  "version": "1.0"
}
```

**Alternative with Interval:**

```json
{
  "name": "Hourly Check",
  "task_name": "check_status",
  "interval": {
    "hours": 1,
    "minutes": 0,
    "seconds": 0,
    "days": 0
  },
  "args": [],
  "kwargs": {},
  "queue_name": "default",
  "priority": "low",
  "tags": ["monitoring"],
  "metadata": {},
  "max_retries": 1,
  "retry_delay": 30,
  "version": "1.0"
}
```

**Response:** `ScheduleViewDto`

### Update Schedule

Updates an existing schedule.

```
PUT /api/v1/schedules/{schedule_id}
```

**Path Parameters:**

- `schedule_id` (required): The ID of the schedule to update

**Request Body:**

```json
{
  "name": "Updated Daily Report",
  "cron_expression": "0 1 * * *",
  "args": ["daily"],
  "kwargs": {"format": "excel"},
  "priority": "high",
  "tags": ["report", "daily", "important"],
  "max_retries": 5,
  "status": "active"
}
```

**Response:** `ScheduleViewDto`

### Delete Schedule

Deletes a schedule.

```
DELETE /api/v1/schedules/{schedule_id}
```

**Path Parameters:**

- `schedule_id` (required): The ID of the schedule to delete

**Response:** No content (204)

### Pause Schedule

Pauses a schedule.

```
POST /api/v1/schedules/{schedule_id}/pause
```

**Path Parameters:**

- `schedule_id` (required): The ID of the schedule to pause

**Response:** `ScheduleViewDto`

### Resume Schedule

Resumes a paused schedule.

```
POST /api/v1/schedules/{schedule_id}/resume
```

**Path Parameters:**

- `schedule_id` (required): The ID of the schedule to resume

**Response:** `ScheduleViewDto`

## Queue Endpoints

### List Queues

Retrieves a list of all queues.

```
GET /api/v1/queues
```

**Response:**

```json
{
  "items": [
    {
      "name": "default",
      "size": 10,
      "is_paused": false
    },
    {
      "name": "reports",
      "size": 5,
      "is_paused": true
    }
  ],
  "total": 2
}
```

### Pause Queue

Pauses a queue, preventing jobs from being processed.

```
POST /api/v1/queues/{queue_name}/pause
```

**Path Parameters:**

- `queue_name` (required): The name of the queue to pause

**Response:** No content (204)

### Resume Queue

Resumes a paused queue.

```
POST /api/v1/queues/{queue_name}/resume
```

**Path Parameters:**

- `queue_name` (required): The name of the queue to resume

**Response:** No content (204)

### Clear Queue

Clears all jobs from a queue.

```
POST /api/v1/queues/{queue_name}/clear
```

**Path Parameters:**

- `queue_name` (required): The name of the queue to clear

**Response:** No content (204)

## Task Endpoints

### List Tasks

Retrieves a list of all registered tasks.

```
GET /api/v1/tasks
```

**Response:**

```json
{
  "items": [
    {
      "name": "process_data",
      "description": "Process data with various options",
      "is_async": true,
      "timeout": 300,
      "max_retries": 3,
      "retry_delay": 60,
      "queue": "default",
      "version": "1.0"
    },
    {
      "name": "generate_report",
      "description": "Generate a report in various formats",
      "is_async": true,
      "timeout": 600,
      "max_retries": 2,
      "retry_delay": 120,
      "queue": "reports",
      "version": "1.0"
    }
  ],
  "total": 2
}
```

### Get Task

Retrieves a specific task by name.

```
GET /api/v1/tasks/{task_name}
```

**Path Parameters:**

- `task_name` (required): The name of the task to retrieve

**Query Parameters:**

- `version` (optional): The version of the task to retrieve

**Response:** `TaskInfoDto` (See above for structure)

## Client Integration

Here's an example of integrating with the Jobs API from a TypeScript client:

```typescript
// Job service client
class JobsClient {
  private baseUrl: string;
  private authToken: string;

  constructor(baseUrl: string, authToken: string) {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
  }

  // Common fetch method with authentication
  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.authToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(url, { ...options, headers });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API error: ${response.status}`);
    }
    
    return await response.json();
  }

  // Job methods
  async listJobs(params: {
    queue_name?: string;
    status?: string[];
    priority?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<JobListDto> {
    const queryParams = new URLSearchParams();
    
    if (params.queue_name) queryParams.set('queue_name', params.queue_name);
    if (params.status) params.status.forEach(s => queryParams.append('status', s));
    if (params.priority) queryParams.set('priority', params.priority);
    if (params.limit) queryParams.set('limit', params.limit.toString());
    if (params.offset) queryParams.set('offset', params.offset.toString());
    
    return this.fetch<JobListDto>(`/api/v1/jobs?${queryParams.toString()}`);
  }

  async getJob(jobId: string): Promise<JobViewDto> {
    return this.fetch<JobViewDto>(`/api/v1/jobs/${jobId}`);
  }

  async createJob(jobData: CreateJobDto): Promise<JobViewDto> {
    return this.fetch<JobViewDto>('/api/v1/jobs', {
      method: 'POST',
      body: JSON.stringify(jobData)
    });
  }

  async cancelJob(jobId: string, reason?: string): Promise<JobViewDto> {
    return this.fetch<JobViewDto>(`/api/v1/jobs/${jobId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  }

  async retryJob(jobId: string): Promise<JobViewDto> {
    return this.fetch<JobViewDto>(`/api/v1/jobs/${jobId}/retry`, {
      method: 'POST'
    });
  }

  async runJobSync<T>(jobData: RunSyncJobDto): Promise<T> {
    return this.fetch<T>('/api/v1/jobs/run-sync', {
      method: 'POST',
      body: JSON.stringify(jobData)
    });
  }

  // Schedule methods
  async createSchedule(scheduleData: CreateScheduleDto): Promise<ScheduleViewDto> {
    return this.fetch<ScheduleViewDto>('/api/v1/schedules', {
      method: 'POST',
      body: JSON.stringify(scheduleData)
    });
  }

  // Queue methods
  async listQueues(): Promise<QueueListDto> {
    return this.fetch<QueueListDto>('/api/v1/queues');
  }

  // Task methods
  async listTasks(): Promise<TaskListDto> {
    return this.fetch<TaskListDto>('/api/v1/tasks');
  }
}

// Usage example
async function example() {
  const client = new JobsClient('https://api.example.com', 'your-auth-token');
  
  // Create a job
  const job = await client.createJob({
    task_name: 'process_data',
    args: [42, 'test'],
    kwargs: { format: 'json' },
    priority: 'high',
    tags: ['data']
  });
  
  console.log(`Created job: ${job.id}`);
  
  // Create a recurring schedule
  const schedule = await client.createSchedule({
    name: 'Daily Report',
    task_name: 'generate_report',
    cron_expression: '0 0 * * *',
    args: ['daily'],
    kwargs: { format: 'pdf' },
    queue_name: 'reports'
  });
  
  console.log(`Created schedule: ${schedule.id}`);
}
```

## Server Integration

Here's how to integrate the Jobs API into your FastAPI application:

```python
from fastapi import FastAPI
from uno.jobs import register_jobs_endpoints
from uno.dependencies.service import configure_services

app = FastAPI()

# Configure dependencies
configure_services()

# Register jobs endpoints
endpoints = register_jobs_endpoints(
    app_or_router=app,
    path_prefix="/api/v1",
    include_auth=True
)

# You can access the registered endpoints
job_endpoints = endpoints["jobs"]
schedule_endpoints = endpoints["schedules"]
queue_endpoints = endpoints["queues"]
task_endpoints = endpoints["tasks"]
```

## Data Models

### Enums

#### PriorityEnum

- `critical`: Highest priority
- `high`: High priority
- `normal`: Normal priority (default)
- `low`: Low priority

#### StatusEnum

- `pending`: Job is waiting to be processed
- `reserved`: Job is reserved by a worker but not started
- `running`: Job is currently being processed
- `completed`: Job has been successfully completed
- `failed`: Job has failed and won't be retried
- `retrying`: Job has failed but will be retried
- `cancelled`: Job has been cancelled by user
- `timeout`: Job exceeded its timeout limit

### DTOs

#### JobBaseDto

Base DTO for job data.

| Field | Type | Description |
| ----- | ---- | ----------- |
| task_name | string | Task to execute |
| args | array | Positional arguments for task |
| kwargs | object | Keyword arguments for task |
| queue_name | string | Queue to place job in |
| priority | PriorityEnum | Job priority level |

#### CreateJobDto

DTO for creating a new job (extends JobBaseDto).

| Field | Type | Description |
| ----- | ---- | ----------- |
| scheduled_at | string (datetime) | When to execute the job (None for immediate) |
| max_retries | integer | Maximum retry attempts |
| retry_delay | integer | Delay between retries in seconds |
| timeout | integer | Timeout for job execution in seconds |
| tags | array of string | Tags for categorization |
| metadata | object | Additional metadata |
| version | string | Specific version of task to use |
| job_id | string | Specific ID for the job (generated if not provided) |

#### JobViewDto

DTO for viewing job details.

| Field | Type | Description |
| ----- | ---- | ----------- |
| id | string | Unique job identifier |
| task_name | string | Task being executed |
| args | array | Positional arguments for task |
| kwargs | object | Keyword arguments for task |
| queue_name | string | Queue the job is in |
| priority | PriorityEnum | Job priority level |
| status | StatusEnum | Current job status |
| scheduled_at | string (datetime) | When the job is scheduled to run |
| created_at | string (datetime) | When the job was created |
| started_at | string (datetime) | When the job started execution |
| completed_at | string (datetime) | When the job finished execution |
| result | any | Job execution result |
| error | JobErrorDto | Error information if job failed |
| retry_count | integer | Current retry count |
| max_retries | integer | Maximum retry attempts |
| retry_delay | integer | Delay between retries in seconds |
| tags | array of string | Tags for categorization |
| metadata | object | Additional metadata |
| worker_id | string | ID of worker processing the job |
| timeout | integer | Timeout for job execution in seconds |
| version | string | Version of task being used |
| duration | number | Duration of execution in seconds |

#### ScheduleIntervalDto

DTO for interval-based scheduling.

| Field | Type | Description |
| ----- | ---- | ----------- |
| seconds | integer | Seconds component of interval |
| minutes | integer | Minutes component of interval |
| hours | integer | Hours component of interval |
| days | integer | Days component of interval |

#### CreateScheduleDto

DTO for creating a new schedule.

| Field | Type | Description |
| ----- | ---- | ----------- |
| name | string | Name for the schedule |
| task_name | string | Task to execute |
| cron_expression | string | Cron expression for scheduling (mutually exclusive with interval) |
| interval | ScheduleIntervalDto | Interval for scheduling (mutually exclusive with cron_expression) |
| args | array | Positional arguments for task |
| kwargs | object | Keyword arguments for task |
| queue_name | string | Queue to use |
| priority | PriorityEnum | Job priority level |
| tags | array of string | Tags for categorization |
| metadata | object | Additional metadata |
| max_retries | integer | Maximum retry attempts |
| retry_delay | integer | Delay between retries in seconds |
| timeout | integer | Timeout for job execution in seconds |
| version | string | Specific version of task to use |

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded with no content to return
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a detail message explaining the error:

```json
{
  "detail": "Failed to create job: Task not found: process_data"
}
```

## Best Practices

### Creating Jobs

1. **Use appropriate priority levels**:
   - Use `critical` only for truly urgent tasks
   - Use `high` for important tasks that should run before normal ones
   - Use `normal` for most tasks
   - Use `low` for background tasks that can wait

2. **Set reasonable timeouts**:
   - Always set a timeout to prevent tasks from running indefinitely
   - Consider the expected runtime and add a buffer

3. **Configure retries appropriately**:
   - Set `max_retries` based on expected failure modes
   - Use `retry_delay` to implement backoff between attempts

### Working with Schedules

1. **Use cron expressions for complex schedules**:
   - Daily at specific time: `0 8 * * *` (8:00 AM daily)
   - Weekdays only: `0 9 * * 1-5` (9:00 AM Monday-Friday)
   - Monthly: `0 0 1 * *` (Midnight on the 1st of each month)

2. **Use intervals for simple recurring tasks**:
   - Hourly checks: `{"hours": 1}`
   - Every 15 minutes: `{"minutes": 15}`
   - Daily: `{"days": 1}`

3. **Add meaningful metadata**:
   - Include information about who created the schedule
   - Document the purpose of the schedule
   - Use tags for categorization and filtering