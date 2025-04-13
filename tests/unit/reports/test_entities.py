"""Tests for the Reports module domain entities."""
import pytest
from datetime import datetime
from typing import Dict, Any, Optional

from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
)


def test_report_field_definition_creation():
    """Test creating a report field definition."""
    field = ReportFieldDefinition(
        id="field1",
        name="test_field",
        display_name="Test Field",
        field_type=ReportFieldType.DB_COLUMN,
        field_config={"table": "users", "column": "name"},
        description="A test field",
        order=1,
        format_string="{} - formatted",
        is_visible=True,
    )
    
    assert field.id == "field1"
    assert field.name == "test_field"
    assert field.display_name == "Test Field"
    assert field.field_type == ReportFieldType.DB_COLUMN
    assert field.field_config == {"table": "users", "column": "name"}
    assert field.description == "A test field"
    assert field.order == 1
    assert field.format_string == "{} - formatted"
    assert field.is_visible is True
    assert field.parent_field_id is None
    assert field.parent_field is None
    assert field.child_fields == []
    assert field.report_templates == []


def test_report_field_definition_validation_success():
    """Test successful validation of a report field definition."""
    # Test DB_COLUMN field type
    field = ReportFieldDefinition(
        id="field1",
        name="test_field",
        display_name="Test Field",
        field_type=ReportFieldType.DB_COLUMN,
        field_config={"table": "users", "column": "name"},
    )
    result = field.validate()
    assert result.is_success
    
    # Test ATTRIBUTE field type
    field = ReportFieldDefinition(
        id="field2",
        name="test_field_attr",
        display_name="Test Attribute Field",
        field_type=ReportFieldType.ATTRIBUTE,
        field_config={"attribute_type_id": "attr1"},
    )
    result = field.validate()
    assert result.is_success
    
    # Test METHOD field type
    field = ReportFieldDefinition(
        id="field3",
        name="test_field_method",
        display_name="Test Method Field",
        field_type=ReportFieldType.METHOD,
        field_config={"method": "get_data", "module": "app.reports"},
    )
    result = field.validate()
    assert result.is_success
    
    # Test QUERY field type
    field = ReportFieldDefinition(
        id="field4",
        name="test_field_query",
        display_name="Test Query Field",
        field_type=ReportFieldType.QUERY,
        field_config={"query_id": "query1"},
    )
    result = field.validate()
    assert result.is_success
    
    # Test AGGREGATE field type
    field = ReportFieldDefinition(
        id="field5",
        name="test_field_aggregate",
        display_name="Test Aggregate Field",
        field_type=ReportFieldType.AGGREGATE,
        field_config={"function": "sum", "field": "amount"},
    )
    result = field.validate()
    assert result.is_success
    
    # Test RELATED field type
    field = ReportFieldDefinition(
        id="field6",
        name="test_field_related",
        display_name="Test Related Field",
        field_type=ReportFieldType.RELATED,
        field_config={"relation": "user_profiles", "field": "bio"},
    )
    result = field.validate()
    assert result.is_success


def test_report_field_definition_validation_failure():
    """Test validation failures for report field definitions."""
    # Test invalid field type
    field = ReportFieldDefinition(
        id="field1",
        name="test_field",
        display_name="Test Field",
        field_type="invalid_type",
        field_config={},
    )
    result = field.validate()
    assert result.is_failure
    assert "Field type must be one of" in str(result.error)
    
    # Test DB_COLUMN missing required config
    field = ReportFieldDefinition(
        id="field2",
        name="test_field",
        display_name="Test Field",
        field_type=ReportFieldType.DB_COLUMN,
        field_config={},  # Missing table and column
    )
    result = field.validate()
    assert result.is_failure
    assert "Field config for DB_COLUMN must include" in str(result.error)
    
    # Test ATTRIBUTE missing required config
    field = ReportFieldDefinition(
        id="field3",
        name="test_field",
        display_name="Test Field",
        field_type=ReportFieldType.ATTRIBUTE,
        field_config={},  # Missing attribute_type_id
    )
    result = field.validate()
    assert result.is_failure
    assert "Field config for ATTRIBUTE must include attribute_type_id" in str(result.error)


