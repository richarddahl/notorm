# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import VARCHAR

from tests.conftest import db_column

from uno.db.tables import MetaRecord, User
from uno.db.sql_emitters import AlterGrantSQL, InsertMetaTypeRecordSQL
from uno.config import settings


class TestUser:
    schema = settings.DB_SCHEMA

    def test_user_structure(self):
        assert User.display_name == "User"
        assert User.display_name_plural == "Users"
        assert User.__name__ == "User"
        assert User.__module__ == f"{settings.DB_SCHEMA}.auth.tables"
        assert User.__table_args__[1].get("schema") == "uno"
        assert User.__tablename__ == "user"
        assert list(User.__table__.columns.keys()) == [
            "id",
            "email",
            "handle",
            "full_name",
            "tenant_id",
            "default_group_id",
            "is_superuser",
            "created_by_id",
            "modified_by_id",
            "deleted_by_id",
        ]

    def test_user_indices(self, db_connection):
        """Test the index_definitions on the user table in the database."""
        db_inspector = inspect(db_connection)
        assert db_inspector.get_indexes("user", schema=self.schema) == [
            {
                "name": "ix_uno_user_email",
                "unique": False,
                "column_names": ["email"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_handle",
                "unique": False,
                "column_names": ["handle"],
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
            {
                "name": "ix_uno_user_default_group_id",
                "unique": False,
                "column_names": ["default_group_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_user_primary_key(self, db_connection):
        """Test the primary key constraint on the user table in the database."""
        db_inspector = inspect(db_connection)
        assert db_inspector.get_pk_constraint("user", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_user",
            "comment": None,
        }

    def test_user_foreign_keys(self, db_connection):
        """Test the foreign keys on the user table in the database."""
        db_inspector = inspect(db_connection)
        assert db_inspector.get_foreign_keys("user", schema=self.schema) == [
            {
                "name": "fk_user_tenant_id",
                "constrained_columns": ["tenant_id"],
                "referred_schema": "uno",
                "referred_table": "tenant",
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
                "name": "fk_user_created_by_id",
                "constrained_columns": ["created_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
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
                "name": "fk_user_deleted_by_id",
                "constrained_columns": ["deleted_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

    def test_user_unique_constraints(self, db_connection):
        """Test the unique constraints on the user table in the database."""
        db_inspector = inspect(db_connection)
        assert db_inspector.get_unique_constraints("user", schema=self.schema) == [
            {
                "name": "uq_user_email",
                "column_names": ["email"],
                "duplicates_index": "ix_uno_user_email",
            },
            {
                "name": "uq_user_handle",
                "column_names": ["handle"],
                "duplicates_index": "ix_uno_user_handle",
            },
        ]

    def test_user_check_constraints(self, db_connection):
        """Test the check constraints on the user table in the database."""
        db_inspector = inspect(db_connection)
        assert db_inspector.get_check_constraints("user", schema=self.schema) == [
            {
                "name": "ck_user_is_superuser",
                "sqltext": "(is_superuser = 'false' AND default_group_id IS NOT NULL) OR (is_superuser = 'true' AND default_group_id IS NULL)",
            },
        ]
    schema = settings.DB_SCHEMA

    def test_meta_structure(self):
        assert MetaRecord.display_name == "Meta Record"
        assert MetaRecord.display_name_plural == "Meta Records"
        assert AlterGrantSQL in MetaRecord.sql_emitters
        assert InsertMetaTypeRecordSQL in MetaRecord.sql_emitters
        assert MetaRecord.__name__ == "MetaRecord"
        assert MetaRecord.__module__ == f"{settings.DB_SCHEMA}.db.tables"
        assert MetaRecord.__table_args__.get("schema") == "uno"
        assert MetaRecord.__tablename__ == "meta"
        # print(list(MetaRecord.__table__.columns.keys()))
        assert list(MetaRecord.__table__.columns.keys()) == [
            "id",
            "meta_type_name",
        ]

    def test_meta_indices(self, db_connection):
        """Test the index_definitions on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_indexes("meta", schema=self.schema))
        assert db_inspector.get_indexes("meta", schema=self.schema) == [
            {
                "name": "ix_uno_meta_meta_type_name",
                "unique": False,
                "column_names": ["meta_type_name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_meta_primary_key(self, db_connection):
        """Test the primary key constraint on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_pk_constraint("meta", schema=self.schema))
        assert db_inspector.get_pk_constraint("meta", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_meta",
            "comment": None,
        }

    def test_meta_foreign_keys(self, db_connection):
        """Test the foreign keys on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_foreign_keys("meta", schema=self.schema))
        assert db_inspector.get_foreign_keys("meta", schema=self.schema) == [
            {
                "name": "fk_meta_meta_type_name",
                "constrained_columns": ["meta_type_name"],
                "referred_schema": "uno",
                "referred_table": "meta_type",
                "referred_columns": ["name"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

    def test_meta_unique_constraints(self, db_connection):
        """Test the unique constraints on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_unique_constraints("meta", schema=self.schema))
        assert db_inspector.get_unique_constraints("meta", schema=self.schema) == []

    def test_meta_check_constraints(self, db_connection):
        """Test the check constraints on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_check_constraints("meta", schema=self.schema))
        assert db_inspector.get_check_constraints("meta", schema=self.schema) == []

    def test_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_meta_type_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta", "meta_type_name", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
