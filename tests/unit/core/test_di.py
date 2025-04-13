"""
Tests for the dependency injection system.

This module tests the functionality of the DI container, including:
- Service registration and resolution
- Singleton, scoped, and transient lifetime management
- Service dependencies and auto-wiring
- Lifecycle management
"""

import pytest
from typing import List, Protocol, runtime_checkable

from uno.core.di import (
    DIContainer, ServiceLifetime, ServiceRegistration,
    initialize_container, get_container, reset_container,
    get_service, create_scope
)
from uno.core.errors import DomainError
from uno.core.protocols import Initializable, Disposable


# =============================================================================
# Test Interfaces and Implementations
# =============================================================================

@runtime_checkable
class IMessageService(Protocol):
    """Test message service interface."""
    
    def get_message(self) -> str:
        """Get a message."""
        ...


@runtime_checkable
class IGreetingService(Protocol):
    """Test greeting service interface."""
    
    def greet(self, name: str) -> str:
        """Greet someone."""
        ...


class SimpleMessageService(IMessageService):
    """Simple message service implementation."""
    
    def get_message(self) -> str:
        """Get a simple message."""
        return "Hello, World!"


class ConfigurableMessageService(IMessageService):
    """Configurable message service implementation."""
    
    def __init__(self, message: str = "Configurable message"):
        """Initialize with a message."""
        self.message = message
    
    def get_message(self) -> str:
        """Get the configured message."""
        return self.message


class SimpleGreetingService(IGreetingService):
    """Simple greeting service implementation."""
    
    def __init__(self, message_service: IMessageService):
        """Initialize with a message service."""
        self.message_service = message_service
    
    def greet(self, name: str) -> str:
        """Greet someone using the message service."""
        base_message = self.message_service.get_message()
        return f"{base_message} {name}!"


class LifecycleService(Initializable, Disposable):
    """Service with initialization and disposal."""
    
    def __init__(self):
        """Initialize the service."""
        self.initialized = False
        self.disposed = False
        self.messages: List[str] = []
    
    def initialize(self) -> None:
        """Initialize the service."""
        self.initialized = True
        self.messages.append("initialized")
    
    def dispose(self) -> None:
        """Dispose of the service."""
        self.disposed = True
        self.messages.append("disposed")
    
    def get_status(self) -> str:
        """Get the service status."""
        return f"Initialized: {self.initialized}, Disposed: {self.disposed}"


# =============================================================================
# Tests
# =============================================================================

@pytest.fixture(autouse=True)
def setup_teardown():
    """Set up and tear down the DI container for each test."""
    # Reset the container before the test
    reset_container()
    yield
    # Reset the container after the test
    reset_container()


def test_container_initialization():
    """Test that a container can be initialized."""
    # Container should not be available before initialization
    with pytest.raises(DomainError):
        get_container()
    
    # Initialize the container
    initialize_container()
    
    # Container should be available after initialization
    container = get_container()
    assert container is not None
    assert isinstance(container, DIContainer)


def test_singleton_registration_and_resolution():
    """Test singleton registration and resolution."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Register a singleton service
    container.register_singleton(IMessageService, SimpleMessageService)
    
    # Resolve the service
    service1 = get_service(IMessageService)
    service2 = get_service(IMessageService)
    
    # The services should be the same instance
    assert service1 is service2
    assert service1.get_message() == "Hello, World!"


def test_instance_registration():
    """Test registering an existing instance."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Create an instance
    message_service = ConfigurableMessageService("Custom message")
    
    # Register the instance
    container.register_instance(IMessageService, message_service)
    
    # Resolve the service
    service = get_service(IMessageService)
    
    # The service should be the same instance
    assert service is message_service
    assert service.get_message() == "Custom message"


def test_scoped_registration_and_resolution():
    """Test scoped registration and resolution."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Register a scoped service
    container.register_scoped(IMessageService, ConfigurableMessageService)
    
    # Create scopes
    with create_scope("scope1") as scope1:
        with create_scope("scope2") as scope2:
            # Resolve the service in each scope
            service1a = scope1.get_service(IMessageService)
            service1b = scope1.get_service(IMessageService)
            service2 = scope2.get_service(IMessageService)
            
            # Services in the same scope should be the same instance
            assert service1a is service1b
            
            # Services in different scopes should be different instances
            assert service1a is not service2
            
            # All services should work correctly
            assert service1a.get_message() == "Configurable message"
            assert service2.get_message() == "Configurable message"


def test_transient_registration_and_resolution():
    """Test transient registration and resolution."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Register a transient service
    container.register_transient(IMessageService, ConfigurableMessageService)
    
    # Resolve the service multiple times
    service1 = get_service(IMessageService)
    service2 = get_service(IMessageService)
    
    # The services should be different instances
    assert service1 is not service2
    
    # All services should work correctly
    assert service1.get_message() == "Configurable message"
    assert service2.get_message() == "Configurable message"


def test_dependency_resolution():
    """Test automatic dependency resolution."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Register services
    container.register_singleton(IMessageService, SimpleMessageService)
    container.register_singleton(IGreetingService, SimpleGreetingService)
    
    # Resolve the greeting service
    greeting_service = get_service(IGreetingService)
    
    # The greeting service should have a message service injected
    assert greeting_service.greet("Alice") == "Hello, World! Alice!"


def test_factory_registration():
    """Test registering a service with a factory."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Define a factory function
    def create_message_service() -> IMessageService:
        return ConfigurableMessageService("Factory-created message")
    
    # Register a factory
    container.register_factory(IMessageService, create_message_service)
    
    # Resolve the service
    service = get_service(IMessageService)
    
    # The service should be created by the factory
    assert service.get_message() == "Factory-created message"


def test_lifecycle_management():
    """Test service lifecycle management."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Register a lifecycle service
    container.register_singleton(LifecycleService)
    
    # Resolve the service
    service = get_service(LifecycleService)
    
    # The service should be automatically initialized
    assert service.initialized
    assert "initialized" in service.messages
    
    # The service is not disposed yet
    assert not service.disposed
    
    # Reset the container (which should dispose services)
    reset_container()
    
    # Verify disposal messages
    assert "disposed" in service.messages