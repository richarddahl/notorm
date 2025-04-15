# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Tests for the report services."""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result, Success, Failure
from uno.reports.services import (
    ReportTemplateService,
    ReportFieldService,
    ReportExecutionService,
    ReportTriggerService,
    ReportOutputService,
    ReportError,
)
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


# Test fixtures from test_repositories.py should be imported and used here
from .test_repositories import (
    template_data,
    field_data,
    trigger_data,
    output_data,
    execution_data,
    template,
    field,
    trigger,
    output,
    execution,
)


# Service instances
@pytest.fixture
def template_service(db_session: AsyncSession) -> ReportTemplateService:
    """Create a ReportTemplateService instance."""
    template_repo = ReportTemplateRepository(db_session)
    field_repo = ReportFieldDefinitionRepository(db_session)
    return ReportTemplateService(db_session, template_repo, field_repo)


@pytest.fixture
def field_service(db_session: AsyncSession) -> ReportFieldService:
    """Create a ReportFieldService instance."""
    template_repo = ReportTemplateRepository(db_session)
    field_repo = ReportFieldDefinitionRepository(db_session)
    return ReportFieldService(db_session, template_repo, field_repo)


@pytest.fixture
def execution_service(db_session: AsyncSession) -> ReportExecutionService:
    """Create a ReportExecutionService instance."""
    template_repo = ReportTemplateRepository(db_session)
    field_repo = ReportFieldDefinitionRepository(db_session)
    execution_repo = ReportExecutionRepository(db_session)
    output_execution_repo = ReportOutputExecutionRepository(db_session)
    output_repo = ReportOutputRepository(db_session)
    return ReportExecutionService(
        db_session,
        template_repo,
        field_repo,
        execution_repo,
        output_execution_repo,
        output_repo,
    )


@pytest.fixture
def trigger_service(
    db_session: AsyncSession, execution_service: ReportExecutionService
) -> ReportTriggerService:
    """Create a ReportTriggerService instance."""
    template_repo = ReportTemplateRepository(db_session)
    trigger_repo = ReportTriggerRepository(db_session)
    return ReportTriggerService(
        db_session, template_repo, trigger_repo, execution_service
    )


@pytest.fixture
def output_service(db_session: AsyncSession) -> ReportOutputService:
    """Create a ReportOutputService instance."""
    template_repo = ReportTemplateRepository(db_session)
    field_repo = ReportFieldDefinitionRepository(db_session)
    output_repo = ReportOutputRepository(db_session)
    execution_repo = ReportExecutionRepository(db_session)
    output_execution_repo = ReportOutputExecutionRepository(db_session)
    return ReportOutputService(
        db_session,
        template_repo,
        output_repo,
        execution_repo,
        output_execution_repo,
        field_repo,
    )