def test_report_field_definition_relationships():
    """Test relationship methods for field definitions."""
    field1 = ReportFieldDefinition(
        id="field1",
        name="parent_field",
        display_name="Parent Field",
        field_type=ReportFieldType.DB_COLUMN,
        field_config={"table": "users", "column": "name"},
    )
    
    field2 = ReportFieldDefinition(
        id="field2",
        name="child_field",
        display_name="Child Field",
        field_type=ReportFieldType.DB_COLUMN,
        field_config={"table": "users", "column": "email"},
    )
    
    # Test parent-child relationship
    field1.add_child_field(field2)
    assert field2 in field1.child_fields
    assert field2.parent_field == field1
    assert field2.parent_field_id == "field1"
    
    # Test template relationship
    template = ReportTemplate(
        id="template1",
        name="Test Template",
        description="A test template",
        base_object_type="user",
    )
    
    field1.add_to_template(template)
    assert template in field1.report_templates
    assert field1 in template.fields
    
    # Test removing from template
    field1.remove_from_template(template)
    assert template not in field1.report_templates
    assert field1 not in template.fields


def test_report_template_creation():
    """Test creating a report template."""
    template = ReportTemplate(
        id="template1",
        name="Test Template",
        description="A test template",
        base_object_type="user",
        format_config={"orientation": "portrait"},
        parameter_definitions={"user_id": {"type": "string", "required": True}},
        cache_policy={"ttl": 3600},
        version="1.2.0",
    )
    
    assert template.id == "template1"
    assert template.name == "Test Template"
    assert template.description == "A test template"
    assert template.base_object_type == "user"
    assert template.format_config == {"orientation": "portrait"}
    assert template.parameter_definitions == {"user_id": {"type": "string", "required": True}}
    assert template.cache_policy == {"ttl": 3600}
    assert template.version == "1.2.0"
    assert template.fields == []
    assert template.triggers == []
    assert template.outputs == []
    assert template.executions == []


def test_report_template_validation_success():
    """Test successful validation of a report template."""
    template = ReportTemplate(
        id="template1",
        name="Test Template",
        description="A test template",
        base_object_type="user",
        parameter_definitions={"user_id": {"type": "string", "required": True}},
    )
    
    result = template.validate()
    assert result.is_success


def test_report_template_validation_failure():
    """Test validation failures for report templates."""
    # Test invalid parameter definition
    template = ReportTemplate(
        id="template1",
        name="Test Template",
        description="A test template",
        base_object_type="user",
        parameter_definitions={"user_id": "string"},  # Not a dict
    )
    
    result = template.validate()
    assert result.is_failure
    assert "Parameter definition for user_id must be a dictionary" in str(result.error)
    
    # Test parameter missing type
    template = ReportTemplate(
        id="template1",
        name="Test Template",
        description="A test template",
        base_object_type="user",
        parameter_definitions={"user_id": {"required": True}},  # Missing type
    )
    
    result = template.validate()
    assert result.is_failure
    assert "Parameter definition for user_id must include a type" in str(result.error)


