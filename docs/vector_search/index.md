# Vector Search Documentation

Welcome to the vector search documentation for the Uno Framework. This section covers how to use PostgreSQL with pgvector to implement powerful vector similarity search capabilities.

## Table of Contents

### Getting Started
- [Overview](./overview.md) - Introduction to vector search in Uno
- [pgvector Integration](./pgvector_integration.md) - How pgvector is integrated with PostgreSQL
- [Docker Setup](./docker_setup.md) - Setting up Docker with pgvector for development

### Usage Guides
- [API Usage](./api_usage.md) - Using the vector search APIs
- [Dependency Injection](./dependency_injection.md) - DI integration for vector services

### Advanced Topics
- [Hybrid Search](./hybrid_search.md) - Combining graph traversal with vector similarity
- [RAG Implementation](./rag.md) - Retrieval-Augmented Generation
- [Event-Driven Architecture](./events.md) - Event-based embedding updates

## Quick Start

1. **Set up the Docker environment**:
   ```bash
   cd /path/to/notorm/docker
   ./rebuild.sh
   ```

2. **Create the database with vector support**:
   ```bash
   export ENV=dev
   cd /path/to/notorm
   python src/scripts/createdb.py
   ```

3. **Use vector search in your application**:
   ```python
   from uno.dependencies import get_service_provider
   
   # Get the service provider
   provider = get_service_provider()
   
   # Get vector search service
   document_search = provider.get_vector_search_service(```

   entity_type="document",
   table_name="documents"
```
   )
   
   # Search for similar documents
   results = await document_search.search({```

   "query_text": "How do I use vector search?",
   "limit": 10,
   "threshold": 0.7
```
   })
   ```

## Key Features

- **Vector Similarity Search**: Find semantically similar content
- **Automatic Embedding Generation**: Database triggers handle embedding creation
- **Efficient Indexing**: HNSW and IVF-Flat indexes for fast search
- **Hybrid Search**: Combine graph traversal with vector similarity
- **RAG Support**: Build context for LLMs from vector search results
- **Event-Driven Updates**: Real-time embedding updates with priority queue

## Support and Feedback

If you have questions or feedback about vector search, please submit an issue in the GitHub repository.