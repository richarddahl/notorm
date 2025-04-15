"""
Integration tests for database-level permissions.

This module tests the database-level permission system, including permission assignments,
checks, and integration with Row-Level Security (RLS) and SQL operations.
"""

import pytest
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum

from sqlalchemy import (
    text,
    Column,
    String,
    Boolean,
    ForeignKey,
    Integer,
    Table,
    MetaData,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends, APIRouter, Request, Response

from uno.database.session import async_session
from uno.database.db_manager import DBManager
from uno.database.db_manager import DBManager
from uno.model import UnoModel
from uno.enums import SQLOperation, TenantType
from uno.sql.emitter import SQLEmitter
from uno.sql.config import ConnectionConfig
from uno.sql.emitters.security import RowLevelSecurity, UserRowLevelSecurity
from uno.sql.emitters.grants import AlterGrants


# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration]


# Test models for permission tests
class TestMetaType(UnoModel):
    """Test meta type model for permission tests."""

    __tablename__ = "test_perm_meta_type"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)


class TestPermission(UnoModel):
    """Test permission model for permission tests."""

    __tablename__ = "test_perm_permission"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(Integer, primary_key=True, autoincrement=True)
    meta_type_id = Column(String, ForeignKey("test_perm_meta_type.id"), nullable=False)
    operation = Column(String, nullable=False)


class TestRole(UnoModel):
    """Test role model for permission tests."""

    __tablename__ = "test_perm_role"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    tenant_id = Column(String, ForeignKey("test_perm_tenant.id"), nullable=False)


class TestRolePermission(UnoModel):
    """Test role-permission association model for permission tests."""

    __tablename__ = "test_perm_role_permission"
    __test__ = False  # Prevent pytest from collecting this model as a test

    role_id = Column(String, ForeignKey("test_perm_role.id"), primary_key=True)
    permission_id = Column(
        Integer, ForeignKey("test_perm_permission.id"), primary_key=True
    )


class TestUser(UnoModel):
    """Test user model for permission tests."""

    __tablename__ = "test_perm_user"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    handle = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)
    is_tenant_admin = Column(Boolean, default=False)
    tenant_id = Column(String, ForeignKey("test_perm_tenant.id"), nullable=True)


class TestUserRole(UnoModel):
    """Test user-role association model for permission tests."""

    __tablename__ = "test_perm_user_role"
    __test__ = False  # Prevent pytest from collecting this model as a test

    user_id = Column(String, ForeignKey("test_perm_user.id"), primary_key=True)
    role_id = Column(String, ForeignKey("test_perm_role.id"), primary_key=True)


class TestTenant(UnoModel):
    """Test tenant model for permission tests."""

    __tablename__ = "test_perm_tenant"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tenant_type = Column(String, nullable=False, default="INDIVIDUAL")


class TestResource(UnoModel):
    """Test resource model that will be subject to permissions."""

    __tablename__ = "test_perm_resource"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tenant_id = Column(String, ForeignKey("test_perm_tenant.id"), nullable=False)
    owner_id = Column(String, ForeignKey("test_perm_user.id"), nullable=False)


@pytest.fixture(scope="module")
async def schema_manager():
    """Create a schema manager for testing."""
    return DBManager()


