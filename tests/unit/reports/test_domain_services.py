# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Tests for the report domain services."""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, patch, MagicMock

from uno.core.errors.result import Result, Success, Failure
from uno.reports.domain_services import (
    ReportFieldDefinitionService,
    ReportTemplateService,
    ReportTriggerService,
    ReportOutputService,
    ReportExecutionService,
    ReportOutputExecutionService,
)
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


# Mock fixtures for testing
@pytest.fixture
def mock_field_repo():
    """Create a mock field definition repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_template_repo():
    """Create a mock template repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_trigger_repo():
    """Create a mock trigger repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_output_repo():
    """Create a mock output repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_execution_repo():
    """Create a mock execution repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_output_execution_repo():
    """Create a mock output execution repository."""
    repo = AsyncMock()
    return repo


# Service fixtures
@pytest.fixture
def field_definition_service(mock_field_repo):
    """Create a field definition service with a mock repository."""
    return ReportFieldDefinitionService(mock_field_repo)


@pytest.fixture
def output_execution_service(mock_output_execution_repo):
    """Create an output execution service with a mock repository."""
    return ReportOutputExecutionService(mock_output_execution_repo)


@pytest.fixture
def execution_service(mock_execution_repo):
    """Create an execution service with a mock repository."""
    return ReportExecutionService(mock_execution_repo)


@pytest.fixture
def output_service(mock_output_repo):
    """Create an output service with a mock repository."""
    return ReportOutputService(mock_output_repo)


@pytest.fixture
def trigger_service(mock_trigger_repo):
    """Create a trigger service with a mock repository."""
    return ReportTriggerService(mock_trigger_repo)


@pytest.fixture
def template_service(mock_template_repo, field_definition_service, trigger_service, output_service):
    """Create a template service with mock dependencies."""
    return ReportTemplateService(
        mock_template_repo,
        field_definition_service,
        trigger_service,
        output_service
    )


# Entity fixture generators
@pytest.fixture
def create_field_definition():
    """Create a field definition entity for testing."""
    def _create_field(id_=None, name=None, field_type=None, parent_field_id=None):
        return ReportFieldDefinition(
            id=id_ or str(uuid.uuid4()),
            name=name or f"test_field_{uuid.uuid4().hex[:8]}",
            display_name="Test Field",
            field_type=field_type or ReportFieldType.DB_COLUMN,
            field_config={"table": "customer", "column": "name"},
            description="Field for testing",
            order=1,
            format_string=None,
            conditional_formats=None,
            is_visible=True,
            parent_field_id=parent_field_id
        )
    return _create_field


@pytest.fixture
def create_template():
    """Create a template entity for testing."""
    def _create_template(id_=None, name=None, base_object_type=None):
        return ReportTemplate(
            id=id_ or str(uuid.uuid4()),
            name=name or f"Test Template {uuid.uuid4()}",
            description="Template for testing",
            base_object_type=base_object_type or "customer",
            format_config={
                "title_format": "{name} - Generated on {date}",
                "show_footer": True
            },
            parameter_definitions={
                "start_date": {
                    "type": "date",
                    "required": True,
                    "default": "today-30d"
                }
            },
            cache_policy={
                "ttl_seconds": 3600,
                "invalidate_on_event": "customer_updated"
            },
            version="1.0.0"
        )
    return _create_template


@pytest.fixture
def create_trigger():
    """Create a trigger entity for testing."""
    def _create_trigger(id_=None, template_id=None, trigger_type=None):
        return ReportTrigger(
            id=id_ or str(uuid.uuid4()),
            report_template_id=template_id or str(uuid.uuid4()),
            trigger_type=trigger_type or ReportTriggerType.SCHEDULED,
            trigger_config={
                "timezone": "UTC",
                "run_on_holidays": False
            },
            schedule="interval:24:hours",
            is_active=True
        )
    return _create_trigger


@pytest.fixture
def create_output():
    """Create an output entity for testing."""
    def _create_output(id_=None, template_id=None, output_type=None):
        return ReportOutput(
            id=id_ or str(uuid.uuid4()),
            report_template_id=template_id or str(uuid.uuid4()),
            output_type=output_type or ReportOutputType.EMAIL,
            format=ReportFormat.PDF,
            output_config={
                "recipients": ["test@example.com"],
                "subject": "Test Report"
            },
            format_config={
                "page_size": "letter",
                "orientation": "portrait"
            },
            is_active=True
        )
    return _create_output


@pytest.fixture
def create_execution():
    """Create an execution entity for testing."""
    def _create_execution(id_=None, template_id=None, status=None):
        return ReportExecution(
            id=id_ or str(uuid.uuid4()),
            report_template_id=template_id or str(uuid.uuid4()),
            triggered_by="test_user",
            trigger_type=ReportTriggerType.MANUAL,
            parameters={
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            },
            status=status or ReportExecutionStatus.PENDING,
            started_at=datetime.utcnow()
        )
    return _create_execution


@pytest.fixture
def create_output_execution():
    """Create an output execution entity for testing."""
    def _create_output_execution(id_=None, execution_id=None, output_id=None, status=None):
        return ReportOutputExecution(
            id=id_ or str(uuid.uuid4()),
            report_execution_id=execution_id or str(uuid.uuid4()),
            report_output_id=output_id or str(uuid.uuid4()),
            status=status or ReportExecutionStatus.PENDING
        )
    return _create_output_execution


class TestReportFieldDefinitionService:
    """Tests for the ReportFieldDefinitionService class."""

    async def test_find_by_name(self, field_definition_service, mock_field_repo, create_field_definition):
        """Test finding a field definition by name."""
        # Arrange
        field = create_field_definition(name="test_field")
        mock_field_repo.find_by_name.return_value = field
        
        # Act
        result = await field_definition_service.find_by_name("test_field")
        
        # Assert
        mock_field_repo.find_by_name.assert_called_once_with("test_field")
        assert result.is_success
        assert result.value == field

    async def test_find_by_name_exception(self, field_definition_service, mock_field_repo):
        """Test finding a field definition by name when an exception occurs."""
        # Arrange
        mock_field_repo.find_by_name.side_effect = Exception("Test error")
        
        # Act
        result = await field_definition_service.find_by_name("test_field")
        
        # Assert
        mock_field_repo.find_by_name.assert_called_once_with("test_field")
        assert result.is_failure
        assert "Test error" in str(result.error)

    async def test_find_by_field_type(self, field_definition_service, mock_field_repo, create_field_definition):
        """Test finding field definitions by field type."""
        # Arrange
        fields = [
            create_field_definition(field_type=ReportFieldType.DB_COLUMN),
            create_field_definition(field_type=ReportFieldType.DB_COLUMN)
        ]
        mock_field_repo.find_by_field_type.return_value = fields
        
        # Act
        result = await field_definition_service.find_by_field_type(ReportFieldType.DB_COLUMN)
        
        # Assert
        mock_field_repo.find_by_field_type.assert_called_once_with(ReportFieldType.DB_COLUMN)
        assert result.is_success
        assert result.value == fields

    async def test_find_by_parent_field_id(self, field_definition_service, mock_field_repo, create_field_definition):
        """Test finding field definitions by parent field ID."""
        # Arrange
        parent_id = str(uuid.uuid4())
        fields = [
            create_field_definition(parent_field_id=parent_id),
            create_field_definition(parent_field_id=parent_id)
        ]
        mock_field_repo.find_by_parent_field_id.return_value = fields
        
        # Act
        result = await field_definition_service.find_by_parent_field_id(parent_id)
        
        # Assert
        mock_field_repo.find_by_parent_field_id.assert_called_once_with(parent_id)
        assert result.is_success
        assert result.value == fields

    async def test_find_by_template_id(self, field_definition_service, mock_field_repo, create_field_definition):
        """Test finding field definitions by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        fields = [
            create_field_definition(),
            create_field_definition()
        ]
        mock_field_repo.find_by_template_id.return_value = fields
        
        # Act
        result = await field_definition_service.find_by_template_id(template_id)
        
        # Assert
        mock_field_repo.find_by_template_id.assert_called_once_with(template_id)
        assert result.is_success
        assert result.value == fields


class TestReportTemplateService:
    """Tests for the ReportTemplateService class."""

    async def test_find_by_name(self, template_service, mock_template_repo, create_template):
        """Test finding a template by name."""
        # Arrange
        template = create_template(name="test_template")
        mock_template_repo.find_by_name.return_value = template
        
        # Act
        result = await template_service.find_by_name("test_template")
        
        # Assert
        mock_template_repo.find_by_name.assert_called_once_with("test_template")
        assert result.is_success
        assert result.value == template

    async def test_find_by_base_object_type(self, template_service, mock_template_repo, create_template):
        """Test finding templates by base object type."""
        # Arrange
        templates = [
            create_template(base_object_type="customer"),
            create_template(base_object_type="customer")
        ]
        mock_template_repo.find_by_base_object_type.return_value = templates
        
        # Act
        result = await template_service.find_by_base_object_type("customer")
        
        # Assert
        mock_template_repo.find_by_base_object_type.assert_called_once_with("customer")
        assert result.is_success
        assert result.value == templates

    async def test_get_with_relationships(self, template_service, mock_template_repo, create_template):
        """Test getting a template with all relationships loaded."""
        # Arrange
        template_id = str(uuid.uuid4())
        template = create_template(id_=template_id)
        mock_template_repo.find_with_relationships.return_value = Success(template)
        
        # Act
        result = await template_service.get_with_relationships(template_id)
        
        # Assert
        mock_template_repo.find_with_relationships.assert_called_once_with(template_id)
        assert result.is_success
        assert result.value == template

    async def test_create_with_relationships_success(self, template_service, mock_template_repo, create_template, field_definition_service):
        """Test creating a template with field relationships."""
        # Arrange
        template = create_template()
        field_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        
        # Mock repository methods
        mock_template_repo.create.return_value = Success(template)
        mock_template_repo.update = AsyncMock()
        mock_template_repo.find_with_relationships.return_value = Success(template)
        
        # Mock field service
        field_definition_service.get = AsyncMock(return_value=Success(ReportFieldDefinition(
            id=field_ids[0],
            name="Test Field",
            display_name="Test Field",
            field_type=ReportFieldType.DB_COLUMN,
            field_config={"table": "customer", "column": "name"}
        )))
        
        # Act
        result = await template_service.create_with_relationships(template, field_ids)
        
        # Assert
        mock_template_repo.create.assert_called_once_with(template)
        mock_template_repo.update.assert_called_once()
        mock_template_repo.find_with_relationships.assert_called_once_with(template.id)
        assert result.is_success
        assert result.value == template

    async def test_update_fields(self, template_service, mock_template_repo, create_template, field_definition_service, create_field_definition):
        """Test updating the fields associated with a template."""
        # Arrange
        template_id = str(uuid.uuid4())
        template = create_template(id_=template_id)
        
        # Create existing fields
        existing_field_id = str(uuid.uuid4())
        existing_field = create_field_definition(id_=existing_field_id)
        template.fields = [existing_field]
        
        # Create new field to add
        new_field_id = str(uuid.uuid4())
        new_field = create_field_definition(id_=new_field_id)
        
        # Field IDs to add and remove
        field_ids_to_add = [new_field_id]
        field_ids_to_remove = [existing_field_id]
        
        # Mock repository methods
        mock_template_repo.find_with_relationships.return_value = Success(template)
        mock_template_repo.update = AsyncMock()
        
        # Mock field service
        field_definition_service.get = AsyncMock(return_value=Success(new_field))
        
        # Act
        result = await template_service.update_fields(
            template_id=template_id,
            field_ids_to_add=field_ids_to_add,
            field_ids_to_remove=field_ids_to_remove
        )
        
        # Assert
        mock_template_repo.find_with_relationships.assert_called_once_with(template_id)
        mock_template_repo.update.assert_called_once_with(template)
        assert result.is_success

    @patch("uno.dependencies.get_service")
    async def test_execute_template(self, mock_get_service, template_service, mock_template_repo, create_template):
        """Test executing a report template."""
        # Arrange
        template_id = str(uuid.uuid4())
        template = create_template(id_=template_id)
        template.outputs = [
            ReportOutput(
                id=str(uuid.uuid4()),
                report_template_id=template_id,
                output_type=ReportOutputType.EMAIL,
                format=ReportFormat.PDF,
                is_active=True
            )
        ]
        
        # Mock parameters
        triggered_by = "test_user"
        trigger_type = ReportTriggerType.MANUAL
        parameters = {"param1": "value1"}
        
        # Mock repository methods
        mock_template_repo.find_with_relationships.return_value = Success(template)
        
        # Mock execution repository
        mock_execution_repo = AsyncMock()
        mock_execution_repo.create.return_value = Success(ReportExecution(
            id=str(uuid.uuid4()),
            report_template_id=template_id,
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            parameters=parameters
        ))
        
        # Mock output execution repository
        mock_output_execution_repo = AsyncMock()
        mock_output_execution_repo.create.return_value = Success(ReportOutputExecution(
            id=str(uuid.uuid4()),
            report_execution_id="",
            report_output_id=""
        ))
        
        # Mock get_service
        mock_get_service.side_effect = lambda cls: mock_execution_repo if cls == ReportExecutionRepository else mock_output_execution_repo
        
        # Act
        result = await template_service.execute_template(
            template_id=template_id,
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            parameters=parameters
        )
        
        # Assert
        mock_template_repo.find_with_relationships.assert_called_once_with(template_id)
        mock_execution_repo.create.assert_called_once()
        assert result.is_success
        assert result.value.report_template_id == template_id
        assert result.value.triggered_by == triggered_by
        assert result.value.trigger_type == trigger_type
        assert result.value.parameters == parameters


class TestReportTriggerService:
    """Tests for the ReportTriggerService class."""

    async def test_find_by_template_id(self, trigger_service, mock_trigger_repo, create_trigger):
        """Test finding triggers by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        triggers = [
            create_trigger(template_id=template_id),
            create_trigger(template_id=template_id)
        ]
        mock_trigger_repo.find_by_template_id.return_value = triggers
        
        # Act
        result = await trigger_service.find_by_template_id(template_id)
        
        # Assert
        mock_trigger_repo.find_by_template_id.assert_called_once_with(template_id)
        assert result.is_success
        assert result.value == triggers

    async def test_find_by_trigger_type(self, trigger_service, mock_trigger_repo, create_trigger):
        """Test finding triggers by trigger type."""
        # Arrange
        trigger_type = ReportTriggerType.SCHEDULED
        triggers = [
            create_trigger(trigger_type=trigger_type),
            create_trigger(trigger_type=trigger_type)
        ]
        mock_trigger_repo.find_by_trigger_type.return_value = triggers
        
        # Act
        result = await trigger_service.find_by_trigger_type(trigger_type)
        
        # Assert
        mock_trigger_repo.find_by_trigger_type.assert_called_once_with(trigger_type)
        assert result.is_success
        assert result.value == triggers

    async def test_find_active_triggers(self, trigger_service, mock_trigger_repo, create_trigger):
        """Test finding all active triggers."""
        # Arrange
        triggers = [create_trigger(), create_trigger()]
        mock_trigger_repo.find_active_triggers.return_value = triggers
        
        # Act
        result = await trigger_service.find_active_triggers()
        
        # Assert
        mock_trigger_repo.find_active_triggers.assert_called_once()
        assert result.is_success
        assert result.value == triggers

    async def test_find_active_scheduled_triggers(self, trigger_service, mock_trigger_repo, create_trigger):
        """Test finding active scheduled triggers."""
        # Arrange
        triggers = [
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED),
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED)
        ]
        mock_trigger_repo.find_active_scheduled_triggers.return_value = triggers
        
        # Act
        result = await trigger_service.find_active_scheduled_triggers()
        
        # Assert
        mock_trigger_repo.find_active_scheduled_triggers.assert_called_once()
        assert result.is_success
        assert result.value == triggers

    @patch("uno.dependencies.get_service")
    async def test_process_due_triggers(self, mock_get_service, trigger_service, mock_trigger_repo, create_trigger):
        """Test processing all due scheduled triggers."""
        # Arrange
        triggers = [
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED),
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED)
        ]
        
        # Mock repository methods
        mock_trigger_repo.find_active_scheduled_triggers.return_value = triggers
        mock_trigger_repo.update = AsyncMock()
        
        # Mock template service
        mock_template_service = AsyncMock()
        mock_template_service.execute_template.return_value = Success(ReportExecution(
            id=str(uuid.uuid4()),
            report_template_id="",
            triggered_by="scheduler",
            trigger_type=ReportTriggerType.SCHEDULED
        ))
        
        # Mock get_service
        mock_get_service.return_value = mock_template_service
        
        # Act
        result = await trigger_service.process_due_triggers()
        
        # Assert
        mock_trigger_repo.find_active_scheduled_triggers.assert_called_once()
        assert mock_template_service.execute_template.call_count == len(triggers)
        assert mock_trigger_repo.update.call_count == len(triggers)
        assert result.is_success
        assert result.value == len(triggers)


class TestReportOutputService:
    """Tests for the ReportOutputService class."""

    async def test_find_by_template_id(self, output_service, mock_output_repo, create_output):
        """Test finding outputs by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        outputs = [
            create_output(template_id=template_id),
            create_output(template_id=template_id)
        ]
        mock_output_repo.find_by_template_id.return_value = outputs
        
        # Act
        result = await output_service.find_by_template_id(template_id)
        
        # Assert
        mock_output_repo.find_by_template_id.assert_called_once_with(template_id)
        assert result.is_success
        assert result.value == outputs

    async def test_find_by_output_type(self, output_service, mock_output_repo, create_output):
        """Test finding outputs by output type."""
        # Arrange
        output_type = ReportOutputType.EMAIL
        outputs = [
            create_output(output_type=output_type),
            create_output(output_type=output_type)
        ]
        mock_output_repo.find_by_output_type.return_value = outputs
        
        # Act
        result = await output_service.find_by_output_type(output_type)
        
        # Assert
        mock_output_repo.find_by_output_type.assert_called_once_with(output_type)
        assert result.is_success
        assert result.value == outputs

    async def test_find_active_outputs(self, output_service, mock_output_repo, create_output):
        """Test finding all active outputs."""
        # Arrange
        outputs = [create_output(), create_output()]
        mock_output_repo.find_active_outputs.return_value = outputs
        
        # Act
        result = await output_service.find_active_outputs()
        
        # Assert
        mock_output_repo.find_active_outputs.assert_called_once()
        assert result.is_success
        assert result.value == outputs


class TestReportExecutionService:
    """Tests for the ReportExecutionService class."""

    async def test_find_by_template_id(self, execution_service, mock_execution_repo, create_execution):
        """Test finding executions by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        executions = [
            create_execution(template_id=template_id),
            create_execution(template_id=template_id)
        ]
        mock_execution_repo.find_by_template_id.return_value = executions
        
        # Act
        result = await execution_service.find_by_template_id(template_id)
        
        # Assert
        mock_execution_repo.find_by_template_id.assert_called_once_with(template_id)
        assert result.is_success
        assert result.value == executions

    async def test_find_by_status(self, execution_service, mock_execution_repo, create_execution):
        """Test finding executions by status."""
        # Arrange
        status = ReportExecutionStatus.PENDING
        executions = [
            create_execution(status=status),
            create_execution(status=status)
        ]
        mock_execution_repo.find_by_status.return_value = executions
        
        # Act
        result = await execution_service.find_by_status(status)
        
        # Assert
        mock_execution_repo.find_by_status.assert_called_once_with(status)
        assert result.is_success
        assert result.value == executions

    async def test_find_by_triggered_by(self, execution_service, mock_execution_repo, create_execution):
        """Test finding executions by triggered by."""
        # Arrange
        triggered_by = "test_user"
        executions = [create_execution(), create_execution()]
        mock_execution_repo.find_by_triggered_by.return_value = executions
        
        # Act
        result = await execution_service.find_by_triggered_by(triggered_by)
        
        # Assert
        mock_execution_repo.find_by_triggered_by.assert_called_once_with(triggered_by)
        assert result.is_success
        assert result.value == executions

    async def test_find_with_output_executions(self, execution_service, mock_execution_repo, create_execution):
        """Test finding an execution with output executions loaded."""
        # Arrange
        execution_id = str(uuid.uuid4())
        execution = create_execution(id_=execution_id)
        mock_execution_repo.find_with_output_executions.return_value = Success(execution)
        
        # Act
        result = await execution_service.find_with_output_executions(execution_id)
        
        # Assert
        mock_execution_repo.find_with_output_executions.assert_called_once_with(execution_id)
        assert result.is_success
        assert result.value == execution

    async def test_find_recent_executions(self, execution_service, mock_execution_repo, create_execution):
        """Test finding recent executions."""
        # Arrange
        limit = 5
        executions = [create_execution(), create_execution()]
        mock_execution_repo.find_recent_executions.return_value = executions
        
        # Act
        result = await execution_service.find_recent_executions(limit)
        
        # Assert
        mock_execution_repo.find_recent_executions.assert_called_once_with(limit)
        assert result.is_success
        assert result.value == executions

    async def test_update_execution_status_success(self, execution_service, mock_execution_repo, create_execution):
        """Test successfully updating the status of an execution."""
        # Arrange
        execution_id = str(uuid.uuid4())
        execution = create_execution(id_=execution_id)
        new_status = ReportExecutionStatus.COMPLETED
        
        # Mock repository methods
        mock_execution_repo.get.return_value = Success(execution)
        mock_execution_repo.update.return_value = Success(execution)
        
        # Act
        result = await execution_service.update_execution_status(
            execution_id=execution_id,
            status=new_status
        )
        
        # Assert
        mock_execution_repo.get.assert_called_once_with(execution_id)
        mock_execution_repo.update.assert_called_once()
        assert result.is_success
        assert result.value.status == new_status


class TestReportOutputExecutionService:
    """Tests for the ReportOutputExecutionService class."""

    async def test_find_by_execution_id(self, output_execution_service, mock_output_execution_repo, create_output_execution):
        """Test finding output executions by execution ID."""
        # Arrange
        execution_id = str(uuid.uuid4())
        output_executions = [
            create_output_execution(execution_id=execution_id),
            create_output_execution(execution_id=execution_id)
        ]
        mock_output_execution_repo.find_by_execution_id.return_value = output_executions
        
        # Act
        result = await output_execution_service.find_by_execution_id(execution_id)
        
        # Assert
        mock_output_execution_repo.find_by_execution_id.assert_called_once_with(execution_id)
        assert result.is_success
        assert result.value == output_executions

    async def test_find_by_output_id(self, output_execution_service, mock_output_execution_repo, create_output_execution):
        """Test finding output executions by output ID."""
        # Arrange
        output_id = str(uuid.uuid4())
        output_executions = [
            create_output_execution(output_id=output_id),
            create_output_execution(output_id=output_id)
        ]
        mock_output_execution_repo.find_by_output_id.return_value = output_executions
        
        # Act
        result = await output_execution_service.find_by_output_id(output_id)
        
        # Assert
        mock_output_execution_repo.find_by_output_id.assert_called_once_with(output_id)
        assert result.is_success
        assert result.value == output_executions

    async def test_find_by_status(self, output_execution_service, mock_output_execution_repo, create_output_execution):
        """Test finding output executions by status."""
        # Arrange
        status = ReportExecutionStatus.PENDING
        output_executions = [
            create_output_execution(status=status),
            create_output_execution(status=status)
        ]
        mock_output_execution_repo.find_by_status.return_value = output_executions
        
        # Act
        result = await output_execution_service.find_by_status(status)
        
        # Assert
        mock_output_execution_repo.find_by_status.assert_called_once_with(status)
        assert result.is_success
        assert result.value == output_executions

    async def test_update_output_execution_status_success(self, output_execution_service, mock_output_execution_repo, create_output_execution):
        """Test successfully updating the status of an output execution."""
        # Arrange
        output_execution_id = str(uuid.uuid4())
        output_execution = create_output_execution(id_=output_execution_id)
        new_status = ReportExecutionStatus.COMPLETED
        
        # Mock repository methods
        mock_output_execution_repo.get.return_value = Success(output_execution)
        mock_output_execution_repo.update.return_value = Success(output_execution)
        
        # Act
        result = await output_execution_service.update_output_execution_status(
            output_execution_id=output_execution_id,
            status=new_status
        )
        
        # Assert
        mock_output_execution_repo.get.assert_called_once_with(output_execution_id)
        mock_output_execution_repo.update.assert_called_once()
        assert result.is_success
        assert result.value.status == new_status