"""
Integration tests for database transaction management.

These tests verify the transaction management features of the database module,
including commit, rollback, nested transactions, and distributed transactions.
"""

import pytest
import asyncio
from typing import List, Dict, Any, Optional, Type
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError

from uno.database.session import async_session
from uno.database.enhanced_session import (
    EnhancedAsyncSessionFactory,
    enhanced_async_session,
    SessionOperationGroup
)
from uno.database.enhanced_pool_session import (
    EnhancedPooledSessionFactory,
    enhanced_pool_session,
    EnhancedPooledSessionOperationGroup
)
from uno.database.config import ConnectionConfig
from uno.settings import uno_settings
from uno.database.errors import (
    DatabaseTransactionError,
    DatabaseIntegrityError,
)
from uno.core.errors.result import Result, Success, Failure


@pytest.fixture(scope="module")
async def setup_test_tables():
    """Create test tables for transaction testing."""
    async with async_session() as session:
        # Create a test_transactions table
        await session.execute(text("""
        CREATE TABLE IF NOT EXISTS test_transactions (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            value INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """))
        
        # Create a second test table for multi-table transactions
        await session.execute(text("""
        CREATE TABLE IF NOT EXISTS test_transaction_details (
            id SERIAL PRIMARY KEY,
            transaction_id INTEGER NOT NULL REFERENCES test_transactions(id) ON DELETE CASCADE,
            detail TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """))
        
        # Create an audit log table for testing transaction hooks
        await session.execute(text("""
        CREATE TABLE IF NOT EXISTS test_transaction_audit (
            id SERIAL PRIMARY KEY,
            operation TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            details JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """))
        
        # Commit the schema changes
        await session.commit()
    
    # Return database config for tests to use
    return ConnectionConfig(
        db_role=f"{uno_settings.DB_NAME}_login",
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST or "localhost",
        db_port=uno_settings.DB_PORT or 5432,
        db_user_pw=uno_settings.DB_USER_PW or "password",
        db_driver=uno_settings.DB_ASYNC_DRIVER or "postgresql+asyncpg",
    )


@pytest.fixture(scope="function")
async def clean_test_tables():
    """Clean test tables before each test."""
    async with async_session() as session:
        await session.execute(text("DELETE FROM test_transaction_audit"))
        await session.execute(text("DELETE FROM test_transaction_details"))
        await session.execute(text("DELETE FROM test_transactions"))
        await session.commit()


