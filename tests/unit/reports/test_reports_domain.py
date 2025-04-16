"""
Tests for the Reports domain entities.

This module contains tests for the domain entities in the reports module.
"""

import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from uno.core.errors.result import Result, Success, Failure
from uno.reports.entities import (
    # Enum values
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
    
    # Domain entities
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution
)


# Test fixtures
@pytest.fixture
def field_definition_id() -> str:
    """Create a test field definition ID."""
    return str(uuid.uuid4())


@pytest.fixture
def field_definition(field_definition_id: str) -> ReportFieldDefinition:
    """Create a test field definition."""
    return ReportFieldDefinition(
        id=field_definition_id,
        name="customer_name",
        display="Customer Name",
        field_type=ReportFieldType.DB_COLUMN,
        field_config={
            "table": "customers",
            "column": "name"
        },
        description="Customer full name",
        order=1,
        format_string="{0}"
    )


@pytest.fixture
def template_id() -> str:
    """Create a test template ID."""
    return str(uuid.uuid4())


@pytest.fixture
def template(template_id: str) -> ReportTemplate:
    """Create a test report template."""
    return ReportTemplate(
        id=template_id,
        name="Customer Report",
        description="Report showing customer information",
        base_object_type="customer",
        format_config={"title": "Customer Information Report"},
        parameter_definitions={
            "start_date": {
                "type": "date",
                "display": "Start Date",
                "required": True
            },
            "end_date": {
                "type": "date",
                "display": "End Date",
                "required": True
            }
        },
        version="1.0.0"
    )


@pytest.fixture
def trigger_id() -> str:
    """Create a test trigger ID."""
    return str(uuid.uuid4())


@pytest.fixture
def trigger(trigger_id: str, template_id: str) -> ReportTrigger:
    """Create a test report trigger."""
    return ReportTrigger(
        id=trigger_id,
        report_template_id=template_id,
        trigger_type=ReportTriggerType.SCHEDULED,
        trigger_config={"timezone": "UTC"},
        schedule="0 9 * * 1",  # Every Monday at 9am
        is_active=True
    )


@pytest.fixture
def output_id() -> str:
    """Create a test output ID."""
    return str(uuid.uuid4())


@pytest.fixture
def output(output_id: str, template_id: str) -> ReportOutput:
    """Create a test report output."""
    return ReportOutput(
        id=output_id,
        report_template_id=template_id,
        output_type=ReportOutputType.EMAIL,
        format=ReportFormat.PDF,
        output_config={
            "recipients": ["user@example.com"],
            "subject": "Customer Report for {start_date} to {end_date}"
        },
        format_config={
            "page_size": "A4",
            "orientation": "portrait"
        }
    )


@pytest.fixture
def execution_id() -> str:
    """Create a test execution ID."""
    return str(uuid.uuid4())


@pytest.fixture
def execution(execution_id: str, template_id: str) -> ReportExecution:
    """Create a test report execution."""
    return ReportExecution(
        id=execution_id,
        report_template_id=template_id,
        triggered_by="user1",
        trigger_type=ReportTriggerType.MANUAL,
        parameters={
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        },
        status=ReportExecutionStatus.PENDING
    )


@pytest.fixture
def output_execution_id() -> str:
    """Create a test output execution ID."""
    return str(uuid.uuid4())


@pytest.fixture
def output_execution(output_execution_id: str, execution_id: str, output_id: str) -> ReportOutputExecution:
    """Create a test report output execution."""
    return ReportOutputExecution(
        id=output_execution_id,
        report_execution_id=execution_id,
        report_output_id=output_id,
        status=ReportExecutionStatus.PENDING
    )


