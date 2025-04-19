# Vector Search in UNO

This guide provides a comprehensive overview of vector search capabilities in the UNO framework, including embedding models, vector storage, semantic search, and integration with domain entities.

## Overview

Vector search enables finding content based on semantic similarity rather than exact keyword matches. UNO's vector search capabilities leverage modern embedding models to convert text into high-dimensional vectors and PostgreSQL's pgvector extension for efficient similarity search.

Key components of UNO's vector search system:

1. **Embedding Models**: Convert text to vector representations
2. **Vector Storage**: Store and query embedding vectors efficiently 
3. **Semantic Search Engine**: Coordinate embedding and search operations
4. **Domain Integration**: Connect vector search with domain entities
5. **API Endpoints**: Expose search capabilities via REST API

## Embedding Models

UNO provides a unified interface for text embedding models through the `EmbeddingModel` abstraction:

```python
from uno.ai.embeddings import get_embedding_model, EmbeddingModel

# Get the default embedding model (sentence-transformers)
model = get_embedding_model()

# Convert text to embedding vector
text = "Example document for semantic search"
embedding = model.embed(text)  # Returns numpy array

# Convert multiple texts in one call (more efficient)
texts = ["Document 1", "Document 2", "Document 3"]
embeddings = model.embed_batch(texts)  # Returns numpy array
```

### Supported Embedding Models

UNO supports multiple embedding backends:

1. **Sentence Transformers**: Open source models for local embedding
2. **OpenAI Embeddings**: High-quality embeddings via OpenAI API

```python
from uno.ai.embeddings import (
    SentenceTransformerModel, 
    OpenAIEmbeddingModel,
    embedding_registry
)

# Use specific Sentence Transformer model
st_model = SentenceTransformerModel(model_name="all-MiniLM-L6-v2")

# Use OpenAI embedding model
openai_model = OpenAIEmbeddingModel(
    model_name="text-embedding-ada-002",
    api_key="your-api-key"  # Optional, can use OPENAI_API_KEY env var
)

# Register models for later use
embedding_registry.register("minilm", st_model)
embedding_registry.register("openai", openai_model)

# Use registered model
model = get_embedding_model("openai")
```

## Vector Storage

UNO provides vector storage capabilities to save, query, and manage embedding vectors:

```python
from uno.ai.vector_storage import create_vector_storage

# Create vector storage with PostgreSQL/pgvector
storage = await create_vector_storage(
    storage_type="pgvector",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    table_name="vector_embeddings",
    dimensions=384,  # Match your embedding model's dimensions
    schema="public"
)

# Initialize storage (creates tables and indexes if needed)
await storage.initialize()

# Store embedding for an entity
entity_id = "doc123"
entity_type = "document"
embedding = model.embed("Example document text")
metadata = {"title": "Example Document", "author": "John Doe"}

record_id = await storage.store(
    entity_id=entity_id,
    entity_type=entity_type,
    embedding=embedding,
    metadata=metadata
)

# Search for similar entities
query_embedding = model.embed("Find similar documents")
results = await storage.search(
    query_embedding=query_embedding,
    entity_type="document",  # Optional filter
    limit=10,
    similarity_threshold=0.7  # Minimum similarity score (0-1)
)

# Delete entity embeddings
await storage.delete(entity_id="doc123")

# Clean up 
await storage.close()
```

### pgvector Integration

UNO uses PostgreSQL with the pgvector extension for efficient vector storage and similarity search. The implementation:

1. Automatically creates necessary tables and indexes
2. Implements efficient vector indexing with IVF (Inverted File) for fast approximate search
3. Supports metadata storage alongside vectors
4. Provides optimized batch operations

## Semantic Search Engine

The `SemanticSearchEngine` class combines embedding models with vector storage:

