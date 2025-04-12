# Scheduler

The Scheduler component manages the creation and execution of jobs on a time-based schedule.

## Overview

The Scheduler provides a flexible, reliable way to schedule recurring jobs, enabling applications to:

- Schedule periodic maintenance tasks
- Generate reports at regular intervals
- Perform daily data synchronization
- Execute future one-time tasks
- Trigger event-based job schedules

## Schedule Types

The scheduler supports several types of schedules:

### Cron Schedule

Uses cron expressions for maximum flexibility:

```python
from uno.jobs.scheduler import Scheduler, CronSchedule

scheduler = Scheduler()

# Add a task that runs at 2:30 AM every day
scheduler.schedule(
    task="maintenance.clean_old_data",
    schedule=CronSchedule("30 2 * * *")
)
```

### Interval Schedule

Runs a task at fixed time intervals:

```python
from uno.jobs.scheduler import IntervalSchedule
from datetime import timedelta

# Run every 5 minutes
scheduler.schedule(
    task="monitor.check_system_health",
    schedule=IntervalSchedule(timedelta(minutes=5))
)
```

### One-time Schedule

Executes a task once at a specific time:

```python
from uno.jobs.scheduler import OneTimeSchedule
from datetime import datetime, timezone

# Run at a specific future time
future_time = datetime.now(timezone.utc) + timedelta(hours=24)
scheduler.schedule(
    task="notifications.send_reminder",
    schedule=OneTimeSchedule(future_time)
)
```

### Daily Schedule

Runs a task at specific times each day:

```python
from uno.jobs.scheduler import DailySchedule

# Run at 9:00 AM, 1:00 PM, and 5:00 PM every day
scheduler.schedule(
    task="reports.generate_status_report",
    schedule=DailySchedule(["09:00", "13:00", "17:00"])
)
```

### Weekly Schedule

Runs a task on specific days of the week:

```python
from uno.jobs.scheduler import WeeklySchedule

# Run every Monday and Thursday at 10:00 AM
scheduler.schedule(
    task="reports.generate_weekly_report",
    schedule=WeeklySchedule(
        days=["monday", "thursday"],
        time="10:00"
    )
)
```

### Monthly Schedule

Runs a task on specific days of the month:

```python
from uno.jobs.scheduler import MonthlySchedule

# Run on the 1st and 15th of each month at noon
scheduler.schedule(
    task="accounting.process_invoices",
    schedule=MonthlySchedule(
        days=[1, 15],
        time="12:00"
    )
)
```

## Scheduler Configuration

The scheduler offers many configuration options:

```python
from uno.jobs.scheduler import Scheduler

scheduler = Scheduler(
    # Queue configuration
    queue_name="scheduled",          # Queue for scheduled jobs
    
    # Execution settings
    timezone="UTC",                  # Timezone for schedules
    check_interval=60,               # Scheduler tick interval in seconds
    
    # Reliability settings
    missed_threshold=300,            # Seconds after which a job is considered missed
    
    # Fault tolerance
    lock_timeout=300,                # Seconds until a scheduler lock expires
    
    # Observability
    metrics_enabled=True,            # Whether to collect metrics
    
    # Storage
    storage=scheduler_storage        # Storage backend
)
```

## Schedule Configuration

Each schedule can be configured with additional options:

```python
from uno.jobs.scheduler import CronSchedule

# Configure a scheduled task
scheduler.schedule(
    # Basic task information
    task="reports.generate_report",                  # Task to execute
    schedule=CronSchedule("0 9 * * 1-5"),           # Schedule definition
    
    # Task parameters
    args=["daily", "pdf"],                          # Positional arguments
    kwargs={"detailed": True},                      # Keyword arguments
    
    # Execution settings
    queue="reports",                                # Specific queue for this task
    priority="high",                                # Priority level
    
    # Time constraints
    start_date=datetime(2023, 4, 1),               # When to start scheduling
    end_date=datetime(2023, 12, 31),               # When to stop scheduling
    timezone="America/New_York",                    # Timezone for this schedule
    
    # Retry settings
    max_retries=3,                                  # Maximum retry attempts
    retry_delay=60,                                 # Seconds between retries
    
    # Identification
    tags=["report", "daily"],                       # Tags for filtering
    metadata={"department": "finance"},             # Custom metadata
    
    # Execution constraints
    timeout=300,                                    # Timeout in seconds
    unique=True,                                    # Only one instance at a time
    
    # Naming
    name="daily-finance-report"                     # Unique name for this schedule
)
```

## Managing Schedules

The scheduler provides methods for managing schedules:

### Adding a Schedule

```python
# Add a new schedule
schedule_id = await scheduler.schedule(
    task="maintenance.cleanup",
    schedule=CronSchedule("0 0 * * *")
)
```

### Getting a Schedule

```python
# Get a schedule by ID
schedule = await scheduler.get_schedule(schedule_id)

# Get a schedule by name
schedule = await scheduler.get_schedule_by_name("daily-finance-report")
```

### Updating a Schedule

```python
# Update a schedule's settings
await scheduler.update_schedule(
    schedule_id,
    schedule=CronSchedule("0 1 * * *"),  # New schedule
    args=["daily", "html"],              # New arguments
    priority="normal"                     # New priority
)
```

