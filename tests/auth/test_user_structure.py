from __future__ import annotations

''' 
import datetime

import pytest

from sqlalchemy import inspect, Inspector, Column
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

from uno.database.base import engine
from uno.apps.authorization.models import (
    Tenant,
    User,
    TableOperation,
    Role,
    RoleTableOperation,
    Group,
    UserGroupRole,
)
from uno.apps.authorization.enums import TenantType
from uno.config import settings  # type: ignore

from tests.conftest import (
    print_indices,
    print_pk_constraint,
    print_foreign_keys,
    print_uq_constraints,
    print_ck_constraints,
    db_column,
)


class TestUserStructure:
    # user Table Tests
    schema = "uno"

    def test_user_indices(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_indices(db_inspector, "user", schema=self.schema)
        assert db_inspector.get_indexes("user", schema=self.schema) == [
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
                "unique": False,
                "column_names": ["handle"],
                "include_columns": [],
                "dialect_options": {"postgresql_include": []},
            },
            {
                "name": "ix_uno_user_id",
                "unique": True,
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
                "name": "ix_uno_user_owned_by_id",
                "unique": False,
                "column_names": ["owned_by_id"],
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

    def test_user_primary_key_constraint(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_pk_constraint(db_inspector, "user", schema=self.schema)
        assert db_inspector.get_pk_constraint("user", schema=self.schema) == {
            "constrained_columns": ["id"],
            "name": "pk_user",
            "comment": None,
        }

    def test_user_foreign_keys(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_foreign_keys(db_inspector, "user", schema=self.schema)
        assert db_inspector.get_foreign_keys("user", schema=self.schema) == [
            {
                "name": "fk_user_default_group_id",
                "constrained_columns": ["default_group_id"],
                "referred_schema": "uno",
                "referred_table": "group",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user_deleted_by_id",
                "constrained_columns": ["deleted_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user_id",
                "constrained_columns": ["id"],
                "referred_schema": "uno",
                "referred_table": "related_object",
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
                "options": {"ondelete": "CASCADE"},
                "comment": None,
            },
            {
                "name": "fk_user_owned_by_id",
                "constrained_columns": ["owned_by_id"],
                "referred_schema": "uno",
                "referred_table": "user",
                "referred_columns": ["id"],
                "options": {"ondelete": "CASCADE"},
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

    def test_user_unique_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_uq_constraints(db_inspector, "user", schema=self.schema)
        assert db_inspector.get_unique_constraints("user", schema=self.schema) == []

    def test_user_check_constraints(self, db_connection):
        db_inspector = inspect(db_connection)
        # print_ck_constraints(db_inspector, "user", schema=self.schema)
        assert db_inspector.get_check_constraints("user", schema=self.schema) == [
            {
                "name": "ck_user_ck_user_is_superuser",
                "sqltext": "is_superuser = false AND default_group_id IS NOT NULL OR is_superuser = true AND default_group_id IS NULL AND is_superuser = false AND is_tenant_admin = false OR is_superuser = true AND is_tenant_admin = false OR is_superuser = false AND is_tenant_admin = true",
                "comment": None,
            }
        ]

    def test_user_id_column(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "user", "id", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), VARCHAR)
        assert column.get("type").length == 26

    def test_user_email(self, db_connection):
        db_inspector = inspect(db_connection)
        column = db_column(db_inspector, "user", "email", schema=self.schema)
        assert column is not None
        assert column.get("nullable") is False
        assert isinstance(column.get("type"), TEXT)


"""

 def test_user_full_name(db_inspector):
    column = db_column(db_inspector, "user", "full_name")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 255



 def test_user_handle(db_inspector):
    column = db_column(db_inspector, "user", "handle")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 255


# hashed_password Table Tests

 def test_hashed_password_structure(db_inspector):
    assert [
        "id",
        "hashed_password",
        "is_active",
        "created_at",
        "modified_at",
    ] == [
        c.get("name")
        for c in db_inspector.get_columns("hashed_password", schema="auth")
    ]
    assert db_inspector.get_indexes("hashed_password", schema="auth") == []
    assert db_inspector.get_pk_constraint("hashed_password", schema="auth") == {
        "constrained_columns": ["id"],
        "name": "hashed_password_pkey",
        "comment": None,
    }
    assert db_inspector.get_foreign_keys("hashed_password", schema="auth") == [
        {
            "name": "hashed_password_id_fkey",
            "constrained_columns": ["id"],
            "referred_schema": "auth",
            "referred_table": "user",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        }
    ]
    assert db_inspector.get_unique_constraints("hashed_password", schema="auth") == []



 def test_hashed_password_id(db_inspector):
    column = db_column(db_inspector, "hashed_password", "id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_hashed_password_hashed_password(db_inspector):
    column = db_column(db_inspector, "hashed_password", "hashed_password")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 128



 def test_hashed_password_is_active(db_inspector):
    column = db_column(db_inspector, "hashed_password", "is_active")
    assert column is not None
    assert column.get("nullable") is False
    assert column.get("default") == "true"
    assert isinstance(column.get("type"), BOOLEAN)



 def test_hashed_password_created_at(db_inspector):
    column = db_column(db_inspector, "hashed_password", "created_at")
    assert column is not None
    assert column.get("nullable") is False
    assert column.get("default") == "now()"
    assert isinstance(column.get("type"), TIMESTAMP)



 def test_hashed_password_modified_at(db_inspector):
    column = db_column(db_inspector, "hashed_password", "modified_at")
    assert column is not None
    assert column.get("nullable") is False
    assert column.get("default") == "now()"
    assert isinstance(column.get("type"), TIMESTAMP)


# user_admin Table Tests

 def test_user_admin_structure(db_inspector):
    assert [
        "id",
        "is_superuser",
        "is_customer_admin",
        "is_verified",
        "is_locked",
        "is_suspended",
        "suspension_expiration",
        "customer_id",
    ] == [c.get("name") for c in db_inspector.get_columns("user_admin", schema="auth")]

    assert db_inspector.get_indexes("user_admin", schema="auth") == [
        {
            "name": "auth_user_admin_customer_id_idx",
            "unique": False,
            "column_names": ["customer_id"],
            "include_columns": [],
            "dialect_options": {"postgresql_include": []},
        }
    ]

    assert db_inspector.get_pk_constraint("user_admin", schema="auth") == {
        "constrained_columns": ["id"],
        "name": "user_admin_pkey",
        "comment": None,
    }

    assert db_inspector.get_foreign_keys("user_admin", schema="auth") == [
        {
            "name": "user_admin_customer_id_fkey",
            "constrained_columns": ["customer_id"],
            "referred_schema": "auth",
            "referred_table": "customer",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
        {
            "name": "user_admin_id_fkey",
            "constrained_columns": ["id"],
            "referred_schema": "auth",
            "referred_table": "user",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
            "comment": None,
        },
    ]
    assert db_inspector.get_unique_constraints("user_admin", schema="auth") == []



 def test_user_is_superuser(db_inspector):
    column = db_column(db_inspector, "user_admin", "is_superuser")
    assert column is not None
    assert column.get("default") == "false"
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), BOOLEAN)



 def test_user_is_customer_admin(db_inspector):
    column = db_column(db_inspector, "user_admin", "is_customer_admin")
    assert column is not None
    assert column.get("default") == "false"
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), BOOLEAN)



 def test_user_is_verified(db_inspector):
    column = db_column(db_inspector, "user_admin", "is_verified")
    assert column is not None
    assert column.get("default") == "false"
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), BOOLEAN)



 def test_user_is_locked(db_inspector):
    column = db_column(db_inspector, "user_admin", "is_locked")
    assert column is not None
    assert column.get("default") == "false"
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), BOOLEAN)



 def test_user_is_suspended(db_inspector):
    column = db_column(db_inspector, "user_admin", "is_suspended")
    assert column is not None
    assert column.get("default") == "false"
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), BOOLEAN)



 def test_user_suspension_expiration(db_inspector):
    column = db_column(db_inspector, "user_admin", "suspension_expiration")
    assert column is not None
    assert column.get("default") is None
    assert column.get("nullable") is True
    assert isinstance(column.get("type"), TIMESTAMP)



 def test_user_customer_id(db_inspector):
    column = db_column(db_inspector, "user_admin", "customer_id")
    assert column is not None
    assert column.get("nullable") is True
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26


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


# role Table Tests

 def test_role_structure(db_inspector):
    assert [
        "id",
        "customer_id",
        "name",
        "description",
    ] == [c.get("name") for c in db_inspector.get_columns("role", schema="auth")]

    assert db_inspector.get_pk_constraint("role", schema="auth") == {
        "constrained_columns": ["id"],
        "name": "role_pkey",
        "comment": None,
    }
    assert db_inspector.get_indexes("role", schema="auth") == [
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
    assert db_inspector.get_foreign_keys("role", schema="auth") == [
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
    assert db_inspector.get_unique_constraints("role", schema="auth") == [
        {
            "column_names": ["customer_id", "name"],
            "name": "uq_role_customer_id_name",
            "comment": None,
        }
    ]



 def test_role_id(db_inspector):
    column = db_column(db_inspector, "role", "id")
    assert column is not None
    assert column.get("nullable") is False
    assert column.get("default") == "audit.create_meta_record()"
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_role_group_id(db_inspector):
    column = db_column(db_inspector, "role", "customer_id")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 26



 def test_role_name(db_inspector):
    column = db_column(db_inspector, "role", "name")
    assert column is not None
    assert column.get("nullable") is False
    assert isinstance(column.get("type"), TEXT)
    assert column.get("type").length == 255



 def test_role_description(db_inspector):
    column = db_column(db_inspector, "role", "description")
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
            "referred_table": "role",
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
            "referred_table": "role",
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

'''
