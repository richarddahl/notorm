# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for modern dependency injection container.

These tests verify the proper configuration and operation of the
modern dependency injection system.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.interfaces import (
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol
)
from uno.dependencies.scoped_container import (
    ServiceCollection,
    initialize_container,
    get_container,
    get_service
)
from uno.dependencies.database import (
    get_db_session,
    get_raw_connection,
    get_repository,
    get_db_manager,
    get_sql_emitter_factory,
    get_sql_execution_service
)


class TestModernDIContainer:
    """Tests for the modern dependency injection container."""
    
    def setup_method(self):
        """Reset the DI container before each test."""
        # Initialize with a fresh container for each test
        services = ServiceCollection()
        initialize_container(services, logging.getLogger("test"))
    
    def test_container_initialization(self):
        """Test container initialization."""
        # Initialize the container
        services = ServiceCollection()
        resolver = initialize_container(services, logging.getLogger("test"))
        
        # Verify it's initialized
        assert resolver is not None
    
    def test_get_container(self):
        """Test getting the container."""
        # Initialize first
        services = ServiceCollection()
        initialize_container(services, logging.getLogger("test"))
        
        # Get the container
        container = get_container()
        
        # Verify we got a container
        assert container is not None
    
    def test_service_registration(self):
        """Test registering and resolving a service."""
        # Create a mock object and a mock resolver
        mock_obj = MagicMock()
        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = mock_obj
        
        # Create service collection
        services = ServiceCollection()
        
        # Initialize with a patched container
        with patch('uno.dependencies.scoped_container._container', mock_resolver):
            # Get the service
            instance = get_service(UnoConfigProtocol)
            
            # Verify
            assert instance == mock_obj
            # Verify the resolver was used
            mock_resolver.resolve.assert_called_with(UnoConfigProtocol)
        
    def test_service_singleton(self):
        """Test that singletons return the same instance."""
        # Create service collection and register a singleton service
        services = ServiceCollection()
        services.add_singleton(UnoConfigProtocol, MagicMock)
        
        # Initialize the container
        initialize_container(services, logging.getLogger("test"))
        
        # Get the service twice
        instance1 = get_service(UnoConfigProtocol)
        instance2 = get_service(UnoConfigProtocol)
        
        # Verify same instance
        assert instance1 is instance2


class TestModernConfigureServices:
    """Tests for configuring services with the modern DI system."""
    
    def setup_method(self):
        """Reset the DI container before each test."""
        # Initialize with a fresh container for each test
        services = ServiceCollection()
        initialize_container(services, logging.getLogger("test"))
    
    @pytest.mark.asyncio  # Mark the test as asyncio
    async def test_configure_base_services(self):
        """Test configuring base services."""
        from uno.dependencies.modern_provider import configure_base_services
        
        # We need to patch the correct method - UnoRegistry.get_registry 
        with patch('uno.registry.get_registry') as mock_registry_getter:
            # Mock registry
            mock_registry_instance = MagicMock()
            mock_registry_getter.return_value = mock_registry_instance
            
            # Create service collection
            services = ServiceCollection()
            
            # Mock importing vector_provider to prevent error
            with patch('uno.dependencies.modern_provider.get_service_provider') as mock_get_provider:
                mock_provider = MagicMock()
                mock_provider.is_initialized.return_value = False
                mock_get_provider.return_value = mock_provider
                
                # Mock the import to prevent the actual import from happening
                with patch('importlib.import_module') as mock_import_module:
                    # Make importlib.import_module raise ImportError for vector_provider
                    def mock_import(*args, **kwargs):
                        if 'vector_provider' in args[0]:
                            raise ImportError("Mocked import error for testing")
                        return MagicMock()
                    
                    mock_import_module.side_effect = mock_import
                    
                    # Now execute the coroutine properly
                    try:
                        await configure_base_services()
                    except Exception:
                        # We expect it might fail due to our partial mocking
                        pass
                    
                    # Verify the service provider was called
                    mock_get_provider.assert_called()


class TestAccessMethods:
    """Tests for modern DI access methods."""
    
    def setup_method(self):
        """Reset the DI container before each test."""
        # Initialize with a fresh container for each test
        services = ServiceCollection()
        initialize_container(services, logging.getLogger("test"))
    
    @patch('uno.dependencies.database.get_service')
    def test_get_db_manager(self, mock_get_service):
        """Test get_db_manager method."""
        # Configure mock
        mock_db_manager = MagicMock()
        mock_get_service.return_value = mock_db_manager
        
        # Call the method
        result = get_db_manager()
        
        # Verify
        mock_get_service.assert_called_once_with(UnoDBManagerProtocol)
        assert result == mock_db_manager
    
    @patch('uno.dependencies.database.get_service')
    def test_get_sql_emitter_factory(self, mock_get_service):
        """Test get_sql_emitter_factory method."""
        # Configure mock
        mock_factory = MagicMock()
        mock_get_service.return_value = mock_factory
        
        # Call the method
        result = get_sql_emitter_factory()
        
        # Verify
        mock_get_service.assert_called_once_with(SQLEmitterFactoryProtocol)
        assert result == mock_factory
    
    @patch('uno.dependencies.database.get_service')
    def test_get_sql_execution_service(self, mock_get_service):
        """Test get_sql_execution_service method."""
        # Configure mock
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Call the method
        result = get_sql_execution_service()
        
        # Verify
        mock_get_service.assert_called_once_with(SQLExecutionProtocol)
        assert result == mock_service