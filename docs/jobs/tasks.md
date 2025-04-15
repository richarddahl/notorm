# Tasks

The Tasks component defines the work to be executed by the background processing system.

## Overview

Tasks are the building blocks of the background processing system, representing the actual work to be performed. The task system provides:

- A simple way to define and register tasks
- Type safety and validation for task parameters
- Configuration options for execution behavior
- Support for both synchronous and asynchronous tasks
- Middleware for cross-cutting concerns

## Defining Tasks

Tasks can be defined in several ways:

### Using the Task Decorator

The simplest way to define a task:

```python
from uno.jobs.tasks import task

@task
async def process_upload(file_id: str, options: dict = None) -> dict:```

"""Process an uploaded file.
``````

```
```

Args:```

file_id: ID of the file to process
options: Processing options
```
    
Returns:```

Processing results
```
"""
options = options or {}
# Implementation details...
return {"status": "processed", "file_id": file_id}
```
```

### With Task Configuration

Add configuration options:

```python
@task(```

name="process_upload",                 # Custom task name
max_retries=3,                         # Maximum retry attempts
retry_delay=60,                        # Seconds between retries
timeout=300,                           # Timeout in seconds
queue="uploads",                       # Default queue name
priority="high",                       # Default priority
description="Process an uploaded file"  # Task description
```
)
async def process_upload(file_id: str, options: dict = None) -> dict:```

# Implementation details...
pass
```
```

### Using Task Classes

For more complex tasks with shared behavior:

```python
from uno.jobs.tasks import Task

class ProcessingTask(Task):```

# Default configuration
max_retries = 3
retry_delay = 60
queue = "processing"
``````

```
```

# Shared behavior
async def validate_input(self, *args, **kwargs):```

# Input validation
pass
```
``````

```
```

async def report_result(self, result):```

# Report or post-process results
pass
```
```

@task(base=ProcessingTask)
async def process_image(image_id: str, format: str = "jpg") -> dict:```

# Implementation details...
pass
```

@task(base=ProcessingTask)
async def process_video(video_id: str, resolution: str = "hd") -> dict:```

# Implementation details...
pass
```
```

### Synchronous Tasks

For CPU-bound operations:

```python
@task(asynchronous=False)
def compute_statistics(data_set_id: str) -> dict:```

"""Compute statistics for a data set.
``````

```
```

This task is CPU-bound, so it's defined as synchronous.
"""
# CPU-intensive computation...
return {"mean": 10.5, "median": 9.2, "std_dev": 2.1}
```
```

## Task Registry

Tasks are tracked in a central registry:

```python
from uno.jobs.tasks import TaskRegistry

# Get all registered tasks
all_tasks = TaskRegistry.get_all_tasks()

# Get a specific task by name
upload_task = TaskRegistry.get_task("process_upload")

# Check if a task exists
if TaskRegistry.has_task("process_upload"):```

# Do something with the task
pass
```
```

### Manual Registration

Tasks can be manually registered:

```python
# Register a function as a task
async def notify_user(user_id: str, message: str):```

# Implementation details...
pass
```

TaskRegistry.register(```

notify_user, 
name="notify_user",
max_retries=2
```
)
```

## Task Configuration Options

Tasks offer many configuration options:

### Retry Settings

Configure how tasks handle failures:

```python
@task(```

max_retries=3,                # Maximum retry attempts
retry_delay=60,               # Seconds between retries
retry_backoff=True,           # Use exponential backoff
retry_backoff_factor=2,       # Backoff multiplier
retry_jitter=True,            # Add random jitter to retry delay
retry_for_exceptions=[        # Only retry for these exceptions```

ConnectionError,
TimeoutError
```
]
```
)
async def external_api_call(endpoint: str, data: dict) -> dict:```

# Implementation details...
pass
```
```

### Timeout Settings

Prevent tasks from running too long:

```python
@task(```

timeout=300,                  # 5 minute timeout
timeout_action="terminate"    # Kill the task if it exceeds timeout
```
)
async def long_running_process(job_id: str) -> dict:```

# Implementation details...
pass
```
```

### Queue Settings

Control which queue and priority to use:

```python
@task(```

queue="reports",              # Default queue
priority="normal"             # Default priority
```
)
async def generate_report(report_type: str) -> dict:```

# Implementation details...
pass
```
```

### Uniqueness

Prevent duplicate task execution:

```python
@task(```

unique=True,                     # Only one instance can run at a time
unique_key=lambda id: f"user:{id}"  # Custom unique key function
```
)
async def process_user_data(user_id: str) -> dict:```

# This task will only run once per user_id concurrently
pass
```
```

### Resource Limits

Limit resource usage:

```python
@task(```

max_memory="512MB",           # Maximum memory usage
cpu_limit=0.5                 # Maximum CPU usage (fraction of a core)
```
)
async def resource_intensive_task(data_id: str) -> dict:```

# Implementation details...
pass
```
```

## Task Dependencies

Tasks can depend on other tasks:

### Chaining Tasks

Execute tasks in sequence:

```python
from uno.jobs.tasks import chain

# Define tasks
@task
async def process_image(image_id: str) -> dict:```

# Process the image
return {"processed_image_id": f"proc_{image_id}"}
```

@task
async def generate_thumbnail(processed_image_id: str) -> dict:```

# Generate thumbnail
return {"thumbnail_id": f"thumb_{processed_image_id}"}
```

@task
async def update_metadata(thumbnail_id: str, processed_image_id: str) -> dict:```

# Update metadata
return {"status": "complete"}
```

# Chain the tasks
image_processing_workflow = chain(```

process_image,
generate_thumbnail,
update_metadata
```
)

# Execute the chain
await queue.enqueue(```

task=image_processing_workflow,
args=["image_123"]
```
)
```

### Task Groups

Execute tasks in parallel:

```python
from uno.jobs.tasks import group

# Define tasks
@task
async def resize_image(image_id: str, size: str) -> dict:```

# Resize the image
return {"resized_id": f"{image_id}_{size}"}
```

# Create a group to resize in multiple dimensions
resize_group = group(```

[resize_image.s("image_123", "small"),
 resize_image.s("image_123", "medium"),
 resize_image.s("image_123", "large")]
```
)

# Execute the group
await queue.enqueue(task=resize_group)
```

### Complex Workflows

Combine chains and groups:

```python
from uno.jobs.tasks import chain, group

workflow = chain(```

process_image.s("image_123"),
group([```

resize_image.s("small"),
resize_image.s("medium"),
resize_image.s("large")
```
]),
update_metadata.s()
```
)

await queue.enqueue(task=workflow)
```

## Task Context

Tasks can access contextual information:

```python
@task
async def task_with_context(data_id: str) -> dict:```

# Access the job context
from uno.jobs.context import get_current_job
job = get_current_job()
``````

```
```

# Access job information
job_id = job.id
enqueued_at = job.created_at
``````

```
```

# Access task metadata
metadata = job.metadata
user_id = metadata.get("user_id")
``````

```
```

# Implementation details...
return {"status": "complete"}
```
```

## Task Middleware

Middleware allows cross-cutting concerns:

```python
from uno.jobs.middleware import TaskMiddleware

class LoggingMiddleware(TaskMiddleware):```

async def before_task(self, task_func, args, kwargs, job):```

print(f"Starting task {task_func.__name__} with args={args}, kwargs={kwargs}")
return args, kwargs
```
``````

```
```

async def after_task(self, task_func, args, kwargs, result, job):```

print(f"Completed task {task_func.__name__} with result={result}")
return result
```
``````

```
```

async def on_error(self, task_func, args, kwargs, error, job):```

print(f"Error in task {task_func.__name__}: {error}")
return error
```
```

# Register globally
from uno.jobs.tasks import register_middleware
register_middleware(LoggingMiddleware())

# Or register for a specific task
@task(middleware=[LoggingMiddleware()])
async def monitored_task(data_id: str) -> dict:```

# Implementation details...
pass
```
```

## Task Versioning

Handle task definition changes:

```python
# Version 1
@task(name="process_data", version="1.0")
async def process_data_v1(data_id: str) -> dict:```

# Original implementation
pass
```

# Version 2 with new parameter
@task(name="process_data", version="2.0")
async def process_data_v2(data_id: str, options: dict = None) -> dict:```

# New implementation
pass
```

# Enqueue with version
await queue.enqueue(```

task="process_data",
args=["data_123"],
version="2.0"
```
)
```

## Task Discovery

The system can automatically discover tasks:

```python
from uno.jobs.tasks import discover_tasks

# Discover tasks in a module
discover_tasks("myapp.tasks")

# Discover tasks in multiple modules
discover_tasks(["myapp.tasks.reports", "myapp.tasks.processing"])

# Discover tasks with a pattern
discover_tasks("myapp.tasks.*")
```

## Error Handling

Tasks can define custom error handling:

```python
@task
async def task_with_error_handling(data_id: str) -> dict:```

try:```

# Implementation details...
return {"status": "complete"}
```
except ConnectionError as e:```

# Handle connection errors specifically
logging.error(f"Connection error: {str(e)}")
raise  # Re-raise for automatic retry
```
except Exception as e:```

# Handle other errors
logging.error(f"Unexpected error: {str(e)}")
return {"status": "error", "message": str(e)}
```
```
```

## Task Hooks

Define hooks for additional task behavior:

```python
@task
async def task_with_hooks(data_id: str) -> dict:```

# Implementation details...
return {"status": "complete"}
```

@task_with_hooks.on_success
async def handle_success(job, result):```

print(f"Task succeeded with result: {result}")
```

@task_with_hooks.on_failure
async def handle_failure(job, error):```

print(f"Task failed with error: {error}")
```

@task_with_hooks.on_retry
async def handle_retry(job, error, retry_count):```

print(f"Task being retried ({retry_count}) after error: {error}")
```
```

## Testing Tasks

The system provides utilities for testing tasks:

```python
from uno.jobs.testing import test_task

# Test a task function
result = await test_task(```

process_upload,
args=["file_123"],
kwargs={"options": {"format": "pdf"}}
```
)
assert result["status"] == "processed"

# Test with mocked dependencies
with patch("external_service.api_call") as mock_api:```

mock_api.return_value = {"success": True}
result = await test_task(external_api_task, args=["endpoint_1"])
assert result["status"] == "success"
```
```