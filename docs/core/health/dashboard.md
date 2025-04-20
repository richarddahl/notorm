# Health Dashboard

The health dashboard provides a web-based interface for monitoring the health status of application components, services, dependencies, and resources.

## Overview

The health dashboard extends the health check framework with a visual monitoring interface. It provides:

1. Real-time health status visualization
2. Historical health status tracking
3. Drill-down into health check groups and individual checks
4. WebSocket-based real-time updates
5. Integration with the alerting system

## Key Components

### HealthDashboardConfig

The `HealthDashboardConfig` class configures the health dashboard:

```python
class HealthDashboardConfig(BaseModel):
    enabled: bool = True
    route_prefix: str = "/health/dashboard"
    api_prefix: str = "/health/api"
    require_auth: bool = False
    update_interval: float = 5.0  # seconds
    templates_dir: str | None = None
    static_dir: str | None = None
    history_size: int = 100  # number of historical status points to keep
    show_on_sidebar: bool = True
    auto_refresh: bool = True
```

### HealthDashboard

The `HealthDashboard` class provides the dashboard implementation:

```python
class HealthDashboard:
    def __init__(
        self,
        app: FastAPI,
        config: Optional[HealthDashboardConfig] = None,
        health_config: Optional[HealthConfig] = None,
        logger: logging.Logger | None = None,
    ): ...
    
    async def shutdown(self) -> None: ...
```

## Dashboard Features

The health dashboard provides several key features:

### Main Dashboard

The main dashboard shows:
- Overall system health status
- Status of each health check group
- Critical health checks status
- Recent status changes

### Health Groups View

The health groups view shows:
- List of all health check groups
- Status of each group
- Number of checks in each group
- Ability to trigger checks for a specific group

### Health History View

The health history view shows:
- Historical health status over time
- Timeline of status changes
- Ability to see trends and patterns in health status

### Real-time Updates

The dashboard uses WebSockets to provide real-time updates:
- Live status changes
- Automatic refreshing of health check results
- Push notifications for status changes

## Usage Examples

### Setting Up the Dashboard

```python
from fastapi import FastAPI
from uno.core.health import setup_health_dashboard, HealthDashboardConfig

app = FastAPI()

# Configure the dashboard
dashboard_config = HealthDashboardConfig(
    enabled=True,
    route_prefix="/monitoring/health",
    api_prefix="/monitoring/health/api",
    require_auth=True,
    update_interval=10.0,
    history_size=200,
    auto_refresh=True
)

# Setup the dashboard
dashboard = setup_health_dashboard(
    app=app,
    config=dashboard_config
)
```

### Accessing the Dashboard

Once set up, the dashboard can be accessed at the configured route prefix:

```
http://your-server/monitoring/health
```

The dashboard provides several views:

- Main Dashboard: `/monitoring/health`
- Groups View: `/monitoring/health/groups`
- History View: `/monitoring/health/history`

### API Endpoints

The dashboard provides several API endpoints:

```
GET /monitoring/health/api/status - Get current health status
GET /monitoring/health/api/report - Get detailed health report
GET /monitoring/health/api/history - Get health status history
GET /monitoring/health/api/groups - Get health check groups
GET /monitoring/health/api/groups/{group} - Get details for a specific group

POST /monitoring/health/api/trigger - Trigger all health checks
POST /monitoring/health/api/groups/{group}/trigger - Trigger checks for a specific group
```

### WebSocket Connection

The dashboard provides a WebSocket endpoint for real-time updates:

```
WS /monitoring/health/api/ws
```

The WebSocket accepts commands:
- `{"command": "trigger"}` - Trigger all health checks
- `{"command": "trigger_group", "group": "database"}` - Trigger checks for a specific group
- `{"command": "get_report"}` - Get full health report
- `{"command": "get_history"}` - Get health history
- `{"command": "get_groups"}` - Get health check groups

## Integration with Monitoring System

The health dashboard can be integrated with the broader monitoring system:

```python
from fastapi import FastAPI
from uno.core.monitoring import setup_monitoring
from uno.core.monitoring.config import MonitoringConfig
from uno.core.monitoring.dashboard import DashboardConfig
from uno.core.health import HealthConfig, HealthDashboardConfig, setup_health_dashboard

app = FastAPI()

# Setup monitoring
monitoring_config = MonitoringConfig(
    service_name="my-service",
    environment="production",
    health=HealthConfig(
        enabled=True,
        path_prefix="/health",
        include_details=True
    )
)

# Setup monitoring dashboard
dashboard_config = DashboardConfig(
    enabled=True,
    route_prefix="/monitoring/dashboard"
)

# Setup monitoring
setup_monitoring(
    app=app,
    config=monitoring_config,
    dashboard_config=dashboard_config
)

# Setup specialized health dashboard
health_dashboard_config = HealthDashboardConfig(
    enabled=True,
    route_prefix="/monitoring/health",
    api_prefix="/monitoring/health/api"
)

# Setup health dashboard
setup_health_dashboard(
    app=app,
    config=health_dashboard_config
)
```

## Customization

The health dashboard can be customized by providing template and static directories:

```python
from pathlib import Path
from fastapi import FastAPI
from uno.core.health import setup_health_dashboard, HealthDashboardConfig

app = FastAPI()

# Get custom template and static directories
templates_dir = str(Path(__file__).parent / "templates")
static_dir = str(Path(__file__).parent / "static")

# Configure the dashboard with custom directories
dashboard_config = HealthDashboardConfig(
    enabled=True,
    route_prefix="/monitoring/health",
    templates_dir=templates_dir,
    static_dir=static_dir
)

# Setup the dashboard
dashboard = setup_health_dashboard(
    app=app,
    config=dashboard_config
)
```

This allows you to provide custom HTML templates and static files (CSS, JavaScript) for the dashboard.