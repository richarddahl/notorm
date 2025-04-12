"""
Unit tests for vector update service.

These tests ensure the vector update service correctly manages
embedding updates, priorities, and event handling.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime
import json

from uno.domain.vector_update_service import (
    VectorUpdateService,
    BatchVectorUpdateService,
    UpdateTask
)
from uno.domain.vector_events import (
    VectorContentEvent,
    VectorEmbeddingUpdateRequested,
    VectorEmbeddingUpdated
)


@pytest.fixture
def mock_event_dispatcher():
    """Create a mock event dispatcher."""
    dispatcher = MagicMock()
    dispatcher.dispatch = AsyncMock()
    return dispatcher


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def vector_update_service(mock_event_dispatcher):
    """Create a VectorUpdateService with mocked components."""
    service = VectorUpdateService(
        dispatcher=mock_event_dispatcher,
        batch_size=5,
        update_interval=0.1  # Short interval for testing
    )
    
    # Mock embedding generation to return a fixed vector
    service._generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    
    # Mock the session
    service._get_session = AsyncMock(return_value=mock_session())
    
    return service


@pytest.mark.asyncio
async def test_queue_update(vector_update_service):
    """Test queueing an update task."""
    # Queue an update
    await vector_update_service.queue_update(
        entity_id="doc1",
        entity_type="document",
        content="This is test content",
        priority=10
    )
    
    # Check the queue
    assert vector_update_service._queue.qsize() == 1
    
    # Get the task
    task = vector_update_service._queue.get()
    assert task.entity_id == "doc1"
    assert task.entity_type == "document"
    assert task.content == "This is test content"
    assert task.priority == 10
    assert isinstance(task.timestamp, datetime)


@pytest.mark.asyncio
async def test_process_batch(vector_update_service, mock_session):
    """Test processing a batch of update tasks."""
    # Add tasks to the queue
    for i in range(3):
        await vector_update_service.queue_update(
            entity_id=f"doc{i}",
            entity_type="document",
            content=f"Content for document {i}",
            priority=10-i  # Higher priority for earlier documents
        )
    
    # Process the batch
    await vector_update_service._process_batch()
    
    # Check that the session was used
    assert mock_session().execute.called
    
    # Check that the embedding was generated for each task
    assert vector_update_service._generate_embedding.call_count == 3
    
    # Check that events were dispatched
    assert vector_update_service._dispatcher.dispatch.call_count == 3


@pytest.mark.asyncio
async def test_process_event(vector_update_service):
    """Test processing a vector content event."""
    # Create an event
    event = VectorContentEvent(
        entity_id="doc1",
        entity_type="document",
        content="Updated content for vector embedding",
        timestamp=datetime.now()
    )
    
    # Process the event
    await vector_update_service.process_event(event)
    
    # Check the queue
    assert vector_update_service._queue.qsize() == 1
    
    # The task should have the event's content
    task = vector_update_service._queue.get()
    assert task.entity_id == "doc1"
    assert task.entity_type == "document"
    assert task.content == "Updated content for vector embedding"


@pytest.mark.asyncio
async def test_update_loop(vector_update_service):
    """Test the update loop behavior."""
    # Setup
    vector_update_service._running = True
    
    # Mock _process_batch to track calls
    vector_update_service._process_batch = AsyncMock()
    
    # Start the update loop in a task
    task = asyncio.create_task(vector_update_service._update_loop())
    
    # Wait a bit to let the loop run
    await asyncio.sleep(0.3)  # Should allow multiple iterations with 0.1 interval
    
    # Stop the loop
    vector_update_service._running = False
    await task
    
    # Check that _process_batch was called multiple times
    assert vector_update_service._process_batch.call_count >= 2


@pytest.mark.asyncio
async def test_start_stop(vector_update_service):
    """Test starting and stopping the service."""
    # Start with a patched _update_loop
    with patch.object(vector_update_service, '_update_loop', AsyncMock()) as mock_loop:
        # Start the service
        await vector_update_service.start()
        
        # Check state
        assert vector_update_service._running is True
        
        # Stop the service
        await vector_update_service.stop()
        
        # Check state
        assert vector_update_service._running is False
        
        # Check that the loop was called
        assert mock_loop.called


@pytest.mark.asyncio
async def test_get_stats(vector_update_service):
    """Test getting service statistics."""
    # Queue some updates
    await vector_update_service.queue_update(
        entity_id="doc1",
        entity_type="document",
        content="This is test content",
        priority=10
    )
    
    await vector_update_service.queue_update(
        entity_id="doc2",
        entity_type="document",
        content="This is another test",
        priority=5
    )
    
    # Mock some processing stats
    vector_update_service._processed_count = 10
    vector_update_service._error_count = 2
    vector_update_service._last_processed = datetime.now()
    
    # Get stats
    stats = vector_update_service.get_stats()
    
    # Check stats
    assert stats["queue_size"] == 2
    assert stats["processed_count"] == 10
    assert stats["error_count"] == 2
    assert "last_processed" in stats
    assert "uptime" in stats


@pytest.fixture
def batch_update_service(mock_event_dispatcher, mock_session):
    """Create a BatchVectorUpdateService with mocked components."""
    service = BatchVectorUpdateService(
        dispatcher=mock_event_dispatcher
    )
    
    # Mock the session
    service._get_session = AsyncMock(return_value=mock_session)
    
    # Mock content query results
    mock_session.execute.return_value.__aenter__.return_value.fetchall.return_value = [
        {"id": "doc1", "title": "Test 1", "content": "Content 1"},
        {"id": "doc2", "title": "Test 2", "content": "Content 2"}
    ]
    
    return service


@pytest.mark.asyncio
async def test_batch_update_all_entities(batch_update_service, mock_session):
    """Test batch updating all entities."""
    # Execute the update
    result = await batch_update_service.update_all_entities(
        entity_type="document",
        content_fields=["title", "content"]
    )
    
    # Check that the query was executed
    assert mock_session.execute.called
    
    # Check that events were dispatched for each entity
    assert batch_update_service._dispatcher.dispatch.call_count == 2
    
    # Check the result stats
    assert result["entity_type"] == "document"
    assert result["processed"] == 2
    assert result["errors"] == 0


@pytest.mark.asyncio
async def test_batch_update_entities_by_ids(batch_update_service, mock_session):
    """Test batch updating specific entities by ID."""
    # Execute the update
    result = await batch_update_service.update_entities_by_ids(
        entity_type="document",
        entity_ids=["doc1", "doc2"],
        content_fields=["title", "content"]
    )
    
    # Check that the query was executed with the IDs
    call_args = mock_session.execute.call_args[0][0]
    assert "IN" in str(call_args) or "= ANY" in str(call_args)
    
    # Check that events were dispatched for each entity
    assert batch_update_service._dispatcher.dispatch.call_count == 2
    
    # Check the result stats
    assert result["entity_type"] == "document"
    assert result["processed"] == 2
    assert result["errors"] == 0