# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for dependency injection with DBManager.

These tests verify that the DBManager can be properly injected
via the modern dependency injection system.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch

from uno.dependencies.interfaces import UnoDBManagerProtocol
from uno.dependencies.database import get_db_manager
from uno.database.db_manager import DBManager
from uno.dependencies.scoped_container import ServiceCollection, initialize_container


@pytest.fixture
def setup_modern_di():
    """Set up modern dependency injection for tests."""
    # Create a mock db_manager with all required methods
    mock_db_manager = MagicMock(spec=DBManager)
    
    # Add methods that are expected on the protocol
    for method_name in [
        'execute_ddl', 'execute_script', 'create_schema', 'drop_schema',
        'execute_from_emitter', 'execute_from_emitters', 'create_extension',
        'table_exists', 'function_exists', 'type_exists', 'trigger_exists',
        'policy_exists'
    ]:
        setattr(mock_db_manager, method_name, MagicMock())
    
    # Import and configure the container from scratch
    import uno.dependencies.scoped_container as container_module
    
    # Reset the container before starting
    container_module._container = None
    
    # Create a fresh service collection
    services = ServiceCollection()
    
    # Register the protocol implementation directly
    services.add_singleton(UnoDBManagerProtocol, DBManager)
    # Register the concrete instance
    services.add_instance(UnoDBManagerProtocol, mock_db_manager)
    services.add_instance(DBManager, mock_db_manager)
    
    # Initialize the container
    logger = logging.getLogger("test")
    initialize_container(services, logger)
    
    # Reset the container after the test
    try:
        yield mock_db_manager
    finally:
        # This ensures we don't leave a configured container that might affect other tests
        container_module._container = None


class TestDBManagerDI:
    """Tests for DBManager dependency injection."""
    
    def test_get_db_manager_from_container(self, setup_modern_di):
        """Test retrieving the DBManager from the DI container."""
        # Get the DBManager from the container using the get_service function directly
        # instead of get_db_manager() to better test our fixture setup
        from uno.dependencies.scoped_container import get_service
        db_manager = get_service(UnoDBManagerProtocol)
        
        # Verify we got the right instance
        assert db_manager is setup_modern_di
    
    def test_methods_accessible_via_di(self, setup_modern_di):
        """Test that DBManager methods are accessible through DI."""
        # Configure mocks for the db_manager methods
        setup_modern_di.execute_ddl = MagicMock()
        setup_modern_di.execute_script = MagicMock()
        setup_modern_di.create_schema = MagicMock()
        
        # Get the DBManager directly from the container
        from uno.dependencies.scoped_container import get_service
        db_manager = get_service(UnoDBManagerProtocol)
        
        # Call some methods
        db_manager.execute_ddl("CREATE TABLE test (id INT);")
        db_manager.execute_script("SELECT 1;")
        db_manager.create_schema("test_schema")
        
        # Verify the methods were called
        setup_modern_di.execute_ddl.assert_called_once_with("CREATE TABLE test (id INT);")
        setup_modern_di.execute_script.assert_called_once_with("SELECT 1;")
        setup_modern_di.create_schema.assert_called_once_with("test_schema")