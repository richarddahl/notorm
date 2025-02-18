# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import VARCHAR, BIGINT

from uno.db.tables import RelatedObject

from uno.db.sql_emitters import AlterGrantSQL

from tests.conftest import (
    print_indices,
    print_pk_constraint,
    print_foreign_keys,
    print_uq_constraints,
    print_ck_constraints,
    db_column,
)

from uno.config import settings


class TestRelatedObject:
    schema = "uno"

    def test_relatedobject_structure(self):
        assert RelatedObject.display_name == "Related Object"
        assert RelatedObject.display_name_plural == "Related Objects"
        assert AlterGrantSQL in RelatedObject.sql_emitters
        # assert InsertObjectTypeRecordSQL in RelatedObject.sql_emitters
        assert RelatedObject.__name__ == "RelatedObject"
        assert RelatedObject.__module__ == f"{settings.DB_SCHEMA}.db.tables"
        assert RelatedObject.__table_args__.get("schema") == "uno"
        assert RelatedObject.__tablename__ == "relatedobject"
        assert list(RelatedObject.__table__.columns.keys()) == [
            "id",
            "objecttype_name",
        ]

    def test_relatedobject_indices(self, db_connection):
        """Test the index_definitions on the relatedobject table in the database."""
        db_inspector = inspect(db_connection)
        print_indices(db_inspector, "relatedobject", schema=self.schema)
        assert db_inspector.get_indexes("relatedobject", schema=self.schema) == [
            {
                "name": "ix_uno_relatedobject_id",
                "unique": False,
                "column_names": ["id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_relatedobject_objecttype_name",
                "unique": False,
                "column_names": ["objecttype_name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_relatedobject_primary_key(self, db_connection):
        """Test the primary key constraint on the relatedobject table in the database."""
        db_inspector = inspect(db_connection)
        # print_pk_constraint(db_inspector, "relatedobject", schema=self.schema)
        assert db_inspector.get_pk_constraint("relatedobject", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_relatedobject",
            "comment": None,
        }

    def test_relatedobject_foreign_keys(self, db_connection):
        """Test the foreign keys on the relatedobject table in the database."""
        db_inspector = inspect(db_connection)
        # print_foreign_keys(db_inspector, "relatedobject", schema=self.schema)
        assert db_inspector.get_foreign_keys("relatedobject", schema=self.schema) == [
            {
                "name": "fk_relatedobject_objecttype_name",
                "constrained_columns": ["objecttype_name"],
                "referred_schema": "uno",
                "referred_table": "objecttype",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

    def test_relatedobject_unique_constraints(self, db_connection):
        """Test the unique constraints on the relatedobject table in the database."""
        db_inspector = inspect(db_connection)
        # print_uq_constraints(db_inspector, "relatedobject", schema=self.schema)
        assert (
            db_inspector.get_unique_constraints("relatedobject", schema=self.schema)
            == []
        )

    def test_relatedobject_check_constraints(self, db_connection):
        """Test the check constraints on the relatedobject table in the database."""
        db_inspector = inspect(db_connection)
        # print_ck_constraints(db_inspector, "relatedobject", schema=self.schema)
        assert (
            db_inspector.get_check_constraints("relatedobject", schema=self.schema)
            == []
        )

    def test_relatedobject_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "relatedobject", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_relatedobject_objecttype_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(
            db_inspector, "relatedobject", "objecttype_name", schema=self.schema
        )
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), BIGINT)
