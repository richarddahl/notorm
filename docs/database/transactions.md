# Transaction Management

This guide explains how to manage database transactions in the Uno framework.

## Overview

Transactions ensure that database operations either complete fully or not at all, maintaining data consistency. The Uno framework provides multiple approaches to transaction management, from low-level transaction control to high-level patterns like Unit of Work.

## Transaction Basics

At its core, a transaction in Uno can be managed using SQLAlchemy's session transaction API:

```python
from uno.infrastructure.database import UnoDB
from sqlalchemy.ext.asyncio import AsyncSession

# Create database interface
db = UnoDB(connection_string="postgresql+asyncpg://user:password@localhost:5432/dbname")

# Basic transaction example
async def transfer_funds(from_account_id: int, to_account_id: int, amount: float):
    async with db.session() as session:
        async with session.begin():
            # All operations within this block are part of a single transaction
            
            # Debit from account
            await session.execute(
                "UPDATE accounts SET balance = balance - :amount WHERE id = :account_id",
                {"amount": amount, "account_id": from_account_id}
            )
            
            # Credit to account
            await session.execute(
                "UPDATE accounts SET balance = balance + :amount WHERE id = :account_id",
                {"amount": amount, "account_id": to_account_id}
            )
            
            # Transaction is automatically committed if no exception occurs
            # If an exception occurs, the transaction is automatically rolled back
```

## Transaction Context Manager

Uno provides a transaction context manager for more control over transactions:

```python
from uno.infrastructure.database.transaction import transaction
from sqlalchemy.ext.asyncio import AsyncSession

async def transfer_funds(from_account_id: int, to_account_id: int, amount: float):
    # Get a session with transaction
    async with transaction() as session:
        # Debit from account
        await session.execute(
            "UPDATE accounts SET balance = balance - :amount WHERE id = :account_id",
            {"amount": amount, "account_id": from_account_id}
        )
        
        # Credit to account
        await session.execute(
            "UPDATE accounts SET balance = balance + :amount WHERE id = :account_id",
            {"amount": amount, "account_id": to_account_id}
        )
```

The transaction context manager handles:
- Beginning the transaction
- Committing on successful completion
- Rolling back on exceptions
- Proper session cleanup

## Unit of Work Pattern

The Unit of Work pattern provides a higher-level abstraction for transaction management, particularly useful when working with domain entities:

```python
from uno.core.uow import UnitOfWork, get_unit_of_work
from uno.domain.entity import EntityRepository

async def transfer_funds(from_account_id: UUID, to_account_id: UUID, amount: float):
    # Get a Unit of Work
    async with get_unit_of_work() as uow:
        # Get repositories
        account_repo = uow.get_repository(AccountRepository)
        transaction_repo = uow.get_repository(TransactionRepository)
        
        # Get accounts
        from_account = await account_repo.get_by_id(from_account_id)
        to_account = await account_repo.get_by_id(to_account_id)
        
        if not from_account or not to_account:
            raise ValueError("Account not found")
        
        # Perform operations on domain entities
        from_account.withdraw(amount)
        to_account.deposit(amount)
        
        # Create transaction record
        transaction = Transaction.create(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount
        )
        
        # Save changes
        await account_repo.update(from_account)
        await account_repo.update(to_account)
        await transaction_repo.add(transaction)
        
        # Transaction is automatically committed if no exception occurs
```

The Unit of Work pattern:
- Coordinates operations across multiple repositories
- Ensures all changes are part of a single transaction
- Collects and publishes domain events
- Provides a clear boundary for transactions

## Transaction Isolation Levels

Uno allows configuring transaction isolation levels:

```python
from uno.infrastructure.database.transaction import transaction
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def read_accounts(isolation_level="READ COMMITTED"):
    async with transaction(isolation_level=isolation_level) as session:
        # Set transaction isolation level
        await session.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
        
        # Perform read operations
        result = await session.execute("SELECT * FROM accounts")
        return result.fetchall()

# Usage with different isolation levels
accounts_read_committed = await read_accounts("READ COMMITTED")
accounts_repeatable_read = await read_accounts("REPEATABLE READ")
accounts_serializable = await read_accounts("SERIALIZABLE")
```

Common isolation levels:

| Isolation Level | Description |
|-----------------|-------------|
| READ UNCOMMITTED | Lowest isolation; reads uncommitted changes (not recommended) |
| READ COMMITTED | Reads only committed changes; default in PostgreSQL |
| REPEATABLE READ | Ensures repeated reads return same results within transaction |
| SERIALIZABLE | Highest isolation; ensures transactions run as if serialized |

## Nested Transactions

Uno supports nested transactions with savepoints:

```python
from uno.infrastructure.database.transaction import transaction, savepoint

async def complex_operation():
    async with transaction() as session:
        # Main transaction operations
        await session.execute("UPDATE settings SET value = 'new_value' WHERE key = 'app_status'")
        
        try:
            # Create a savepoint
            async with savepoint(session, "user_update"):
                # Operations that might fail
                await session.execute("UPDATE users SET status = 'active' WHERE id = 1")
                await session.execute("INSERT INTO audit_log (user_id, action) VALUES (1, 'status_change')")
                
                # This might raise an exception
                await risky_operation()
                
        except Exception as e:
            # Only the operations since the savepoint are rolled back
            # The main transaction continues
            print(f"User update failed: {e}")
        
        # Continue with main transaction
        await session.execute("UPDATE settings SET last_updated = NOW()")
```

Savepoints allow:
- Rolling back a portion of a transaction
- Continuing the main transaction after a partial rollback
- Implementing more complex transaction flows

## Event-Driven Transactions

Uno integrates transaction management with the event system:

```python
from uno.core.uow import UnitOfWork, get_unit_of_work
from uno.domain.entity import AggregateRoot

async def place_order(customer_id: UUID, items: List[dict]):
    async with get_unit_of_work() as uow:
        # Get repositories
        order_repo = uow.get_repository(OrderRepository)
        inventory_repo = uow.get_repository(InventoryRepository)
        
        # Create order
        order = Order.create(customer_id, items)
        
        # Update inventory
        for item in items:
            product = await inventory_repo.get_by_id(item["product_id"])
            product.reduce_stock(item["quantity"])
            await inventory_repo.update(product)
        
        # Save order
        await order_repo.add(order)
        
        # Events are automatically collected and published after successful commit
        # order.record_event(OrderPlaced(...)) - called inside Order.create()
        # product.record_event(StockReduced(...)) - called inside product.reduce_stock()
```

The Unit of Work automatically:
- Collects events recorded by domain entities
- Publishes events after successful transaction commit
- Discards events if the transaction is rolled back

## Distributed Transactions

For operations spanning multiple databases or services, Uno provides distributed transaction management:

```python
from uno.core.uow.distributed import (
    DistributedUnitOfWork, 
    UnitOfWorkParticipant,
    DatabaseParticipant, 
    EventStoreParticipant
)

# Create participants
db_participant = DatabaseParticipant(db_session)
event_store_participant = EventStoreParticipant(event_store)
external_service_participant = ExternalServiceParticipant(api_client)

# Create distributed UoW
uow = DistributedUnitOfWork(
    participants=[db_participant, event_store_participant, external_service_participant]
)

# Use distributed UoW
async with uow:
    # Operations across multiple systems
    # Database operations
    user = await user_repo.get_by_id(user_id)
    user.update_email(new_email)
    await user_repo.update(user)
    
    # Event store operations
    await event_store.append_events([UserEmailUpdated(user_id=user_id)])
    
    # External service operations
    await external_service.update_user_email(user_id, new_email)
    
    # All participants will be committed or rolled back together
```

