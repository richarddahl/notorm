# Workflow System API Reference

This document provides a comprehensive reference for the Workflow System API endpoints following the domain-driven design approach. It includes request and response formats, authentication requirements, and integration examples.

## Overview

The Workflow module follows the domain-driven design (DDD) architecture pattern with clear separation of:

- **Domain Entities**: Core business objects with behavior
- **DTOs (Data Transfer Objects)**: Objects for API serialization/deserialization
- **Schema Managers**: Components responsible for conversion between entities and DTOs
- **Repositories**: Data access layer for persisting workflow entities
- **Services**: Business logic for workflow operations
- **API Integration**: RESTful endpoints for workflow management

## Base URL

All API endpoints are prefixed with `/api/v1/workflows`.

## Authentication

All API endpoints require authentication using a valid JWT token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## Workflow Definition Management

### List Workflow Definitions

Retrieves a paginated list of workflow definitions, optionally filtered by status.

**Endpoint:** `GET /api/v1/workflows/definitions`  
**Query Parameters:**
- `status` (optional): Filter by workflow status (DRAFT, ACTIVE, INACTIVE, ARCHIVED)
- `name` (optional): Filter by name (case-insensitive partial match)
- `limit` (optional, default=50): Maximum number of items to return
- `offset` (optional, default=0): Number of items to skip

**Response:** Paginated list of workflow definitions
```json
{
  "items": [
    {
      "id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
      "name": "New Product Notification",
      "description": "Notifies sales team when new products are added",
      "status": "ACTIVE",
      "version": "1.0.0",
      "trigger": {
        "id": "01HFGC3F6PNRWZ3K4P6Q7R8T9N",
        "entity_type": "product",
        "operations": ["CREATE"],
        "created_at": "2023-11-15T14:30:22.123Z",
        "updated_at": "2023-11-15T14:30:22.123Z"
      },
      "conditions": [
        {
          "id": "01HFGD4G7QPSXZ3K4P6Q7R8T9P",
          "type": "FIELD",
          "field": "category",
          "operator": "EQUALS",
          "value": "electronics",
          "order": 1,
          "created_at": "2023-11-15T14:30:22.123Z",
          "updated_at": "2023-11-15T14:30:22.123Z"
        }
      ],
      "actions": [
        {
          "id": "01HFGE5H8RQTYZ3K4P6Q7R8T9Q",
          "type": "NOTIFICATION",
          "config": {
            "title": "New Electronics Product",
            "body": "A new product has been added: {{name}}",
            "priority": "NORMAL"
          },
          "order": 1,
          "recipients": [
            {
              "id": "01HFGF6J9SRUZ3K4P6Q7R8T9R",
              "type": "ROLE",
              "value": "sales_manager",
              "created_at": "2023-11-15T14:30:22.123Z",
              "updated_at": "2023-11-15T14:30:22.123Z"
            }
          ],
          "created_at": "2023-11-15T14:30:22.123Z",
          "updated_at": "2023-11-15T14:30:22.123Z"
        }
      ],
      "created_at": "2023-11-15T14:30:22.123Z",
      "updated_at": "2023-11-15T14:30:22.123Z"
    }
  ],
  "total": 24,
  "limit": 50,
  "offset": 0
}
```

### Get Workflow Definition

Retrieves a single workflow definition by ID.

**Endpoint:** `GET /api/v1/workflows/definitions/{workflow_id}`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow definition to retrieve

