# Apache AGE Graph Database Integration

The Uno framework integrates seamlessly with Apache AGE, a PostgreSQL extension that provides graph database functionality. This document explains how Uno leverages AGE for graph queries, knowledge representations, and complex relationship traversals.

## Overview

Apache AGE (A Graph Extension) is a PostgreSQL extension that adds graph database functionality to PostgreSQL. It allows you to use graph data models and Cypher query language alongside traditional relational database features. Uno integrates with AGE to provide:

1. **Automatic Synchronization**: Changes to relational tables are automatically synchronized with the graph representation
2. **Graph Queries**: Complex traversal and path finding operations using the Cypher query language
3. **Knowledge Graphs**: Building and querying knowledge graphs for AI features
4. **Optimized Performance**: Efficient graph algorithms for relationship traversal

## Architecture

The integration between Uno and Apache AGE follows this architecture:

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  Uno Application  │────▶│ Uno Graph Models  │────▶│ Graph SQL Emitter │
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └─────────┬─────────┘```
```

                                                      │
                                                      ▼
```
```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│   Graph Results   │◀────│   Graph Queries   │◀────│  PostgreSQL + AGE │
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

### Key Components

1. **GraphPathQuery**: Core component for executing graph path queries using Cypher
2. **GraphNavigator**: Advanced graph traversal with algorithms like BFS, Dijkstra, and A*
3. **KnowledgeConstructor**: Builds knowledge graphs from extracted entities and relationships
4. **GraphSQLEmitter**: Generates DDL/SQL for creating and synchronizing graph structures
5. **GraphPathQueryService**: Connects graph queries with entity repositories

## Setup and Configuration

### PostgreSQL Configuration

Apache AGE is automatically installed and configured when you set up the Uno Docker environment. The Docker setup scripts (`docker/scripts/init-db.sh`) handle the installation and configuration of AGE.

### Creating a Graph

Graphs in AGE are created automatically during initialization, but you can also create them manually:

```sql
-- Load AGE extension
LOAD 'age';

-- Create a graph
SELECT * FROM ag_catalog.create_graph('your_graph_name');
```

## Graph Models

Uno automatically maps your domain models to graph nodes and relationships based on your relational schema. The mapping is done through a combination of attributes and conventions.

### Entity Mapping

Entities in the domain model are mapped to nodes in the graph:

```python
from uno.model import UnoModel
from sqlalchemy import Column, Integer, String

class User(UnoModel):```

"""User entity that will be mapped to a graph node."""
``````

```
```

__tablename__ = "users"
``````

```
```

id = Column(Integer, primary_key=True)
name = Column(String)
email = Column(String)
```
```

### Relationship Mapping

Relationships between entities are mapped to edges in the graph:

```python
from uno.model import UnoModel
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Post(UnoModel):```

"""Post entity that will be mapped to a graph node."""
``````

```
```

__tablename__ = "posts"
``````

```
```

id = Column(Integer, primary_key=True)
title = Column(String)
content = Column(String)
user_id = Column(Integer, ForeignKey("users.id"))
``````

```
```

# This relationship will be mapped to a graph edge
user = relationship("User", back_populates="posts")
```
```

## Data Synchronization

Uno automatically synchronizes changes between relational tables and the graph database using PostgreSQL triggers. The synchronization is bidirectional, ensuring consistency between both representations.

### Synchronization Triggers

The system creates the following triggers for each entity:

1. **INSERT Trigger**: Creates a node in the graph when a record is inserted into a table
2. **UPDATE Trigger**: Updates the corresponding node when a record is updated
3. **DELETE Trigger**: Removes the node from the graph when a record is deleted

### Edge Creation

Edges are created based on foreign key relationships. When a relationship between two entities is established, a corresponding edge is created in the graph.

## Graph Queries

Uno provides several ways to query the graph database, from simple path queries to complex traversals.

### GraphPathQuery

The `GraphPathQuery` class allows you to execute Cypher path queries against the graph database:

```python
from uno.domain.graph_path_query import GraphPathQuery, PathQuerySpecification

# Create a graph path query executor
graph_query = GraphPathQuery(track_performance=True, use_cache=True)

# Define a path query specification
query_spec = PathQuerySpecification(```

