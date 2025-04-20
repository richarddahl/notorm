"""
PostgreSQL Event Store Example

This example demonstrates how to use the PostgreSQL implementation of the EventStore
for event sourcing and event-driven architecture.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

from pydantic import Field

from uno.core.events import Event, PostgresEventStore, PostgresEventStoreConfig
from uno.core.logging import get_logger


# Define some domain events
class UserCreated(Event):
    """Event indicating a user was created."""

    user_id: str
    email: str
    username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserEmailChanged(Event):
    """Event indicating a user's email was changed."""

    user_id: str
    old_email: str
    new_email: str
    changed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserDeactivated(Event):
    """Event indicating a user was deactivated."""

    user_id: str
    reason: str | None = None
    deactivated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# User aggregate (simplified)
class User:
    """User aggregate root."""

    def __init__(self, user_id: str, email: str, username: str):
        """Initialize a new User aggregate."""
        self.user_id = user_id
        self.email = email
        self.username = username
        self.active = True
        self.created_at = datetime.now(UTC)
        self.version = 0

    @classmethod
    async def create(
        cls, email: str, username: str, event_store: PostgresEventStore
    ) -> "User":
        """Create a new user and store the UserCreated event."""
        user_id = str(uuid.uuid4())

        # Create the UserCreated event
        event = UserCreated(
            user_id=user_id,
            email=email,
            username=username,
            aggregate_id=user_id,
            aggregate_type="User",
        )

        # Store the event
        await event_store.append_events([event])

        # Create and return a new User
        user = cls(user_id, email, username)
        user.version = 1
        return user

    @classmethod
    async def load(cls, user_id: str, event_store: PostgresEventStore) -> "User":
        """Load a User from events in the event store."""
        # Get all events for this user
        events = await event_store.get_events_by_aggregate(user_id)

        if not events:
            raise ValueError(f"User with ID {user_id} not found")

        # Apply the events to reconstruct the User
        return cls.apply_events(events)

    @classmethod
    def apply_events(cls, events: list[Event]) -> "User":
        """Apply events to reconstruct a User."""
        # First event should be UserCreated
        create_event = events[0]
        if not isinstance(create_event, UserCreated):
            raise ValueError("First event must be UserCreated")

        # Create the User from the first event
        user = cls(
            user_id=create_event.user_id,
            email=create_event.email,
            username=create_event.username,
        )
        user.created_at = create_event.created_at

        # Apply remaining events
        for event in events[1:]:
            if isinstance(event, UserEmailChanged):
                user.email = event.new_email
            elif isinstance(event, UserDeactivated):
                user.active = False

            # Update version
            user.version = event.aggregate_version or 0

        return user

    async def change_email(
        self, new_email: str, event_store: PostgresEventStore
    ) -> None:
        """Change the user's email and store the UserEmailChanged event."""
        # Create the UserEmailChanged event
        event = UserEmailChanged(
            user_id=self.user_id,
            old_email=self.email,
            new_email=new_email,
            aggregate_id=self.user_id,
            aggregate_type="User",
            aggregate_version=self.version + 1,
        )

        # Store the event with optimistic concurrency
        await event_store.append_events([event], expected_version=self.version)

        # Update user state
        self.email = new_email
        self.version += 1

    async def deactivate(
        self, reason: Optional[str], event_store: PostgresEventStore
    ) -> None:
        """Deactivate the user and store the UserDeactivated event."""
        if not self.active:
            raise ValueError("User is already deactivated")

        # Create the UserDeactivated event
        event = UserDeactivated(
            user_id=self.user_id,
            reason=reason,
            aggregate_id=self.user_id,
            aggregate_type="User",
            aggregate_version=self.version + 1,
        )

        # Store the event with optimistic concurrency
        await event_store.append_events([event], expected_version=self.version)

        # Update user state
        self.active = False
        self.version += 1


async def run_example():
    """Run the PostgreSQL event store example."""
    # Set up logging
    logger = get_logger("example")
    logger.info("Starting PostgreSQL event store example")

    # Configure the event store
    config = PostgresEventStoreConfig(
        connection_string="postgresql+asyncpg://username:password@localhost:5432/mydatabase",
        schema="public",
        table_name="domain_events",
        create_schema_if_missing=True,
        use_notifications=True,
    )

    # Create the event store
    event_store = PostgresEventStore(config=config)

    try:
        # Initialize the event store
        await event_store.initialize()
        logger.info("Event store initialized")

        # Create a new user
        user = await User.create(
            email="john.doe@example.com", username="johndoe", event_store=event_store
        )
        logger.info(f"Created user: {user.username} ({user.email})")

        # Change the user's email
        await user.change_email("john.doe.new@example.com", event_store)
        logger.info(f"Changed user email to: {user.email}")

        # Deactivate the user
        await user.deactivate("User requested account deletion", event_store)
        logger.info("Deactivated user")

        # Load the user from events
        loaded_user = await User.load(user.user_id, event_store)
        logger.info(
            f"Loaded user from events: {loaded_user.username} ({loaded_user.email})"
        )
        logger.info(f"User is {'inactive' if not loaded_user.active else 'active'}")

        # Get all events for the user
        events = await event_store.get_events_by_aggregate(user.user_id)
        logger.info(f"Found {len(events)} events for user {user.user_id}")

        for event in events:
            logger.info(
                f"Event: {event.event_type}, Version: {event.aggregate_version}"
            )

        # Get all UserCreated events
        created_events = await event_store.get_events_by_type(
            UserCreated.get_event_type()
        )
        logger.info(f"Found {len(created_events)} UserCreated events")

    except Exception as e:
        logger.error(f"Error in example: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("PostgreSQL event store example completed")


if __name__ == "__main__":
    asyncio.run(run_example())
