"""
Example of using the new dependency injection system in a real-world service.

This module demonstrates how to implement services using the new dependency injection
system in the Uno framework.
"""

import logging
from typing import List, Dict, Any, Optional, Protocol
import asyncio

from uno.dependencies.decorators import (
    singleton,
    scoped,
    transient,
    inject_params,
    injectable_class
)
from uno.dependencies.modern_provider import ServiceLifecycle
from uno.dependencies.interfaces import (
    ConfigProtocol,
    UnoDatabaseProviderProtocol,
    EventBusProtocol
)


# Define a service interface using Protocol
class UserServiceProtocol(Protocol):
    """Protocol for user services."""
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get a user by ID."""
        ...
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        ...
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        ...
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user."""
        ...
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        ...


# Define events for the user service
class UserCreatedEvent:
    """Event raised when a user is created."""
    
    def __init__(self, user_id: str, user_data: Dict[str, Any]):
        """Initialize the event."""
        self.user_id = user_id
        self.user_data = user_data


class UserUpdatedEvent:
    """Event raised when a user is updated."""
    
    def __init__(self, user_id: str, user_data: Dict[str, Any]):
        """Initialize the event."""
        self.user_id = user_id
        self.user_data = user_data


class UserDeletedEvent:
    """Event raised when a user is deleted."""
    
    def __init__(self, user_id: str):
        """Initialize the event."""
        self.user_id = user_id


