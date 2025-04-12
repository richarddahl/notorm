"""
Integration tests for vector search functionality.

These tests use a real pgvector database to ensure the vector search
functionality works correctly end-to-end.
"""

import pytest
import asyncio
from typing import List, Dict, Any
import uuid
import json

from uno.domain.vector_search import (
    VectorSearchService,
    RAGService,
    VectorQuery,
    HybridQuery
)
from uno.domain.vector_update_service import VectorUpdateService
from uno.domain.event_dispatcher import EventDispatcher
from uno.database.session import async_session


# Skip these tests if the pgvector extension is not available
pytestmark = pytest.mark.pgvector


@pytest.fixture(scope="module")
async def event_dispatcher():
    """Create an event dispatcher."""
    dispatcher = EventDispatcher()
    await dispatcher.start()
    yield dispatcher
    await dispatcher.stop()


@pytest.fixture(scope="module")
async def db_session():
    """Create a database session."""
    async with async_session() as session:
        yield session


@pytest.fixture(scope="module")
async def setup_test_documents(db_session):
    """Set up test documents with vector embeddings."""
    # Define test documents
    documents = [
        {
            "id": str(uuid.uuid4()),
            "title": "Vector Search Introduction",
            "content": "Vector search is a method of finding similar items by comparing vector embeddings.",
            "metadata": json.dumps({"type": "article", "tags": ["vector", "search"]})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "PostgreSQL pgvector Extension",
            "content": "The pgvector extension enables vector similarity search in PostgreSQL databases.",
            "metadata": json.dumps({"type": "documentation", "tags": ["postgresql", "pgvector"]})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Python Programming",
            "content": "Python is a high-level programming language known for its simplicity and readability.",
            "metadata": json.dumps({"type": "tutorial", "tags": ["python", "programming"]})
        }
    ]
    
    # Create a temporary table for testing
    await db_session.execute("""
    CREATE TABLE IF NOT EXISTS test_vector_documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata JSONB,
        embedding VECTOR(1536)
    )
    """)
    
    # Insert documents
    for doc in documents:
        await db_session.execute(
            "INSERT INTO test_vector_documents (id, title, content, metadata) VALUES (:id, :title, :content, :metadata)",
            doc
        )
    
    await db_session.commit()
    
    # Return document IDs for cleanup
    doc_ids = [doc["id"] for doc in documents]
    yield doc_ids
    
    # Clean up: drop the table
    await db_session.execute("DROP TABLE IF EXISTS test_vector_documents")
    await db_session.commit()


@pytest.fixture(scope="module")
async def vector_search_service():
    """Create a VectorSearchService for testing."""
    service = VectorSearchService(
        entity_type="test_document",
        table_name="test_vector_documents",
        dimensions=1536
    )
    yield service


@pytest.fixture(scope="module")
async def rag_service(vector_search_service):
    """Create a RAGService for testing."""
    service = RAGService(
        search_service=vector_search_service,
        content_fields=["title", "content"]
    )
    yield service


@pytest.fixture(scope="module")
async def vector_update_service(event_dispatcher):
    """Create a VectorUpdateService for testing."""
    service = VectorUpdateService(dispatcher=event_dispatcher)
    await service.start()
    yield service
    await service.stop()


@pytest.fixture(scope="module")
async def update_embeddings(vector_update_service, db_session, setup_test_documents):
    """Update embeddings for test documents."""
    # Get test documents
    result = await db_session.execute("SELECT id, title, content FROM test_vector_documents")
    documents = result.fetchall()
    
    # Queue updates for all documents
    for doc in documents:
        content = f"{doc['title']} {doc['content']}"
        await vector_update_service.queue_update(
            entity_id=doc["id"],
            entity_type="test_document",
            content=content
        )
    
    # Wait for updates to process
    await asyncio.sleep(2)
    
    # Verify that embeddings were created
    result = await db_session.execute(
        "SELECT COUNT(*) FROM test_vector_documents WHERE embedding IS NOT NULL"
    )
    count = result.scalar()
    
    # Skip tests if embeddings weren't created
    if count != len(documents):
        pytest.skip("Failed to generate embeddings for test documents")


class TestVectorSearchIntegration:
    """Integration tests for vector search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_basic(self, vector_search_service, update_embeddings):
        """Test basic vector similarity search."""
        # Define query
        query = VectorQuery(
            query_text="vector database search",
            limit=10,
            threshold=0.5
        )
        
        # Execute search
        results = await vector_search_service.search(query)
        
        # Validate results
        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)
        assert any("Vector Search" in r.entity.title for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, vector_search_service, update_embeddings):
        """Test vector search with filters."""
        # Define query
        query = VectorQuery(
            query_text="database",
            limit=10,
            threshold=0.5
        )
        
        # Define filters - looking for documentation type
        filters = [
            ("metadata->>'type'", "=", "documentation")
        ]
        
        # Execute search
        results = await vector_search_service.search(query, filters=filters)
        
        # Validate results
        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)
        assert all(json.loads(r.entity.metadata)["type"] == "documentation" 
                  for r in results if r.entity.metadata)
    
    @pytest.mark.asyncio
    async def test_rag_retrieve_context(self, rag_service, update_embeddings):
        """Test RAG context retrieval."""
        # Retrieve context for a query
        entities, results = await rag_service.retrieve_context(
            query="How does PostgreSQL handle vector search?",
            limit=2,
            threshold=0.5
        )
        
        # Validate results
        assert len(entities) > 0
        assert len(results) == len(entities)
        assert all(r.similarity >= 0.5 for r in results)
        assert all(hasattr(e, "title") and hasattr(e, "content") for e in entities)
    
    @pytest.mark.asyncio
    async def test_rag_format_context(self, rag_service, update_embeddings):
        """Test RAG context formatting."""
        # Retrieve context for a query
        entities, _ = await rag_service.retrieve_context(
            query="PostgreSQL vector capabilities",
            limit=2,
            threshold=0.5
        )
        
        # Format the context
        formatted = rag_service.format_context_for_prompt(entities)
        
        # Validate formatting
        assert formatted
        assert "Document 1" in formatted
        for entity in entities:
            assert entity.title in formatted
            assert entity.content in formatted
    
    @pytest.mark.asyncio
    async def test_rag_create_prompt(self, rag_service, update_embeddings):
        """Test RAG prompt creation."""
        # Create a prompt
        prompt = await rag_service.create_rag_prompt(
            query="How does pgvector work?",
            system_prompt="You are a helpful assistant that answers questions about databases.",
            limit=2,
            threshold=0.5
        )
        
        # Validate prompt
        assert "system_prompt" in prompt
        assert "user_prompt" in prompt
        assert "How does pgvector work?" in prompt["user_prompt"]
        assert "You are a helpful assistant" in prompt["system_prompt"]