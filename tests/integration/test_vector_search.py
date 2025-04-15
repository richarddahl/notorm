"""
Integration tests for vector search functionality.

These tests use a real pgvector database to ensure the vector search
functionality works correctly end-to-end, covering:
- Similarity search with various metrics (cosine, L2, inner product)
- Hybrid search with keyword filtering 
- Strongly-typed search results
- Performance benchmarks
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, TypeVar, Generic, Optional, Tuple
import uuid
import json
from dataclasses import dataclass, field

from uno.domain.vector_search import (
    VectorSearchService,
    RAGService,
    VectorQuery,
    HybridQuery,
    SearchResult,
    VectorMetric,
    VectorFilterOperator,
    VectorFilterType
)
from uno.domain.vector_update_service import VectorUpdateService
from uno.domain.event_dispatcher import EventDispatcher
from uno.database.session import async_session


# Skip these tests if the pgvector extension is not available
pytestmark = pytest.mark.pgvector


# Generic type for strongly-typed search results
T = TypeVar('T')


@dataclass
class TypedSearchResult(Generic[T], SearchResult):
    """Strongly-typed search result with entity of type T."""
    entity: T
    similarity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestDocument:
    """Test document class for strongly-typed results."""
    id: str
    title: str
    content: str
    metadata: Optional[str] = None
    embedding: Optional[List[float]] = None


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
    # Define test documents - expanded test set for more comprehensive testing
    documents = [
        {
            "id": str(uuid.uuid4()),
            "title": "Vector Search Introduction",
            "content": "Vector search is a method of finding similar items by comparing vector embeddings.",
            "metadata": json.dumps({"type": "article", "tags": ["vector", "search"], "category": "introduction"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "PostgreSQL pgvector Extension",
            "content": "The pgvector extension enables vector similarity search in PostgreSQL databases.",
            "metadata": json.dumps({"type": "documentation", "tags": ["postgresql", "pgvector"], "category": "database"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Python Programming",
            "content": "Python is a high-level programming language known for its simplicity and readability.",
            "metadata": json.dumps({"type": "tutorial", "tags": ["python", "programming"], "category": "language"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Neural Networks and Embeddings",
            "content": "Neural networks can generate embeddings that capture semantic meaning of text and images.",
            "metadata": json.dumps({"type": "article", "tags": ["machine learning", "embeddings"], "category": "ai"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Similarity Metrics in Vector Search",
            "content": "Vector search uses metrics like cosine similarity, Euclidean distance (L2), and dot product.",
            "metadata": json.dumps({"type": "article", "tags": ["vector", "metrics"], "category": "search"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Hybrid Search Systems",
            "content": "Hybrid search combines vector similarity with keyword filtering for better results.",
            "metadata": json.dumps({"type": "documentation", "tags": ["hybrid", "search"], "category": "search"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Database Indexing Strategies",
            "content": "Proper indexing is crucial for efficient database queries in vector search systems.",
            "metadata": json.dumps({"type": "tutorial", "tags": ["database", "indexing"], "category": "database"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Retrieval Augmented Generation",
            "content": "RAG combines information retrieval with text generation for accurate context-aware responses.",
            "metadata": json.dumps({"type": "article", "tags": ["rag", "llm"], "category": "ai"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Vector Databases Comparison",
            "content": "Comparing pgvector, Pinecone, Milvus, and other vector database technologies.",
            "metadata": json.dumps({"type": "comparison", "tags": ["database", "vector"], "category": "database"})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Semantic Search Implementation",
            "content": "Building semantic search systems requires embedding models and similarity computation.",
            "metadata": json.dumps({"type": "tutorial", "tags": ["semantic", "search"], "category": "implementation"})
        }
    ]
    
    # Create a temporary table for testing with support for different vector metrics
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
    
    # Return document objects for use in tests
    yield documents
    
    # Clean up: drop the table
    await db_session.execute("DROP TABLE IF EXISTS test_vector_documents")
    await db_session.commit()


@pytest.fixture(scope="module")
async def setup_typed_documents(db_session):
    """Set up test documents for strongly-typed search results."""
    # Create a temporary table for typed documents
    await db_session.execute("""
    CREATE TABLE IF NOT EXISTS test_typed_documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata JSONB,
        embedding VECTOR(1536)
    )
    """)
    
    # Use a different set of documents for typed testing
    documents = [
        {
            "id": str(uuid.uuid4()),
            "title": "Typed Document 1",
            "content": "This is a document for testing strongly-typed search results.",
            "metadata": json.dumps({"type": "test", "tags": ["typed", "search"]})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Typed Document 2",
            "content": "Strong typing ensures that search results have the correct structure.",
            "metadata": json.dumps({"type": "test", "tags": ["typed", "results"]})
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Typed Document 3",
            "content": "Generic result types provide better developer experience in vector search.",
            "metadata": json.dumps({"type": "test", "tags": ["generic", "typing"]})
        }
    ]
    
    # Insert documents
    for doc in documents:
        await db_session.execute(
            "INSERT INTO test_typed_documents (id, title, content, metadata) VALUES (:id, :title, :content, :metadata)",
            doc
        )
    
    await db_session.commit()
    
    # Return document objects for use in tests
    yield documents
    
    # Clean up: drop the table
    await db_session.execute("DROP TABLE IF EXISTS test_typed_documents")
    await db_session.commit()


@pytest.fixture(scope="module")
async def setup_benchmark_documents(db_session):
    """Set up a larger set of documents for performance benchmarking."""
    # Create a temporary table for benchmarking
    await db_session.execute("""
    CREATE TABLE IF NOT EXISTS test_benchmark_documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata JSONB,
        embedding VECTOR(1536)
    )
    """)
    
    # Insert a larger number of documents for benchmarking
    benchmark_docs = []
    categories = ["technology", "science", "business", "health", "education"]
    types = ["article", "blog", "tutorial", "documentation", "report"]
    
    # Create 100 documents for benchmarking
    for i in range(100):
        doc_id = str(uuid.uuid4())
        category = categories[i % len(categories)]
        doc_type = types[i % len(types)]
        
        doc = {
            "id": doc_id,
            "title": f"Benchmark Document {i+1}",
            "content": f"This is benchmark document {i+1} for performance testing of vector search with category {category}.",
            "metadata": json.dumps({
                "type": doc_type,
                "category": category,
                "index": i,
                "tags": ["benchmark", category, doc_type]
            })
        }
        benchmark_docs.append(doc)
        
        await db_session.execute(
            "INSERT INTO test_benchmark_documents (id, title, content, metadata) VALUES (:id, :title, :content, :metadata)",
            doc
        )
    
    await db_session.commit()
    
    # Return document objects for use in tests
    yield benchmark_docs
    
    # Clean up: drop the table
    await db_session.execute("DROP TABLE IF EXISTS test_benchmark_documents")
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
async def vector_search_l2():
    """Create a VectorSearchService with L2 distance metric."""
    service = VectorSearchService(
        entity_type="test_document",
        table_name="test_vector_documents",
        dimensions=1536,
        metric=VectorMetric.L2
    )
    yield service


@pytest.fixture(scope="module")
async def vector_search_ip():
    """Create a VectorSearchService with inner product metric."""
    service = VectorSearchService(
        entity_type="test_document",
        table_name="test_vector_documents",
        dimensions=1536,
        metric=VectorMetric.INNER_PRODUCT
    )
    yield service


@pytest.fixture(scope="module")
async def vector_search_typed():
    """Create a VectorSearchService for typed results."""
    service = VectorSearchService(
        entity_type="test_document",
        table_name="test_typed_documents",
        dimensions=1536,
        metric=VectorMetric.COSINE,
        result_class=TestDocument
    )
    yield service


@pytest.fixture(scope="module")
async def vector_search_benchmark():
    """Create a VectorSearchService for benchmarking."""
    service = VectorSearchService(
        entity_type="benchmark_document",
        table_name="test_benchmark_documents",
        dimensions=1536,
        metric=VectorMetric.COSINE
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


@pytest.fixture(scope="module")
async def update_typed_embeddings(vector_update_service, db_session, setup_typed_documents):
    """Update embeddings for typed test documents."""
    # Get test documents
    result = await db_session.execute("SELECT id, title, content FROM test_typed_documents")
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
        "SELECT COUNT(*) FROM test_typed_documents WHERE embedding IS NOT NULL"
    )
    count = result.scalar()
    
    # Skip tests if embeddings weren't created
    if count != len(documents):
        pytest.skip("Failed to generate embeddings for typed test documents")


@pytest.fixture(scope="module")
async def update_benchmark_embeddings(vector_update_service, db_session, setup_benchmark_documents):
    """Update embeddings for benchmark documents."""
    # Get benchmark documents
    result = await db_session.execute("SELECT id, title, content FROM test_benchmark_documents")
    documents = result.fetchall()
    
    # Queue updates for all documents
    for doc in documents:
        content = f"{doc['title']} {doc['content']}"
        await vector_update_service.queue_update(
            entity_id=doc["id"],
            entity_type="benchmark_document",
            content=content
        )
    
    # Wait for updates to process (may take longer for larger dataset)
    await asyncio.sleep(5)
    
    # Verify that embeddings were created
    result = await db_session.execute(
        "SELECT COUNT(*) FROM test_benchmark_documents WHERE embedding IS NOT NULL"
    )
    count = result.scalar()
    
    # Skip tests if not all embeddings were created
    if count < len(documents) * 0.9:  # Allow for some failures (at least 90% success)
        pytest.skip(f"Failed to generate enough embeddings for benchmark documents ({count}/{len(documents)})")


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
    async def test_search_with_cosine_metric(self, vector_search_service, update_embeddings):
        """Test vector search with cosine similarity metric."""
        # Define query with explicit cosine metric
        query = VectorQuery(
            query_text="neural networks embedding generation",
            limit=5,
            threshold=0.5,
            metric=VectorMetric.COSINE
        )
        
        # Execute search
        results = await vector_search_service.search(query)
        
        # Validate results
        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)
        
        # Results should include documents about neural networks and embeddings
        result_titles = [r.entity.title.lower() for r in results]
        assert any("neural" in title or "embedding" in title for title in result_titles)
    
    @pytest.mark.asyncio
    async def test_search_with_l2_metric(self, vector_search_l2, update_embeddings):
        """Test vector search with L2 distance metric."""
        # Define query for L2 distance
        query = VectorQuery(
            query_text="database search similarity metrics",
            limit=5,
            # Note: lower is better for L2 distance, so we use an upper threshold
            threshold=0.8,  # L2 values are typically higher, anything below this threshold is good
            metric=VectorMetric.L2
        )
        
        # Execute search
        results = await vector_search_l2.search(query)
        
        # Validate results
        assert len(results) > 0
        # For L2, lower values are better, so threshold is a maximum value
        assert all(r.similarity <= 0.8 for r in results)
        
        # Should find documents about databases and search
        result_titles = [r.entity.title.lower() for r in results]
        assert any("database" in title or "search" in title for title in result_titles)
    
    @pytest.mark.asyncio
    async def test_search_with_inner_product_metric(self, vector_search_ip, update_embeddings):
        """Test vector search with inner product metric."""
        # Define query for inner product
        query = VectorQuery(
            query_text="vector search implementation",
            limit=5,
            threshold=0.5,
            metric=VectorMetric.INNER_PRODUCT
        )
        
        # Execute search
        results = await vector_search_ip.search(query)
        
        # Validate results
        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)
        
        # Should find documents about vector search implementation
        result_titles = [r.entity.title.lower() for r in results]
        assert any("vector" in title or "search" in title or "implementation" in title 
                  for title in result_titles)
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, vector_search_service, update_embeddings):
        """Test hybrid search combining vector similarity with keyword filtering."""
        # Define hybrid query
        query = HybridQuery(
            query_text="vector database",
            keyword_query="pgvector OR postgres",
            limit=5,
            threshold=0.5,
            filter_weight=0.3,  # 30% weight to keyword matches
        )
        
        # Execute hybrid search
        results = await vector_search_service.hybrid_search(query)
        
        # Validate results
        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)
        
        # Results should prioritize documents that mention pgvector or postgres
        result_contents = [r.entity.content.lower() for r in results]
        result_titles = [r.entity.title.lower() for r in results]
        
        # At least one result should mention pgvector or postgres
        assert any("pgvector" in content or "postgres" in content or 
                  "pgvector" in title or "postgres" in title
                  for content, title in zip(result_contents, result_titles))
    
    @pytest.mark.asyncio
    async def test_hybrid_search_with_filters(self, vector_search_service, update_embeddings):
        """Test hybrid search with additional metadata filters."""
        # Define hybrid query
        query = HybridQuery(
            query_text="vector search",
            keyword_query="database OR similarity",
            limit=5,
            threshold=0.5,
            filter_weight=0.3,
        )
        
        # Define metadata filters - look for articles only
        filters = [
            ("metadata->>'type'", "=", "article")
        ]
        
        # Execute hybrid search with filters
        results = await vector_search_service.hybrid_search(query, filters=filters)
        
        # Validate results
        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)
        
        # All results should be articles
        for r in results:
            metadata = json.loads(r.entity.metadata)
            assert metadata["type"] == "article"
    
    @pytest.mark.asyncio
    async def test_typed_search_results(self, vector_search_typed, update_typed_embeddings):
        """Test strongly-typed search results."""
        # Define query for typed document search
        query = VectorQuery(
            query_text="typed search results",
            limit=5,
            threshold=0.5,
        )
        
        # Execute search
        results = await vector_search_typed.search(query)
        
        # Validate results
        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)
        
        # Check that results are properly typed
        assert all(isinstance(r.entity, TestDocument) for r in results)
        assert all(hasattr(r.entity, "id") for r in results)
        assert all(hasattr(r.entity, "title") for r in results)
        assert all(hasattr(r.entity, "content") for r in results)
        
        # Convert to typed search results
        typed_results = [
            TypedSearchResult[TestDocument](
                entity=r.entity,
                similarity=r.similarity,
                metadata={"source": "typed_documents"}
            ) 
            for r in results
        ]
        
        # Check typed results
        assert all(isinstance(r, TypedSearchResult) for r in typed_results)
        assert all(isinstance(r.entity, TestDocument) for r in typed_results)
        assert all(r.metadata.get("source") == "typed_documents" for r in typed_results)
    
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


class TestVectorSearchPerformance:
    """Performance benchmarks for vector search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_performance(self, vector_search_benchmark, update_benchmark_embeddings):
        """Benchmark performance of vector search."""
        # Define query for performance testing
        query = VectorQuery(
            query_text="vector similarity search in databases",
            limit=10,
            threshold=0.5
        )
        
        # Measure search time over multiple runs
        num_runs = 5
        search_times = []
        
        for _ in range(num_runs):
            start_time = time.time()
            results = await vector_search_benchmark.search(query)
            end_time = time.time()
            
            # Record search time
            search_time = end_time - start_time
            search_times.append(search_time)
            
            # Validate that results were returned
            assert len(results) > 0
        
        # Calculate statistics
        avg_time = sum(search_times) / num_runs
        min_time = min(search_times)
        max_time = max(search_times)
        std_dev = statistics.stdev(search_times) if len(search_times) > 1 else 0
        
        # Log performance metrics
        print(f"\nVector Search Performance (n={num_runs}):")
        print(f"  Average search time: {avg_time:.4f} seconds")
        print(f"  Min search time: {min_time:.4f} seconds")
        print(f"  Max search time: {max_time:.4f} seconds")
        print(f"  Standard deviation: {std_dev:.4f} seconds")
        
        # Performance assertion - search should be reasonably fast
        # This is a flexible assertion that can be adjusted based on environment
        assert avg_time < 1.0, "Vector search is too slow, average time exceeds 1 second"
    
    @pytest.mark.asyncio
    async def test_hybrid_search_performance(self, vector_search_benchmark, update_benchmark_embeddings):
        """Benchmark performance of hybrid search."""
        # Define hybrid query for performance testing
        query = HybridQuery(
            query_text="vector database performance",
            keyword_query="benchmark OR performance OR optimization",
            limit=10,
            threshold=0.5,
            filter_weight=0.3
        )
        
        # Measure search time over multiple runs
        num_runs = 5
        search_times = []
        
        for _ in range(num_runs):
            start_time = time.time()
            results = await vector_search_benchmark.hybrid_search(query)
            end_time = time.time()
            
            # Record search time
            search_time = end_time - start_time
            search_times.append(search_time)
            
            # Validate that results were returned
            assert len(results) > 0
        
        # Calculate statistics
        avg_time = sum(search_times) / num_runs
        min_time = min(search_times)
        max_time = max(search_times)
        std_dev = statistics.stdev(search_times) if len(search_times) > 1 else 0
        
        # Log performance metrics
        print(f"\nHybrid Search Performance (n={num_runs}):")
        print(f"  Average search time: {avg_time:.4f} seconds")
        print(f"  Min search time: {min_time:.4f} seconds")
        print(f"  Max search time: {max_time:.4f} seconds")
        print(f"  Standard deviation: {std_dev:.4f} seconds")
        
        # Performance assertion - hybrid search should also be reasonably fast
        # This is a flexible assertion that can be adjusted based on environment
        assert avg_time < 1.5, "Hybrid search is too slow, average time exceeds 1.5 seconds"
    
    @pytest.mark.asyncio
    async def test_search_with_filters_performance(self, vector_search_benchmark, update_benchmark_embeddings):
        """Benchmark performance of vector search with filters."""
        # Define query for performance testing
        query = VectorQuery(
            query_text="technical documentation and tutorials",
            limit=10,
            threshold=0.5
        )
        
        # Define filters - test with category and type filters
        filters = [
            ("metadata->>'category'", "=", "technology"),
            ("metadata->>'type'", "IN", ("documentation", "tutorial"))
        ]
        
        # Measure search time over multiple runs
        num_runs = 5
        search_times = []
        
        for _ in range(num_runs):
            start_time = time.time()
            results = await vector_search_benchmark.search(query, filters=filters)
            end_time = time.time()
            
            # Record search time
            search_time = end_time - start_time
            search_times.append(search_time)
        
        # Calculate statistics
        avg_time = sum(search_times) / num_runs
        min_time = min(search_times)
        max_time = max(search_times)
        std_dev = statistics.stdev(search_times) if len(search_times) > 1 else 0
        
        # Log performance metrics
        print(f"\nFiltered Search Performance (n={num_runs}):")
        print(f"  Average search time: {avg_time:.4f} seconds")
        print(f"  Min search time: {min_time:.4f} seconds")
        print(f"  Max search time: {max_time:.4f} seconds")
        print(f"  Standard deviation: {std_dev:.4f} seconds")
        
        # Performance assertion
        assert avg_time < 1.2, "Filtered search is too slow, average time exceeds 1.2 seconds"