@pytest.fixture(scope="module")
async def test_schema(schema_manager):
    """Create a test schema for permission tests."""
    async with async_session() as session:
        # Drop schema if it exists
        await session.execute(text("DROP SCHEMA IF EXISTS test_perms CASCADE"))

        # Create schema
        await session.execute(text("CREATE SCHEMA test_perms"))

        # Create tables in the schema
        models = [
            TestMetaType,
            TestPermission,
            TestRole,
            TestRolePermission,
            TestUser,
            TestUserRole,
            TestTenant,
            TestResource,
        ]
        for model in models:
            model.__table__.schema = "test_perms"
            await session.execute(text(schema_manager.create_table_sql(model)))

        # Create functions for permission checks
        await session.execute(
            text(
                """
            -- Function to check permission based on user and role
            CREATE OR REPLACE FUNCTION test_perms.check_permission(
                p_user_id TEXT,
                p_meta_type_id TEXT,
                p_operation TEXT
            )
            RETURNS BOOLEAN AS $$
            DECLARE
                has_permission BOOLEAN;
            BEGIN
                -- Check if the user has any role with the permission
                SELECT EXISTS(
                    SELECT 1
                    FROM test_perms.test_perm_user_role ur
                    JOIN test_perms.test_perm_role_permission rp ON ur.role_id = rp.role_id
                    JOIN test_perms.test_perm_permission p ON rp.permission_id = p.id
                    WHERE ur.user_id = p_user_id
                    AND p.meta_type_id = p_meta_type_id
                    AND p.operation = p_operation
                ) INTO has_permission;
                
                RETURN has_permission;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to check if user is superuser or tenant admin
            CREATE OR REPLACE FUNCTION test_perms.check_user_status(
                p_user_id TEXT
            )
            RETURNS TABLE(
                is_superuser BOOLEAN,
                is_tenant_admin BOOLEAN,
                tenant_id TEXT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    u.is_superuser,
                    u.is_tenant_admin,
                    u.tenant_id
                FROM test_perms.test_perm_user u
                WHERE u.id = p_user_id;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to set user context for permission checks
            CREATE OR REPLACE FUNCTION test_perms.set_permission_context(
                p_user_id TEXT
            )
            RETURNS VOID AS $$
            DECLARE
                v_is_superuser BOOLEAN;
                v_is_tenant_admin BOOLEAN;
                v_tenant_id TEXT;
                v_user_email TEXT;
            BEGIN
                -- Get user information
                SELECT 
                    u.is_superuser,
                    u.is_tenant_admin,
                    u.tenant_id,
                    u.email
                INTO
                    v_is_superuser,
                    v_is_tenant_admin,
                    v_tenant_id,
                    v_user_email
                FROM test_perms.test_perm_user u
                WHERE u.id = p_user_id;
                
                -- Set context variables
                PERFORM set_config('test_perms.user_id', p_user_id, TRUE);
                PERFORM set_config('test_perms.is_superuser', v_is_superuser::TEXT, TRUE);
                PERFORM set_config('test_perms.is_tenant_admin', v_is_tenant_admin::TEXT, TRUE);
                
                IF v_tenant_id IS NOT NULL THEN
                    PERFORM set_config('test_perms.tenant_id', v_tenant_id, TRUE);
                END IF;
                
                IF v_user_email IS NOT NULL THEN
                    PERFORM set_config('test_perms.email', v_user_email, TRUE);
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to get all roles for a user
            CREATE OR REPLACE FUNCTION test_perms.get_user_roles(
                p_user_id TEXT
            )
            RETURNS TABLE(
                role_id TEXT,
                role_name TEXT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT r.id, r.name
                FROM test_perms.test_perm_user_role ur
                JOIN test_perms.test_perm_role r ON ur.role_id = r.id
                WHERE ur.user_id = p_user_id;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to get all permissions for a user
            CREATE OR REPLACE FUNCTION test_perms.get_user_permissions(
                p_user_id TEXT
            )
            RETURNS TABLE(
                meta_type_id TEXT,
                operation TEXT
            ) AS $$
            BEGIN
                -- Get permissions from roles
                RETURN QUERY
                SELECT DISTINCT p.meta_type_id, p.operation
                FROM test_perms.test_perm_user_role ur
                JOIN test_perms.test_perm_role_permission rp ON ur.role_id = rp.role_id
                JOIN test_perms.test_perm_permission p ON rp.permission_id = p.id
                WHERE ur.user_id = p_user_id;
            END;
            $$ LANGUAGE plpgsql;
        """
            )
        )

        # Apply RLS to TestResource table
        config = ConnectionConfig(DB_NAME="uno_test", DB_SCHEMA="test_perms")
        rls = RowLevelSecurity(config=config, table=TestResource.__table__)
        await session.execute(
            text(
                f"""
            -- Enable RLS for the TestResource table
            ALTER TABLE test_perms.{TestResource.__tablename__} ENABLE ROW LEVEL SECURITY;
            
            -- Create RLS policies
            -- 1. SELECT policy
            CREATE POLICY resource_select_policy
            ON test_perms.{TestResource.__tablename__} FOR SELECT
            USING (
                current_setting('test_perms.is_superuser', TRUE)::BOOLEAN OR
                tenant_id = current_setting('test_perms.tenant_id', TRUE)::TEXT OR
                owner_id = current_setting('test_perms.user_id', TRUE)::TEXT
            );
            
            -- 2. INSERT policy
            CREATE POLICY resource_insert_policy
            ON test_perms.{TestResource.__tablename__} FOR INSERT
            WITH CHECK (
                current_setting('test_perms.is_superuser', TRUE)::BOOLEAN OR
                (
                    tenant_id = current_setting('test_perms.tenant_id', TRUE)::TEXT AND
                    (
                        current_setting('test_perms.is_tenant_admin', TRUE)::BOOLEAN OR
                        owner_id = current_setting('test_perms.user_id', TRUE)::TEXT
                    )
                )
            );
            
            -- 3. UPDATE policy
            CREATE POLICY resource_update_policy
            ON test_perms.{TestResource.__tablename__} FOR UPDATE
            USING (
                current_setting('test_perms.is_superuser', TRUE)::BOOLEAN OR
                (
                    tenant_id = current_setting('test_perms.tenant_id', TRUE)::TEXT AND
                    (
                        current_setting('test_perms.is_tenant_admin', TRUE)::BOOLEAN OR
                        owner_id = current_setting('test_perms.user_id', TRUE)::TEXT
                    )
                )
            );
            
            -- 4. DELETE policy
            CREATE POLICY resource_delete_policy
            ON test_perms.{TestResource.__tablename__} FOR DELETE
            USING (
                current_setting('test_perms.is_superuser', TRUE)::BOOLEAN OR
                (
                    tenant_id = current_setting('test_perms.tenant_id', TRUE)::TEXT AND
                    (
                        current_setting('test_perms.is_tenant_admin', TRUE)::BOOLEAN OR
                        owner_id = current_setting('test_perms.user_id', TRUE)::TEXT
                    )
                )
            );
        """
            )
        )

        await session.commit()

    # Return the schema name
    return "test_perms"


