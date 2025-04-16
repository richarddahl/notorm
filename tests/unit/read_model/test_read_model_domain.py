"""
Tests for the Read Model module domain entities.

These tests verify the behavior of the domain entities in the Read Model module,
ensuring they meet the business requirements and behave as expected.
"""

import uuid
import pytest
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any

from uno.read_model.entities import (
    ReadModelId, ProjectionId, QueryId, 
    ReadModel, Projection, Query, QueryResult, CacheEntry, ProjectorConfiguration,
    CacheLevel, ProjectionType, QueryType
)


class TestValueObjects:
    """Tests for the value objects in the Read Model module."""
    
    def test_read_model_id_creation(self):
        """Test creating a ReadModelId."""
        id_value = str(uuid.uuid4())
        read_model_id = ReadModelId(value=id_value)
        assert read_model_id.value == id_value
    
    def test_projection_id_creation(self):
        """Test creating a ProjectionId."""
        id_value = str(uuid.uuid4())
        projection_id = ProjectionId(value=id_value)
        assert projection_id.value == id_value
    
    def test_query_id_creation(self):
        """Test creating a QueryId."""
        id_value = str(uuid.uuid4())
        query_id = QueryId(value=id_value)
        assert query_id.value == id_value


class TestReadModel:
    """Tests for the ReadModel entity."""
    
    def test_read_model_creation(self):
        """Test creating a ReadModel instance."""
        id_value = str(uuid.uuid4())
        read_model_id = ReadModelId(value=id_value)
        data = {"name": "Test Model", "value": 42}
        metadata = {"source": "test"}
        
        model = ReadModel(
            id=read_model_id,
            version=1,
            data=data,
            metadata=metadata
        )
        
        assert model.id == read_model_id
        assert model.version == 1
        assert model.data == data
        assert model.metadata == metadata
        assert model.model_type == "ReadModel"
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)
    
    def test_read_model_update(self):
        """Test updating a ReadModel with new data."""
        id_value = str(uuid.uuid4())
        read_model_id = ReadModelId(value=id_value)
        original_data = {"name": "Test Model", "value": 42}
        
        model = ReadModel(
            id=read_model_id,
            version=1,
            data=original_data
        )
        
        # Save original values for comparison
        original_created_at = model.created_at
        original_updated_at = model.updated_at
        
        # Update with new data
        new_data = {"name": "Updated Model", "value": 43, "extra": "field"}
        updated_model = model.update(new_data)
        
        # Check that we got a new instance with updated properties
        assert updated_model is not model
        assert updated_model.id == read_model_id
        assert updated_model.version == 2
        assert updated_model.created_at == original_created_at
        assert updated_model.updated_at > original_updated_at
        
        # The data should be merged, not replaced
        expected_data = {"name": "Updated Model", "value": 43, "extra": "field"}
        assert updated_model.data == expected_data
    
    def test_read_model_set_metadata(self):
        """Test setting metadata on a ReadModel."""
        id_value = str(uuid.uuid4())
        read_model_id = ReadModelId(value=id_value)
        original_metadata = {"source": "test"}
        
        model = ReadModel(
            id=read_model_id,
            version=1,
            metadata=original_metadata
        )
        
        # Set new metadata
        updated_model = model.set_metadata("category", "example")
        
        # Check that we got a new instance with updated properties
        assert updated_model is not model
        assert updated_model.id == read_model_id
        assert updated_model.version == 1  # Version shouldn't change for metadata updates
        
        # The metadata should be updated
        expected_metadata = {"source": "test", "category": "example"}
        assert updated_model.metadata == expected_metadata


class TestProjection:
    """Tests for the Projection entity."""
    
    def test_projection_creation(self):
        """Test creating a Projection instance."""
        id_value = str(uuid.uuid4())
        projection_id = ProjectionId(value=id_value)
        
        projection = Projection(
            id=projection_id,
            name="TestProjection",
            event_type="TestEvent",
            read_model_type="TestReadModel",
            projection_type=ProjectionType.STANDARD,
            is_active=True,
            configuration={"batch_size": 100}
        )
        
        assert projection.id == projection_id
        assert projection.name == "TestProjection"
        assert projection.event_type == "TestEvent"
        assert projection.read_model_type == "TestReadModel"
        assert projection.projection_type == ProjectionType.STANDARD
        assert projection.is_active is True
        assert projection.configuration == {"batch_size": 100}
        assert isinstance(projection.created_at, datetime)
        assert isinstance(projection.updated_at, datetime)
    
    def test_projection_activate_deactivate(self):
        """Test activating and deactivating a Projection."""
        projection = Projection(
            id=ProjectionId(value=str(uuid.uuid4())),
            name="TestProjection",
            event_type="TestEvent",
            read_model_type="TestReadModel",
            is_active=False  # Start inactive
        )
        
        # Activate
        original_updated_at = projection.updated_at
        projection.activate()
        assert projection.is_active is True
        assert projection.updated_at > original_updated_at
        
        # Deactivate
        original_updated_at = projection.updated_at
        projection.deactivate()
        assert projection.is_active is False
        assert projection.updated_at > original_updated_at
    
    def test_projection_update_configuration(self):
        """Test updating a Projection's configuration."""
        original_config = {"batch_size": 100}
        projection = Projection(
            id=ProjectionId(value=str(uuid.uuid4())),
            name="TestProjection",
            event_type="TestEvent",
            read_model_type="TestReadModel",
            configuration=original_config
        )
        
        # Update configuration
        original_updated_at = projection.updated_at
        projection.update_configuration({"timeout": 30, "batch_size": 200})
        
        # Configuration should be updated (not replaced)
        expected_config = {"batch_size": 200, "timeout": 30}
        assert projection.configuration == expected_config
        assert projection.updated_at > original_updated_at