**Response:** Complete workflow definition
```json
{
  "id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
  "name": "New Product Notification",
  "description": "Notifies sales team when new products are added",
  "status": "ACTIVE",
  "version": "1.0.0",
  "trigger": {
    "id": "01HFGC3F6PNRWZ3K4P6Q7R8T9N",
    "entity_type": "product",
    "operations": ["CREATE"],
    "created_at": "2023-11-15T14:30:22.123Z",
    "updated_at": "2023-11-15T14:30:22.123Z"
  },
  "conditions": [
    {
      "id": "01HFGD4G7QPSXZ3K4P6Q7R8T9P",
      "type": "FIELD",
      "field": "category",
      "operator": "EQUALS",
      "value": "electronics",
      "order": 1,
      "created_at": "2023-11-15T14:30:22.123Z",
      "updated_at": "2023-11-15T14:30:22.123Z"
    }
  ],
  "actions": [
    {
      "id": "01HFGE5H8RQTYZ3K4P6Q7R8T9Q",
      "type": "NOTIFICATION",
      "config": {
        "title": "New Electronics Product",
        "body": "A new product has been added: {{name}}",
        "priority": "NORMAL"
      },
      "order": 1,
      "recipients": [
        {
          "id": "01HFGF6J9SRUZ3K4P6Q7R8T9R",
          "type": "ROLE",
          "value": "sales_manager",
          "created_at": "2023-11-15T14:30:22.123Z",
          "updated_at": "2023-11-15T14:30:22.123Z"
        }
      ],
      "created_at": "2023-11-15T14:30:22.123Z",
      "updated_at": "2023-11-15T14:30:22.123Z"
    }
  ],
  "created_at": "2023-11-15T14:30:22.123Z",
  "updated_at": "2023-11-15T14:30:22.123Z"
}
```

### Create Workflow Definition

Creates a new workflow definition.

**Endpoint:** `POST /api/v1/workflows/definitions`  
**Request Body:** WorkflowDefCreateDto
```json
{
  "name": "Price Change Alert",
  "description": "Notifies customers when product prices decrease",
  "status": "ACTIVE",
  "version": "1.0.0",
  "trigger": {
    "entity_type": "product",
    "operations": ["UPDATE"]
  },
  "conditions": [
    {
      "type": "FIELD",
      "field": "price",
      "operator": "DECREASED",
      "order": 1
    }
  ],
  "actions": [
    {
      "type": "EMAIL",
      "config": {
        "subject": "Price Drop Alert",
        "body": "Good news! The price of {{name}} has dropped to {{price}}.",
        "template": "price_drop"
      },
      "order": 1,
      "recipients": [
        {
          "type": "DYNAMIC",
          "value": "product.interested_customers"
        }
      ]
    }
  ]
}
```

**Response:** Created workflow definition with ID
```json
{
  "id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
  "name": "Price Change Alert",
  "description": "Notifies customers when product prices decrease",
  "status": "ACTIVE",
  "version": "1.0.0",
  "trigger": {
    "id": "01HFGC3F6PNRWZ3K4P6Q7R8T9N",
    "entity_type": "product",
    "operations": ["UPDATE"],
    "created_at": "2023-11-15T14:30:22.123Z",
    "updated_at": "2023-11-15T14:30:22.123Z"
  },
  "conditions": [
    {
      "id": "01HFGD4G7QPSXZ3K4P6Q7R8T9P",
      "type": "FIELD",
      "field": "price",
      "operator": "DECREASED",
      "order": 1,
      "created_at": "2023-11-15T14:30:22.123Z",
      "updated_at": "2023-11-15T14:30:22.123Z"
    }
  ],
  "actions": [
    {
      "id": "01HFGE5H8RQTYZ3K4P6Q7R8T9Q",
      "type": "EMAIL",
      "config": {
        "subject": "Price Drop Alert",
        "body": "Good news! The price of {{name}} has dropped to {{price}}.",
        "template": "price_drop"
      },
      "order": 1,
      "recipients": [
        {
          "id": "01HFGF6J9SRUZ3K4P6Q7R8T9R",
          "type": "DYNAMIC",
          "value": "product.interested_customers",
          "created_at": "2023-11-15T14:30:22.123Z",
          "updated_at": "2023-11-15T14:30:22.123Z"
        }
      ],
      "created_at": "2023-11-15T14:30:22.123Z",
      "updated_at": "2023-11-15T14:30:22.123Z"
    }
  ],
  "created_at": "2023-11-15T14:30:22.123Z",
  "updated_at": "2023-11-15T14:30:22.123Z"
}
```

### Update Workflow Definition

Updates an existing workflow definition.

**Endpoint:** `PUT /api/v1/workflows/definitions/{workflow_id}`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow definition to update

**Request Body:** WorkflowDefUpdateDto (same structure as WorkflowDefCreateDto)

