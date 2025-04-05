# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest
import pytest_asyncio

from unittest import IsolatedAsyncioTestCase

from uno.auth.objects import User
from uno.config import settings


class TestUser(IsolatedAsyncioTestCase):

    def setUp(self):
        """
        Set up the test case by initializing the asyncio event loop.

        This method retrieves the current event loop and assigns it to an instance variable.
        It then assigns the same event loop as the active event loop, ensuring that asynchronous
        operations executed within the tests use a consistent and dedicated event loop.
        """
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

    async def test_user_model_field_structure(self):
        """
        Test that the User model contains all the expected fields.

        This test verifies that the User model has the correct field structure by checking
        that all required fields exist, including:
        - Basic identity fields (id, email, handle, full_name)
        - Relationship fields (tenant, default_group, group)
        - Boolean status flags (is_superuser, is_active, is_deleted)
        - Audit trail fields (created_at, created_by, modified_at, modified_by, deleted_at, deleted_by)
        """

        assert "id" in User.model_fields.keys()
        assert "email" in User.model_fields.keys()
        assert "handle" in User.model_fields.keys()
        assert "full_name" in User.model_fields.keys()
        assert "tenant" in User.model_fields.keys()
        assert "default_group" in User.model_fields.keys()
        assert "is_superuser" in User.model_fields.keys()
        assert "is_active" in User.model_fields.keys()
        assert "is_deleted" in User.model_fields.keys()
        assert "created_at" in User.model_fields.keys()
        assert "created_by" in User.model_fields.keys()
        assert "modified_at" in User.model_fields.keys()
        assert "modified_by" in User.model_fields.keys()
        assert "deleted_at" in User.model_fields.keys()
        assert "deleted_by" in User.model_fields.keys()

    async def test_minimal_user_model_fields(self):
        """
        Test the initialization of a User model with minimal required fields.

        This test verifies that:
        1. Required fields (email, handle, full_name) are properly assigned
        2. Optional fields have correct default values (is_active=True, is_deleted=False)
        3. Relationship fields (tenant, default_group, group) are None by default
        4. Audit fields (created_at, created_by, etc.) start as None
        5. The is_superuser flag can be set during initialization

        This ensures the User model constructor behaves as expected with minimal input.
        """
        user = User(
            email="admin@notorm.tech",
            handle="admin",
            full_name="Admin",
            is_superuser=True,
        )

        assert user.id == None
        assert user.email == "admin@notorm.tech"
        assert user.handle == "admin"
        assert user.full_name == "Admin"
        assert user.tenant is None
        assert user.default_group is None
        assert user.is_superuser == True
        assert user.is_active == True
        assert user.is_deleted == False
        assert user.created_at is None
        assert user.created_by is None
        assert user.modified_at is None
        assert user.modified_by is None
        assert user.deleted_at is None
        assert user.deleted_by is None

    async def test_email_field_validation(self):
        """
        Test that the email field validation raises a ValueError when an improperly formatted
        email address is provided during the instantiation of a User object.

        This test ensures that the email field, when missing the necessary "@" symbol or formatted
        incorrectly, correctly triggers a ValueError exception, thereby enforcing proper email validation.
        """
        with pytest.raises(ValueError):
            User(
                id="01JNH7SBRV60R5RC1G61E30C1G",
                email="adminnotorm.tech",
                handle="admin",
                full_name="Admin",
                tenant=None,
                default_group=None,
                is_superuser=True,
                is_active=True,
                is_deleted=False,
                created_at="2024-01-01T00:00:00Z",
                created_by=None,
                modified_at="2024-01-01T00:00:00Z",
                modified_by=None,
                deleted_at=None,
                deleted_by=None,
            )

    async def test_full_user_model_fields(self):
        """
        Test that the User model can be instantiated with all expected fields correctly populated.

        This test verifies that creating a User instance with a full set of data including identifiers,
        contact information, status flags, and timestamp fields does not raise any errors and that all
        fields are properly assigned. The test ensures the integrity of the User model by checking the data
        types and values, particularly for date-time entries and boolean flags, to match the intended user
        profile configuration.
        """
        user = User(
            id="01JNH7SBRV60R5RC1G61E30C1G",
            email="admin@notorm.tech",
            handle="admin",
            full_name="Admin",
            tenant=None,
            default_group=None,
            is_superuser=True,
            is_active=True,
            is_deleted=False,
            created_at="2024-01-01T00:00:00Z",
            created_by=None,
            modified_at="2024-01-01T00:00:00Z",
            modified_by=None,
            deleted_at=None,
            deleted_by=None,
        )

    async def test_user_model_set_display_names(self):
        """
        Tests that the User model's configuration properties are correctly set.

        Verifies:
        - The table name is set to "user", ensuring the proper linkage to the corresponding database table.
        - The singular display name is "User", which is used for human-readable identification.
        - The plural display name is "Users", which is essential when referring to multiple user instances.
        """
        assert User.model.__table__.name == "user"
        assert User.display_name == "User"
        assert User.display_name_plural == "Users"

    async def test_user_view_schema(self):
        """
        Tests that the User model's view_schema attribute is properly constructed.

        This test verifies:
        - The view_schema is not None.
        - The view_schema contains exactly 16 fields.
        - Each expected field ('id', 'email', 'handle', 'full_name', 'tenant', 'default_group',
            'group', 'is_superuser', 'is_active', 'is_deleted', 'created_at', 'created_by',
            'modified_at', 'modified_by', 'deleted_at', and 'deleted_by') is present in the model_fields.
        """
        User.set_schemas()
        user = User(
            id="01JNH7SBRV60R5RC1G61E30C1G",
            email="admin@notorm.tech",
            handle="admin",
            full_name="Admin",
            tenant=None,
            default_group=None,
            is_superuser=True,
            is_active=True,
            is_deleted=False,
            created_at="2024-01-01T00:00:00Z",
            created_by=None,
            modified_at="2024-01-01T00:00:00Z",
            modified_by=None,
            deleted_at=None,
            deleted_by=None,
        )
        assert user.view_schema is not None
        assert len(user.view_schema.model_fields) == 15
        assert "id" in user.view_schema.model_fields.keys()
        assert "email" in user.view_schema.model_fields.keys()
        assert "handle" in user.view_schema.model_fields.keys()
        assert "full_name" in user.view_schema.model_fields.keys()
        assert "tenant_id" in user.view_schema.model_fields.keys()
        assert "default_group_id" in user.view_schema.model_fields.keys()
        assert "is_superuser" in user.view_schema.model_fields.keys()
        assert "is_active" in user.view_schema.model_fields.keys()
        assert "is_deleted" in user.view_schema.model_fields.keys()
        assert "created_at" in user.view_schema.model_fields.keys()
        assert "created_by_id" in user.view_schema.model_fields.keys()
        assert "modified_at" in user.view_schema.model_fields.keys()
        assert "modified_by_id" in user.view_schema.model_fields.keys()
        assert "deleted_at" in user.view_schema.model_fields.keys()
        assert "deleted_by_id" in user.view_schema.model_fields.keys()

    async def test_user_edit_schema(self):
        """
        Test that the User model's edit_schema is correctly configured.

        This test verifies that:
        - The edit_schema attribute of a User instance is not None.
        - The edit_schema contains exactly eight fields.
        - The expected fields are present: 'id', 'email', 'handle', 'full_name', 'tenant', 'default_group', 'group', and 'is_superuser'.
        """
        User.set_schemas()
        user = User(
            id="01JNH7SBRV60R5RC1G61E30C1G",
            email="admin@notorm.tech",
            handle="admin",
            full_name="Admin",
            tenant=None,
            default_group=None,
            is_superuser=True,
            is_active=True,
            is_deleted=False,
            created_at="2024-01-01T00:00:00Z",
            created_by=None,
            modified_at="2024-01-01T00:00:00Z",
            modified_by=None,
            deleted_at=None,
            deleted_by=None,
        )
        assert user.edit_schema is not None
        assert len(user.edit_schema.model_fields) == 6
        assert "email" in user.edit_schema.model_fields.keys()
        assert "handle" in user.edit_schema.model_fields.keys()
        assert "full_name" in user.edit_schema.model_fields.keys()
        assert "tenant_id" in user.edit_schema.model_fields.keys()
        assert "default_group_id" in user.edit_schema.model_fields.keys()
        assert "is_superuser" in user.edit_schema.model_fields.keys()
