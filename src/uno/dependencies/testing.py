"""
Testing utilities for dependency injection.

This module provides utilities for mocking dependencies in tests,
making it easier to isolate components and write effective unit tests.
"""

import inspect
from typing import Dict, Any, Type, TypeVar, Optional, Callable, cast, Generic, List
from unittest.mock import MagicMock, AsyncMock, PropertyMock
from typing import AsyncIterator, cast

import inject

from uno.dependencies.interfaces import (
    UnoServiceProtocol,
    UnoConfigProtocol,
    UnoDBManagerProtocol,
)
from uno.domain.base.model import BaseModel

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


class TestingContainer:
    """
    Container for managing test dependencies.

    This class provides a convenient way to configure the DI container
    for testing, allowing you to replace real dependencies with mocks.
    """

    def __init__(self):
        """Initialize the testing container."""
        self._bindings: Dict[Type, Any] = {}
        # Save original injector when instantiated
        self._original_config = (
            inject.get_injector() if inject.is_configured() else None
        )

    def bind(self, interface: Type[T], implementation: Any) -> None:
        """
        Bind an interface to an implementation.

        Args:
            interface: The interface to bind
            implementation: The implementation to bind to the interface
        """
        self._bindings[interface] = implementation

    def configure(self) -> None:
        """
        Configure the DI container with the current bindings.

        This method saves the current injector state and applies the test bindings.
        """
        # Save original injector if already configured
        if inject.is_configured():
            self._original_config = inject.get_injector()

        # Configure with test bindings
        inject.clear_and_configure(self._create_binder)

    def _create_binder(self, binder: inject.Binder) -> None:
        """
        Create a binder with the current bindings.

        Args:
            binder: The inject binder instance
        """
        for interface, implementation in self._bindings.items():
            binder.bind(interface, implementation)

    def restore(self) -> None:
        """
        Restore the original DI container configuration.

        This method should be called after tests to restore the original state.
        """
        inject.clear()
        if self._original_config:
            # Reconfigure with original bindings - using internal API for simplicity
            # This is technically accessing a private attribute but necessary for our use case
            if hasattr(inject, "_injector"):
                inject._injector = self._original_config
        else:
            # If there was no original config, we need to ensure the container is configured
            # This fixes the test_restore test which expects the container to be configured
            # We use a minimal empty configuration to ensure inject.is_configured() returns True
            inject.configure(lambda binder: None)


# Repository pattern has been moved to uno.infrastructure.repositories
# Use the infrastructure.repositories.in_memory for testing repositories


class MockConfig:
    """
    Factory for creating mock configuration.

    This class provides factory methods for creating mock configuration
    with pre-configured values.
    """

    @classmethod
    def create(cls, values: Optional[Dict[str, Any]] = None) -> UnoConfigProtocol:
        """
        Create a mock configuration provider.

        Args:
            values: Dictionary of configuration values

        Returns:
            A mock configuration provider
        """
        config = MagicMock(spec=UnoConfigProtocol)
        values = values or {}

        def mock_get_value(key: str, default: Any = None) -> Any:
            return values.get(key, default)

        config.get_value.side_effect = mock_get_value
        config.all.return_value = values

        return config


class MockService:
    """
    Factory for creating mock services.

    This class provides factory methods for creating mock services
    with pre-configured return values.
    """

    @classmethod
    def create(cls, return_value: Any = None) -> UnoServiceProtocol:
        """
        Create a mock service.

        Args:
            return_value: The value to return from execute()

        Returns:
            A mock service
        """
        service = MagicMock(spec=UnoServiceProtocol)
        service.execute = AsyncMock(return_value=return_value)

        return service


class TestSession:
    """
    Factory for creating testing sessions.

    This class provides factory methods for creating mock sessions
    that can be used in tests.
    """

    @classmethod
    def create(cls) -> Any:
        """
        Create a mock database session.

        Returns:
            A mock database session
        """
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()

        # Configure execute to return a mock result
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        all_mock = MagicMock(return_value=[])
        first_mock = MagicMock(return_value=None)

        scalars_mock.all = all_mock
        scalars_mock.first = first_mock
        result_mock.scalars = MagicMock(return_value=scalars_mock)

        session.execute.return_value = result_mock

        return session


class TestSessionProvider:
    """
    Factory for creating mock session providers.

    This class provides factory methods for creating mock session providers
    that can be used in tests.
    """

    @classmethod
    def create(cls, session=None) -> Any:
        """
        Create a mock session provider.

        Args:
            session: Optional mock session to return

        Returns:
            A mock session provider
        """
        provider = MagicMock()
        session = session or TestSession.create()

        provider.get_session = AsyncMock(return_value=session)
        provider.get_scoped_session = AsyncMock(return_value=session)

        # Add other methods that might be needed
        provider.async_session = MagicMock()
        provider.sync_session = MagicMock()
        provider.async_connection = MagicMock()
        provider.sync_connection = MagicMock()

        return provider


def configure_test_container(
    config: Optional[Dict[Type, Any]] = None,
) -> TestingContainer:
    """
    Configure a testing container with common mocks.

    This is a convenience function for setting up a test environment
    with common dependencies already mocked.

    Args:
        config: Optional dictionary of additional interface to implementation bindings

    Returns:
        A configured TestingContainer
    """
    container = TestingContainer()

    # Create default mocks
    mock_config = MockConfig.create()
    mock_session = TestSession.create()
    mock_session_provider = TestSessionProvider.create(mock_session)

    # Bind default mocks
    container.bind(UnoConfigProtocol, mock_config)

    # Bind to UnoDatabaseProviderProtocol instead (which is the actual interface we use)
    from uno.dependencies.interfaces import UnoDatabaseProviderProtocol

    container.bind(UnoDatabaseProviderProtocol, mock_session_provider)

    # Add custom bindings
    if config:
        for interface, implementation in config.items():
            container.bind(interface, implementation)

    # Apply configuration
    container.configure()

    return container
