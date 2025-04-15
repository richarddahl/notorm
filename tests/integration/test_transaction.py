"""
Integration tests for transaction handling.

These tests verify that transaction handling works correctly with a real database,
focusing on isolation levels, concurrency control, and error handling.
"""

import os
import asyncio
import logging
import time
import pytest
from typing import List, Dict, Any, Optional, Tuple, Set
import random
import string

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.exc import (
    OperationalError, 
    SQLAlchemyError, 
    IntegrityError,
    TimeoutError,
)

from uno.database.config import ConnectionConfig
from uno.database.enhanced_session import (
    enhanced_async_session,
    SessionOperationGroup,
)
from uno.database.enhanced_db import EnhancedUnoDb
from uno.database.session import async_session
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
async def setup_test_tables():
    """Set up test tables for transaction tests."""
    async with async_session() as session:
        # Create test tables for transaction tests
        await session.execute(text("""
        DROP TABLE IF EXISTS transaction_test_accounts;
        DROP TABLE IF EXISTS transaction_test_logs;
        
        CREATE TABLE transaction_test_accounts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            balance DECIMAL(15, 2) NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT positive_balance CHECK (balance >= 0)
        );
        
        CREATE TABLE transaction_test_logs (
            id SERIAL PRIMARY KEY,
            account_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            amount DECIMAL(15, 2),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            transaction_id VARCHAR(50),
            CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES transaction_test_accounts(id)
        );
        
        -- Insert initial test data
        INSERT INTO transaction_test_accounts (name, balance, version) VALUES
        ('Account A', 1000.00, 1),
        ('Account B', 500.00, 1),
        ('Account C', 250.00, 1);
        """))
        await session.commit()
    
    # Return a cleanup function
    def cleanup():
        pass
    
    return cleanup


@pytest.fixture(scope="module")
def logger() -> logging.Logger:
    """Get a logger for testing."""
    logger = logging.getLogger("test.transaction_integration")
    logger.setLevel(logging.DEBUG)
    return logger