class TestQuery:
    """Tests for the Query entity."""
    
    def test_query_creation(self):
        """Test creating a Query instance."""
        id_value = str(uuid.uuid4())
        query_id = QueryId(value=id_value)
        
        query = Query(
            id=query_id,
            query_type=QueryType.GET_BY_ID,
            read_model_type="TestReadModel",
            parameters={"id": "12345"}
        )
        
        assert query.id == query_id
        assert query.query_type == QueryType.GET_BY_ID
        assert query.read_model_type == "TestReadModel"
        assert query.parameters == {"id": "12345"}
        assert isinstance(query.created_at, datetime)
    
    def test_query_has_id_parameter(self):
        """Test the has_id_parameter property."""
        # Query with ID parameter
        query_with_id = Query(
            id=QueryId(value=str(uuid.uuid4())),
            query_type=QueryType.GET_BY_ID,
            read_model_type="TestReadModel",
            parameters={"id": "12345"}
        )
        assert query_with_id.has_id_parameter is True
        
        # Query without ID parameter
        query_without_id = Query(
            id=QueryId(value=str(uuid.uuid4())),
            query_type=QueryType.FIND,
            read_model_type="TestReadModel",
            parameters={"criteria": {"name": "test"}}
        )
        assert query_without_id.has_id_parameter is False
    
    def test_query_has_criteria_parameter(self):
        """Test the has_criteria_parameter property."""
        # Query with criteria parameter
        query_with_criteria = Query(
            id=QueryId(value=str(uuid.uuid4())),
            query_type=QueryType.FIND,
            read_model_type="TestReadModel",
            parameters={"criteria": {"name": "test"}}
        )
        assert query_with_criteria.has_criteria_parameter is True
        
        # Query without criteria parameter
        query_without_criteria = Query(
            id=QueryId(value=str(uuid.uuid4())),
            query_type=QueryType.GET_BY_ID,
            read_model_type="TestReadModel",
            parameters={"id": "12345"}
        )
        assert query_without_criteria.has_criteria_parameter is False


class TestQueryResult:
    """Tests for the QueryResult entity."""
    
    def test_query_result_creation(self):
        """Test creating a QueryResult instance."""
        query_id = QueryId(value=str(uuid.uuid4()))
        read_model = ReadModel(
            id=ReadModelId(value=str(uuid.uuid4())),
            version=1,
            data={"name": "Test"}
        )
        
        result = QueryResult(
            query_id=query_id,
            execution_time_ms=42.5,
            result_count=1,
            results=read_model,
            is_cached=False
        )
        
        assert result.query_id == query_id
        assert result.execution_time_ms == 42.5
        assert result.result_count == 1
        assert result.results == read_model
        assert result.is_cached is False
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.id, str)


