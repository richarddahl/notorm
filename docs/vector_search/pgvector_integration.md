# PostgreSQL pgvector Integration

This document explains how the Uno Framework integrates with pgvector to provide powerful vector search capabilities.

## What is pgvector?

[pgvector](https://github.com/pgvector/pgvector) is a PostgreSQL extension that adds support for vector similarity search. It enables:

1. Storage of embedding vectors directly in PostgreSQL
2. Efficient vector similarity search using multiple distance metrics
3. Advanced indexing for fast search on large vector collections

## Integration with Uno Framework

Uno's pgvector integration provides:

1. **Automatic embedding generation** through database triggers
2. **Efficient indexing** with HNSW and IVF-Flat algorithms
3. **Hybrid search** combining graph database and vector similarity
4. **Role-based security** consistent with the rest of the framework
5. **Event-driven architecture** for real-time updates

## Database Setup

The integration adds several components to your PostgreSQL database:

### 1. SQL Functions

```sql
-- Generate embeddings from text
CREATE OR REPLACE FUNCTION uno.generate_embedding(
    text_content TEXT,
    dimensions INT DEFAULT 1536
) RETURNS vector ...

-- Calculate cosine similarity between vectors
CREATE OR REPLACE FUNCTION uno.cosine_similarity(
    a vector,
    b vector
) RETURNS float8 ...

-- Create embedding triggers on tables
CREATE OR REPLACE FUNCTION uno.create_embedding_trigger(
    table_name TEXT,
    vector_column_name TEXT DEFAULT 'embedding',
    content_columns TEXT[] DEFAULT '{"content"}',
    dimensions INT DEFAULT 1536
) RETURNS void ...
```

### 2. Vector Indexing Functions

```sql
-- Create HNSW index (faster search, higher memory usage)
CREATE OR REPLACE FUNCTION uno.create_hnsw_index(
    table_name TEXT,
    column_name TEXT DEFAULT 'embedding',
    m INT DEFAULT 16,          
    ef_construction INT DEFAULT 64
) RETURNS void ...

-- Create IVF-Flat index (balanced approach)
CREATE OR REPLACE FUNCTION uno.create_ivfflat_index(
    table_name TEXT,
    column_name TEXT DEFAULT 'embedding',
    lists INT DEFAULT 100
) RETURNS void ...
```

### 3. Search Functions

```sql
-- Perform vector similarity search
CREATE OR REPLACE FUNCTION uno.vector_search(
    table_name TEXT,
    query_embedding vector,
    column_name TEXT DEFAULT 'embedding',
    limit_val INT DEFAULT 10,
    threshold FLOAT DEFAULT 0.7,
    where_clause TEXT DEFAULT NULL
) RETURNS TABLE ...

-- Perform hybrid vector and graph search
CREATE OR REPLACE FUNCTION uno.hybrid_search(
    table_name TEXT,
    query_embedding vector,
    graph_traversal_query TEXT DEFAULT NULL,
    column_name TEXT DEFAULT 'embedding',
    limit_val INT DEFAULT 10,
    threshold FLOAT DEFAULT 0.7
) RETURNS TABLE ...
```

### 4. Standard Tables

```sql
-- Documents table for RAG
CREATE TABLE uno.documents (
    id TEXT PRIMARY KEY DEFAULT uno.gen_ulid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    embedding vector(1536)
);

-- Vector configuration table
CREATE TABLE uno.vector_config (
    entity_type TEXT PRIMARY KEY,
    dimensions INTEGER NOT NULL DEFAULT 1536,
    content_fields TEXT[] NOT NULL,
    index_type TEXT NOT NULL DEFAULT 'hnsw',
    index_options JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## Automatic Embedding Generation

The framework uses database triggers to automatically generate and update embeddings when content changes:

1. When a record is inserted or updated in a vectorized table, triggers fire
2. The content from specified fields is extracted and concatenated
3. The `generate_embedding` function creates a vector of the right dimensions
4. The vector is stored in the embedding column

Example:
```sql
-- Add embedding trigger to a table
SELECT uno.create_embedding_trigger(
    'my_table',
    'embedding',
    ARRAY['title', 'description', 'content'],
    1536
);
```

## Database Indexes

Two index types are supported:

### HNSW (Hierarchical Navigable Small World)

- **Pros**: Faster search, better recall at the same speed
- **Cons**: Slower indexing, higher memory usage
- **Best for**: Search-heavy workloads with infrequent updates

```sql
SELECT uno.create_hnsw_index('my_table', 'embedding');
```

### IVF-Flat (Inverted File with Flat Compression)

- **Pros**: More balanced approach, less memory usage
- **Cons**: Slightly slower search than HNSW
- **Best for**: Balanced workloads or memory-constrained environments

```sql
SELECT uno.create_ivfflat_index('my_table', 'embedding');
```

## Vector Search Operations

### Simple Vector Search

1. Convert query text to embedding
2. Find similar vectors based on distance metric
3. Return results with similarity scores

```sql
SELECT * FROM uno.vector_search(
    'my_table',
    uno.generate_embedding('How do I reset my password?'),
    'embedding',
    10,    -- limit
    0.7,   -- threshold
    'is_active = true'  -- optional WHERE clause
);
```

### Hybrid Graph-Vector Search

1. Perform graph traversal to find connected nodes
2. Perform vector similarity search
3. Combine results with weighted ranking

```sql
SELECT * FROM uno.hybrid_search(
    'documents',
    uno.generate_embedding('How do I use vector search?'),
    'SELECT id::TEXT, distance FROM graph.shortest_path(...)',
    'embedding',
    10,
    0.7
);
```

## Architecture

The pgvector integration follows these design principles:

1. **Database-Native**: Core vector operations happen in PostgreSQL
2. **Auto-Updating**: Embeddings update automatically via triggers
3. **Secure**: Follows role-based access control
4. **Hybrid**: Combines graph and vector search seamlessly
5. **Configurable**: Easily customize dimensions, indexes, and thresholds

## Configuration Options

Configure vector search in `.env_dev`:

```
# VECTOR SEARCH SETTINGS
VECTOR_DIMENSIONS=1536
VECTOR_INDEX_TYPE="hnsw"
VECTOR_BATCH_SIZE=10
VECTOR_UPDATE_INTERVAL=1.0
VECTOR_AUTO_START=True
```

## Performance Considerations

1. **Index Type**: HNSW is faster but uses more memory
2. **Dimensions**: Higher dimensions (1536) are more accurate but slower
3. **Batch Updates**: Use batch processing for bulk operations
4. **Hybrid Search**: Combining graph and vector search may be slower but more accurate