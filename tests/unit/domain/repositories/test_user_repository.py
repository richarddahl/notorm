"""
Tests for the User repository implementation.
"""

import pytest
from typing import Dict, Any, List, Optional, AsyncGenerator, cast
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.models import User, UserRole
from uno.domain.specifications import AttributeSpecification, AndSpecification, OrSpecification
from uno.domain.repositories.sqlalchemy.user import UserRepository, UserModel


class TestUserRepository:
    
    @pytest.fixture
    def session_factory(self):
        """Create a session factory with a mock session."""
        session_mock = AsyncMock(spec=AsyncSession)
        session_mock.__aenter__.return_value = session_mock
        session_mock.__aexit__.return_value = None
        
        def factory():
            return session_mock
        
        # Store session mock for assertions
        factory.session_mock = session_mock
        
        return factory
    
    @pytest.fixture
    def repository(self, session_factory):
        """Create a user repository with the mock session factory."""
        return UserRepository(session_factory=session_factory)
    
    @pytest.fixture
    def user_model(self):
        """Create a sample user model."""
        return UserModel(
            id="1",
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            full_name="Test User",
            role="user",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def user_entity(self):
        """Create a sample user entity."""
        return User(
            id="1",
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    async def test_find_by_username(self, repository, session_factory, user_model):
        """Test finding a user by username."""
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user_model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find user by username
        user = await repository.find_by_username("testuser")
        
        # Verify user
        assert user is not None
        assert user.id == "1"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_email(self, repository, session_factory, user_model):
        """Test finding a user by email."""
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user_model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find user by email
        user = await repository.find_by_email("test@example.com")
        
        # Verify user
        assert user is not None
        assert user.id == "1"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_username_or_email(self, repository, session_factory, user_model):
        """Test finding a user by username or email."""
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user_model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find user by username or email
        user = await repository.find_by_username_or_email("test@example.com")
        
        # Verify user
        assert user is not None
        assert user.id == "1"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_active(self, repository, session_factory, user_model):
        """Test finding active users."""
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [user_model]
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find active users
        users = await repository.find_active()
        
        # Verify users
        assert len(users) == 1
        assert users[0].id == "1"
        assert users[0].username == "testuser"
        assert users[0].is_active is True
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_role(self, repository, session_factory, user_model):
        """Test finding users by role."""
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [user_model]
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find users by role
        users = await repository.find_by_role(UserRole.USER)
        
        # Verify users
        assert len(users) == 1
        assert users[0].id == "1"
        assert users[0].role == UserRole.USER
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_active_by_role(self, repository, session_factory, user_model):
        """Test finding active users by role."""
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [user_model]
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find active users by role
        users = await repository.find_active_by_role(UserRole.USER)
        
        # Verify users
        assert len(users) == 1
        assert users[0].id == "1"
        assert users[0].role == UserRole.USER
        assert users[0].is_active is True
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate(self, repository, session_factory, user_entity, user_model):
        """Test deactivating a user."""
        # Mock session execute result for update
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user_model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Deactivate user
        await repository.deactivate(user_entity)
        
        # Verify user was deactivated
        assert user_entity.is_active is False
        assert user_entity.updated_at is not None
        
        # Verify session was used correctly
        assert session_factory.session_mock.execute.call_count == 1
        assert session_factory.session_mock.commit.call_count == 1
    
    @pytest.mark.asyncio
    async def test_activate(self, repository, session_factory, user_entity, user_model):
        """Test activating a user."""
        # Set user as inactive first
        user_entity.is_active = False
        user_model.is_active = False
        
        # Mock session execute result for update
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user_model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Activate user
        await repository.activate(user_entity)
        
        # Verify user was activated
        assert user_entity.is_active is True
        assert user_entity.updated_at is not None
        
        # Verify session was used correctly
        assert session_factory.session_mock.execute.call_count == 1
        assert session_factory.session_mock.commit.call_count == 1
    
    @pytest.mark.asyncio
    async def test_change_role(self, repository, session_factory, user_entity, user_model):
        """Test changing a user's role."""
        # Mock session execute result for update
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user_model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Change user role
        await repository.change_role(user_entity, UserRole.ADMIN)
        
        # Verify user role was changed
        assert user_entity.role == UserRole.ADMIN
        assert user_entity.updated_at is not None
        
        # Verify session was used correctly
        assert session_factory.session_mock.execute.call_count == 1
        assert session_factory.session_mock.commit.call_count == 1