Distributed transactions use a two-phase commit protocol:
1. Prepare phase: All participants prepare to commit
2. Commit phase: All participants commit if all prepared successfully
3. Rollback: All participants roll back if any preparation fails

## Retryable Transactions

For handling transient failures, Uno provides retryable transactions:

```python
from uno.infrastructure.database.transaction import retryable_transaction
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure retry behavior
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((OperationalError, InterfaceError))
)
async def update_user_with_retry(user_id: UUID, new_email: str):
    async with retryable_transaction() as session:
        # This transaction will be retried up to 3 times
        # with exponential backoff if certain exceptions occur
        await session.execute(
            "UPDATE users SET email = :email WHERE id = :id",
            {"email": new_email, "id": user_id}
        )
```

## Transaction Hooks

Transaction hooks allow executing code at specific points in the transaction lifecycle:

```python
from uno.infrastructure.database.transaction import transaction, TransactionHooks

class AuditHooks(TransactionHooks):
    """Hooks for audit logging during transactions."""
    
    async def before_begin(self, session):
        """Called before the transaction begins."""
        # Set up transaction context
        await session.execute("SET LOCAL app.transaction_id = :id", {"id": str(uuid4())})
    
    async def after_begin(self, session):
        """Called after the transaction begins."""
        # Log transaction start
        await session.execute(
            "INSERT INTO audit_log (action, details) VALUES ('tx_begin', :details)",
            {"details": "Transaction started"}
        )
    
    async def before_commit(self, session):
        """Called before the transaction commits."""
        # Perform pre-commit validation
        pass
    
    async def after_commit(self, session):
        """Called after the transaction commits."""
        # Log transaction commit
        print("Transaction committed successfully")
    
    async def before_rollback(self, session):
        """Called before the transaction rolls back."""
        # Log rollback reason
        pass
    
    async def after_rollback(self, session):
        """Called after the transaction rolls back."""
        # Log transaction rollback
        print("Transaction rolled back")

# Use hooks with transaction
async with transaction(hooks=AuditHooks()) as session:
    # Transaction operations
    await session.execute("UPDATE users SET status = 'active' WHERE id = :id", {"id": 1})
```

## Transaction Monitoring

Monitor transaction performance and health:

```python
from uno.infrastructure.database.transaction import transaction_metrics
from uno.core.metrics import MetricsRegistry

# Register transaction metrics
metrics = MetricsRegistry()
transaction_metrics.register_metrics(metrics)

# Transaction with metrics
async with transaction(collect_metrics=True) as session:
    # Transaction operations
    await session.execute("UPDATE users SET status = 'active' WHERE id = :id", {"id": 1})

# Get transaction metrics
tx_metrics = metrics.get_metrics("database.transactions")
print(f"Active transactions: {tx_metrics['active_transactions']}")
print(f"Committed transactions: {tx_metrics['committed_transactions']}")
print(f"Rolled back transactions: {tx_metrics['rolled_back_transactions']}")
print(f"Average transaction duration: {tx_metrics['transaction_duration_avg']}ms")
```

## Integration with Repositories

Uno's repositories integrate seamlessly with transactions:

```python
from uno.domain.entity import SQLAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    """Repository for User entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, user_mapper)

# Using repository with transaction
async def update_user_email(user_id: UUID, new_email: str):
    async with transaction() as session:
        # Create repository with session
        user_repo = UserRepository(session)
        
        # Use repository
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        user.email = new_email
        await user_repo.update(user)
```

## Integration with Domain Services

Domain services can use transactions through the Unit of Work pattern:

```python
from uno.domain.entity import DomainServiceWithUnitOfWork
from uno.core.errors.result import Result, Success, Failure

class UserService(DomainServiceWithUnitOfWork[User, UUID]):
    """Service for user operations with built-in transaction support."""
    
    async def update_user_with_profile(
        self, 
        user_id: UUID, 
        email: str, 
        profile_data: dict
    ) -> Result[User, str]:
        """Update a user and their profile in a single transaction."""
        async with self.unit_of_work:
            # Get repositories
            user_repo = self.unit_of_work.get_repository(UserRepository)
            profile_repo = self.unit_of_work.get_repository(ProfileRepository)
            
            # Get user
            user = await user_repo.get_by_id(user_id)
            if not user:
                return Failure(f"User with ID {user_id} not found")
                
            # Update user
            user.email = email
            await user_repo.update(user)
            
            # Update profile
            profile = await profile_repo.get_by_user_id(user_id)
            if profile:
                profile.update(profile_data)
                await profile_repo.update(profile)
            else:
                profile = Profile.create(user_id, profile_data)
                await profile_repo.add(profile)
            
            return Success(user)
```

## Best Practices

### Handling Transaction Scope

```python
# DON'T: Create transactions inside loops
async def update_users(user_ids: List[UUID], new_status: str):
    for user_id in user_ids:
        async with transaction() as session:  # BAD: Creates a separate transaction for each user
            await session.execute(
                "UPDATE users SET status = :status WHERE id = :id",
                {"status": new_status, "id": user_id}
            )

# DO: Create a single transaction around the entire operation
async def update_users(user_ids: List[UUID], new_status: str):
    async with transaction() as session:
        for user_id in user_ids:
            await session.execute(
                "UPDATE users SET status = :status WHERE id = :id",
                {"status": new_status, "id": user_id}
            )
```

### Transaction Size

```python
# DON'T: Create excessively large transactions
async def process_monthly_data():
    async with transaction() as session:  # BAD: Transaction will be very large
        # Process thousands of records
        records = await session.execute("SELECT * FROM monthly_data WHERE processed = FALSE")
        for record in records:
            # Complex processing for each record
            await process_record(record, session)

# DO: Break large operations into smaller transactions
async def process_monthly_data():
    # Fetch IDs outside transaction
    result = await session.execute("SELECT id FROM monthly_data WHERE processed = FALSE")
    record_ids = result.scalars().all()
    
    # Process in batches
    batch_size = 100
    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i+batch_size]
        async with transaction() as session:
            for record_id in batch:
                record = await session.execute(
                    "SELECT * FROM monthly_data WHERE id = :id",
                    {"id": record_id}
                ).fetchone()
                await process_record(record, session)
```

### Handling Exceptions

```python
# DON'T: Catch exceptions without rolling back
async def update_user(user_id: UUID, data: dict):
    async with db.session() as session:
        try:
            await session.begin()
            await session.execute(
                "UPDATE users SET name = :name WHERE id = :id",
                {"name": data["name"], "id": user_id}
            )
            await session.commit()  # BAD: Won't be reached if there's an exception
        except Exception as e:
            # Missing rollback
            print(f"Error: {e}")

# DO: Use context manager or ensure proper rollback
async def update_user(user_id: UUID, data: dict):
    async with db.session() as session:
        async with session.begin():  # This will handle rollback automatically
            await session.execute(
                "UPDATE users SET name = :name WHERE id = :id",
                {"name": data["name"], "id": user_id}
            )
            # Transaction is automatically committed if no exception occurs
```

### Choosing the Right Isolation Level

```python
# DON'T: Use unnecessarily high isolation levels
async def read_user_count():
    async with transaction(isolation_level="SERIALIZABLE") as session:  # BAD: Too strict for a simple read
        result = await session.execute("SELECT COUNT(*) FROM users")
        return result.scalar()

# DO: Use appropriate isolation levels
async def read_user_count():
    async with transaction(isolation_level="READ COMMITTED") as session:  # Good for simple reads
        result = await session.execute("SELECT COUNT(*) FROM users")
        return result.scalar()

# Processing financial transactions might require stronger isolation
async def transfer_funds(from_account: UUID, to_account: UUID, amount: float):
    async with transaction(isolation_level="REPEATABLE READ") as session:
        # Financial transactions may need higher isolation
```

