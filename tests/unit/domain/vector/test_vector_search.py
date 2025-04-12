"""
Unit tests for vector search service.

These tests ensure the vector search functionality works correctly,
including similarity search, hybrid search, and embedding generation.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from uno.domain.vector_search import (
    VectorSearchService,
    RAGService,
    VectorSearchResult,
    VectorQuery,
    HybridQuery
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    mock = AsyncMock()
    mock.execute.return_value = AsyncMock()
    return mock


@pytest.fixture
def mock_pool():
    """Create a mock connection pool."""
    mock = AsyncMock()
    mock.acquire.return_value.__aenter__.return_value = mock_session()
    return mock


@pytest.fixture
def vector_search_service():
    """Create a VectorSearchService with mocked components."""
    with patch('uno.domain.vector_search.async_session') as mock_session:
        mock_session.return_value = mock_pool()
        
        # Create the service
        service = VectorSearchService(
            entity_type="document",
            table_name="documents",
            dimensions=1536
        )
        
        # Mock the embedding function
        service._generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        
        return service


@pytest.mark.asyncio
async def test_search_basic(vector_search_service, mock_session):
    """Test basic vector similarity search."""
    # Setup mock
    mock_result = [
        {"id": "doc1", "similarity": 0.95, "metadata": json.dumps({"type": "article"})},
        {"id": "doc2", "similarity": 0.85, "metadata": json.dumps({"type": "blog"})}
    ]
    
    # Configure the mock session to return our test data
    session = mock_session()
    session.execute.return_value.__aenter__.return_value.fetchall.return_value = mock_result
    
    # Setup query
    query = VectorQuery(query_text="test query")
    
    # Execute search
    with patch.object(vector_search_service, '_get_session', return_value=session):
        results = await vector_search_service.search(query)
    
    # Assertions
    assert len(results) == 2
    assert results[0].id == "doc1"
    assert results[0].similarity == 0.95
    assert results[0].metadata["type"] == "article"
    assert results[1].id == "doc2"
    assert results[1].similarity == 0.85
    assert results[1].metadata["type"] == "blog"


@pytest.mark.asyncio
async def test_hybrid_search(vector_search_service, mock_session):
    """Test hybrid search combining graph and vector search."""
    # Setup mock
    mock_result = [
        {"id": "doc1", "similarity": 0.92, "metadata": json.dumps({"type": "article", "graph_distance": 1})},
        {"id": "doc3", "similarity": 0.78, "metadata": json.dumps({"type": "wiki", "graph_distance": 2})}
    ]
    
    # Configure the mock session to return our test data
    session = mock_session()
    session.execute.return_value.__aenter__.return_value.fetchall.return_value = mock_result
    
    # Setup query
    query = HybridQuery(
        query_text="test query",
        limit=5,
        graph_depth=2
    )
    
    # Execute search
    with patch.object(vector_search_service, '_get_session', return_value=session):
        results = await vector_search_service.hybrid_search(query)
    
    # Assertions
    assert len(results) == 2
    assert results[0].id == "doc1"
    assert results[0].similarity == 0.92
    assert results[0].metadata["type"] == "article"
    assert results[0].metadata["graph_distance"] == 1
    assert results[1].id == "doc3"
    assert results[1].similarity == 0.78
    assert results[1].metadata["graph_distance"] == 2


@pytest.mark.asyncio
async def test_generate_embedding(vector_search_service):
    """Test embedding generation."""
    # Setup
    text = "This is a test document for embedding generation."
    expected_dimensions = 1536
    
    # Generate embedding
    embedding = await vector_search_service.generate_embedding(text)
    
    # Assertions
    assert isinstance(embedding, list)
    assert len(embedding) == expected_dimensions
    
    # Check that our mock was called correctly
    vector_search_service._generate_embedding.assert_called_once_with(text)


@pytest.mark.asyncio
async def test_search_with_filters(vector_search_service, mock_session):
    """Test vector search with additional filters."""
    # Setup mock
    mock_result = [
        {"id": "doc5", "similarity": 0.89, "metadata": json.dumps({"type": "report"})}
    ]
    
    # Configure the mock session to return our test data
    session = mock_session()
    session.execute.return_value.__aenter__.return_value.fetchall.return_value = mock_result
    
    # Setup query with filters
    query = VectorQuery(
        query_text="test query",
        limit=10, 
        threshold=0.8
    )
    
    # Define filters
    filters = [
        ("type", "=", "report"),
        ("status", "=", "published")
    ]
    
    # Execute search
    with patch.object(vector_search_service, '_get_session', return_value=session):
        results = await vector_search_service.search(query, filters=filters)
    
    # Assertions
    assert len(results) == 1
    assert results[0].id == "doc5"
    assert results[0].similarity == 0.89
    assert results[0].metadata["type"] == "report"
    
    # Check SQL contained our filters
    call_args = session.execute.call_args[0][0]
    assert "type = " in str(call_args)
    assert "status = " in str(call_args)


@pytest.mark.asyncio
async def test_search_with_entity_loading(vector_search_service, mock_session):
    """Test vector search with entity loading."""
    # Setup mock
    mock_result = [
        {"id": "doc1", "similarity": 0.95, "metadata": json.dumps({"type": "article"})}
    ]
    
    # Configure the mock session to return our test data
    session = mock_session()
    fetch_mock = session.execute.return_value.__aenter__.return_value.fetchall
    fetch_mock.side_effect = [
        mock_result,  # First call for search results
        [{"id": "doc1", "title": "Test Article", "content": "This is test content"}]  # Second call for entity loading
    ]
    
    # Setup query
    query = VectorQuery(query_text="test query")
    
    # Execute search
    with patch.object(vector_search_service, '_get_session', return_value=session):
        results = await vector_search_service.search(query, load_entities=True)
    
    # Assertions
    assert len(results) == 1
    assert results[0].id == "doc1"
    assert results[0].similarity == 0.95
    assert results[0].entity is not None
    assert results[0].entity.id == "doc1"
    assert results[0].entity.title == "Test Article"
    assert results[0].entity.content == "This is test content"