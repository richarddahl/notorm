# Migrating to the Workflow Management System

This guide provides a path for migrating from legacy notification systems or custom automation code to the Workflow Management System. It offers a structured approach to ensure a smooth transition with minimal disruption.

## Overview

The Workflow Management System replaces the need for:

- Custom notification code in application services
- Hardcoded email templates
- Event listeners for automation
- Scheduled jobs for recurring tasks
- Point-to-point integrations with external systems

By centralizing these automations in the workflow system, you gain:

- **Visual Designer**: No coding required for common automations
- **Centralized Management**: All automations in one place
- **Dynamic Content**: Template-based content generation
- **Flexibility**: Easily modifiable without code changes
- **Monitoring**: Built-in execution history and analytics

## Migration Process

### Phase 1: Inventory Existing Automations

Before migrating, catalog your existing automations:

1. **Create an inventory spreadsheet** with these columns:
   - Automation Name
   - Trigger Event (what initiates it)
   - Business Conditions (when it should run)
   - Actions (what it does)
   - Recipients (who gets notified)
   - Priority (for migration ordering)
   - Complexity (simple, medium, complex)
   - Code Location (where to find the current implementation)

2. **Categorize automations** by type:
   - Notifications
   - Emails
   - Database updates
   - External system integrations
   - Scheduled processes

3. **Prioritize migrations** based on:
   - Business importance
   - Implementation complexity
   - Dependencies between automations

### Phase 2: Plan the Migration Approach

Choose an approach for each automation:

1. **Direct Migration**: Recreate the exact functionality in the workflow system
2. **Enhanced Migration**: Improve the automation during migration
3. **Consolidation**: Combine multiple related automations into one workflow
4. **Redesign**: Completely rethink the automation for the new system

Develop a migration schedule with timeframes and responsibilities.

### Phase 3: Implement Parallel Systems

For critical automations, follow these steps:

1. **Build the workflow** in the new system
2. **Run both systems** in parallel (the old code and the new workflow)
3. **Compare outputs** to ensure consistency
4. **Log differences** for investigation
5. **Debug and refine** the workflow until results match

### Phase 4: Cut Over

For each automation:

1. **Disable legacy code** (comment out, don't delete yet)
2. **Activate the workflow** in production
3. **Monitor closely** for the first few days
4. **Have a rollback plan** ready in case of issues

### Phase 5: Clean Up

After successful migration:

1. **Remove legacy code** once workflows are proven stable
2. **Update documentation** to reflect the new implementations
3. **Train team members** on workflow management
4. **Standardize workflow patterns** for future development

## Migration Examples

### Example 1: New User Welcome Email

#### Legacy Implementation (Service Code)

```python
# In UserService.py
def create_user(user_data):
    # Create user in database
    user = db.create_user(user_data)
    
    # Send welcome email
    if user.status == 'active':
        subject = "Welcome to Our Platform"
        body = f"Hello {user.name},\n\nWelcome to our platform!"
        email_service.send_email(user.email, subject, body)
    
    return user
```

#### Workflow Implementation

```json
{
  "name": "New User Welcome",
  "trigger": {
    "entity_type": "user",
    "operations": ["create"]
  },
  "conditions": [
    {
      "type": "field",
      "field": "status",
      "operator": "equals",
      "value": "active"
    }
  ],
  "actions": [
    {
      "type": "email",
      "subject": "Welcome to Our Platform",
      "body": "Hello {{name}},\n\nWelcome to our platform!",
      "recipients": [
        {
          "type": "field",
          "value": "email"
        }
      ]
    }
  ]
}
```

### Example 2: Order Status Notification

#### Legacy Implementation (Event Listener)

```python
# In OrderEventListener.py
@event_handler("order.status_changed")
def handle_order_status_change(event):
    order = event.data
    customer = db.get_user(order.customer_id)
    
    if order.status == "shipped":
        notification_service.send_notification(
            customer.id,
            "Order Shipped",
            f"Your order #{order.number} has been shipped.",
            "medium"
        )
        
        # Also notify internal team
        if order.total > 1000:
            team_ids = db.get_users_by_role("fulfillment_manager")
            for team_id in team_ids:
                notification_service.send_notification(
                    team_id,
                    "High-value Order Shipped",
                    f"Order #{order.number} (${order.total}) has been shipped.",
                    "high"
                )
```

#### Workflow Implementation

```json
{
  "name": "Order Shipped Notification",
  "trigger": {
    "entity_type": "order",
    "operations": ["update"]
  },
  "conditions": [
    {
      "type": "field",
      "field": "status",
      "operator": "equals",
      "value": "shipped"
    }
  ],
  "actions": [
    {
      "type": "notification",
      "title": "Order Shipped",
      "body": "Your order #{{order_number}} has been shipped.",
      "priority": "medium",
      "recipients": [
        {
          "type": "user",
          "value": "{{customer_id}}"
        }
      ]
    },
    {
      "type": "notification",
      "title": "High-value Order Shipped",
      "body": "Order #{{order_number}} (${{total}}) has been shipped.",
      "priority": "high",
      "conditions": [
        {
          "type": "field",
          "field": "total",
          "operator": "greater_than",
          "value": "1000"
        }
      ],
      "recipients": [
        {
          "type": "role",
          "value": "fulfillment_manager"
        }
      ]
    }
  ]
}
```

### Example 3: Daily Reports (Scheduled Job)

#### Legacy Implementation (Cron Job)

```python
# In scheduled_tasks.py
@scheduled_task("0 9 * * *")  # Run at 9 AM daily
def send_daily_sales_report():
    yesterday = date.today() - timedelta(days=1)
    
    # Get sales data
    sales = db.query("""
        SELECT COUNT(*) as count, SUM(total) as total 
        FROM orders 
        WHERE DATE(created_at) = %s AND status = 'completed'
    """, yesterday)
    
    # Generate report
    subject = f"Daily Sales Report - {yesterday.strftime('%Y-%m-%d')}"
    body = f"""
    Daily Sales Report for {yesterday.strftime('%Y-%m-%d')}:
    
    Orders Completed: {sales['count']}
    Total Revenue: ${sales['total']}
    """
    
    # Send to management team
    managers = db.get_users_by_role("sales_manager")
    for manager in managers:
        email_service.send_email(manager.email, subject, body)
```

#### Workflow Implementation

```json
{
  "name": "Daily Sales Report",
  "trigger": {
    "entity_type": "scheduler",
    "operations": ["tick"],
    "schedule": {
      "type": "cron",
      "expression": "0 9 * * *"
    }
  },
  "actions": [
    {
      "type": "database",
      "operation": "query",
      "target_entity": "order",
      "query": {
        "status": "completed",
        "created_at": {
          "operator": "date_equals",
          "value": "{{now() - interval '1 day'}}"
        }
      },
      "aggregate": {
        "count": {"function": "count", "field": "id"},
        "total": {"function": "sum", "field": "total"}
      },
      "result_variable": "yesterday_sales"
    },
    {
      "type": "email",
      "subject": "Daily Sales Report - {{(now() - interval '1 day') | date('%Y-%m-%d')}}",
      "body": "Daily Sales Report for {{(now() - interval '1 day') | date('%Y-%m-%d')}}:\n\nOrders Completed: {{yesterday_sales.count}}\nTotal Revenue: ${{yesterday_sales.total | number(2)}}",
      "recipients": [
        {
          "type": "role",
          "value": "sales_manager"
        }
      ]
    }
  ]
}
```

## Common Migration Challenges

### Challenge 1: Complex Business Logic

If your legacy automation contains complex business logic that's difficult to express with the workflow system's conditions:

**Solutions:**
1. **Break it down** into simpler workflows that work together
2. **Create a custom condition evaluator** (see [Custom Extensions](/docs/workflows/custom-extensions.md))
3. **Implement a service endpoint** that the workflow can call via webhook

### Challenge 2: Custom Data Processing

Legacy code that performs complex data transformations before sending notifications:

**Solutions:**
1. **Use template expressions** for simple transformations
2. **Create database views** to pre-compute complex data
3. **Implement a transformation microservice** that workflows can call

### Challenge 3: Stateful Processes

Workflows that need to maintain state across multiple steps:

**Solutions:**
1. **Use database records** to track state between workflow executions
2. **Create transition entities** to coordinate between workflows
3. **Break into multiple workflows** that trigger each other (see [Advanced Patterns](/docs/workflows/advanced-patterns.md))

### Challenge 4: External System Dependencies

Legacy automations that integrate with external systems:

**Solutions:**
1. **Use webhook actions** for direct integration
2. **Create an integration service** that workflows can call
3. **Implement custom action executors** for specialized integrations

## Testing Strategies

### Parallel Testing

1. **Log comparison**:
   - Create a logging wrapper around the legacy system
   - Configure workflow to log to the same format
   - Run automated tests to compare outputs

2. **Shadow execution**:
   - Run both systems simultaneously in production
   - Route real events to both systems
   - Compare results without affecting users

### Workflow Simulation

1. Use the built-in **simulation tool** with real-world data samples
2. Create **test scenarios** covering the full range of inputs
3. Review **simulated outputs** before activating workflows

### Load Testing

1. **Generate test data** at production scale
2. **Measure performance** of workflows under load
3. **Optimize workflows** if needed (see Performance section in [Advanced Patterns](/docs/workflows/advanced-patterns.md))

## Organizational Change Management

### Training

1. Provide **workflow designer training** to relevant team members
2. Create a **workflow design guide** specific to your organization
3. Document **standard patterns** for common automation types

### Governance

1. Establish **workflow approval processes** for production environments
2. Create **naming conventions** for workflows and related components
3. Define **testing requirements** before workflow activation
4. Implement **monitoring and alerting** for workflow failures

### Support Model

1. Designate **workflow administrators** to help with design and troubleshooting
2. Create a **workflow helpdesk** procedure for issues and questions
3. Establish **escalation paths** for workflow failures

## Conclusion

Migrating to the Workflow Management System requires careful planning and a phased approach, but the benefits are substantial:

1. **Reduced code maintenance** as automation logic moves out of application code
2. **Faster updates** to business processes without code deployments
3. **Improved visibility** into automation execution and performance
4. **Greater flexibility** in adapting to changing business requirements
5. **Empowered business users** who can create and modify workflows

By following this guide, you can successfully migrate your legacy automations to the new workflow system with minimal disruption and maximum benefit.

## Additional Resources

- [Workflow API Reference](/docs/api/workflows.md)
- [Advanced Patterns Guide](/docs/workflows/advanced-patterns.md)
- [Custom Extensions Documentation](/docs/workflows/custom-extensions.md)
- [Security Considerations](/docs/workflows/security.md)
- [Comprehensive Tutorial](/docs/workflows/tutorial.md)