```python
from uno.ai.semantic_search import SemanticSearchEngine

# Create search engine
engine = SemanticSearchEngine(
    embedding_model="default",  # or "openai", etc.
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    table_name="vector_embeddings",
    schema="public"
)

# Initialize the engine (sets up storage)
await engine.initialize()

# Index a document
document_id = await engine.index_document(
    document="Example document with important information about semantic search.",
    entity_id="doc123",
    entity_type="document",
    metadata={"title": "Semantic Search Guide", "author": "Jane Smith"}
)

# Index multiple documents in batch
batch_docs = [
    {
        "text": "Document 1 content",
        "entity_id": "doc1",
        "entity_type": "document",
        "metadata": {"title": "Doc 1"}
    },
    {
        "text": "Document 2 content",
        "entity_id": "doc2",
        "entity_type": "document",
        "metadata": {"title": "Doc 2"}
    }
]
doc_ids = await engine.index_batch(batch_docs)

# Search for similar documents
results = await engine.search(
    query="Find information about semantic search",
    entity_type="document",  # Optional filter
    limit=5,
    similarity_threshold=0.7
)

# Each result contains:
# - id: Internal ID
# - entity_id: Original entity ID
# - entity_type: Entity type
# - metadata: Stored metadata
# - similarity: Similarity score (0-1)

# Delete a document
await engine.delete_document(entity_id="doc123")

# Clean up
await engine.close()
```

## Integration with Domain Entities

UNO provides utilities to automatically index and search domain entities:

```python
from uno.ai.semantic_search.integration import EntityIndexer, connect_entity_events
from uno.core.unified_events import EventBus, UnoDomainEvent

# Define domain entity events
class ProductCreatedEvent(UnoDomainEvent):
    entity: Product

class ProductUpdatedEvent(UnoDomainEvent):
    entity: Product

class ProductDeletedEvent(UnoDomainEvent):
    entity_id: UUID
    entity_type: str = "product"

# Create event bus
event_bus = EventBus()

# Create entity indexer
indexer = EntityIndexer(
    engine=search_engine,
    entity_type="product",
    # Extract text for search from entity
    text_extractor=lambda p: f"{p.name} {p.description} {p.category}",
    # Extract metadata to store with vector
    metadata_extractor=lambda p: {
        "name": p.name,
        "price": p.price,
        "category": p.category,
    },
    entity_class=Product,
)

# Connect to domain events
connect_entity_events(
    indexer=indexer,
    event_bus=event_bus,
    entity_created_event=ProductCreatedEvent,
    entity_updated_event=ProductUpdatedEvent,
    entity_deleted_event=ProductDeletedEvent,
)

# Now when events are published, entities will be automatically indexed
# This keeps the search index in sync with your domain data
```

## API Integration

UNO provides FastAPI endpoints for semantic search:

```python
from fastapi import FastAPI
from uno.ai.semantic_search.api import integrate_semantic_search

# Create FastAPI app
app = FastAPI()

# Add semantic search endpoints
integrate_semantic_search(
    app,
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    prefix="/api/semantic",
    tags=["semantic-search"]
)

# This creates the following endpoints:
# - POST /api/semantic/index - Index a document
# - POST /api/semantic/batch - Index multiple documents
# - POST /api/semantic/search - Search for documents
# - GET /api/semantic/search - Search with query parameters
# - POST /api/semantic/delete - Delete a document
# - DELETE /api/semantic/documents/{entity_id} - Delete by ID
```

### Custom Search Endpoints

You can also create custom endpoints that combine semantic search with your domain logic:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()

class ProductSearchResult(BaseModel):
    id: UUID
    name: str
    description: str
    price: float
    similarity: float

