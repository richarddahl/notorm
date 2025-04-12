"""
Performance benchmarks for vector search functionality.

These benchmarks measure the performance of vector search operations
under different conditions to help identify bottlenecks and
optimization opportunities.
"""

import pytest
import asyncio
import time
import uuid
import json
import random
from typing import List, Dict, Any, Optional

from uno.domain.vector_search import (
    VectorSearchService,
    RAGService,
    VectorQuery,
    HybridQuery
)
from uno.database.session import async_session


# Skip these benchmarks in normal test runs
pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.pgvector,
    pytest.mark.skipif(
        "not config.getoption('--run-benchmark')",
        reason="Only run when --run-benchmark is specified"
    )
]


@pytest.fixture(scope="module")
async def vector_search_service():
    """Create a VectorSearchService for benchmarking."""
    service = VectorSearchService(
        entity_type="benchmark_document",
        table_name="benchmark_documents",
        dimensions=1536
    )
    yield service


@pytest.fixture(scope="module")
async def db_session():
    """Create a database session."""
    async with async_session() as session:
        yield session


@pytest.fixture(scope="module")
async def setup_benchmark_environment(db_session):
    """Set up the benchmark environment with test data."""
    # Create a benchmark table
    await db_session.execute("""
    DROP TABLE IF EXISTS benchmark_documents;
    
    CREATE TABLE benchmark_documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata JSONB,
        embedding VECTOR(1536)
    );
    
    CREATE INDEX IF NOT EXISTS benchmark_documents_embedding_idx ON benchmark_documents
    USING hnsw (embedding vector_cosine_ops);
    """)
    
    await db_session.commit()
    
    # Generate random embeddings
    def generate_random_embedding(dims=1536):
        """Generate a random unit vector."""
        vec = [random.gauss(0, 1) for _ in range(dims)]
        # Normalize to unit length
        magnitude = sum(x*x for x in vec) ** 0.5
        return [x/magnitude for x in vec]
    
    # Generate benchmark data with different sizes
    batch_sizes = [100, 1000, 5000]
    total_docs = sum(batch_sizes)
    
    print(f"Setting up benchmark with {total_docs} documents...")
    
    for batch_size in batch_sizes:
        documents = []
        for i in range(batch_size):
            doc_id = str(uuid.uuid4())
            title = f"Benchmark Document {i}"
            content = f"This is benchmark document {i} with random content for testing vector search performance."
            metadata = json.dumps({"type": "benchmark", "batch_size": batch_size, "index": i})
            embedding = generate_random_embedding()
            
            documents.append({
                "id": doc_id,
                "title": title,
                "content": content,
                "metadata": metadata,
                "embedding": embedding
            })
        
        # Insert documents in batches
        for i in range(0, len(documents), 100):
            batch = documents[i:i+100]
            query = """
            INSERT INTO benchmark_documents (id, title, content, metadata, embedding)
            VALUES (:id, :title, :content, :metadata, :embedding)
            """
            await db_session.execute(query, batch)
            await db_session.commit()
        
        print(f"Inserted batch of {batch_size} documents")
    
    yield
    
    # Clean up
    await db_session.execute("DROP TABLE IF EXISTS benchmark_documents")
    await db_session.commit()


