# Hybrid Search Queries

This guide explores hybrid search capabilities that combine graph traversal with vector similarity in uno.

## Overview

Hybrid search combines the strengths of both:

- **Graph Database**: Excellent for relationships and structured data traversal
- **Vector Search**: Powerful for semantic similarity and concept matching

This enables complex queries like:
- Find documents similar to "machine learning" that are connected to a specific topic
- Find products semantically similar to the user's query but only within a certain category
- Find experts whose descriptions match a topic and who are connected to a project

## How Hybrid Queries Work

A hybrid query in uno:

1. **Starts with a graph traversal** defined by a Cypher path pattern
2. **Filters the results** using vector similarity
3. **Returns ranked results** based on similarity

## Components Created for Hybrid Search

When using `VectorIntegrationEmitter`, it creates:

1. **Cypher Vector Search Function**: For calling vector search from Cypher queries
2. **Hybrid Search Function**: For combined graph+vector queries

## Hybrid Query Execution

Here's how a hybrid query executes:

1. The Cypher path pattern is executed to find matching node IDs
2. These IDs are intersected with the results of vector similarity search
3. Results are ranked by similarity score
4. Entities are loaded from the repository

## Example Hybrid Queries

### Finding Similar Documents in a Category

```python
hybrid_query = HybridQuery(```

query_text="machine learning algorithms comparison",
limit=10,
threshold=0.7,
start_node_type="Document",
start_filters={"category": "technical"},
path_pattern="(n:Document)-[:HAS_CATEGORY]->(:Category {name: 'AI'})"
```
)
```

This finds documents:
- That are in the "AI" category
- Starting from "technical" documents
- Ranked by similarity to "machine learning algorithms comparison"

### Multi-hop Graph Traversal with Similarity

```python
complex_query = HybridQuery(```

query_text="encryption best practices",
start_node_type="Document",
path_pattern="(n:Document)-[:AUTHORED_BY]->(:Author)-[:WORKS_AT]->(:Organization {name: 'Security Experts Inc.'})-[:PUBLISHED]->(end_node:Document)",
combine_method="weighted",
graph_weight=0.3,
vector_weight=0.7
```
)
```

This finds documents:
- Published by an organization named "Security Experts Inc."
- Where the author works at that organization
- Ranked by similarity to "encryption best practices"
- With weights applied to balance graph and vector relevance

## Implementation Details

### Cypher Integration

The system creates a special function to use vector search within Cypher:

```sql
SELECT * FROM cypher('graph', $$```

MATCH (doc:Document)
WHERE doc.id IN $${schema}.cypher_vector_search('encryption algorithms')$$
RETURN doc
```
$$) AS (result agtype);
```

### Weighted Combination

For the "weighted" combine method:

```python
final_score = (graph_weight * graph_score) + (vector_weight * similarity)
```

Where:
- graph_score is normalized based on path length/complexity
- similarity is the cosine similarity from vector search

### Performance Optimization

The hybrid search functions:
- Use temporary tables to efficiently process result sets
- Apply vector search only to the subset of documents that match the graph query
- Use efficient INNER JOIN operations for result combination

## Best Practices

1. **Narrow Graph Patterns First**: Start with a specific graph pattern to reduce the candidates for vector search

2. **Balance Thresholds**: Set similarity thresholds appropriately based on your embedding model

3. **Use Indices**: Ensure your graph has appropriate indices for the traversal patterns

4. **Monitor Performance**: Track execution time for hybrid queries, as they involve both graph and vector operations