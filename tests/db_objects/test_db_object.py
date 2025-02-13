# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import VARCHAR, BIGINT

from uno.obj.tables import DBObject

from uno.db.sql_emitters import AlterGrantSQL

from tests.conftest import (
    print_indices,
    print_pk_constraint,
    print_foreign_keys,
    print_uq_constraints,
    print_ck_constraints,
    db_column,
)


class TestDBObject:
    schema = "uno"

    def test_db_object_structure(self):
        assert DBObject.display_name == "DB Object"
        assert DBObject.display_name_plural == "DB Objects"
        assert AlterGrantSQL in DBObject.sql_emitters
        # assert InsertObjectTypeRecordSQL in DBObject.sql_emitters
        assert DBObject.__name__ == "DBObject"
        assert DBObject.__module__ == "uno.obj.tables"
        assert DBObject.__table_args__.get("schema") == "uno"
        assert DBObject.__tablename__ == "db_object"
        assert list(DBObject.__table__.columns.keys()) == [
            "id",
            "object_type_id",
        ]

    def test_db_object_indices(self, db_connection):
        """Test the index_definitions on the db_object table in the database."""
        db_inspector = inspect(db_connection)
        # print_indices(db_inspector, "db_object", schema=self.schema)
        assert db_inspector.get_indexes("db_object", schema=self.schema) == [
            {
                "name": "ix_uno_db_object_id",
                "unique": False,
                "column_names": ["id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_db_object_object_type_id",
                "unique": False,
                "column_names": ["object_type_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_db_object_primary_key(self, db_connection):
        """Test the primary key constraint on the db_object table in the database."""
        db_inspector = inspect(db_connection)
        # print_pk_constraint(db_inspector, "db_object", schema=self.schema)
        assert db_inspector.get_pk_constraint("db_object", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_db_object",
            "comment": None,
        }

    def test_db_object_foreign_keys(self, db_connection):
        """Test the foreign keys on the db_object table in the database."""
        db_inspector = inspect(db_connection)
        # print_foreign_keys(db_inspector, "db_object", schema=self.schema)
        assert db_inspector.get_foreign_keys("db_object", schema=self.schema) == [
            {
                "name": "fk_db_object_object_type_id",
                "constrained_columns": ["object_type_id"],
                "referred_schema": "uno",
                "referred_table": "object_type",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

    def test_db_object_unique_constraints(self, db_connection):
        """Test the unique constraints on the db_object table in the database."""
        db_inspector = inspect(db_connection)
        # print_uq_constraints(db_inspector, "db_object", schema=self.schema)
        assert (
            db_inspector.get_unique_constraints("db_object", schema=self.schema) == []
        )

    def test_db_object_check_constraints(self, db_connection):
        """Test the check constraints on the db_object table in the database."""
        db_inspector = inspect(db_connection)
        # print_ck_constraints(db_inspector, "db_object", schema=self.schema)
        assert db_inspector.get_check_constraints("db_object", schema=self.schema) == []

    def test_db_object_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "db_object", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_db_object_object_type_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(
            db_inspector, "db_object", "object_type_id", schema=self.schema
        )
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), BIGINT)
