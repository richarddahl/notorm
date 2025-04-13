"""
Performance benchmarks for the authorization module functionality.

These benchmarks measure the performance of authorization operations
under different conditions to help identify bottlenecks and
optimization opportunities.
"""

import pytest
import asyncio
import time
import uuid
import json
import random
from typing import Dict, List, Optional, Any, Tuple
from email_validator import validate_email

from uno.core.errors.result import Result, Success, Failure
from uno.enums import SQLOperation, TenantType
from uno.authorization.entities import (
    User,
    Group,
    Role,
    Permission,
    ResponsibilityRole,
    Tenant
)
from uno.authorization.domain_repositories import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    PermissionRepository,
    ResponsibilityRoleRepository,
    TenantRepository
)
from uno.authorization.domain_services import (
    UserService,
    GroupService,
    RoleService,
    PermissionService,
    ResponsibilityRoleService,
    TenantService
)
from uno.database.session import async_session
from uno.dependencies import get_service, register_service


# Skip these benchmarks in normal test runs
pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.skipif(
        "not config.getoption('--run-benchmark')",
        reason="Only run when --run-benchmark is specified"
    )
]


@pytest.fixture(scope="module")
async def db_session():
    """Create a database session."""
    async with async_session() as session:
        yield session


@pytest.fixture(scope="module")
async def authorization_services():
    """Create authorization services for benchmarking."""
    # Create repositories
    user_repo = UserRepository()
    group_repo = GroupRepository()
    role_repo = RoleRepository()
    permission_repo = PermissionRepository()
    responsibility_repo = ResponsibilityRoleRepository()
    tenant_repo = TenantRepository()
    
    # Create services
    tenant_service = TenantService(tenant_repo)
    register_service(TenantService, tenant_service)
    
    responsibility_service = ResponsibilityRoleService(responsibility_repo, tenant_service)
    register_service(ResponsibilityRoleService, responsibility_service)
    
    permission_service = PermissionService(permission_repo)
    register_service(PermissionService, permission_service)
    
    user_service = UserService(user_repo)
    register_service(UserService, user_service)
    
    group_service = GroupService(group_repo, user_service, tenant_service)
    register_service(GroupService, group_service)
    
    role_service = RoleService(
        role_repo, 
        user_service, 
        permission_service, 
        tenant_service, 
        responsibility_service
    )
    register_service(RoleService, role_service)
    
    # Update services with circular dependencies
    user_service.group_service = group_service
    user_service.role_service = role_service
    user_service.tenant_service = tenant_service
    
    services = {
        "user_service": user_service,
        "group_service": group_service,
        "role_service": role_service,
        "permission_service": permission_service,
        "responsibility_service": responsibility_service,
        "tenant_service": tenant_service,
    }
    
    yield services