**Response:** Updated workflow definition with ID (same structure as Create response)

### Delete Workflow Definition

Deletes a workflow definition.

**Endpoint:** `DELETE /api/v1/workflows/definitions/{workflow_id}`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow definition to delete

**Response:** Success indicator
```json
{
  "success": true,
  "message": "Workflow definition deleted successfully"
}
```

### Update Workflow Definition Status

Updates the status of a workflow definition.

**Endpoint:** `PATCH /api/v1/workflows/definitions/{workflow_id}/status`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow definition to update

**Request Body:** Status update
```json
{
  "status": "ACTIVE"  // ACTIVE, INACTIVE, ARCHIVED
}
```

**Response:** Updated workflow definition (same structure as Get response)

## Workflow Execution Records

### List Execution Records

Retrieves a paginated list of workflow execution records, optionally filtered.

**Endpoint:** `GET /api/v1/workflows/executions`  
**Query Parameters:**
- `workflow_id` (optional): Filter by workflow definition ID
- `status` (optional): Filter by execution status (SUCCESS, FAILURE, PARTIAL)
- `entity_type` (optional): Filter by entity type
- `entity_id` (optional): Filter by entity ID
- `from_date` (optional): Filter by start date (ISO format)
- `to_date` (optional): Filter by end date (ISO format)
- `limit` (optional, default=50): Maximum number of items to return
- `offset` (optional, default=0): Number of items to skip

**Response:** Paginated list of workflow execution records
```json
{
  "items": [
    {
      "id": "01HFGG7K0TSVZ3K4P6Q7R8T9S",
      "workflow_id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
      "workflow_name": "New Product Notification",
      "status": "SUCCESS",
      "entity_type": "product",
      "entity_id": "01HFGH8L1UTWZ3K4P6Q7R8T9T",
      "operation": "CREATE",
      "started_at": "2023-11-15T14:30:22.123Z",
      "completed_at": "2023-11-15T14:30:23.456Z",
      "duration_ms": 1333,
      "conditions_result": true,
      "actions_total": 1,
      "actions_success": 1,
      "actions_failed": 0,
      "action_results": [
        {
          "action_id": "01HFGE5H8RQTYZ3K4P6Q7R8T9Q",
          "type": "NOTIFICATION",
          "status": "SUCCESS",
          "started_at": "2023-11-15T14:30:22.789Z",
          "completed_at": "2023-11-15T14:30:23.123Z",
          "duration_ms": 334,
          "recipients_count": 3,
          "details": "Notification sent to 3 recipients"
        }
      ]
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0
}
```

### Get Execution Record Details

Retrieves detailed information about a specific workflow execution.

**Endpoint:** `GET /api/v1/workflows/executions/{execution_id}`  
**Path Parameters:**
- `execution_id`: The ID of the execution record to retrieve

**Response:** Complete workflow execution record (same structure as in List Executions)

### Retry Failed Action

Retries a failed workflow action.

**Endpoint:** `POST /api/v1/workflows/executions/{execution_id}/actions/{action_id}/retry`  
**Path Parameters:**
- `execution_id`: The ID of the execution record
- `action_id`: The ID of the action to retry

**Response:** Success indicator
```json
{
  "success": true,
  "message": "Action retry initiated",
  "action_id": "01HFGE5H8RQTYZ3K4P6Q7R8T9Q"
}
```

## Workflow Simulation

### Simulate Workflow Execution

Simulates a workflow execution with test data without performing actual actions.

**Endpoint:** `POST /api/v1/workflows/definitions/{workflow_id}/simulate`  
**Path Parameters:**
- `workflow_id`: The ID of the workflow definition to simulate

**Request Body:** Simulation request
```json
{
  "operation": "CREATE",
  "entity_data": {
    "id": "01HFGH8L1UTWZ3K4P6Q7R8T9T",
    "name": "Smartphone XYZ",
    "category": "electronics",
    "price": 799.99,
    "description": "Latest smartphone with advanced features"
  }
}
```