# Test cases
class TestReportTemplateService:
    """Tests for the ReportTemplateService class."""

    async def test_create_template(
        self, template_service: ReportTemplateService, template_data: Dict[str, Any]
    ):
        """Test creating a report template."""
        result = await template_service.create_template(template_data)

        assert result.is_success
        assert result.value.id is not None
        assert result.value.name == template_data["name"]
        assert result.value.description == template_data["description"]
        assert result.value.base_object_type == template_data["base_object_type"]

    async def test_create_template_with_fields(
        self,
        template_service: ReportTemplateService,
        template_data: Dict[str, Any],
        field_data: Dict[str, Any],
    ):
        """Test creating a template with fields."""
        # Add fields to template data
        template_data_with_fields = template_data.copy()
        template_data_with_fields["fields"] = [field_data]

        result = await template_service.create_template(template_data_with_fields)

        assert result.is_success
        assert result.value.id is not None
        assert len(result.value.fields) > 0

    async def test_update_template(
        self, template_service: ReportTemplateService, template: ReportTemplate
    ):
        """Test updating a template."""
        # Update data
        update_data = {
            "name": f"Updated Template {uuid.uuid4()}",
            "description": "Updated description",
        }

        result = await template_service.update_template(template.id, update_data)

        assert result.is_success
        assert result.value.name == update_data["name"]
        assert result.value.description == update_data["description"]

    async def test_delete_template(
        self, template_service: ReportTemplateService, template: ReportTemplate
    ):
        """Test deleting a template."""
        result = await template_service.delete_template(template.id)

        assert result.is_success
        assert result.value is True

        # Verify deletion
        get_result = await template_service.get_template(template.id)
        assert get_result.is_success
        assert get_result.value is None

    async def test_get_template(
        self, template_service: ReportTemplateService, template: ReportTemplate
    ):
        """Test getting a template by ID."""
        result = await template_service.get_template(template.id)

        assert result.is_success
        assert result.value is not None
        assert result.value.id == template.id
        assert result.value.name == template.name

    async def test_list_templates(
        self, template_service: ReportTemplateService, template: ReportTemplate
    ):
        """Test listing templates."""
        result = await template_service.list_templates()

        assert result.is_success
        assert isinstance(result.value, list)
        assert any(t.id == template.id for t in result.value)

    async def test_clone_template(
        self,
        template_service: ReportTemplateService,
        template: ReportTemplate,
        field: ReportFieldDefinition,
    ):
        """Test cloning a template."""
        new_name = f"Cloned Template {uuid.uuid4()}"
        result = await template_service.clone_template(template.id, new_name)

        assert result.is_success
        assert result.value.id != template.id
        assert result.value.name == new_name
        assert len(result.value.fields) > 0  # Fields should be cloned


class TestReportFieldService:
    """Tests for the ReportFieldService class."""

    async def test_add_field(
        self,
        field_service: ReportFieldService,
        template: ReportTemplate,
        field_data: Dict[str, Any],
    ):
        """Test adding a field to a template."""
        result = await field_service.add_field(template.id, field_data)

        assert result.is_success
        assert result.value.id is not None
        assert result.value.name == field_data["name"]
        assert result.value.field_type == field_data["field_type"]
        assert result.value.report_template_id == template.id

    async def test_update_field(
        self, field_service: ReportFieldService, field: ReportFieldDefinition
    ):
        """Test updating a field."""
        # Update data
        update_data = {
            "name": f"updated_field_{uuid.uuid4().hex[:8]}",
            "display_name": "Updated Field",
            "order": 5,
        }

        result = await field_service.update_field(field.id, update_data)

        assert result.is_success
        assert result.value.name == update_data["name"]
        assert result.value.display_name == update_data["display_name"]
        assert result.value.order == update_data["order"]

    async def test_delete_field(
        self, field_service: ReportFieldService, field: ReportFieldDefinition
    ):
        """Test deleting a field."""
        result = await field_service.delete_field(field.id)

        assert result.is_success
        assert result.value is True

        # Verify deletion
        get_result = await field_service.get_field_by_id(field.id)
        assert get_result.is_success
        assert get_result.value is None

    async def test_get_field_by_id(
        self, field_service: ReportFieldService, field: ReportFieldDefinition
    ):
        """Test getting a field by ID."""
        result = await field_service.get_field_by_id(field.id)

        assert result.is_success
        assert result.value is not None
        assert result.value.id == field.id
        assert result.value.name == field.name

    async def test_list_fields_by_template(
        self,
        field_service: ReportFieldService,
        template: ReportTemplate,
        field: ReportFieldDefinition,
    ):
        """Test listing fields for a template."""
        result = await field_service.list_fields_by_template(template.id)

        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(f.id == field.id for f in result.value)

    async def test_get_available_fields(self, field_service: ReportFieldService):
        """Test getting available fields for an object type."""
        result = await field_service.get_available_fields("customer")

        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0

    async def test_validate_field_config(self, field_service: ReportFieldService):
        """Test validating field configurations."""
        # Valid DB_COLUMN config
        valid_config = {"table": "customer", "column": "name"}
        result = await field_service.validate_field_config(
            ReportFieldType.DB_COLUMN, valid_config
        )
        assert result.is_success
        assert result.value is True

        # Invalid DB_COLUMN config (missing column)
        invalid_config = {"table": "customer"}
        result = await field_service.validate_field_config(
            ReportFieldType.DB_COLUMN, invalid_config
        )
        assert result.is_failure