def random_transaction_id() -> str:
    """Generate a random transaction ID for testing."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


@pytest.mark.integration
@pytest.mark.asyncio
class TestTransactionIntegration:
    """Integration tests for transaction handling."""
    
    async def test_basic_transaction_commit(self, setup_test_tables, database_config):
        """Test basic transaction commit."""
        # Generate a unique transaction ID
        tx_id = random_transaction_id()
        
        # Use enhanced async session
        async with enhanced_async_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
        ) as session:
            # Start a transaction
            async with session.begin():
                # Update account balance
                await session.execute(
                    text("UPDATE transaction_test_accounts SET balance = balance - 100 WHERE id = 1")
                )
                
                # Log the transaction
                await session.execute(
                    text("""
                    INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                    VALUES (1, 'DEBIT', 100, :tx_id)
                    """),
                    {"tx_id": tx_id}
                )
                
                # Transaction is automatically committed at the end of the context
        
        # Verify changes in a separate session
        async with async_session() as verify_session:
            # Check account balance
            result = await verify_session.execute(
                text("SELECT balance FROM transaction_test_accounts WHERE id = 1")
            )
            balance = (await result.fetchone())[0]
            assert balance == 900.00
            
            # Check log entry
            result = await verify_session.execute(
                text("SELECT COUNT(*) FROM transaction_test_logs WHERE transaction_id = :tx_id"),
                {"tx_id": tx_id}
            )
            count = (await result.fetchone())[0]
            assert count == 1

    async def test_transaction_rollback(self, setup_test_tables, database_config):
        """Test transaction rollback on error."""
        # Generate a unique transaction ID
        tx_id = random_transaction_id()
        
        # Use enhanced async session
        async with enhanced_async_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
        ) as session:
            try:
                # Start a transaction
                async with session.begin():
                    # Update account balance
                    await session.execute(
                        text("UPDATE transaction_test_accounts SET balance = balance - 600 WHERE id = 2")
                    )
                    
                    # Log the transaction
                    await session.execute(
                        text("""
                        INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                        VALUES (2, 'DEBIT', 600, :tx_id)
                        """),
                        {"tx_id": tx_id}
                    )
                    
                    # This should trigger the CHECK constraint and cause a rollback
                    await session.execute(
                        text("UPDATE transaction_test_accounts SET balance = -100 WHERE id = 3")
                    )
                    
                    # This should not be executed
                    await session.execute(
                        text("""
                        INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                        VALUES (3, 'DEBIT', 350, :tx_id)
                        """),
                        {"tx_id": tx_id}
                    )
            except SQLAlchemyError:
                # Expected error
                pass
        
        # Verify rollback occurred in a separate session
        async with async_session() as verify_session:
            # Check account balances - should be unchanged
            result = await verify_session.execute(
                text("SELECT balance FROM transaction_test_accounts WHERE id = 2")
            )
            balance = (await result.fetchone())[0]
            assert balance == 500.00
            
            # Check log entries - should have none for this transaction
            result = await verify_session.execute(
                text("SELECT COUNT(*) FROM transaction_test_logs WHERE transaction_id = :tx_id"),
                {"tx_id": tx_id}
            )
            count = (await result.fetchone())[0]
            assert count == 0

    async def test_concurrent_transactions(self, setup_test_tables, database_config):
        """Test concurrent transactions and row locking."""
        # Generate unique transaction IDs
        tx_id1 = random_transaction_id()
        tx_id2 = random_transaction_id()
        
        # Create a session operation group
        async with SessionOperationGroup(name="concurrent_tx_test") as group:
            # Define transaction operations
            async def transaction1():
                async with enhanced_async_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                ) as session:
                    # Start a transaction
                    async with session.begin():
                        # Lock the row with FOR UPDATE
                        await session.execute(
                            text("SELECT * FROM transaction_test_accounts WHERE id = 1 FOR UPDATE")
                        )
                        
                        # Update and slow down to allow concurrent transaction attempt
                        await session.execute(
                            text("UPDATE transaction_test_accounts SET balance = balance - 50, version = version + 1 WHERE id = 1")
                        )
                        
                        # Log the transaction
                        await session.execute(
                            text("""
                            INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                            VALUES (1, 'DEBIT', 50, :tx_id)
                            """),
                            {"tx_id": tx_id1}
                        )
                        
                        # Sleep to simulate slow operation
                        await asyncio.sleep(0.5)
                        
                        # Transaction is automatically committed at the end of the context
                return "tx1_success"
            
            async def transaction2():
                # Small delay to ensure transaction1 starts first
                await asyncio.sleep(0.1)
                
                async with enhanced_async_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                    # Short timeout to prevent long test run
                    timeout_seconds=2.0
                ) as session:
                    try:
                        # Start a transaction
                        async with session.begin():
                            # Try to lock the same row - should block until tx1 completes
                            await session.execute(
                                text("SELECT * FROM transaction_test_accounts WHERE id = 1 FOR UPDATE")
                            )
                            
                            # If we get here, the first transaction has completed
                            # Read the updated version
                            result = await session.execute(
                                text("SELECT balance, version FROM transaction_test_accounts WHERE id = 1")
                            )
                            row = await result.fetchone()
                            balance, version = row
                            
                            # Update the row
                            await session.execute(
                                text("""
                                UPDATE transaction_test_accounts 
                                SET balance = balance - 25, version = version + 1 
                                WHERE id = 1 AND version = :version
                                """),
                                {"version": version}
                            )
                            
                            # Log the transaction
                            await session.execute(
                                text("""
                                INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                                VALUES (1, 'DEBIT', 25, :tx_id)
                                """),
                                {"tx_id": tx_id2}
                            )
                            
                        return "tx2_success"
                    except SQLAlchemyError as e:
                        return f"tx2_error: {str(e)}"
            
            # Run both transactions in parallel
            task1 = group.task_group.create_task(transaction1(), name="tx1")
            task2 = group.task_group.create_task(transaction2(), name="tx2")
            
            # Wait for both to complete
            result1 = await task1
            result2 = await task2
            
            # Verify both transactions succeeded
            assert result1 == "tx1_success"
            assert result2 == "tx2_success"
            
            # Verify final balance in a separate session
            async with async_session() as verify_session:
                # Check final account balance (original 1000 - 50 - 25 = 925)
                result = await verify_session.execute(
                    text("SELECT balance, version FROM transaction_test_accounts WHERE id = 1")
                )
                balance, version = await result.fetchone()
                assert balance == 925.00
                assert version == 3  # Initial version 1, then 2 updates
                
                # Check both log entries exist
                result = await verify_session.execute(
                    text("SELECT COUNT(*) FROM transaction_test_logs WHERE transaction_id IN (:tx_id1, :tx_id2)"),
                    {"tx_id1": tx_id1, "tx_id2": tx_id2}
                )
                count = (await result.fetchone())[0]
                assert count == 2

    async def test_transaction_isolation_levels(self, setup_test_tables, database_config):
        """Test different transaction isolation levels."""
        # Use SERIALIZABLE isolation to ensure strict transaction isolation
        async with enhanced_async_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
        ) as session:
            # Set isolation level
            await session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
            
            # Start a transaction
            async with session.begin():
                # Read account 3 balance
                result = await session.execute(
                    text("SELECT balance FROM transaction_test_accounts WHERE id = 3")
                )
                balance = (await result.fetchone())[0]
                
                # Update the balance
                await session.execute(
                    text("UPDATE transaction_test_accounts SET balance = balance + 100 WHERE id = 3")
                )
                
                # In a concurrent session, verify the change is not visible
                async with async_session() as verify_session:
                    result = await verify_session.execute(
                        text("SELECT balance FROM transaction_test_accounts WHERE id = 3")
                    )
                    concurrent_balance = (await result.fetchone())[0]
                    
                    # Changes should not be visible until transaction commits
                    assert concurrent_balance == 250.00
                    assert concurrent_balance != balance + 100
            
            # Transaction should now be committed
            
            # Verify changes are now visible
            async with async_session() as final_verify_session:
                result = await final_verify_session.execute(
                    text("SELECT balance FROM transaction_test_accounts WHERE id = 3")
                )
                final_balance = (await result.fetchone())[0]
                assert final_balance == 350.00

    async def test_optimistic_locking(self, setup_test_tables, database_config):
        """Test optimistic locking with version numbers."""
        # Generate unique transaction IDs
        tx_id1 = random_transaction_id()
        tx_id2 = random_transaction_id()
        
        # Create a session operation group
        async with SessionOperationGroup(name="optimistic_lock_test") as group:
            # Define transaction operations
            async def transaction1():
                async with enhanced_async_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                ) as session:
                    # Read current version
                    result = await session.execute(
                        text("SELECT version FROM transaction_test_accounts WHERE id = 2")
                    )
                    version = (await result.fetchone())[0]
                    
                    # Wait a bit to allow transaction2 to read same version
                    await asyncio.sleep(0.2)
                    
                    # Start a transaction
                    async with session.begin():
                        # Update with version check (optimistic locking)
                        result = await session.execute(
                            text("""
                            UPDATE transaction_test_accounts 
                            SET balance = balance - 100, version = version + 1 
                            WHERE id = 2 AND version = :version
                            RETURNING version
                            """),
                            {"version": version}
                        )
                        
                        # Check if update succeeded
                        update_result = await result.fetchone()
                        if update_result:
                            # Log the transaction
                            await session.execute(
                                text("""
                                INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                                VALUES (2, 'DEBIT', 100, :tx_id)
                                """),
                                {"tx_id": tx_id1}
                            )
                            return "tx1_success"
                        else:
                            return "tx1_optimistic_lock_failed"
            
            async def transaction2():
                # Small delay to ensure we read same version
                await asyncio.sleep(0.1)
                
                async with enhanced_async_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                ) as session:
                    # Read current version
                    result = await session.execute(
                        text("SELECT version FROM transaction_test_accounts WHERE id = 2")
                    )
                    version = (await result.fetchone())[0]
                    
                    # Wait a bit to ensure transaction1 commits first
                    await asyncio.sleep(0.3)
                    
                    # Start a transaction
                    async with session.begin():
                        # Update with version check (optimistic locking)
                        result = await session.execute(
                            text("""
                            UPDATE transaction_test_accounts 
                            SET balance = balance - 50, version = version + 1 
                            WHERE id = 2 AND version = :version
                            RETURNING version
                            """),
                            {"version": version}
                        )
                        
                        # Check if update succeeded
                        update_result = await result.fetchone()
                        if update_result:
                            # Log the transaction
                            await session.execute(
                                text("""
                                INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                                VALUES (2, 'DEBIT', 50, :tx_id)
                                """),
                                {"tx_id": tx_id2}
                            )
                            return "tx2_success"
                        else:
                            return "tx2_optimistic_lock_failed"
            
            # Run both transactions in parallel
            task1 = group.task_group.create_task(transaction1(), name="tx1")
            task2 = group.task_group.create_task(transaction2(), name="tx2")
            
            # Wait for both to complete
            result1 = await task1
            result2 = await task2
            
            # Verify first transaction succeeded and second failed
            assert result1 == "tx1_success"
            assert result2 == "tx2_optimistic_lock_failed"
            
            # Verify final state in a separate session
            async with async_session() as verify_session:
                # Check final account balance and version
                result = await verify_session.execute(
                    text("SELECT balance, version FROM transaction_test_accounts WHERE id = 2")
                )
                balance, version = await result.fetchone()
                assert balance == 400.00  # Original 500 - 100 from tx1
                assert version == 2  # Incremented once by tx1
                
                # Check only the first transaction's log entry exists
                result = await verify_session.execute(
                    text("SELECT COUNT(*) FROM transaction_test_logs WHERE transaction_id = :tx_id"),
                    {"tx_id": tx_id1}
                )
                count1 = (await result.fetchone())[0]
                assert count1 == 1
                
                result = await verify_session.execute(
                    text("SELECT COUNT(*) FROM transaction_test_logs WHERE transaction_id = :tx_id"),
                    {"tx_id": tx_id2}
                )
                count2 = (await result.fetchone())[0]
                assert count2 == 0

    async def test_transaction_retry(self, setup_test_tables, database_config, logger):
        """Test transaction retry logic."""
        # Create an EnhancedUnoDb instance
        db = EnhancedUnoDb(logger=logger)
        
        # Define a function that may fail and need retries
        @db.retry(max_attempts=3, retry_exceptions=[OperationalError])
        async def transfer_with_retry(from_id, to_id, amount, tx_id):
            async with enhanced_async_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            ) as session:
                # Start a transaction
                async with session.begin():
                    # Read source account
                    result = await session.execute(
                        text("SELECT balance FROM transaction_test_accounts WHERE id = :id"),
                        {"id": from_id}
                    )
                    from_balance = (await result.fetchone())[0]
                    
                    # Check funds
                    if from_balance < amount:
                        raise ValueError("Insufficient funds")
                    
                    # Update source account
                    await session.execute(
                        text("""
                        UPDATE transaction_test_accounts 
                        SET balance = balance - :amount 
                        WHERE id = :id
                        """),
                        {"id": from_id, "amount": amount}
                    )
                    
                    # Log debit
                    await session.execute(
                        text("""
                        INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                        VALUES (:id, 'DEBIT', :amount, :tx_id)
                        """),
                        {"id": from_id, "amount": amount, "tx_id": tx_id}
                    )
                    
                    # Simulate potential failure for retry
                    if random.random() < 0.5:  # 50% chance
                        raise OperationalError("Simulated transient error", None, None)
                    
                    # Update destination account
                    await session.execute(
                        text("""
                        UPDATE transaction_test_accounts 
                        SET balance = balance + :amount 
                        WHERE id = :id
                        """),
                        {"id": to_id, "amount": amount}
                    )
                    
                    # Log credit
                    await session.execute(
                        text("""
                        INSERT INTO transaction_test_logs (account_id, action, amount, transaction_id) 
                        VALUES (:id, 'CREDIT', :amount, :tx_id)
                        """),
                        {"id": to_id, "amount": amount, "tx_id": tx_id}
                    )
                    
                    return True
        
        # Generate unique transaction ID
        tx_id = random_transaction_id()
        
        # Retry-enabled transfer
        success = await transfer_with_retry(1, 3, 75, tx_id)
        assert success is True
        
        # Verify final state in a separate session
        async with async_session() as verify_session:
            # Check final account balances
            result = await verify_session.execute(
                text("SELECT balance FROM transaction_test_accounts WHERE id = 1")
            )
            from_balance = (await result.fetchone())[0]
            
            result = await verify_session.execute(
                text("SELECT balance FROM transaction_test_accounts WHERE id = 3")
            )
            to_balance = (await result.fetchone())[0]
            
            # Verify balances match expected values
            # Account 1 should have 925 - 75 = 850
            # Account 3 should have 350 + 75 = 425
            assert from_balance == 850.00
            assert to_balance == 425.00
            
            # Check that both log entries exist with the same transaction ID
            result = await verify_session.execute(
                text("""
                SELECT COUNT(*) FROM transaction_test_logs 
                WHERE transaction_id = :tx_id
                """),
                {"tx_id": tx_id}
            )
            count = (await result.fetchone())[0]
            assert count == 2  # One debit and one credit
            
            # Verify the debit and credit logs
            result = await verify_session.execute(
                text("""
                SELECT account_id, action, amount FROM transaction_test_logs 
                WHERE transaction_id = :tx_id
                ORDER BY action
                """),
                {"tx_id": tx_id}
            )
            logs = await result.fetchall()
            
            assert len(logs) == 2
            credit_log, debit_log = logs  # Ordered by action CREDIT, DEBIT
            
            assert debit_log[0] == 1  # account_id
            assert debit_log[1] == 'DEBIT'  # action
            assert debit_log[2] == 75.00  # amount
            
            assert credit_log[0] == 3  # account_id
            assert credit_log[1] == 'CREDIT'  # action
            assert credit_log[2] == 75.00  # amount

    async def test_cleanup_test_tables(self, database_config):
        """Clean up test tables."""
        async with async_session() as session:
            await session.execute(text("""
            DROP TABLE IF EXISTS transaction_test_logs;
            DROP TABLE IF EXISTS transaction_test_accounts;
            """))
            await session.commit()