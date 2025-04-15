"""
Integration tests for distributed transaction scenarios.

These tests verify that the connection pool handles distributed transactions correctly,
including transaction isolation, rollback scenarios, and transaction metrics.
"""

import asyncio
import logging
import time
import pytest
from typing import Dict, List, Set, Tuple, Optional, Any
import random

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig,
    get_connection_manager,
)
from uno.database.enhanced_pool_session import (
    SessionPoolConfig,
    enhanced_pool_session,
    EnhancedPooledSessionOperationGroup,
)
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
def session_pool_config() -> SessionPoolConfig:
    """Get session pool configuration for testing."""
    return SessionPoolConfig(
        min_sessions=3,
        max_sessions=10,
        target_free_sessions=2,
        idle_timeout=30.0,
        max_lifetime=300.0,
        connection_pool_config=ConnectionPoolConfig(
            initial_size=2,
            min_size=1,
            max_size=5,
        ),
        use_enhanced_connection_pool=True,
    )


@pytest.mark.integration
class TestDistributedTransactions:
    """Integration tests for distributed transactions."""
    
    @pytest.mark.asyncio
    async def test_transaction_isolation(
        self,
        database_config: ConnectionConfig,
        session_pool_config: SessionPoolConfig,
    ):
        """Test transaction isolation levels and behavior."""
        # Create test tables
        async with enhanced_pool_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
            session_pool_config=session_pool_config,
        ) as session:
            await session.execute(text("""
            DROP TABLE IF EXISTS test_transaction_isolation;
            CREATE TABLE test_transaction_isolation (
                id SERIAL PRIMARY KEY,
                counter INTEGER NOT NULL,
                updated_by TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Initialize with one record
            INSERT INTO test_transaction_isolation (counter, updated_by)
            VALUES (0, 'init');
            """))
            await session.commit()
        
        try:
            # Function to update the counter with specified isolation level
            async def update_counter(tx_id: str, isolation_level: str):
                async with enhanced_pool_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                    isolation_level=isolation_level,
                ) as session:
                    # Start transaction explicitly
                    transaction = await session.begin()
                    
                    # Read current counter value
                    result = await session.execute(
                        text("SELECT counter FROM test_transaction_isolation WHERE id = 1")
                    )
                    current_value = (await result.fetchone())[0]
                    
                    # Simulate some processing time (critical for race condition testing)
                    await asyncio.sleep(0.2)
                    
                    # Update counter
                    new_value = current_value + 1
                    await session.execute(
                        text("""
                        UPDATE test_transaction_isolation 
                        SET counter = :counter, updated_by = :updated_by 
                        WHERE id = 1
                        """),
                        {"counter": new_value, "updated_by": f"tx-{tx_id}"}
                    )
                    
                    # Commit transaction
                    await transaction.commit()
                    
                    return new_value
            
            # Test read committed isolation (default)
            # This should allow "lost update" scenario
            tasks = [
                update_counter("RC-1", "READ COMMITTED"),
                update_counter("RC-2", "READ COMMITTED"),
                update_counter("RC-3", "READ COMMITTED"),
            ]
            rc_results = await asyncio.gather(*tasks)
            
            # Read the final value
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            ) as session:
                result = await session.execute(
                    text("""
                    SELECT counter, updated_by FROM test_transaction_isolation WHERE id = 1
                    """)
                )
                row = await result.fetchone()
                rc_final_value = row[0]
                rc_final_updater = row[1]
                
                # In READ COMMITTED, we expect "lost updates"
                # The final value may be less than 3 because transactions may overwrite each other
                assert rc_final_value <= 3, f"Expected final value <= 3, got {rc_final_value}"
                
                # Reset the counter for the next test
                await session.execute(
                    text("""
                    UPDATE test_transaction_isolation 
                    SET counter = 0, updated_by = 'reset' 
                    WHERE id = 1
                    """)
                )
                await session.commit()
            
            # Test repeatable read isolation (stronger)
            # This should prevent "lost update" scenario
            tasks = [
                update_counter("RR-1", "REPEATABLE READ"),
                update_counter("RR-2", "REPEATABLE READ"),
                update_counter("RR-3", "REPEATABLE READ"),
            ]
            
            # These may raise exceptions due to serialization failures
            # We'll use gather with return_exceptions to capture them
            rr_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful updates vs serialization errors
            success_count = sum(1 for r in rr_results if isinstance(r, int))
            error_count = sum(1 for r in rr_results if isinstance(r, Exception))
            
            # Read the final value
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            ) as session:
                result = await session.execute(
                    text("""
                    SELECT counter, updated_by FROM test_transaction_isolation WHERE id = 1
                    """)
                )
                row = await result.fetchone()
                rr_final_value = row[0]
                rr_final_updater = row[1]
                
                # In REPEATABLE READ, we expect the final value to equal the number of successful transactions
                # Some transactions may have been aborted due to serialization failures
                assert rr_final_value == success_count, \
                    f"Expected final value {success_count}, got {rr_final_value}"
                
                # Verify we had some serialization failures in REPEATABLE READ
                # (sometimes all might succeed by chance, but it's unlikely)
                logging.info(
                    f"REPEATABLE READ test: {success_count} successes, {error_count} errors, "
                    f"final value: {rr_final_value}, updater: {rr_final_updater}"
                )
                
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
                await session.execute(text("DROP TABLE IF EXISTS test_transaction_isolation"))
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(
        self,
        database_config: ConnectionConfig,
        session_pool_config: SessionPoolConfig,
    ):
        """Test transaction rollback behavior with proper cleanup."""
        # Create test tables
        async with enhanced_pool_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
            session_pool_config=session_pool_config,
        ) as session:
            await session.execute(text("""
            DROP TABLE IF EXISTS test_transaction_rollback;
            CREATE TABLE test_transaction_rollback (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))
            await session.commit()
        
        try:
            # Test successful transaction
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
                session_pool_config=session_pool_config,
            ) as session:
                # Start a transaction
                transaction = await session.begin()
                
                # Insert some data
                await session.execute(
                    text("INSERT INTO test_transaction_rollback (value) VALUES ('success-1')"),
                )
                await session.execute(
                    text("INSERT INTO test_transaction_rollback (value) VALUES ('success-2')"),
                )
                
                # Commit the transaction
                await transaction.commit()
            
            # Test failed transaction with explicit rollback
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
                session_pool_config=session_pool_config,
            ) as session:
                # Start a transaction
                transaction = await session.begin()
                
                try:
                    # Insert some data
                    await session.execute(
                        text("INSERT INTO test_transaction_rollback (value) VALUES ('rollback-1')"),
                    )
                    
                    # Simulate an error
                    raise ValueError("Simulated error to trigger rollback")
                    
                except ValueError:
                    # Explicitly roll back the transaction
                    await transaction.rollback()
            
            # Test failed transaction with implicit rollback
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
                    # This transaction will be automatically rolled back on exception
                    await session.execute(
                        text("INSERT INTO test_transaction_rollback (value) VALUES ('implicit-rollback-1')"),
                    )
                    
                    # Simulate an error
                    raise ValueError("Simulated error for implicit rollback")
            except ValueError:
                # Expected exception
                pass
            
            # Verify transaction results
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
                session_pool_config=session_pool_config,
            ) as session:
                result = await session.execute(
                    text("SELECT value FROM test_transaction_rollback ORDER BY id")
                )
                values = [row[0] for row in await result.fetchall()]
                
                # Only the successful transaction should have committed data
                assert len(values) == 2, f"Expected 2 rows, found {len(values)}: {values}"
                assert values == ["success-1", "success-2"], f"Unexpected values: {values}"
                
                # Check that the connection pool still works after rollbacks
                await session.execute(
                    text("INSERT INTO test_transaction_rollback (value) VALUES ('after-rollback')"),
                )
                await session.commit()
                
                # Verify the additional insert
                result = await session.execute(
                    text("SELECT COUNT(*) FROM test_transaction_rollback")
                )
                count = (await result.fetchone())[0]
                assert count == 3, f"Expected 3, got {count}"
        
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
                await session.execute(text("DROP TABLE IF EXISTS test_transaction_rollback"))
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_distributed_operations(
        self,
        database_config: ConnectionConfig,
        session_pool_config: SessionPoolConfig,
    ):
        """Test distributed operations across multiple database sessions."""
        # Create test tables
        async with enhanced_pool_session(
            db_driver=database_config.db_driver,
            db_name=database_config.db_name,
            db_host=database_config.db_host,
            db_port=database_config.db_port,
            db_user_pw=database_config.db_user_pw,
            db_role=database_config.db_role,
            session_pool_config=session_pool_config,
        ) as session:
            await session.execute(text("""
            DROP TABLE IF EXISTS test_distributed_orders;
            DROP TABLE IF EXISTS test_distributed_items;
            DROP TABLE IF EXISTS test_distributed_inventory;
            
            CREATE TABLE test_distributed_orders (
                id SERIAL PRIMARY KEY,
                status TEXT NOT NULL,
                total DECIMAL(10, 2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE test_distributed_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES test_distributed_orders(id),
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE test_distributed_inventory (
                product_name TEXT PRIMARY KEY,
                stock_count INTEGER NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Initialize inventory
            INSERT INTO test_distributed_inventory (product_name, stock_count)
            VALUES 
                ('Product A', 100),
                ('Product B', 50),
                ('Product C', 30);
            """))
            await session.commit()
        
        try:
            # Create a session group for coordinated operations
            async with EnhancedPooledSessionOperationGroup(
                name="distributed_operations_test",
                session_pool_config=session_pool_config,
            ) as group:
                # Create sessions for different operations
                orders_session = await group.create_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                )
                
                inventory_session = await group.create_session(
                    db_driver=database_config.db_driver,
                    db_name=database_config.db_name,
                    db_host=database_config.db_host,
                    db_port=database_config.db_port,
                    db_user_pw=database_config.db_user_pw,
                    db_role=database_config.db_role,
                )
                
                # Define distributed operation functions
                async def create_order(session, items: List[Dict[str, Any]]) -> int:
                    """Create an order with items."""
                    # Start transaction
                    transaction = await session.begin()
                    
                    try:
                        # Create order
                        result = await session.execute(
                            text("""
                            INSERT INTO test_distributed_orders (status, total)
                            VALUES ('pending', 0)
                            RETURNING id
                            """)
                        )
                        order_id = (await result.fetchone())[0]
                        
                        # Add items
                        total = 0
                        for item in items:
                            product_name = item["product_name"]
                            quantity = item["quantity"]
                            price = item["price"]
                            
                            await session.execute(
                                text("""
                                INSERT INTO test_distributed_items 
                                (order_id, product_name, quantity, price)
                                VALUES (:order_id, :product_name, :quantity, :price)
                                """),
                                {
                                    "order_id": order_id,
                                    "product_name": product_name,
                                    "quantity": quantity,
                                    "price": price
                                }
                            )
                            
                            total += quantity * price
                        
                        # Update order total
                        await session.execute(
                            text("""
                            UPDATE test_distributed_orders 
                            SET total = :total
                            WHERE id = :order_id
                            """),
                            {"order_id": order_id, "total": total}
                        )
                        
                        # Commit transaction
                        await transaction.commit()
                        return order_id
                        
                    except Exception as e:
                        # Roll back on error
                        await transaction.rollback()
                        raise e
                
                async def update_inventory(session, items: List[Dict[str, Any]]) -> Dict[str, int]:
                    """Update inventory for items."""
                    # Start transaction
                    transaction = await session.begin()
                    
                    try:
                        results = {}
                        
                        for item in items:
                            product_name = item["product_name"]
                            quantity = item["quantity"]
                            
                            # Check current inventory
                            result = await session.execute(
                                text("""
                                SELECT stock_count FROM test_distributed_inventory
                                WHERE product_name = :product_name
                                FOR UPDATE
                                """),
                                {"product_name": product_name}
                            )
                            
                            row = await result.fetchone()
                            if not row:
                                raise ValueError(f"Product not found: {product_name}")
                            
                            current_stock = row[0]
                            
                            if current_stock < quantity:
                                raise ValueError(f"Insufficient stock for {product_name}: {current_stock} < {quantity}")
                            
                            # Update inventory
                            new_stock = current_stock - quantity
                            await session.execute(
                                text("""
                                UPDATE test_distributed_inventory
                                SET stock_count = :new_stock, last_updated = CURRENT_TIMESTAMP
                                WHERE product_name = :product_name
                                """),
                                {"product_name": product_name, "new_stock": new_stock}
                            )
                            
                            results[product_name] = new_stock
                        
                        # Commit transaction
                        await transaction.commit()
                        return results
                        
                    except Exception as e:
                        # Roll back on error
                        await transaction.rollback()
                        raise e
                
                # Define a coordinated operation that manages both operations
                async def process_order(items: List[Dict[str, Any]]) -> Dict[str, Any]:
                    """Process a complete order with inventory updates."""
                    try:
                        # First check if we have sufficient inventory
                        inventory_check = await update_inventory(inventory_session, items)
                        
                        # Then create the order
                        order_id = await create_order(orders_session, items)
                        
                        # Update order status to 'confirmed'
                        await orders_session.execute(
                            text("""
                            UPDATE test_distributed_orders 
                            SET status = 'confirmed'
                            WHERE id = :order_id
                            """),
                            {"order_id": order_id}
                        )
                        await orders_session.commit()
                        
                        return {
                            "success": True,
                            "order_id": order_id,
                            "inventory": inventory_check
                        }
                        
                    except ValueError as e:
                        # Expected for inventory issues
                        return {
                            "success": False,
                            "error": str(e)
                        }
                
                # Process a valid order
                valid_items = [
                    {"product_name": "Product A", "quantity": 5, "price": 10.99},
                    {"product_name": "Product B", "quantity": 3, "price": 24.99},
                ]
                
                valid_result = await process_order(valid_items)
                assert valid_result["success"], f"Valid order failed: {valid_result}"
                
                # Process an order with insufficient inventory
                invalid_items = [
                    {"product_name": "Product C", "quantity": 100, "price": 5.99},
                ]
                
                invalid_result = await process_order(invalid_items)
                assert not invalid_result["success"], "Invalid order should fail"
                assert "Insufficient stock" in invalid_result["error"]
                
                # Verify the state after operations
                # Check orders
                result = await orders_session.execute(
                    text("""
                    SELECT COUNT(*) FROM test_distributed_orders WHERE status = 'confirmed'
                    """)
                )
                confirmed_count = (await result.fetchone())[0]
                assert confirmed_count == 1, f"Expected 1 confirmed order, got {confirmed_count}"
                
                # Check inventory levels
                result = await inventory_session.execute(
                    text("""
                    SELECT product_name, stock_count FROM test_distributed_inventory 
                    ORDER BY product_name
                    """)
                )
                
                inventory = {row[0]: row[1] for row in await result.fetchall()}
                assert inventory["Product A"] == 95, f"Expected 95 Product A, got {inventory['Product A']}"
                assert inventory["Product B"] == 47, f"Expected 47 Product B, got {inventory['Product B']}"
                assert inventory["Product C"] == 30, f"Expected 30 Product C, got {inventory['Product C']}"
        
        finally:
            # Clean up test tables
            async with enhanced_pool_session(
                db_driver=database_config.db_driver,
                db_name=database_config.db_name,
                db_host=database_config.db_host,
                db_port=database_config.db_port,
                db_user_pw=database_config.db_user_pw,
                db_role=database_config.db_role,
            ) as session:
                await session.execute(text("""
                DROP TABLE IF EXISTS test_distributed_items;
                DROP TABLE IF EXISTS test_distributed_orders;
                DROP TABLE IF EXISTS test_distributed_inventory;
                """))
                await session.commit()


if __name__ == "__main__":
    # For manual running of tests
    pytest.main(["-xvs", __file__])