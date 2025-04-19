# Metrics Framework

The UNO Metrics Framework provides a comprehensive solution for collecting, tracking, and exporting application metrics with rich contextual information and integration with the logging and error handling systems.

## Overview

The metrics framework is designed to provide:

- **Structured metrics collection**: Various metric types (Counter, Gauge, Histogram, Timer) with semantic meaning
- **Context propagation**: Metrics context is maintained and can be integrated with the logging context
- **Error framework integration**: Seamless integration with the UNO error framework
- **HTTP request tracking**: Middleware for automatic tracking of HTTP requests
- **Prometheus integration**: Export metrics in Prometheus format for easy integration with monitoring systems
- **Transaction metrics**: Specialized utilities for tracking database transactions

## Key Concepts

### Metric Types

The framework provides four primary metric types:

- **Counter**: A cumulative metric that can only increase
- **Gauge**: A metric that can increase or decrease
- **Histogram**: A sample of observations for analyzing distributions
- **Timer**: A specialized metric for tracking durations

```python
from uno.core.metrics import counter, gauge, histogram, timer

# Create and use a counter
async def increment_requests():
    request_counter = await counter("requests.total", 
                                   description="Total number of requests",
                                   tags={"component": "api"})
    await request_counter.increment()

# Create and use a gauge
async def track_connections(count):
    connections_gauge = await gauge("connections.active",
                                   description="Active connections",
                                   unit="COUNT")
    await connections_gauge.set(count)

# Create and use a histogram
async def record_response_size(size):
    response_size = await histogram("response.size",
                                   description="Response size in bytes",
                                   unit="BYTES")
    await response_size.observe(size)

# Create and use a timer
async def time_operation():
    operation_timer = await timer("operation.duration",
                                 description="Operation duration",
                                 tags={"type": "background"})
    
    async with TimerContext(operation_timer):
        # Operation to time
        await perform_operation()
```

### Metrics Registry

The metrics registry is responsible for managing metrics and exporting them:

```python
from uno.core.metrics import get_metrics_registry, configure_metrics, MetricsConfig

# Configure metrics with default settings
registry = configure_metrics()

# Configure with custom settings
config = MetricsConfig(
    enabled=True,
    service_name="my-service",
    environment="production",
    export_interval=30.0,
    console_export=True,
    prometheus_export=True,
)
registry = configure_metrics(config)

# Get the global registry
registry = get_metrics_registry()
```

### Metric Decorators

You can use the `timed` decorator to automatically time function execution:

```python
from uno.core.metrics import timed

# Time a synchronous function
@timed("user_service.get_user", description="Time to retrieve user")
def get_user(user_id):
    # Function implementation
    return user

# Time an asynchronous function
@timed("user_service.create_user", description="Time to create user")
async def create_user(user_data):
    # Function implementation
    return user
```

### Context Management

You can track metrics with additional context:

```python
from uno.core.metrics import MetricsContext, with_metrics_context

# Add context directly
@with_metrics_context(component="user_service")
async def get_user(user_id):
    # All metrics in this function will include the component tag
    # ...

# Track an operation with context
async def process_order(order_id):
    async with MetricsContext("order_processing", tags={"order_type": "express"}):
        # Processing code
        # Metrics will be collected automatically
```

## Integration with HTTP

The `MetricsMiddleware` provides automatic tracking of HTTP requests:

```python
from fastapi import FastAPI
from uno.core.metrics import MetricsMiddleware

app = FastAPI()

# Add metrics middleware
app.add_middleware(
    MetricsMiddleware,
    metrics_path="/metrics",  # Prometheus endpoint
    excluded_paths=["/health"]  # Paths to exclude from metrics
)
```

## Transaction Metrics

For tracking database transactions:

```python
from uno.core.metrics import TransactionContext
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user_with_transaction(session: AsyncSession, user_data):
    async with TransactionContext(session, "create_user") as tx:
        # Execute queries
        result = await session.execute(...)
        
        # Record queries (optional, for more detailed metrics)
        await tx.record_query(rows=1)
        
        # Commit happens automatically on exit
```

## Custom Metrics Collection

For custom metrics collection patterns:

```python
from uno.core.metrics import get_metrics_registry

async def custom_metrics_collection():
    registry = get_metrics_registry()
    
    # Create custom metrics
    request_counter = await registry.get_or_create_counter(
        name="custom.requests",
        description="Custom requests counter",
        tags={"custom_tag": "value"}
    )
    
    # Increment the counter
    await request_counter.increment()
```

## Prometheus Integration

Metrics are automatically available in Prometheus format at the configured endpoint:

```python
# Example output from /metrics endpoint
# TYPE uno_http_requests_total counter
# HELP uno_http_requests_total Total number of HTTP requests
uno_http_requests_total{method="GET",path="/api/users"} 42
```

## Best Practices

1. **Use semantic naming**: Follow a consistent naming convention for metrics
2. **Include relevant tags**: Add service, environment, and component tags to metrics
3. **Use appropriate metric types**: Choose the right metric type for what you're measuring
4. **Avoid high cardinality tags**: Limit the number of possible values for tags
5. **Integrate with tracing**: Include trace IDs in metrics for correlation
6. **Monitor metric collection**: Watch for performance impacts from excessive metrics
7. **Document metric meanings**: Provide clear descriptions for all metrics

## Migration from Legacy Metrics

If you're currently using the legacy metrics module (`uno.core.monitoring.metrics`), here's how to migrate:

```python
# Legacy usage
from uno.core.monitoring import (
    Counter, Gauge, Histogram, Timer,
    get_metrics_registry, MetricsMiddleware
)

# New usage
from uno.core.metrics import (
    Counter, Gauge, Histogram, Timer,
    get_metrics_registry, MetricsMiddleware,
    configure_metrics, MetricsConfig
)
```

The new module maintains API compatibility while providing enhanced functionality and integration with the logging and error frameworks.