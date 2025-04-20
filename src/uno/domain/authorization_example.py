"""
Example usage of the advanced authorization system.

This module demonstrates how to use the authorization system,
including RBAC and multi-tenant authorization.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from uno.domain.application_services import ServiceContext
from uno.domain.authorization import (
    AuthorizationPolicy,
    AuthorizationService,
    CompositePolicy,
    OwnershipPolicy,
    Permission,
    Role,
    SimplePolicy,
    TenantPolicy,
    get_authorization_service,
)
from uno.domain.models import AggregateRoot, Entity
from uno.domain.multi_tenant import (
    MultiTenantAuthorizationService,
    Tenant,
    TenantRbacService,
    get_multi_tenant_auth_service,
)
from uno.domain.rbac import RbacService, User, get_rbac_service

# Sample domain model


@dataclass
class Product(Entity):
    """Product entity."""

    name: str
    price: float
    owner_id: str
    tenant_id: str
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(datetime.UTC))
    updated_at: Optional[datetime] = None


@dataclass
class Order(AggregateRoot):
    """Order aggregate root."""

    customer_id: str
    products: List[str]
    total: float
    owner_id: str
    tenant_id: str
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(datetime.UTC))
    updated_at: Optional[datetime] = None


# Basic authorization example


async def basic_authorization_example():
    """Example of basic authorization with policies."""
    print("\n=== Basic Authorization Example ===\n")

    # Get the authorization service
    auth_service = get_authorization_service()

    # Create policies
    product_read_policy = SimplePolicy("products", "read")
    product_write_policy = OwnershipPolicy("products", "write", "owner_id")

    # Register policies
    auth_service.register_policy(product_read_policy)
    auth_service.register_policy(product_write_policy)

    # Create service contexts
    admin_context = ServiceContext(
        user_id="admin",
        is_authenticated=True,
        permissions=["products:read", "products:write", "orders:*"],
    )

    user_context = ServiceContext(
        user_id="user1", is_authenticated=True, permissions=["products:read"]
    )

    # Create sample product
    product = Product(
        id="prod-1",
        name="Sample Product",
        price=99.99,
        owner_id="admin",
        tenant_id="tenant1",
    )

    # Check authorization
    print("Admin Context:")
    print(
        f"  Can read products: {await auth_service.authorize(admin_context, 'products', 'read')}"
    )
    print(
        f"  Can write products: {await auth_service.authorize(admin_context, 'products', 'write', product)}"
    )
    print(
        f"  Can delete products: {await auth_service.authorize(admin_context, 'products', 'delete')}"
    )

    print("\nUser Context:")
    print(
        f"  Can read products: {await auth_service.authorize(user_context, 'products', 'read')}"
    )
    print(
        f"  Can write products: {await auth_service.authorize(user_context, 'products', 'write', product)}"
    )

    # Create product owned by user1
    user_product = Product(
        id="prod-2",
        name="User Product",
        price=49.99,
        owner_id="user1",
        tenant_id="tenant1",
    )

    print(
        f"  Can write own products: {await auth_service.authorize(user_context, 'products', 'write', user_product)}"
    )


# RBAC example


async def rbac_example():
    """Example of role-based access control."""
    print("\n=== RBAC Example ===\n")

    # Get the RBAC service
    rbac_service = get_rbac_service()

    # Create roles
    admin_role = rbac_service.create_role(
        "admin",
        [
            "products:read",
            "products:write",
            "products:delete",
            "orders:read",
            "orders:write",
            "orders:delete",
        ],
    )

    manager_role = rbac_service.create_role(
        "manager", ["products:read", "products:write", "orders:read", "orders:write"]
    )

    user_role = rbac_service.create_role("user", ["products:read", "orders:read"])

    # Create users
    admin_user = rbac_service.create_user("admin", ["admin"])
    manager_user = rbac_service.create_user("manager", ["manager"])
    user1 = rbac_service.create_user("user1", ["user"])
    user2 = rbac_service.create_user(
        "user2", ["user"], ["orders:write"]
    )  # User with extra permission

    # Check permissions
    print("Admin User:")
    print(f"  Has admin role: {admin_user.has_role('admin')}")
    print(
        f"  Can read products: {rbac_service.has_permission('admin', 'products:read')}"
    )
    print(
        f"  Can write products: {rbac_service.has_permission('admin', 'products:write')}"
    )
    print(
        f"  Can delete products: {rbac_service.has_permission('admin', 'products:delete')}"
    )

    print("\nManager User:")
    print(f"  Has manager role: {manager_user.has_role('manager')}")
    print(
        f"  Can read products: {rbac_service.has_permission('manager', 'products:read')}"
    )
    print(
        f"  Can write products: {rbac_service.has_permission('manager', 'products:write')}"
    )
    print(
        f"  Can delete products: {rbac_service.has_permission('manager', 'products:delete')}"
    )

    print("\nRegular User:")
    print(f"  Has user role: {user1.has_role('user')}")
    print(
        f"  Can read products: {rbac_service.has_permission('user1', 'products:read')}"
    )
    print(
        f"  Can write products: {rbac_service.has_permission('user1', 'products:write')}"
    )

    print("\nUser with Extra Permission:")
    print(f"  Has user role: {user2.has_role('user')}")
    print(
        f"  Can read products: {rbac_service.has_permission('user2', 'products:read')}"
    )
    print(f"  Can write orders: {rbac_service.has_permission('user2', 'orders:write')}")

    # Create service contexts
    admin_context = rbac_service.create_service_context("admin")
    manager_context = rbac_service.create_service_context("manager")
    user_context = rbac_service.create_service_context("user1")

    # Get the authorization service
    auth_service = get_authorization_service()

    # Create policies
    product_read_policy = SimplePolicy("products", "read")
    product_write_policy = OwnershipPolicy("products", "write", "owner_id")

    # Register policies
    auth_service.register_policy(product_read_policy)
    auth_service.register_policy(product_write_policy)

    # Create sample product
    product = Product(
        id="prod-1",
        name="Sample Product",
        price=99.99,
        owner_id="admin",
        tenant_id="tenant1",
    )

    # Check authorization
    print("\nAdmin Context Authorization:")
    print(
        f"  Can read products: {await auth_service.authorize(admin_context, 'products', 'read')}"
    )
    print(
        f"  Can write products: {await auth_service.authorize(admin_context, 'products', 'write', product)}"
    )
    print(
        f"  Can delete products: {await auth_service.authorize(admin_context, 'products', 'delete')}"
    )

    print("\nManager Context Authorization:")
    print(
        f"  Can read products: {await auth_service.authorize(manager_context, 'products', 'read')}"
    )
    print(
        f"  Can write products: {await auth_service.authorize(manager_context, 'products', 'write', product)}"
    )
    print(
        f"  Can delete products: {await auth_service.authorize(manager_context, 'products', 'delete')}"
    )

    print("\nUser Context Authorization:")
    print(
        f"  Can read products: {await auth_service.authorize(user_context, 'products', 'read')}"
    )
    print(
        f"  Can write products: {await auth_service.authorize(user_context, 'products', 'write', product)}"
    )


# Multi-tenant example


async def multi_tenant_example():
    """Example of multi-tenant authorization."""
    print("\n=== Multi-Tenant Example ===\n")

    # Get the multi-tenant authorization service
    mt_auth_service = get_multi_tenant_auth_service()

    # Get the tenant RBAC service
    tenant_rbac = mt_auth_service.rbac_service

    # Create tenants
    tenant1 = tenant_rbac.create_tenant("tenant1", "Tenant 1")
    tenant2 = tenant_rbac.create_tenant("tenant2", "Tenant 2")

    # Create global roles
    tenant_rbac.create_role(
        "global_admin",
        [
            "products:read",
            "products:write",
            "products:delete",
            "orders:read",
            "orders:write",
            "orders:delete",
            "tenants:read",
            "tenants:write",
            "users:*",
        ],
    )

    # Create tenant-specific roles
    tenant_rbac.create_role(
        "tenant_admin",
        [
            "products:read",
            "products:write",
            "products:delete",
            "orders:read",
            "orders:write",
            "orders:delete",
        ],
        "tenant1",
    )

    tenant_rbac.create_role(
        "tenant_admin",
        [
            "products:read",
            "products:write",
            "products:delete",
            "orders:read",
            "orders:write",
            "orders:delete",
        ],
        "tenant2",
    )

    tenant_rbac.create_role("tenant_user", ["products:read", "orders:read"], "tenant1")

    tenant_rbac.create_role("tenant_user", ["products:read", "orders:read"], "tenant2")

    # Create global user (system admin)
    tenant_rbac.create_user("global_admin", ["global_admin"])

    # Create tenant-specific users
    tenant_rbac.create_user("tenant1_admin", ["tenant_admin"], tenant_id="tenant1")
    tenant_rbac.create_user("tenant1_user", ["tenant_user"], tenant_id="tenant1")
    tenant_rbac.create_user("tenant2_admin", ["tenant_admin"], tenant_id="tenant2")
    tenant_rbac.create_user("tenant2_user", ["tenant_user"], tenant_id="tenant2")

    # Create multi-tenant user (user in both tenants)
    tenant_rbac.create_user("multi_tenant_user", ["tenant_user"], tenant_id="tenant1")
    tenant_rbac.add_user_to_tenant("multi_tenant_user", "tenant2", ["tenant_user"])

    # Register policies
    mt_auth_service.register_tenant_isolation_policy("products", "read", "tenant1")
    mt_auth_service.register_tenant_isolation_policy("products", "write", "tenant1")
    mt_auth_service.register_tenant_isolation_policy("products", "read", "tenant2")
    mt_auth_service.register_tenant_isolation_policy("products", "write", "tenant2")

    # Create sample products
    product_tenant1 = Product(
        id="prod-t1",
        name="Tenant 1 Product",
        price=99.99,
        owner_id="tenant1_admin",
        tenant_id="tenant1",
    )

    product_tenant2 = Product(
        id="prod-t2",
        name="Tenant 2 Product",
        price=149.99,
        owner_id="tenant2_admin",
        tenant_id="tenant2",
    )

    # Check authorization
    print("Global Admin:")
    global_admin_context = tenant_rbac.create_service_context("global_admin")
    print(
        f"  Can access tenant1 product: {await mt_auth_service.authorize(global_admin_context, 'products', 'read', product_tenant1)}"
    )
    print(
        f"  Can access tenant2 product: {await mt_auth_service.authorize(global_admin_context, 'products', 'read', product_tenant2)}"
    )

    print("\nTenant 1 Admin:")
    tenant1_admin_context = tenant_rbac.create_service_context(
        "tenant1_admin", "tenant1"
    )
    print(
        f"  Can access tenant1 product: {await mt_auth_service.authorize(tenant1_admin_context, 'products', 'read', product_tenant1)}"
    )
    print(
        f"  Can access tenant2 product: {await mt_auth_service.authorize(tenant1_admin_context, 'products', 'read', product_tenant2)}"
    )

    print("\nTenant 2 Admin:")
    tenant2_admin_context = tenant_rbac.create_service_context(
        "tenant2_admin", "tenant2"
    )
    print(
        f"  Can access tenant1 product: {await mt_auth_service.authorize(tenant2_admin_context, 'products', 'read', product_tenant1)}"
    )
    print(
        f"  Can access tenant2 product: {await mt_auth_service.authorize(tenant2_admin_context, 'products', 'read', product_tenant2)}"
    )

    print("\nMulti-Tenant User:")
    # Check in tenant 1 context
    mt_user_context1 = tenant_rbac.create_service_context(
        "multi_tenant_user", "tenant1"
    )
    print(
        f"  In tenant1 context, can access tenant1 product: {await mt_auth_service.authorize(mt_user_context1, 'products', 'read', product_tenant1)}"
    )
    print(
        f"  In tenant1 context, can access tenant2 product: {await mt_auth_service.authorize(mt_user_context1, 'products', 'read', product_tenant2)}"
    )

    # Check in tenant 2 context
    mt_user_context2 = tenant_rbac.create_service_context(
        "multi_tenant_user", "tenant2"
    )
    print(
        f"  In tenant2 context, can access tenant1 product: {await mt_auth_service.authorize(mt_user_context2, 'products', 'read', product_tenant1)}"
    )
    print(
        f"  In tenant2 context, can access tenant2 product: {await mt_auth_service.authorize(mt_user_context2, 'products', 'read', product_tenant2)}"
    )


# Integration with application services


class ExampleServiceContext(ServiceContext):
    """Extended service context for the example."""

    @classmethod
    def from_rbac(
        cls, user_id: str, rbac_service: RbacService
    ) -> "ExampleServiceContext":
        """Create a service context from RBAC information."""
        user = rbac_service.get_user(user_id)
        if not user:
            return cls.create_anonymous()

        permissions = rbac_service.get_user_permissions(user_id)

        return cls(user_id=user_id, is_authenticated=True, permissions=permissions)

    @classmethod
    def from_tenant_rbac(
        cls, user_id: str, tenant_id: str, rbac_service: TenantRbacService
    ) -> "ExampleServiceContext":
        """Create a service context from tenant RBAC information."""
        return rbac_service.create_service_context(user_id, tenant_id)


async def application_integration_example():
    """Example of integrating authorization with application services."""
    print("\n=== Application Integration Example ===\n")

    # Create RBAC setup
    rbac_service = get_rbac_service()

    # Create roles
    rbac_service.create_role(
        "admin",
        [
            "products:read",
            "products:write",
            "products:delete",
            "orders:read",
            "orders:write",
            "orders:delete",
        ],
    )

    rbac_service.create_role("user", ["products:read", "orders:read"])

    # Create users
    rbac_service.create_user("admin", ["admin"])
    rbac_service.create_user("user", ["user"])

    # Create service contexts
    admin_context = ExampleServiceContext.from_rbac("admin", rbac_service)
    user_context = ExampleServiceContext.from_rbac("user", rbac_service)

    # Create auth service and policies
    auth_service = get_authorization_service()
    auth_service.register_policy(SimplePolicy("products", "read"))
    auth_service.register_policy(OwnershipPolicy("products", "write", "owner_id"))

    # Create products
    admin_product = Product(
        id="admin-prod",
        name="Admin Product",
        price=99.99,
        owner_id="admin",
        tenant_id="default",
    )

    user_product = Product(
        id="user-prod",
        name="User Product",
        price=49.99,
        owner_id="user",
        tenant_id="default",
    )

    # Simulate application service authorization
    print("Admin Authorization:")
    print(
        f"  Can read products: {await auth_service.authorize(admin_context, 'products', 'read')}"
    )
    print(
        f"  Can write own products: {await auth_service.authorize(admin_context, 'products', 'write', admin_product)}"
    )
    print(
        f"  Can write user products: {await auth_service.authorize(admin_context, 'products', 'write', user_product)}"
    )

    print("\nUser Authorization:")
    print(
        f"  Can read products: {await auth_service.authorize(user_context, 'products', 'read')}"
    )
    print(
        f"  Can write own products: {await auth_service.authorize(user_context, 'products', 'write', user_product)}"
    )
    print(
        f"  Can write admin products: {await auth_service.authorize(user_context, 'products', 'write', admin_product)}"
    )


async def run_examples():
    """Run all the examples."""
    await basic_authorization_example()
    await rbac_example()
    await multi_tenant_example()
    await application_integration_example()


if __name__ == "__main__":
    asyncio.run(run_examples())
