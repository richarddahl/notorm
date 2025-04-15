# Reports Module Enhancement Plan

## Overview

The reports module aims to provide a flexible, user-customizable system for generating reports based on data within the UNO framework. This enhancement plan outlines the approach to developing a comprehensive reporting system that enables end-users to define reports that can be generated on-demand, scheduled, triggered by database events, or based on matched queries.

## Core Requirements

1. **End-User Customization**
   - User-friendly interfaces for report definition
   - Flexible field selection and configuration
   - Support for complex filtering and criteria

2. **Multiple Generation Methods**
   - On-demand report generation
   - Scheduled report generation (time-based)
   - Event-driven generation (database events)
   - Query-based generation (when data matches specific criteria)

3. **Flexible Field Definitions**
   - Database columns
   - Business logic function results
   - Class method results
   - Related database record reports
   - Lists of objects
   - Custom queries using the existing query framework

4. **Integration with Other Systems**
   - Attributes system for dynamic properties
   - Values system for type-safe value representation
   - Queries system for complex data access patterns
   - Workflows system for process orchestration
   - Events system for responding to changes

## Architecture

### Report Definitions

A report definition consists of several components:

1. **Report Template**: Core structure that defines the report format, fields, and behavior
2. **Field Definitions**: Specifications for each field in the report
3. **Datasource Configuration**: Where and how to obtain data for the report
4. **Trigger Configuration**: What causes the report to generate
5. **Output Configuration**: Format and delivery mechanisms

### Report Generation Process

```
+----------------+     +------------------+     +--------------------+
| Trigger Event  |---->| Report Execution |---->| Data Acquisition   |
+----------------+     +------------------+     +--------------------+```
```

                        |                         |
                        v                         v
```
```
+----------------+     +------------------+     +--------------------+
| Delivery       |<----| Formatting       |<----| Data Transformation|
+----------------+     +------------------+     +--------------------+
```

### Key Components

#### 1. Report Definition Service

Manages report templates and configurations, allowing users to define:
- Report structure (fields, layout, grouping)
- Data sources and field mappings
- Filters and parameters
- Formatting rules and conditional formatting
- Output formats (CSV, PDF, JSON, etc.)

#### 2. Report Field Manager

Handles the definition and management of report fields, supporting:
- Direct database columns
- Calculated fields
- Attribute-based fields
- Method-based fields
- Query-based fields
- Aggregate/statistical fields

#### 3. Report Execution Engine

Responsible for:
- Processing report definitions
- Acquiring data from various sources
- Applying transformations and calculations
- Formatting output according to specifications
- Handling pagination and large datasets
- Caching strategies for performance

#### 4. Report Trigger System

Manages when reports are generated:
- Manual triggers (on-demand generation)
- Time-based triggers (scheduled reports)
- Event-based triggers (database events)
- Query-based triggers (data condition matching)

#### 5. Report Delivery System

Handles output distribution:
- File storage
- Email delivery
- Webhook notifications
- Integration with notification systems
- Archiving and retrieval

## Data Model Enhancement

### New Models

#### `ReportTemplate`

```python
class ReportTemplateModel(DefaultModelMixin, UnoModel):```

"""Defines the structure and behavior of a report."""
``````

```
```

# Basic information
name: Mapped[PostgresTypes.String255]
description: Mapped[str]
``````

```
```

# Configuration
base_object_type: Mapped[str]  # What type of entity this report is based on
format_config: Mapped[Dict[str, Any]]  # JSON configuration for output format
parameter_definitions: Mapped[Dict[str, Any]]  # User parameters the report accepts
cache_policy: Mapped[Dict[str, Any]]  # How report results are cached
version: Mapped[str]  # For template versioning
``````

```
```

# Relations to other components
fields: Mapped[List["ReportFieldDefinitionModel"]]
triggers: Mapped[List["ReportTriggerModel"]]
outputs: Mapped[List["ReportOutputModel"]]
```
```

#### `ReportFieldDefinition`

```python
class ReportFieldDefinitionModel(DefaultModelMixin, UnoModel):```

"""Defines a field within a report template."""
``````

```
```

# Field identification
name: Mapped[PostgresTypes.String255]
display_name: Mapped[str]
description: Mapped[Optional[str]]
``````

```
```

