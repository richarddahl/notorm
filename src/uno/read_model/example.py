"""Example of the read model projection system for the Uno framework.

This module demonstrates how to use the read model projection system
to create and query read models optimized for specific use cases.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from uno.domain.events import DomainEvent, EventBus, InMemoryEventStore
from uno.read_model.read_model import ReadModel, InMemoryReadModelRepository
from uno.read_model.projector import Projection, Projector
from uno.read_model.query_service import ReadModelQueryService
from uno.read_model.cache_service import InMemoryReadModelCache


# Define some example domain events
class UserCreatedEvent(DomainEvent):
    """Event raised when a user is created."""
    
    user_id: str
    username: str
    email: str
    created_at: datetime


class UserUpdatedEvent(DomainEvent):
    """Event raised when a user is updated."""
    
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None


class UserDeletedEvent(DomainEvent):
    """Event raised when a user is deleted."""
    
    user_id: str


# Define a read model for user queries
class UserReadModel(ReadModel):
    """Read model for user queries."""
    
    user_id: str
    username: str
    email: str
    is_active: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# Define projections for the read model
class UserCreatedProjection(Projection[UserReadModel, UserCreatedEvent]):
    """Projection that creates a user read model when a user is created."""
    
    async def apply(self, event: UserCreatedEvent) -> Optional[UserReadModel]:
        """
        Apply a UserCreatedEvent to create a user read model.
        
        Args:
            event: The event to apply
            
        Returns:
            The created user read model
        """
        # Create a new read model from the event data
        return UserReadModel(
            id=event.user_id,  # Use the user_id as the read model ID
            user_id=event.user_id,
            username=event.username,
            email=event.email,
            is_active=True,
            last_updated=datetime.utcnow()  # Use current time instead of event timestamp
        )


class UserUpdatedProjection(Projection[UserReadModel, UserUpdatedEvent]):
    """Projection that updates a user read model when a user is updated."""
    
    async def apply(self, event: UserUpdatedEvent) -> Optional[UserReadModel]:
        """
        Apply a UserUpdatedEvent to update a user read model.
        
        Args:
            event: The event to apply
            
        Returns:
            The updated user read model, or None if the user doesn't exist
        """
        # Get the existing read model
        read_model = await self.repository.get(event.user_id)
        if not read_model:
            self.logger.warning(f"User read model not found for user {event.user_id}")
            return None
        
        # Update the read model with the event data
        update_data: Dict[str, Any] = {}
        if event.username is not None:
            update_data["username"] = event.username
        if event.email is not None:
            update_data["email"] = event.email
        
        # Only update if there are changes
        if update_data:
            # Update the last_updated field
            update_data["last_updated"] = datetime.utcnow()
            # Create a new read model with the updated data
            updated_model = read_model.model_copy(update=update_data)
            return updated_model
        
        return None


class UserDeletedProjection(Projection[UserReadModel, UserDeletedEvent]):
    """Projection that marks a user read model as inactive when a user is deleted."""
    
    async def apply(self, event: UserDeletedEvent) -> Optional[UserReadModel]:
        """
        Apply a UserDeletedEvent to mark a user read model as inactive.
        
        Args:
            event: The event to apply
            
        Returns:
            The updated user read model, or None if the user doesn't exist
        """
        # Get the existing read model
        read_model = await self.repository.get(event.user_id)
        if not read_model:
            self.logger.warning(f"User read model not found for user {event.user_id}")
            return None
        
        # Mark the user as inactive
        updated_model = read_model.model_copy(update={
            "is_active": False,
            "last_updated": datetime.utcnow()
        })
        
        return updated_model


# Example of using the read model projection system
async def run_example():
    """Run the read model projection system example."""
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("read_model_example")
    
    # Create the event bus
    event_bus = EventBus(logger=logger)
    event_store = InMemoryEventStore(logger=logger)
    
    # Create the repository and cache
    repository = InMemoryReadModelRepository(UserReadModel, logger=logger)
    cache = InMemoryReadModelCache(UserReadModel, logger=logger)
    
    # Create the projector
    projector = Projector(event_bus, event_store, logger=logger)
    
    # Create the projections
    created_projection = UserCreatedProjection(
        UserReadModel, UserCreatedEvent, repository, logger=logger
    )
    updated_projection = UserUpdatedProjection(
        UserReadModel, UserUpdatedEvent, repository, logger=logger
    )
    deleted_projection = UserDeletedProjection(
        UserReadModel, UserDeletedEvent, repository, logger=logger
    )
    
    # Register the projections with the projector
    projector.register_projection(created_projection)
    projector.register_projection(updated_projection)
    projector.register_projection(deleted_projection)
    
    # Create the query service
    query_service = ReadModelQueryService(
        repository, UserReadModel, cache, logger=logger
    )
    
    # Generate some events
    user_id = "user-123"
    created_event = UserCreatedEvent(
        user_id=user_id,
        username="johndoe",
        email="john@example.com",
        created_at=datetime.utcnow(),
        event_type="user_created",
        aggregate_id=user_id,
        aggregate_type="user",
        event_id="event-1"  # Add event_id
    )
    
    updated_event = UserUpdatedEvent(
        user_id=user_id,
        username="johndoe2",
        event_type="user_updated",
        aggregate_id=user_id,
        aggregate_type="user",
        event_id="event-2"  # Add event_id
    )
    
    deleted_event = UserDeletedEvent(
        user_id=user_id,
        event_type="user_deleted",
        aggregate_id=user_id,
        aggregate_type="user",
        event_id="event-3"  # Add event_id
    )
    
    # Publish the events
    logger.info("Publishing events...")
    await event_bus.publish(created_event)
    await event_bus.publish(updated_event)
    
    # Query the read model
    logger.info("Querying read model...")
    user = await query_service.get_by_id(user_id)
    logger.info(f"User read model: {user}")
    
    # Publish the delete event
    logger.info("Publishing delete event...")
    await event_bus.publish(deleted_event)
    
    # Query the read model again
    logger.info("Querying read model again...")
    user = await query_service.get_by_id(user_id)
    logger.info(f"User read model after delete: {user}")
    
    # Find active users
    logger.info("Finding active users...")
    active_users = await query_service.find({"is_active": True})
    logger.info(f"Active users: {active_users}")
    
    # Find inactive users
    logger.info("Finding inactive users...")
    inactive_users = await query_service.find({"is_active": False})
    logger.info(f"Inactive users: {inactive_users}")


if __name__ == "__main__":
    asyncio.run(run_example())