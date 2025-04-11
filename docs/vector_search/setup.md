# Setting Up Vector Search

This guide explains how to set up and configure vector search for your tables in Uno.

## Prerequisites

1. PostgreSQL 12+ with pgvector extension installed
2. Uno framework configured with PostgreSQL access

## Installation

### 1. Install pgvector Extension

First, install the pgvector extension on your PostgreSQL server:

```bash
# On the PostgreSQL server
sudo apt-get install postgresql-server-dev-12  # Adjust version as needed
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

### 2. Create Extension in Database

The vector SQL emitters will create the extension automatically, but you can also do it manually:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Setting Up a Table for Vector Search

To enable vector search for a table, use the `VectorSQLEmitter`:

```python
from sqlalchemy import Table
from uno.sql.emitters.vector import VectorSQLEmitter, VectorConfig

# Create vector config
vector_config = VectorConfig(
    dimensions=1536,  # OpenAI embedding dimensions
    index_type="hnsw",  # "hnsw", "ivfflat", or "none"
    m=16,             # HNSW m parameter
    ef_construction=64,  # HNSW ef_construction parameter
    ef_search=40      # HNSW search parameter
)

# Create vector SQL emitter
vector_emitter = VectorSQLEmitter(
    table=your_table,
    vector_columns=["title", "content"],  # Columns to vectorize
    exclude_columns=["id"],  # Columns to exclude
    vector_config=vector_config
)

# Generate and execute SQL
db_manager.execute_from_emitter(vector_emitter)
```

This will:

1. Add a vector column to your table
2. Create a vector index for efficient similarity search
3. Create a trigger function to automatically generate embeddings

## Index Types

The system supports multiple index types:

### HNSW Index

Hierarchical Navigable Small World (HNSW) indexes are generally faster for search but slower to build:

```python
vector_config = VectorConfig(
    dimensions=1536,
    index_type="hnsw",
    m=16,             # Controls index quality/size
    ef_construction=64,  # Controls build time/quality
    ef_search=40      # Controls search time/quality
)
```

### IVF-Flat Index

IVF-Flat indexes are faster to build but can be slower for search:

```python
vector_config = VectorConfig(
    dimensions=1536,
    index_type="ivfflat",
    lists=100,        # Number of clusters
    probes=10         # Number of clusters to search
)
```

### No Index

For small tables or testing, you can disable indexing:

```python
vector_config = VectorConfig(
    dimensions=1536,
    index_type="none"
)
```

## Integrating with Graph Database

To enable hybrid searches that combine graph traversal with vector similarity, use `VectorIntegrationEmitter`:

```python
integration_emitter = VectorIntegrationEmitter(
    table=your_table,
    vector_config=vector_config
)

db_manager.execute_from_emitter(integration_emitter)
```

This creates functions for searching within graph query results by vector similarity.