# Field configuration
report_template_id: Mapped[PostgresTypes.String26]
field_type: Mapped[str]  # db_column, attribute, method, query, aggregate
field_config: Mapped[Dict[str, Any]]  # Configuration specific to field_type
``````

```
```

# Presentation
order: Mapped[int]
format_string: Mapped[Optional[str]]
conditional_formats: Mapped[Optional[Dict[str, Any]]]
is_visible: Mapped[bool]
``````

```
```

# Relations
report_template: Mapped["ReportTemplateModel"]
parent_field: Mapped[Optional["ReportFieldDefinitionModel"]]
child_fields: Mapped[List["ReportFieldDefinitionModel"]]
```
```

#### `ReportTrigger`

```python
class ReportTriggerModel(DefaultModelMixin, UnoModel):```

"""Defines when a report should be generated."""
``````

```
```

# Trigger configuration
report_template_id: Mapped[PostgresTypes.String26]
trigger_type: Mapped[str]  # manual, scheduled, event, query
trigger_config: Mapped[Dict[str, Any]]  # Configuration specific to trigger_type
``````

```
```

# For scheduled triggers
schedule: Mapped[Optional[str]]  # Cron-style expression
``````

```
```

# For event triggers
event_type: Mapped[Optional[str]]
entity_type: Mapped[Optional[str]]
``````

```
```

# For query triggers
query_id: Mapped[Optional[PostgresTypes.String26]]
``````

```
```

# Status
is_active: Mapped[bool]
last_triggered: Mapped[Optional[datetime]]
``````

```
```

# Relations
report_template: Mapped["ReportTemplateModel"]
```
```

#### `ReportOutput`

```python
class ReportOutputModel(DefaultModelMixin, UnoModel):```

"""Defines how report results should be delivered."""
``````

```
```

# Output configuration
report_template_id: Mapped[PostgresTypes.String26]
output_type: Mapped[str]  # file, email, webhook, notification
output_config: Mapped[Dict[str, Any]]  # Configuration specific to output_type
``````

```
```

# Format
format: Mapped[str]  # csv, pdf, json, html, etc.
format_config: Mapped[Dict[str, Any]]
``````

```
```

# Status
is_active: Mapped[bool]
``````

```
```

# Relations
report_template: Mapped["ReportTemplateModel"]
```
```

#### `ReportExecution`

```python
class ReportExecutionModel(DefaultModelMixin, UnoModel):```

"""Records of report generation executions."""
``````

```
```

# Execution details
report_template_id: Mapped[PostgresTypes.String26]
triggered_by: Mapped[str]  # trigger ID or user ID
trigger_type: Mapped[str]  # manual, scheduled, event, query
``````

```
```

# Parameters provided
parameters: Mapped[Dict[str, Any]]
``````

```
```

# Execution status
status: Mapped[str]  # pending, running, completed, failed
started_at: Mapped[datetime]
completed_at: Mapped[Optional[datetime]]
error_details: Mapped[Optional[str]]
``````

```
```

# Result
row_count: Mapped[Optional[int]]
execution_time_ms: Mapped[Optional[int]]
result_hash: Mapped[Optional[str]]
``````

```
```

# Relations
report_template: Mapped["ReportTemplateModel"]
``````

report_outputs: Mapped[List["ReportOutputExecutionModel"]]
```
```

#### `ReportOutputExecution`

```python
class ReportOutputExecutionModel(DefaultModelMixin, UnoModel):```

"""Records of report output delivery."""
``````

```
```

# Execution reference
report_execution_id: Mapped[PostgresTypes.String26]
report_output_id: Mapped[PostgresTypes.String26]
``````

```
```

# Output status
status: Mapped[str]  # pending, completed, failed
completed_at: Mapped[Optional[datetime]]
error_details: Mapped[Optional[str]]
``````

```
```

# Result details
output_location: Mapped[Optional[str]]  # URL, file path, etc.
output_size_bytes: Mapped[Optional[int]]
``````

```
```

# Relations
report_execution: Mapped["ReportExecutionModel"]
report_output: Mapped["ReportOutputModel"]
```
```

## Service Layer

### ReportTemplateService

Central service for managing report templates:

```python
class ReportTemplateService:```

"""Service for managing report templates."""
``````

```
```

