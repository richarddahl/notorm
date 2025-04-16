"""
Tests for the Read Model repositories.

This module contains tests for all repository implementations in the read_model module.
"""

import uuid
import pytest
import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional
import json

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode

from uno.read_model.entities import (
    ReadModel, ReadModelId, Projection, ProjectionId, Query, QueryId,
    CacheEntry, ProjectorConfiguration, CacheLevel, ProjectionType, QueryType
)
from uno.read_model.domain_repositories import (
    InMemoryReadModelRepository, InMemoryProjectionRepository, 
    InMemoryQueryRepository, InMemoryCacheRepository,
    InMemoryProjectorConfigurationRepository
)


# Test data fixtures
@pytest.fixture
def read_model_id() -> ReadModelId:
    """Create a test read model ID."""
    return ReadModelId(value=str(uuid.uuid4()))


@pytest.fixture
def read_model(read_model_id: ReadModelId) -> ReadModel:
    """Create a test read model."""
    return ReadModel(
        id=read_model_id,
        version=1,
        data={"name": "Test Model", "value": 42},
        metadata={"source": "test"}
    )


@pytest.fixture
def projection_id() -> ProjectionId:
    """Create a test projection ID."""
    return ProjectionId(value=str(uuid.uuid4()))


@pytest.fixture
def projection(projection_id: ProjectionId) -> Projection:
    """Create a test projection."""
    return Projection(
        id=projection_id,
        name="TestProjection",
        event_type="TestEvent",
        read_model_type="TestReadModel",
        projection_type=ProjectionType.STANDARD,
        is_active=True,
        configuration={"key": "value"}
    )


@pytest.fixture
def query_id() -> QueryId:
    """Create a test query ID."""
    return QueryId(value=str(uuid.uuid4()))


@pytest.fixture
def query(query_id: QueryId) -> Query:
    """Create a test query."""
    return Query(
        id=query_id,
        query_type=QueryType.GET_BY_ID,
        read_model_type="TestReadModel",
        parameters={"id": "test-id"}
    )


@pytest.fixture
def cache_entry(read_model_id: ReadModelId) -> CacheEntry:
    """Create a test cache entry."""
    return CacheEntry(
        read_model_id=read_model_id,
        read_model_type="TestReadModel",
        key="test-key",
        value={"name": "Test Model", "value": 42},
        level=CacheLevel.MEMORY,
        expires_at=datetime.now(UTC) + timedelta(hours=1)
    )


@pytest.fixture
def projector_config(projection: Projection) -> ProjectorConfiguration:
    """Create a test projector configuration."""
    config = ProjectorConfiguration(
        name="TestProjector",
        async_processing=True,
        batch_size=100,
        cache_enabled=True,
        cache_ttl_seconds=3600
    )
    config.add_projection(projection)
    return config


class TestInMemoryReadModelRepository:
    """Tests for InMemoryReadModelRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryReadModelRepository:
        """Create a test repository."""
        return InMemoryReadModelRepository(model_type=ReadModel)

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository: InMemoryReadModelRepository, read_model: ReadModel):
        """Test saving and retrieving a read model."""
        # Arrange & Act
        save_result = await repository.save(read_model)
        get_result = await repository.get_by_id(read_model.id)
        
        # Assert
        assert save_result.is_success() is True
        assert save_result.value == read_model
        assert get_result.is_success() is True
        assert get_result.value == read_model
        assert get_result.value.id == read_model.id
        assert get_result.value.data == read_model.data
        assert get_result.value.metadata == read_model.metadata

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: InMemoryReadModelRepository, read_model_id: ReadModelId):
        """Test getting a non-existent read model."""
        # Act
        result = await repository.get_by_id(read_model_id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_find(self, repository: InMemoryReadModelRepository, read_model: ReadModel):
        """Test finding read models by criteria."""
        # Arrange
        await repository.save(read_model)
        
        # Act
        result = await repository.find({"version": 1})
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0] == read_model

    @pytest.mark.asyncio
    async def test_find_no_matches(self, repository: InMemoryReadModelRepository, read_model: ReadModel):
        """Test finding read models with no matches."""
        # Arrange
        await repository.save(read_model)
        
        # Act
        result = await repository.find({"version": 999})
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 0

    @pytest.mark.asyncio
    async def test_delete(self, repository: InMemoryReadModelRepository, read_model: ReadModel):
        """Test deleting a read model."""
        # Arrange
        await repository.save(read_model)
        
        # Act
        delete_result = await repository.delete(read_model.id)
        get_result = await repository.get_by_id(read_model.id)
        
        # Assert
        assert delete_result.is_success() is True
        assert delete_result.value is True
        assert get_result.is_success() is True
        assert get_result.value is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository: InMemoryReadModelRepository, read_model_id: ReadModelId):
        """Test deleting a non-existent read model."""
        # Act
        result = await repository.delete(read_model_id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is False


class TestInMemoryProjectionRepository:
    """Tests for InMemoryProjectionRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryProjectionRepository:
        """Create a test repository."""
        return InMemoryProjectionRepository(model_type=Projection)

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository: InMemoryProjectionRepository, projection: Projection):
        """Test saving and retrieving a projection."""
        # Arrange & Act
        save_result = await repository.save(projection)
        get_result = await repository.get_by_id(projection.id)
        
        # Assert
        assert save_result.is_success() is True
        assert save_result.value == projection
        assert get_result.is_success() is True
        assert get_result.value == projection
        assert get_result.value.id == projection.id
        assert get_result.value.name == projection.name
        assert get_result.value.event_type == projection.event_type
        assert get_result.value.read_model_type == projection.read_model_type

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: InMemoryProjectionRepository, projection_id: ProjectionId):
        """Test getting a non-existent projection."""
        # Act
        result = await repository.get_by_id(projection_id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_get_by_event_type(self, repository: InMemoryProjectionRepository, projection: Projection):
        """Test getting projections by event type."""
        # Arrange
        await repository.save(projection)
        
        # Act
        result = await repository.get_by_event_type(projection.event_type)
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0] == projection

    @pytest.mark.asyncio
    async def test_get_by_read_model_type(self, repository: InMemoryProjectionRepository, projection: Projection):
        """Test getting projections by read model type."""
        # Arrange
        await repository.save(projection)
        
        # Act
        result = await repository.get_by_read_model_type(projection.read_model_type)
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0] == projection

    @pytest.mark.asyncio
    async def test_delete(self, repository: InMemoryProjectionRepository, projection: Projection):
        """Test deleting a projection."""
        # Arrange
        await repository.save(projection)
        
        # Act
        delete_result = await repository.delete(projection.id)
        get_result = await repository.get_by_id(projection.id)
        
        # Assert
        assert delete_result.is_success() is True
        assert delete_result.value is True
        assert get_result.is_success() is True
        assert get_result.value is None


