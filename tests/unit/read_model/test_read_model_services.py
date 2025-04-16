"""
Tests for the Read Model services.

This module contains tests for all service implementations in the read_model module.
"""

import uuid
import pytest
import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional, cast
from dataclasses import dataclass

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails
from uno.domain.events import DomainEvent

from uno.read_model.entities import (
    ReadModel, ReadModelId, Projection, ProjectionId, Query, QueryId,
    CacheEntry, ProjectorConfiguration, CacheLevel, ProjectionType, QueryType
)
from uno.read_model.domain_repositories import (
    InMemoryReadModelRepository, InMemoryProjectionRepository, 
    InMemoryQueryRepository, InMemoryCacheRepository,
    InMemoryProjectorConfigurationRepository
)
from uno.read_model.domain_services import (
    ReadModelService, ProjectionService, CacheService, QueryService
)


# Test events for projection testing
@dataclass
class TestEvent(DomainEvent):
    """Test event for projection testing."""
    event_id: str
    event_type: str = "TestEvent"
    aggregate_id: str = "test-aggregate"
    data: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    version: int = 1
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize default values."""
        if self.data is None:
            self.data = {}
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


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
def event() -> TestEvent:
    """Create a test event."""
    return TestEvent(
        event_id=str(uuid.uuid4()),
        data={"name": "Test Model", "value": 42}
    )


class TestReadModelService:
    """Tests for ReadModelService."""

    @pytest.fixture
    def repository(self) -> InMemoryReadModelRepository:
        """Create a test repository."""
        return InMemoryReadModelRepository(model_type=ReadModel)

    @pytest.fixture
    def cache_repository(self) -> InMemoryCacheRepository:
        """Create a test cache repository."""
        return InMemoryCacheRepository()

    @pytest.fixture
    def cache_service(self, cache_repository: InMemoryCacheRepository) -> CacheService:
        """Create a test cache service."""
        return CacheService(cache_repository=cache_repository)

    @pytest.fixture
    def service(self, repository: InMemoryReadModelRepository) -> ReadModelService:
        """Create a test service without caching."""
        return ReadModelService(repository=repository, model_type=ReadModel)

    @pytest.fixture
    def service_with_cache(
        self, repository: InMemoryReadModelRepository, cache_service: CacheService
    ) -> ReadModelService:
        """Create a test service with caching."""
        return ReadModelService(
            repository=repository,
            model_type=ReadModel,
            cache_service=cache_service
        )

    @pytest.mark.asyncio
    async def test_get_by_id(self, service: ReadModelService, read_model: ReadModel):
        """Test getting a read model by ID."""
        # Arrange
        await service.repository.save(read_model)
        
        # Act
        result = await service.get_by_id(read_model.id)
        
        # Assert
        assert result.is_success() is True
        assert result.value == read_model
        assert result.value.id == read_model.id
        assert result.value.data == read_model.data
        assert result.value.metadata == read_model.metadata

    @pytest.mark.asyncio
    async def test_get_by_id_with_cache(self, service_with_cache: ReadModelService, read_model: ReadModel):
        """Test getting a read model by ID with caching."""
        # Arrange
        await service_with_cache.repository.save(read_model)
        
        # Act - First call should hit the repository
        result1 = await service_with_cache.get_by_id(read_model.id)
        
        # Change the model in the repository but not the cache
        modified_model = read_model.update({"value": 99})
        await service_with_cache.repository.save(modified_model)
        
        # Act - Second call should hit the cache
        result2 = await service_with_cache.get_by_id(read_model.id)
        
        # Assert
        assert result1.is_success() is True
        assert result1.value == read_model
        assert result2.is_success() is True
        # The second result should come from cache, so it won't have the updated value
        assert result2.value.data["value"] == 42
        assert result2.value != modified_model

    @pytest.mark.asyncio
    async def test_find(self, service: ReadModelService, read_model: ReadModel):
        """Test finding read models by criteria."""
        # Arrange
        await service.repository.save(read_model)
        
        # Act
        result = await service.find({"version": 1})
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0] == read_model

    @pytest.mark.asyncio
    async def test_save(self, service: ReadModelService, read_model: ReadModel):
        """Test saving a read model."""
        # Act
        result = await service.save(read_model)
        
        # Assert
        assert result.is_success() is True
        assert result.value == read_model
        
        # Verify it was saved in the repository
        get_result = await service.repository.get_by_id(read_model.id)
        assert get_result.is_success() is True
        assert get_result.value == read_model

    @pytest.mark.asyncio
    async def test_save_with_cache(self, service_with_cache: ReadModelService, read_model: ReadModel):
        """Test saving a read model with caching."""
        # Act
        result = await service_with_cache.save(read_model)
        
        # Directly verify it's in the cache
        cache_result = await service_with_cache.cache_service.get(
            read_model.id.value, 
            ReadModel.__name__
        )
        
        # Assert
        assert result.is_success() is True
        assert result.value == read_model
        assert cache_result.is_success() is True
        assert cache_result.value == read_model

    @pytest.mark.asyncio
    async def test_delete(self, service: ReadModelService, read_model: ReadModel):
        """Test deleting a read model."""
        # Arrange
        await service.repository.save(read_model)
        
        # Act
        result = await service.delete(read_model.id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is True
        
        # Verify it was deleted from the repository
        get_result = await service.repository.get_by_id(read_model.id)
        assert get_result.is_success() is True
        assert get_result.value is None

    @pytest.mark.asyncio
    async def test_delete_with_cache(self, service_with_cache: ReadModelService, read_model: ReadModel):
        """Test deleting a read model with caching."""
        # Arrange
        await service_with_cache.save(read_model)
        
        # Act
        result = await service_with_cache.delete(read_model.id)
        
        # Directly verify it's removed from the cache
        cache_result = await service_with_cache.cache_service.get(
            read_model.id.value, 
            ReadModel.__name__
        )
        
        # Assert
        assert result.is_success() is True
        assert result.value is True
        assert cache_result.is_success() is True
        assert cache_result.value is None


class TestProjectionService:
    """Tests for ProjectionService."""

    class TestProjectionService(ProjectionService[Projection, ReadModel]):
        """Test-specific projection service implementation."""
        
        async def _apply_event_logic(self, event: DomainEvent, projection: Projection) -> Optional[ReadModel]:
            """Implement event application logic for tests."""
            if not isinstance(event, TestEvent):
                return None
                
            # Create or update a read model based on the event data
            model_id = ReadModelId(value=event.aggregate_id)
            
            # Check if the model exists
            result = await self.read_model_repository.get_by_id(model_id)
            
            if result.value:
                # Update existing model
                updated_model = result.value.update(event.data)
                return updated_model
            else:
                # Create new model
                new_model = ReadModel(
                    id=model_id,
                    version=1,
                    data=event.data,
                    metadata={"event_id": event.event_id}
                )
                return new_model

    @pytest.fixture
    def projection_repository(self) -> InMemoryProjectionRepository:
        """Create a test projection repository."""
        return InMemoryProjectionRepository(model_type=Projection)

    @pytest.fixture
    def read_model_repository(self) -> InMemoryReadModelRepository:
        """Create a test read model repository."""
        return InMemoryReadModelRepository(model_type=ReadModel)

    @pytest.fixture
    def service(
        self, 
        projection_repository: InMemoryProjectionRepository,
        read_model_repository: InMemoryReadModelRepository
    ) -> TestProjectionService:
        """Create a test service."""
        return TestProjectionService(
            projection_repository=projection_repository,
            read_model_repository=read_model_repository,
            read_model_type=ReadModel,
            projection_type=Projection
        )

    @pytest.mark.asyncio
    async def test_get_by_id(self, service: TestProjectionService, projection: Projection):
        """Test getting a projection by ID."""
        # Arrange
        await service.projection_repository.save(projection)
        
        # Act
        result = await service.get_by_id(projection.id)
        
        # Assert
        assert result.is_success() is True
        assert result.value == projection
        assert result.value.id == projection.id
        assert result.value.name == projection.name
        assert result.value.event_type == projection.event_type

    @pytest.mark.asyncio
    async def test_get_by_event_type(self, service: TestProjectionService, projection: Projection):
        """Test getting projections by event type."""
        # Arrange
        await service.projection_repository.save(projection)
        
        # Act
        result = await service.get_by_event_type(projection.event_type)
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0] == projection

    @pytest.mark.asyncio
    async def test_save(self, service: TestProjectionService, projection: Projection):
        """Test saving a projection."""
        # Act
        result = await service.save(projection)
        
        # Assert
        assert result.is_success() is True
        assert result.value == projection
        
        # Verify it was saved in the repository
        get_result = await service.projection_repository.get_by_id(projection.id)
        assert get_result.is_success() is True
        assert get_result.value == projection

    @pytest.mark.asyncio
    async def test_delete(self, service: TestProjectionService, projection: Projection):
        """Test deleting a projection."""
        # Arrange
        await service.projection_repository.save(projection)
        
        # Act
        result = await service.delete(projection.id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is True
        
        # Verify it was deleted from the repository
        get_result = await service.projection_repository.get_by_id(projection.id)
        assert get_result.is_success() is True
        assert get_result.value is None

    @pytest.mark.asyncio
    async def test_apply_event_create(self, service: TestProjectionService, projection: Projection, event: TestEvent):
        """Test applying an event to create a read model."""
        # Arrange
        await service.projection_repository.save(projection)
        
        # Act
        result = await service.apply_event(event, projection)
        
        # Assert
        assert result.is_success() is True
        assert result.value is not None
        assert result.value.id.value == event.aggregate_id
        assert result.value.data == event.data
        assert result.value.metadata["event_id"] == event.event_id
        
        # Verify the model was saved in the repository
        get_result = await service.read_model_repository.get_by_id(result.value.id)
        assert get_result.is_success() is True
        assert get_result.value is not None
        assert get_result.value.id.value == event.aggregate_id

    @pytest.mark.asyncio
    async def test_apply_event_update(self, service: TestProjectionService, projection: Projection, event: TestEvent):
        """Test applying an event to update an existing read model."""
        # Arrange
        existing_model = ReadModel(
            id=ReadModelId(value=event.aggregate_id),
            version=1,
            data={"name": "Original Model", "value": 100},
            metadata={}
        )
        await service.read_model_repository.save(existing_model)
        
        # Act
        result = await service.apply_event(event, projection)
        
        # Assert
        assert result.is_success() is True
        assert result.value is not None
        assert result.value.id.value == event.aggregate_id
        assert result.value.data == event.data  # Data should be updated
        assert result.value.version == 2  # Version should be incremented
        
        # Verify the model was updated in the repository
        get_result = await service.read_model_repository.get_by_id(result.value.id)
        assert get_result.is_success() is True
        assert get_result.value is not None
        assert get_result.value.data == event.data

    @pytest.mark.asyncio
    async def test_apply_event_inactive_projection(
        self, service: TestProjectionService, projection: Projection, event: TestEvent
    ):
        """Test applying an event with an inactive projection."""
        # Arrange
        projection.is_active = False
        await service.projection_repository.save(projection)
        
        # Act
        result = await service.apply_event(event, projection)
        
        # Assert
        assert result.is_success() is True
        assert result.value is None
        
        # Verify no model was created
        model_id = ReadModelId(value=event.aggregate_id)
        get_result = await service.read_model_repository.get_by_id(model_id)
        assert get_result.is_success() is True
        assert get_result.value is None


class TestCacheService:
    """Tests for CacheService."""

    @pytest.fixture
    def cache_repository(self) -> InMemoryCacheRepository:
        """Create a test cache repository."""
        return InMemoryCacheRepository()

    @pytest.fixture
    def service(self, cache_repository: InMemoryCacheRepository) -> CacheService:
        """Create a test service."""
        return CacheService(cache_repository=cache_repository)

    @pytest.fixture
    def read_model_id() -> ReadModelId:
        """Create a test read model ID."""
        return ReadModelId(value=str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_set_and_get(self, service: CacheService, read_model_id: ReadModelId):
        """Test setting and getting a cache entry."""
        # Arrange
        key = "test-key"
        value = {"name": "Test Model", "value": 42}
        model_type = "TestReadModel"
        
        # Act
        set_result = await service.set(key, value, model_type, read_model_id)
        get_result = await service.get(key, model_type)
        
        # Assert
        assert set_result.is_success() is True
        assert set_result.value is True
        assert get_result.is_success() is True
        assert get_result.value == value

    @pytest.mark.asyncio
    async def test_get_missing(self, service: CacheService):
        """Test getting a non-existent cache entry."""
        # Act
        result = await service.get("non-existent", "TestModel")
        
        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, service: CacheService, read_model_id: ReadModelId):
        """Test setting a cache entry with TTL."""
        # Arrange
        key = "ttl-key"
        value = {"name": "Test Model", "value": 42}
        model_type = "TestReadModel"
        ttl_seconds = 0.1  # Very short TTL for testing
        
        # Act
        set_result = await service.set(key, value, model_type, read_model_id, ttl_seconds)
        get_result_before = await service.get(key, model_type)
        
        # Wait for TTL to expire
        await asyncio.sleep(0.2)
        
        get_result_after = await service.get(key, model_type)
        
        # Assert
        assert set_result.is_success() is True
        assert set_result.value is True
        assert get_result_before.is_success() is True
        assert get_result_before.value == value
        assert get_result_after.is_success() is True
        assert get_result_after.value is None  # Entry should be expired

    @pytest.mark.asyncio
    async def test_delete(self, service: CacheService, read_model_id: ReadModelId):
        """Test deleting a cache entry."""
        # Arrange
        key = "delete-key"
        value = {"name": "Test Model", "value": 42}
        model_type = "TestReadModel"
        
        await service.set(key, value, model_type, read_model_id)
        
        # Act
        delete_result = await service.delete(key, model_type)
        get_result = await service.get(key, model_type)
        
        # Assert
        assert delete_result.is_success() is True
        assert delete_result.value is True
        assert get_result.is_success() is True
        assert get_result.value is None

    @pytest.mark.asyncio
    async def test_clear(self, service: CacheService, read_model_id: ReadModelId):
        """Test clearing all cache entries."""
        # Arrange
        await service.set("key1", "value1", "Model1", read_model_id)
        await service.set("key2", "value2", "Model2", read_model_id)
        
        # Act
        clear_result = await service.clear()
        get_result1 = await service.get("key1", "Model1")
        get_result2 = await service.get("key2", "Model2")
        
        # Assert
        assert clear_result.is_success() is True
        assert clear_result.value is True
        assert get_result1.is_success() is True
        assert get_result1.value is None
        assert get_result2.is_success() is True
        assert get_result2.value is None

    @pytest.mark.asyncio
    async def test_clear_by_model_type(self, service: CacheService, read_model_id: ReadModelId):
        """Test clearing cache entries by model type."""
        # Arrange
        await service.set("key1", "value1", "Model1", read_model_id)
        await service.set("key2", "value2", "Model2", read_model_id)
        
        # Act - Clear only Model1 entries
        clear_result = await service.clear("Model1")
        get_result1 = await service.get("key1", "Model1")
        get_result2 = await service.get("key2", "Model2")
        
        # Assert
        assert clear_result.is_success() is True
        assert clear_result.value is True
        assert get_result1.is_success() is True
        assert get_result1.value is None
        assert get_result2.is_success() is True
        assert get_result2.value == "value2"  # Model2 should still be in cache


class TestQueryService:
    """Tests for QueryService."""

    @pytest.fixture
    def read_model_repository(self) -> InMemoryReadModelRepository:
        """Create a test read model repository."""
        return InMemoryReadModelRepository(model_type=ReadModel)

    @pytest.fixture
    def cache_repository(self) -> InMemoryCacheRepository:
        """Create a test cache repository."""
        return InMemoryCacheRepository()

    @pytest.fixture
    def cache_service(self, cache_repository: InMemoryCacheRepository) -> CacheService:
        """Create a test cache service."""
        return CacheService(cache_repository=cache_repository)

    @pytest.fixture
    def service(self, read_model_repository: InMemoryReadModelRepository) -> QueryService:
        """Create a test service without caching."""
        return QueryService(
            repository=read_model_repository,
            query_type=Query,
            model_type=ReadModel
        )

    @pytest.fixture
    def service_with_cache(
        self, read_model_repository: InMemoryReadModelRepository, cache_service: CacheService
    ) -> QueryService:
        """Create a test service with caching."""
        return QueryService(
            repository=read_model_repository,
            query_type=Query,
            model_type=ReadModel,
            cache_service=cache_service
        )

    @pytest.fixture
    def read_model() -> ReadModel:
        """Create a test read model with a known ID."""
        return ReadModel(
            id=ReadModelId(value="test-id"),
            version=1,
            data={"name": "Test Model", "value": 42},
            metadata={"source": "test"}
        )

    @pytest.mark.asyncio
    async def test_execute_get_by_id(self, service: QueryService, read_model: ReadModel, query_id: QueryId):
        """Test executing a GET_BY_ID query."""
        # Arrange
        await service.repository.save(read_model)
        query = Query(
            id=query_id,
            query_type=QueryType.GET_BY_ID,
            read_model_type="TestReadModel",
            parameters={"id": read_model.id.value}
        )
        
        # Act
        result = await service.execute(query)
        
        # Assert
        assert result.is_success() is True
        assert result.value == read_model

    @pytest.mark.asyncio
    async def test_execute_find(self, service: QueryService, read_model: ReadModel, query_id: QueryId):
        """Test executing a FIND query."""
        # Arrange
        await service.repository.save(read_model)
        query = Query(
            id=query_id,
            query_type=QueryType.FIND,
            read_model_type="TestReadModel",
            parameters={"criteria": {"version": 1}}
        )
        
        # Act
        result = await service.execute(query)
        
        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, list)
        assert len(result.value) == 1
        assert result.value[0] == read_model

    @pytest.mark.asyncio
    async def test_execute_list(self, service: QueryService, read_model: ReadModel, query_id: QueryId):
        """Test executing a LIST query."""
        # Arrange
        await service.repository.save(read_model)
        query = Query(
            id=query_id,
            query_type=QueryType.LIST,
            read_model_type="TestReadModel",
            parameters={}
        )
        
        # Act
        result = await service.execute(query)
        
        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, list)
        assert len(result.value) == 1
        assert result.value[0] == read_model

    @pytest.mark.asyncio
    async def test_execute_custom_query(self, service: QueryService, query_id: QueryId):
        """Test executing a CUSTOM query."""
        # Arrange
        query = Query(
            id=query_id,
            query_type=QueryType.CUSTOM,
            read_model_type="TestReadModel",
            parameters={"custom_param": "value"}
        )
        
        # Act
        result = await service.execute(query)
        
        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_IMPLEMENTED

    @pytest.mark.asyncio
    async def test_execute_with_metrics(self, service: QueryService, read_model: ReadModel, query_id: QueryId):
        """Test executing a query with metrics."""
        # Arrange
        await service.repository.save(read_model)
        query = Query(
            id=query_id,
            query_type=QueryType.GET_BY_ID,
            read_model_type="TestReadModel",
            parameters={"id": read_model.id.value}
        )
        
        # Act
        result = await service.execute_with_metrics(query)
        
        # Assert
        assert result.is_success() is True
        assert result.value.query_id == query.id
        assert result.value.result_count == 1
        assert result.value.execution_time_ms > 0
        assert result.value.results == read_model

    @pytest.mark.asyncio
    async def test_execute_with_cache(self, service_with_cache: QueryService, read_model: ReadModel, query_id: QueryId):
        """Test query execution with caching."""
        # Arrange
        await service_with_cache.repository.save(read_model)
        query = Query(
            id=query_id,
            query_type=QueryType.GET_BY_ID,
            read_model_type="TestReadModel",
            parameters={"id": read_model.id.value}
        )
        
        # Act - First execution should hit the repository
        result1 = await service_with_cache.execute(query)
        
        # Modify the model in the repository but not the cache
        modified_model = read_model.update({"value": 99})
        await service_with_cache.repository.save(modified_model)
        
        # Act - Second execution should hit the cache
        result2 = await service_with_cache.execute(query)
        
        # Assert
        assert result1.is_success() is True
        assert result1.value == read_model
        assert result2.is_success() is True
        # The second result should come from cache, so it won't have the updated value
        assert result2.value.data["value"] == 42
        assert result2.value != modified_model