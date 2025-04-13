# Advanced Workflow Patterns

This guide covers advanced patterns and techniques for creating powerful, efficient workflows in the Workflow Management System.

## Table of Contents

- [Chained Workflows](#chained-workflows)
- [Composite Conditions](#composite-conditions)
- [Dynamic Content Generation](#dynamic-content-generation)
- [Multi-Entity Workflows](#multi-entity-workflows)
- [Scheduled Workflows](#scheduled-workflows)
- [Workflow Templates](#workflow-templates)
- [Bulk Notifications](#bulk-notifications)
- [Performance Optimization](#performance-optimization)

## Chained Workflows

Chained workflows allow you to create a sequence of interconnected workflows where one workflow triggers another, creating a multi-step business process.

### Implementation Technique

1. **Database Action as Trigger**: Use a database action in the first workflow to create or update a record that will trigger the next workflow.

```json
{
  "type": "database",
  "operation": "create",
  "target_entity": "workflow_transition",
  "field_mapping": {
    "source_workflow_id": "{{workflow_id}}",
    "entity_id": "{{entity_id}}",
    "status": "ready_for_next_step"
  }
}
```

2. **Transition Entity**: Create a special entity type (e.g., `workflow_transition`) that serves as a bridge between workflows.

3. **Second Workflow Trigger**: Configure the second workflow to listen for the creation of transition records.

```json
{
  "entity_type": "workflow_transition",
  "operations": ["create"]
}
```

4. **Context Passing**: Pass context data between workflows using the transition entity.

### Example: Order Processing

A complete order processing workflow chain:

1. **First Workflow**: Triggered when a new order is created
   - Validates order details
   - Creates a `workflow_transition` record with status "ready_for_processing"

2. **Second Workflow**: Triggered by the transition record
   - Processes payment
   - Updates the transition record with status "ready_for_fulfillment"

3. **Third Workflow**: Triggered by the updated transition record
   - Handles order fulfillment
   - Sends shipping notification

### Best Practices

- Keep the chain manageable (3-5 workflows maximum)
- Include error handling at each step
- Log transition state changes for debugging
- Consider timeout conditions for long-running workflows

## Composite Conditions

Composite conditions allow you to create complex logic by combining multiple conditions with logical operators (AND, OR, NOT).

### Implementation Technique

Use the composite condition type with nested conditions:

```json
{
  "type": "composite",
  "operator": "and",
  "conditions": [
    {
      "type": "field",
      "field": "total",
      "operator": "gt",
      "value": "100"
    },
    {
      "type": "composite",
      "operator": "or",
      "conditions": [
        {
          "type": "field",
          "field": "customer_type",
          "operator": "eq",
          "value": "vip"
        },
        {
          "type": "field",
          "field": "is_first_purchase",
          "operator": "eq",
          "value": "true"
        }
      ]
    }
  ]
}
```

### Common Patterns

1. **Inclusion/Exclusion Logic**:
   ```json
   {
     "type": "composite",
     "operator": "and",
     "conditions": [
       { "include condition" },
       {
         "type": "composite",
         "operator": "not",
         "conditions": [
           { "exclude condition" }
         ]
       }
     ]
   }
   ```

2. **Multiple Criteria Matching**:
   ```json
   {
     "type": "composite",
     "operator": "or",
     "conditions": [
       { "criteria 1" },
       { "criteria 2" },
       { "criteria 3" }
     ]
   }
   ```

3. **Complex Business Rules**:
   ```json
   {
     "type": "composite",
     "operator": "and",
     "conditions": [
       { "primary condition" },
       {
         "type": "composite",
         "operator": "or",
         "conditions": [
           { "secondary condition A" },
           {
             "type": "composite",
             "operator": "and",
             "conditions": [
               { "secondary condition B1" },
               { "secondary condition B2" }
             ]
           }
         ]
       }
     ]
   }
   ```

### Best Practices

- Limit nesting depth to 3-4 levels for readability
- Group related conditions together
- Name conditions descriptively in the designer
- Test complex conditions thoroughly with the simulator

## Dynamic Content Generation

Dynamic content allows you to generate personalized notification messages based on entity data and context.

### Templating Techniques

1. **Basic Field Substitution**:
   ```
   Your order #{{order_number}} has been shipped.
   ```

2. **Conditional Content**:
   ```
   {% if total > 100 %}Thank you for your large order!{% else %}Thank you for your order.{% endif %}
   ```

3. **Formatting Values**:
   ```
   Total: ${{total | number(2)}}
   ```

4. **Iteration**:
   ```
   Your items:{% for item in items %}\n- {{item.name}} ({{item.quantity}}){% endfor %}
   ```

5. **Including Data from Related Entities**:
   ```
   Your order will be delivered to {{shipping_address.street}}, {{shipping_address.city}}
   ```

### Example: Rich Notification Template

```
Hi {{customer.first_name}},

Your order #{{order_number}} placed on {{created_at | date('MMM D, YYYY')}} has been {{status}}.

{% if items %}
Order items:
{% for item in items %}
- {{item.quantity}}x {{item.product_name}} (${{item.price | number(2)}})
{% endfor %}
{% endif %}

Total: ${{total | number(2)}}
{% if shipping_method %}
Shipping Method: {{shipping_method}}
Estimated Delivery: {{estimated_delivery | date('MMM D, YYYY')}}
{% endif %}

{% if status == 'shipped' %}
Tracking Number: {{tracking_number}}
Track your package: {{tracking_url}}
{% endif %}

{% if total > 100 %}
As a thank you for your purchase over $100, you've received a 10% discount code for your next order: {{discount_code}}
{% endif %}

Thank you for shopping with us!
```

### Best Practices

- Test templates with different data scenarios
- Use default values for optional fields
- Keep templates maintainable by factoring out complex logic
- Document available variables and formatting options
- Handle missing data gracefully

## Multi-Entity Workflows

Multi-entity workflows operate across different entity types, allowing for complex business processes.

### Implementation Techniques

1. **Using Database Actions**:
   - Configure a workflow that's triggered by one entity type
   - Use database actions to query or modify related entities

2. **Entity Relationships**:
   - Store relationship information in the entity data
   - Access related entity data through relationship fields

3. **Transition Entities**:
   - Create special entities that track the state of multi-entity processes
   - Use these entities to coordinate across multiple workflows

### Example: Coordinated Order and Inventory Workflow

1. **Order Workflow** (triggered by order creation):
   - Check inventory levels via database query
   - Create inventory reservation
   - Send confirmation notification

2. **Inventory Workflow** (triggered by inventory changes):
   - Update product availability
   - Trigger reorder notifications if level is low
   - Update related order status if needed

### Best Practices

- Clearly document entity relationships
- Use consistent field names across related entities
- Include error handling for missing relationships
- Consider transaction boundaries carefully
- Test multi-entity workflows thoroughly

## Scheduled Workflows

Scheduled workflows execute based on time patterns rather than immediate database events.

### Implementation Techniques

1. **Time-Based Trigger**:
   ```json
   {
     "entity_type": "scheduler",
     "operations": ["tick"],
     "schedule": {
       "type": "cron",
       "expression": "0 9 * * 1-5"
     }
   }
   ```

2. **Relative Time Conditions**:
   ```json
   {
     "type": "time",
     "operator": "before",
     "field": "due_date",
     "value": "3d"
   }
   ```

3. **Batch Processing**:
   - Use database actions to retrieve entities meeting certain criteria
   - Process these entities in a single scheduled workflow execution

### Example: Follow-up Reminders

A workflow that sends follow-up reminders for incomplete tasks:

```json
{
  "name": "Task Follow-up Reminder",
  "trigger": {
    "entity_type": "scheduler",
    "operations": ["tick"],
    "schedule": {
      "type": "cron",
      "expression": "0 9 * * 1-5"
    }
  },
  "actions": [
    {
      "type": "database",
      "operation": "query",
      "target_entity": "task",
      "query": {
        "status": "in_progress",
        "due_date": {
          "operator": "lt",
          "value": "now() + interval '2 day'"
        },
        "reminder_sent": {
          "operator": "is",
          "value": "null"
        }
      },
      "result_variable": "tasks_due_soon"
    },
    {
      "type": "notification",
      "title": "Tasks Due Soon",
      "body": "You have {{tasks_due_soon.length}} tasks due within 2 days.",
      "for_each": "tasks_due_soon",
      "recipients": [
        {
          "type": "user",
          "value": "{{item.assignee_id}}"
        }
      ]
    },
    {
      "type": "database",
      "operation": "update",
      "target_entity": "task",
      "for_each": "tasks_due_soon",
      "field_mapping": {
        "reminder_sent": "{{now()}}"
      },
      "filter": {
        "id": "{{item.id}}"
      }
    }
  ]
}
```

### Common Scheduling Patterns

1. **Daily Report**: `0 8 * * 1-5` (8 AM Monday-Friday)
2. **Monthly Reconciliation**: `0 0 1 * *` (Midnight on 1st of month)  
3. **Weekly Cleanup**: `0 0 * * 0` (Midnight on Sunday)
4. **End of Day Processing**: `0 18 * * 1-5` (6 PM Monday-Friday)
5. **Hourly Check**: `0 * * * *` (Every hour)

### Best Practices

- Use the simulator to test scheduled workflows
- Include error handling for exceptional conditions
- Avoid scheduling multiple heavy workflows at the same time
- Log execution details for monitoring
- Implement idempotent actions to prevent duplication if a workflow runs twice

## Workflow Templates

Workflow templates allow administrators to create predefined workflow configurations that can be quickly applied to specific entities.

### Implementation Techniques

1. **Base Template Definition**:
   - Create a workflow with placeholder variables for configurable elements
   - Store the template in a `workflow_template` entity

2. **Template Instantiation**:
   - When applying a template, copy its structure to a new workflow
   - Replace placeholder variables with specific values

3. **Template Parameters**:
   - Define which aspects of the template can be customized
   - Provide UI for configuring these parameters

### Example: New Product Announcement Template

```json
{
  "name": "New {{entity_type}} Announcement",
  "description": "Announces new {{entity_type}} to relevant stakeholders",
  "trigger": {
    "entity_type": "{{entity_type}}",
    "operations": ["create"]
  },
  "conditions": [
    {
      "type": "field",
      "field": "{{status_field}}",
      "operator": "eq",
      "value": "{{active_status}}"
    }
  ],
  "actions": [
    {
      "type": "notification",
      "title": "New {{entity_type}}: {{name_template}}",
      "body": "{{description_template}}",
      "recipients": [
        {
          "type": "{{recipient_type}}",
          "value": "{{recipient_value}}"
        }
      ]
    }
  ],
  "parameters": {
    "entity_type": {
      "label": "Entity Type",
      "type": "string",
      "required": true
    },
    "status_field": {
      "label": "Status Field",
      "type": "string",
      "required": true
    },
    "active_status": {
      "label": "Active Status Value",
      "type": "string",
      "required": true
    },
    "name_template": {
      "label": "Name Template",
      "type": "string",
      "required": true,
      "default": "{{name}}"
    },
    "description_template": {
      "label": "Description Template",
      "type": "text",
      "required": true,
      "default": "A new {{entity_type}} '{{name}}' has been created."
    },
    "recipient_type": {
      "label": "Recipient Type",
      "type": "string",
      "required": true,
      "options": ["user", "role", "department", "dynamic"]
    },
    "recipient_value": {
      "label": "Recipient Value",
      "type": "string",
      "required": true
    }
  }
}
```

### Best Practices

- Design templates for common business scenarios
- Document each template thoroughly
- Provide sensible defaults for parameters
- Create templates for different levels of complexity
- Allow templates to be versioned

## Bulk Notifications

Bulk notifications allow efficient processing of multiple notifications in a single workflow execution.

### Implementation Techniques

1. **Aggregation Queries**:
   - Use database actions to collect multiple entities for notification
   - Apply aggregation functions (count, sum, etc.) as needed

2. **Batched Processing**:
   - Define a batch size to prevent overwhelming notification systems
   - Process entities in manageable chunks

3. **Summary Notifications**:
   - Condense multiple individual events into a single summary notification
   - Include counts, statistics, or lists of affected items

### Example: Daily Task Summary

```json
{
  "name": "Daily Task Summary",
  "trigger": {
    "entity_type": "scheduler",
    "operations": ["tick"],
    "schedule": {
      "type": "cron",
      "expression": "0 17 * * 1-5"
    }
  },
  "actions": [
    {
      "type": "database",
      "operation": "query",
      "target_entity": "user",
      "query": {
        "is_active": true
      },
      "result_variable": "active_users"
    },
    {
      "type": "notification",
      "title": "Daily Task Summary",
      "body": "# Task Summary for {{today | date('MMM D')}}\n\n{% set completed = get_tasks(user_id, 'completed', today) %}\n{% set pending = get_tasks(user_id, 'pending') %}\n\n{% if completed.length > 0 %}## Completed Today ({{completed.length}})\n{% for task in completed %}- {{task.title}}\n{% endfor %}{% endif %}\n\n{% if pending.length > 0 %}## Pending ({{pending.length}})\n{% for task in pending %}- {{task.title}} {% if task.due_date %}(Due: {{task.due_date | date('MMM D')}}){% endif %}\n{% endfor %}{% endif %}\n\n{% if pending.length == 0 and completed.length == 0 %}You have no tasks.{% endif %}",
      "for_each": "active_users",
      "recipients": [
        {
          "type": "user",
          "value": "{{item.id}}"
        }
      ],
      "context_enrichment": {
        "user_id": "{{item.id}}",
        "today": "{{now()}}"
      }
    }
  ],
  "functions": {
    "get_tasks": {
      "query": {
        "assignee_id": "{{params.0}}",
        "status": "{{params.1}}",
        "where_date": {
          "field": "{{params.1 == 'completed' ? 'completed_at' : 'created_at'}}",
          "operator": "{{params.length > 2 ? 'date_equals' : 'before'}}",
          "value": "{{params.length > 2 ? params.2 : 'now() + interval \\'1 day\\''}}"
        }
      }
    }
  }
}
```

### Best Practices

- Set reasonable batch sizes (e.g., 100-500 entities per batch)
- Include rate limiting for external notification channels
- Provide clear summaries rather than overwhelming detail
- Allow users to customize their notification preferences
- Include links to more detailed views
- Implement error recovery for batch processing

## Performance Optimization

Optimize workflows for performance, especially when dealing with high-volume events or complex logic.

### Optimization Techniques

1. **Specific Triggers**:
   - Limit operations to only those needed (e.g., "create" instead of ["create", "update"])
   - Add specific field-change triggers for updates rather than triggering on any update

2. **Early Filtering**:
   - Place the most restrictive conditions first in composite conditions
   - Use database conditions before complex in-memory evaluations

3. **Efficient Queries**:
   - Limit fields returned by database actions to only those needed
   - Add appropriate indexes to frequently queried fields
   - Use pagination for large result sets

4. **Caching**:
   - Cache frequently used reference data
   - Store previous calculation results when appropriate

5. **Asynchronous Processing**:
   - Use deferred processing for non-time-critical notifications
   - Implement backoff strategies for retries

### Example: Optimized High-Volume Workflow

```json
{
  "name": "Optimized Order Notification",
  "trigger": {
    "entity_type": "order",
    "operations": ["create"],
    "field_triggers": ["status"]
  },
  "conditions": [
    {
      "type": "field",
      "field": "status",
      "operator": "eq",
      "value": "completed"
    },
    {
      "type": "field",
      "field": "total",
      "operator": "gt",
      "value": "0"
    }
  ],
  "actions": [
    {
      "type": "notification",
      "title": "Order Completed",
      "body": "Your order #{{order_number}} has been completed.",
      "priority": "normal",
      "delivery_strategy": "deferred",
      "recipients": [
        {
          "type": "user",
          "value": "{{customer_id}}"
        }
      ]
    }
  ],
  "optimization": {
    "condition_evaluation_strategy": "short_circuit",
    "action_execution_strategy": "parallel",
    "max_execution_time_ms": 5000,
    "deferred_execution_interval_ms": 60000
  }
}
```

### Performance Monitoring

1. **Execution Metrics**:
   - Track average execution time per workflow
   - Monitor the number of workflow executions per minute
   - Record action success/failure rates

2. **Resource Usage**:
   - Monitor memory usage during workflow execution
   - Track database connection usage
   - Monitor notification delivery rates

3. **Optimization Opportunities**:
   - Identify workflows that frequently timeout
   - Find conditions that rarely evaluate to true
   - Look for duplicate or redundant notifications

### Best Practices

- Test workflows under load before deploying to production
- Implement circuit breakers for external services
- Monitor workflow execution times and set appropriate timeouts
- Use batch processing for high-volume workflows
- Schedule resource-intensive workflows during off-peak hours
- Archive old execution logs regularly

## Conclusion

These advanced patterns provide powerful techniques for creating sophisticated workflow solutions. By leveraging these patterns, you can build efficient, scalable workflow systems that handle complex business processes effectively.