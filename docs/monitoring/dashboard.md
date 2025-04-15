# Monitoring Dashboard

The Uno framework includes a comprehensive web-based monitoring dashboard that provides a unified interface for viewing health, metrics, resources, and events in your application.

## Overview

The monitoring dashboard consists of several components:

1. **Dashboard UI**: A web interface for viewing monitoring data
2. **Dashboard API**: REST API endpoints for accessing monitoring data
3. **WebSocket Updates**: Real-time updates via WebSocket connections
4. **Resource Integration**: Integration with the resource monitoring system

## Getting Started

To set up the monitoring dashboard for your FastAPI application:

```python
from fastapi import FastAPI
from uno.core.monitoring.dashboard import DashboardConfig, setup_monitoring_dashboard
from uno.core.monitoring.integration import setup_monitoring

app = FastAPI()

# Set up monitoring with dashboard
setup_monitoring(```

app,
dashboard_config=DashboardConfig(```

enabled=True,
route_prefix="/monitoring/dashboard",
api_prefix="/monitoring/api",
update_interval=5.0  # Update every 5 seconds
```
)
```
)
```

Alternatively, you can set up the dashboard separately:

```python
from uno.core.monitoring.dashboard import setup_monitoring_dashboard

# Set up monitoring first
setup_monitoring(app)

# Then set up the dashboard
setup_monitoring_dashboard(```

app,
DashboardConfig(```

enabled=True,
route_prefix="/monitoring/dashboard",
api_prefix="/monitoring/api"
```
)
```
)
```

## Dashboard Pages

The dashboard includes several pages:

- **Overview**: Main dashboard with key metrics and health status
- **Health**: Detailed health status for all checks
- **Metrics**: Visualization of application metrics
- **Resources**: Information about system and application resources
- **Events**: Log of application events

## Dashboard Configuration

The `DashboardConfig` class allows you to configure the dashboard:

```python
from uno.core.monitoring.dashboard import DashboardConfig

config = DashboardConfig(```

# Enable/disable the dashboard
enabled=True,
``````

```
```

# URL prefixes
route_prefix="/monitoring/dashboard",
api_prefix="/monitoring/api",
``````

```
```

# Security options
require_api_key=True,
api_key="your-secret-key",
``````

```
```

# Update settings
update_interval=5.0,  # Update every 5 seconds
``````

```
```

# Custom directories (optional)
templates_dir="/path/to/custom/templates",
static_dir="/path/to/custom/static"
```
)
```

## Security

The dashboard can be secured using an API key:

```python
config = DashboardConfig(```

require_api_key=True,
api_key="your-secret-key"
```
)
```

When API key security is enabled:

1. A login page is presented at the dashboard URL
2. Users must enter the correct API key to access the dashboard
3. The API key is stored in a cookie for future sessions
4. All API endpoints require the API key as a header (`X-API-Key`)

You can also set the API key via environment variable:

```bash
export UNO_DASHBOARD_API_KEY="your-secret-key"
```

## WebSocket Updates

The dashboard uses WebSocket connections to provide real-time updates. This connection is automatically established when you load the dashboard.

WebSocket messages have the following format:

```json
{
  "type": "update",
  "data": {```

"timestamp": 1649943600.123456,
"health_status": "healthy",
"resources": {
  "healthy": 10,
  "degraded": 2,
  "unhealthy": 0
},
"system": {
  "cpu": 15.2,
  "memory": 42.7
},
"http": {
  "requests": 1245,
  "response_time": 125.3
}
```
  }
}
```

## API Endpoints

The dashboard provides API endpoints for accessing monitoring data:

- `/monitoring/api/health`: Health status information
- `/monitoring/api/metrics`: Application metrics
- `/monitoring/api/resources`: Resource information
- `/monitoring/api/events`: Recent events
- `/monitoring/api/overview`: Simplified overview of all monitoring data
- `/monitoring/api/ws`: WebSocket endpoint for real-time updates

## Customization

You can customize the dashboard by providing your own templates and static files:

```python
config = DashboardConfig(```

templates_dir="/path/to/custom/templates",
static_dir="/path/to/custom/static"
```
)
```

The templates should be compatible with FastAPI's `Jinja2Templates` system and follow the same structure as the default templates.

## Integration with Alerts

The dashboard can display alerts when health checks fail or metrics exceed thresholds:

```python
from uno.core.monitoring.alerts import configure_alerts, AlertChannel

configure_alerts(```

channels=[```

AlertChannel.EMAIL("admin@example.com"),
AlertChannel.SLACK("#alerts"),
AlertChannel.WEBHOOK("https://example.com/webhook")
```
],
display_in_dashboard=True
```
)
```

## Example

Here's a complete example of setting up the monitoring dashboard with custom health checks and metrics:

```python
from fastapi import FastAPI
from uno.core.monitoring.config import MonitoringConfig
from uno.core.monitoring.dashboard import DashboardConfig
from uno.core.monitoring.integration import setup_monitoring
from uno.core.monitoring.health import register_health_check, HealthStatus, HealthCheckResult
from uno.core.monitoring.metrics import counter, gauge, timer

app = FastAPI()

# Health check for database
async def check_database():```

# Perform a simple database query
try:```

await db.execute("SELECT 1")
return HealthCheckResult(
    status=HealthStatus.HEALTHY,
    message="Database connection successful"
)
```
except Exception as e:```

return HealthCheckResult(
    status=HealthStatus.UNHEALTHY,
    message=f"Database connection failed: {str(e)}"
)
```
```

@app.on_event("startup")
async def startup_event():```

# Configure monitoring
config = MonitoringConfig(```

service_name="my-service",
environment="production"
```
)
``````

```
```

# Configure dashboard
dashboard_config = DashboardConfig(```

enabled=True,
require_api_key=True,
api_key="your-secret-key"
```
)
``````

```
```

# Set up monitoring with dashboard
setup_monitoring(app, config, dashboard_config)
``````

```
```

# Register health checks
await register_health_check(```

name="database",
check_func=check_database,
description="Checks database connectivity",
tags=["database", "critical"]
```
)
```

@app.get("/")
async def root():```

# Increment request counter
req_counter = await counter("http_requests_total")
await req_counter.increment()
``````

```
```

# Measure response time
request_timer = await timer("http_request_duration")
async with await request_timer.time():```

# Process the request
return {"message": "Hello World"}
```
```
```

For a more comprehensive example, see the `examples/monitoring_dashboard_example.py` file.

## Running the Example

To run the example:

```bash
cd src/uno/core/examples
python monitoring_dashboard_example.py
```

Then visit:

- Dashboard: http://localhost:8000/monitoring/dashboard
- API Endpoint: http://localhost:8000/
- Health Status: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics