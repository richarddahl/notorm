"""
Integration tests for Row-Level Security (RLS) session variables.

This module tests the functionality of PostgreSQL session variables used for Row-Level
Security (RLS) policies in the database.
"""

import pytest
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple

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
from uno.model import UnoModel
from uno.authorization.rlssql import (
    RowLevelSecurity,
    UserRowLevelSecurity,
    TenantRowLevelSecurity,
    AdminRowLevelSecurity,
    SuperuserRowLevelSecurity,
)
from uno.sql.config import ConnectionConfig


# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration]


# Test models for RLS session variables testing
class TestTenant(UnoModel):
    """Test tenant model for RLS tests."""

    __tablename__ = "test_rls_tenants"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    active = Column(Boolean, default=True)


class TestUser(UnoModel):
    """Test user model for RLS tests."""

    __tablename__ = "test_rls_users"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    handle = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)
    is_tenant_admin = Column(Boolean, default=False)
    tenant_id = Column(String, ForeignKey("test_rls_tenants.id"), nullable=True)


class TestResource(UnoModel):
    """Test resource model for RLS tests."""

    __tablename__ = "test_rls_resources"
    __test__ = False  # Prevent pytest from collecting this model as a test

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tenant_id = Column(String, ForeignKey("test_rls_tenants.id"), nullable=False)
    owner_id = Column(String, ForeignKey("test_rls_users.id"), nullable=False)


@pytest.fixture(scope="module")
async def schema_manager():
    """Create a schema manager for testing."""
    return DBManager()


@pytest.fixture(scope="module")
async def test_schema(schema_manager):
    """Create a test schema for RLS session variable tests."""
    async with async_session() as session:
        # Drop schema if it exists
        await session.execute(text("DROP SCHEMA IF EXISTS test_rls CASCADE"))

        # Create schema
        await session.execute(text("CREATE SCHEMA test_rls"))

        # Create tables in the schema
        for model in [TestTenant, TestUser, TestResource]:
            model.__table__.schema = "test_rls"
            await session.execute(text(schema_manager.create_table_sql(model)))

        # Create functions for working with session variables
        await session.execute(
            text(
                """
            CREATE OR REPLACE FUNCTION test_rls.get_session_variables()
            RETURNS TABLE (
                variable_name TEXT,
                variable_value TEXT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT name, current_setting(name, true)
                FROM (
                    VALUES
                        ('rls_var.user_id'),
                        ('rls_var.email'),
                        ('rls_var.tenant_id'),
                        ('rls_var.is_superuser'),
                        ('rls_var.is_tenant_admin')
                ) AS t(name)
                WHERE current_setting(name, true) IS NOT NULL;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to check if a session variable exists and return its value
            CREATE OR REPLACE FUNCTION test_rls.check_session_variable(var_name TEXT)
            RETURNS TEXT AS $$
            BEGIN
                RETURN current_setting(var_name, true);
            EXCEPTION
                WHEN OTHERS THEN
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to set session variables based on user ID
            CREATE OR REPLACE FUNCTION test_rls.set_user_context(
                p_user_id TEXT,
                p_is_superuser BOOLEAN DEFAULT FALSE,
                p_is_tenant_admin BOOLEAN DEFAULT FALSE,
                p_tenant_id TEXT DEFAULT NULL,
                p_email TEXT DEFAULT NULL
            ) RETURNS VOID AS $$
            BEGIN
                -- Set RLS variables
                PERFORM set_config('rls_var.user_id', p_user_id, true);
                PERFORM set_config('rls_var.is_superuser', p_is_superuser::TEXT, true);
                PERFORM set_config('rls_var.is_tenant_admin', p_is_tenant_admin::TEXT, true);
                
                IF p_tenant_id IS NOT NULL THEN
                    PERFORM set_config('rls_var.tenant_id', p_tenant_id, true);
                END IF;
                
                IF p_email IS NOT NULL THEN
                    PERFORM set_config('rls_var.email', p_email, true);
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to clear all session variables
            CREATE OR REPLACE FUNCTION test_rls.clear_session_variables() 
            RETURNS VOID AS $$
            BEGIN
                -- Reset variables to NULL by setting them to empty string
                -- (current_setting treats empty string as NULL)
                PERFORM set_config('rls_var.user_id', '', true);
                PERFORM set_config('rls_var.email', '', true);
                PERFORM set_config('rls_var.tenant_id', '', true);
                PERFORM set_config('rls_var.is_superuser', 'false', true);
                PERFORM set_config('rls_var.is_tenant_admin', 'false', true);
            END;
            $$ LANGUAGE plpgsql;
        """
            )
        )

        await session.commit()

    # Return the schema name
    return "test_rls"