**Response:** Simulation results
```json
{
  "workflow_id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M",
  "workflow_name": "New Product Notification",
  "status": "SUCCESS",
  "trigger": {
    "entity_type": "product",
    "operations": ["CREATE"]
  },
  "conditions": [
    {
      "type": "FIELD",
      "field": "category",
      "operator": "EQUALS",
      "value": "electronics",
      "result": true,
      "description": "Field 'category' equals 'electronics'"
    }
  ],
  "conditions_result": true,
  "actions": [
    {
      "type": "NOTIFICATION",
      "status": "SUCCESS",
      "config": {
        "title": "New Electronics Product",
        "body": "A new product has been added: Smartphone XYZ"
      },
      "recipients": [
        {
          "type": "ROLE",
          "value": "sales_manager",
          "resolved_users": ["user1", "user2", "user3"]
        }
      ],
      "result": {
        "recipients_count": 3,
        "details": "Notification would be sent to 3 recipients"
      }
    }
  ],
  "simulation_time": "2023-11-15T14:30:22.123Z"
}
```

## Configuration Endpoints

### List Entity Types

Retrieves a list of available entity types for workflow triggers.

**Endpoint:** `GET /api/v1/workflows/config/entity-types`  
**Response:** Array of entity types
```json
[
  { "id": "product", "name": "Product", "description": "Product entity" },
  { "id": "order", "name": "Order", "description": "Order entity" },
  { "id": "customer", "name": "Customer", "description": "Customer entity" }
]
```

### List Entity Fields

Retrieves a list of fields for a specific entity type.

**Endpoint:** `GET /api/v1/workflows/config/entity-types/{entity_type}/fields`  
**Path Parameters:**
- `entity_type`: The entity type to get fields for

**Response:** Array of entity fields
```json
[
  {
    "id": "name",
    "name": "Name",
    "type": "STRING",
    "required": true,
    "description": "Product name"
  },
  {
    "id": "category",
    "name": "Category",
    "type": "STRING",
    "required": true,
    "description": "Product category"
  },
  {
    "id": "price",
    "name": "Price",
    "type": "DECIMAL",
    "required": true,
    "description": "Product price"
  }
]
```

### List Action Types

Retrieves a list of available action types.

**Endpoint:** `GET /api/v1/workflows/config/action-types`  
**Response:** Array of action types
```json
[
  {
    "id": "NOTIFICATION",
    "name": "In-App Notification",
    "description": "Sends in-app notifications to users",
    "config_schema": {
      "title": { "type": "STRING", "required": true, "description": "Notification title" },
      "body": { "type": "STRING", "required": true, "description": "Notification body" },
      "priority": { 
        "type": "ENUM", 
        "required": false, 
        "default": "NORMAL",
        "options": ["LOW", "NORMAL", "HIGH", "URGENT"]
      }
    },
    "requires_recipients": true
  },
  {
    "id": "EMAIL",
    "name": "Email Notification",
    "description": "Sends email notifications to users",
    "config_schema": {
      "subject": { "type": "STRING", "required": true, "description": "Email subject" },
      "body": { "type": "STRING", "required": true, "description": "Email body (supports HTML)" },
      "template": { "type": "STRING", "required": false, "description": "Email template name" }
    },
    "requires_recipients": true
  },
  {
    "id": "WEBHOOK",
    "name": "Webhook",
    "description": "Calls an external webhook with event data",
    "config_schema": {
      "url": { "type": "STRING", "required": true, "description": "Webhook URL" },
      "method": { 
        "type": "ENUM", 
        "required": false, 
        "default": "POST",
        "options": ["GET", "POST", "PUT", "PATCH", "DELETE"]
      },
      "headers": { "type": "OBJECT", "required": false, "description": "HTTP headers" }
    },
    "requires_recipients": false
  }
]
```

### List Condition Types

Retrieves a list of available condition types.

