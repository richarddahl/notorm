# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for UnoObj schema generation and validation.

This module tests the schema generation and validation functionality of UnoObj
without requiring actual database access or model instantiation.
"""

import asyncio
from unittest import IsolatedAsyncioTestCase

from uno.authorization.objs import User


class TestUnoObjSchema(IsolatedAsyncioTestCase):
    """
    Tests for UnoObj schema generation and validation.
    
    This test suite focuses on the schema-related functionality of UnoObj,
    including schema generation, field inclusion/exclusion, and validation.
    """

    def setUp(self):
        """
        Set up the test case by initializing the asyncio event loop.
        """
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    async def test_schema_creation(self):
        """
        Test that schemas are correctly created from UnoObj.
        
        This test verifies that:
        1. Schemas are created correctly
        2. Schema managers hold references to the schema classes
        """
        # Create a User object
        user = User(
            email="schema_test@notorm.tech",
            handle="schema_test",
            full_name="Schema Test User",
            is_superuser=False
        )
        
        # Ensure schemas are created
        user._ensure_schemas_created()
        
        # Check that schemas exist
        self.assertIsNotNone(user.schema_manager)
        self.assertTrue(user.schema_manager.schemas)
        
        # Check that view_schema and edit_schema are created
        view_schema = user.schema_manager.get_schema("view_schema")
        edit_schema = user.schema_manager.get_schema("edit_schema")
        
        self.assertIsNotNone(view_schema)
        self.assertIsNotNone(edit_schema)

    async def test_view_schema_field_inclusion(self):
        """
        Test that view_schema includes the correct fields.
        
        This test verifies that the view_schema includes all fields
        that should be visible to users in read operations.
        """
        # Create a User object
        user = User(
            email="view_schema_test@notorm.tech",
            handle="view_schema_test",
            full_name="View Schema Test User",
            is_superuser=False
        )
        
        # Ensure schemas are created
        user._ensure_schemas_created()
        
        # Get the view schema
        view_schema = user.schema_manager.get_schema("view_schema")
        
        # Check that key fields are included
        required_fields = [
            "id", "email", "handle", "full_name", "is_superuser",
            "is_active", "is_deleted", "tenant_id", "default_group_id"
        ]
        
        for field in required_fields:
            self.assertIn(field, view_schema.model_fields)
        
        # Check that excluded fields are not included
        excluded_fields = ["created_by", "modified_by", "deleted_by", "tenant", "default_group"]
        for field in excluded_fields:
            self.assertNotIn(field, view_schema.model_fields)

    async def test_edit_schema_field_inclusion(self):
        """
        Test that edit_schema includes only the editable fields.
        
        This test verifies that the edit_schema includes only fields
        that should be editable by users in write operations.
        """
        # Create a User object
        user = User(
            email="edit_schema_test@notorm.tech",
            handle="edit_schema_test",
            full_name="Edit Schema Test User",
            is_superuser=False
        )
        
        # Ensure schemas are created
        user._ensure_schemas_created()
        
        # Get the edit schema
        edit_schema = user.schema_manager.get_schema("edit_schema")
        
        # Check that only editable fields are included
        editable_fields = [
            "email", "handle", "full_name", "tenant_id", 
            "default_group_id", "is_superuser"
        ]
        
        for field in editable_fields:
            self.assertIn(field, edit_schema.model_fields)
        
        # Check that non-editable fields are excluded
        non_editable_fields = [
            "id", "created_at", "modified_at", "deleted_at",
            "created_by_id", "modified_by_id", "deleted_by_id",
            "is_active", "is_deleted"
        ]
        
        for field in non_editable_fields:
            self.assertNotIn(field, edit_schema.model_fields)

    async def test_schema_validation(self):
        """
        Test that schemas correctly validate data.
        
        This test verifies that schemas apply appropriate validation
        rules to data based on field types and constraints.
        """
        # Create a User object
        user = User(
            email="validation_test@notorm.tech",
            handle="validation_test",
            full_name="Validation Test User",
            is_superuser=False
        )
        
        # Ensure schemas are created
        user._ensure_schemas_created()
        
        # Get the edit schema class
        edit_schema_class = user.schema_manager.get_schema("edit_schema")
        
        # Create a valid schema instance
        valid_schema = edit_schema_class(
            email="valid@notorm.tech",
            handle="valid_handle",
            full_name="Valid User",
            is_superuser=False
        )
        
        self.assertEqual(valid_schema.email, "valid@notorm.tech")
        self.assertEqual(valid_schema.handle, "valid_handle")
        
        # Test validation error for invalid email
        try:
            invalid_schema = edit_schema_class(
                email="invalid-email",  # Invalid email format
                handle="invalid_handle",
                full_name="Invalid User",
                is_superuser=False
            )
            self.fail("Should have raised validation error for invalid email")
        except Exception as e:
            # Expect validation error
            self.assertIn("email", str(e).lower())