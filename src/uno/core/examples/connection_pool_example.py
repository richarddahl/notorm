"""
Example usage of the enhanced connection pool.

This example demonstrates how to use the enhanced connection pool for
high-performance database operations.
"""

import asyncio
import time
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    ConnectionPoolStrategy,
    get_connection_manager,
    enhanced_async_connection,
)
from uno.database.enhanced_pool_session import (
    SessionPoolConfig,
    enhanced_pool_session,
    EnhancedPooledSessionOperationGroup,
)


async def basic_connection_example():
    """Basic example of using the enhanced connection pool."""
    print("Basic connection example:")
    
    # Using the enhanced connection pool with default settings
    async with enhanced_async_connection() as connection:
        # Use the connection for a simple query
        result = await connection.execute(text("SELECT 1 as value"))
        value = (await result.fetchone())[0]
        print(f"Query result: {value}")


async def configure_pool_example():
    """Example of configuring the connection pool."""
    print("\nConfiguring connection pool:")
    
    # Get the connection manager
    manager = get_connection_manager()
    
    # Create a custom configuration for high-throughput workloads
    high_throughput_config = ConnectionPoolConfig(
        # Pool sizing
        initial_size=10,
        min_size=5,
        max_size=50,
        
        # Connection lifecycle
        idle_timeout=600.0,  # 10 minutes
        max_lifetime=3600.0,  # 1 hour
        
        # Strategy
        strategy=ConnectionPoolStrategy.HIGH_THROUGHPUT,
        
        # Dynamic scaling
        dynamic_scaling_enabled=True,
        scale_up_threshold=0.7,  # Scale up when 70% utilized
        scale_down_threshold=0.3,  # Scale down when below 30% utilized
    )
    
    # Create a custom configuration for low-latency workloads
    low_latency_config = ConnectionPoolConfig(
        # Pool sizing
        initial_size=5,
        min_size=3,
        max_size=20,
        
        # Connection lifecycle
        idle_timeout=300.0,  # 5 minutes
        max_lifetime=1800.0,  # 30 minutes
        
        # Strategy
        strategy=ConnectionPoolStrategy.LOW_LATENCY,
        
        # Dynamic scaling
        dynamic_scaling_enabled=True,
        scale_up_threshold=0.6,  # Scale up when 60% utilized
        scale_down_threshold=0.2,  # Scale down when below 20% utilized
    )
    
    # Apply configuration to specific database roles
    manager.configure_pool(role="analytics", config=high_throughput_config)
    manager.configure_pool(role="user_service", config=low_latency_config)
    
    # Set default configuration for other roles
    default_config = ConnectionPoolConfig(
        strategy=ConnectionPoolStrategy.BALANCED,
    )
    manager.configure_pool(config=default_config)
    
    print("Connection pool configured with different strategies for different roles")


async def session_example():
    """Example of using enhanced session with connection pool."""
    print("\nEnhanced session example:")
    
    # Using the enhanced session with connection pool
    async with enhanced_pool_session() as session:
        # Use the session for a simple query
        result = await session.execute(text("SELECT 2 as value"))
        value = (await result.fetchone())[0]
        print(f"Session query result: {value}")


async def session_operation_group_example():
    """Example of using the session operation group."""
    print("\nSession operation group example:")
    
    # Create a session operation group
    async with EnhancedPooledSessionOperationGroup(name="example_group") as group:
        # Create a session
        session = await group.create_session()
        
        # Define some example operations
        async def get_number(s: AsyncSession, number: int) -> int:
            result = await s.execute(text(f"SELECT {number} as value"))
            value = (await result.fetchone())[0]
            return value
        
        # Run operations in parallel
        results = await group.run_parallel_operations(
            session,
            [
                lambda s: get_number(s, 1),
                lambda s: get_number(s, 2),
                lambda s: get_number(s, 3),
                lambda s: get_number(s, 4),
                lambda s: get_number(s, 5),
            ],
            max_concurrency=3  # Run up to 3 operations concurrently
        )
        
        print(f"Parallel operation results: {results}")
        
        # Run operations in a transaction
        results = await group.run_in_transaction(
            session,
            [
                lambda s: get_number(s, 10),
                lambda s: get_number(s, 20),
            ]
        )
        
        print(f"Transaction operation results: {results}")


async def performance_benchmark():
    """Benchmark comparing standard vs. enhanced connection pool."""
    print("\nPerformance benchmark:")
    
    # Configure session for benchmarking
    session_config = SessionPoolConfig(
        min_sessions=10,
        max_sessions=50,
    )
    
    # Number of queries to run
    num_queries = 1000
    
    # Function to run a batch of queries
    async def run_queries(session_context):
        async with session_context as session:
            start_time = time.time()
            
            for i in range(num_queries):
                result = await session.execute(text("SELECT 1"))
                await result.fetchone()
            
            end_time = time.time()
            return end_time - start_time
    
    # Create operation group for parallel sessions
    async with EnhancedPooledSessionOperationGroup() as group:
        # Create 5 sessions
        sessions = []
        for i in range(5):
            session = await group.create_session(
                session_pool_config=session_config
            )
            sessions.append(session)
        
        # Run queries in parallel from different sessions
        tasks = []
        for session in sessions:
            # Create a task for each session
            async def run_query_batch(s):
                start_time = time.time()
                
                for i in range(200):  # 200 queries per session = 1000 total
                    result = await s.execute(text("SELECT 1"))
                    await result.fetchone()
                
                end_time = time.time()
                return end_time - start_time
            
            tasks.append(group.run_operation(session, run_query_batch))
        
        # Wait for all tasks to complete
        durations = await asyncio.gather(*tasks)
        
        # Calculate statistics
        total_duration = max(durations)  # Total duration is the max of parallel operations
        queries_per_second = num_queries / total_duration
        
        print(f"Ran {num_queries} queries in {total_duration:.2f} seconds")
        print(f"Throughput: {queries_per_second:.2f} queries/second")


async def metrics_example():
    """Example of accessing connection pool metrics."""
    print("\nConnection pool metrics example:")
    
    # First, generate some load to have interesting metrics
    async with EnhancedPooledSessionOperationGroup() as group:
        # Create 5 sessions
        sessions = []
        for i in range(5):
            session = await group.create_session()
            sessions.append(session)
        
        # Run some queries
        tasks = []
        for session in sessions:
            for _ in range(10):
                tasks.append(group.run_operation(
                    session,
                    lambda s: s.execute(text("SELECT 1"))
                ))
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    
    # Now get metrics
    manager = get_connection_manager()
    metrics = manager.get_metrics()
    
    # Pretty print metrics
    for pool_name, pool_metrics in metrics.items():
        print(f"\nPool: {pool_name}")
        print(f"  Size: {pool_metrics['size']['current']} connections")
        print(f"  Active: {pool_metrics['size']['active']} connections")
        print(f"  Idle: {pool_metrics['size']['idle']} connections")
        print(f"  Current load: {pool_metrics['performance']['current_load']:.2f}")
        print(f"  Avg wait time: {pool_metrics['performance']['avg_wait_time']:.4f}s")
        print(f"  Uptime: {pool_metrics['uptime']:.2f}s")


async def main():
    """Run all examples."""
    await basic_connection_example()
    await configure_pool_example()
    await session_example()
    await session_operation_group_example()
    await performance_benchmark()
    await metrics_example()
    
    # Close the connection manager for clean shutdown
    manager = get_connection_manager()
    await manager.close()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())