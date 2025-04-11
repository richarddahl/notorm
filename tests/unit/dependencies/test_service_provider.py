"""
Tests for the unified ServiceProvider.

This module contains tests for the ServiceProvider class, which
provides a centralized interface for accessing services.
"""

import pytest
from unittest.mock import MagicMock, patch, call

from typing import Protocol, runtime_checkable
from uno.dependencies.provider import ServiceProvider, get_service_provider

@runtime_checkable
class CustomServiceProtocol(Protocol):
    """Protocol for testing custom service registration."""
    def do_something(self) -> str:
        """Do something and return a result."""
        ...
from uno.dependencies.interfaces import (
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol,
    SchemaManagerProtocol,
)


class TestServiceProvider:
    """Tests for the ServiceProvider class."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('uno.dependencies.provider.inject'):
            self.provider = ServiceProvider()

    def test_initialization(self):
        """Test service provider initialization."""
        assert not self.provider._initialized
        
        with patch('uno.dependencies.provider.inject') as mock_inject:
            mock_inject.is_configured.return_value = False
            
            self.provider.initialize()
            
            assert self.provider._initialized
            mock_inject.is_configured.assert_called_once()
            mock_inject.configure.assert_called_once()

    def test_get_service_uninitialized(self):
        """Test getting a service when provider is not initialized."""
        with pytest.raises(ValueError):
            self.provider.get_service(UnoConfigProtocol)

    def test_get_service(self):
        """Test getting a service."""
        mock_service = MagicMock()
        
        with patch('uno.dependencies.provider.get_instance') as mock_get_instance:
            mock_get_instance.return_value = mock_service
            
            # Initialize provider
            with patch('uno.dependencies.provider.inject') as mock_inject:
                mock_inject.is_configured.return_value = True
                self.provider.initialize()
            
            # Get service
            service = self.provider.get_service(UnoConfigProtocol)
            
            assert service == mock_service
            mock_get_instance.assert_called_once_with(UnoConfigProtocol)

    def test_specialized_service_getters(self):
        """Test specialized service getter methods."""
        with patch('uno.dependencies.provider.get_instance') as mock_get_instance:
            # Create different mock services for each type
            service_mocks = {
                UnoConfigProtocol: MagicMock(name="config"),
                UnoDatabaseProviderProtocol: MagicMock(name="db_provider"),
                UnoDBManagerProtocol: MagicMock(name="db_manager"),
                SQLEmitterFactoryProtocol: MagicMock(name="sql_factory"),
                SQLExecutionProtocol: MagicMock(name="sql_execution"),
                SchemaManagerProtocol: MagicMock(name="schema_manager"),
            }
            
            # Configure mock to return appropriate service for each type
            mock_get_instance.side_effect = lambda t: service_mocks.get(t, MagicMock())
            
            # Initialize provider
            with patch('uno.dependencies.provider.inject') as mock_inject:
                mock_inject.is_configured.return_value = True
                self.provider.initialize()
            
            # Test each specialized getter
            assert self.provider.get_config() == service_mocks[UnoConfigProtocol]
            assert self.provider.get_db_provider() == service_mocks[UnoDatabaseProviderProtocol]
            assert self.provider.get_db_manager() == service_mocks[UnoDBManagerProtocol]
            assert self.provider.get_sql_emitter_factory() == service_mocks[SQLEmitterFactoryProtocol]
            assert self.provider.get_sql_execution_service() == service_mocks[SQLExecutionProtocol]
            assert self.provider.get_schema_manager() == service_mocks[SchemaManagerProtocol]
            
            # Check that get_instance was called with the right types
            expected_calls = [
                call(UnoConfigProtocol),
                call(UnoDatabaseProviderProtocol),
                call(UnoDBManagerProtocol),
                call(SQLEmitterFactoryProtocol),
                call(SQLExecutionProtocol),
                call(SchemaManagerProtocol),
            ]
            
            mock_get_instance.assert_has_calls(expected_calls, any_order=True)
            assert mock_get_instance.call_count == len(expected_calls)

    def test_register_service(self):
        """Test registering and retrieving a custom service."""
        # Create a custom service implementation
        class CustomService:
            def do_something(self) -> str:
                return "custom service result"
        
        custom_service = CustomService()
        
        # Initialize provider
        with patch('uno.dependencies.provider.inject') as mock_inject:
            mock_inject.is_configured.return_value = True
            self.provider.initialize()
        
        # Register the custom service
        self.provider.register_service(CustomServiceProtocol, custom_service)
        
        # Retrieve the custom service
        retrieved_service = self.provider.get_service(CustomServiceProtocol)
        
        # Verify it's the same instance
        assert retrieved_service is custom_service
        assert isinstance(retrieved_service, CustomServiceProtocol)
        assert retrieved_service.do_something() == "custom service result"

    def test_get_service_provider(self):
        """Test getting the global service provider instance."""
        with patch('uno.dependencies.provider._service_provider') as mock_provider:
            provider = get_service_provider()
            assert provider == mock_provider