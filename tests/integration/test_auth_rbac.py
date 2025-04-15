"""
Integration tests for Role-Based Access Control (RBAC).

This module tests RBAC functionality including role assignment, permission checking,
and integration with database row-level security.
"""

import os
import pytest
import logging
import asyncio
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass, field

from sqlalchemy import text, Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends, APIRouter, HTTPException, Request
from fastapi.testclient import TestClient

from uno.domain.rbac import RbacService, User as RbacUser, Role
from uno.domain.authorization import (
    Permission,
    Role as AuthRole,
    AuthorizationService,
    ServiceContext,
    SimplePolicy,
    OwnershipPolicy,
    TenantPolicy,
)
from uno.database.session import async_session
from uno.database.schema_manager import SchemaManager
from uno.authorization.rlssql import (
    RowLevelSecurity,
    UserRowLevelSecurity,
    TenantRowLevelSecurity,
    AdminRowLevelSecurity,
    DefaultRowLevelSecurity,
    SuperuserRowLevelSecurity,
)
from uno.model import UnoModel
from uno.sql.emitter import SQLEmitter
from uno.sql.config import ConnectionConfig
from uno.enums import SQLOperation


# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration]


# Test models for RBAC and RLS testing
class TestTenant(UnoModel):
    """Test tenant model for RBAC tests."""

    __tablename__ = "test_tenants"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    active = Column(Boolean, default=True)


class TestUser(UnoModel):
    """Test user model for RBAC tests."""

    __tablename__ = "test_users"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    handle = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)
    is_tenant_admin = Column(Boolean, default=False)
    tenant_id = Column(String, ForeignKey("test_tenants.id"), nullable=True)


class TestResource(UnoModel):
    """Test resource model for RBAC and RLS tests."""

    __tablename__ = "test_resources"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tenant_id = Column(String, ForeignKey("test_tenants.id"), nullable=False)
    owner_id = Column(String, ForeignKey("test_users.id"), nullable=False)
    is_public = Column(Boolean, default=False)


class TestUserRole(UnoModel):
    """User-role association model for RBAC tests."""

    __tablename__ = "test_user_roles"
    __test__ = False  # Prevent pytest from collecting this model as a test

    user_id = Column(String, ForeignKey("test_users.id"), primary_key=True)
    role_id = Column(String, primary_key=True)


class TestRolePermission(UnoModel):
    """Role-permission association model for RBAC tests."""

    __tablename__ = "test_role_permissions"
    __test__ = False  # Prevent pytest from collecting this model as a test

    role_id = Column(String, primary_key=True)
    permission = Column(String, primary_key=True)


@pytest.fixture(scope="module")
async def schema_manager():
    """Create a schema manager for testing."""
    return SchemaManager()