class TestReportFieldDefinition:
    """Tests for ReportFieldDefinition entity."""
    
    def test_creation(self, field_definition: ReportFieldDefinition):
        """Test creating a field definition."""
        # Assert basic properties
        assert field_definition.name == "customer_name"
        assert field_definition.display == "Customer Name"
        assert field_definition.field_type == ReportFieldType.DB_COLUMN
        assert field_definition.field_config == {"table": "customers", "column": "name"}
        assert field_definition.description == "Customer full name"
        assert field_definition.order == 1
        assert field_definition.format_string == "{0}"
        assert field_definition.conditional_formats is None
        assert field_definition.is_visible is True
        assert field_definition.parent_field_id is None
        assert field_definition.parent_field is None
        assert field_definition.child_fields == []
        assert field_definition.report_templates == []
    
    def test_validate_valid_db_column(self, field_definition: ReportFieldDefinition):
        """Test validation with valid DB_COLUMN field type."""
        # Act
        result = field_definition.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_invalid_field_type(self, field_definition: ReportFieldDefinition):
        """Test validation with invalid field type."""
        # Arrange
        field_definition.field_type = "invalid_type"
        
        # Act
        result = field_definition.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Field type must be one of" in result.error
    
    def test_validate_missing_required_config(self, field_definition: ReportFieldDefinition):
        """Test validation with missing required config."""
        # Arrange
        field_definition.field_config = {"table": "customers"}  # Missing 'column'
        
        # Act
        result = field_definition.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Field config for DB_COLUMN must include column" in result.error
    
    def test_validate_attribute_type(self, field_definition: ReportFieldDefinition):
        """Test validation with ATTRIBUTE field type."""
        # Arrange
        field_definition.field_type = ReportFieldType.ATTRIBUTE
        field_definition.field_config = {"attribute_type_id": "123"}
        
        # Act
        result = field_definition.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_attribute_type_missing_config(self, field_definition: ReportFieldDefinition):
        """Test validation with ATTRIBUTE field type missing config."""
        # Arrange
        field_definition.field_type = ReportFieldType.ATTRIBUTE
        field_definition.field_config = {}
        
        # Act
        result = field_definition.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Field config for ATTRIBUTE must include attribute_type_id" in result.error
    
    def test_add_to_template(self, field_definition: ReportFieldDefinition, template: ReportTemplate):
        """Test adding a field to a template."""
        # Act
        field_definition.add_to_template(template)
        
        # Assert
        assert template in field_definition.report_templates
        assert field_definition in template.fields
    
    def test_remove_from_template(self, field_definition: ReportFieldDefinition, template: ReportTemplate):
        """Test removing a field from a template."""
        # Arrange
        field_definition.add_to_template(template)
        
        # Act
        field_definition.remove_from_template(template)
        
        # Assert
        assert template not in field_definition.report_templates
        assert field_definition not in template.fields
    
    def test_add_child_field(self, field_definition: ReportFieldDefinition):
        """Test adding a child field."""
        # Arrange
        child_field = ReportFieldDefinition(
            id=str(uuid.uuid4()),
            name="customer_email",
            display="Customer Email",
            field_type=ReportFieldType.DB_COLUMN,
            field_config={
                "table": "customers",
                "column": "email"
            }
        )
        
        # Act
        field_definition.add_child_field(child_field)
        
        # Assert
        assert child_field in field_definition.child_fields
        assert child_field.parent_field == field_definition
        assert child_field.parent_field_id == field_definition.id


