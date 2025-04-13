# Workflow System Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Workflow Management System. Follow the problem-solution patterns below to quickly address workflow issues.

## Workflow Not Triggering

### Problem: Workflow doesn't execute when expected

#### Possible Causes:

1. **Workflow is inactive**
   - **Symptoms**: No execution records in history
   - **Solution**: Check the workflow status in the dashboard and set it to "active"

2. **Trigger configuration mismatch**
   - **Symptoms**: No execution records despite active status
   - **Solution**: Verify that the entity type and operations match the expected events

3. **Condition evaluation failure**
   - **Symptoms**: Execution records exist but show "conditions not met"
   - **Solution**: Use the simulator to test with different data and adjust conditions

4. **Event not being generated**
   - **Symptoms**: No workflow executions for specific entities
   - **Solution**: Verify that the event is being emitted by the application

### Diagnostic Steps:

1. Check the workflow status in the dashboard
2. View execution history to see if the workflow is triggered but conditions fail
3. Use the simulator with data that should trigger the workflow
4. Check application logs for event generation

### Example Resolution:

```
Workflow: "New Order Notification"
Issue: Not triggering for new orders
Investigation:
- Workflow status: Active ✓
- Execution history: No records ✗
- Simulated with test data: Works ✓
- Checked entity type: "order" ✓
- Checked operations: ["created"] ✗ (Mismatch!)

Solution: Changed operations from ["created"] to ["create"] to match the actual event name
```

## Notifications Not Sent

### Problem: Workflow executes but notifications aren't received

#### Possible Causes:

1. **Recipient configuration error**
   - **Symptoms**: Action shows success but no notifications received
   - **Solution**: Check recipient type and value configuration

2. **Missing recipient data**
   - **Symptoms**: Execution logs show "No recipients found"
   - **Solution**: Verify that the entity data contains the required recipient fields

3. **Template rendering error**
   - **Symptoms**: Logs show template errors
   - **Solution**: Check template syntax in notification title and body

4. **Notification service issues**
   - **Symptoms**: Action fails with service errors
   - **Solution**: Check notification service status

### Diagnostic Steps:

1. Check execution details for the specific workflow run
2. Review the "Action Results" section for error messages
3. Verify the presence of recipient data in the entity
4. Test template rendering with the simulator

### Example Resolution:

```
Workflow: "Order Confirmation"
Issue: Notifications not sent to customers
Investigation:
- Execution status: Success ✓
- Action status: Success ✓
- Recipients found: 0 ✗
- Recipient configuration: type="user", value="customer_id" ✓
- Entity data check: "customer_id" field missing ✗

Solution: The field name in the data is "buyer_id" not "customer_id". Updated recipient value to "{{buyer_id}}"
```

## Webhook Action Failures

### Problem: Webhook actions fail to execute properly

#### Possible Causes:

1. **Invalid URL**
   - **Symptoms**: Action fails with "Invalid URL" error
   - **Solution**: Check URL format and accessibility

2. **Authentication failure**
   - **Symptoms**: Logs show 401/403 responses
   - **Solution**: Verify authentication credentials in headers

3. **Request format issues**
   - **Symptoms**: Logs show 400 Bad Request responses
   - **Solution**: Check payload format and required fields

4. **CORS restrictions**
   - **Symptoms**: Logs show CORS-related errors
   - **Solution**: Configure CORS on the target server or use a proxy

### Diagnostic Steps:

1. Check execution action details for HTTP status codes
2. Review error messages in execution logs
3. Test webhook URL independently using a tool like curl or Postman
4. Verify credentials and payload format

### Example Resolution:

```
Workflow: "Inventory Update"
Issue: Webhook action fails with 401 Unauthorized
Investigation:
- URL correct: ✓
- Headers: Basic authentication included ✓
- Credentials: Password expired ✗

Solution: Updated authentication token in webhook configuration
```

## Template Rendering Errors

### Problem: Templates in notifications/emails fail to render properly

#### Possible Causes:

1. **Missing variables**
   - **Symptoms**: Templates show "{{variable}}" literally in output
   - **Solution**: Ensure variable names match available entity data

2. **Syntax errors**
   - **Symptoms**: Action fails with template parsing errors
   - **Solution**: Fix template syntax (missing brackets, quotes, etc.)

3. **Type errors**
   - **Symptoms**: Errors like "cannot format number as date"
   - **Solution**: Use appropriate filters for data types or check field types

4. **Complex expressions**
   - **Symptoms**: Action fails with evaluation errors
   - **Solution**: Simplify complex expressions or move logic to template helpers