def test_report_template_relationships():
    """Test relationship methods for templates."""
    template = ReportTemplate(
        id="template1",
        name="Test Template",
        description="A test template",
        base_object_type="user",
    )
    
    # Test field relationship
    field = ReportFieldDefinition(
        id="field1",
        name="test_field",
        display_name="Test Field",
        field_type=ReportFieldType.DB_COLUMN,
        field_config={"table": "users", "column": "name"},
    )
    
    template.add_field(field)
    assert field in template.fields
    assert template in field.report_templates
    
    template.remove_field(field)
    assert field not in template.fields
    assert template not in field.report_templates
    
    # Test trigger relationship
    trigger = ReportTrigger(
        id="trigger1",
        report_template_id="",  # Will be set by add_trigger
        trigger_type=ReportTriggerType.MANUAL,
    )
    
    template.add_trigger(trigger)
    assert trigger in template.triggers
    assert trigger.report_template == template
    assert trigger.report_template_id == "template1"
    
    template.remove_trigger(trigger)
    assert trigger not in template.triggers
    assert trigger.report_template is None
    assert trigger.report_template_id is None
    
    # Test output relationship
    output = ReportOutput(
        id="output1",
        report_template_id="",  # Will be set by add_output
        output_type=ReportOutputType.FILE,
        format=ReportFormat.PDF,
        output_config={"path": "/reports"},
    )
    
    template.add_output(output)
    assert output in template.outputs
    assert output.report_template == template
    assert output.report_template_id == "template1"
    
    template.remove_output(output)
    assert output not in template.outputs
    assert output.report_template is None
    assert output.report_template_id is None
    
    # Test execution relationship
    execution = ReportExecution(
        id="execution1",
        report_template_id="",  # Will be set by add_execution
        triggered_by="user1",
        trigger_type=ReportTriggerType.MANUAL,
    )
    
    template.add_execution(execution)
    assert execution in template.executions
    assert execution.report_template == template
    assert execution.report_template_id == "template1"


def test_report_trigger_creation():
    """Test creating a report trigger."""
    # Test manual trigger
    trigger = ReportTrigger(
        id="trigger1",
        report_template_id="template1",
        trigger_type=ReportTriggerType.MANUAL,
    )
    
    assert trigger.id == "trigger1"
    assert trigger.report_template_id == "template1"
    assert trigger.trigger_type == ReportTriggerType.MANUAL
    assert trigger.trigger_config == {}
    assert trigger.schedule is None
    assert trigger.event_type is None
    assert trigger.entity_type is None
    assert trigger.query_id is None
    assert trigger.is_active is True
    assert trigger.last_triggered is None
    
    # Test scheduled trigger
    trigger = ReportTrigger(
        id="trigger2",
        report_template_id="template1",
        trigger_type=ReportTriggerType.SCHEDULED,
        schedule="0 0 * * *",  # Daily at midnight
    )
    
    assert trigger.schedule == "0 0 * * *"
    
    # Test event trigger
    trigger = ReportTrigger(
        id="trigger3",
        report_template_id="template1",
        trigger_type=ReportTriggerType.EVENT,
        event_type="user.created",
        entity_type="user",
    )
    
    assert trigger.event_type == "user.created"
    assert trigger.entity_type == "user"
    
    # Test query trigger
    trigger = ReportTrigger(
        id="trigger4",
        report_template_id="template1",
        trigger_type=ReportTriggerType.QUERY,
        query_id="query1",
    )
    
    assert trigger.query_id == "query1"


def test_report_trigger_validation_success():
    """Test successful validation of report triggers."""
    # Test manual trigger
    trigger = ReportTrigger(
        id="trigger1",
        report_template_id="template1",
        trigger_type=ReportTriggerType.MANUAL,
    )
    
    result = trigger.validate()
    assert result.is_success
    
    # Test scheduled trigger
    trigger = ReportTrigger(
        id="trigger2",
        report_template_id="template1",
        trigger_type=ReportTriggerType.SCHEDULED,
        schedule="0 0 * * *",
    )
    
    result = trigger.validate()
    assert result.is_success
    
    # Test event trigger
    trigger = ReportTrigger(
        id="trigger3",
        report_template_id="template1",
        trigger_type=ReportTriggerType.EVENT,
        event_type="user.created",
    )
    
    result = trigger.validate()
    assert result.is_success
    
    # Test query trigger
    trigger = ReportTrigger(
        id="trigger4",
        report_template_id="template1",
        trigger_type=ReportTriggerType.QUERY,
        query_id="query1",
    )
    
    result = trigger.validate()
    assert result.is_success


