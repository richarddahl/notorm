"""
Example demonstrating modern async patterns in uno.

This example shows:
1. Structured concurrency with TaskGroup
2. Transaction management with context managers
3. Resource management with async context managers
4. Proper error handling and propagation
5. Cancellation handling
"""

import asyncio
import logging
import signal
from datetime import datetime
from typing import List, Dict, Any, Optional

from uno.core.async.helpers import TaskGroup, setup_signal_handler
from uno.core.async_integration import (
    retry, BackoffStrategy, concurrent_limited, AsyncCache, timeout_handler
)
from uno.core.async_manager import get_async_manager
from uno.database.transaction import transaction
from uno.database.transaction_factory import create_write_transaction_manager
from uno.database.session import AsyncSessionFactory
from uno.core.result import Result, Success, Failure


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example resource class with proper lifecycle management
class AsyncResource:
    def __init__(self, name: str):
        self.name = name
        self.is_initialized = False
        logger.info(f"Creating resource {name}")
    
    async def __aenter__(self) -> 'AsyncResource':
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup()
    
    async def initialize(self) -> None:
        """Initialize the resource."""
        logger.info(f"Initializing resource {self.name}")
        await asyncio.sleep(0.1)  # Simulate initialization
        self.is_initialized = True
    
    async def cleanup(self) -> None:
        """Clean up the resource."""
        logger.info(f"Cleaning up resource {self.name}")
        await asyncio.sleep(0.1)  # Simulate cleanup
        self.is_initialized = False
    
    async def operation(self, value: str) -> str:
        """Example operation that uses the resource."""
        if not self.is_initialized:
            raise RuntimeError(f"Resource {self.name} is not initialized")
        
        logger.info(f"Resource {self.name}: processing {value}")
        await asyncio.sleep(0.2)  # Simulate processing
        return f"{self.name} processed {value}"


# Example service with transaction management
class UserService:
    def __init__(self, session_factory: AsyncSessionFactory):
        self.session_factory = session_factory
        self.transaction_manager = create_write_transaction_manager(session_factory)
    
    async def get_user(self, user_id: str) -> Result[Dict[str, Any], Exception]:
        """Get a user using transaction context manager."""
        try:
            async with self.transaction_manager() as session:
                # In a real implementation, this would query the database
                logger.info(f"Getting user {user_id}")
                await asyncio.sleep(0.2)  # Simulate database query
                
                # Simulate user retrieval
                user = {
                    "id": user_id,
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@example.com",
                    "created_at": datetime.now()
                }
                
                return Success(user)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return Failure(e)
    
    @retry(
        max_attempts=3,
        retry_exceptions=[ConnectionError, TimeoutError],
        backoff_strategy=BackoffStrategy.EXPONENTIAL,
        max_delay=5.0
    )
    async def update_user(self, user_id: str, data: Dict[str, Any]) -> Result[Dict[str, Any], Exception]:
        """Update a user with retry logic."""
        try:
            async with self.transaction_manager() as session:
                logger.info(f"Updating user {user_id} with {data}")
                
                # Simulate database update
                await asyncio.sleep(0.3)
                
                # Simulate intermittent error (1 in 3 chance)
                if asyncio.get_running_loop().time() % 3 < 1:
                    raise ConnectionError("Simulated connection error")
                
                # Simulate updated user
                user = {
                    "id": user_id,
                    "name": data.get("name", f"User {user_id}"),
                    "email": data.get("email", f"user{user_id}@example.com"),
                    "updated_at": datetime.now()
                }
                
                return Success(user)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return Failure(e)


# Example task processing with concurrency limiting
class TaskProcessor:
    def __init__(self):
        self.cache = AsyncCache(ttl=60.0, max_size=100)
    
    @concurrent_limited(max_concurrent=5)
    async def process_task(self, task_id: str, data: Dict[str, Any]) -> Result[str, Exception]:
        """Process a task with concurrency limiting."""
        try:
            logger.info(f"Processing task {task_id}")
            
            # Check cache first
            cached_result = await self.cache.get_async(task_id)
            if cached_result:
                logger.info(f"Using cached result for task {task_id}")
                return Success(cached_result)
            
            # Simulate processing
            await asyncio.sleep(0.5)
            
            # Generate result
            result = f"Task {task_id} processed with {len(data)} data items"
            
            # Cache the result
            await self.cache.set_async(task_id, result)
            
            return Success(result)
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            return Failure(e)
    
    @timeout_handler(timeout_seconds=2.0)
    async def process_with_timeout(self, task_id: str) -> Result[str, Exception]:
        """Process a task with timeout."""
        try:
            logger.info(f"Processing task {task_id} with timeout")
            
            # Simulate a potentially long-running operation
            delay = float(task_id) % 3
            await asyncio.sleep(delay)
            
            return Success(f"Task {task_id} processed in {delay:.2f}s")
        except asyncio.TimeoutError:
            logger.error(f"Timeout processing task {task_id}")
            return Failure(asyncio.TimeoutError(f"Processing task {task_id} timed out"))
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            return Failure(e)


# Main function demonstrating structured concurrency
async def main():
    # Get the async manager
    manager = get_async_manager()
    
    # Set up signal handlers
    await setup_signal_handler(signal.SIGINT, handle_signal)
    await setup_signal_handler(signal.SIGTERM, handle_signal)
    
    # Services
    session_factory = AsyncSessionFactory()
    user_service = UserService(session_factory)
    task_processor = TaskProcessor()
    
    # Process multiple users concurrently using TaskGroup
    async with TaskGroup() as group:
        # Create tasks for getting users
        tasks = []
        for i in range(5):
            task = group.create_task(user_service.get_user(str(i)))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = []
        for task in tasks:
            try:
                result = await task
                if result.is_success:
                    results.append(result.value)
                else:
                    logger.error(f"Failed to get user: {result.error}")
            except asyncio.CancelledError:
                logger.warning("Task was cancelled")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
    
    # Process tasks with proper resource management
    async with AsyncResource("TaskResource") as resource:
        # Process tasks
        async with TaskGroup() as group:
            for i in range(3):
                task_id = str(i)
                data = {"key": f"value{i}", "timestamp": datetime.now()}
                
                # Process with the resource
                task = group.create_task(
                    process_with_resource(resource, task_id, data, task_processor)
                )
    
    # Update users with proper transaction management
    updates = [
        ("1", {"name": "Updated User 1"}),
        ("2", {"email": "new2@example.com"}),
        ("3", {"name": "Updated User 3", "email": "new3@example.com"})
    ]
    
    async with TaskGroup() as group:
        for user_id, data in updates:
            group.create_task(user_service.update_user(user_id, data))
    
    # Process tasks with timeouts
    async with TaskGroup() as group:
        for i in range(5):
            group.create_task(task_processor.process_with_timeout(str(i)))
    
    logger.info("All operations completed successfully")


async def process_with_resource(
    resource: AsyncResource,
    task_id: str,
    data: Dict[str, Any],
    processor: TaskProcessor
) -> None:
    """Process a task using a resource."""
    # Use the resource
    processed = await resource.operation(f"Task {task_id}")
    logger.info(f"Resource processing result: {processed}")
    
    # Process the task
    result = await processor.process_task(task_id, data)
    if result.is_success:
        logger.info(f"Task processing result: {result.value}")
    else:
        logger.error(f"Task processing failed: {result.error}")


async def handle_signal(sig: signal.Signals) -> None:
    """Handle signal with graceful shutdown."""
    logger.info(f"Received signal {sig.name}, initiating shutdown")
    
    # Get the async manager
    manager = get_async_manager()
    
    # Initiate shutdown
    await manager.shutdown()


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())