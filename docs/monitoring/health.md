# Health Checks

Health checks are a critical component of any production application, providing real-time information about the status and availability of your service and its dependencies.

## Overview

The Uno framework's health check system allows you to:

- Register custom health checks for your application components
- Monitor dependent services (databases, caches, etc.)
- Aggregate health status across multiple checks
- Expose health status through HTTP endpoints
- Integrate with container orchestration systems

## Basic Usage

```python
from uno.core.monitoring.health import HealthRegistry, HealthCheck, HealthStatus

# Create a registry
registry = HealthRegistry()

# Define a simple health check
class DatabaseHealthCheck(HealthCheck):
    async def check(self) -> HealthStatus:
        try:
            # Perform a simple database query
            await db.execute("SELECT 1")
            return HealthStatus.healthy("Database connection successful")
        except Exception as e:
            return HealthStatus.unhealthy(f"Database connection failed: {str(e)}")

# Register the health check
registry.register("database", DatabaseHealthCheck())

# In your FastAPI application:
from uno.core.monitoring.integration import setup_monitoring

app = FastAPI()
setup_monitoring(app, health_registry=registry)
```

## Health Status

Health checks can report one of three statuses:

- `HEALTHY`: The component is working as expected
- `DEGRADED`: The component is working but with reduced functionality or performance
- `UNHEALTHY`: The component is not working properly

Each status can include:
- A message explaining the status
- Additional data providing context about the status
- Time when the check was performed

## Built-in Health Checks

The framework provides several built-in health checks:

- `DatabaseHealthCheck`: Verifies database connectivity
- `RedisHealthCheck`: Checks Redis connection and responsiveness
- `DiskSpaceHealthCheck`: Monitors available disk space
- `MemoryUsageHealthCheck`: Tracks memory consumption
- `ServiceHealthCheck`: Verifies connectivity to dependent services

## Custom Health Checks

Creating custom health checks is straightforward:

```python
from uno.core.monitoring.health import HealthCheck, HealthStatus

class CustomServiceHealthCheck(HealthCheck):
    def __init__(self, service_client):
        self.service_client = service_client
        
    async def check(self) -> HealthStatus:
        try:
            response = await self.service_client.ping()
            if response.status_code == 200:
                return HealthStatus.healthy("Service is responding")
            else:
                return HealthStatus.degraded(
                    f"Service returned unexpected status: {response.status_code}",
                    data={"response": response.json()}
                )
        except Exception as e:
            return HealthStatus.unhealthy(f"Service check failed: {str(e)}")
```

## Health Check Registration

Health checks can be registered with tags for organizational purposes:

```python
registry.register("payment-service", PaymentServiceHealthCheck(), 
                  tags=["external", "critical"])
```

You can then query health checks by tag:
```python
critical_checks = registry.get_checks_by_tag("critical")
```

## HTTP Endpoints

When integrated with FastAPI, the health check system exposes endpoints:

- `/health`: Overall application health status
- `/health/live`: Liveness checks (is the application running?)
- `/health/ready`: Readiness checks (is the application ready to accept requests?)
- `/health/detailed`: Detailed health information for all components

## Integration with Kubernetes

The health endpoints are designed to work with Kubernetes:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Resource Health Integration

The health check system automatically integrates with the resource management system:

```python
from uno.core.resources import ResourceManager
from uno.core.monitoring.health import ResourceHealthAdapter

# Create a resource health adapter
adapter = ResourceHealthAdapter(resource_manager)

# Register with health registry
registry.register_adapter(adapter)
```

This integration provides health information about all managed resources in your application.