# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import VARCHAR, BIGINT

from uno.db.tables import Meta
from uno.db.sql_emitters import AlterGrantSQL, InsertMetaTypeRecordSQL

from tests.conftest import db_column

from uno.config import settings


class TestRelatedObject:
    schema = "uno"

    def test_relatedobject_structure(self):
        assert Meta.display_name == "Meta Object"
        assert Meta.display_name_plural == "Meta Objects"
        assert AlterGrantSQL in Meta.sql_emitters
        assert InsertMetaTypeRecordSQL in Meta.sql_emitters
        assert Meta.__name__ == "Meta"
        assert Meta.__module__ == f"{settings.DB_SCHEMA}.db.tables"
        assert Meta.__table_args__.get("schema") == "uno"
        assert Meta.__tablename__ == "meta"
        # print(list(Meta.__table__.columns.keys()))
        assert list(Meta.__table__.columns.keys()) == [
            "id",
            "metatype_name",
            "is_active",
            "is_deleted",
            "created_at",
            "created_by_id",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ]

    def test_relatedobject_indices(self, db_connection):
        """Test the index_definitions on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_indexes("meta", schema=self.schema))
        assert db_inspector.get_indexes("meta", schema=self.schema) == [
            {
                "name": "ix_uno_meta_created_by_id",
                "unique": False,
                "column_names": ["created_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_meta_deleted_by_id",
                "unique": False,
                "column_names": ["deleted_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_meta_metatype_name",
                "unique": False,
                "column_names": ["metatype_name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_meta_modified_by_id",
                "unique": False,
                "column_names": ["modified_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_relatedobject_primary_key(self, db_connection):
        """Test the primary key constraint on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_pk_constraint("meta", schema=self.schema))
        assert db_inspector.get_pk_constraint("meta", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_meta",
            "comment": None,
        }

    def test_relatedobject_foreign_keys(self, db_connection):
        """Test the foreign keys on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_foreign_keys("meta", schema=self.schema))
        assert db_inspector.get_foreign_keys("meta", schema=self.schema) == [
            {
                "name": "fk_meta_created_by_id",
                "constrained_columns": ["created_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_meta_deleted_by_id",
                "constrained_columns": ["deleted_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_meta_metatype_name",
                "constrained_columns": ["metatype_name"],
                "referred_schema": "uno",
                "referred_table": "meta_type",
                "referred_columns": ["name"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_meta_modified_by_id",
                "constrained_columns": ["modified_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

    def test_relatedobject_unique_constraints(self, db_connection):
        """Test the unique constraints on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_unique_constraints("meta", schema=self.schema))
        assert db_inspector.get_unique_constraints("meta", schema=self.schema) == []

    def test_relatedobject_check_constraints(self, db_connection):
        """Test the check constraints on the meta table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_check_constraints("meta", schema=self.schema))
        assert db_inspector.get_check_constraints("meta", schema=self.schema) == []

    def test_meta_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_relatedobject_metatype_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta", "metatype_name", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
