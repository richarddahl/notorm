# Transaction Management in uno

This guide covers best practices for transaction management in uno.

## Introduction

Robust transaction management is critical for ensuring data integrity in database operations. uno provides several patterns and utilities for handling transactions effectively in both synchronous and asynchronous code.

## Basic Transaction Patterns

### Context Manager Pattern

The recommended approach for working with transactions is to use the context manager pattern with `session.begin()`:

```python
async with enhanced_async_session() as session:
    # Start a transaction
    async with session.begin():
        # All operations within this block will be part of the transaction
        await session.execute(text("UPDATE accounts SET balance = balance - 100 WHERE id = 1"))
        await session.execute(text("INSERT INTO account_logs (account_id, action) VALUES (1, 'DEBIT')"))
        
        # Transaction is automatically committed if all operations succeed
        # or rolled back if any exception occurs
```

### Manual Transaction Management

For more control over the transaction lifecycle, you can manually manage transactions:

```python
async with enhanced_async_session() as session:
    try:
        # Start a transaction
        await session.begin()
        
        # Perform operations
        await session.execute(text("UPDATE accounts SET balance = balance - 100 WHERE id = 1"))
        await session.execute(text("INSERT INTO account_logs (account_id, action) VALUES (1, 'DEBIT')"))
        
        # Commit the transaction
        await session.commit()
    except Exception as e:
        # Roll back the transaction on error
        await session.rollback()
        raise
```

## Advanced Transaction Patterns

### Nested Transactions

uno supports nested transactions using savepoints, which allow you to roll back part of a transaction while keeping other parts:

```python
async with enhanced_async_session() as session:
    # Start outer transaction
    async with session.begin():
        # Perform initial operations
        await session.execute(text("UPDATE accounts SET balance = balance - 100 WHERE id = 1"))
        
        # Start nested transaction (creates a savepoint)
        async with session.begin_nested():
            # Perform operations that might need to be rolled back separately
            await session.execute(text("UPDATE accounts SET status = 'pending' WHERE id = 1"))
            
            # If an error occurs here, only the nested transaction is rolled back
            # to the savepoint, while the outer transaction can continue
            if some_condition:
                raise Exception("Nested operation failed")
        
        # Continue with the outer transaction
        await session.execute(text("INSERT INTO account_logs (account_id, action) VALUES (1, 'DEBIT')"))
        
        # Outer transaction is committed if all operations succeed
```

### Coordinating Multiple Transactions with SessionOperationGroup

For coordinating multiple sessions and transactions, use `SessionOperationGroup`:

```python
async with SessionOperationGroup(name="account_transfer") as group:
    # Create sessions
    session1 = await group.create_session()
    session2 = await group.create_session()
    
    # Define transaction operations
    async def debit_operation(session):
        await session.execute(text("UPDATE accounts SET balance = balance - 100 WHERE id = 1"))
        return True
    
    async def credit_operation(session):
        await session.execute(text("UPDATE accounts SET balance = balance + 100 WHERE id = 2"))
        return True
    
    # Run operations in separate transactions
    debit_task = group.task_group.create_task(
        debit_operation(session1),
        name="debit_op"
    )
    
    credit_task = group.task_group.create_task(
        credit_operation(session2),
        name="credit_op"
    )
    
    # Wait for both to complete
    debit_result = await debit_task
    credit_result = await credit_task
```

### Running Multiple Operations in a Single Transaction

To run multiple operations in a single transaction, use the `run_in_transaction` method:

```python
async with SessionOperationGroup() as group:
    # Create session
    session = await group.create_session()
    
    # Define operations
    async def operation1(session):
        await session.execute(text("UPDATE accounts SET balance = balance - 100 WHERE id = 1"))
        return 1
    
    async def operation2(session):
        await session.execute(text("INSERT INTO account_logs (account_id, action) VALUES (1, 'DEBIT')"))
        return 2
    
    # Run operations in a single transaction
    results = await group.run_in_transaction(
        session,
        [operation1, operation2]
    )
    
    # Results will contain results from each operation [1, 2]
```

