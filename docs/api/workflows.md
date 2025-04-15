# Workflow System API Reference

This document provides a comprehensive reference for the Workflow System API endpoints, including request and response formats, authentication requirements, and examples.

## Base URL

All API endpoints are prefixed with `/api/workflows`.

## Authentication

All API endpoints require authentication using a valid JWT token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## Workflow Management

### List Workflows

Retrieves a list of all workflows, optionally filtered by status.

**Endpoint:** `GET /api/workflows/`  
**Query Parameters:**
- `status` (optional): Filter by workflow status (active, inactive, draft)

**Response:** Array of workflow definitions
```json
[
  {```

"id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
"name": "New Product Notification",
"description": "Notifies sales team when new products are added",
"status": "active",
"version": 1,
"trigger": {
  "entity_type": "product",
  "operations": ["create"]
},
"conditions": [
  {```

"type": "field",
"field": "category",
"operator": "eq",
"value": "electronics"
```
  }
],
"actions": [
  {```

"type": "notification",
"title": "New Electronics Product",
"body": "A new product has been added: {{name}}",
"priority": "normal",
"recipients": [
  {
    "type": "role",
    "value": "sales_manager"
  }
]
```
  }
],
"created_at": "2023-11-15T14:30:22.123Z",
"updated_at": "2023-11-15T14:30:22.123Z"
```
  }
]
```

### Get Workflow

Retrieves a single workflow by ID.

**Endpoint:** `GET /api/workflows/{workflow_id}`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow to retrieve

**Response:** Workflow definition
```json
{
  "id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
  "name": "New Product Notification",
  "description": "Notifies sales team when new products are added",
  "status": "active",
  "version": 1,
  "trigger": {```

"entity_type": "product",
"operations": ["create"]
```
  },
  "conditions": [```

{
  "type": "field",
  "field": "category",
  "operator": "eq",
  "value": "electronics"
}
```
  ],
  "actions": [```

{
  "type": "notification",
  "title": "New Electronics Product",
  "body": "A new product has been added: {{name}}",
  "priority": "normal",
  "recipients": [```

{
  "type": "role",
  "value": "sales_manager"
}
```
  ]
}
```
  ],
  "created_at": "2023-11-15T14:30:22.123Z",
  "updated_at": "2023-11-15T14:30:22.123Z"
}
```

### Create Workflow

Creates a new workflow.

**Endpoint:** `POST /api/workflows/`  
**Request Body:** Workflow definition schema
```json
{
  "name": "Price Change Alert",
  "description": "Notifies customers when product prices decrease",
  "status": "active",
  "trigger": {```

"entity_type": "product",
"operations": ["update"]
```
  },
  "conditions": [```

{
  "type": "field",
  "field": "price",
  "operator": "decreased"
}
```
  ],
  "actions": [```

{
  "type": "email",
  "subject": "Price Drop Alert",
  "body": "Good news! The price of {{name}} has dropped to {{price}}.",
  "recipients": [```

{
  "type": "dynamic",
  "value": "product.interested_customers"
}
```
  ]
}
```
  ]
}
```

**Response:** Created workflow ID
```json
{
  "id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M"
}
```

### Update Workflow

Updates an existing workflow.

**Endpoint:** `PUT /api/workflows/{workflow_id}`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow to update

**Request Body:** Complete workflow definition schema (same as Create)

**Response:** Updated workflow ID
```json
{
  "id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M"
}
```

### Delete Workflow

Deletes a workflow.

**Endpoint:** `DELETE /api/workflows/{workflow_id}`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow to delete

**Response:** Success indicator
```json
{
  "success": true
}
```

### Update Workflow Status

Updates the status of a workflow (activate/deactivate).

**Endpoint:** `PATCH /api/workflows/{workflow_id}/status`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow to update

**Request Body:** Status update
```json
{
  "status": "active"  // or "inactive"
}
```

**Response:** Updated workflow ID
```json
{
  "id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M"
}
```

## Workflow Execution

### List Executions

Retrieves a list of workflow execution logs, optionally filtered.

**Endpoint:** `GET /api/workflows/executions`  
**Query Parameters:**
- `workflow_id` (optional): Filter by workflow ID
- `execution_status` (optional): Filter by execution status (success, failure, partial)
- `limit` (optional, default=100): Maximum number of executions to return
- `offset` (optional, default=0): Number of executions to skip

**Response:** Array of workflow execution logs
```json
[
  {```

"id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
"workflow_id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
"workflow_name": "New Product Notification",
"status": "success",
"entity_type": "product",
"entity_id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
"operation": "create",
"started_at": "2023-11-15T14:30:22.123Z",
"completed_at": "2023-11-15T14:30:23.456Z",
"duration_ms": 1333,
"conditions_result": true,
"actions_total": 1,
"actions_success": 1,
"actions_failed": 0,
"action_results": [
  {```

"action_id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
"type": "notification",
"status": "success",
"started_at": "2023-11-15T14:30:22.789Z",
"completed_at": "2023-11-15T14:30:23.123Z",
"duration_ms": 334,
"recipients_count": 3,
"details": "Notification sent to 3 recipients"
```
  }
]
```
  }
]
```

