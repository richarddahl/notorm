# Resource Management

The Uno framework includes a comprehensive resource management system for handling connection pooling, lifecycle management, health monitoring, and circuit breaking. This system ensures that application resources are properly managed throughout their lifecycle, providing robustness and reliability.

## Core Components

### Resource Registry

The `ResourceRegistry` provides centralized tracking and management of resources:

```python
from uno.core.resources import get_resource_registry

# Get the global registry
registry = get_resource_registry()

# Register a resource
await registry.register("my_resource", resource)

# Get a resource
resource = await registry.get("my_resource")

# Unregister a resource
await registry.unregister("my_resource")

# Close all resources
await registry.close()
```

### Connection Pool

The `ConnectionPool` provides efficient resource pooling with health checking:

```python
from uno.core.resources import ConnectionPool

# Create a pool
pool = ConnectionPool(```

name="db_pool",
factory=create_connection,  # async function that creates a connection
close_func=close_connection,  # async function that closes a connection
validate_func=validate_connection,  # async function that validates a connection
max_size=10,  # maximum pool size
min_size=2,   # minimum pool size (maintain this many)
max_idle=5,   # maximum idle connections
```
)

# Start the pool
await pool.start()

# Get a connection from the pool
conn = await pool.acquire()

# Use the connection
# ...

# Return the connection to the pool
await pool.release(conn)

# Close the pool when done
await pool.close()
```

### Circuit Breaker

The `CircuitBreaker` prevents cascading failures when external services fail:

```python
from uno.core.resources import CircuitBreaker

# Create a circuit breaker
circuit = CircuitBreaker(```

name="api_circuit",
failure_threshold=5,  # open after 5 failures
recovery_timeout=30.0,  # wait 30 seconds before trying again
```
)

# Use the circuit breaker
async def call_api():```

# The actual API call
return await api_client.get("/endpoint")
```

# Call through the circuit breaker
try:```

result = await circuit(call_api)
```
except CircuitBreakerOpenError:```

# Circuit is open, handle accordingly
result = fallback_value()
```
```

### Resource Monitor

The `ResourceMonitor` tracks resource health and usage:

```python
from uno.core.resource_monitor import get_resource_monitor, ResourceHealth

# Get the monitor
monitor = get_resource_monitor()

# Start monitoring
await monitor.start()

# Get metrics for all resources
metrics = await monitor.get_metrics()

# Get health summary
health = await monitor.get_health_summary()

# Get health of a specific resource
resource_health = await monitor.get_resource_health("db_pool")
```

### Resource Manager

The `ResourceManager` integrates with the application lifecycle:

```python
from uno.core.resource_management import get_resource_manager

# Get the manager
manager = get_resource_manager()

# Initialize
await manager.initialize()

# Add lifecycle hooks
manager.add_startup_hook(my_startup_function)
manager.add_shutdown_hook(my_shutdown_function)

# Create database pools
pools = await manager.create_database_pools()

# Create session factory
session_factory = await manager.create_session_factory()
```

## Context Managers

The framework provides several context managers for safe resource handling:

```python
from uno.core.resource_management import (```

managed_connection_pool, 
managed_background_task
```
)

# Managed connection pool
async with managed_connection_pool("api_pool", create_pool) as pool:```

# Pool is automatically registered and started
# Use the pool...
# It will be automatically closed and unregistered
```

# Managed background task
async with managed_background_task(```

"monitor_task", 
monitoring_function,
restart_on_failure=True
```
) as task:```

# Task is automatically registered and started
# It will be automatically stopped and unregistered
```
```

## Database Integration

Resource management is deeply integrated with the database layer:

```python
from uno.database.pooled_session import pooled_async_session

# Use a pooled database session
async with pooled_async_session() as session:```

# Session uses a connection from the pool
# with circuit breaker protection
result = await session.execute("SELECT 1")
```
    
# Session and connection automatically cleaned up
```

Advanced transaction coordination:

```python
from uno.database.pooled_session import PooledSessionOperationGroup

# Coordinate multiple database operations
async with PooledSessionOperationGroup() as op_group:```

# Create a session
session = await op_group.create_session()
``````

```
```

# Run operations in a transaction
results = await op_group.run_in_transaction(```

session,
[operation1, operation2, operation3]
```
)
``````

```
```

# Run operations concurrently
task1 = await op_group.run_operation(session, operation1)
task2 = await op_group.run_operation(session, operation2)
``````

```
```

# All sessions are automatically closed
```
```

## FastAPI Integration

Integration with FastAPI for resource management:

```python
from fastapi import FastAPI
from uno.core.fastapi_integration import (```

