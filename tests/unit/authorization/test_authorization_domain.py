"""
Tests for the Authorization module domain components.

This module contains comprehensive tests for the Authorization module domain entities,
repositories, and services to ensure proper functionality and compliance with 
domain-driven design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

from uno.core.result import Success, Failure
from uno.enums import SQLOperation, TenantType
from uno.authorization.entities import (
    User, Group, Role, Permission, ResponsibilityRole, Tenant
)
from uno.authorization.domain_repositories import (
    UserRepository, GroupRepository, RoleRepository, 
    PermissionRepository, ResponsibilityRoleRepository, TenantRepository
)
from uno.authorization.domain_services import (
    UserService, GroupService, RoleService, 
    PermissionService, ResponsibilityRoleService, TenantService
)

# Test Data
TEST_USER_ID = "test_user"
TEST_GROUP_ID = "test_group"
TEST_ROLE_ID = "test_role"
TEST_PERMISSION_ID = 1
TEST_RESPONSIBILITY_ID = "test_responsibility"
TEST_TENANT_ID = "test_tenant"


class TestUserEntity:
    """Tests for the User domain entity."""

    def test_create_user(self):
        """Test creating a user entity."""
        # Arrange
        user_id = TEST_USER_ID
        email = "test@example.com"
        handle = "testuser"
        full_name = "Test User"
        
        # Act
        user = User(
            id=user_id,
            email=email,
            handle=handle,
            full_name=full_name
        )
        
        # Assert
        assert user.id == user_id
        assert user.email == email
        assert user.handle == handle
        assert user.full_name == full_name
        assert user.is_superuser is False
        assert user.tenant_id is None
        assert user.tenant is None
        assert user.default_group_id is None
        assert user.default_group is None
        assert isinstance(user.groups, list)
        assert len(user.groups) == 0
        assert isinstance(user.roles, list)
        assert len(user.roles) == 0

    def test_validate_user_valid(self):
        """Test validation with a valid user."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=True
        )
        
        # Act & Assert
        user.validate()  # Should not raise an exception

    def test_validate_user_valid_with_default_group(self):
        """Test validation with a valid user with default group."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=False,
            default_group_id="default_group"
        )
        
        # Act & Assert
        user.validate()  # Should not raise an exception

    def test_validate_user_invalid_empty_email(self):
        """Test validation with empty email."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="",  # Empty email
            handle="testuser",
            full_name="Test User"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email cannot be empty"):
            user.validate()

    def test_validate_user_invalid_empty_handle(self):
        """Test validation with empty handle."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="",  # Empty handle
            full_name="Test User"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Handle cannot be empty"):
            user.validate()

    def test_validate_user_invalid_empty_full_name(self):
        """Test validation with empty full name."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name=""  # Empty full name
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Full name cannot be empty"):
            user.validate()

    def test_validate_user_invalid_superuser_with_default_group(self):
        """Test validation with superuser having a default group."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=True,
            default_group_id="default_group"  # Superuser with default group
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Superuser cannot have a default group"):
            user.validate()

    def test_validate_user_invalid_nonsuperuser_without_default_group(self):
        """Test validation with non-superuser not having a default group."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=False,
            default_group_id=None  # Non-superuser without default group
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Non-superuser must have a default group"):
            user.validate()

    def test_add_to_group(self):
        """Test adding a user to a group."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        
        # Act
        user.add_to_group(group)
        
        # Assert
        assert group in user.groups
        assert len(user.groups) == 1
        
        # Adding the same group again should not duplicate
        user.add_to_group(group)
        assert len(user.groups) == 1

    def test_remove_from_group(self):
        """Test removing a user from a group."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        
        user.add_to_group(group)
        assert group in user.groups
        
        # Act
        user.remove_from_group(group)
        
        # Assert
        assert group not in user.groups
        assert len(user.groups) == 0
        
        # Removing a group that's not in the list should not raise an error
        user.remove_from_group(group)

    def test_add_role(self):
        """Test adding a role to a user."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        # Act
        user.add_role(role)
        
        # Assert
        assert role in user.roles
        assert len(user.roles) == 1
        
        # Adding the same role again should not duplicate
        user.add_role(role)
        assert len(user.roles) == 1

    def test_remove_role(self):
        """Test removing a role from a user."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        user.add_role(role)
        assert role in user.roles
        
        # Act
        user.remove_role(role)
        
        # Assert
        assert role not in user.roles
        assert len(user.roles) == 0
        
        # Removing a role that's not in the list should not raise an error
        user.remove_role(role)

    def test_has_permission_superuser(self):
        """Test that a superuser has all permissions."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=True
        )
        
        # Act & Assert
        assert user.has_permission("any_meta_type", SQLOperation.SELECT) is True
        assert user.has_permission("any_meta_type", SQLOperation.INSERT) is True
        assert user.has_permission("any_meta_type", SQLOperation.UPDATE) is True
        assert user.has_permission("any_meta_type", SQLOperation.DELETE) is True

    def test_has_permission_regular_user(self):
        """Test permission checking for a regular user."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=False,
            default_group_id=TEST_GROUP_ID
        )
        
        role1 = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        permission1 = Permission(
            id=1,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        permission2 = Permission(
            id=2,
            meta_type_id="meta_type_1",
            operation=SQLOperation.INSERT
        )
        
        # Role has SELECT and INSERT permissions on meta_type_1
        role1.add_permission(permission1)
        role1.add_permission(permission2)
        
        # Add role to user
        user.add_role(role1)
        
        # Act & Assert
        assert user.has_permission("meta_type_1", SQLOperation.SELECT) is True
        assert user.has_permission("meta_type_1", SQLOperation.INSERT) is True
        assert user.has_permission("meta_type_1", SQLOperation.UPDATE) is False
        assert user.has_permission("meta_type_1", SQLOperation.DELETE) is False
        assert user.has_permission("meta_type_2", SQLOperation.SELECT) is False


class TestGroupEntity:
    """Tests for the Group domain entity."""

    def test_create_group(self):
        """Test creating a group entity."""
        # Arrange
        group_id = TEST_GROUP_ID
        name = "Test Group"
        tenant_id = TEST_TENANT_ID
        
        # Act
        group = Group(
            id=group_id,
            name=name,
            tenant_id=tenant_id
        )
        
        # Assert
        assert group.id == group_id
        assert group.name == name
        assert group.tenant_id == tenant_id
        assert group.tenant is None
        assert isinstance(group.users, list)
        assert len(group.users) == 0

    def test_validate_group_valid(self):
        """Test validation with a valid group."""
        # Arrange
        group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        
        # Act & Assert
        group.validate()  # Should not raise an exception

    def test_validate_group_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        group = Group(
            id=TEST_GROUP_ID,
            name="",  # Empty name
            tenant_id=TEST_TENANT_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Name cannot be empty"):
            group.validate()

    def test_validate_group_invalid_empty_tenant_id(self):
        """Test validation with empty tenant ID."""
        # Arrange
        group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=""  # Empty tenant ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tenant ID cannot be empty"):
            group.validate()

    def test_add_user(self):
        """Test adding a user to a group."""
        # Arrange
        group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        # Act
        group.add_user(user)
        
        # Assert
        assert user in group.users
        assert group in user.groups
        assert len(group.users) == 1
        
        # Adding the same user again should not duplicate
        group.add_user(user)
        assert len(group.users) == 1

    def test_remove_user(self):
        """Test removing a user from a group."""
        # Arrange
        group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        group.add_user(user)
        assert user in group.users
        assert group in user.groups
        
        # Act
        group.remove_user(user)
        
        # Assert
        assert user not in group.users
        assert group not in user.groups
        assert len(group.users) == 0
        
        # Removing a user that's not in the group should not raise an error
        group.remove_user(user)


class TestRoleEntity:
    """Tests for the Role domain entity."""

    def test_create_role(self):
        """Test creating a role entity."""
        # Arrange
        role_id = TEST_ROLE_ID
        name = "Test Role"
        description = "Test Role Description"
        tenant_id = TEST_TENANT_ID
        responsibility_role_id = TEST_RESPONSIBILITY_ID
        
        # Act
        role = Role(
            id=role_id,
            name=name,
            description=description,
            tenant_id=tenant_id,
            responsibility_role_id=responsibility_role_id
        )
        
        # Assert
        assert role.id == role_id
        assert role.name == name
        assert role.description == description
        assert role.tenant_id == tenant_id
        assert role.responsibility_role_id == responsibility_role_id
        assert role.tenant is None
        assert role.responsibility is None
        assert isinstance(role.permissions, list)
        assert len(role.permissions) == 0
        assert isinstance(role.users, list)
        assert len(role.users) == 0

    def test_validate_role_valid(self):
        """Test validation with a valid role."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        # Act & Assert
        role.validate()  # Should not raise an exception

    def test_validate_role_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="",  # Empty name
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Name cannot be empty"):
            role.validate()

    def test_validate_role_invalid_empty_description(self):
        """Test validation with empty description."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="",  # Empty description
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Description cannot be empty"):
            role.validate()

    def test_validate_role_invalid_empty_tenant_id(self):
        """Test validation with empty tenant ID."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id="",  # Empty tenant ID
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tenant ID cannot be empty"):
            role.validate()

    def test_validate_role_invalid_empty_responsibility_role_id(self):
        """Test validation with empty responsibility role ID."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=""  # Empty responsibility role ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Responsibility role ID cannot be empty"):
            role.validate()

    def test_add_permission(self):
        """Test adding a permission to a role."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        # Act
        role.add_permission(permission)
        
        # Assert
        assert permission in role.permissions
        assert len(role.permissions) == 1
        
        # Adding the same permission again should not duplicate
        role.add_permission(permission)
        assert len(role.permissions) == 1

    def test_remove_permission(self):
        """Test removing a permission from a role."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        role.add_permission(permission)
        assert permission in role.permissions
        
        # Act
        role.remove_permission(permission)
        
        # Assert
        assert permission not in role.permissions
        assert len(role.permissions) == 0
        
        # Removing a permission that's not in the role should not raise an error
        role.remove_permission(permission)

    def test_add_user(self):
        """Test adding a user to a role."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        # Act
        role.add_user(user)
        
        # Assert
        assert user in role.users
        assert role in user.roles
        assert len(role.users) == 1
        
        # Adding the same user again should not duplicate
        role.add_user(user)
        assert len(role.users) == 1

    def test_remove_user(self):
        """Test removing a user from a role."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        role.add_user(user)
        assert user in role.users
        assert role in user.roles
        
        # Act
        role.remove_user(user)
        
        # Assert
        assert user not in role.users
        assert role not in user.roles
        assert len(role.users) == 0
        
        # Removing a user that's not in the role should not raise an error
        role.remove_user(user)

    def test_has_permission(self):
        """Test checking if a role has a specific permission."""
        # Arrange
        role = Role(
            id=TEST_ROLE_ID,
            name="Test Role",
            description="Test Role Description",
            tenant_id=TEST_TENANT_ID,
            responsibility_role_id=TEST_RESPONSIBILITY_ID
        )
        
        permission1 = Permission(
            id=1,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        permission2 = Permission(
            id=2,
            meta_type_id="meta_type_1",
            operation=SQLOperation.INSERT
        )
        
        role.add_permission(permission1)
        role.add_permission(permission2)
        
        # Act & Assert
        assert role.has_permission("meta_type_1", SQLOperation.SELECT) is True
        assert role.has_permission("meta_type_1", SQLOperation.INSERT) is True
        assert role.has_permission("meta_type_1", SQLOperation.UPDATE) is False
        assert role.has_permission("meta_type_2", SQLOperation.SELECT) is False


class TestPermissionEntity:
    """Tests for the Permission domain entity."""

    def test_create_permission(self):
        """Test creating a permission entity."""
        # Arrange
        permission_id = TEST_PERMISSION_ID
        meta_type_id = "meta_type_1"
        operation = SQLOperation.SELECT
        
        # Act
        permission = Permission(
            id=permission_id,
            meta_type_id=meta_type_id,
            operation=operation
        )
        
        # Assert
        assert permission.id == permission_id
        assert permission.meta_type_id == meta_type_id
        assert permission.operation == operation
        assert isinstance(permission.roles, list)
        assert len(permission.roles) == 0

    def test_validate_permission_valid(self):
        """Test validation with a valid permission."""
        # Arrange
        permission = Permission(
            id=TEST_PERMISSION_ID,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        # Act & Assert
        permission.validate()  # Should not raise an exception

    def test_validate_permission_invalid_empty_meta_type_id(self):
        """Test validation with empty meta type ID."""
        # Arrange
        permission = Permission(
            id=TEST_PERMISSION_ID,
            meta_type_id="",  # Empty meta type ID
            operation=SQLOperation.SELECT
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Meta type ID cannot be empty"):
            permission.validate()

    def test_validate_permission_invalid_empty_operation(self):
        """Test validation with empty operation."""
        # Arrange
        permission = Permission(
            id=TEST_PERMISSION_ID,
            meta_type_id="meta_type_1",
            operation=None  # Empty operation
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Operation cannot be empty"):
            permission.validate()

    def test_permission_equality(self):
        """Test permission equality comparison."""
        # Arrange
        permission1 = Permission(
            id=1,
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        permission2 = Permission(
            id=2,  # Different ID
            meta_type_id="meta_type_1",
            operation=SQLOperation.SELECT
        )
        
        permission3 = Permission(
            id=3,
            meta_type_id="meta_type_2",  # Different meta type
            operation=SQLOperation.SELECT
        )
        
        permission4 = Permission(
            id=4,
            meta_type_id="meta_type_1",
            operation=SQLOperation.INSERT  # Different operation
        )
        
        # Act & Assert
        # Same meta type and operation should be considered equal, even with different IDs
        assert permission1 == permission2
        
        # Different meta type should not be equal
        assert permission1 != permission3
        
        # Different operation should not be equal
        assert permission1 != permission4
        
        # Non-Permission objects should not be equal
        assert permission1 != "not a permission"


class TestResponsibilityRoleEntity:
    """Tests for the ResponsibilityRole domain entity."""

    def test_create_responsibility_role(self):
        """Test creating a responsibility role entity."""
        # Arrange
        responsibility_id = TEST_RESPONSIBILITY_ID
        name = "Test Responsibility"
        description = "Test Responsibility Description"
        tenant_id = TEST_TENANT_ID
        
        # Act
        responsibility = ResponsibilityRole(
            id=responsibility_id,
            name=name,
            description=description,
            tenant_id=tenant_id
        )
        
        # Assert
        assert responsibility.id == responsibility_id
        assert responsibility.name == name
        assert responsibility.description == description
        assert responsibility.tenant_id == tenant_id
        assert responsibility.tenant is None

    def test_validate_responsibility_role_valid(self):
        """Test validation with a valid responsibility role."""
        # Arrange
        responsibility = ResponsibilityRole(
            id=TEST_RESPONSIBILITY_ID,
            name="Test Responsibility",
            description="Test Responsibility Description",
            tenant_id=TEST_TENANT_ID
        )
        
        # Act & Assert
        responsibility.validate()  # Should not raise an exception

    def test_validate_responsibility_role_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        responsibility = ResponsibilityRole(
            id=TEST_RESPONSIBILITY_ID,
            name="",  # Empty name
            description="Test Responsibility Description",
            tenant_id=TEST_TENANT_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Name cannot be empty"):
            responsibility.validate()

    def test_validate_responsibility_role_invalid_empty_description(self):
        """Test validation with empty description."""
        # Arrange
        responsibility = ResponsibilityRole(
            id=TEST_RESPONSIBILITY_ID,
            name="Test Responsibility",
            description="",  # Empty description
            tenant_id=TEST_TENANT_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Description cannot be empty"):
            responsibility.validate()

    def test_validate_responsibility_role_invalid_empty_tenant_id(self):
        """Test validation with empty tenant ID."""
        # Arrange
        responsibility = ResponsibilityRole(
            id=TEST_RESPONSIBILITY_ID,
            name="Test Responsibility",
            description="Test Responsibility Description",
            tenant_id=""  # Empty tenant ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tenant ID cannot be empty"):
            responsibility.validate()


class TestTenantEntity:
    """Tests for the Tenant domain entity."""

    def test_create_tenant(self):
        """Test creating a tenant entity."""
        # Arrange
        tenant_id = TEST_TENANT_ID
        name = "Test Tenant"
        tenant_type = TenantType.ORGANIZATION
        
        # Act
        tenant = Tenant(
            id=tenant_id,
            name=name,
            tenant_type=tenant_type
        )
        
        # Assert
        assert tenant.id == tenant_id
        assert tenant.name == name
        assert tenant.tenant_type == tenant_type
        assert isinstance(tenant.users, list)
        assert len(tenant.users) == 0
        assert isinstance(tenant.groups, list)
        assert len(tenant.groups) == 0
        assert isinstance(tenant.roles, list)
        assert len(tenant.roles) == 0

    def test_validate_tenant_valid(self):
        """Test validation with a valid tenant."""
        # Arrange
        tenant = Tenant(
            id=TEST_TENANT_ID,
            name="Test Tenant",
            tenant_type=TenantType.ORGANIZATION
        )
        
        # Act & Assert
        tenant.validate()  # Should not raise an exception

    def test_validate_tenant_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        tenant = Tenant(
            id=TEST_TENANT_ID,
            name="",  # Empty name
            tenant_type=TenantType.ORGANIZATION
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Name cannot be empty"):
            tenant.validate()

    def test_add_user(self):
        """Test adding a user to a tenant."""
        # Arrange
        tenant = Tenant(
            id=TEST_TENANT_ID,
            name="Test Tenant",
            tenant_type=TenantType.ORGANIZATION
        )
        
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )
        
        # Act
        tenant.add_user(user)
        
        # Assert
        assert user in tenant.users
        assert user.tenant_id == tenant.id
        assert user.tenant == tenant
        assert len(tenant.users) == 1
        
        # Adding the same user again should not duplicate
        tenant.add_user(user)
        assert len(tenant.users) == 1


# Repository Tests

class TestUserRepository:
    """Tests for the UserRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a UserRepository instance."""
        return UserRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting a user by ID successfully."""
        # Arrange
        user_id = TEST_USER_ID
        mock_session.get.return_value = User(
            id=user_id,
            email="test@example.com",
            handle="testuser",
            full_name="Test User"
        )

        # Act
        result = await repository.get_by_id(user_id, mock_session)

        # Assert
        assert result.is_success
        user = result.value
        assert user.id == user_id
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_email(self, repository, mock_session):
        """Test finding a user by email."""
        # Arrange
        email = "test@example.com"
        mock_session.execute.return_value.scalars.return_value.first.return_value = User(
            id=TEST_USER_ID,
            email=email,
            handle="testuser",
            full_name="Test User"
        )

        # Act
        result = await repository.find_by_email(email, mock_session)

        # Assert
        assert result is not None
        assert result.email == email
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_handle(self, repository, mock_session):
        """Test finding a user by handle."""
        # Arrange
        handle = "testuser"
        tenant_id = TEST_TENANT_ID
        mock_session.execute.return_value.scalars.return_value.first.return_value = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle=handle,
            full_name="Test User",
            tenant_id=tenant_id
        )

        # Act
        result = await repository.find_by_handle(handle, tenant_id, mock_session)

        # Assert
        assert result is not None
        assert result.handle == handle
        assert result.tenant_id == tenant_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_tenant(self, repository, mock_session):
        """Test finding users by tenant."""
        # Arrange
        tenant_id = TEST_TENANT_ID
        users = [
            User(id="user1", email="user1@example.com", handle="user1", full_name="User 1", tenant_id=tenant_id),
            User(id="user2", email="user2@example.com", handle="user2", full_name="User 2", tenant_id=tenant_id)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = users

        # Act
        result = await repository.find_by_tenant(tenant_id, 10, 0, mock_session)

        # Assert
        assert len(result) == 2
        assert all(user.tenant_id == tenant_id for user in result)
        mock_session.execute.assert_called_once()


class TestGroupRepository:
    """Tests for the GroupRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a GroupRepository instance."""
        return GroupRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting a group by ID successfully."""
        # Arrange
        group_id = TEST_GROUP_ID
        mock_session.get.return_value = Group(
            id=group_id,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )

        # Act
        result = await repository.get_by_id(group_id, mock_session)

        # Assert
        assert result.is_success
        group = result.value
        assert group.id == group_id
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_name(self, repository, mock_session):
        """Test finding a group by name."""
        # Arrange
        name = "Test Group"
        tenant_id = TEST_TENANT_ID
        mock_session.execute.return_value.scalars.return_value.first.return_value = Group(
            id=TEST_GROUP_ID,
            name=name,
            tenant_id=tenant_id
        )

        # Act
        result = await repository.find_by_name(name, tenant_id, mock_session)

        # Assert
        assert result is not None
        assert result.name == name
        assert result.tenant_id == tenant_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_tenant(self, repository, mock_session):
        """Test finding groups by tenant."""
        # Arrange
        tenant_id = TEST_TENANT_ID
        groups = [
            Group(id="group1", name="Group 1", tenant_id=tenant_id),
            Group(id="group2", name="Group 2", tenant_id=tenant_id)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = groups

        # Act
        result = await repository.find_by_tenant(tenant_id, 10, 0, mock_session)

        # Assert
        assert len(result) == 2
        assert all(group.tenant_id == tenant_id for group in result)
        mock_session.execute.assert_called_once()


# Service Tests

class TestUserService:
    """Tests for the UserService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=UserRepository)

    @pytest.fixture
    def mock_group_repository(self):
        """Create a mock group repository."""
        return AsyncMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_repository, mock_group_repository):
        """Create a UserService instance."""
        service = UserService(repository=mock_repository)
        service.group_repository = mock_group_repository
        return service

    @pytest.mark.asyncio
    async def test_create_user_success(self, service, mock_repository):
        """Test creating a user successfully."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=True
        )
        mock_repository.save.return_value = Success(user)

        # Act
        result = await service.create(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=True
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_USER_ID
        assert result.value.email == "test@example.com"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_validation_error(self, service):
        """Test creating a user with validation error."""
        # Act - Missing required full_name
        result = await service.create(
            id=TEST_USER_ID,
            email="test@example.com",
            handle="testuser",
            full_name="",  # Empty full name
            is_superuser=True
        )

        # Assert
        assert result.is_failure
        assert "Full name cannot be empty" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_email_success(self, service, mock_repository):
        """Test finding a user by email successfully."""
        # Arrange
        email = "test@example.com"
        user = User(
            id=TEST_USER_ID,
            email=email,
            handle="testuser",
            full_name="Test User"
        )
        mock_repository.find_by_email.return_value = user

        # Act
        result = await service.find_by_email(email)

        # Assert
        assert result.is_success
        assert result.value.email == email
        mock_repository.find_by_email.assert_called_once_with(email, None)

    @pytest.mark.asyncio
    async def test_find_by_email_not_found(self, service, mock_repository):
        """Test finding a user by email when not found."""
        # Arrange
        email = "nonexistent@example.com"
        mock_repository.find_by_email.return_value = None

        # Act
        result = await service.find_by_email(email)

        # Assert
        assert result.is_success
        assert result.value is None
        mock_repository.find_by_email.assert_called_once_with(email, None)

    @pytest.mark.asyncio
    async def test_add_to_group_success(self, service, mock_repository, mock_group_repository):
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
        
        mock_repository.get.return_value = user
        mock_group_repository.get.return_value = group
        mock_repository.save.return_value = Success(user)

        # Act
        result = await service.add_to_group(user_id, group_id)

        # Assert
        assert result.is_success
        assert group in result.value.groups
        mock_repository.get.assert_called_once_with(user_id)
        mock_group_repository.get.assert_called_once_with(group_id)
        mock_repository.save.assert_called_once()


class TestGroupService:
    """Tests for the GroupService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=GroupRepository)

    @pytest.fixture
    def mock_user_repository(self):
        """Create a mock user repository."""
        return AsyncMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_repository, mock_user_repository):
        """Create a GroupService instance."""
        service = GroupService(repository=mock_repository)
        service.user_repository = mock_user_repository
        return service

    @pytest.mark.asyncio
    async def test_create_group_success(self, service, mock_repository):
        """Test creating a group successfully."""
        # Arrange
        group = Group(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )
        mock_repository.save.return_value = Success(group)

        # Act
        result = await service.create(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=TEST_TENANT_ID
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_GROUP_ID
        assert result.value.name == "Test Group"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_group_validation_error(self, service):
        """Test creating a group with validation error."""
        # Act - Missing required tenant_id
        result = await service.create(
            id=TEST_GROUP_ID,
            name="Test Group",
            tenant_id=""  # Empty tenant ID
        )

        # Assert
        assert result.is_failure
        assert "Tenant ID cannot be empty" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_name_success(self, service, mock_repository):
        """Test finding a group by name successfully."""
        # Arrange
        name = "Test Group"
        tenant_id = TEST_TENANT_ID
        group = Group(
            id=TEST_GROUP_ID,
            name=name,
            tenant_id=tenant_id
        )
        mock_repository.find_by_name.return_value = group

        # Act
        result = await service.find_by_name(name, tenant_id)

        # Assert
        assert result.is_success
        assert result.value.name == name
        assert result.value.tenant_id == tenant_id
        mock_repository.find_by_name.assert_called_once_with(name, tenant_id, None)

    @pytest.mark.asyncio
    async def test_add_user_success(self, service, mock_repository, mock_user_repository):
        """Test adding a user to a group successfully."""
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
        
        mock_repository.get.return_value = group
        mock_user_repository.get.return_value = user
        mock_repository.save.return_value = Success(group)

        # Act
        result = await service.add_user(group_id, user_id)

        # Assert
        assert result.is_success
        assert user in result.value.users
        mock_repository.get.assert_called_once_with(group_id)
        mock_user_repository.get.assert_called_once_with(user_id)
        mock_repository.save.assert_called_once()