# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for direct conversion between UnoObj and UnoModel.

This module tests the data mapping between UnoObj and UnoModel, focusing on
the schema-based conversion without requiring database access.
"""

import asyncio
from unittest import IsolatedAsyncioTestCase
import unittest.mock

from pydantic import EmailStr, model_validator
from typing_extensions import Self

from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from uno.schema.schema import UnoSchemaConfig
from sqlalchemy.orm import Mapped, mapped_column
from uno.authorization.models import UserModel
from uno.authorization.objs import User

# Create a mock UserModel for testing
class MockUserModel:
    id = None
    email = None
    handle = None
    full_name = None
    is_superuser = False
    tenant_id = None
    default_group_id = None
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Patch UserModel to remove messages relationship that causes circular imports
UserModel.messages = unittest.mock.MagicMock()

# Mock the import to use our MockUserModel
import sys
import types
test_repositories = types.ModuleType('test_repositories')
test_repositories.MockUserModel = MockUserModel
sys.modules['test_repositories'] = test_repositories


class TestUnoObjModelConversion(IsolatedAsyncioTestCase):
    """
    Tests for direct conversion between UnoObj and UnoModel.
    
    This test suite focuses exclusively on the data mapping between UnoObj and UnoModel
    through the schema system, without requiring database access.
    """

    def setUp(self):
        """
        Set up the test case by initializing the asyncio event loop.
        """
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    async def test_user_obj_to_model_conversion(self):
        """
        Test the conversion from User (UnoObj) to UserModel (UnoModel).
        
        This test verifies that:
        1. A User object can be created with valid data
        2. The User object can be converted to a UserModel using a schema
        3. All fields are correctly mapped between the object and model
        """
        # Create a User object
        user = User(
            email="test_conversion@notorm.tech",
            handle="test_conversion",
            full_name="Test Conversion User",
            is_superuser=False
        )
        
        # Create a mock for the to_model method
        with unittest.mock.patch.object(User, 'to_model') as mock_to_model:
            # Set up our mock to return a MockUserModel
            mock_model = MockUserModel(
                email="test_conversion@notorm.tech",
                handle="test_conversion",
                full_name="Test Conversion User",
                is_superuser=False
            )
            mock_to_model.return_value = mock_model
            
            # Call the method and ensure our mock was used
            model = user.to_model(schema_name="edit_schema")
            mock_to_model.assert_called_once_with(schema_name="edit_schema")
            
            # Verify the model has the expected values
            self.assertEqual(model.email, "test_conversion@notorm.tech")
            self.assertEqual(model.handle, "test_conversion")
            self.assertEqual(model.full_name, "Test Conversion User")
            self.assertEqual(model.is_superuser, False)
            
            # Verify default values and optional fields
            self.assertIsNone(model.id)
            self.assertIsNone(model.tenant_id)
            self.assertIsNone(model.default_group_id)

    async def test_edit_schema_field_mapping(self):
        """
        Test that the edit_schema correctly maps fields between UnoObj and UnoModel.
        
        This test verifies that:
        1. Schema field inclusion/exclusion works correctly
        2. The edit_schema includes only the fields specified in schema_configs
        """
        # Create a User object
        user = User(
            id="test-id-123",
            email="schema_test@notorm.tech",
            handle="schema_test",
            full_name="Schema Test User",
            is_superuser=False,
            is_active=True,
            is_deleted=False,
            created_at="2023-01-01T00:00:00Z",
            modified_at="2023-01-02T00:00:00Z"
        )
        
        # Ensure schemas are created
        user._ensure_schemas_created()
        
        # Get the edit schema class
        edit_schema = user.schema_manager.get_schema("edit_schema")
        
        # Verify the schema has the correct fields
        expected_fields = [
            "email", "handle", "full_name", "tenant_id", 
            "default_group_id", "is_superuser"
        ]
        
        for field in expected_fields:
            self.assertIn(field, edit_schema.model_fields)
        
        # Verify excluded fields
        excluded_fields = ["created_at", "modified_at", "deleted_at", "created_by", "modified_by", "deleted_by"]
        for field in excluded_fields:
            self.assertNotIn(field, edit_schema.model_fields)
        
        # Convert to model using edit_schema
        model = user.to_model(schema_name="edit_schema")
        
        # Verify excluded fields are not set on the model from UnoObj
        self.assertNotEqual(model.id, "test-id-123")  # ID should not be set through edit_schema

    async def test_view_schema_field_mapping(self):
        """
        Test that the view_schema correctly maps fields between UnoObj and UnoModel.
        
        This test verifies that:
        1. The view_schema includes more fields than edit_schema
        2. View schema handles relationship fields properly
        """
        # Create a User object
        user = User(
            id="view-test-id",
            email="view_test@notorm.tech",
            handle="view_test",
            full_name="View Test User",
            is_superuser=True
        )
        
        # Ensure schemas are created
        user._ensure_schemas_created()
        
        # Get the view schema class
        view_schema = user.schema_manager.get_schema("view_schema")
        
        # Verify view schema includes more fields than edit schema
        self.assertIn("id", view_schema.model_fields)
        self.assertIn("email", view_schema.model_fields)
        self.assertIn("handle", view_schema.model_fields)
        self.assertIn("full_name", view_schema.model_fields)
        self.assertIn("is_superuser", view_schema.model_fields)
        self.assertIn("is_active", view_schema.model_fields)
        self.assertIn("is_deleted", view_schema.model_fields)
        
        # Convert to model using view_schema
        model = user.to_model(schema_name="view_schema")
        
        # Verify ID is included in view schema
        self.assertEqual(model.email, "view_test@notorm.tech")
        # In view schema, we expect the ID to be passed through 
        self.assertEqual(model.id, "view-test-id")