@router.get("/products/search/{query}", response_model=List[ProductSearchResult])
async def search_products(query: str, engine=Depends(get_search_engine)):
    """Search for products with semantic search."""
    # Perform semantic search
    results = await engine.search(
        query=query, 
        entity_type="product", 
        limit=10, 
        similarity_threshold=0.6
    )
    
    # Map search results to domain entities
    search_results = []
    for result in results:
        # Get product ID from entity_id
        product_id = UUID(result["entity_id"])
        
        # Get product from repository
        product = await product_repository.get_by_id(product_id)
        if product:
            search_results.append(
                ProductSearchResult(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    similarity=result["similarity"],
                )
            )
            
    return search_results
```

## Configuration Options

### Embedding Model Configuration

```python
from uno.ai.embeddings import embedding_registry

# Register a custom model configuration
embedding_registry.create_and_register(
    name="custom_model",
    model_type="sentence_transformer",
    model_name="paraphrase-MiniLM-L6-v2"
)

# Use a more sophisticated model
embedding_registry.create_and_register(
    name="multilingual",
    model_type="sentence_transformer",
    model_name="paraphrase-multilingual-mpnet-base-v2"
)

# Register OpenAI model with custom parameters
embedding_registry.create_and_register(
    name="ada_embedding",
    model_type="openai",
    model_name="text-embedding-ada-002",
    api_key="your-api-key-here"
)
```

### Vector Storage Configuration

```python
# Configure vector storage with custom parameters
storage = await create_vector_storage(
    storage_type="pgvector",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    table_name="custom_embeddings",
    dimensions=1536,  # For OpenAI embeddings
    schema="vector_data"
)

# Advanced initialization checks
try:
    await storage.initialize()
except RuntimeError as e:
    # Handle missing pgvector extension
    print(f"Vector storage initialization failed: {e}")
    print("Please ensure pgvector extension is installed in PostgreSQL")
```

## Best Practices

### Choosing the Right Embedding Model

1. **For local deployment**: Use `SentenceTransformerModel` with models like:
   - `all-MiniLM-L6-v2` (384 dimensions) - Fast, good quality
   - `all-mpnet-base-v2` (768 dimensions) - Better quality, slower
   - `paraphrase-multilingual-mpnet-base-v2` - For multilingual content

2. **For high-quality search**: Use `OpenAIEmbeddingModel` with:
   - `text-embedding-ada-002` (1536 dimensions) - Excellent quality
   - `text-embedding-3-small` (1536 dimensions) - Latest model, better quality
   - `text-embedding-3-large` (3072 dimensions) - Highest quality, more dimensions

3. **Consider your data**: Match the embedding model to your content:
   - Technical content may need domain-specific models
   - Content in multiple languages needs multilingual models
   - Short text benefits from models fine-tuned on similar data

### Optimizing Search Performance

1. **Text Preprocessing**:
   ```python
   def preprocess_text(text):
       """Preprocess text for better embedding quality."""
       # Remove excessive whitespace
       text = " ".join(text.split())
       # Truncate very long texts
       if len(text) > 8000:
           text = text[:8000]
       return text
       
   # Use in indexing
   await engine.index_document(
       document=preprocess_text(document),
       entity_id=entity_id,
       entity_type=entity_type
   )
   
   # Use in search
   results = await engine.search(
       query=preprocess_text(query_text)
   )
   ```

2. **Chunking Long Documents**:
   ```python
   def chunk_document(text, chunk_size=1000, overlap=100):
       """Split document into overlapping chunks."""
       chunks = []
       start = 0
       while start < len(text):
           end = min(start + chunk_size, len(text))
           if end != len(text):
               # Find the last space to avoid cutting words
               end = text.rfind(' ', start, end) + 1
           chunks.append(text[start:end])
           start = end - overlap
       return chunks
   
   # Index each chunk separately
   chunks = chunk_document(long_document)
   for i, chunk in enumerate(chunks):
       await engine.index_document(
           document=chunk,
           entity_id=f"{document_id}_chunk_{i}",
           entity_type="document_chunk",
           metadata={"document_id": document_id, "chunk_number": i}
       )
   ```

3. **Batch Processing**:
   ```python
   # Prepare batch of documents
   batch = []
   for doc in documents:
       batch.append({
           "text": preprocess_text(doc.content),
           "entity_id": str(doc.id),
           "entity_type": "document",
           "metadata": {"title": doc.title, "author": doc.author}
       })
       
       # Process in manageable batches
       if len(batch) >= 100:
           await engine.index_batch(batch)
           batch = []
           
   # Process remaining items
   if batch:
       await engine.index_batch(batch)
   ```

### Entity Integration

1. **Efficient Text Extraction**:
   ```python
   def extract_product_text(product):
       """Extract searchable text from product entity."""
       # Include all relevant searchable fields
       fields = [
           product.name,
           product.description,
           product.category,
           # Include tags as space-separated values
           " ".join(product.tags) if product.tags else "",
           # Include brand
           product.brand
       ]
       # Join with spaces and clean up
       return " ".join(field for field in fields if field)
   
   # Use in entity indexer
   indexer = EntityIndexer(
       engine=engine,
       entity_type="product",
       text_extractor=extract_product_text,
       # ...
   )
   ```

2. **Useful Metadata**:
   ```python
   def extract_product_metadata(product):
       """Extract metadata useful for filtering and display."""
       return {
           "name": product.name,
           "price": float(product.price),
           "category": product.category,
           "brand": product.brand,
           "in_stock": product.inventory > 0,
           "rating": float(product.rating) if product.rating else None,
           "created_at": product.created_at.isoformat(),
       }
   ```

3. **Selective Indexing**:
   ```python
   def should_index_product(product):
       """Determine if a product should be indexed."""
       # Don't index inactive products
       if not product.is_active:
           return False
       # Don't index products with no description
       if not product.description or len(product.description) < 10:
           return False
       return True
   
   # Use with event handler
   @event_bus.subscribe(ProductUpdatedEvent)
   async def handle_product_updated(event):
       product = event.entity
       if should_index_product(product):
           await indexer.index_entity(product)
       else:
           # Remove from index if it exists
           await indexer.delete_entity(str(product.id))
   ```

## Advanced Examples

### Hybrid Search (Keyword + Semantic)

```python
from uno.ai.semantic_search import SemanticSearchEngine
from sqlalchemy import text

