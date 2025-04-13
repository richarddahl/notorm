# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Tests for the report repositories."""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from uno.reports.repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)
from uno.reports.objs import (
    ReportTemplate,
    ReportFieldDefinition,
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


# Test data
@pytest.fixture
def template_data() -> Dict[str, Any]:
    """Sample report template data."""
    return {
        "name": f"Test Template {uuid.uuid4()}",
        "description": "Template for testing",
        "base_object_type": "customer",
        "format_config": {
            "title_format": "{name} - Generated on {date}",
            "show_footer": True
        },
        "parameter_definitions": {
            "start_date": {
                "type": "date",
                "required": True,
                "default": "today-30d"
            },
            "customer_type": {
                "type": "string",
                "required": False,
                "choices": ["individual", "business", "government"]
            }
        },
        "cache_policy": {
            "ttl_seconds": 3600,
            "invalidate_on_event": "customer_updated"
        },
        "version": "1.0.0"
    }


@pytest.fixture
def field_data() -> Dict[str, Any]:
    """Sample report field data."""
    return {
        "name": f"test_field_{uuid.uuid4().hex[:8]}",
        "display_name": "Test Field",
        "description": "Field for testing",
        "field_type": ReportFieldType.DB_COLUMN,
        "field_config": {
            "table": "customer",
            "column": "name"
        },
        "order": 1,
        "format_string": None,
        "conditional_formats": None,
        "is_visible": True
    }


@pytest.fixture
def trigger_data() -> Dict[str, Any]:
    """Sample report trigger data."""
    return {
        "trigger_type": ReportTriggerType.SCHEDULED,
        "trigger_config": {
            "timezone": "UTC",
            "run_on_holidays": False
        },
        "schedule": "interval:24:hours",
        "is_active": True
    }


@pytest.fixture
def output_data() -> Dict[str, Any]:
    """Sample report output data."""
    return {
        "output_type": ReportOutputType.EMAIL,
        "output_config": {
            "recipients": ["test@example.com"],
            "subject": "Test Report",
            "body": "Please find the attached report."
        },
        "format": ReportFormat.PDF,
        "format_config": {
            "page_size": "letter",
            "orientation": "portrait"
        },
        "is_active": True
    }


@pytest.fixture
def execution_data() -> Dict[str, Any]:
    """Sample report execution data."""
    return {
        "triggered_by": "test_user",
        "trigger_type": ReportTriggerType.MANUAL,
        "parameters": {
            "start_date": "2023-01-01",
            "end_date": "2023-12-31"
        },
        "status": ReportExecutionStatus.PENDING,
        "started_at": datetime.utcnow()
    }


@pytest.fixture
async def template(
    db_session: AsyncSession,
    template_data: Dict[str, Any]
) -> ReportTemplate:
    """Create a test template."""
    repo = ReportTemplateRepository(db_session)
    template = ReportTemplate(**template_data)
    result = await repo.create(template, db_session)
    assert result.is_success
    return result.value


@pytest.fixture
async def field(
    db_session: AsyncSession,
    template: ReportTemplate,
    field_data: Dict[str, Any]
) -> ReportFieldDefinition:
    """Create a test field."""
    repo = ReportFieldDefinitionRepository(db_session)
    field_data["report_template_id"] = template.id
    field = ReportFieldDefinition(**field_data)
    result = await repo.create(field, db_session)
    assert result.is_success
    return result.value


@pytest.fixture
async def trigger(
    db_session: AsyncSession,
    template: ReportTemplate,
    trigger_data: Dict[str, Any]
) -> ReportTrigger:
    """Create a test trigger."""
    repo = ReportTriggerRepository(db_session)
    trigger_data["report_template_id"] = template.id
    trigger = ReportTrigger(**trigger_data)
    result = await repo.create(trigger, db_session)
    assert result.is_success
    return result.value


@pytest.fixture
async def output(
    db_session: AsyncSession,
    template: ReportTemplate,
    output_data: Dict[str, Any]
) -> ReportOutput:
    """Create a test output."""
    repo = ReportOutputRepository(db_session)
    output_data["report_template_id"] = template.id
    output = ReportOutput(**output_data)
    result = await repo.create(output, db_session)
    assert result.is_success
    return result.value


@pytest.fixture
async def execution(
    db_session: AsyncSession,
    template: ReportTemplate,
    execution_data: Dict[str, Any]
) -> ReportExecution:
    """Create a test execution."""
    repo = ReportExecutionRepository(db_session)
    execution_data["report_template_id"] = template.id
    execution = ReportExecution(**execution_data)
    result = await repo.create(execution, db_session)
    assert result.is_success
    return result.value


# Test cases
class TestReportTemplateRepository:
    """Tests for the ReportTemplateRepository class."""

    async def test_create_template(
        self,
        db_session: AsyncSession,
        template_data: Dict[str, Any]
    ):
        """Test creating a report template."""
        repo = ReportTemplateRepository(db_session)
        template = ReportTemplate(**template_data)
        result = await repo.create(template, db_session)
        
        assert result.is_success
        assert result.value.id is not None
        assert result.value.name == template_data["name"]
        assert result.value.description == template_data["description"]
        assert result.value.base_object_type == template_data["base_object_type"]
    
    async def test_get_template_by_id(
        self,
        db_session: AsyncSession,
        template: ReportTemplate
    ):
        """Test retrieving a template by ID."""
        repo = ReportTemplateRepository(db_session)
        result = await repo.get_by_id(template.id, db_session)
        
        assert result.is_success
        assert result.value is not None
        assert result.value.id == template.id
        assert result.value.name == template.name
    
    async def test_get_template_by_name(
        self,
        db_session: AsyncSession,
        template: ReportTemplate
    ):
        """Test retrieving a template by name."""
        repo = ReportTemplateRepository(db_session)
        result = await repo.get_by_name(template.name, db_session)
        
        assert result.is_success
        assert result.value is not None
        assert result.value.id == template.id
        assert result.value.name == template.name
    
    async def test_list_templates(
        self,
        db_session: AsyncSession,
        template: ReportTemplate
    ):
        """Test listing templates."""
        repo = ReportTemplateRepository(db_session)
        result = await repo.list_templates(None, db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert any(t.id == template.id for t in result.value)
    
    async def test_update_template(
        self,
        db_session: AsyncSession,
        template: ReportTemplate
    ):
        """Test updating a template."""
        repo = ReportTemplateRepository(db_session)
        
        # Update template
        new_name = f"Updated Template {uuid.uuid4()}"
        template.name = new_name
        result = await repo.update(template, db_session)
        
        assert result.is_success
        assert result.value.name == new_name
        
        # Verify update
        get_result = await repo.get_by_id(template.id, db_session)
        assert get_result.is_success
        assert get_result.value.name == new_name
    
    async def test_delete_template(
        self,
        db_session: AsyncSession,
        template: ReportTemplate
    ):
        """Test deleting a template."""
        repo = ReportTemplateRepository(db_session)
        
        # Delete template
        result = await repo.delete(template.id, db_session)
        assert result.is_success
        assert result.value is True
        
        # Verify deletion
        get_result = await repo.get_by_id(template.id, db_session)
        assert get_result.is_success
        assert get_result.value is None


class TestReportFieldRepository:
    """Tests for the ReportFieldDefinitionRepository class."""

    async def test_create_field(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        field_data: Dict[str, Any]
    ):
        """Test creating a field."""
        repo = ReportFieldDefinitionRepository(db_session)
        field_data["report_template_id"] = template.id
        field = ReportFieldDefinition(**field_data)
        result = await repo.create(field, db_session)
        
        assert result.is_success
        assert result.value.id is not None
        assert result.value.name == field_data["name"]
        assert result.value.field_type == field_data["field_type"]
    
    async def test_get_field_by_id(
        self,
        db_session: AsyncSession,
        field: ReportFieldDefinition
    ):
        """Test retrieving a field by ID."""
        repo = ReportFieldDefinitionRepository(db_session)
        result = await repo.get_by_id(field.id, db_session)
        
        assert result.is_success
        assert result.value is not None
        assert result.value.id == field.id
        assert result.value.name == field.name
    
    async def test_list_fields_by_template(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        field: ReportFieldDefinition
    ):
        """Test listing fields for a template."""
        repo = ReportFieldDefinitionRepository(db_session)
        result = await repo.list_by_template(template.id, db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(f.id == field.id for f in result.value)
    
    async def test_update_field(
        self,
        db_session: AsyncSession,
        field: ReportFieldDefinition
    ):
        """Test updating a field."""
        repo = ReportFieldDefinitionRepository(db_session)
        
        # Update field
        new_name = f"updated_field_{uuid.uuid4().hex[:8]}"
        field.name = new_name
        result = await repo.update(field, db_session)
        
        assert result.is_success
        assert result.value.name == new_name
        
        # Verify update
        get_result = await repo.get_by_id(field.id, db_session)
        assert get_result.is_success
        assert get_result.value.name == new_name
    
    async def test_delete_field(
        self,
        db_session: AsyncSession,
        field: ReportFieldDefinition
    ):
        """Test deleting a field."""
        repo = ReportFieldDefinitionRepository(db_session)
        
        # Delete field
        result = await repo.delete(field.id, db_session)
        assert result.is_success
        assert result.value is True
        
        # Verify deletion
        get_result = await repo.get_by_id(field.id, db_session)
        assert get_result.is_success
        assert get_result.value is None
    
    async def test_bulk_create_fields(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        field_data: Dict[str, Any]
    ):
        """Test bulk creating fields."""
        repo = ReportFieldDefinitionRepository(db_session)
        
        # Create field data for bulk creation
        fields = []
        for i in range(3):
            data = field_data.copy()
            data["name"] = f"bulk_field_{i}_{uuid.uuid4().hex[:8]}"
            data["report_template_id"] = template.id
            fields.append(ReportFieldDefinition(**data))
        
        # Bulk create
        result = await repo.bulk_create(fields, db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) == 3
        assert all(f.id is not None for f in result.value)


class TestReportTriggerRepository:
    """Tests for the ReportTriggerRepository class."""

    async def test_create_trigger(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        trigger_data: Dict[str, Any]
    ):
        """Test creating a trigger."""
        repo = ReportTriggerRepository(db_session)
        trigger_data["report_template_id"] = template.id
        trigger = ReportTrigger(**trigger_data)
        result = await repo.create(trigger, db_session)
        
        assert result.is_success
        assert result.value.id is not None
        assert result.value.trigger_type == trigger_data["trigger_type"]
    
    async def test_get_trigger_by_id(
        self,
        db_session: AsyncSession,
        trigger: ReportTrigger
    ):
        """Test retrieving a trigger by ID."""
        repo = ReportTriggerRepository(db_session)
        result = await repo.get_by_id(trigger.id, db_session)
        
        assert result.is_success
        assert result.value is not None
        assert result.value.id == trigger.id
        assert result.value.trigger_type == trigger.trigger_type
    
    async def test_list_triggers_by_template(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        trigger: ReportTrigger
    ):
        """Test listing triggers for a template."""
        repo = ReportTriggerRepository(db_session)
        result = await repo.list_by_template(template.id, db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(t.id == trigger.id for t in result.value)
    
    async def test_list_by_event_type(
        self,
        db_session: AsyncSession,
        template: ReportTemplate
    ):
        """Test listing triggers by event type."""
        repo = ReportTriggerRepository(db_session)
        
        # Create event trigger
        event_trigger = ReportTrigger(
            report_template_id=template.id,
            trigger_type=ReportTriggerType.EVENT,
            event_type="test_event",
            is_active=True
        )
        create_result = await repo.create(event_trigger, db_session)
        assert create_result.is_success
        
        # List triggers by event type
        result = await repo.list_by_event_type("test_event", db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(t.id == event_trigger.id for t in result.value)
    
    async def test_list_active_scheduled_triggers(
        self,
        db_session: AsyncSession,
        trigger: ReportTrigger
    ):
        """Test listing active scheduled triggers."""
        repo = ReportTriggerRepository(db_session)
        result = await repo.list_active_scheduled_triggers(db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(t.id == trigger.id for t in result.value)
    
    async def test_update_trigger(
        self,
        db_session: AsyncSession,
        trigger: ReportTrigger
    ):
        """Test updating a trigger."""
        repo = ReportTriggerRepository(db_session)
        
        # Update trigger
        trigger.is_active = False
        result = await repo.update(trigger, db_session)
        
        assert result.is_success
        assert result.value.is_active is False
        
        # Verify update
        get_result = await repo.get_by_id(trigger.id, db_session)
        assert get_result.is_success
        assert get_result.value.is_active is False
    
    async def test_delete_trigger(
        self,
        db_session: AsyncSession,
        trigger: ReportTrigger
    ):
        """Test deleting a trigger."""
        repo = ReportTriggerRepository(db_session)
        
        # Delete trigger
        result = await repo.delete(trigger.id, db_session)
        assert result.is_success
        assert result.value is True
        
        # Verify deletion
        get_result = await repo.get_by_id(trigger.id, db_session)
        assert get_result.is_success
        assert get_result.value is None
    
    async def test_update_last_triggered(
        self,
        db_session: AsyncSession,
        trigger: ReportTrigger
    ):
        """Test updating the last_triggered timestamp."""
        repo = ReportTriggerRepository(db_session)
        
        # Update last_triggered
        now = datetime.utcnow()
        result = await repo.update_last_triggered(trigger.id, now, db_session)
        
        assert result.is_success
        assert result.value is True
        
        # Verify update
        get_result = await repo.get_by_id(trigger.id, db_session)
        assert get_result.is_success
        assert get_result.value.last_triggered is not None
        # Check dates are close (within a second)
        assert abs((get_result.value.last_triggered - now).total_seconds()) < 1


class TestReportOutputRepository:
    """Tests for the ReportOutputRepository class."""

    async def test_create_output(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        output_data: Dict[str, Any]
    ):
        """Test creating an output."""
        repo = ReportOutputRepository(db_session)
        output_data["report_template_id"] = template.id
        output = ReportOutput(**output_data)
        result = await repo.create(output, db_session)
        
        assert result.is_success
        assert result.value.id is not None
        assert result.value.output_type == output_data["output_type"]
        assert result.value.format == output_data["format"]
    
    async def test_get_output_by_id(
        self,
        db_session: AsyncSession,
        output: ReportOutput
    ):
        """Test retrieving an output by ID."""
        repo = ReportOutputRepository(db_session)
        result = await repo.get_by_id(output.id, db_session)
        
        assert result.is_success
        assert result.value is not None
        assert result.value.id == output.id
        assert result.value.output_type == output.output_type
    
    async def test_list_outputs_by_template(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        output: ReportOutput
    ):
        """Test listing outputs for a template."""
        repo = ReportOutputRepository(db_session)
        result = await repo.list_by_template(template.id, db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(o.id == output.id for o in result.value)
    
    async def test_update_output(
        self,
        db_session: AsyncSession,
        output: ReportOutput
    ):
        """Test updating an output."""
        repo = ReportOutputRepository(db_session)
        
        # Update output
        new_format = ReportFormat.JSON
        output.format = new_format
        result = await repo.update(output, db_session)
        
        assert result.is_success
        assert result.value.format == new_format
        
        # Verify update
        get_result = await repo.get_by_id(output.id, db_session)
        assert get_result.is_success
        assert get_result.value.format == new_format
    
    async def test_delete_output(
        self,
        db_session: AsyncSession,
        output: ReportOutput
    ):
        """Test deleting an output."""
        repo = ReportOutputRepository(db_session)
        
        # Delete output
        result = await repo.delete(output.id, db_session)
        assert result.is_success
        assert result.value is True
        
        # Verify deletion
        get_result = await repo.get_by_id(output.id, db_session)
        assert get_result.is_success
        assert get_result.value is None


class TestReportExecutionRepository:
    """Tests for the ReportExecutionRepository class."""

    async def test_create_execution(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        execution_data: Dict[str, Any]
    ):
        """Test creating an execution."""
        repo = ReportExecutionRepository(db_session)
        execution_data["report_template_id"] = template.id
        execution = ReportExecution(**execution_data)
        result = await repo.create(execution, db_session)
        
        assert result.is_success
        assert result.value.id is not None
        assert result.value.status == execution_data["status"]
        assert result.value.trigger_type == execution_data["trigger_type"]
    
    async def test_get_execution_by_id(
        self,
        db_session: AsyncSession,
        execution: ReportExecution
    ):
        """Test retrieving an execution by ID."""
        repo = ReportExecutionRepository(db_session)
        result = await repo.get_by_id(execution.id, db_session)
        
        assert result.is_success
        assert result.value is not None
        assert result.value.id == execution.id
        assert result.value.status == execution.status
    
    async def test_list_executions_by_template(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        execution: ReportExecution
    ):
        """Test listing executions for a template."""
        repo = ReportExecutionRepository(db_session)
        result = await repo.list_by_template(template.id, db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(e.id == execution.id for e in result.value)
    
    async def test_list_executions_by_status(
        self,
        db_session: AsyncSession,
        template: ReportTemplate,
        execution: ReportExecution
    ):
        """Test listing executions by status."""
        repo = ReportExecutionRepository(db_session)
        result = await repo.list_by_template(template.id, status=execution.status, db_session=db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert all(e.status == execution.status for e in result.value)
    
    async def test_update_execution(
        self,
        db_session: AsyncSession,
        execution: ReportExecution
    ):
        """Test updating an execution."""
        repo = ReportExecutionRepository(db_session)
        
        # Update execution
        execution.parameters = {"updated": True}
        result = await repo.update(execution, db_session)
        
        assert result.is_success
        assert result.value.parameters["updated"] is True
        
        # Verify update
        get_result = await repo.get_by_id(execution.id, db_session)
        assert get_result.is_success
        assert get_result.value.parameters["updated"] is True
    
    async def test_update_execution_status(
        self,
        db_session: AsyncSession,
        execution: ReportExecution
    ):
        """Test updating execution status."""
        repo = ReportExecutionRepository(db_session)
        
        # Update status
        new_status = ReportExecutionStatus.IN_PROGRESS
        result = await repo.update_status(execution.id, new_status, db_session=db_session)
        
        assert result.is_success
        assert result.value is True
        
        # Verify update
        get_result = await repo.get_by_id(execution.id, db_session)
        assert get_result.is_success
        assert get_result.value.status == new_status
    
    async def test_complete_execution(
        self,
        db_session: AsyncSession,
        execution: ReportExecution
    ):
        """Test completing an execution."""
        repo = ReportExecutionRepository(db_session)
        
        # Complete execution
        row_count = 100
        execution_time_ms = 1500
        result_hash = "test_hash"
        result = await repo.complete_execution(
            execution.id, 
            row_count, 
            execution_time_ms, 
            result_hash, 
            db_session
        )
        
        assert result.is_success
        assert result.value is True
        
        # Verify update
        get_result = await repo.get_by_id(execution.id, db_session)
        assert get_result.is_success
        assert get_result.value.status == ReportExecutionStatus.COMPLETED
        assert get_result.value.row_count == row_count
        assert get_result.value.execution_time_ms == execution_time_ms
        assert get_result.value.result_hash == result_hash
        assert get_result.value.completed_at is not None


class TestReportOutputExecutionRepository:
    """Tests for the ReportOutputExecutionRepository class."""

    @pytest.fixture
    async def output_execution_data(
        self,
        execution: ReportExecution,
        output: ReportOutput
    ) -> Dict[str, Any]:
        """Sample report output execution data."""
        return {
            "report_execution_id": execution.id,
            "report_output_id": output.id,
            "status": ReportExecutionStatus.PENDING
        }
    
    @pytest.fixture
    async def output_execution(
        self,
        db_session: AsyncSession,
        execution: ReportExecution,
        output: ReportOutput,
        output_execution_data: Dict[str, Any]
    ) -> ReportOutputExecution:
        """Create a test output execution."""
        repo = ReportOutputExecutionRepository(db_session)
        output_execution = ReportOutputExecution(**output_execution_data)
        result = await repo.create(output_execution, db_session)
        assert result.is_success
        return result.value
    
    async def test_create_output_execution(
        self,
        db_session: AsyncSession,
        output_execution_data: Dict[str, Any]
    ):
        """Test creating an output execution."""
        repo = ReportOutputExecutionRepository(db_session)
        output_execution = ReportOutputExecution(**output_execution_data)
        result = await repo.create(output_execution, db_session)
        
        assert result.is_success
        assert result.value.id is not None
        assert result.value.report_execution_id == output_execution_data["report_execution_id"]
        assert result.value.report_output_id == output_execution_data["report_output_id"]
    
    async def test_get_output_execution_by_id(
        self,
        db_session: AsyncSession,
        output_execution: ReportOutputExecution
    ):
        """Test retrieving an output execution by ID."""
        repo = ReportOutputExecutionRepository(db_session)
        result = await repo.get_by_id(output_execution.id, db_session)
        
        assert result.is_success
        assert result.value is not None
        assert result.value.id == output_execution.id
        assert result.value.status == output_execution.status
    
    async def test_list_output_executions_by_execution(
        self,
        db_session: AsyncSession,
        execution: ReportExecution,
        output_execution: ReportOutputExecution
    ):
        """Test listing output executions for an execution."""
        repo = ReportOutputExecutionRepository(db_session)
        result = await repo.list_by_execution(execution.id, db_session)
        
        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(oe.id == output_execution.id for oe in result.value)
    
    async def test_update_output_execution(
        self,
        db_session: AsyncSession,
        output_execution: ReportOutputExecution
    ):
        """Test updating an output execution."""
        repo = ReportOutputExecutionRepository(db_session)
        
        # Update output execution
        new_status = ReportExecutionStatus.IN_PROGRESS
        output_execution.status = new_status
        result = await repo.update(output_execution, db_session)
        
        assert result.is_success
        assert result.value.status == new_status
        
        # Verify update
        get_result = await repo.get_by_id(output_execution.id, db_session)
        assert get_result.is_success
        assert get_result.value.status == new_status
    
    async def test_complete_output_execution(
        self,
        db_session: AsyncSession,
        output_execution: ReportOutputExecution
    ):
        """Test completing an output execution."""
        repo = ReportOutputExecutionRepository(db_session)
        
        # Complete output execution
        output_location = "file:///tmp/report.pdf"
        output_size_bytes = 12345
        result = await repo.complete_output_execution(
            output_execution.id,
            output_location,
            output_size_bytes,
            db_session
        )
        
        assert result.is_success
        assert result.value is True
        
        # Verify update
        get_result = await repo.get_by_id(output_execution.id, db_session)
        assert get_result.is_success
        assert get_result.value.status == ReportExecutionStatus.COMPLETED
        assert get_result.value.output_location == output_location
        assert get_result.value.output_size_bytes == output_size_bytes
        assert get_result.value.completed_at is not None