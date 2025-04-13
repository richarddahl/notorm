# Workflow Management System

The workflow management system provides a powerful and flexible way to define and execute automated workflows based on database events. With a visual designer interface, administrators can create custom notification workflows without requiring developer intervention.

## Key Features

- **Visual Workflow Designer**: Drag-and-drop interface for creating workflows
- **Advanced Conditions**: Complex condition evaluation with logical operators
- **Multiple Action Types**: Notifications, emails, webhooks, and database operations
- **Dynamic Recipients**: Flexible recipient targeting based on entity attributes
- **Simulation Tools**: Test workflows before deploying them
- **Execution Monitoring**: Track workflow execution history and performance

## Core Components

The workflow system is built on several key components:

### 1. Workflow Engine

The workflow engine is responsible for:
- Processing database events
- Evaluating trigger conditions
- Executing configured actions
- Recording execution history

### 2. Action Executors

Action executors handle different types of actions:
- **Notification Executor**: Sends in-app notifications
- **Email Executor**: Sends email notifications
- **Webhook Executor**: Makes HTTP calls to external systems
- **Database Executor**: Performs database operations
- **Custom Executor**: Executes custom code or integrations

### 3. Condition Evaluators

Condition evaluators provide complex condition logic:
- **Field Conditions**: Evaluate entity field values
- **Time Conditions**: Time-based scheduling
- **Role Conditions**: User role-based conditions
- **Composite Conditions**: Combine multiple conditions (AND, OR, NOT)

### 4. Recipient Resolvers

Recipient resolvers determine who should receive notifications:
- **User**: Specific users by ID
- **Role**: All users with specific roles
- **Department**: All users in specific departments
- **Dynamic**: Recipients determined by entity attributes

### 5. Admin Interface

The admin interface provides a complete workflow management experience:
- **Workflow Dashboard**: Overview of all workflows
- **Workflow Designer**: Visual workflow creation tool
- **Execution History**: View workflow execution logs
- **Simulation Tools**: Test workflows with sample data

## Getting Started

To access the workflow system, navigate to the Admin Dashboard and select "Workflows" from the Integration section.

### Creating a Workflow

1. From the Workflow Dashboard, click "Create Workflow"
2. Define basic workflow information:
   - Name
   - Description
   - Entity type
   - Trigger operations (create, update, delete)
3. Add conditions (optional):
   - Field conditions
   - Time conditions
   - Role conditions
   - Composite conditions
4. Configure actions:
   - Notification actions
   - Email actions
   - Webhook actions
   - Database actions
5. Define recipients for notification and email actions
6. Test the workflow using the simulation tool
7. Save and activate the workflow

### Monitoring Workflows

The Workflow Dashboard provides:
- Status of all workflows (active/inactive)
- Execution history
- Success/failure rates
- Performance metrics

Click on any execution record to view detailed information about what happened during workflow execution, including condition evaluation results and action outcomes.

## Technical Architecture

The workflow system uses a modular architecture with dependency injection:

- **Event-Driven**: Integrates with the domain event system
- **Extensible**: Easily add new action types, condition types, and recipient resolvers
- **Scalable**: Designed for high-volume event processing
- **Reliable**: Comprehensive error handling and retry capabilities

## Programmatic Usage

While the visual designer is recommended for most users, workflows can also be created programmatically:

```python
from uno.workflows.objs import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
)
from uno.workflows.provider import WorkflowService
from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowConditionType,
)
import inject

# Get the workflow service
workflow_service = inject.instance(WorkflowService)

# Create a workflow definition
workflow = WorkflowDef(
    name="New Order Notification",
    description="Send notifications when new orders are created",
    status="active",
    version=1,
)

# Add a trigger
trigger = WorkflowTrigger(
    entity_type="order",
    operations=["create"],
)
workflow.triggers.append(trigger)

# Add a condition
condition = WorkflowCondition(
    type="field",
    field="total",
    operator="gt",
    value="100",
)
workflow.conditions.append(condition)

# Add an action
action = WorkflowAction(
    type="notification",
    title="New Order",
    body="A new order #{{order_number}} has been created.",
    priority="normal",
)
workflow.actions.append(action)

# Add a recipient
recipient = WorkflowRecipient(
    type="role",
    value="sales_manager",
)
action.recipients.append(recipient)

# Save the workflow
async def create_workflow():
    result = await workflow_service.create_workflow(workflow)
    if result.is_success:
        workflow_id = result.value
        print(f"Created workflow with ID: {workflow_id}")
    else:
        print(f"Error creating workflow: {result.error}")

# Run the example
import asyncio
asyncio.run(create_workflow())
```

