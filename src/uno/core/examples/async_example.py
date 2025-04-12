"""
Example usage of the Async-First Architecture utilities.

This module demonstrates how to use the async utilities in a real application
with proper cancellation handling, structured concurrency, and resource management.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

from uno.core.async_manager import (
    get_async_manager,
    run_application,
    as_task,
)
from uno.core.async_utils import (
    TaskGroup,
    timeout,
    AsyncLock,
    Limiter,
    RateLimiter,
)
from uno.core.async_integration import (
    cancellable,
    timeout_handler,
    retry,
    concurrent_limited,
    rate_limited,
    AsyncBatcher,
    AsyncCache,
)
from uno.database.enhanced_session import (
    enhanced_async_session,
    SessionOperationGroup,
)
from uno.database.enhanced_db import EnhancedUnoDb


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


# Rate limiter for API calls
api_limiter = RateLimiter(
    rate=10,
    burst=20,
    name="api_limiter",
)


# Enhanced database instance
db = EnhancedUnoDb()


@rate_limited(operations_per_second=10)
@retry(max_attempts=3)
@timeout_handler(timeout_seconds=5.0)
async def make_api_call(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make an API call with rate limiting and retry logic.
    
    Args:
        endpoint: API endpoint
        data: Request data
        
    Returns:
        API response
    """
    # Simulate API call
    await asyncio.sleep(0.1)
    return {"status": "success", "data": {"id": 123}}


@cancellable
async def process_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of items with proper cancellation handling.
    
    Args:
        items: List of items to process
        
    Returns:
        Processed items
    """
    results = []
    
    # Create a task group for concurrent processing
    async with TaskGroup(name="process_items") as group:
        # Create a task for each item
        tasks = [
            group.create_task(
                process_item(item),
                name=f"process_item_{i}"
            )
            for i, item in enumerate(items)
        ]
        
        # Wait for all tasks to complete
        for task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing item: {str(e)}")
    
    return results


@concurrent_limited(max_concurrent=5)
async def process_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single item with concurrency limiting.
    
    Args:
        item: Item to process
        
    Returns:
        Processed item
    """
    # Simulate processing
    await asyncio.sleep(0.2)
    
    # Make an API call
    response = await make_api_call("/process", item)
    
    # Add the response to the item
    item["response"] = response
    
    return item


@as_task("database_operation")
async def perform_database_operations(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Perform database operations with proper error handling.
    
    Args:
        items: Items to process
        
    Returns:
        Processed items
    """
    results = []
    
    # Use a session operation group for coordinated transactions
    async with SessionOperationGroup() as op_group:
        # Create a session
        session = await op_group.create_session()
        
        # Perform operations in a transaction
        async with session.begin():
            for item in items:
                # Process the item
                try:
                    # Simulate database operation
                    await asyncio.sleep(0.1)
                    
                    # Add result
                    results.append({
                        **item,
                        "processed": True,
                    })
                
                except Exception as e:
                    logger.error(f"Error in database operation: {str(e)}")
                    # Transaction will be rolled back on error
                    raise
    
    return results


async def startup() -> None:
    """Initialize the application."""
    logger.info("Starting application")
    
    # Register resources with the async manager
    manager = get_async_manager()
    await manager.register_resource(db, name="database")
    
    # Start some background tasks
    manager.create_task(background_task(), name="background_task")


async def background_task() -> None:
    """Run a background task with proper cancellation handling."""
    logger.info("Starting background task")
    
    try:
        while True:
            # Do some work
            await asyncio.sleep(1)
            
            # Check if shutting down
            manager = get_async_manager()
            if manager.is_shutting_down():
                logger.info("Background task shutting down")
                break
    
    except asyncio.CancelledError:
        logger.info("Background task cancelled")
        raise


async def cleanup() -> None:
    """Clean up application resources."""
    logger.info("Cleaning up application resources")
    
    # Clean up manually if needed
    # Most resources will be handled by the async manager
    pass


async def main() -> None:
    """Main application entry point."""
    # Run the application with the AsyncManager
    await run_application(
        startup_func=startup,
        cleanup_func=cleanup,
    )


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())