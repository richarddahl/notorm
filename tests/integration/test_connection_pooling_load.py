"""
Integration tests for connection pooling under load.

These tests verify that the connection pool functions correctly under high load,
including scaling behavior, connection reuse, and performance characteristics.
"""

import asyncio
import logging
import time
from typing import Dict, List, Set, Optional
import pytest
import random
import statistics
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
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
from uno.core.monitoring.metrics import MetricsRegistry
from uno.settings import uno_settings


@pytest.fixture(scope="module")
def database_config() -> ConnectionConfig:
    """Get database configuration for testing."""
    return ConnectionConfig(
        db_role=f"{uno_settings.DB_NAME}_login",
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST or "localhost",
        db_port=uno_settings.DB_PORT or 5432,
        db_user_pw=uno_settings.DB_USER_PW or "password",
        db_driver=uno_settings.DB_ASYNC_DRIVER or "postgresql+asyncpg",
    )


@pytest.fixture(scope="module")
def pool_config() -> ConnectionPoolConfig:
    """Get pool configuration for testing."""
    return ConnectionPoolConfig(
        initial_size=3,
        min_size=2,
        max_size=10,
        target_free_connections=2,
        idle_timeout=20.0,
        max_lifetime=300.0,
        connection_timeout=5.0,
        validation_interval=5.0,
        strategy=ConnectionPoolStrategy.BALANCED,
        dynamic_scaling_enabled=True,
        scale_up_threshold=0.7,
        scale_down_threshold=0.3,
        retry_attempts=2,
    )


@pytest.fixture(scope="module")
def session_pool_config() -> SessionPoolConfig:
    """Get session pool configuration for testing."""
    return SessionPoolConfig(
        min_sessions=3,
        max_sessions=15,
        target_free_sessions=2,
        idle_timeout=20.0,
        max_lifetime=300.0,
        connection_pool_config=ConnectionPoolConfig(
            initial_size=3,
            min_size=2,
            max_size=10,
        ),
        use_enhanced_connection_pool=True,
    )


@pytest.fixture(scope="module")
def metrics_registry() -> MetricsRegistry:
    """Get metrics registry for testing."""
    return MetricsRegistry()


