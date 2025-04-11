# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for dependency injection with DBManager.

These tests verify that the DBManager can be properly injected
via the dependency injection container.
"""

import pytest
import inject
from unittest.mock import MagicMock, patch

from uno.dependencies.container import configure_di, get_instance
from uno.dependencies.interfaces import UnoDBManagerProtocol
from uno.dependencies.database import get_db_manager
from uno.database.db_manager import DBManager


@pytest.fixture
def setup_di():
    """Set up dependency injection for tests."""
    # Create a mock binder
    binder = MagicMock()
    
    # Mock the get_instance function to return a mock db_manager
    mock_db_manager = MagicMock(spec=DBManager)
    
    # Configure the mock binder
    def mock_bind(interface, instance):
        if interface in (DBManager, UnoDBManagerProtocol):
            # Store the db_manager in the fixture
            mock_bind.db_manager = instance
    
    binder.bind = mock_bind
    mock_bind.db_manager = mock_db_manager
    
    # Configure DI with our mock binder
    with patch('inject.Binder', return_value=binder):
        with patch('inject.instance', return_value=mock_db_manager):
            # Configure the DI container
            configure_di(binder)
            yield mock_db_manager


class TestDBManagerDI:
    """Tests for DBManager dependency injection."""
    
    def test_get_db_manager_from_container(self, setup_di):
        """Test retrieving the DBManager from the DI container."""
        with patch('uno.dependencies.database.get_instance', return_value=setup_di):
            # Get the DBManager from the container
            db_manager = get_db_manager()
            
            # Verify we got the right instance
            assert db_manager is setup_di
    
    def test_methods_accessible_via_di(self, setup_di):
        """Test that DBManager methods are accessible through DI."""
        # Configure mocks for the db_manager methods
        setup_di.execute_ddl = MagicMock()
        setup_di.execute_script = MagicMock()
        setup_di.create_schema = MagicMock()
        
        with patch('uno.dependencies.database.get_instance', return_value=setup_di):
            # Get the DBManager
            db_manager = get_db_manager()
            
            # Call some methods
            db_manager.execute_ddl("CREATE TABLE test (id INT);")
            db_manager.execute_script("SELECT 1;")
            db_manager.create_schema("test_schema")
            
            # Verify the methods were called
            setup_di.execute_ddl.assert_called_once_with("CREATE TABLE test (id INT);")
            setup_di.execute_script.assert_called_once_with("SELECT 1;")
            setup_di.create_schema.assert_called_once_with("test_schema")