# Vector Search API

The Vector Search API provides powerful semantic search capabilities using PostgreSQL's pgvector extension, including similarity search, RAG (Retrieval-Augmented Generation), and hybrid search combining vector similarity with graph traversal.

## Key Features

- Vector index management
- Embedding generation and storage
- Semantic similarity search using text or vector queries
- Hybrid search combining graph traversal with vector similarity
- Retrieval-Augmented Generation (RAG) prompt creation
- Bulk document indexing for efficient processing

## API Endpoints

### Index Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vector-search/indexes` | POST | Create a new vector index |
| `/api/vector-search/indexes` | GET | List all vector indexes |
| `/api/vector-search/indexes/{index_id}` | GET | Get a vector index by ID |
| `/api/vector-search/indexes/{index_id}` | PUT | Update a vector index |
| `/api/vector-search/indexes/{index_id}` | DELETE | Delete a vector index |

### Embedding Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vector-search/embeddings` | POST | Create a new embedding from content |
| `/api/vector-search/embeddings/with-vector` | POST | Create a new embedding with a pre-generated vector |
| `/api/vector-search/embeddings/{embedding_id}` | GET | Get an embedding by ID |
| `/api/vector-search/embeddings/{embedding_id}` | PUT | Update an embedding |
| `/api/vector-search/embeddings/{embedding_id}` | DELETE | Delete an embedding |
| `/api/vector-search/generate-embedding` | POST | Generate an embedding vector for text |

### Search Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vector-search/search/text` | POST | Search using text |
| `/api/vector-search/search/vector` | POST | Search using a vector |
| `/api/vector-search/search/hybrid` | POST | Search using hybrid of vector and graph |

### RAG (Retrieval-Augmented Generation)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vector-search/rag/prompt` | POST | Create a RAG prompt with retrieved context |

### Document Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vector-search/documents` | POST | Index a document for vector search |
| `/api/vector-search/documents/search` | POST | Search documents using vector similarity |
| `/api/vector-search/documents/rag` | POST | Generate a RAG prompt using document search |

## Basic Usage Examples

### Create a Vector Index

```python
import requests
import json

# Create a new vector index
index_data = {
    "name": "document-index",
    "dimension": 1536,
    "index_type": "hnsw",
    "distance_metric": "cosine"
}

response = requests.post(
    "http://localhost:8000/api/vector-search/indexes", 
    json=index_data
)
print(json.dumps(response.json(), indent=2))
```

### Index a Document

```python
import requests

# Index a document
document = {
    "id": "doc1",
    "title": "Introduction to Vector Search",
    "content": "Vector search is a technique that enables similarity search by...",
    "metadata": {
        "author": "John Doe",
        "tags": ["vector", "search", "embeddings"]
    }
}

response = requests.post(
    "http://localhost:8000/api/vector-search/documents", 
    json=document
)
print(response.json())
```

### Search Documents

```python
import requests

# Search for similar documents
query = "How does vector similarity work?"
response = requests.post(
    "http://localhost:8000/api/vector-search/documents/search",
    json={
        "query": query,
        "limit": 5,
        "threshold": 0.7
    }
)
print(json.dumps(response.json(), indent=2))
```

### Generate a RAG Prompt

```python
import requests

# Generate a RAG prompt
data = {
    "query": "Explain how vector search handles large datasets",
    "system_prompt": "You are a helpful assistant that answers questions based on the provided context. If the context doesn't contain relevant information, acknowledge that you don't know.",
    "limit": 3,
    "threshold": 0.7
}

response = requests.post(
    "http://localhost:8000/api/vector-search/documents/rag", 
    json=data
)
print(json.dumps(response.json(), indent=2))
```

## Integration with Domain-Driven Design

The Vector Search API is implemented using a domain-driven design approach, which provides several benefits:

1. **Clear separation of concerns**: The API is structured around domain concepts like vector indices, embeddings, and search operations.
2. **Rich domain model**: Domain entities contain business logic and validation rules.
3. **Repository pattern**: Data access is abstracted behind repository interfaces.
4. **Service layer**: Complex operations are encapsulated in service classes.
5. **Dependency injection**: Components are loosely coupled for better testability.

## Using with the Uno Framework

The Vector Search module integrates seamlessly with the Uno framework:

```python
from fastapi import FastAPI, Depends
from uno.vector_search import (
    router as vector_search_router,
    configure_vector_search_dependencies,
    get_vector_search_service
)
from uno.vector_search.domain_services import VectorSearchService

# Configure dependencies
inject.configure(configure_vector_search_dependencies)

# Create FastAPI app
app = FastAPI()

# Include vector search router
app.include_router(vector_search_router)

# Example endpoint using vector search service
@app.get("/example")
async def example(
    vector_search_service: VectorSearchService = Depends(get_vector_search_service)
):
    # Use vector search service
    result = await vector_search_service.search_documents(
        query="example query",
        limit=5,
        threshold=0.7
    )
    return {"results": result.value if result.is_success() else []}
```

## API Reference

Each endpoint accepts and returns structured data in JSON format. Below are some key data structures:

### VectorIndexDTO

```json
{
  "id": "string",
  "name": "string",
  "dimension": 1536,
  "index_type": "hnsw",
  "distance_metric": "cosine",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "metadata": {}
}
```

### EmbeddingDTO

```json
{
  "id": "string",
  "vector": [0.1, 0.2, 0.3, ...],
  "source_id": "string",
  "source_type": "string",
  "model": "default",
  "dimension": 1536,
  "created_at": "2023-01-01T00:00:00Z",
  "metadata": {}
}
```

### SearchResultDTO

```json
{
  "id": "string",
  "similarity": 0.95,
  "entity_id": "string",
  "entity_type": "string",
  "rank": 1,
  "metadata": {}
}
```

### RAGPromptResponseDTO

```json
{
  "system_prompt": "string",
  "user_prompt": "string"
}
```

For more detailed information about the API, refer to the OpenAPI documentation available at `/docs` when running the API server.