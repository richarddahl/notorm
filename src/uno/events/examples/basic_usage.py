"""
Basic usage examples for the Uno event system.

This module demonstrates the core functionality of the event system,
including defining events, subscribing to events, and publishing events.
"""

import asyncio
from datetime import datetime, UTC
from typing import Optional, List

from pydantic import Field

from uno.events import (
    Event,
    EventBus,
    EventHandler,
    event_handler,
    EventSubscriber,
    initialize_events,
    publish_event,
    subscribe,
)


# 1. Define some event classes
class UserCreated(Event):
    """Event emitted when a user is created."""
    
    username: str
    email: str
    roles: List[str] = Field(default_factory=list)


class UserUpdated(Event):
    """Event emitted when a user is updated."""
    
    username: str
    email: Optional[str] = None
    roles: Optional[List[str]] = None


class UserDeleted(Event):
    """Event emitted when a user is deleted."""
    
    username: str


# 2. Define an event handler class
class UserEventHandler(EventHandler[UserCreated]):
    """Handler for user-related events."""
    
    async def handle(self, event: UserCreated) -> None:
        """Handle the UserCreated event."""
        print(f"Class-based handler: User {event.username} created with email {event.email}")


# 3. Define a subscriber with multiple handlers
class UserEventSubscriber(EventSubscriber):
    """Subscriber for user-related events."""
    
    @event_handler(UserCreated)
    async def on_user_created(self, event: UserCreated) -> None:
        """Handle the UserCreated event."""
        print(f"Subscriber: User {event.username} created with email {event.email}")
        print(f"Roles: {', '.join(event.roles)}")
    
    @event_handler(UserUpdated)
    async def on_user_updated(self, event: UserUpdated) -> None:
        """Handle the UserUpdated event."""
        print(f"Subscriber: User {event.username} updated")
        if event.email:
            print(f"New email: {event.email}")
        if event.roles:
            print(f"New roles: {', '.join(event.roles)}")
    
    @event_handler(UserDeleted)
    async def on_user_deleted(self, event: UserDeleted) -> None:
        """Handle the UserDeleted event."""
        print(f"Subscriber: User {event.username} deleted")


# 4. Define a standalone function handler
@event_handler(UserCreated)
async def log_user_created(event: UserCreated) -> None:
    """Log when a user is created."""
    print(f"Function handler: Logging user creation: {event.username} at {event.timestamp}")


async def run_example() -> None:
    """Run the basic usage example."""
    # Initialize the event system
    initialize_events()
    
    # Get the event bus
    event_bus = EventBus()
    
    # Create and register handlers
    user_handler = UserEventHandler()
    user_subscriber = UserEventSubscriber(event_bus)
    
    # Register standalone function handler
    subscribe(UserCreated, log_user_created)
    
    # Register class-based handler
    subscribe(UserCreated, user_handler)
    
    # Create and publish events
    created_event = UserCreated(
        username="alice",
        email="alice@example.com",
        roles=["user", "admin"],
    )
    
    updated_event = UserUpdated(
        username="alice",
        email="alice.new@example.com",
    )
    
    deleted_event = UserDeleted(
        username="alice",
    )
    
    # Publish events
    await event_bus.publish(created_event)
    print("---")
    await event_bus.publish(updated_event)
    print("---")
    await event_bus.publish(deleted_event)


if __name__ == "__main__":
    asyncio.run(run_example())