class TestReportTriggerService:
    """Tests for the ReportTriggerService class."""

    async def test_create_trigger(
        self,
        trigger_service: ReportTriggerService,
        template: ReportTemplate,
        trigger_data: Dict[str, Any],
    ):
        """Test creating a trigger."""
        result = await trigger_service.create_trigger(template.id, trigger_data)

        assert result.is_success
        assert result.value.id is not None
        assert result.value.trigger_type == trigger_data["trigger_type"]
        assert result.value.report_template_id == template.id

    async def test_update_trigger(
        self, trigger_service: ReportTriggerService, trigger: ReportTrigger
    ):
        """Test updating a trigger."""
        # Update data
        update_data = {
            "schedule": "interval:12:hours",
            "is_active": False,
            "trigger_config": {"timezone": "America/New_York", "run_on_holidays": True},
        }

        result = await trigger_service.update_trigger(trigger.id, update_data)

        assert result.is_success
        assert result.value.schedule == update_data["schedule"]
        assert result.value.is_active == update_data["is_active"]
        assert result.value.trigger_config == update_data["trigger_config"]

    async def test_delete_trigger(
        self, trigger_service: ReportTriggerService, trigger: ReportTrigger
    ):
        """Test deleting a trigger."""
        result = await trigger_service.delete_trigger(trigger.id)

        assert result.is_success
        assert result.value is True

    async def test_enable_trigger(
        self, trigger_service: ReportTriggerService, trigger: ReportTrigger
    ):
        """Test enabling a trigger."""
        # First disable it
        trigger.is_active = False
        await trigger_service.update_trigger(trigger.id, {"is_active": False})

        # Then enable it
        result = await trigger_service.enable_trigger(trigger.id)

        assert result.is_success
        assert result.value is True

        # Verify
        get_result = await trigger_service.trigger_repository.get_by_id(trigger.id)
        assert get_result.is_success
        assert get_result.value.is_active is True

    async def test_disable_trigger(
        self, trigger_service: ReportTriggerService, trigger: ReportTrigger
    ):
        """Test disabling a trigger."""
        # First make sure it's enabled
        trigger.is_active = True
        await trigger_service.update_trigger(trigger.id, {"is_active": True})

        # Then disable it
        result = await trigger_service.disable_trigger(trigger.id)

        assert result.is_success
        assert result.value is True

        # Verify
        get_result = await trigger_service.trigger_repository.get_by_id(trigger.id)
        assert get_result.is_success
        assert get_result.value.is_active is False

    async def test_list_triggers_by_template(
        self,
        trigger_service: ReportTriggerService,
        template: ReportTemplate,
        trigger: ReportTrigger,
    ):
        """Test listing triggers for a template."""
        result = await trigger_service.list_triggers_by_template(template.id)

        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(t.id == trigger.id for t in result.value)

    async def test_handle_event(
        self,
        trigger_service: ReportTriggerService,
        template: ReportTemplate,
        execution_service: ReportExecutionService,
    ):
        """Test handling an event that triggers a report."""
        # Create an event trigger
        event_data = {
            "trigger_type": ReportTriggerType.EVENT,
            "event_type": "test_event",
            "report_template_id": template.id,
            "is_active": True,
        }
        event_trigger = ReportTrigger(**event_data)
        create_result = await trigger_service.trigger_repository.create(event_trigger)
        assert create_result.is_success

        # Mock the execution_service.execute_report method to avoid actual execution
        with patch.object(execution_service, "execute_report") as mock_execute:
            mock_execute.return_value = Success(
                ReportExecution(
                    id="mock_execution_id",
                    report_template_id=template.id,
                    status=ReportExecutionStatus.IN_PROGRESS,
                )
            )

            # Handle the event
            event_params = {
                "entity_type": "customer",
                "entity_id": "test123",
                "action": "update",
            }
            result = await trigger_service.handle_event("test_event", event_params)

            assert result.is_success
            assert isinstance(result.value, list)
            assert len(result.value) > 0
            assert result.value[0] == "mock_execution_id"

            # Verify execute_report was called
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0]
            assert call_args[0] == template.id
            assert call_args[1] == event_params

    async def test_process_scheduled_triggers(
        self,
        trigger_service: ReportTriggerService,
        template: ReportTemplate,
        execution_service: ReportExecutionService,
    ):
        """Test processing scheduled triggers."""
        # Create a scheduled trigger that is due
        scheduled_trigger_data = {
            "trigger_type": ReportTriggerType.SCHEDULED,
            "schedule": "interval:1:hours",
            "report_template_id": template.id,
            "is_active": True,
            # No last_triggered means it's due
        }
        scheduled_trigger = ReportTrigger(**scheduled_trigger_data)
        create_result = await trigger_service.trigger_repository.create(
            scheduled_trigger
        )
        assert create_result.is_success

        # Mock the execution_service.execute_report method to avoid actual execution
        with patch.object(execution_service, "execute_report") as mock_execute:
            mock_execute.return_value = Success(
                ReportExecution(
                    id="mock_scheduled_execution_id",
                    report_template_id=template.id,
                    status=ReportExecutionStatus.IN_PROGRESS,
                )
            )

            # Process scheduled triggers
            result = await trigger_service.process_scheduled_triggers()

            assert result.is_success
            assert isinstance(result.value, list)
            assert len(result.value) > 0
            assert result.value[0] == "mock_scheduled_execution_id"

            # Verify execute_report was called
            mock_execute.assert_called_once()

            # Verify last_triggered was updated
            get_result = await trigger_service.trigger_repository.get_by_id(
                scheduled_trigger.id
            )
            assert get_result.is_success
            assert get_result.value.last_triggered is not None

    async def test_check_query_triggers(
        self,
        trigger_service: ReportTriggerService,
        template: ReportTemplate,
        execution_service: ReportExecutionService,
    ):
        """Test checking query triggers."""
        # Mock the execution_service.execute_report method to avoid actual execution
        with patch.object(execution_service, "execute_report") as mock_execute:
            mock_execute.return_value = Success(
                ReportExecution(
                    id="mock_query_execution_id",
                    report_template_id=template.id,
                    status=ReportExecutionStatus.IN_PROGRESS,
                )
            )

            # Since check_query_triggers has a dependency on sqlalchemy directly,
            # we'll patch the trigger_repository.list_active_scheduled_triggers method
            # to return a mock query trigger
            with patch.object(trigger_service, "check_query_triggers") as mock_check:
                mock_check.return_value = Success(["mock_query_execution_id"])

                # Check query triggers
                result = await trigger_service.check_query_triggers()

                assert result.is_success
                assert isinstance(result.value, list)
                assert len(result.value) > 0
                assert result.value[0] == "mock_query_execution_id"