def test_report_trigger_validation_failure():
    """Test validation failures for report triggers."""
    # Test invalid trigger type
    trigger = ReportTrigger(
        id="trigger1",
        report_template_id="template1",
        trigger_type="invalid_type",
    )
    
    result = trigger.validate()
    assert result.is_failure
    assert "Trigger type must be one of" in str(result.error)
    
    # Test scheduled trigger missing schedule
    trigger = ReportTrigger(
        id="trigger2",
        report_template_id="template1",
        trigger_type=ReportTriggerType.SCHEDULED,
        # Missing schedule
    )
    
    result = trigger.validate()
    assert result.is_failure
    assert "Scheduled triggers must include a schedule" in str(result.error)
    
    # Test event trigger missing event_type
    trigger = ReportTrigger(
        id="trigger3",
        report_template_id="template1",
        trigger_type=ReportTriggerType.EVENT,
        # Missing event_type
    )
    
    result = trigger.validate()
    assert result.is_failure
    assert "Event triggers must include an event_type" in str(result.error)
    
    # Test query trigger missing query_id
    trigger = ReportTrigger(
        id="trigger4",
        report_template_id="template1",
        trigger_type=ReportTriggerType.QUERY,
        # Missing query_id
    )
    
    result = trigger.validate()
    assert result.is_failure
    assert "Query triggers must include a query_id" in str(result.error)


def test_report_output_creation():
    """Test creating a report output."""
    output = ReportOutput(
        id="output1",
        report_template_id="template1",
        output_type=ReportOutputType.FILE,
        format=ReportFormat.PDF,
        output_config={"path": "/reports"},
        format_config={"page_size": "A4"},
    )
    
    assert output.id == "output1"
    assert output.report_template_id == "template1"
    assert output.output_type == ReportOutputType.FILE
    assert output.format == ReportFormat.PDF
    assert output.output_config == {"path": "/reports"}
    assert output.format_config == {"page_size": "A4"}
    assert output.is_active is True
    assert output.report_template is None
    assert output.output_executions == []


def test_report_output_validation_success():
    """Test successful validation of report outputs."""
    # Test file output
    output = ReportOutput(
        id="output1",
        report_template_id="template1",
        output_type=ReportOutputType.FILE,
        format=ReportFormat.PDF,
        output_config={"path": "/reports"},
    )
    
    result = output.validate()
    assert result.is_success
    
    # Test email output
    output = ReportOutput(
        id="output2",
        report_template_id="template1",
        output_type=ReportOutputType.EMAIL,
        format=ReportFormat.PDF,
        output_config={"recipients": ["user@example.com"]},
    )
    
    result = output.validate()
    assert result.is_success
    
    # Test webhook output
    output = ReportOutput(
        id="output3",
        report_template_id="template1",
        output_type=ReportOutputType.WEBHOOK,
        format=ReportFormat.JSON,
        output_config={"url": "https://example.com/webhook"},
    )
    
    result = output.validate()
    assert result.is_success


def test_report_output_validation_failure():
    """Test validation failures for report outputs."""
    # Test invalid output type
    output = ReportOutput(
        id="output1",
        report_template_id="template1",
        output_type="invalid_type",
        format=ReportFormat.PDF,
    )
    
    result = output.validate()
    assert result.is_failure
    assert "Output type must be one of" in str(result.error)
    
    # Test invalid format
    output = ReportOutput(
        id="output2",
        report_template_id="template1",
        output_type=ReportOutputType.FILE,
        format="invalid_format",
    )
    
    result = output.validate()
    assert result.is_failure
    assert "Format must be one of" in str(result.error)
    
    # Test file output missing path
    output = ReportOutput(
        id="output3",
        report_template_id="template1",
        output_type=ReportOutputType.FILE,
        format=ReportFormat.PDF,
        output_config={},  # Missing path
    )
    
    result = output.validate()
    assert result.is_failure
    assert "File output must include a path in output_config" in str(result.error)
    
    # Test email output missing recipients
    output = ReportOutput(
        id="output4",
        report_template_id="template1",
        output_type=ReportOutputType.EMAIL,
        format=ReportFormat.PDF,
        output_config={},  # Missing recipients
    )
    
    result = output.validate()
    assert result.is_failure
    assert "Email output must include recipients in output_config" in str(result.error)
    
    # Test webhook output missing url
    output = ReportOutput(
        id="output5",
        report_template_id="template1",
        output_type=ReportOutputType.WEBHOOK,
        format=ReportFormat.JSON,
        output_config={},  # Missing url
    )
    
    result = output.validate()
    assert result.is_failure
    assert "Webhook output must include a URL in output_config" in str(result.error)


