"""
Tests for the protocol testing framework.

This module contains tests for the protocol testing utilities.
"""

import unittest
from typing import Protocol, Optional, List, TypeVar, runtime_checkable
import asyncio

from uno.core.protocol_testing import ProtocolMock, ProtocolTestCase
from uno.core.protocol_validator import ProtocolValidationError, implements


# Define some protocols for testing
T = TypeVar('T')


@runtime_checkable
class Repository(Protocol[T]):
    """Simple repository protocol for testing."""
    
    async def get(self, id: str) -> Optional[T]:
        """Get an entity by id."""
        ...
    
    async def list(self) -> List[T]:
        """List all entities."""
        ...
    
    async def save(self, entity: T) -> T:
        """Save an entity."""
        ...
    
    async def delete(self, id: str) -> bool:
        """Delete an entity by id."""
        ...


class User:
    """Simple user class for testing."""
    
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name


@implements(Repository[User])
class UserRepository:
    """Implementation of Repository[User] for testing."""
    
    def __init__(self):
        self.users = {}
    
    async def get(self, id: str) -> Optional[User]:
        """Get a user by id."""
        return self.users.get(id)
    
    async def list(self) -> List[User]:
        """List all users."""
        return list(self.users.values())
    
    async def save(self, entity: User) -> User:
        """Save a user."""
        self.users[entity.id] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        """Delete a user by id."""
        if id in self.users:
            del self.users[id]
            return True
        return False


class InvalidRepository:
    """Invalid implementation that's missing methods."""
    
    async def get(self, id: str) -> Optional[User]:
        """Get a user by id."""
        return None
    
    # Missing list, save, delete


class TestProtocolMock(unittest.TestCase):
    """Test the ProtocolMock utility."""
    
    def test_create_mock(self):
        """Test creating a mock implementation."""
        # Create a mock
        repo_mock = ProtocolMock[Repository[User]]()
        
        # Configure return values
        user = User(id="1", name="Test")
        repo_mock.configure_method("get", return_value=asyncio.Future())
        repo_mock.mock.get.return_value.set_result(user)
        
        repo_mock.configure_method("list", return_value=asyncio.Future())
        repo_mock.mock.list.return_value.set_result([user])
        
        repo_mock.configure_method("save", return_value=asyncio.Future())
        repo_mock.mock.save.return_value.set_result(user)
        
        repo_mock.configure_method("delete", return_value=asyncio.Future())
        repo_mock.mock.delete.return_value.set_result(True)
        
        # Create the mock implementation
        repo = repo_mock.create()
        
        # Test the implementation
        async def test_repo():
            # Test get
            result_user = await repo.get("1")
            self.assertEqual(result_user, user)
            repo.get.assert_called_once_with("1")
            
            # Test list
            result_users = await repo.list()
            self.assertEqual(result_users, [user])
            repo.list.assert_called_once()
            
            # Test save
            result_user = await repo.save(user)
            self.assertEqual(result_user, user)
            repo.save.assert_called_once_with(user)
            
            # Test delete
            result = await repo.delete("1")
            self.assertTrue(result)
            repo.delete.assert_called_once_with("1")
        
        # Run the async test
        asyncio.run(test_repo())
    
    def test_invalid_protocol(self):
        """Test passing a non-protocol type."""
        with self.assertRaises(TypeError):
            ProtocolMock(User)
    
    def test_missing_method(self):
        """Test configuring a method that doesn't exist in the protocol."""
        repo_mock = ProtocolMock[Repository[User]]()
        with self.assertRaises(AttributeError):
            repo_mock.configure_method("nonexistent_method")


class TestUserRepository(ProtocolTestCase[Repository[User]]):
    """Test a repository implementation using ProtocolTestCase."""
    
    protocol_type = Repository[User]
    implementation_type = UserRepository
    
    def test_implementation_static(self):
        """Test that the implementation passes static validation."""
        self.validate_implementation_static()
    
    def test_invalid_implementation(self):
        """Test that invalid implementations fail validation."""
        with self.assertRaises(ProtocolValidationError):
            self.validate_implementation_static(InvalidRepository)
    
    def test_implementation_runtime(self):
        """Test that the implementation works at runtime."""
        repo = self.create_implementation()
        
        # Test a few operations
        async def test_repo():
            # Create a user
            user = User(id="1", name="Test")
            saved_user = await repo.save(user)
            self.assertEqual(saved_user, user)
            
            # Get the user
            retrieved_user = await repo.get("1")
            self.assertEqual(retrieved_user, user)
            
            # List all users
            users = await repo.list()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0], user)
            
            # Delete the user
            result = await repo.delete("1")
            self.assertTrue(result)
            
            # Verify the user is gone
            self.assertEqual(await repo.get("1"), None)
            self.assertEqual(await repo.list(), [])
        
        # Run the async test
        asyncio.run(test_repo())
    
    def test_mock_creation(self):
        """Test creating a mock implementation."""
        repo_mock = self.create_mock()
        self.assertIsInstance(repo_mock, ProtocolMock)
        
        # Configure the mock
        repo_mock.configure_method("get", return_value=asyncio.Future())
        repo_mock.mock.get.return_value.set_result(None)
        
        # Create the implementation
        repo = repo_mock.create()
        
        # Test it
        async def test_mock():
            result = await repo.get("1")
            self.assertIsNone(result)
            repo.get.assert_called_once_with("1")
        
        # Run the async test
        asyncio.run(test_mock())


if __name__ == "__main__":
    unittest.main()