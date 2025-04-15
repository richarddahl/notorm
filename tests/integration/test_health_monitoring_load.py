"""
Integration tests for health monitoring under load.

These tests verify that the connection pool health monitoring functions correctly 
under high load, including circuit breaker behavior, connection validation, and recovery.
"""

import asyncio
import logging
import time
import pytest
from typing import Dict, List, Set, Tuple, Optional, Any, AsyncGenerator
import random
import statistics

from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

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
)
from uno.settings import uno_settings
from uno.core.resource_management import ResourceMonitor


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
def health_pool_config() -> ConnectionPoolConfig:
    """Get pool configuration for testing health monitoring."""
    return ConnectionPoolConfig(
        initial_size=3,
        min_size=2,
        max_size=10,
        target_free_connections=2,
        idle_timeout=5.0,  # Short idle timeout for testing
        max_lifetime=30.0,  # Short lifetime for testing
        connection_timeout=2.0,  # Short timeout for faster tests
        validation_interval=1.0,  # Validate connections frequently
        health_check_interval=1.0,  # Check health every second
        dynamic_scaling_enabled=True,
        scale_up_threshold=0.7,
        scale_down_threshold=0.3,
        retry_attempts=2,
        circuit_breaker_threshold=3,  # Trip after 3 failures
        circuit_breaker_recovery=5.0,  # Short recovery time for testing
    )


@pytest.fixture(scope="module")
def resource_monitor() -> ResourceMonitor:
    """Get a resource monitor for testing."""
    return ResourceMonitor()