### Get Execution Details

Retrieves detailed information about a specific workflow execution.

**Endpoint:** `GET /api/workflows/{workflow_id}/executions/{execution_id}`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow
- `execution_id`: The ID of the execution to retrieve

**Response:** Workflow execution log (same structure as in List Executions)

### Retry Failed Action

Retries a failed workflow action.

**Endpoint:** `POST /api/workflows/{workflow_id}/executions/{execution_id}/actions/{action_id}/retry`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow
- `execution_id`: The ID of the execution
- `action_id`: The ID of the action to retry

**Response:** Success indicator
```json
{
  "success": true
}
```

## Workflow Simulation

### Simulate Workflow

Simulates a workflow execution with test data.

**Endpoint:** `POST /api/workflows/{workflow_id}/simulate`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow to simulate

**Request Body:** Simulation request
```json
{
  "operation": "create",
  "entity_data": {```

"id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
"name": "Smartphone XYZ",
"category": "electronics",
"price": 799.99,
"description": "Latest smartphone with advanced features"
```
  }
}
```

**Response:** Simulation results
```json
{
  "workflow_id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
  "workflow_name": "New Product Notification",
  "status": "success",
  "trigger": {```

"entity_type": "product",
"operations": ["create"]
```
  },
  "conditions": [```

{
  "type": "field",
  "field": "category",
  "operator": "eq",
  "value": "electronics",
  "result": true,
  "description": "Field 'category' equals 'electronics'"
}
```
  ],
  "conditions_result": true,
  "actions": [```

{
  "type": "notification",
  "status": "success",
  "config": {```

"title": "New Electronics Product",
"body": "A new product has been added: Smartphone XYZ"
```
  },
  "recipients": [```

{
  "type": "role",
  "value": "sales_manager",
  "resolved_users": ["user1", "user2", "user3"]
}
```
  ],
  "result": {```

"recipients_count": 3,
"details": "Notification would be sent to 3 recipients"
```
  }
}
```
  ],
  "simulation_time": "2023-11-15T14:30:22.123Z"
}
```

## Configuration Endpoints

### Entity Types

Retrieves a list of available entity types for workflow triggers.

**Endpoint:** `GET /api/workflows/entity-types`  
**Response:** Array of entity types
```json
[
  { "id": "product", "label": "Product" },
  { "id": "order", "label": "Order" },
  { "id": "customer", "label": "Customer" }
]
```

### Entity Fields

Retrieves a list of fields for a specific entity type.

**Endpoint:** `GET /api/workflows/entity-types/{entity_type}/fields`  
**Path Parameters:**
- `entity_type`: The entity type to get fields for

**Response:** Array of entity fields
```json
[
  {```

"id": "name",
"label": "Name",
"type": "string",
"required": true
```
  },
  {```

"id": "category",
"label": "Category",
"type": "string",
"required": true
```
  },
  {```

"id": "price",
"label": "Price",
"type": "number",
"required": true
```
  }
]
```

### Action Types

Retrieves a list of available action types.

**Endpoint:** `GET /api/workflows/action-types`  
**Response:** Array of action types
```json
[
  {```

"id": "notification",
"label": "In-App Notification",
"config_schema": {
  "title": { "type": "string", "required": true },
  "body": { "type": "string", "required": true },
  "priority": { "type": "string", "required": false, "default": "normal" }
},
"requires_recipients": true
```
  },
  {```

"id": "email",
"label": "Email Notification",
"config_schema": {
  "subject": { "type": "string", "required": true },
  "body": { "type": "string", "required": true },
  "template": { "type": "string", "required": false }
},
"requires_recipients": true
```
  },
  {```

"id": "webhook",
"label": "Webhook",
"config_schema": {
  "url": { "type": "string", "required": true },
  "method": { "type": "string", "required": false, "default": "POST" }
},
"requires_recipients": false
```
  }
]
```

### Condition Types

Retrieves a list of available condition types.

**Endpoint:** `GET /api/workflows/condition-types`  
**Response:** Array of condition types
```json
[
  {```

"id": "field",
"label": "Field Condition",
"config_schema": {
  "field": { "type": "string", "required": true },
  "operator": { "type": "string", "required": true },
  "value": { "type": "string", "required": false }
}
```
  },
  {```

"id": "time",
"label": "Time Condition",
"config_schema": {
  "days": { "type": "array", "required": false },
  "start_time": { "type": "string", "required": false },
  "end_time": { "type": "string", "required": false }
}
```
  },
  {```

"id": "role",
"label": "Role Condition",
"config_schema": {
  "role": { "type": "string", "required": true }
}
```
  }
]
```

### Recipient Types

Retrieves a list of available recipient types.

