# Using QueryModel with Workflow Conditions

## Overview

The uno framework provides powerful integration between the QueryModel system and the Workflow module, enabling complex conditional logic in workflows through graph-based queries.

This integration allows workflow administrators to define sophisticated targeting rules by leveraging saved queries as workflow conditions. When a workflow is triggered, the condition evaluation can use the graph database to determine if the event's associated record matches the specified query.

## Key Benefits

- **Complex Condition Logic**: Express conditions that would be difficult with simple field matching
- **Reusable Query Definitions**: Define queries once and use them in multiple workflows
- **Graph Database Power**: Leverage graph paths to express complex relationships
- **Performance Optimized**: Uses the QueryExecutor with caching and optimized execution paths
- **Administrator-Friendly**: Non-developers can build complex business rules

## How It Works

1. A query is defined using QueryPath and QueryValue objects, which specify graph paths and matching criteria
2. The query is saved in the database
3. A workflow condition is created with type `QUERY_MATCH` and references the saved query
4. When a database event occurs, the workflow engine evaluates the condition by:
   - Checking if the event's record matches the saved query
   - Using the optimized QueryExecutor to execute the graph query
   - Determining if the condition is met based on the query result

## Implementation Components

### 1. WorkflowConditionType

The workflow module defines a `QUERY_MATCH` condition type:

```python
class WorkflowConditionType(enum.StrEnum):```

"""Types of workflow conditions"""
FIELD_VALUE = "field_value"
TIME_BASED = "time_based"
ROLE_BASED = "role_based"
QUERY_MATCH = "query_match"  # Uses existing QueryModel for complex conditions
CUSTOM = "custom"
```
```

### 2. WorkflowConditionModel

The `WorkflowConditionModel` includes a reference to a `QueryModel`:

```python
query_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(```

ForeignKey("query.id", ondelete="SET NULL"),
nullable=True,
index=True,
doc="Reference to a QueryModel for complex condition evaluation (used with QUERY_MATCH type)",
info={"edge": "USES_QUERY", "reverse_edge": "USED_BY_CONDITIONS"},
```
)
```

### 3. WorkflowEngine

The workflow engine includes a handler for `QUERY_MATCH` conditions:

```python
async def _handle_query_match_condition(```

self,
condition: WorkflowCondition,
event: WorkflowEventModel,
context: Dict[str, Any]
```
) -> Result[bool, WorkflowError]:```

"""
Handle a query match condition by evaluating the record against a saved Query.
``````

```
```

This allows complex filtering using the query system to determine if a workflow
should execute for a given record. The query execution leverages the graph database
for complex queries that involve many joins, returning the IDs of matching records.
"""
# Implementation details
```
```

### 4. QueryExecutor

The `QueryExecutor` provides optimized methods for executing queries and checking if records match:

```python
async def execute_query(```

self,
query: Query,
session: Optional[AsyncSession] = None,
force_refresh: bool = False,
```
) -> Result[List[str], QueryExecutionError]:```

"""Execute a query and return matching record IDs."""
# Implementation with caching and optimization
```

async def check_record_matches_query(```

self,
query: Query,
record_id: str,
session: Optional[AsyncSession] = None,
force_refresh: bool = False,
```
) -> Result[bool, QueryExecutionError]:```

"""Check if a specific record matches a query."""
# Optimized implementation
```
```

## Usage Example

### 1. Define a Query with Graph Paths

```python
# Create query paths for graph traversal
segment_path = QueryPath(```

source_meta_type_id=customer_meta_type.id,
target_meta_type_id=customer_meta_type.id,
cypher_path="(s:Customer)-[:HAS_SEGMENT]->(t:Segment)",
data_type="str",
```
)
await segment_path.save()

region_path = QueryPath(```

source_meta_type_id=customer_meta_type.id,
target_meta_type_id=customer_meta_type.id,
cypher_path="(s:Customer)-[:IN_REGION]->(t:Region)",
data_type="str",
```
)
await region_path.save()

# Create query values
segment_value = QueryValue(```

query_path_id=segment_path.id,
include=Include.INCLUDE,
match=Match.AND,
lookup="equal",
```
)
segment_value.values = [{"id": "premium", "name": "Premium"}]
await segment_value.save()

region_value = QueryValue(```

query_path_id=region_path.id,
include=Include.INCLUDE,
match=Match.AND,
lookup="equal",
```
)
region_value.values = [{"id": "na", "name": "North America"}]
await region_value.save()

# Create a complex query
premium_query = Query(```

name="Premium North American Customers",
description="Customers in the premium segment from North America",
query_meta_type_id=customer_meta_type.id,
include_values=Include.INCLUDE,
match_values=Match.AND,  # Both conditions must be met
```
)
premium_query.query_values = [segment_value, region_value]
await premium_query.save()
```

### 2. Create a Workflow with a Query Match Condition

```python
# Create a workflow
workflow = WorkflowDef(```

name="Premium NA Customer Welcome",
description="Send a welcome email to new premium customers in North America",
status=WorkflowStatus.ACTIVE,
```
)

# Add a trigger for customer creation
trigger = WorkflowTrigger(```

entity_type="customer",
operation=WorkflowDBEvent.INSERT,
is_active=True,
```
)
workflow.triggers.append(trigger)

# Add a condition using the complex query
condition = WorkflowCondition(```

condition_type=WorkflowConditionType.QUERY_MATCH,
name="Is Premium North American Customer",
description="Only send welcome email to premium customers in North America",
query_id=premium_query.id,
```
)
workflow.conditions.append(condition)

# Add actions and recipients
# ...

# Create the workflow
await workflow_service.create_workflow(workflow)
```

### 3. Trigger an Event and Evaluate Condition

```python
# Create a customer created event
event = CustomerCreatedEvent(```

customer_id="customer456",
name="Jane Smith",
region="North America",
segment="premium",
```
)

# Dispatch the event
await event_dispatcher.dispatch(event)
```

## Performance Considerations

The QueryExecutor includes several performance optimizations:

1. **Result Caching**: Frequently used query results are cached
2. **Direct Record Checking**: Optimized checking for single records
3. **COUNT Optimization**: For counting match results without fetching all data
4. **Query Planning**: Analysis to determine the most efficient execution path

## Best Practices

1. **Keep Queries Focused**: Design queries to match specific business rules
2. **Cache Management**: Configure caching based on data volatility
3. **Test Performance**: For large datasets, test query performance before deployment
4. **Monitor Execution**: Watch query execution times for potential optimizations
5. **Reuse Common Queries**: Define standard queries for common business conditions

## Extensions and Future Development

Possible extensions to this integration include:

1. **UI Integration**: Visual query builder for workflow conditions
2. **Event Context Access**: Allow queries to access event context data
3. **Conditional Actions**: Use query results to determine specific actions
4. **Analytics**: Track condition evaluation for workflow optimization
5. **Compound Conditions**: Combine multiple query conditions with boolean logic