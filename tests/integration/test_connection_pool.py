"""
Integration tests for the connection pool.

These tests verify that the connection pool functions correctly with a real database,
including connection creation, validation, reuse, and error handling.
"""

import os
import asyncio
import logging
import time
import pytest
from typing import List, Dict, Any, Optional, Tuple, Set

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    ConnectionPoolStrategy,
    EnhancedConnectionPool,
    EnhancedAsyncEnginePool,
    get_connection_manager,
    enhanced_async_engine,
    enhanced_async_connection,
)
from uno.database.enhanced_pool_session import (
    SessionPoolConfig,
    EnhancedPooledSessionFactory,
    enhanced_pool_session,
    EnhancedPooledSessionOperationGroup,
)
from uno.database.session import async_session
from uno.core.resources import ResourceRegistry
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
        initial_size=2,
        min_size=1,
        max_size=5,
        target_free_connections=1,
        idle_timeout=30.0,  # 30 seconds
        max_lifetime=300.0,  # 5 minutes
        connection_timeout=5.0,  # 5 seconds
        validation_interval=5.0,  # 5 seconds
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
        min_sessions=2,
        max_sessions=10,
        target_free_sessions=1,
        idle_timeout=30.0,  # 30 seconds
        max_lifetime=300.0,  # 5 minutes
        connection_pool_config=ConnectionPoolConfig(
            initial_size=2,
            min_size=1,
            max_size=5,
        ),
        use_enhanced_connection_pool=True,
    )


@pytest.fixture(scope="module")
def resource_registry() -> ResourceRegistry:
    """Get a resource registry for testing."""
    return ResourceRegistry()


@pytest.fixture(scope="module")
def logger() -> logging.Logger:
    """Get a logger for testing."""
    logger = logging.getLogger("test.connection_pool")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.mark.integration