async def hybrid_search(
    query: str,
    engine: SemanticSearchEngine,
    db_session,
    entity_type: str = "product",
    limit: int = 10
):
    """
    Perform hybrid search combining vector similarity and keyword matching.
    
    Args:
        query: Search query
        engine: Semantic search engine
        db_session: Database session
        entity_type: Entity type to search
        limit: Maximum results to return
        
    Returns:
        Combined search results
    """
    # 1. Perform semantic search
    semantic_results = await engine.search(
        query=query,
        entity_type=entity_type,
        limit=limit*2,  # Get more results for re-ranking
        similarity_threshold=0.6
    )
    
    semantic_scores = {r["entity_id"]: r["similarity"] for r in semantic_results}
    semantic_ids = list(semantic_scores.keys())
    
    if not semantic_ids:
        return []
    
    # 2. Perform keyword search on same entities
    keyword_sql = text(f"""
        SELECT 
            p.id as entity_id,
            ts_rank_cd(to_tsvector('english', p.name || ' ' || p.description), 
                       plainto_tsquery('english', :query)) as keyword_score
        FROM products p
        WHERE p.id = ANY(:ids)
        ORDER BY keyword_score DESC
        LIMIT :limit
    """)
    
    keyword_results = await db_session.execute(
        keyword_sql, 
        {"query": query, "ids": semantic_ids, "limit": limit*2}
    )
    
    keyword_scores = {str(r.entity_id): r.keyword_score for r in keyword_results}
    
    # 3. Combine and re-rank results
    combined_results = []
    for entity_id in set(semantic_scores.keys()) | set(keyword_scores.keys()):
        sem_score = semantic_scores.get(entity_id, 0)
        key_score = keyword_scores.get(entity_id, 0)
        
        # Combined score (weighted sum)
        combined_score = (sem_score * 0.7) + (key_score * 0.3)
        
        combined_results.append({
            "entity_id": entity_id,
            "semantic_score": sem_score,
            "keyword_score": key_score,
            "combined_score": combined_score
        })
    
    # Sort by combined score
    combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Return top results
    return combined_results[:limit]
