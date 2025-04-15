# Vector Search Triggers

This document explains the PostgreSQL trigger system that powers the vector search functionality in uno.

## Overview

The vector search system uses PostgreSQL triggers to automatically:

1. **Generate embeddings** for new records
2. **Update embeddings** when relevant fields change
3. **Maintain vector indices** for efficient search

This approach ensures data consistency and minimizes application code complexity.

## How Triggers Work

When you set up vector search for a table using `VectorSQLEmitter`, it creates:

1. **Vector Column**: Adds an `embedding` column to your table with the `vector` data type
2. **Embedding Function**: Creates a function to generate embeddings from text
3. **Trigger Functions**: Creates functions that run on insert/update
4. **Triggers**: Attaches those functions to your table events

### Embedding Generation

The system creates a PostgreSQL function to generate embeddings:

```sql
CREATE OR REPLACE FUNCTION schema.generate_embedding(```

text_input TEXT
```
) RETURNS vector(dimensions) AS $$```

-- Function body that generates an embedding
```
$$ LANGUAGE plpgsql;
```

In the default implementation:
- The function creates a deterministic embedding based on the text
- In production, you would modify this to call an external embedding API

### Insert Trigger

When a new record is inserted:

1. The trigger function concatenates the text from the specified columns
2. It calls the embedding function to generate a vector
3. It stores the vector in the `embedding` column

### Update Trigger

When a record is updated:

1. The trigger checks if any vectorized columns changed
2. If so, it regenerates the embedding
3. It updates the `embedding` column with the new vector

## Customizing Embedding Generation

For production use, you'll likely want to customize the embedding generation function to use a real embedding API. Here's an example of modifying the function:

```sql
CREATE OR REPLACE FUNCTION schema.generate_embedding(```

text_input TEXT
```
) RETURNS vector(1536) AS $$
DECLARE```

result vector(1536);
response JSONB;
```
BEGIN```

-- Call external API (example using PostgreSQL's http extension)
SELECT content::jsonb INTO response
FROM http_post(```

'https://api.openai.com/v1/embeddings',
jsonb_build_object(
    'input', text_input,
    'model', 'text-embedding-3-small'
)::text,
'application/json',
ARRAY[
    'Authorization: Bearer ' || current_setting('app.openai_key', true)
]
```
);
``````

```
```

-- Parse response to get embedding
result := array_to_vector(```

(response->'data'->0->'embedding')::text::float[]
```
);
``````

```
```

RETURN result;
```
END;
$$ LANGUAGE plpgsql;
```

## Vector Index Management

The system also creates appropriate indices based on your configuration:

### HNSW Index

```sql
CREATE INDEX table_embedding_idx 
ON schema.table 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

### IVF-Flat Index

```sql
CREATE INDEX table_embedding_idx 
ON schema.table 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

## Performance Considerations

- **Trigger Overhead**: Embedding generation adds overhead to insert/update operations
- **Index Build Time**: Vector indices can take time to build for large tables
- **Memory Usage**: Vector indices consume more memory than standard indices

For large tables, consider:
1. Disable triggers during bulk operations
2. Create indices after bulk loads
3. Use selective columnar vector indexing