# Workflow Module

The Workflow Module enables tenant administrators to define custom notification workflows based on database events without requiring developer intervention.

## Key Features

- **User-defined workflows**: Define custom workflows that react to database events
- **Conditional execution**: Set conditions for when workflows should execute
- **Multiple action types**: Support for notifications, emails, webhooks, and more
- **Flexible recipient targeting**: Target users, roles, groups, or based on attributes
- **Event-driven architecture**: Integrated with both domain events and database triggers
- **Execution logging**: Track workflow executions and troubleshoot issues

## Architecture

The workflow module consists of the following key components:

1. **Workflow Definition**: Represents a complete workflow with its triggers, conditions, actions, and recipients.
2. **Workflow Trigger**: Defines what database events trigger a workflow.
3. **Workflow Condition**: Specifies additional conditions that must be met for a workflow to execute.
4. **Workflow Action**: Defines what actions to take when a workflow is triggered.
5. **Workflow Recipient**: Specifies who should receive notifications from a workflow.
6. **Workflow Engine**: Core component that executes workflows based on events.
7. **Event Integration**: Connects to both domain events and database events.

## Getting Started

### Creating a Workflow Definition

```python
from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowConditionType,
)
from uno.workflows.objs import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
)
from uno.workflows.provider import WorkflowService
from uno.enums import WorkflowDBEvent

import inject

# Get the workflow service
workflow_service = inject.instance(WorkflowService)

# Create a workflow definition
workflow = WorkflowDef(
    name="New User Notification",
    description="Send notifications when new users are created",
    status=WorkflowStatus.ACTIVE,
    version="1.0.0",
)

# Add a trigger for user creation
trigger = WorkflowTrigger(
    entity_type="user",
    operation=WorkflowDBEvent.INSERT,
    is_active=True,
)
workflow.triggers.append(trigger)

# Add a condition for verified users only
condition = WorkflowCondition(
    condition_type=WorkflowConditionType.FIELD_VALUE,
    condition_config={
        "field": "is_verified", 
        "operator": "eq", 
        "value": True
    },
    name="User is verified",
)
workflow.conditions.append(condition)

# Add a notification action
action = WorkflowAction(
    action_type=WorkflowActionType.NOTIFICATION,
    action_config={
        "title": "New User Registration",
        "message": "A new verified user has registered: {{ payload.username }}",
    },
    name="Send admin notification",
)
workflow.actions.append(action)

# Add admin recipients
recipient = WorkflowRecipient(
    recipient_type=WorkflowRecipientType.ROLE,
    recipient_id="admin",
    name="All administrators",
)
workflow.recipients.append(recipient)

# Save the workflow
async def create_workflow():
    result = await workflow_service.create_workflow(workflow)
    if result.is_ok():
        workflow_id = result.unwrap()
        print(f"Created workflow with ID: {workflow_id}")
    else:
        print(f"Error creating workflow: {result.unwrap_err()}")
```

### Starting the Event Listener

To process database events in real-time, you need to start the PostgreSQL event listener:

```python
import asyncio
from uno.workflows.provider import WorkflowService
import inject

# Get the workflow service
workflow_service = inject.instance(WorkflowService)

async def start_listener():
    # Start the PostgreSQL event listener
    result = await workflow_service.start_event_listener()
    
    if result.is_ok():
        print("Event listener started")
        try:
            # Keep the listener running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            # Stop the listener when the application stops
            await workflow_service.stop_event_listener()
            print("Event listener stopped")
    else:
        print(f"Failed to start event listener: {result.unwrap_err()}")

# Run the listener
asyncio.run(start_listener())
```

### Integration with Domain Events

The workflow module can also be triggered by domain events:

```python
from uno.domain.events import DomainEvent
from uno.domain.event_dispatcher import EventDispatcher
from uno.workflows.engine import WorkflowEventHandler
import inject

# Create a domain event
class UserCreatedEvent(DomainEvent):
    def __init__(self, user_id, username, email):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.email = email

# Get the event dispatcher and workflow event handler
event_dispatcher = inject.instance(EventDispatcher)
workflow_handler = inject.instance(WorkflowEventHandler)

# Register the workflow handler
event_dispatcher.register_handler(UserCreatedEvent, workflow_handler)

# Dispatch an event
async def dispatch_event():
    event = UserCreatedEvent("user123", "johndoe", "john@example.com")
    await event_dispatcher.dispatch(event)

# Run the example
asyncio.run(dispatch_event())
```

## Workflow Conditions

Conditions determine whether a workflow should execute. The module supports several types of conditions:

### Field Value Conditions

```python
# Check if a field equals a value
condition = WorkflowCondition(
    condition_type=WorkflowConditionType.FIELD_VALUE,
    condition_config={
        "field": "status",
        "operator": "eq",
        "value": "approved"
    }
)

# Check if a field is greater than a value
condition = WorkflowCondition(
    condition_type=WorkflowConditionType.FIELD_VALUE,
    condition_config={
        "field": "amount",
        "operator": "gt",
        "value": 1000
    }
)
```

Supported operators:
- `eq`: Equals
- `neq`: Not equals
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `in`: In a list of values
- `nin`: Not in a list of values
- `contains`: Contains a substring
- `startswith`: Starts with a substring
- `endswith`: Ends with a substring

