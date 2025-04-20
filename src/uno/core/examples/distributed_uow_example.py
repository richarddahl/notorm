"""
Distributed Unit of Work Example

This example demonstrates how to use the Distributed Unit of Work pattern
to coordinate transactions across multiple databases and services.
"""

import asyncio
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from uno.core.uow import (
    DistributedUnitOfWork,
    DatabaseUnitOfWork,
    TransactionParticipant,
    EventStoreParticipant,
)
from uno.core.events import Event, PostgresEventStore, PostgresEventStoreConfig
from uno.core.errors import Result, Error
from uno.core.logging import get_logger, configure_logging


# Define domain events
class UserCreated(Event):
    """Event indicating a user was created."""

    user_id: str
    email: str
    username: str


class OrderCreated(Event):
    """Event indicating an order was created."""

    order_id: str
    user_id: str
    total_amount: float
    items: list[dict[str, Any]]


# Mock databases
class UserDatabase:
    """Mock user database for demonstration."""

    def __init__(self):
        """Initialize the user database."""
        self.users: dict[str, dict[str, Any]] = {}
        self.in_transaction = False
        self.logger = get_logger("users.db")

    async def connect(self) -> "UserDatabase":
        """Connect to the database."""
        self.logger.info("Connected to user database")
        return self

    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        self.logger.info("Beginning user database transaction")
        self.in_transaction = True

    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        self.logger.info("Committing user database transaction")
        self.in_transaction = False

    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        self.logger.info("Rolling back user database transaction")
        self.in_transaction = False

    async def create_user(self, user_id: str, email: str, username: str) -> None:
        """Create a new user."""
        if not self.in_transaction:
            raise RuntimeError("Not in a transaction")

        self.users[user_id] = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "created_at": datetime.now(UTC),
        }
        self.logger.info(f"Created user {user_id}: {username}")


class OrderDatabase:
    """Mock order database for demonstration."""

    def __init__(self):
        """Initialize the order database."""
        self.orders: dict[str, dict[str, Any]] = {}
        self.in_transaction = False
        self.logger = get_logger("orders.db")

    async def connect(self) -> "OrderDatabase":
        """Connect to the database."""
        self.logger.info("Connected to order database")
        return self

    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        self.logger.info("Beginning order database transaction")
        self.in_transaction = True

    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        self.logger.info("Committing order database transaction")
        self.in_transaction = False

    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        self.logger.info("Rolling back order database transaction")
        self.in_transaction = False

    async def create_order(
        self,
        order_id: str,
        user_id: str,
        total_amount: float,
        items: list[dict[str, Any]],
    ) -> None:
        """Create a new order."""
        if not self.in_transaction:
            raise RuntimeError("Not in a transaction")

        self.orders[order_id] = {
            "order_id": order_id,
            "user_id": user_id,
            "total_amount": total_amount,
            "items": items,
            "created_at": datetime.now(UTC),
        }
        self.logger.info(f"Created order {order_id} for user {user_id}")


