"""
Tests for meta repositories.

This module contains tests for the MetaType and MetaRecord repositories.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from uno.dependencies.testing import MockRepository
from uno.meta.models import MetaTypeModel, MetaRecordModel
from uno.meta.repositories import MetaTypeRepository, MetaRecordRepository


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


class TestMetaTypeRepository:
    """Tests for the MetaTypeRepository class."""
    
    @pytest.mark.asyncio
    async def test_get_all_types(self, mock_session):
        """Test getting all meta types."""
        # Create test meta types
        test_types = [
            MetaTypeModel(id="user"),
            MetaTypeModel(id="group")
        ]
        
        # Configure the mock to return our test types
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.all.return_value = test_types
        
        # Create repository and call the method
        repo = MetaTypeRepository(mock_session)
        result = await repo.get_all_types()
        
        # Verify the result
        assert result == test_types
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_type_by_id(self, mock_session):
        """Test getting a meta type by ID."""
        # Create a test meta type
        test_type = MetaTypeModel(id="user")
        
        # Configure the mock to return our test type
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.first.return_value = test_type
        
        # Create repository and call the method
        repo = MetaTypeRepository(mock_session)
        result = await repo.get_type_by_id("user")
        
        # Verify the result
        assert result == test_type
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()


class TestMetaRecordRepository:
    """Tests for the MetaRecordRepository class."""
    
    @pytest.mark.asyncio
    async def test_find_by_type(self, mock_session):
        """Test finding meta records by type."""
        # Create test meta records
        test_records = [
            MetaRecordModel(id="record-1", meta_type_id="user"),
            MetaRecordModel(id="record-2", meta_type_id="user")
        ]
        
        # Configure the mock to return our test records
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.all.return_value = test_records
        
        # Create repository and call the method
        repo = MetaRecordRepository(mock_session)
        result = await repo.find_by_type("user")
        
        # Verify the result
        assert result == test_records
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_ids(self, mock_session):
        """Test finding meta records by IDs."""
        # Create test meta records
        test_records = [
            MetaRecordModel(id="record-1", meta_type_id="user"),
            MetaRecordModel(id="record-2", meta_type_id="user")
        ]
        
        # Configure the mock to return our test records
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.all.return_value = test_records
        
        # Create repository and call the method
        repo = MetaRecordRepository(mock_session)
        result = await repo.find_by_ids(["record-1", "record-2"])
        
        # Verify the result
        assert result == test_records
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_ids_empty(self, mock_session):
        """Test finding meta records with empty ID list."""
        # Create repository and call the method
        repo = MetaRecordRepository(mock_session)
        result = await repo.find_by_ids([])
        
        # Verify the result is an empty list
        assert result == []
        
        # Verify no query was executed
        mock_session.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_with_type(self, mock_session):
        """Test creating a meta record with type."""
        # Create a test meta record
        test_record = MetaRecordModel(id="record-1", meta_type_id="user")
        
        # Configure the mock to return our test record
        mock_result = mock_session.execute.return_value
        mock_scalars = mock_result.scalars.return_value
        mock_scalars.first.return_value = test_record
        
        # Create repository and call the method
        repo = MetaRecordRepository(mock_session)
        result = await repo.create_with_type("record-1", "user")
        
        # Verify the result
        assert result == test_record
        
        # Verify the query was constructed correctly
        mock_session.execute.assert_called_once()