@pytest.mark.integration
class TestConnectionPoolingLoad:
    """Integration tests for connection pooling under load."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_concurrent_access(
        self,
        database_config: ConnectionConfig,
        pool_config: ConnectionPoolConfig,
    ):
        """Test that the connection pool handles concurrent access effectively."""
        # Get the connection manager
        manager = get_connection_manager()
        
        # Configure the pool
        manager.configure_pool(
            role=database_config.db_role,
            config=pool_config,
        )
        
        # Create a set to track connection PIDs
        conn_pids: Set[int] = set()
        
        # Record timing metrics
        acquisition_times: List[float] = []
        query_times: List[float] = []
        
        # Create a coroutine for executing a query
        async def execute_query(i: int):
            start_time = time.time()
            
            try:
                async with enhanced_async_connection(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                ) as conn:
                    acquisition_time = time.time() - start_time
                    acquisition_times.append(acquisition_time)
                    
                    # Execute a query with some variability in execution time
                    query_start = time.time()
                    sleep_time = random.uniform(0.05, 0.2)
                    
                    # Mix of fast and slow queries
                    if i % 5 == 0:
                        # Simulate a slow query
                        result = await conn.execute(
                            text(f"SELECT pg_backend_pid(), pg_sleep({sleep_time})")
                        )
                    else:
                        # Normal query
                        result = await conn.execute(
                            text("SELECT pg_backend_pid()")
                        )
                    
                    row = await result.fetchone()
                    pid = row[0]
                    
                    # Record the backend PID
                    conn_pids.add(pid)
                    
                    query_time = time.time() - query_start
                    query_times.append(query_time)
                    
                    return i, pid
                    
            except Exception as e:
                # Record errors but don't fail the test
                return i, f"Error: {str(e)}"
        
        try:
            # Execute concurrent queries in two waves to test scaling
            # First wave - slightly under capacity
            tasks = [execute_query(i) for i in range(8)]
            results = await asyncio.gather(*tasks)
            
            # Wait a moment for pool to adjust
            await asyncio.sleep(1)
            
            # Second wave - over capacity to test scaling up
            tasks = [execute_query(i) for i in range(8, 20)]
            results.extend(await asyncio.gather(*tasks))
            
            # Get metrics
            metrics = manager.get_metrics()
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            
            # Calculate statistics
            avg_acquisition = statistics.mean(acquisition_times)
            avg_query = statistics.mean(query_times)
            max_acquisition = max(acquisition_times)
            
            # Verify results
            assert len(results) == 20, "Expected 20 query executions"
            
            # Number of unique connections should be less than operations (reuse)
            # but more than initial (scaling up occurred)
            assert len(conn_pids) < 20, "Expected connection reuse"
            assert len(conn_pids) > pool_config.initial_size, "Expected pool scaling"
            
            # Verify pool metrics
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                
                # Pool should have scaled up
                assert pool_metrics["size"]["current"] > pool_config.initial_size
                assert pool_metrics["size"]["max_size"] >= pool_metrics["size"]["current"]
                
                # Pool should show activity
                assert pool_metrics["size"]["active"] > 0 or pool_metrics["size"]["idle"] > 0
                
                # Verify scaling metrics
                assert "scale_up_events" in pool_metrics["operations"]
                
                # Verify wait times are reasonable
                assert pool_metrics["performance"]["avg_wait_time"] >= 0
        
        finally:
            # Clean up
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_session_pool_under_load(
        self,
        database_config: ConnectionConfig,
        session_pool_config: SessionPoolConfig,
    ):
        """Test the session pool under high load with mixed-duration transactions."""
        # Create a test table
        async with enhanced_pool_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
        ) as session:
            await session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_session_pool_load (
                id SERIAL PRIMARY KEY,
                thread_id INTEGER NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """))
            await session.commit()
        
        # Define workload operations
        async def read_operation(session_id: int):
            """Read operation with variable duration."""
            try:
                async with enhanced_pool_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                    session_pool_config=session_pool_config,
                ) as session:
                    # Add some randomness to query duration
                    limit = random.randint(1, 10)
                    
                    result = await session.execute(
                        text("""
                        SELECT id, thread_id, value 
                        FROM test_session_pool_load 
                        ORDER BY created_at DESC 
                        LIMIT :limit
                        """),
                        {"limit": limit}
                    )
                    
                    rows = await result.fetchall()
                    return {"session_id": session_id, "operation": "read", "count": len(rows)}
            except Exception as e:
                return {"session_id": session_id, "operation": "read", "error": str(e)}
        
        async def write_operation(session_id: int):
            """Write operation with variable duration."""
            try:
                async with enhanced_pool_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                    session_pool_config=session_pool_config,
                ) as session:
                    # Insert 1-5 rows
                    count = random.randint(1, 5)
                    
                    for i in range(count):
                        value = f"value-{session_id}-{i}-{time.time()}"
                        
                        await session.execute(
                            text("""
                            INSERT INTO test_session_pool_load (thread_id, value)
                            VALUES (:thread_id, :value)
                            """),
                            {"thread_id": session_id, "value": value}
                        )
                    
                    # Random sleep to simulate processing time
                    await asyncio.sleep(random.uniform(0.05, 0.2))
                    
                    await session.commit()
                    return {"session_id": session_id, "operation": "write", "count": count}
            except Exception as e:
                return {"session_id": session_id, "operation": "write", "error": str(e)}
        
        async def mixed_transaction(session_id: int):
            """Mixed read-write transaction."""
            try:
                async with enhanced_pool_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                    session_pool_config=session_pool_config,
                ) as session:
                    # First read some data
                    result = await session.execute(
                        text("""
                        SELECT COUNT(*) FROM test_session_pool_load
                        """)
                    )
                    
                    count = (await result.fetchone())[0]
                    
                    # Then write based on what we read
                    value = f"tx-{session_id}-count-{count}-{time.time()}"
                    
                    await session.execute(
                        text("""
                        INSERT INTO test_session_pool_load (thread_id, value)
                        VALUES (:thread_id, :value)
                        """),
                        {"thread_id": session_id, "value": value}
                    )
                    
                    # Simulate some processing time
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    await session.commit()
                    return {"session_id": session_id, "operation": "mixed", "read_count": count}
            except Exception as e:
                return {"session_id": session_id, "operation": "mixed", "error": str(e)}
        
        try:
            # Create mix of operations
            operations = []
            
            # 40% reads
            operations.extend([read_operation(i) for i in range(20)])
            
            # 40% writes
            operations.extend([write_operation(i + 100) for i in range(20)])
            
            # 20% mixed transactions
            operations.extend([mixed_transaction(i + 200) for i in range(10)])
            
            # Execute them all concurrently
            start_time = time.time()
            results = await asyncio.gather(*operations)
            total_time = time.time() - start_time
            
            # Count success and errors
            success_count = sum(1 for r in results if "error" not in r)
            error_count = sum(1 for r in results if "error" in r)
            
            # Get session factory metrics
            manager = get_connection_manager()
            conn_metrics = manager.get_metrics()
            
            # Analyze results
            assert success_count > 0, "Expected some operations to succeed"
            assert error_count < len(operations) * 0.1, f"Too many errors: {error_count}"
            
            # Verify pool scaled appropriately
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            if pool_name in conn_metrics:
                pool_metrics = conn_metrics[pool_name]
                
                # Check that pool scaled up to handle load
                assert pool_metrics["size"]["max_size_reached"] >= pool_metrics["size"]["initial_size"]
                
                # Check connection reuse
                assert pool_metrics["size"]["total_created"] < len(operations)
                
                # Check health
                assert pool_metrics["health"]["health_check_failures"] == 0
                
                # Log relevant metrics for analysis
                logging.info(f"Connection pool metrics under load: {pool_metrics}")
        
        finally:
            # Clean up test table
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            ) as session:
                await session.execute(text("DROP TABLE IF EXISTS test_session_pool_load"))
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_connection_health_monitoring_under_load(
        self,
        database_config: ConnectionConfig,
        pool_config: ConnectionPoolConfig,
    ):
        """Test health monitoring of connections under load."""
        # Get connection manager
        manager = get_connection_manager()
        
        # Configure pool with aggressive health checking
        health_pool_config = ConnectionPoolConfig(
            initial_size=3,
            min_size=2,
            max_size=8,
            health_check_interval=2.0,  # Check health every 2 seconds
            validation_interval=1.0,    # Validate connections frequently
            connection_timeout=3.0,     # Shorter timeout for faster tests
            retry_attempts=2,           # Limited retries
            dynamic_scaling_enabled=True,
            scale_up_threshold=0.6,     # Scale up earlier
            scale_down_threshold=0.3,
        )
        
        manager.configure_pool(
            role=database_config.db_role,
            config=health_pool_config,
        )
        
        # Track operations and errors
        successful_ops = 0
        failed_ops = 0
        health_check_count = 0
        
        async def execute_with_tracking(i: int):
            """Execute a query and track results."""
            nonlocal successful_ops, failed_ops
            
            try:
                async with enhanced_async_connection(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                ) as conn:
                    # For every 7th connection, run a health check query
                    if i % 7 == 0:
                        nonlocal health_check_count
                        health_check_count += 1
                        
                        result = await conn.execute(text("""
                            SELECT 1 as is_healthy, 
                            pg_sleep(0.1), -- slight delay to simulate health check
                            pg_backend_pid()
                        """))
                        is_healthy, _, pid = await result.fetchone()
                        assert is_healthy == 1
                    else:
                        # Normal query
                        result = await conn.execute(text("SELECT pg_backend_pid()"))
                        pid = (await result.fetchone())[0]
                    
                    successful_ops += 1
                    return pid
            except SQLAlchemyError as e:
                failed_ops += 1
                return f"Error: {str(e)}"
        
        try:
            # Execute in several waves to test pool resilience
            pids = set()
            all_results = []
            
            # First wave - baseline
            tasks = [execute_with_tracking(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            # Extract PIDs to track connection reuse
            for result in results:
                if isinstance(result, int):
                    pids.add(result)
            
            # Wait for health checks to run
            await asyncio.sleep(2.5)
            
            # Second wave - connections should be reused
            tasks = [execute_with_tracking(i) for i in range(10, 25)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            for result in results:
                if isinstance(result, int):
                    pids.add(result)
            
            # Wait again for health checks
            await asyncio.sleep(2.5)
            
            # Third wave - heavy load
            tasks = [execute_with_tracking(i) for i in range(25, 50)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            for result in results:
                if isinstance(result, int):
                    pids.add(result)
            
            # Get metrics
            metrics = manager.get_metrics()
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            
            # Validate outcomes
            assert successful_ops > 0, "Expected some operations to succeed"
            assert health_check_count > 0, "Expected some health checks to run"
            
            # Check health monitoring metrics
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                
                # Verify health checks occurred
                assert pool_metrics["health"]["health_check_count"] > 0
                
                # Log health metrics
                logging.info(f"Health metrics: {pool_metrics['health']}")
                
                # Connection validations should have occurred
                assert pool_metrics["health"]["validation_count"] > 0
                
                # Pool should have maintained health
                assert pool_metrics["health"]["circuit_breaker_trips"] == 0
        
        finally:
            # Clean up
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_transaction_metrics_collection(
        self,
        database_config: ConnectionConfig,
        session_pool_config: SessionPoolConfig,
        metrics_registry: MetricsRegistry,
    ):
        """Test metrics collection for transaction performance."""
        # Create test table
        async with enhanced_pool_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
        ) as session:
            await session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_transaction_metrics (
                id SERIAL PRIMARY KEY,
                op_type TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """))
            await session.commit()
        
        # Create operation group to manage sessions
        async def run_tracked_transaction(op_group, i: int, success: bool = True):
            """Run a tracked transaction with metrics."""
            session = await op_group.create_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            )
            
            start_time = time.time()
            metrics_key = f"transaction.{i}"
            
            try:
                # Start transaction
                metrics_registry.timer(metrics_key, "start")
                
                # Record operation type
                op_type = "success" if success else "fail"
                
                # Insert a record
                await session.execute(
                    text("""
                    INSERT INTO test_transaction_metrics (op_type, value)
                    VALUES (:op_type, :value)
                    """),
                    {"op_type": op_type, "value": f"value-{i}-{time.time()}"}
                )
                
                # Add some variable duration
                sleep_time = random.uniform(0.05, 0.2)
                await asyncio.sleep(sleep_time)
                
                if not success:
                    # Simulate a failure
                    raise ValueError("Simulated transaction failure")
                
                # Commit transaction
                await session.commit()
                metrics_registry.timer(metrics_key, "end", {"status": "success"})
                metrics_registry.counter("transaction.success", 1, {"type": op_type})
                return {"txn": i, "status": "success", "duration": time.time() - start_time}
                
            except Exception as e:
                # Roll back transaction
                await session.rollback()
                metrics_registry.timer(metrics_key, "end", {"status": "failure"})
                metrics_registry.counter("transaction.failure", 1, {"error": str(e)})
                return {"txn": i, "status": "failure", "error": str(e), "duration": time.time() - start_time}
        
        try:
            # Execute transactions with metrics tracking
            async with EnhancedPooledSessionOperationGroup(
                name="transaction_metrics_test",
                session_pool_config=session_pool_config,
            ) as op_group:
                # Run successful transactions
                success_tasks = [
                    op_group.task_group.create_task(
                        run_tracked_transaction(op_group, i, True),
                        name=f"success_txn_{i}"
                    ) for i in range(15)
                ]
                
                # Run some failure cases
                fail_tasks = [
                    op_group.task_group.create_task(
                        run_tracked_transaction(op_group, i + 100, False),
                        name=f"fail_txn_{i + 100}"
                    ) for i in range(5)
                ]
                
                # Wait for all to complete
                all_results = await asyncio.gather(
                    *[task.wait() for task in success_tasks + fail_tasks]
                )
                
                # Get connection manager metrics
                manager = get_connection_manager()
                conn_metrics = manager.get_metrics()
                
                # Get transaction metrics
                timer_metrics = metrics_registry.get_timer_metrics()
                counter_metrics = metrics_registry.get_counter_metrics()
                
                # Validate metrics
                assert "transaction.success" in counter_metrics
                assert counter_metrics["transaction.success"]["count"] >= 15
                
                assert "transaction.failure" in counter_metrics
                assert counter_metrics["transaction.failure"]["count"] >= 5
                
                # Check for transaction timing metrics
                assert len(timer_metrics) > 0
                
                # Check for transaction metrics in connection pool
                pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
                if pool_name in conn_metrics:
                    pool_metrics = conn_metrics[pool_name]
                    
                    # Transaction stats should be collected
                    assert "transaction_count" in pool_metrics["performance"]
                    assert pool_metrics["performance"]["transaction_count"] > 0
                    
                    # Should have some rollbacks
                    assert "transaction_rollbacks" in pool_metrics["performance"]
                    assert pool_metrics["performance"]["transaction_rollbacks"] > 0
                    
                    # Should have rollback rate
                    assert "rollback_rate" in pool_metrics["performance"]
                    assert 0 <= pool_metrics["performance"]["rollback_rate"] <= 1.0
        
        finally:
            # Clean up test table
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            ) as session:
                await session.execute(text("DROP TABLE IF EXISTS test_transaction_metrics"))
                await session.commit()


if __name__ == "__main__":
    # For manual running of tests
    pytest.main(["-xvs", __file__])