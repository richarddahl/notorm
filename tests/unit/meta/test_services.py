"""
Tests for meta services.

This module contains tests for the MetaType and MetaRecord services.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from uno.dependencies.testing import MockRepository
from uno.meta.models import MetaTypeModel, MetaRecordModel
from uno.meta.services import MetaTypeService, MetaRecordService


class TestMetaTypeService:
    """Tests for the MetaTypeService class."""
    
    @pytest.mark.asyncio
    async def test_execute_with_type_id(self):
        """Test executing with a type ID."""
        # Create a test meta type
        test_type = MagicMock(id="user")
        
        # Create a mock repository
        mock_repo = MockRepository.create()
        mock_repo.get_type_by_id = AsyncMock(return_value=test_type)
        
        # Create service and call execute
        service = MetaTypeService(mock_repo)
        result = await service.execute(type_id="user")
        
        # Verify the result
        assert len(result) == 1
        assert result[0] == test_type
        
        # Verify the repository method was called
        mock_repo.get_type_by_id.assert_called_once_with("user")
    
    @pytest.mark.asyncio
    async def test_execute_with_type_id_not_found(self):
        """Test executing with a type ID that doesn't exist."""
        # Create a mock repository
        mock_repo = MockRepository.create()
        mock_repo.get_type_by_id = AsyncMock(return_value=None)
        
        # Create service and call execute
        service = MetaTypeService(mock_repo)
        result = await service.execute(type_id="nonexistent")
        
        # Verify the result is an empty list
        assert result == []
        
        # Verify the repository method was called
        mock_repo.get_type_by_id.assert_called_once_with("nonexistent")
    
    @pytest.mark.asyncio
    async def test_execute_all_types(self):
        """Test executing without a type ID to get all types."""
        # Create test meta types
        test_types = [
            MagicMock(id="user"),
            MagicMock(id="group")
        ]
        
        # Create a mock repository
        mock_repo = MockRepository.create()
        mock_repo.get_all_types = AsyncMock(return_value=test_types)
        
        # Create service and call execute
        service = MetaTypeService(mock_repo)
        result = await service.execute()
        
        # Verify the result
        assert result == test_types
        
        # Verify the repository method was called
        mock_repo.get_all_types.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_type(self):
        """Test getting a specific type."""
        # Create a test meta type
        test_type = MagicMock(id="user")
        
        # Create a mock repository
        mock_repo = MockRepository.create()
        mock_repo.get_type_by_id = AsyncMock(return_value=test_type)
        
        # Create service and call method
        service = MetaTypeService(mock_repo)
        result = await service.get_type("user")
        
        # Verify the result
        assert result == test_type
        
        # Verify the repository method was called
        mock_repo.get_type_by_id.assert_called_once_with("user")


class TestMetaRecordService:
    """Tests for the MetaRecordService class."""
    
    @pytest.mark.asyncio
    async def test_execute_with_record_id(self):
        """Test executing with a record ID."""
        # Create a test meta record
        test_record = MagicMock(id="record-1", meta_type_id="user")
        
        # Create a mock repository
        mock_repo = MockRepository.create()
        mock_repo.get = AsyncMock(return_value=test_record)
        
        # Create service and call execute
        service = MetaRecordService(mock_repo)
        result = await service.execute(record_id="record-1")
        
        # Verify the result
        assert len(result) == 1
        assert result[0] == test_record
        
        # Verify the repository method was called
        mock_repo.get.assert_called_once_with("record-1")
    
    @pytest.mark.asyncio
    async def test_execute_with_record_ids(self):
        """Test executing with a list of record IDs."""
        # Create test meta records
        test_records = [
            MagicMock(id="record-1", meta_type_id="user"),
            MagicMock(id="record-2", meta_type_id="user")
        ]
        
        # Create a mock repository
        mock_repo = MockRepository.create()
        mock_repo.find_by_ids = AsyncMock(return_value=test_records)
        
        # Create service and call execute
        service = MetaRecordService(mock_repo)
        result = await service.execute(record_ids=["record-1", "record-2"])
        
        # Verify the result
        assert result == test_records
        
        # Verify the repository method was called
        mock_repo.find_by_ids.assert_called_once_with(["record-1", "record-2"])
    
    @pytest.mark.asyncio
    async def test_execute_with_type_id(self):
        """Test executing with a type ID."""
        # Create test meta records
        test_records = [
            MagicMock(id="record-1", meta_type_id="user"),
            MagicMock(id="record-2", meta_type_id="user")
        ]
        
        # Create a mock repository
        mock_repo = MockRepository.create()
        mock_repo.find_by_type = AsyncMock(return_value=test_records)
        
        # Create service and call execute
        service = MetaRecordService(mock_repo)
        result = await service.execute(type_id="user")
        
        # Verify the result
        assert result == test_records
        
        # Verify the repository method was called
        mock_repo.find_by_type.assert_called_once_with(
            type_id="user",
            limit=None,
            offset=None
        )
    
    @pytest.mark.asyncio
    async def test_create_record_with_type_service(self):
        """Test creating a record with type verification."""
        # Create a test meta type and record
        test_type = MagicMock(id="user")
        test_record = MagicMock(id="record-1", meta_type_id="user")
        
        # Create a mock repository and type service
        mock_repo = MockRepository.create()
        mock_repo.create_with_type = AsyncMock(return_value=test_record)
        
        mock_type_service = MagicMock()
        mock_type_service.get_type = AsyncMock(return_value=test_type)
        
        # Create service and call method
        service = MetaRecordService(mock_repo, type_service=mock_type_service)
        result = await service.create_record("record-1", "user")
        
        # Verify the result
        assert result == test_record
        
        # Verify the methods were called
        mock_type_service.get_type.assert_called_once_with("user")
        mock_repo.create_with_type.assert_called_once_with("record-1", "user")
    
    @pytest.mark.asyncio
    async def test_create_record_with_invalid_type(self):
        """Test creating a record with invalid type."""
        # Create a mock repository and type service
        mock_repo = MockRepository.create()
        mock_repo.create_with_type = AsyncMock()
        
        mock_type_service = MagicMock()
        mock_type_service.get_type = AsyncMock(return_value=None)
        
        # Create service with a logger
        mock_logger = MagicMock()
        service = MetaRecordService(
            mock_repo, 
            type_service=mock_type_service,
            logger=mock_logger
        )
        
        # Call create_record
        result = await service.create_record("record-1", "nonexistent")
        
        # Verify the result is None
        assert result is None
        
        # Verify type was checked but no creation was attempted
        mock_type_service.get_type.assert_called_once_with("nonexistent")
        mock_repo.create_with_type.assert_not_called()
        
        # Verify a warning was logged
        mock_logger.warning.assert_called_once()