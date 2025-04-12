"""
Unit tests for RAG (Retrieval-Augmented Generation) service.

These tests ensure the RAG service works correctly for retrieving context
and formatting it for use in LLM prompts.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from uno.domain.vector_search import (
    RAGService,
    VectorSearchService,
    VectorSearchResult,
    VectorQuery
)


@pytest.fixture
def mock_vector_search_service():
    """Create a mock VectorSearchService."""
    service = MagicMock(spec=VectorSearchService)
    
    # Setup mock search method
    async def mock_search(query, **kwargs):
        # Return different results based on the query text
        if query.query_text == "test query":
            return [
                VectorSearchResult(
                    id="doc1",
                    similarity=0.95,
                    metadata={"type": "article"},
                    entity=MagicMock(
                        id="doc1",
                        title="Test Article",
                        content="This is test content about AI.",
                        metadata={"author": "Test Author"}
                    )
                ),
                VectorSearchResult(
                    id="doc2",
                    similarity=0.85,
                    metadata={"type": "blog"},
                    entity=MagicMock(
                        id="doc2",
                        title="Test Blog",
                        content="This is blog content about machine learning.",
                        metadata={"author": "Another Author"}
                    )
                )
            ]
        elif query.query_text == "empty query":
            return []
        else:
            return [
                VectorSearchResult(
                    id="doc3",
                    similarity=0.75,
                    metadata={"type": "wiki"},
                    entity=MagicMock(
                        id="doc3",
                        title="Generic Article",
                        content="Generic content for testing.",
                        metadata={"author": "Unknown"}
                    )
                )
            ]
    
    service.search = AsyncMock(side_effect=mock_search)
    return service


@pytest.fixture
def rag_service(mock_vector_search_service):
    """Create a RAGService with mocked VectorSearchService."""
    return RAGService(
        search_service=mock_vector_search_service,
        content_fields=["title", "content"]
    )


@pytest.mark.asyncio
async def test_retrieve_context_basic(rag_service):
    """Test basic context retrieval."""
    # Execute retrieval
    entities, results = await rag_service.retrieve_context(
        query="test query",
        limit=5,
        threshold=0.7
    )
    
    # Assertions
    assert len(entities) == 2
    assert len(results) == 2
    assert entities[0].id == "doc1"
    assert entities[0].title == "Test Article"
    assert entities[1].id == "doc2"
    assert entities[1].title == "Test Blog"
    assert results[0].similarity == 0.95
    assert results[1].similarity == 0.85


@pytest.mark.asyncio
async def test_retrieve_context_empty(rag_service):
    """Test context retrieval with no results."""
    # Execute retrieval
    entities, results = await rag_service.retrieve_context(
        query="empty query",
        limit=5,
        threshold=0.7
    )
    
    # Assertions
    assert len(entities) == 0
    assert len(results) == 0


@pytest.mark.asyncio
async def test_retrieve_context_with_threshold(rag_service, mock_vector_search_service):
    """Test context retrieval with high threshold filtering."""
    # Setup mock to return results with varying similarities
    mock_search_results = [
        VectorSearchResult(
            id="doc1",
            similarity=0.95,
            entity=MagicMock(id="doc1")
        ),
        VectorSearchResult(
            id="doc2",
            similarity=0.65,  # Below our test threshold
            entity=MagicMock(id="doc2")
        )
    ]
    mock_vector_search_service.search.return_value = mock_search_results
    
    # Execute retrieval with high threshold
    entities, results = await rag_service.retrieve_context(
        query="threshold test",
        limit=5,
        threshold=0.8  # Only the first result is above this
    )
    
    # Assertions
    assert len(entities) == 1  # Only one result above threshold
    assert len(results) == 1
    assert entities[0].id == "doc1"
    assert results[0].similarity == 0.95


def test_format_context_for_prompt(rag_service):
    """Test context formatting for LLM prompt."""
    # Setup
    entities = [
        MagicMock(
            id="doc1",
            title="Test Article",
            content="This is test content about AI.",
            metadata={"author": "Test Author"}
        ),
        MagicMock(
            id="doc2",
            title="Test Blog",
            content="This is blog content about machine learning.",
            metadata={"author": "Another Author"}
        )
    ]
    
    # Format context
    formatted_context = rag_service.format_context_for_prompt(entities)
    
    # Assertions
    assert "Document 1" in formatted_context
    assert "Test Article" in formatted_context
    assert "This is test content about AI." in formatted_context
    assert "Document 2" in formatted_context
    assert "Test Blog" in formatted_context
    assert "This is blog content about machine learning." in formatted_context


@pytest.mark.asyncio
async def test_create_rag_prompt(rag_service):
    """Test complete RAG prompt creation."""
    # Setup
    query = "What is AI?"
    system_prompt = "You are a helpful assistant."
    
    # Create prompt
    prompt = await rag_service.create_rag_prompt(
        query=query,
        system_prompt=system_prompt,
        limit=5,
        threshold=0.7
    )
    
    # Assertions
    assert "system_prompt" in prompt
    assert "user_prompt" in prompt
    assert system_prompt in prompt["system_prompt"]
    assert query in prompt["user_prompt"]
    assert "Test Article" in prompt["user_prompt"]
    assert "Test Blog" in prompt["user_prompt"]
    assert "This is test content about AI." in prompt["user_prompt"]
    assert "This is blog content about machine learning." in prompt["user_prompt"]


@pytest.mark.asyncio
async def test_create_rag_prompt_with_no_context(rag_service):
    """Test RAG prompt creation when no relevant context is found."""
    # Create prompt with a query that returns no results
    prompt = await rag_service.create_rag_prompt(
        query="empty query",
        system_prompt="You are a helpful assistant.",
        limit=5,
        threshold=0.7
    )
    
    # Assertions
    assert "system_prompt" in prompt
    assert "user_prompt" in prompt
    assert "empty query" in prompt["user_prompt"]
    assert "I couldn't find specific information" in prompt["user_prompt"] or \
           "No relevant context found" in prompt["user_prompt"]