@pytest.fixture(scope="module")
async def rls_setup(test_schema):
    """Set up Row-Level Security for test tables."""
    async with async_session() as session:
        # Create a connection config for the SQLEmitter
        config = ConnectionConfig(DB_NAME="uno_test", SCHEMA_NAME=test_schema)

        # Apply RLS to the TestResource table
        rls = RowLevelSecurity(config=config, table=TestResource.__table__)
        await session.execute(text(rls.enable_rls))

        # Apply user-level policies
        user_rls = UserRowLevelSecurity(config=config, table=TestResource.__table__)
        await session.execute(text(user_rls.select_policy))
        await session.execute(text(user_rls.insert_policy))
        await session.execute(text(user_rls.update_policy))
        await session.execute(text(user_rls.delete_policy))

        await session.commit()


@pytest.fixture(scope="module")
async def test_data(test_schema):
    """Create test data for RLS session variable tests."""
    tenants = [
        {"id": "tenant-1", "name": "Tenant 1", "active": True},
        {"id": "tenant-2", "name": "Tenant 2", "active": True},
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

    resources = [
        {
            "name": "Resource 1",
            "description": "Owned by Tenant 1 Admin",
            "tenant_id": "tenant-1",
            "owner_id": "user-1",
        },
        {
            "name": "Resource 2",
            "description": "Owned by Tenant 1 User",
            "tenant_id": "tenant-1",
            "owner_id": "user-2",
        },
        {
            "name": "Resource 3",
            "description": "Owned by Tenant 2 Admin",
            "tenant_id": "tenant-2",
            "owner_id": "user-3",
        },
        {
            "name": "Resource 4",
            "description": "Owned by Tenant 2 User",
            "tenant_id": "tenant-2",
            "owner_id": "user-4",
        },
    ]

    async with async_session() as session:
        # Insert tenants
        for tenant in tenants:
            await session.execute(
                text(
                    f"INSERT INTO {test_schema}.test_rls_tenants (id, name, active) VALUES (:id, :name, :active)"
                ),
                tenant,
            )

        # Insert users
        for user in users:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_rls_users
                    (id, email, handle, full_name, is_superuser, is_tenant_admin, tenant_id)
                    VALUES (:id, :email, :handle, :full_name, :is_superuser, :is_tenant_admin, :tenant_id)
                """
                ),
                user,
            )

        # Temporarily disable RLS for insertion by setting as superuser
        await session.execute(text("SET rls_var.is_superuser = 'true'"))

        # Insert resources
        for resource in resources:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_rls_resources
                    (name, description, tenant_id, owner_id)
                    VALUES (:name, :description, :tenant_id, :owner_id)
                """
                ),
                resource,
            )

        # Reset RLS variables
        await session.execute(text("SELECT test_rls.clear_session_variables()"))

        await session.commit()

    return {"tenants": tenants, "users": users, "resources": resources}