class TestInMemoryQueryRepository:
    """Tests for InMemoryQueryRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryQueryRepository:
        """Create a test repository."""
        return InMemoryQueryRepository(model_type=Query)

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository: InMemoryQueryRepository, query: Query):
        """Test saving and retrieving a query."""
        # Arrange & Act
        save_result = await repository.save(query)
        get_result = await repository.get_by_id(query.id)
        
        # Assert
        assert save_result.is_success() is True
        assert save_result.value == query
        assert get_result.is_success() is True
        assert get_result.value == query
        assert get_result.value.id == query.id
        assert get_result.value.query_type == query.query_type
        assert get_result.value.read_model_type == query.read_model_type
        assert get_result.value.parameters == query.parameters

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: InMemoryQueryRepository, query_id: QueryId):
        """Test getting a non-existent query."""
        # Act
        result = await repository.get_by_id(query_id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_find(self, repository: InMemoryQueryRepository, query: Query):
        """Test finding queries by criteria."""
        # Arrange
        await repository.save(query)
        
        # Act
        result = await repository.find({"query_type": QueryType.GET_BY_ID})
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0] == query

    @pytest.mark.asyncio
    async def test_delete(self, repository: InMemoryQueryRepository, query: Query):
        """Test deleting a query."""
        # Arrange
        await repository.save(query)
        
        # Act
        delete_result = await repository.delete(query.id)
        get_result = await repository.get_by_id(query.id)
        
        # Assert
        assert delete_result.is_success() is True
        assert delete_result.value is True
        assert get_result.is_success() is True
        assert get_result.value is None


class TestInMemoryCacheRepository:
    """Tests for InMemoryCacheRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryCacheRepository:
        """Create a test repository."""
        return InMemoryCacheRepository()

    @pytest.mark.asyncio
    async def test_set_and_get(self, repository: InMemoryCacheRepository, cache_entry: CacheEntry):
        """Test setting and getting a cache entry."""
        # Arrange & Act
        set_result = await repository.set(cache_entry)
        get_result = await repository.get(cache_entry.key, cache_entry.read_model_type)
        
        # Assert
        assert set_result.is_success() is True
        assert set_result.value == cache_entry
        assert get_result.is_success() is True
        assert get_result.value == cache_entry
        assert get_result.value.key == cache_entry.key
        assert get_result.value.read_model_type == cache_entry.read_model_type
        assert get_result.value.value == cache_entry.value

    @pytest.mark.asyncio
    async def test_get_not_found(self, repository: InMemoryCacheRepository):
        """Test getting a non-existent cache entry."""
        # Act
        result = await repository.get("non-existent", "TestModel")
        
        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_expired_entry(self, repository: InMemoryCacheRepository, read_model_id: ReadModelId):
        """Test that expired entries are not returned."""
        # Arrange
        expired_entry = CacheEntry(
            read_model_id=read_model_id,
            read_model_type="TestReadModel",
            key="expired-key",
            value={"name": "Test Model", "value": 42},
            level=CacheLevel.MEMORY,
            expires_at=datetime.now(UTC) - timedelta(hours=1)  # Expired 1 hour ago
        )
        await repository.set(expired_entry)
        
        # Act
        result = await repository.get(expired_entry.key, expired_entry.read_model_type)
        
        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_delete(self, repository: InMemoryCacheRepository, cache_entry: CacheEntry):
        """Test deleting a cache entry."""
        # Arrange
        await repository.set(cache_entry)
        
        # Act
        delete_result = await repository.delete(cache_entry.key, cache_entry.read_model_type)
        get_result = await repository.get(cache_entry.key, cache_entry.read_model_type)
        
        # Assert
        assert delete_result.is_success() is True
        assert delete_result.value is True
        assert get_result.is_success() is True
        assert get_result.value is None

    @pytest.mark.asyncio
    async def test_clear(self, repository: InMemoryCacheRepository, cache_entry: CacheEntry, read_model_id: ReadModelId):
        """Test clearing all cache entries."""
        # Arrange
        await repository.set(cache_entry)
        other_entry = CacheEntry(
            read_model_id=read_model_id,
            read_model_type="OtherReadModel",
            key="other-key",
            value={"name": "Other Model", "value": 99},
            level=CacheLevel.MEMORY
        )
        await repository.set(other_entry)
        
        # Act
        clear_result = await repository.clear()
        get_result1 = await repository.get(cache_entry.key, cache_entry.read_model_type)
        get_result2 = await repository.get(other_entry.key, other_entry.read_model_type)
        
        # Assert
        assert clear_result.is_success() is True
        assert clear_result.value is True
        assert get_result1.is_success() is True
        assert get_result1.value is None
        assert get_result2.is_success() is True
        assert get_result2.value is None

    @pytest.mark.asyncio
    async def test_clear_by_model_type(self, repository: InMemoryCacheRepository, cache_entry: CacheEntry, read_model_id: ReadModelId):
        """Test clearing cache entries by model type."""
        # Arrange
        await repository.set(cache_entry)
        other_entry = CacheEntry(
            read_model_id=read_model_id,
            read_model_type="OtherReadModel",
            key="other-key",
            value={"name": "Other Model", "value": 99},
            level=CacheLevel.MEMORY
        )
        await repository.set(other_entry)
        
        # Act - Clear only TestReadModel entries
        clear_result = await repository.clear(cache_entry.read_model_type)
        get_result1 = await repository.get(cache_entry.key, cache_entry.read_model_type)
        get_result2 = await repository.get(other_entry.key, other_entry.read_model_type)
        
        # Assert
        assert clear_result.is_success() is True
        assert clear_result.value is True
        assert get_result1.is_success() is True
        assert get_result1.value is None
        assert get_result2.is_success() is True
        assert get_result2.value == other_entry