def test_report_output_relationships():
    """Test relationship methods for outputs."""
    output = ReportOutput(
        id="output1",
        report_template_id="template1",
        output_type=ReportOutputType.FILE,
        format=ReportFormat.PDF,
        output_config={"path": "/reports"},
    )
    
    # Test execution relationship
    output_execution = ReportOutputExecution(
        id="output_execution1",
        report_execution_id="execution1",
        report_output_id="output1",
    )
    
    output.add_execution(output_execution)
    assert output_execution in output.output_executions
    assert output_execution.report_output == output
    assert output_execution.report_output_id == "output1"


def test_report_execution_creation():
    """Test creating a report execution."""
    execution = ReportExecution(
        id="execution1",
        report_template_id="template1",
        triggered_by="user1",
        trigger_type=ReportTriggerType.MANUAL,
        parameters={"user_id": "user123"},
        status=ReportExecutionStatus.PENDING,
    )
    
    assert execution.id == "execution1"
    assert execution.report_template_id == "template1"
    assert execution.triggered_by == "user1"
    assert execution.trigger_type == ReportTriggerType.MANUAL
    assert execution.parameters == {"user_id": "user123"}
    assert execution.status == ReportExecutionStatus.PENDING
    assert isinstance(execution.started_at, datetime)
    assert execution.completed_at is None
    assert execution.error_details is None
    assert execution.row_count is None
    assert execution.execution_time_ms is None
    assert execution.result_hash is None
    assert execution.report_template is None
    assert execution.output_executions == []


def test_report_execution_validation_success():
    """Test successful validation of report executions."""
    execution = ReportExecution(
        id="execution1",
        report_template_id="template1",
        triggered_by="user1",
        trigger_type=ReportTriggerType.MANUAL,
        status=ReportExecutionStatus.PENDING,
    )
    
    result = execution.validate()
    assert result.is_success


def test_report_execution_validation_failure():
    """Test validation failures for report executions."""
    # Test invalid status
    execution = ReportExecution(
        id="execution1",
        report_template_id="template1",
        triggered_by="user1",
        trigger_type=ReportTriggerType.MANUAL,
        status="invalid_status",
    )
    
    result = execution.validate()
    assert result.is_failure
    assert "Status must be one of" in str(result.error)
    
    # Test invalid trigger type
    execution = ReportExecution(
        id="execution2",
        report_template_id="template1",
        triggered_by="user1",
        trigger_type="invalid_type",
        status=ReportExecutionStatus.PENDING,
    )
    
    result = execution.validate()
    assert result.is_failure
    assert "Trigger type must be one of" in str(result.error)


def test_report_execution_update_status():
    """Test updating the status of a report execution."""
    execution = ReportExecution(
        id="execution1",
        report_template_id="template1",
        triggered_by="user1",
        trigger_type=ReportTriggerType.MANUAL,
        status=ReportExecutionStatus.PENDING,
    )
    
    # Test updating to running
    result = execution.update_status(ReportExecutionStatus.RUNNING)
    assert result.is_success
    assert execution.status == ReportExecutionStatus.RUNNING
    assert execution.completed_at is None
    assert execution.error_details is None
    
    # Test updating to completed
    result = execution.update_status(ReportExecutionStatus.COMPLETED)
    assert result.is_success
    assert execution.status == ReportExecutionStatus.COMPLETED
    assert execution.completed_at is not None
    assert execution.error_details is None
    
    # Test updating to failed with error details
    execution.completed_at = None  # Reset for test
    result = execution.update_status(ReportExecutionStatus.FAILED, "Error processing report")
    assert result.is_success
    assert execution.status == ReportExecutionStatus.FAILED
    assert execution.completed_at is not None
    assert execution.error_details == "Error processing report"
    
    # Test invalid status
    result = execution.update_status("invalid_status")
    assert result.is_failure
    assert "Status must be one of" in str(result.error)
    # Status should not change on error
    assert execution.status == ReportExecutionStatus.FAILED


