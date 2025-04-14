# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example integration test using the Uno testing utilities.

This module demonstrates how to use the integration testing utilities
to write effective integration tests for Uno applications.
"""

import os
import pytest
import pytest_asyncio
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from uno.database.repository import Repository
from uno.dependencies.modern_provider import ServiceProvider
from uno.testing.integration import IntegrationTestHarness, TestEnvironment
from uno.testing.mock_data.generators import ModelDataGenerator


# Define test models, repositories, and services for demonstration

Base = declarative_base()


class User(Base):
    """Example user model for demonstration."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    bio = Column(Text, nullable=True)


class UserCreateDTO(BaseModel):
    """Data transfer object for creating a user."""
    username: str
    email: str
    bio: str = None


class UserResponseDTO(BaseModel):
    """Data transfer object for user responses."""
    id: int
    username: str
    email: str
    bio: str = None


class UserRepository(Repository):
    """Repository for user operations."""
    
    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def get_by_id(self, user_id: int) -> User:
        """Get a user by ID."""
        query = f"SELECT * FROM users WHERE id = :id"
        result = await self.session.execute(query, {"id": user_id})
        return result.mappings().first()
    
    async def get_by_username(self, username: str) -> User:
        """Get a user by username."""
        query = f"SELECT * FROM users WHERE username = :username"
        result = await self.session.execute(query, {"username": username})
        return result.mappings().first()
    
    async def list_users(self, limit: int = 10, offset: int = 0) -> list:
        """List users with pagination."""
        query = f"SELECT * FROM users LIMIT :limit OFFSET :offset"
        result = await self.session.execute(query, {"limit": limit, "offset": offset})
        return result.mappings().all()


class UserService:
    """Service for user operations."""
    
    def __init__(self, repository: UserRepository):
        """Initialize the user service."""
        self.repository = repository
    
    async def create_user(self, user_data: UserCreateDTO) -> User:
        """Create a new user."""
        # Check if username is taken
        existing = await self.repository.get_by_username(user_data.username)
        if existing:
            raise ValueError("Username already taken")
            
        # Create the user
        user_dict = user_data.dict()
        return await self.repository.create(user_dict)
    
    async def get_user(self, user_id: int) -> User:
        """Get a user by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user
    
    async def list_users(self, limit: int = 10, offset: int = 0) -> list:
        """List users with pagination."""
        return await self.repository.list_users(limit, offset)


# Integration test setup

@pytest.fixture(scope="module")
def integration_harness():
    """Create an integration test harness."""
    harness = IntegrationTestHarness(
        services=[IntegrationTestHarness.get_postgres_config()]
    )
    with harness.start_services():
        yield harness


@pytest_asyncio.fixture
async def setup_database(integration_harness):
    """Set up the database with tables for testing."""
    # Get connection string
    db_url = integration_harness.get_connection_string("postgres")
    
    # Create tables
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.schema import CreateTable
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        await conn.execute(CreateTable(User.__table__))
    
    yield db_url


@pytest_asyncio.fixture
async def test_environment(integration_harness, setup_database):
    """Create a test environment."""
    async with integration_harness.create_test_environment() as env:
        yield env


# Test examples

async def test_user_repository(test_environment):
    """Test the user repository."""
    # Get repository from the environment
    repo = test_environment.get_repository(UserRepository)
    
    # Create test user data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "bio": "This is a test user"
    }
    
    # Create a user
    await repo.create(user_data)
    
    # Fetch the user
    user = await repo.get_by_username("testuser")
    
    # Verify user properties
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"
    assert user["bio"] == "This is a test user"


async def test_user_service(test_environment):
    """Test the user service."""
    # Get repository from the environment
    repo = test_environment.get_repository(UserRepository)
    
    # Create service with repository
    service = UserService(repo)
    
    # Create test user
    user_data = UserCreateDTO(
        username="serviceuser",
        email="service@example.com",
        bio="This is a service test"
    )
    
    # Create a user through the service
    user = await service.create_user(user_data)
    
    # Fetch users
    users = await service.list_users()
    
    # Verify user list
    assert len(users) == 1
    assert users[0]["username"] == "serviceuser"


async def test_with_mock_data(test_environment):
    """Test using mock data generators."""
    # Get repository from the environment
    repo = test_environment.get_repository(UserRepository)
    
    # Create a mock data generator
    generator = ModelDataGenerator(seed=42)
    
    # Generate user data
    user_data = generator.generate_for_model(UserCreateDTO)
    
    # Create a user
    await repo.create(user_data)
    
    # Verify the user exists
    user = await repo.get_by_username(user_data["username"])
    assert user is not None
    assert user["email"] == user_data["email"]


async def test_with_bulk_data(test_environment):
    """Test loading bulk test data."""
    # Create test data
    test_data = {
        "users": [
            {"username": "bulk1", "email": "bulk1@example.com", "bio": "Bulk test user 1"},
            {"username": "bulk2", "email": "bulk2@example.com", "bio": "Bulk test user 2"},
            {"username": "bulk3", "email": "bulk3@example.com", "bio": "Bulk test user 3"}
        ]
    }
    
    # Set up test data
    await test_environment.db.bulk_insert("users", test_data["users"])
    
    # Verify data loaded correctly
    count = await test_environment.db.count_rows("users", "username LIKE 'bulk%'")
    assert count == 3
    
    # Verify specific user
    user = await test_environment.db.execute_sql(
        "SELECT * FROM users WHERE username = :username",
        username="bulk2"
    )
    user_row = user.mappings().first()
    assert user_row["email"] == "bulk2@example.com"