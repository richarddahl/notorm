# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import inspect, Integer
from sqlalchemy.dialects.postgresql import TEXT, VARCHAR

# from uno.obj.tables import MetaType

# from uno.obj.sql_emitters import InsertMetaTypeRecordSQL

from tests.conftest import db_column

'''
class TestMetaType:
    schema = "uno"

    def test_metatype_model_structure(self):
        """
        Test the structure of the MetaType Model.
        The constraints, index_definitions, and field_definitions are tested in other methods.
        """
        assert MetaType.__name__ == MetaType
        assert MetaType.__module__ == f"{settings.DB_SCHEMA}.obj.models"
        assert MetaType.schema_name == "uno"
        assert MetaType.table_name == "meta_type"
        assert MetaType.table_name_plural == "metatypes"
        assert MetaType.display_name == "Table Type"
        assert MetaType.display_name == "Table Types"
        assert list(MetaType.field_definitions.keys()) == ["id", "db_schema", "name"]
        # assert MetaType.constraint_definitions == [
        #    UniqueDefinition(
        #        columns=["db_schema", "name"], name="uq_MetaType_db_schema_name"
        #    )
        # ]
        assert MetaType.index_definitions == []
        assert InsertTableOperation in MetaType.sql_emitters

        meta_type = MetaType(db_schema="uno", name="table_test")
        assert str(meta_type) == f"{settings.DB_SCHEMA}.table_test"

    def test_metatype_indices(self, db_connection):
        """Test the index_definitions on the meta_type table in the database."""
        db_inspector = inspect(db_connection)
        assert db_inspector.get_indexes("meta_type", schema=self.schema) == [
            {
                "name": "ix_uno_metatype_db_schema",
                "unique": False,
                "column_names": ["db_schema"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_metatype_name",
                "unique": False,
                "column_names": ["id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_metatype_name",
                "unique": False,
                "column_names": ["name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "uq_MetaType_db_schema_name",
                "unique": True,
                "column_names": ["db_schema", "name"],
                "duplicates_constraint": "uq_MetaType_db_schema_name",
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_metatype_primary_key(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_pk_constraint(db_inspector, "meta_type", schema=self.schema)
        assert db_inspector.get_pk_constraint("meta_type", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_metatype",
            "comment": None,
        }

    def test_metatype_foreign_keys(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_foreign_keys(db_inspector, "meta_type", schema=self.schema)
        assert db_inspector.get_foreign_keys("meta_type", schema=self.schema) == []

    def test_metatype_unique_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_uq_constraints(db_inspector, "meta_type", schema=self.schema)
        assert db_inspector.get_unique_constraints(
            "meta_type", schema=self.schema
        ) == [
            {
                "column_names": ["db_schema", "name"],
                "name": "uq_MetaType_db_schema_name",
                "comment": None,
            }
        ]

    def test_metatype_check_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_ck_constraints(db_inspector, "meta_type", schema=self.schema)
        assert (
            db_inspector.get_check_constraints("meta_type", schema=self.schema) == []
        )

    def test_metatype_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta_type", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), Integer)

    def test_metatype_db_schema_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta_type", "db_schema", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), TEXT)

    def test_metatype_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta_type", "name", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), TEXT)

'''
