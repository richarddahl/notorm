# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
'''
from sqlalchemy import inspect, Integer
from sqlalchemy.dialects.postgresql import TEXT, VARCHAR

from tests.conftest import db_column

from uno.db.tables import MetaType
from uno.db.sql.table_sql_emitters import AlterGrants
from uno.config import settings


class TestMetaType:
    schema = settings.DB_SCHEMA

    def test_meta_type_structure(self):
        assert MetaType.display_name == "Meta Type"
        assert MetaType.display_name_plural == "Meta Types"
        assert AlterGrants in MetaType.sql_emitters
        assert MetaType.__name__ == "MetaType"
        assert MetaType.__module__ == f"{settings.DB_SCHEMA}.db.tables"
        assert MetaType.__table_args__.get("schema") == "uno"
        assert MetaType.__tablename__ == "meta_type"
        # print(list(MetaRecord.__table__.columns.keys()))
        assert list(MetaType.__table__.columns.keys()) == ["name"]

    def test_meta_type_indices(self, db_connection):
        """Test the index_definitions on the meta_type table in the database."""
        db_inspector = inspect(db_connection)
        assert db_inspector.get_indexes("meta_type", schema=self.schema) == [
            {
                "name": "ix_uno_meta_type_id",
                "unique": True,
                "column_names": ["name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_meta_type_primary_key(self, db_connection):
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_pk_constraint("meta_type", schema=self.schema))
        assert db_inspector.get_pk_constraint("meta_type", schema=self.schema) == {
            "constrained_columns": ["name"],
            "name": "pk_meta_type",
            "comment": None,
        }

    def test_meta_type_foreign_keys(self, db_connection):
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_foreign_keys("meta_type", schema=self.schema))
        assert db_inspector.get_foreign_keys("meta_type", schema=self.schema) == []

    def test_meta_type_unique_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_unique_constraints("meta_type", schema=self.schema))
        assert (
            db_inspector.get_unique_constraints("meta_type", schema=self.schema) == []
        )

    def test_meta_type_check_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_check_constraints("meta_type", schema=self.schema))
        assert db_inspector.get_check_constraints("meta_type", schema=self.schema) == []

    def test_meta_type_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta_type", "name", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)

'''