@pytest.fixture(scope="module")
async def setup_benchmark_environment(db_session, authorization_services):
    """Set up the benchmark environment with test data."""
    user_service = authorization_services["user_service"]
    group_service = authorization_services["group_service"]
    role_service = authorization_services["role_service"]
    permission_service = authorization_services["permission_service"]
    responsibility_service = authorization_services["responsibility_service"]
    tenant_service = authorization_services["tenant_service"]
    
    # Create test data
    tenant_count = 5
    users_per_tenant = 20
    groups_per_tenant = 5
    roles_per_tenant = 10
    permissions_count = 30
    responsibility_per_tenant = 5
    
    created_entities = {
        "tenants": [],
        "users": [],
        "groups": [],
        "roles": [],
        "permissions": [],
        "responsibilities": [],
    }
    
    print(f"Setting up authorization benchmark environment...")
    
    # Create tenants
    for i in range(tenant_count):
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=f"Benchmark_Tenant_{i}",
            tenant_type=TenantType.ORGANIZATION if i % 2 == 0 else TenantType.INDIVIDUAL,
        )
        
        result = await tenant_service.create(tenant)
        if result.is_success:
            created_entities["tenants"].append(result.value)
    
    print(f"Created {len(created_entities['tenants'])} tenants")
    
    # Create permissions
    for i in range(permissions_count):
        permission = Permission(
            meta_type_id=f"meta_type_{i % 10}",
            operation=SQLOperation.SELECT if i % 4 == 0 else 
                      SQLOperation.INSERT if i % 4 == 1 else
                      SQLOperation.UPDATE if i % 4 == 2 else
                      SQLOperation.DELETE,
        )
        
        result = await permission_service.create(permission)
        if result.is_success:
            created_entities["permissions"].append(result.value)
    
    print(f"Created {len(created_entities['permissions'])} permissions")
    
    # For each tenant, create responsibilities, roles, groups, and users
    for tenant in created_entities["tenants"]:
        # Create responsibilities
        tenant_responsibilities = []
        for i in range(responsibility_per_tenant):
            responsibility = ResponsibilityRole(
                id=str(uuid.uuid4()),
                name=f"Responsibility_{tenant.name}_{i}",
                description=f"Benchmark responsibility {i} for tenant {tenant.name}",
                tenant_id=tenant.id,
            )
            
            result = await responsibility_service.create(responsibility)
            if result.is_success:
                created_entities["responsibilities"].append(result.value)
                tenant_responsibilities.append(result.value)
        
        # Create roles with permissions
        tenant_roles = []
        for i in range(roles_per_tenant):
            if not tenant_responsibilities:
                continue
                
            responsibility = random.choice(tenant_responsibilities)
            
            role = Role(
                id=str(uuid.uuid4()),
                name=f"Role_{tenant.name}_{i}",
                description=f"Benchmark role {i} for tenant {tenant.name}",
                tenant_id=tenant.id,
                responsibility_role_id=responsibility.id,
            )
            
            result = await role_service.create(role)
            if result.is_success:
                role = result.value
                created_entities["roles"].append(role)
                tenant_roles.append(role)
                
                # Add permissions to role
                permissions_to_add = random.sample(
                    created_entities["permissions"],
                    min(5, len(created_entities["permissions"]))
                )
                
                for permission in permissions_to_add:
                    await role_service.add_permission(role.id, permission.id)
        
        # Create groups
        tenant_groups = []
        for i in range(groups_per_tenant):
            group = Group(
                id=str(uuid.uuid4()),
                name=f"Group_{tenant.name}_{i}",
                tenant_id=tenant.id,
            )
            
            result = await group_service.create(group)
            if result.is_success:
                created_entities["groups"].append(result.value)
                tenant_groups.append(result.value)
        
        # Create users
        for i in range(users_per_tenant):
            if not tenant_groups:
                continue
                
            default_group = random.choice(tenant_groups)
            
            user = User(
                id=str(uuid.uuid4()),
                email=f"user_{i}_{uuid.uuid4().hex[:8]}@example.com",
                handle=f"user_{tenant.name}_{i}",
                full_name=f"Benchmark User {i}",
                is_superuser=i == 0,  # First user is superuser
                tenant_id=tenant.id,
                default_group_id=None if i == 0 else default_group.id,  # Superuser has no default group
            )
            
            result = await user_service.create(user)
            if result.is_success:
                user = result.value
                created_entities["users"].append(user)
                
                # Add user to groups (except superuser)
                if i > 0:
                    # Add to default group
                    await group_service.add_user(default_group.id, user.id)
                    
                    # Add to additional random groups
                    additional_groups = random.sample(
                        [g for g in tenant_groups if g.id != default_group.id],
                        min(2, len(tenant_groups) - 1)
                    )
                    
                    for group in additional_groups:
                        await group_service.add_user(group.id, user.id)
                
                # Add roles to user
                if tenant_roles:
                    roles_to_add = random.sample(
                        tenant_roles,
                        min(3, len(tenant_roles))
                    )
                    
                    for role in roles_to_add:
                        await role_service.add_user(role.id, user.id)
    
    print(f"Created {len(created_entities['users'])} users")
    print(f"Created {len(created_entities['groups'])} groups")
    print(f"Created {len(created_entities['roles'])} roles")
    print(f"Created {len(created_entities['responsibilities'])} responsibilities")
    
    yield created_entities


