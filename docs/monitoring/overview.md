# Monitoring and Observability

The Uno framework provides a comprehensive monitoring and observability system that helps you understand the health, performance, and behavior of your application in production.

## Overview

The monitoring and observability framework in Uno consists of five main components:

1. **Metrics Collection**: Collect numerical measurements about your application's performance and behavior.
2. **Distributed Tracing**: Track requests as they flow through your application and external services.
3. **Health Checking**: Monitor the health of your application and its dependencies.
4. **Structured Event Logging**: Record significant events with rich context.
5. **Resource Monitoring**: Track resource usage and health across your application.

## Getting Started

To set up monitoring for your FastAPI application, use the `setup_monitoring` function:

```python
from fastapi import FastAPI
from uno.core.monitoring import setup_monitoring, MonitoringConfig

app = FastAPI()

# Configure and set up monitoring
config = MonitoringConfig(
    service_name="my-service",
    environment="production"
)
setup_monitoring(app, config)
```

This will:

1. Add metrics collection with a Prometheus endpoint at `/metrics`
2. Set up distributed tracing with HTTP propagation
3. Add health check endpoints at `/health`
4. Configure structured logging
5. Set up event logging

## Monitoring Configuration

The `MonitoringConfig` class allows you to configure all aspects of the monitoring system:

```python
from uno.core.monitoring import (
    MonitoringConfig, MetricsConfig, TracingConfig,
    LoggingConfig, HealthConfig, EventsConfig
)

config = MonitoringConfig(
    service_name="my-service",
    environment="production",
    
    # Metrics configuration
    metrics=MetricsConfig(
        enabled=True,
        export_interval=60.0,
        prometheus_enabled=True,
        metrics_path="/metrics",
    ),
    
    # Tracing configuration
    tracing=TracingConfig(
        enabled=True,
        service_name="my-service",
        sampling_rate=0.1,  # Sample 10% of requests
        log_spans=False,
    ),
    
    # Health check configuration
    health=HealthConfig(
        enabled=True,
        include_details=True,
        path_prefix="/health",
    ),
    
    # Event logging configuration
    events=EventsConfig(
        enabled=True,
        min_level="INFO",
        log_events=True,
    ),
    
    # Logging configuration
    logging=LoggingConfig(
        level="INFO",
        json_format=True,
        log_to_console=True,
        include_context=True,
        include_trace_info=True,
    ),
)
```

## Additional Endpoints

To add more monitoring endpoints, use the `create_monitoring_endpoints` function:

```python
from uno.core.monitoring import create_monitoring_endpoints

create_monitoring_endpoints(
    app,
    prefix="/management",
    tags=["management"]
)
```

This adds endpoints for:

- `/management/resources`: List all resources
- `/management/resources/{name}`: Get details for a specific resource
- `/management/info`: Get runtime information

## Integration with Resource Management

The monitoring system integrates seamlessly with Uno's resource management system:

```python
from uno.core.resource_monitor import get_resource_monitor
from uno.core.monitoring import get_health_registry

# Add resource checks to health registry
health_registry = get_health_registry()
await health_registry.add_resource_checks()
```

## Next Steps

For more details on each component, see the specific documentation:

- [Metrics Collection](metrics.md)
- [Distributed Tracing](tracing.md)
- [Health Checking](health.md)
- [Structured Event Logging](events.md)
- [Resource Monitoring](resources.md)