### Diagnostic Steps:

1. Use the simulator to test template rendering
2. Check execution logs for specific template errors
3. Verify available data fields in entity context
4. Test templates with different data types

### Example Resolution:

```
Workflow: "Order Summary"
Issue: Email template shows "{{items}}" literally in output
Investigation:
- Entity data contains "items" field: ✓
- Field type: Array ✓
- Template usage: "{{items}}" (Can't directly render arrays) ✗

Solution: Changed template to use iteration:
```html
{% for item in items %}
- {{item.name}}: {{item.quantity}} x ${{item.price}}
{% endfor %}
```
```

## Database Action Issues

### Problem: Database actions fail to execute correctly

#### Possible Causes:

1. **Permission issues**
   - **Symptoms**: Action fails with permission errors
   - **Solution**: Check workflow service account permissions

2. **Invalid field mapping**
   - **Symptoms**: Action fails with "unknown column" errors
   - **Solution**: Verify field names in mapping match database schema

3. **Data type mismatches**
   - **Symptoms**: Action fails with type conversion errors
   - **Solution**: Ensure data types match schema expectations

4. **Constraint violations**
   - **Symptoms**: Action fails with constraint errors
   - **Solution**: Check for unique constraints, foreign keys, or other violations

### Diagnostic Steps:

1. Check execution action details for specific database errors
2. Review field mappings against entity schema
3. Verify required fields are provided
4. Test expressions used in field mappings

### Example Resolution:

```
Workflow: "Product Update"
Issue: Database action fails with constraint violation
Investigation:
- Target entity: "product_inventory" ✓
- Operation: "update" ✓
- Field mapping: quantity="{{units}}" ✓
- Error: "NOT NULL constraint failed: product_inventory.last_updated" ✗

Solution: Added missing required field to mapping: last_updated="{{now()}}"
```

## Performance Issues

### Problem: Workflows execute slowly or cause system performance problems

#### Possible Causes:

1. **Complex condition evaluation**
   - **Symptoms**: Long delays between trigger and action execution
   - **Solution**: Simplify conditions or optimize evaluation order

2. **Inefficient database queries**
   - **Symptoms**: Slow database action execution
   - **Solution**: Optimize queries, add indexes, or limit result sizes

3. **High volume execution**
   - **Symptoms**: System slowdown during peak events
   - **Solution**: Add rate limiting or batch processing for high-volume entities

4. **Resource-intensive actions**
   - **Symptoms**: Individual actions take excessive time
   - **Solution**: Optimize action implementation or move to background processing

### Diagnostic Steps:

1. Check execution timing metrics in logs
2. Identify slow components (condition evaluation, specific actions)
3. Monitor system resource usage during workflow execution
4. Test with different volumes of data

### Example Resolution:

```
Workflow: "Daily Report Generation"
Issue: Takes over 10 minutes to execute, causing API timeouts
Investigation:
- Database query retrieving all records without limit ✗
- Complex template with many iterations ✗
- Large number of recipients (>500) ✗

Solution:
1. Added pagination to database query (limit=1000, process in batches)
2. Simplified template by pre-aggregating data
3. Grouped recipients by department and sent one email per department
Result: Execution time reduced to 45 seconds
```

## Complex Workflows

### Problem: Complex workflow logic is difficult to implement or debug

#### Possible Causes:

1. **Too many conditions in one workflow**
   - **Symptoms**: Difficult to understand or manage
   - **Solution**: Break into multiple simpler workflows

2. **Stateful process requirements**
   - **Symptoms**: Need to track state between events
   - **Solution**: Use transition entities or database for state management

3. **Circular dependencies**
   - **Symptoms**: Workflows triggering each other in loops
   - **Solution**: Redesign workflow dependencies or add guards

4. **Order-dependent actions**
   - **Symptoms**: Actions need specific execution order
   - **Solution**: Use action ordering or chained workflows

### Diagnostic Steps:

1. Create a diagram of workflow dependencies
2. Identify complex conditions that could be simplified
3. Look for circular references between workflows
4. Check for state management needs

### Example Resolution:

```
Workflow: "Order Processing"
Issue: Complex state management across multiple steps
Investigation:
- Single workflow with 12 conditions and 8 actions ✗
- Needs to track state between different events ✗
- Actions depend on previous action results ✗

Solution: Split into multiple workflows:
1. "Order Validation" - Triggered on order creation
2. "Payment Processing" - Triggered by validation workflow
3. "Fulfillment" - Triggered by payment workflow
4. "Shipping" - Triggered by fulfillment workflow
Each workflow updates a state field that triggers the next workflow.
```