class TestInMemoryProjectorConfigurationRepository:
    """Tests for InMemoryProjectorConfigurationRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryProjectorConfigurationRepository:
        """Create a test repository."""
        return InMemoryProjectorConfigurationRepository()

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository: InMemoryProjectorConfigurationRepository, projector_config: ProjectorConfiguration):
        """Test saving and retrieving a projector configuration."""
        # Arrange & Act
        save_result = await repository.save(projector_config)
        get_result = await repository.get_by_id(projector_config.id)
        
        # Assert
        assert save_result.is_success() is True
        assert save_result.value == projector_config
        assert get_result.is_success() is True
        assert get_result.value == projector_config
        assert get_result.value.id == projector_config.id
        assert get_result.value.name == projector_config.name
        assert len(get_result.value.projections) == len(projector_config.projections)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: InMemoryProjectorConfigurationRepository):
        """Test getting a non-existent configuration."""
        # Act
        result = await repository.get_by_id("non-existent")
        
        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_get_by_name(self, repository: InMemoryProjectorConfigurationRepository, projector_config: ProjectorConfiguration):
        """Test getting a configuration by name."""
        # Arrange
        await repository.save(projector_config)
        
        # Act
        result = await repository.get_by_name(projector_config.name)
        
        # Assert
        assert result.is_success() is True
        assert result.value == projector_config
        assert result.value.name == projector_config.name

    @pytest.mark.asyncio
    async def test_delete(self, repository: InMemoryProjectorConfigurationRepository, projector_config: ProjectorConfiguration):
        """Test deleting a configuration."""
        # Arrange
        await repository.save(projector_config)
        
        # Act
        delete_result = await repository.delete(projector_config.id)
        get_result = await repository.get_by_id(projector_config.id)
        
        # Assert
        assert delete_result.is_success() is True
        assert delete_result.value is True
        assert get_result.is_success() is True
        assert get_result.value is None

    @pytest.mark.asyncio
    async def test_delete_removes_from_name_index(self, repository: InMemoryProjectorConfigurationRepository, projector_config: ProjectorConfiguration):
        """Test that deleting a configuration removes it from the name index."""
        # Arrange
        await repository.save(projector_config)
        
        # Act
        delete_result = await repository.delete(projector_config.id)
        get_by_name_result = await repository.get_by_name(projector_config.name)
        
        # Assert
        assert delete_result.is_success() is True
        assert delete_result.value is True
        assert get_by_name_result.is_success() is True
        assert get_by_name_result.value is None