async def create_template(self, template_data: dict) -> Result[ReportTemplate, ReportError]:```

"""Create a new report template."""
```
    
async def update_template(self, template_id: str, template_data: dict) -> Result[ReportTemplate, ReportError]:```

"""Update an existing report template."""
```
    
async def delete_template(self, template_id: str) -> Result[bool, ReportError]:```

"""Delete a report template."""
```
    
async def get_template(self, template_id: str) -> Result[Optional[ReportTemplate], ReportError]:```

"""Get a report template by ID."""
```
    
async def list_templates(self, filters: dict = None) -> Result[List[ReportTemplate], ReportError]:```

"""List report templates, optionally filtered."""
```
    
async def clone_template(self, template_id: str, new_name: str) -> Result[ReportTemplate, ReportError]:```

"""Clone an existing template with a new name."""
```
```
```

### ReportFieldService

Manages report field definitions:

```python
class ReportFieldService:```

"""Service for managing report field definitions."""
``````

```
```

async def add_field(self, template_id: str, field_data: dict) -> Result[ReportFieldDefinition, ReportError]:```

"""Add a field to a report template."""
```
    
async def update_field(self, field_id: str, field_data: dict) -> Result[ReportFieldDefinition, ReportError]:```

"""Update a field definition."""
```
    
async def delete_field(self, field_id: str) -> Result[bool, ReportError]:```

"""Delete a field from a report template."""
```
    
async def get_available_fields(self, base_object_type: str) -> Result[List[Dict[str, Any]], ReportError]:```

"""Get available fields for a specific object type."""
```
    
async def validate_field_config(self, field_type: str, field_config: dict) -> Result[bool, ReportError]:```

"""Validate a field configuration."""
```
```
```

### ReportExecutionService

Handles report execution and data retrieval:

```python
class ReportExecutionService:```

"""Service for executing reports and retrieving data."""
``````

```
```

async def execute_report(```

self, 
template_id: str, 
parameters: dict = None,
trigger_type: str = "manual",
user_id: str = None
```
) -> Result[ReportExecution, ReportError]:```

"""Execute a report with optional parameters."""
```
    
async def get_execution_status(self, execution_id: str) -> Result[dict, ReportError]:```

"""Get the status of a report execution."""
```
    
async def cancel_execution(self, execution_id: str) -> Result[bool, ReportError]:```

"""Cancel a running report execution."""
```
    
async def get_execution_result(self, execution_id: str) -> Result[Any, ReportError]:```

"""Get the result of a completed report execution."""
```
    
async def list_executions(```

self, 
template_id: str = None, 
status: str = None,
date_range: Tuple[datetime, datetime] = None
```
) -> Result[List[ReportExecution], ReportError]:```

"""List report executions, optionally filtered."""
```
```
```

### ReportTriggerService

Manages automated report triggers:

```python
class ReportTriggerService:```

"""Service for managing report triggers."""
``````

```
```

async def create_trigger(self, template_id: str, trigger_data: dict) -> Result[ReportTrigger, ReportError]:```

"""Create a new trigger for a report template."""
```
    
async def update_trigger(self, trigger_id: str, trigger_data: dict) -> Result[ReportTrigger, ReportError]:```

"""Update an existing trigger."""
```
    
async def delete_trigger(self, trigger_id: str) -> Result[bool, ReportError]:```

"""Delete a trigger."""
```
    
async def enable_trigger(self, trigger_id: str) -> Result[bool, ReportError]:```

"""Enable a trigger."""
```
    
async def disable_trigger(self, trigger_id: str) -> Result[bool, ReportError]:```

"""Disable a trigger."""
```
    
async def handle_event(self, event_type: str, event_data: dict) -> Result[List[str], ReportError]:```

"""Handle an event that might trigger reports (returns execution IDs)."""
```
    
async def check_query_triggers(self) -> Result[List[str], ReportError]:```

"""Check query-based triggers and execute reports if conditions are met."""
```
```
```

### ReportOutputService

Manages report output formatting and delivery:

```python
class ReportOutputService:```

"""Service for handling report output and delivery."""
``````

```
```

async def create_output_config(self, template_id: str, output_data: dict) -> Result[ReportOutput, ReportError]:```

"""Create a new output configuration for a report template."""
```
    