path="(s:User)-[:CREATED]->(p:Post)",
params={"s.name": "John Doe"},
limit=10
```
)

# Execute the query
entity_ids, metadata = await graph_query.execute(query_spec)
```

### GraphNavigator

For more advanced graph traversal, use the `GraphNavigator` class:

```python
from uno.ai.graph_integration.graph_navigator import create_graph_navigator

# Create a graph navigator
navigator = await create_graph_navigator(```

connection_string="postgresql://user:pass@localhost:5432/dbname",
graph_name="knowledge_graph"
```
)

# Find the shortest path between two nodes
path = await navigator.find_shortest_path(```

start_node_id="user123",
end_node_id="post456",
relationship_types=["CREATED", "VIEWED", "COMMENTED_ON"],
max_depth=5
```
)

# Extract a subgraph centered on a node
subgraph = await navigator.extract_subgraph(```

center_node_id="user123",
max_depth=3,
relationship_types=["FOLLOWS", "FRIENDS_WITH"]
```
)

# Find similar nodes
similar_nodes = await navigator.find_similar_nodes(```

node_id="user123",
similarity_metric="jaccard",
top_k=10
```
)
```

### Query Path Integration

The `GraphPathQueryService` connects graph queries with entity repositories:

```python
from uno.domain.graph_path_query import GraphPathQuery, GraphPathQueryService, PathQuerySpecification

# Create a graph path query service
query_service = GraphPathQueryService(GraphPathQuery())

# Execute a path query and get entity objects
users, metadata = await query_service.query_entities(```

query=PathQuerySpecification(```

path="(s:User)-[:FOLLOWS]->(t:User)",
params={"s.id": "user123"}
```
),
repository=user_repository,
entity_type=User
```
)
```

## AI Integration

Uno's graph database integration includes components for AI-enhanced features.

### Knowledge Graph Construction

The `KnowledgeConstructor` class builds knowledge graphs from extracted entities and relationships:

```python
from uno.ai.graph_integration.knowledge_constructor import KnowledgeConstructor

# Create a knowledge constructor
knowledge_constructor = KnowledgeConstructor(```

connection_string="postgresql://user:pass@localhost:5432/dbname",
graph_name="knowledge_graph"
```
)

# Extract entities and relationships from text
extracted_data = await knowledge_constructor.extract_knowledge_from_text(```

text="John Doe is the CEO of Acme Corporation, which was founded in 1990."
```
)

# Build a knowledge graph
graph_data = await knowledge_constructor.construct_graph(```

entities=extracted_data["entities"],
relationships=extracted_data["relationships"]
```
)
```

### Retrieval-Augmented Generation (RAG)

The graph database can be used for context retrieval in RAG systems:

```python
from uno.ai.graph_integration.graph_navigator import create_graph_navigator

# Create a graph navigator
navigator = await create_graph_navigator(```

connection_string="postgresql://user:pass@localhost:5432/dbname",
graph_name="knowledge_graph"
```
)

# Find graph context for a query
context_items = await navigator.find_context_for_rag(```

query="What projects is John working on?",
relevant_nodes=["user123", "project456"],
max_results=5,
strategy="hybrid"
```
)
```

## Performance Optimization

The graph query system includes several performance optimizations:

### Query Caching

Path queries are cached based on their parameters:

```python
# Create a graph path query with caching
graph_query = GraphPathQuery(use_cache=True, cache_ttl=300)
```

### Performance Tracking

Query performance is tracked to identify optimization opportunities:

```python
# Create a graph path query with performance tracking
graph_query = GraphPathQuery(track_performance=True)

# Execute a query
entity_ids, metadata = await graph_query.execute(query_spec)

# Access performance metrics
execution_time = metadata.execution_time
```

### Optimized Algorithms

The `GraphNavigator` implements optimized algorithms for graph traversal:

1. **Breadth-First Search**: For finding the shortest path by number of hops
2. **Dijkstra's Algorithm**: For finding the shortest path by edge weight
3. **A* Algorithm**: For finding paths using heuristics
4. **Bidirectional Search**: For faster path finding between two nodes

## Advanced Features

### Community Detection

Identify communities or clusters within the graph:

```python
communities = await navigator.detect_communities(```

algorithm="louvain",
min_community_size=3,
max_communities=10
```
)
```

### Similarity Search

