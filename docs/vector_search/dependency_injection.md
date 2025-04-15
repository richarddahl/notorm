# Vector Search Dependency Injection

This document explains how to use the vector search components with the uno dependency injection system.

## Overview

The vector search components are fully integrated with the uno dependency injection system, allowing for:

- Type-safe access to vector services
- Centralized configuration management
- Consistent service initialization
- Easy testing with mocks
- Clean separation of concerns

## Service Provider

The vector search components are registered with the service provider at application startup. The following services are available:

- `VectorConfigServiceProtocol`: Configuration for vector search components
- `VectorSearchServiceProtocol`: Services for performing vector similarity searches
- `RAGServiceProtocol`: Services for retrieval-augmented generation
- `VectorUpdateServiceProtocol`: Services for managing vector embedding updates
- `BatchVectorUpdateServiceProtocol`: Services for batch vector operations

## Getting Vector Services

### Using the Service Provider

The easiest way to access vector services is through the service provider:

```python
from uno.dependencies import get_service_provider

# Get the service provider
provider = get_service_provider()

# Get vector configuration
vector_config = provider.get_vector_config()

# Get vector search service for a specific entity type
document_search = provider.get_vector_search_service(```

entity_type="document",
table_name="documents"
```
)

# Get RAG service
rag_service = provider.get_rag_service(document_search)

# Get vector update service
update_service = provider.get_vector_update_service()

# Get batch update service
batch_service = provider.get_batch_vector_update_service()
```

### Direct Access Functions

You can also use direct access functions for some services:

```python
from uno.dependencies import get_vector_search_service, get_rag_service

# Get vector search service
document_search = get_vector_search_service(```

entity_type="document",
table_name="documents"
```
)

# Get RAG service
rag_service = get_rag_service(document_search)
```

### FastAPI Dependency Injection

Vector services integrate with FastAPI's dependency injection system:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import VectorConfigServiceProtocol
from uno.dependencies.fastapi import inject_dependency

router = APIRouter()

@router.get("/vector/config")
async def get_config(```

config: VectorConfigServiceProtocol = Depends(inject_dependency(VectorConfigServiceProtocol))
```
):```

"""Get vector search configuration."""
return {```

"default_dimensions": config.get_dimensions(),
"default_index_type": config.get_index_type(),
"vectorizable_entities": list(config.get_all_vectorizable_entities().keys())
```
}
```
```

## Configuration

Vector search components can be configured in `uno_settings.py`:

```python
# Vector search configuration
VECTOR_DIMENSIONS = 1536  # Default embedding dimensions
VECTOR_INDEX_TYPE = "hnsw"  # Default index type (hnsw, ivfflat)
VECTOR_BATCH_SIZE = 10  # Default batch size for updates
VECTOR_UPDATE_INTERVAL = 1.0  # Default update interval in seconds
VECTOR_AUTO_START = True  # Whether to auto-start the update service

# Pre-configure vector entities
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

## Custom Entity Registration

You can register custom entity types with the vector configuration service:

```python
from uno.dependencies import get_service_provider

# Get vector config service
provider = get_service_provider()
vector_config = provider.get_vector_config()

# Register a new vectorizable entity
vector_config.register_vectorizable_entity(```

entity_type="custom_entity",
fields=["title", "description", "content"],
dimensions=1536,
index_type="hnsw"
```
)
```

## Example Usage

Here's a complete example of using vector search with dependency injection:

```python
import asyncio
from uno.dependencies import get_service_provider, initialize_services

async def main():```

# Initialize services
initialize_services()
provider = get_service_provider()
``````

```
```

# Get vector search service
document_search = provider.get_vector_search_service(```

entity_type="document",
table_name="documents"
```
)
``````

```
```

# Define a query
class SearchQuery:```

def __init__(self, query_text, limit=5, threshold=0.7):
    self.query_text = query_text
    self.limit = limit
    self.threshold = threshold
    self.metric = "cosine"
    
def model_dump(self):
    return {
        "query_text": self.query_text,
        "limit": self.limit,
        "threshold": self.threshold,
        "metric": self.metric
    }
```
``````

```
```

# Perform a search
query = SearchQuery("Example search query")
results = await document_search.search(query)
``````

```
```

# Process results
for result in results:```

print(f"ID: {result.id}, Similarity: {result.similarity}")
if result.entity:
    print(f"Title: {result.entity.title}")
    print(f"Content: {result.entity.content[:100]}...")
print()
```
```

if __name__ == "__main__":```

asyncio.run(main())
```
```

## Testing

The vector search components are designed for easy testing with mocks:

```python
import pytest
from unittest.mock import MagicMock
from uno.dependencies import (```

ServiceProvider,
VectorConfigServiceProtocol,
VectorSearchServiceProtocol
```
)

@pytest.fixture
def mock_vector_config():```

"""Mock vector configuration service."""
config = MagicMock(spec=VectorConfigServiceProtocol)
config.get_dimensions.return_value = 1536
config.get_index_type.return_value = "hnsw"
config.is_vectorizable.return_value = True
config.get_vectorizable_fields.return_value = ["title", "content"]
return config
```

@pytest.fixture
def mock_service_provider(mock_vector_config):```

"""Mock service provider with vector services."""
provider = ServiceProvider()
provider._initialized = True
provider.register_service(VectorConfigServiceProtocol, mock_vector_config)
return provider
```

def test_vector_search(mock_service_provider, mock_vector_config):```

"""Test vector search with mocked services."""
# Arrange
provider = mock_service_provider
assert provider.get_vector_config() == mock_vector_config
``````

```
```

# Act/Assert - further test implementation...
```
```

For more complete examples, see:
- `/docs/vector_search/di_example.py`: Complete example of using vector search with DI
- `/src/uno/vector_search/endpoints.py`: FastAPI endpoints using vector search services
- `/tests/unit/dependencies/test_vector_provider.py`: Unit tests for vector DI components