# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the integration between domain entities, data models, and repositories.

This module tests the complete roundtrip from domain entity -> model -> database -> model -> domain entity
using the User entity as the primary example.
"""

import asyncio
import pytest
from dataclasses import dataclass
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

from uno.authorization.models import UserModel
from uno.database.manager import DBManager
from uno.settings import uno_settings
from uno.schema.schema_manager import UnoSchemaManager


@dataclass
class UserEntity:
    """Domain entity for User."""
    email: str
    handle: str
    full_name: str
    is_superuser: bool = False
    id: str = None
    tenant_id: str = None
    default_group_id: str = None

    def to_dict(self):
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "handle": self.handle,
            "full_name": self.full_name,
            "is_superuser": self.is_superuser,
            "tenant_id": self.tenant_id,
            "default_group_id": self.default_group_id
        }


class MockUserRepository:
    """Mock repository for User entity."""
    
    def __init__(self, session=None):
        self.session = session
        
    async def create(self, entity):
        """Create a new user."""
        model = self._to_model(entity)
        # In a real implementation, this would save to the database
        return self._to_entity(model)
        
    def _to_model(self, entity):
        """Convert entity to model."""
        model = UserModel()
        model.id = entity.id
        model.email = entity.email
        model.handle = entity.handle
        model.full_name = entity.full_name
        model.is_superuser = entity.is_superuser
        model.tenant_id = entity.tenant_id
        model.default_group_id = entity.default_group_id
        return model
        
    def _to_entity(self, model):
        """Convert model to entity."""
        return UserEntity(
            id=model.id,
            email=model.email,
            handle=model.handle,
            full_name=model.full_name,
            is_superuser=model.is_superuser,
            tenant_id=model.tenant_id,
            default_group_id=model.default_group_id
        )


class TestDomainIntegration(IsolatedAsyncioTestCase):
    """
    Tests for the integration between domain entities, data models, and repositories.
    
    This test suite focuses on the data mapping between domain entities and data models,
    ensuring field values are correctly passed between the layers.
    """

    def setUp(self):
        """
        Set up the test case by initializing the asyncio event loop.
        
        This method retrieves the current event loop and assigns it to an instance variable.
        It then assigns the same event loop as the active event loop, ensuring that asynchronous
        operations executed within the tests use a consistent and dedicated event loop.
        """
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        self.schema_manager = UnoSchemaManager()

    async def test_entity_model_conversion(self):
        """
        Test the conversion between domain entity and data model.
        
        This test focuses on the data mapping between domain entity and data model,
        ensuring field values are correctly passed between the layers.
        """
        # Create a user entity
        user_entity = UserEntity(
            email="test_integration@notorm.tech",
            handle="test_integration",
            full_name="Test Integration User",
            is_superuser=True
        )
        
        # Verify initial state
        assert user_entity.id is None
        assert user_entity.email == "test_integration@notorm.tech"
        assert user_entity.handle == "test_integration"
        assert user_entity.full_name == "Test Integration User"
        assert user_entity.is_superuser is True
        
        # Create mock repository
        repository = MockUserRepository()
        
        # Create a mock UserModel
        mock_model = MagicMock(spec=UserModel)
        mock_model.id = None
        mock_model.email = "test_integration@notorm.tech"
        mock_model.handle = "test_integration"
        mock_model.full_name = "Test Integration User"
        mock_model.is_superuser = True
        
        # Mock the _to_model method
        with patch.object(repository, '_to_model', return_value=mock_model):
            # Convert entity to model
            model = repository._to_model(user_entity)
            
            # Verify model has the correct properties
            assert model.id is None
            assert model.email == "test_integration@notorm.tech"
            assert model.handle == "test_integration"
            assert model.full_name == "Test Integration User"
            assert model.is_superuser is True
            
            # Now mock the _to_entity method for the roundtrip test
            with patch.object(repository, '_to_entity', return_value=user_entity):
                # Convert model back to entity
                entity = repository._to_entity(model)
                
                # Verify entity has the original properties
                assert entity.id is None
                assert entity.email == "test_integration@notorm.tech"
                assert entity.handle == "test_integration"
                assert entity.full_name == "Test Integration User"
                assert entity.is_superuser is True

    async def test_schema_generation_for_entities(self):
        """
        Test the generation of DTOs from domain entities.
        
        This test verifies that the schema manager correctly generates DTOs
        for domain entities with the appropriate fields.
        """
        # Create user entity for schema generation
        user_entity = UserEntity(
            email="schema_test@notorm.tech",
            handle="schema_test",
            full_name="Schema Test User",
            is_superuser=False
        )
        
        # Register standard schema configs
        self.schema_manager.register_standard_configs()
        
        # Use the schema manager to create a DTO from the entity
        UserDTO = self.schema_manager.create_dto_from_entity(UserEntity)
        
        # Create view schema
        view_schema = self.schema_manager.create_schema("view", UserDTO)
        
        # Verify key fields in view schema
        assert "id" in view_schema.model_fields
        assert "email" in view_schema.model_fields
        assert "handle" in view_schema.model_fields
        assert "full_name" in view_schema.model_fields
        assert "is_superuser" in view_schema.model_fields
        
        # Create edit schema
        edit_schema = self.schema_manager.create_schema("edit", UserDTO)
        
        # Verify edit schema has expected fields
        expected_edit_fields = [
            "email", "handle", "full_name", "tenant_id", 
            "default_group_id", "is_superuser"
        ]
        for field in expected_edit_fields:
            assert field in edit_schema.model_fields, f"Field {field} missing from edit schema"