async def update_output_config(self, output_id: str, output_data: dict) -> Result[ReportOutput, ReportError]:```

"""Update an existing output configuration."""
```
    
async def delete_output_config(self, output_id: str) -> Result[bool, ReportError]:```

"""Delete an output configuration."""
```
    
async def format_report(self, execution_id: str, format: str) -> Result[bytes, ReportError]:```

"""Format a report result in the specified format."""
```
    
async def deliver_report(self, execution_id: str, output_id: str) -> Result[bool, ReportError]:```

"""Deliver a report according to an output configuration."""
```
```
```

## Integration with Other Modules

### Attributes System Integration

```python
class AttributeReportFieldHandler:```

"""Handler for attribute-based report fields."""
``````

```
```

async def get_available_attributes(self, object_type: str) -> List[Dict[str, Any]]:```

"""Get attributes available for a specific object type."""
```
    
async def resolve_attribute_value(self, entity_id: str, attribute_id: str) -> Any:```

"""Resolve the value of an attribute for an entity."""
```
```
```

### Query System Integration

```python
class QueryReportFieldHandler:```

"""Handler for query-based report fields."""
``````

```
```

async def get_available_queries(self, object_type: str) -> List[Dict[str, Any]]:```

"""Get queries available for a specific object type."""
```
    
async def execute_query_for_field(self, query_id: str, parameters: dict) -> List[Any]:```

"""Execute a query and return results for a report field."""
```
```
```

### Workflow System Integration

```python
class WorkflowReportIntegration:```

"""Integration between reports and workflows."""
``````

```
```

async def attach_report_to_workflow(self, workflow_id: str, report_id: str, config: dict) -> bool:```

"""Attach a report generation step to a workflow."""
```
    
async def trigger_report_from_workflow(self, workflow_id: str, execution_id: str, report_id: str) -> str:```

"""Trigger a report as part of a workflow execution."""
```
```
```

### Event System Integration

```python
class EventReportIntegration:```

"""Integration between events and reports."""
``````

```
```

async def register_event_handlers(self):```

"""Register event handlers for report triggers."""
```
    
async def handle_event(self, event_type: str, event_data: dict):```

"""Handle an event and trigger reports if configured."""
```
```
```

## Implementation Approach

### Phase 1: Core Data Model and Services

1. Implement the enhanced data models described above
2. Develop basic service interfaces and implementations
3. Create a repository layer for data access
4. Implement core validation logic
5. Set up unit tests

### Phase 2: Report Field System

1. Implement the field definition and management system
2. Develop handlers for different field types:
   - Database column handler
   - Attribute handler
   - Method handler
   - Query handler
   - Aggregate handler
3. Implement field validation
4. Create field value resolution system

### Phase 3: Report Execution Engine

1. Develop the report execution pipeline
2. Implement data acquisition strategies
3. Create the transformation and calculation engine
4. Develop output formatting capabilities
5. Implement caching strategies
6. Add performance monitoring

### Phase 4: Trigger and Delivery Systems

1. Implement manual trigger interface
2. Develop the scheduled trigger system
3. Integrate with the event system for event-based triggers
4. Implement the query-based trigger system
5. Develop the output delivery mechanisms
6. Implement notification integration

### Phase 5: Integration and Usability

1. Develop API endpoints for all operations
2. Create CLI tools for report management
3. Implement permission and access control
4. Develop documentation and examples
5. Create visualization components

## API Design

The Reports API will provide endpoints for:

1. **Report Template Management**
   - Create/update/delete report templates
   - List and search templates
   - Get template details

2. **Field Management**
   - Add/update/delete fields
   - Get available fields for object types
   - Configure field options

3. **Report Execution**
   - Execute reports on demand
   - Get execution status
   - Retrieve execution results
   - Cancel executions

4. **Trigger Management**
   - Configure automated triggers
   - Enable/disable triggers
   - Test trigger conditions

5. **Output Management**
   - Configure output formats and destinations
   - Preview formatted outputs
   - Download report results

## Concrete Examples

### Example 1: Creating a Simple Sales Report

```python
# Creating a report template
template = await report_service.create_template({```

