# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import inspect, Integer
from sqlalchemy.dialects.postgresql import TEXT, VARCHAR

# from uno.obj.tables import ObjectType

# from uno.obj.sql_emitters import InsertObjectTypeRecordSQL

from tests.conftest import (
    print_indices,
    print_pk_constraint,
    print_foreign_keys,
    print_uq_constraints,
    print_ck_constraints,
    db_column,
)

'''
class TestObjectType:
    schema = "uno"

    def test_object_type_model_structure(self):
        """
        Test the structure of the ObjectType Model.
        The constraints, index_definitions, and field_definitions are tested in other methods.
        """
        assert ObjectType.__name__ == "ObjectType"
        assert ObjectType.__module__ == "uno.obj.models"
        assert ObjectType.schema_name == "uno"
        assert ObjectType.table_name == "object_type"
        assert ObjectType.table_name_plural == "object_types"
        assert ObjectType.display_name == "Table Type"
        assert ObjectType.display_name_plural == "Table Types"
        assert list(ObjectType.field_definitions.keys()) == ["id", "db_schema", "name"]
        # assert ObjectType.constraint_definitions == [
        #    UniqueDefinition(
        #        columns=["db_schema", "name"], name="uq_ObjectType_db_schema_name"
        #    )
        # ]
        assert ObjectType.index_definitions == []
        assert InsertTableOperation in ObjectType.sql_emitters

        object_type = ObjectType(db_schema="uno", name="table_test")
        assert str(object_type) == "uno.table_test"

    def test_object_type_indices(self, db_connection):
        """Test the index_definitions on the object_type table in the database."""
        db_inspector = inspect(db_connection)
        # print_indices(db_inspector, "object_type", schema=self.schema)
        assert db_inspector.get_indexes("object_type", schema=self.schema) == [
            {
                "name": "ix_uno_object_type_db_schema",
                "unique": False,
                "column_names": ["db_schema"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_object_type_id",
                "unique": False,
                "column_names": ["id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_object_type_name",
                "unique": False,
                "column_names": ["name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "uq_ObjectType_db_schema_name",
                "unique": True,
                "column_names": ["db_schema", "name"],
                "duplicates_constraint": "uq_ObjectType_db_schema_name",
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_object_type_primary_key(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_pk_constraint(db_inspector, "object_type", schema=self.schema)
        assert db_inspector.get_pk_constraint("object_type", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_object_type",
            "comment": None,
        }

    def test_object_type_foreign_keys(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_foreign_keys(db_inspector, "object_type", schema=self.schema)
        assert db_inspector.get_foreign_keys("object_type", schema=self.schema) == []

    def test_object_type_unique_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_uq_constraints(db_inspector, "object_type", schema=self.schema)
        assert db_inspector.get_unique_constraints(
            "object_type", schema=self.schema
        ) == [
            {
                "column_names": ["db_schema", "name"],
                "name": "uq_ObjectType_db_schema_name",
                "comment": None,
            }
        ]

    def test_object_type_check_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_ck_constraints(db_inspector, "object_type", schema=self.schema)
        assert (
            db_inspector.get_check_constraints("object_type", schema=self.schema) == []
        )

    def test_object_type_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "object_type", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), Integer)

    def test_object_type_db_schema_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "object_type", "db_schema", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), TEXT)

    def test_object_type_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "object_type", "name", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), TEXT)

'''
