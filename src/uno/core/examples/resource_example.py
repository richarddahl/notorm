"""
Example usage of the Resource Management utilities.

This module demonstrates how to use the resource management components
for proper resource lifecycle, connection pooling, and monitoring.
"""

import asyncio
import logging
import time
import signal
import os
import sys
from typing import List, Dict, Any

import uvicorn
from fastapi import FastAPI, Depends

from uno.core.async_manager import get_async_manager, run_application
from uno.core.resource_management import (
    get_resource_manager,
    initialize_resources,
    managed_connection_pool,
    managed_background_task,
)
from uno.core.resource_monitor import (
    get_resource_monitor,
    start_resource_monitoring,
)
from uno.core.resources import (
    ConnectionPool,
    CircuitBreaker,
    BackgroundTask,
    get_resource_registry,
)
from uno.core.fastapi_integration import (
    setup_resource_management,
    create_health_endpoint,
    create_resource_monitoring_endpoints,
    db_session_dependency,
)
from uno.database.pooled_session import (
    pooled_async_session,
    PooledSessionOperationGroup,
)


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def example_background_task() -> None:
    """
    Example background task that runs periodically.
    
    This task demonstrates proper cancellation handling and
    integration with the resource management system.
    """
    logger.info("Background task started")
    
    try:
        # Get the async manager to check for shutdown
        manager = get_async_manager()
        
        # Run until shutdown is initiated
        while not manager.is_shutting_down():
            # Simulate some work
            logger.info("Background task running...")
            await asyncio.sleep(5.0)
            
            # Perform a database operation with the pooled session
            async with pooled_async_session() as session:
                # Execute a simple query
                result = await session.execute("SELECT 1 as test")
                row = result.fetchone()
                logger.info(f"Database query result: {row}")
    
    except asyncio.CancelledError:
        # Handle cancellation cleanly
        logger.info("Background task cancelled")
        raise
    
    except Exception as e:
        logger.error(f"Error in background task: {str(e)}", exc_info=True)
    
    finally:
        logger.info("Background task stopped")


async def example_connection_factory() -> ConnectionPool:
    """
    Example factory function for creating a connection pool.
    
    Returns:
        A connection pool
    """
    # Define the connection creation function
    async def create_connection():
        logger.info("Creating example connection")
        # Simulate connection creation
        await asyncio.sleep(0.1)
        return {"id": id({}), "created_at": time.time()}
    
    # Define the connection close function
    async def close_connection(conn):
        logger.info(f"Closing example connection {conn['id']}")
        # Simulate connection close
        await asyncio.sleep(0.1)
    
    # Define the connection validation function
    async def validate_connection(conn):
        # Simulate validation
        await asyncio.sleep(0.1)
        return True
    
    # Create the pool
    return ConnectionPool(
        name="example_pool",
        factory=create_connection,
        close_func=close_connection,
        validate_func=validate_connection,
        max_size=5,
        min_size=1,
        logger=logger,
    )


async def demo_resource_operations() -> None:
    """
    Demonstrate various resource management operations.
    """
    logger.info("Starting resource operations demo")
    
    # Get the resource registry
    registry = get_resource_registry()
    
    # Create and register a circuit breaker
    circuit_breaker = CircuitBreaker(
        name="example_circuit",
        failure_threshold=3,
        recovery_timeout=10.0,
        logger=logger,
    )
    
    await registry.register("example_circuit", circuit_breaker)
    logger.info("Registered example circuit breaker")
    
    # Create a connection pool with a context manager
    async with managed_connection_pool(
        "example_pool",
        example_connection_factory,
    ) as pool:
        logger.info("Created and registered example connection pool")
        
        # Use the pool to get connections
        conn1 = await pool.acquire()
        logger.info(f"Acquired connection {conn1['id']}")
        
        # Release the connection
        await pool.release(conn1)
        logger.info("Released connection")
        
        # Get pool metrics
        metrics = pool.get_metrics()
        logger.info(f"Pool metrics: {metrics}")
    
    # Create a background task with a context manager
    async with managed_background_task(
        "example_task",
        example_background_task,
        restart_on_failure=True,
    ) as task:
        logger.info("Created and registered example background task")
        
        # Let the task run for a bit
        await asyncio.sleep(10.0)
    
    # Check what resources are still registered
    resources = registry.get_all_resources()
    logger.info(f"Registered resources: {', '.join(resources.keys())}")
    
    logger.info("Resource operations demo completed")


async def startup() -> None:
    """
    Application startup function.
    """
    logger.info("Application starting")
    
    # Initialize resources
    await initialize_resources()
    
    # Start resource monitoring
    await start_resource_monitoring()
    
    # Run demo operations
    manager = get_async_manager()
    manager.create_task(demo_resource_operations())


async def cleanup() -> None:
    """
    Application cleanup function.
    """
    logger.info("Application shutting down")


async def run_standalone_demo() -> None:
    """
    Run a standalone demo of resource management.
    """
    # Run the application
    await run_application(
        startup_func=startup,
        cleanup_func=cleanup,
    )


def create_fastapi_app() -> FastAPI:
    """
    Create a FastAPI application with resource management integration.
    
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Resource Management Demo",
        description="Demo of Uno framework resource management",
        version="1.0.0",
    )
    
    # Set up resource management
    setup_resource_management(app)
    
    # Create health endpoint
    create_health_endpoint(app)
    
    # Create resource monitoring endpoints
    create_resource_monitoring_endpoints(app)
    
    # Create an example API endpoint
    @app.get("/example", summary="Example endpoint")
    async def example_endpoint(session = Depends(db_session_dependency)):
        """
        Example endpoint that uses a database session.
        
        Returns:
            Example data
        """
        # Execute a simple query
        result = await session.execute("SELECT 1 as test")
        row = result.fetchone()
        
        return {
            "message": "Example endpoint",
            "database_result": dict(row) if row else None,
            "timestamp": time.time(),
        }
    
    # Create an example for session operation group
    @app.get("/advanced-example", summary="Advanced example endpoint")
    async def advanced_example():
        """
        Example endpoint that uses a session operation group.
        
        Returns:
            Example data
        """
        results = []
        
        # Use a session operation group
        async with PooledSessionOperationGroup() as op_group:
            # Create a session
            session = await op_group.create_session(pool_size=5, min_size=1)
            
            # Run operations in a transaction
            await op_group.run_in_transaction(
                session,
                [
                    lambda s: s.execute("SELECT 1 as test1"),
                    lambda s: s.execute("SELECT 2 as test2"),
                ]
            )
            
            # Run operations concurrently
            task1 = await op_group.run_operation(
                session,
                lambda s: s.execute("SELECT 3 as test3")
            )
            task2 = await op_group.run_operation(
                session,
                lambda s: s.execute("SELECT 4 as test4")
            )
            
            # Collect results
            for result in [task1, task2]:
                row = result.fetchone()
                results.append(dict(row) if row else None)
        
        return {
            "message": "Advanced example endpoint",
            "results": results,
            "timestamp": time.time(),
        }
    
    return app


def run_fastapi_demo() -> None:
    """
    Run a FastAPI demo of resource management.
    """
    # Create the FastAPI app
    app = create_fastapi_app()
    
    # Run the app
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    # Check if running as a FastAPI app
    if len(sys.argv) > 1 and sys.argv[1] == "--fastapi":
        run_fastapi_demo()
    else:
        # Run the standalone demo
        asyncio.run(run_standalone_demo())