class TestReportTemplate:
    """Tests for ReportTemplate entity."""
    
    def test_creation(self, template: ReportTemplate):
        """Test creating a report template."""
        # Assert basic properties
        assert template.name == "Customer Report"
        assert template.description == "Report showing customer information"
        assert template.base_object_type == "customer"
        assert template.format_config == {"title": "Customer Information Report"}
        assert "start_date" in template.parameter_definitions
        assert "end_date" in template.parameter_definitions
        assert template.version == "1.0.0"
        assert template.fields == []
        assert template.triggers == []
        assert template.outputs == []
        assert template.executions == []
    
    def test_validate_valid_template(self, template: ReportTemplate):
        """Test validation with a valid template."""
        # Act
        result = template.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_invalid_parameter_definition(self, template: ReportTemplate):
        """Test validation with invalid parameter definition."""
        # Arrange
        template.parameter_definitions = {
            "invalid_param": "not_a_dict"  # Should be a dict
        }
        
        # Act
        result = template.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Parameter definition for invalid_param must be a dictionary" in result.error
    
    def test_validate_parameter_missing_type(self, template: ReportTemplate):
        """Test validation with parameter missing type."""
        # Arrange
        template.parameter_definitions = {
            "invalid_param": {
                "display": "Invalid Param"
                # Missing 'type'
            }
        }
        
        # Act
        result = template.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Parameter definition for invalid_param must include a type" in result.error
    
    def test_validate_with_invalid_field(self, template: ReportTemplate, field_definition: ReportFieldDefinition):
        """Test validation with an invalid field."""
        # Arrange
        field_definition.field_type = "invalid_type"  # Make the field invalid
        template.add_field(field_definition)
        
        # Act
        result = template.validate()
        
        # Assert
        assert result.is_success() is False
        assert f"Invalid field '{field_definition.name}'" in result.error
    
    def test_add_field(self, template: ReportTemplate, field_definition: ReportFieldDefinition):
        """Test adding a field to the template."""
        # Act
        template.add_field(field_definition)
        
        # Assert
        assert field_definition in template.fields
        assert template in field_definition.report_templates
    
    def test_remove_field(self, template: ReportTemplate, field_definition: ReportFieldDefinition):
        """Test removing a field from the template."""
        # Arrange
        template.add_field(field_definition)
        
        # Act
        template.remove_field(field_definition)
        
        # Assert
        assert field_definition not in template.fields
        assert template not in field_definition.report_templates
    
    def test_add_trigger(self, template: ReportTemplate, trigger: ReportTrigger):
        """Test adding a trigger to the template."""
        # Act
        template.add_trigger(trigger)
        
        # Assert
        assert trigger in template.triggers
        assert trigger.report_template == template
        assert trigger.report_template_id == template.id
    
    def test_remove_trigger(self, template: ReportTemplate, trigger: ReportTrigger):
        """Test removing a trigger from the template."""
        # Arrange
        template.add_trigger(trigger)
        
        # Act
        template.remove_trigger(trigger)
        
        # Assert
        assert trigger not in template.triggers
        assert trigger.report_template is None
        assert trigger.report_template_id is None
    
    def test_add_output(self, template: ReportTemplate, output: ReportOutput):
        """Test adding an output to the template."""
        # Act
        template.add_output(output)
        
        # Assert
        assert output in template.outputs
        assert output.report_template == template
        assert output.report_template_id == template.id
    
    def test_remove_output(self, template: ReportTemplate, output: ReportOutput):
        """Test removing an output from the template."""
        # Arrange
        template.add_output(output)
        
        # Act
        template.remove_output(output)
        
        # Assert
        assert output not in template.outputs
        assert output.report_template is None
        assert output.report_template_id is None
    
    def test_add_execution(self, template: ReportTemplate, execution: ReportExecution):
        """Test adding an execution to the template."""
        # Act
        template.add_execution(execution)
        
        # Assert
        assert execution in template.executions
        assert execution.report_template == template
        assert execution.report_template_id == template.id


class TestReportTrigger:
    """Tests for ReportTrigger entity."""
    
    def test_creation(self, trigger: ReportTrigger, template_id: str):
        """Test creating a report trigger."""
        # Assert basic properties
        assert trigger.report_template_id == template_id
        assert trigger.trigger_type == ReportTriggerType.SCHEDULED
        assert trigger.trigger_config == {"timezone": "UTC"}
        assert trigger.schedule == "0 9 * * 1"
        assert trigger.is_active is True
        assert trigger.event_type is None
        assert trigger.entity_type is None
        assert trigger.query_id is None
        assert trigger.last_triggered is None
        assert trigger.report_template is None
    
    def test_validate_valid_scheduled_trigger(self, trigger: ReportTrigger):
        """Test validation with a valid scheduled trigger."""
        # Act
        result = trigger.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_invalid_trigger_type(self, trigger: ReportTrigger):
        """Test validation with an invalid trigger type."""
        # Arrange
        trigger.trigger_type = "invalid_type"
        
        # Act
        result = trigger.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Trigger type must be one of" in result.error
    
    def test_validate_scheduled_missing_schedule(self, trigger: ReportTrigger):
        """Test validation with a scheduled trigger missing schedule."""
        # Arrange
        trigger.schedule = None
        
        # Act
        result = trigger.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Scheduled triggers must include a schedule" in result.error
    
    def test_validate_event_trigger(self, trigger: ReportTrigger):
        """Test validation with an event trigger."""
        # Arrange
        trigger.trigger_type = ReportTriggerType.EVENT
        trigger.event_type = "user.created"
        
        # Act
        result = trigger.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_event_trigger_missing_event_type(self, trigger: ReportTrigger):
        """Test validation with an event trigger missing event type."""
        # Arrange
        trigger.trigger_type = ReportTriggerType.EVENT
        trigger.event_type = None
        
        # Act
        result = trigger.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Event triggers must include an event_type" in result.error
    
    def test_validate_query_trigger(self, trigger: ReportTrigger):
        """Test validation with a query trigger."""
        # Arrange
        trigger.trigger_type = ReportTriggerType.QUERY
        trigger.query_id = "query123"
        
        # Act
        result = trigger.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_query_trigger_missing_query_id(self, trigger: ReportTrigger):
        """Test validation with a query trigger missing query ID."""
        # Arrange
        trigger.trigger_type = ReportTriggerType.QUERY
        trigger.query_id = None
        
        # Act
        result = trigger.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Query triggers must include a query_id" in result.error


