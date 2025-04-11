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
    
    # Get the service under test
    from uno.dependencies.scoped_container import get_service
    with get_service(UserRepository) as repo:
        service = get_service(UserServiceProtocol)
        
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
        stored_user = await repo.get_user("test1")
        assert stored_user == user_data


@pytest.mark.asyncio
async def test_get_users(setup_test_container):
    """Test getting all users."""
    # Get the service under test
    from uno.dependencies.scoped_container import get_service
    with get_service(UserRepository) as repo:
        service = get_service(UserServiceProtocol)
        
        # Create some users
        await repo.create_user({"id": "user1", "name": "User 1"})
        await repo.create_user({"id": "user2", "name": "User 2"})
        
        # Get all users
        users = await service.get_users()
        
        # Verify the result
        assert len(users) == 2
        assert {"id": "user1", "name": "User 1"} in users
        assert {"id": "user2", "name": "User 2"} in users


@pytest.mark.asyncio
async def test_name_length_validation(setup_test_container):
    """Test validation of user name length."""
    # Get the service under test
    from uno.dependencies.scoped_container import get_service
    service = get_service(UserServiceProtocol)
    
    # Create a user with a too-long name
    long_name = "X" * 100  # 100 characters
    user_data = {"id": "long_name", "name": long_name}
    result = await service.create_user(user_data)
    
    # Verify the name was truncated
    assert len(result["name"]) == 50  # from the mock configuration


@pytest.mark.asyncio
async def test_lifecycle(setup_test_container):
    """Test service lifecycle."""
    # Get the service under test
    from uno.dependencies.scoped_container import get_service
    service = get_service(UserServiceProtocol)
    
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