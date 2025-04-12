# Monitoring Examples

This guide provides practical examples of using the monitoring and observability framework in different scenarios.

## Complete Application Example

Here's a complete example of integrating monitoring into a FastAPI application:

```python
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Request
from typing import Dict, List, Optional

from uno.core.monitoring.metrics import MetricsRegistry, Counter, Histogram
from uno.core.monitoring.tracing import Tracer
from uno.core.monitoring.health import HealthRegistry, HealthCheck, HealthStatus
from uno.core.monitoring.events import EventLogger, EventType, EventSeverity
from uno.core.monitoring.resources import ResourceMonitor
from uno.core.monitoring.integration import setup_monitoring
from uno.core.resources import ResourceManager

# Create FastAPI app
app = FastAPI(title="Example Service")

# Initialize monitoring components
metrics_registry = MetricsRegistry()
tracer = Tracer()
health_registry = HealthRegistry()
event_logger = EventLogger()
resource_manager = ResourceManager()
resource_monitor = ResourceMonitor(resource_manager)

# Register metrics
request_counter = metrics_registry.create_counter(
    name="requests_total",
    description="Total number of requests",
    labels=["endpoint", "method", "status"]
)

request_duration = metrics_registry.create_histogram(
    name="request_duration_seconds",
    description="Request duration in seconds",
    labels=["endpoint", "method"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 5]
)

# Define health checks
class DatabaseHealthCheck(HealthCheck):
    async def check(self) -> HealthStatus:
        # Simulate database check
        await asyncio.sleep(0.1)
        return HealthStatus.healthy("Database is connected")

class ApiHealthCheck(HealthCheck):
    async def check(self) -> HealthStatus:
        # Simulate external API check
        try:
            # Simulate API call
            await asyncio.sleep(0.1)
            return HealthStatus.healthy("API is available")
        except Exception as e:
            return HealthStatus.unhealthy(f"API check failed: {str(e)}")

# Register health checks
health_registry.register("database", DatabaseHealthCheck())
health_registry.register("external_api", ApiHealthCheck())

# Setup monitoring
setup_monitoring(
    app,
    metrics_registry=metrics_registry,
    tracer=tracer,
    health_registry=health_registry,
    event_logger=event_logger,
    resource_monitor=resource_monitor
)

# Define a dependency to access the current span
def get_current_span(request: Request):
    return request.state.span

# Define routes
@app.get("/api/items", response_model=List[Dict])
async def get_items(span=Depends(get_current_span)):
    # Add span attributes
    span.set_attribute("items.count", 10)
    
    # Log event
    event_logger.log_event(
        event_type=EventType.USER_ACTIVITY,
        severity=EventSeverity.INFO,
        message="Getting all items",
        context={"count": 10}
    )
    
    # Record metric
    request_counter.inc(labels={"endpoint": "/api/items", "method": "GET", "status": "success"})
    
    # Return data
    return [{"id": i, "name": f"Item {i}"} for i in range(10)]

@app.get("/api/items/{item_id}", response_model=Dict)
async def get_item(item_id: int, span=Depends(get_current_span)):
    # Create child span for detailed operation
    with tracer.start_span("get_item_details", parent=span) as child_span:
        child_span.set_attribute("item.id", item_id)
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # Record metric
        request_counter.inc(labels={"endpoint": "/api/items/{item_id}", "method": "GET", "status": "success"})
        
        # Log event
        event_logger.log_event(
            event_type=EventType.USER_ACTIVITY,
            severity=EventSeverity.INFO,
            message=f"Getting item {item_id}",
            context={"item_id": item_id}
        )
        
        # Return data
        if item_id < 100:
            return {"id": item_id, "name": f"Item {item_id}", "description": "A sample item"}
        else:
            # Record error metric
            request_counter.inc(labels={"endpoint": "/api/items/{item_id}", "method": "GET", "status": "error"})
            
            # Log error event
            event_logger.log_event(
                event_type=EventType.SYSTEM_ERROR,
                severity=EventSeverity.ERROR,
                message=f"Item {item_id} not found",
                context={"item_id": item_id}
            )
            
            raise HTTPException(status_code=404, detail="Item not found")

# Start the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Database Operations Monitoring

Monitor database operations:

```python
from uno.core.monitoring.metrics import Timer
from uno.core.monitoring.tracing import tracer