class TestReportOutput:
    """Tests for ReportOutput entity."""
    
    def test_creation(self, output: ReportOutput, template_id: str):
        """Test creating a report output."""
        # Assert basic properties
        assert output.report_template_id == template_id
        assert output.output_type == ReportOutputType.EMAIL
        assert output.format == ReportFormat.PDF
        assert output.output_config["recipients"] == ["user@example.com"]
        assert output.format_config["page_size"] == "A4"
        assert output.is_active is True
        assert output.report_template is None
        assert output.output_executions == []
    
    def test_validate_valid_email_output(self, output: ReportOutput):
        """Test validation with a valid email output."""
        # Act
        result = output.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_invalid_output_type(self, output: ReportOutput):
        """Test validation with an invalid output type."""
        # Arrange
        output.output_type = "invalid_type"
        
        # Act
        result = output.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Output type must be one of" in result.error
    
    def test_validate_invalid_format(self, output: ReportOutput):
        """Test validation with an invalid format."""
        # Arrange
        output.format = "invalid_format"
        
        # Act
        result = output.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Format must be one of" in result.error
    
    def test_validate_file_output_missing_path(self, output: ReportOutput):
        """Test validation with a file output missing path."""
        # Arrange
        output.output_type = ReportOutputType.FILE
        output.output_config = {}  # Missing path
        
        # Act
        result = output.validate()
        
        # Assert
        assert result.is_success() is False
        assert "File output must include a path in output_config" in result.error
    
    def test_validate_email_output_missing_recipients(self, output: ReportOutput):
        """Test validation with an email output missing recipients."""
        # Arrange
        output.output_config = {}  # Missing recipients
        
        # Act
        result = output.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Email output must include recipients in output_config" in result.error
    
    def test_validate_webhook_output_missing_url(self, output: ReportOutput):
        """Test validation with a webhook output missing URL."""
        # Arrange
        output.output_type = ReportOutputType.WEBHOOK
        output.output_config = {}  # Missing URL
        
        # Act
        result = output.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Webhook output must include a URL in output_config" in result.error
    
    def test_add_execution(self, output: ReportOutput, output_execution: ReportOutputExecution):
        """Test adding an output execution."""
        # Act
        output.add_execution(output_execution)
        
        # Assert
        assert output_execution in output.output_executions
        assert output_execution.report_output == output
        assert output_execution.report_output_id == output.id


