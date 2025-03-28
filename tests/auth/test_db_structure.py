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


class TestUserStructure:

    def test_user_triggers_and_functions(self, connection, test_db):
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_delete_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_delete_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_insert_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_insert_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'insert_meta_record')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_insert_meta_record_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'insert_record_status_columns')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_insert_record_status_columns_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_manage_audit_columns')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_manage_audit_columns_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_update_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_update_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_truncate_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_truncate_graph_trigger')"
            )
        ).scalar()

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
            "created_by_id",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ] == [
            c.get("name")
            for c in db_inspector.get_columns("user", schema=settings.DB_SCHEMA)
        ]

    def test_user_indices(self, connection, test_db):
        db_inspector = inspect(connection)
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

    def test_user_primary_key_constraint(self, connection):
        db_inspector = inspect(connection)
        # print(db_inspector.get_pk_constraint("user", schema=settings.DB_SCHEMA))
        assert db_inspector.get_pk_constraint("user", schema=settings.DB_SCHEMA) == {
            "constrained_columns": ["id"],
            "name": "pk_user",
            "comment": None,
        }

    def test_user_foreign_keys(self, connection):
        db_inspector = inspect(connection)
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

    def test_user_unique_constraints(self, connection):
        db_inspector = inspect(connection)
        # print(db_inspector.get_unique_constraints("user", schema=settings.DB_SCHEMA))
        assert (
            db_inspector.get_unique_constraints("user", schema=settings.DB_SCHEMA) == []
        )

    def test_user_check_constraints(self, connection):
        db_inspector = inspect(connection)
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


class TestUserGroupStructure:
    def test_user_group_triggers_and_functions(self, connection, test_db):

        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_delete_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_delete_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_insert_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_insert_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_update_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_update_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_truncate_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_truncate_graph_trigger')"
            )
        ).scalar()