"name": "Monthly Sales Report",
"description": "Summarizes sales by product category",
"base_object_type": "order",
"format_config": {```

"default_format": "pdf",
"layout": "portrait",
"grouping": ["category"]
```
},
"parameter_definitions": {```

"start_date": {"type": "date", "required": True},
"end_date": {"type": "date", "required": True},
"include_canceled": {"type": "boolean", "default": False}
```
}
```
})

# Adding fields to the report
await field_service.add_field(template.id, {```

"name": "category",
"display_name": "Product Category",
"field_type": "db_column",
"field_config": {```

"table": "products",
"column": "category",
"join_path": ["order_items", "products"]
```
},
"order": 1
```
})

await field_service.add_field(template.id, {```

"name": "total_sales",
"display_name": "Total Sales",
"field_type": "aggregate",
"field_config": {```

"function": "sum",
"field": "price",
"group_by": ["category"]
```
},
"format_string": "${:,.2f}",
"order": 2
```
})

# Setting up a scheduled trigger
await trigger_service.create_trigger(template.id, {```

"trigger_type": "scheduled",
"schedule": "0 0 1 * *",  # First day of month at midnight
"trigger_config": {```

"parameters": {
    "start_date": {"relative": "first_day_last_month"},
    "end_date": {"relative": "last_day_last_month"},
    "include_canceled": False
}
```
}
```
})

# Configuring output delivery
await output_service.create_output_config(template.id, {```

"output_type": "email",
"format": "pdf",
"output_config": {```

"recipients": ["sales@example.com", "management@example.com"],
"subject": "Monthly Sales Report - {start_date:%B %Y}",
"body": "Attached is the monthly sales report for {start_date:%B %Y}."
```
}
```
})
```

### Example 2: Customer Activity Report with Attributes

```python
# Creating a report that includes attribute data
template = await report_service.create_template({```

"name": "Customer Activity Report",
"description": "Customer engagement with custom attributes",
"base_object_type": "customer",
"format_config": {```

"default_format": "csv"
```
}
```
})

# Database column field
await field_service.add_field(template.id, {```

"name": "customer_name",
"display_name": "Customer",
"field_type": "db_column",
"field_config": {```

"table": "customers",
"column": "name"
```
},
"order": 1
```
})

# Attribute-based field
await field_service.add_field(template.id, {```

"name": "customer_segment",
"display_name": "Segment",
"field_type": "attribute",
"field_config": {```

"attribute_type_id": "segment_attribute_id"
```
},
"order": 2
```
})

# Method-based field
await field_service.add_field(template.id, {```

"name": "days_since_last_order",
"display_name": "Days Since Last Order",
"field_type": "method",
"field_config": {```

"method": "calculate_days_since_last_order",
"module": "customer_analytics"
```
},
"order": 3
```
})

# Query-based field
await field_service.add_field(template.id, {```

"name": "open_support_tickets",
"display_name": "Open Support Tickets",
"field_type": "query",
"field_config": {```

"query_id": "customer_open_tickets_query_id",
"value_field": "count"
```
},
"order": 4
```
})

# Event trigger for report generation
await trigger_service.create_trigger(template.id, {```

"trigger_type": "event",
"event_type": "customer_segment_change",
"entity_type": "customer",
"trigger_config": {```

"parameters": {}
```
}
```
})
```

## Performance Considerations

1. **Asynchronous Execution**
   - Long-running reports should be executed asynchronously
   - Provide status updates and notifications on completion

2. **Data Caching**
   - Cache intermediate results for frequently used data
   - Implement smart invalidation strategies

3. **Incremental Processing**
   - Support incremental report generation for large datasets
   - Allow resuming interrupted report generation

4. **Query Optimization**
   - Analyze and optimize queries generated for reports
   - Use database-specific features for performance

5. **Resource Limits**
   - Implement configurable limits for report size and execution time
   - Provide resource usage estimates before execution

## Conclusion

The enhanced reports module will provide a powerful, flexible system for end-user customization of reports. By integrating with existing systems (attributes, values, queries, workflows, and events), reports can leverage the full capabilities of the UNO framework.

This plan focuses on a modular, extensible architecture that can grow with the system's needs. The phased implementation approach ensures steady progress while allowing for feedback and refinement along the way.

By implementing this plan, the reports module will enable:
- Business users to create and customize reports without developer intervention
- Automated report generation based on business events and conditions
- Rich data presentation drawing from multiple sources
- Efficient delivery of insights to stakeholders in their preferred format