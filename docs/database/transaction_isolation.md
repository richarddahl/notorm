# Transaction Isolation Levels

This guide explains the transaction isolation levels available in PostgreSQL and their appropriate use cases in uno applications.

## Overview

Transaction isolation determines how and when changes made by one transaction are visible to other concurrent transactions. PostgreSQL supports all four isolation levels defined in the SQL standard:

- **READ UNCOMMITTED**
- **READ COMMITTED**
- **REPEATABLE READ**
- **SERIALIZABLE**

In practice, PostgreSQL's implementation of READ UNCOMMITTED behaves like READ COMMITTED, as it does not allow dirty reads.

## Isolation Levels Explained

### READ COMMITTED (Default)

This is PostgreSQL's default isolation level. It guarantees that:

- Queries only see data committed before the query began
- No dirty reads (uncommitted data) are possible
- However, a query might see changes committed during query execution (non-repeatable reads)

**Example Use Cases:**
- General-purpose transactions
- When you need to balance performance with data integrity
- Most OLTP workloads

```python
await db.execute_transaction(
    operations=my_operations,
    isolation_level="READ COMMITTED"
)
```

### REPEATABLE READ

This level guarantees that:

- All queries in a transaction see a snapshot of data as it was at the start of the transaction
- No non-repeatable reads or dirty reads
- However, phantom reads might occur (where new rows appear in a repeated query)

**Example Use Cases:**
- When consistent analysis or reporting is needed
- When you need to run multiple queries and get consistent results
- Read-heavy transactions that scan large datasets

```python
await db.execute_transaction(
    operations=my_operations,
    isolation_level="REPEATABLE READ"
)
```

### SERIALIZABLE

The strictest isolation level. It guarantees that:

- All transactions are executed as if they were run one after another (serially)
- No anomalies (dirty reads, non-repeatable reads, or phantom reads) are possible
- Transactions might need to be retried more often due to serialization failures

**Example Use Cases:**
- Financial transactions requiring strict consistency
- When concurrent transactions might create subtle data integrity issues
- When the application logic depends on consistent behavior

```python
# Option 1: Manual specification
await db.execute_transaction(
    operations=my_operations,
    isolation_level="SERIALIZABLE"
)

# Option 2: Dedicated method with automatic retries
await db.execute_serializable_transaction(
    operations=my_operations,
    timeout_seconds=10.0,
    retry_attempts=3
)
```

## Choosing the Right Isolation Level

Consider these factors when selecting an isolation level:

1. **Consistency Requirements**: How important is it that concurrent transactions see a consistent state?
2. **Performance Needs**: Higher isolation levels may reduce concurrency
3. **Retry Tolerance**: Higher isolation levels may cause more transaction failures requiring retries

## Best Practices

1. **Use the Default When Possible**: Start with READ COMMITTED (the default) and increase isolation only when needed
2. **Keep Transactions Short**: Regardless of isolation level, minimize transaction duration
3. **Handle Retries**: For SERIALIZABLE transactions, always implement retry logic
4. **Set Statement Timeouts**: Prevent long-running transactions from blocking others
5. **Test Concurrent Workloads**: Test your chosen isolation level with realistic concurrency patterns

## Common Patterns and Examples

### Pattern 1: Balance Transfer (SERIALIZABLE)

When transferring amounts between accounts, use SERIALIZABLE to prevent anomalies:

```python
async def transfer_funds(from_account_id, to_account_id, amount):
    async def _execute_transfer(session):
        # Check balance
        from_account = await session.get(Account, from_account_id)
        if from_account.balance < amount:
            raise InsufficientFundsError("Insufficient funds")
        
        # Update accounts
        from_account.balance -= amount
        to_account = await session.get(Account, to_account_id)
        to_account.balance += amount
        
        # Save changes
        session.add(from_account)
        session.add(to_account)
        
        return {"status": "success", "new_balance": from_account.balance}
    
    return await db.execute_serializable_transaction(
        operations=_execute_transfer,
        retry_attempts=3
    )
```

### Pattern 2: Read-Only Analysis (REPEATABLE READ)

For consistent reporting across multiple queries:

```python
async def generate_monthly_report(month, year):
    async def _execute_report(session):
        # Multiple queries that need to see consistent data
        total_sales = await session.execute(sales_query)
        top_products = await session.execute(products_query)
        customer_stats = await session.execute(customers_query)
        
        return {
            "total_sales": total_sales.scalar(),
            "top_products": top_products.scalars().all(),
            "customer_stats": customer_stats.scalars().all(),
        }
    
    return await db.execute_transaction(
        operations=_execute_report,
        isolation_level="REPEATABLE READ"
    )
```

### Pattern 3: High-Throughput Operations (READ COMMITTED)

For maximum throughput when strict consistency isn't critical:

```python
async def log_user_activity(user_id, activity_data):
    async def _execute_logging(session):
        log_entry = ActivityLog(user_id=user_id, data=activity_data)
        session.add(log_entry)
        return log_entry.id
    
    return await db.execute_transaction(
        operations=_execute_logging,
        isolation_level="READ COMMITTED"
    )
```

## Error Handling

The enhanced transaction support in uno includes specialized error types:

- `DatabaseTransactionError`: Base class for transaction errors
- `DatabaseTransactionRollbackError`: When a transaction is rolled back
- `DatabaseTransactionConflictError`: For deadlocks or serialization failures
- `DatabaseQueryTimeoutError`: When a transaction times out

All transaction-related errors include useful context to help with debugging and retry logic.

## Deadlock Detection and Handling

For complex transactions that might encounter deadlocks, use the retry capabilities:

```python
# The enhanced database operations automatically handle deadlocks
# with configurable retry logic
await db.execute_transaction(
    operations=complex_operations,
    isolation_level="REPEATABLE READ",
    timeout_seconds=5.0  # Set reasonable timeouts
)
```

The `pg_error_handler` module provides utilities to detect specific PostgreSQL error types:

```python
from uno.database.pg_error_handler import is_deadlock_error, is_serialization_error

# Can be used in custom retry logic
if is_deadlock_error(exception):
    # Handle deadlock specifically
    pass
```

## Advanced: Setting Transaction Characteristics

In addition to isolation levels, you can also set other transaction characteristics using SQL:

```python
async def complex_transaction(session):
    # Set transaction to read-only
    await session.execute("SET TRANSACTION READ ONLY")
    
    # Set other characteristics
    await session.execute("SET TRANSACTION DEFERRABLE")
    
    # Execute queries...
    result = await session.execute(query)
    
    return result.scalars().all()
```

## Performance Considerations

Higher isolation levels come with potential performance costs:

1. **READ COMMITTED**: Best performance, minimal blocking
2. **REPEATABLE READ**: Moderate performance impact
3. **SERIALIZABLE**: Highest impact, may require more retries

Monitor your application's performance and adjust isolation levels based on actual workload patterns.