### Pausing a Schedule

```python
# Pause a schedule temporarily
await scheduler.pause_schedule(schedule_id)
```

### Resuming a Schedule

```python
# Resume a paused schedule
await scheduler.resume_schedule(schedule_id)
```

### Deleting a Schedule

```python
# Remove a schedule permanently
await scheduler.delete_schedule(schedule_id)
```

### Listing Schedules

```python
# List all schedules
schedules = await scheduler.list_schedules()

# List with filtering
schedules = await scheduler.list_schedules(
    status="active",
    tags=["report"]
)
```

## Scheduler Lifecycle

The scheduler has the following lifecycle:

1. **Creation**: Configure the scheduler
2. **Startup**: Initialize and start the scheduler
3. **Running**: Scheduler checks for due jobs on intervals
4. **Shutdown**: Gracefully stop the scheduler

Control the lifecycle with:

```python
# Start the scheduler
await scheduler.start()

# Pause all schedules
await scheduler.pause()

# Resume all schedules
await scheduler.resume()

# Shutdown gracefully
await scheduler.shutdown()
```

## Immediate Execution

Trigger schedules immediately, regardless of their next scheduled time:

```python
# Trigger a scheduled job right now
await scheduler.trigger_now(schedule_id)

# Trigger with specific parameters
await scheduler.trigger_now(
    schedule_id,
    args=["special-report"],
    kwargs={"urgent": True}
)
```

## Observability

The scheduler provides detailed insights into its operation:

### Getting Next Run Times

```python
# Get the next N run times for a schedule
next_runs = await scheduler.get_next_run_times(
    schedule_id,
    count=5
)
"""
[
    "2023-04-13T02:30:00Z",
    "2023-04-14T02:30:00Z",
    "2023-04-15T02:30:00Z",
    "2023-04-16T02:30:00Z",
    "2023-04-17T02:30:00Z"
]
"""
```

### Schedule Status

```python
# Get detailed schedule status
status = await scheduler.get_schedule_status(schedule_id)
"""
{
    "name": "daily-finance-report",
    "status": "active",
    "last_run": "2023-04-12T09:00:00Z",
    "last_result": "success",
    "next_run": "2023-04-13T09:00:00Z",
    "run_count": 42,
    "success_count": 40,
    "error_count": 2,
    "average_duration": 15.3
}
"""
```

### Scheduler Statistics

```python
# Get overall scheduler statistics
stats = await scheduler.get_statistics()
"""
{
    "schedules_total": 25,
    "schedules_active": 23,
    "schedules_paused": 2,
    "jobs_triggered_total": 1050,
    "jobs_triggered_last_24h": 120,
    "success_rate": 0.98,
    "scheduler_uptime": 604800,
    "missed_schedules": 0
}
"""
```

## Fault Tolerance

The scheduler is designed for fault tolerance:

### Distributed Locking

Prevents multiple scheduler instances from creating duplicate jobs:

```python
# Create a scheduler with distributed locking
from uno.jobs.storage import RedisStorage
from uno.jobs.scheduler import Scheduler

storage = RedisStorage(redis_url="redis://localhost:6379/0")
scheduler = Scheduler(
    storage=storage,
    lock_timeout=300,
    instance_id="scheduler-1"
)
```

### Missed Schedule Handling

Handles missed schedules due to downtime:

```python
# Configure missed schedule handling
scheduler = Scheduler(
    missed_threshold=300,                # Consider missed after 5 minutes
    missed_schedule_handling="trigger",  # Trigger missed schedules
    max_missed_schedules=10              # Maximum missed schedules to trigger
)
```

### Error Handling

Handles schedule execution errors:

```python
# Register error handlers
@scheduler.on_schedule_error
async def handle_schedule_error(schedule_id, exception):
    print(f"Error executing schedule {schedule_id}: {exception}")
```

## Advanced Features

### Schedule Inheritance

Create schedule templates for reuse:

```python
from uno.jobs.scheduler import ScheduleTemplate

# Create a template
daily_morning_template = ScheduleTemplate(
    schedule=CronSchedule("0 9 * * *"),
    timezone="America/New_York",
    max_retries=3,
    retry_delay=60
)

# Use the template
scheduler.schedule(
    task="reports.generate_daily_report",
    template=daily_morning_template,
    kwargs={"department": "sales"}
)
```

### Event-based Scheduling

Trigger schedules based on events:

```python
from uno.jobs.scheduler import EventTrigger

# Create an event-triggered schedule
scheduler.schedule(
    task="inventory.reorder_products",
    schedule=EventTrigger("inventory.low_stock"),
    kwargs={"threshold": 10}
)

# Trigger the schedule via an event
await scheduler.trigger_event("inventory.low_stock", {"product_id": 123})
```

### Schedule Versioning

Track changes to schedules:

```python
# Update a schedule with versioning
await scheduler.update_schedule(
    schedule_id,
    schedule=new_schedule,
    version=2,  # Current version
    changelog="Updated schedule to run at 1 AM instead of midnight"
)

# Get schedule history
history = await scheduler.get_schedule_history(schedule_id)
```