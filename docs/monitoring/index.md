# Monitoring & Observability

The Uno framework provides a comprehensive monitoring and observability system to help you understand your application's behavior, performance, and health in production environments.

## Overview

Modern applications require robust monitoring and observability to ensure reliability and performance. The Uno monitoring framework provides:

- **Metrics Collection**: Track application performance, resource usage, and business metrics
- **Distributed Tracing**: Follow requests across service boundaries
- **Health Checking**: Monitor the health of your application and its dependencies
- **Structured Event Logging**: Record significant application events
- **Resource Monitoring**: Track resource usage and performance

## Key Features

- **Unified API**: Consistent interfaces for all monitoring components
- **OpenTelemetry Integration**: Export data to OpenTelemetry collectors
- **Prometheus Compatibility**: Native support for Prometheus metrics
- **FastAPI Integration**: Built-in middleware and endpoints
- **Low Overhead**: Minimal performance impact
- **Extensible**: Easy to add custom monitoring components

## Components

The monitoring framework consists of several integrated components:

| Component | Purpose | Documentation |
|-----------|---------|---------------|
| Metrics | Collect numerical measurements | [Metrics Documentation](metrics.md) |
| Tracing | Track request flows | [Tracing Documentation](tracing.md) |
| Health Checks | Monitor system health | [Health Checks Documentation](health.md) |
| Event Logging | Record structured events | [Event Logging Documentation](events.md) |
| Resource Monitoring | Track resource usage | [Resource Monitoring Documentation](resources.md) |

## Getting Started

To get started with the monitoring framework, add the necessary components to your FastAPI application:

```python
from fastapi import FastAPI
from uno.core.monitoring.integration import setup_monitoring
from uno.core.monitoring.metrics import MetricsRegistry
from uno.core.monitoring.health import HealthRegistry
from uno.core.monitoring.tracing import Tracer
from uno.core.monitoring.events import EventLogger
from uno.core.monitoring.resources import ResourceMonitor
from uno.core.resources import ResourceManager

# Create your FastAPI app
app = FastAPI()

# Initialize monitoring components
metrics_registry = MetricsRegistry()
health_registry = HealthRegistry()
tracer = Tracer()
event_logger = EventLogger()
resource_manager = ResourceManager()
resource_monitor = ResourceMonitor(resource_manager)

# Setup monitoring
setup_monitoring(```

app,
metrics_registry=metrics_registry,
health_registry=health_registry,
tracer=tracer,
event_logger=event_logger,
resource_monitor=resource_monitor
```
)
```

This setup will add all necessary middleware and endpoints to your application, providing immediate visibility into its behavior.

## Configuration

The monitoring system can be configured through environment variables, configuration files, or programmatically:

```python
from uno.core.monitoring.config import MonitoringConfig

config = MonitoringConfig(```

service_name="my-service",
environment="production",
metrics_enabled=True,
tracing_enabled=True,
health_checks_enabled=True,
resource_monitoring_enabled=True
```
)
```

For more details, see the [Configuration Documentation](configuration.md).

## Integration

The monitoring framework integrates with:

- **FastAPI**: Middleware and endpoints
- **OpenTelemetry**: Exporters for metrics and traces
- **Prometheus**: Native exposition format
- **Resource Management**: Monitoring of managed resources
- **Error Handling**: Integration with the Uno error system

For more details, see the [Integration Documentation](integration.md).

## Examples

Practical examples of using the monitoring framework:

- Complete FastAPI application with monitoring
- Database operation monitoring
- External API client monitoring
- Background task monitoring
- Custom health checks
- Resource monitoring

For more examples, see the [Examples Documentation](examples.md).

## Best Practices

To get the most from the monitoring framework:

1. **Use Structured Events**: Prefer structured events over unstructured logging
2. **Add Business Metrics**: Track metrics that matter to your business
3. **Define Meaningful Health Checks**: Check what's important for your application
4. **Add Tracing to Critical Paths**: Ensure visibility into performance bottlenecks
5. **Monitor Resources**: Track all critical resources

## Next Steps

- Explore the [Metrics Documentation](metrics.md) to start collecting application metrics
- Set up [Health Checks](health.md) for your application components
- Implement [Distributed Tracing](tracing.md) for request flows
- Configure [Event Logging](events.md) for significant application events
- Monitor your application's [Resources](resources.md)