@pytest.mark.integration
class TestHealthMonitoringLoad:
    """Integration tests for health monitoring under load."""
    
    @pytest.mark.asyncio
    async def test_health_checks_during_load(
        self,
        database_config: ConnectionConfig,
        health_pool_config: ConnectionPoolConfig,
    ):
        """Test that health checks continue during high load."""
        # Get connection manager
        manager = get_connection_manager()
        
        # Configure pool with health checking config
        manager.configure_pool(
            role=database_config.db_role,
            config=health_pool_config,
        )
        
        # Create a test table
        async with enhanced_async_connection(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
        ) as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_health_checks (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """))
            
            # Start with a clean slate
            await conn.execute(text("TRUNCATE TABLE test_health_checks"))
            
            # Commit changes
            await conn.commit()
        
        try:
            # Track health check statistics
            health_checks_occurred = 0
            validation_checks_occurred = 0
            
            # Function to perform a query
            async def perform_query(i: int) -> Dict[str, Any]:
                start_time = time.time()
                error = None
                
                try:
                    async with enhanced_async_connection(
                        db_driver=database_config.db_driver,
                        db_name=database_config.db_name,
                        db_host=database_config.db_host,
                        db_port=database_config.db_port,
                        db_user_pw=database_config.db_user_pw,
                        db_role=database_config.db_role,
                    ) as conn:
                        # Random query execution time
                        sleep_time = random.uniform(0.05, 0.2)
                        
                        # Simulate a load with some real work
                        if i % 3 == 0:
                            # Write operation
                            value = f"value-{i}-{time.time()}"
                            await conn.execute(
                                text("""
                                INSERT INTO test_health_checks (value)
                                VALUES (:value)
                                """),
                                {"value": value}
                            )
                            await conn.commit()
                            operation = "write"
                            
                        else:
                            # Read operation
                            result = await conn.execute(
                                text(f"""
                                SELECT id, value, pg_sleep({sleep_time}) 
                                FROM test_health_checks 
                                ORDER BY id DESC LIMIT 5
                                """)
                            )
                            rows = await result.fetchall()
                            operation = "read"
                            
                        # Check connection metadata to see if health checks happened
                        health_check_metadata = getattr(conn, "_health_check_count", 0)
                        validation_metadata = getattr(conn, "_validation_count", 0)
                        
                        if health_check_metadata:
                            nonlocal health_checks_occurred
                            health_checks_occurred += 1
                            
                        if validation_metadata:
                            nonlocal validation_checks_occurred
                            validation_checks_occurred += 1
                            
                        # Record connection ID for tracking
                        connection_id = str(id(conn))
                            
                        return {
                            "operation": operation,
                            "duration": time.time() - start_time,
                            "connection_id": connection_id,
                            "success": True,
                        }
                        
                except Exception as e:
                    error = str(e)
                    return {
                        "operation": "unknown",
                        "duration": time.time() - start_time,
                        "error": error,
                        "success": False,
                    }
            
            # Run multiple waves of concurrent queries
            all_results = []
            connections_seen = set()
            
            # First wave - normal load
            tasks = [perform_query(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            # Track connections
            for result in results:
                if "connection_id" in result:
                    connections_seen.add(result["connection_id"])
            
            # Wait for health checks to run
            await asyncio.sleep(3)
            
            # Second wave - heavy load
            tasks = [perform_query(i) for i in range(10, 50)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            # Track connections
            for result in results:
                if "connection_id" in result:
                    connections_seen.add(result["connection_id"])
            
            # Wait for health checks to run
            await asyncio.sleep(3)
            
            # Third wave - another burst
            tasks = [perform_query(i) for i in range(50, 70)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            # Get pool metrics
            metrics = manager.get_metrics()
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            
            # Analyze results
            success_count = sum(1 for r in all_results if r.get("success", False))
            error_count = len(all_results) - success_count
            
            # Verify that health checks occurred
            assert health_checks_occurred > 0, "Expected health checks to occur during load"
            assert validation_checks_occurred > 0, "Expected validation checks to occur during load"
            
            # Verify most operations succeeded
            assert success_count > len(all_results) * 0.95, f"Too many errors: {error_count}/{len(all_results)}"
            
            # Verify connection reuse (fewer connections than operations)
            assert len(connections_seen) < len(all_results), "Expected connection reuse"
            
            # Check pool metrics
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                
                # Verify pool health metrics were collected
                assert "health" in pool_metrics
                assert pool_metrics["health"]["health_check_count"] > 0
                assert pool_metrics["health"]["validation_count"] > 0
                
                # Log metrics for analysis
                logging.info(f"Pool health metrics: {pool_metrics['health']}")
                
                # Verify pool scaled appropriately
                assert pool_metrics["size"]["current"] <= health_pool_config.max_size
                assert pool_metrics["size"]["current"] >= health_pool_config.min_size
        
        finally:
            # Clean up test table
            async with enhanced_async_connection(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            ) as conn:
                await conn.execute(text("DROP TABLE IF EXISTS test_health_checks"))
                await conn.commit()
            
            # Clean up connection manager
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_under_load(
        self,
        database_config: ConnectionConfig,
        health_pool_config: ConnectionPoolConfig,
    ):
        """Test circuit breaker behavior under load with simulated failures."""
        # Get connection manager
        manager = get_connection_manager()
        
        # Configure pool with circuit breaker config
        circuit_config = ConnectionPoolConfig(
            initial_size=2,
            min_size=1,
            max_size=5,
            connection_timeout=1.0,  # Short timeout for faster tests
            retry_attempts=1,  # Limited retries
            circuit_breaker_threshold=3,  # Trip after 3 failures
            circuit_breaker_recovery=3.0,  # Short recovery time for testing
            health_check_interval=1.0,  # Check health every second
        )
        
        manager.configure_pool(
            role=database_config.db_role,
            config=circuit_config,
        )
        
        # Create a proxy to inject failures
        class ConnectionFailureProxy:
            """Proxy to simulate connection failures."""
            
            def __init__(self, real_execute):
                """Initialize with the real execute function."""
                self.real_execute = real_execute
                self.failure_rate = 0.0
                self.failure_count = 0
                self.success_count = 0
                self.lock = asyncio.Lock()
            
            def set_failure_rate(self, rate: float) -> None:
                """Set the failure rate (0.0-1.0)."""
                self.failure_rate = max(0.0, min(1.0, rate))
            
            async def execute(self, *args, **kwargs):
                """Execute with potential failure."""
                async with self.lock:
                    if random.random() < self.failure_rate:
                        self.failure_count += 1
                        # Simulate a database error
                        raise OperationalError("Connection failure (simulated)", None, None)
                    else:
                        self.success_count += 1
                        return await self.real_execute(*args, **kwargs)
        
        # Create the proxy
        proxy = None
        
        try:
            # Function to run queries with the proxy
            async def run_queries(count: int, proxy: ConnectionFailureProxy, expected_success_rate: float) -> Dict[str, Any]:
                """Run a series of queries with an expected success rate."""
                results = []
                
                for i in range(count):
                    try:
                        async with enhanced_async_connection(
                            db_driver=database_config.db_driver,
                            db_name=database_config.db_name,
                            db_host=database_config.db_host,
                            db_port=database_config.db_port,
                            db_user_pw=database_config.db_user_pw,
                            db_role=database_config.db_role,
                        ) as conn:
                            # Save the real execute function if not already saved
                            if proxy is None:
                                nonlocal proxy
                                proxy = ConnectionFailureProxy(conn.execute)
                            
                            # Monkey patch the execute function
                            conn.execute = proxy.execute
                            
                            # Try to execute a simple query
                            await conn.execute(text("SELECT 1"))
                            results.append({"success": True})
                            
                    except Exception as e:
                        results.append({"success": False, "error": str(e)})
                
                # Calculate success rate
                success_count = sum(1 for r in results if r.get("success", False))
                success_rate = success_count / len(results) if results else 0
                
                return {
                    "count": len(results),
                    "success_count": success_count,
                    "success_rate": success_rate,
                    "expected_success_rate": expected_success_rate,
                    "proxy_stats": {
                        "success_count": proxy.success_count,
                        "failure_count": proxy.failure_count,
                    }
                }
            
            # Test phases
            # 1. Normal operation
            proxy = ConnectionFailureProxy(None)  # Will be set in first query
            proxy.set_failure_rate(0.0)
            normal_results = await run_queries(10, proxy, 1.0)
            
            # Verify normal operation
            assert normal_results["success_rate"] > 0.9, "Expected high success rate under normal operation"
            
            # 2. Introduce a high failure rate to trip circuit breaker
            proxy.set_failure_rate(0.8)
            failure_results = await run_queries(20, proxy, 0.2)
            
            # Verify circuit breaker eventually trips
            # The success rate might be higher than expected due to retries,
            # but should be below a certain threshold
            assert failure_results["success_rate"] < 0.5, "Expected low success rate with high failures"
            
            # Get metrics to check circuit breaker status
            metrics = manager.get_metrics()
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                logging.info(f"Circuit breaker metrics: {pool_metrics['health']}")
                
                # Should see circuit breaker trips in the metrics
                assert pool_metrics["health"]["circuit_breaker_trips"] > 0, "Expected circuit breaker to trip"
            
            # 3. Wait for circuit breaker reset
            await asyncio.sleep(circuit_config.circuit_breaker_recovery + 1)
            
            # 4. Return to normal operation
            proxy.set_failure_rate(0.0)
            recovery_results = await run_queries(10, proxy, 1.0)
            
            # Verify recovery
            assert recovery_results["success_rate"] > 0.7, "Expected recovery after circuit breaker reset"
            
            # Final metrics check
            metrics = manager.get_metrics()
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                
                # Should see circuit breaker resets
                assert pool_metrics["health"]["circuit_breaker_resets"] > 0, "Expected circuit breaker to reset"
                
                logging.info(f"Final circuit breaker metrics: {pool_metrics['health']}")
        
        finally:
            # Clean up connection manager
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_connection_recycling_under_load(
        self,
        database_config: ConnectionConfig,
        health_pool_config: ConnectionPoolConfig,
    ):
        """Test connection recycling behavior under load."""
        # Get connection manager
        manager = get_connection_manager()
        
        # Configure pool with aggressive recycling
        recycle_config = ConnectionPoolConfig(
            initial_size=3,
            min_size=2,
            max_size=8,
            idle_timeout=2.0,  # Short idle timeout for testing
            max_lifetime=5.0,  # Short lifetime for testing
            validation_interval=1.0,  # Validate frequently
            recycle_threshold=5,  # Recycle after 5 operations
            dynamic_scaling_enabled=True,
            scale_up_threshold=0.7,
            scale_down_threshold=0.3,
        )
        
        manager.configure_pool(
            role=database_config.db_role,
            config=recycle_config,
        )
        
        try:
            # Track connection IDs to detect recycling
            connection_pids = {}
            
            # Function to execute queries and track connections
            async def track_connection(i: int) -> Dict[str, Any]:
                try:
                    async with enhanced_async_connection(
                        db_driver=database_config.db_driver,
                        db_name=database_config.db_name,
                        db_host=database_config.db_host,
                        db_port=database_config.db_port,
                        db_user_pw=database_config.db_user_pw,
                        db_role=database_config.db_role,
                    ) as conn:
                        # Get the PostgreSQL backend PID
                        result = await conn.execute(text("SELECT pg_backend_pid()"))
                        pid = (await result.fetchone())[0]
                        
                        # Track the connection object ID and PID
                        conn_id = id(conn)
                        
                        return {
                            "connection_id": conn_id,
                            "pid": pid,
                            "operation": i,
                            "success": True,
                        }
                
                except Exception as e:
                    return {
                        "error": str(e),
                        "operation": i,
                        "success": False,
                    }
            
            # Run multiple waves with sleep between to allow recycling
            all_results = []
            
            # First wave - establish connections
            tasks = [track_connection(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            # Track initial connections
            for result in results:
                if "connection_id" in result and "pid" in result:
                    connection_pids[result["connection_id"]] = result["pid"]
            
            # Wait to allow some connections to be recycled
            await asyncio.sleep(3)
            
            # Second wave - should reuse some connections, but some might be recycled
            tasks = [track_connection(i) for i in range(10, 30)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            # Track connections that might be recycled (same conn_id, different pid)
            recycled_connections = 0
            connection_reuses = 0
            
            for result in results:
                if "connection_id" in result and "pid" in result:
                    conn_id = result["connection_id"]
                    pid = result["pid"]
                    
                    if conn_id in connection_pids:
                        # Connection object was reused
                        connection_reuses += 1
                        
                        if connection_pids[conn_id] != pid:
                            # The PID changed, indicating recycling
                            recycled_connections += 1
                            # Update the PID
                            connection_pids[conn_id] = pid
                    else:
                        # New connection
                        connection_pids[conn_id] = pid
            
            # Wait again to allow more connections to be recycled
            await asyncio.sleep(3)
            
            # Third wave - should show more recycling
            tasks = [track_connection(i) for i in range(30, 50)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            
            # Count additional recycling
            for result in results:
                if "connection_id" in result and "pid" in result:
                    conn_id = result["connection_id"]
                    pid = result["pid"]
                    
                    if conn_id in connection_pids:
                        # Connection object was reused
                        connection_reuses += 1
                        
                        if connection_pids[conn_id] != pid:
                            # The PID changed, indicating recycling
                            recycled_connections += 1
                            # Update the PID
                            connection_pids[conn_id] = pid
                    else:
                        # New connection
                        connection_pids[conn_id] = pid
            
            # Get pool metrics
            metrics = manager.get_metrics()
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            
            # Verify recycling occurred
            assert recycled_connections > 0, "Expected some connection recycling to occur"
            
            # Check metrics
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                
                # Log recycling metrics
                logging.info(f"Connection recycling: {recycled_connections} recycled out of {connection_reuses} reuses")
                logging.info(f"Pool recycling metrics: {pool_metrics['operations']}")
                
                # Pool should show recycling events
                if "recycled_connections" in pool_metrics["operations"]:
                    assert pool_metrics["operations"]["recycled_connections"] > 0, "Expected recycling in metrics"
        
        finally:
            # Clean up connection manager
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_health_monitoring_with_resource_monitoring(
        self,
        database_config: ConnectionConfig,
        health_pool_config: ConnectionPoolConfig,
        resource_monitor: ResourceMonitor,
    ):
        """Test health monitoring with resource monitoring integration."""
        # Get connection manager
        manager = get_connection_manager()
        
        # Configure pool with resource monitoring
        resource_config = ConnectionPoolConfig(
            initial_size=2,
            min_size=1,
            max_size=6,
            health_check_interval=1.0,
            dynamic_scaling_enabled=True,
            scale_up_threshold=0.7,
            scale_down_threshold=0.3,
            resource_monitor=resource_monitor,
        )
        
        manager.configure_pool(
            role=database_config.db_role,
            config=resource_config,
        )
        
        try:
            # Start resource monitoring
            await resource_monitor.start()
            
            # Function to execute queries
            async def execute_query(i: int, memory_intensive: bool = False) -> Dict[str, Any]:
                try:
                    async with enhanced_async_connection(
                        db_driver=database_config.db_driver,
                        db_name=database_config.db_name,
                        db_host=database_config.db_host,
                        db_port=database_config.db_port,
                        db_user_pw=database_config.db_user_pw,
                        db_role=database_config.db_role,
                    ) as conn:
                        if memory_intensive:
                            # Use a query that uses more memory
                            await conn.execute(text("""
                            WITH RECURSIVE large_data AS (
                                SELECT 1 as n, '1' as data
                                UNION ALL
                                SELECT n+1, data || '-' || (n+1)::text
                                FROM large_data
                                WHERE n < 1000
                            )
                            SELECT sum(length(data)) FROM large_data
                            """))
                        else:
                            # Simple query
                            await conn.execute(text("SELECT 1"))
                        
                        return {
                            "operation": i,
                            "memory_intensive": memory_intensive,
                            "success": True,
                        }
                
                except Exception as e:
                    return {
                        "operation": i,
                        "memory_intensive": memory_intensive,
                        "error": str(e),
                        "success": False,
                    }
            
            # Execute a mix of regular and memory-intensive queries
            tasks = []
            
            # Regular queries
            tasks.extend([execute_query(i, False) for i in range(20)])
            
            # Memory-intensive queries
            tasks.extend([execute_query(i + 100, True) for i in range(5)])
            
            # Run all queries
            results = await asyncio.gather(*tasks)
            
            # Get resource monitoring metrics
            resource_metrics = await resource_monitor.get_metrics()
            
            # Get pool metrics
            metrics = manager.get_metrics()
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            
            # Count successes
            success_count = sum(1 for r in results if r.get("success", False))
            
            # Verify queries succeeded
            assert success_count > len(results) * 0.9, f"Expected most queries to succeed, got {success_count}/{len(results)}"
            
            # Verify resource metrics were collected
            assert "cpu_usage" in resource_metrics, "Expected CPU metrics"
            assert "memory_usage" in resource_metrics, "Expected memory metrics"
            
            # Check pool metrics
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                
                # Log resource metrics
                logging.info(f"Resource metrics: {resource_metrics}")
                logging.info(f"Pool metrics: {pool_metrics}")
                
                # Verify resource metrics integration
                if "resources" in pool_metrics:
                    assert "cpu_usage" in pool_metrics["resources"], "Expected CPU metrics in pool"
                    assert "memory_usage" in pool_metrics["resources"], "Expected memory metrics in pool"
        
        finally:
            # Stop resource monitoring
            await resource_monitor.stop()
            
            # Clean up connection manager
            await manager.close()


if __name__ == "__main__":
    # For manual running of tests
    pytest.main(["-xvs", __file__])