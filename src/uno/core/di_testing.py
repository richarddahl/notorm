"""
Testing utilities for Uno's dependency injection system.

This module provides tools for testing code that uses the Uno DI container, including
mocking dependencies, creating test containers, and resetting container state.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional, Type, TypeVar, cast

from . import di
from .errors import DomainError

T = TypeVar("T")


class TestContainer:
    """
    Helper class for managing DI containers in tests.
    
    TestContainer provides a convenient way to create isolated DI containers
    for testing, with methods for registering and mocking services.
    """
    
    def __init__(self):
        """Initialize a test container helper."""
        self._original_container = None
        self._container = None
    
    def setup(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Set up a test container.
        
        This method saves the current global container (if any) and creates
        a new container for testing.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        # Save original container if it exists
        self._original_container = di._container
        
        # Reset the global container
        di._container = None
        
        # Create a new container for testing
        di.initialize_container(logger)
        self._container = di.get_container()
    
    def teardown(self) -> None:
        """
        Tear down the test container.
        
        This method restores the original global container saved during setup.
        """
        # Restore original container
        di._container = self._original_container
        self._container = None
    
    def register_mock(self, service_type: Type[T], mock_instance: T) -> None:
        """
        Register a mock service in the test container.
        
        Args:
            service_type: The type of service to mock
            mock_instance: The mock instance to use
            
        Raises:
            DomainError: If the test container is not set up
        """
        if self._container is None:
            raise DomainError(
                message="Test container is not set up",
                code="TEST_CONTAINER_NOT_SETUP",
            )
            
        self._container.register_instance(service_type, mock_instance)
    
    def get_container(self) -> di.DIContainer:
        """
        Get the test container.
        
        Returns:
            The test container
            
        Raises:
            DomainError: If the test container is not set up
        """
        if self._container is None:
            raise DomainError(
                message="Test container is not set up",
                code="TEST_CONTAINER_NOT_SETUP",
            )
            
        return self._container


@contextmanager
def test_container(logger: Optional[logging.Logger] = None):
    """
    Context manager for creating a test container.
    
    This context manager creates a temporary DI container for testing
    and restores the original container when the context exits.
    
    Example:
        ```python
        def test_my_service():
            with test_container() as container:
                # Register mocks
                container.register_instance(Database, MockDatabase())
                
                # Test code that uses the DI container
                service = di.get_service(MyService)
                assert service.do_something() == expected_result
        ```
    
    Args:
        logger: Optional logger for diagnostic information
        
    Yields:
        The test container
    """
    test_helper = TestContainer()
    
    try:
        # Set up test container
        test_helper.setup(logger)
        yield test_helper.get_container()
    finally:
        # Tear down test container
        test_helper.teardown()


def create_test_scope():
    """
    Create a test scope for the current container.
    
    This function creates a scope with a unique "test" ID for testing
    scoped services.
    
    Returns:
        A test service scope
    """
    return di.get_container().create_scope()


@contextmanager
def inject_mock(service_type: Type[T], mock_instance: T):
    """
    Temporarily inject a mock service into the global container.
    
    This context manager temporarily replaces a service in the global
    container with a mock implementation, then restores the original
    implementation when the context exits.
    
    Example:
        ```python
        def test_my_function():
            mock_service = MagicMock(spec=MyService)
            mock_service.do_something.return_value = "mocked result"
            
            with inject_mock(MyService, mock_service):
                result = my_function_that_uses_di()
                assert result == "expected result using mock"
        ```
    
    Args:
        service_type: The type of service to mock
        mock_instance: The mock instance to use
        
    Yields:
        None
    """
    container = di.get_container()
    
    # Save original registration and instance (if it exists)
    original_registration = container._registry.get_registration(service_type)
    original_instance = container._registry._singleton_instances.get(service_type)
    
    try:
        # Register mock instance
        container.register_instance(service_type, mock_instance)
        yield
    finally:
        # Restore original registration and instance
        if original_registration is not None:
            container._registry.register(original_registration)
            
            if original_instance is not None:
                container._registry._singleton_instances[service_type] = original_instance
            elif service_type in container._registry._singleton_instances:
                del container._registry._singleton_instances[service_type]