# Transaction participants
class UserDatabaseParticipant(TransactionParticipant):
    """Transaction participant for the user database."""

    def __init__(self, db: UserDatabase):
        """Initialize the user database participant."""
        self.db = db
        self.logger = get_logger("users.participant")
        self._prepared_tx: dict[str, bool] = {}

    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        """Prepare the user database for a transaction."""
        try:
            await self.db.begin_transaction()
            self._prepared_tx[transaction_id] = True
            self.logger.info(f"Prepared user database for transaction {transaction_id}")
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to prepare user database: {e}")
            return Result.err(
                Error(
                    message=f"Failed to prepare user database: {str(e)}",
                    error_code="USER_DB_PREPARE_FAILED",
                )
            )

    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        """Commit the user database transaction."""
        if transaction_id not in self._prepared_tx:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared",
                    error_code="TX_NOT_PREPARED",
                )
            )

        try:
            await self.db.commit_transaction()
            del self._prepared_tx[transaction_id]
            self.logger.info(
                f"Committed user database for transaction {transaction_id}"
            )
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to commit user database: {e}")
            return Result.err(
                Error(
                    message=f"Failed to commit user database: {str(e)}",
                    error_code="USER_DB_COMMIT_FAILED",
                )
            )

    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        """Rollback the user database transaction."""
        if transaction_id not in self._prepared_tx:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared",
                    error_code="TX_NOT_PREPARED",
                )
            )

        try:
            await self.db.rollback_transaction()
            del self._prepared_tx[transaction_id]
            self.logger.info(
                f"Rolled back user database for transaction {transaction_id}"
            )
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to rollback user database: {e}")
            return Result.err(
                Error(
                    message=f"Failed to rollback user database: {str(e)}",
                    error_code="USER_DB_ROLLBACK_FAILED",
                )
            )


class OrderDatabaseParticipant(TransactionParticipant):
    """Transaction participant for the order database."""

    def __init__(self, db: OrderDatabase):
        """Initialize the order database participant."""
        self.db = db
        self.logger = get_logger("orders.participant")
        self._prepared_tx: dict[str, bool] = {}

    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        """Prepare the order database for a transaction."""
        try:
            await self.db.begin_transaction()
            self._prepared_tx[transaction_id] = True
            self.logger.info(
                f"Prepared order database for transaction {transaction_id}"
            )
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to prepare order database: {e}")
            return Result.err(
                Error(
                    message=f"Failed to prepare order database: {str(e)}",
                    error_code="ORDER_DB_PREPARE_FAILED",
                )
            )

    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        """Commit the order database transaction."""
        if transaction_id not in self._prepared_tx:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared",
                    error_code="TX_NOT_PREPARED",
                )
            )

        try:
            await self.db.commit_transaction()
            del self._prepared_tx[transaction_id]
            self.logger.info(
                f"Committed order database for transaction {transaction_id}"
            )
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to commit order database: {e}")
            return Result.err(
                Error(
                    message=f"Failed to commit order database: {str(e)}",
                    error_code="ORDER_DB_COMMIT_FAILED",
                )
            )

    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        """Rollback the order database transaction."""
        if transaction_id not in self._prepared_tx:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared",
                    error_code="TX_NOT_PREPARED",
                )
            )

        try:
            await self.db.rollback_transaction()
            del self._prepared_tx[transaction_id]
            self.logger.info(
                f"Rolled back order database for transaction {transaction_id}"
            )
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to rollback order database: {e}")
            return Result.err(
                Error(
                    message=f"Failed to rollback order database: {str(e)}",
                    error_code="ORDER_DB_ROLLBACK_FAILED",
                )
            )


# Mock event store (using the in-memory one for the example)
class MockEventStore:
    """Mock event store for demonstration."""

    def __init__(self):
        """Initialize the mock event store."""
        self.events: list[Event] = []
        self.logger = get_logger("events.store")

    async def append_events(self, events: list[Event]) -> None:
        """Append events to the store."""
        self.events.extend(events)
        self.logger.info(f"Stored {len(events)} events")


