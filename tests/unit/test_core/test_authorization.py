"""
Tests for the advanced authorization system.

This module contains tests for the authorization system, including
policies, RBAC, and multi-tenant authorization.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

import pytest

from uno.domain.authorization import (
    Permission, Role, AuthorizationService, AuthorizationPolicy,
    SimplePolicy, OwnershipPolicy, TenantPolicy, CompositePolicy,
    get_authorization_service
)
from uno.domain.rbac import RbacService, User, get_rbac_service
from uno.domain.multi_tenant import (
    Tenant, TenantRbacService, MultiTenantAuthorizationService,
    get_multi_tenant_auth_service
)
from uno.domain.application_services import ServiceContext
from uno.domain.model import Entity, AggregateRoot
from uno.domain.exceptions import AuthorizationError


# Test domain model

@dataclass
class TestEntity(Entity):
    """Test entity for authorization tests."""
    
    name: str
    value: int = 0
    owner_id: str = "unknown"
    tenant_id: str = "default"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


@dataclass
class TestAggregate(AggregateRoot):
    """Test aggregate for authorization tests."""
    
    name: str
    items: List[str] = field(default_factory=list)
    owner_id: str = "unknown"
    tenant_id: str = "default"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# Authorization policy tests

@pytest.fixture
def auth_service():
    """Create a fresh authorization service for testing."""
    return AuthorizationService()


@pytest.fixture
def simple_context():
    """Create a simple service context for testing."""
    return ServiceContext(
        user_id="user1",
        is_authenticated=True,
        permissions=["entity:read", "entity:write"]
    )


@pytest.fixture
def admin_context():
    """Create an admin service context for testing."""
    return ServiceContext(
        user_id="admin",
        is_authenticated=True,
        permissions=["*:*"]  # Wildcard permission
    )


@pytest.fixture
def test_entity():
    """Create a test entity for testing."""
    return TestEntity(
        id="test-1",
        name="Test Entity",
        value=42,
        owner_id="user1",
        tenant_id="tenant1"
    )


@pytest.fixture
def admin_entity():
    """Create a test entity owned by admin for testing."""
    return TestEntity(
        id="admin-1",
        name="Admin Entity",
        value=100,
        owner_id="admin",
        tenant_id="tenant1"
    )


@pytest.mark.asyncio
async def test_simple_policy(auth_service, simple_context, admin_context):
    """Test SimplePolicy authorization."""
    # Create policy
    policy = SimplePolicy("entity", "read")
    
    # Register policy
    auth_service.register_policy(policy)
    
    # Test authorization
    assert await auth_service.authorize(simple_context, "entity", "read")
    assert await auth_service.authorize(admin_context, "entity", "read")
    assert not await auth_service.authorize(simple_context, "entity", "delete")  # No permission
    
    # Test authorize_or_raise
    await auth_service.authorize_or_raise(simple_context, "entity", "read")
    with pytest.raises(AuthorizationError):
        await auth_service.authorize_or_raise(simple_context, "entity", "delete")


@pytest.mark.asyncio
async def test_ownership_policy(auth_service, simple_context, admin_context, test_entity, admin_entity):
    """Test OwnershipPolicy authorization."""
    # Create policy
    policy = OwnershipPolicy("entity", "write", "owner_id")
    
    # Register policy
    auth_service.register_policy(policy)
    
    # Test authorization with ownership
    assert await auth_service.authorize(simple_context, "entity", "write", test_entity)  # User owns entity
    assert not await auth_service.authorize(simple_context, "entity", "write", admin_entity)  # User doesn't own entity
    assert await auth_service.authorize(admin_context, "entity", "write", admin_entity)  # Admin owns entity
    
    # Test with missing target
    assert not await auth_service.authorize(simple_context, "entity", "write")  # No target


@pytest.mark.asyncio
async def test_tenant_policy(auth_service, simple_context, test_entity):
    """Test TenantPolicy authorization."""
    # Create policy
    policy = TenantPolicy("entity", "read", "tenant_id")
    
    # Register policy
    auth_service.register_policy(policy)
    
    # Create tenant context
    tenant_context = ServiceContext(
        user_id="user1",
        tenant_id="tenant1",
        is_authenticated=True,
        permissions=["entity:read"]
    )
    
    other_tenant_context = ServiceContext(
        user_id="user2",
        tenant_id="tenant2",
        is_authenticated=True,
        permissions=["entity:read"]
    )
    
    # Test authorization with tenant isolation
    assert await auth_service.authorize(tenant_context, "entity", "read", test_entity)  # Same tenant
    assert not await auth_service.authorize(other_tenant_context, "entity", "read", test_entity)  # Different tenant
    
    # Test with missing target or tenant_id
    assert not await auth_service.authorize(tenant_context, "entity", "read")  # No target
    assert not await auth_service.authorize(simple_context, "entity", "read", test_entity)  # No tenant_id in context


@pytest.mark.asyncio
async def test_composite_policy(auth_service, simple_context, test_entity, admin_entity):
    """Test CompositePolicy authorization."""
    # Create policies
    read_policy = SimplePolicy("entity", "read")
    ownership_policy = OwnershipPolicy("entity", "write", "owner_id")
    
    # Create composite policy (ALL mode - both policies must pass)
    composite_all = CompositePolicy(
        "entity", "edit",
        [read_policy, ownership_policy],
        CompositePolicy.CombinationMode.ALL
    )
    
    # Create composite policy (ANY mode - any policy must pass)
    composite_any = CompositePolicy(
        "entity", "access",
        [read_policy, ownership_policy],
        CompositePolicy.CombinationMode.ANY
    )
    
    # Register policies
    auth_service.register_policy(composite_all)
    auth_service.register_policy(composite_any)
    
    # Test ALL mode
    assert await auth_service.authorize(simple_context, "entity", "edit", test_entity)  # Both pass
    assert not await auth_service.authorize(simple_context, "entity", "edit", admin_entity)  # Ownership fails
    
    # Update context to remove read permission
    no_read_context = ServiceContext(
        user_id="user1",
        is_authenticated=True,
        permissions=["entity:write"]
    )
    assert not await auth_service.authorize(no_read_context, "entity", "edit", test_entity)  # Read fails
    
    # Test ANY mode
    assert await auth_service.authorize(simple_context, "entity", "access", test_entity)  # Both pass
    assert await auth_service.authorize(simple_context, "entity", "access", admin_entity)  # Read passes
    assert await auth_service.authorize(no_read_context, "entity", "access", test_entity)  # Ownership passes
    
    # Create a context with no permissions
    no_perms_context = ServiceContext(
        user_id="user1",
        is_authenticated=True,
        permissions=[]
    )
    assert not await auth_service.authorize(no_perms_context, "entity", "access", test_entity)  # Both fail


# RBAC tests

@pytest.fixture
def rbac_service():
    """Create a fresh RBAC service for testing."""
    return RbacService()


def test_rbac_roles_and_permissions(rbac_service):
    """Test RBAC roles and permissions."""
    # Create roles
    admin_role = rbac_service.create_role("admin", [
        "entity:read", "entity:write", "entity:delete"
    ])
    
    user_role = rbac_service.create_role("user", [
        "entity:read"
    ])
    
    # Check role permissions
    assert admin_role.has_permission(Permission.from_string("entity:read"))
    assert admin_role.has_permission(Permission.from_string("entity:write"))
    assert admin_role.has_permission(Permission.from_string("entity:delete"))
    
    assert user_role.has_permission(Permission.from_string("entity:read"))
    assert not user_role.has_permission(Permission.from_string("entity:write"))
    
    # Add permission to role
    rbac_service.add_permission_to_role("user", "entity:write")
    user_role = rbac_service.get_role("user")
    assert user_role.has_permission(Permission.from_string("entity:write"))
    
    # Remove permission from role
    rbac_service.remove_permission_from_role("user", "entity:write")
    user_role = rbac_service.get_role("user")
    assert not user_role.has_permission(Permission.from_string("entity:write"))
    
    # Update role
    rbac_service.update_role("user", ["entity:read", "entity:write"])
    user_role = rbac_service.get_role("user")
    assert user_role.has_permission(Permission.from_string("entity:write"))
    
    # Delete role
    assert rbac_service.delete_role("user")
    assert rbac_service.get_role("user") is None


def test_rbac_users_and_roles(rbac_service):
    """Test RBAC users and roles."""
    # Create roles
    rbac_service.create_role("admin", [
        "entity:read", "entity:write", "entity:delete"
    ])
    
    rbac_service.create_role("user", [
        "entity:read"
    ])
    
    # Create users
    admin_user = rbac_service.create_user("admin", ["admin"])
    user1 = rbac_service.create_user("user1", ["user"])
    user2 = rbac_service.create_user("user2", ["user"], ["extra:permission"])
    
    # Check user roles
    assert admin_user.has_role("admin")
    assert user1.has_role("user")
    assert user2.has_role("user")
    
    # Check user permissions
    assert rbac_service.has_permission("admin", "entity:read")
    assert rbac_service.has_permission("admin", "entity:write")
    assert rbac_service.has_permission("admin", "entity:delete")
    
    assert rbac_service.has_permission("user1", "entity:read")
    assert not rbac_service.has_permission("user1", "entity:write")
    
    assert rbac_service.has_permission("user2", "entity:read")
    assert rbac_service.has_permission("user2", "extra:permission")
    
    # Add role to user
    rbac_service.add_role_to_user("user1", "admin")
    assert rbac_service.has_permission("user1", "entity:write")
    
    # Remove role from user
    rbac_service.remove_role_from_user("user1", "admin")
    assert not rbac_service.has_permission("user1", "entity:write")
    
    # Add direct permission to user
    rbac_service.add_permission_to_user("user1", "direct:permission")
    assert rbac_service.has_permission("user1", "direct:permission")
    
    # Remove direct permission from user
    rbac_service.remove_permission_from_user("user1", "direct:permission")
    assert not rbac_service.has_permission("user1", "direct:permission")
    
    # Update user
    rbac_service.update_user("user1", ["admin"], ["updated:permission"])
    assert rbac_service.has_permission("user1", "entity:write")  # From admin role
    assert rbac_service.has_permission("user1", "updated:permission")  # Direct permission
    
    # Delete user
    assert rbac_service.delete_user("user1")
    assert rbac_service.get_user("user1") is None


def test_rbac_service_context(rbac_service):
    """Test creating service context from RBAC."""
    # Create roles and users
    rbac_service.create_role("admin", [
        "entity:read", "entity:write", "entity:delete"
    ])
    
    rbac_service.create_user("admin", ["admin"])
    
    # Create service context
    context = rbac_service.create_service_context("admin")
    
    # Check context
    assert context.user_id == "admin"
    assert context.is_authenticated
    assert "entity:read" in context.permissions
    assert "entity:write" in context.permissions
    assert "entity:delete" in context.permissions
    
    # Try to create context for non-existent user
    with pytest.raises(ValueError):
        rbac_service.create_service_context("nonexistent")


@pytest.mark.asyncio
async def test_rbac_authorization_integration(rbac_service, auth_service, test_entity, admin_entity):
    """Test integration between RBAC and authorization service."""
    # Create roles
    rbac_service.create_role("admin", [
        "entity:read", "entity:write", "entity:delete"
    ])
    
    rbac_service.create_role("user", [
        "entity:read"
    ])
    
    # Create users
    rbac_service.create_user("admin", ["admin"])
    rbac_service.create_user("user1", ["user"])
    
    # Register policies
    auth_service.register_policy(SimplePolicy("entity", "read"))
    auth_service.register_policy(OwnershipPolicy("entity", "write", "owner_id"))
    
    # Create service contexts
    admin_context = rbac_service.create_service_context("admin")
    user_context = rbac_service.create_service_context("user1")
    
    # Test authorization
    assert await auth_service.authorize(admin_context, "entity", "read")
    assert await auth_service.authorize(admin_context, "entity", "write", admin_entity)
    assert await auth_service.authorize(admin_context, "entity", "delete")
    
    assert await auth_service.authorize(user_context, "entity", "read")
    assert not await auth_service.authorize(user_context, "entity", "write", admin_entity)  # Not owner
    assert await auth_service.authorize(user_context, "entity", "write", test_entity)  # Is owner
    assert not await auth_service.authorize(user_context, "entity", "delete")  # No permission


# Multi-tenant tests

@pytest.fixture
def tenant_rbac_service():
    """Create a fresh tenant RBAC service for testing."""
    return TenantRbacService()


@pytest.fixture
def mt_auth_service(tenant_rbac_service):
    """Create a fresh multi-tenant authorization service for testing."""
    return MultiTenantAuthorizationService(tenant_rbac_service)


def test_tenant_creation_and_management(tenant_rbac_service):
    """Test tenant creation and management."""
    # Create tenants
    tenant1 = tenant_rbac_service.create_tenant("tenant1", "Tenant 1")
    tenant2 = tenant_rbac_service.create_tenant("tenant2", "Tenant 2")
    
    # Check tenants
    assert tenant_rbac_service.get_tenant("tenant1") == tenant1
    assert tenant_rbac_service.get_tenant("tenant2") == tenant2
    
    # Update tenant
    tenant1 = tenant_rbac_service.update_tenant("tenant1", "Updated Tenant 1", False, {"key": "value"})
    assert tenant1.name == "Updated Tenant 1"
    assert not tenant1.active
    assert tenant1.metadata == {"key": "value"}
    
    # Delete tenant
    assert tenant_rbac_service.delete_tenant("tenant2")
    assert tenant_rbac_service.get_tenant("tenant2") is None


def test_tenant_specific_roles_and_users(tenant_rbac_service):
    """Test tenant-specific roles and users."""
    # Create tenants
    tenant_rbac_service.create_tenant("tenant1", "Tenant 1")
    tenant_rbac_service.create_tenant("tenant2", "Tenant 2")
    
    # Create global roles
    tenant_rbac_service.create_role("global_admin", [
        "entity:read", "entity:write", "entity:delete"
    ])
    
    # Create tenant-specific roles
    tenant_rbac_service.create_role("tenant_admin", [
        "entity:read", "entity:write", "entity:delete"
    ], "tenant1")
    
    tenant_rbac_service.create_role("tenant_user", [
        "entity:read"
    ], "tenant1")
    
    tenant_rbac_service.create_role("tenant_user", [
        "entity:read"
    ], "tenant2")
    
    # Create global user
    tenant_rbac_service.create_user("global_admin", ["global_admin"])
    
    # Create tenant-specific users
    tenant_rbac_service.create_user("tenant1_admin", ["tenant_admin"], tenant_id="tenant1")
    tenant_rbac_service.create_user("tenant1_user", ["tenant_user"], tenant_id="tenant1")
    tenant_rbac_service.create_user("tenant2_user", ["tenant_user"], tenant_id="tenant2")
    
    # Check roles
    assert tenant_rbac_service.get_role("global_admin") is not None
    assert tenant_rbac_service.get_role("tenant_admin", "tenant1") is not None
    assert tenant_rbac_service.get_role("tenant_user", "tenant1") is not None
    assert tenant_rbac_service.get_role("tenant_user", "tenant2") is not None
    
    # Check users
    assert tenant_rbac_service.get_user("global_admin") is not None
    assert tenant_rbac_service.get_user("tenant1_admin", "tenant1") is not None
    assert tenant_rbac_service.get_user("tenant1_user", "tenant1") is not None
    assert tenant_rbac_service.get_user("tenant2_user", "tenant2") is not None
    
    # Check permissions
    assert tenant_rbac_service.has_permission("global_admin", "entity:read")
    assert tenant_rbac_service.has_permission("tenant1_admin", "entity:write", "tenant1")
    assert tenant_rbac_service.has_permission("tenant1_user", "entity:read", "tenant1")
    assert not tenant_rbac_service.has_permission("tenant1_user", "entity:write", "tenant1")
    
    # Add a user to a tenant
    tenant_rbac_service.add_user_to_tenant("global_admin", "tenant1", ["tenant_admin"])
    assert tenant_rbac_service.get_user("global_admin", "tenant1") is not None
    assert tenant_rbac_service.has_permission("global_admin", "entity:write", "tenant1")
    
    # Get user tenants
    assert set(tenant_rbac_service.get_user_tenants("global_admin")) == {"tenant1"}
    
    # Remove user from tenant
    tenant_rbac_service.remove_user_from_tenant("global_admin", "tenant1")
    assert tenant_rbac_service.get_user("global_admin", "tenant1") is None
    assert tenant_rbac_service.get_user_tenants("global_admin") == []


def test_multi_tenant_user(tenant_rbac_service):
    """Test user in multiple tenants."""
    # Create tenants
    tenant_rbac_service.create_tenant("tenant1", "Tenant 1")
    tenant_rbac_service.create_tenant("tenant2", "Tenant 2")
    
    # Create tenant-specific roles
    tenant_rbac_service.create_role("tenant1_role", [
        "entity:read", "entity:write"
    ], "tenant1")
    
    tenant_rbac_service.create_role("tenant2_role", [
        "entity:read", "entity:delete"
    ], "tenant2")
    
    # Create multi-tenant user
    tenant_rbac_service.create_user("multi_user", ["tenant1_role"], tenant_id="tenant1")
    tenant_rbac_service.add_user_to_tenant("multi_user", "tenant2", ["tenant2_role"])
    
    # Check tenant memberships
    assert set(tenant_rbac_service.get_user_tenants("multi_user")) == {"tenant1", "tenant2"}
    
    # Check permissions in different tenants
    assert tenant_rbac_service.has_permission("multi_user", "entity:write", "tenant1")
    assert not tenant_rbac_service.has_permission("multi_user", "entity:delete", "tenant1")
    
    assert tenant_rbac_service.has_permission("multi_user", "entity:delete", "tenant2")
    assert not tenant_rbac_service.has_permission("multi_user", "entity:write", "tenant2")
    
    # Create service contexts for different tenants
    tenant1_context = tenant_rbac_service.create_service_context("multi_user", "tenant1")
    tenant2_context = tenant_rbac_service.create_service_context("multi_user", "tenant2")
    
    # Check context permissions
    assert "entity:write" in tenant1_context.permissions
    assert "entity:delete" not in tenant1_context.permissions
    
    assert "entity:delete" in tenant2_context.permissions
    assert "entity:write" not in tenant2_context.permissions


@pytest.mark.asyncio
async def test_multi_tenant_authorization(mt_auth_service, tenant_rbac_service, test_entity):
    """Test multi-tenant authorization."""
    # Create tenants
    tenant_rbac_service.create_tenant("tenant1", "Tenant 1")
    tenant_rbac_service.create_tenant("tenant2", "Tenant 2")
    
    # Create tenant-specific roles
    tenant_rbac_service.create_role("tenant_admin", [
        "entity:read", "entity:write", "entity:delete"
    ], "tenant1")
    
    tenant_rbac_service.create_role("tenant_user", [
        "entity:read"
    ], "tenant1")
    
    # Create tenant-specific users
    tenant_rbac_service.create_user("tenant1_admin", ["tenant_admin"], tenant_id="tenant1")
    tenant_rbac_service.create_user("tenant1_user", ["tenant_user"], tenant_id="tenant1")
    
    # Register tenant-specific policies
    mt_auth_service.register_tenant_isolation_policy("entity", "read", "tenant1")
    mt_auth_service.register_tenant_isolation_policy("entity", "write", "tenant1")
    
    # Create contexts
    admin_context = tenant_rbac_service.create_service_context("tenant1_admin", "tenant1")
    user_context = tenant_rbac_service.create_service_context("tenant1_user", "tenant1")
    
    # Create entity in tenant1
    tenant1_entity = TestEntity(
        id="t1-entity",
        name="Tenant 1 Entity",
        owner_id="tenant1_admin",
        tenant_id="tenant1"
    )
    
    # Create entity in tenant2
    tenant2_entity = TestEntity(
        id="t2-entity",
        name="Tenant 2 Entity",
        owner_id="tenant2_user",
        tenant_id="tenant2"
    )
    
    # Test authorization with tenant isolation
    assert await mt_auth_service.authorize(admin_context, "entity", "read", tenant1_entity)  # Same tenant
    assert not await mt_auth_service.authorize(admin_context, "entity", "read", tenant2_entity)  # Different tenant
    
    assert await mt_auth_service.authorize(user_context, "entity", "read", tenant1_entity)  # Has read permission
    assert not await mt_auth_service.authorize(user_context, "entity", "write", tenant1_entity)  # No write permission


if __name__ == "__main__":
    pytest.main(["-v", __file__])