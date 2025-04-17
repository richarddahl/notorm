"""
Example of using the Domain-Driven Design approach in Uno.

This example demonstrates how to use the domain-driven design approach
to implement business logic in a clean, maintainable way.
"""

import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any

from uno.domain.core import Entity, ValueObject, AggregateRoot, DomainEvent
from uno.dependencies import (
    get_domain_service,
    get_domain_repository,
    get_event_publisher,
    get_event_bus
)


# Value Objects - Immutable objects defined by their attributes, not identity
class Address(ValueObject):
    """Value object representing a physical address."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


class Money(ValueObject):
    """Value object representing a monetary amount."""
    amount: float
    currency: str = "USD"
    
    def add(self, other: "Money") -> "Money":
        """Add another monetary amount."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        """Subtract another monetary amount."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} from {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)


# Domain Events - Represent something significant that occurred
class UserCreatedEvent(DomainEvent):
    """Event triggered when a user is created."""
    user_id: str
    username: str
    email: str


class UserAddressChangedEvent(DomainEvent):
    """Event triggered when a user's address changes."""
    user_id: str
    old_address: Optional[Dict[str, Any]]
    new_address: Dict[str, Any]


# Entities - Objects with identity that persists across state changes
class User(AggregateRoot):
    """
    User entity representing a system user.
    
    This is an aggregate root that contains personal information and preferences.
    """
    username: str
    email: str
    display_name: Optional[str] = None
    address: Optional[Address] = None
    is_active: bool = True
    
    def change_email(self, new_email: str) -> None:
        """
        Change the user's email address.
        
        Args:
            new_email: The new email address
        """
        if "@" not in new_email:
            raise ValueError("Invalid email address")
            
        old_email = self.email
        self.email = new_email
        self.updated_at = datetime.now(datetime.UTC)
    
    def change_address(self, new_address: Address) -> None:
        """
        Change the user's address.
        
        Args:
            new_address: The new address
        """
        old_address = None
        if self.address:
            old_address = self.address.model_dump()
            
        self.address = new_address
        self.updated_at = datetime.now(datetime.UTC)
        
        # Create an event for this change
        event = UserAddressChangedEvent(
            user_id=self.id,
            old_address=old_address,
            new_address=new_address.model_dump()
        )
        self.add_event(event)
    
    def deactivate(self) -> None:
        """Deactivate the user."""
        if not self.is_active:
            return
            
        self.is_active = False
        self.updated_at = datetime.now(datetime.UTC)


# Example usage in a service layer
async def create_user(username: str, email: str, address: Optional[Address] = None) -> User:
    """
    Create a new user.
    
    Args:
        username: The username
        email: The email address
        address: Optional physical address
        
    Returns:
        The created user
    """
    # Create the user entity
    user = User(
        username=username,
        email=email,
        address=address,
        is_active=True,
        created_at=datetime.now(datetime.UTC)
    )
    
    # Get the user service from DI
    user_service = get_domain_service(User)
    
    # Save the user
    saved_user = await user_service.save(user)
    
    # Create and publish an event
    event = UserCreatedEvent(
        user_id=saved_user.id,
        username=saved_user.username,
        email=saved_user.email
    )
    
    # Get the event publisher
    publisher = get_event_publisher()
    await publisher.publish(event)
    
    return saved_user


# Example event handler
async def notify_user_creation(event: UserCreatedEvent) -> None:
    """
    Handle user creation events by sending a welcome email.
    
    Args:
        event: The user created event
    """
    print(f"Would send welcome email to {event.email} for new user {event.username}")


# Example of subscribing to events
async def setup_event_handlers():
    """Subscribe to domain events."""
    # Get the event bus
    event_bus = get_event_bus()
    
    # Subscribe to specific event types
    event_bus.subscribe(UserCreatedEvent, notify_user_creation)


# Main example function
async def run_example():
    """Run the domain model example."""
    # Set up event handlers
    await setup_event_handlers()
    
    # Create a new user
    address = Address(
        street="123 Main St",
        city="Anytown",
        state="CA",
        zip_code="12345"
    )
    
    user = await create_user(
        username="johndoe",
        email="john@example.com",
        address=address
    )
    
    print(f"Created user: {user.username} (ID: {user.id})")
    
    # Change the user's address
    new_address = Address(
        street="456 Oak Ave",
        city="Othertown",
        state="NY",
        zip_code="67890"
    )
    user.change_address(new_address)
    
    # Save the updated user
    user_service = get_domain_service(User)
    updated_user = await user_service.save(user)
    
    # Process any pending events
    publisher = get_event_publisher()
    await publisher.publish_pending_events()
    
    print(f"Updated user address to {updated_user.address.city}, {updated_user.address.state}")
    
    # Get the user by ID
    retrieved_user = await user_service.get_by_id(user.id)
    print(f"Retrieved user: {retrieved_user.username} from {retrieved_user.address.city}")


if __name__ == "__main__":
    # In a real application, this would be part of the application startup
    # Initialize all services
    from uno.dependencies import initialize_services
    initialize_services()
    
    # Run the example
    asyncio.run(run_example())