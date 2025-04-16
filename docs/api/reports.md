# Reports API

The Reports API provides a comprehensive interface for managing report templates, generating reports, and delivering report outputs. This module is fully implemented using the domain-driven design pattern.

## Key Concepts

The Reports module consists of several core entities:

- **Report Templates**: Define the structure, behavior, and formatting of reports
- **Report Fields**: Define the data points that make up a report
- **Report Triggers**: Define when reports should be automatically generated
- **Report Outputs**: Define how reports should be delivered (file, email, etc.)
- **Report Executions**: Track the execution of report generation tasks

## API Endpoints

### Report Field Definitions

Endpoints for managing report field definitions.

#### Create Field Definition

```
POST /api/v1/report-field-definitions
```

Create a new report field definition.

**Request Body:**

```json
{
  "name": "customer_name",
  "display": "Customer Name",
  "field_type": "db_column",
  "field_config": {
    "table": "customers",
    "column": "name"
  },
  "description": "The customer's full name",
  "order": 1,
  "format_string": null,
  "conditional_formats": null,
  "is_visible": true,
  "parent_field_id": null
}
```

**Response:**

```json
{
  "id": "fd123e4567-e89b-12d3-a456-426614174000",
  "name": "customer_name",
  "display": "Customer Name",
  "field_type": "db_column",
  "field_config": {
    "table": "customers",
    "column": "name"
  },
  "description": "The customer's full name",
  "order": 1,
  "format_string": null,
  "conditional_formats": null,
  "is_visible": true,
  "parent_field_id": null
}
```

#### Get Field Definition

```
GET /api/v1/report-field-definitions/{field_definition_id}
```

Get a specific report field definition by ID.

#### List Field Definitions

```
GET /api/v1/report-field-definitions
```

List report field definitions with filtering.

**Query Parameters:**

- `name`: Filter by field name
- `field_type`: Filter by field type (`db_column`, `attribute`, `method`, `query`, `aggregate`, `related`, `custom`)
- `parent_field_id`: Filter by parent field ID
- `template_id`: Filter by template ID
- `is_visible`: Filter by visibility
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

#### Update Field Definition

```
PATCH /api/v1/report-field-definitions/{field_definition_id}
```

Update a report field definition.

**Request Body:**

```json
{
  "display": "Customer Full Name",
  "description": "The customer's full legal name",
  "order": 2,
  "is_visible": true
}
```

#### Delete Field Definition

```
DELETE /api/v1/report-field-definitions/{field_definition_id}
```

Delete a report field definition.

### Report Templates

Endpoints for managing report templates.

#### Create Template

```
POST /api/v1/report-templates
```

Create a new report template.

**Request Body:**

```json
{
  "name": "monthly_sales_report",
  "description": "Monthly sales by customer and product",
  "base_object_type": "Order",
  "format_config": {
    "page_size": "letter",
    "orientation": "landscape"
  },
  "parameter_definitions": {
    "start_date": {
      "type": "date",
      "required": true
    },
    "end_date": {
      "type": "date",
      "required": true
    },
    "customer_id": {
      "type": "string",
      "required": false
    }
  },
  "cache_policy": {
    "max_age_seconds": 3600
  },
  "version": "1.0.0",
  "field_ids": [
    "fd123e4567-e89b-12d3-a456-426614174000"
  ]
}
```

**Response:**

```json
{
  "id": "rt123e4567-e89b-12d3-a456-426614174000",
  "name": "monthly_sales_report",
  "description": "Monthly sales by customer and product",
  "base_object_type": "Order",
  "format_config": {
    "page_size": "letter",
    "orientation": "landscape"
  },
  "parameter_definitions": {
    "start_date": {
      "type": "date",
      "required": true
    },
    "end_date": {
      "type": "date",
      "required": true
    },
    "customer_id": {
      "type": "string",
      "required": false
    }
  },
  "cache_policy": {
    "max_age_seconds": 3600
  },
  "version": "1.0.0",
  "fields": [
    {
      "id": "fd123e4567-e89b-12d3-a456-426614174000",
      "name": "customer_name",
      "display": "Customer Name",
      "field_type": "db_column",
      "field_config": {
        "table": "customers",
        "column": "name"
      },
      "description": "The customer's full name",
      "order": 1,
      "format_string": null,
      "conditional_formats": null,
      "is_visible": true,
      "parent_field_id": null
    }
  ]
}
```

#### Get Template

```
GET /api/v1/report-templates/{template_id}
```

Get a specific report template by ID.