def test_report_execution_relationships():
    """Test relationship methods for executions."""
    execution = ReportExecution(
        id="execution1",
        report_template_id="template1",
        triggered_by="user1",
        trigger_type=ReportTriggerType.MANUAL,
        status=ReportExecutionStatus.PENDING,
    )
    
    # Test output execution relationship
    output_execution = ReportOutputExecution(
        id="output_execution1",
        report_execution_id="",  # Will be set by add_output_execution
        report_output_id="output1",
    )
    
    execution.add_output_execution(output_execution)
    assert output_execution in execution.output_executions
    assert output_execution.report_execution == execution
    assert output_execution.report_execution_id == "execution1"


def test_report_output_execution_creation():
    """Test creating a report output execution."""
    output_execution = ReportOutputExecution(
        id="output_execution1",
        report_execution_id="execution1",
        report_output_id="output1",
        status=ReportExecutionStatus.PENDING,
    )
    
    assert output_execution.id == "output_execution1"
    assert output_execution.report_execution_id == "execution1"
    assert output_execution.report_output_id == "output1"
    assert output_execution.status == ReportExecutionStatus.PENDING
    assert output_execution.completed_at is None
    assert output_execution.error_details is None
    assert output_execution.output_location is None
    assert output_execution.output_size_bytes is None
    assert output_execution.report_execution is None
    assert output_execution.report_output is None


def test_report_output_execution_validation_success():
    """Test successful validation of report output executions."""
    output_execution = ReportOutputExecution(
        id="output_execution1",
        report_execution_id="execution1",
        report_output_id="output1",
        status=ReportExecutionStatus.PENDING,
    )
    
    result = output_execution.validate()
    assert result.is_success


def test_report_output_execution_validation_failure():
    """Test validation failures for report output executions."""
    # Test invalid status
    output_execution = ReportOutputExecution(
        id="output_execution1",
        report_execution_id="execution1",
        report_output_id="output1",
        status="invalid_status",
    )
    
    result = output_execution.validate()
    assert result.is_failure
    assert "Status must be one of" in str(result.error)


def test_report_output_execution_update_status():
    """Test updating the status of a report output execution."""
    output_execution = ReportOutputExecution(
        id="output_execution1",
        report_execution_id="execution1",
        report_output_id="output1",
        status=ReportExecutionStatus.PENDING,
    )
    
    # Test updating to running
    result = output_execution.update_status(ReportExecutionStatus.RUNNING)
    assert result.is_success
    assert output_execution.status == ReportExecutionStatus.RUNNING
    assert output_execution.completed_at is None
    assert output_execution.error_details is None
    
    # Test updating to completed
    result = output_execution.update_status(ReportExecutionStatus.COMPLETED)
    assert result.is_success
    assert output_execution.status == ReportExecutionStatus.COMPLETED
    assert output_execution.completed_at is not None
    assert output_execution.error_details is None
    
    # Test updating to failed with error details
    output_execution.completed_at = None  # Reset for test
    result = output_execution.update_status(ReportExecutionStatus.FAILED, "Error delivering report")
    assert result.is_success
    assert output_execution.status == ReportExecutionStatus.FAILED
    assert output_execution.completed_at is not None
    assert output_execution.error_details == "Error delivering report"
    
    # Test invalid status
    result = output_execution.update_status("invalid_status")
    assert result.is_failure
    assert "Status must be one of" in str(result.error)
    # Status should not change on error
    assert output_execution.status == ReportExecutionStatus.FAILED