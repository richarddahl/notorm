# Using Vector Search

This guide shows how to use the vector search capabilities in your application.

## Basic Vector Search

For simple vector similarity search:

```python
from uno.domain.vector_search import VectorSearchService, VectorQuery

# Create vector search service
vector_search = VectorSearchService(
    entity_type=Document,
    table_name="document",
    repository=document_repository
    # schema parameter is optional, defaults to uno_settings.DB_SCHEMA
)

# Create a search query
query = VectorQuery(
    query_text="How do I implement vector search?",
    limit=10,
    threshold=0.75,
    metric="cosine"  # Options: "cosine", "l2", "dot"
)

# Perform search
results = await vector_search.search(query)

# Process results
for result in results:
    print(f"ID: {result.id}, Similarity: {result.similarity}")
    if result.entity:
        print(f"Title: {result.entity.title}")
```

## Distance Metrics

The system supports three distance metrics:

1. **Cosine Similarity** (`"cosine"`): Measures the angle between vectors, useful for comparing text embeddings.
2. **Euclidean Distance** (`"l2"`): Measures the straight-line distance between vectors.
3. **Dot Product** (`"dot"`): Measures the product of corresponding dimensions.

Choose the metric based on your embedding model and use case.

## Hybrid Graph and Vector Search

For more complex queries that combine graph traversal with vector similarity:

```python
from uno.domain.vector_search import HybridQuery

# Create a hybrid query
hybrid_query = HybridQuery(
    query_text="How do I use vector search with graph databases?",
    limit=10,
    threshold=0.7,
    start_node_type="Document",
    start_filters={"category": "technical"},
    path_pattern="(n:Document)-[:REFERENCES]->(:Topic)-[:RELATED_TO]->(end_node:Document)"
)

# Perform hybrid search
hybrid_results = await vector_search.hybrid_search(hybrid_query)

# Process results
for result in hybrid_results:
    print(f"ID: {result.id}, Similarity: {result.similarity}")
    # Results have additional metadata about graph traversal
    print(f"Path data: {result.metadata}")
```

This will:
1. Start from Document nodes with category "technical"
2. Traverse the graph along the specified path
3. Rank the results by vector similarity to the query text

## Using RAG (Retrieval-Augmented Generation)

For LLM applications, you can use the RAG service to retrieve relevant context:

```python
from uno.domain.vector_search import RAGService

# Create RAG service
rag_service = RAGService(
    vector_search=vector_search
)

# Get entities for context
entities, search_results = await rag_service.retrieve_context(
    query="Explain vector search in databases",
    limit=5,
    threshold=0.7
)

# Format context for an LLM
context = rag_service.format_context_for_prompt(entities)

# Or get a complete RAG prompt
rag_prompt = await rag_service.create_rag_prompt(
    query="Explain vector search in databases",
    system_prompt="You are a helpful assistant...",
    limit=5,
    threshold=0.7
)

# Use with your LLM service
system_prompt = rag_prompt["system_prompt"]
user_prompt = rag_prompt["user_prompt"]
```

## Custom RAG Context Formatting

You can customize how entities are formatted for RAG by subclassing:

```python
class DocumentRAG(RAGService[Document]):
    def format_context_for_prompt(self, entities: List[Document]) -> str:
        context_parts = []
        
        for i, doc in enumerate(entities):
            context_text = f"[Document {i+1}]\n"
            context_text += f"Title: {doc.title}\n"
            context_text += f"Content: {doc.content}\n"
            
            if doc.author:
                context_text += f"Author: {doc.author}\n"
                
            context_parts.append(context_text)
        
        return "\n---\n".join(context_parts)
```

## Generating Embeddings Directly

If you need to generate an embedding for external use:

```python
# Generate embedding vector
embedding = await vector_search.generate_embedding("Text to embed")

# embedding is a list of floats
print(f"Generated embedding with {len(embedding)} dimensions")
```

This uses the same embedding function as your database triggers for consistency.