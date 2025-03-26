# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
import json
import pytz

import asyncio
import pytest
import pytest_asyncio

from unittest import IsolatedAsyncioTestCase

from pydantic.fields import FieldInfo

from sqlalchemy import func, text, select, update, delete, ForeignKey
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.dialects.postgresql import BOOLEAN

# from fastapi.testclient import TestClient

from uno.config import settings
from uno.pkgs.auth.models import User

# from uno.rltd.models import TableType, RelatedObject
# from tests.pgjwt.test_pgjwt import encode_test_token
from uno.db.management.db_manager import DBManager

# from tests.conftest import mock_rls_vars


# client = TestClient(app)


@pytest.mark.asyncio
async def test_create_user(session, test_db):
    # Creates the superuser and returns it's id.
    db_manager = DBManager()
    new_superuser_id = await db_manager.create_superuser(
        email="new_admin@notorm.tech",
        handle="new_admin",
        full_name="New Admin",
    )
    assert new_superuser_id is not None


'''
class TestUser(IsolatedAsyncioTestCase):
    """Tests for the User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, session, test_db):
        # Creates the superuser and returns it's id.
        db_manager = DBManager()
        new_superuser_id = await db_manager.create_superuser(
            email="new_admin@notorm.tech",
            handle="new_admin",
            full_name="New Admin",
        )
        assert new_superuser_id is not None


        with session.begin():
            stmt = select(User.table).where(User.table.email == "new_admin@notorm.tech")
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="admin")
                )
            )
            superuser = session.scalar(stmt)

            assert superuser is not None
            assert superuser.email == "new_admin@notorm.tech"
            assert superuser.handle == "new_admin"
            assert superuser.full_name == "New Admin"
            assert superuser.is_superuser is True
            assert superuser.is_tenant_admin is False
            assert superuser.is_active is True
            assert superuser.is_deleted is False
            assert superuser.created_at is not None
            assert superuser.modified_at is not None
            assert superuser.deleted_at is None
            session.commit()

    def test_soft_delete_user(self, session, superuser_id):
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="admin")
                )
            )
            session.execute(
                delete(User.table).where(User.table.email == "new_admin@notorm.tech")
            )
            session.commit()

        # Test to see if the soft delete workked
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="reader")
                )
            )
            superuser = session.scalar(
                select(User.table).where(User.table.email == "new_admin@notorm.tech")
            )

            assert superuser is not None
            assert superuser.email == "new_admin@notorm.tech"
            assert superuser.handle == "new_admin"
            assert superuser.full_name == "New Admin"
            assert superuser.is_superuser is True
            assert superuser.is_tenant_admin is False
            assert superuser.is_active is False
            assert superuser.is_deleted is True
            assert superuser.created_at is not None
            assert superuser.modified_at is not None
            assert superuser.deleted_at is not None
            session.commit()

        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="admin")
                )
            )
            # Actually delete the soft deleted user
            session.execute(
                delete(User.table).where(User.table.email == "new_admin@notorm.tech")
            )
            session.commit()

        # Test to see if the actual delete worked
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="admin")
                )
            )
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 1

    ############################
    # Admin user related tests #
    ############################

    def test_admin_user(self, session, superuser_id):
        """Tests that the admin user, created in create_db.create_db was created correctly."""
        with session.begin():
            session.execute(func.uno.mock_authorize_user(*mock_rls_vars(superuser_id)))
            admin_user = session.scalar(
                select(User.table).where(User.table.email == settings.SUPERUSER_EMAIL)
            )
            assert admin_user is not None
            assert admin_user.email == settings.SUPERUSER_EMAIL
            assert admin_user.handle == settings.SUPERUSER_HANDLE
            assert admin_user.full_name == settings.SUPERUSER_FULL_NAME
            assert admin_user.is_superuser is True
            assert admin_user.is_tenant_admin is False
            assert admin_user.is_active is True
            assert admin_user.is_deleted is False
            assert admin_user.created_at is not None
            assert admin_user.modified_at is not None
            assert admin_user.deleted_at is None
            session.commit()

    ############################
    # Row Level Security Tests #
    ############################

    ##############
    # SELECT Tests
    # Superuser SELECT Test
    def test_rls_superuser_select(self, session, superuser_id, user_dict):
        """Tests that a superuser can select all users with each role except the login role."""
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="admin")
                )
            )
            # Test with admin role
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 20

            # Test with writer role
            session.execute(func.uno.mock_role("writer"))
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 20

            # Test with reader role
            session.execute(func.uno.mock_role("reader"))
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 20

            # Test with login role
            session.execute(func.uno.mock_role("login"))
            stmt = select(func.count()).select_from(User.table)
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(stmt)
            assert "permission denied" in str(excinfo.value)

    # Tenant Admin SELECT User Test
    def test_rls_tenant_admin_select(self, session, user_dict):
        """Tests that tenant users can only select users from their tenant."""
        acme_admin = user_dict.get("admin@acme.com")
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(
                        acme_admin.get("id"),
                        email=acme_admin.get("email"),
                        is_superuser="false",
                        is_tenant_admin="true",
                        tenant_id=acme_admin.get("tenant_id"),
                        role_name="admin",
                    )
                )
            )

            # Test with admin role
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 10

            # Test with writer role
            session.execute(func.uno.mock_role("writer"))
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 10

            # Test with reader role
            session.execute(func.uno.mock_role("reader"))
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 10

            # Test with login role
            session.execute(func.uno.mock_role("login"))
            stmt = select(func.count()).select_from(User.table)
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(stmt)
            assert "permission denied" in str(excinfo.value)

    # Non-Privileged User SELECT Test
    def test_rls_non_privileged_user_select(self, session, superuser_id, user_dict):
        """Tests that non-privileged users can only select users from their tenant."""
        acme_user = user_dict.get("admin@acme.com")
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(
                        acme_user.get("id"),
                        email=acme_user.get("email"),
                        is_superuser="false",
                        is_tenant_admin="false",
                        tenant_id=acme_user.get("tenant_id"),
                        role_name="admin",
                    )
                )
            )
            # Test with admin role
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 10

            # Test with writer role
            session.execute(func.uno.mock_role("writer"))
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 10

            # Test with reader role
            session.execute(func.uno.mock_role("reader"))
            stmt = select(func.count()).select_from(User.table)
            user_count = session.execute(stmt)
            assert user_count.scalar() == 10

            # Test with login role
            session.execute(func.uno.mock_role("login"))
            stmt = select(func.count()).select_from(User.table)
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(stmt)
            assert "permission denied" in str(excinfo.value)

    ############################
    # INSERT/UPDATE/DELETE Tests

    # Superuser INSERT, UPDATE, DELETE Test
    @pytest.mark.parametrize("role_name", ["admin", "writer"])
    def test_rls_superuser_can_insert_update_delete(
        self, session, superuser_id, new_user, role_name, tenant_dict
    ):
        """
        Tests that a user can be INSERTED, UPDATED, and DELETED
            by a superuser with the admin and writer roles.
        """

        with session.begin():
            # INSERT the user with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            session.add(new_user)

        with session.begin():
            # Verify the user was INSERTED with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            assert new_user.id is not None

            # UPDATE the user with the admin role
            stmt = select(User.table).where(User.table.email == new_user.email)
            new_user = session.scalar(stmt)
            new_user.full_name = "Updated User"

        with session.begin():
            # Verify the user was UPDATED with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            assert new_user.full_name == "Updated User"

            # UPDATE the user's TENANT with the admin role
            stmt = select(User.table).where(User.table.email == new_user.email)
            new_user = session.scalar(stmt)
            new_user.tenant_id = tenant_dict.get("Nacme Corp").get("id")

        with session.begin():
            # Verify the user's tenant ID was UPDATED with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            assert new_user.tenant_id == tenant_dict.get("Nacme Corp").get("id")

            # DELETE the user with the admin role (trigger sets is_deleted to True)
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            session.execute(
                (delete(User.table).where(User.table.email == new_user.email))
            )

        with session.begin():
            # Verify that new_user.is_deleted was set to True with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            stmt = select(User.table).where(User.table.email == new_user.email)
            new_user = session.scalar(stmt)
            assert new_user.is_deleted is True

            # Actually DELETE the user with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            session.execute(
                (delete(User.table).where(User.table.email == new_user.email))
            )

        with session.begin():
            # Verify the user was DELETED with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name=role_name)
                )
            )
            assert session.scalar(stmt) is None

    # Superuser cannot INSERT, UPDATE, DELETE Test with reader role
    def test_rls_superuser_cannot_insert_update_with_reader(
        self, session, superuser_id, new_user, user_dict
    ):
        """
        Tests that a user cannot be INSERTED, UPDATED, or DELETED
            by a superuser with the reader role.
        """
        with session.begin():
            # Try to INSERT the user with the admin role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="reader")
                )
            )
            session.add(new_user)
            with pytest.raises(ProgrammingError) as excinfo:
                session.commit()
            assert "permission denied" in str(excinfo.value)

        new_user_email = user_dict.get("user1@acme.com").get("email")
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="reader")
                )
            )

            # UPDATE a user with the reader role
            stmt = select(User.table).where(User.table.email == new_user_email)
            new_user = session.scalar(stmt)
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="reader")
                )
            )
            new_user.full_name = "Updated User"
            with pytest.raises(ProgrammingError) as excinfo:
                session.commit()
            assert "permission denied" in str(excinfo.value)

        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="reader")
                )
            )
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(
                    (delete(User.table).where(User.table.email == new_user_email))
                )
            assert "permission denied" in str(excinfo.value)

    # Superuser cannot INSERT, UPDATE, DELETE Test with login role
    def test_rls_superuser_cannot_insert_update_with_login(
        self, session, superuser_id, new_user, user_dict
    ):
        """
        Tests that a user cannot be INSERTED, UPDATED, or DELETED
            by a superuser with the login role.
        """
        with session.begin():
            # INSERT a user with the login role
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="login")
                )
            )
            session.add(new_user)
            with pytest.raises(ProgrammingError) as excinfo:
                session.commit()
            assert "permission denied" in str(excinfo.value)

        new_user_email = user_dict.get("user1@acme.com").get("email")
        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="login")
                )
            )

            # SELECT a user with the login role
            stmt = select(User.table).where(User.table.email == new_user_email)
            with pytest.raises(ProgrammingError) as excinfo:
                new_user = session.scalar(stmt)
            assert "permission denied" in str(excinfo.value)

        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="login")
                )
            )
            new_user.full_name = "Updated User"
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(
                    update(User.table)
                    .where(User.table.email == new_user_email)
                    .values(full_name="Updated User")
                )
            assert "permission denied" in str(excinfo.value)

        with session.begin():
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(superuser_id, role_name="login")
                )
            )
            session.execute(func.uno.mock_role("login"))
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(
                    (delete(User.table).where(User.table.email == new_user_email))
                )
            assert "permission denied" in str(excinfo.value)

    def test_rls_tenant_admin_create_update_delete_tenant_user(
        self,
        session,
        acme_tenant,
        acme_group,
        nacme_tenant,
        acme_admin_vars,
    ):
        """Tests that a tenant user can be inserted, updated, and deleted by a tenant admin.

        Also tests that the tenant user's tenant_id CANNOT be changed by a tenant admin.

        """
        acme_user = User.table(
            email="user@acme.com",
            handle="acme user",
            full_name="ACME User",
            tenant_id=acme_tenant.get("id"),
            default_group_id=acme_group.get("id"),
        )
        with session.begin():
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            # Create the user
            session.add(acme_user)
            session.commit()

        with session.begin():
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            acme_user.full_name = "Updated ACME User"
            # Verify the user was updated
            assert acme_user.full_name == "Updated ACME User"
            session.add(acme_user)
            session.commit()

        with session.begin():
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            # Try to UPDATE the user's TENANT
            acme_user.tenant_id = nacme_tenant.get("id")
            session.add(acme_user)
            # Verify the user's tenant ID was not updated and a RLS error was raised
            with pytest.raises(ProgrammingError) as excinfo:
                session.commit()
            assert "new row violates row-level security policy" in str(excinfo.value)

        with session.begin():
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            # DELETE the user (trigger sets is_deleted to True)
            session.execute(
                (delete(User.table).where(User.table.email == acme_user.email))
            )

        with session.begin():
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            # Verify that new_user.is_deleted was set to True
            stmt = select(User.table).where(User.table.email == acme_user.email)
            user = session.scalar(stmt)
            assert user.is_deleted is True

            # Actually DELETE the user with the admin role
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            session.execute((delete(User.table).where(User.table.email == user.email)))

        with session.begin():
            # Verify the user was DELETED
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            assert session.scalar(stmt) is None

    def test_rls_tenant_admin_create_non_tenant_user(
        self,
        session,
        acme_group,
        nacme_tenant,
        acme_admin_vars,
    ):
        """Tests that a tenant admin cannot create a user with a different tenant_id."""
        with session.begin():
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            acme_user = User.table(
                email="not_acme@acme.com",
                handle="not_acme user",
                full_name="Not ACME User",
                tenant_id=nacme_tenant.get("id"),
                default_group_id=acme_group.get("id"),
            )
            session.add(acme_user)
            with pytest.raises(ProgrammingError) as excinfo:
                session.commit()
            assert "new row violates row-level security policy" in str(excinfo.value)

    def test_rls_tenant_admin_delete_non_tenant_user(
        self,
        session,
        acme_admin_vars,
        superuser_id,
    ):
        """Tests that a tenant admin cannot delete a user with a different tenant_id."""
        with session.begin():
            session.execute(func.uno.mock_authorize_user(*acme_admin_vars))
            # The RLS prevents the select from returning the user, so we can't delete it but get no error
            session.execute(
                delete(User.table).where(User.table.email == "admin@nacme.com")
            )
            session.commit()

        with session.begin():
            session.execute(func.uno.mock_authorize_user(*mock_rls_vars(superuser_id)))
            stmt = select(User.table).where(User.table.email == "admin@nacme.com")
            user_not_deleted = session.scalar(stmt)
            assert user_not_deleted is not None

    def test_rls_regular_user_cannot_create_a_user(
        self, session, superuser_id, data_dict
    ):
        """Tests that a regular user cannot create a user."""
        with session.begin():
            acme_user = data_dict.get("users").get("user1@acme.com")
            acme = data_dict.get("tenants").get("Acme Inc.")
            session.execute(
                func.uno.mock_authorize_user(
                    *mock_rls_vars(
                        acme_user.get("email"),
                    )
                )
            )
            unauthorized_acme_user = User.table(
                email="unauthorized@acme.com",
                handle="unauthorized acme user",
                full_name="Unauthorized ACME User",
                tenant_id=acme.get("id"),
            )
            session.add(unauthorized_acme_user)
            with pytest.raises(ProgrammingError):
                session.commit()


    def test_user_obj_select_model_creation(self):
        """Tests the User model."""
        user_obj = UserObj(app=app)
        assert user_obj is not None
        select_model = user_obj.models.get("SelectUser")
        assert select_model is not None
        assert select_model.__annotations__ is not None
        assert select_model.__annotations__.get("id") == str
        assert select_model.__annotations__.get("email") == str
        assert select_model.__annotations__.get("handle") == str
        assert select_model.__annotations__.get("full_name") == str
        assert select_model.__annotations__.get("tenant_id") == str | None
        assert select_model.__annotations__.get("default_group_id") == str | None
        assert select_model.__annotations__.get("is_superuser") == bool
        assert select_model.__annotations__.get("is_tenant_admin") == bool
        assert select_model.__annotations__.get("is_active") == bool
        assert select_model.__annotations__.get("is_deleted") == bool
        assert select_model.__annotations__.get("created_at") == datetime.datetime
        assert select_model.__annotations__.get("owned_by_id") == str | None
        assert select_model.__annotations__.get("modified_at") == datetime.datetime
        assert select_model.__annotations__.get("modified_by_id") == str | None
        assert (
            select_model.__annotations__.get("deleted_at") == datetime.datetime | None
        )
        assert select_model.__annotations__.get("deleted_by_id") == str | None

    def test_user_obj_insert_model_creation(self):
        user_obj = UserObj(app=app)
        assert user_obj is not None
        insert_model = user_obj.models.get("InsertUser")
        assert insert_model is not None
        assert insert_model.__annotations__ is not None
        assert insert_model.__annotations__.get("id") is None
        assert insert_model.__annotations__.get("email") == str
        assert insert_model.__annotations__.get("handle") == str
        assert insert_model.__annotations__.get("full_name") == str
        assert insert_model.__annotations__.get("tenant_id") == str | None
        assert insert_model.__annotations__.get("default_group_id") == str | None
        assert insert_model.__annotations__.get("is_superuser") == bool
        assert insert_model.__annotations__.get("is_tenant_admin") == bool
        assert insert_model.__annotations__.get("is_active") is None
        assert insert_model.__annotations__.get("is_deleted") is None
        assert insert_model.__annotations__.get("created_at") is None
        assert insert_model.__annotations__.get("owned_by_id") is None
        assert insert_model.__annotations__.get("modified_at") is None
        assert insert_model.__annotations__.get("modified_by_id") is None
        assert insert_model.__annotations__.get("deleted_at") is None
        assert insert_model.__annotations__.get("deleted_by_id") is None

    def test_user_obj_update_model_creation(self):
        user_obj = UserObj(app=app)
        assert user_obj is not None
        update_model = user_obj.models.get("UpdateUser")
        assert update_model is not None
        assert update_model.__annotations__ is not None
        assert update_model.__annotations__.get("id") == str
        assert update_model.__annotations__.get("email") == str
        assert update_model.__annotations__.get("handle") == str
        assert update_model.__annotations__.get("full_name") == str
        assert update_model.__annotations__.get("tenant_id") == str | None
        assert update_model.__annotations__.get("default_group_id") == str | None
        assert update_model.__annotations__.get("is_superuser") == bool
        assert update_model.__annotations__.get("is_tenant_admin") == bool
        assert update_model.__annotations__.get("is_active") == bool
        assert update_model.__annotations__.get("is_deleted") == bool
        assert update_model.__annotations__.get("created_at") is None
        assert update_model.__annotations__.get("owned_by_id") == str | None
        assert update_model.__annotations__.get("modified_at") is None
        assert update_model.__annotations__.get("modified_by_id") is None
        assert update_model.__annotations__.get("deleted_at") is None
        assert update_model.__annotations__.get("deleted_by_id") is None

    def test_user_obj_list_model_creation(self):
        user_obj = UserObj(app=app)
        assert user_obj is not None
        list_model = user_obj.models.get("ListUser")
        assert list_model is not None
        assert list_model.__annotations__ is not None
        assert list_model.__annotations__.get("id") == str
        assert list_model.__annotations__.get("email") == str
        assert list_model.__annotations__.get("handle") == str
        assert list_model.__annotations__.get("full_name") == str
        assert list_model.__annotations__.get("tenant_id") is None
        assert list_model.__annotations__.get("default_group_id") is None
        assert list_model.__annotations__.get("is_superuser") is None
        assert list_model.__annotations__.get("is_tenant_admin") is None
        assert list_model.__annotations__.get("is_active") is None
        assert list_model.__annotations__.get("is_deleted") is None
        assert list_model.__annotations__.get("created_at") is None
        assert list_model.__annotations__.get("owned_by_id") is None
        assert list_model.__annotations__.get("modified_at") is None
        assert list_model.__annotations__.get("modified_by_id") is None
        assert list_model.__annotations__.get("deleted_at") is None
        assert list_model.__annotations__.get("deleted_by_id") is None

    def test_user_model_instantiation(self, session, superuser_id):
        """Tests that the admin user, created in create_db.create_db was created correctly."""
        session.execute(func.uno.mock_authorize_user(*mock_rls_vars(superuser_id)))
        admin_user = session.scalar(
            select(User).where(User.email == settings.SUPERUSER_EMAIL)
        ).__dict__
        user_obj = UserObj(app=app)
        assert user_obj is not None

        select_model = user_obj.models.get("SelectUser")(**admin_user)
        assert select_model is not None

        insert_model = user_obj.models.get("InsertUser")(**admin_user)
        assert insert_model is not None

        update_model = user_obj.models.get("UpdateUser")(**admin_user)
        assert update_model is not None

        list_model = user_obj.models.get("ListUser")(**admin_user)
        assert list_model is not None

    def test_user_get_route(self, create_test_functions):
        token = encode_test_token()
        response = client.get("/api/auth/users", headers={"Authorization": token})
        assert response.status_code == 200
        assert response.json() is not None

    def test_user_get_by_id_route(self, superuser_id, create_test_functions):
        """Test that the /api/users/{id} endpoint returns a UserObj SelectUser model."""
        token = encode_test_token()
        response = client.get(
            f"/api/auth/users/{superuser_id}", headers={"Authorization": token}
        )
        assert response.status_code == 200

        # Validate the response structure against the SelectUser model
        user_obj = UserObj(app=app)
        select_user_model = user_obj.models.get("SelectUser")
        assert select_user_model is not None
        user = select_user_model(**response.json())

        # Check if the response data matches the SelectUser model's annotations
        for field, field_type in select_user_model.__annotations__.items():
            assert isinstance(getattr(user, field), field_type)

    def test_user_get_by_id_route_with_incorrect_id(self, create_test_functions):
        token = encode_test_token()
        response = client.get(
            "/api/auth/users/0123456789ABCDEFGHIJKLMNOP",
            headers={"Authorization": token},
        )
        assert response.status_code == 404


"""
# Define a router that returns a select_user_model
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/api/users/{user_id}", response_model=UserObj.models["SelectUser"])
async def get_user(user_id: str):
    # Simulate fetching a user from the database
    user_obj = UserObj(app=app)
    select_user_model = user_obj.models.get("SelectUser")
    if not select_user_model:
        raise HTTPException(status_code=404, detail="User not found")

    # Example user data
    user_data = {
        "id": user_id,
        "email": "example@example.com",
        "handle": "example_handle",
        "full_name": "Example User",
        "tenant_id": None,
        "default_group_id": None,
        "is_superuser": False,
        "is_tenant_admin": False,
        "is_active": True,
        "is_deleted": False,
        "created_at": datetime.datetime.now(),
        "owned_by_id": None,
        "modified_at": datetime.datetime.now(),
        "modified_by_id": None,
        "deleted_at": None,
        "deleted_by_id": None,
    }

    return select_user_model(**user_data)

"""
'''
