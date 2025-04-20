# pgvector Integration in UNO

This guide explains how to use PostgreSQL's pgvector extension with UNO for efficient vector similarity search and retrieval.

## Overview

pgvector is a PostgreSQL extension that adds support for vector similarity search. It enables storing embedding vectors and performing efficient nearest-neighbor searches using various distance metrics. UNO integrates seamlessly with pgvector to provide high-performance vector search capabilities.

Key features of pgvector in UNO:
- Store and query embedding vectors in PostgreSQL 
- Support for multiple similarity metrics (cosine, L2, inner product)
- Efficient indexing for large vector collections
- Batch operations for high throughput
- Automatic extension management

## Installation

### Docker Setup

The UNO Docker environment automatically installs pgvector. No additional setup is required.

### Manual Installation

If you're using a custom PostgreSQL installation, you'll need to install the pgvector extension:

#### Ubuntu/Debian

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y postgresql-server-dev-15 build-essential git

# Clone pgvector repository
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# Build and install
make
sudo make install

# Now connect to your database and run:
# CREATE EXTENSION vector;
```

#### macOS with Homebrew

```bash
# Install pgvector
brew install pgvector

# If using PostgreSQL from Homebrew, the extension should be available
```

#### Windows

For Windows, it's recommended to use the Docker environment or install PostgreSQL via WSL2.

### Verifying Installation

You can verify that pgvector is installed correctly:

```python
from uno.infrastructure.database.postgresql import PostgresExtensions
from uno.infrastructure.database import UnoDB

# Connect to database
db = UnoDB(connection_string="postgresql://user:pass@localhost:5432/mydb")

async def verify_pgvector():
    async with db.session() as session:
        # Create extensions manager
        extensions = PostgresExtensions(session)
        
        # Check for vector extension
        has_vector = await extensions.has_extension("vector")
        
        if has_vector:
            print("pgvector extension is installed")
        else:
            print("pgvector extension is not installed")
            # Try to create it
            try:
                await extensions.create_extension("vector")
                print("Successfully installed pgvector extension")
            except Exception as e:
                print(f"Failed to install pgvector: {e}")
```

## Basic Usage

### Initializing Vector Storage

```python
from uno.ai.vector_storage import create_vector_storage

# Create pgvector storage
storage = await create_vector_storage(
    storage_type="pgvector",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    table_name="vector_embeddings",
    dimensions=384,  # Dimensions must match your embedding model
    schema="public"
)

# Initialize storage (creates tables and indexes)
await storage.initialize()
```

The `initialize()` method:
1. Verifies pgvector extension is available
2. Creates the vector table if it doesn't exist
3. Creates appropriate indexes for fast similarity search
4. Prepares the storage for embedding operations

### Storing Vector Embeddings

```python
import numpy as np
from uno.ai.embeddings import get_embedding_model

# Get embedding model
model = get_embedding_model()

# Generate embedding for text
text = "Example document for semantic search"
embedding = model.embed(text)  # numpy array of shape (dimensions,)

# Store in pgvector
record_id = await storage.store(
    entity_id="doc123",         # Your application entity ID
    entity_type="document",     # Type of entity
    embedding=embedding,        # Numpy array
    metadata={                  # Optional metadata
        "title": "Example Document",
        "author": "John Doe",
        "tags": ["example", "documentation"]
    }
)
```

### Searching Vector Embeddings

```python
# Generate query embedding
query = "Find similar documents about search"
query_embedding = model.embed(query)

# Search for similar embeddings
results = await storage.search(
    query_embedding=query_embedding,
    entity_type="document",        # Optional filter by type 
    limit=10,                      # Maximum results to return
    similarity_threshold=0.7       # Minimum similarity score (0-1)
)

# Process results
for result in results:
    print(f"Entity: {result['entity_id']}")
    print(f"Type: {result['entity_type']}")
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Metadata: {result['metadata']}")
    print("---")
```

### Batch Operations

For better performance with many embeddings:

```python
# Prepare batch of items
batch_items = []
for i in range(100):
    text = f"Document {i} with content..."
    embedding = model.embed(text)
    
    batch_items.append({
        "entity_id": f"doc{i}",
        "entity_type": "document",
        "embedding": embedding,
        "metadata": {"title": f"Document {i}", "index": i}
    })

# Store batch of embeddings
record_ids = await storage.store_batch(batch_items)
```

### Deleting Embeddings

```python
# Delete a specific entity
await storage.delete(entity_id="doc123")