**Endpoint:** `GET /api/v1/workflows/config/condition-types`  
**Response:** Array of condition types
```json
[
  {
    "id": "FIELD",
    "name": "Field Condition",
    "description": "Condition based on entity field values",
    "config_schema": {
      "field": { "type": "STRING", "required": true, "description": "Entity field name" },
      "operator": { 
        "type": "ENUM", 
        "required": true,
        "options": [
          "EQUALS", "NOT_EQUALS", "GREATER_THAN", "LESS_THAN", 
          "GREATER_THAN_OR_EQUALS", "LESS_THAN_OR_EQUALS",
          "CONTAINS", "NOT_CONTAINS", "STARTS_WITH", "ENDS_WITH",
          "IN", "NOT_IN", "IS_NULL", "IS_NOT_NULL", 
          "INCREASED", "DECREASED", "CHANGED"
        ]
      },
      "value": { "type": "ANY", "required": false, "description": "Comparison value" }
    }
  },
  {
    "id": "TIME",
    "name": "Time Condition",
    "description": "Condition based on time constraints",
    "config_schema": {
      "days": { 
        "type": "ARRAY", 
        "required": false,
        "item_type": "ENUM",
        "options": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"],
        "description": "Days of week"
      },
      "start_time": { "type": "STRING", "required": false, "description": "Start time (HH:MM format)" },
      "end_time": { "type": "STRING", "required": false, "description": "End time (HH:MM format)" }
    }
  },
  {
    "id": "ROLE",
    "name": "Role Condition",
    "description": "Condition based on user roles",
    "config_schema": {
      "role": { "type": "STRING", "required": true, "description": "Role name" }
    }
  }
]
```

### List Recipient Types

Retrieves a list of available recipient types.

**Endpoint:** `GET /api/v1/workflows/config/recipient-types`  
**Response:** Array of recipient types
```json
[
  {
    "id": "USER",
    "name": "Specific User",
    "description": "Targets a specific user by ID",
    "config_schema": {
      "value": { "type": "STRING", "required": true, "description": "User ID" }
    }
  },
  {
    "id": "ROLE",
    "name": "User Role",
    "description": "Targets all users with a specific role",
    "config_schema": {
      "value": { "type": "STRING", "required": true, "description": "Role name" }
    }
  },
  {
    "id": "DEPARTMENT",
    "name": "Department",
    "description": "Targets all users in a specific department",
    "config_schema": {
      "value": { "type": "STRING", "required": true, "description": "Department name" }
    }
  },
  {
    "id": "DYNAMIC",
    "name": "Dynamic Recipients",
    "description": "Dynamically resolves recipients based on entity relationships",
    "config_schema": {
      "value": { "type": "STRING", "required": true, "description": "Entity relationship path" }
    }
  },
  {
    "id": "EMAIL",
    "name": "Email Address",
    "description": "Targets a specific email address",
    "config_schema": {
      "value": { "type": "STRING", "required": true, "description": "Email address" }
    }
  }
]
```

## Error Handling

The API follows standard HTTP status codes for errors with a consistent response format:

```json
{
  "status_code": 404,
  "error": "NOT_FOUND",
  "message": "Workflow definition with ID 01HFGB2D5NSJWZ3K4P6Q7R8T9M not found",
  "details": {
    "resource_type": "workflow_definition",
    "resource_id": "01HFGB2D5NSJWZ3K4P6Q7R8T9M"
  },
  "timestamp": "2023-11-15T14:30:22.123Z"
}
```

Common status codes:

- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

## Pagination

For endpoints that return lists, standardized pagination is supported with a consistent response format:

```json
{
  "items": [...],  // Array of items
  "total": 156,    // Total number of items matching the query
  "limit": 50,     // Maximum number of items per page
  "offset": 0      // Offset from the start of the result set
}
```

Query parameters:
- `limit`: Maximum number of items to return (default: 50)
- `offset`: Number of items to skip (default: 0)

## Data Transfer Objects (DTOs)

### WorkflowDefCreateDto

DTO for creating a new workflow definition.

```python
class WorkflowDefCreateDto(BaseModel):
    name: str
    description: str
    status: WorkflowStatusEnum = WorkflowStatusEnum.DRAFT
    version: str = "1.0.0"
    trigger: WorkflowTriggerCreateDto
    conditions: List[WorkflowConditionCreateDto] = []
    actions: List[WorkflowActionCreateDto] = []
```

### WorkflowDefUpdateDto

DTO for updating an existing workflow definition.