#### List Templates

```
GET /api/v1/report-templates
```

List report templates with filtering.

**Query Parameters:**

- `name`: Filter by template name
- `base_object_type`: Filter by base object type
- `field_id`: Filter by associated field ID
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

#### Update Template

```
PATCH /api/v1/report-templates/{template_id}
```

Update a report template.

**Request Body:**

```json
{
  "description": "Updated monthly sales by customer and product",
  "format_config": {
    "page_size": "letter",
    "orientation": "portrait"
  },
  "cache_policy": {
    "max_age_seconds": 1800
  }
}
```

#### Update Template Fields

```
PUT /api/v1/report-templates/{template_id}/fields
```

Update the fields associated with a report template.

**Request Body:**

```json
{
  "field_ids_to_add": [
    "fd123e4567-e89b-12d3-a456-426614174001"
  ],
  "field_ids_to_remove": [
    "fd123e4567-e89b-12d3-a456-426614174000"
  ]
}
```

#### Delete Template

```
DELETE /api/v1/report-templates/{template_id}
```

Delete a report template.

#### Execute Template

```
POST /api/v1/report-templates/{template_id}/execute
```

Execute a report template.

**Request Body:**

```json
{
  "triggered_by": "user@example.com",
  "parameters": {
    "start_date": "2023-01-01",
    "end_date": "2023-01-31"
  }
}
```

**Response:**

```json
{
  "id": "re123e4567-e89b-12d3-a456-426614174000",
  "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
  "triggered_by": "user@example.com",
  "trigger_type": "manual",
  "parameters": {
    "start_date": "2023-01-01",
    "end_date": "2023-01-31"
  },
  "status": "completed",
  "started_at": "2023-02-01T10:00:00Z",
  "completed_at": "2023-02-01T10:01:30Z",
  "error_details": null,
  "row_count": 1500,
  "execution_time_ms": 90000,
  "result_hash": "a1b2c3d4e5f6",
  "output_executions": []
}
```

### Report Triggers

Endpoints for managing report triggers.

#### Create Trigger

```
POST /api/v1/report-triggers
```

Create a new report trigger.

**Request Body:**

```json
{
  "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
  "trigger_type": "scheduled",
  "trigger_config": {
    "retry_count": 3
  },
  "schedule": "0 0 1 * *",
  "is_active": true
}
```

**Response:**

```json
{
  "id": "tr123e4567-e89b-12d3-a456-426614174000",
  "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
  "trigger_type": "scheduled",
  "trigger_config": {
    "retry_count": 3
  },
  "schedule": "0 0 1 * *",
  "is_active": true,
  "last_triggered": null
}
```

#### Get Trigger

```
GET /api/v1/report-triggers/{trigger_id}
```

Get a specific report trigger by ID.

#### List Triggers

```
GET /api/v1/report-triggers
```

List report triggers with filtering.

**Query Parameters:**

- `report_template_id`: Filter by template ID
- `trigger_type`: Filter by trigger type (`manual`, `scheduled`, `event`, `query`)
- `is_active`: Filter by active status
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

#### Update Trigger

```
PATCH /api/v1/report-triggers/{trigger_id}
```

Update a report trigger.

**Request Body:**

```json
{
  "schedule": "0 0 15 * *",
  "is_active": false
}
```

#### Delete Trigger

```
DELETE /api/v1/report-triggers/{trigger_id}
```

Delete a report trigger.

#### Process Due Triggers

```
POST /api/v1/report-triggers/process-due
```

Process all due scheduled triggers.

**Response:**

```json
{
  "processed": 3
}
```

### Report Outputs

Endpoints for managing report outputs.

#### Create Output

```
POST /api/v1/report-outputs
```

Create a new report output.

**Request Body:**

```json
{
  "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
  "output_type": "email",
  "format": "pdf",
  "output_config": {
    "recipients": ["user@example.com"],
    "subject": "Monthly Sales Report"
  },
  "format_config": {
    "page_size": "letter",
    "orientation": "landscape"
  },
  "is_active": true
}
```

**Response:**

```json
{
  "id": "ro123e4567-e89b-12d3-a456-426614174000",
  "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
  "output_type": "email",
  "format": "pdf",
  "output_config": {
    "recipients": ["user@example.com"],
    "subject": "Monthly Sales Report"
  },
  "format_config": {
    "page_size": "letter",
    "orientation": "landscape"
  },
  "is_active": true
}
```

#### Get Output

```
GET /api/v1/report-outputs/{output_id}
```

