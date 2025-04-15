# Custom Reports Module

The Reports module provides a comprehensive system for creating, configuring, and executing customizable reports within your application. It allows end-users to define reports based on any entity in the system and configure how and when those reports are generated and delivered.

## Key Features

- **Template-based Report Definitions**: Define report templates that can be reused and shared
- **Field Customization**: Configure the exact fields to include in reports with support for:
  - Database columns
  - Calculated fields
  - Aggregates
  - Method results
  - Related records
  - Custom queries
- **Multiple Trigger Methods**:
  - On-demand manual execution
  - Scheduled execution (time-based)
  - Event-driven execution
  - Query-based conditional execution
- **Flexible Output Formats**:
  - CSV
  - JSON
  - PDF
  - Excel
  - HTML
  - Plain Text
- **Multiple Delivery Methods**:
  - File
  - Email
  - Webhook
  - Notifications
- **Execution Management**:
  - Track execution status
  - View execution history
  - Cancel running executions
  - Retry failed executions

## Architecture

The Reports module follows a clean architecture pattern with clear separation of concerns:

1. **Core Domain Layer**:
   - Pydantic models defining report objects
   - Enums defining field types, trigger types, output types, etc.

2. **Repository Layer**:
   - Database access for all report entities
   - Transaction management
   - Data persistence

3. **Service Layer**:
   - Business logic for report operations
   - Field validation and processing
   - Trigger handling and scheduling
   - Execution and delivery management

4. **API Layer**:
   - FastAPI endpoints for all report operations
   - Request/response validation
   - Authentication and authorization
   - Error handling

5. **CLI Layer**:
   - Command-line interface for report management
   - Automation capabilities
   - Scripting support

6. **Web UI Layer**:
   - Web components for report configuration
   - Execution and monitoring interfaces
   - Result visualization

## Getting Started

For detailed instructions on using the Reports module, see the following guides:

- [Creating Report Templates](templates.md)
- [Configuring Report Fields](fields.md)
<!-- TODO: Create report triggers documentation -->
<!-- - [Setting Up Report Triggers](triggers.md) -->
<!-- TODO: Create report outputs documentation -->
<!-- - [Managing Report Outputs](outputs.md) -->
<!-- TODO: Create report execution documentation -->
<!-- - [Executing and Monitoring Reports](execution.md) -->
<!-- TODO: Create report events documentation -->
<!-- - [Integrating with Events](events.md) -->
<!-- TODO: Create report CLI documentation -->
<!-- - [Automating with CLI](cli.md) -->

## API Reference

The Reports module exposes a comprehensive API for integration with other systems:

<!-- TODO: Create report API documentation -->
<!-- - [Report Templates API](api/templates.md) -->
<!-- - [Report Fields API](api/fields.md) -->
<!-- - [Report Triggers API](api/triggers.md) -->
<!-- - [Report Outputs API](api/outputs.md) -->
<!-- - [Report Executions API](api/executions.md) -->