# Create a timer for database operations
db_timer = metrics_registry.create_timer(
    name="database_operation_duration",
    description="Duration of database operations",
    labels=["operation", "table"]
)

async def execute_query(query: str, params: dict = None, table: str = None):
    # Start timing the operation
    with db_timer.time(labels={"operation": "query", "table": table or "unknown"}):
        # Create a span for the query
        with tracer.start_span("database_query") as span:
            span.set_attribute("db.statement", query)
            span.set_attribute("db.params", str(params))
            span.set_attribute("db.table", table or "unknown")
            
            try:
                # Execute the query
                result = await db.execute(query, params)
                
                # Record success
                span.set_status("OK")
                return result
            except Exception as e:
                # Record error
                span.set_status("ERROR", description=str(e))
                span.record_exception(e)
                
                # Log error event
                event_logger.log_exception(
                    exception=e,
                    event_type=EventType.SYSTEM_ERROR,
                    message="Database query failed",
                    context={"query": query, "table": table}
                )
                
                # Re-raise the exception
                raise
```

## External API Client Monitoring

Monitor external API calls:

```python
import aiohttp
from uno.core.monitoring.tracing import tracer, extract_context, inject_context
from uno.core.monitoring.metrics import Counter, Histogram

# Create metrics
api_request_counter = metrics_registry.create_counter(
    name="api_requests_total",
    description="Total number of API requests",
    labels=["endpoint", "method", "status"]
)

api_request_duration = metrics_registry.create_histogram(
    name="api_request_duration_seconds",
    description="API request duration in seconds",
    labels=["endpoint", "method"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 5, 10]
)

class MonitoredApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
    
    async def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        
        # Start a span for this request
        with tracer.start_span(f"http_request_{method.lower()}") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            
            # Inject tracing context into headers
            headers = kwargs.get("headers", {})
            inject_context(span, headers)
            kwargs["headers"] = headers
            
            start_time = time.time()
            try:
                # Make the request
                async with self.session.request(method, url, **kwargs) as response:
                    # Record duration
                    duration = time.time() - start_time
                    api_request_duration.observe(
                        duration,
                        labels={"endpoint": path, "method": method}
                    )
                    
                    # Record response attributes
                    span.set_attribute("http.status_code", response.status)
                    
                    # Record success or failure
                    status = "success" if response.status < 400 else "error"
                    api_request_counter.inc(
                        labels={"endpoint": path, "method": method, "status": status}
                    )
                    
                    # Set span status
                    if response.status < 400:
                        span.set_status("OK")
                    else:
                        span.set_status("ERROR", f"HTTP status {response.status}")
                    
                    # Return response data
                    content = await response.json()
                    return content
            except Exception as e:
                # Record error
                duration = time.time() - start_time
                api_request_duration.observe(
                    duration,
                    labels={"endpoint": path, "method": method}
                )
                
                api_request_counter.inc(
                    labels={"endpoint": path, "method": method, "status": "exception"}
                )
                
                # Record error in span
                span.set_status("ERROR", str(e))
                span.record_exception(e)
                
                # Log error event
                event_logger.log_exception(
                    exception=e,
                    event_type=EventType.INTEGRATION_ERROR,
                    message="API request failed",
                    context={"url": url, "method": method}
                )
                
                # Re-raise the exception
                raise
    
    async def get(self, path: str, **kwargs):
        return await self.request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs):
        return await self.request("POST", path, **kwargs)
    
    async def close(self):
        await self.session.close()