setup_resource_management,
create_health_endpoint,
create_resource_monitoring_endpoints,
db_session_dependency,
```
)

# Create app
app = FastAPI()

# Set up resource management
setup_resource_management(app)

# Add health endpoint
create_health_endpoint(app)

# Add resource monitoring endpoints
create_resource_monitoring_endpoints(app)

# Use session dependency
@app.get("/data")
async def get_data(session = Depends(db_session_dependency)):```

# Session uses a connection from the pool
result = await session.execute("SELECT * FROM data")
return {"data": result.fetchall()}
```
```

## Key Features

### Lifecycle Management

Resources go through a well-defined lifecycle:

1. **Registration**: Resources are registered with the resource registry
2. **Initialization**: Resources are initialized and started
3. **Usage**: Resources are acquired, used, and released
4. **Monitoring**: Resources are monitored for health and performance
5. **Cleanup**: Resources are properly closed and unregistered

### Health Monitoring

Resources are constantly monitored for health:

- **Health Status**: `HEALTHY`, `DEGRADED`, `UNHEALTHY`, or `UNKNOWN`
- **Health Checks**: Custom health checks can be registered
- **Metrics Collection**: Usage statistics are collected
- **Reporting**: Health summary available via API

### Connection Pooling

Efficient connection pooling:

- **Pooled Connections**: Database connections are pooled for efficiency
- **Validation**: Connections are validated to ensure they're working
- **Scaling**: Pools automatically scale based on demand
- **Idle Management**: Idle connections are closed to free resources

### Circuit Breaking

Robust circuit breaking for external services:

- **Failure Threshold**: Circuit opens after consecutive failures
- **Recovery**: Circuit transitions to half-open to test recovery
- **Fallback**: Alternative paths can be taken when circuit is open

### FastAPI Integration

Seamless integration with FastAPI:

- **Middleware**: Resource management middleware for request handling
- **Health Endpoints**: Built-in health check endpoints
- **Dependencies**: Session dependency for controllers
- **Lifecycle Hooks**: Event handlers for startup/shutdown

## Best Practices

### Connection Management

Use the highest-level API for your use case:

1. For most cases, use the session context manager:
   ```python
   async with pooled_async_session() as session:```

   # Use session
```
   ```

2. For advanced cases with multiple operations, use the operation group:
   ```python
   async with PooledSessionOperationGroup() as group:```

   session = await group.create_session()```
```

   # Use session
``` with coordinated operations
   ```

3. Manual pool management is also available:
   ```python
   engine_factory = PooledAsyncEngineFactory()
   pool = await engine_factory.create_engine_pool(config)
   engine = await pool.acquire()
   # Use engine
   await pool.release(engine)
   ```

### Resource Lifecycle

Follow proper resource lifecycle patterns:

1. Use context managers to ensure proper cleanup:
   ```python
   async with managed_connection_pool("name", factory) as pool:```

   # Use pool
```
   ```

2. Register long-lived resources with the registry:
   ```python
   registry = get_resource_registry()
   await registry.register("name", resource)
   # Later when finished:
   await registry.unregister("name")
   ```

3. Use the resource manager for application lifecycle:
   ```python
   manager = get_resource_manager()
   manager.add_startup_hook(initialize_resources)
   manager.add_shutdown_hook(cleanup_resources)
   ```

### Health Monitoring

Implement proper health checks:

1. Set up resource monitoring:
   ```python
   monitor = get_resource_monitor()
   await monitor.start()
   ```

2. Register custom health checks:
   ```python
   await monitor.register_health_check(```

   "my_resource", 
   lambda: check_resource_health()
```
   )
   ```

3. Check health in your application:
   ```python
   health = await monitor.get_health_summary()
   if health["overall_health"] != "HEALTHY":```

   # Handle degraded or unhealthy status
```
   ```

### Circuit Breaking

Use circuit breakers for external services:

1. Create a circuit breaker:
   ```python
   circuit = CircuitBreaker(```

   name="service_circuit",
   failure_threshold=5,
   recovery_timeout=30.0,
```
   )
   ```

2. Register with the registry:
   ```python
   await registry.register("service_circuit", circuit)
   ```

3. Use the circuit breaker:
   ```python
   try:```

   result = await circuit(call_service)
```
   except CircuitBreakerOpenError:```

   # Handle open circuit case
   result = fallback_value()
```
   ```

## Integration with Other Components

The resource management system integrates with other Uno framework components:

- **Async-First Architecture**: Uses the enhanced async utilities for robust async operations
- **Database Layer**: Enhanced database connections with pooling and circuit breaking
- **API Layer**: FastAPI integration for health monitoring and resource management
- **Event System**: Resource lifecycle events for monitoring and management
- **Configuration**: Resource configuration from application settings