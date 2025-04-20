# Distributed Unit of Work

The Distributed Unit of Work pattern extends the standard Unit of Work pattern to handle distributed transactions across multiple services, databases, and other resources. It provides a robust way to maintain data consistency in a distributed system by implementing a two-phase commit protocol.

## Overview

In a distributed system, operations often span multiple services or databases. Ensuring transaction consistency across these boundaries is challenging. The Distributed Unit of Work pattern addresses this challenge by providing:

1. Coordination of transactions across multiple services
2. Implementation of the two-phase commit protocol
3. Consistent handling of failures
4. Integration with different types of resources (databases, message queues, event stores, etc.)

## Two-Phase Commit Protocol

The Distributed Unit of Work implements the two-phase commit protocol, which consists of two phases:

1. **Prepare Phase**: All participants prepare their changes but don't commit them. Each participant confirms that it can commit the changes successfully.
2. **Commit Phase**: If all participants successfully prepare, they all commit. If any participant fails to prepare, all participants roll back.

This ensures that either all changes are committed or none are, maintaining consistency across the distributed system.

## Key Components

### DistributedUnitOfWork

The main class that coordinates the distributed transaction:

```python
from uno.core.uow import DistributedUnitOfWork

# Create a distributed UoW
uow = DistributedUnitOfWork()

# Register participants
user_db_id = uow.register_participant("user_db", user_db_participant)
order_db_id = uow.register_participant("order_db", order_db_participant)
event_store_id = uow.register_participant("event_store", event_store_participant)

# Use the UoW with a context manager
async with uow:
    # Perform operations using the participants
    # All changes will be prepared and committed atomically
    # or all changes will be rolled back
```

### TransactionParticipant

Interface for participants in a distributed transaction:

```python
class CustomParticipant(TransactionParticipant):
    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        # Prepare the participant for committing
        # Return Result.ok(True) if successful
        # Return Result.err(Error(...)) if preparation fails
        
    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        # Commit the prepared changes
        # Return Result.ok(True) if successful
        # Return Result.err(Error(...)) if commit fails
        
    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        # Roll back the prepared changes
        # Return Result.ok(True) if successful
        # Return Result.err(Error(...)) if rollback fails
```

### UnitOfWorkParticipant

Adapter that allows regular Unit of Work instances to participate in distributed transactions:

```python
from uno.core.uow import UnitOfWorkParticipant, DatabaseUnitOfWork

# Create a regular UoW
database_uow = DatabaseUnitOfWork(connection_factory)

# Adapt it to participate in distributed transactions
participant = UnitOfWorkParticipant(database_uow, "database")

# Register with distributed UoW
dist_uow = DistributedUnitOfWork()
participant_id = dist_uow.register_participant("database", participant)
```

### EventStoreParticipant

Special participant for event stores that ensures events are only committed when the entire transaction succeeds:

```python
from uno.core.uow import EventStoreParticipant
from uno.core.events import PostgresEventStore, PostgresEventStoreConfig

# Create an event store
config = PostgresEventStoreConfig(connection_string="...")
event_store = PostgresEventStore(config)

# Create the participant
participant = EventStoreParticipant(event_store, "events")
participant_id = dist_uow.register_participant("events", participant)

# Add events to be committed with the transaction
event = UserCreated(user_id="123", name="John Doe")
participant.add_events(dist_uow.transaction.transaction_id, [event])
```

## Usage Example

### Complete Example

Here's a complete example of using the Distributed Unit of Work to coordinate a transaction across a user database, an order database, and an event store:

```python
import asyncio
import uuid
from typing import Dict, List, Any

from uno.core.uow import (
    DistributedUnitOfWork, 
    TransactionParticipant,
    EventStoreParticipant,
)
from uno.core.events import Event, PostgresEventStore, PostgresEventStoreConfig
from uno.core.errors import Result, Error
from uno.core.logging import get_logger

# Define participants for each resource
class UserDatabaseParticipant(TransactionParticipant):
    def __init__(self, db_connection):
        self.db = db_connection
        
    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        try:
            await self.db.begin_transaction()
            return Result.ok(True)
        except Exception as e:
            return Result.err(Error(message=str(e)))
    
    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        try:
            await self.db.commit_transaction()
            return Result.ok(True)
        except Exception as e:
            return Result.err(Error(message=str(e)))
    
    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        try:
            await self.db.rollback_transaction()
            return Result.ok(True)
        except Exception as e:
            return Result.err(Error(message=str(e)))

class OrderDatabaseParticipant(TransactionParticipant):
    # Similar implementation...
    pass

# Define domain events
class UserCreated(Event):
    user_id: str
    name: str

class OrderCreated(Event):
    order_id: str
    user_id: str
    total: float

# Create a service that uses distributed transactions
class UserOrderService:
    def __init__(self, user_db, order_db, event_store):
        self.user_db = user_db
        self.order_db = order_db
        self.event_store = event_store
        
    async def create_user_with_order(self, user_data, order_data) -> dict[str, str]:
        # Create a distributed unit of work
        uow = DistributedUnitOfWork()
        
        # Register participants
        user_participant = UserDatabaseParticipant(self.user_db)
        order_participant = OrderDatabaseParticipant(self.order_db)
        event_participant = EventStoreParticipant(self.event_store, "events")
        
        user_id = uow.register_participant("user_db", user_participant)
        order_id = uow.register_participant("order_db", order_participant)
        event_id = uow.register_participant("events", event_participant)
        
        # Create IDs for new entities
        user_entity_id = str(uuid.uuid4())
        order_entity_id = str(uuid.uuid4())
        
        try:
            # Execute the transaction
            async with uow:
                # Create user
                await self.user_db.create_user(user_entity_id, user_data)
                
                # Create order
                await self.order_db.create_order(order_entity_id, user_entity_id, order_data)
                
                # Create events for the changes
                user_event = UserCreated(
                    user_id=user_entity_id, 
                    name=user_data["name"],
                    aggregate_id=user_entity_id,
                    aggregate_type="User"
                )
                
                order_event = OrderCreated(
                    order_id=order_entity_id,
                    user_id=user_entity_id,
                    total=order_data["total"],
                    aggregate_id=order_entity_id,
                    aggregate_type="Order"
                )
                
                # Add events to be committed
                event_participant.add_events(
                    uow.transaction.transaction_id, 
                    [user_event, order_event]
                )
                
                # Transaction will be committed when context exits
            
            return {
                "user_id": user_entity_id,
                "order_id": order_entity_id
            }
            
        except Exception as e:
            # Transaction will be rolled back when context exits with exception
            get_logger().error(f"Failed to create user with order: {e}")
            raise
```

## Advanced Features

### Transaction Status Monitoring

You can monitor the status of a distributed transaction:

```python
# Get transaction status
status = uow.get_transaction_status()
print(f"Transaction {status['transaction_id']} is {status['status']}")
print(f"Participants: {status['participant_count']}")
print(f"Prepared: {status['prepared_count']}")
print(f"Committed: {status['committed_count']}")
```

### Explicitly Managing Transaction Phases

While the context manager handles the transaction flow automatically, you can also control the phases explicitly if needed:

```python
uow = DistributedUnitOfWork()
# Register participants...

# Manually control the transaction flow
await uow.begin()

try:
    # Perform operations
    
    # Phase 1: Prepare
    prepared = await uow.prepare_all()
    if not prepared:
        await uow.rollback_all()
        raise RuntimeError("Preparation failed")
        
    # Phase 2: Commit
    committed = await uow.commit_all()
    if not committed:
        # This is a critical situation - partial commit
        # May require manual recovery
        raise RuntimeError("Partial commit failure")
        
except Exception:
    await uow.rollback_all()
    raise
```

## Best Practices

### Resource Allocation

- **Minimize Transaction Duration**: Keep distributed transactions as short as possible to reduce lock contention
- **Release Resources**: Always ensure resources are released, even in error scenarios
- **Proper Cleanup**: The Distributed UoW should be used with a context manager to ensure proper cleanup

### Error Handling

- **Proper Error Recovery**: Implement robust error handling in participant implementations
- **Idempotent Operations**: Design participants to support idempotent operations to handle retry scenarios
- **Timeout Handling**: Set appropriate timeouts for prepare, commit, and rollback operations

### Monitoring

- **Transaction Logging**: Enable detailed logging for distributed transactions
- **Health Checks**: Implement health checks for transaction participants
- **Transaction Metrics**: Track metrics like transaction duration, success rate, and failure patterns

## Limitations

- **Performance Overhead**: Two-phase commit adds overhead compared to local transactions
- **Blocking**: Participants may hold locks during the prepare phase, which can lead to contention
- **Coordinator Failure**: If the coordinator fails after prepare but before commit, participants may remain in a prepared state

## Conclusion

The Distributed Unit of Work pattern provides a robust way to maintain data consistency across distributed systems. By implementing the two-phase commit protocol, it ensures that either all changes are committed or none are, preserving consistency even in the face of failures.

While it does add some overhead compared to local transactions, the pattern is essential for scenarios where consistency must be maintained across multiple services or databases.