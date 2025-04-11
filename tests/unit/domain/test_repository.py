"""
Unit tests for the domain repository implementations.
"""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from uno.domain.core import Entity, DomainException
from uno.domain.repository import Repository, UnoDBRepository


class TestEntity(Entity):
    """Test entity for repository tests."""
    name: str
    description: str = ""
    
    
@pytest.fixture
def mock_db_factory():
    """Create a mock DB factory."""
    db_mock = AsyncMock()
    db_factory_mock = MagicMock()
    db_factory_mock.return_value = db_mock
    return db_factory_mock


@pytest.fixture
def test_entity():
    """Create a test entity for tests."""
    return TestEntity(
        id="test-id-123",
        name="Test Entity",
        description="Test description",
        created_at=datetime(2023, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def entity_dict():
    """Create a dictionary representation of a test entity."""
    return {
        "id": "test-id-123",
        "name": "Test Entity",
        "description": "Test description",
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "updated_at": None
    }


class TestUnoDBRepository:
    """Test the UnoDBRepository implementation."""
    
    def test_init(self, mock_db_factory):
        """Test repository initialization."""
        repo = UnoDBRepository(TestEntity, db_factory=mock_db_factory)
        assert repo.entity_type == TestEntity
        assert repo.db_factory == mock_db_factory
        assert repo._db is None
    
    @pytest.mark.asyncio
    async def test_get_entity_found(self, mock_db_factory, entity_dict):
        """Test getting an entity that exists."""
        db_mock = AsyncMock()
        db_mock.get.return_value = entity_dict
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            entity = await repo.get("test-id-123")
            
            assert entity is not None
            assert isinstance(entity, TestEntity)
            assert entity.id == "test-id-123"
            assert entity.name == "Test Entity"
            assert entity.description == "Test description"
            
            db_mock.get.assert_called_once_with(id="test-id-123")
    
    @pytest.mark.asyncio
    async def test_get_entity_not_found(self, mock_db_factory):
        """Test getting an entity that doesn't exist."""
        db_mock = AsyncMock()
        db_mock.get.return_value = None
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            entity = await repo.get("nonexistent-id")
            
            assert entity is None
            db_mock.get.assert_called_once_with(id="nonexistent-id")
    
    @pytest.mark.asyncio
    async def test_get_entity_exception(self, mock_db_factory):
        """Test handling exceptions when getting an entity."""
        from uno.database.db import NotFoundException
        
        db_mock = AsyncMock()
        db_mock.get.side_effect = NotFoundException("Entity not found")
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            entity = await repo.get("test-id-123")
            
            assert entity is None
            db_mock.get.assert_called_once_with(id="test-id-123")
    
    @pytest.mark.asyncio
    async def test_list_entities(self, mock_db_factory, entity_dict):
        """Test listing entities with filters."""
        db_mock = AsyncMock()
        db_mock.filter.return_value = [entity_dict, entity_dict]
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            entities = await repo.list(
                filters={"name": "Test"},
                order_by=["name"],
                limit=10,
                offset=0
            )
            
            assert len(entities) == 2
            assert all(isinstance(e, TestEntity) for e in entities)
            assert all(e.name == "Test Entity" for e in entities)
            
            # Check that filter conversion was handled correctly
            db_mock.filter.assert_called_once()
            call_args = db_mock.filter.call_args
            assert call_args is not None
            
            # Filter params were converted correctly
            filter_params = call_args.kwargs.get('filters') or call_args.args[0]
            assert filter_params is not None
            
    @pytest.mark.asyncio
    async def test_add_entity(self, mock_db_factory, test_entity, entity_dict):
        """Test adding a new entity."""
        db_mock = AsyncMock()
        db_mock.create.return_value = (entity_dict, True)
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            result = await repo.add(test_entity)
            
            assert result is not None
            assert isinstance(result, TestEntity)
            assert result.id == test_entity.id
            assert result.name == test_entity.name
            
            db_mock.create.assert_called_once()
            call_args = db_mock.create.call_args
            assert call_args is not None
            
            # Entity data was converted correctly
            model_data = call_args.args[0]
            assert model_data is not None
            assert model_data.get('id') == test_entity.id
            assert model_data.get('name') == test_entity.name
    
    @pytest.mark.asyncio
    async def test_add_entity_duplicate(self, mock_db_factory, test_entity):
        """Test adding a duplicate entity."""
        from uno.database.db import UniqueViolationError
        
        db_mock = AsyncMock()
        db_mock.create.side_effect = UniqueViolationError()
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            
            with pytest.raises(DomainException) as exc_info:
                await repo.add(test_entity)
                
            assert "Entity already exists" in str(exc_info.value)
            assert exc_info.value.code == "ALREADY_EXISTS"
    
    @pytest.mark.asyncio
    async def test_update_entity(self, mock_db_factory, test_entity, entity_dict):
        """Test updating an existing entity."""
        db_mock = AsyncMock()
        # Entity exists
        db_mock.get.return_value = entity_dict
        # Update succeeds
        db_mock.update.return_value = entity_dict
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            
            # Modify entity
            test_entity.name = "Updated Name"
            result = await repo.update(test_entity)
            
            assert result is not None
            assert isinstance(result, TestEntity)
            
            # Check that the update was called with the expected data
            db_mock.update.assert_called_once()
            call_args = db_mock.update.call_args
            assert call_args is not None
            
            # Entity data was converted correctly
            model_data = call_args.args[0]
            assert model_data is not None
            assert model_data.get('name') == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_entity_not_found(self, mock_db_factory, test_entity):
        """Test updating a non-existent entity."""
        db_mock = AsyncMock()
        # Entity doesn't exist
        db_mock.get.return_value = None
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            
            with pytest.raises(DomainException) as exc_info:
                await repo.update(test_entity)
                
            assert "not found" in str(exc_info.value)
            assert exc_info.value.code == "NOT_FOUND"
            
            # Update should not be called if entity doesn't exist
            db_mock.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_entity(self, mock_db_factory, test_entity):
        """Test removing an entity."""
        db_mock = AsyncMock()
        db_mock.delete.return_value = True
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            await repo.remove(test_entity)
            
            db_mock.delete.assert_called_once_with(id=test_entity.id)
    
    @pytest.mark.asyncio
    async def test_remove_by_id(self, mock_db_factory):
        """Test removing an entity by ID."""
        db_mock = AsyncMock()
        db_mock.delete.return_value = True
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            result = await repo.remove_by_id("test-id-123")
            
            assert result is True
            db_mock.delete.assert_called_once_with(id="test-id-123")
    
    @pytest.mark.asyncio
    async def test_remove_by_id_not_found(self, mock_db_factory):
        """Test removing a non-existent entity."""
        from uno.database.db import NotFoundException
        
        db_mock = AsyncMock()
        db_mock.delete.side_effect = NotFoundException("Entity not found")
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            result = await repo.remove_by_id("nonexistent-id")
            
            assert result is False
            db_mock.delete.assert_called_once_with(id="nonexistent-id")
    
    @pytest.mark.asyncio
    async def test_exists(self, mock_db_factory, entity_dict):
        """Test checking if an entity exists."""
        db_mock = AsyncMock()
        db_mock.get.return_value = entity_dict
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            result = await repo.exists("test-id-123")
            
            assert result is True
            db_mock.get.assert_called_once_with(id="test-id-123")
    
    @pytest.mark.asyncio
    async def test_exists_not_found(self, mock_db_factory):
        """Test checking if a non-existent entity exists."""
        from uno.database.db import NotFoundException
        
        db_mock = AsyncMock()
        db_mock.get.side_effect = NotFoundException("Entity not found")
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            result = await repo.exists("nonexistent-id")
            
            assert result is False
            db_mock.get.assert_called_once_with(id="nonexistent-id")
    
    @pytest.mark.asyncio
    async def test_count(self, mock_db_factory, entity_dict):
        """Test counting entities with filters."""
        db_mock = AsyncMock()
        db_mock.filter.return_value = [entity_dict, entity_dict]
        
        with patch('uno.database.db.UnoDBFactory', return_value=db_mock):
            repo = UnoDBRepository(TestEntity)
            count = await repo.count(filters={"name": "Test"})
            
            assert count == 2
            
            # Filter was passed correctly
            db_mock.filter.assert_called_once()
            call_args = db_mock.filter.call_args
            assert call_args is not None