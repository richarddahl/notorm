# Transaction Metrics

The UNO Transaction Metrics framework provides specialized tools for tracking and analyzing database transaction performance within your application.

## Overview

The transaction metrics system provides:

- **Transaction tracking**: Monitor duration, query count, and success/failure rates
- **Query statistics**: Track query count and affected rows per transaction
- **Isolation levels**: Monitor usage of different transaction isolation levels
- **Savepoint tracking**: Track savepoint creation and rollbacks
- **Integration with metrics framework**: Export metrics to the metrics registry

## Key Concepts

### Transaction Metrics

The `TransactionMetrics` class collects detailed metrics for a single transaction:

```python
from uno.core.metrics import TransactionMetrics

# Metrics properties
transaction = await get_transaction("tx123")
print(f"Duration: {transaction.duration_ms}ms")
print(f"Queries: {transaction.query_count}")
print(f"Success: {transaction.success}")
print(f"Isolation: {transaction.isolation_level}")
```

### Transaction Context

The most common way to use transaction metrics is with the `TransactionContext`:

```python
from uno.core.metrics import TransactionContext
from sqlalchemy.ext.asyncio import AsyncSession

async def create_order(session: AsyncSession, order_data):
    # Automatically tracks transaction metrics
    async with TransactionContext(session, "create_order") as tx:
        # Execute queries
        result = await session.execute(...)
        
        # Optionally record detailed query metrics
        await tx.record_query(rows=1)
        
        # Create a savepoint (tracked automatically)
        savepoint = await tx.savepoint()
        
        try:
            # More operations
            await session.execute(...)
        except Exception:
            # Rollback to savepoint (tracked automatically)
            await tx.rollback_to_savepoint(savepoint)
        
        # Transaction automatically commits on exit if no exceptions
        # Metrics automatically recorded
```

### Transaction Metrics Tracker

For more advanced use cases, you can access the metrics tracker directly:

```python
from uno.core.metrics import get_transaction_metrics_tracker

async def analyze_transactions():
    tracker = get_transaction_metrics_tracker()
    
    # Get active transactions
    active = await tracker.get_active_transactions()
    print(f"Active transactions: {len(active)}")
    
    # Get recent transactions
    recent = await tracker.get_recent_transactions(limit=10)
    
    # Get transaction statistics
    stats = await tracker.get_transaction_statistics()
    print(f"Success rate: {stats['success_rate'] * 100:.1f}%")
    print(f"Avg duration: {stats['avg_duration_ms']:.2f}ms")
```

## Integration with Metrics Framework

Transaction metrics are automatically exported to the metrics registry as:

- `db.transaction.duration`: Timer for transaction duration
- `db.transaction.count`: Counter for total transactions
- `db.transaction.success`: Counter for successful transactions
- `db.transaction.failure`: Counter for failed transactions
- `db.query.count`: Counter for database queries
- `db.query.rows`: Histogram for rows affected/returned
- `db.transaction.isolation_level`: Counter for isolation levels
- `db.transaction.savepoint`: Counter for savepoints
- `db.transaction.rollback_to_savepoint`: Counter for rollbacks to savepoints

## Using with Different ORMs

### SQLAlchemy

```python
from sqlalchemy.ext.asyncio import AsyncSession
from uno.core.metrics import TransactionContext

async def sqlalchemy_example(session: AsyncSession):
    async with TransactionContext(session, "sqlalchemy_operation") as tx:
        await session.execute("SELECT * FROM users")
        # Metrics automatically tracked
```

### Asyncpg

```python
import asyncpg
from uno.core.metrics import TransactionContext

async def asyncpg_example():
    conn = await asyncpg.connect(...)
    
    async with TransactionContext(conn, "asyncpg_operation") as tx:
        await conn.execute("SELECT * FROM users")
        # Metrics automatically tracked
```

## Custom Transaction Tracking

For more complex scenarios, you can manually track transactions:

```python
from uno.core.metrics import get_transaction_metrics_tracker

async def custom_transaction_tracking():
    tracker = get_transaction_metrics_tracker()
    tx_id = "custom-tx-123"
    
    # Start tracking
    await tracker.start_transaction(tx_id, isolation_level="SERIALIZABLE")
    
    try:
        # Your transaction logic here
        
        # Record queries
        await tracker.record_query(tx_id, rows=5)
        
        # End with success
        await tracker.end_transaction(tx_id, success=True)
    except Exception as e:
        # End with failure
        await tracker.end_transaction(tx_id, success=False, error=str(e))
        raise
```

## Best Practices

1. **Use TransactionContext**: Prefer the context manager for automatic tracking
2. **Unique transaction IDs**: Use unique IDs for transactions to avoid conflicts
3. **Record detailed metrics**: For critical transactions, record query details
4. **Monitor transaction duration**: Set alerts for slow transactions
5. **Track isolation levels**: Monitor usage of stricter isolation levels
6. **Analyze transaction patterns**: Use metrics to identify patterns in transaction behavior

## Transaction Metrics in Monitoring Systems

When integrated with Prometheus, you can create dashboards to monitor:

- Transaction success rate over time
- Transaction duration percentiles
- Number of active transactions
- Queries per transaction
- Isolation level usage
- Savepoint usage

## Migration from Legacy Transaction Metrics

If you're currently using the legacy transaction metrics module (`uno.core.monitoring.transaction_metrics`), here's how to migrate:

```python
# Legacy usage
from uno.core.monitoring.transaction_metrics import (
    TransactionMetrics, TransactionMetricsTracker,
    get_transaction_metrics_tracker, TransactionContext
)

# New usage
from uno.core.metrics import (
    TransactionMetrics, TransactionMetricsTracker,
    get_transaction_metrics_tracker, TransactionContext
)
```

The new module maintains API compatibility while providing better integration with the logging, error, and metrics frameworks.