### Time-Based Conditions

```python
condition = WorkflowCondition(
    condition_type=WorkflowConditionType.TIME_BASED,
    condition_config={
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "start_time": "09:00",
        "end_time": "17:00",
        "timezone": "UTC"
    }
)
```

### Role-Based Conditions

```python
condition = WorkflowCondition(
    condition_type=WorkflowConditionType.ROLE_BASED,
    condition_config={
        "user_field": "created_by",
        "required_role": "admin"
    }
)
```

### Query Match Conditions

For complex filtering needs, you can use existing QueryModel definitions:

```python
# First create or retrieve a QueryModel
from uno.queries.objs import Query

# Get an existing query that filters customers by region and purchase history
complex_query = await Query.get("query123")

# Create a workflow condition using this query
condition = WorkflowCondition(
    condition_type=WorkflowConditionType.QUERY_MATCH,
    name="Customer matches market segment",
    description="Only run workflow for premium customers in North America",
    query_id=complex_query.id
)
```

This leverages the power of the QueryModel system to create sophisticated conditions without having to implement complex filtering logic in the workflow conditions themselves.

## Action Types

The workflow module supports several types of actions:

### Notification Actions

Send in-app notifications:

```python
action = WorkflowAction(
    action_type=WorkflowActionType.NOTIFICATION,
    action_config={
        "title": "Order Approved",
        "message": "Order #{{ payload.order_id }} has been approved",
        "priority": "medium"
    }
)
```

### Email Actions

Send email notifications:

```python
action = WorkflowAction(
    action_type=WorkflowActionType.EMAIL,
    action_config={
        "subject": "New Order Notification",
        "template": "order_notification",
        "variables": {
            "order_id": "{{ payload.order_id }}",
            "customer": "{{ payload.customer_name }}",
            "amount": "{{ payload.amount }}"
        }
    }
)
```

### Webhook Actions

Call external webhooks:

```python
action = WorkflowAction(
    action_type=WorkflowActionType.WEBHOOK,
    action_config={
        "url": "https://example.com/api/webhook",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer {{ secret.api_key }}"
        },
        "payload": {
            "event": "order.created",
            "order_id": "{{ payload.order_id }}",
            "amount": "{{ payload.amount }}"
        }
    }
)
```

## Recipient Types

The workflow module supports several types of recipients:

### User Recipients

```python
recipient = WorkflowRecipient(
    recipient_type=WorkflowRecipientType.USER,
    recipient_id="user123"
)
```

### Role Recipients

```python
recipient = WorkflowRecipient(
    recipient_type=WorkflowRecipientType.ROLE,
    recipient_id="admin"
)
```

### Group Recipients

```python
recipient = WorkflowRecipient(
    recipient_type=WorkflowRecipientType.GROUP,
    recipient_id="sales_team"
)
```

### Attribute Recipients

```python
recipient = WorkflowRecipient(
    recipient_type=WorkflowRecipientType.ATTRIBUTE,
    recipient_id="department",
    notification_config={
        "attribute_value": "sales"
    }
)
```

## Execution Logs

You can retrieve execution logs to monitor workflow executions:

```python
import inject
from uno.workflows.provider import WorkflowService

# Get the workflow service
workflow_service = inject.instance(WorkflowService)

async def get_logs():
    # Get logs for a specific workflow
    result = await workflow_service.get_execution_logs(
        workflow_id="workflow123",
        status="success",
        limit=10,
        offset=0
    )
    
    if result.is_ok():
        logs = result.unwrap()
        print(f"Found {len(logs)} logs")
        for log in logs:
            print(f"Execution {log.id}: {log.status} - {log.executed_at}")
    else:
        print(f"Error retrieving logs: {result.unwrap_err()}")

# Run the example
asyncio.run(get_logs())
```

## Custom Extensions

You can extend the workflow module with custom condition handlers, action handlers, and recipient resolvers:

```python
from uno.workflows.engine import WorkflowEngine
from uno.workflows.models import WorkflowConditionType, WorkflowActionType

# Get the workflow engine
workflow_engine = inject.instance(WorkflowEngine)

# Register a custom condition handler
workflow_engine.register_condition_handler(
    WorkflowConditionType.CUSTOM,
    my_custom_condition_handler
)

# Register a custom action handler
workflow_engine.register_action_handler(
    WorkflowActionType.CUSTOM,
    my_custom_action_handler
)

# Register a custom recipient resolver
workflow_engine.register_recipient_resolver(
    WorkflowRecipientType.CUSTOM,
    my_custom_recipient_resolver
)
```

## Troubleshooting

If workflows are not executing as expected, check the following:

1. **Workflow Status**: Ensure the workflow status is set to `ACTIVE`.
2. **Trigger Configuration**: Verify the entity type and operation match the events you're trying to capture.
3. **Condition Configuration**: Check that conditions are correctly configured and not too restrictive.
4. **Event Listener**: Make sure the PostgreSQL event listener is running.
5. **Execution Logs**: Check the execution logs for errors or failed conditions.

For more information, see the [API Reference](/docs/api/workflows.md) and [Examples](/docs/workflows/examples.md).