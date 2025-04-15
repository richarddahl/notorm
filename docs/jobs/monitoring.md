# Job System Monitoring

The uno Background Processing System includes comprehensive monitoring capabilities to help you track system health, performance, and job execution metrics.

## Overview

Monitoring is critical for production deployments to ensure:

- System health and reliability
- Resource utilization and bottlenecks
- Job execution performance
- Early detection of issues

The monitoring subsystem provides:
1. Metrics collection and reporting
2. Health checks and status monitoring
3. System event logging

## Metrics Collection

The `JobMetrics` class collects and manages metrics for the background processing system, providing visibility into job execution and system performance.

### Available Metrics

The following metrics are tracked:

#### Counter Metrics
- `job_enqueued`: Number of jobs enqueued (labels: queue, task, priority)
- `job_started`: Number of jobs started (labels: queue, task, worker)
- `job_completed`: Number of jobs completed successfully (labels: queue, task, worker)
- `job_failed`: Number of jobs that failed (labels: queue, task, worker, error_type)
- `job_retry`: Number of job retries (labels: queue, task)
- `job_cancelled`: Number of jobs cancelled (labels: queue, task)

#### Gauge Metrics
- `queue_length`: Number of jobs in queue (labels: queue, status)
- `worker_busy`: Number of busy workers (labels: worker_type)
- `worker_idle`: Number of idle workers (labels: worker_type)

#### Histogram Metrics
- `execution_time`: Job execution time in seconds (labels: queue, task)
- `wait_time`: Job wait time in seconds (labels: queue, task, priority)

### Usage

```python
from uno.jobs.monitoring.metrics import JobMetrics, JobMetricsCollector

# Create metrics
metrics = JobMetrics()

# Record metrics manually
metrics.record_job_enqueued(queue="default", task="email", priority="HIGH")
metrics.record_execution_time(queue="default", task="email", seconds=1.5)

# Or use the built-in collector
collector = JobMetricsCollector(job_manager, metrics)
await collector.start()

# Get all metrics
all_metrics = metrics.get_metrics()
```

## Health Checks

The health check system monitors the operational status of the job system components and provides alerts for degraded or unhealthy conditions.

### Available Health Checks

- `JobQueueHealthCheck`: Monitors queue length, failed jobs, and stalled jobs
- `WorkerHealthCheck`: Monitors worker activity and processing status
- `SchedulerHealthCheck`: Monitors scheduler activity and schedule processing
- `JobSystemHealthChecker`: Manages and aggregates all health checks

### Health Status Levels

- `HEALTHY`: Component is operating normally
- `DEGRADED`: Component is functioning but experiencing issues
- `UNHEALTHY`: Component is not functioning properly

### Usage

```python
from uno.jobs.monitoring.health import JobSystemHealthChecker

# Create health checker
health_checker = JobSystemHealthChecker(job_manager)
await health_checker.start()

# Get system health
health_status = await health_checker.get_system_health()

# Health status contains:
# - Overall status (healthy, degraded, unhealthy)
# - Status message
# - Individual check results
# - Timestamp
```

## Integration with Application Monitoring

The job system monitoring can be integrated with your application's existing monitoring system:

### Prometheus Integration

```python
from uno.core.monitoring.metrics import PrometheusMetricsExporter

# Create exporter
exporter = PrometheusMetricsExporter(metrics_manager=job_metrics.metrics_manager)

# Export metrics
prometheus_metrics = exporter.export_metrics()
```

### Health API Integration

```python
from fastapi import FastAPI
from uno.jobs.admin.api import router as jobs_router

app = FastAPI()
app.include_router(jobs_router)

# The /jobs/health endpoint provides health check status
# The /jobs/metrics endpoint provides metrics data
```

## Alerting

You can set up alerts based on health checks and metrics:

```python
from uno.core.monitoring.alerts import AlertManager
from uno.jobs.monitoring.health import JobSystemHealthChecker

# Create alerting system
alert_manager = AlertManager()

# Add alert for unhealthy job system
alert_manager.add_alert(```

name="job_system_unhealthy",
condition=lambda: health_checker.get_system_health().status != "healthy",
message="Job system is not healthy",
severity="critical",
```
)

# Start alert monitoring
await alert_manager.start_monitoring()
```

## Performance Monitoring

The metrics system includes specific performance-focused metrics:

- Execution time histograms show processing time distribution
- Wait time histograms show queue delay distribution
- Queue length gauges show backlog size

Use these metrics to identify:
- Slow tasks that might need optimization
- Queue bottlenecks that might need more workers
- Resource constraints that might need addressing

## Logging

The job system integrates with Python's logging system:

```python
import logging
from uno.jobs.manager import JobManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uno.jobs")

# Create job manager with logger
job_manager = JobManager(```

storage=storage,
logger=logger,
```
)
```

Important events that are logged include:
- Job lifecycle events (enqueued, started, completed, failed)
- Worker lifecycle events (started, stopped)
- Scheduler events (schedule triggered, job created)
- Error conditions and exceptions

## Best Practices

1. **Regular Monitoring**: Check metrics and health status regularly
2. **Alert on Critical Issues**: Set up alerts for unhealthy status and high failure rates
3. **Monitor Queue Lengths**: Large queues may indicate worker capacity issues
4. **Track Error Rates**: Sudden increases in failures may indicate systemic problems
5. **Performance Trending**: Track execution times to catch performance degradation
6. **Resource Usage**: Monitor worker utilization to balance capacity
7. **Stalled Jobs**: Configure monitoring for hung or stalled jobs