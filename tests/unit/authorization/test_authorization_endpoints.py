"""
Tests for the Authorization module API endpoints.

This module contains comprehensive tests for the Authorization module API endpoints
to ensure proper functionality and compliance with domain-driven design principles.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from enum import Enum

from uno.core.result import Success, Failure
from uno.enums import SQLOperation, TenantType
from uno.authorization.entities import (
    User, Group, Role, Permission, ResponsibilityRole, Tenant
)
from uno.authorization.domain_services import (
    UserService, GroupService, RoleService, 
    PermissionService, ResponsibilityRoleService, TenantService
)
from uno.authorization.domain_endpoints import (
    user_router,
    group_router,
    role_router,
    permission_router,
    responsibility_role_router,
    tenant_router,
    register_auth_endpoints,
)

# Test data
TEST_USER_ID = "test_user"
TEST_GROUP_ID = "test_group"
TEST_ROLE_ID = "test_role"
TEST_PERMISSION_ID = 1
TEST_RESPONSIBILITY_ID = "test_responsibility"
TEST_TENANT_ID = "test_tenant"


class TestAuthorizationEndpoints:
    """Tests for the Authorization module endpoints."""

    @pytest.fixture
    def mock_user_service(self):
        """Create a mock user service."""
        return AsyncMock(spec=UserService)

    @pytest.fixture
    def mock_group_service(self):
        """Create a mock group service."""
        return AsyncMock(spec=GroupService)

    @pytest.fixture
    def mock_role_service(self):
        """Create a mock role service."""
        return AsyncMock(spec=RoleService)

    @pytest.fixture
    def mock_permission_service(self):
        """Create a mock permission service."""
        return AsyncMock(spec=PermissionService)

    @pytest.fixture
    def mock_responsibility_role_service(self):
        """Create a mock responsibility role service."""
        return AsyncMock(spec=ResponsibilityRoleService)

    @pytest.fixture
    def mock_tenant_service(self):
        """Create a mock tenant service."""
        return AsyncMock(spec=TenantService)

    @pytest.fixture
    def app(self, mock_user_service, mock_group_service, mock_role_service, 
            mock_permission_service, mock_responsibility_role_service, mock_tenant_service):
        """Create a FastAPI test application with auth routers."""
        app = FastAPI()
        
        # Patch dependency injection to use mock services
        with patch("uno.authorization.domain_endpoints.get_service") as mock_get_service:
            # Configure the mock to return appropriate service based on type
            def get_service_side_effect(service_type):
                if service_type == UserService:
                    return mock_user_service
                elif service_type == GroupService:
                    return mock_group_service
                elif service_type == RoleService:
                    return mock_role_service
                elif service_type == PermissionService:
                    return mock_permission_service
                elif service_type == ResponsibilityRoleService:
                    return mock_responsibility_role_service
                elif service_type == TenantService:
                    return mock_tenant_service
                return None
                
            mock_get_service.side_effect = get_service_side_effect
            
            # Register routers with the app
            register_auth_endpoints(app)
            
            yield app

    @pytest.fixture
    def client(self, app):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    # User endpoint tests
    
    def test_create_user_success(self, client, mock_user_service):
        """Test creating a user successfully."""
        # Arrange
        new_user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=True
        )
        mock_user_service.create.return_value = Success(new_user)
        
        # Act
        response = client.post(
            "/api/users/",
            json={
                "id": TEST_USER_ID,
                "email": "test@example.com",
                "handle": "testuser",
                "full_name": "Test User",
                "is_superuser": True
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_USER_ID
        assert response.json()["email"] == "test@example.com"
        mock_user_service.create.assert_called_once()

    def test_create_user_validation_error(self, client, mock_user_service):
        """Test creating a user with validation error."""
        # Arrange
        error_msg = "Full name cannot be empty"
        mock_user_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/users/",
            json={
                "id": TEST_USER_ID,
                "email": "test@example.com",
                "handle": "testuser",
                "full_name": "",  # Empty full name will cause validation error
                "is_superuser": True
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_user_service.create.assert_called_once()

    def test_get_user_by_id_success(self, client, mock_user_service):
        """Test getting a user by ID successfully."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        mock_user_service.get_by_id.return_value = Success(user)
        
        # Act
        response = client.get(f"/api/users/{TEST_USER_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_USER_ID
        assert response.json()["email"] == "test@example.com"
        mock_user_service.get_by_id.assert_called_once_with(TEST_USER_ID)

    def test_get_user_by_id_not_found(self, client, mock_user_service):
        """Test getting a user by ID when not found."""
        # Arrange
        mock_user_service.get_by_id.return_value = Success(None)
        
        # Act
        response = client.get(f"/api/users/{TEST_USER_ID}")
        
        # Assert
        assert response.status_code == 404
        mock_user_service.get_by_id.assert_called_once_with(TEST_USER_ID)

    def test_get_user_by_email_success(self, client, mock_user_service):
        """Test getting a user by email successfully."""
        # Arrange
        email = "test@example.com"
        user = User(
            id=TEST_USER_ID,
            email=email,
            handle="testuser",
            full_name="Test User"
        )
        mock_user_service.find_by_email.return_value = Success(user)
        
        # Act
        response = client.get(f"/api/users/by-email/{email}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_USER_ID
        assert response.json()["email"] == email
        mock_user_service.find_by_email.assert_called_once_with(email)

    def test_get_user_by_email_not_found(self, client, mock_user_service):
        """Test getting a user by email when not found."""
        # Arrange
        email = "nonexistent@example.com"
        mock_user_service.find_by_email.return_value = Success(None)
        
        # Act
        response = client.get(f"/api/users/by-email/{email}")
        
        # Assert
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
        mock_user_service.find_by_email.assert_called_once_with(email)

    def test_get_user_by_handle_success(self, client, mock_user_service):
        """Test getting a user by handle successfully."""
        # Arrange
        handle = "testuser"
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle=handle,
            full_name="Test User"
        )
        mock_user_service.find_by_handle.return_value = Success(user)
        
        # Act
        response = client.get(f"/api/users/by-handle/{handle}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_USER_ID
        assert response.json()["handle"] == handle
        mock_user_service.find_by_handle.assert_called_once_with(handle, None)

    def test_get_users_by_tenant_success(self, client, mock_user_service):
        """Test getting users by tenant successfully."""
        # Arrange
        tenant_id = TEST_TENANT_ID
        users = [
            User(id="user1", email="user1@example.com", handle="user1", full_name="User 1", tenant_id=tenant_id),
            User(id="user2", email="user2@example.com", handle="user2", full_name="User 2", tenant_id=tenant_id)
        ]
        mock_user_service.find_by_tenant.return_value = Success(users)
        
        # Act
        response = client.get(f"/api/users/in-tenant/{tenant_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["tenant_id"] == tenant_id
        assert response.json()[1]["tenant_id"] == tenant_id
        mock_user_service.find_by_tenant.assert_called_once_with(tenant_id, 100, 0)

    def test_get_users_by_group_success(self, client, mock_user_service):
        """Test getting users by group successfully."""
        # Arrange
        group_id = TEST_GROUP_ID
        users = [
            User(id="user1", email="user1@example.com", handle="user1", full_name="User 1"),
            User(id="user2", email="user2@example.com", handle="user2", full_name="User 2")
        ]
        
        # Set up navigation properties
        group = Group(id=group_id, name="Test Group", tenant_id=TEST_TENANT_ID)
        for user in users:
            user.add_to_group(group)
            
        mock_user_service.find_by_group.return_value = Success(users)
        
        # Act
        response = client.get(f"/api/users/in-group/{group_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_user_service.find_by_group.assert_called_once_with(group_id, 100, 0)

    def test_add_user_to_group_success(self, client, mock_user_service):
        """Test adding a user to a group successfully."""
        # Arrange
        user_id = TEST_USER_ID
        group_id = TEST_GROUP_ID
        
        user = User(
            id=user_id,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        group = Group(
            id=group_id,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        
        user.add_to_group(group)
        mock_user_service.add_to_group.return_value = Success(user)
        
        # Act
        response = client.post(f"/api/users/{user_id}/groups/{group_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == user_id
        mock_user_service.add_to_group.assert_called_once_with(user_id, group_id)

    def test_check_user_permission_success(self, client, mock_user_service):
        """Test checking user permission successfully."""
        # Arrange
        user_id = TEST_USER_ID
        meta_type_id = "meta_type_1"
        operation = SQLOperation.SELECT
        
        mock_user_service.check_permission.return_value = Success(True)
        
        # Act
        response = client.get(f"/api/users/{user_id}/check-permission/{meta_type_id}/{operation.value}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["has_permission"] is True
        mock_user_service.check_permission.assert_called_once()

    # Group endpoint tests
    
    def test_create_group_success(self, client, mock_group_service):
        """Test creating a group successfully."""
        # Arrange
        new_group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        mock_group_service.create.return_value = Success(new_group)
        
        # Act
        response = client.post(
            "/api/groups/",
            json={
                "id": TEST_GROUP_ID,
                "name": "Test Group",
                "tenant_id": TEST_TENANT_ID
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_GROUP_ID
        assert response.json()["name"] == "Test Group"
        assert response.json()["tenant_id"] == TEST_TENANT_ID
        mock_group_service.create.assert_called_once()

    def test_get_group_by_name_success(self, client, mock_group_service):
        """Test getting a group by name successfully."""
        # Arrange
        name = "Test Group"
        tenant_id = TEST_TENANT_ID
        group = Group(
            id=TEST_GROUP_ID,
            name=name,
            tenant_id=tenant_id
        )
        mock_group_service.find_by_name.return_value = Success(group)
        
        # Act
        response = client.get(f"/api/groups/by-name/{name}?tenant_id={tenant_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_GROUP_ID
        assert response.json()["name"] == name
        assert response.json()["tenant_id"] == tenant_id
        mock_group_service.find_by_name.assert_called_once_with(name, tenant_id)

    def test_get_groups_by_tenant_success(self, client, mock_group_service):
        """Test getting groups by tenant successfully."""
        # Arrange
        tenant_id = TEST_TENANT_ID
        groups = [
            Group(id="group1", name="Group 1", tenant_id=tenant_id),
            Group(id="group2", name="Group 2", tenant_id=tenant_id)
        ]
        mock_group_service.find_by_tenant.return_value = Success(groups)
        
        # Act
        response = client.get(f"/api/groups/in-tenant/{tenant_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["tenant_id"] == tenant_id
        assert response.json()[1]["tenant_id"] == tenant_id
        mock_group_service.find_by_tenant.assert_called_once_with(tenant_id, 100, 0)

    def test_get_groups_by_user_success(self, client, mock_group_service):
        """Test getting groups by user successfully."""
        # Arrange
        user_id = TEST_USER_ID
        groups = [
            Group(id="group1", name="Group 1", tenant_id=TEST_TENANT_ID),
            Group(id="group2", name="Group 2", tenant_id=TEST_TENANT_ID)
        ]
        mock_group_service.find_by_user.return_value = Success(groups)
        
        # Act
        response = client.get(f"/api/groups/for-user/{user_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_group_service.find_by_user.assert_called_once_with(user_id, 100, 0)

    def test_add_user_to_group_from_group_success(self, client, mock_group_service):
        """Test adding a user to a group from the group endpoint successfully."""
        # Arrange
        group_id = TEST_GROUP_ID
        user_id = TEST_USER_ID
        
        group = Group(
            id=group_id,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        
        user = User(
            id=user_id,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        group.add_user(user)
        mock_group_service.add_user.return_value = Success(group)
        
        # Act
        response = client.post(f"/api/groups/{group_id}/users/{user_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == group_id
        mock_group_service.add_user.assert_called_once_with(group_id, user_id)

    # Role endpoint tests
    
    def test_create_role_success(self, client, mock_role_service):
        """Test creating a role successfully."""
        # Arrange
        new_role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        mock_role_service.create.return_value = Success(new_role)
        
        # Act
        response = client.post(
            "/api/roles/",
            json={
                "id": TEST_ROLE_ID,
                "name": "Test Role",
                "description": "Test Role Description",
                "tenant_id": TEST_TENANT_ID,
                "responsibility_role_id": TEST_RESPONSIBILITY_ID
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ROLE_ID
        assert response.json()["name"] == "Test Role"
        assert response.json()["tenant_id"] == TEST_TENANT_ID
        assert response.json()["responsibility_role_id"] == TEST_RESPONSIBILITY_ID
        mock_role_service.create.assert_called_once()

    def test_get_role_by_name_success(self, client, mock_role_service):
        """Test getting a role by name successfully."""
        # Arrange
        name = "Test Role"
        tenant_id = TEST_TENANT_ID
        role = Role(
            id=TEST_ROLE_ID,
            name=name,
            description="Test Role Description",
            tenant_id=tenant_id,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        mock_role_service.find_by_name.return_value = Success(role)
        
        # Act
        response = client.get(f"/api/roles/by-name/{name}?tenant_id={tenant_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ROLE_ID
        assert response.json()["name"] == name
        assert response.json()["tenant_id"] == tenant_id
        mock_role_service.find_by_name.assert_called_once_with(name, tenant_id)

    def test_add_permission_to_role_success(self, client, mock_role_service):
        """Test adding a permission to a role successfully."""
        # Arrange
        role_id = TEST_ROLE_ID
        permission_id = TEST_PERMISSION_ID
        
        role = Role(
            id=role_id,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        permission = Permission(
            id=permission_id,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        role.add_permission(permission)
        mock_role_service.add_permission.return_value = Success(role)
        
        # Act
        response = client.post(f"/api/roles/{role_id}/permissions/{permission_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == role_id
        mock_role_service.add_permission.assert_called_once_with(role_id, permission_id)

    def test_check_role_permission_success(self, client, mock_role_service):
        """Test checking role permission successfully."""
        # Arrange
        role_id = TEST_ROLE_ID
        meta_type_id = "meta_type_1"
        operation = SQLOperation.SELECT
        
        mock_role_service.has_permission.return_value = Success(True)
        
        # Act
        response = client.get(f"/api/roles/{role_id}/check-permission/{meta_type_id}/{operation.value}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["has_permission"] is True
        mock_role_service.has_permission.assert_called_once()

    # Permission endpoint tests
    
    def test_create_permission_success(self, client, mock_permission_service):
        """Test creating a permission successfully."""
        # Arrange
        new_permission = Permission(
            id=TEST_PERMISSION_ID,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        mock_permission_service.create.return_value = Success(new_permission)
        
        # Act
        response = client.post(
            "/api/permissions/",
            json={
                "id": TEST_PERMISSION_ID,
                "meta_type_id": "meta_type_1",
                "operation": SQLOperation.SELECT.value
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_PERMISSION_ID
        assert response.json()["meta_type_id"] == "meta_type_1"
        assert response.json()["operation"] == SQLOperation.SELECT.value
        mock_permission_service.create.assert_called_once()

    def test_get_permissions_by_meta_type_success(self, client, mock_permission_service):
        """Test getting permissions by meta type successfully."""
        # Arrange
        meta_type_id = "meta_type_1"
        permissions = [
            Permission(id=1, meta_type_id=meta_type_id, operation=SQLOperation.SELECT),
            Permission(id=2, meta_type_id=meta_type_id, operation=SQLOperation.INSERT)
        ]
        mock_permission_service.find_by_meta_type.return_value = Success(permissions)
        
        # Act
        response = client.get(f"/api/permissions/for-meta-type/{meta_type_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["meta_type_id"] == meta_type_id
        assert response.json()[1]["meta_type_id"] == meta_type_id
        mock_permission_service.find_by_meta_type.assert_called_once_with(meta_type_id, 100, 0)

    def test_get_permission_by_meta_type_and_operation_success(self, client, mock_permission_service):
        """Test getting a permission by meta type and operation successfully."""
        # Arrange
        meta_type_id = "meta_type_1"
        operation = SQLOperation.SELECT
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            meta_type_id=meta_type_id,
            operation=operation
        )
        mock_permission_service.find_by_meta_type_and_operation.return_value = Success(permission)
        
        # Act
        response = client.get(f"/api/permissions/exact/{meta_type_id}/{operation.value}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_PERMISSION_ID
        assert response.json()["meta_type_id"] == meta_type_id
        assert response.json()["operation"] == operation.value
        mock_permission_service.find_by_meta_type_and_operation.assert_called_once_with(meta_type_id, operation.value)

    # ResponsibilityRole endpoint tests
    
    def test_create_responsibility_role_success(self, client, mock_responsibility_role_service):
        """Test creating a responsibility role successfully."""
        # Arrange
        new_responsibility = ResponsibilityRole(
            id=TEST_RESPONSIBILITY_ID,
            name="Test Responsibility",
            description="Test Responsibility Description",
            tenant_id=TEST_TENANT_ID
        )
        mock_responsibility_role_service.create.return_value = Success(new_responsibility)
        
        # Act
        response = client.post(
            "/api/responsibility-roles/",
            json={
                "id": TEST_RESPONSIBILITY_ID,
                "name": "Test Responsibility",
                "description": "Test Responsibility Description",
                "tenant_id": TEST_TENANT_ID
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RESPONSIBILITY_ID
        assert response.json()["name"] == "Test Responsibility"
        assert response.json()["tenant_id"] == TEST_TENANT_ID
        mock_responsibility_role_service.create.assert_called_once()

    def test_get_responsibility_role_by_name_success(self, client, mock_responsibility_role_service):
        """Test getting a responsibility role by name successfully."""
        # Arrange
        name = "Test Responsibility"
        tenant_id = TEST_TENANT_ID
        responsibility = ResponsibilityRole(
            id=TEST_RESPONSIBILITY_ID,
            name=name,
            description="Test Responsibility Description",
            tenant_id=tenant_id
        )
        mock_responsibility_role_service.find_by_name.return_value = Success(responsibility)
        
        # Act
        response = client.get(f"/api/responsibility-roles/by-name/{name}?tenant_id={tenant_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RESPONSIBILITY_ID
        assert response.json()["name"] == name
        assert response.json()["tenant_id"] == tenant_id
        mock_responsibility_role_service.find_by_name.assert_called_once_with(name, tenant_id)

    # Tenant endpoint tests
    
    def test_create_tenant_success(self, client, mock_tenant_service):
        """Test creating a tenant successfully."""
        # Arrange
        new_tenant = Tenant(
            id=TEST_TENANT_ID,
            name="Test Tenant",
            tenant_type=TenantType.ORGANIZATION
        )
        mock_tenant_service.create.return_value = Success(new_tenant)
        
        # Act
        response = client.post(
            "/api/tenants/",
            json={
                "id": TEST_TENANT_ID,
                "name": "Test Tenant",
                "tenant_type": TenantType.ORGANIZATION.value
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_TENANT_ID
        assert response.json()["name"] == "Test Tenant"
        assert response.json()["tenant_type"] == TenantType.ORGANIZATION.value
        mock_tenant_service.create.assert_called_once()

    def test_get_tenant_by_name_success(self, client, mock_tenant_service):
        """Test getting a tenant by name successfully."""
        # Arrange
        name = "Test Tenant"
        tenant = Tenant(
            id=TEST_TENANT_ID,
            name=name,
            tenant_type=TenantType.ORGANIZATION
        )
        mock_tenant_service.find_by_name.return_value = Success(tenant)
        
        # Act
        response = client.get(f"/api/tenants/by-name/{name}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_TENANT_ID
        assert response.json()["name"] == name
        mock_tenant_service.find_by_name.assert_called_once_with(name)

    def test_get_tenants_by_type_success(self, client, mock_tenant_service):
        """Test getting tenants by type successfully."""
        # Arrange
        tenant_type = TenantType.ORGANIZATION
        tenants = [
            Tenant(id="tenant1", name="Tenant 1", tenant_type=tenant_type),
            Tenant(id="tenant2", name="Tenant 2", tenant_type=tenant_type)
        ]
        mock_tenant_service.find_by_type.return_value = Success(tenants)
        
        # Act
        response = client.get(f"/api/tenants/by-type/{tenant_type.value}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["tenant_type"] == tenant_type.value
        assert response.json()[1]["tenant_type"] == tenant_type.value
        mock_tenant_service.find_by_type.assert_called_once_with(tenant_type.value, 100, 0)

    def test_add_user_to_tenant_success(self, client, mock_tenant_service):
        """Test adding a user to a tenant successfully."""
        # Arrange
        tenant_id = TEST_TENANT_ID
        user_id = TEST_USER_ID
        
        tenant = Tenant(
            id=tenant_id,
            name="Test Tenant",
            tenant_type=TenantType.ORGANIZATION
        )
        
        user = User(
            id=user_id,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        tenant.add_user(user)
        mock_tenant_service.add_user.return_value = Success(tenant)
        
        # Act
        response = client.post(f"/api/tenants/{tenant_id}/users/{user_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == tenant_id
        mock_tenant_service.add_user.assert_called_once_with(tenant_id, user_id)