Find nodes similar to a given node:

```python
similar_nodes = await navigator.find_similar_nodes(```

node_id="user123",
similarity_metric="common_neighbors",
top_k=10
```
)
```

### Path Reasoning

Find paths with reasoning capabilities:

```python
path = await navigator.find_path_with_reasoning(```

start_node_id="concept1",
end_node_id="concept2",
reasoning_type="causal",
max_depth=5
```
)

# Access the reasoning explanation
explanation = path.metadata["explanation"]
```

## Integration with Query System

The graph path query system integrates with Uno's query system:

```python
from uno.queries.filter import UnoFilter
from uno.queries.objs import QueryPath

# Create a query path
path = QueryPath("User").via("CREATED").to("Post")

# Create a graph path query specification from a query path
query_spec = PathQuerySpecification(path=path)

# Execute the query
entity_ids, metadata = await graph_query.execute(query_spec)
```

## Cypher Query Examples

Uno uses the Cypher query language for graph operations. Here are some common query patterns:

### Finding Connected Nodes

```cypher
MATCH (user:User)-[:CREATED]->(post:Post)
WHERE user.name = 'John Doe'
RETURN post
```

### Finding Paths

```cypher
MATCH path = shortestPath((userA:User)-[*..5]-(userB:User))
WHERE userA.id = 'user123' AND userB.id = 'user456'
RETURN path
```

### Graph Algorithms

```cypher
MATCH (user:User)
CALL algo.pageRank.stream('User', 'FOLLOWS', {iterations:20, dampingFactor:0.85})
YIELD nodeId, score
RETURN user.name AS name, score
ORDER BY score DESC
LIMIT 10
```

## Best Practices

1. **Use Indexes**: Create indexes on frequently queried node properties
2. **Optimize Path Expressions**: Keep path expressions as specific as possible
3. **Use Parameterized Queries**: Always use parameterized queries to prevent injection
4. **Cache Results**: Cache frequently executed queries
5. **Monitor Performance**: Track query performance and optimize slow queries
6. **Use the Right Algorithm**: Choose the appropriate algorithm for each traversal task
7. **Limit Results**: Always limit the number of results to prevent performance issues
8. **Use Traversal Modes**: Use different traversal modes for different query patterns
9. **Batch Operations**: Batch operations for better performance
10. **Keep Graph in Sync**: Ensure the graph is kept in sync with the relational database

## Common Operations

### Creating a Node

```cypher
CREATE (user:User {id: 'user123', name: 'John Doe', email: 'john@example.com'})
RETURN user
```

### Creating a Relationship

```cypher
MATCH (userA:User), (userB:User)
WHERE userA.id = 'user123' AND userB.id = 'user456'
CREATE (userA)-[:FOLLOWS]->(userB)
```

### Finding Relationships

```cypher
MATCH (user:User)-[r:CREATED]->(post:Post)
WHERE user.id = 'user123'
RETURN type(r), count(r)
```

### Deleting Nodes and Relationships

```cypher
MATCH (user:User {id: 'user123'})
DETACH DELETE user
```

## Troubleshooting

### Common Issues

1. **Missing AGE Extension**: Make sure the AGE extension is properly installed
2. **Graph Synchronization Issues**: Check that triggers are properly created
3. **Performance Problems**: Optimize queries and use appropriate algorithms
4. **Memory Issues**: Limit result sets and use pagination

### Diagnostic Queries

```sql
-- Check AGE installation
SELECT * FROM pg_extension WHERE extname = 'age';

-- List available graphs
SELECT * FROM ag_catalog.ag_graph;

-- Check graph statistics
SELECT * FROM ag_catalog.ag_graph_statistics('your_graph_name');
```

## Conclusion

The Apache AGE integration in Uno provides powerful graph database capabilities that complement the relational database foundation. By leveraging the strengths of both paradigms, Uno offers a flexible and efficient solution for complex data modeling and querying needs.

## Related Topics

- [Domain-Driven Design](domain_driven_design.md)
- [Query System](/docs/queries/overview.md)
<!-- TODO: Create AI documentation -->
<!-- - [AI Integration](/docs/ai/overview.md) -->
<!-- TODO: Create performance documentation -->
<!-- - [Performance Optimization](/docs/performance/overview.md) -->