# Define a repository for user data
@scoped
class UserRepository:
    """Repository for user data."""
    
    def __init__(
        self,
        db_provider: UnoDatabaseProviderProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            db_provider: The database provider
            logger: Optional logger
        """
        self.db_provider = db_provider
        self.logger = logger or logging.getLogger("uno.user_repository")
        # In-memory storage for demonstration
        self.users: Dict[str, Dict[str, Any]] = {}
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            The user data or an empty dict if not found
        """
        self.logger.debug(f"Getting user {user_id}")
        return self.users.get(user_id, {})
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.
        
        Returns:
            A list of all users
        """
        self.logger.debug(f"Getting all users ({len(self.users)} total)")
        return list(self.users.values())
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_data: The user data
            
        Returns:
            The created user data
        """
        user_id = user_data.get("id")
        self.logger.info(f"Creating user {user_id}")
        self.users[user_id] = user_data
        return user_data
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a user.
        
        Args:
            user_id: The user ID
            user_data: The updated user data
            
        Returns:
            The updated user data or an empty dict if not found
        """
        self.logger.info(f"Updating user {user_id}")
        if user_id in self.users:
            current_user = self.users[user_id]
            updated_user = {**current_user, **user_data}
            self.users[user_id] = updated_user
            return updated_user
        return {}
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if the user was deleted, False otherwise
        """
        self.logger.info(f"Deleting user {user_id}")
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False


# Implement the user service with lifecycle management
@singleton(UserServiceProtocol)
@injectable_class()
class UserService(UserServiceProtocol, ServiceLifecycle):
    """Service for managing users."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        event_bus: EventBusProtocol,
        config: ConfigProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            user_repository: The user repository
            event_bus: The event bus
            config: The configuration service
            logger: Optional logger
        """
        self.user_repository = user_repository
        self.event_bus = event_bus
        self.config = config
        self.logger = logger or logging.getLogger("uno.user_service")
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service."""
        self.logger.info("Initializing user service")
        
        # Load configuration
        self.max_users = self.config.get("MAX_USERS", 100)
        self.user_name_max_length = self.config.get("USER_NAME_MAX_LENGTH", 50)
        
        # Subscribe to events
        # Note: This is just an example. In a real application, you would
        # have a proper event subscription mechanism.
        if hasattr(self.event_bus, "subscribe"):
            self.event_bus.subscribe("user_created", self._handle_user_created)
            self.event_bus.subscribe("user_updated", self._handle_user_updated)
            self.event_bus.subscribe("user_deleted", self._handle_user_deleted)
        
        # Create some demo users
        await self._create_demo_users()
        
        self.initialized = True
        self.logger.info("User service initialized")
    
    async def dispose(self) -> None:
        """Dispose the service."""
        self.logger.info("Disposing user service")
        
        # Clean up resources
        if hasattr(self.event_bus, "unsubscribe"):
            self.event_bus.unsubscribe("user_created", self._handle_user_created)
            self.event_bus.unsubscribe("user_updated", self._handle_user_updated)
            self.event_bus.unsubscribe("user_deleted", self._handle_user_deleted)
        
        self.initialized = False
        self.logger.info("User service disposed")
    
    async def _create_demo_users(self) -> None:
        """Create demo users."""
        self.logger.debug("Creating demo users")
        
        demo_users = [
            {"id": "user1", "name": "Demo User 1", "email": "user1@example.com"},
            {"id": "user2", "name": "Demo User 2", "email": "user2@example.com"},
            {"id": "user3", "name": "Demo User 3", "email": "user3@example.com"},
        ]
        
        for user in demo_users:
            await self.user_repository.create_user(user)
        
        self.logger.debug(f"Created {len(demo_users)} demo users")
    
    async def _handle_user_created(self, event: UserCreatedEvent) -> None:
        """
        Handle a user created event.
        
        Args:
            event: The event
        """
        self.logger.info(f"User {event.user_id} created")
        # Additional business logic here
    
    async def _handle_user_updated(self, event: UserUpdatedEvent) -> None:
        """
        Handle a user updated event.
        
        Args:
            event: The event
        """
        self.logger.info(f"User {event.user_id} updated")
        # Additional business logic here
    
    async def _handle_user_deleted(self, event: UserDeletedEvent) -> None:
        """
        Handle a user deleted event.
        
        Args:
            event: The event
        """
        self.logger.info(f"User {event.user_id} deleted")
        # Additional business logic here
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            The user data
        """
        self.logger.debug(f"Getting user {user_id}")
        return await self.user_repository.get_user(user_id)
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.
        
        Returns:
            A list of all users
        """
        self.logger.debug("Getting all users")
        users = await self.user_repository.get_users()
        
        # Apply business rules
        if len(users) > self.max_users:
            self.logger.warning(f"User count ({len(users)}) exceeds maximum ({self.max_users})")
        
        return users
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_data: The user data
            
        Returns:
            The created user data
        """
        user_id = user_data.get("id")
        self.logger.info(f"Creating user {user_id}")
        
        # Validate user data
        if len(user_data.get("name", "")) > self.user_name_max_length:
            user_data["name"] = user_data["name"][:self.user_name_max_length]
            self.logger.warning(f"User name for {user_id} truncated to {self.user_name_max_length} characters")
        
        # Create the user
        user = await self.user_repository.create_user(user_data)
        
        # Publish event
        if hasattr(self.event_bus, "publish"):
            await self.event_bus.publish(UserCreatedEvent(user_id, user))
        
        return user
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a user.
        
        Args:
            user_id: The user ID
            user_data: The updated user data
            
        Returns:
            The updated user data
        """
        self.logger.info(f"Updating user {user_id}")
        
        # Validate user data
        if "name" in user_data and len(user_data["name"]) > self.user_name_max_length:
            user_data["name"] = user_data["name"][:self.user_name_max_length]
            self.logger.warning(f"User name for {user_id} truncated to {self.user_name_max_length} characters")
        
        # Update the user
        user = await self.user_repository.update_user(user_id, user_data)
        
        # Publish event if the user was updated
        if user and hasattr(self.event_bus, "publish"):
            await self.event_bus.publish(UserUpdatedEvent(user_id, user))
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if the user was deleted
        """
        self.logger.info(f"Deleting user {user_id}")
        
        # Delete the user
        success = await self.user_repository.delete_user(user_id)
        
        # Publish event if the user was deleted
        if success and hasattr(self.event_bus, "publish"):
            await self.event_bus.publish(UserDeletedEvent(user_id))
        
        return success


# Example of using the service with the inject_params decorator
@inject_params()
async def process_user(user_id: str, user_service: UserServiceProtocol) -> Dict[str, Any]:
    """
    Process a user.
    
    Args:
        user_id: The user ID
        user_service: The user service (injected)
        
    Returns:
        The processed user data
    """
    # Get the user
    user = await user_service.get_user(user_id)
    
    # Process the user data
    # This is just an example, in a real application you would do more here
    if user:
        user["processed"] = True
    
    return user