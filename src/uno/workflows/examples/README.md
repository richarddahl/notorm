# Workflow Module Examples

This directory contains examples demonstrating how to use the workflow module in Uno.

## Examples

### Query Integration Example

File: [query_integration.py](./query_integration.py)

This example demonstrates how to:
- Create a QueryModel for filtering premium customers
- Create a workflow that uses the query as a condition
- Trigger the workflow with a domain event

The example shows the powerful integration between the QueryModel system and workflow conditions, allowing complex filtering rules to be used for determining when workflows should be executed.

To run the example:
```bash
python -m src.uno.workflows.examples.query_integration
```

## Key Concepts

### QueryModel Integration

The workflow module integrates with the QueryModel system to allow complex filtering conditions:

1. **QueryModel as Condition**: Use existing QueryModel instances to define when workflows should trigger
2. **User-Defined Queries**: Leverage user-defined queries for workflow conditions without code changes
3. **Complex Filtering**: Apply sophisticated filtering that would be difficult to express in simple condition configuration

### Event-Driven Workflow Execution

Workflows are triggered by domain events and database operations:

1. **Domain Events**: Use existing domain events to trigger workflows
2. **Database Operations**: Trigger workflows on database insert, update, or delete operations
3. **Conditions**: Apply conditions to determine when workflows should execute
4. **Actions**: Perform actions such as sending notifications, emails, or webhooks

## Best Practices

1. **Create Reusable Queries**: Design queries that can be reused across multiple workflows
2. **Test Workflows**: Use the examples as templates for testing your own workflows
3. **Start Simple**: Begin with simple workflows and gradually add complexity
4. **Monitor Execution**: Use the workflow execution logs to monitor and troubleshoot workflow execution

## Related Documentation

- [Workflow Overview](/docs/workflows/overview.md)
- [Query System Documentation](/docs/queries/overview.md)