# Vector Search Examples

This directory contains examples demonstrating the vector search capabilities of uno.

## Contents

- `vector_search_example.py`: Comprehensive example demonstrating basic vector search, filtering, hybrid search, RAG, and embedding generation

## Prerequisites

1. PostgreSQL with pgvector extension installed
2. Database setup with uno
3. Sample document data in the database

## Setting Up the Environment

1. Ensure PostgreSQL is running with pgvector extension:
   ```bash
   cd /path/to/notorm/docker
   ./rebuild.sh
   ```

2. Create the database with vector support:
   ```bash
   export ENV=dev
   cd /path/to/notorm
   python src/scripts/createdb.py
   ```

3. Create example documents:
   ```bash
   python src/scripts/vector_demo.py
   ```

## Running the Examples

To run the main example:

```bash
cd /path/to/notorm
python examples/vector_search/vector_search_example.py
```

## Example Features

### Basic Vector Search

```python
# Get vector search service
document_search = provider.get_vector_search_service(
    entity_type="document",
    table_name="documents"
)

# Define a search query
query = VectorQuery(
    query_text="How does vector search work?",
    limit=5,
    threshold=0.7
)

# Execute the search
results = await document_search.search(query)
```

### Filtered Search

```python
# Define filters (SQL WHERE conditions)
filters = [
    ("metadata->>'category'", "=", "technical"),
    ("created_at", ">", "2023-01-01")
]

# Execute the search with filters
results = await document_search.search(query, filters=filters)
```

### Hybrid Search

```python
# Define a hybrid search query
query = HybridQuery(
    query_text="machine learning algorithms",
    limit=5,
    threshold=0.7,
    graph_depth=2,
    graph_weight=0.3
)

# Execute the hybrid search
results = await document_search.hybrid_search(query)
```

### Retrieval-Augmented Generation (RAG)

```python
# Get RAG service
rag_service = provider.get_rag_service(
    entity_type="document",
    table_name="documents"
)

# Create a RAG prompt
prompt = await rag_service.create_rag_prompt(
    query="What are the key principles of effective database design?",
    system_prompt="You are a helpful assistant that provides information about databases.",
    limit=3,
    threshold=0.7
)
```

### Embedding Generation

```python
# Generate embedding for text
embedding = await document_search.generate_embedding(
    "Vector embeddings are numerical representations of text."
)
```

### Vector Content Updates

```python
# Get vector update service
update_service = provider.get_vector_update_service()

# Queue an update
await update_service.queue_update(
    entity_id="example123",
    entity_type="document",
    content="This is example content that will be vectorized.",
    priority=5
)
```

## Further Learning

For more information about vector search in uno, refer to the [Vector Search Documentation](../../docs/vector_search/overview.md).