# Transaction Management

Proper transaction management is essential for maintaining data integrity and performance in database operations. The uno framework provides modern, async-friendly transaction management utilities.

## Core Transaction Utilities

### Simple Transaction Context Manager

The most basic transaction context manager is provided by `uno.database.transaction`:

```python
from uno.database.transaction import transaction

async def update_user(session, user_id, data):
    async with transaction(session):
        # All operations within this block are part of the same transaction
        user = await session.query(User).filter(User.id == user_id).first()
        for key, value in data.items():
            setattr(user, key, value)
        
        # Transaction is automatically committed on successful exit
        # Or rolled back if an exception occurs
```

### Class-based Transaction Context

For more complex scenarios, you can use the `TransactionContext` class:

```python
from uno.database.transaction import TransactionContext

async def complex_update(session, data):
    async with TransactionContext(session) as tx_session:
        # tx_session is the same as session, but managed by the context
        await tx_session.execute(...)
        
        # Transaction is committed or rolled back automatically
```

## Transaction Factories

The `transaction_factory` module provides utilities to create reusable transaction managers:

```python
from uno.database.transaction_factory import (
    create_transaction_manager,
    create_read_transaction_manager,
    create_write_transaction_manager,
)
from uno.database.session import AsyncSessionFactory

# Create a session factory
session_factory = AsyncSessionFactory()

# Create transaction managers for different roles
read_tx = create_read_transaction_manager(session_factory)
write_tx = create_write_transaction_manager(session_factory)

async def read_data():
    # This creates a session with the "reader" role
    async with read_tx() as session:
        # Query data
        result = await session.execute(query)
        return result.scalars().all()

async def update_data(data):
    # This creates a session with the "writer" role
    async with write_tx() as session:
        # Update data
        user = User(**data)
        session.add(user)
        # Transaction is committed automatically
```

## Read-Only Transactions

Use read-only transactions for operations that don't modify data:

```python
from uno.database.transaction_factory import readonly_transaction

async def get_user_report(session, user_id):
    async with readonly_transaction(session):
        # This transaction is optimized for reading
        # May use different isolation levels or other optimizations
        return await session.execute(...)
```

## Integrating with Database Repositories

Database repositories should use transaction management consistently:

```python
from uno.database.transaction import transaction
from uno.core.result import Success, Failure, Result

class UserRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.write_tx = create_write_transaction_manager(session_factory)
    
    async def update_user(self, user_id, data) -> Result[User, Exception]:
        try:
            async with self.write_tx() as session:
                user = await session.query(User).filter(User.id == user_id).first()
                if not user:
                    return Failure(ValueError(f"User {user_id} not found"))
                
                for key, value in data.items():
                    setattr(user, key, value)
                
                # Transaction is committed automatically
                return Success(user)
        except Exception as e:
            return Failure(e)
```

## Nested Transactions

While not explicitly supported by all databases, the transaction utilities ensure consistent behavior with nested transactions:

```python
async def complex_operation(session):
    async with transaction(session):
        # Outer transaction
        await operation1()
        
        async with transaction(session):
            # Inner transaction - this becomes a savepoint in PostgreSQL
            # or is ignored in databases that don't support savepoints
            await operation2()
        
        # If operation2 fails, only its changes are rolled back
        # If operation1 fails, all changes are rolled back
```

## Best Practices

1. **Always** use transaction context managers rather than manual commit/rollback
2. **Always** ensure that transactions are as short as possible
3. **Use** read-only transactions for read operations
4. **Consider** isolation levels for performance optimization
5. **Avoid** long-running transactions that could block other operations

## Anti-Patterns to Avoid

1. ❌ Manual commit/rollback calls
2. ❌ Inconsistent transaction management across repositories
3. ❌ Overly broad transactions that reduce concurrency
4. ❌ Not handling exceptions within transactions
5. ❌ Using transactions when not necessary (e.g., for simple reads)