## Advanced Patterns

### Outbox Pattern

The outbox pattern ensures reliable event publishing even if the service fails after committing the transaction:

```python
from uno.infrastructure.database.transaction import transaction
from uno.core.events import Event

async def process_order(order_data: dict):
    async with transaction() as session:
        # Create and save order
        order = Order.create(
            customer_id=order_data["customer_id"],
            items=order_data["items"]
        )
        await session.execute(
            "INSERT INTO orders (id, customer_id, total) VALUES (:id, :customer_id, :total)",
            {
                "id": order.id,
                "customer_id": order.customer_id,
                "total": order.calculate_total()
            }
        )
        
        # Save events to outbox
        order_created_event = OrderCreated(
            order_id=order.id,
            customer_id=order.customer_id,
            total=order.calculate_total()
        )
        
        await session.execute(
            """
            INSERT INTO outbox_events 
            (id, aggregate_type, aggregate_id, event_type, payload, created_at)
            VALUES (:id, :aggregate_type, :aggregate_id, :event_type, :payload, :created_at)
            """,
            {
                "id": str(uuid4()),
                "aggregate_type": "order",
                "aggregate_id": str(order.id),
                "event_type": "order_created",
                "payload": order_created_event.model_dump_json(),
                "created_at": datetime.now(datetime.UTC)
            }
        )
        
        # Transaction is committed, events are in the outbox
        # A separate process will read from the outbox and publish events
```

### Saga Pattern

For long-running business processes that span multiple services:

```python
from uno.infrastructure.database.transaction import transaction
from enum import Enum, auto

class OrderStatus(Enum):
    CREATED = auto()
    PAYMENT_PENDING = auto()
    PAYMENT_COMPLETED = auto()
    INVENTORY_RESERVED = auto()
    SHIPPING_PENDING = auto()
    COMPLETED = auto()
    CANCELLED = auto()

async def create_order_saga(order_data: dict):
    # Start saga
    saga_id = uuid4()
    
    async with transaction() as session:
        # Create order
        order_id = uuid4()
        await session.execute(
            """
            INSERT INTO orders 
            (id, customer_id, total, status)
            VALUES (:id, :customer_id, :total, :status)
            """,
            {
                "id": order_id,
                "customer_id": order_data["customer_id"],
                "total": sum(item["price"] * item["quantity"] for item in order_data["items"]),
                "status": OrderStatus.CREATED.name
            }
        )
        
        # Create saga record
        await session.execute(
            """
            INSERT INTO sagas
            (id, type, status, data, created_at)
            VALUES (:id, :type, :status, :data, :created_at)
            """,
            {
                "id": saga_id,
                "type": "create_order",
                "status": "started",
                "data": json.dumps({"order_id": str(order_id)}),
                "created_at": datetime.now(datetime.UTC)
            }
        )
        
        # Record first step
        await session.execute(
            """
            INSERT INTO saga_steps
            (saga_id, step, status, created_at)
            VALUES (:saga_id, :step, :status, :created_at)
            """,
            {
                "saga_id": saga_id,
                "step": "create_order",
                "status": "completed",
                "created_at": datetime.now(datetime.UTC)
            }
        )
    
    # Saga is started, subsequent steps will be handled by saga orchestrator
    return {"saga_id": saga_id, "order_id": order_id}
```

## Conclusion

Uno provides comprehensive transaction management capabilities, from basic session transactions to advanced patterns like Unit of Work, distributed transactions, and sagas. By choosing the right approach for your use case, you can ensure data consistency while maintaining clean, maintainable code.

For more detailed guidance on related patterns:

- [Unit of Work](../core/uow/index.md): Transaction management with the Unit of Work pattern
- [Event System](../core/events/index.md): Event-driven architecture with transactions
- [Connection Management](connections.md): Database connection management