# Vector Search in Uno

Uno provides powerful vector search capabilities through PostgreSQL's pgvector extension, allowing for semantic similarity searches and integrating with the existing graph database functionality.

## Overview

Vector search enables applications to find semantically similar content by comparing embedding vectors. This is particularly useful for:

- Semantic search
- Recommendation systems
- Content discovery
- Anomaly detection
- Retrieval-Augmented Generation (RAG)

Uno leverages PostgreSQL's pgvector extension to provide these capabilities natively in the database, offering several advantages:

- Automatic embedding generation using database triggers
- Efficient vector indexing with HNSW and IVF-Flat
- Transaction support and ACID properties
- Integration with the graph database for hybrid searches
- Proper role-based security model

## Architecture

The vector search implementation in Uno follows these architectural principles:

1. **Database-Native**: Core vector functionality lives directly in PostgreSQL
2. **Event-Driven**: Updates to vector embeddings use events and queues
3. **Integrated**: Vector search works with existing graph capabilities
4. **Dependency-Injected**: Components follow the DI pattern for clean integration
5. **Configurable**: Settings are managed through the standard config system

Key components include:

- **VectorSQLEmitter**: Generates SQL for vector columns, functions, and triggers
- **VectorSearchService**: High-level service for performing similarity searches
- **RAGService**: Service for retrieval-augmented generation
- **VectorEventHandler**: Processes vector-related events
- **VectorUpdateService**: Manages vector embedding updates with priority queuing

## Features

### Native PostgreSQL Integration

- Vector data type (pgvector extension)
- Automatic embedding generation via triggers
- Efficient vector indexing (HNSW and IVF-Flat)
- SQL functions for vector operations

### Search Capabilities

- Similarity search with configurable metrics (cosine, L2, dot product)
- Hybrid search combining graph traversal with vector similarity
- Filtering options for combining vector search with traditional SQL conditions
- Configurable thresholds and result limits

### RAG Support

- Retrieval-Augmented Generation for LLMs
- Context formatting for prompt creation
- Metadata extraction and processing

### Event-Driven Architecture

- Event system for vector content changes
- Priority-based update queue
- Batch processing capabilities
- Asynchronous embedding generation

## Getting Started

### Prerequisites

- PostgreSQL 12+ with pgvector extension
- Uno framework (latest version)

### Database Setup

The pgvector extension and vector functionality are automatically set up when you run:

```bash
python src/scripts/createdb.py
```

This script:
1. Creates the pgvector extension
2. Sets up helper functions for vector operations
3. Creates a documents table for RAG
4. Establishes triggers for automatic embedding generation

### Using Vector Search

```python
from uno.dependencies import get_service_provider

# Get the service provider
provider = get_service_provider()

# Get vector search service for documents
document_search = provider.get_vector_search_service(```

entity_type="document",
table_name="documents"
```
)

# Define a query
class SearchQuery:```

def __init__(self, query_text, limit=5, threshold=0.7):```

self.query_text = query_text
self.limit = limit
self.threshold = threshold
self.metric = "cosine"
```
``````

```
```

def model_dump(self):```

return {
    "query_text": self.query_text,
    "limit": self.limit,
    "threshold": self.threshold,
    "metric": self.metric
}
```
```

# Perform a search
query = SearchQuery("How do I use vector search?")
results = await document_search.search(query)

# Process results
for result in results:```

print(f"ID: {result.id}, Similarity: {result.similarity}")
if result.entity:```

print(f"Title: {result.entity.title}")
print(f"Content: {result.entity.content[:100]}...")
```
print()
```
```

### FastAPI Integration

Vector search endpoints are automatically registered with FastAPI:

```python
# GET /api/vector/config
# POST /api/vector/search/documents
# POST /api/vector/hybrid/documents
```

See the API documentation for details on using these endpoints.

## Advanced Configuration

### Vector Dimensions

The default embedding dimension is 1536 (OpenAI Ada 2), but you can configure different dimensions for different entity types:

```python
# In uno_settings.py
VECTOR_DIMENSIONS = 1536
VECTOR_ENTITIES = {```

"document": {```

"fields": ["title", "content"],
"dimensions": 1536,
"index_type": "hnsw"
```
},
"product": {```

"fields": ["name", "description"],
"dimensions": 384,
"index_type": "ivfflat"
```
}
```
}
```

### Index Types

Uno supports two index types:
- **HNSW**: Faster search but slower indexing and more memory usage
- **IVF-Flat**: Balanced approach with good search speed and memory usage

Configure in settings:
```python
VECTOR_INDEX_TYPE = "hnsw"  # Default index type
```

### Update Behavior

Control how vector embeddings are updated:
```python
VECTOR_BATCH_SIZE = 10      # Batch size for updates
VECTOR_UPDATE_INTERVAL = 1.0  # Update interval in seconds
VECTOR_AUTO_START = True    # Auto-start the update service
```

## Testing Vector Search

Uno includes comprehensive integration tests for vector search capabilities to ensure all components work correctly together:

### Running Vector Search Tests

```bash
# Run vector search integration tests
pytest tests/integration/test_vector_search.py --run-integration --run-pgvector

# Run vector search performance benchmarks
cd tests/integration
./run_benchmarks.py --csv
```

### Test Coverage

The integration tests for vector search cover:

1. **Basic Similarity Search**: Tests for different similarity metrics (cosine, L2, inner product)
2. **Hybrid Search**: Tests combining vector similarity with keyword filtering
3. **Search with Metadata Filters**: Tests filtering vectors by associated metadata
4. **Strongly-Typed Results**: Tests for type-safe search results
5. **RAG Integration**: Tests for retrieval-augmented generation
6. **Performance Benchmarks**: Measures and compares performance for various search operations

### Example Test

```python
@pytest.mark.asyncio
async def test_search_with_cosine_metric(vector_search_service, update_embeddings):```

"""Test vector search with cosine similarity metric."""
# Define query with explicit cosine metric
query = VectorQuery(```

query_text="neural networks embedding generation",
limit=5,
threshold=0.5,
metric=VectorMetric.COSINE
```
)
``````

```
```

# Execute search
results = await vector_search_service.search(query)
``````

```
```

# Validate results
assert len(results) > 0
assert all(r.similarity >= 0.5 for r in results)
assert results[0].similarity <= 1.0
```
```

## Further Reading

- [pgvector Integration](./pgvector_integration.md) - Detailed explanation of the PostgreSQL pgvector integration
- [Docker Setup](./docker_setup.md) - Setting up Docker with pgvector for development
- [API Usage](./api_usage.md) - How to use the vector search APIs in your application
- [Dependency Injection](./dependency_injection.md) - How to use vector search with the DI system
- [Hybrid Queries](./hybrid_queries.md) - Combining graph traversal with vector similarity
- [RAG Implementation](./rag.md) - Using Retrieval-Augmented Generation
- [Event-Driven Architecture](./event_driven.md) - How vector updates are processed