**Endpoint:** `GET /api/workflows/recipient-types`  
**Response:** Array of recipient types
```json
[
  {```

"id": "user",
"label": "Specific User",
"config_schema": {
  "value": { "type": "string", "required": true }
}
```
  },
  {```

"id": "role",
"label": "User Role",
"config_schema": {
  "value": { "type": "string", "required": true }
}
```
  },
  {```

"id": "department",
"label": "Department",
"config_schema": {
  "value": { "type": "string", "required": true }
}
```
  },
  {```

"id": "dynamic",
"label": "Dynamic Recipients",
"config_schema": {
  "value": { "type": "string", "required": true }
}
```
  }
]
```

## Error Handling

The API follows standard HTTP status codes for errors:

- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses include a detail message:

```json
{
  "detail": "Workflow with ID 01HFGB2D5NSJWZ3K4P6Q7R8T9M not found"
}
```

## Pagination

For endpoints that return lists, standard offset-based pagination is supported through query parameters:

- `limit`: Maximum number of items to return (default: 100)
- `offset`: Number of items to skip (default: 0)

## Data Types

### WorkflowDefinitionSchema

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the workflow |
| name | string | Name of the workflow |
| description | string | Optional description of the workflow |
| status | string | Status of the workflow (active, inactive, draft) |
| version | integer | Version number of the workflow |
| trigger | WorkflowTriggerSchema | The trigger configuration for the workflow |
| conditions | array | List of condition configurations for the workflow |
| actions | array | List of action configurations for the workflow |
| created_at | string | Timestamp when the workflow was created |
| updated_at | string | Timestamp when the workflow was last updated |

### WorkflowTriggerSchema

| Field | Type | Description |
|-------|------|-------------|
| entity_type | string | The entity type this trigger applies to |
| operations | array | The operations that will trigger the workflow (create, update, delete) |

### WorkflowConditionSchema

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the condition |
| type | string | The type of condition (field, time, role, composite) |
| field | string | The field to evaluate for field conditions |
| operator | string | The operator for field conditions (eq, ne, gt, lt, etc.) |
| value | string | The value for field conditions |
| config | object | Additional configuration for the condition |
| order | integer | The order of evaluation for the condition |

### WorkflowActionSchema

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the action |
| type | string | The type of action (notification, email, webhook, database) |
| title | string | The title for notification actions |
| body | string | The body for notification and email actions |
| subject | string | The subject for email actions |
| url | string | The URL for webhook actions |
| method | string | The HTTP method for webhook actions |
| priority | string | The priority for notification actions |
| template | string | The template for email actions |
| operation | string | The operation for database actions |
| target_entity | string | The target entity for database actions |
| field_mapping | object | Field mapping for database actions |
| config | object | Additional configuration for the action |
| order | integer | The order of execution for the action |
| recipients | array | Recipients for the action |

### WorkflowRecipientSchema

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the recipient |
| type | string | The type of recipient (user, role, department, dynamic) |
| value | string | The value for the recipient (user ID, role name, etc.) |
| action_id | string | The action this recipient is associated with |

### WorkflowExecutionLogSchema

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the execution log |
| workflow_id | string | The ID of the workflow that was executed |
| workflow_name | string | The name of the workflow that was executed |
| status | string | The status of the execution (success, failure, partial) |
| entity_type | string | The entity type that triggered the workflow |
| entity_id | string | The ID of the entity that triggered the workflow |
| operation | string | The operation that triggered the workflow |
| started_at | string | Timestamp when the execution started |
| completed_at | string | Timestamp when the execution completed |
| duration_ms | integer | The duration of the execution in milliseconds |
| conditions_result | boolean | Whether all conditions passed |
| actions_total | integer | The total number of actions |
| actions_success | integer | The number of successful actions |
| actions_failed | integer | The number of failed actions |
| action_results | array | The results of the action executions |

## Template Variables

Workflow actions (notifications, emails) support template variables using the double-curly brace syntax:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{entity_field}}` | Any field from the entity that triggered the workflow | `{{name}}`, `{{price}}`, `{{category}}` |
| `{{entity_id}}` | The ID of the entity that triggered the workflow | `{{entity_id}}` |
| `{{operation}}` | The operation that triggered the workflow | `{{operation}}` |
| `{{workflow_id}}` | The ID of the workflow | `{{workflow_id}}` |
| `{{workflow_name}}` | The name of the workflow | `{{workflow_name}}` |
| `{{execution_id}}` | The ID of the execution | `{{execution_id}}` |
| `{{timestamp}}` | The current timestamp | `{{timestamp}}` |

## Rate Limiting

API requests are rate-limited to prevent abuse:
- 100 requests per minute for workflow management endpoints
- 300 requests per minute for configuration endpoints
- 500 requests per minute for workflow execution endpoints

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2023-11-10 | Initial API release |
| 1.1 | 2023-12-15 | Added simulation endpoint and recipient types |