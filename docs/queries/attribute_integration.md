# Attribute-Query Integration

This document outlines the integration between the Attributes module, Values module, and the Graph Database Query system. It describes how to effectively query objects based on their attributes using graph database capabilities.

## Overview

The Uno framework leverages the graph database to provide powerful querying capabilities for attributes. This allows complex queries that would be difficult or inefficient to express in pure SQL.

## Graph Structure

Attributes and values are represented in the graph database with the following structure:

```
(Object)-[:HAS_ATTRIBUTE]->(Attribute)-[:ATTRIBUTE_TYPE]->(AttributeType)
(Attribute)-[:HAS_VALUE]->(Value)
```

This structure enables efficient traversal and querying based on attribute types and values.

## Query Patterns

### Find Objects with Specific Attribute Type

```cypher
MATCH (o:Object)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType)
WHERE at.name = 'Priority'
RETURN o
```

### Find Objects with Specific Attribute Value

```cypher
MATCH (o:Object)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(v:Value)
WHERE v.value = 'High'
RETURN o
```

### Find Objects with Specific Attribute Type and Value

```cypher
MATCH (o:Object)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType),
      (a)-[:HAS_VALUE]->(v:Value)
WHERE at.name = 'Priority' AND v.value = 'High'
RETURN o
```

### Complex Attribute-Based Queries

Find objects with multiple specific attributes:

```cypher
MATCH (o:Object)
WHERE 
  EXISTS {
    MATCH (o)-[:HAS_ATTRIBUTE]->(a1:Attribute)-[:ATTRIBUTE_TYPE]->(at1:AttributeType),
          (a1)-[:HAS_VALUE]->(v1:Value)
    WHERE at1.name = 'Priority' AND v1.value = 'High'
  }
  AND
  EXISTS {
    MATCH (o)-[:HAS_ATTRIBUTE]->(a2:Attribute)-[:ATTRIBUTE_TYPE]->(at2:AttributeType),
          (a2)-[:HAS_VALUE]->(v2:Value)
    WHERE at2.name = 'Status' AND v2.value = 'Active'
  }
RETURN o
```

## Implementation

### Query Path Registration

We'll register attribute-specific query paths to enable easy and efficient querying:

```python
# Register attribute query paths
attribute_path = QueryPath(
    source_meta_type_id="task",
    target_meta_type_id="priority",
    cypher_path="(s:Task)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType {name: 'Priority'})-[:HAS_VALUE]->(t:Value)",
    data_type="str"
)
await attribute_path.save()
```

### QueryModel Integration

Create queryable attribute paths for common attribute types:

```python
# Create a query for high priority tasks
priority_query = Query(
    name="High Priority Tasks",
    description="Tasks with high priority",
    query_meta_type_id="task",
    include_values=Include.INCLUDE,
    match_values=Match.AND
)

# Create query values
priority_value = QueryValue(
    query_path_id=attribute_path.id,
    include=Include.INCLUDE,
    match=Match.AND,
    lookup="equal"
)
priority_value.values = [high_priority_value]

# Associate query value with query
priority_query.query_values = [priority_value]
await priority_query.save()
```

### Custom Query Functions

Implement specialized functions for attribute-based queries:

```python
async def find_objects_by_attribute(
    object_type: str,
    attribute_type: str,
    value: Any
) -> List[str]:
    """
    Find objects with a specific attribute type and value.
    
    Args:
        object_type: The type of object to search
        attribute_type: The attribute type name
        value: The attribute value
        
    Returns:
        List of object IDs matching the criteria
    """
    cypher_query = f"""
    MATCH (o:{object_type})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType),
          (a)-[:HAS_VALUE]->(v:Value)
    WHERE at.name = $attribute_type AND v.value = $value
    RETURN o.id
    """
    
    async with enhanced_async_session() as session:
        result = await session.execute(
            text(cypher_query),
            {"attribute_type": attribute_type, "value": str(value)}
        )
        return [row[0] for row in result.fetchall()]
```

## Query Optimization

### Path Indexing

Create graph database indexes for commonly queried paths:

```sql
CREATE INDEX idx_attribute_type_name ON :`AttributeType`(name);
CREATE INDEX idx_value_value ON :`Value`(value);
```

### Query Caching

Implement caching for frequent attribute-based queries:

```python
@cached(ttl=300)  # Cache for 5 minutes
async def get_objects_with_attribute(attribute_type: str, value: Any) -> List[str]:
    # Implementation
    ...
```

### Result Windowing

For large result sets, implement windowing:

```python
async def find_objects_by_attribute_paged(
    object_type: str,
    attribute_type: str,
    value: Any,
    limit: int = 100,
    offset: int = 0
) -> List[str]:
    # Implementation with LIMIT and OFFSET
    ...
```

## Integration with UI Components

The UI for attribute-based queries should provide:

1. **Attribute Type Selection**: A dropdown or search field to select attribute types
2. **Value Selection**: Type-appropriate input for the selected attribute type
3. **Multiple Attribute Criteria**: UI for adding multiple attribute conditions
4. **Boolean Logic**: Controls for AND/OR logic between conditions
5. **Results Preview**: Live preview of matching results count

### UI Component Architecture

The UI components will follow this architecture:

```
AttributeQueryBuilder
  ├── AttributeTypeSelector
  ├── QueryConditionList
  │     ├── AttributeCondition
  │     │     ├── AttributeTypeInput
  │     │     └── AttributeValueInput (dynamically selected based on type)
  │     └── LogicOperatorSelector (AND/OR)
  ├── ResultsPreview
  └── SaveQueryButton
```

### Value Type-Specific Inputs

Each value type will have an appropriate input component:

- **BooleanValue**: Toggle or radio buttons
- **TextValue**: Text input with optional operations (contains, starts with, etc.)
- **IntegerValue/DecimalValue**: Numeric input with optional range
- **DateValue/DateTimeValue**: Date picker
- **TimeValue**: Time picker

## Examples

### Example 1: Find Tasks by Priority and Status

```python
# Find high priority active tasks
results = await find_objects_with_attributes(
    object_type="Task",
    conditions=[
        {"attribute_type": "Priority", "value": "High"},
        {"attribute_type": "Status", "value": "Active"}
    ],
    logic="AND"
)
```

### Example 2: Find Tasks with Due Date Range

```python
# Find tasks due next week
next_week_start = datetime.date.today() + datetime.timedelta(days=7)
next_week_end = next_week_start + datetime.timedelta(days=7)

results = await find_objects_by_attribute_range(
    object_type="Task",
    attribute_type="DueDate",
    min_value=next_week_start,
    max_value=next_week_end
)
```

## Conclusion

The integration between attributes, values, and the graph database query system provides a powerful mechanism for complex object queries. By leveraging graph database capabilities, we can efficiently query objects based on their attributes in ways that would be difficult with traditional SQL queries.

The approach outlined in this document focuses on performance, flexibility, and developer experience, making it easy to create and execute attribute-based queries while maintaining good performance characteristics.