```

### Content Recommendations

```python
from uno.ai.semantic_search import SemanticSearchEngine

async def recommend_similar_content(
    item_id: str,
    engine: SemanticSearchEngine,
    entity_type: str = "article",
    limit: int = 5
):
    """
    Recommend similar content based on an existing item.
    
    Args:
        item_id: ID of the reference item
        engine: Semantic search engine
        entity_type: Entity type
        limit: Maximum recommendations
        
    Returns:
        List of similar items
    """
    # 1. Get the item's text from database
    item = await item_repository.get_by_id(item_id)
    if not item:
        return []
    
    # 2. Extract text for embedding
    item_text = f"{item.title} {item.summary} {item.content}"
    
    # 3. Search for similar items
    results = await engine.search(
        query=item_text,
        entity_type=entity_type,
        limit=limit + 1,  # Get one extra to filter out the source item
        similarity_threshold=0.7
    )
    
    # 4. Filter out the source item
    recommendations = [
        result for result in results 
        if result["entity_id"] != item_id
    ][:limit]
    
    return recommendations
```

### User Personalized Search

```python
from uno.ai.semantic_search import SemanticSearchEngine
import numpy as np

async def personalized_search(
    query: str,
    user_id: str,
    engine: SemanticSearchEngine,
    user_embedding_model,
    entity_type: str = "product",
    limit: int = 10
):
    """
    Personalize search results based on user preferences.
    
    Args:
        query: Search query
        user_id: User ID for personalization
        engine: Semantic search engine
        user_embedding_model: Model for user embeddings
        entity_type: Entity type to search
        limit: Maximum results
        
    Returns:
        Personalized search results
    """
    # 1. Get the user's preference embedding
    user_profile = await user_repository.get_user_profile(user_id)
    if not user_profile:
        # Fall back to non-personalized search
        return await engine.search(query, entity_type, limit)
    
    # Generate user embedding from preferences/history
    user_preferences = " ".join([
        *user_profile.favorite_categories,
        *user_profile.recent_searches,
        *[item.name for item in user_profile.purchased_items[-10:]]
    ])
    
    user_embedding = user_embedding_model.embed(user_preferences)
    
    # 2. Get query embedding
    query_embedding = engine.embedding_model.embed(query)
    
    # 3. Create a blended query vector (70% query, 30% user preferences)
    blended_embedding = (0.7 * query_embedding) + (0.3 * user_embedding)
    
    # Normalize the vector
    blended_embedding = blended_embedding / np.linalg.norm(blended_embedding)
    
    # 4. Search with the blended vector
    results = await engine.vector_storage.search(
        query_embedding=blended_embedding,
        entity_type=entity_type,
        limit=limit,
        similarity_threshold=0.6
    )
    
    return results
```

## Conclusion

UNO's vector search capabilities provide a powerful foundation for building semantic search, recommendations, and other AI-powered features in your applications. By combining embedding models with efficient vector storage and integration with your domain model, you can create intelligent features that understand the meaning of content rather than just matching keywords.

For more information, see the related documentation:

- [pgvector Integration](pgvector.md): Detailed guide to PostgreSQL's vector extension
- [Hybrid Search](hybrid_search.md): Combining vector and keyword search
- [RAG Implementation](rag.md): Building Retrieval-Augmented Generation systems
- [PostgreSQL Features](../database/postgresql_features.md): Advanced PostgreSQL capabilities
- [Domain Entity Framework](../domain/entity_framework.md): Working with domain entities