## Custom Extensions

The workflow system can be extended with custom components:

### Custom Action Executors

```python
from uno.workflows.executor import ActionExecutorBase, register_executor

class CustomExecutor(ActionExecutorBase):
    """Custom action executor for specialized integrations."""
    
    async def execute(self, action, context):
        # Custom execution logic
        return {"status": "success", "details": "Custom action executed"}

# Register the executor
register_executor("custom", CustomExecutor())
```

### Custom Condition Evaluators

```python
from uno.workflows.conditions import ConditionEvaluatorBase, register_evaluator

class CustomEvaluator(ConditionEvaluatorBase):
    """Custom condition evaluator for specialized logic."""
    
    async def evaluate(self, condition, context):
        # Custom evaluation logic
        return True

# Register the evaluator
register_evaluator("custom", CustomEvaluator())
```

### Custom Recipient Resolvers

```python
from uno.workflows.recipients import RecipientResolverBase, register_resolver

class CustomResolver(RecipientResolverBase):
    """Custom recipient resolver for specialized targeting."""
    
    async def resolve(self, recipient, context):
        # Custom resolution logic
        return ["user1", "user2"]

# Register the resolver
register_resolver("custom", CustomResolver())
```

## API Reference

The workflow system provides a comprehensive REST API:

### Endpoints

- `GET /api/workflows`: List all workflows
- `GET /api/workflows/{id}`: Get a specific workflow
- `POST /api/workflows`: Create a new workflow
- `PUT /api/workflows/{id}`: Update a workflow
- `DELETE /api/workflows/{id}`: Delete a workflow
- `PATCH /api/workflows/{id}/status`: Update workflow status
- `GET /api/workflows/executions`: List execution logs
- `GET /api/workflows/{id}/executions/{execution_id}`: Get execution details
- `POST /api/workflows/{id}/simulate`: Simulate workflow execution

For complete API documentation, refer to the [API Reference](/docs/api/workflows.md).

## Troubleshooting

If workflows are not executing as expected, check:

1. **Workflow Status**: Ensure the workflow is active
2. **Trigger Configuration**: Verify entity type and operations
3. **Condition Logic**: Ensure conditions are not too restrictive
4. **Action Configuration**: Check for valid action settings
5. **Recipient Setup**: Verify recipient targeting is correct
6. **Execution Logs**: Review execution history for failures or errors

## Documentation Resources

### Getting Started
- [Quick Start Guide](/docs/workflows/quick-start.md): Create your first workflow in 5 minutes
- [Comprehensive Tutorial](/docs/workflows/tutorial.md): Step-by-step guide with practical examples

### Technical Documentation
- [API Reference](/docs/api/workflows.md): Complete REST API documentation
- [Advanced Workflow Patterns](/docs/workflows/advanced-patterns.md): Sophisticated techniques for complex workflows
- [Custom Extensions](/docs/workflows/custom-extensions.md): Extend the system with custom components
- [Security Considerations](/docs/workflows/security.md): Security best practices and implementation guidelines
- [Troubleshooting Guide](/docs/workflows/troubleshooting.md): Diagnose and resolve common workflow issues
- [Performance Optimization](/docs/workflows/performance.md): Strategies for scaling and optimizing workflows

### Adoption & Migration
- [Migration Guide](/docs/workflows/migration-guide.md): Transition from legacy notification systems