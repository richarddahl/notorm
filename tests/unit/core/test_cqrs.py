"""
Tests for the CQRS (Command Query Responsibility Segregation) implementation.

This module tests the functionality of the CQRS system, including:
- Command creation and handling
- Query creation and handling
- Command and query bus routing
- Handler registration and discovery
- Mediator pattern
"""

import pytest
import asyncio
from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock, AsyncMock

from uno.core.cqrs import (
    BaseCommand, BaseQuery, BaseCommandHandler, BaseQueryHandler,
    CommandBus, QueryBus, HandlerRegistry, Mediator,
    command_handler, query_handler,
    initialize_mediator, reset_mediator, get_mediator,
    execute_command, execute_query
)
from uno.core.errors.base import UnoError


# =============================================================================
# Test Commands, Queries, and Handlers
# =============================================================================

class CreateUserCommand(BaseCommand[str]):
    """Command to create a user."""
    
    def __init__(self, username: str, email: str, **kwargs):
        """
        Initialize a create user command.
        
        Args:
            username: The username
            email: The email address
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.username = username
        self.email = email


class UpdateUserCommand(BaseCommand[bool]):
    """Command to update a user."""
    
    def __init__(self, user_id: str, username: Optional[str] = None, email: Optional[str] = None, **kwargs):
        """
        Initialize an update user command.
        
        Args:
            user_id: The user ID
            username: Optional new username
            email: Optional new email address
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.user_id = user_id
        self.username = username
        self.email = email