# Delete all entities of a specific type
await storage.delete(entity_id="doc123", entity_type="document")
```

## Vector Table Schema

When initializing vector storage, UNO creates a table with the following schema:

```sql
CREATE TABLE vector_embeddings (
    id SERIAL PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vector_embeddings_entity_id ON vector_embeddings(entity_id);
CREATE INDEX idx_vector_embeddings_entity_type ON vector_embeddings(entity_type);
CREATE INDEX idx_vector_embeddings_embedding ON vector_embeddings USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
```

Key components:
- `entity_id` and `entity_type`: Store application entity identifiers
- `embedding`: pgvector column storing the actual vector
- `metadata`: JSONB column for storing associated data
- Indexes to speed up lookups and similarity search

## Vector Indexing

pgvector supports multiple indexing methods for different performance characteristics:

### IVF (Inverted File)

The default index used by UNO is IVF (Inverted File):

```sql
CREATE INDEX idx_vector_embeddings_embedding 
ON vector_embeddings USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);
```

IVF indexes:
- Divide vectors into lists for approximate similarity search
- Offer good balance of search speed and accuracy
- Are best for most use cases

The `lists` parameter controls the number of partitions. A good rule of thumb is:
- For small tables (< 1M rows): `lists = sqrt(row_count)`
- For large tables: `lists = sqrt(row_count) / 2` 

### HNSW (Hierarchical Navigable Small World)

For even faster searches on newer versions of pgvector:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate HNSW index SQL
hnsw_index = emitter.create_index(
    name="hnsw_vector_embeddings_index",
    table_name="vector_embeddings",
    expression="embedding vector_cosine_ops",
    method="hnsw",
    parameters={"m": 16, "ef_construction": 64}
)

# Create the index
async with db.session() as session:
    await session.execute(hnsw_index)
```

HNSW indexes:
- Offer better search performance than IVF
- Require more memory and longer build times
- Are best for applications requiring fast responses

## Similarity Metrics

pgvector supports different similarity metrics:

### L2 Distance (Euclidean)

```python
# Search using L2 distance (lower is more similar)
await session.execute(f"""
    SELECT 
        entity_id, 
        entity_type, 
        embedding <-> $1::vector as distance
    FROM vector_embeddings
    ORDER BY distance ASC
    LIMIT 10
""", [embedding_str])
```

### Cosine Similarity

```python
# Search using cosine similarity (higher is more similar)
await session.execute(f"""
    SELECT 
        entity_id, 
        entity_type, 
        1 - (embedding <=> $1::vector) as similarity
    FROM vector_embeddings
    ORDER BY similarity DESC
    LIMIT 10
""", [embedding_str])
```

### Inner Product

```python
# Search using inner product (higher is more similar)
await session.execute(f"""
    SELECT 
        entity_id, 
        entity_type, 
        embedding <#> $1::vector as similarity
    FROM vector_embeddings
    ORDER BY similarity DESC
    LIMIT 10
""", [embedding_str])
```

UNO's vector storage uses cosine similarity by default (1 - cosine distance).

## Advanced Techniques

### Custom Vector Table Configuration

You can configure the vector table with custom settings:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate custom vector table
custom_table = f"""
CREATE TABLE IF NOT EXISTS custom_embeddings (
    id SERIAL PRIMARY KEY,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB,
    embedding_model VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_custom_embeddings_entity_id 
ON custom_embeddings(entity_id);

CREATE INDEX IF NOT EXISTS idx_custom_embeddings_entity_type 
ON custom_embeddings(entity_type);

CREATE INDEX IF NOT EXISTS idx_custom_embeddings_active 
ON custom_embeddings(is_active);

CREATE INDEX IF NOT EXISTS idx_custom_embeddings_embedding 
ON custom_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
"""

# Execute the SQL
async with db.session() as session:
    await session.execute(custom_table)
```

### Optimizing Index Performance

For large vector collections, you can tune indexing parameters:

```python
# Create an optimized IVF index
optimized_ivf = f"""
-- Drop existing index (if any)
DROP INDEX IF EXISTS idx_vector_embeddings_embedding;

-- Create optimized index with larger lists parameter for better performance
CREATE INDEX idx_vector_embeddings_embedding 
ON vector_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1000);
"""

async with db.session() as session:
    await session.execute(optimized_ivf)
```

### Hybrid Search Queries

Combine vector search with traditional SQL filters:

```python
from uno.ai.vector_storage import PGVectorStorage
import numpy as np

# Create storage
storage = PGVectorStorage(connection_string="...")
await storage.initialize()