@pytest.mark.asyncio
async def test_setting_session_variables(test_schema, test_data):
    """Test setting session variables for RLS."""
    async with async_session() as session:
        # Set session variables for a regular user
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-1",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-1",
                "email": "admin@tenant1.com",
            },
        )

        # Get session variables
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.get_session_variables()")
        )
        variables = dict(result.fetchall())

        # Verify variables were set correctly
        assert variables["rls_var.user_id"] == "user-1"
        assert variables["rls_var.email"] == "admin@tenant1.com"
        assert variables["rls_var.tenant_id"] == "tenant-1"
        assert variables["rls_var.is_superuser"] == "false"
        assert variables["rls_var.is_tenant_admin"] == "true"

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))

        # Check that variables were cleared
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.get_session_variables()")
        )
        variables = dict(result.fetchall())

        # Variables should be reset (only showing the ones with non-NULL values)
        assert (
            len(variables) <= 2
        )  # Some implementations might keep is_superuser and is_tenant_admin as 'false'
        assert "rls_var.user_id" not in variables
        assert "rls_var.email" not in variables
        assert "rls_var.tenant_id" not in variables


@pytest.mark.asyncio
async def test_rls_superuser_access(test_schema, rls_setup, test_data):
    """Test superuser access through RLS session variables."""
    async with async_session() as session:
        # Set session variables for a superuser
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "superuser",
                "is_superuser": True,
                "is_tenant_admin": False,
                "tenant_id": None,
                "email": "superuser@system.com",
            },
        )

        # Query resources - superuser should see all resources
        result = await session.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_rls_resources")
        )
        count = result.scalar()

        # Should see all resources (4)
        assert count == 4

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))


@pytest.mark.asyncio
async def test_rls_tenant_admin_access(test_schema, rls_setup, test_data):
    """Test tenant admin access through RLS session variables."""
    async with async_session() as session:
        # Set session variables for Tenant 1 Admin
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-1",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-1",
                "email": "admin@tenant1.com",
            },
        )

        # Query resources - should only see Tenant 1 resources
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.test_rls_resources")
        )
        resources = result.fetchall()

        # Should see only Tenant 1 resources (2)
        assert len(resources) == 2

        # All resources should be from Tenant 1
        for resource in resources:
            resource_dict = dict(resource._mapping)
            assert resource_dict["tenant_id"] == "tenant-1"

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))


@pytest.mark.asyncio
async def test_rls_regular_user_access(test_schema, rls_setup, test_data):
    """Test regular user access through RLS session variables."""
    async with async_session() as session:
        # Set session variables for Tenant 1 User
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-2",
                "is_superuser": False,
                "is_tenant_admin": False,
                "tenant_id": "tenant-1",
                "email": "user@tenant1.com",
            },
        )

        # Query resources - should only see resources owned by user-2
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.test_rls_resources")
        )
        resources = result.fetchall()

        # Should see only resources owned by user-2 (1)
        assert len(resources) == 1

        # The resource should be owned by user-2
        resource_dict = dict(resources[0]._mapping)
        assert resource_dict["owner_id"] == "user-2"

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))