@pytest.fixture(scope="module")
async def test_data(test_schema):
    """Create test data for permission tests."""
    # Define data to insert
    meta_types = [{"id": "resource"}, {"id": "user"}, {"id": "tenant"}, {"id": "role"}]

    permissions = [
        {"meta_type_id": "resource", "operation": "SELECT"},
        {"meta_type_id": "resource", "operation": "INSERT"},
        {"meta_type_id": "resource", "operation": "UPDATE"},
        {"meta_type_id": "resource", "operation": "DELETE"},
        {"meta_type_id": "user", "operation": "SELECT"},
        {"meta_type_id": "user", "operation": "INSERT"},
        {"meta_type_id": "user", "operation": "UPDATE"},
        {"meta_type_id": "user", "operation": "DELETE"},
        {"meta_type_id": "tenant", "operation": "SELECT"},
        {"meta_type_id": "tenant", "operation": "UPDATE"},
        {"meta_type_id": "role", "operation": "SELECT"},
        {"meta_type_id": "role", "operation": "INSERT"},
        {"meta_type_id": "role", "operation": "UPDATE"},
        {"meta_type_id": "role", "operation": "DELETE"},
    ]

    tenants = [
        {"id": "tenant-1", "name": "Tenant 1", "tenant_type": "ORGANIZATION"},
        {"id": "tenant-2", "name": "Tenant 2", "tenant_type": "ORGANIZATION"},
    ]

    roles = [
        {
            "id": "admin",
            "name": "Administrator",
            "description": "Full access",
            "tenant_id": "tenant-1",
        },
        {
            "id": "editor",
            "name": "Editor",
            "description": "Can edit resources",
            "tenant_id": "tenant-1",
        },
        {
            "id": "viewer",
            "name": "Viewer",
            "description": "Read-only access",
            "tenant_id": "tenant-1",
        },
        {
            "id": "admin-t2",
            "name": "Administrator",
            "description": "Full access",
            "tenant_id": "tenant-2",
        },
        {
            "id": "editor-t2",
            "name": "Editor",
            "description": "Can edit resources",
            "tenant_id": "tenant-2",
        },
        {
            "id": "viewer-t2",
            "name": "Viewer",
            "description": "Read-only access",
            "tenant_id": "tenant-2",
        },
    ]

    users = [
        {
            "id": "user-1",
            "email": "admin@tenant1.com",
            "handle": "admin1",
            "full_name": "Tenant 1 Admin",
            "is_superuser": False,
            "is_tenant_admin": True,
            "tenant_id": "tenant-1",
        },
        {
            "id": "user-2",
            "email": "editor@tenant1.com",
            "handle": "editor1",
            "full_name": "Tenant 1 Editor",
            "is_superuser": False,
            "is_tenant_admin": False,
            "tenant_id": "tenant-1",
        },
        {
            "id": "user-3",
            "email": "viewer@tenant1.com",
            "handle": "viewer1",
            "full_name": "Tenant 1 Viewer",
            "is_superuser": False,
            "is_tenant_admin": False,
            "tenant_id": "tenant-1",
        },
        {
            "id": "user-4",
            "email": "admin@tenant2.com",
            "handle": "admin2",
            "full_name": "Tenant 2 Admin",
            "is_superuser": False,
            "is_tenant_admin": True,
            "tenant_id": "tenant-2",
        },
        {
            "id": "user-5",
            "email": "editor@tenant2.com",
            "handle": "editor2",
            "full_name": "Tenant 2 Editor",
            "is_superuser": False,
            "is_tenant_admin": False,
            "tenant_id": "tenant-2",
        },
        {
            "id": "superuser",
            "email": "superuser@system.com",
            "handle": "superuser",
            "full_name": "System Superuser",
            "is_superuser": True,
            "is_tenant_admin": False,
            "tenant_id": None,
        },
    ]

    async with async_session() as session:
        # Insert meta types
        for meta_type in meta_types:
            await session.execute(
                text(
                    f"INSERT INTO {test_schema}.test_perm_meta_type (id) VALUES (:id)"
                ),
                meta_type,
            )

        # Insert permissions
        permission_ids = {}
        for permission in permissions:
            result = await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_perm_permission (meta_type_id, operation) 
                    VALUES (:meta_type_id, :operation)
                    RETURNING id
                """
                ),
                permission,
            )
            perm_id = result.scalar()
            key = f"{permission['meta_type_id']}:{permission['operation']}"
            permission_ids[key] = perm_id

        # Insert tenants
        for tenant in tenants:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_perm_tenant (id, name, tenant_type) 
                    VALUES (:id, :name, :tenant_type)
                """
                ),
                tenant,
            )

        # Insert roles
        for role in roles:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_perm_role (id, name, description, tenant_id) 
                    VALUES (:id, :name, :description, :tenant_id)
                """
                ),
                role,
            )

        # Insert users
        for user in users:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_perm_user 
                    (id, email, handle, full_name, is_superuser, is_tenant_admin, tenant_id) 
                    VALUES (:id, :email, :handle, :full_name, :is_superuser, :is_tenant_admin, :tenant_id)
                """
                ),
                user,
            )

        # Assign roles to users
        user_roles = [
            {"user_id": "user-1", "role_id": "admin"},  # Tenant 1 Admin gets admin role
            {
                "user_id": "user-2",
                "role_id": "editor",
            },  # Tenant 1 Editor gets editor role
            {
                "user_id": "user-3",
                "role_id": "viewer",
            },  # Tenant 1 Viewer gets viewer role
            {
                "user_id": "user-4",
                "role_id": "admin-t2",
            },  # Tenant 2 Admin gets admin role
            {
                "user_id": "user-5",
                "role_id": "editor-t2",
            },  # Tenant 2 Editor gets editor role
            {"user_id": "superuser", "role_id": "admin"},  # Superuser gets admin role
        ]

        for user_role in user_roles:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_perm_user_role (user_id, role_id) 
                    VALUES (:user_id, :role_id)
                """
                ),
                user_role,
            )

        # Assign permissions to roles
        role_permissions = [
            # Admin role has all resource permissions
            {"role_id": "admin", "permission_id": permission_ids["resource:SELECT"]},
            {"role_id": "admin", "permission_id": permission_ids["resource:INSERT"]},
            {"role_id": "admin", "permission_id": permission_ids["resource:UPDATE"]},
            {"role_id": "admin", "permission_id": permission_ids["resource:DELETE"]},
            {"role_id": "admin", "permission_id": permission_ids["user:SELECT"]},
            {"role_id": "admin", "permission_id": permission_ids["user:UPDATE"]},
            {"role_id": "admin", "permission_id": permission_ids["tenant:SELECT"]},
            {"role_id": "admin", "permission_id": permission_ids["role:SELECT"]},
            # Editor role has create, read, update permissions
            {"role_id": "editor", "permission_id": permission_ids["resource:SELECT"]},
            {"role_id": "editor", "permission_id": permission_ids["resource:INSERT"]},
            {"role_id": "editor", "permission_id": permission_ids["resource:UPDATE"]},
            {"role_id": "editor", "permission_id": permission_ids["user:SELECT"]},
            {"role_id": "editor", "permission_id": permission_ids["tenant:SELECT"]},
            {"role_id": "editor", "permission_id": permission_ids["role:SELECT"]},
            # Viewer role has only read permissions
            {"role_id": "viewer", "permission_id": permission_ids["resource:SELECT"]},
            {"role_id": "viewer", "permission_id": permission_ids["user:SELECT"]},
            {"role_id": "viewer", "permission_id": permission_ids["tenant:SELECT"]},
            {"role_id": "viewer", "permission_id": permission_ids["role:SELECT"]},
            # Tenant 2 roles - same permissions as tenant 1 roles
            {"role_id": "admin-t2", "permission_id": permission_ids["resource:SELECT"]},
            {"role_id": "admin-t2", "permission_id": permission_ids["resource:INSERT"]},
            {"role_id": "admin-t2", "permission_id": permission_ids["resource:UPDATE"]},
            {"role_id": "admin-t2", "permission_id": permission_ids["resource:DELETE"]},
            {"role_id": "admin-t2", "permission_id": permission_ids["user:SELECT"]},
            {"role_id": "admin-t2", "permission_id": permission_ids["user:UPDATE"]},
            {"role_id": "admin-t2", "permission_id": permission_ids["tenant:SELECT"]},
            {"role_id": "admin-t2", "permission_id": permission_ids["role:SELECT"]},
            {
                "role_id": "editor-t2",
                "permission_id": permission_ids["resource:SELECT"],
            },
            {
                "role_id": "editor-t2",
                "permission_id": permission_ids["resource:INSERT"],
            },
            {
                "role_id": "editor-t2",
                "permission_id": permission_ids["resource:UPDATE"],
            },
            {"role_id": "editor-t2", "permission_id": permission_ids["user:SELECT"]},
            {"role_id": "editor-t2", "permission_id": permission_ids["tenant:SELECT"]},
            {"role_id": "editor-t2", "permission_id": permission_ids["role:SELECT"]},
        ]

        for role_permission in role_permissions:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_perm_role_permission (role_id, permission_id) 
                    VALUES (:role_id, :permission_id)
                """
                ),
                role_permission,
            )

        # Insert resources
        resources = [
            {
                "name": "Resource 1",
                "description": "Owned by Admin",
                "tenant_id": "tenant-1",
                "owner_id": "user-1",
            },
            {
                "name": "Resource 2",
                "description": "Owned by Editor",
                "tenant_id": "tenant-1",
                "owner_id": "user-2",
            },
            {
                "name": "Resource 3",
                "description": "Owned by Viewer",
                "tenant_id": "tenant-1",
                "owner_id": "user-3",
            },
            {
                "name": "Resource 4",
                "description": "Owned by T2 Admin",
                "tenant_id": "tenant-2",
                "owner_id": "user-4",
            },
            {
                "name": "Resource 5",
                "description": "Owned by T2 Editor",
                "tenant_id": "tenant-2",
                "owner_id": "user-5",
            },
        ]

        # Need to temporarily disable RLS to insert the resources
        await session.execute(text(f"SET test_perms.is_superuser = 'true'"))

        for resource in resources:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_perm_resource (name, description, tenant_id, owner_id) 
                    VALUES (:name, :description, :tenant_id, :owner_id)
                """
                ),
                resource,
            )

        # Reset session variables
        await session.execute(
            text(
                f"""
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.user_id = '';
            SET test_perms.email = '';
        """
            )
        )

        await session.commit()

    # Return test data
    return {
        "meta_types": meta_types,
        "permissions": permission_ids,
        "tenants": tenants,
        "roles": roles,
        "users": users,
        "user_roles": user_roles,
        "role_permissions": role_permissions,
        "resources": resources,
    }


@pytest.mark.asyncio
async def test_permission_checks(test_schema, test_data):
    """Test permission checking mechanism."""
    async with async_session() as session:
        # Check admin permissions
        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-1", "meta_type_id": "resource", "operation": "SELECT"},
        )
        assert result.scalar() is True

        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-1", "meta_type_id": "resource", "operation": "DELETE"},
        )
        assert result.scalar() is True

        # Check editor permissions
        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-2", "meta_type_id": "resource", "operation": "SELECT"},
        )
        assert result.scalar() is True

        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-2", "meta_type_id": "resource", "operation": "UPDATE"},
        )
        assert result.scalar() is True

        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-2", "meta_type_id": "resource", "operation": "DELETE"},
        )
        assert result.scalar() is False  # Editor doesn't have DELETE permission

        # Check viewer permissions
        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-3", "meta_type_id": "resource", "operation": "SELECT"},
        )
        assert result.scalar() is True

        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-3", "meta_type_id": "resource", "operation": "INSERT"},
        )
        assert result.scalar() is False  # Viewer doesn't have INSERT permission


@pytest.mark.asyncio
async def test_get_user_permissions(test_schema, test_data):
    """Test retrieving all permissions for a user."""
    async with async_session() as session:
        # Get permissions for admin user
        result = await session.execute(
            text(f"SELECT * FROM test_perms.get_user_permissions(:user_id)"),
            {"user_id": "user-1"},
        )
        admin_permissions = result.fetchall()

        # Admin should have multiple permissions
        assert len(admin_permissions) >= 8

        # Check if admin has resource permissions
        resource_permissions = [p for p in admin_permissions if p[0] == "resource"]
        assert len(resource_permissions) >= 4

        # Get permissions for viewer user
        result = await session.execute(
            text(f"SELECT * FROM test_perms.get_user_permissions(:user_id)"),
            {"user_id": "user-3"},
        )
        viewer_permissions = result.fetchall()

        # Viewer should have only SELECT permissions
        assert all(p[1] == "SELECT" for p in viewer_permissions)

        # The number of permissions should match our setup
        assert len(viewer_permissions) == 4  # One SELECT for each meta type


@pytest.mark.asyncio
async def test_set_permission_context(test_schema, test_data):
    """Test setting permission context for a user."""
    async with async_session() as session:
        # Set permission context for admin user
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-1"},
        )

        # Check that context was set correctly
        result = await session.execute(
            text("SELECT current_setting('test_perms.user_id', TRUE)")
        )
        assert result.scalar() == "user-1"

        result = await session.execute(
            text("SELECT current_setting('test_perms.is_tenant_admin', TRUE)")
        )
        assert result.scalar() == "true"

        result = await session.execute(
            text("SELECT current_setting('test_perms.tenant_id', TRUE)")
        )
        assert result.scalar() == "tenant-1"

        # Set permission context for superuser
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "superuser"},
        )

        # Check that context was set correctly
        result = await session.execute(
            text("SELECT current_setting('test_perms.user_id', TRUE)")
        )
        assert result.scalar() == "superuser"

        result = await session.execute(
            text("SELECT current_setting('test_perms.is_superuser', TRUE)")
        )
        assert result.scalar() == "true"

        # Clear context variables for other tests
        await session.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_rls_with_permissions_admin(test_schema, test_data):
    """Test RLS with permissions for admin user."""
    async with async_session() as session:
        # Set permission context for tenant 1 admin user
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-1"},
        )

        # Admin should see all resources for their tenant
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.test_perm_resource")
        )
        resources = result.fetchall()

        # Should see all tenant 1 resources
        tenant_1_resources = [
            r for r in test_data["resources"] if r["tenant_id"] == "tenant-1"
        ]
        assert len(resources) == len(tenant_1_resources)

        # Insert a new resource
        result = await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_resource 
                (name, description, tenant_id, owner_id)
                VALUES ('Admin New Resource', 'Created by admin', 'tenant-1', 'user-1')
                RETURNING id
            """
            )
        )
        new_resource_id = result.scalar()

        # Update an existing resource
        await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_perm_resource
                SET description = 'Updated by admin'
                WHERE tenant_id = 'tenant-1' AND owner_id = 'user-2'
            """
            )
        )

        # Delete a resource
        result = await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_perm_resource 
                WHERE tenant_id = 'tenant-1' AND owner_id = 'user-3'
                RETURNING id
            """
            )
        )
        deleted_id = result.scalar()
        assert deleted_id is not None

        # Try to access tenant 2 resources (should fail)
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_perm_resource
                SET description = 'Should fail'
                WHERE tenant_id = 'tenant-2'
            """
            )
        )
        assert result.rowcount == 0  # No rows should be updated

        # Verify changes
        await session.commit()

        # Clear context variables for other tests
        await session.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_rls_with_permissions_editor(test_schema, test_data):
    """Test RLS with permissions for editor user."""
    async with async_session() as session:
        # Set permission context for tenant 1 editor user
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-2"},
        )

        # Editor should see all resources for their tenant
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.test_perm_resource")
        )
        resources = result.fetchall()

        # Should see all tenant 1 resources
        tenant_1_resources = [
            r for r in test_data["resources"] if r["tenant_id"] == "tenant-1"
        ]
        assert (
            len(resources) >= 2
        )  # At least 2 resources (accounting for deletions in previous tests)

        # Insert a new resource
        result = await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_resource 
                (name, description, tenant_id, owner_id)
                VALUES ('Editor New Resource', 'Created by editor', 'tenant-1', 'user-2')
                RETURNING id
            """
            )
        )
        new_resource_id = result.scalar()

        # Update own resource
        await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_perm_resource
                SET description = 'Updated by editor'
                WHERE tenant_id = 'tenant-1' AND owner_id = 'user-2'
            """
            )
        )

        # Try to update admin's resource (should fail due to RLS)
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_perm_resource
                SET description = 'Should fail'
                WHERE tenant_id = 'tenant-1' AND owner_id = 'user-1'
            """
            )
        )

        # Should have permission but RLS restricts to own resources
        assert result.rowcount == 0  # No rows should be updated

        # Try to delete a resource (should fail due to missing permission)
        result = await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_perm_resource 
                WHERE tenant_id = 'tenant-1' AND owner_id = 'user-2'
            """
            )
        )
        # This is an interesting case - editor doesn't have DELETE permission in RBAC,
        # but RLS would allow deletion of own resources. RBAC should take precedence.
        assert result.rowcount == 0  # No rows should be deleted

        # Verify changes
        await session.commit()

        # Clear context variables for other tests
        await session.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_rls_with_permissions_superuser(test_schema, test_data):
    """Test RLS with permissions for superuser."""
    async with async_session() as session:
        # Set permission context for superuser
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "superuser"},
        )

        # Superuser should see all resources
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.test_perm_resource")
        )
        resources = result.fetchall()

        # Should see resources from all tenants
        assert (
            len(resources) >= 4
        )  # At least 4 resources (accounting for possible deletions in previous tests)

        # Insert a resource in any tenant
        result = await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_resource 
                (name, description, tenant_id, owner_id)
                VALUES ('Superuser Resource', 'Created by superuser', 'tenant-2', 'superuser')
                RETURNING id
            """
            )
        )
        new_resource_id = result.scalar()

        # Update any resource
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_perm_resource
                SET description = 'Updated by superuser'
                WHERE tenant_id = 'tenant-2'
            """
            )
        )
        assert result.rowcount > 0  # At least one row should be updated

        # Delete any resource
        result = await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_perm_resource 
                WHERE id = (
                    SELECT id FROM {test_schema}.test_perm_resource
                    WHERE tenant_id = 'tenant-2'
                    LIMIT 1
                )
            """
            )
        )
        assert result.rowcount == 1  # One row should be deleted

        # Verify changes
        await session.commit()

        # Clear context variables for other tests
        await session.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_cross_tenant_isolation(test_schema, test_data):
    """Test isolation between tenants with RBAC and RLS."""
    async with async_session() as session:
        # Set permission context for tenant 1 admin
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-1"},
        )

        # Count tenant 1 resources
        result = await session.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_perm_resource")
        )
        tenant1_count = result.scalar()

        # Set permission context for tenant 2 admin
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-4"},
        )

        # Count tenant 2 resources
        result = await session.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_perm_resource")
        )
        tenant2_count = result.scalar()

        # Should see different resources
        assert tenant1_count != tenant2_count

        # Try to access tenant 1 resources from tenant 2 (should fail)
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_perm_resource
                SET description = 'Cross-tenant update should fail'
                WHERE tenant_id = 'tenant-1'
            """
            )
        )
        assert result.rowcount == 0  # No rows should be updated

        # Clear context variables for other tests
        await session.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_permission_inheritance(test_schema, test_data):
    """Test permission inheritance through roles."""
    async with async_session() as session:
        # Create a new role with inherited permissions
        await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_role (id, name, description, tenant_id)
                VALUES ('custom-role', 'Custom Role', 'Role with inherited permissions', 'tenant-1')
            """
            )
        )

        # Inherit permissions from viewer role
        result = await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_role_permission (role_id, permission_id)
                SELECT 'custom-role', permission_id
                FROM {test_schema}.test_perm_role_permission
                WHERE role_id = 'viewer'
            """
            )
        )

        # Add custom-role to user-3
        await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_user_role (user_id, role_id)
                VALUES ('user-3', 'custom-role')
            """
            )
        )

        # Check that user-3 has all permissions from both roles
        result = await session.execute(
            text(f"SELECT * FROM test_perms.get_user_permissions(:user_id)"),
            {"user_id": "user-3"},
        )
        permissions = result.fetchall()

        # Should still have 4 SELECT permissions (duplicates are eliminated)
        assert len(permissions) == 4
        assert all(p[1] == "SELECT" for p in permissions)

        # Add INSERT permission to custom-role
        resource_insert_id = next(
            p_id
            for key, p_id in test_data["permissions"].items()
            if key == "resource:INSERT"
        )

        await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_role_permission (role_id, permission_id)
                VALUES ('custom-role', :permission_id)
            """
            ),
            {"permission_id": resource_insert_id},
        )

        # Check that user-3 now has INSERT permission
        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-3", "meta_type_id": "resource", "operation": "INSERT"},
        )
        assert result.scalar() is True

        # Set permission context and try to insert
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-3"},
        )

        # This should work now because the user has INSERT permission
        result = await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_resource 
                (name, description, tenant_id, owner_id)
                VALUES ('Viewer Resource', 'Created by viewer with custom role', 'tenant-1', 'user-3')
                RETURNING id
            """
            )
        )
        assert result.scalar() is not None

        # Verify changes
        await session.commit()

        # Clear context variables for other tests
        await session.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_permission_revocation(test_schema, test_data):
    """Test permission revocation."""
    async with async_session() as session:
        # First verify that user-2 (editor) has UPDATE permission
        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-2", "meta_type_id": "resource", "operation": "UPDATE"},
        )
        assert result.scalar() is True

        # Remove UPDATE permission from editor role
        resource_update_id = next(
            p_id
            for key, p_id in test_data["permissions"].items()
            if key == "resource:UPDATE"
        )

        await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_perm_role_permission
                WHERE role_id = 'editor' AND permission_id = :permission_id
            """
            ),
            {"permission_id": resource_update_id},
        )

        # Verify permission was revoked
        result = await session.execute(
            text(
                f"SELECT test_perms.check_permission(:user_id, :meta_type_id, :operation)"
            ),
            {"user_id": "user-2", "meta_type_id": "resource", "operation": "UPDATE"},
        )
        assert result.scalar() is False

        # Set permission context and try to update
        await session.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-2"},
        )

        # Get ID of a resource owned by user-2
        result = await session.execute(
            text(
                f"""
                SELECT id FROM {test_schema}.test_perm_resource
                WHERE owner_id = 'user-2'
                LIMIT 1
            """
            )
        )
        resource_id = result.scalar()

        # Try to update (should fail despite RLS allowing it, because permission was revoked)
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_perm_resource
                SET description = 'Should fail due to revoked permission'
                WHERE id = :id
            """
            ),
            {"id": resource_id},
        )
        assert result.rowcount == 0  # No rows should be updated

        # Verify changes
        await session.commit()

        # Clear context variables for other tests
        await session.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_session_persistence_and_isolation(test_schema, test_data):
    """Test persistence of permission context across operations and isolation between sessions."""
    # Create two independent sessions
    async with async_session() as session1, async_session() as session2:
        # Set different permission contexts in each session
        await session1.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-1"},  # Tenant 1 Admin
        )

        await session2.execute(
            text(f"SELECT test_perms.set_permission_context(:user_id)"),
            {"user_id": "user-4"},  # Tenant 2 Admin
        )

        # Count resources in each session
        result1 = await session1.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_perm_resource")
        )
        count1 = result1.scalar()

        result2 = await session2.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_perm_resource")
        )
        count2 = result2.scalar()

        # Counts should be different due to tenant isolation
        assert count1 != count2

        # Perform an operation in session1
        await session1.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_resource 
                (name, description, tenant_id, owner_id)
                VALUES ('Session1 Resource', 'Created in session 1', 'tenant-1', 'user-1')
            """
            )
        )

        # Perform an operation in session2
        await session2.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_resource 
                (name, description, tenant_id, owner_id)
                VALUES ('Session2 Resource', 'Created in session 2', 'tenant-2', 'user-4')
            """
            )
        )

        # Check that context is still correct in session1
        result = await session1.execute(
            text("SELECT current_setting('test_perms.tenant_id', TRUE)")
        )
        assert result.scalar() == "tenant-1"

        # Check that context is still correct in session2
        result = await session2.execute(
            text("SELECT current_setting('test_perms.tenant_id', TRUE)")
        )
        assert result.scalar() == "tenant-2"

        # Commit both sessions
        await session1.commit()
        await session2.commit()

        # Clear context variables in both sessions
        await session1.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )

        await session2.execute(
            text(
                """
            SET test_perms.user_id = '';
            SET test_perms.is_superuser = '';
            SET test_perms.is_tenant_admin = '';
            SET test_perms.tenant_id = '';
            SET test_perms.email = '';
        """
            )
        )