@pytest.fixture(scope="module")
async def test_schema(schema_manager):
    """Create a test schema for RBAC tests."""
    async with async_session() as session:
        # Drop schema if it exists
        await session.execute(text("DROP SCHEMA IF EXISTS test_rbac CASCADE"))

        # Create schema
        await session.execute(text("CREATE SCHEMA test_rbac"))

        # Create tables in the schema
        for model in [
            TestTenant,
            TestUser,
            TestResource,
            TestUserRole,
            TestRolePermission,
        ]:
            model.__table__.schema = "test_rbac"
            await session.execute(text(schema_manager.create_table_sql(model)))

        # Create session variables for RLS
        await session.execute(
            text(
                """
            -- Create session variables for RLS
            DO $$
            BEGIN
                -- Check if the variables are already defined
                PERFORM 1 FROM pg_settings WHERE name = 'rls_var.user_id';
                IF NOT FOUND THEN
                    -- Set up RLS variables
                    PERFORM set_config('rls_var.user_id', '', false);
                    PERFORM set_config('rls_var.email', '', false);
                    PERFORM set_config('rls_var.tenant_id', '', false);
                    PERFORM set_config('rls_var.is_superuser', 'false', false);
                    PERFORM set_config('rls_var.is_tenant_admin', 'false', false);
                END IF;
            END $$;
        """
            )
        )

        # Create permissible_groups function
        await session.execute(
            text(
                """
            -- Create permissible_groups function
            CREATE OR REPLACE FUNCTION test_rbac.permissible_groups(table_name text, operation text)
            RETURNS text[] AS $$
            DECLARE
                user_id text;
                groups text[];
            BEGIN
                -- Get current user ID from session variable
                user_id := current_setting('rls_var.user_id', true);
                
                -- Placeholder function - in real implementation, this would query groups
                -- that have permissions for the given table and operation
                groups := ARRAY[]::text[];
                
                RETURN groups;
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
            )
        )

        await session.commit()

    # Return the schema name
    return "test_rbac"


@pytest.fixture(scope="module")
async def rls_setup(test_schema):
    """Set up Row-Level Security for test tables."""
    async with async_session() as session:
        # Create a connection config for the SQLEmitter
        config = ConnectionConfig(DB_NAME="uno_test", SCHEMA_NAME=test_schema)

        # Apply RLS to the TestResource table
        emitter = SQLEmitter(config=config, table=TestResource.__table__)

        # Enable RLS
        rls = RowLevelSecurity(config=config, table=TestResource.__table__)
        await session.execute(text(rls.enable_rls))

        # Apply default policies
        default_rls = DefaultRowLevelSecurity(
            config=config, table=TestResource.__table__
        )
        await session.execute(text(default_rls.select_policy))
        await session.execute(text(default_rls.insert_policy))
        await session.execute(text(default_rls.update_policy))
        await session.execute(text(default_rls.delete_policy))

        await session.commit()


@pytest.fixture
async def test_tenants():
    """Create test tenants for RBAC tests."""
    tenants = [
        {"id": "tenant-1", "name": "Tenant 1", "active": True},
        {"id": "tenant-2", "name": "Tenant 2", "active": True},
    ]

    async with async_session() as session:
        for tenant in tenants:
            await session.execute(
                text(
                    "INSERT INTO test_rbac.test_tenants (id, name, active) VALUES (:id, :name, :active)"
                ),
                tenant,
            )
        await session.commit()

    return tenants


@pytest.fixture
async def test_users(test_tenants):
    """Create test users for RBAC tests."""
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
            "email": "user@tenant1.com",
            "handle": "user1",
            "full_name": "Tenant 1 User",
            "is_superuser": False,
            "is_tenant_admin": False,
            "tenant_id": "tenant-1",
        },
        {
            "id": "user-3",
            "email": "admin@tenant2.com",
            "handle": "admin2",
            "full_name": "Tenant 2 Admin",
            "is_superuser": False,
            "is_tenant_admin": True,
            "tenant_id": "tenant-2",
        },
        {
            "id": "user-4",
            "email": "user@tenant2.com",
            "handle": "user2",
            "full_name": "Tenant 2 User",
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
        for user in users:
            await session.execute(
                text(
                    """
                    INSERT INTO test_rbac.test_users 
                    (id, email, handle, full_name, is_superuser, is_tenant_admin, tenant_id) 
                    VALUES (:id, :email, :handle, :full_name, :is_superuser, :is_tenant_admin, :tenant_id)
                """
                ),
                user,
            )
        await session.commit()

    return users


@pytest.fixture
async def test_roles():
    """Create test roles for RBAC tests."""
    roles = [
        {"id": "admin", "name": "Administrator"},
        {"id": "editor", "name": "Editor"},
        {"id": "viewer", "name": "Viewer"},
    ]

    return roles


@pytest.fixture
async def test_role_permissions(test_roles):
    """Create test role permissions for RBAC tests."""
    role_permissions = [
        # Admin role permissions
        {"role_id": "admin", "permission": "resource:create"},
        {"role_id": "admin", "permission": "resource:read"},
        {"role_id": "admin", "permission": "resource:update"},
        {"role_id": "admin", "permission": "resource:delete"},
        {"role_id": "admin", "permission": "user:read"},
        {"role_id": "admin", "permission": "user:update"},
        # Editor role permissions
        {"role_id": "editor", "permission": "resource:create"},
        {"role_id": "editor", "permission": "resource:read"},
        {"role_id": "editor", "permission": "resource:update"},
        # Viewer role permissions
        {"role_id": "viewer", "permission": "resource:read"},
    ]

    async with async_session() as session:
        for rp in role_permissions:
            await session.execute(
                text(
                    "INSERT INTO test_rbac.test_role_permissions (role_id, permission) VALUES (:role_id, :permission)"
                ),
                rp,
            )
        await session.commit()

    return role_permissions


@pytest.fixture
async def test_user_roles(test_users, test_roles):
    """Assign roles to test users."""
    user_roles = [
        {"user_id": "user-1", "role_id": "admin"},  # Tenant 1 Admin gets admin role
        {"user_id": "user-2", "role_id": "editor"},  # Tenant 1 User gets editor role
        {"user_id": "user-3", "role_id": "admin"},  # Tenant 2 Admin gets admin role
        {"user_id": "user-4", "role_id": "viewer"},  # Tenant 2 User gets viewer role
        {"user_id": "superuser", "role_id": "admin"},  # Superuser gets admin role
    ]

    async with async_session() as session:
        for ur in user_roles:
            await session.execute(
                text(
                    "INSERT INTO test_rbac.test_user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
                ),
                ur,
            )
        await session.commit()

    return user_roles


@pytest.fixture
async def test_resources(test_users):
    """Create test resources for RBAC and RLS tests."""
    resources = [
        {
            "name": "Resource 1",
            "description": "Owned by Tenant 1 Admin",
            "tenant_id": "tenant-1",
            "owner_id": "user-1",
            "is_public": False,
        },
        {
            "name": "Resource 2",
            "description": "Owned by Tenant 1 User",
            "tenant_id": "tenant-1",
            "owner_id": "user-2",
            "is_public": False,
        },
        {
            "name": "Resource 3",
            "description": "Owned by Tenant 2 Admin",
            "tenant_id": "tenant-2",
            "owner_id": "user-3",
            "is_public": False,
        },
        {
            "name": "Resource 4",
            "description": "Owned by Tenant 2 User",
            "tenant_id": "tenant-2",
            "owner_id": "user-4",
            "is_public": False,
        },
        {
            "name": "Public Resource",
            "description": "Public resource accessible to all",
            "tenant_id": "tenant-1",
            "owner_id": "user-1",
            "is_public": True,
        },
    ]

    # Only insert resources, don't use RLS yet
    async with async_session() as session:
        # Temporarily disable RLS for insertion
        await session.execute(text("SET rls_var.is_superuser = 'true'"))

        for i, resource in enumerate(resources, 1):
            await session.execute(
                text(
                    """
                    INSERT INTO test_rbac.test_resources 
                    (name, description, tenant_id, owner_id, is_public) 
                    VALUES (:name, :description, :tenant_id, :owner_id, :is_public)
                """
                ),
                resource,
            )

        # Reset RLS variables
        await session.execute(text("SET rls_var.is_superuser = 'false'"))
        await session.commit()

    return resources


@pytest.fixture
def rbac_service():
    """Create an RBAC service for testing."""
    rbac = RbacService()

    # Create roles with permissions
    rbac.create_role(
        "admin",
        [
            "resource:create",
            "resource:read",
            "resource:update",
            "resource:delete",
            "user:read",
            "user:update",
        ],
    )
    rbac.create_role("editor", ["resource:create", "resource:read", "resource:update"])
    rbac.create_role("viewer", ["resource:read"])

    # Create users with roles
    rbac.create_user("user-1", ["admin"])  # Tenant 1 Admin
    rbac.create_user("user-2", ["editor"])  # Tenant 1 User
    rbac.create_user("user-3", ["admin"])  # Tenant 2 Admin
    rbac.create_user("user-4", ["viewer"])  # Tenant 2 User
    rbac.create_user("superuser", ["admin"])  # Superuser

    return rbac


@pytest.fixture
def auth_service():
    """Create an authorization service for testing."""
    auth_service = AuthorizationService()

    # Register policies for resources
    auth_service.register_policy(SimplePolicy("resource", "read"))
    auth_service.register_policy(
        OwnershipPolicy("resource", "update", owner_field="owner_id")
    )
    auth_service.register_policy(
        TenantPolicy("resource", "delete", tenant_field="tenant_id")
    )

    return auth_service


@pytest.fixture
def test_api(rbac_service, auth_service):
    """Create a FastAPI test application with RBAC integration."""
    app = FastAPI()

    # Add middleware for setting RLS variables
    @app.middleware("http")
    async def rls_middleware(request: Request, call_next):
        """Middleware to set RLS variables based on the current user."""
        user_id = request.headers.get("X-User-ID")

        # If no user ID is provided, proceed without setting variables
        if not user_id:
            return await call_next(request)

        # Get user from RBAC service
        user = rbac_service.get_user(user_id)
        if not user:
            return await call_next(request)

        # Create service context
        context = rbac_service.create_service_context(user_id)

        # Set user info in request state for route handlers
        request.state.user_id = user_id
        request.state.context = context

        # Get additional user info (assuming you would get this from a database in a real app)
        is_superuser = user_id == "superuser"
        is_tenant_admin = user_id in ["user-1", "user-3"]
        tenant_id = (
            "tenant-1"
            if user_id in ["user-1", "user-2"]
            else ("tenant-2" if user_id in ["user-3", "user-4"] else None)
        )
        email = f"{user_id}@example.com"

        # Set RLS session variables in the database
        async with async_session() as session:
            await session.execute(text(f"SET rls_var.user_id = '{user_id}'"))
            await session.execute(text(f"SET rls_var.email = '{email}'"))
            await session.execute(text(f"SET rls_var.is_superuser = '{is_superuser}'"))
            await session.execute(
                text(f"SET rls_var.is_tenant_admin = '{is_tenant_admin}'")
            )
            if tenant_id:
                await session.execute(text(f"SET rls_var.tenant_id = '{tenant_id}'"))
            await session.commit()

        # Continue with the request
        response = await call_next(request)
        return response

    # Add routes for testing
    router = APIRouter()

    @router.get("/resources")
    async def list_resources():
        """List resources using RLS."""
        async with async_session() as session:
            result = await session.execute(
                text("SELECT * FROM test_rbac.test_resources")
            )
            resources = [dict(r) for r in result.mappings()]
            return {"resources": resources}

    @router.get("/resources/{resource_id}")
    async def get_resource(resource_id: int, request: Request):
        """Get a resource with RBAC check."""
        # Get service context
        if not hasattr(request.state, "context"):
            raise HTTPException(status_code=401, detail="Unauthorized")

        context = request.state.context

        # Authorize
        if not await auth_service.authorize(context, "resource", "read"):
            raise HTTPException(
                status_code=403, detail="Not authorized to read resources"
            )

        # Fetch resource (RLS will filter if not accessible)
        async with async_session() as session:
            result = await session.execute(
                text("SELECT * FROM test_rbac.test_resources WHERE id = :id"),
                {"id": resource_id},
            )
            resource = result.mappings().first()

            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")

            return {"resource": dict(resource)}

    @router.post("/resources")
    async def create_resource(resource: dict, request: Request):
        """Create a resource with RBAC check."""
        # Get service context
        if not hasattr(request.state, "context"):
            raise HTTPException(status_code=401, detail="Unauthorized")

        context = request.state.context

        # Authorize
        if not await auth_service.authorize(context, "resource", "create"):
            raise HTTPException(
                status_code=403, detail="Not authorized to create resources"
            )

        # Set owner ID and tenant ID
        resource["owner_id"] = request.state.user_id

        # Get tenant ID from RLS variables (would typically come from user record)
        tenant_id = None
        async with async_session() as session:
            result = await session.execute(
                text("SELECT current_setting('rls_var.tenant_id', true)")
            )
            tenant_id = result.scalar()

        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant ID not available")

        resource["tenant_id"] = tenant_id

        # Create resource (RLS will allow/deny based on policies)
        async with async_session() as session:
            try:
                result = await session.execute(
                    text(
                        """
                        INSERT INTO test_rbac.test_resources 
                        (name, description, tenant_id, owner_id, is_public) 
                        VALUES (:name, :description, :tenant_id, :owner_id, :is_public)
                        RETURNING id
                    """
                    ),
                    resource,
                )
                resource_id = result.scalar()
                await session.commit()

                return {"id": resource_id, "message": "Resource created"}
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Failed to create resource: {str(e)}"
                )

    @router.put("/resources/{resource_id}")
    async def update_resource(resource_id: int, updates: dict, request: Request):
        """Update a resource with RBAC check."""
        # Get service context
        if not hasattr(request.state, "context"):
            raise HTTPException(status_code=401, detail="Unauthorized")

        context = request.state.context

        # Fetch resource first (for ownership check)
        async with async_session() as session:
            result = await session.execute(
                text("SELECT * FROM test_rbac.test_resources WHERE id = :id"),
                {"id": resource_id},
            )
            resource = result.mappings().first()

            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")

            # Convert to dict for ownership check
            resource_dict = dict(resource)

        # Authorize with ownership check
        if not await auth_service.authorize(
            context, "resource", "update", resource_dict
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to update this resource"
            )

        # Update resource (RLS will allow/deny based on policies)
        async with async_session() as session:
            try:
                # Only allow updating name and description
                updates_filtered = {
                    k: v
                    for k, v in updates.items()
                    if k in ["name", "description", "is_public"]
                }

                # Build update SQL
                update_parts = [f"{k} = :{k}" for k in updates_filtered.keys()]
                if not update_parts:
                    return {"message": "No valid fields to update"}

                update_sql = f"""
                    UPDATE test_rbac.test_resources 
                    SET {', '.join(update_parts)}
                    WHERE id = :id
                """

                # Execute update
                params = {**updates_filtered, "id": resource_id}
                result = await session.execute(text(update_sql), params)
                await session.commit()

                if result.rowcount == 0:
                    raise HTTPException(
                        status_code=403, detail="Failed to update resource (RLS denied)"
                    )

                return {"message": "Resource updated"}
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Failed to update resource: {str(e)}"
                )

    @router.delete("/resources/{resource_id}")
    async def delete_resource(resource_id: int, request: Request):
        """Delete a resource with RBAC check."""
        # Get service context
        if not hasattr(request.state, "context"):
            raise HTTPException(status_code=401, detail="Unauthorized")

        context = request.state.context

        # Fetch resource first (for tenant check)
        async with async_session() as session:
            result = await session.execute(
                text("SELECT * FROM test_rbac.test_resources WHERE id = :id"),
                {"id": resource_id},
            )
            resource = result.mappings().first()

            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")

            # Convert to dict for tenant check
            resource_dict = dict(resource)

        # Authorize with tenant check
        if not await auth_service.authorize(
            context, "resource", "delete", resource_dict
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this resource"
            )

        # Delete resource (RLS will allow/deny based on policies)
        async with async_session() as session:
            try:
                result = await session.execute(
                    text("DELETE FROM test_rbac.test_resources WHERE id = :id"),
                    {"id": resource_id},
                )
                await session.commit()

                if result.rowcount == 0:
                    raise HTTPException(
                        status_code=403, detail="Failed to delete resource (RLS denied)"
                    )

                return {"message": "Resource deleted"}
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Failed to delete resource: {str(e)}"
                )

    @router.get("/users/me/permissions")
    async def get_my_permissions(request: Request):
        """Get current user's permissions."""
        # Get user ID from request
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")

        # Get user from RBAC service
        user = rbac_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user permissions
        permissions = rbac_service.get_user_permissions(user_id)

        return {"user_id": user_id, "permissions": permissions}

    app.include_router(router)

    return app


@pytest.fixture
def test_client(test_api):
    """Create a test client for the FastAPI application."""
    return TestClient(test_api)


class TestRbacService:
    """Tests for RBAC service functionality."""

    def test_role_creation(self, rbac_service):
        """Test role creation with permissions."""
        # Test an existing role
        role = rbac_service.get_role("admin")
        assert role is not None
        assert role.name == "admin"
        assert "resource:create" in [str(p) for p in role.permissions]
        assert "resource:read" in [str(p) for p in role.permissions]

        # Create a new role
        new_role = rbac_service.create_role("custom", ["custom:read", "custom:write"])
        assert new_role is not None
        assert new_role.name == "custom"
        assert "custom:read" in [str(p) for p in new_role.permissions]
        assert "custom:write" in [str(p) for p in new_role.permissions]

        # Get the created role
        retrieved_role = rbac_service.get_role("custom")
        assert retrieved_role is not None
        assert retrieved_role.name == "custom"
        assert "custom:read" in [str(p) for p in retrieved_role.permissions]

    def test_user_permissions(self, rbac_service):
        """Test user permission assignment and checking."""
        # Test an existing user
        user_1 = rbac_service.get_user("user-1")  # Tenant 1 Admin
        assert user_1 is not None
        assert user_1.has_role("admin")
        assert rbac_service.has_permission("user-1", "resource:read")
        assert rbac_service.has_permission("user-1", "resource:create")
        assert rbac_service.has_permission("user-1", "resource:update")
        assert rbac_service.has_permission("user-1", "resource:delete")

        # Test another user with different role
        user_4 = rbac_service.get_user("user-4")  # Tenant 2 User (viewer)
        assert user_4 is not None
        assert user_4.has_role("viewer")
        assert rbac_service.has_permission("user-4", "resource:read")
        assert not rbac_service.has_permission("user-4", "resource:create")
        assert not rbac_service.has_permission("user-4", "resource:update")
        assert not rbac_service.has_permission("user-4", "resource:delete")

    def test_role_modification(self, rbac_service):
        """Test role permission modifications."""
        # Add permission to role
        rbac_service.add_permission_to_role("viewer", "custom:read")

        # Check that viewer now has the new permission
        assert rbac_service.has_permission("user-4", "custom:read")

        # Remove permission
        rbac_service.remove_permission_from_role("viewer", "custom:read")

        # Check that permission was removed
        assert not rbac_service.has_permission("user-4", "custom:read")

    def test_user_role_assignment(self, rbac_service):
        """Test assigning and removing roles from users."""
        # Add editor role to user-4 (who is a viewer)
        rbac_service.add_role_to_user("user-4", "editor")

        # Check that user now has both roles
        user = rbac_service.get_user("user-4")
        assert "viewer" in user.roles
        assert "editor" in user.roles

        # Check that user now has editor permissions
        assert rbac_service.has_permission("user-4", "resource:create")
        assert rbac_service.has_permission("user-4", "resource:update")

        # Remove viewer role
        rbac_service.remove_role_from_user("user-4", "viewer")

        # Check that user no longer has viewer role but still has editor
        user = rbac_service.get_user("user-4")
        assert "viewer" not in user.roles
        assert "editor" in user.roles

        # Reset roles for other tests
        rbac_service.update_user("user-4", roles=["viewer"])

    def test_service_context_creation(self, rbac_service):
        """Test creation of service context with user permissions."""
        # Create service context for admin user
        context = rbac_service.create_service_context("user-1")
        assert context.user_id == "user-1"
        assert context.is_authenticated
        assert "resource:read" in context.permissions
        assert "resource:create" in context.permissions

        # Create service context for viewer user
        context = rbac_service.create_service_context("user-4")
        assert context.user_id == "user-4"
        assert context.is_authenticated
        assert "resource:read" in context.permissions
        assert "resource:create" not in context.permissions


@pytest.mark.asyncio
class TestDatabaseRowLevelSecurity:
    """Tests for Row-Level Security integration with the database."""

    async def test_superuser_access(self, rls_setup, test_resources):
        """Test that a superuser can access all resources."""
        async with async_session() as session:
            # Set superuser RLS variables
            await session.execute(text("SET rls_var.user_id = 'superuser'"))
            await session.execute(text("SET rls_var.email = 'superuser@system.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'true'"))

            # Query resources
            result = await session.execute(
                text("SELECT * FROM test_rbac.test_resources")
            )
            resources = list(result.mappings())

            # Superuser should see all 5 resources
            assert len(resources) == 5

    async def test_tenant_admin_access(self, rls_setup, test_resources):
        """Test that a tenant admin can access resources for their tenant."""
        async with async_session() as session:
            # Set tenant admin RLS variables for Tenant 1
            await session.execute(text("SET rls_var.user_id = 'user-1'"))
            await session.execute(text("SET rls_var.email = 'admin@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'true'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # Query resources
            result = await session.execute(
                text("SELECT * FROM test_rbac.test_resources")
            )
            resources = list(result.mappings())

            # Tenant 1 admin should see 3 resources (2 from tenant 1 + 1 public)
            assert len(resources) == 3
            tenant_ids = [r["tenant_id"] for r in resources]
            assert all(tid == "tenant-1" for tid in tenant_ids)

    async def test_regular_user_access(self, rls_setup, test_resources):
        """Test that a regular user can access only resources they own."""
        async with async_session() as session:
            # Set regular user RLS variables for Tenant 1
            await session.execute(text("SET rls_var.user_id = 'user-2'"))
            await session.execute(text("SET rls_var.email = 'user@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'false'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # Query resources
            result = await session.execute(
                text("SELECT * FROM test_rbac.test_resources")
            )
            resources = list(result.mappings())

            # Regular user should see their own resources and public ones
            # In this case, 1 owned by them and 1 public
            owner_ids = [r["owner_id"] for r in resources]
            is_public = [r["is_public"] for r in resources]

            # Either it's owned by the user or it's public
            for i, owner in enumerate(owner_ids):
                assert owner == "user-2" or is_public[i] == True

    async def test_insert_permissions(self, rls_setup):
        """Test insert permissions with RLS."""
        async with async_session() as session:
            # Try inserting as tenant admin
            await session.execute(text("SET rls_var.user_id = 'user-1'"))
            await session.execute(text("SET rls_var.email = 'admin@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'true'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # Insert a resource
            await session.execute(
                text(
                    """
                    INSERT INTO test_rbac.test_resources 
                    (name, description, tenant_id, owner_id, is_public) 
                    VALUES ('Admin Resource', 'Created by admin', 'tenant-1', 'user-1', false)
                """
                )
            )
            await session.commit()

            # Try inserting as regular user
            await session.execute(text("SET rls_var.user_id = 'user-2'"))
            await session.execute(text("SET rls_var.email = 'user@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'false'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # Insert a resource (should be allowed since they're setting themselves as owner)
            await session.execute(
                text(
                    """
                    INSERT INTO test_rbac.test_resources 
                    (name, description, tenant_id, owner_id, is_public) 
                    VALUES ('User Resource', 'Created by user', 'tenant-1', 'user-2', false)
                """
                )
            )
            await session.commit()

            # Try inserting for another tenant (should fail)
            with pytest.raises(Exception):
                await session.execute(
                    text(
                        """
                        INSERT INTO test_rbac.test_resources 
                        (name, description, tenant_id, owner_id, is_public) 
                        VALUES ('Invalid Resource', 'Wrong tenant', 'tenant-2', 'user-2', false)
                    """
                    )
                )
                await session.commit()

    async def test_update_permissions(self, rls_setup, test_resources):
        """Test update permissions with RLS."""
        async with async_session() as session:
            # Get ID of a resource owned by user-2
            await session.execute(text("SET rls_var.is_superuser = 'true'"))
            result = await session.execute(
                text(
                    "SELECT id FROM test_rbac.test_resources WHERE owner_id = 'user-2' LIMIT 1"
                )
            )
            resource_id = result.scalar()

            # Try updating as the owner
            await session.execute(text("SET rls_var.user_id = 'user-2'"))
            await session.execute(text("SET rls_var.email = 'user@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'false'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # Update should succeed (owner can update their own resource)
            await session.execute(
                text(
                    """
                    UPDATE test_rbac.test_resources 
                    SET description = 'Updated by owner'
                    WHERE id = :id
                """
                ),
                {"id": resource_id},
            )
            await session.commit()

            # Get ID of a resource owned by user-1
            await session.execute(text("SET rls_var.is_superuser = 'true'"))
            result = await session.execute(
                text(
                    "SELECT id FROM test_rbac.test_resources WHERE owner_id = 'user-1' LIMIT 1"
                )
            )
            admin_resource_id = result.scalar()

            # Try updating as a non-owner regular user
            await session.execute(text("SET rls_var.user_id = 'user-2'"))
            await session.execute(text("SET rls_var.email = 'user@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'false'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # This should update 0 rows (RLS prevents update)
            result = await session.execute(
                text(
                    """
                    UPDATE test_rbac.test_resources 
                    SET description = 'Update by non-owner'
                    WHERE id = :id
                """
                ),
                {"id": admin_resource_id},
            )
            await session.commit()
            assert result.rowcount == 0  # No rows updated due to RLS

    async def test_delete_permissions(self, rls_setup, test_resources):
        """Test delete permissions with RLS."""
        async with async_session() as session:
            # Create a test resource to delete
            await session.execute(text("SET rls_var.is_superuser = 'true'"))
            result = await session.execute(
                text(
                    """
                    INSERT INTO test_rbac.test_resources 
                    (name, description, tenant_id, owner_id, is_public) 
                    VALUES ('Delete Test', 'To be deleted', 'tenant-1', 'user-2', false)
                    RETURNING id
                """
                )
            )
            delete_resource_id = result.scalar()
            await session.commit()

            # Try deleting as a non-admin user (should fail)
            await session.execute(text("SET rls_var.user_id = 'user-2'"))
            await session.execute(text("SET rls_var.email = 'user@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'false'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # This should delete 0 rows (policy prevents delete for non-admin users)
            result = await session.execute(
                text("DELETE FROM test_rbac.test_resources WHERE id = :id"),
                {"id": delete_resource_id},
            )
            await session.commit()
            assert result.rowcount == 0  # No rows deleted due to RLS

            # Try deleting as a tenant admin (should succeed)
            await session.execute(text("SET rls_var.user_id = 'user-1'"))
            await session.execute(text("SET rls_var.email = 'admin@tenant1.com'"))
            await session.execute(text("SET rls_var.is_superuser = 'false'"))
            await session.execute(text("SET rls_var.is_tenant_admin = 'true'"))
            await session.execute(text("SET rls_var.tenant_id = 'tenant-1'"))

            # This should delete the resource (admin can delete)
            result = await session.execute(
                text("DELETE FROM test_rbac.test_resources WHERE id = :id"),
                {"id": delete_resource_id},
            )
            await session.commit()
            assert result.rowcount == 1  # One row deleted


class TestRbacApiIntegration:
    """Tests for RBAC integration with API endpoints."""

    def test_permissions_endpoint(self, test_client):
        """Test that users can get their permissions."""
        # Test as admin user
        response = test_client.get(
            "/users/me/permissions", headers={"X-User-ID": "user-1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-1"
        assert "resource:read" in data["permissions"]
        assert "resource:create" in data["permissions"]
        assert "resource:update" in data["permissions"]
        assert "resource:delete" in data["permissions"]

        # Test as viewer user
        response = test_client.get(
            "/users/me/permissions", headers={"X-User-ID": "user-4"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-4"
        assert "resource:read" in data["permissions"]
        assert "resource:create" not in data["permissions"]
        assert "resource:update" not in data["permissions"]
        assert "resource:delete" not in data["permissions"]

    def test_resource_listing_with_rls(self, test_client, test_resources):
        """Test that RLS is applied when listing resources."""
        # Test as superuser (should see all resources)
        response = test_client.get("/resources", headers={"X-User-ID": "superuser"})
        assert response.status_code == 200
        data = response.json()
        assert (
            len(data["resources"]) >= 5
        )  # Should see at least the 5 original resources

        # Test as tenant 1 admin (should see tenant 1 resources)
        response = test_client.get("/resources", headers={"X-User-ID": "user-1"})
        assert response.status_code == 200
        data = response.json()
        # Should see tenant 1 resources (including public ones)
        for resource in data["resources"]:
            assert resource["tenant_id"] == "tenant-1"

        # Test as tenant 2 user (should see only their resources and public ones)
        response = test_client.get("/resources", headers={"X-User-ID": "user-4"})
        assert response.status_code == 200
        data = response.json()
        for resource in data["resources"]:
            # Either owned by user or public
            assert resource["owner_id"] == "user-4" or resource["is_public"] == True

    def test_resource_creation_with_rbac(self, test_client):
        """Test that RBAC is applied when creating resources."""
        # Test as editor user (should be allowed to create)
        response = test_client.post(
            "/resources",
            headers={"X-User-ID": "user-2"},
            json={
                "name": "New Editor Resource",
                "description": "Created via API",
                "is_public": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Resource created"

        # Test as viewer user (should be denied)
        response = test_client.post(
            "/resources",
            headers={"X-User-ID": "user-4"},
            json={
                "name": "New Viewer Resource",
                "description": "Should fail",
                "is_public": False,
            },
        )
        assert response.status_code == 403
        assert "Not authorized to create resources" in response.json()["detail"]

    def test_resource_update_with_ownership_check(self, test_client, test_resources):
        """Test that ownership checks are applied when updating resources."""
        # First, get a resource owned by user-2
        response = test_client.get("/resources", headers={"X-User-ID": "user-2"})
        assert response.status_code == 200
        resources = response.json()["resources"]
        owned_resource = next((r for r in resources if r["owner_id"] == "user-2"), None)
        assert owned_resource is not None

        # Update as the owner (should succeed)
        response = test_client.put(
            f"/resources/{owned_resource['id']}",
            headers={"X-User-ID": "user-2"},
            json={"name": "Updated Resource", "description": "Updated via API"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Resource updated"

        # Get a resource not owned by user-2
        response = test_client.get("/resources", headers={"X-User-ID": "user-1"})
        assert response.status_code == 200
        resources = response.json()["resources"]
        admin_resource = next((r for r in resources if r["owner_id"] == "user-1"), None)
        assert admin_resource is not None

        # Try to update as non-owner (should fail)
        response = test_client.put(
            f"/resources/{admin_resource['id']}",
            headers={"X-User-ID": "user-2"},
            json={"name": "Unauthorized Update", "description": "Should fail"},
        )
        assert response.status_code == 403
        assert "Not authorized to update this resource" in response.json()["detail"]

    def test_resource_deletion_with_tenant_check(self, test_client, test_resources):
        """Test that tenant checks are applied when deleting resources."""
        # Create a resource to delete as admin
        response = test_client.post(
            "/resources",
            headers={"X-User-ID": "user-1"},
            json={
                "name": "Resource to Delete",
                "description": "Will be deleted",
                "is_public": False,
            },
        )
        assert response.status_code == 200
        resource_id = response.json()["id"]

        # Try to delete from another tenant (should fail)
        response = test_client.delete(
            f"/resources/{resource_id}",
            headers={"X-User-ID": "user-3"},  # Tenant 2 admin
        )
        assert response.status_code == 404  # Resource not found because of RLS

        # Delete as tenant admin (should succeed)
        response = test_client.delete(
            f"/resources/{resource_id}",
            headers={"X-User-ID": "user-1"},  # Tenant 1 admin
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Resource deleted"
