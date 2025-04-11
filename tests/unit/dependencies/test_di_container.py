# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for dependency injection container.

These tests verify the proper configuration and operation of the
dependency injection system.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch

import inject
from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.interfaces import (
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol
)
from uno.dependencies.container import (
    configure_di,
    get_container,
    get_instance,
    UnoConfig
)
from uno.dependencies import (
    get_db_session,
    get_raw_connection,
    get_repository,
    get_db_manager,
    get_sql_emitter_factory,
    get_sql_execution_service
)


class TestDIContainer:
    """Tests for the dependency injection container."""
    
    def setup_method(self):
        """Reset the DI container before each test."""
        inject.clear()
    
    def test_container_configuration(self):
        """Test that the container can be configured."""
        # Configure the container
        inject.configure(lambda binder: None)
        
        # Verify it's configured
        assert inject.is_configured()
    
    def test_get_container(self):
        """Test getting the container."""
        # Get the container
        container = get_container()
        
        # Verify we got a container
        assert container is not None
        assert inject.is_configured()
    
    @patch('inject.instance')
    def test_get_instance(self, mock_instance):
        """Test getting an instance from the container."""
        # Configure mock
        mock_obj = MagicMock()
        mock_instance.return_value = mock_obj
        
        # Get an instance
        instance = get_instance(UnoConfigProtocol)
        
        # Verify the mock was called
        mock_instance.assert_called_once_with(UnoConfigProtocol)
        assert instance == mock_obj
    
    def test_uno_config(self):
        """Test UnoConfig implementation."""
        # Create a config with test settings
        settings = MagicMock()
        settings.TEST_KEY = "test_value"
        settings.__dict__ = {"TEST_KEY": "test_value", "_private": "hidden"}
        
        config = UnoConfig(settings=settings)
        
        # Test get_value
        assert config.get_value("TEST_KEY") == "test_value"
        assert config.get_value("MISSING", "default") == "default"
        
        # Test all
        all_values = config.all()
        assert "TEST_KEY" in all_values
        assert all_values["TEST_KEY"] == "test_value"
        assert "_private" not in all_values


class TestDIConfiguration:
    """Tests for DI configuration."""
    
    def setup_method(self):
        """Reset the DI container before each test."""
        inject.clear()
    
    @patch('uno.dependencies.container.UnoRegistry')
    def test_configure_di_core_services(self, mock_registry):
        """Test configuring core services."""
        # Create a mock binder
        binder = MagicMock()
        
        # Mock registry
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance
        
        # Configure DI
        configure_di(binder)
        
        # Verify core bindings
        assert any(call[0][0] == UnoConfigProtocol for call in binder.bind.call_args_list)
        assert any(call[0][0] == logging.Logger for call in binder.bind.call_args_list)
    
    @patch('uno.dependencies.container.DatabaseProvider')
    def test_configure_di_database_components(self, mock_provider_class):
        """Test configuring database components."""
        # Create mock objects
        binder = MagicMock()
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider
        
        # Configure DI
        with patch('uno.dependencies.container.DBManager') as mock_db_manager_class:
            mock_db_manager = MagicMock()
            mock_db_manager_class.return_value = mock_db_manager
            
            configure_di(binder)
            
            # Verify database bindings
            assert any(call[0][0] == UnoDatabaseProviderProtocol for call in binder.bind.call_args_list)
            assert any(call[0][0] == UnoDBManagerProtocol for call in binder.bind.call_args_list)
    
    @patch('uno.dependencies.container.SQLEmitterFactoryService')
    @patch('uno.dependencies.container.SQLExecutionService')
    def test_configure_di_sql_services(self, mock_execution_class, mock_factory_class):
        """Test configuring SQL services."""
        # Create mock objects
        binder = MagicMock()
        mock_factory = MagicMock()
        mock_execution = MagicMock()
        mock_factory_class.return_value = mock_factory
        mock_execution_class.return_value = mock_execution
        
        # Configure DI
        configure_di(binder)
        
        # Verify SQL service bindings
        assert any(call[0][0] == SQLEmitterFactoryProtocol for call in binder.bind.call_args_list)
        assert any(call[0][0] == SQLExecutionProtocol for call in binder.bind.call_args_list)
        
        # Verify factory methods were called
        mock_factory.register_core_emitters.assert_called_once()


class TestAccessMethods:
    """Tests for DI access methods."""
    
    def setup_method(self):
        """Reset the DI container before each test."""
        inject.clear()
    
    @patch('uno.dependencies.database.get_instance')
    def test_get_db_manager(self, mock_get_instance):
        """Test get_db_manager method."""
        # Configure mock
        mock_db_manager = MagicMock()
        mock_get_instance.return_value = mock_db_manager
        
        # Call the method
        result = get_db_manager()
        
        # Verify
        mock_get_instance.assert_called_once_with(UnoDBManagerProtocol)
        assert result == mock_db_manager
    
    @patch('uno.dependencies.database.get_instance')
    def test_get_sql_emitter_factory(self, mock_get_instance):
        """Test get_sql_emitter_factory method."""
        # Configure mock
        mock_factory = MagicMock()
        mock_get_instance.return_value = mock_factory
        
        # Call the method
        result = get_sql_emitter_factory()
        
        # Verify
        mock_get_instance.assert_called_once_with(SQLEmitterFactoryProtocol)
        assert result == mock_factory
    
    @patch('uno.dependencies.database.get_instance')
    def test_get_sql_execution_service(self, mock_get_instance):
        """Test get_sql_execution_service method."""
        # Configure mock
        mock_service = MagicMock()
        mock_get_instance.return_value = mock_service
        
        # Call the method
        result = get_sql_execution_service()
        
        # Verify
        mock_get_instance.assert_called_once_with(SQLExecutionProtocol)
        assert result == mock_service