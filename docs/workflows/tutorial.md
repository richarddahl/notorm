# Workflow System Tutorial

This tutorial guides you through creating, testing, and deploying workflows in the Workflow Management System. We'll build a practical example: an order processing workflow that sends notifications, updates inventory, and generates reports.

## Prerequisites

Before starting this tutorial, ensure you have:

1. Access to the Admin Dashboard with workflow management permissions
2. Basic understanding of the workflow system concepts (triggers, conditions, actions)
3. Test environment to safely experiment with workflows

## Example Scenario: Order Processing Workflow

In this tutorial, we'll create a workflow that:
1. Triggers when a new order is created or updated
2. Checks order conditions (amount, payment status)
3. Sends notifications to different stakeholders
4. Updates inventory records
5. Integrates with external systems

## Step 1: Accessing the Workflow Designer

1. Log in to the Admin Dashboard
2. Navigate to the "Integration" section
3. Select "Workflows" from the menu
4. Click the "Create Workflow" button

## Step 2: Define Basic Workflow Information

Fill in the basic information for your workflow:

1. **Name**: "Order Processing Workflow"
2. **Description**: "Handles order notifications and inventory updates"
3. **Entity Type**: Select "order" from the dropdown
4. **Trigger Operations**: Select "create" and "update"

Click "Next" to continue to the Conditions tab.

## Step 3: Add Conditions

Let's add conditions to ensure the workflow only runs for valid orders:

1. Click "Add Condition" to create the first condition
2. Set the following values:
   - **Type**: "Field Condition"
   - **Field**: "status"
   - **Operator**: "equals"
   - **Value**: "confirmed"

Click "Add Condition" again to add a second condition:

1. Set the following values:
   - **Type**: "Field Condition"
   - **Field**: "total"
   - **Operator**: "greater than"
   - **Value**: "0"

Click "Add Condition" once more to add a composite condition:

1. Set the following values:
   - **Type**: "Composite Condition"
   - **Operator**: "OR"
   - Add nested conditions:
     - **Type**: "Field Condition"
     - **Field**: "is_priority"
     - **Operator**: "equals"
     - **Value**: "true"
   - Add another nested condition:
     - **Type**: "Field Condition"
     - **Field**: "total"
     - **Operator**: "greater than"
     - **Value**: "500"

This composite condition will match if either the order is marked as priority OR the total amount exceeds $500.

Click "Next" to continue to the Actions tab.

## Step 4: Configure Actions

Now, let's add actions to perform when the conditions are met:

### Action 1: Customer Notification

1. Click "Add Action" to create the first action
2. Set the following values:
   - **Type**: "Notification"
   - **Title**: "Order Confirmation"
   - **Body**: "Thank you for your order #{{order_number}}. Your order has been confirmed and is being processed."
   - **Priority**: "Normal"
   
3. Configure recipients:
   - Click "Add Recipient"
   - **Type**: "User"
   - **Value**: "{{customer_id}}"

### Action 2: Admin Notification

1. Click "Add Action" to create a second action
2. Set the following values:
   - **Type**: "Notification"
   - **Title**: "New Order #{{order_number}}"
   - **Body**: "A new order has been confirmed. Order total: ${{total}}. {% if is_priority %}This is a priority order.{% endif %}"
   - **Priority**: "High"
   
3. Configure recipients:
   - Click "Add Recipient" 
   - **Type**: "Role"
   - **Value**: "order_manager"

### Action 3: Inventory Update

1. Click "Add Action" to create a third action
2. Set the following values:
   - **Type**: "Database"
   - **Operation**: "update"
   - **Target Entity**: "inventory"
   - **Field Mapping**:```

 ```json
 {
   "status": "reserved",
   "reserved_quantity": "{{item_quantity}}",
   "reserved_at": "{{now()}}",
   "order_id": "{{id}}"
 }
 ```
```
   - **Filter**: ```

 ```json
 {
   "product_id": "{{product_id}}"
 }
 ```
```

### Action 4: External System Integration

1. Click "Add Action" to create a fourth action
2. Set the following values:
   - **Type**: "Webhook"
   - **URL**: "https://api.shipping-partner.com/orders"
   - **Method**: "POST"
   - **Headers**:```

 ```json
 {
   "Content-Type": "application/json",
   "Authorization": "Bearer {{env.SHIPPING_API_KEY}}"
 }
 ```
```
   - **Body**:```

 ```json
 {
   "order_id": "{{id}}",
   "customer_name": "{{customer.name}}",
   "shipping_address": "{{shipping_address}}",
   "items": "{{items}}",
   "priority": "{{is_priority}}"
 }
 ```
```

Click "Next" to proceed to the Review tab.

