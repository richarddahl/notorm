# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest

from sqlalchemy import inspect, Inspector, text
from sqlalchemy.dialects.postgresql import (
    VARCHAR,
    ENUM,
    TEXT,
    BOOLEAN,
    TIMESTAMP,
    BIGINT,
    JSONB,
    ARRAY,
    TEXT,
)

from uno.enums import TenantType
from uno.config import settings  # type: ignore
from tests.conftest import db_column


class TestUserTable:

    def test_user_table(self, connection, test_db):
        db_inspector = inspect(connection)
        # print(db_inspector.get_columns("user", schema=settings.DB_SCHEMA))
        assert [
            "email",
            "handle",
            "full_name",
            "tenant_id",
            "default_group_id",
            "is_superuser",
            "id",
            "is_active",
            "is_deleted",
            "created_at",
            "modified_at",
            "deleted_at",
            "created_by_id",
            "modified_by_id",
            "deleted_by_id",
        ] == [
            c.get("name")
            for c in db_inspector.get_columns("user", schema=settings.DB_SCHEMA)
        ]

        # print(db_inspector.get_indexes("user", schema=settings.DB_SCHEMA))
        assert db_inspector.get_indexes("user", schema=settings.DB_SCHEMA) == [
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
                "name": "ix_uno_user_id",
                "unique": False,
                "column_names": ["id"],
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

        # print(db_inspector.get_pk_constraint("user", schema=settings.DB_SCHEMA))
        assert db_inspector.get_pk_constraint("user", schema=settings.DB_SCHEMA) == {
            "constrained_columns": ["id"],
            "name": "pk_user",
            "comment": None,
        }

        # print(db_inspector.get_foreign_keys("user", schema=settings.DB_SCHEMA))
        assert db_inspector.get_foreign_keys("user", schema=settings.DB_SCHEMA) == [
            {
                "name": "fk_user_created_by_id",
                "constrained_columns": ["created_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "RESTRICT"},
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
                "options": {"ondelete": "SET NULL"},
                "comment": None,
            },
            {
                "name": "fk_user_id",
                "constrained_columns": ["id"],
                "referred_schema": "uno",
                "referred_table": "meta",
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
                "options": {"ondelete": "RESTRICT"},
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

        # print(db_inspector.get_unique_constraints("user", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_unique_constraints("user", schema=settings.DB_SCHEMA) == []
        )

        # print(db_inspector.get_check_constraints("user", schema=settings.DB_SCHEMA))
        assert db_inspector.get_check_constraints(
            "user", schema=settings.DB_SCHEMA
        ) == [
            {
                "name": "ck_user_ck_user_is_superuser",
                "sqltext": "is_superuser = false AND default_group_id IS NOT NULL OR is_superuser = true AND default_group_id IS NULL",
                "comment": None,
            }
        ]

    def test_user_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "user",
            "id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_user_email(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "user",
            "email",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 255

    def test_user_handle(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "user",
            "handle",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 255

    def test_user_full_name(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "user",
            "full_name",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 255


class TestUserGroupTable:

    def test_user_group_table(self, connection, test_db):
        db_inspector = inspect(connection)
        # print(db_inspector.get_columns("user_group", schema=settings.DB_SCHEMA))
        assert [
            "user_id",
            "group_id",
        ] == [
            c.get("name")
            for c in db_inspector.get_columns("user__group", schema=settings.DB_SCHEMA)
        ]

        # print(db_inspector.get_pk_constraint("user__group", schema=settings.DB_SCHEMA))
        assert db_inspector.get_pk_constraint(
            "user__group", schema=settings.DB_SCHEMA
        ) == {
            "constrained_columns": ["user_id", "group_id"],
            "name": "pk_user__group",
            "comment": None,
        }

        assert db_inspector.get_foreign_keys(
            "user__group", schema=settings.DB_SCHEMA
        ) == [
            {
                "name": "fk_user__group_group_id",
                "constrained_columns": ["group_id"],
                "referred_schema": "uno",
                "referred_table": "group",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user__group_user_id",
                "constrained_columns": ["user_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

        # print(db_inspector.get_indexes("user__group", schema=settings.DB_SCHEMA))
        assert db_inspector.get_indexes("user__group", schema=settings.DB_SCHEMA) == [
            {
                "name": "ix_user_group_user_id_group_id",
                "unique": False,
                "column_names": ["user_id", "group_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            }
        ]

        # print(db_inspector.get_unique_constraints("user_group", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_unique_constraints(
                "user__group", schema=settings.DB_SCHEMA
            )
            == []
        )

        # print(db_inspector.get_check_constraints("user_group", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_check_constraints("user__group", schema=settings.DB_SCHEMA)
            == []
        )

    def test_user_group_user_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "user__group",
            "user_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_user_group_group_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "user__group",
            "group_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26


class TestUserRoleTable:

    def test_user_role_table(self, connection, test_db):
        db_inspector = inspect(connection)
        # print(db_inspector.get_columns("user_role", schema=settings.DB_SCHEMA))
        assert [
            "user_id",
            "role_id",
        ] == [
            c.get("name")
            for c in db_inspector.get_columns("user__role", schema=settings.DB_SCHEMA)
        ]

        # print(db_inspector.get_pk_constraint("user__role", schema=settings.DB_SCHEMA))
        assert db_inspector.get_pk_constraint(
            "user__role", schema=settings.DB_SCHEMA
        ) == {
            "constrained_columns": ["user_id", "role_id"],
            "name": "pk_user__role",
            "comment": None,
        }

        # print(db_inspector.get_foreign_keys("user__role", schema=settings.DB_SCHEMA))
        assert db_inspector.get_foreign_keys(
            "user__role", schema=settings.DB_SCHEMA
        ) == [
            {
                "name": "fk_user__role_role_id",
                "constrained_columns": ["role_id"],
                "referred_schema": "uno",
                "referred_table": "role",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user__role_user_id",
                "constrained_columns": ["user_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

        # print(db_inspector.get_indexes("user__role", schema=settings.DB_SCHEMA))
        assert db_inspector.get_indexes("user__role", schema=settings.DB_SCHEMA) == [
            {
                "name": "ix_user_role_user_id_role_id",
                "unique": False,
                "column_names": ["user_id", "role_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            }
        ]

        # print(db_inspector.get_unique_constraints("user_role", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_unique_constraints("user__role", schema=settings.DB_SCHEMA)
            == []
        )

        # print(db_inspector.get_check_constraints("user_role", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_check_constraints("user__role", schema=settings.DB_SCHEMA)
            == []
        )


class TestTenantTable:

    def test_tenant_table(self, connection, test_db):
        db_inspector = inspect(connection)
        # print(db_inspector.get_columns("tenant", schema=settings.DB_SCHEMA))
        assert [
            "name",
            "tenant_type",
            "id",
            "is_active",
            "is_deleted",
            "created_at",
            "modified_at",
            "deleted_at",
            "created_by_id",
            "modified_by_id",
            "deleted_by_id",
        ] == [
            c.get("name")
            for c in db_inspector.get_columns("tenant", schema=settings.DB_SCHEMA)
        ]

        # print(db_inspector.get_indexes("tenant", schema=settings.DB_SCHEMA))
        assert db_inspector.get_indexes("tenant", schema=settings.DB_SCHEMA) == [
            {
                "name": "ix_tenant_name",
                "unique": False,
                "column_names": ["name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_tenant_created_by_id",
                "unique": False,
                "column_names": ["created_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_tenant_deleted_by_id",
                "unique": False,
                "column_names": ["deleted_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_tenant_id",
                "unique": False,
                "column_names": ["id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_tenant_modified_by_id",
                "unique": False,
                "column_names": ["modified_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_tenant_name",
                "unique": False,
                "column_names": ["name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "uq_tenant_name",
                "unique": True,
                "column_names": ["name"],
                "duplicates_constraint": "uq_tenant_name",
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

        # print(db_inspector.get_pk_constraint("tenant", schema=settings.DB_SCHEMA))
        assert db_inspector.get_pk_constraint("tenant", schema=settings.DB_SCHEMA) == {
            "constrained_columns": ["id"],
            "name": "pk_tenant",
            "comment": None,
        }

        # print(db_inspector.get_foreign_keys("tenant", schema=settings.DB_SCHEMA))
        assert db_inspector.get_foreign_keys("tenant", schema=settings.DB_SCHEMA) == [
            {
                "name": "fk_tenant_created_by_id",
                "constrained_columns": ["created_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "RESTRICT"},
                "comment": None,
            },
            {
                "name": "fk_tenant_deleted_by_id",
                "constrained_columns": ["deleted_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "SET NULL"},
                "comment": None,
            },
            {
                "name": "fk_tenant_id",
                "constrained_columns": ["id"],
                "referred_schema": "uno",
                "referred_table": "meta",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_tenant_modified_by_id",
                "constrained_columns": ["modified_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "RESTRICT"},
                "comment": None,
            },
        ]

        # print(db_inspector.get_unique_constraints("tenant", schema=settings.DB_SCHEMA))
        assert db_inspector.get_unique_constraints(
            "tenant", schema=settings.DB_SCHEMA
        ) == [
            {
                "column_names": ["name"],
                "comment": None,
                "name": "uq_tenant_name",
            },
        ]

        # print(db_inspector.get_check_constraints("tenant", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_check_constraints("tenant", schema=settings.DB_SCHEMA)
            == []
        )

    def test_tenant_type(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "tenant_type",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), ENUM)
        assert column.get("type").name == "tenanttype"
        assert column.get("type").enums == [
            TenantType.INDIVIDUAL.name,
            TenantType.PROFESSIONAL.name,
            TenantType.TEAM.name,
            TenantType.CORPORATE.name,
            TenantType.ENTERPRISE.name,
        ]

    def test_tenant_name(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "name",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 255

    def test_tenant_is_active(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "is_active",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), BOOLEAN)

    def test_tenant_is_deleted(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "is_deleted",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), BOOLEAN)

    def test_tenant_created_at(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "created_at",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), TIMESTAMP)

    def test_tenant_modified_at(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "modified_at",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), TIMESTAMP)

    def test_tenant_deleted_at(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "deleted_at",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == True
        assert isinstance(column.get("type"), TIMESTAMP)

    def test_tenant_created_by_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "created_by_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_tenant_modified_by_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "modified_by_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_tenant_deleted_by_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "tenant",
            "deleted_by_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == True
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26


class TestRoleTable:
    def test_role_table(self, connection, test_db):
        db_inspector = inspect(connection)
        # print(db_inspector.get_columns("role", schema=settings.DB_SCHEMA))
        assert [
            "tenant_id",
            "name",
            "description",
            "responsibility_role_id",
            "id",
            "is_active",
            "is_deleted",
            "created_at",
            "modified_at",
            "deleted_at",
            "created_by_id",
            "modified_by_id",
            "deleted_by_id",
        ] == [
            c.get("name")
            for c in db_inspector.get_columns("role", schema=settings.DB_SCHEMA)
        ]

        # print(db_inspector.get_indexes("role", schema=settings.DB_SCHEMA))
        assert db_inspector.get_indexes("role", schema=settings.DB_SCHEMA) == [
            {
                "name": "ix_role_tenant_id_name",
                "unique": False,
                "column_names": ["tenant_id", "name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_role_created_by_id",
                "unique": False,
                "column_names": ["created_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_role_deleted_by_id",
                "unique": False,
                "column_names": ["deleted_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_role_id",
                "unique": False,
                "column_names": ["id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_role_modified_by_id",
                "unique": False,
                "column_names": ["modified_by_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_role_name",
                "unique": False,
                "column_names": ["name"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_role_responsibility_role_id",
                "unique": False,
                "column_names": ["responsibility_role_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_role_tenant_id",
                "unique": False,
                "column_names": ["tenant_id"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "uq_role_tenant_id",
                "unique": True,
                "column_names": ["tenant_id", "name"],
                "duplicates_constraint": "uq_role_tenant_id",
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
        ]

        # print(db_inspector.get_pk_constraint("role", schema=settings.DB_SCHEMA))
        assert db_inspector.get_pk_constraint("role", schema=settings.DB_SCHEMA) == {
            "constrained_columns": ["id"],
            "name": "pk_role",
            "comment": None,
        }

        # print(db_inspector.get_foreign_keys("role", schema=settings.DB_SCHEMA))
        assert db_inspector.get_foreign_keys("role", schema=settings.DB_SCHEMA) == [
            {
                "name": "fk_role_created_by_id",
                "constrained_columns": ["created_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "RESTRICT"},
                "comment": None,
            },
            {
                "name": "fk_role_deleted_by_id",
                "constrained_columns": ["deleted_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "SET NULL"},
                "comment": None,
            },
            {
                "name": "fk_role_id",
                "constrained_columns": ["id"],
                "referred_schema": "uno",
                "referred_table": "meta",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_role_modified_by_id",
                "constrained_columns": ["modified_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "RESTRICT"},
                "comment": None,
            },
            {
                "name": "fk_role_responsibility_role_id",
                "constrained_columns": ["responsibility_role_id"],
                "referred_schema": "uno",
                "referred_table": "responsibility_role",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_role_tenant_id",
                "constrained_columns": ["tenant_id"],
                "referred_schema": "uno",
                "referred_table": "tenant",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

        # print(db_inspector.get_unique_constraints("role", schema=settings.DB_SCHEMA))
        assert db_inspector.get_unique_constraints(
            "role", schema=settings.DB_SCHEMA
        ) == [
            {
                "column_names": ["tenant_id", "name"],
                "name": "uq_role_tenant_id",
                "comment": None,
            }
        ]

        # print(db_inspector.get_check_constraints("role", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_check_constraints("role", schema=settings.DB_SCHEMA) == []
        )

    def test_role_tenant_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "tenant_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_role_name(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "name",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 255

    def test_role_description(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "description",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)

    def test_role_is_active(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "is_active",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), BOOLEAN)

    def test_role_is_deleted(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "is_deleted",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), BOOLEAN)

    def test_role_created_at(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "created_at",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), TIMESTAMP)

    def test_role_modified_at(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "modified_at",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), TIMESTAMP)

    def test_role_deleted_at(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "deleted_at",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == True
        assert isinstance(column.get("type"), TIMESTAMP)

    def test_role_created_by_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "created_by_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_role_modified_by_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "modified_by_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_role_deleted_by_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "deleted_by_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == True
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_role_responsibility_role_id(self, connection):
        db_inspector = inspect(connection)
        column = db_column(
            db_inspector,
            "role",
            "responsibility_role_id",
            schema=settings.DB_SCHEMA,
        )
        assert column is not None
        assert column.get("nullable") == False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26


class TestRolePermission:
    def test_role_permission_table(self, connection, test_db):
        db_inspector = inspect(connection)
        # print(db_inspector.get_columns("role_permission", schema=settings.DB_SCHEMA))
        assert [
            "role_id",
            "permission_id",
        ] == [
            c.get("name")
            for c in db_inspector.get_columns(
                "role__permission", schema=settings.DB_SCHEMA
            )
        ]

        assert db_inspector.get_pk_constraint(
            "role__permission", schema=settings.DB_SCHEMA
        ) == {
            "constrained_columns": ["role_id", "permission_id"],
            "name": "pk_role__permission",
            "comment": None,
        }

        assert db_inspector.get_foreign_keys(
            "role__permission", schema=settings.DB_SCHEMA
        ) == [
            {
                "name": "fk_role__permission_permission_id",
                "constrained_columns": ["permission_id"],
                "referred_schema": "uno",
                "referred_table": "permission",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_role__permission_role_id",
                "constrained_columns": ["role_id"],
                "referred_schema": "uno",
                "referred_table": "role",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
        ]

        # print(db_inspector.get_indexes("role_permission", schema=settings.DB_SCHEMA))
        assert db_inspector.get_indexes(
            "role__permission", schema=settings.DB_SCHEMA
        ) == [
            {
                "column_names": [
                    "role_id",
                    "permission_id",
                ],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
                "name": "ix_role_permission_role_id_permission_id",
                "unique": False,
            },
        ]

        assert (
            db_inspector.get_check_constraints(
                "role__permission", schema=settings.DB_SCHEMA
            )
            == []
        )

        assert (
            db_inspector.get_unique_constraints(
                "role__permission", schema=settings.DB_SCHEMA
            )
            == []
        )
        assert db_inspector.get_pk_constraint(
            "role__permission", schema=settings.DB_SCHEMA
        ) == {
            "constrained_columns": ["role_id", "permission_id"],
            "name": "pk_role__permission",
            "comment": None,
        }