class TestCacheEntry:
    """Tests for the CacheEntry entity."""
    
    def test_cache_entry_creation(self):
        """Test creating a CacheEntry instance."""
        read_model_id = ReadModelId(value=str(uuid.uuid4()))
        read_model = ReadModel(
            id=read_model_id,
            version=1,
            data={"name": "Test"}
        )
        
        # Create a cache entry with an expiry time
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        entry = CacheEntry(
            read_model_id=read_model_id,
            read_model_type="TestReadModel",
            key="test-key",
            value=read_model,
            level=CacheLevel.MEMORY,
            expires_at=expires_at
        )
        
        assert entry.read_model_id == read_model_id
        assert entry.read_model_type == "TestReadModel"
        assert entry.key == "test-key"
        assert entry.value == read_model
        assert entry.level == CacheLevel.MEMORY
        assert entry.expires_at == expires_at
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.id, str)
    
    def test_is_expired(self):
        """Test the is_expired method."""
        # Create a cache entry that's not expired
        future_time = datetime.now(UTC) + timedelta(hours=1)
        unexpired_entry = CacheEntry(
            read_model_id=ReadModelId(value=str(uuid.uuid4())),
            read_model_type="TestReadModel",
            key="test-key",
            value="test-value",
            level=CacheLevel.MEMORY,
            expires_at=future_time
        )
        assert unexpired_entry.is_expired() is False
        
        # Create a cache entry that is expired
        past_time = datetime.now(UTC) - timedelta(hours=1)
        expired_entry = CacheEntry(
            read_model_id=ReadModelId(value=str(uuid.uuid4())),
            read_model_type="TestReadModel",
            key="test-key",
            value="test-value",
            level=CacheLevel.MEMORY,
            expires_at=past_time
        )
        assert expired_entry.is_expired() is True
        
        # Create a cache entry with no expiry
        no_expiry_entry = CacheEntry(
            read_model_id=ReadModelId(value=str(uuid.uuid4())),
            read_model_type="TestReadModel",
            key="test-key",
            value="test-value",
            level=CacheLevel.MEMORY,
            expires_at=None
        )
        assert no_expiry_entry.is_expired() is False


class TestProjectorConfiguration:
    """Tests for the ProjectorConfiguration entity."""
    
    def test_projector_configuration_creation(self):
        """Test creating a ProjectorConfiguration instance."""
        config = ProjectorConfiguration(
            name="test-projector",
            async_processing=True,
            batch_size=100,
            cache_enabled=True,
            cache_ttl_seconds=3600,
            rebuild_on_startup=False
        )
        
        assert config.name == "test-projector"
        assert config.async_processing is True
        assert config.batch_size == 100
        assert config.cache_enabled is True
        assert config.cache_ttl_seconds == 3600
        assert config.rebuild_on_startup is False
        assert len(config.projections) == 0
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)
    
    def test_add_remove_projection(self):
        """Test adding and removing projections from a configuration."""
        config = ProjectorConfiguration(
            name="test-projector"
        )
        
        # Create a projection to add
        projection = Projection(
            id=ProjectionId(value=str(uuid.uuid4())),
            name="TestProjection",
            event_type="TestEvent",
            read_model_type="TestReadModel"
        )
        
        # Add the projection
        original_updated_at = config.updated_at
        config.add_projection(projection)
        assert len(config.projections) == 1
        assert config.projections[0] == projection
        assert config.updated_at > original_updated_at
        
        # Adding the same projection again should not duplicate it
        config.add_projection(projection)
        assert len(config.projections) == 1
        
        # Remove the projection
        original_updated_at = config.updated_at
        result = config.remove_projection(projection.id)
        assert result is True
        assert len(config.projections) == 0
        assert config.updated_at > original_updated_at
        
        # Removing a non-existent projection should return False
        non_existent_id = ProjectionId(value=str(uuid.uuid4()))
        result = config.remove_projection(non_existent_id)
        assert result is False
    
    def test_config_methods(self):
        """Test the configuration helper methods."""
        config = ProjectorConfiguration(
            name="test-projector",
            async_processing=False,
            cache_enabled=False,
            rebuild_on_startup=False,
            batch_size=50,
            cache_ttl_seconds=1800
        )
        
        # Enable async processing
        original_updated_at = config.updated_at
        config.enable_async_processing()
        assert config.async_processing is True
        assert config.updated_at > original_updated_at
        
        # Disable async processing
        original_updated_at = config.updated_at
        config.disable_async_processing()
        assert config.async_processing is False
        assert config.updated_at > original_updated_at
        
        # Enable caching
        original_updated_at = config.updated_at
        config.enable_caching()
        assert config.cache_enabled is True
        assert config.updated_at > original_updated_at
        
        # Disable caching
        original_updated_at = config.updated_at
        config.disable_caching()
        assert config.cache_enabled is False
        assert config.updated_at > original_updated_at
        
        # Set cache TTL
        original_updated_at = config.updated_at
        config.set_cache_ttl(7200)
        assert config.cache_ttl_seconds == 7200
        assert config.updated_at > original_updated_at
        
        # Set batch size
        original_updated_at = config.updated_at
        config.set_batch_size(200)
        assert config.batch_size == 200
        assert config.updated_at > original_updated_at
        
        # Enable rebuild on startup
        original_updated_at = config.updated_at
        config.enable_rebuild_on_startup()
        assert config.rebuild_on_startup is True
        assert config.updated_at > original_updated_at
        
        # Disable rebuild on startup
        original_updated_at = config.updated_at
        config.disable_rebuild_on_startup()
        assert config.rebuild_on_startup is False
        assert config.updated_at > original_updated_at