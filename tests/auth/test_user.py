# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest
from unittest import IsolatedAsyncioTestCase


from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import VARCHAR

from uno.db.management.db_manager import DBManager
from uno.errors import HTTPException
from uno.auth.objs import User
from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaTypeRecord

from uno.config import settings


class TestUser(IsolatedAsyncioTestCase):

    async def test_db_creation(self):

        db_manager = DBManager()
        db_manager.create_db()
        super_user = await db_manager.create_superuser()
        assert super_user is not None
        assert isinstance(super_user, User)
        assert super_user.is_superuser is True
        assert super_user.is_active is True
        assert super_user.is_deleted is False
        assert super_user.email == settings.SUPERUSER_EMAIL
        assert super_user.handle == settings.SUPERUSER_HANDLE
        assert super_user.full_name == settings.SUPERUSER_FULL_NAME
        assert super_user.tenant_id == None
        assert super_user.default_group_id == None


'''
    async def test_user_select(self):
        result = await User.list()
        if result is None:
            raise HTTPException(status_code=404, detail="Object not found")
        assert result is not None


    def test_user_structure(self):
        assert User.display_name == "User"
        assert User.display_name_plural == "Users"
        assert User.__name__ == "User"
        assert User.__module__ == f"{settings.DB_SCHEMA}.auth.tables"
        assert User.__table_args__[1].get("schema") == "uno"
        assert User.__tablename__ == "user"
        # print(User.table.columns.keys())
        assert list(User.table.columns.keys()) == [
            "id",
            "email",
            "handle",
            "full_name",
            "tenant_id",
            "default_group_id",
            "is_superuser",
            "is_active",
            "is_deleted",
            "created_at",
            "modified_at",
            "deleted_at",
            "created_by_id",
            "modified_by_id",
            "deleted_by_id",
        ]

    def test_user_indices(self, db_connection):
        """Test the index_definitions on the user table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_indexes("user", schema=self.schema))
        assert db_inspector.get_indexes("user", schema=self.schema) == [
            {
                "name": "ix_uno_user_created_by_id",
                "unique": False,
                "column_names": ["created_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_default_group_id",
                "unique": False,
                "column_names": ["default_group_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_deleted_by_id",
                "unique": False,
                "column_names": ["deleted_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_email",
                "unique": True,
                "column_names": ["email"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_handle",
                "unique": True,
                "column_names": ["handle"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_is_superuser",
                "unique": False,
                "column_names": ["is_superuser"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_modified_by_id",
                "unique": False,
                "column_names": ["modified_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_tenant_id",
                "unique": False,
                "column_names": ["tenant_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_user_primary_key(self, db_connection):
        """Test the primary key constraint on the user table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_pk_constraint("user", schema=self.schema))
        assert db_inspector.get_pk_constraint("user", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_user",
            "comment": None,
        }

    def test_user_foreign_keys(self, db_connection):
        """Test the foreign keys on the user table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_foreign_keys("user", schema=self.schema))
        assert db_inspector.get_foreign_keys("user", schema=self.schema) == [
            {
                "name": "fk_user_created_by_id",
                "constrained_columns": ["created_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user_default_group_id",
                "constrained_columns": ["default_group_id"],
                "referred_schema": "uno",
                "referred_table": "group",
                "referred_columns": ["id"],
                "options": {"ondelete": "SET NULL"},
                "comment": None,
            },
            {
                "name": "fk_user_deleted_by_id",
                "constrained_columns": ["deleted_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user_id",
                "constrained_columns": ["id"],
                "referred_schema": "uno",
                "referred_table": "meta_record",
                "referred_columns": ["id"],
                "options": {},
                "comment": None,
            },
            {
                "name": "fk_user_modified_by_id",
                "constrained_columns": ["modified_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user_tenant_id",
                "constrained_columns": ["tenant_id"],
                "referred_schema": "uno",
                "referred_table": "tenant",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

    def test_user_unique_constraints(self, db_connection):
        """Test the unique constraints on the user table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_unique_constraints("user", schema=self.schema))
        assert db_inspector.get_unique_constraints("user", schema=self.schema) == []

    def test_user_check_constraints(self, db_connection):
        """Test the check constraints on the user table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_check_constraints("user", schema=self.schema))
        assert db_inspector.get_check_constraints("user", schema=self.schema) == [
            {
                "name": "ck_user_ck_user_is_superuser",
                "sqltext": "is_superuser = false AND default_group_id IS NOT NULL OR is_superuser = true AND default_group_id IS NULL",
                "comment": None,
            }
        ]

'''