class TestReportExecution:
    """Tests for ReportExecution entity."""
    
    def test_creation(self, execution: ReportExecution, template_id: str):
        """Test creating a report execution."""
        # Assert basic properties
        assert execution.report_template_id == template_id
        assert execution.triggered_by == "user1"
        assert execution.trigger_type == ReportTriggerType.MANUAL
        assert execution.parameters == {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
        assert execution.status == ReportExecutionStatus.PENDING
        assert execution.started_at is not None
        assert execution.completed_at is None
        assert execution.error_details is None
        assert execution.row_count is None
        assert execution.execution_time_ms is None
        assert execution.report_template is None
        assert execution.output_executions == []
    
    def test_validate_valid_execution(self, execution: ReportExecution):
        """Test validation with a valid execution."""
        # Act
        result = execution.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_invalid_status(self, execution: ReportExecution):
        """Test validation with an invalid status."""
        # Arrange
        execution.status = "invalid_status"
        
        # Act
        result = execution.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Status must be one of" in result.error
    
    def test_validate_invalid_trigger_type(self, execution: ReportExecution):
        """Test validation with an invalid trigger type."""
        # Arrange
        execution.trigger_type = "invalid_trigger"
        
        # Act
        result = execution.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Trigger type must be one of" in result.error
    
    def test_update_status_to_completed(self, execution: ReportExecution):
        """Test updating status to completed."""
        # Act
        result = execution.update_status(ReportExecutionStatus.COMPLETED)
        
        # Assert
        assert result.is_success() is True
        assert execution.status == ReportExecutionStatus.COMPLETED
        assert execution.completed_at is not None
    
    def test_update_status_to_failed_with_error(self, execution: ReportExecution):
        """Test updating status to failed with error details."""
        # Act
        result = execution.update_status(
            ReportExecutionStatus.FAILED,
            error_details="Connection timeout"
        )
        
        # Assert
        assert result.is_success() is True
        assert execution.status == ReportExecutionStatus.FAILED
        assert execution.completed_at is not None
        assert execution.error_details == "Connection timeout"
    
    def test_update_status_invalid(self, execution: ReportExecution):
        """Test updating to an invalid status."""
        # Act
        result = execution.update_status("invalid_status")
        
        # Assert
        assert result.is_success() is False
        assert "Status must be one of" in result.error
    
    def test_add_output_execution(self, execution: ReportExecution, output_execution: ReportOutputExecution):
        """Test adding an output execution."""
        # Act
        execution.add_output_execution(output_execution)
        
        # Assert
        assert output_execution in execution.output_executions
        assert output_execution.report_execution == execution
        assert output_execution.report_execution_id == execution.id


class TestReportOutputExecution:
    """Tests for ReportOutputExecution entity."""
    
    def test_creation(self, output_execution: ReportOutputExecution, execution_id: str, output_id: str):
        """Test creating a report output execution."""
        # Assert basic properties
        assert output_execution.report_execution_id == execution_id
        assert output_execution.report_output_id == output_id
        assert output_execution.status == ReportExecutionStatus.PENDING
        assert output_execution.completed_at is None
        assert output_execution.error_details is None
        assert output_execution.output_location is None
        assert output_execution.output_size_bytes is None
        assert output_execution.report_execution is None
        assert output_execution.report_output is None
    
    def test_validate_valid_output_execution(self, output_execution: ReportOutputExecution):
        """Test validation with a valid output execution."""
        # Act
        result = output_execution.validate()
        
        # Assert
        assert result.is_success() is True
    
    def test_validate_invalid_status(self, output_execution: ReportOutputExecution):
        """Test validation with an invalid status."""
        # Arrange
        output_execution.status = "invalid_status"
        
        # Act
        result = output_execution.validate()
        
        # Assert
        assert result.is_success() is False
        assert "Status must be one of" in result.error
    
    def test_update_status_to_completed(self, output_execution: ReportOutputExecution):
        """Test updating status to completed."""
        # Act
        result = output_execution.update_status(ReportExecutionStatus.COMPLETED)
        
        # Assert
        assert result.is_success() is True
        assert output_execution.status == ReportExecutionStatus.COMPLETED
        assert output_execution.completed_at is not None
    
    def test_update_status_to_failed_with_error(self, output_execution: ReportOutputExecution):
        """Test updating status to failed with error details."""
        # Act
        result = output_execution.update_status(
            ReportExecutionStatus.FAILED,
            error_details="File I/O error"
        )
        
        # Assert
        assert result.is_success() is True
        assert output_execution.status == ReportExecutionStatus.FAILED
        assert output_execution.completed_at is not None
        assert output_execution.error_details == "File I/O error"
    
    def test_update_status_invalid(self, output_execution: ReportOutputExecution):
        """Test updating to an invalid status."""
        # Act
        result = output_execution.update_status("invalid_status")
        
        # Assert
        assert result.is_success() is False
        assert "Status must be one of" in result.error