```python
class WorkflowDefUpdateDto(BaseModel):
    name: str
    description: str
    status: WorkflowStatusEnum
    version: str
    trigger: WorkflowTriggerUpdateDto
    conditions: List[WorkflowConditionUpdateDto] = []
    actions: List[WorkflowActionUpdateDto] = []
```

### WorkflowDefViewDto

DTO for viewing a workflow definition.

```python
class WorkflowDefViewDto(BaseModel):
    id: str
    name: str
    description: str
    status: WorkflowStatusEnum
    version: str
    trigger: WorkflowTriggerViewDto
    conditions: List[WorkflowConditionViewDto] = []
    actions: List[WorkflowActionViewDto] = []
    created_at: datetime
    updated_at: datetime
```

### WorkflowDefFilterParams

DTO for filtering workflow definitions.

```python
class WorkflowDefFilterParams(BaseModel):
    name: Optional[str] = None
    status: Optional[WorkflowStatusEnum] = None
    entity_type: Optional[str] = None
    limit: int = 50
    offset: int = 0
```

### WorkflowExecutionRecordViewDto

DTO for viewing workflow execution records.

```python
class WorkflowExecutionRecordViewDto(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    status: WorkflowExecutionStatusEnum
    entity_type: str
    entity_id: str
    operation: WorkflowTriggerOperationEnum
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    conditions_result: bool
    actions_total: int
    actions_success: int
    actions_failed: int
    action_results: List[WorkflowActionResultDto] = []
```

### WorkflowActionResultDto

DTO for workflow action execution results.

```python
class WorkflowActionResultDto(BaseModel):
    action_id: str
    type: WorkflowActionTypeEnum
    status: WorkflowExecutionStatusEnum
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    recipients_count: Optional[int]
    details: Optional[str]
```

## Integration with Domain-Driven Design

### Schema Managers

Schema managers handle the conversion between domain entities and DTOs:

```python
class WorkflowDefSchemaManager:
    def entity_to_dto(self, entity: WorkflowDef) -> WorkflowDefViewDto:
        """Convert a workflow definition entity to a DTO."""
        
    def dto_to_entity(self, dto: Union[WorkflowDefCreateDto, WorkflowDefUpdateDto]) -> WorkflowDef:
        """Convert a DTO to a workflow definition entity."""
```

### API Integration

Register workflow endpoints with FastAPI:

```python
def register_workflow_definition_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    workflow_service: Optional[WorkflowService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for workflow definitions."""
    
def register_workflow_execution_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    workflow_execution_service: Optional[WorkflowExecutionService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for workflow executions."""

def register_workflow_config_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    workflow_config_service: Optional[WorkflowConfigService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for workflow configuration."""
    
def register_workflow_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    workflow_service: Optional[WorkflowService] = None,
    workflow_execution_service: Optional[WorkflowExecutionService] = None,
    workflow_config_service: Optional[WorkflowConfigService] = None,
) -> Dict[str, Any]:
    """Register all workflow endpoints."""
```

## Template Variables

Workflow actions support template variables using the double-curly brace syntax:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{entity_field}}` | Any field from the entity that triggered the workflow | `{{name}}`, `{{price}}`, `{{category}}` |
| `{{entity_id}}` | The ID of the entity that triggered the workflow | `{{entity_id}}` |
| `{{operation}}` | The operation that triggered the workflow | `{{operation}}` |
| `{{workflow_id}}` | The ID of the workflow | `{{workflow_id}}` |
| `{{workflow_name}}` | The name of the workflow | `{{workflow_name}}` |
| `{{execution_id}}` | The ID of the execution | `{{execution_id}}` |
| `{{timestamp}}` | The current timestamp | `{{timestamp}}` |
| `{{user_id}}` | The ID of the current user | `{{user_id}}` |
| `{{user_name}}` | The name of the current user | `{{user_name}}` |

## Rate Limiting

API requests are rate-limited to prevent abuse:

- 100 requests per minute for workflow management endpoints
- 300 requests per minute for configuration endpoints
- 500 requests per minute for workflow execution endpoints

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 2.0.0 | 2025-04-16 | Domain-driven design implementation |
| 1.1.0 | 2023-12-15 | Added simulation endpoint and recipient types |
| 1.0.0 | 2023-11-10 | Initial API release |