"""
Tests for the example services using the new dependency injection system.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
import logging

from uno.dependencies.scoped_container import ServiceCollection, initialize_container
from uno.dependencies.interfaces import UnoConfigProtocol, EventBusProtocol
from uno.dependencies.interfaces import UnoDatabaseProviderProtocol
from uno.domain.service_example import (
    UserRepository,
    UserService,
    UserServiceProtocol,
    UserCreatedEvent
)


@pytest.fixture
def setup_test_container():
    """Set up a test container with mocked dependencies."""
    # Create a service collection for testing
    services = ServiceCollection()
    
    # Create mock dependencies
    mock_config = MagicMock(spec=UnoConfigProtocol)
    mock_config.get_value.side_effect = lambda key, default=None: {
        "MAX_USERS": 100,
        "USER_NAME_MAX_LENGTH": 50
    }.get(key, default)
    
    mock_db_provider = MagicMock(spec=UnoDatabaseProviderProtocol)
    
    mock_event_bus = MagicMock(spec=EventBusProtocol)
    mock_event_bus.publish = AsyncMock()
    mock_event_bus.subscribe = MagicMock()
    
    mock_logger = MagicMock(spec=logging.Logger)
    
    # Register mocks
    services.add_instance(UnoConfigProtocol, mock_config)
    services.add_instance(UnoDatabaseProviderProtocol, mock_db_provider)
    services.add_instance(EventBusProtocol, mock_event_bus)
    services.add_instance(logging.Logger, mock_logger)
    
    # Register the repository and service
    services.add_scoped(UserRepository)
    services.add_singleton(UserServiceProtocol, UserService)
    
    # Initialize the container
    initialize_container(services)
    
    # Return mock dependencies for assertions
    return {
        "config": mock_config,
        "db_provider": mock_db_provider,
        "event_bus": mock_event_bus,
        "logger": mock_logger
    }


@pytest.mark.asyncio
async def test_create_user(setup_test_container):
    """Test creating a user."""
    # Get mocked dependencies
    mocks = setup_test_container
    
    # Create a mock repository
    mock_repository = MagicMock()
    stored_users = {}
    
    async def mock_create_user(user_data):
        user_id = user_data.get("id")
        stored_users[user_id] = user_data
        return user_data
        
    async def mock_get_user(user_id):
        return stored_users.get(user_id, {})
    
    mock_repository.create_user = AsyncMock(side_effect=mock_create_user)
    mock_repository.get_user = AsyncMock(side_effect=mock_get_user)
    
    # Create the service with mock dependencies
    service = UserService(
        user_repository=mock_repository,
        event_bus=mocks["event_bus"],
        config=mocks["config"],
        logger=mocks["logger"]
    )
    
    # Initialize the service
    await service.initialize()
    
    # Create a user
    user_data = {"id": "test1", "name": "Test User", "email": "test@example.com"}
    result = await service.create_user(user_data)
    
    # Verify the result
    assert result == user_data
    
    # Verify the event was published
    mocks["event_bus"].publish.assert_called_once()
    args, _ = mocks["event_bus"].publish.call_args
    assert isinstance(args[0], UserCreatedEvent)
    assert args[0].user_id == "test1"
    
    # Verify the user was stored in the repository
    stored_user = await mock_repository.get_user("test1")
    assert stored_user == user_data


@pytest.mark.asyncio
async def test_get_users(setup_test_container):
    """Test getting all users."""
    # Get mocked dependencies
    mocks = setup_test_container
    
    # Create a mock repository
    mock_repository = MagicMock()
    stored_users = {}
    
    async def mock_create_user(user_data):
        user_id = user_data.get("id")
        stored_users[user_id] = user_data
        return user_data
        
    async def mock_get_users():
        return list(stored_users.values())
    
    mock_repository.create_user = AsyncMock(side_effect=mock_create_user)
    mock_repository.get_users = AsyncMock(side_effect=mock_get_users)
    
    # Create the service with mock dependencies
    service = UserService(
        user_repository=mock_repository,
        event_bus=mocks["event_bus"],
        config=mocks["config"],
        logger=mocks["logger"]
    )
    
    # Replace the _create_demo_users method to avoid creating demo users
    service._create_demo_users = AsyncMock()
    
    # Initialize the service
    await service.initialize()
    
    # Create some users directly through the repository
    await mock_repository.create_user({"id": "user1", "name": "User 1"})
    await mock_repository.create_user({"id": "user2", "name": "User 2"})
    
    # Get all users
    users = await service.get_users()
    
    # Verify the result - no demo users since we mocked the _create_demo_users method
    assert len(users) == 2
    assert {"id": "user1", "name": "User 1"} in users
    assert {"id": "user2", "name": "User 2"} in users


@pytest.mark.asyncio
async def test_name_length_validation(setup_test_container):
    """Test validation of user name length."""
    # Get mocked dependencies
    mocks = setup_test_container
    
    # Create mock repository
    mock_repository = MagicMock()
    
    async def mock_create_user(user_data):
        return user_data
    
    mock_repository.create_user = AsyncMock(side_effect=mock_create_user)
    
    # Configure mock config to return the max length value
    mocks["config"].get_value.return_value = 50  # Set max name length to 50
    
    # Create the service with mock dependencies
    service = UserService(
        user_repository=mock_repository,
        event_bus=mocks["event_bus"],
        config=mocks["config"],
        logger=mocks["logger"]
    )
    
    # Initialize the service
    await service.initialize()
    
    # Create a user with a too-long name
    long_name = "X" * 100  # 100 characters
    user_data = {"id": "long_name", "name": long_name}
    result = await service.create_user(user_data)
    
    # Verify the name was truncated
    assert len(result["name"]) == 50  # from the mock configuration


@pytest.mark.asyncio
async def test_lifecycle(setup_test_container):
    """Test service lifecycle."""
    # Fetch mock dependencies
    mocks = setup_test_container
    
    # Create a mock repository
    mock_repository = MagicMock()
    
    # Setup the get_users method to return demo users for testing
    users_data = [
        {"id": "user1", "name": "Demo User 1", "email": "user1@example.com"},
        {"id": "user2", "name": "Demo User 2", "email": "user2@example.com"},
        {"id": "user3", "name": "Demo User 3", "email": "user3@example.com"},
    ]
    
    # Make create_user store the users
    created_users = []
    
    async def mock_create_user(user_data):
        created_users.append(user_data)
        return user_data
    
    async def mock_get_users():
        return created_users
    
    mock_repository.create_user = AsyncMock(side_effect=mock_create_user)
    mock_repository.get_users = AsyncMock(side_effect=mock_get_users)
    
    # Now create the service with mocked dependencies
    service = UserService(
        user_repository=mock_repository,
        event_bus=mocks["event_bus"],
        config=mocks["config"],
        logger=mocks["logger"]
    )
    
    # Initialize the service
    await service.initialize()
    
    # Verify demo users were created
    users = await service.get_users()
    assert len(users) == 3
    assert any(u["id"] == "user1" for u in users)
    assert any(u["id"] == "user2" for u in users)
    assert any(u["id"] == "user3" for u in users)
    
    # Dispose the service
    await service.dispose()