# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import importlib

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import VARCHAR

# from tests.conftest import db_column

from uno.meta.objs import MetaRecord
from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaTypeRecord
from uno.config import settings


for module in settings.LOAD_MODULES:
    globals()[f"{module.split('.')[1]}_objs"] = importlib.import_module(
        f"{module}.objs"
    )


class TestMetaRecord:
    schema = settings.DB_SCHEMA

    def test_db_creation(self):
        from uno.db.management.db_manager import DBManager

        db_manager = DBManager()
        db_manager.create_db()
        db_manager.create_superuser()


'''
    def test_meta_structure(self):
        assert MetaRecord.display_name == "Meta Record"
        assert MetaRecord.display_name_plural == "Meta Records"
        assert AlterGrants in MetaRecord.sql_emitters
        assert InsertMetaTypeRecord in MetaRecord.sql_emitters
        assert MetaRecord.__name__ == "MetaRecord"
        assert MetaRecord.__module__ == f"{settings.DB_SCHEMA}.db.tables"
        assert MetaRecord.__table_args__.get("schema") == "uno"
        assert MetaRecord.__tablename__ == "meta_record"
        # print(list(MetaRecord.table.columns.keys()))
        assert list(MetaRecord.table.columns.keys()) == [
            "id",
            "meta_type_id",
        ]

    def test_meta_indices(self, db_connection):
        """Test the index_definitions on the meta_record table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_indexes("meta_record", schema=self.schema))
        assert db_inspector.get_indexes("meta_record", schema=self.schema) == [
            {
                "name": "ix_uno_meta_record_meta_type_id",
                "unique": False,
                "column_names": ["meta_type_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

    def test_meta_primary_key(self, db_connection):
        """Test the primary key constraint on the meta_record table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_pk_constraint("meta_record", schema=self.schema))
        assert db_inspector.get_pk_constraint("meta_record", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_meta_record",
            "comment": None,
        }

    def test_meta_foreign_keys(self, db_connection):
        """Test the foreign keys on the meta_record table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_foreign_keys("meta_record", schema=self.schema))
        assert db_inspector.get_foreign_keys("meta_record", schema=self.schema) == [
            {
                "name": "fk_meta_record_meta_type_id",
                "constrained_columns": ["meta_type_id"],
                "referred_schema": "uno",
                "referred_table": "meta_type",
                "referred_columns": ["name"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

    def test_meta_unique_constraints(self, db_connection):
        """Test the unique constraints on the meta_record table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_unique_constraints("meta_record", schema=self.schema))
        assert (
            db_inspector.get_unique_constraints("meta_record", schema=self.schema) == []
        )

    def test_meta_check_constraints(self, db_connection):
        """Test the check constraints on the meta_record table in the database."""
        db_inspector = inspect(db_connection)
        # print(db_inspector.get_check_constraints("meta_record", schema=self.schema))
        assert (
            db_inspector.get_check_constraints("meta_record", schema=self.schema) == []
        )

    def test_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "meta_record", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_meta_type_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(
            db_inspector, "meta_record", "meta_type_id", schema=self.schema
        )
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)

'''