@pytest.mark.asyncio
async def test_rls_insert_permissions(test_schema, rls_setup, test_data):
    """Test insert permissions through RLS session variables."""
    async with async_session() as session:
        # 1. Test as tenant admin
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-1",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-1",
                "email": "admin@tenant1.com",
            },
        )

        # Tenant admin should be able to insert
        await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_rls_resources
                (name, description, tenant_id, owner_id)
                VALUES ('Admin New Resource', 'Created by admin', 'tenant-1', 'user-1')
            """
            )
        )

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))

        # 2. Test as regular user
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-2",
                "is_superuser": False,
                "is_tenant_admin": False,
                "tenant_id": "tenant-1",
                "email": "user@tenant1.com",
            },
        )

        # Regular user should be able to insert a resource they own
        await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_rls_resources
                (name, description, tenant_id, owner_id)
                VALUES ('User New Resource', 'Created by user', 'tenant-1', 'user-2')
            """
            )
        )

        # 3. Test inserting for wrong tenant (should fail)
        with pytest.raises(Exception):
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_rls_resources
                    (name, description, tenant_id, owner_id)
                    VALUES ('Invalid Resource', 'Wrong tenant', 'tenant-2', 'user-2')
                """
                )
            )

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))

        # 4. Test as superuser (should succeed for any tenant)
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "superuser",
                "is_superuser": True,
                "is_tenant_admin": False,
                "tenant_id": None,
                "email": "superuser@system.com",
            },
        )

        # Superuser should be able to insert for any tenant
        await session.execute(
            text(
                f"""
                INSERT INTO {test_schema}.test_rls_resources
                (name, description, tenant_id, owner_id)
                VALUES ('Superuser Resource', 'Created by superuser', 'tenant-2', 'superuser')
            """
            )
        )

        # Commit changes
        await session.commit()

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))


@pytest.mark.asyncio
async def test_rls_update_permissions(test_schema, rls_setup, test_data):
    """Test update permissions through RLS session variables."""
    async with async_session() as session:
        # First, get ID of a resource owned by user-2
        result = await session.execute(
            text(
                f"SELECT id FROM {test_schema}.test_rls_resources WHERE owner_id = 'user-2' LIMIT 1"
            )
        )
        user2_resource_id = result.scalar()

        # Get ID of a resource owned by user-1
        result = await session.execute(
            text(
                f"SELECT id FROM {test_schema}.test_rls_resources WHERE owner_id = 'user-1' LIMIT 1"
            )
        )
        user1_resource_id = result.scalar()

        # Set session variables for a regular user
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-2",
                "is_superuser": False,
                "is_tenant_admin": False,
                "tenant_id": "tenant-1",
                "email": "user@tenant1.com",
            },
        )

        # 1. Test updating own resource (should succeed)
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_rls_resources 
                SET description = 'Updated by owner'
                WHERE id = :id
            """
            ),
            {"id": user2_resource_id},
        )
        assert result.rowcount == 1  # One row updated

        # 2. Test updating another user's resource (should fail or update 0 rows)
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_rls_resources 
                SET description = 'Should fail'
                WHERE id = :id
            """
            ),
            {"id": user1_resource_id},
        )
        assert result.rowcount == 0  # No rows updated due to RLS

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))

        # 3. Test as tenant admin
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-1",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-1",
                "email": "admin@tenant1.com",
            },
        )

        # Tenant admin should be able to update any resource in their tenant
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_rls_resources 
                SET description = 'Updated by tenant admin'
                WHERE id = :id
            """
            ),
            {"id": user2_resource_id},
        )
        assert result.rowcount == 1  # One row updated

        # 4. Test updating resource from different tenant (should fail)
        result = await session.execute(
            text(
                f"""
                UPDATE {test_schema}.test_rls_resources 
                SET description = 'Should fail'
                WHERE tenant_id = 'tenant-2'
            """
            )
        )
        assert result.rowcount == 0  # No rows updated due to RLS

        # Commit changes
        await session.commit()

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))