@pytest.mark.asyncio
async def test_vector_search_small_dataset(vector_search_service, setup_benchmark_environment, benchmark):
    """Benchmark vector search on a small dataset (100 documents)."""
    # Generate a test query
    query = VectorQuery(
        query_text="performance benchmark test",
        limit=10,
        threshold=0.5
    )
    
    # Create a filter for the small batch
    filters = [
        ("metadata->>'batch_size'", "=", "100")
    ]
    
    # Define async benchmark function
    async def search_benchmark():
        results = await vector_search_service.search(query, filters=filters)
        return results
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(search_benchmark()), 
        iterations=10,
        rounds=3
    )
    
    print(f"Vector search on small dataset took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_vector_search_medium_dataset(vector_search_service, setup_benchmark_environment, benchmark):
    """Benchmark vector search on a medium dataset (1000 documents)."""
    # Generate a test query
    query = VectorQuery(
        query_text="performance benchmark test",
        limit=10,
        threshold=0.5
    )
    
    # Create a filter for the medium batch
    filters = [
        ("metadata->>'batch_size'", "=", "1000")
    ]
    
    # Define async benchmark function
    async def search_benchmark():
        results = await vector_search_service.search(query, filters=filters)
        return results
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(search_benchmark()), 
        iterations=5,
        rounds=3
    )
    
    print(f"Vector search on medium dataset took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_vector_search_large_dataset(vector_search_service, setup_benchmark_environment, benchmark):
    """Benchmark vector search on a large dataset (5000 documents)."""
    # Generate a test query
    query = VectorQuery(
        query_text="performance benchmark test",
        limit=10,
        threshold=0.5
    )
    
    # Create a filter for the large batch
    filters = [
        ("metadata->>'batch_size'", "=", "5000")
    ]
    
    # Define async benchmark function
    async def search_benchmark():
        results = await vector_search_service.search(query, filters=filters)
        return results
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(search_benchmark()), 
        iterations=3,
        rounds=3
    )
    
    print(f"Vector search on large dataset took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_vector_search_with_limit_variations(vector_search_service, setup_benchmark_environment, benchmark):
    """Benchmark vector search with different result limits."""
    # Define test limits
    limits = [10, 50, 100, 500]
    
    # Generate test embeddings
    def generate_random_embedding(dims=1536):
        vec = [random.gauss(0, 1) for _ in range(dims)]
        magnitude = sum(x*x for x in vec) ** 0.5
        return [x/magnitude for x in vec]
    
    # Prepare a random embedding for the query
    embedding = generate_random_embedding()
    
    # Results to compare
    search_times = {}
    
    # Run benchmarks for each limit
    for limit in limits:
        # Generate a test query
        query = VectorQuery(
            query_text="performance benchmark test",
            limit=limit,
            threshold=0.3  # Lower threshold to ensure we get enough results
        )
        
        # Define async benchmark function for this limit
        async def search_benchmark():
            results = await vector_search_service.search(query)
            return results
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(search_benchmark()), 
            iterations=3,
            rounds=3,
            name=f"vector_search_limit_{limit}"
        )
        
        search_times[limit] = runtime
        print(f"Vector search with limit={limit} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nVector search performance by result limit:")
    for limit in limits:
        print(f"  Limit {limit}: {search_times[limit]:.4f} seconds")


@pytest.mark.asyncio
async def test_hybrid_search_performance(vector_search_service, setup_benchmark_environment, benchmark):
    """Benchmark hybrid search combining vector search with graph traversal."""
    # Generate a test query
    query = HybridQuery(
        query_text="performance benchmark test",
        limit=10,
        threshold=0.5,
        graph_depth=2
    )
    
    # Define async benchmark function
    async def hybrid_search_benchmark():
        results = await vector_search_service.hybrid_search(query)
        return results
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(hybrid_search_benchmark()), 
        iterations=3,
        rounds=3
    )
    
    print(f"Hybrid search took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_rag_context_retrieval_performance(setup_benchmark_environment, benchmark):
    """Benchmark RAG context retrieval performance."""
    # Create RAG service with the vector search service
    vector_service = VectorSearchService(
        entity_type="benchmark_document",
        table_name="benchmark_documents",
        dimensions=1536
    )
    
    rag_service = RAGService(
        search_service=vector_service,
        content_fields=["title", "content"]
    )
    
    # Define async benchmark function
    async def rag_benchmark():
        entities, results = await rag_service.retrieve_context(
            query="performance benchmark test",
            limit=5,
            threshold=0.5
        )
        return entities, results
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(rag_benchmark()), 
        iterations=5,
        rounds=3
    )
    
    print(f"RAG context retrieval took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_vector_embedding_generation_performance(vector_search_service, benchmark):
    """Benchmark vector embedding generation performance."""
    # Generate test text of different lengths
    texts = [
        "Short test text",
        "Medium length test text with some more words to process",
        "A longer test paragraph that contains multiple sentences. This text is designed to test the performance of embedding generation with more content. It should be substantially longer than the previous examples to measure scaling with text length."
    ]
    
    # Benchmark each text length
    for i, text in enumerate(texts):
        # Define async benchmark function for this text
        async def embedding_benchmark():
            embedding = await vector_search_service.generate_embedding(text)
            return embedding
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(embedding_benchmark()), 
            iterations=10,
            rounds=3,
            name=f"embedding_generation_{i+1}"
        )
        
        print(f"Embedding generation for text {i+1} ({len(text)} chars) took {runtime:.4f} seconds")