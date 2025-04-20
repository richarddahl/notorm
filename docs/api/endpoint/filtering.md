# Filtering with the Unified Endpoint Framework

The Unified Endpoint Framework provides a powerful filtering mechanism that integrates seamlessly with the domain entity framework. This guide explains how to use the filtering capabilities, including support for Apache AGE knowledge graph.

## Introduction to Filtering

Filtering allows clients to retrieve subsets of data based on specific criteria, such as field values, ranges, and patterns. The filtering mechanism supports:

- **Field-based filtering**: Filter by field values using various operators
- **Sorting**: Sort results by multiple fields
- **Pagination**: Limit and offset results for paginated display
- **Query parameters**: Use HTTP query parameters or JSON bodies for filtering
- **Apache AGE integration**: Optionally use Apache AGE knowledge graph for powerful relationship-based filtering

## Filtering Components

The filtering mechanism consists of the following components:

### 1. Filter Protocol

The `FilterProtocol` defines the interface for filtering operations:

```python
class FilterProtocol(Protocol, Generic[T, IdType]):
    """Protocol for filtering operations."""
    
    async def filter_entities(
        self,
        entity_type: str,
        filter_criteria: Union[dict[str, Any], list[QueryParameter]],
        *,
        sort_by: list[str] | None = None,
        sort_dir: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_count: bool = True,
    ) -> tuple[list[IdType], Optional[int]]:
        """Filter entities based on criteria and return IDs."""
        ...
```

### 2. Filter Backends

The framework provides multiple filter backends:

- **SqlFilterBackend**: Uses SQL queries for filtering
- **GraphFilterBackend**: Uses Apache AGE knowledge graph for filtering

```python
# SQL backend
sql_backend = SqlFilterBackend(session_factory)

# Graph backend with SQL fallback
graph_backend = GraphFilterBackend(
    session_factory, 
    fallback_backend=sql_backend
)
```

### 3. Filterable Endpoint Classes

The framework provides endpoint classes with filtering capabilities:

- **FilterableEndpoint**: Base class for filterable endpoints
- **FilterableCrudEndpoint**: CRUD endpoints with filtering
- **FilterableCqrsEndpoint**: CQRS endpoints with filtering

```python
# Create a filterable CRUD endpoint
endpoint = FilterableCrudEndpoint(
    service=product_service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    filter_backend=filter_backend,
    entity_type="Product",
    tags=["Products"],
    path="/api/products",
)
```

### 4. Filter Models

The filtering mechanism uses the following models:

- **FilterOperator**: Enum of supported operators
- **SortDirection**: Enum of sort directions (ascending, descending)
- **FilterField**: Field to filter on (name, operator, value)
- **SortField**: Field to sort by (name, direction)
- **FilterCondition**: Condition for filtering (field or group)
- **FilterCriteria**: Complete filter criteria (conditions, sort, limit, offset)
- **FilterRequest**: Request for filtering (criteria, include_count)
- **FilterResponse**: Response to a filter request (data, metadata)

## Using Filtering with HTTP Query Parameters

You can use HTTP query parameters to filter entities:

```
GET /api/products?filter.name:contains=laptop&filter.price:gte=1000&sort=price:desc&limit=10&offset=0
```

This will:
1. Filter products where name contains "laptop" and price is greater than or equal to 1000
2. Sort by price in descending order
3. Return up to 10 products, starting from the first one

## Using Filtering with JSON Requests

You can also use JSON to define complex filtering criteria:

```json
POST /api/products/filter
{
  "criteria": {
    "conditions": [
      {
        "type": "field",
        "field": {
          "name": "name",
          "operator": "contains",
          "value": "laptop"
        }
      },
      {
        "type": "field",
        "field": {
          "name": "price",
          "operator": "gte",
          "value": 1000
        }
      }
    ],
    "sort": [
      {
        "name": "price",
        "direction": "desc"
      }
    ],
    "limit": 10,
    "offset": 0
  },
  "include_count": true
}
```

## Supported Filter Operators

The filtering mechanism supports the following operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal | `filter.field:eq=value` |
| `ne` | Not equal | `filter.field:ne=value` |
| `gt` | Greater than | `filter.field:gt=value` |
| `gte` | Greater than or equal | `filter.field:gte=value` |
| `lt` | Less than | `filter.field:lt=value` |
| `lte` | Less than or equal | `filter.field:lte=value` |
| `in` | In a list | `filter.field:in=value1,value2` |
| `not_in` | Not in a list | `filter.field:not_in=value1,value2` |
| `contains` | Contains substring | `filter.field:contains=value` |
| `starts_with` | Starts with substring | `filter.field:starts_with=value` |
| `ends_with` | Ends with substring | `filter.field:ends_with=value` |
| `is_null` | Is null | `filter.field:is_null` |
| `is_not_null` | Is not null | `filter.field:is_not_null` |
| `between` | Between two values | `filter.field:between=min,max` |