@pytest.mark.asyncio
async def test_user_creation_performance(authorization_services, benchmark):
    """Benchmark the performance of creating users."""
    user_service = authorization_services["user_service"]
    
    # Define async benchmark function
    async def create_user_benchmark():
        user_id = str(uuid.uuid4())
        email = f"bench_user_{uuid.uuid4().hex[:8]}@example.com"
        
        user = User(
            id=user_id,
            email=email,
            handle=f"bench_user_{uuid.uuid4().hex[:8]}",
            full_name="Benchmark Test User",
            is_superuser=False,
        )
        
        result = await user_service.create(user)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(create_user_benchmark()),
        iterations=10,
        rounds=3,
        name="user_creation"
    )
    
    print(f"User creation took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_permission_check_performance(authorization_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of checking user permissions."""
    user_service = authorization_services["user_service"]
    
    # Get test data
    users = setup_benchmark_environment["users"]
    
    if not users:
        pytest.skip("No test users available")
    
    # Select a user with roles for testing
    test_users = []
    for user in users:
        roles_result = await authorization_services["role_service"].find_by_user(user.id)
        if roles_result.is_success and roles_result.value:
            test_users.append(user)
            if len(test_users) >= 3:
                break
    
    if not test_users:
        pytest.skip("No users with roles found")
    
    test_user = test_users[0]
    meta_type_id = "meta_type_1"  # Using a meta type ID that should exist
    operation = SQLOperation.SELECT
    
    # Define async benchmark function
    async def check_permission_benchmark():
        result = await user_service.check_permission(test_user.id, meta_type_id, operation)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(check_permission_benchmark()),
        iterations=50,
        rounds=3,
        name="permission_check"
    )
    
    print(f"Permission check took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_user_role_assignment_performance(authorization_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of assigning roles to users."""
    user_service = authorization_services["user_service"]
    role_service = authorization_services["role_service"]
    
    # Get test data
    users = setup_benchmark_environment["users"]
    roles = setup_benchmark_environment["roles"]
    
    if not users or not roles:
        pytest.skip("No test users or roles available")
    
    test_user = users[0]
    test_role = roles[0]
    
    # Define async benchmark function
    async def role_assignment_benchmark():
        result = await user_service.add_role(test_user.id, test_role.id)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(role_assignment_benchmark()),
        iterations=10,
        rounds=3,
        name="role_assignment"
    )
    
    print(f"Role assignment took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_role_permission_query_performance(authorization_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying for role permissions."""
    role_service = authorization_services["role_service"]
    
    # Get test data
    roles = setup_benchmark_environment["roles"]
    
    if not roles:
        pytest.skip("No test roles available")
    
    # Select roles with permissions for testing
    test_roles = []
    for role in roles:
        permission_result = await authorization_services["permission_service"].find_by_role(role.id)
        if permission_result.is_success and permission_result.value:
            test_roles.append(role)
            if len(test_roles) >= 3:
                break
    
    if not test_roles:
        pytest.skip("No roles with permissions found")
    
    results = {}
    
    for i, role in enumerate(test_roles[:3]):
        # Define async benchmark function
        async def query_permissions_benchmark():
            result = await authorization_services["permission_service"].find_by_role(role.id)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_permissions_benchmark()),
            iterations=20,
            rounds=3,
            name=f"role_permission_query_{i}"
        )
        
        results[f"role_{i}"] = runtime
        print(f"Role permission query for role {i} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nRole permission query performance by role:")
    for role_key, time in results.items():
        print(f"  {role_key}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_user_by_tenant_query_performance(authorization_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying users by tenant."""
    user_service = authorization_services["user_service"]
    
    # Get test data
    tenants = setup_benchmark_environment["tenants"]
    
    if not tenants:
        pytest.skip("No test tenants available")
    
    results = {}
    
    for i, tenant in enumerate(tenants[:3]):
        # Define async benchmark function
        async def query_users_benchmark():
            result = await user_service.find_by_tenant(tenant.id)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_users_benchmark()),
            iterations=10,
            rounds=3,
            name=f"users_by_tenant_{i}"
        )
        
        results[f"tenant_{i}"] = runtime
        print(f"Users by tenant query for tenant {i} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nUsers by tenant query performance by tenant:")
    for tenant_key, time in results.items():
        print(f"  {tenant_key}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_tenant_relationship_loading_performance(authorization_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of loading tenant relationships."""
    tenant_service = authorization_services["tenant_service"]
    
    # Get test data
    tenants = setup_benchmark_environment["tenants"]
    
    if not tenants:
        pytest.skip("No test tenants available")
    
    results = {}
    
    for i, tenant in enumerate(tenants[:3]):
        # Define async benchmark function
        async def load_relationships_benchmark():
            result = await tenant_service.get_with_relationships(tenant.id)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(load_relationships_benchmark()),
            iterations=5,
            rounds=3,
            name=f"tenant_relationships_{i}"
        )
        
        results[f"tenant_{i}"] = runtime
        print(f"Tenant relationship loading for tenant {i} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nTenant relationship loading performance by tenant:")
    for tenant_key, time in results.items():
        print(f"  {tenant_key}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_find_users_by_role_performance(authorization_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of finding users by role."""
    user_service = authorization_services["user_service"]
    
    # Get test data
    roles = setup_benchmark_environment["roles"]
    
    if not roles:
        pytest.skip("No test roles available")
    
    # Select roles with users for testing
    test_roles = []
    for role in roles:
        users_result = await user_service.find_by_role(role.id)
        if users_result.is_success and users_result.value:
            test_roles.append(role)
            if len(test_roles) >= 3:
                break
    
    if not test_roles:
        pytest.skip("No roles with users found")
    
    results = {}
    
    for i, role in enumerate(test_roles[:3]):
        # Define async benchmark function
        async def find_users_benchmark():
            result = await user_service.find_by_role(role.id)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(find_users_benchmark()),
            iterations=10,
            rounds=3,
            name=f"users_by_role_{i}"
        )
        
        results[f"role_{i}"] = runtime
        print(f"Users by role query for role {i} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nUsers by role query performance by role:")
    for role_key, time in results.items():
        print(f"  {role_key}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_role_has_permission_performance(authorization_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of checking if a role has a permission."""
    role_service = authorization_services["role_service"]
    
    # Get test data
    roles = setup_benchmark_environment["roles"]
    
    if not roles:
        pytest.skip("No test roles available")
    
    # Select roles with permissions for testing
    test_roles = []
    for role in roles:
        permission_result = await authorization_services["permission_service"].find_by_role(role.id)
        if permission_result.is_success and permission_result.value:
            test_roles.append(role)
            if len(test_roles) >= 3:
                break
    
    if not test_roles:
        pytest.skip("No roles with permissions found")
    
    results = {}
    
    for i, role in enumerate(test_roles[:3]):
        # Get a permission to check
        permission_result = await authorization_services["permission_service"].find_by_role(role.id)
        if permission_result.is_failure or not permission_result.value:
            continue
            
        permission = permission_result.value[0]
        
        # Define async benchmark function
        async def has_permission_benchmark():
            result = await role_service.has_permission(
                role.id, 
                permission.meta_type_id, 
                permission.operation
            )
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(has_permission_benchmark()),
            iterations=50,
            rounds=3,
            name=f"role_has_permission_{i}"
        )
        
        results[f"role_{i}"] = runtime
        print(f"Role has permission check for role {i} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nRole has permission check performance by role:")
    for role_key, time in results.items():
        print(f"  {role_key}: {time:.4f} seconds")