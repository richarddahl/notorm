# Queries API

This document provides an overview of the Queries API, which allows you to manage queries, query paths, and query values for filtering data in the knowledge graph.

## Overview

The Queries API provides endpoints for creating, managing, and executing queries:

- **Query Paths**: Define paths in the knowledge graph for querying relationships
- **Query Values**: Define filter values for query paths
- **Queries**: Combine query values and sub-queries to filter data

The API follows domain-driven design principles with consistent RESTful endpoints for each entity type.

## API Structure

### Query Paths

Query paths represent paths in the knowledge graph that can be used for filtering data. They define how to navigate from a source node to a target node.

#### Create Query Path

```http
POST /api/v1/query-paths
```

Request body:
```json
{
  "source_meta_type_id": "product",
  "target_meta_type_id": "category",
  "cypher_path": "()-[:HAS_CATEGORY]->()",
  "data_type": "string"
}
```

#### Get Query Path

```http
GET /api/v1/query-paths/{path_id}
```

#### List Query Paths

```http
GET /api/v1/query-paths
```

Optional query parameters:
- `source_meta_type_id`: Filter by source meta type
- `target_meta_type_id`: Filter by target meta type
- `data_type`: Filter by data type

#### Update Query Path

```http
PUT /api/v1/query-paths/{path_id}
```

Request body:
```json
{
  "cypher_path": "()-[:UPDATED_CATEGORY]->()",
  "data_type": "string"
}
```

#### Delete Query Path

```http
DELETE /api/v1/query-paths/{path_id}
```

### Query Values

Query values represent filter values for query paths, defining specific filtering criteria.

#### Create Query Value

```http
POST /api/v1/query-values
```

Request body:
```json
{
  "query_path_id": "path123",
  "include": "INCLUDE",
  "match": "AND",
  "lookup": "equal",
  "values": ["red", "blue", "green"]
}
```

#### Get Query Value

```http
GET /api/v1/query-values/{value_id}
```

#### List Query Values

```http
GET /api/v1/query-values
```

Optional query parameters:
- `query_path_id`: Filter by query path
- `include`: Filter by include/exclude (INCLUDE/EXCLUDE)
- `match`: Filter by match type (AND/OR)

#### Update Query Value

```http
PUT /api/v1/query-values/{value_id}
```

Request body:
```json
{
  "lookup": "contains",
  "values": ["yellow", "purple"]
}
```

#### Delete Query Value

```http
DELETE /api/v1/query-values/{value_id}
```

### Queries

Queries combine query values and sub-queries to filter data.

#### Create Query

```http
POST /api/v1/queries
```

Request body:
```json
{
  "name": "Red Products",
  "query_meta_type_id": "product",
  "description": "Query for red products",
  "include_values": "INCLUDE",
  "match_values": "AND",
  "include_queries": "INCLUDE",
  "match_queries": "AND",
  "query_values": [
    {
      "query_path_id": "path123",
      "include": "INCLUDE",
      "match": "AND", 
      "lookup": "equal",
      "values": ["red"]
    }
  ],
  "sub_queries": []
}
```

#### Get Query

```http
GET /api/v1/queries/{query_id}
```

#### List Queries

```http
GET /api/v1/queries
```

Optional query parameters:
- `name`: Filter by name
- `query_meta_type_id`: Filter by meta type

#### Update Query

```http
PUT /api/v1/queries/{query_id}
```

Request body:
```json
{
  "name": "Updated Red Products",
  "description": "Updated query for red products",
  "query_values": [
    {
      "query_path_id": "path123",
      "lookup": "contains",
      "values": ["dark red", "light red"]
    }
  ]
}
```

#### Delete Query

```http
DELETE /api/v1/queries/{query_id}
```

## Query Execution

To execute a query and filter data:

```http
POST /api/v1/queries/{query_id}/execute/{entity_type}
```

Request body:
```json
{
  "filters": {
    "price": {"lookup": "gt", "val": 100}
  },
  "options": {
    "limit": 20,
    "offset": 0,
    "order_by": ["name"]
  }
}
```

Response body:
```json
{
  "results": [
    {"id": "prod1", "name": "Red Chair", "price": 199.99},
    {"id": "prod2", "name": "Red Table", "price": 299.99}
  ],
  "count": 2
}
```

## Integration with FastAPI Applications

To integrate the Queries API into your FastAPI application:

```python
from fastapi import FastAPI
from uno.queries import (
    register_query_endpoints,
    QueryPathRepository,
    QueryValueRepository,
    QueryRepository,
)

# Create FastAPI app
app = FastAPI()

# Register query endpoints with default settings
endpoints = register_query_endpoints(
    app_or_router=app,
    path_prefix="/api/v1",
    dependencies=None,
    include_auth=True,
)

# Or with custom repositories
from uno.database.db_manager import DBManager

db_manager = DBManager()
query_path_repository = QueryPathRepository(db_manager)
query_value_repository = QueryValueRepository(db_manager)
query_repository = QueryRepository(db_manager)

endpoints = register_query_endpoints(
    app_or_router=app,
    path_prefix="/api/v1",
    dependencies=None,
    include_auth=True,
    query_path_repository=query_path_repository,
    query_value_repository=query_value_repository,
    query_repository=query_repository,
)
```

## Lookup Types

The following lookup types are supported for query values:

- `eq`: Equal
- `ne`: Not equal
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `in`: In a list of values
- `not_in`: Not in a list of values
- `contains`: Contains substring
- `not_contains`: Does not contain substring
- `starts_with`: Starts with
- `ends_with`: Ends with
- `is_null`: Is null
- `is_not_null`: Is not null

## Match Types

The following match types are supported for combining multiple values or queries:

- `AND`: All conditions must match
- `OR`: Any condition can match

## Include/Exclude Types

The following include/exclude types are supported:

- `INCLUDE`: Include records matching the conditions
- `EXCLUDE`: Exclude records matching the conditions