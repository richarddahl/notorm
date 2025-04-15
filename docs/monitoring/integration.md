# FastAPI Integration

The monitoring and observability framework provides seamless integration with FastAPI applications.

## Overview

The integration layer offers:

- Automatic middleware setup for tracing and metrics
- Pre-configured endpoints for health, metrics, and resource monitoring
- Dashboard pages for visualizing monitoring data
- Response time and error tracking
- Request/response logging

## Basic Setup

To integrate the monitoring framework with your FastAPI application:

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

## Middleware Components

The integration adds several middleware components:

### Metrics Middleware

Tracks request counts, durations, and status codes:

```python
from uno.core.monitoring.integration import MetricsMiddleware

app.add_middleware(```

MetricsMiddleware,
metrics_registry=metrics_registry,
exclude_paths=["/metrics", "/health"]
```
)
```

### Tracing Middleware

Adds distributed tracing to all requests:

```python
from uno.core.monitoring.integration import TracingMiddleware

app.add_middleware(```

TracingMiddleware,
tracer=tracer,
exclude_paths=["/metrics"]
```
)
```

### Logging Middleware

Logs request and response information:

```python
from uno.core.monitoring.integration import EventLoggingMiddleware

app.add_middleware(```

EventLoggingMiddleware,
event_logger=event_logger,
log_request_body=False,
log_response_body=False
```
)
```

## Monitoring Endpoints

The integration adds several endpoints to your application:

### Health Endpoints

```
GET /health
GET /health/live
GET /health/ready
GET /health/detailed
```

### Metrics Endpoints

```
GET /metrics
GET /metrics/prometheus
```

### Resource Monitoring Endpoints

```
GET /resources
GET /resources/{resource_id}
GET /resources/{resource_id}/metrics
```

## Custom Endpoint Configuration

Customize the endpoint paths:

```python
setup_monitoring(```

app,
health_endpoint_path="/api/health",
metrics_endpoint_path="/api/metrics",
resources_endpoint_path="/api/resources"
```
)
```

## Error Tracking

Track exceptions and error responses:

```python
from uno.core.monitoring.integration import setup_error_handling

setup_error_handling(```

app,
event_logger=event_logger,
metrics_registry=metrics_registry
```
)
```

This will:
- Log all exceptions as error events
- Track error counts in metrics
- Associate errors with the current trace

## Dashboard Integration

Add a monitoring dashboard to your application:

```python
from uno.core.monitoring.integration import setup_dashboard

setup_dashboard(```

app,
dashboard_path="/monitoring",
metrics_registry=metrics_registry,
health_registry=health_registry,
resource_monitor=resource_monitor
```
)
```

## Request Context

The integration provides access to monitoring context in request handlers:

```python
from fastapi import Request, Depends
from uno.core.monitoring.integration import get_monitoring_context

@app.get("/api/data")
async def get_data(```

request: Request,
monitoring: dict = Depends(get_monitoring_context)
```
):```

# Access the current span
span = monitoring["span"]
``````

```
```

# Add custom attributes to the span
span.set_attribute("custom.attribute", "value")
``````

```
```

# Use the event logger
event_logger = monitoring["event_logger"]
event_logger.log_event(```

event_type="DATA_ACCESS",
severity="INFO",
message="Accessing data endpoint"
```
)
``````

```
```

# Return data
return {"data": "value"}
```
```

## Application Lifecycle Integration

Integrate with application startup and shutdown:

```python
from uno.core.monitoring.integration import register_lifecycle_handlers

register_lifecycle_handlers(```

app,
metrics_registry=metrics_registry,
tracer=tracer,
resource_monitor=resource_monitor
```
)
```

This ensures that:
- Metrics exporters are initialized on startup
- Tracer providers are shut down gracefully
- Resource monitors are started and stopped properly

## OpenTelemetry Integration

The monitoring framework integrates with OpenTelemetry:

```python
from uno.core.monitoring.integration import setup_opentelemetry

setup_opentelemetry(```

service_name="my-service",
app=app,
tracer=tracer,
metrics_registry=metrics_registry,
otlp_endpoint="http://otel-collector:4317"
```
)
```

## Configuration from Environment Variables

Configure the monitoring system from environment variables:

```python
from uno.core.monitoring.integration import setup_monitoring_from_env

# Reads configuration from environment variables
setup_monitoring_from_env(app)
```

Example environment variables:
```
UNO_MONITORING_ENABLED=true
UNO_METRICS_ENABLED=true
UNO_TRACING_ENABLED=true
UNO_HEALTH_CHECKS_ENABLED=true
UNO_RESOURCE_MONITORING_ENABLED=true
UNO_OTLP_ENDPOINT=http://otel-collector:4317
UNO_PROMETHEUS_ENDPOINT=/metrics
```

## Security Considerations

The monitoring endpoints may expose sensitive information. To secure them:

```python
from fastapi import Security
from fastapi.security import APIKeyHeader
from uno.core.monitoring.integration import setup_monitoring

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):```

if api_key != "your-secret-key":```

raise HTTPException(status_code=403, detail="Invalid API Key")
```
return api_key
```

setup_monitoring(```

app,
security_dependency=verify_api_key,
secure_paths=["/metrics", "/health/detailed", "/resources"]
```
)
```

This approach ensures that monitoring data remains accessible to authorized users while protected from unauthorized access.