"""
Tests for authorization services.

This module contains tests for the User and Group services.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from uno.dependencies.testing import MockRepository
from uno.authorization.models import UserModel, GroupModel
from uno.authorization.services import UserService, GroupService


class TestUserService:
    """Tests for the UserService class."""
    
    @pytest.mark.asyncio
    async def test_execute_with_tenant_filter(self):
        """Test executing with tenant filter."""
        # Create test users
        test_users = [
            MagicMock(id="test-id-1", email="user1@example.com"),
            MagicMock(id="test-id-2", email="user2@example.com")
        ]
        
        # Create a mock repository with custom methods
        mock_repo = MockRepository.with_items(test_users)
        mock_repo.find_by_tenant = AsyncMock(return_value=test_users)
        
        # Create service and call execute
        service = UserService(mock_repo)
        result = await service.execute(tenant_id="tenant-1")
        
        # Verify the result
        assert result == test_users
        
        # Verify the repository method was called
        mock_repo.find_by_tenant.assert_called_once_with(
            tenant_id="tenant-1", 
            limit=None, 
            offset=None
        )
        
    @pytest.mark.asyncio
    async def test_execute_with_superusers_filter(self):
        """Test executing with superusers filter."""
        # Create test users
        test_users = [
            MagicMock(id="test-id-1", email="admin@example.com", is_superuser=True)
        ]
        
        # Create a mock repository with custom methods
        mock_repo = MockRepository.with_items(test_users)
        mock_repo.find_superusers = AsyncMock(return_value=test_users)
        
        # Create service and call execute
        service = UserService(mock_repo)
        result = await service.execute(superusers_only=True)
        
        # Verify the result
        assert result == test_users
        
        # Verify the repository method was called
        mock_repo.find_superusers.assert_called_once_with(
            limit=None, 
            offset=None
        )
        
    @pytest.mark.asyncio
    async def test_get_user_by_email_or_handle_email(self):
        """Test getting a user by email."""
        # Create a test user
        test_user = MagicMock(id="test-id", email="test@example.com")
        
        # Create a mock repository with custom methods
        mock_repo = MockRepository.create()
        mock_repo.find_by_email = AsyncMock(return_value=test_user)
        
        # Create service and call method
        service = UserService(mock_repo)
        result = await service.get_user_by_email_or_handle("test@example.com")
        
        # Verify the result
        assert result == test_user
        
        # Verify the repository method was called
        mock_repo.find_by_email.assert_called_once_with("test@example.com")
        
    @pytest.mark.asyncio
    async def test_get_user_by_email_or_handle_handle(self):
        """Test getting a user by handle."""
        # Create a test user
        test_user = MagicMock(id="test-id", handle="testuser")
        
        # Create a mock repository with custom methods
        mock_repo = MockRepository.create()
        mock_repo.find_by_email = AsyncMock(return_value=None)
        mock_repo.find_by_handle = AsyncMock(return_value=test_user)
        
        # Create service and call method
        service = UserService(mock_repo)
        result = await service.get_user_by_email_or_handle("testuser", tenant_id="tenant-1")
        
        # Verify the result
        assert result == test_user
        
        # Verify the repository methods were called
        mock_repo.find_by_email.assert_called_once_with("testuser")
        mock_repo.find_by_handle.assert_called_once_with(
            handle="testuser", 
            tenant_id="tenant-1"
        )


class TestGroupService:
    """Tests for the GroupService class."""
    
    @pytest.mark.asyncio
    async def test_execute_with_tenant_filter(self):
        """Test executing with tenant filter."""
        # Create test groups
        test_groups = [
            MagicMock(id="test-id-1", name="Group One"),
            MagicMock(id="test-id-2", name="Group Two")
        ]
        
        # Create a mock repository with custom methods
        mock_repo = MockRepository.with_items(test_groups)
        mock_repo.find_by_tenant = AsyncMock(return_value=test_groups)
        
        # Create service and call execute
        service = GroupService(mock_repo)
        result = await service.execute(tenant_id="tenant-1")
        
        # Verify the result
        assert result == test_groups
        
        # Verify the repository method was called
        mock_repo.find_by_tenant.assert_called_once_with(
            tenant_id="tenant-1", 
            limit=None, 
            offset=None
        )
        
    @pytest.mark.asyncio
    async def test_execute_with_name_filter(self):
        """Test executing with name filter."""
        # Create a test group
        test_group = MagicMock(id="test-id", name="Test Group")
        
        # Create a mock repository with custom methods
        mock_repo = MockRepository.create()
        mock_repo.find_by_name = AsyncMock(return_value=test_group)
        
        # Create service and call execute
        service = GroupService(mock_repo)
        result = await service.execute(tenant_id="tenant-1", name="Test Group")
        
        # Verify the result
        assert result == [test_group]
        
        # Verify the repository method was called
        mock_repo.find_by_name.assert_called_once_with(
            name="Test Group", 
            tenant_id="tenant-1"
        )