## Apache AGE Integration

The filtering mechanism can optionally use Apache AGE knowledge graph for powerful relationship-based filtering.

### What is Apache AGE?

Apache AGE (A Graph Extension) is a PostgreSQL extension that provides graph database functionality. It allows you to store and query graph data within PostgreSQL using the Cypher query language.

### Benefits of Apache AGE for Filtering

Using Apache AGE for filtering provides several benefits:

1. **Relationship-based filtering**: Filter based on relationships between entities
2. **Path queries**: Find entities based on path expressions
3. **Graph algorithms**: Use graph algorithms for filtering
4. **Integration with SQL**: Combine graph and relational queries

### Configuring Apache AGE for Filtering

To use Apache AGE for filtering:

1. Ensure Apache AGE is installed in your PostgreSQL database
2. Create a `GraphFilterBackend` with a session factory
3. Optionally provide a fallback backend for when AGE is not available
4. Use the `GraphFilterBackend` with your endpoints

```python
# Create a session factory for database connections
session_factory = create_session_factory()

# Create a SQL filter backend as fallback
sql_backend = SqlFilterBackend(session_factory)

# Create a graph filter backend that uses Apache AGE
graph_backend = GraphFilterBackend(
    session_factory, 
    fallback_backend=sql_backend
)

# Create a filterable CRUD endpoint that uses the graph backend
endpoint = FilterableCrudEndpoint(
    service=product_service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    filter_backend=graph_backend,
    entity_type="Product",
    tags=["Products"],
    path="/api/products",
)
```

### Advanced Graph Filtering Examples

Using Apache AGE, you can perform advanced filtering operations:

1. **Filter by relationship**

```json
{
  "criteria": {
    "conditions": [
      {
        "type": "field",
        "field": {
          "name": "related_to",
          "operator": "relationship",
          "value": {
            "target": "Category",
            "conditions": [
              {
                "type": "field",
                "field": {
                  "name": "name",
                  "operator": "eq",
                  "value": "Electronics"
                }
              }
            ]
          }
        }
      }
    ]
  }
}
```

2. **Filter by path**

```json
{
  "criteria": {
    "conditions": [
      {
        "type": "field",
        "field": {
          "name": "path",
          "operator": "exists",
          "value": {
            "start": "Product",
            "end": "User",
            "path": "PURCHASED_BY",
            "length": {
              "min": 1,
              "max": 3
            }
          }
        }
      }
    ]
  }
}
```

## Implementing Custom Filter Backends

You can implement custom filter backends by extending the `FilterBackend` abstract base class:

```python
class CustomFilterBackend(FilterBackend):
    """Custom filter backend."""
    
    async def filter_entities(
        self,
        entity_type: str,
        filter_criteria: Union[dict[str, Any], list[QueryParameter]],
        *,
        sort_by: list[str] | None = None,
        sort_dir: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_count: bool = True,
    ) -> tuple[list[str], Optional[int]]:
        """Filter entities based on criteria."""
        # Custom implementation...
    
    async def count_entities(
        self,
        entity_type: str,
        filter_criteria: Union[dict[str, Any], list[QueryParameter]],
    ) -> int:
        """Count entities based on criteria."""
        # Custom implementation...
```

## Best Practices

### 1. Use the Right Backend for Your Needs

- Use `SqlFilterBackend` for simple filtering needs
- Use `GraphFilterBackend` for relationship-based filtering
- Provide a fallback backend for when Apache AGE is not available

### 2. Optimize Performance

- Use pagination (limit and offset) to limit result size
- Use selective fields to reduce data transfer
- Index fields used for filtering
- Create graph indexes for commonly used paths

### 3. Handle Validation

- Validate filter parameters to prevent injection
- Limit operator usage based on field types
- Set reasonable limits for pagination

### 4. Document Your API

- Document available filter operators
- Provide examples for common filtering patterns
- Explain the performance implications of different filter operations

## Conclusion

The filtering mechanism in the Unified Endpoint Framework provides a powerful and flexible way to filter entities, with optional support for Apache AGE knowledge graph. By using the filterable endpoint classes and filter backends, you can easily implement advanced filtering capabilities in your API.

## Next Steps

- [Apache AGE Integration Guide](apache_age_integration.md)
- [Advanced Filtering Examples](advanced_filtering.md)
- [Performance Optimization for Filtering](filtering_performance.md)