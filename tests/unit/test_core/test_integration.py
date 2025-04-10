# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the integration between UnoObj, UnoModel, and UnoDB.

This module tests the complete roundtrip from UnoObj -> UnoModel -> UnoDB -> UnoModel -> UnoObj
using the User class as the primary example.
"""

import asyncio
from unittest import IsolatedAsyncioTestCase

from uno.authorization.objs import User
from uno.authorization.models import UserModel
from uno.database.manager import DBManager
from uno.settings import uno_settings


class TestUnoIntegration(IsolatedAsyncioTestCase):
    """
    Tests for the integration between the UnoObj, UnoModel, and UnoDB classes.
    
    This test suite focuses on the data mapping between UnoObj and UnoModel,
    ensuring field values are correctly passed between the two layers.
    """

    def setUp(self):
        """
        Set up the test case by initializing the asyncio event loop.
        
        This method retrieves the current event loop and assigns it to an instance variable.
        It then assigns the same event loop as the active event loop, ensuring that asynchronous
        operations executed within the tests use a consistent and dedicated event loop.
        """
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    async def test_create_superuser_obj_model_conversion(self):
        """
        Test the conversion between UnoObj and UnoModel using schema.
        
        This test focuses on the data mapping between UnoObj and UnoModel via schema,
        ensuring field values are correctly passed between the layers.
        """
        # Create a superuser UnoObj instance
        superuser = User(
            email="test_integration@notorm.tech",
            handle="test_integration",
            full_name="Test Integration User",
            is_superuser=True
        )
        
        # Verify initial state
        assert superuser.id is None
        assert superuser.email == "test_integration@notorm.tech"
        assert superuser.handle == "test_integration"
        assert superuser.full_name == "Test Integration User"
        assert superuser.is_superuser is True
        
        # Ensure schemas are created
        superuser._ensure_schemas_created()
        
        # Get the schema and use it to convert to UnoModel
        db_model = superuser.to_model(schema_name="edit_schema")
        
        # Verify UnoModel instance
        assert isinstance(db_model, UserModel)
        assert db_model.id is None
        assert db_model.email == "test_integration@notorm.tech"
        assert db_model.handle == "test_integration"
        assert db_model.full_name == "Test Integration User"
        assert db_model.is_superuser is True

    async def test_schema_generation_consistency(self):
        """
        Test the consistency of schema generation from UnoObj.
        
        This test verifies that the schema generation process creates the expected
        schemas with the correct fields, and that the fields align with the UnoObj fields.
        """
        # Create a User instance to generate schemas
        user = User(
            email="schema_test@notorm.tech",
            handle="schema_test",
            full_name="Schema Test User",
            is_superuser=False
        )
        
        # Ensure schemas are created
        user._ensure_schemas_created()
        
        # Get the view schema
        view_schema = user.schema_manager.get_schema("view_schema")
        assert view_schema is not None
        
        # Verify key fields in view schema
        assert "id" in view_schema.model_fields
        assert "email" in view_schema.model_fields
        assert "handle" in view_schema.model_fields
        assert "full_name" in view_schema.model_fields
        assert "is_superuser" in view_schema.model_fields
        
        # Get the edit schema
        edit_schema = user.schema_manager.get_schema("edit_schema")
        assert edit_schema is not None
        
        # Verify edit schema has expected fields according to schema_configs
        expected_edit_fields = [
            "email", "handle", "full_name", "tenant_id", 
            "default_group_id", "is_superuser"
        ]
        for field in expected_edit_fields:
            assert field in edit_schema.model_fields, f"Field {field} missing from edit schema"