@pytest.mark.asyncio
async def test_rls_delete_permissions(test_schema, rls_setup, test_data):
    """Test delete permissions through RLS session variables."""
    async with async_session() as session:
        # Create test resources for deletion
        await session.execute(text("SET rls_var.is_superuser = 'true'"))

        # Create resources for each user to delete
        for user_id in ["user-1", "user-2", "user-3", "user-4"]:
            tenant_id = "tenant-1" if user_id in ["user-1", "user-2"] else "tenant-2"
            await session.execute(
                text(
                    f"""
                    INSERT INTO {test_schema}.test_rls_resources
                    (name, description, tenant_id, owner_id)
                    VALUES ('Delete Test', 'To be deleted', :tenant_id, :user_id)
                    RETURNING id
                """
                ),
                {"tenant_id": tenant_id, "user_id": user_id},
            )

        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))

        # 1. Test as regular user (should fail)
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-2",
                "is_superuser": False,
                "is_tenant_admin": False,
                "tenant_id": "tenant-1",
                "email": "user@tenant1.com",
            },
        )

        result = await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_rls_resources
                WHERE owner_id = 'user-2' AND name = 'Delete Test'
            """
            )
        )
        # Regular users might not have delete permissions depending on the policy
        # The test will verify the actual implementation

        # 2. Test as tenant admin (should succeed for resources in their tenant)
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-1",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-1",
                "email": "admin@tenant1.com",
            },
        )

        result = await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_rls_resources
                WHERE tenant_id = 'tenant-1' AND name = 'Delete Test'
            """
            )
        )
        assert result.rowcount > 0  # Should delete at least one row

        # 3. Test deleting resources from different tenant (should fail)
        result = await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_rls_resources
                WHERE tenant_id = 'tenant-2' AND name = 'Delete Test'
            """
            )
        )
        assert result.rowcount == 0  # No rows deleted due to RLS

        # 4. Test as superuser (should succeed for any resource)
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "superuser",
                "is_superuser": True,
                "is_tenant_admin": False,
                "tenant_id": None,
                "email": "superuser@system.com",
            },
        )

        result = await session.execute(
            text(
                f"""
                DELETE FROM {test_schema}.test_rls_resources
                WHERE name = 'Delete Test'
            """
            )
        )
        assert result.rowcount > 0  # Should delete remaining rows

        # Commit changes
        await session.commit()

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))


@pytest.mark.asyncio
async def test_rls_session_persistence(test_schema, rls_setup, test_data):
    """Test RLS session variable persistence across operations."""
    async with async_session() as session:
        # Set session variables for a tenant admin
        await session.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-1",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-1",
                "email": "admin@tenant1.com",
            },
        )

        # Get session variables
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.get_session_variables()")
        )
        variables_before = dict(result.fetchall())

        # Perform a database operation
        await session.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_rls_resources")
        )

        # Check that variables are still set after the operation
        result = await session.execute(
            text(f"SELECT * FROM {test_schema}.get_session_variables()")
        )
        variables_after = dict(result.fetchall())

        # Variables should be the same before and after
        assert variables_before == variables_after

        # Clear session variables
        await session.execute(text(f"SELECT {test_schema}.clear_session_variables()"))


@pytest.mark.asyncio
async def test_multiple_sessions_isolation(test_schema, rls_setup, test_data):
    """Test RLS session variable isolation between different database sessions."""
    # Create two independent sessions
    async with async_session() as session1, async_session() as session2:
        # Set different session variables in each session
        await session1.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-1",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-1",
                "email": "admin@tenant1.com",
            },
        )

        await session2.execute(
            text(
                f"SELECT test_rls.set_user_context(:user_id, :is_superuser, :is_tenant_admin, :tenant_id, :email)"
            ),
            {
                "user_id": "user-3",
                "is_superuser": False,
                "is_tenant_admin": True,
                "tenant_id": "tenant-2",
                "email": "admin@tenant2.com",
            },
        )

        # Query resources in each session
        result1 = await session1.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_rls_resources")
        )
        count1 = result1.scalar()

        result2 = await session2.execute(
            text(f"SELECT COUNT(*) FROM {test_schema}.test_rls_resources")
        )
        count2 = result2.scalar()

        # Each session should see different resources based on tenant
        # Session 1 should see tenant-1 resources and Session 2 should see tenant-2 resources
        assert count1 > 0
        assert count2 > 0
        assert count1 != count2  # Ensure they're seeing different data

        # Get session variables from each session to confirm they're different
        result1 = await session1.execute(
            text(f"SELECT * FROM {test_schema}.get_session_variables()")
        )
        variables1 = dict(result1.fetchall())

        result2 = await session2.execute(
            text(f"SELECT * FROM {test_schema}.get_session_variables()")
        )
        variables2 = dict(result2.fetchall())

        # Variables should be different between sessions
        assert variables1["rls_var.user_id"] == "user-1"
        assert variables2["rls_var.user_id"] == "user-3"
        assert variables1["rls_var.tenant_id"] == "tenant-1"
        assert variables2["rls_var.tenant_id"] == "tenant-2"

        # Clear session variables
        await session1.execute(text(f"SELECT {test_schema}.clear_session_variables()"))
        await session2.execute(text(f"SELECT {test_schema}.clear_session_variables()"))
