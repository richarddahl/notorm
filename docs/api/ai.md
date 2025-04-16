# AI Module API

The AI Module provides a comprehensive set of AI capabilities for the Uno framework, including semantic search, embeddings, content generation, recommendations, and anomaly detection.

## Key Features

- Vector embeddings for text and documents
- Semantic search with customizable similarity metrics
- Retrieval Augmented Generation (RAG) for LLM context enhancement
- Multi-model support (Sentence Transformers, OpenAI, Hugging Face)
- Batch processing for efficient operations
- Domain-driven design for clean architecture

## API Endpoints

### Embedding Model Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/embedding-models` | POST | Create a new embedding model |
| `/api/ai/embedding-models` | GET | List all embedding models |
| `/api/ai/embedding-models/{model_id}` | GET | Get an embedding model by ID |
| `/api/ai/embedding-models/{model_id}` | PUT | Update an embedding model |
| `/api/ai/embedding-models/{model_id}` | DELETE | Delete an embedding model |

### Embedding Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/embeddings/generate` | POST | Generate an embedding vector for text |
| `/api/ai/embeddings` | POST | Create and store an embedding for text |
| `/api/ai/embeddings/batch` | POST | Batch create embeddings for multiple texts |
| `/api/ai/embeddings/similarity` | POST | Compute similarity between two embedding vectors |

### Semantic Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/search/index` | POST | Index a document for semantic search |
| `/api/ai/search/index/batch` | POST | Batch index documents for semantic search |
| `/api/ai/search` | POST | Perform a semantic search |
| `/api/ai/search/documents/{entity_id}` | DELETE | Delete document from the search index |

### Retrieval Augmented Generation (RAG)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/rag/prompt` | POST | Create a RAG prompt with retrieved context |

## Basic Usage Examples

### Creating an Embedding Model

```python
import requests
import json

# Create a new embedding model
model_data = {
    "name": "sentence-transformers/all-MiniLM-L6-v2",
    "model_type": "sentence_transformer",
    "dimensions": 384,
    "normalize_vectors": True
}

response = requests.post(
    "http://localhost:8000/api/ai/embedding-models", 
    json=model_data
)
print(json.dumps(response.json(), indent=2))
```

### Generating an Embedding

```python
import requests

# Generate embedding for text
data = {
    "text": "This is a sample text to embed",
    "model_name": "sentence-transformers/all-MiniLM-L6-v2"
}

response = requests.post(
    "http://localhost:8000/api/ai/embeddings/generate", 
    json=data
)
print(f"Dimension: {len(response.json()['vector'])}")
```

### Indexing a Document

```python
import requests

# Index a document for semantic search
doc_data = {
    "content": "This is a sample document about artificial intelligence and machine learning.",
    "entity_id": "doc-123",
    "entity_type": "article",
    "metadata": {
        "author": "Jane Smith",
        "tags": ["AI", "ML", "tutorial"]
    }
}

response = requests.post(
    "http://localhost:8000/api/ai/search/index", 
    json=doc_data
)
print(json.dumps(response.json(), indent=2))
```

### Performing a Semantic Search

```python
import requests

# Perform semantic search
search_data = {
    "query_text": "machine learning concepts",
    "entity_type": "article"
}

response = requests.post(
    "http://localhost:8000/api/ai/search?limit=5&similarity_threshold=0.6", 
    json=search_data
)
print(json.dumps(response.json(), indent=2))
```

### Creating a RAG Prompt

```python
import requests

# Create RAG prompt
rag_data = {
    "query": "Explain machine learning in simple terms",
    "system_prompt": "You are a helpful assistant that explains complex topics in simple terms. Use the provided context to answer the user's question accurately.",
    "entity_type": "article"
}

response = requests.post(
    "http://localhost:8000/api/ai/rag/prompt?limit=3&similarity_threshold=0.6", 
    json=rag_data
)
print(json.dumps(response.json(), indent=2))
```

## Integration with Domain-Driven Design

The AI module follows a domain-driven design approach with clear separation of concerns:

1. **Domain Entities**: Core business objects like `EmbeddingModel`, `Embedding`, `SearchQuery`, etc.
2. **Value Objects**: Immutable identifiers like `EmbeddingId`, `ModelId`, etc.
3. **Repositories**: Data access interfaces for persistence operations
4. **Domain Services**: Business logic operations that work with multiple entities
5. **Application Services**: Coordinate domain services and other application components
6. **DTOs**: Data transfer objects for API request/response payloads

## Using with the Uno Framework

The AI module integrates seamlessly with the Uno framework:

```python
from fastapi import FastAPI, Depends
from uno.ai import (
    ai_router,
    configure_ai_dependencies,
    get_embedding_service,
    get_semantic_search_service
)
from uno.ai.domain_services import EmbeddingService, SemanticSearchService

# Configure dependencies
inject.configure(configure_ai_dependencies)

# Create FastAPI app
app = FastAPI()

# Include AI router
app.include_router(ai_router)

# Example endpoint using AI services
@app.post("/api/custom/embed-and-search")
async def embed_and_search(
    text: str,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    search_service: SemanticSearchService = Depends(get_semantic_search_service)
):
    # Generate embedding
    embedding_result = await embedding_service.generate_embedding(text)
    if embedding_result.is_failure():
        return {"error": embedding_result.error}
    
    vector = embedding_result.value
    
    # Use vector for search
    search_result = await search_service.search_by_vector(
        vector=vector,
        limit=5,
        similarity_threshold=0.7
    )
    
    # Return combined results
    return {
        "embedding_dimensions": len(vector),
        "search_results": search_result.value if search_result.is_success() else []
    }
```

## Configuration

When using the AI module, you may need to configure additional dependencies:

```python
# Set up environment
import os
os.environ["OPENAI_API_KEY"] = "your-openai-key"

# Configure Uno's dependency injection
from uno.ai import configure_ai_dependencies
import inject

# Add AI module dependencies to the container
def configure_dependencies(binder):
    # Configure base dependencies
    from uno.dependencies import configure_base_dependencies
    configure_base_dependencies(binder)
    
    # Configure AI dependencies
    configure_ai_dependencies(binder)
    
    # Add any custom bindings
    # ...

# Initialize the container
inject.configure(configure_dependencies)
```

## Model Support

The AI module supports multiple embedding model types:

1. **Sentence Transformers** - Efficient models like `all-MiniLM-L6-v2`
2. **Hugging Face Transformers** - Models like BERT, RoBERTa, etc.
3. **OpenAI** - Models like `text-embedding-3-small` from OpenAI API
4. **Custom** - Custom model implementations

You can extend the module to support additional model types by implementing new model handlers in the embedding service.