@pytest.mark.integration
class TestDatabaseTransactions:
    """Integration tests for database transaction management."""
    
    @pytest.mark.asyncio
    async def test_basic_transaction_commit(self, setup_test_tables, clean_test_tables):
        """Test that transactions commit changes correctly."""
        # Insert data with explicit transaction and commit
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                    {"name": "test1", "value": 100}
                )
                # Transaction commits automatically at the end of the with block
            
            # Verify the data was committed
            result = await session.execute(text("SELECT COUNT(*) FROM test_transactions"))
            count = (await result.fetchone())[0]
            assert count == 1, "Transaction should have committed the data"
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, setup_test_tables, clean_test_tables):
        """Test that transactions properly roll back changes on error."""
        # Try to insert data that will cause an error
        async with async_session() as session:
            try:
                async with session.begin():
                    # Insert valid data
                    await session.execute(
                        text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                        {"name": "valid", "value": 100}
                    )
                    
                    # Insert invalid data (violates NOT NULL constraint)
                    await session.execute(
                        text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                        {"name": None, "value": 200}
                    )
                    
                    # This should not be reached
                    assert False, "Should have raised an exception"
            except Exception:
                # Exception expected - continue to verification
                pass
            
            # Verify no data was committed (transaction was rolled back)
            result = await session.execute(text("SELECT COUNT(*) FROM test_transactions"))
            count = (await result.fetchone())[0]
            assert count == 0, "Transaction should have been rolled back"
    
    @pytest.mark.asyncio
    async def test_explicit_rollback(self, setup_test_tables, clean_test_tables):
        """Test explicitly rolling back a transaction."""
        async with async_session() as session:
            # Start transaction
            transaction = await session.begin()
            
            # Insert data
            await session.execute(
                text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                {"name": "rollback_test", "value": 300}
            )
            
            # Explicitly roll back the transaction
            await transaction.rollback()
            
            # Verify no data was committed
            result = await session.execute(text("SELECT COUNT(*) FROM test_transactions"))
            count = (await result.fetchone())[0]
            assert count == 0, "Transaction should have been rolled back"
    
    @pytest.mark.asyncio
    async def test_nested_transactions(self, setup_test_tables, clean_test_tables):
        """Test nested transactions with savepoints."""
        async with async_session() as session:
            # Start the outer transaction
            async with session.begin():
                # Insert data in the outer transaction
                await session.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                    {"name": "outer", "value": 400}
                )
                
                # Start a nested transaction (savepoint)
                try:
                    async with session.begin_nested():
                        # Insert data in the nested transaction
                        await session.execute(
                            text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                            {"name": "inner", "value": 500}
                        )
                        
                        # Simulate an error in the nested transaction
                        raise ValueError("Test error in nested transaction")
                        
                except ValueError:
                    # Expected exception - the nested transaction should be rolled back
                    pass
                
                # Insert more data in the outer transaction
                await session.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                    {"name": "outer2", "value": 600}
                )
            
            # Verify only the outer transaction data was committed
            result = await session.execute(
                text("SELECT name, value FROM test_transactions ORDER BY id")
            )
            rows = await result.fetchall()
            
            # Should have two rows: "outer" and "outer2", but not "inner"
            assert len(rows) == 2, "Should have two rows committed"
            assert rows[0][0] == "outer", "First row should be from outer transaction"
            assert rows[1][0] == "outer2", "Second row should be from outer transaction"
            
            # Verify the "inner" row is not present
            result = await session.execute(
                text("SELECT COUNT(*) FROM test_transactions WHERE name = 'inner'")
            )
            count = (await result.fetchone())[0]
            assert count == 0, "Nested transaction should have been rolled back"
    
    @pytest.mark.asyncio
    async def test_multi_table_transaction(self, setup_test_tables, clean_test_tables):
        """Test transactions spanning multiple tables."""
        async with async_session() as session:
            # Start transaction
            async with session.begin():
                # Insert parent record
                result = await session.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value) RETURNING id"),
                    {"name": "parent", "value": 700}
                )
                parent_id = (await result.fetchone())[0]
                
                # Insert child records
                for i in range(3):
                    await session.execute(
                        text("INSERT INTO test_transaction_details (transaction_id, detail) VALUES (:id, :detail)"),
                        {"id": parent_id, "detail": f"Detail {i+1}"}
                    )
            
            # Verify all records were committed
            result = await session.execute(
                text("SELECT COUNT(*) FROM test_transactions WHERE id = :id"),
                {"id": parent_id}
            )
            parent_count = (await result.fetchone())[0]
            assert parent_count == 1, "Parent record should have been committed"
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM test_transaction_details WHERE transaction_id = :id"),
                {"id": parent_id}
            )
            details_count = (await result.fetchone())[0]
            assert details_count == 3, "Child records should have been committed"
    
    @pytest.mark.asyncio
    async def test_transaction_isolation(self, setup_test_tables, clean_test_tables):
        """Test transaction isolation levels."""
        # Start two concurrent sessions
        async with async_session() as session1, async_session() as session2:
            # Session 1: Start a transaction and insert data without committing
            async with session1.begin():
                await session1.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                    {"name": "isolation_test", "value": 800}
                )
                
                # Session 2: Try to read the uncommitted data (should not see it)
                result = await session2.execute(
                    text("SELECT COUNT(*) FROM test_transactions WHERE name = 'isolation_test'")
                )
                count = (await result.fetchone())[0]
                
                # Test with READ COMMITTED isolation (default in PostgreSQL)
                # Session 2 should not see Session 1's uncommitted changes
                assert count == 0, "Session 2 should not see uncommitted changes from Session 1"
            
            # Now that Session 1 has committed, Session 2 should see the changes
            result = await session2.execute(
                text("SELECT COUNT(*) FROM test_transactions WHERE name = 'isolation_test'")
            )
            count = (await result.fetchone())[0]
            assert count == 1, "Session 2 should see committed changes from Session 1"
    
    @pytest.mark.asyncio
    async def test_enhanced_session_transaction(self, setup_test_tables, clean_test_tables):
        """Test transactions with the enhanced session manager."""
        # Create a unique test name for this test
        test_name = f"enhanced_{uuid.uuid4().hex[:8]}"
        
        # Use enhanced async session with transaction
        async with enhanced_async_session() as session:
            # Start a transaction
            async with session.begin():
                await session.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                    {"name": test_name, "value": 900}
                )
                
                # Query within the transaction
                result = await session.execute(
                    text("SELECT COUNT(*) FROM test_transactions WHERE name = :name"),
                    {"name": test_name}
                )
                count = (await result.fetchone())[0]
                assert count == 1, "Data should be visible within the transaction"
            
            # Verify the transaction was committed
            result = await session.execute(
                text("SELECT COUNT(*) FROM test_transactions WHERE name = :name"),
                {"name": test_name}
            )
            count = (await result.fetchone())[0]
            assert count == 1, "Transaction should have been committed"
    
    @pytest.mark.asyncio
    async def test_operation_group_transactions(self, setup_test_tables, clean_test_tables):
        """Test transactions with the operation group."""
        # Create a session operation group
        async with SessionOperationGroup() as group:
            # Create a session
            session = await group.create_session()
            
            # Define transaction operations
            async def insert_operation(session: AsyncSession):
                result = await session.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value) RETURNING id"),
                    {"name": "group_test", "value": 1000}
                )
                return (await result.fetchone())[0]
            
            async def insert_details_operation(session: AsyncSession, parent_id: int):
                await session.execute(
                    text("INSERT INTO test_transaction_details (transaction_id, detail) VALUES (:id, :detail)"),
                    {"id": parent_id, "detail": "Group Detail"}
                )
                return True
            
            # Run operations in a transaction
            operations = [
                insert_operation,
                lambda s: insert_details_operation(s, parent_id=1)  # This will use the ID from the first operation
            ]
            
            # This will fail because we're using a hardcoded ID before it exists
            with pytest.raises(Exception):
                await group.run_in_transaction(session, operations)
            
            # Create a better approach - execute sequentially with dependencies
            parent_id = await group.run_operation(session, insert_operation)
            
            # Start a transaction for the details
            async with session.begin():
                await insert_details_operation(session, parent_id)
            
            # Verify the data was committed
            result = await session.execute(
                text("SELECT COUNT(*) FROM test_transaction_details WHERE transaction_id = :id"),
                {"id": parent_id}
            )
            count = (await result.fetchone())[0]
            assert count == 1, "Transaction should have been committed"
    
    @pytest.mark.asyncio
    async def test_connection_pooled_transactions(self, setup_test_tables, clean_test_tables):
        """Test transactions with the connection pooled sessions."""
        # Create a pooled session factory
        factory = EnhancedPooledSessionFactory()
        
        # Use enhanced pooled session with transaction
        async with enhanced_pool_session(factory=factory) as session:
            # Start a transaction
            async with session.begin():
                await session.execute(
                    text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                    {"name": "pooled_test", "value": 1100}
                )
                
                # Create a savepoint
                savepoint = await session.begin_nested()
                
                try:
                    # Insert data that will be rolled back
                    await session.execute(
                        text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                        {"name": "pooled_savepoint", "value": 1200}
                    )
                    
                    # Rollback to the savepoint
                    await savepoint.rollback()
                    
                    # Insert more data after the savepoint rollback
                    await session.execute(
                        text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                        {"name": "pooled_after_savepoint", "value": 1300}
                    )
                except Exception as e:
                    # If the database doesn't support savepoints, skip this test
                    pytest.skip(f"Database doesn't support savepoints: {str(e)}")
            
            # Verify the correct data was committed
            result = await session.execute(
                text("SELECT name, value FROM test_transactions WHERE name LIKE 'pooled_%' ORDER BY id")
            )
            rows = await result.fetchall()
            
            # Should have two rows: "pooled_test" and "pooled_after_savepoint", but not "pooled_savepoint"
            assert len(rows) == 2, "Should have two rows committed"
            assert rows[0][0] == "pooled_test", "First row should be the initial insert"
            assert rows[1][0] == "pooled_after_savepoint", "Second row should be the post-savepoint insert"
            
            # Verify the savepoint row is not present
            result = await session.execute(
                text("SELECT COUNT(*) FROM test_transactions WHERE name = 'pooled_savepoint'")
            )
            count = (await result.fetchone())[0]
            assert count == 0, "Savepoint should have been rolled back"
    
    @pytest.mark.asyncio
    async def test_concurrent_transactions(self, setup_test_tables, clean_test_tables):
        """Test concurrent transactions with multiple sessions."""
        # Create a unique prefix for this test
        prefix = f"concurrent_{uuid.uuid4().hex[:8]}"
        
        # Define a function to run a transaction
        async def run_transaction(index: int):
            async with async_session() as session:
                async with session.begin():
                    # Insert a record
                    await session.execute(
                        text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                        {"name": f"{prefix}_{index}", "value": 1000 + index}
                    )
                    
                    # Simulate some work
                    await asyncio.sleep(0.1)
                    
                    # Insert a detail record
                    result = await session.execute(
                        text("SELECT id FROM test_transactions WHERE name = :name"),
                        {"name": f"{prefix}_{index}"}
                    )
                    transaction_id = (await result.fetchone())[0]
                    
                    await session.execute(
                        text("INSERT INTO test_transaction_details (transaction_id, detail) VALUES (:id, :detail)"),
                        {"id": transaction_id, "detail": f"Detail for {index}"}
                    )
                    
                    # Simulate more work
                    await asyncio.sleep(0.1)
            
            return index
        
        # Run 5 concurrent transactions
        tasks = [run_transaction(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all transactions were completed
        assert sorted(results) == list(range(5)), "All transactions should have completed"
        
        # Verify all data was committed
        async with async_session() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM test_transactions WHERE name LIKE :prefix"),
                {"prefix": f"{prefix}_%"}
            )
            count = (await result.fetchone())[0]
            assert count == 5, "All transaction records should have been committed"
            
            result = await session.execute(
                text("""
                SELECT COUNT(*) 
                FROM test_transaction_details d
                JOIN test_transactions t ON d.transaction_id = t.id
                WHERE t.name LIKE :prefix
                """),
                {"prefix": f"{prefix}_%"}
            )
            count = (await result.fetchone())[0]
            assert count == 5, "All detail records should have been committed"


@pytest.mark.integration
class TestTransactionCleanup:
    """Tests for proper transaction cleanup in error scenarios."""
    
    @pytest.mark.asyncio
    async def test_transaction_cleanup_on_exception(self, setup_test_tables, clean_test_tables):
        """Test that transactions are properly cleaned up when an exception occurs."""
        # Insert initial data
        async with async_session() as session:
            await session.execute(
                text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                {"name": "cleanup_test", "value": 2000}
            )
            await session.commit()
        
        # Try to update with a transaction that will fail
        try:
            async with async_session() as session:
                async with session.begin():
                    # First update is valid
                    await session.execute(
                        text("UPDATE test_transactions SET value = :value WHERE name = :name"),
                        {"name": "cleanup_test", "value": 2100}
                    )
                    
                    # Simulate an error in the transaction
                    raise ValueError("Simulated error in transaction")
        except ValueError:
            # Expected exception
            pass
        
        # Verify the transaction was rolled back
        async with async_session() as session:
            result = await session.execute(
                text("SELECT value FROM test_transactions WHERE name = 'cleanup_test'")
            )
            value = (await result.fetchone())[0]
            assert value == 2000, "Transaction should have been rolled back"
            
            # Verify the session is still usable
            await session.execute(
                text("UPDATE test_transactions SET value = :value WHERE name = :name"),
                {"name": "cleanup_test", "value": 2200}
            )
            await session.commit()
            
            # Verify the update worked
            result = await session.execute(
                text("SELECT value FROM test_transactions WHERE name = 'cleanup_test'")
            )
            value = (await result.fetchone())[0]
            assert value == 2200, "Session should still be usable after error"
    
    @pytest.mark.asyncio
    async def test_transaction_cleanup_on_cancellation(self, setup_test_tables, clean_test_tables):
        """Test that transactions are properly cleaned up when a task is cancelled."""
        # Insert initial data
        async with async_session() as session:
            await session.execute(
                text("INSERT INTO test_transactions (name, value) VALUES (:name, :value)"),
                {"name": "cancel_test", "value": 3000}
            )
            await session.commit()
        
        # Define a task that will be cancelled
        async def cancellable_task():
            async with async_session() as session:
                async with session.begin():
                    # Update data
                    await session.execute(
                        text("UPDATE test_transactions SET value = :value WHERE name = :name"),
                        {"name": "cancel_test", "value": 3100}
                    )
                    
                    # Long sleep that will be interrupted
                    await asyncio.sleep(10.0)
        
        # Create and start the task
        task = asyncio.create_task(cancellable_task())
        
        # Give the task time to start the transaction
        await asyncio.sleep(0.2)
        
        # Cancel the task
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            # Expected exception
            pass
        
        # Verify the transaction was rolled back
        async with async_session() as session:
            result = await session.execute(
                text("SELECT value FROM test_transactions WHERE name = 'cancel_test'")
            )
            value = (await result.fetchone())[0]
            assert value == 3000, "Transaction should have been rolled back on cancellation"


if __name__ == "__main__":
    # For manual running of tests
    pytest.main(["-xvs", __file__])