"""
# customer Table Tests

 def test_customer_structure(db_inspector):
    assert [
        "id",
        "name",
        "customer_type",
    ] == [c.get("name") for c in db_inspector.get_columns("customer", schema="auth")]
    assert db_inspector.get_indexes("customer", schema="auth") == [
        {
            "name": "customer_name_key",
            "unique": True,
            "column_names": ["name"],
            "duplicates_constraint": "customer_name_key",
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        }
    ]
    assert db_inspector.get_pk_constraint("customer", schema="auth") == {
        "constrained_columns": ["id"],
        "name": "customer_pkey",
        "comment": None,
    }
    assert db_inspector.get_foreign_keys("customer", schema="auth") == [
        {
            "name": "customer_id_fkey",
            "constrained_columns": ["id"],
            "referred_schema": "audit",
            "referred_table": "meta",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        }
    ]
    assert db_inspector.get_unique_constraints("customer", schema="auth") == [
        {"column_names": ["name"], "name": "customer_name_key", "comment": None}
    ]



 def test_customer_id(db_inspector):
    column = db_column(db_inspector, "customer", "id")
    assert column is not None
    assert column.get("nullable") is False
    assert column.get("default") == "audit.create_meta_record()"
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_customer_name(db_inspector):
    column = db_column(db_inspector, "customer", "name")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 255



 def test_customer_customer_type(db_inspector):
    column = db_column(db_inspector, "customer", "customer_type")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), ENUM)
    assert column.get("type").name == "customertype"


# group Table Tests

 def test_group_structure(db_inspector):
    assert [
        "id",
        "parent_id",
        "name",
        "customer_id",
    ] == [c.get("name") for c in db_inspector.get_columns("group", schema="auth")]
    assert db_inspector.get_indexes("group", schema="auth") == [
        {
            "name": "auth_group_customer_id_idx",
            "unique": False,
            "column_names": ["customer_id"],
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
        {
            "name": "auth_group_parent_id_idx",
            "unique": False,
            "column_names": ["parent_id"],
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
        {
            "name": "uq_group_customer_id_name",
            "unique": True,
            "column_names": ["customer_id", "name"],
            "duplicates_constraint": "uq_group_customer_id_name",
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
    ]

    assert db_inspector.get_pk_constraint("group", schema="auth") == {
        "constrained_columns": ["id"],
        "name": "group_pkey",
        "comment": None,
    }
    assert db_inspector.get_foreign_keys("group", schema="auth") == [
        {
            "name": "group_customer_id_fkey",
            "constrained_columns": ["customer_id"],
            "referred_schema": "auth",
            "referred_table": "customer",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
        {
            "name": "group_id_fkey",
            "constrained_columns": ["id"],
            "referred_schema": "audit",
            "referred_table": "meta",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
        {
            "name": "group_parent_id_fkey",
            "constrained_columns": ["parent_id"],
            "referred_schema": "auth",
            "referred_table": "group",
            "referred_columns": ["id"],
            "options": {"ondelete": "SET NULL"},
            "comment": None,
        },
    ]

    assert db_inspector.get_unique_constraints("group", schema="auth") == [
        {
            "column_names": ["customer_id", "name"],
            "name": "uq_group_customer_id_name",
            "comment": None,
        }
    ]



 def test_group_id(db_inspector):
    column = db_column(db_inspector, "group", "id")
    assert column is not None
    assert column.get("nullable") is False
    assert column.get("default") == "audit.create_meta_record()"
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_group_name(db_inspector):
    column = db_column(db_inspector, "group", "name")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 255



 def test_group_parent_id(db_inspector):
    column = db_column(db_inspector, "group", "parent_id")
    assert column is not None
    assert column.get("nullable") is True
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26


# group_permission Table Tests

 def test_group_permission_structure(db_inspector):
    assert [
        "id",
        "group_id",
        "name",
        "permissions",
    ] == [
        c.get("name")
        for c in db_inspector.get_columns("group_permission", schema="auth")
    ]
    assert db_inspector.get_pk_constraint("group_permission", schema="auth") == {
        "constrained_columns": ["id"],
        "name": "group_permission_pkey",
        "comment": None,
    }
    assert db_inspector.get_foreign_keys("group_permission", schema="auth") == [
        {
            "name": "group_permission_group_id_fkey",
            "constrained_columns": ["group_id"],
            "referred_schema": "auth",
            "referred_table": "group",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        }
    ]
    assert db_inspector.get_indexes("group_permission", schema="auth") == [
        {
            "name": "auth_group_permission_group_id_idx",
            "unique": False,
            "column_names": ["group_id"],
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
        {
            "name": "uq_group_permission_name",
            "unique": True,
            "column_names": ["group_id", "name"],
            "duplicates_constraint": "uq_group_permission_name",
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
        {
            "name": "uq_group_permission_permissions",
            "unique": True,
            "column_names": ["group_id", "permissions"],
            "duplicates_constraint": "uq_group_permission_permissions",
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
    ]
    assert db_inspector.get_unique_constraints("group_permission", schema="auth") == [
        {
            "column_names": ["group_id", "name"],
            "name": "uq_group_permission_name",
            "comment": None,
        },
        {
            "column_names": ["group_id", "permissions"],
            "name": "uq_group_permission_permissions",
            "comment": None,
        },
    ]



 def test_group_permission_id(db_inspector):
    column = db_column(db_inspector, "group_permission", "id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), BIGINT)



 def test_group_permission_group_id(db_inspector):
    column = db_column(db_inspector, "group_permission", "group_id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_group_permission_permission(db_inspector):
    column = db_column(db_inspector, "group_permission", "permissions")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), ARRAY)
    # assert column.get("type").name == "permission"


# access_role Table Tests

 def test_role_structure(db_inspector):
    assert [
        "id",
        "customer_id",
        "name",
        "description",
    ] == [c.get("name") for c in db_inspector.get_columns("access_role", schema="auth")]

    assert db_inspector.get_pk_constraint("access_role", schema="auth") == {
        "constrained_columns": ["id"],
        "name": "role_pkey",
        "comment": None,
    }
    assert db_inspector.get_indexes("access_role", schema="auth") == [
        {
            "name": "auth_role_customer_id_idx",
            "unique": False,
            "column_names": ["customer_id"],
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
        {
            "name": "uq_role_customer_id_name",
            "unique": True,
            "column_names": ["customer_id", "name"],
            "duplicates_constraint": "uq_role_customer_id_name",
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        },
    ]
    assert db_inspector.get_foreign_keys("access_role", schema="auth") == [
        {
            "name": "role_customer_id_fkey",
            "constrained_columns": ["customer_id"],
            "referred_schema": "auth",
            "referred_table": "customer",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
        {
            "name": "role_id_fkey",
            "constrained_columns": ["id"],
            "referred_schema": "audit",
            "referred_table": "meta",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
    ]
    assert db_inspector.get_unique_constraints("access_role", schema="auth") == [
        {
            "column_names": ["customer_id", "name"],
            "name": "uq_role_customer_id_name",
            "comment": None,
        }
    ]



 def test_role_id(db_inspector):
    column = db_column(db_inspector, "access_role", "id")
    assert column is not None
    assert column.get("nullable") is False
    assert column.get("default") == "audit.create_meta_record()"
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_role_group_id(db_inspector):
    column = db_column(db_inspector, "access_role", "customer_id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_role_name(db_inspector):
    column = db_column(db_inspector, "access_role", "name")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 255



 def test_role_description(db_inspector):
    column = db_column(db_inspector, "access_role", "description")
    assert column is not None
    assert column.get("nullable") is True
    assert isinstance(column.get("type"), TEXT)


# role__group_permission Table Tests

 def test_role__group_permission_structure(db_inspector):
    assert [
        "role_id",
        "group_permission_id",
    ] == [
        c.get("name")
        for c in db_inspector.get_columns("role__group_permission", schema="auth")
    ]
    assert db_inspector.get_pk_constraint("role__group_permission", schema="auth") == {
        "constrained_columns": ["role_id", "group_permission_id"],
        "name": "role__group_permission_pkey",
        "comment": None,
    }
    assert db_inspector.get_foreign_keys("role__group_permission", schema="auth") == [
        {
            "name": "role__group_permission_group_permission_id_fkey",
            "constrained_columns": ["group_permission_id"],
            "referred_schema": "auth",
            "referred_table": "group_permission",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
        {
            "name": "role__group_permission_role_id_fkey",
            "constrained_columns": ["role_id"],
            "referred_schema": "auth",
            "referred_table": "access_role",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
    ]
    assert db_inspector.get_indexes("role__group_permission", schema="auth") == [
        {
            "name": "ix_role_id__group_permission_id",
            "unique": False,
            "column_names": ["role_id", "group_permission_id"],
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        }
    ]
    assert (
        db_inspector.get_unique_constraints("role__group_permission", schema="auth")
        == []
    )



 def test_role__group_permission_role_id(db_inspector):
    column = db_column(db_inspector, "role__group_permission", "role_id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_role__group_permission_group_id(db_inspector):
    column = db_column(db_inspector, "role__group_permission", "group_permission_id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), BIGINT)


# user__role Table Tests

 def test_user__role_structure(db_inspector):
    assert [
        "user_id",
        "role_id",
    ] == [c.get("name") for c in db_inspector.get_columns("user__role", schema="auth")]

    assert db_inspector.get_pk_constraint("user__role", schema="auth") == {
        "constrained_columns": ["user_id", "role_id"],
        "name": "user__role_pkey",
        "comment": None,
    }
    assert db_inspector.get_foreign_keys("user__role", schema="auth") == [
        {
            "name": "user__role_role_id_fkey",
            "constrained_columns": ["role_id"],
            "referred_schema": "auth",
            "referred_table": "access_role",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
        {
            "name": "user__role_user_id_fkey",
            "constrained_columns": ["user_id"],
            "referred_schema": "auth",
            "referred_table": "user",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
    ]
    assert db_inspector.get_indexes("user__role", schema="auth") == [
        {
            "name": "ix_user_id__role_id",
            "unique": False,
            "column_names": ["user_id", "role_id"],
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        }
    ]
    assert db_inspector.get_unique_constraints("user__role", schema="auth") == []



 def test_user__role_user_id(db_inspector):
    column = db_column(db_inspector, "user__role", "user_id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_user__role_group_id(db_inspector):
    column = db_column(db_inspector, "user__role", "role_id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26

"""
