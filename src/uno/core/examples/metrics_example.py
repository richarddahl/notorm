# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example for using the metrics framework.

This module demonstrates how to use the UNO metrics framework with
various metric types, context propagation, transaction metrics,
and integration with FastAPI.
"""

import asyncio
import random
import time
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, Request

from uno.core.metrics import (
    configure_metrics,
    get_metrics_registry,
    MetricsConfig,
    MetricUnit,
    timed,
    counter,
    gauge,
    histogram,
    timer,
    with_metrics_context,
    MetricsContext,
    MetricsMiddleware,
    TransactionContext,
    get_transaction_metrics_tracker,
)
from uno.core.logging import configure_logging, get_logger, LogConfig


# Configure logging and metrics
def setup_observability() -> None:
    """Configure logging and metrics for the application."""
    # Configure logging
    configure_logging(LogConfig(
        level="DEBUG",
        format="json",
        console_output=True,
    ))
    
    # Configure metrics
    metrics_config = MetricsConfig(
        enabled=True,
        service_name="example-service",
        environment="development",
        export_interval=10.0,  # More frequent for demo
        console_export=True,
        prometheus_export=True,
        default_tags={
            "region": "us-west",
            "version": "1.0.0",
        }
    )
    configure_metrics(metrics_config)


# Get a logger for this module
logger = get_logger("examples.metrics")


# Example of counter metrics
async def increment_counters() -> None:
    """Example of using counter metrics."""
    # Create counters
    requests_counter = await counter(
        "example.requests.total",
        description="Total example requests",
        tags={"endpoint": "example"},
    )
    
    errors_counter = await counter(
        "example.errors.total",
        description="Total example errors",
        tags={"endpoint": "example"},
    )
    
    # Increment counters
    for _ in range(5):
        await requests_counter.increment()
        
        # Simulate some errors
        if random.random() < 0.3:
            await errors_counter.increment()
            logger.warning("Simulated error occurred")
    
    logger.info("Counter example completed")


# Example of gauge metrics
async def update_gauges() -> None:
    """Example of using gauge metrics."""
    # Create a gauge for active connections
    connections_gauge = await gauge(
        "example.connections.active",
        description="Active connections",
        unit=MetricUnit.COUNT,
        tags={"service": "example"},
    )
    
    # Simulate connection activity
    for i in range(5):
        # Add some connections
        await connections_gauge.increment(random.randint(1, 5))
        logger.info(f"Added connections, iteration {i}")
        await asyncio.sleep(0.1)
        
        # Remove some connections
        await connections_gauge.decrement(random.randint(1, 3))
        logger.info(f"Removed connections, iteration {i}")
        await asyncio.sleep(0.1)
    
    # Set to a specific value
    await connections_gauge.set(10)
    logger.info("Set connections to 10")
    
    logger.info("Gauge example completed")


# Example of histogram metrics
async def record_histograms() -> None:
    """Example of using histogram metrics."""
    # Create a histogram for response size
    response_size = await histogram(
        "example.response.size",
        description="Example response size in bytes",
        unit=MetricUnit.BYTES,
        tags={"service": "example"},
    )
    
    # Record some values
    for _ in range(10):
        size = random.randint(100, 10000)
        await response_size.observe(size)
        logger.info(f"Recorded response size: {size} bytes")
    
    # Get statistics
    stats = await response_size._histogram.get_statistics()
    logger.info(f"Response size statistics: {stats}")
    
    logger.info("Histogram example completed")


# Example of timer metrics
async def time_operations() -> None:
    """Example of using timer metrics."""
    # Create a timer
    operation_timer = await timer(
        "example.operation.duration",
        description="Example operation duration",
        tags={"service": "example"},
    )
    
    # Use the timer with a context manager
    for i in range(3):
        async with TimerContext(operation_timer):
            # Simulate some work
            await asyncio.sleep(random.uniform(0.1, 0.5))
            logger.info(f"Completed operation in context {i}")
    
    # Record a duration directly
    duration = random.uniform(50, 200)
    await operation_timer.record(duration)
    logger.info(f"Recorded operation duration directly: {duration}ms")
    
    # Get statistics
    stats = await operation_timer.get_statistics()
    logger.info(f"Operation timer statistics: {stats}")
    
    logger.info("Timer example completed")


# Example of using the timed decorator
@timed("example.function.duration", description="Example function duration")
async def timed_function(iterations: int = 3) -> Dict[str, Any]:
    """
    Example function with timed decorator.
    
    Args:
        iterations: Number of iterations to perform
    
    Returns:
        Results dictionary
    """
    results = {"iterations": iterations, "values": []}
    
    for i in range(iterations):
        # Simulate some work
        await asyncio.sleep(random.uniform(0.05, 0.2))
        
        # Add a result
        value = random.randint(1, 100)
        results["values"].append(value)
        logger.info(f"Timed function iteration {i}: {value}")
    
    logger.info("Timed function completed")
    return results


# Example of using metrics context
@with_metrics_context(component="user_service")
async def user_service_operation(user_id: str) -> Dict[str, Any]:
    """
    Example operation with metrics context.
    
    Args:
        user_id: User identifier
    
    Returns:
        User data
    """
    # Create a counter with the inherited context
    operation_counter = await counter(
        "example.user.operations",
        description="User operations",
    )
    await operation_counter.increment()
    
    # Simulate some work
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    # Log with the same context
    logger.info(f"Processed user: {user_id}")
    
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "status": "active",
    }


# Example of using transaction metrics
class MockSession:
    """Mock database session for example purposes."""
    
    async def begin(self):
        """Begin a transaction."""
        return self
    
    async def commit(self):
        """Commit a transaction."""
        pass
    
    async def rollback(self):
        """Rollback a transaction."""
        pass
    
    async def execute(self, query: str) -> int:
        """
        Execute a query.
        
        Args:
            query: SQL query
            
        Returns:
            Number of affected rows
        """
        # Simulate query execution
        await asyncio.sleep(random.uniform(0.05, 0.2))
        return random.randint(1, 10)
    
    async def begin_nested(self):
        """Create a savepoint."""
        return self


async def transaction_example(success: bool = True) -> Dict[str, Any]:
    """
    Example of tracking database transactions.
    
    Args:
        success: Whether the transaction should succeed
        
    Returns:
        Transaction statistics
    """
    # Create a mock session
    session = MockSession()
    
    try:
        # Use transaction context for automatic metrics tracking
        async with TransactionContext(session, "example_transaction") as tx:
            # Execute some queries
            rows = await session.execute("SELECT * FROM users")
            await tx.record_query(rows=rows)
            logger.info(f"Query 1 affected {rows} rows")
            
            rows = await session.execute("INSERT INTO logs VALUES (...)")
            await tx.record_query(rows=rows)
            logger.info(f"Query 2 affected {rows} rows")
            
            # Create a savepoint
            savepoint = await tx.savepoint()
            logger.info("Created savepoint")
            
            # Execute another query
            rows = await session.execute("UPDATE users SET status = 'active'")
            await tx.record_query(rows=rows)
            logger.info(f"Query 3 affected {rows} rows")
            
            # Simulate a failure if requested
            if not success:
                raise ValueError("Simulated transaction failure")
            
            # If successful, the transaction will be committed automatically
            logger.info("Transaction completed successfully")
    
    except Exception as e:
        # Transaction will be rolled back automatically
        logger.error(f"Transaction failed: {str(e)}")
        
        # Propagate the error
        raise
    
    # Get transaction statistics
    tracker = get_transaction_metrics_tracker()
    stats = await tracker.get_transaction_statistics()
    
    return stats


# Example of using metrics with FastAPI
app = FastAPI(title="Metrics Example API")

# Add metrics middleware
app.add_middleware(
    MetricsMiddleware,
    metrics_path="/metrics",
    excluded_paths=["/health"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    This endpoint is excluded from metrics collection.
    """
    return {"status": "healthy"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user details with metrics tracking."""
    try:
        # Use the metrics context for this operation
        async with MetricsContext("api.get_user", tags={"method": "GET"}):
            # Call the user service operation
            result = await user_service_operation(user_id)
            return {"user": result}
    
    except Exception as e:
        # The metrics context will record the failure
        logger.exception(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions")
async def create_transaction(success: bool = True):
    """Create a transaction with metrics tracking."""
    try:
        # Track the transaction
        stats = await transaction_example(success)
        return {"result": "success", "stats": stats}
    
    except Exception as e:
        logger.exception(f"Transaction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/examples")
async def run_metric_examples():
    """Run all metric examples and return results."""
    # Run all the examples
    await increment_counters()
    await update_gauges()
    await record_histograms()
    await time_operations()
    
    # Run the timed function
    result = await timed_function(iterations=5)
    
    # Get all metrics
    registry = get_metrics_registry()
    metrics = await registry.get_all_metrics()
    
    return {
        "examples_run": ["counters", "gauges", "histograms", "timers", "timed_function"],
        "timed_function_result": result,
        "metrics_count": len(metrics),
    }


# Example of running the metrics examples
async def run_examples():
    """Run all metrics examples."""
    # Configure logging and metrics
    setup_observability()
    
    logger.info("Starting metrics examples")
    
    # Run examples
    try:
        await increment_counters()
        await update_gauges()
        await record_histograms()
        await time_operations()
        await timed_function(iterations=5)
        await user_service_operation("user123")
        
        # Transaction examples
        await transaction_example(success=True)
        try:
            await transaction_example(success=False)
        except ValueError:
            logger.info("Caught expected transaction failure")
    
    except Exception as e:
        logger.exception(f"Error in examples: {str(e)}")
    
    logger.info("Metrics examples completed")
    
    # Let metrics export
    await asyncio.sleep(1)
    
    # Shutdown metrics
    registry = get_metrics_registry()
    await registry.shutdown()


if __name__ == "__main__":
    # Run the examples as a standalone script
    asyncio.run(run_examples())
    
    # To start the FastAPI app, uncomment:
    # import uvicorn
    # setup_observability()
    # uvicorn.run(app, host="0.0.0.0", port=8000)