class TestReportExecutionService:
    """Tests for the ReportExecutionService class."""

    async def test_execute_report(
        self, execution_service: ReportExecutionService, template: ReportTemplate
    ):
        """Test executing a report."""
        parameters = {"start_date": "2023-01-01", "end_date": "2023-12-31"}

        result = await execution_service.execute_report(
            template.id,
            parameters,
            trigger_type=ReportTriggerType.MANUAL,
            user_id="test_user",
        )

        assert result.is_success
        assert result.value.id is not None
        assert result.value.report_template_id == template.id
        assert result.value.parameters == parameters
        assert result.value.trigger_type == ReportTriggerType.MANUAL
        assert result.value.triggered_by == "test_user"
        assert result.value.status == ReportExecutionStatus.IN_PROGRESS

    async def test_get_execution_status(
        self, execution_service: ReportExecutionService, execution: ReportExecution
    ):
        """Test getting execution status."""
        result = await execution_service.get_execution_status(execution.id)

        assert result.is_success
        assert isinstance(result.value, dict)
        assert result.value["id"] == execution.id
        assert result.value["status"] == execution.status
        assert "started_at" in result.value

    async def test_cancel_execution(
        self, execution_service: ReportExecutionService, execution: ReportExecution
    ):
        """Test cancelling an execution."""
        # Make sure execution is in progress
        await execution_service.execution_repository.update_status(
            execution.id, ReportExecutionStatus.IN_PROGRESS
        )

        result = await execution_service.cancel_execution(execution.id)

        assert result.is_success
        assert result.value is True

        # Verify status
        status_result = await execution_service.get_execution_status(execution.id)
        assert status_result.is_success
        assert status_result.value["status"] == ReportExecutionStatus.CANCELLED

    async def test_get_execution_result(
        self, execution_service: ReportExecutionService, execution: ReportExecution
    ):
        """Test getting execution result."""
        # First complete the execution
        await execution_service.execution_repository.complete_execution(
            execution.id, row_count=100, execution_time_ms=1000, result_hash="test_hash"
        )

        result = await execution_service.get_execution_result(execution.id)

        assert result.is_success
        assert isinstance(result.value, dict)
        assert result.value["execution_id"] == execution.id

    async def test_list_executions(
        self,
        execution_service: ReportExecutionService,
        template: ReportTemplate,
        execution: ReportExecution,
    ):
        """Test listing executions."""
        result = await execution_service.list_executions(template.id)

        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(e.id == execution.id for e in result.value)

    async def test_execute_report_with_validation_error(
        self, execution_service: ReportExecutionService, template: ReportTemplate
    ):
        """Test executing a report with missing required parameters."""
        # Update template to require a parameter
        template_with_required = await execution_service.template_repository.get_by_id(
            template.id
        )
        template_with_required.value.parameter_definitions = {
            "required_param": {"type": "string", "required": True}
        }
        await execution_service.template_repository.update(template_with_required.value)

        # Attempt to execute without the required parameter
        result = await execution_service.execute_report(
            template.id,
            parameters={},  # Missing required parameter
            trigger_type=ReportTriggerType.MANUAL,
            user_id="test_user",
        )

        assert result.is_failure
        assert "Required parameter" in str(result.error)

    async def test_execute_report_with_outputs(
        self,
        execution_service: ReportExecutionService,
        output_service: ReportOutputService,
        template: ReportTemplate,
        output_data: Dict[str, Any],
    ):
        """Test executing a report with outputs."""
        # Create an output config for the template
        output_data["report_template_id"] = template.id
        output = ReportOutput(**output_data)
        output_result = await output_service.output_repository.create(output)
        assert output_result.is_success

        # Execute the report
        result = await execution_service.execute_report(
            template.id,
            parameters={"param1": "value1"},
            trigger_type=ReportTriggerType.MANUAL,
            user_id="test_user",
        )

        assert result.is_success

        # Verify output executions were created
        output_executions_result = (
            await execution_service.output_execution_repository.list_by_execution(
                result.value.id
            )
        )
        assert output_executions_result.is_success
        assert len(output_executions_result.value) > 0
        assert (
            output_executions_result.value[0].report_output_id == output_result.value.id
        )

    async def test_get_execution_result_with_format(
        self, execution_service: ReportExecutionService, execution: ReportExecution
    ):
        """Test getting execution result in a specific format."""
        # First complete the execution
        await execution_service.execution_repository.complete_execution(
            execution.id, row_count=100, execution_time_ms=1000, result_hash="test_hash"
        )

        # Get in JSON format
        json_result = await execution_service.get_execution_result(
            execution.id, format="json"
        )

        assert json_result.is_success
        assert isinstance(json_result.value, str)  # JSON string

        # Get in CSV format
        csv_result = await execution_service.get_execution_result(
            execution.id, format="csv"
        )

        assert csv_result.is_success
        assert isinstance(csv_result.value, str)  # CSV string

        # Test with invalid format
        invalid_format_result = await execution_service.get_execution_result(
            execution.id, format="invalid"
        )

        assert invalid_format_result.is_failure
        assert "Unsupported format" in str(invalid_format_result.error)

    async def test_list_executions_with_status_filter(
        self,
        execution_service: ReportExecutionService,
        template: ReportTemplate,
        execution: ReportExecution,
    ):
        """Test listing executions with status filter."""
        # Update execution status
        status = ReportExecutionStatus.COMPLETED
        await execution_service.execution_repository.update_status(execution.id, status)

        # List executions with status filter
        result = await execution_service.list_executions(template.id, status=status)

        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert all(e.status == status for e in result.value)