@pytest.mark.asyncio
async def test_grant_and_revoke_role(test_schema, test_data):
    """Test granting and revoking roles."""
    async with async_session() as session:
        # Get initial permissions for user-3 (viewer)
        result = await session.execute(
            text(f"SELECT * FROM test_perms.get_user_permissions(:user_id)"),
            {"user_id": "user-3"},
        )
        initial_permissions = result.fetchall()
        initial_permission_count = len(initial_permissions)

        # Grant editor role to user-3
        await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_perm_user_role (user_id, role_id)
                VALUES ('user-3', 'editor')
            """
            )
        )

        # Get updated permissions
        result = await session.execute(
            text(f"SELECT * FROM test_perms.get_user_permissions(:user_id)"),
            {"user_id": "user-3"},
        )
        updated_permissions = result.fetchall()

        # Should have more permissions now
        assert len(updated_permissions) > initial_permission_count

        # Specifically, should now have INSERT and UPDATE permissions
        operations = [p[1] for p in updated_permissions if p[0] == "resource"]
        assert "INSERT" in operations
        assert "UPDATE" in operations

        # Revoke editor role
        await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_perm_user_role
                WHERE user_id = 'user-3' AND role_id = 'editor'
            """
            )
        )

        # Check permissions again
        result = await session.execute(
            text(f"SELECT * FROM test_perms.get_user_permissions(:user_id)"),
            {"user_id": "user-3"},
        )
        final_permissions = result.fetchall()

        # Should be back to original permissions
        assert len(final_permissions) == initial_permission_count

        # Verify changes
        await session.commit()
