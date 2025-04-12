# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example demonstrating the monitoring and observability framework.

This module shows how to use the various monitoring components including
metrics, tracing, health checks, and structured logging.
"""

import asyncio
import time
import random
import logging
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Depends, HTTPException

from uno.core.monitoring import (
    # Configuration
    MonitoringConfig, configure_monitoring,
    
    # Metrics
    counter, gauge, histogram, timer, timed, MetricUnit,
    
    # Tracing
    trace, get_current_trace_id, get_current_span_id, SpanKind,
    
    # Health
    HealthStatus, HealthCheckResult, register_health_check, get_health_status,
    
    # Events
    log_event, EventLevel, EventType,
    
    # Integration
    setup_monitoring, create_monitoring_endpoints
)
from uno.core.errors import (
    UnoError, ErrorCode, Result, Success, Failure, of, failure, from_exception,
    with_error_context, add_error_context
)


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("monitoring_example")


# Example data
ITEMS = {
    "1": {"id": "1", "name": "Item 1", "price": 10.0},
    "2": {"id": "2", "name": "Item 2", "price": 20.0},
    "3": {"id": "3", "name": "Item 3", "price": 30.0},
}


# Example service with monitoring
class ItemService:
    """Service for managing items with monitoring."""
    
    def __init__(self):
        """Initialize the service."""
        # Initialize counters
        self._setup_metrics()
    
    async def _setup_metrics(self) -> None:
        """Set up metrics for the service."""
        # Create counters
        self.get_counter = await counter(
            name="items_get_total",
            description="Total number of item get operations",
            tags={"service": "item_service"}
        )
        
        self.get_error_counter = await counter(
            name="items_get_error_total",
            description="Total number of item get errors",
            tags={"service": "item_service"}
        )
        
        # Create gauges
        self.items_count = await gauge(
            name="items_count",
            description="Number of items in the store",
            unit=MetricUnit.COUNT,
            tags={"service": "item_service"}
        )
        
        # Set initial count
        await self.items_count.set(len(ITEMS))
        
        # Create histograms
        self.item_price = await histogram(
            name="item_price",
            description="Distribution of item prices",
            unit=MetricUnit.NONE,
            tags={"service": "item_service"}
        )
        
        # Record initial prices
        for item in ITEMS.values():
            await self.item_price.observe(item["price"])
        
        # Create timers
        self.get_duration = await timer(
            name="items_get_duration",
            description="Duration of item get operations",
            tags={"service": "item_service"}
        )
    
    @trace(name="get_item", kind=SpanKind.INTERNAL)
    @with_error_context
    async def get_item(self, item_id: str) -> Result[Dict[str, Any]]:
        """
        Get an item by ID.
        
        Args:
            item_id: ID of the item to get
            
        Returns:
            Result containing the item or an error
        """
        # Add context for error handling and tracing
        add_error_context(item_id=item_id, operation="get_item")
        
        # Start timing
        async with await self.get_duration.time():
            # Increment counter
            await self.get_counter.increment()
            
            # Add some random delay
            await asyncio.sleep(random.uniform(0.01, 0.1))
            
            # Check if item exists
            if item_id not in ITEMS:
                # Increment error counter
                await self.get_error_counter.increment()
                
                # Log event
                await log_event(
                    name="item_not_found",
                    message=f"Item not found: {item_id}",
                    level=EventLevel.WARNING,
                    event_type=EventType.BUSINESS,
                    data={"item_id": item_id}
                )
                
                # Return failure
                return failure(UnoError(
                    message=f"Item not found: {item_id}",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    item_id=item_id
                ))
            
            # Get item
            item = ITEMS[item_id]
            
            # Log event
            await log_event(
                name="item_retrieved",
                message=f"Item retrieved: {item_id}",
                level=EventLevel.INFO,
                event_type=EventType.BUSINESS,
                data={"item_id": item_id, "item_name": item["name"]}
            )
            
            # Return success
            return of(item)


# Example health check
async def database_health_check() -> HealthCheckResult:
    """
    Check the health of the database.
    
    Returns:
        Health check result
    """
    # Simulate database check
    await asyncio.sleep(0.1)
    
    # Randomly fail sometimes
    if random.random() < 0.1:
        return HealthCheckResult(
            status=HealthStatus.DEGRADED,
            message="Database is slow",
            details={"response_time": 500}
        )
    
    return HealthCheckResult(
        status=HealthStatus.HEALTHY,
        message="Database is healthy",
        details={"response_time": 50}
    )


# Create FastAPI app with monitoring
app = FastAPI(title="Monitoring Example")

# Set up monitoring
monitoring_config = MonitoringConfig(
    service_name="monitoring-example",
    environment="development",
    metrics=MetricsConfig(
        enabled=True,
        export_interval=30.0,
        prometheus_enabled=True,
        metrics_path="/metrics",
    ),
    tracing=TracingConfig(
        enabled=True,
        service_name="monitoring-example",
        sampling_rate=1.0,
        log_spans=True,
    ),
    health=HealthConfig(
        enabled=True,
        include_details=True,
        path_prefix="/health",
    ),
    events=EventsConfig(
        enabled=True,
        min_level="INFO",
        log_events=True,
    ),
)

# Configure monitoring
configure_monitoring(monitoring_config)
setup_monitoring(app, monitoring_config)
create_monitoring_endpoints(app)

# Register health checks
@app.on_event("startup")
async def register_health_checks():
    """Register health checks on startup."""
    await register_health_check(
        name="database",
        check_func=database_health_check,
        description="Check database health",
        tags=["database"]
    )


# Create service instance
item_service = ItemService()


# API endpoints
@app.get("/items", summary="List all items")
@trace(name="list_items", kind=SpanKind.SERVER)
async def list_items():
    """
    List all items.
    
    Returns:
        List of all items
    """
    await log_event(
        name="list_items",
        message="Listing all items",
        level=EventLevel.INFO,
        event_type=EventType.BUSINESS
    )
    
    return list(ITEMS.values())


@app.get("/items/{item_id}", summary="Get an item by ID")
@trace(name="get_item_api", kind=SpanKind.SERVER)
async def get_item(item_id: str):
    """
    Get an item by ID.
    
    Args:
        item_id: ID of the item to get
        
    Returns:
        The item with the given ID
        
    Raises:
        404: If the item is not found
    """
    # Get the item
    result = await item_service.get_item(item_id)
    
    # Handle result
    if result.is_success:
        return result.value
    else:
        error = result.error
        
        if isinstance(error, UnoError) and error.error_code == ErrorCode.RESOURCE_NOT_FOUND:
            raise HTTPException(status_code=404, detail=str(error))
        else:
            raise HTTPException(status_code=500, detail=str(error))


@app.get("/status", summary="Get application status")
@timed(timer_name="status_duration", description="Duration of status endpoint")
async def status():
    """
    Get application status.
    
    Returns:
        Application status
    """
    health_status = await get_health_status()
    trace_id = get_current_trace_id()
    span_id = get_current_span_id()
    
    return {
        "status": "ok",
        "health": health_status.name,
        "trace_id": trace_id,
        "span_id": span_id,
        "timestamp": time.time()
    }


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)