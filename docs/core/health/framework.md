# Health Check Framework

The health check framework provides a comprehensive system for monitoring the health and status of application components, services, dependencies, and resources.

## Overview

Health checks are essential for monitoring and maintaining the reliability of complex applications. The health check framework in Uno provides:

1. A standardized way to define and register health checks
2. A central registry for managing and aggregating health statuses
3. Configurable health check policies and timeouts
4. FastAPI integration for health check endpoints
5. Integration with resource monitoring
6. Context propagation across async boundaries

## Key Components

### HealthStatus

The `HealthStatus` enum represents the possible states of a service or component:

```python
class HealthStatus(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()
```

### HealthCheckResult

The `HealthCheckResult` class represents the result of a health check with status, message, details, and timing information:

```python
class HealthCheckResult(BaseModel):
    status: HealthStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    check_duration_ms: Optional[float] = None
```

### HealthCheck

The `HealthCheck` class represents an individual health check with timeout handling and caching:

```python
class HealthCheck:
    def __init__(
        self,
        name: str,
        check_func: Callable[[], Awaitable[HealthCheckResult]],
        timeout: float = 5.0,
        description: str | None = None,
        tags: list[str] | None = None,
        critical: bool = False,
        group: str | None = None,
    ): ...
```

### HealthRegistry

The `HealthRegistry` class manages health checks and provides aggregated health status:

```python
class HealthRegistry:
    async def register(self, check: HealthCheck) -> None: ...
    async def unregister(self, check_id: str) -> None: ...
    async def check_all(self, force: bool = False) -> Dict[str, HealthCheckResult]: ...
    async def check_group(self, group: str, force: bool = False) -> Dict[str, HealthCheckResult]: ...
    async def get_status(self, force: bool = False) -> HealthStatus: ...
    async def get_health_report(self, force: bool = False) -> Dict[str, Any]: ...
```

### HealthEndpoint

The `HealthEndpoint` class provides FastAPI integration for health checking:

```python
class HealthEndpoint:
    @staticmethod
    def create_router(
        prefix: str = "/health",
        tags: list[str] = ["health"],
        include_details: bool = True,
    ) -> APIRouter: ...
    
    @staticmethod
    def setup(
        app: FastAPI,
        prefix: str = "/health",
        tags: list[str] = ["health"],
        include_details: bool = True,
        register_resource_checks: bool = True,
    ) -> None: ...
```

## Usage Examples

### Basic Health Check

```python
from uno.core.health import health_check, HealthStatus, HealthCheckResult

# Simple decorator approach
@health_check(
    name="database_connection",
    description="Checks if database connection is healthy",
    tags=["database", "critical"],
    critical=True,
    group="database"
)
async def check_database_connection():
    try:
        # Check database connection
        await database.ping()
        return True  # Will be converted to HealthCheckResult
    except Exception as e:
        return False  # Will be converted to HealthCheckResult
```

### Custom Health Check Result

```python
from uno.core.health import health_check, HealthStatus, HealthCheckResult

@health_check(
    name="redis_connection",
    description="Checks Redis connection and performance",
    tags=["cache", "redis"],
    group="cache"
)
async def check_redis_connection():
    try:
        # Perform Redis check
        start_time = time.time()
        await redis.ping()
        latency_ms = (time.time() - start_time) * 1000
        
        # Determine status based on latency
        status = HealthStatus.HEALTHY
        if latency_ms > 100:
            status = HealthStatus.DEGRADED
        
        return HealthCheckResult(
            status=status,
            message=f"Redis connection is {status.name.lower()}",
            details={"latency_ms": latency_ms}
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Redis connection failed: {str(e)}",
            details={"error": str(e)}
        )
```

### Manual Health Check Registration

```python
from uno.core.health import register_health_check, HealthStatus, HealthCheckResult

async def check_external_api():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.example.com/health") as response:
                if response.status == 200:
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        message="External API is available"
                    )
                else:
                    return HealthCheckResult(
                        status=HealthStatus.DEGRADED,
                        message=f"External API returned status {response.status}",
                        details={"status_code": response.status}
                    )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"External API is unavailable: {str(e)}",
            details={"error": str(e)}
        )

# Register the health check
check_id = await register_health_check(
    name="external_api",
    check_func=check_external_api,
    description="Checks if external API is available",
    tags=["api", "external"],
    timeout=3.0,
    group="external"
)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from uno.core.health import HealthEndpoint

app = FastAPI()

# Setup health check endpoints
HealthEndpoint.setup(
    app=app,
    prefix="/health",
    tags=["monitoring", "health"],
    include_details=True,
    register_resource_checks=True
)
```

### Getting Health Status

```python
from uno.core.health import get_health_registry, get_health_status

# Get the overall health status
status = await get_health_status()
if status != HealthStatus.HEALTHY:
    print(f"System is {status.name}")
    
# Get detailed health report
registry = get_health_registry()
report = await registry.get_health_report()
print(f"Overall status: {report['status']}")
print(f"Total checks: {report['checks_total']}")
```

### Health Check Groups

```python
from uno.core.health import get_health_registry

# Get registry
registry = get_health_registry()

# Check a specific group
database_status = await registry.get_group_status("database")
if database_status != HealthStatus.HEALTHY:
    print(f"Database group is {database_status.name}")
    
# Run all checks in a group
results = await registry.check_group("cache", force=True)
for check_id, result in results.items():
    print(f"Check {check_id}: {result.status.name} - {result.message}")
```

## Integration with Resource Monitoring

The health check framework integrates with the resource monitoring system to provide health checks for system resources:

```python
from uno.core.health import get_health_registry

# Add resource checks
registry = get_health_registry()
await registry.add_resource_checks()

# Get resource health
resource_health = await registry.get_resource_health()
print(f"Resource health: {resource_health['overall_health']}")
```

## Health Context Propagation

The health check framework provides a context variable for propagating health information across async boundaries:

```python
from uno.core.health import health_context

# Get health context
context = health_context.get()
status = context.get("health_status")
if status:
    print(f"Current health status: {status.name}")
```

## Configuration

The health check framework can be configured using the `HealthConfig` class:

```python
from uno.core.health import HealthConfig, get_health_registry

# Create custom configuration
config = HealthConfig(
    enabled=True,
    path_prefix="/system/health",
    include_details=True,
    register_resource_checks=True,
    cache_ttl=60,
    check_timeout=5.0,
    include_in_context=True,
    alerting_enabled=True,
    dashboard_enabled=True,
    log_health_checks=True
)

# Create registry with custom configuration
registry = HealthRegistry(config=config)
```