Get a specific report output by ID.

#### List Outputs

```
GET /api/v1/report-outputs
```

List report outputs with filtering.

**Query Parameters:**

- `report_template_id`: Filter by template ID
- `output_type`: Filter by output type (`file`, `email`, `webhook`, `notification`)
- `format`: Filter by format (`csv`, `pdf`, `json`, `html`, `excel`, `text`)
- `is_active`: Filter by active status
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

#### Update Output

```
PATCH /api/v1/report-outputs/{output_id}
```

Update a report output.

**Request Body:**

```json
{
  "output_config": {
    "recipients": ["user@example.com", "manager@example.com"],
    "subject": "Updated: Monthly Sales Report"
  },
  "is_active": false
}
```

#### Delete Output

```
DELETE /api/v1/report-outputs/{output_id}
```

Delete a report output.

### Report Executions

Endpoints for managing report executions.

#### Get Execution

```
GET /api/v1/report-executions/{execution_id}
```

Get a specific report execution by ID.

#### List Executions

```
GET /api/v1/report-executions
```

List report executions with filtering.

**Query Parameters:**

- `report_template_id`: Filter by template ID
- `triggered_by`: Filter by triggered by
- `trigger_type`: Filter by trigger type
- `status`: Filter by status (`pending`, `running`, `completed`, `failed`, `canceled`)
- `created_after`: Filter by created after date
- `created_before`: Filter by created before date
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

#### Update Execution Status

```
PATCH /api/v1/report-executions/{execution_id}/status
```

Update a report execution status.

**Request Body:**

```json
{
  "status": "completed",
  "error_details": null
}
```

### Report Output Executions

Endpoints for managing report output executions.

#### Get Output Execution

```
GET /api/v1/report-output-executions/{output_execution_id}
```

Get a specific report output execution by ID.

#### List Output Executions

```
GET /api/v1/report-output-executions
```

List report output executions with filtering.

**Query Parameters:**

- `report_execution_id`: Filter by execution ID
- `report_output_id`: Filter by output ID
- `status`: Filter by status
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

#### Update Output Execution Status

```
PATCH /api/v1/report-output-executions/{output_execution_id}/status
```

Update a report output execution status.

**Request Body:**

```json
{
  "status": "completed",
  "error_details": null,
  "output_location": "/reports/monthly_sales_report/202301.pdf",
  "output_size_bytes": 1024000
}
```

## Integration with Applications

You can integrate the Reports API into your FastAPI application using the provided functions:

```python
from fastapi import FastAPI
from uno.reports.api_integration import register_reports_endpoints

app = FastAPI()

# Register all Reports endpoints
endpoints = register_reports_endpoints(
    app_or_router=app,
    path_prefix="/api/v1",
    include_auth=True
)

# Or register specific endpoint groups
from uno.reports.api_integration import (
    register_report_template_endpoints,
    register_report_execution_endpoints
)

# Just templates and executions
template_endpoints = register_report_template_endpoints(app, path_prefix="/api/v1")
execution_endpoints = register_report_execution_endpoints(app, path_prefix="/api/v1")
```

## Field Types

The Reports module supports several field types, each with its own configuration requirements:

- `db_column`: A direct column from a database table (requires `table` and `column` in `field_config`)
- `attribute`: A field from an attribute type (requires `attribute_type_id` in `field_config`)
- `method`: A method to call to get the field value (requires `method` and `module` in `field_config`)
- `query`: A query to execute to get the field value (requires `query_id` in `field_config`)
- `aggregate`: An aggregation of other fields (requires `function` and `field` in `field_config`)
- `related`: A field from a related entity (requires `relation` and `field` in `field_config`)
- `custom`: A custom field with custom processing (flexible `field_config`)

## Trigger Types

Reports can be triggered in multiple ways:

- `manual`: Triggered manually by a user
- `scheduled`: Triggered on a schedule (using cron-like syntax)
- `event`: Triggered by a system event
- `query`: Triggered when a query returns specific results

## Output Types

Reports can be delivered in various ways:

- `file`: Output to a file (requires `path` in `output_config`)
- `email`: Send via email (requires `recipients` in `output_config`)
- `webhook`: Send to a webhook (requires `url` in `output_config`)
- `notification`: Send as a system notification

## Output Formats

Reports can be generated in multiple formats:

- `csv`: Comma-separated values
- `pdf`: Portable Document Format
- `json`: JavaScript Object Notation
- `html`: HyperText Markup Language
- `excel`: Microsoft Excel
- `text`: Plain text