# Business logic service
class UserOrderService:
    """Service for user and order operations."""

    def __init__(
        self,
        user_db: UserDatabase,
        order_db: OrderDatabase,
        event_store: MockEventStore,
    ):
        """Initialize the service."""
        self.user_db = user_db
        self.order_db = order_db
        self.event_store = event_store
        self.logger = get_logger("service")

    async def create_user_and_order(
        self,
        email: str,
        username: str,
        total_amount: float,
        items: list[dict[str, Any]],
    ) -> dict[str, str]:
        """
        Create a user and an initial order in a single distributed transaction.

        Args:
            email: User's email
            username: User's username
            total_amount: Order total
            items: Order items

        Returns:
            Dictionary with user_id and order_id
        """
        # Create IDs
        user_id = str(uuid.uuid4())
        order_id = str(uuid.uuid4())

        # Create a distributed unit of work
        uow = DistributedUnitOfWork()

        # Register participants
        user_participant_id = uow.register_participant(
            "user_db", UserDatabaseParticipant(self.user_db)
        )
        order_participant_id = uow.register_participant(
            "order_db", OrderDatabaseParticipant(self.order_db)
        )
        event_participant_id = uow.register_participant(
            "event_store", EventStoreParticipant(self.event_store, "events")
        )

        try:
            # Execute the transaction
            async with uow:
                # Create user
                await self.user_db.create_user(user_id, email, username)

                # Create order
                await self.order_db.create_order(order_id, user_id, total_amount, items)

                # Create events
                user_event = UserCreated(
                    event_id=str(uuid.uuid4()),
                    user_id=user_id,
                    email=email,
                    username=username,
                    aggregate_id=user_id,
                    aggregate_type="User",
                )

                order_event = OrderCreated(
                    event_id=str(uuid.uuid4()),
                    order_id=order_id,
                    user_id=user_id,
                    total_amount=total_amount,
                    items=items,
                    aggregate_id=order_id,
                    aggregate_type="Order",
                )

                # Add events to the event store participant
                event_participant = uow.participants[event_participant_id]
                event_participant.add_events(
                    uow.transaction.transaction_id, [user_event, order_event]
                )

                # The transaction will be committed when the context exits

            self.logger.info(
                f"Successfully created user {user_id} and order {order_id}"
            )
            return {"user_id": user_id, "order_id": order_id}

        except Exception as e:
            self.logger.error(f"Error creating user and order: {e}")
            # The transaction will be rolled back when the context exits
            raise


async def run_example():
    """Run the distributed unit of work example."""
    # Configure logging
    configure_logging()
    logger = get_logger("example")
    logger.info("Starting distributed unit of work example")

    try:
        # Create the databases and event store
        user_db = await UserDatabase().connect()
        order_db = await OrderDatabase().connect()
        event_store = MockEventStore()

        # Create the service
        service = UserOrderService(user_db, order_db, event_store)

        # Create a user and order
        result = await service.create_user_and_order(
            email="john.doe@example.com",
            username="johndoe",
            total_amount=99.99,
            items=[
                {
                    "product_id": "prod-1",
                    "name": "Product 1",
                    "price": 49.99,
                    "quantity": 1,
                },
                {
                    "product_id": "prod-2",
                    "name": "Product 2",
                    "price": 25.00,
                    "quantity": 2,
                },
            ],
        )

        logger.info(f"Created user {result['user_id']} and order {result['order_id']}")

        # Verify the results
        logger.info(f"User count: {len(user_db.users)}")
        logger.info(f"Order count: {len(order_db.orders)}")
        logger.info(f"Event count: {len(event_store.events)}")

        # Show events
        for event in event_store.events:
            logger.info(f"Event: {event.event_type}, Aggregate: {event.aggregate_id}")

        # Demonstrate a failed transaction
        logger.info("\nDemonstrating a failed transaction:")
        try:
            # This will fail because the OrderDatabaseParticipant will throw an error
            result = await service.create_user_and_order(
                email="will.fail@example.com",
                username="willfail",
                total_amount=-10.0,  # This will cause the order creation to fail
                items=[],
            )
        except Exception as e:
            logger.info(f"Transaction failed as expected: {e}")

            # Verify nothing was committed
            logger.info(f"User count after failure: {len(user_db.users)}")
            logger.info(f"Order count after failure: {len(order_db.orders)}")
            logger.info(f"Event count after failure: {len(event_store.events)}")

    except Exception as e:
        logger.error(f"Error in example: {e}")
    finally:
        logger.info("Completed distributed unit of work example")


if __name__ == "__main__":
    asyncio.run(run_example())
