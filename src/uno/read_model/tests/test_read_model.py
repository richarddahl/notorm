"""Unit tests for the read model projection system.

This module contains comprehensive tests for the read model projection system,
ensuring that all components work correctly individually and together.
"""

import asyncio
import logging
import unittest
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from unittest.mock import Mock, MagicMock, patch, AsyncMock

import pytest

from uno.domain.events import DomainEvent, EventBus, InMemoryEventStore
from uno.read_model.read_model import (
    ReadModel, ReadModelRepository, InMemoryReadModelRepository
)
from uno.read_model.projector import Projection, Projector, AsyncProjector
from uno.read_model.query_service import (
    ReadModelQueryService, GetByIdQuery, FindByQuery
)
from uno.read_model.cache_service import (
    ReadModelCache, InMemoryReadModelCache
)


# Define test events and read models
class TestEvent(DomainEvent):
    """Test event for testing projections."""
    
    entity_id: str
    data: str


class TestReadModel(ReadModel):
    """Test read model for testing projections."""
    
    entity_id: str
    data: str


class TestProjection(Projection[TestReadModel, TestEvent]):
    """Test projection for testing the projector."""
    
    async def apply(self, event: TestEvent) -> Optional[TestReadModel]:
        """Apply a test event to create or update a test read model."""
        return TestReadModel(
            id=event.entity_id,
            entity_id=event.entity_id,
            data=event.data
        )


@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    return EventBus()


@pytest.fixture
def event_store():
    """Create an event store for testing."""
    return InMemoryEventStore()


@pytest.fixture
def repository():
    """Create a repository for testing."""
    return InMemoryReadModelRepository(TestReadModel)


@pytest.fixture
def cache():
    """Create a cache for testing."""
    return InMemoryReadModelCache(TestReadModel)


@pytest.fixture
def projection(repository):
    """Create a projection for testing."""
    return TestProjection(TestReadModel, TestEvent, repository)


@pytest.fixture
def projector(event_bus, event_store):
    """Create a projector for testing."""
    return Projector(event_bus, event_store)


@pytest.fixture
def query_service(repository, cache):
    """Create a query service for testing."""
    return ReadModelQueryService(repository, TestReadModel, cache)


@pytest.mark.asyncio
async def test_read_model_repository(repository):
    """Test the read model repository."""
    # Create a read model
    model = TestReadModel(
        id="test-1",
        entity_id="test-1",
        data="test data"
    )
    
    # Save the model
    saved_model = await repository.save(model)
    assert saved_model.id == model.id
    assert saved_model.entity_id == model.entity_id
    assert saved_model.data == model.data
    
    # Get the model by ID
    retrieved_model = await repository.get("test-1")
    assert retrieved_model is not None
    assert retrieved_model.id == model.id
    assert retrieved_model.entity_id == model.entity_id
    assert retrieved_model.data == model.data
    
    # Find models by criteria
    found_models = await repository.find({"entity_id": "test-1"})
    assert len(found_models) == 1
    assert found_models[0].id == model.id
    
    # Delete the model
    deleted = await repository.delete("test-1")
    assert deleted is True
    
    # Verify the model is gone
    retrieved_model = await repository.get("test-1")
    assert retrieved_model is None


@pytest.mark.asyncio
async def test_cache_service(cache):
    """Test the cache service."""
    # Create a read model
    model = TestReadModel(
        id="test-1",
        entity_id="test-1",
        data="test data"
    )
    
    # Set the model in the cache
    await cache.set("test-1", model)
    
    # Get the model from the cache
    cached_model = await cache.get("test-1")
    assert cached_model is not None
    assert cached_model.id == model.id
    assert cached_model.entity_id == model.entity_id
    assert cached_model.data == model.data
    
    # Delete the model from the cache
    await cache.delete("test-1")
    
    # Verify the model is gone
    cached_model = await cache.get("test-1")
    assert cached_model is None
    
    # Test TTL expiration
    await cache.set("test-2", model, ttl=1)
    cached_model = await cache.get("test-2")
    assert cached_model is not None
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    cached_model = await cache.get("test-2")
    assert cached_model is None
    
    # Test clear
    await cache.set("test-3", model)
    await cache.clear()
    cached_model = await cache.get("test-3")
    assert cached_model is None


@pytest.mark.asyncio
async def test_projection(projection, repository):
    """Test the projection."""
    # Create a test event
    event = TestEvent(
        entity_id="test-1",
        data="test data",
        event_type="test_event",
        aggregate_id="test-1",
        aggregate_type="test"
    )
    
    # Apply the projection
    read_model = await projection.apply(event)
    assert read_model is not None
    assert read_model.id == event.entity_id
    assert read_model.entity_id == event.entity_id
    assert read_model.data == event.data
    
    # Save the read model
    await projection.handle_event(event)
    
    # Verify the read model was saved
    saved_model = await repository.get("test-1")
    assert saved_model is not None
    assert saved_model.id == event.entity_id
    assert saved_model.entity_id == event.entity_id
    assert saved_model.data == event.data