## Template Helpers and Tips

### Common Template Patterns

Use these patterns to solve common template challenges:

#### Conditional Formatting

```
{% if value > 1000 %}
  <span style="color: green">{{value | currency}}</span>
{% else %}
  <span style="color: black">{{value | currency}}</span>
{% endif %}
```

#### Default Values

```
{{ customer_name | default('Valued Customer') }}
```

#### Date Formatting

```
{{ created_at | date('MMM D, YYYY') }}
```

#### List Formatting

```
<ul>
{% for item in items %}
  <li>{{ item.name }}: {{ item.quantity }} x {{ item.price | currency }}</li>
{% endfor %}
</ul>
```

#### Conditional Sections

```
{% if items.length > 0 %}
  <h3>Order Items</h3>
  <ul>
  {% for item in items %}
    <li>{{ item.name }}</li>
  {% endfor %}
  </ul>
{% else %}
  <p>No items in this order.</p>
{% endif %}
```

## System Administration Issues

### Problem: Administrative or system-level issues with the workflow engine

#### Possible Causes:

1. **Insufficient resources**
   - **Symptoms**: Failed workflows, system timeouts
   - **Solution**: Increase memory/CPU allocation for workflow services

2. **Database connection issues**
   - **Symptoms**: Database-related errors in logs
   - **Solution**: Check connection pool settings and database health

3. **Queue overflow**
   - **Symptoms**: Delayed workflow execution
   - **Solution**: Increase worker count or queue capacity

4. **High error rates**
   - **Symptoms**: Many failures across different workflows
   - **Solution**: Check for system-wide issues or configuration problems

### Diagnostic Steps:

1. Monitor system metrics (CPU, memory, disk usage)
2. Check logs for recurring error patterns
3. Verify database connectivity and performance
4. Test basic workflow functionality

### Example Resolution:

```
Issue: All workflows failing with database timeout errors
Investigation:
- System CPU usage: Normal ✓
- Memory usage: Normal ✓
- Database connections maxed out ✗
- Connection pool size: 10 ✗

Solution: Increased database connection pool size to 50 and added connection timeout handling
```

## Troubleshooting Commands

Use these commands to debug workflow issues:

### View Recent Workflow Executions

```sql
SELECT 
    w.name AS workflow_name,
    e.status,
    e.started_at,
    e.completed_at,
    e.duration_ms,
    e.entity_id,
    e.entity_type,
    e.operation
FROM 
    workflow_executions e
JOIN 
    workflows w ON e.workflow_id = w.id
ORDER BY 
    e.started_at DESC
LIMIT 100;
```

### Find Failed Actions

```sql
SELECT 
    w.name AS workflow_name,
    e.entity_id,
    a.type AS action_type,
    a.status AS action_status,
    a.error,
    a.started_at
FROM 
    workflow_action_results a
JOIN 
    workflow_executions e ON a.execution_id = e.id
JOIN 
    workflows w ON e.workflow_id = w.id
WHERE 
    a.status = 'failure'
ORDER BY 
    a.started_at DESC
LIMIT 100;
```

### Check Workflow Trigger Counts

```sql
SELECT 
    w.name AS workflow_name,
    COUNT(e.id) AS execution_count,
    SUM(CASE WHEN e.conditions_result THEN 1 ELSE 0 END) AS conditions_met_count,
    SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN e.status = 'failure' THEN 1 ELSE 0 END) AS failure_count
FROM 
    workflows w
LEFT JOIN 
    workflow_executions e ON w.id = e.workflow_id
WHERE 
    e.started_at > NOW() - INTERVAL '24 HOURS'
GROUP BY 
    w.id, w.name
ORDER BY 
    execution_count DESC;
```

## Getting Further Help

If you've followed the troubleshooting steps above and still encounter issues:

1. **Check Documentation**:
   - Review the [API Reference](/docs/api/workflows.md)
   - See [Advanced Patterns](/docs/workflows/advanced-patterns.md) for complex workflow solutions

2. **System Logs**:
   - Check application logs for detailed error information
   - Review database logs for query-related issues

3. **Get Support**:
   - Contact the system administrator for your organization
   - Submit detailed information including:
     - Workflow ID and name
     - Execution ID for failed executions
     - Exact error messages
     - Steps to reproduce the issue
     - Any recent changes to the workflow

4. **Community Resources**:
   - Check the knowledge base for similar issues
   - Search community forums for solutions

Remember to provide specific error messages and context when seeking help, as this significantly improves the chances of quick resolution.