# Generate query embedding
query_embedding = np.array([...])  # Your embedding vector
embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"

# Execute hybrid query
async with storage.pool.acquire() as conn:
    results = await conn.fetch(f"""
        SELECT 
            id, 
            entity_id, 
            entity_type, 
            metadata,
            1 - (embedding <=> $1::vector) as similarity
        FROM {storage.schema}.{storage.table_name}
        WHERE 
            -- Vector similarity filter
            1 - (embedding <=> $1::vector) >= $2
            -- Standard SQL filters
            AND entity_type = $3
            AND metadata->>'category' = $4
            AND (metadata->>'created_at')::timestamp > $5
        ORDER BY similarity DESC
        LIMIT $6
    """, 
    embedding_str, 
    0.7,  # similarity threshold
    "product",  # entity type filter
    "electronics",  # metadata category filter
    "2023-01-01",  # date filter
    10  # limit
    )
```

### Partitioning for Large Collections

For very large vector collections, consider table partitioning:

```python
# Create a partitioned vector table by entity_type
partitioned_table = """
CREATE TABLE vector_embeddings (
    id SERIAL PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY LIST (entity_type);

-- Create partitions for different entity types
CREATE TABLE vector_embeddings_products 
PARTITION OF vector_embeddings 
FOR VALUES IN ('product');

CREATE TABLE vector_embeddings_documents 
PARTITION OF vector_embeddings 
FOR VALUES IN ('document');

CREATE TABLE vector_embeddings_users 
PARTITION OF vector_embeddings 
FOR VALUES IN ('user');

-- Create table for all other types
CREATE TABLE vector_embeddings_other 
PARTITION OF vector_embeddings 
DEFAULT;

-- Create indexes on partitions
CREATE INDEX idx_vector_embeddings_products_embedding 
ON vector_embeddings_products 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_vector_embeddings_documents_embedding 
ON vector_embeddings_documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
"""

async with db.session() as session:
    await session.execute(partitioned_table)
```

## Performance Considerations

### Vector Dimensions

The number of dimensions impacts performance:
- Lower dimensions (128-384): Better performance, less memory
- Higher dimensions (768-1536): Better accuracy, more memory
- Very high dimensions (3072+): Best accuracy, but significantly higher resource usage

Choose dimensions based on your requirements:
- For faster performance: 128-384 dimensions
- For better accuracy: 768-1536 dimensions
- For highest accuracy: 1536+ dimensions

### Index Type Selection

Choose the right index type for your use case:
- **No index**: Best for tables with < 1,000 rows
- **IVF index**: Good balance of build time and search speed
- **HNSW index**: Fastest searches, but slow to build and update

### Memory Considerations

pgvector indexes can consume significant memory:
- Plan for at least 2-3x the size of your vector data in RAM
- For HNSW indexes, memory requirements are even higher
- Consider vertical scaling (more RAM) for large collections

### Batch Processing

Use batch operations when possible:
- Batch inserts are much faster than individual inserts
- For bulk loading, consider using PostgreSQL's COPY command
- Index after loading data for large datasets

## Integration with UNO Components

### Semantic Search Engine

The `SemanticSearchEngine` class provides a higher-level interface:

```python
from uno.ai.semantic_search import SemanticSearchEngine

# Create search engine
engine = SemanticSearchEngine(
    embedding_model="default",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    table_name="vector_embeddings",
    schema="public"
)

# Initialize the engine (this sets up pgvector)
await engine.initialize()

# Now you can use higher-level methods
await engine.index_document(
    document="Example document text",
    entity_id="doc123",
    entity_type="document",
    metadata={"title": "Example"}
)

# Search with text queries directly
results = await engine.search(
    query="Find similar documents",
    entity_type="document",
    limit=10
)
```

### Entity Repository Integration

Integrate vector search with domain repositories:

```python
from uno.domain.entity import EntityRepository
from uno.ai.semantic_search import SemanticSearchEngine
from typing import List, Optional