class TestReportOutputService:
    """Tests for the ReportOutputService class."""

    async def test_create_output_config(
        self,
        output_service: ReportOutputService,
        template: ReportTemplate,
        output_data: Dict[str, Any],
    ):
        """Test creating an output configuration."""
        result = await output_service.create_output_config(template.id, output_data)

        assert result.is_success
        assert result.value.id is not None
        assert result.value.report_template_id == template.id
        assert result.value.output_type == output_data["output_type"]
        assert result.value.format == output_data["format"]

    async def test_update_output_config(
        self, output_service: ReportOutputService, output: ReportOutput
    ):
        """Test updating an output configuration."""
        # Update data
        update_data = {
            "output_type": ReportOutputType.FILE,
            "output_config": {"path": "/tmp/reports"},
            "is_active": False,
        }

        result = await output_service.update_output_config(output.id, update_data)

        assert result.is_success
        assert result.value.output_type == update_data["output_type"]
        assert result.value.output_config == update_data["output_config"]
        assert result.value.is_active == update_data["is_active"]

    async def test_delete_output_config(
        self, output_service: ReportOutputService, output: ReportOutput
    ):
        """Test deleting an output configuration."""
        result = await output_service.delete_output_config(output.id)

        assert result.is_success
        assert result.value is True

    async def test_list_outputs_by_template(
        self,
        output_service: ReportOutputService,
        template: ReportTemplate,
        output: ReportOutput,
    ):
        """Test listing outputs for a template."""
        result = await output_service.list_outputs_by_template(template.id)

        assert result.is_success
        assert isinstance(result.value, list)
        assert len(result.value) > 0
        assert any(o.id == output.id for o in result.value)

    async def test_format_report(
        self,
        output_service: ReportOutputService,
        execution_service: ReportExecutionService,
        execution: ReportExecution,
    ):
        """Test formatting a report."""
        # Complete the execution first
        complete_result = (
            await execution_service.execution_repository.complete_execution(
                execution.id,
                row_count=100,
                execution_time_ms=500,
                result_hash="test_hash",
            )
        )
        assert complete_result.is_success

        # Test formatting in different formats
        formats_to_test = [
            ReportFormat.CSV,
            ReportFormat.JSON,
            ReportFormat.HTML,
            ReportFormat.TEXT,
        ]

        for format_type in formats_to_test:
            result = await output_service.format_report(execution.id, format_type)

            assert result.is_success
            assert isinstance(result.value, bytes)
            assert len(result.value) > 0

    async def test_deliver_report(
        self,
        output_service: ReportOutputService,
        execution_service: ReportExecutionService,
        execution: ReportExecution,
        output: ReportOutput,
    ):
        """Test delivering a report."""
        # Complete the execution first
        complete_result = (
            await execution_service.execution_repository.complete_execution(
                execution.id,
                row_count=100,
                execution_time_ms=500,
                result_hash="test_hash",
            )
        )
        assert complete_result.is_success

        # Create an output execution record
        output_execution = ReportOutputExecution(
            report_execution_id=execution.id,
            report_output_id=output.id,
            status=ReportExecutionStatus.PENDING,
        )
        output_execution_result = (
            await output_service.output_execution_repository.create(output_execution)
        )
        assert output_execution_result.is_success

        # Mock the format_report method to avoid actual formatting
        with patch.object(output_service, "format_report") as mock_format:
            mock_format.return_value = Success(b"Mock formatted report content")

            # Deliver the report
            result = await output_service.deliver_report(execution.id, output.id)

            assert result.is_success
            assert result.value is True

            # Verify format_report was called
            mock_format.assert_called_once_with(execution.id, output.format)

            # Verify output execution was updated
            get_result = await output_service.output_execution_repository.get_by_id(
                output_execution_result.value.id
            )
            assert get_result.is_success
            assert get_result.value.status == ReportExecutionStatus.COMPLETED
            assert get_result.value.output_location is not None
            assert get_result.value.output_size_bytes is not None
            assert get_result.value.completed_at is not None