@pytest.mark.asyncio
async def test_projector(projector, projection, event_bus, repository):
    """Test the projector."""
    # Register the projection
    projector.register_projection(projection)
    
    # Create a test event
    event = TestEvent(
        entity_id="test-1",
        data="test data",
        event_type="test_event",
        aggregate_id="test-1",
        aggregate_type="test"
    )
    
    # Publish the event
    await event_bus.publish(event)
    
    # Verify the read model was created
    saved_model = await repository.get("test-1")
    assert saved_model is not None
    assert saved_model.id == event.entity_id
    assert saved_model.entity_id == event.entity_id
    assert saved_model.data == event.data
    
    # Unregister the projection
    projector.unregister_projection(projection)
    
    # Create another test event
    event2 = TestEvent(
        entity_id="test-2",
        data="test data 2",
        event_type="test_event",
        aggregate_id="test-2",
        aggregate_type="test"
    )
    
    # Publish the event
    await event_bus.publish(event2)
    
    # Verify no read model was created for the second event
    saved_model2 = await repository.get("test-2")
    assert saved_model2 is None


@pytest.mark.asyncio
async def test_async_projector(event_bus, event_store, projection, repository):
    """Test the async projector."""
    # Create an async projector
    async_projector = AsyncProjector(event_bus, event_store)
    
    # Register the projection
    async_projector.register_projection(projection)
    
    # Start the projector
    await async_projector.start()
    
    # Create a test event
    event = TestEvent(
        entity_id="test-1",
        data="test data",
        event_type="test_event",
        aggregate_id="test-1",
        aggregate_type="test"
    )
    
    # Publish the event
    await event_bus.publish(event)
    
    # Give the async projector time to process the event
    await asyncio.sleep(0.1)
    
    # Verify the read model was created
    saved_model = await repository.get("test-1")
    assert saved_model is not None
    assert saved_model.id == event.entity_id
    assert saved_model.entity_id == event.entity_id
    assert saved_model.data == event.data
    
    # Stop the projector
    await async_projector.stop()


@pytest.mark.asyncio
async def test_query_service(query_service, repository):
    """Test the query service."""
    # Create a read model
    model = TestReadModel(
        id="test-1",
        entity_id="test-1",
        data="test data"
    )
    
    # Save the model
    await repository.save(model)
    
    # Get the model by ID
    retrieved_model = await query_service.get_by_id("test-1")
    assert retrieved_model is not None
    assert retrieved_model.id == model.id
    assert retrieved_model.entity_id == model.entity_id
    assert retrieved_model.data == model.data
    
    # Find models by criteria
    found_models = await query_service.find({"entity_id": "test-1"})
    assert len(found_models) == 1
    assert found_models[0].id == model.id
    
    # Test caching
    # The second get should be from cache
    with patch.object(repository, 'get', AsyncMock()) as mock_get:
        cached_model = await query_service.get_by_id("test-1")
        assert cached_model is not None
        assert cached_model.id == model.id
        mock_get.assert_not_called()
    
    # Test query handlers
    get_by_id_query = GetByIdQuery("test-1")
    get_by_id_result = await query_service.handle_query(get_by_id_query)
    assert get_by_id_result is not None
    assert get_by_id_result.id == model.id
    
    find_query = FindByQuery({"entity_id": "test-1"})
    find_result = await query_service.handle_query(find_query)
    assert len(find_result) == 1
    assert find_result[0].id == model.id
    
    # Test unsupported query
    with pytest.raises(ValueError):
        await query_service.handle_query(cast(Any, "not a query"))


@pytest.mark.asyncio
async def test_rebuild_all(projector, projection, repository, event_store):
    """Test rebuilding all read models."""
    # Register the projection
    projector.register_projection(projection)
    
    # Create test events
    events = [
        TestEvent(
            entity_id=f"test-{i}",
            data=f"test data {i}",
            event_type="test_event",
            aggregate_id=f"test-{i}",
            aggregate_type="test"
        )
        for i in range(5)
    ]
    
    # Add events to the event store
    for event in events:
        await event_store.append(event)
    
    # Rebuild all read models
    await projector.rebuild_all()
    
    # Verify all read models were created
    for i in range(5):
        saved_model = await repository.get(f"test-{i}")
        assert saved_model is not None
        assert saved_model.id == f"test-{i}"
        assert saved_model.entity_id == f"test-{i}"
        assert saved_model.data == f"test data {i}"