## Step 5: Review and Save

Review all the workflow components:
1. Basic information
2. Trigger settings
3. Conditions
4. Actions and recipients

If everything looks correct, click "Save Workflow" to create your workflow.

## Step 6: Test the Workflow

Before activating the workflow in production, let's test it:

1. On the workflow details page, click the "Simulate" tab
2. Select "create" as the operation
3. Enter test order data:
   ```json
   {```

 "id": "test-order-123",
 "order_number": "ORD-123456",
 "status": "confirmed",
 "total": 750,
 "is_priority": false,
 "customer_id": "CUST-001",
 "customer": {
   "name": "John Doe"
 },
 "shipping_address": "123 Main St, Anytown, US 12345",
 "items": [
   {```

 "product_id": "PROD-001",
 "name": "Premium Widget",
 "quantity": 3,
 "price": 250
```
   }
 ],
 "created_at": "2023-11-15T10:30:00Z"
```
   }
   ```

4. Click "Run Simulation"

The simulation will show:
- Whether conditions were met
- Preview of actions that would be executed
- Recipients who would receive notifications
- Details of database operations and webhook calls

## Step 7: Activate the Workflow

Once you're satisfied with the simulation results:

1. Go back to the workflow details page
2. Set the Status to "Active"
3. Click "Save"

Your workflow is now live and will process orders according to the defined conditions and actions.

## Step 8: Monitor Execution

Monitor your workflow's performance:

1. Go to the "Executions" tab on the workflow details page
2. Review execution history, including:
   - Timestamps
   - Condition evaluation results
   - Action execution status
   - Error messages (if any)

For specific executions, click on the execution ID to see detailed information about that instance.

## Enhancing the Workflow

Now that you have a basic workflow, here are some ways to enhance it:

### Add Conditional Logic

Modify the notification body to include conditional content:

```
Thank you for your order #{{order_number}}.

{% if total > 1000 %}
As a valued customer spending over $1,000, you've earned free shipping!
{% endif %}

{% if items.length > 5 %}
Your bulk order of {{items.length}} items will be processed with priority.
{% endif %}

Estimated delivery: {{estimated_delivery_date | date('MMM D, YYYY')}}
```

### Add Time-Based Conditions

Add a condition that only runs the workflow during business hours:

1. Add a new condition
2. Set the following values:
   - **Type**: "Time Condition"
   - **Days**: "Monday, Tuesday, Wednesday, Thursday, Friday"
   - **Start Time**: "09:00"
   - **End Time**: "17:00"

### Add Follow-up Workflow

Create a follow-up workflow that sends a delivery confirmation:

1. Create a new workflow named "Order Delivery Notification"
2. Set the trigger to activate when an order status is updated to "delivered"
3. Add an email action that sends a delivery confirmation to the customer
4. Include a request for product review

## Best Practices

As you build more workflows, keep these best practices in mind:

1. **Start Simple**: Begin with basic workflows and add complexity gradually
2. **Test Thoroughly**: Always use the simulator before activating workflows
3. **Monitor Performance**: Regularly check execution logs for errors or issues
4. **Use Templates**: Create reusable workflow templates for common patterns
5. **Document**: Keep documentation of your workflows, especially for complex business processes
6. **Security**: Be careful with sensitive data in notifications and webhooks
7. **Optimize**: For high-volume entities, optimize conditions to filter early

## Troubleshooting

If your workflow isn't behaving as expected:

1. **Check Conditions**: Ensure conditions are correctly defined
2. **Verify Trigger**: Confirm the entity type and operations are correct
3. **Test Data**: Use the simulator with different test data to verify behavior
4. **Check Logs**: Review execution logs for errors or warnings
5. **Recipient Configuration**: Verify that recipients are properly configured
6. **Action Order**: Make sure actions are ordered correctly

## Conclusion

You've now created, tested, and activated a comprehensive order processing workflow. This workflow demonstrates key features of the system:

- Multiple conditions with composite logic
- Different action types (notifications, database operations, webhooks)
- Dynamic content with template expressions
- Integration with external systems

As you become more familiar with the workflow system, you can create increasingly sophisticated workflows to automate various business processes across your organization.

## Next Steps

To continue learning about workflows:

1. <!-- TODO: Create API documentation -->Explore the API Documentation to programmatically create and manage workflows (coming soon)
2. <!-- TODO: Create advanced patterns guide -->Learn about Advanced Patterns for complex workflow scenarios (coming soon)
3. <!-- TODO: Create custom extensions guide -->Discover how to extend the system with Custom Extensions (coming soon)
4. <!-- TODO: Create security considerations guide -->Review Security Considerations for production workflows (coming soon)