class DeleteUserCommand(BaseCommand[bool]):
    """Command to delete a user."""
    
    def __init__(self, user_id: str, **kwargs):
        """
        Initialize a delete user command.
        
        Args:
            user_id: The user ID
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.user_id = user_id


class GetUserQuery(BaseQuery[Dict[str, Any]]):
    """Query to get a user."""
    
    def __init__(self, user_id: str, **kwargs):
        """
        Initialize a get user query.
        
        Args:
            user_id: The user ID
            **kwargs: Additional query arguments
        """
        super().__init__(**kwargs)
        self.user_id = user_id


class ListUsersQuery(BaseQuery[List[Dict[str, Any]]]):
    """Query to list users."""
    
    def __init__(self, limit: Optional[int] = None, offset: Optional[int] = None, **kwargs):
        """
        Initialize a list users query.
        
        Args:
            limit: Optional limit on number of users to return
            offset: Optional offset for pagination
            **kwargs: Additional query arguments
        """
        super().__init__(**kwargs)
        self.limit = limit
        self.offset = offset


class CountUsersQuery(BaseQuery[int]):
    """Query to count users."""
    
    def __init__(self, **kwargs):
        """
        Initialize a count users query.
        
        Args:
            **kwargs: Additional query arguments
        """
        super().__init__(**kwargs)


class UserCommandHandler(BaseCommandHandler[CreateUserCommand, str]):
    """Handler for user creation commands."""
    
    def __init__(self):
        """Initialize the handler."""
        super().__init__()
        self.users: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    async def handle(self, command: CreateUserCommand) -> str:
        """
        Handle a create user command.
        
        Args:
            command: The command to handle
            
        Returns:
            The new user ID
        """
        # Generate user ID
        user_id = f"user_{self.next_id}"
        self.next_id += 1
        
        # Create user
        self.users[user_id] = {
            "id": user_id,
            "username": command.username,
            "email": command.email,
            "created_at": command.timestamp.isoformat()
        }
        
        return user_id


class UserUpdateCommandHandler(BaseCommandHandler[UpdateUserCommand, bool]):
    """Handler for user update commands."""
    
    def __init__(self, user_repository: Dict[str, Dict[str, Any]]):
        """
        Initialize the handler.
        
        Args:
            user_repository: Repository of users
        """
        super().__init__()
        self.users = user_repository
    
    async def handle(self, command: UpdateUserCommand) -> bool:
        """
        Handle an update user command.
        
        Args:
            command: The command to handle
            
        Returns:
            True if the user was updated, False otherwise
        """
        if command.user_id not in self.users:
            return False
        
        # Update user
        if command.username is not None:
            self.users[command.user_id]["username"] = command.username
        
        if command.email is not None:
            self.users[command.user_id]["email"] = command.email
        
        self.users[command.user_id]["updated_at"] = command.timestamp.isoformat()
        
        return True


class UserDeleteCommandHandler(BaseCommandHandler[DeleteUserCommand, bool]):
    """Handler for user deletion commands."""
    
    def __init__(self, user_repository: Dict[str, Dict[str, Any]]):
        """
        Initialize the handler.
        
        Args:
            user_repository: Repository of users
        """
        super().__init__()
        self.users = user_repository
    
    async def handle(self, command: DeleteUserCommand) -> bool:
        """
        Handle a delete user command.
        
        Args:
            command: The command to handle
            
        Returns:
            True if the user was deleted, False otherwise
        """
        if command.user_id not in self.users:
            return False
        
        # Delete user
        del self.users[command.user_id]
        
        return True


class UserQueryHandler(BaseQueryHandler[GetUserQuery, Dict[str, Any]]):
    """Handler for user queries."""
    
    def __init__(self, user_repository: Dict[str, Dict[str, Any]]):
        """
        Initialize the handler.
        
        Args:
            user_repository: Repository of users
        """
        super().__init__()
        self.users = user_repository
    
    async def handle(self, query: GetUserQuery) -> Dict[str, Any]:
        """
        Handle a get user query.
        
        Args:
            query: The query to handle
            
        Returns:
            The user data, or an empty dict if not found
        """
        return self.users.get(query.user_id, {})


class UsersQueryHandler(BaseQueryHandler[ListUsersQuery, List[Dict[str, Any]]]):
    """Handler for listing users."""
    
    def __init__(self, user_repository: Dict[str, Dict[str, Any]]):
        """
        Initialize the handler.
        
        Args:
            user_repository: Repository of users
        """
        super().__init__()
        self.users = user_repository
    
    async def handle(self, query: ListUsersQuery) -> List[Dict[str, Any]]:
        """
        Handle a list users query.
        
        Args:
            query: The query to handle
            
        Returns:
            List of users
        """
        users = list(self.users.values())
        
        # Apply pagination
        if query.offset is not None:
            users = users[query.offset:]
        
        if query.limit is not None:
            users = users[:query.limit]
        
        return users


class UserCountQueryHandler(BaseQueryHandler[CountUsersQuery, int]):
    """Handler for counting users."""
    
    def __init__(self, user_repository: Dict[str, Dict[str, Any]]):
        """
        Initialize the handler.
        
        Args:
            user_repository: Repository of users
        """
        super().__init__()
        self.users = user_repository
    
    async def handle(self, query: CountUsersQuery) -> int:
        """
        Handle a count users query.
        
        Args:
            query: The query to handle
            
        Returns:
            Number of users
        """
        return len(self.users)


# =============================================================================
# Test Service with Decorators
# =============================================================================

class UserService:
    """Service for user management using decorator-based handlers."""
    
    def __init__(self):
        """Initialize the service."""
        self.users: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    @command_handler(CreateUserCommand)
    async def create_user(self, command: CreateUserCommand) -> str:
        """
        Create a user.
        
        Args:
            command: The command to handle
            
        Returns:
            The new user ID
        """
        # Generate user ID
        user_id = f"user_{self.next_id}"
        self.next_id += 1
        
        # Create user
        self.users[user_id] = {
            "id": user_id,
            "username": command.username,
            "email": command.email,
            "created_at": command.timestamp.isoformat()
        }
        
        return user_id
    
    @query_handler(GetUserQuery)
    async def get_user(self, query: GetUserQuery) -> Dict[str, Any]:
        """
        Get a user.
        
        Args:
            query: The query to handle
            
        Returns:
            The user data, or an empty dict if not found
        """
        return self.users.get(query.user_id, {})
    
    @command_handler(DeleteUserCommand)
    async def delete_user(self, command: DeleteUserCommand) -> bool:
        """
        Delete a user.
        
        Args:
            command: The command to handle
            
        Returns:
            True if the user was deleted, False otherwise
        """
        if command.user_id not in self.users:
            return False
        
        # Delete user
        del self.users[command.user_id]
        
        return True


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def setup_teardown():
    """Set up and tear down the mediator for each test."""
    # Reset mediator before test
    reset_mediator()
    
    yield
    
    # Reset mediator after test
    reset_mediator()


@pytest.fixture
def command_bus():
    """Create a command bus."""
    return CommandBus()


@pytest.fixture
def query_bus():
    """Create a query bus."""
    return QueryBus()


@pytest.fixture
def user_repository():
    """Create a user repository."""
    return {}


@pytest.fixture
def command_handler(user_repository):
    """Create a command handler."""
    return UserCommandHandler()


@pytest.fixture
def update_handler(user_repository):
    """Create an update handler."""
    return UserUpdateCommandHandler(user_repository)


@pytest.fixture
def delete_handler(user_repository):
    """Create a delete handler."""
    return UserDeleteCommandHandler(user_repository)


@pytest.fixture
def query_handler(user_repository):
    """Create a query handler."""
    return UserQueryHandler(user_repository)


@pytest.fixture
def list_handler(user_repository):
    """Create a list handler."""
    return UsersQueryHandler(user_repository)


@pytest.fixture
def count_handler(user_repository):
    """Create a count handler."""
    return UserCountQueryHandler(user_repository)


@pytest.fixture
def mediator(command_bus, query_bus):
    """Create a mediator."""
    return Mediator(command_bus, query_bus)


# =============================================================================
# Tests
# =============================================================================

def test_command_creation():
    """Test creating commands."""
    # Create a command
    command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    
    # Check command properties
    assert command.command_id is not None
    assert command.command_type == "CreateUserCommand"
    assert command.timestamp is not None
    assert command.username == "testuser"
    assert command.email == "test@example.com"
    
    # Test string representation
    assert str(command) == f"CreateUserCommand(id={command.command_id})"


def test_query_creation():
    """Test creating queries."""
    # Create a query
    query = GetUserQuery(user_id="123")
    
    # Check query properties
    assert query.query_id is not None
    assert query.query_type == "GetUserQuery"
    assert query.timestamp is not None
    assert query.user_id == "123"
    
    # Test string representation
    assert str(query) == f"GetUserQuery(id={query.query_id})"


@pytest.mark.asyncio
async def test_command_handler():
    """Test command handler."""
    # Create a handler
    handler = UserCommandHandler()
    
    # Create a command
    command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    
    # Handle the command
    user_id = await handler.handle(command)
    
    # Check the result
    assert user_id is not None
    assert user_id.startswith("user_")
    assert handler.users[user_id]["username"] == "testuser"
    assert handler.users[user_id]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_query_handler():
    """Test query handler."""
    # Create a user repository
    users = {
        "user_1": {
            "id": "user_1",
            "username": "testuser",
            "email": "test@example.com"
        }
    }
    
    # Create a handler
    handler = UserQueryHandler(users)
    
    # Create a query
    query = GetUserQuery(user_id="user_1")
    
    # Handle the query
    user = await handler.handle(query)
    
    # Check the result
    assert user is not None
    assert user["id"] == "user_1"
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"
    
    # Test non-existent user
    query = GetUserQuery(user_id="user_2")
    user = await handler.handle(query)
    assert user == {}


@pytest.mark.asyncio
async def test_command_bus_registration_and_execution(command_bus, command_handler):
    """Test registering and executing commands with the command bus."""
    # Register the handler
    command_bus.register(CreateUserCommand, command_handler)
    
    # Create a command
    command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    
    # Execute the command
    user_id = await command_bus.execute(command)
    
    # Check the result
    assert user_id is not None
    assert user_id.startswith("user_")
    assert command_handler.users[user_id]["username"] == "testuser"
    assert command_handler.users[user_id]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_query_bus_registration_and_execution(query_bus, user_repository, query_handler):
    """Test registering and executing queries with the query bus."""
    # Add a user to the repository
    user_repository["user_1"] = {
        "id": "user_1",
        "username": "testuser",
        "email": "test@example.com"
    }
    
    # Register the handler
    query_bus.register(GetUserQuery, query_handler)
    
    # Create a query
    query = GetUserQuery(user_id="user_1")
    
    # Execute the query
    user = await query_bus.execute(query)
    
    # Check the result
    assert user is not None
    assert user["id"] == "user_1"
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_mediator(
    mediator, command_handler, update_handler, delete_handler,
    query_handler, list_handler, count_handler
):
    """Test the mediator pattern."""
    # Register handlers
    mediator.command_bus.register(CreateUserCommand, command_handler)
    mediator.command_bus.register(UpdateUserCommand, update_handler)
    mediator.command_bus.register(DeleteUserCommand, delete_handler)
    mediator.query_bus.register(GetUserQuery, query_handler)
    mediator.query_bus.register(ListUsersQuery, list_handler)
    mediator.query_bus.register(CountUsersQuery, count_handler)
    
    # Create a user
    create_command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    user_id = await mediator.execute_command(create_command)
    
    # Get the user
    get_query = GetUserQuery(user_id=user_id)
    user = await mediator.execute_query(get_query)
    
    assert user["id"] == user_id
    assert user["username"] == "testuser"
    
    # Update the user
    update_command = UpdateUserCommand(
        user_id=user_id,
        username="updateduser"
    )
    result = await mediator.execute_command(update_command)
    assert result is True
    
    # Get the updated user
    user = await mediator.execute_query(get_query)
    assert user["username"] == "updateduser"
    
    # Count users
    count_query = CountUsersQuery()
    count = await mediator.execute_query(count_query)
    assert count == 1
    
    # List users
    list_query = ListUsersQuery()
    users = await mediator.execute_query(list_query)
    assert len(users) == 1
    assert users[0]["id"] == user_id
    
    # Delete the user
    delete_command = DeleteUserCommand(user_id=user_id)
    result = await mediator.execute_command(delete_command)
    assert result is True
    
    # Count users again
    count = await mediator.execute_query(count_query)
    assert count == 0


@pytest.mark.asyncio
async def test_handler_registry():
    """Test the handler registry."""
    # Create buses and registry
    command_bus = CommandBus()
    query_bus = QueryBus()
    registry = HandlerRegistry(command_bus, query_bus)
    
    # Create handlers
    command_handler = UserCommandHandler()
    query_handler = UserQueryHandler(command_handler.users)
    
    # Register handlers
    registry.register_command_handler(CreateUserCommand, command_handler)
    registry.register_query_handler(GetUserQuery, query_handler)
    
    # Create commands and queries
    create_command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    
    # Execute command
    user_id = await command_bus.execute(create_command)
    
    # Create query
    get_query = GetUserQuery(user_id=user_id)
    
    # Execute query
    user = await query_bus.execute(get_query)
    
    # Check results
    assert user["id"] == user_id
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_decorator_based_handlers():
    """Test decorator-based handlers."""
    # Create service
    service = UserService()
    
    # Create registry
    registry = HandlerRegistry()
    
    # Scan service
    count = registry.scan_instance(service)
    
    # Verify that handlers were registered
    assert count == 3
    
    # Create command and query
    create_command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    
    # Execute command
    user_id = await registry.command_bus.execute(create_command)
    
    # Create query
    get_query = GetUserQuery(user_id=user_id)
    
    # Execute query
    user = await registry.query_bus.execute(get_query)
    
    # Check results
    assert user["id"] == user_id
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"
    
    # Delete user
    delete_command = DeleteUserCommand(user_id=user_id)
    result = await registry.command_bus.execute(delete_command)
    assert result is True
    
    # Verify deletion
    user = await registry.query_bus.execute(get_query)
    assert user == {}


@pytest.mark.asyncio
async def test_global_mediator():
    """Test the global mediator."""
    # Initialize mediator
    command_bus = CommandBus()
    query_bus = QueryBus()
    initialize_mediator(command_bus, query_bus)
    
    # Create and register handlers
    command_handler = UserCommandHandler()
    command_bus.register(CreateUserCommand, command_handler)
    
    query_handler = UserQueryHandler(command_handler.users)
    query_bus.register(GetUserQuery, query_handler)
    
    # Execute command
    command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    user_id = await execute_command(command)
    
    # Execute query
    query = GetUserQuery(user_id=user_id)
    user = await execute_query(query)
    
    # Check results
    assert user["id"] == user_id
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_error_handling(command_bus):
    """Test error handling in the command bus."""
    # Create a failing handler
    class FailingHandler(BaseCommandHandler[CreateUserCommand, str]):
        async def handle(self, command: CreateUserCommand) -> str:
            raise ValueError("Test error")
    
    # Register the handler
    command_bus.register(CreateUserCommand, FailingHandler())
    
    # Create a command
    command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    
    # Execute the command and expect an exception
    with pytest.raises(UnoError) as excinfo:
        await command_bus.execute(command)
    
    # Check the exception
    assert "Error executing command CreateUserCommand" in str(excinfo.value)
    assert excinfo.value.code == "COMMAND_EXECUTION_ERROR"
    assert excinfo.value.category.name == "UNEXPECTED"


@pytest.mark.asyncio
async def test_handler_not_found(command_bus, query_bus):
    """Test behavior when no handler is found."""
    # Create commands and queries
    command = CreateUserCommand(
        username="testuser",
        email="test@example.com"
    )
    
    query = GetUserQuery(user_id="123")
    
    # Execute command without handler
    with pytest.raises(UnoError) as excinfo:
        await command_bus.execute(command)
    
    # Check the exception
    assert "No handler registered for command CreateUserCommand" in str(excinfo.value)
    assert excinfo.value.code == "COMMAND_HANDLER_NOT_FOUND"
    
    # Execute query without handler
    with pytest.raises(UnoError) as excinfo:
        await query_bus.execute(query)
    
    # Check the exception
    assert "No handler registered for query GetUserQuery" in str(excinfo.value)
    assert excinfo.value.code == "QUERY_HANDLER_NOT_FOUND"


@pytest.mark.asyncio
async def test_handler_inheritance(command_bus):
    """Test handler inheritance."""
    # Create a base command
    class BaseTestCommand(BaseCommand[str]):
        def __init__(self, value: str, **kwargs):
            super().__init__(**kwargs)
            self.value = value
    
    # Create derived commands
    class DerivedTestCommand1(BaseTestCommand):
        pass
    
    class DerivedTestCommand2(BaseTestCommand):
        pass
    
    # Create a handler for the base command
    class BaseCommandHandler(BaseCommandHandler[BaseTestCommand, str]):
        async def handle(self, command: BaseTestCommand) -> str:
            return f"Handled: {command.value}"
    
    # Register the handler for the base command
    command_bus.register(BaseTestCommand, BaseCommandHandler())
    
    # Create commands
    base_command = BaseTestCommand(value="base")
    derived_command1 = DerivedTestCommand1(value="derived1")
    derived_command2 = DerivedTestCommand2(value="derived2")
    
    # Execute commands
    base_result = await command_bus.execute(base_command)
    derived_result1 = await command_bus.execute(derived_command1)
    derived_result2 = await command_bus.execute(derived_command2)
    
    # Check results
    assert base_result == "Handled: base"
    assert derived_result1 == "Handled: derived1"
    assert derived_result2 == "Handled: derived2"


@pytest.mark.asyncio
async def test_duplicate_handler_registration(command_bus):
    """Test duplicate handler registration."""
    # Create handlers
    handler1 = UserCommandHandler()
    handler2 = UserCommandHandler()
    
    # Register the first handler
    command_bus.register(CreateUserCommand, handler1)
    
    # Try to register a second handler for the same command
    with pytest.raises(UnoError) as excinfo:
        command_bus.register(CreateUserCommand, handler2)
    
    # Check the exception
    assert "Command handler already registered" in str(excinfo.value)
    assert excinfo.value.code == "COMMAND_HANDLER_ALREADY_REGISTERED"
    assert excinfo.value.category.name == "CONFLICT"