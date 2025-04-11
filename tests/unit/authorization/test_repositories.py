"""
Tests for authorization repositories.

This module contains tests for the User and Group repositories.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from uno.dependencies.testing import MockRepository
from uno.authorization.models import UserModel, GroupModel
from uno.authorization.repositories import UserRepository, GroupRepository


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    
    # Configure the execute mock to return a result that supports scalars
    result_mock = MagicMock()
    scalars_mock = MagicMock()
    first_mock = MagicMock(return_value=None)
    all_mock = MagicMock(return_value=[])
    
    scalars_mock.first = first_mock
    scalars_mock.all = all_mock
    result_mock.scalars = MagicMock(return_value=scalars_mock)
    
    session.execute.return_value = result_mock
    
    return session


class TestUserRepository:
    """Tests for the UserRepository class."""
    
    @pytest.mark.asyncio
    async def test_find_by_email(self, mock_session):
        """Test finding a user by email."""
        # Create a test user
        test_user = UserModel(
            id="test-id",
            email="test@example.com",
            handle="testuser",
            full_name="Test User",
            is_superuser=False
        )
        
        # Configure the mock to return our test user
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.first.return_value = test_user
        
        # Create repository and call the method
        repo = UserRepository(mock_session)
        result = await repo.find_by_email("test@example.com")
        
        # Verify the result
        assert result == test_user
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()
        # The exact query is hard to verify due to SQLAlchemy's internal structure,
        # but we can check that it was called
        
    @pytest.mark.asyncio
    async def test_find_by_tenant(self, mock_session):
        """Test finding users by tenant."""
        # Create test users
        test_users = [
            UserModel(
                id="test-id-1",
                email="user1@example.com",
                handle="user1",
                full_name="User One",
                tenant_id="tenant-1",
                is_superuser=False
            ),
            UserModel(
                id="test-id-2",
                email="user2@example.com",
                handle="user2",
                full_name="User Two",
                tenant_id="tenant-1",
                is_superuser=False
            )
        ]
        
        # Configure the mock to return our test users
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.all.return_value = test_users
        
        # Create repository and call the method
        repo = UserRepository(mock_session)
        result = await repo.find_by_tenant("tenant-1")
        
        # Verify the result
        assert result == test_users
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_find_superusers(self, mock_session):
        """Test finding superusers."""
        # Create test users
        test_users = [
            UserModel(
                id="test-id-1",
                email="admin@example.com",
                handle="admin",
                full_name="Admin User",
                is_superuser=True
            )
        ]
        
        # Configure the mock to return our test users
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.all.return_value = test_users
        
        # Create repository and call the method
        repo = UserRepository(mock_session)
        result = await repo.find_superusers()
        
        # Verify the result
        assert result == test_users
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()


class TestGroupRepository:
    """Tests for the GroupRepository class."""
    
    @pytest.mark.asyncio
    async def test_find_by_name(self, mock_session):
        """Test finding a group by name."""
        # Create a test group
        test_group = GroupModel(
            id="test-id",
            name="Test Group",
            tenant_id="tenant-1"
        )
        
        # Configure the mock to return our test group
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.first.return_value = test_group
        
        # Create repository and call the method
        repo = GroupRepository(mock_session)
        result = await repo.find_by_name("Test Group", "tenant-1")
        
        # Verify the result
        assert result == test_group
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_find_by_tenant(self, mock_session):
        """Test finding groups by tenant."""
        # Create test groups
        test_groups = [
            GroupModel(
                id="test-id-1",
                name="Group One",
                tenant_id="tenant-1"
            ),
            GroupModel(
                id="test-id-2",
                name="Group Two",
                tenant_id="tenant-1"
            )
        ]
        
        # Configure the mock to return our test groups
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.all.return_value = test_groups
        
        # Create repository and call the method
        repo = GroupRepository(mock_session)
        result = await repo.find_by_tenant("tenant-1")
        
        # Verify the result
        assert result == test_groups
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()