class ProductRepository(EntityRepository[Product, UUID]):
    """Repository for Product entities with semantic search capabilities."""
    
    def __init__(self, session, search_engine: SemanticSearchEngine):
        super().__init__(session)
        self.search_engine = search_engine
    
    async def find_similar_products(
        self, 
        query: str, 
        limit: int = 10
    ) -> list[Product]:
        """Find products similar to the query text."""
        # Search using the engine
        results = await self.search_engine.search(
            query=query,
            entity_type="product",
            limit=limit
        )
        
        # Get product IDs
        product_ids = [UUID(result["entity_id"]) for result in results]
        
        if not product_ids:
            return []
        
        # Fetch actual products
        products = []
        for product_id in product_ids:
            product = await self.get_by_id(product_id)
            if product:
                products.append(product)
        
        return products
    
    async def find_similar_to_product(
        self, 
        product_id: UUID,
        limit: int = 5
    ) -> list[Product]:
        """Find products similar to an existing product."""
        # Get the source product
        product = await self.get_by_id(product_id)
        if not product:
            return []
        
        # Generate text for search
        product_text = f"{product.name} {product.description} {product.category}"
        
        # Search for similar products, excluding the source
        results = await self.search_engine.search(
            query=product_text,
            entity_type="product",
            limit=limit + 1  # Get extra results to filter out source
        )
        
        # Filter out the source product
        filtered_results = [
            result for result in results 
            if result["entity_id"] != str(product_id)
        ][:limit]
        
        # Get product IDs
        product_ids = [UUID(result["entity_id"]) for result in filtered_results]
        
        if not product_ids:
            return []
        
        # Fetch actual products
        products = []
        for pid in product_ids:
            p = await self.get_by_id(pid)
            if p:
                products.append(p)
        
        return products
```

## Best Practices

### Handling Different Embedding Models

If you use multiple embedding models:

```python
# Create different tables for different model dimensions
openai_storage = await create_vector_storage(
    storage_type="pgvector",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    table_name="openai_embeddings",
    dimensions=1536,  # OpenAI embedding dimensions
    schema="vectors"
)

minilm_storage = await create_vector_storage(
    storage_type="pgvector",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    table_name="minilm_embeddings",
    dimensions=384,  # MiniLM embedding dimensions
    schema="vectors"
)

# Or store model information in metadata
await storage.store(
    entity_id="doc123",
    entity_type="document",
    embedding=embedding,
    metadata={
        "title": "Example Document",
        "embedding_model": "text-embedding-ada-002"
    }
)
```

### Upgrading pgvector

When upgrading pgvector:

1. Back up your vector data
2. Install the new version of pgvector
3. Recreate indexes with new algorithms/parameters
4. Verify queries still work correctly

```python
# Example of recreating indexes after upgrade
async with db.session() as session:
    # Drop old indexes
    await session.execute("""
        DROP INDEX IF EXISTS idx_vector_embeddings_embedding;
    """)
    
    # Create new index with upgraded parameters
    await session.execute("""
        CREATE INDEX idx_vector_embeddings_embedding 
        ON vector_embeddings 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
```

### Regular Maintenance

For optimal performance:

```python
async def maintain_vector_database():
    """Perform regular maintenance on vector database."""
    async with db.session() as session:
        # Vacuum the table to reclaim space and update statistics
        await session.execute(f"VACUUM ANALYZE {schema}.{table_name}")
        
        # Reindex to improve performance
        await session.execute(f"REINDEX INDEX idx_{table_name}_embedding")
```

### Monitoring

Monitor pgvector performance:

```python
async def check_vector_stats():
    """Check vector storage statistics."""
    async with db.session() as session:
        # Get table stats
        table_stats = await session.fetch(f"""
            SELECT 
                pg_size_pretty(pg_total_relation_size('{schema}.{table_name}')) as total_size,
                pg_size_pretty(pg_relation_size('{schema}.{table_name}')) as table_size,
                pg_size_pretty(pg_indexes_size('{schema}.{table_name}')) as index_size,
                (SELECT count(*) FROM {schema}.{table_name}) as row_count
        """)
        
        # Get index stats
        index_stats = await session.fetch(f"""
            SELECT
                indexname,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
            FROM pg_indexes
            WHERE tablename = '{table_name}' AND schemaname = '{schema}'
        """)
        
        return {
            "table_stats": dict(table_stats[0]),
            "index_stats": [dict(row) for row in index_stats]
        }
```

## Conclusion

pgvector provides a powerful foundation for vector search in UNO applications. By leveraging PostgreSQL's robust infrastructure with pgvector's specialized capabilities, you can implement efficient semantic search, recommendations, and other AI-powered features that understand the meaning of your content.

For more information on vector search capabilities, see:

- [Vector Search Overview](overview.md): General vector search concepts
- [Hybrid Search](hybrid_search.md): Combining vector and keyword search
- [RAG Implementation](rag.md): Building Retrieval-Augmented Generation systems
- [PostgreSQL Features](../database/postgresql_features.md): Other PostgreSQL capabilities