```

## Background Task Monitoring

Monitor background tasks:

```python
import asyncio
from uno.core.monitoring.tracing import Tracer
from uno.core.monitoring.metrics import Counter, Gauge
from uno.core.monitoring.events import EventLogger, EventType, EventSeverity

# Create metrics
task_counter = metrics_registry.create_counter(
    name="background_tasks_total",
    description="Total number of background tasks",
    labels=["task", "status"]
)

active_tasks = metrics_registry.create_gauge(
    name="background_tasks_active",
    description="Number of active background tasks",
    labels=["task"]
)

class TaskMonitor:
    def __init__(self, tracer: Tracer, event_logger: EventLogger):
        self.tracer = tracer
        self.event_logger = event_logger
    
    async def run_task(self, task_name: str, task_func, *args, **kwargs):
        # Increment active tasks
        active_tasks.inc(labels={"task": task_name})
        
        # Create a span for this task
        with self.tracer.start_span(f"background_task.{task_name}") as span:
            span.set_attribute("task.name", task_name)
            
            # Log task start
            self.event_logger.log_event(
                event_type=EventType.SYSTEM_EVENT,
                severity=EventSeverity.INFO,
                message=f"Starting background task: {task_name}",
                context={"task": task_name, "args": str(args), "kwargs": str(kwargs)}
            )
            
            try:
                # Run the task
                start_time = time.time()
                result = await task_func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success
                task_counter.inc(labels={"task": task_name, "status": "success"})
                
                # Log task completion
                self.event_logger.log_event(
                    event_type=EventType.SYSTEM_EVENT,
                    severity=EventSeverity.INFO,
                    message=f"Completed background task: {task_name}",
                    context={"task": task_name, "duration": duration}
                )
                
                # Set span attributes
                span.set_attribute("task.duration", duration)
                span.set_status("OK")
                
                return result
            except Exception as e:
                # Record failure
                task_counter.inc(labels={"task": task_name, "status": "error"})
                
                # Record error in span
                span.set_status("ERROR", str(e))
                span.record_exception(e)
                
                # Log error event
                self.event_logger.log_exception(
                    exception=e,
                    event_type=EventType.SYSTEM_ERROR,
                    message=f"Background task failed: {task_name}",
                    context={"task": task_name}
                )
                
                # Re-raise the exception
                raise
            finally:
                # Decrement active tasks
                active_tasks.dec(labels={"task": task_name})

# Usage example
task_monitor = TaskMonitor(tracer, event_logger)

async def process_data(data_id: str):
    # Task implementation
    await asyncio.sleep(1)
    return {"processed": True, "data_id": data_id}

# Run the task with monitoring
result = await task_monitor.run_task("process_data", process_data, "data-123")
```

## Custom Health Check Implementation

Implement custom health checks:

```python
from uno.core.monitoring.health import HealthCheck, HealthStatus

class RedisHealthCheck(HealthCheck):
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    async def check(self) -> HealthStatus:
        try:
            # Check Redis connectivity
            ping_result = await self.redis_client.ping()
            if ping_result:
                # Check memory usage
                info = await self.redis_client.info("memory")
                used_memory = info["used_memory"]
                used_memory_peak = info["used_memory_peak"]
                memory_fragmentation_ratio = info["mem_fragmentation_ratio"]
                
                # Define thresholds
                memory_warning_threshold = 0.8  # 80% of peak
                frag_warning_threshold = 1.5
                
                # Calculate status
                if used_memory > used_memory_peak * memory_warning_threshold:
                    return HealthStatus.degraded(
                        "Redis memory usage high",
                        data={
                            "used_memory_human": info["used_memory_human"],
                            "used_memory_peak_human": info["used_memory_peak_human"],
                            "memory_usage_percentage": used_memory / used_memory_peak
                        }
                    )
                elif memory_fragmentation_ratio > frag_warning_threshold:
                    return HealthStatus.degraded(
                        "Redis memory fragmentation high",
                        data={
                            "fragmentation_ratio": memory_fragmentation_ratio
                        }
                    )
                else:
                    return HealthStatus.healthy(
                        "Redis is healthy",
                        data={
                            "used_memory_human": info["used_memory_human"],
                            "used_memory_peak_human": info["used_memory_peak_human"],
                            "fragmentation_ratio": memory_fragmentation_ratio
                        }
                    )
            else:
                return HealthStatus.unhealthy("Redis ping failed")
        except Exception as e:
            return HealthStatus.unhealthy(f"Redis health check failed: {str(e)}")

