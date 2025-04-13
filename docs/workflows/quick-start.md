# Workflow System Quick Start Guide

This quick start guide will help you get up and running with the Workflow System in just a few minutes. Follow these simple steps to create your first workflow.

## What You Can Automate

The Workflow System allows you to automate business processes in response to database events:

- **Send notifications** when records are created or updated
- **Trigger emails** based on specific conditions
- **Update related records** automatically
- **Integrate with external systems** via webhooks
- **Schedule recurring tasks**

## 5-Minute Setup: Your First Workflow

### Step 1: Access the Workflow Dashboard

1. Log in to the Admin Dashboard
2. Navigate to "Integration" > "Workflows"
3. Click "Create Workflow"

### Step 2: Define the Workflow Trigger

1. Enter a name for your workflow (e.g., "New User Welcome")
2. Set the trigger:
   - **Entity Type**: "user"
   - **Operations**: "create"

### Step 3: Set Up a Simple Condition (Optional)

1. Click "Add Condition"
2. Create a field condition:
   - **Field**: "status"
   - **Operator**: "equals"
   - **Value**: "active"

### Step 4: Add a Notification Action

1. Click "Add Action"
2. Configure a notification:
   - **Type**: "Notification"
   - **Title**: "Welcome to the Platform"
   - **Body**: "Hello {{name}}, welcome to our platform! We're excited to have you join us."
   - **Recipients**: Set to "User" and value to "{{id}}" (sends to the new user)

### Step 5: Test and Activate

1. Click "Save"
2. Click "Simulate" to test with sample data
3. If the simulation looks good, click "Activate"

That's it! You've created your first workflow. When new users are created, they'll automatically receive a welcome notification.

## Common Workflow Recipes

### Customer Order Notifications

```json
{
  "name": "Order Confirmation",
  "trigger": {
    "entity_type": "order",
    "operations": ["create"]
  },
  "conditions": [
    {
      "type": "field",
      "field": "status",
      "operator": "equals",
      "value": "confirmed"
    }
  ],
  "actions": [
    {
      "type": "notification",
      "title": "Order Confirmed",
      "body": "Your order #{{order_number}} for ${{total}} has been confirmed.",
      "recipients": [
        {
          "type": "user",
          "value": "{{customer_id}}"
        }
      ]
    }
  ]
}
```

### Task Assignment Notification

```json
{
  "name": "Task Assignment",
  "trigger": {
    "entity_type": "task",
    "operations": ["update"]
  },
  "conditions": [
    {
      "type": "field",
      "field": "assignee_id",
      "operator": "changed"
    }
  ],
  "actions": [
    {
      "type": "notification",
      "title": "New Task Assigned",
      "body": "You have been assigned to: {{title}}",
      "recipients": [
        {
          "type": "user",
          "value": "{{assignee_id}}"
        }
      ]
    }
  ]
}
```

### Scheduled Report Generation

```json
{
  "name": "Weekly Activity Report",
  "trigger": {
    "entity_type": "scheduler",
    "operations": ["tick"],
    "schedule": {
      "type": "cron",
      "expression": "0 9 * * 1"  // 9 AM every Monday
    }
  },
  "actions": [
    {
      "type": "database",
      "operation": "query",
      "target_entity": "activity",
      "query": {
        "created_at": {
          "operator": "between",
          "value": ["{{now() - interval '7 days'}}", "{{now()}}"]
        }
      },
      "result_variable": "weekly_activities"
    },
    {
      "type": "email",
      "subject": "Weekly Activity Report",
      "body": "Activity summary for the past week: {{weekly_activities.length}} new activities.",
      "recipients": [
        {
          "type": "role",
          "value": "manager"
        }
      ]
    }
  ]
}
```

## Key Concepts at a Glance

### Triggers

Workflows are triggered by database events:

- **Create**: When a new record is created
- **Update**: When an existing record is updated
- **Delete**: When a record is deleted
- **Schedule**: Based on time patterns (cron expressions)

### Conditions

Control when workflows execute:

- **Field Conditions**: Compare field values (equals, greater than, etc.)
- **Time Conditions**: Only run during specific times
- **Role Conditions**: Based on user roles
- **Composite Conditions**: Combine conditions with AND, OR, NOT operators

### Actions

What the workflow does when triggered:

- **Notifications**: In-app notifications
- **Emails**: Email messages
- **Webhooks**: HTTP calls to external systems
- **Database**: Create, update, or query database records

### Recipients

Who receives notifications:

- **User**: Specific user by ID
- **Role**: All users with a specific role
- **Department**: All users in a specific department
- **Dynamic**: Recipients determined by data values

## Template Variables

Use these in notification and email bodies:

- `{{field_name}}`: Inserts the value of a field
- `{% if condition %}...{% endif %}`: Conditional content
- `{% for item in items %}...{% endfor %}`: Iteration
- `{{value | filter}}`: Format values (date, number, etc.)

## Next Steps

Now that you've created your first workflow, explore these resources:

- [Comprehensive Tutorial](/docs/workflows/tutorial.md): Step-by-step guide with a complete example
- [API Reference](/docs/api/workflows.md): Programmatically create and manage workflows
- [Advanced Patterns](/docs/workflows/advanced-patterns.md): Sophisticated workflow techniques
- [Custom Extensions](/docs/workflows/custom-extensions.md): Extend the system with custom components

## Quick Tips

- **Test First**: Always use the simulator before activating workflows
- **Start Simple**: Begin with basic workflows and add complexity gradually
- **Monitor**: Check execution logs to verify workflows are running as expected
- **Optimize**: For high-volume entities, ensure conditions efficiently filter events
- **Security**: Be careful not to include sensitive data in notification templates