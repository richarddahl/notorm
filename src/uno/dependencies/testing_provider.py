"""
Testing utilities for the modern dependency injection system.

This module provides utilities for testing with the UnoServiceProvider,
including test containers and mocks.
"""

import inspect
import logging
from contextlib import contextmanager
from typing import Dict, Type, TypeVar, Any, Optional, Callable, List, Set, Generic, cast

from uno.dependencies.scoped_container import ServiceScope, ServiceCollection
from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
    Initializable,
    Disposable,
    AsyncInitializable,
    AsyncDisposable,
)

T = TypeVar('T')


class MockService:
    """
    Base class for mock services in tests.
    
    This class can be used as a base class for mock services,
    providing common functionality and tracking method calls.
    """
    
    def __init__(self):
        """Initialize the mock service."""
        self.calls: Dict[str, List[List[Any]]] = {}
        self.initialized = False
        self.disposed = False
    
    def _record_call(self, method_name: str, *args, **kwargs):
        """
        Record a method call.
        
        Args:
            method_name: The name of the method called
            args: Positional arguments passed to the method
            kwargs: Keyword arguments passed to the method
        """
        if method_name not in self.calls:
            self.calls[method_name] = []
        
        self.calls[method_name].append([args, kwargs])
    
    def initialize(self) -> None:
        """Initialize the mock service."""
        self._record_call('initialize')
        self.initialized = True
    
    def dispose(self) -> None:
        """Dispose the mock service."""
        self._record_call('dispose')
        self.disposed = True
    
    async def initialize_async(self) -> None:
        """Initialize the mock service asynchronously."""
        self._record_call('initialize_async')
        self.initialized = True
    
    async def dispose_async(self) -> None:
        """Dispose the mock service asynchronously."""
        self._record_call('dispose_async')
        self.disposed = True


class TestServiceProvider(UnoServiceProvider):
    """
    Test-specific service provider for the Uno framework.
    
    This class extends UnoServiceProvider with test-specific functionality,
    such as tracking registered services and recording method calls.
    """
    
    def __init__(self):
        """Initialize the test service provider."""
        super().__init__("test")
        self.registered_services: Dict[Type, Any] = {}
        self.initialized_services: Set[Type] = set()
        self.disposed_services: Set[Type] = set()
    
    def register_mock(self, service_type: Type[T], mock: T, lifecycle=None) -> None:
        """
        Register a mock service.
        
        Args:
            service_type: The service type to register
            mock: The mock service instance
            lifecycle: Optional service lifecycle
        """
        self.register_instance(service_type, mock)
        self.registered_services[service_type] = mock
    
    def create_and_register_mock(self, service_type: Type[T], lifecycle=None) -> T:
        """
        Create and register a mock service.
        
        Args:
            service_type: The service type to register
            lifecycle: Optional service lifecycle
            
        Returns:
            The created mock service
        """
        mock = MockService()
        self.register_mock(service_type, mock, lifecycle)
        return cast(T, mock)
    
    def reset(self) -> None:
        """Reset the test service provider."""
        self._base_services = ServiceCollection()
        self._extensions = {}
        self._lifecycle_queue = []
        self._initialized = False
        self._initializing = False
        self.registered_services = {}
        self.initialized_services = set()
        self.disposed_services = set()


@contextmanager
def test_service_provider() -> TestServiceProvider:
    """
    Create a test service provider for use in tests.
    
    This context manager creates a TestServiceProvider instance for use in tests,
    resetting it after the test is complete.
    
    Yields:
        The test service provider
    """
    provider = TestServiceProvider()
    try:
        yield provider
    finally:
        provider.reset()


def configure_test_provider() -> TestServiceProvider:
    """
    Configure a test service provider with common mock services.
    
    This function creates and configures a TestServiceProvider with common
    mock services for testing.
    
    Returns:
        The configured test service provider
    """
    provider = TestServiceProvider()
    
    # Configure common mock services here
    # provider.register_mock(UnoConfigProtocol, MockConfig())
    
    return provider