# Register the health check
redis_client = get_redis_client()
health_registry.register("redis", RedisHealthCheck(redis_client))
```

## Resource Monitor for Connection Pools

Monitor connection pools:

```python
from uno.core.monitoring.resources import ResourceTypeMonitor
from uno.core.resources import ResourceManager

class ConnectionPoolMonitor(ResourceTypeMonitor):
    def __init__(self, resource_manager: ResourceManager):
        super().__init__(resource_manager, resource_type="connection_pool")
    
    def setup_metrics(self):
        self.add_metric(
            name="connections_total",
            description="Total number of connections in the pool",
            metric_type="gauge",
            labels=["pool_name", "pool_type"]
        )
        self.add_metric(
            name="connections_active",
            description="Number of active connections",
            metric_type="gauge",
            labels=["pool_name", "pool_type"]
        )
        self.add_metric(
            name="connections_idle",
            description="Number of idle connections",
            metric_type="gauge",
            labels=["pool_name", "pool_type"]
        )
        self.add_metric(
            name="connections_max",
            description="Maximum number of connections",
            metric_type="gauge",
            labels=["pool_name", "pool_type"]
        )
        self.add_metric(
            name="checkout_time",
            description="Time to checkout a connection",
            metric_type="histogram",
            labels=["pool_name", "pool_type"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
        )
    
    async def collect_metrics(self, resource):
        # Get pool stats
        stats = await resource.get_stats()
        
        # Update metrics
        self.update_metric(
            "connections_total",
            stats["total_connections"],
            labels={"pool_name": resource.name, "pool_type": resource.pool_type}
        )
        self.update_metric(
            "connections_active",
            stats["active_connections"],
            labels={"pool_name": resource.name, "pool_type": resource.pool_type}
        )
        self.update_metric(
            "connections_idle",
            stats["idle_connections"],
            labels={"pool_name": resource.name, "pool_type": resource.pool_type}
        )
        self.update_metric(
            "connections_max",
            stats["max_connections"],
            labels={"pool_name": resource.name, "pool_type": resource.pool_type}
        )
    
    def setup_health_check(self, resource):
        # Define threshold-based health check
        def check_health():
            stats = resource.get_stats_sync()
            total = stats["total_connections"]
            max_conn = stats["max_connections"]
            usage_ratio = total / max_conn if max_conn > 0 else 0
            
            if usage_ratio > 0.9:
                return HealthStatus.degraded(
                    f"Connection pool {resource.name} near capacity",
                    data={
                        "usage_ratio": usage_ratio,
                        "active_connections": stats["active_connections"],
                        "total_connections": total,
                        "max_connections": max_conn
                    }
                )
            elif usage_ratio > 0.7:
                return HealthStatus.degraded(
                    f"Connection pool {resource.name} high usage",
                    data={
                        "usage_ratio": usage_ratio,
                        "active_connections": stats["active_connections"],
                        "total_connections": total,
                        "max_connections": max_conn
                    }
                )
            else:
                return HealthStatus.healthy(
                    f"Connection pool {resource.name} healthy",
                    data={
                        "usage_ratio": usage_ratio,
                        "active_connections": stats["active_connections"],
                        "total_connections": total,
                        "max_connections": max_conn
                    }
                )
        
        return check_health

# Register the monitor
pool_monitor = ConnectionPoolMonitor(resource_manager)
resource_monitor.register_type_monitor(pool_monitor)
```

These examples demonstrate how to use the monitoring and observability framework in various real-world scenarios, providing practical guidance for implementation.