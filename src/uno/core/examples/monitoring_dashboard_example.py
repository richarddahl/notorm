"""
Example showing how to use the monitoring dashboard.

This example demonstrates:
1. Setting up a FastAPI application with monitoring
2. Creating custom health checks
3. Registering custom metrics
4. Launching the monitoring dashboard
"""

import asyncio
import random
import time
from fastapi import FastAPI, Depends
from pydantic import BaseModel

from uno.core.monitoring.config import MonitoringConfig
from uno.core.monitoring.integration import setup_monitoring
from uno.core.monitoring.dashboard import DashboardConfig
from uno.core.monitoring.health import (
    register_health_check, HealthStatus, HealthCheckResult
)
from uno.core.monitoring.metrics import (
    counter, gauge, histogram, timer
)
from uno.core.monitoring.events import (
    get_event_logger, EventLevel, EventType
)
from uno.core.resource_monitor import get_resource_monitor


# Define a Pydantic model for our API endpoint
class Item(BaseModel):
    name: str
    price: float


# Create a FastAPI application
app = FastAPI(title="Monitoring Dashboard Example")


# Create some health checks
async def check_database():
    """Example database health check."""
    # Simulate a database check
    if random.random() < 0.9:  # 90% chance of success
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            details={"connection_pool": "main", "query_time_ms": random.uniform(1.0, 5.0)}
        )
    else:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Database connection failed",
            details={"error": "Connection timeout"}
        )


async def check_cache():
    """Example cache health check."""
    # Simulate a cache check
    if random.random() < 0.95:  # 95% chance of success
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Cache connection successful",
            details={"node": "cache-01", "latency_ms": random.uniform(0.5, 2.0)}
        )
    else:
        return HealthCheckResult(
            status=HealthStatus.DEGRADED,
            message="Cache connection degraded",
            details={"warning": "High latency"}
        )


async def check_external_api():
    """Example external API health check."""
    # Simulate an external API check
    if random.random() < 0.85:  # 85% chance of success
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="External API connection successful",
            details={"endpoint": "api.example.com", "response_time_ms": random.uniform(50.0, 200.0)}
        )
    else:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="External API connection failed",
            details={"error": "HTTP 503 Service Unavailable"}
        )


# API routes for the example
@app.get("/")
async def read_root():
    """Root endpoint."""
    # Increment request counter
    req_counter = await counter("http_requests_total", 
                              description="Total HTTP requests",
                              tags={"endpoint": "/"})
    await req_counter.increment()
    
    # Simulate processing time
    start_time = time.time()
    await asyncio.sleep(random.uniform(0.01, 0.05))
    duration = (time.time() - start_time) * 1000  # Convert to ms
    
    # Record response time
    resp_timer = await timer("http_response_time",
                           description="HTTP response time in milliseconds",
                           tags={"endpoint": "/"})
    await resp_timer.record(duration)
    
    # Log event
    event_logger = get_event_logger()
    await event_logger.info(
        name="request_processed",
        message=f"Request processed in {duration:.2f}ms",
        event_type=EventType.TECHNICAL,
        data={"endpoint": "/", "duration_ms": duration}
    )
    
    return {"message": "Welcome to the Monitoring Dashboard Example"}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """Get item by ID."""
    # Increment request counter
    req_counter = await counter("http_requests_total", 
                              description="Total HTTP requests",
                              tags={"endpoint": "/items/{item_id}"})
    await req_counter.increment()
    
    # Simulate processing time
    start_time = time.time()
    await asyncio.sleep(random.uniform(0.05, 0.2))
    duration = (time.time() - start_time) * 1000  # Convert to ms
    
    # Record response time
    resp_timer = await timer("http_response_time",
                           description="HTTP response time in milliseconds",
                           tags={"endpoint": "/items/{item_id}"})
    await resp_timer.record(duration)
    
    # Simulate errors for some requests
    if random.random() < 0.05:  # 5% chance of error
        error_counter = await counter("http_errors_total", 
                                   description="Total HTTP errors",
                                   tags={"endpoint": "/items/{item_id}"})
        await error_counter.increment()
        
        # Log event
        event_logger = get_event_logger()
        await event_logger.error(
            name="item_not_found",
            message=f"Item {item_id} not found",
            event_type=EventType.BUSINESS,
            data={"item_id": item_id}
        )
        
        return {"error": "Item not found"}
    
    # Log event
    event_logger = get_event_logger()
    await event_logger.info(
        name="item_retrieved",
        message=f"Item {item_id} retrieved",
        event_type=EventType.BUSINESS,
        data={"item_id": item_id, "duration_ms": duration}
    )
    
    return {"item_id": item_id, "name": f"Item {item_id}", "price": random.uniform(10.0, 100.0)}