### Using EnhancedUnoDb's execute_in_transaction

The `EnhancedUnoDb` class provides an `execute_in_transaction` method that streamlines transaction handling:

```python
from uno.database.enhanced_db import EnhancedUnoDb

db = EnhancedUnoDb()

# Define transaction operations
async def operation1(session):
    await session.execute(text("UPDATE accounts SET balance = balance - 100 WHERE id = 1"))
    return 1

async def operation2(session):
    await session.execute(text("INSERT INTO account_logs (account_id, action) VALUES (1, 'DEBIT')"))
    return 2

# Execute operations in a transaction
results = await db.execute_in_transaction([operation1, operation2])
```

## Transaction Isolation Levels

PostgreSQL supports different transaction isolation levels that control how transactions interact with each other:

1. **READ UNCOMMITTED**: Allows reading uncommitted changes from other transactions (not supported in PostgreSQL, treated as READ COMMITTED)
2. **READ COMMITTED**: Reads only committed changes from other transactions (default in PostgreSQL)
3. **REPEATABLE READ**: Ensures repeated reads within a transaction return the same result
4. **SERIALIZABLE**: Provides the strictest isolation, ensuring transactions behave as if executed serially

You can set the isolation level at the beginning of a transaction:

```python
async with enhanced_async_session() as session:
    # Set isolation level
    await session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    
    # Start transaction
    async with session.begin():
        # All operations in this transaction use SERIALIZABLE isolation
        ...
```

## Concurrency Control Patterns

### Pessimistic Locking

Use the `FOR UPDATE` clause to lock rows for the duration of a transaction:

```python
async with enhanced_async_session() as session:
    async with session.begin():
        # Lock the row to prevent other transactions from modifying it
        result = await session.execute(
            text("SELECT * FROM accounts WHERE id = 1 FOR UPDATE")
        )
        account = await result.fetchone()
        
        # Perform updates on the locked row
        await session.execute(
            text("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
        )
```

### Optimistic Locking

Use a version number or timestamp to detect and handle concurrent modifications:

```python
async with enhanced_async_session() as session:
    async with session.begin():
        # Read current version
        result = await session.execute(
            text("SELECT balance, version FROM accounts WHERE id = 1")
        )
        balance, version = await result.fetchone()
        
        # Update with version check
        result = await session.execute(
            text("""
            UPDATE accounts 
            SET balance = balance - 100, version = version + 1 
            WHERE id = 1 AND version = :version
            RETURNING version
            """),
            {"version": version}
        )
        
        # Check if update succeeded
        update_result = await result.fetchone()
        if not update_result:
            # Version mismatch due to concurrent update
            raise ConcurrentModificationError("Account was modified concurrently")
```

## Error Handling and Retries

### Transaction Retry Pattern

For handling transient errors, use the retry decorator from `EnhancedUnoDb`:

```python
from uno.database.enhanced_db import EnhancedUnoDb
from sqlalchemy.exc import OperationalError

db = EnhancedUnoDb()

@db.retry(max_attempts=3, retry_exceptions=[OperationalError])
async def transfer_with_retry(from_id, to_id, amount):
    async with enhanced_async_session() as session:
        async with session.begin():
            # Update source account
            await session.execute(
                text("UPDATE accounts SET balance = balance - :amount WHERE id = :id"),
                {"id": from_id, "amount": amount}
            )
            
            # Update destination account
            await session.execute(
                text("UPDATE accounts SET balance = balance + :amount WHERE id = :id"),
                {"id": to_id, "amount": amount}
            )
            
            return True
```

### Handling Deadlocks

Deadlocks can occur when transactions wait for each other's locks. They are handled automatically by PostgreSQL (one transaction will be aborted), but you should be prepared to retry:

```python
from sqlalchemy.exc import OperationalError

async def transfer_with_deadlock_handling(from_id, to_id, amount, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with enhanced_async_session() as session:
                async with session.begin():
                    # Lock accounts in consistent order to minimize deadlocks
                    sorted_ids = sorted([from_id, to_id])
                    for id in sorted_ids:
                        await session.execute(
                            text("SELECT * FROM accounts WHERE id = :id FOR UPDATE"),
                            {"id": id}
                        )
                    
                    # Update source account
                    await session.execute(
                        text("UPDATE accounts SET balance = balance - :amount WHERE id = :id"),
                        {"id": from_id, "amount": amount}
                    )
                    
                    # Update destination account
                    await session.execute(
                        text("UPDATE accounts SET balance = balance + :amount WHERE id = :id"),
                        {"id": to_id, "amount": amount}
                    )
                    
                    return True
        except OperationalError as e:
            if "deadlock detected" in str(e) and attempt < max_retries - 1:
                # Wait a short time before retrying
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            raise
```

## Transaction Handling with Cancellation

uno's enhanced async session management handles task cancellation gracefully:

```python
import asyncio
from uno.core.async_utils import timeout

async def operation_with_timeout():
    try:
        # Apply a timeout to the operation
        async with timeout(5.0, "Database operation timed out"):
            async with enhanced_async_session() as session:
                async with session.begin():
                    # Long-running transaction
                    await session.execute(text("UPDATE accounts SET balance = balance - 100 WHERE id = 1"))
                    await asyncio.sleep(10)  # Will cause timeout
    except asyncio.TimeoutError:
        # Handle timeout
        print("Operation timed out, resources automatically cleaned up")
```

## Testing Transactions

For testing transaction behavior, use the `SessionOperationGroup` to coordinate concurrent operations:

```python
@pytest.mark.asyncio
async def test_concurrent_transaction_behavior():
    async with SessionOperationGroup() as group:
        # Define conflicting operations
        async def operation1():
            async with enhanced_async_session() as session:
                async with session.begin():
                    await session.execute(text("SELECT * FROM accounts WHERE id = 1 FOR UPDATE"))
                    await asyncio.sleep(0.5)  # Simulate work
                    await session.execute(text("UPDATE accounts SET balance = 100 WHERE id = 1"))
        
        async def operation2():
            await asyncio.sleep(0.1)  # Start after op1
            async with enhanced_async_session() as session:
                async with session.begin():
                    # This will block until op1 completes
                    await session.execute(text("SELECT * FROM accounts WHERE id = 1 FOR UPDATE"))
                    await session.execute(text("UPDATE accounts SET balance = 200 WHERE id = 1"))
        
        # Run concurrently
        task1 = group.task_group.create_task(operation1())
        task2 = group.task_group.create_task(operation2())
        
        # Wait for both to complete
        await task1
        await task2
        
        # Verify final state
        async with enhanced_async_session() as session:
            result = await session.execute(text("SELECT balance FROM accounts WHERE id = 1"))
            balance = (await result.fetchone())[0]
            assert balance == 200  # Should be the value from op2
```

## Best Practices

1. **Keep Transactions Short**: Long-running transactions can cause contention and performance issues.

2. **Use Appropriate Isolation Levels**: Choose the right isolation level for your needs. Higher levels provide more guarantees but can reduce concurrency.

3. **Handle Errors Appropriately**: Always ensure transactions are properly committed or rolled back, even when errors occur.

4. **Use FOR UPDATE Sparingly**: Excessive row locking can cause contention. Consider optimistic locking for better concurrency.

5. **Lock Resources in a Consistent Order**: To prevent deadlocks, always lock resources (rows, tables) in the same order across all transactions.

6. **Implement Retry Logic for Transient Errors**: Some errors, like deadlocks or serialization failures, can be resolved by retrying the transaction.

7. **Be Mindful of Transaction Boundaries**: Ensure all related operations are within the same transaction to maintain atomicity.

8. **Use ConnectionPoolConfig Options**: Configure `max_lifetime`, `retry_attempts`, and other options to tune transaction behavior.

## Conclusion

Proper transaction management is essential for maintaining data integrity in database applications. uno provides a comprehensive set of tools for working with transactions effectively in async Python applications.

By leveraging context managers, session groups, proper isolation levels, and retry patterns, you can build robust and reliable applications that handle concurrent database operations correctly.