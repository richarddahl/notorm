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

    def test_objecttype_model_structure(self):
        """
        Test the structure of the ObjectType Model.
        The constraints, index_definitions, and field_definitions are tested in other methods.
        """
        assert ObjectType.__name__ == ObjectType
        assert ObjectType.__module__ == f"{settings.DB_SCHEMA}.obj.models"
        assert ObjectType.schema_name == "uno"
        assert ObjectType.table_name == "objecttype"
        assert ObjectType.table_name_plural == "objecttypes"
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

        objecttype = ObjectType(db_schema="uno", name="table_test")
        assert str(objecttype) == f"{settings.DB_SCHEMA}.table_test"

    def test_objecttype_indices(self, db_connection):
        """Test the index_definitions on the objecttype table in the database."""
        db_inspector = inspect(db_connection)
        # print_indices(db_inspector, "objecttype", schema=self.schema)
        assert db_inspector.get_indexes("objecttype", schema=self.schema) == [
            {
                "name": "ix_uno_objecttype_db_schema",
                "unique": False,
                "column_names": ["db_schema"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_objecttype_name",
                "unique": False,
                "column_names": ["id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_objecttype_name",
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

    def test_objecttype_primary_key(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_pk_constraint(db_inspector, "objecttype", schema=self.schema)
        assert db_inspector.get_pk_constraint("objecttype", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_objecttype",
            "comment": None,
        }

    def test_objecttype_foreign_keys(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_foreign_keys(db_inspector, "objecttype", schema=self.schema)
        assert db_inspector.get_foreign_keys("objecttype", schema=self.schema) == []

    def test_objecttype_unique_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_uq_constraints(db_inspector, "objecttype", schema=self.schema)
        assert db_inspector.get_unique_constraints(
            "objecttype", schema=self.schema
        ) == [
            {
                "column_names": ["db_schema", "name"],
                "name": "uq_ObjectType_db_schema_name",
                "comment": None,
            }
        ]

    def test_objecttype_check_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_ck_constraints(db_inspector, "objecttype", schema=self.schema)
        assert (
            db_inspector.get_check_constraints("objecttype", schema=self.schema) == []
        )

    def test_objecttype_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "objecttype", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), Integer)

    def test_objecttype_db_schema_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "objecttype", "db_schema", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), TEXT)

    def test_objecttype_name_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "objecttype", "name", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), TEXT)

'''