@app.post("/items/")
async def create_item(item: Item):
    """Create a new item."""
    # Increment request counter
    req_counter = await counter("http_requests_total", 
                              description="Total HTTP requests",
                              tags={"endpoint": "/items/"})
    await req_counter.increment()
    
    # Simulate processing time
    start_time = time.time()
    await asyncio.sleep(random.uniform(0.1, 0.3))
    duration = (time.time() - start_time) * 1000  # Convert to ms
    
    # Record response time
    resp_timer = await timer("http_response_time",
                           description="HTTP response time in milliseconds",
                           tags={"endpoint": "/items/"})
    await resp_timer.record(duration)
    
    # Increment items counter
    items_counter = await counter("items_created_total", 
                                description="Total items created")
    await items_counter.increment()
    
    # Set price gauge
    price_gauge = await gauge("item_price",
                            description="Item price",
                            tags={"name": item.name})
    await price_gauge.set(item.price)
    
    # Record price in histogram
    price_hist = await histogram("item_price_distribution",
                               description="Distribution of item prices")
    await price_hist.observe(item.price)
    
    # Log event
    event_logger = get_event_logger()
    await event_logger.info(
        name="item_created",
        message=f"Item {item.name} created with price ${item.price:.2f}",
        event_type=EventType.BUSINESS,
        data={"name": item.name, "price": item.price}
    )
    
    # Generate a random ID for the new item
    item_id = random.randint(1000, 9999)
    return {"item_id": item_id, **item.dict()}


# Background task to simulate system activity
async def simulate_activity():
    """Background task to simulate system activity."""
    # Get metrics
    cpu_gauge = await gauge("system_cpu",
                          description="CPU usage percentage")
    memory_gauge = await gauge("system_memory",
                             description="Memory usage percentage")
    
    # Event logger
    event_logger = get_event_logger()
    
    while True:
        # Update CPU and memory gauges with simulated values
        cpu_value = random.uniform(10.0, 90.0)
        memory_value = random.uniform(20.0, 80.0)
        
        await cpu_gauge.set(cpu_value)
        await memory_gauge.set(memory_value)
        
        # Log warnings for high resource usage
        if cpu_value > 80.0:
            await event_logger.warning(
                name="high_cpu_usage",
                message=f"High CPU usage detected: {cpu_value:.1f}%",
                event_type=EventType.TECHNICAL,
                data={"cpu": cpu_value}
            )
        
        if memory_value > 70.0:
            await event_logger.warning(
                name="high_memory_usage",
                message=f"High memory usage detected: {memory_value:.1f}%",
                event_type=EventType.TECHNICAL,
                data={"memory": memory_value}
            )
        
        # Wait before next update
        await asyncio.sleep(5)


# Setup application
@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    # Configure monitoring
    config = MonitoringConfig(
        service_name="monitoring-example",
        environment="development"
    )
    
    # Configure dashboard
    dashboard_config = DashboardConfig(
        enabled=True,
        route_prefix="/monitoring/dashboard",
        api_prefix="/monitoring/api",
        update_interval=2.0  # Update every 2 seconds for the demo
    )
    
    # Set up monitoring with dashboard
    setup_monitoring(app, config, dashboard_config)
    
    # Register health checks
    await register_health_check(
        name="database",
        check_func=check_database,
        description="Checks database connectivity",
        tags=["database", "critical"]
    )
    
    await register_health_check(
        name="cache",
        check_func=check_cache,
        description="Checks cache connectivity",
        tags=["cache"]
    )
    
    await register_health_check(
        name="external_api",
        check_func=check_external_api,
        description="Checks external API connectivity",
        tags=["external"]
    )
    
    # Start background task
    asyncio.create_task(simulate_activity())
    
    # Start resource monitor
    monitor = get_resource_monitor()
    await monitor.start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)