class TestConnectionPoolIntegration:
    """Integration tests for the enhanced connection pool."""
    
    @pytest.mark.asyncio
    async def test_engine_pool_basic_operations(
        self, 
        database_config: ConnectionConfig, 
        pool_config: ConnectionPoolConfig,
        resource_registry: ResourceRegistry,
        logger: logging.Logger,
    ):
        """Test basic operations of the engine pool with a real database."""
        # Create engine pool
        engine_pool = EnhancedAsyncEnginePool(
            name="test_engine_pool",
            config=database_config,
            pool_config=pool_config,
            resource_registry=resource_registry,
            logger=logger,
        )
        
        try:
            # Start the pool
            await engine_pool.start()
            
            # Verify pool has been created
            assert engine_pool.pool is not None
            assert engine_pool.pool.size >= pool_config.initial_size
            
            # Acquire an engine
            engine = await engine_pool.acquire()
            
            # Verify engine works by executing a simple query
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                value = (await result.fetchone())[0]
                assert value == 1
            
            # Release the engine
            await engine_pool.release(engine)
            
            # Test context manager
            async with engine_pool.engine() as engine:
                # Verify engine works
                async with engine.connect() as conn:
                    result = await conn.execute(text("SELECT 2"))
                    value = (await result.fetchone())[0]
                    assert value == 2
            
            # Get metrics
            metrics = engine_pool.pool.get_metrics()
            
            # Verify metrics
            assert metrics["size"]["current"] >= pool_config.initial_size
            assert metrics["size"]["total_created"] >= pool_config.initial_size
            assert metrics["performance"]["avg_wait_time"] >= 0
            
        finally:
            # Clean up
            await engine_pool.close()
    
    @pytest.mark.asyncio
    async def test_connection_pool_connections(
        self, 
        database_config: ConnectionConfig,
        pool_config: ConnectionPoolConfig,
    ):
        """Test that the connection pool creates and reuses connections properly."""
        # Get the connection manager
        manager = get_connection_manager()
        
        # Configure the pool
        manager.configure_pool(
            role=database_config.db_role,
            config=pool_config,
        )
        
        # Create a set to track connection IDs
        conn_ids: Set[int] = set()
        
        try:
            # Test multiple connections
            for _ in range(10):
                async with enhanced_async_connection(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                ) as conn:
                    # Execute a simple query
                    result = await conn.execute(text("SELECT pg_backend_pid()"))
                    backend_pid = (await result.fetchone())[0]
                    
                    # Store the backend PID to check for connection reuse
                    conn_ids.add(backend_pid)
                    
                    # Do some work to give time for pool maintenance
                    await asyncio.sleep(0.1)
            
            # Get metrics
            metrics = manager.get_metrics()
            
            # We should see connection reuse (fewer unique connections than operations)
            assert len(conn_ids) < 10, "Expected connection reuse"
            
            # Verify pool metrics
            pool_name = f"{database_config.db_role}@{database_config.db_host}/{database_config.db_name}"
            if pool_name in metrics:
                pool_metrics = metrics[pool_name]
                
                # The pool should have created fewer connections than operations
                assert pool_metrics["size"]["total_created"] <= 10
                
                # The pool should have a reasonable current size
                assert pool_metrics["size"]["current"] <= pool_config.max_size
                assert pool_metrics["size"]["current"] >= pool_config.min_size
        
        finally:
            # Clean up
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_session_pool_operations(
        self,
        database_config: ConnectionConfig,
        session_pool_config: SessionPoolConfig,
    ):
        """Test operations with the enhanced pooled session."""
        # Create a session factory
        session_factory = EnhancedPooledSessionFactory(
            session_pool_config=session_pool_config,
        )
        
        try:
            # Create a session
            session = await session_factory.create_pooled_session_async(database_config)
            
            # Execute a test query
            result = await session.execute(text("SELECT current_database()"))
            db_name = (await result.fetchone())[0]
            
            # Verify result
            assert db_name == database_config.db_name
            
            # Close the session
            await session.close()
            
            # Test the session context manager
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
                session_pool_config=session_pool_config,
            ) as session:
                # Execute a test query
                result = await session.execute(text("SELECT current_database()"))
                db_name = (await result.fetchone())[0]
                
                # Verify result
                assert db_name == database_config.db_name
                
                # Commit the transaction to verify it works
                await session.commit()
        
        finally:
            # Cleanup handled by context manager
            pass
    
    @pytest.mark.asyncio
    async def test_parallel_session_operations(
        self,
        database_config: ConnectionConfig,
        session_pool_config: SessionPoolConfig,
    ):
        """Test parallel operations with pooled sessions."""
        # Create test table
        async with async_session() as session:
            await session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_session_pool (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL
            )
            """))
            await session.commit()
        
        try:
            # Use the session operation group
            async with EnhancedPooledSessionOperationGroup(
                name="test_parallel_ops",
                session_pool_config=session_pool_config,
            ) as group:
                # Create multiple sessions
                session1 = await group.create_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                )
                
                session2 = await group.create_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                )
                
                # Define operations
                async def insert_operation(session: AsyncSession, value: str) -> int:
                    result = await session.execute(
                        text("INSERT INTO test_session_pool (value) VALUES (:value) RETURNING id"),
                        {"value": value}
                    )
                    await session.commit()
                    return (await result.fetchone())[0]
                
                async def read_operation(session: AsyncSession, id: int) -> str:
                    result = await session.execute(
                        text("SELECT value FROM test_session_pool WHERE id = :id"),
                        {"id": id}
                    )
                    return (await result.fetchone())[0]
                
                # Run operations in parallel
                insert_task1 = group.task_group.create_task(
                    insert_operation(session1, "value1"),
                    name="insert1"
                )
                
                insert_task2 = group.task_group.create_task(
                    insert_operation(session2, "value2"),
                    name="insert2"
                )
                
                # Wait for inserts to complete
                id1 = await insert_task1
                id2 = await insert_task2
                
                # Read back the values
                read_task1 = group.task_group.create_task(
                    read_operation(session1, id2),  # Cross-read
                    name="read1"
                )
                
                read_task2 = group.task_group.create_task(
                    read_operation(session2, id1),  # Cross-read
                    name="read2"
                )
                
                # Verify reads
                value1 = await read_task1
                value2 = await read_task2
                
                assert value1 == "value2"
                assert value2 == "value1"
                
                # Run operations in a transaction
                async def transaction_operations(session: AsyncSession):
                    operations = [
                        lambda s: insert_operation(s, "batch1"),
                        lambda s: insert_operation(s, "batch2"),
                        lambda s: insert_operation(s, "batch3"),
                    ]
                    return await group.run_in_transaction(session, operations)
                
                # Run the transaction
                results = await group.task_group.create_task(
                    transaction_operations(session1),
                    name="transaction_ops"
                )
                
                # Verify results
                assert len(results) == 3
                assert all(isinstance(id, int) for id in results)
        
        finally:
            # Clean up test table
            async with async_session() as session:
                await session.execute(text("DROP TABLE IF EXISTS test_session_pool"))
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_connection_pool_error_handling(
        self,
        database_config: ConnectionConfig,
        pool_config: ConnectionPoolConfig,
    ):
        """Test that the connection pool handles errors properly."""
        # Create a modified config with an invalid password to force errors
        error_config = ConnectionConfig(
            db_role=database_config.db_role,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw="invalid_password",  # Invalid password to force errors
            db_driver=database_config.db_driver,
        )
        
        # Create a modified pool config with limited retries
        error_pool_config = ConnectionPoolConfig(
            initial_size=1,
            min_size=1,
            max_size=2,
            connection_timeout=2.0,  # Short timeout
            retry_attempts=1,  # Limited retries
            circuit_breaker_threshold=2,  # Trip after 2 failures
            circuit_breaker_recovery=5.0,  # Short recovery time for testing
        )
        
        # Create engine pool
        engine_pool = EnhancedAsyncEnginePool(
            name="test_error_pool",
            config=error_config,
            pool_config=error_pool_config,
        )
        
        try:
            # Start the pool - should fail but handle gracefully
            with pytest.raises((SQLAlchemyError, OperationalError)):
                await engine_pool.start()
            
            # Try to acquire an engine - should fail
            with pytest.raises((SQLAlchemyError, OperationalError)):
                await engine_pool.acquire()
            
            # Verify circuit breaker tripped
            if engine_pool.pool and engine_pool.pool._circuit_breaker:
                assert engine_pool.pool._circuit_breaker.state.is_open, "Circuit breaker should be open"
            
            # Metrics should reflect errors
            if engine_pool.pool:
                metrics = engine_pool.pool.metrics
                assert metrics.connection_errors > 0, "Should record connection errors"
        
        finally:
            # Clean up
            if engine_pool.pool:
                await engine_pool.close()


if __name__ == "__main__":
    # For manual running of tests
    pytest.main(["-xvs", __file__])